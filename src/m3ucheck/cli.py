"""Kommandoradsgränssnitt: m3u-check <fil.m3u>"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .checks import run_checks
from .fix import fix_playlist
from .parser import parse
from .report import Report, render_html, render_json, render_text

EXIT_OK = 0  # inga fel (varningar räknas inte), eller --fix klar
EXIT_ERRORS = 1  # minst ett fel i spellistan
EXIT_IO = 2  # filen kunde inte läsas eller skrivas, eller ogiltiga flaggor

# Spellistor som inte är UTF-8 är nästan alltid sparade i Windows-1252 (Latin-1
# med t.ex. € och ”). cp1252 kan avkoda nästan alla byte, så det är en säker reserv.
FALLBACK_ENCODING = "cp1252"


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


def _describe_os_error(e: OSError) -> str:
    """Ett begripligt svenskt skäl i stället för t.ex. "[Errno 2] No such file or directory"."""
    if isinstance(e, FileNotFoundError):
        return "filen eller mappen finns inte"
    if isinstance(e, IsADirectoryError):
        return "det är en mapp, inte en fil"
    if isinstance(e, PermissionError):
        # Windows ger PermissionError även när man pekar på en mapp.
        return "åtkomst nekad (är det en mapp, eller saknas behörighet?)"
    return e.strerror or str(e)


def _read_playlist(path: Path) -> str:
    """Läs filen som UTF-8 (med eller utan BOM), annars som Windows-1252 med en varning."""
    data = path.read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        print(
            f"Varning: {path.name} är inte UTF-8 (ogiltig byte på position {e.start}). "
            f"Läser den som {FALLBACK_ENCODING}. Kontrollera att åäö blev rätt.",
            file=sys.stderr,
        )
        return data.decode(FALLBACK_ENCODING, errors="replace")


def _same_file(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return False


def _print_stdout(text: str) -> None:
    try:
        print(text, end="")
        sys.stdout.flush()
    except (BrokenPipeError, OSError):
        # Läsaren stängde pipen (t.ex. `| head`). Inget fel för oss; skicka resten
        # till devnull så att Python inte klagar när den stänger stdout.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="m3u-check",
        description="Hitta fel i IPTV-spellistor (M3U).",
        epilog="Exit-kod: 0 inga fel, 1 fel hittades, 2 filen kunde inte läsas eller skrivas.",
    )
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
    return ap


def main(argv: list[str] | None = None) -> int:
    _use_utf8_output()
    ap = _parser()
    args = ap.parse_args(argv)
    if args.fix and (args.errors_only or args.format != "text"):
        ap.error("--fix skriver en spellista och kan inte kombineras med --errors-only eller --format")
    if args.output is not None and not args.fix and _same_file(args.output, args.file):
        print(
            f"Vägrar skriva rapporten över spellistan {args.file}. Välj ett annat namn med -o.",
            file=sys.stderr,
        )
        return EXIT_IO

    try:
        text = _read_playlist(args.file)
    except OSError as e:
        print(f"Kunde inte läsa filen {args.file}: {_describe_os_error(e)}", file=sys.stderr)
        return EXIT_IO

    result = parse(text)
    if args.fix:
        fixed = fix_playlist(result)
        output, code = fixed.text, EXIT_OK
        message = (
            f"{fixed.kept} kanaler kvar, {fixed.removed_duplicates} dubbletter "
            f"och {fixed.removed_invalid} ogiltiga URL:er borttagna"
        )
    else:
        report = Report(len(result.channels), run_checks(result))
        if args.errors_only:
            report = report.errors_only()
        output = _render(report, args.format, args.file.name)
        code = EXIT_ERRORS if report.errors else EXIT_OK
        message = None

    if args.output is None:
        _print_stdout(output)
    else:
        try:
            args.output.write_text(output, encoding="utf-8")
        except OSError as e:
            print(f"Kunde inte skriva filen {args.output}: {_describe_os_error(e)}", file=sys.stderr)
            return EXIT_IO
        message = message or f"Rapporten skrevs till {args.output}"
    if message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
