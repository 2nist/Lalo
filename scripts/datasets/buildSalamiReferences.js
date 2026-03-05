#!/usr/bin/env node
import fs from 'fs'
import path from 'path'

const DEFAULT_SALAMI_ROOT = 'data/raw/salami-data-public'
const DEFAULT_MCGILL_ROOT = 'datasets/mcgill/mcgill_jcrd_salami_Billboard'
const DEFAULT_OUT_DIR = 'data/normalized/salami'

function parseArgs(argv) {
  const args = {
    salamiRoot: DEFAULT_SALAMI_ROOT,
    mcgillRoot: DEFAULT_MCGILL_ROOT,
    outDir: DEFAULT_OUT_DIR,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i]
    if (a === '--salami-root') args.salamiRoot = argv[i + 1] ?? DEFAULT_SALAMI_ROOT
    if (a === '--mcgill-root') args.mcgillRoot = argv[i + 1] ?? DEFAULT_MCGILL_ROOT
    if (a === '--out-dir') args.outDir = argv[i + 1] ?? DEFAULT_OUT_DIR
  }
  return args
}

function normalizeText(v) {
  return String(v ?? '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .replace(/\s+/g, ' ')
}

function tokenSet(str) {
  return new Set(normalizeText(str).split(' ').filter(Boolean))
}

function tokenJaccard(a, b) {
  const aSet = tokenSet(a)
  const bSet = tokenSet(b)
  if (!aSet.size || !bSet.size) return 0
  let inter = 0
  for (const t of aSet) {
    if (bSet.has(t)) inter += 1
  }
  const union = aSet.size + bSet.size - inter
  return inter / union
}

function splitCsvLine(line) {
  const out = []
  let cur = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        cur += '"'
        i += 1
      } else inQuotes = !inQuotes
    } else if (ch === ',' && !inQuotes) {
      out.push(cur)
      cur = ''
    } else cur += ch
  }
  out.push(cur)
  return out
}

function parseCsv(filePath) {
  const text = fs.readFileSync(filePath, 'utf8')
  const lines = text.split(/\r?\n/).filter(Boolean)
  if (lines.length === 0) return []
  const header = splitCsvLine(lines[0])
  return lines.slice(1).map((line) => {
    const cols = splitCsvLine(line)
    const row = {}
    header.forEach((k, i) => { row[k] = cols[i] ?? '' })
    return row
  })
}

function parseFunctionsFile(filePath) {
  const lines = fs.readFileSync(filePath, 'utf8').split(/\r?\n/).filter(Boolean)
  const points = lines.map((line) => {
    const [timeStr, ...labelParts] = line.split('\t')
    const t = Number(timeStr)
    const label = labelParts.join('\t').trim()
    return { t, label }
  }).filter((x) => Number.isFinite(x.t) && x.label)

  const sections = []
  for (let i = 0; i < points.length - 1; i += 1) {
    const cur = points[i]
    const next = points[i + 1]
    const l = cur.label.toLowerCase()
    if (l === 'silence' || l === 'end') continue
    if (!(next.t > cur.t)) continue
    sections.push({
      label: cur.label,
      start_s: Number(cur.t.toFixed(6)),
      end_s: Number(next.t.toFixed(6)),
      duration_s: Number((next.t - cur.t).toFixed(6)),
    })
  }
  return sections
}

function choosePrimaryAnnotator(annotators) {
  if (!annotators.length) return null
  const sorted = [...annotators].sort((a, b) => {
    if (b.sections.length !== a.sections.length) return b.sections.length - a.sections.length
    return a.annotatorFile.localeCompare(b.annotatorFile)
  })
  return sorted[0].annotatorFile
}

function readMcGillSongs(mcgillRoot) {
  if (!fs.existsSync(mcgillRoot)) return []
  const files = fs.readdirSync(mcgillRoot).filter((f) => f.endsWith('.json') && !f.endsWith('.jcrd.json'))
  const rows = []
  for (const file of files) {
    const full = path.join(mcgillRoot, file)
    const raw = fs.readFileSync(full, 'utf8')
    if (!raw.trim()) continue
    try {
      const json = JSON.parse(raw)
      const title = String(json.title ?? '')
      const artist = String(json.artist ?? '')
      rows.push({
        filename: file,
        title,
        artist,
        normTitle: normalizeText(title),
        normArtist: normalizeText(artist),
      })
    } catch {
      // ignore malformed files here
    }
  }
  return rows
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  const salamiRoot = path.resolve(args.salamiRoot)
  const outDir = path.resolve(args.outDir)
  const metadataPath = path.join(salamiRoot, 'metadata', 'metadata.csv')
  const annotationsRoot = path.join(salamiRoot, 'annotations')

  if (!fs.existsSync(metadataPath) || !fs.existsSync(annotationsRoot)) {
    throw new Error(`SALAMI root missing metadata/annotations: ${salamiRoot}`)
  }

  const metadataRows = parseCsv(metadataPath)
  const index = []
  const references = []
  const byId = new Map()

  for (const row of metadataRows) {
    const songId = String(row.SONG_ID ?? '').trim()
    if (!songId) continue
    const songDir = path.join(annotationsRoot, songId, 'parsed')
    const annotators = []
    if (fs.existsSync(songDir)) {
      const files = fs.readdirSync(songDir).filter((f) => f.endsWith('_functions.txt'))
      for (const file of files) {
        const sections = parseFunctionsFile(path.join(songDir, file))
        if (sections.length > 0) annotators.push({ annotatorFile: file, sections })
      }
    }

    const title = String(row.SONG_TITLE ?? '')
    const artist = String(row.ARTIST ?? '')
    index.push({
      song_id: songId,
      title,
      artist,
      norm_title: normalizeText(title),
      norm_artist: normalizeText(artist),
      norm_full: normalizeText(`${title} ${artist}`),
      source: String(row.SOURCE ?? ''),
      genre: String(row.GENRE ?? ''),
      class: String(row.CLASS ?? ''),
      song_duration_s: Number(row.SONG_DURATION || 0),
      annotator_count: annotators.length,
    })
    byId.set(songId, {
      title,
      artist,
      norm_full: normalizeText(`${title} ${artist}`),
      song_duration_s: Number(row.SONG_DURATION || 0),
    })

    references.push({
      song_id: songId,
      title,
      artist,
      primary_annotator: choosePrimaryAnnotator(annotators),
      annotators,
    })
  }

  const byBoth = new Map()
  const byTitle = new Map()
  for (const row of index) {
    const kBoth = `${row.norm_title}|||${row.norm_artist}`
    if (!byBoth.has(kBoth)) byBoth.set(kBoth, [])
    byBoth.get(kBoth).push(row.song_id)
    if (!byTitle.has(row.norm_title)) byTitle.set(row.norm_title, [])
    byTitle.get(row.norm_title).push(row.song_id)
  }

  const mcgillSongs = readMcGillSongs(path.resolve(args.mcgillRoot))
  const matches = mcgillSongs.map((m) => {
    const kBoth = `${m.normTitle}|||${m.normArtist}`
    const both = byBoth.get(kBoth) ?? []
    const titleOnly = both.length ? [] : (byTitle.get(m.normTitle) ?? [])
    let confidence = 'none'
    let matched = []
    let score = 0
    if (both.length === 1) {
      confidence = 'exact_title_artist'
      matched = both
    } else if (both.length > 1) {
      confidence = 'ambiguous_title_artist'
      matched = both
    } else if (titleOnly.length === 1) {
      confidence = 'title_only'
      matched = titleOnly
    } else if (titleOnly.length > 1) {
      confidence = 'ambiguous_title'
      matched = titleOnly
    } else {
      // fuzzy token-set Jaccard on title+artist
      let bestScore = 0
      let bestIds = []
      const needle = normalizeText(`${m.title} ${m.artist}`)
      for (const row of index) {
        const sim = tokenJaccard(needle, row.norm_full)
        if (sim > bestScore + 1e-6) {
          bestScore = sim
          bestIds = [row.song_id]
        } else if (Math.abs(sim - bestScore) < 1e-6 && sim > 0) {
          bestIds.push(row.song_id)
        }
      }
      if (bestScore >= 0.7 && bestIds.length === 1) {
        confidence = bestScore >= 0.85 ? 'strong_fuzzy' : 'fuzzy'
        matched = bestIds
        score = Number(bestScore.toFixed(3))
      } else if (bestScore >= 0.7 && bestIds.length > 1) {
        confidence = 'ambiguous_fuzzy'
        matched = bestIds
        score = Number(bestScore.toFixed(3))
      }
    }
    return {
      filename: m.filename,
      title: m.title,
      artist: m.artist,
      confidence,
      salami_song_ids: matched,
      fuzzy_score: score,
    }
  })

  fs.mkdirSync(outDir, { recursive: true })
  fs.writeFileSync(path.join(outDir, 'salami_song_index.json'), JSON.stringify(index, null, 2))
  fs.writeFileSync(path.join(outDir, 'salami_references.json'), JSON.stringify(references, null, 2))
  fs.writeFileSync(path.join(outDir, 'mcgill_to_salami_matches.json'), JSON.stringify(matches, null, 2))

  const exact = matches.filter((m) => m.confidence === 'exact_title_artist').length
  const strongFuzzy = matches.filter((m) => m.confidence === 'strong_fuzzy').length
  const fuzzy = matches.filter((m) => m.confidence === 'fuzzy').length
  const any = matches.filter((m) => m.confidence !== 'none').length
  console.log(`SALAMI indexed songs: ${index.length}`)
  console.log(`SALAMI refs with parsed annotators: ${references.filter((r) => r.annotators.length > 0).length}`)
  console.log(`McGill matches: ${exact} exact, ${strongFuzzy} strong fuzzy, ${fuzzy} fuzzy, ${any} with any candidate, ${matches.length - any} unmatched`)
  console.log(`Wrote: ${path.join(outDir, 'salami_song_index.json')}`)
  console.log(`Wrote: ${path.join(outDir, 'salami_references.json')}`)
  console.log(`Wrote: ${path.join(outDir, 'mcgill_to_salami_matches.json')}`)
}

try {
  main()
} catch (err) {
  console.error(`buildSalamiReferences error: ${err instanceof Error ? err.message : String(err)}`)
  process.exit(1)
}

