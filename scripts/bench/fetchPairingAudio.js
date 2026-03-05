#!/usr/bin/env node
/**
 * Download YouTube audio for SALAMI pairings (benchmark subset) into data/audio/.
 * Uses yt-dlp via our downloadAudio.js wrapper.
 *
 * Input CSV: data/truth/salami_pairings_benchmark.csv (salami_song_id,youtube_id,...)
 */
import fs from 'fs'
import path from 'path'
import { spawnSync } from 'child_process'

const PAIRINGS = path.resolve('data/truth/salami_pairings_benchmark.csv')

function main() {
  if (!fs.existsSync(PAIRINGS)) {
    console.error(`Missing ${PAIRINGS}. Run: npm run bench:sections:list && node scripts/bench/filterPairings.js`)
    process.exit(1)
  }
  const lines = fs.readFileSync(PAIRINGS, 'utf8').split(/\r?\n/).filter(Boolean)
  const header = lines[0].split(',')
  const sidIdx = header.indexOf('salami_id')
  const ytIdx = header.indexOf('youtube_id')
  if (sidIdx < 0 || ytIdx < 0) {
    console.error('CSV missing salami_id or youtube_id columns')
    process.exit(1)
  }
  for (const row of lines.slice(1)) {
    const cols = row.split(',')
    const salamiId = cols[sidIdx]
    const ytId = cols[ytIdx]
    const url = `https://www.youtube.com/watch?v=${ytId}`
    const slug = `salami_${salamiId}`
    const args = ['scripts/experiments/downloadAudio.js', '--url', url, '--slug', slug, '--out-dir', 'data/audio']
    const res = spawnSync('node', args, { stdio: 'inherit' })
    if (res.status !== 0) {
      console.error(`Failed ${slug}`)
    }
  }
}

main()
