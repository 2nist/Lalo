#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import { execSync } from 'child_process'

const DEFAULT_REPO = 'https://github.com/DDMAL/salami-data-public.git'
const DEFAULT_DEST = 'data/raw/salami-data-public'

function parseArgs(argv) {
  const args = { repo: DEFAULT_REPO, dest: DEFAULT_DEST }
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i]
    if (a === '--repo') args.repo = argv[i + 1] ?? DEFAULT_REPO
    if (a === '--dest') args.dest = argv[i + 1] ?? DEFAULT_DEST
  }
  return args
}

function run(cmd, cwd = process.cwd()) {
  execSync(cmd, { cwd, stdio: 'inherit' })
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  const dest = path.resolve(args.dest)
  const parent = path.dirname(dest)
  fs.mkdirSync(parent, { recursive: true })

  const gitDir = path.join(dest, '.git')
  if (fs.existsSync(gitDir)) {
    console.log(`Updating existing SALAMI repo at ${dest}`)
    run('git fetch --all --tags --prune', dest)
    run('git pull --ff-only', dest)
    return
  }

  if (fs.existsSync(dest) && fs.readdirSync(dest).length > 0) {
    throw new Error(`Destination exists and is not a git repo: ${dest}`)
  }

  console.log(`Cloning SALAMI dataset to ${dest}`)
  run(`git clone --depth 1 ${args.repo} ${dest}`)
}

try {
  main()
} catch (err) {
  console.error(`fetchSalami error: ${err instanceof Error ? err.message : String(err)}`)
  process.exit(1)
}

