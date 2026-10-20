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
.venv\Scripts\python -m pytest tests/test_m3ucheck.py::test_duplicate_url_is_warning   # single test
```

Always use the interpreter in the project's virtual environment (`.venv\Scripts\python`), not a global `python`/`pytest`.

CI (`.github/workflows/tests.yml`) runs `pytest -v` on Python 3.12 for every push and PR. No linter or formatter is configured.

## Architecture

The pipeline is `parser.parse(text) -> ParseResult` → `checks.run_checks(result) -> list[Issue]` → `cli.main` prints the issues.

- `parser.py` is a line-by-line state machine. An `#EXTINF` line becomes a `pending` channel that the next non-`#` line completes. Structural problems (an `#EXTINF` with no URL, or a URL with no `#EXTINF`) are **not** raised. The parser collects them in `ParseResult.errors` as `(line, message)` tuples. Other `#` directives (e.g. `#EXTVLCOPT`) are ignored. Attributes are parsed with `ATTR_RE` into `Channel.attrs`. `group` and `logo` are properties over `attrs`.
- `checks.py` turns parser errors and its own checks into `Issue(level, line, message)`. `level` is the string `"error"` or `"warning"`. The output is sorted by line. A new check usually goes in the `for ch in result.channels` loop. Allowed URL schemes are in `VALID_SCHEMES`.
- `Channel.line` is the 1-based line number of the **`#EXTINF`** line, not the URL line. All per-channel issues report that line.
- `cli.py` handles the exit codes: `0` means no errors, `1` means at least one error (warnings don't count), and `2` means the file couldn't be read. The output format is `rad {line:>4}  {LEVEL:7}  {message}`, followed by a summary line `N kanaler, X fel, Y varningar`.

## Testing notes

- `tests/test_m3ucheck.py::test_cli_on_example_returns_1` depends on `examples/sample.m3u` (4 channels, at least 1 error). Update that test if you change the example file.
- `baseline.txt` and `efter.txt` are gitignored snapshots of CLI output, used to check that a refactor doesn't change behavior. In Windows PowerShell, `>` writes UTF-16, so capture with `.venv\Scripts\python -m m3ucheck.cli examples/sample.m3u | Out-File -Encoding utf8 efter.txt` before you diff.
