#!/usr/bin/env node
/**
 * Compute beats for downloaded pairing audio (data/audio/salami_<id>.*) into data/beats/.
 */
import fs from 'fs'
import path from 'path'
import { spawnSync } from 'child_process'

const AUDIO_DIR = path.resolve('data/audio')
function main() {
  if (!fs.existsSync(AUDIO_DIR)) {
    console.error('No data/audio directory found. Fetch audio first.')
    process.exit(1)
  }
  // create a manifest of slugs
  const files = fs.readdirSync(AUDIO_DIR).filter(f => f.match(/^salami_\d+\.(m4a|mp3|flac|ogg|wav)$/i))
  const manifest = {
    base_path: 'datasets/mcgill/mcgill_jcrd_salami_Billboard', // unused here
    files: files.map(f => path.parse(f).name + '.json'), // dummy
  }
  const tmpList = path.resolve('data/truth/tmp_audio_list.json')
  fs.writeFileSync(tmpList, JSON.stringify(manifest, null, 2))
  const res = spawnSync('python', ['scripts/experiments/compute_beats.py', '--audio-root', 'data/audio', '--list', tmpList, '--out-dir', 'data/beats'], { stdio: 'inherit' })
  fs.unlinkSync(tmpList)
  if (res.status !== 0) process.exit(res.status)
}

main()
