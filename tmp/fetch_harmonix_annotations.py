#!/usr/bin/env python3
"""Fetch Harmonix section + beat annotation files from nicolaus625/cmi on HuggingFace.

Targets only the Harmonix subdirectory to avoid rate-limiting from full tree scan.
For --dev-only benchmark we only need ~30 songs.

Usage: python tmp/fetch_harmonix_annotations.py [--max 35]
Output: data/raw/harmonix/<id>_sections.txt  and  <id>_beats.txt
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download
from huggingface_hub.hf_api import HfApi

REPO_ID = "nicolaus625/cmi"
REPO_TYPE = "dataset"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "harmonix"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEGS_PREFIX = "Harmonix/harmonixset/dataset/segments"
BEATS_PREFIX = "Harmonix/harmonixset/dataset/beats_and_downbeats"
ID_RE = re.compile(r"^(\d{4})_")


def list_hf_dir(prefix: str) -> list:
    api = HfApi()
    items = list(api.list_repo_tree(
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        path_in_repo=prefix,
        expand=False,
    ))
    return [item.path for item in items if hasattr(item, "path")]


def fetch_file(repo_path: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return False
    try:
        local = hf_hub_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            filename=repo_path,
        )
        shutil.copy2(local, dest)
        return True
    except Exception as exc:
        print(f"  [warn] {repo_path}: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=35)
    args = parser.parse_args()

    print(f"Listing segments from {SEGS_PREFIX} ...")
    seg_files = [f for f in list_hf_dir(SEGS_PREFIX) if f.endswith(".txt")]
    print(f"  {len(seg_files)} segment files")

    print(f"Listing beats from {BEATS_PREFIX} ...")
    beat_files = [f for f in list_hf_dir(BEATS_PREFIX) if f.endswith(".txt")]
    print(f"  {len(beat_files)} beat files")

    beats_by_id = {}
    for path in beat_files:
        fn = Path(path).name
        m = ID_RE.match(fn)
        if m:
            beats_by_id[m.group(1)] = path

    downloaded = skipped = 0
    for repo_path in sorted(seg_files)[: args.max]:
        fn = Path(repo_path).name
        m = ID_RE.match(fn)
        if not m:
            continue
        song_id = m.group(1)

        sec_dest = OUT_DIR / f"{song_id}_sections.txt"
        if fetch_file(repo_path, sec_dest):
            downloaded += 1
            print(f"  + {sec_dest.name}")
        else:
            skipped += 1

        if song_id in beats_by_id:
            beat_dest = OUT_DIR / f"{song_id}_beats.txt"
            fetch_file(beats_by_id[song_id], beat_dest)

    print(f"\nDone. {downloaded} fetched, {skipped} already present")
    files = sorted(OUT_DIR.iterdir())
    print(f"Files in {OUT_DIR}: {len(files)}")
    for f in files[:12]:
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
