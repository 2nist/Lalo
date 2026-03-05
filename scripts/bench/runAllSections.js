#!/usr/bin/env node
/**
 * Convenience runner to execute the full section benchmark chain:
 * 1) Build SALAMI references and McGill->SALAMI map
 * 2) Build benchmark list (exact+fuzzy) to data/truth/benchmark_fuzzy.json
 * 3) Run section benchmark (scripts/bench/runBenchmark.js)
 *
 * Usage:
 *   node scripts/bench/runAllSections.js
 *
 * Optional env:
 *   BENCH_LIST=path/to/list.json   (defaults to data/truth/benchmark_fuzzy.json)
 */
import { spawnSync } from 'child_process'
import path from 'path'

const steps = [
  { cmd: 'node', args: ['scripts/datasets/buildSalamiReferences.js'], label: 'buildSalamiReferences' },
  { cmd: 'node', args: ['scripts/bench/makeBenchmarkList.js'], label: 'makeBenchmarkList' },
  { cmd: 'node', args: ['scripts/bench/runBenchmark.js'], label: 'runBenchmark' },
]

function runStep(step) {
  console.log(`\n=== ${step.label} ===`)
  const res = spawnSync(step.cmd, step.args, {
    stdio: 'inherit',
    env: { ...process.env, BENCH_LIST: process.env.BENCH_LIST || path.resolve('data/truth/benchmark_fuzzy.json') },
  })
  if (res.status !== 0) {
    console.error(`Step ${step.label} failed with code ${res.status}`)
    process.exit(res.status || 1)
  }
}

for (const s of steps) runStep(s)
console.log('\nAll section benchmarks completed.')
