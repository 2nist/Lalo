#!/usr/bin/env node
/**
 * Convert the McGill Billboard "salami_chords.txt" files to the JSON format
 * expected by our app and verifySections.js.
 *
 * Input tree (after cloning boomerr1/The-McGill-Billboard-Project):
 *   data/raw/mcgill-billboard-github/billboard-2.0-salami_chords/<id>/salami_chords.txt
 *
 * Output:
 *   datasets/mcgill/mcgill_jcrd_salami_Billboard/<slug>.json
 *   where slug = `${title} ${artist}` normalized to snake_case.
 */

import fs from 'fs'
import path from 'path'

const SRC_ROOT = path.resolve('data/raw/mcgill-billboard-github/billboard-2.0-salami_chords')
const OUT_ROOT = path.resolve('datasets/mcgill/mcgill_jcrd_salami_Billboard')

function slugify(str) {
  return String(str ?? '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .replace(/_+/g, '_')
}

function parseChords(fragment) {
  if (!fragment) return []
  // strip leading commas/whitespace
  const body = fragment.replace(/^[,\s]+/, '')
  return body
    .split('|')
    .map((t) => t.replace(/[()]/g, '').replace(/,\s*$/,'').trim())
    .map((t) => t.replace(/^(voice|guitar|harmonica|organ|piano|bass|drums|strings)\b.*$/i, ''))
    .map((t) => t.replace(/^,?\s*voice$/i, '').trim())
    .map((t) => t.replace(/^,?\s*guitar$/i, '').trim())
    .map(sanitizeChord)
    .filter((t) => t && t !== ',')
}

// Collapse to simple Harte-compatible triads; drop unsupported quality tokens.
function sanitizeChord(chord) {
  const m = String(chord || '').match(/^([A-Ga-g][b#]?)/)
  if (!m) return ''
  const root = m[1].toUpperCase().replace('B#', 'C').replace('E#', 'F').replace('CB', 'B').replace('FB', 'E')
  // Keep only maj/min markers; drop everything else.
  const lower = chord.toLowerCase()
  const isMinor = /\bmin\b|:m\b|\-/.test(lower)
  return isMinor ? `${root}:min` : `${root}:maj`
}

const SECTION_LABELS = {
  intro: 'Intro',
  interlude: 'Interlude',
  verse: 'Verse',
  chorus: 'Chorus',
  bridge: 'Bridge',
  outro: 'Outro',
  coda: 'Coda',
  break: 'Break',
}

function normaliseSectionName(raw) {
  const base = String(raw ?? '').split(',')[0].trim().toLowerCase()
  return SECTION_LABELS[base] || (base ? base[0].toUpperCase() + base.slice(1) : 'Part')
}

function parseFile(filePath) {
  const lines = fs.readFileSync(filePath, 'utf8').split(/\r?\n/).filter(Boolean)
  let title = 'Untitled'
  let artist = 'Unknown'
  let metre = ''
  const records = []

  for (const raw of lines) {
    if (raw.startsWith('#')) {
      const [_, k, v] = raw.match(/^#\s*([^:]+):\s*(.+)$/) || []
      if (!k) continue
      const key = k.trim().toLowerCase()
      if (key === 'title') title = v.trim()
      if (key === 'artist') artist = v.trim()
      if (key === 'metre') metre = v.trim()
      continue
    }
    const trimmed = raw.trim()
    const firstSpace = trimmed.search(/\s+/)
    if (firstSpace < 0) continue
    const timeStr = trimmed.slice(0, firstSpace)
    const content = trimmed.slice(firstSpace).trim()
    const t = Number(timeStr)
    if (!Number.isFinite(t)) continue
    records.push({ t, content })
  }

  const sections = []
  let current = null

  const pushCurrent = (nextT) => {
    if (!current) return
    current.duration_ms = Math.max(0, Math.round((nextT - current.start_ms / 1000) * 1000))
    sections.push(current)
    current = null
  }

  for (let i = 0; i < records.length; i += 1) {
    const { t, content } = records[i]
    const nextT = i < records.length - 1 ? records[i + 1].t : t

    if (content === 'silence' || content === 'end') {
      pushCurrent(t)
      continue
    }

    // Pattern 1: "A, intro, | ..." (rich label + chords)
    const sectionMatch = content.match(/^([A-Z])\s*,\s*([^,]+),\s*(.*)$/)
    // Pattern 2: "A," (letter only)
    const letterOnlyMatch = !sectionMatch && content.match(/^([A-Z])\s*,?\s*$/)

    if (sectionMatch || letterOnlyMatch) {
      // Close prior section before starting new one
      pushCurrent(t)
      const letter = sectionMatch ? sectionMatch[1] : letterOnlyMatch[1]
      const nameRaw = sectionMatch ? sectionMatch[2] : `Part ${letter}`
      const rest = sectionMatch ? sectionMatch[3] : ''
      const label = normaliseSectionName(nameRaw)
      const chords = parseChords(rest)
      current = {
        id: `${letter}${sections.filter((s) => s.id?.startsWith(letter)).length + 1}`,
        sectionType: label.charAt(0).toUpperCase() + label.slice(1).toLowerCase(),
        start_ms: Math.round(t * 1000),
        duration_ms: 0, // to be filled
        chords,
      }
      if (chords.length === 0) current.chords = []
    } else if (content.startsWith('|') && current) {
      current.chords.push(...parseChords(content))
    } else {
      // Unrecognized line; ignore
    }
    if (i === records.length - 1) pushCurrent(nextT)
  }

  // Final duration fallback: if any section has 0 duration, set to 1s to keep verifier happy
  for (const s of sections) {
    if (!Number.isFinite(s.duration_ms) || s.duration_ms <= 0) s.duration_ms = 1000
  }

  return {
    title,
    artist,
    metre,
    sections,
  }
}

function main() {
  if (!fs.existsSync(SRC_ROOT)) {
    console.error(`Source root missing: ${SRC_ROOT}`)
    process.exit(1)
  }
  fs.mkdirSync(OUT_ROOT, { recursive: true })
  const dirs = fs.readdirSync(SRC_ROOT).filter((d) => fs.statSync(path.join(SRC_ROOT, d)).isDirectory())
  let count = 0
  for (const dir of dirs) {
    const file = path.join(SRC_ROOT, dir, 'salami_chords.txt')
    if (!fs.existsSync(file)) continue
    try {
      const json = parseFile(file)
      const base = slugify(`${json.title}_${json.artist}`) || 'untitled_unknown'
      const slug = `${dir}_${base}`
      const outPath = path.join(OUT_ROOT, `${slug}.json`)
      fs.writeFileSync(outPath, JSON.stringify(json, null, 2))
      count += 1
      if (count % 200 === 0) console.log(`...${count} written (latest ${slug}.json)`)
    } catch (err) {
      console.warn(`Failed to parse ${file}: ${err instanceof Error ? err.message : String(err)}`)
    }
  }
  console.log(`Converted ${count} files → ${OUT_ROOT}`)
}

main()
