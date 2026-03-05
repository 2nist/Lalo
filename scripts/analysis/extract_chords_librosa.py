#!/usr/bin/env python3
"""
Lightweight chord extractor using librosa chroma + template matching (24 chords: 12 major, 12 minor).
Output: JSON with {"chords": [{ "time": seconds, "label": "C:maj" }, ...]}

Usage:
  python scripts/analysis/extract_chords_librosa.py --audio path/to/file.mp3 --out data/output/chords.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import List, Dict

import numpy as np
import librosa


ROOTS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def build_templates():
    maj = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0], dtype=float)
    min_ = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0], dtype=float)
    temps = []
    labels = []
    for i, r in enumerate(ROOTS):
        temps.append(np.roll(maj, i))
        labels.append(f"{r}:maj")
    for i, r in enumerate(ROOTS):
        temps.append(np.roll(min_, i))
        labels.append(f"{r}:min")
    temps = np.stack(temps)
    temps = temps / np.linalg.norm(temps, axis=1, keepdims=True)
    return temps, labels


TEMPLATES, TEMPLATE_LABELS = build_templates()


def extract(audio_path: Path, hop_s: float = 0.5) -> List[Dict[str, float]]:
    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    hop = int(sr * hop_s)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    chroma = chroma / np.maximum(1e-6, np.linalg.norm(chroma, axis=0, keepdims=True))
    sims = TEMPLATES @ chroma  # [24, frames]
    best_idx = sims.argmax(axis=0)
    best_lab = [TEMPLATE_LABELS[i] for i in best_idx]
    times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop)
    # collapse consecutive same labels
    events = []
    last_lab = None
    last_t = None
    for t, lab in zip(times, best_lab):
        if lab != last_lab:
            events.append({"time": float(t), "label": lab})
            last_lab = lab
            last_t = t
    return events


def main():
    ap = argparse.ArgumentParser(description="Librosa template chord extractor")
    ap.add_argument("--audio", type=Path, required=True, help="Audio file (wav/mp3/m4a)")
    ap.add_argument("--out", type=Path, default=Path("data/output/chords_librosa.json"))
    ap.add_argument("--hop", type=float, default=0.5, help="Hop size in seconds (default 0.5s)")
    args = ap.parse_args()

    evts = extract(args.audio, hop_s=args.hop)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"chords": evts}, indent=2))
    print(f"Wrote {args.out} with {len(evts)} chord changes")


if __name__ == "__main__":
    main()
