#!/usr/bin/env node
/**
 * Fingerprint downloaded SALAMI pairing audio against salami_public_fpdb.pklz
 * using audfprint, and write matches to data/truth/audfprint_matches_subset.txt.
 *
 * Requires:
 *  - data/audio/salami_<id>.<ext>
 *  - scripts/matching-salami/audfprint/audfprint.py
 *  - scripts/matching-salami/salami_public_fpdb.pklz
 */
import fs from 'fs'
import path from 'path'
import { spawnSync } from 'child_process'

const AUDIO_DIR = path.resolve('data/audio')
const FPDB = path.resolve('scripts/matching-salami/salami_public_fpdb.pklz')
const AUDFPRINT = path.resolve('scripts/matching-salami/audfprint/audfprint.py')
const PYTHON = path.resolve('.venv', 'Scripts', 'python.exe')
const OUT = path.resolve('data/truth/audfprint_matches_subset.txt')

function main() {
  if (!fs.existsSync(FPDB)) {
    console.error(`Missing fingerprint DB: ${FPDB}`)
    process.exit(1)
  }
  const files = fs.readdirSync(AUDIO_DIR).filter(f => f.startsWith('salami_') && f.match(/\.(m4a|mp3|flac|ogg|wav)$/i))
  if (!files.length) {
    console.error(`No salami_*.audio files found in ${AUDIO_DIR}`)
    process.exit(1)
  }
  fs.writeFileSync(OUT, '')
  for (const f of files) {
    const full = path.join(AUDIO_DIR, f)
    console.log(`Matching ${f} ...`)
    const res = spawnSync(PYTHON, [
      AUDFPRINT,
      'match',
      '--dbase', FPDB,
      '--max-matches', '5',
      '--search-depth', '200',
      '--find-time-range',
      '--time-quantile', '0',
      '--opfile', 'stdout',
      full,
    ], { encoding: 'utf8' })
    if (res.status !== 0) {
      console.error(`Match failed for ${f}:`, res.stderr || res.stdout)
      continue
    }
    fs.appendFileSync(OUT, `# ${f}\n${res.stdout}\n`)
  }
  console.log(`Wrote matches to ${OUT}`)
}

main()
