#!/usr/bin/env python3
"""
Broad-strokes chord/section pipeline (audio-optional).

Modes:
  - chords JSON: list of {time: seconds, label: raw_chord}
  - audio path: (stub) not implemented here; intended to be fed by upstream Essentia ACR that outputs chords JSON.

Output JSON:
{
  "key": "G major",
  "bpm": 94,
  "sections": [
    { "label": "A", "start_bar": 1, "end_bar": 16, "progression": ["I","IV","V","IV"], "repeats": 3 },
    ...
  ]
}
"""
from __future__ import annotations
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
try:
    import librosa
except Exception:
    librosa = None

from scripts.analysis.chord_norm import simplify_chord, longest_label

# --- Core analysis functions --- #


def load_chords(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict) and "chords" in data:
        data = data["chords"]
    out = []
    for ev in data:
        t = float(ev.get("time") or ev.get("start") or 0.0)
        label = str(ev.get("label") or ev.get("chord") or "N")
        out.append({"time": t, "label": label})
    return sorted(out, key=lambda x: x["time"])


def estimate_bpm(audio_path: Path) -> float:
    if not librosa:
        return 120.0
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return float(tempo) if tempo else 120.0


def bar_grid(chords, bpm: float, key: str):
    """Quantize chords to bars (4 beats)."""
    spb = 60.0 / bpm
    bar = spb * 4
    if not chords:
        return [], bar
    end_time = max(ev["time"] for ev in chords) + bar
    n_bars = int(np.ceil(end_time / bar))
    bar_labels: List[List] = [[] for _ in range(n_bars)]
    for i, ev in enumerate(chords):
        bar_idx = int(np.floor(ev["time"] / bar))
        # duration to next event or bar end
        nxt = chords[i + 1]["time"] if i + 1 < len(chords) else end_time
        dur = max(0.0, min(nxt, (bar_idx + 1) * bar) - ev["time"])
        rn = simplify_chord(ev["label"], key)
        if bar_idx < n_bars:
            bar_labels[bar_idx].append((rn, dur))
    flat = [longest_label(bl) if bl else "N" for bl in bar_labels]
    return flat, bar


def phrase_fingerprints(bar_seq: List[str], window: int = 4) -> List[str]:
    fps = []
    for i in range(0, len(bar_seq), window):
        chunk = bar_seq[i:i + window]
        if len(chunk) < window:
            break
        fps.append("|".join(chunk))
    return fps


def _dominant_run_length(labels: List[str]) -> int:
    runs = []
    i = 0
    while i < len(labels):
        j = i
        while j < len(labels) and labels[j] == labels[i]:
            j += 1
        runs.append(j - i)
        i = j
    if not runs:
        return 2
    vals, counts = np.unique(runs, return_counts=True)
    return int(vals[np.argmax(counts)])


def _section_name(label_ord: int) -> str:
    lookup = ["Verse", "Chorus", "Bridge", "Break", "Outro"]
    return lookup[label_ord] if label_ord < len(lookup) else f"Section {chr(ord('A') + label_ord)}"


def detect_sections(bar_seq: List[str]) -> List[Dict[str, Any]]:
    phrases = phrase_fingerprints(bar_seq, 4)
    if not phrases:
        return [{"label": "A", "start_bar": 1, "end_bar": len(bar_seq), "progression": bar_seq[:4] or ["N"], "repeats": 1}]
    labels = []
    fp_to_label = {}
    cur_label_ord = 0

    def next_label():
        nonlocal cur_label_ord
        l = chr(ord("A") + cur_label_ord)
        cur_label_ord += 1
        return l

    for fp in phrases:
        if fp not in fp_to_label:
            fp_to_label[fp] = next_label()
        labels.append(fp_to_label[fp])

    # Merge consecutive identical phrase labels, enforce min section based on dominant run
    dominant_run = max(2, _dominant_run_length(labels))
    sections = []
    i = 0
    while i < len(labels):
        j = i
        while j < len(labels) and labels[j] == labels[i]:
            j += 1
        length_phr = j - i
        if length_phr < dominant_run and sections:
            # absorb short blip into previous section
            sections[-1]["phrases"] += length_phr
        else:
            sections.append({"label": labels[i], "phrases": length_phr, "ord": ord(labels[i]) - ord("A")})
        i = j

    # build output with bars
    out = []
    bar_ptr = 0
    for sec in sections:
        start_bar = bar_ptr + 1
        end_bar = bar_ptr + sec["phrases"] * 4
        # pick the most frequent 4-bar phrase in this section
        phrase_slice = phrases[(start_bar - 1) // 4: end_bar // 4]
        if phrase_slice:
            vals, counts = np.unique(phrase_slice, return_counts=True)
            top_phrase = vals[np.argmax(counts)].split("|")
        else:
            top_phrase = bar_seq[start_bar - 1:start_bar - 1 + 4] or ["N"]
        out.append({
            "label": sec["label"],
            "name": _section_name(sec["ord"]),
            "start_bar": start_bar,
            "end_bar": end_bar,
            "progression": top_phrase,
            "repeats": max(1, sec["phrases"] // dominant_run),
        })
        bar_ptr = end_bar
    return out


def analyze(chords: List[Dict[str, Any]], key: str, bpm: float) -> Dict[str, Any]:
    bar_seq, bar_dur = bar_grid(chords, bpm, key)
    sections = detect_sections(bar_seq)
    return {
        "key": key,
        "bpm": round(bpm, 2),
        "bar_duration_s": round(bar_dur, 3),
        "sections": sections,
    }


def main():
    ap = argparse.ArgumentParser(description="Broad-strokes chord sectioning")
    ap.add_argument("--chords-json", type=Path, help="Path to chords JSON (list of {time,label})")
    ap.add_argument("--audio", type=Path, help="Audio path (optional, for BPM only)")
    ap.add_argument("--key", type=str, default="C major", help="Key e.g., 'G major' or 'A minor'")
    ap.add_argument("--bpm", type=float, help="Override BPM; else estimated or 120")
    ap.add_argument("--out", type=Path, default=Path("data/output/broad_sections.json"))
    args = ap.parse_args()

    if not args.chords_json and not args.audio:
        ap.error("Provide --chords-json or --audio")

    chords = load_chords(args.chords_json) if args.chords_json else []
    bpm = args.bpm or (estimate_bpm(args.audio) if args.audio else 120.0)
    result = analyze(chords, args.key, bpm)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
