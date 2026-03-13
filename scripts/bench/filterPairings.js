#!/usr/bin/env node
/**
 * Filter salami_youtube_pairings.csv to only the SALAMI ids in benchmark_exact.json
 * Output: data/truth/salami_pairings_benchmark.csv
 */
import fs from 'fs'
import path from 'path'

const PAIRINGS = path.resolve('data/truth/salami_youtube_pairings.csv')
const BENCH = path.resolve('data/truth/benchmark_exact.json')
const OUT = path.resolve('data/truth/salami_pairings_benchmark.csv')

function main() {
  if (!fs.existsSync(PAIRINGS)) {
    console.error(`Missing pairings CSV at ${PAIRINGS}`)
    process.exit(1)
  }
  if (!fs.existsSync(BENCH)) {
    console.error(`Missing benchmark list at ${BENCH} (run npm run bench:sections:list)`)
    process.exit(1)
  }
  const bench = JSON.parse(fs.readFileSync(BENCH, 'utf8'))
  const keepIds = new Set(
    bench
      .flatMap((r) => r.salami_song_ids || [])
      .map((x) => String(x)),
  )
  const lines = fs.readFileSync(PAIRINGS, 'utf8').split(/\r?\n/).filter(Boolean)
  const header = lines[0]
  const rows = lines.slice(1)
  const filtered = rows.filter((row) => {
    const cols = row.split(',')
    const sid = cols[0]
    return keepIds.has(sid)
  })
  fs.writeFileSync(OUT, [header, ...filtered].join('\n'))
  console.log(`Filtered ${filtered.length} rows → ${OUT}`)
}

main()
