#!/usr/bin/env python3
"""
Rejects staged text files that contain UTF-8 BOM.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


UTF8_BOM = b"\xef\xbb\xbf"
TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".vue",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".css",
    ".scss",
    ".html",
    ".sh",
}


def staged_files() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [
        "git",
        "-c",
        "safe.directory=*",
        "-C",
        str(repo_root),
        "diff",
        "--cached",
        "--name-only",
        "--diff-filter=ACMR",
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    files = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        files.append(repo_root / line.strip())
    return files


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def has_utf8_bom(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            head = f.read(3)
        return head == UTF8_BOM
    except OSError:
        return False


def main() -> int:
    bad_files: list[str] = []
    for path in staged_files():
        if not is_text_file(path):
            continue
        if has_utf8_bom(path):
            bad_files.append(str(path))

    if bad_files:
        print("ERROR: Found files with UTF-8 BOM. Commit rejected.", file=sys.stderr)
        for file_name in bad_files:
            print(f" - {file_name}", file=sys.stderr)
        print(
            "Please convert them to UTF-8 without BOM and commit again.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
