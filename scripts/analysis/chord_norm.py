#!/usr/bin/env python3
"""
Chord normalization helpers for broad-strokes sectioning.

- Roman numeral mapping relative to key
- Enharmonic collapse
- Extension stripping (keeps triad quality only)
"""
from __future__ import annotations
from typing import Tuple

NOTE_TO_SEMITONE = {
    "c": 0, "b#": 0,
    "c#": 1, "db": 1,
    "d": 2,
    "d#": 3, "eb": 3,
    "e": 4, "fb": 4,
    "e#": 5, "f": 5,
    "f#": 6, "gb": 6,
    "g": 7,
    "g#": 8, "ab": 8,
    "a": 9,
    "a#": 10, "bb": 10,
    "b": 11, "cb": 11,
}

DEGREE_TO_ROMAN = ["I", "bII", "II", "bIII", "III", "IV", "#IV", "V", "bVI", "VI", "bVII", "VII"]


def parse_chord(label: str) -> Tuple[str, str]:
    """Split chord into (root, quality). Very naive but good enough for triads."""
    s = label.strip().lower().replace("maj", "m").replace("min", "m")
    root = ""
    if len(s) >= 2 and s[1] in ["b", "#"]:
        root, rest = s[:2], s[2:]
    else:
        root, rest = s[:1], s[1:]
    quality = "m" if rest.startswith("m") else "M"
    return root, quality


def romanize(label: str, key_root: str, key_mode: str) -> str:
    root, qual = parse_chord(label)
    if root not in NOTE_TO_SEMITONE or key_root not in NOTE_TO_SEMITONE:
        return "N"
    key_offset = NOTE_TO_SEMITONE[root] - NOTE_TO_SEMITONE[key_root]
    deg = key_offset % 12
    roman = DEGREE_TO_ROMAN[deg]
    # mode flip: treat minor keys as Aeolian center
    if key_mode.lower().startswith("m"):
        # shift reference so that i=0 maps to key tonic
        roman_map_minor = ["I", "bII", "II", "III", "IV", "V", "bVI", "VI", "bVII", "VII", "iX", "x"]
        roman = roman_map_minor[deg] if deg < len(roman_map_minor) else roman
    if qual == "m":
        # lower-case minor degrees; keep b/#
        if roman.startswith("b") or roman.startswith("#"):
            acc, core = roman[0], roman[1:]
            roman = acc + core.lower()
        else:
            roman = roman.lower()
    return roman


def simplify_chord(label: str, key: str) -> str:
    """Return broad-strokes Roman numeral, dropping extensions/alterations."""
    parts = key.strip().split()
    if not parts:
        return "N"
    key_root = parts[0].lower()
    key_mode = parts[1] if len(parts) > 1 else "major"
    return romanize(label, key_root, key_mode)


def longest_label(labels):
    """Return the label with maximum duration; expects list of (label, dur)."""
    if not labels:
        return "N"
    labels = sorted(labels, key=lambda x: x[1], reverse=True)
    return labels[0][0]


__all__ = ["simplify_chord", "longest_label"]
