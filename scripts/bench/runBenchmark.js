#!/usr/bin/env node
/**
 * Run section benchmark against SALAMI references using the benchmark list.
 *
 * Prereqs:
 *   - data/truth/benchmark_exact.json (npm run bench:sections:list)
 *   - data/normalized/salami/salami_references.json (npm run dataset:build:salami-refs)
 *
 * Outputs per-song stats and summary (mean F1 / label acc).
 */

import fs from 'fs'
import path from 'path'
import { spawnSync } from 'child_process'

const BENCH_LIST = path.resolve('data/truth/benchmark_exact.json')
const SALAMI_REFS = path.resolve('data/normalized/salami/salami_references.json')

function runOne(row) {
  const song = `datasets/mcgill/mcgill_jcrd_salami_Billboard/${row.filename}`
  const salamiId = row.salami_song_ids[0]
  const args = [
    'scripts/verifySections.js',
    '--song', song,
    '--salami-refs', SALAMI_REFS,
    '--salami-song-id', String(salamiId),
    '--salami-annotator', 'primary',
    '--beats-dir', 'data/beats',
    '--beat-snap', '0.25',
    '--min-section', '4',
    '--max-section', '30',
  ]
  const res = spawnSync('node', args, { encoding: 'utf8' })
  if (res.status !== 0) {
    return { ok: false, err: res.stderr || res.stdout || `exit ${res.status}` }
  }
  // parse lines for F1 and weighted accuracy
  const f1Match = res.stdout.match(/F1=([0-9.]+)/)
  const accMatch = res.stdout.match(/Weighted label accuracy=([0-9.]+)/)
  const f1 = f1Match ? Number(f1Match[1]) : NaN
  const acc = accMatch ? Number(accMatch[1]) : NaN
  return { ok: true, f1, acc, log: res.stdout.trim() }
}

function main() {
  if (!fs.existsSync(BENCH_LIST)) {
    console.error('Benchmark list missing. Run: npm run bench:sections:list')
    process.exit(1)
  }
  const list = JSON.parse(fs.readFileSync(BENCH_LIST, 'utf8'))
  if (!Array.isArray(list) || list.length === 0) {
    console.error('Benchmark list is empty.')
    process.exit(1)
  }
  const results = []
  for (const row of list) {
    const r = runOne(row)
    results.push({ filename: row.filename, salami: row.salami_song_ids[0], ...r })
    const status = r.ok ? 'OK' : 'FAIL'
    console.log(`${status} ${row.filename}${r.ok ? ` f1=${r.f1?.toFixed(3)} acc=${r.acc?.toFixed(3)}` : ''}`)
    if (!r.ok) console.log(`  ${r.err}`)
  }
  const ok = results.filter(r => r.ok && Number.isFinite(r.f1) && Number.isFinite(r.acc))
  const meanF1 = ok.reduce((s, r) => s + r.f1, 0) / (ok.length || 1)
  const meanAcc = ok.reduce((s, r) => s + r.acc, 0) / (ok.length || 1)
  console.log(`--- Summary ---`)
  console.log(`Total: ${results.length}, OK: ${ok.length}, Fail: ${results.length - ok.length}`)
  console.log(`Mean F1: ${meanF1.toFixed(3)} | Mean label acc: ${meanAcc.toFixed(3)}`)
}

main()
