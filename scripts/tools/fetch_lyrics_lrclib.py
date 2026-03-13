#!/usr/bin/env python3
"""Fetch synchronized lyrics from LRClib for SALAMI / Harmonix song lists.

Saves per-song JSONs with intervals: [{start:, end:, text:}, ...]

Usage:
  python scripts/tools/fetch_lyrics_lrclib.py --salami 20 --out-dir data/lyrics
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))


def _load_lrclib_class():
    # Load LRCLibService from third_party path by file location
    mod_path = ROOT / "third_party" / "ChordMiniApp" / "python_backend" / "services" / "lyrics" / "lrclib_service.py"
    spec = importlib.util.spec_from_file_location("lrclib_service", str(mod_path))
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load LRClib service from {mod_path}")
    module = importlib.util.module_from_spec(spec)
    # Ensure the ChordMini python_backend root is on sys.path so imports like
    # `from utils.logging import ...` inside lrclib_service resolve properly.
    backend_root = str(mod_path.parents[2])
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    try:
        spec.loader.exec_module(module)  # type: ignore
    finally:
        # leave backend_root on sys.path (harmless) — avoids repeated inserts
        pass
    return module.LRCLibService


def _parse_annotation_for_meta(ann_path: Path) -> Dict[str, Optional[str]]:
    try:
        data = json.loads(ann_path.read_text(encoding="utf-8"))
        title = data.get("title") or data.get("song") or None
        artist = data.get("artist") or data.get("performer") or None
        return {"title": title, "artist": artist}
    except Exception:
        return {"title": None, "artist": None}


def _to_intervals(parsed: List[Dict]) -> List[Dict]:
    # parsed: [{"time": seconds, "text": ...}, ...]
    out: List[Dict] = []
    for i, p in enumerate(parsed):
        start = float(p.get("time", 0.0))
        if i + 1 < len(parsed):
            end = float(parsed[i + 1].get("time", start + 2.0))
        else:
            end = start + 2.0
        out.append({"start": round(start, 3), "end": round(end, 3), "text": p.get("text", "")})
    return out


def fetch_for_salami(max_songs: int, out_dir: Path):
    from scripts.bench.salami_benchmark import _load_salami_pairs

    pairs = _load_salami_pairs(ROOT / "datasets" / "mcgill" / "mcgill_jcrd_salami_Billboard", ROOT / "data" / "salami_audio", max_songs=max_songs)
    if not pairs:
        print("No SALAMI pairs found; check datasets and data/salami_audio")
        return

    LRCLibService = _load_lrclib_class()
    svc = LRCLibService()
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in pairs:
        sid = p["id"]
        ann = Path(p["annotation"]).resolve()
        meta = _parse_annotation_for_meta(ann)
        title = meta.get("title")
        artist = meta.get("artist")
        query = None
        if title and artist:
            print(f"Fetching lyrics for SALAMI {sid}: '{title}' by '{artist}'")
            res = svc.fetch_lyrics(artist=artist, title=title)
        else:
            # fallback to generic query using filename
            query = f"{sid}"
            print(f"Fetching lyrics for SALAMI {sid} with query '{query}'")
            res = svc.fetch_lyrics(search_query=query)

        out_json = out_dir / f"{sid}.lyrics.json"
        if not res.get("success"):
            print(f"  failed: {res.get('error')}")
            out_json.write_text(json.dumps({"success": False, "error": res.get("error"), "meta": {"title": title, "artist": artist}}, indent=2), encoding="utf-8")
            continue

        parsed = res.get("synchronized_lyrics") or []
        if parsed:
            intervals = _to_intervals(parsed)
        else:
            intervals = []

        out_obj = {
            "success": True,
            "has_synchronized": res.get("has_synchronized", False),
            "intervals": intervals,
            "plain_lyrics": res.get("plain_lyrics"),
            "metadata": res.get("metadata", {}),
            "source": res.get("source", "lrclib.net")
        }
        out_json.write_text(json.dumps(out_obj, indent=2), encoding="utf-8")
        print(f"  wrote {out_json}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salami", type=int, default=0, help="Number of SALAMI songs to fetch (0=skip)")
    ap.add_argument("--harmonix", type=int, default=0, help="Number of Harmonix dev songs to fetch (0=skip)")
    ap.add_argument("--out-dir", default="data/lyrics", help="Output directory for per-song lyric JSONs")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)

    if args.salami and args.salami > 0:
        fetch_for_salami(args.salami, out_dir)
    else:
        print("No SALAMI fetch requested. Use --salami N")


if __name__ == "__main__":
    main()
