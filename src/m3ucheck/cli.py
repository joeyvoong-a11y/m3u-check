"""Kommandoradsgränssnitt: m3u-check <fil.m3u>"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checks import run_checks
from .parser import parse


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="m3u-check", description="Hitta fel i IPTV-spellistor (M3U).")
    ap.add_argument("file", type=Path, help="Sökväg till .m3u/.m3u8-fil")
    ap.add_argument("--errors-only", action="store_true", help="Visa bara fel, inte varningar")
    args = ap.parse_args(argv)

    try:
        text = args.file.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"Kunde inte läsa filen: {e}", file=sys.stderr)
        return 2

    result = parse(text)
    issues = run_checks(result)
    if args.errors_only:
        issues = [i for i in issues if i.level == "error"]

    for i in issues:
        print(f"rad {i.line:>4}  {i.level.upper():7}  {i.message}")

    n_err = sum(i.level == "error" for i in issues)
    n_warn = sum(i.level == "warning" for i in issues)
    print(f"\n{len(result.channels)} kanaler, {n_err} fel, {n_warn} varningar")
    return 1 if n_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
