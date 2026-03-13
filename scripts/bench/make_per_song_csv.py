import json
import csv
from pathlib import Path

IN = Path("results/sections-machine-b.madmom.json")
OUT = Path("results/sections-machine-b.madmom.csv")

if not IN.exists():
    raise SystemExit(f"Missing input JSON: {IN}")

J = json.loads(IN.read_text())

rows = []
for r in J.get("per_song", []):
    det = r.get("detector", {}) or {}
    fixed = r.get("fixed_chunks", {}) or {}
    def f1(d, k):
        v = d.get(k, {})
        return v.get("f1") if isinstance(v, dict) else None

    rows.append({
        "id": r.get("id"),
        "audio": r.get("audio"),
        "det_f1_0.5": f1(det, "0.5"),
        "fixed_f1_0.5": f1(fixed, "0.5"),
        "det_f1_3.0": f1(det, "3.0"),
        "fixed_f1_3.0": f1(fixed, "3.0"),
        "det_algorithm": det.get("algorithm"),
        "det_candidates_recorded": det.get("candidates_recorded"),
        # pred_sections may be a list or an integer count depending on runner output
        "det_sections_count": (len(det.get("pred_sections")) if isinstance(det.get("pred_sections"), (list, tuple)) else (det.get("pred_sections") if isinstance(det.get("pred_sections"), int) else None)),
    })

if not rows:
    print("No per-song entries found in JSON; writing empty CSV header")

with OUT.open("w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "id",
        "audio",
        "det_f1_0.5",
        "fixed_f1_0.5",
        "det_f1_3.0",
        "fixed_f1_3.0",
        "det_algorithm",
        "det_candidates_recorded",
        "det_sections_count",
    ]
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for row in rows:
        w.writerow(row)

print(f"Wrote {OUT}")
