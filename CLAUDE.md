# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`m3u-check` is a small, dependency-free Python (>=3.10) CLI that parses IPTV playlists (M3U/M3U8) and reports errors and warnings. It is a 6-week course project, and the weekly roadmap is in README.md ("Plan"). User-facing messages, docstrings, comments and the README are in **Swedish**, so keep new ones in Swedish.

## Commands

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"

.venv\Scripts\python -m m3ucheck.cli examples/sample.m3u    # run the CLI
.venv\Scripts\python -m pytest                              # all tests (pythonpath=src set in pyproject)
.venv\Scripts\python -m pytest tests/test_golden.py         # golden tests only
```

Always use the interpreter in the project's virtual environment (`.venv\Scripts\python`), not a global `python`/`pytest`.

CI (`.github/workflows/tests.yml`) runs `pytest -v` on Python 3.12 for every push and PR. No linter or formatter is configured.

## Architecture principles

These are the rules the code is expected to follow. Reviews should check the code against them by number.

- **P1 – One-way pipeline.** `parser.parse(text) -> ParseResult` → `checks.run_checks(result) -> list[Issue]` → `report.Report` → `report.render_text(report) -> str` → `cli.main` prints it. `--fix` is a side branch: `fix.fix_playlist(result) -> FixResult` (may import `parser` and `checks`). Each stage lives in its own module, and imports only point backwards along the pipeline: `parser` imports nothing from the project, `checks` may import `parser`, `report` and `fix` may import `checks`, and only `cli` imports everything. Any module may import `__version__` from the package.
- **P2 – Pure core, I/O at the edge.** `parser`, `checks`, `report` and `fix` do no file or network I/O, never print, and never exit. Reading files, writing output and choosing the exit code happen only in `cli.py`.
- **P3 – Content problems are data, not exceptions.** A malformed playlist never raises. The parser returns problems as `ParseError` and the checks return `Issue`. Exceptions are only for I/O failures, and `cli.py` turns them into exit code `2`.
- **P4 – Stable codes, text is presentation.** Every `Issue` and `ParseError` has a stable `code` (e.g. `duplicate-url`). Code and tests branch on `code` and `Level`, never on the Swedish message text.
- **P5 – One check, one function.** Each check is a function `(ParseResult) -> Iterable[Issue]` registered in `CHECKS`. Adding a check means adding a function and one list entry, not editing `run_checks`. The order of `CHECKS` is part of the output contract.
- **P6 – Presentation lives in `report.py`.** Formatting and the summary counts are in `report.py`. A new output format (JSON/HTML) is a new `render_*` function; `cli.py` only picks which one to call.
- **P7 – No runtime dependencies.** Only the standard library at runtime. `pytest` is the only dev dependency.
- **P8 – Behaviour changes are explicit.** Any change to CLI output or exit codes must update `tests/test_golden.py` in the same commit, with the reason in the commit message. A refactor must leave the golden tests untouched.
- **P9 – Single source of truth.** Messages, allowed schemes, issue codes and the version number are each defined in exactly one place.

## Architecture details

- `parser.py` is a line-by-line state machine. An `#EXTINF` line becomes a `_PendingExtinf` that the next non-`#` line completes into a `Channel`. Other `#` directives (e.g. `#EXTVLCOPT`) between `#EXTINF` and the URL are kept in `Channel.options`, and the raw `#EXTINF` line in `Channel.extinf`, so `--fix` can write channels back unchanged. The name is split at the first comma outside quotes (`_split_extinf`). A leading BOM is stripped, and blank lines before `#EXTM3U` are allowed. Attributes are parsed with `ATTR_RE` into `Channel.attrs`; `group`, `logo` and `tvg_id` are properties over `attrs`. Parser messages are module constants (`EXTINF_WITHOUT_URL`, `URL_WITHOUT_EXTINF`).
- `Channel.line` is the 1-based line number of the **`#EXTINF`** line, not the URL line. All per-channel issues report that line.
- `checks.py` defines `Level(str, Enum)` (not `StrEnum`, which needs 3.11; format it via `.value`), `Issue(level, line, message, code, channel)`, the check functions, `CHECKS`, `url_problem(url)` (shared with `fix.py`), and `find_duplicates(channels)`, which returns only URLs that occur more than once, with channels in file order. `run_checks` runs `CHECKS` in order and sorts stably by line.
- `report.py` defines `Report(channel_count, issues, show_warnings)` with `errors`, `warnings`, `shown` and `errors_only()` (hides warnings but keeps counting them), and `render_text`, `render_json`, `render_html`. Text format: `rad {line:>4}  {LEVEL:7}  {message}` per issue, then a blank line and `N kanaler, X fel, Y varningar` (plus ` (visas inte)` when warnings are hidden).
- `fix.py`: `fix_playlist` drops duplicates (keeps the first) and invalid URLs, sorts stably by `group-title` (no group last) and keeps the original `#EXTM3U` header.
- `cli.py` reconfigures stdout/stderr to UTF-8 (needed for pipes and the PyInstaller exe). Flags: `--errors-only`, `--format text|json|html`, `--fix`, `-o/--output`, `--version`. Exit codes: `0` no errors (and always for `--fix`), `1` at least one error (warnings don't count), `2` the file couldn't be read or written. `python -m m3ucheck` works via `__main__.py`.

## Known limitations

- `--online` (week 3) is not implemented.
- File reading uses `errors="replace"`, so invalid UTF-8 bytes become `�` silently.

## Testing notes

- `tests/test_golden.py` locks the exact CLI output and exit code for `sample.m3u` and edge cases. Do not change it in a refactor (see P8).
- `tests/test_encoding.py` runs the CLI in a subprocess, because `capsys` never encodes to bytes and can't catch encoding bugs. `tests/test_features.py` covers `--format`, `-o` and `--fix`.
- `tests/test_m3ucheck.py::test_cli_on_example_returns_1` depends on `examples/sample.m3u` (4 channels, at least 1 error). Update that test if you change the example file.
- `baseline.txt` and `efter.txt` are gitignored snapshots of CLI output, used to check that a refactor doesn't change behavior. Capture with `.venv\Scripts\python -m m3ucheck.cli examples/sample.m3u | Out-File -Encoding utf8 efter.txt` and compare with `fc.exe baseline.txt efter.txt`.
