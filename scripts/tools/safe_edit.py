"""
Simple safe-edit utility: backup specified files/directories before automated edits
and provide restore functionality. Writes a persistent `results/edit_log.json` entry
for every backup.

Usage:
  python scripts/tools/safe_edit.py --backup path/to/file1 path/to/dir2
  python scripts/tools/safe_edit.py --restore backups/docs_backup/20260309T123456Z
  python scripts/tools/safe_edit.py --list

This is intentionally small and dependency-free.
"""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

RESULTS_DIR = Path("results")
LOG_PATH = RESULTS_DIR / "edit_log.json"
DEFAULT_BACKUP_ROOT = Path("backups/docs_backup")


def _ensure_dirs():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_BACKUP_ROOT.mkdir(parents=True, exist_ok=True)


def _append_log(entry: dict):
    _ensure_dirs()
    if LOG_PATH.exists():
        try:
            data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = []
    else:
        data = []
    data.append(entry)
    LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def backup_paths(paths: list[str], backup_root: Path | None = None) -> Path:
    _ensure_dirs()
    if backup_root is None:
        backup_root = DEFAULT_BACKUP_ROOT
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest_root = backup_root / ts
    dest_root.mkdir(parents=True, exist_ok=True)

    copied = []
    cwd = Path.cwd()
    for p in paths:
        src = Path(p)
        if not src.exists():
            print(f"WARNING: path not found, skipping: {src}")
            continue
        # mirror path under dest_root
        try:
            rel = src.relative_to(cwd)
        except Exception:
            rel = src.name
        dst = dest_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        copied.append(str(src))

    entry = {
        "timestamp": ts,
        "backup_dir": str(dest_root),
        "paths": copied,
    }
    _append_log(entry)
    print(json.dumps(entry, indent=2))
    return dest_root


def restore_backup(backup_dir: str) -> None:
    b = Path(backup_dir)
    if not b.exists():
        raise FileNotFoundError(f"backup not found: {b}")
    cwd = Path.cwd()
    for p in sorted(b.rglob("*")):
        if p.is_dir():
            continue
        # compute original relative path stored under backup root
        try:
            rel = p.relative_to(b)
        except Exception:
            rel = p.name
        dst = cwd / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        print(f"restored: {dst}")
    print(f"restore completed from {b}")


def list_backups():
    if not DEFAULT_BACKUP_ROOT.exists():
        print("No backups found")
        return
    for d in sorted(DEFAULT_BACKUP_ROOT.iterdir()):
        if d.is_dir():
            print(d.name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="safe_edit.py")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--backup", nargs="+", help="Paths to backup")
    g.add_argument("--restore", help="Backup dir to restore from")
    g.add_argument("--list", action="store_true", help="List backups")

    args = parser.parse_args(argv)

    try:
        if args.backup:
            backup_paths(args.backup)
            return 0
        if args.restore:
            restore_backup(args.restore)
            return 0
        if args.list:
            list_backups()
            return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
