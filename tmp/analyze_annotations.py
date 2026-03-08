#!/usr/bin/env python3
"""Analyze Harmonix annotation corpus statistics for Machine C diagnostics."""
from pathlib import Path
from statistics import mean, median, stdev
from collections import Counter

harmonix = Path("data/raw/harmonix")
sections_files = sorted(harmonix.glob("*_sections.txt"))

all_durations = []
all_labels = []
song_section_counts = []

for f in sections_files:
    rows = []
    with open(f) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    rows.append((float(parts[0]), parts[1]))
                except ValueError:
                    pass

    sections = []
    for i, (start, label) in enumerate(rows):
        end = rows[i + 1][0] if i + 1 < len(rows) else None
        if end and end > start:
            sections.append((end - start, label.lower()))

    for dur, lbl in sections:
        all_durations.append(dur)
        all_labels.append(lbl)
    song_section_counts.append(len(sections))

print(f"Songs: {len(sections_files)}")
print(f"Total sections: {len(all_durations)}")
print(f"Sections/song: mean={mean(song_section_counts):.1f}  min={min(song_section_counts)}  max={max(song_section_counts)}")
print(f"Section duration (s): mean={mean(all_durations):.1f}  median={median(all_durations):.1f}  min={min(all_durations):.1f}  max={max(all_durations):.1f}  stdev={stdev(all_durations):.1f}")
print()

# What fraction of sections are within detector's MIN/MAX bounds?
MIN_S, MAX_S = 8.0, 90.0
in_range = [d for d in all_durations if MIN_S <= d <= MAX_S]
too_short = [d for d in all_durations if d < MIN_S]
too_long = [d for d in all_durations if d > MAX_S]
print(f"Section length vs detector bounds (MIN={MIN_S}s MAX={MAX_S}s):")
print(f"  In range:  {len(in_range):3d}  ({100*len(in_range)/len(all_durations):.0f}%)")
print(f"  Too short: {len(too_short):3d}  ({100*len(too_short)/len(all_durations):.0f}%)")
print(f"  Too long:  {len(too_long):3d}  ({100*len(too_long)/len(all_durations):.0f}%)")
print()

# NMS distance impact: how many true boundaries are within NMS_DISTANCE of each other?
NMS_S = 16.0
nms_lost = 0
total_pairs = 0
for f in sections_files:
    rows = []
    with open(f) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    rows.append(float(parts[0]))
                except ValueError:
                    pass
    boundaries = sorted(rows[1:])  # skip first (song start)
    for i in range(len(boundaries) - 1):
        gap = boundaries[i + 1] - boundaries[i]
        total_pairs += 1
        if gap < NMS_S:
            nms_lost += 1

print(f"True boundary gaps vs NMS_DISTANCE={NMS_S}s:")
print(f"  Boundary pairs closer than NMS: {nms_lost}/{total_pairs}  ({100*nms_lost/total_pairs:.0f}%)")
print(f"  => These adjacent boundaries CANNOT both survive NMS suppression")
print()

# Label distribution
label_counts = Counter(all_labels)
print("Top 15 labels (ground truth):")
for lbl, cnt in label_counts.most_common(15):
    print(f"  {lbl:20s} {cnt:4d}  ({100*cnt/len(all_labels):.1f}%)")

# What does the detector emit for labels?
print()
print("Detector label mapping note:")
print("  Detector emits: 'Section 1', 'Section 2', ... (generic)")
print("  Ground truth uses: verse/chorus/intro/bridge/etc.")
print("  => label_accuracy=0.0 is structurally guaranteed with current output format")
