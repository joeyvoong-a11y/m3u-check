"""Kommandoradsgränssnitt: m3u-check <fil.m3u>"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checks import run_checks
from .parser import parse
from .report import Report, render_text


def _use_utf8_output() -> None:
    # Vid pipe på Windows (och i exe-filen) blir stdout/stderr annars cp1252 och
    # åäö går sönder. PYTHONUTF8 hjälper inte exe-filen, så det görs i koden.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):  # capsys och liknande saknar den
            stream.reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    _use_utf8_output()
    ap = argparse.ArgumentParser(prog="m3u-check", description="Hitta fel i IPTV-spellistor (M3U).")
    ap.add_argument("file", type=Path, help="Sökväg till .m3u/.m3u8-fil")
    ap.add_argument("--errors-only", action="store_true", help="Visa bara fel, inte varningar")
    args = ap.parse_args(argv)

    try:
        # utf-8-sig tar bort en ev. BOM. errors="replace" så att en enstaka
        # felkodad rad inte stoppar kontrollen av resten av filen.
        text = args.file.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as e:
        print(f"Kunde inte läsa filen: {e}", file=sys.stderr)
        return 2

    result = parse(text)
    report = Report(len(result.channels), run_checks(result))
    if args.errors_only:
        report = report.errors_only()

    print(render_text(report), end="")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
