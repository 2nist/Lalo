#!/usr/bin/env node
/**
 * Build a benchmark list of McGill↔SALAMI pairs for section evaluation.
 * Uses exact title+artist matches only (highest confidence).
 *
 * Output: data/truth/benchmark_exact.json
 */

import fs from 'fs'
import path from 'path'

const MATCH_PATH = path.resolve('data/normalized/salami/mcgill_to_salami_matches.json')
const OUT_PATH = path.resolve('data/truth/benchmark_fuzzy.json')

function main() {
  if (!fs.existsSync(MATCH_PATH)) {
    console.error(`Missing match map: ${MATCH_PATH}. Run npm run dataset:build:salami-refs first.`)
    process.exit(1)
  }
  const map = JSON.parse(fs.readFileSync(MATCH_PATH, 'utf8'))
  const exact = map.filter((m) => m.confidence === 'exact_title_artist' && Array.isArray(m.salami_song_ids) && m.salami_song_ids.length === 1)
  const strongFuzzy = map.filter((m) => m.confidence === 'strong_fuzzy' && Array.isArray(m.salami_song_ids) && m.salami_song_ids.length === 1)
  const fuzzy = map.filter((m) => m.confidence === 'fuzzy' && Array.isArray(m.salami_song_ids) && m.salami_song_ids.length === 1)
  const merged = [...exact, ...strongFuzzy, ...fuzzy]
  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true })
  fs.writeFileSync(OUT_PATH, JSON.stringify(merged, null, 2))
  console.log(`Exact matches: ${exact.length}`)
  console.log(`Strong fuzzy: ${strongFuzzy.length}`)
  console.log(`Fuzzy: ${fuzzy.length}`)
  console.log(`Total benchmark entries: ${merged.length}`)
  console.log(`Wrote: ${OUT_PATH}`)
}

main()
