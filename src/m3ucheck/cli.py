"""Kommandoradsgränssnitt: m3u-check <fil.m3u>"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .checks import run_checks
from .fix import fix_playlist
from .parser import parse
from .report import Report, render_html, render_json, render_text


def _use_utf8_output() -> None:
    # Vid pipe på Windows (och i exe-filen) blir stdout/stderr annars cp1252 och
    # åäö går sönder. PYTHONUTF8 hjälper inte exe-filen, så det görs i koden.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):  # capsys och liknande saknar den
            stream.reconfigure(encoding="utf-8")


def _render(report: Report, fmt: str, title: str) -> str:
    if fmt == "json":
        return render_json(report)
    if fmt == "html":
        return render_html(report, title)
    return render_text(report)


def main(argv: list[str] | None = None) -> int:
    _use_utf8_output()
    ap = argparse.ArgumentParser(prog="m3u-check", description="Hitta fel i IPTV-spellistor (M3U).")
    ap.add_argument("file", type=Path, help="Sökväg till .m3u/.m3u8-fil")
    ap.add_argument("--errors-only", action="store_true", help="Visa bara fel, inte varningar")
    ap.add_argument(
        "--format", choices=["text", "json", "html"], default="text", help="Rapportens format (standard: text)"
    )
    ap.add_argument(
        "--fix",
        action="store_true",
        help="Skriv ut en städad spellista (utan dubbletter och ogiltiga URL:er, sorterad per grupp)",
    )
    ap.add_argument("-o", "--output", type=Path, help="Skriv till fil i stället för till skärmen")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    try:
        # utf-8-sig tar bort en ev. BOM. errors="replace" så att en enstaka
        # felkodad rad inte stoppar kontrollen av resten av filen.
        text = args.file.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as e:
        print(f"Kunde inte läsa filen: {e}", file=sys.stderr)
        return 2

    result = parse(text)
    if args.fix:
        fixed = fix_playlist(result)
        output, code = fixed.text, 0
        message = (
            f"{fixed.kept} kanaler kvar, {fixed.removed_duplicates} dubbletter "
            f"och {fixed.removed_invalid} ogiltiga URL:er borttagna"
        )
    else:
        report = Report(len(result.channels), run_checks(result))
        if args.errors_only:
            report = report.errors_only()
        output, code = _render(report, args.format, args.file.name), 1 if report.errors else 0
        message = None

    if args.output is None:
        print(output, end="")
    else:
        try:
            args.output.write_text(output, encoding="utf-8")
        except OSError as e:
            print(f"Kunde inte skriva filen: {e}", file=sys.stderr)
            return 2
        message = message or f"Rapporten skrevs till {args.output}"
    if message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
