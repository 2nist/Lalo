#!/usr/bin/env python3
"""Simple file-change watcher that runs a command when files change.

Usage example:
  ./miniconda3/envs/lalo311/bin/python scripts/tools/live_watcher.py \
    --files scripts/analysis/section_detector.py \
    --command "./miniconda3/envs/lalo311/bin/python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-b-wave5.json 2>&1 | tee results/sections-machine-b-wave5.log" \
    --poll 3

This script uses simple polling (no external deps) so it runs on CI/macOS/linux.
"""
import argparse
import os
import time
import subprocess
import shlex


def run_command(cmd):
    print(f"[live-watcher] Running command: {cmd}")
    try:
        p = subprocess.Popen(cmd, shell=True)
        p.communicate()
        print(f"[live-watcher] Command exited with {p.returncode}")
    except Exception as e:
        print(f"[live-watcher] Command failed: {e}")


def watch(paths, command, poll):
    mtimes = {}
    for p in paths:
        mtimes[p] = os.path.getmtime(p) if os.path.exists(p) else 0

    print(f"[live-watcher] Monitoring {len(paths)} path(s):")
    for p in paths:
        print(f"  - {p}")

    try:
        while True:
            for p in paths:
                try:
                    m = os.path.getmtime(p)
                except FileNotFoundError:
                    m = 0
                if m != mtimes.get(p, 0):
                    print(f"[live-watcher] Change detected: {p} -> {time.ctime(m)}")
                    mtimes[p] = m
                    run_command(command)
            time.sleep(poll)
    except KeyboardInterrupt:
        print('\n[live-watcher] Exiting (KeyboardInterrupt)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', nargs='+', required=True,
                        help='Paths to watch for changes')
    parser.add_argument('--command', required=True,
                        help='Shell command to run when changes are detected')
    parser.add_argument('--poll', type=float, default=3.0,
                        help='Polling interval in seconds')
    args = parser.parse_args()

    watch(args.files, args.command, args.poll)


if __name__ == '__main__':
    main()
