"""
Small regression guard helper to compare SALAMI baseline F1 and new F1.
If regression exceeds threshold it returns exit code 2; else 0.

Usage examples:
  python scripts/tools/regression_guard.py --gain-log results/gain-plan-log.json --new-f1 0.301 --threshold 0.005
  python scripts/tools/regression_guard.py --gain-log results/gain-plan-log.json --new-results results/salami-baseline-heuristic.json

The script supports extracting `salami_baseline.f1_3` from gain-log and comparing
against a numeric value or a simple JSON result file that contains `salami_f1_3`.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def load_gain_log(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_new_results(path: Path) -> float | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    # accept both top-level numeric or nested keys
    for key in ("salami_f1_3", "f1_3", "salami_f1"):
        if key in data:
            return float(data[key])
    # look for nested salami_baseline
    if "salami_baseline" in data and isinstance(data["salami_baseline"], dict):
        if "f1_3" in data["salami_baseline"]:
            return float(data["salami_baseline"]["f1_3"])
    return None


def compare(baseline: float, new: float, threshold: float) -> bool:
    """Return True if new >= baseline - threshold (i.e., no harmful regression)."""
    return new >= (baseline - threshold)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="regression_guard.py")
    parser.add_argument("--gain-log", type=Path, required=True, help="Path to results/gain-plan-log.json")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--new-f1", type=float, help="New SALAMI F1@3.0s value (numeric)")
    group.add_argument("--new-results", type=Path, help="Path to JSON results file containing salami_f1_3 or f1_3")
    parser.add_argument("--threshold", type=float, default=0.005, help="Allowed drop before revert (default=0.005)")

    args = parser.parse_args(argv)

    gain = load_gain_log(args.gain_log)
    baseline = None
    if "salami_baseline" in gain and isinstance(gain["salami_baseline"], dict) and "f1_3" in gain["salami_baseline"]:
        baseline = float(gain["salami_baseline"]["f1_3"])
    else:
        print("ERROR: salami_baseline.f1_3 not found in gain-log", file=sys.stderr)
        return 3

    if args.new_f1 is not None:
        new = args.new_f1
    else:
        new = read_new_results(args.new_results)
        if new is None:
            print("ERROR: could not parse new f1 from new-results file", file=sys.stderr)
            return 4

    ok = compare(baseline, float(new), float(args.threshold))

    print(json.dumps({
        "baseline_f1_3": baseline,
        "new_f1_3": float(new),
        "threshold": float(args.threshold),
        "ok": ok,
    }, indent=2))

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
