#!/usr/bin/env node
/**
 * Download a subset of SALAMI YouTube pairings into data/audio/.
 * Defaults to first 50 rows of salami_youtube_pairings.csv.
 */
import fs from 'fs'
import path from 'path'
import { spawnSync } from 'child_process'

const CSV_PATH = path.resolve('scripts/matching-salami/salami_youtube_pairings.csv')
const OUT_LIST = path.resolve('data/truth/salami_pairings_subset.json')
const AUDIO_DIR = path.resolve('data/audio')

function main() {
  const n = Number(process.env.SUBSET || 50)
  if (!fs.existsSync(CSV_PATH)) {
    console.error(`Missing ${CSV_PATH}`)
    process.exit(1)
  }
  const lines = fs.readFileSync(CSV_PATH, 'utf8').split(/\r?\n/).filter(Boolean)
  const header = lines.shift().split(',')
  const sidIdx = header.indexOf('salami_id')
  const ytIdx = header.indexOf('youtube_id')
  if (sidIdx < 0 || ytIdx < 0) {
    console.error('CSV missing salami_id or youtube_id columns')
    process.exit(1)
  }
  const subset = lines.slice(0, n).map((row) => {
    const cols = row.split(',')
    return { salami_id: cols[sidIdx], youtube_id: cols[ytIdx] }
  })
  fs.mkdirSync(path.dirname(OUT_LIST), { recursive: true })
  fs.writeFileSync(OUT_LIST, JSON.stringify(subset, null, 2))
  fs.mkdirSync(AUDIO_DIR, { recursive: true })
  console.log(`Downloading ${subset.length} tracks...`)
  for (const row of subset) {
    const url = `https://www.youtube.com/watch?v=${row.youtube_id}`
    const slug = `salami_${row.salami_id}`
    const res = spawnSync('node', ['scripts/experiments/downloadAudio.js', '--url', url, '--slug', slug, '--out-dir', 'data/audio'], { stdio: 'inherit' })
    if (res.status !== 0) {
      console.error(`Download failed for ${slug}`)
    }
  }
  console.log(`Done. Audio in ${AUDIO_DIR}`)
}

main()
