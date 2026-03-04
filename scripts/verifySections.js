#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import { importMcGillJson } from '../src/utils/mirImport.js'

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'))
}

function toSec(v) {
  return Number(v) / 1000
}

function fromMsSections(sections) {
  return sections.map((s, i) => {
    const startMs = Number(s.start_ms ?? 0)
    const durationMs = Number(s.duration_ms ?? 0)
    const endMs = startMs + durationMs
    return {
      idx: i,
      label: String(s.sectionType ?? s.name ?? 'Other'),
      startSec: toSec(startMs),
      endSec: toSec(endMs),
    }
  }).filter(s => Number.isFinite(s.startSec) && Number.isFinite(s.endSec) && s.endSec > s.startSec)
}

function fromImportedSections(sections) {
  return sections.map((s, i) => {
    const startSec = toSec(Number(s.sourceStartMs ?? 0))
    const endSec = toSec(Number((s.sourceStartMs ?? 0) + (s.sourceDurationMs ?? 0)))
    return {
      idx: i,
      label: String(s.name ?? 'Part'),
      startSec,
      endSec,
    }
  }).filter(s => Number.isFinite(s.startSec) && Number.isFinite(s.endSec) && s.endSec > s.startSec)
}

function normalizeReference(refJson) {
  if (!Array.isArray(refJson.sections)) {
    throw new Error('Reference JSON must contain a "sections" array.')
  }
  return refJson.sections.map((s, i) => {
    const label = String(s.label ?? s.name ?? `S${i + 1}`)
    const hasMs = Number.isFinite(s.start_ms) && (Number.isFinite(s.end_ms) || Number.isFinite(s.duration_ms))
    const hasSec = Number.isFinite(s.start_s) && (Number.isFinite(s.end_s) || Number.isFinite(s.duration_s))
    let startSec = 0
    let endSec = 0
    if (hasMs) {
      startSec = toSec(Number(s.start_ms))
      endSec = Number.isFinite(s.end_ms)
        ? toSec(Number(s.end_ms))
        : startSec + toSec(Number(s.duration_ms))
    } else if (hasSec) {
      startSec = Number(s.start_s)
      endSec = Number.isFinite(s.end_s)
        ? Number(s.end_s)
        : startSec + Number(s.duration_s)
    } else {
      throw new Error(`Reference section #${i + 1} missing supported timestamps.`)
    }
    return { idx: i, label, startSec, endSec }
  }).filter(s => Number.isFinite(s.startSec) && Number.isFinite(s.endSec) && s.endSec > s.startSec)
}

function uniqueSortedBoundaries(sections) {
  if (sections.length === 0) return []
  const first = sections[0].startSec
  const last = sections[sections.length - 1].endSec
  const starts = sections.map(s => s.startSec)
  const internal = starts.filter((t) => t !== first && t < last)
  return [...new Set(internal.map(t => Number(t.toFixed(3))))].sort((a, b) => a - b)
}

function boundaryMetrics(reference, predicted, toleranceSec) {
  const refB = uniqueSortedBoundaries(reference)
  const predB = uniqueSortedBoundaries(predicted)
  const used = new Set()
  let tp = 0
  for (const p of predB) {
    let best = -1
    let bestDist = Infinity
    for (let i = 0; i < refB.length; i += 1) {
      if (used.has(i)) continue
      const d = Math.abs(p - refB[i])
      if (d <= toleranceSec && d < bestDist) {
        bestDist = d
        best = i
      }
    }
    if (best >= 0) {
      used.add(best)
      tp += 1
    }
  }
  const fp = predB.length - tp
  const fn = refB.length - tp
  const precision = predB.length ? tp / predB.length : 0
  const recall = refB.length ? tp / refB.length : 0
  const f1 = (precision + recall) ? (2 * precision * recall) / (precision + recall) : 0
  return { tp, fp, fn, precision, recall, f1, refCount: refB.length, predCount: predB.length }
}

function segmentOverlap(a, b) {
  const start = Math.max(a.startSec, b.startSec)
  const end = Math.min(a.endSec, b.endSec)
  return Math.max(0, end - start)
}

function labelAgreement(reference, predicted) {
  if (!reference.length || !predicted.length) return { weightedAccuracy: 0, totalDur: 0 }
  let correctDur = 0
  let totalDur = 0
  for (const ref of reference) {
    const dur = ref.endSec - ref.startSec
    totalDur += dur
    let best = null
    let bestOverlap = 0
    for (const pred of predicted) {
      const ov = segmentOverlap(ref, pred)
      if (ov > bestOverlap) {
        bestOverlap = ov
        best = pred
      }
    }
    if (!best || bestOverlap <= 0) continue
    const refNorm = ref.label.trim().toLowerCase()
    const predNorm = best.label.trim().toLowerCase()
    if (refNorm === predNorm) correctDur += dur
  }
  return {
    weightedAccuracy: totalDur ? correctDur / totalDur : 0,
    totalDur,
  }
}

function parseArgs(argv) {
  const out = {
    song: '',
    reference: '',
    salamiRefs: '',
    salamiSongId: '',
    salamiAnnotator: 'primary',
    strategy: 'auto-json',
    tolerance: 0.5,
    mode: 'compare',
  }
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i]
    if (a === '--song') out.song = argv[i + 1] ?? ''
    if (a === '--reference') out.reference = argv[i + 1] ?? ''
    if (a === '--salami-refs') out.salamiRefs = argv[i + 1] ?? ''
    if (a === '--salami-song-id') out.salamiSongId = argv[i + 1] ?? ''
    if (a === '--salami-annotator') out.salamiAnnotator = argv[i + 1] ?? 'primary'
    if (a === '--strategy') out.strategy = argv[i + 1] ?? 'auto-json'
    if (a === '--tolerance') out.tolerance = Number(argv[i + 1] ?? 0.5)
    if (a === '--mode') out.mode = argv[i + 1] ?? 'compare'
  }
  return out
}

function printUsage() {
  console.log('Usage:')
  console.log('  npm run verify:sections -- --song <dataset json> [--strategy auto-json|dataset] [--reference <reference json>] [--tolerance 0.5]')
  console.log('  npm run verify:sections -- --song <dataset json> --salami-refs data/normalized/salami/salami_references.json --salami-song-id <id> [--salami-annotator primary|textfile1_functions.txt|textfile2_functions.txt]')
  console.log('  npm run verify:sections -- --mode template --song <dataset json>')
  console.log('')
  console.log('Reference JSON format:')
  console.log('  { "sections": [ { "label":"Verse", "start_s":12.0, "end_s":35.4 } ] }')
  console.log('  or use start_ms/end_ms (or duration_*) fields.')
}

function referenceFromSalami(args) {
  const refs = readJson(path.resolve(args.salamiRefs))
  if (!Array.isArray(refs)) throw new Error('SALAMI refs must be a JSON array.')
  const row = refs.find((r) => String(r.song_id) === String(args.salamiSongId))
  if (!row) throw new Error(`SALAMI song_id not found: ${args.salamiSongId}`)
  if (!Array.isArray(row.annotators) || row.annotators.length === 0) {
    throw new Error(`SALAMI song_id has no annotator sections: ${args.salamiSongId}`)
  }

  let chosen = null
  if (args.salamiAnnotator === 'primary') {
    chosen = row.annotators.find((a) => a.annotatorFile === row.primary_annotator) ?? row.annotators[0]
  } else {
    chosen = row.annotators.find((a) => a.annotatorFile === args.salamiAnnotator) ?? null
  }
  if (!chosen) {
    throw new Error(`SALAMI annotator not found for song ${args.salamiSongId}: ${args.salamiAnnotator}`)
  }

  return {
    name: `salami:${args.salamiSongId}:${chosen.annotatorFile}`,
    sections: (chosen.sections ?? []).map((s, i) => ({
      idx: i,
      label: String(s.label ?? `S${i + 1}`),
      startSec: Number(s.start_s),
      endSec: Number(s.end_s),
    })).filter((s) => Number.isFinite(s.startSec) && Number.isFinite(s.endSec) && s.endSec > s.startSec),
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  if (!args.song) {
    printUsage()
    process.exit(1)
  }

  const songPath = path.resolve(args.song)
  if (!fs.existsSync(songPath)) {
    throw new Error(`Song file not found: ${songPath}`)
  }
  const songJson = readJson(songPath)

  if (args.mode === 'template') {
    const template = { sections: fromMsSections(songJson.sections ?? []) }
    console.log(JSON.stringify(template, null, 2))
    return
  }

  const imported = importMcGillJson(songJson, { sectionStrategy: args.strategy })
  const predicted = fromImportedSections(imported)
  let reference = []
  let referenceName = 'dataset_sections'
  if (args.salamiRefs && args.salamiSongId) {
    const fromSalami = referenceFromSalami(args)
    reference = fromSalami.sections
    referenceName = fromSalami.name
  } else if (args.reference) {
    const refPath = path.resolve(args.reference)
    const refJson = readJson(refPath)
    reference = normalizeReference(refJson)
    referenceName = path.basename(refPath)
  } else {
    reference = fromMsSections(songJson.sections ?? [])
  }

  const b = boundaryMetrics(reference, predicted, args.tolerance)
  const l = labelAgreement(reference, predicted)

  console.log(`Song: ${songJson.title ?? path.basename(songPath)} — ${songJson.artist ?? 'Unknown'}`)
  console.log(`Strategy: ${args.strategy}`)
  console.log(`Reference: ${referenceName}`)
  console.log(`Tolerance: ${args.tolerance}s`)
  console.log('')
  console.log('Boundary metrics')
  console.log(`  TP=${b.tp} FP=${b.fp} FN=${b.fn}`)
  console.log(`  Precision=${b.precision.toFixed(3)} Recall=${b.recall.toFixed(3)} F1=${b.f1.toFixed(3)}`)
  console.log(`  Pred boundaries=${b.predCount} Ref boundaries=${b.refCount}`)
  console.log('')
  console.log('Label overlap metric')
  console.log(`  Weighted label accuracy=${l.weightedAccuracy.toFixed(3)} (duration-weighted exact label match)`)
}

try {
  main()
} catch (err) {
  console.error(`verifySections error: ${err instanceof Error ? err.message : String(err)}`)
  process.exit(1)
}
