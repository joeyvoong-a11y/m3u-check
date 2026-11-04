"""Tester för poleringen i Hemuppgift 4, steg 3 (se docs/hemuppgift4-polering.md)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from m3ucheck.checks import run_checks
from m3ucheck.cli import main
from m3ucheck.parser import parse

EXAMPLE = Path(__file__).parent.parent / "examples" / "sample.m3u"
SRC = Path(__file__).parent.parent / "src"


@pytest.mark.parametrize("text", ["", "\n\n  \n"])
def test_empty_file_is_its_own_error(text):
    issues = run_checks(parse(text))
    assert [(i.level.value, i.code) for i in issues] == [("error", "empty-file")]


def test_header_without_channels_is_warning():
    issues = run_checks(parse("#EXTM3U\n"))
    assert [(i.level.value, i.code) for i in issues] == [("warning", "no-channels")]


def test_no_channels_warning_not_added_when_errors_explain_it():
    codes = [i.code for i in run_checks(parse("#EXTM3U\n#EXTINF:-1,A\n"))]
    assert codes == ["extinf-without-url"]


def test_directory_gives_swedish_reason(tmp_path, capsys):
    assert main([str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert err.startswith(f"Kunde inte läsa filen {tmp_path}: ")
    assert "Errno" not in err


def test_non_utf8_file_is_read_as_cp1252_with_warning(tmp_path, capsys):
    f = tmp_path / "latin.m3u"
    f.write_bytes('#EXTM3U\n#EXTINF:-1,Kanal ÅÄÖ\nhttps://example.com/1\n'.encode("cp1252"))
    assert main([str(f), "--format", "json"]) == 0
    captured = capsys.readouterr()
    assert '"channel": "Kanal ÅÄÖ"' in captured.out
    assert captured.err.startswith("Varning: latin.m3u är inte UTF-8")


def test_refuses_to_overwrite_playlist_with_report(tmp_path, capsys):
    f = tmp_path / "lista.m3u"
    f.write_bytes(EXAMPLE.read_bytes())
    assert main([str(f), "-o", str(f)]) == 2
    assert f.read_bytes() == EXAMPLE.read_bytes()
    assert capsys.readouterr().err.startswith("Vägrar skriva rapporten över spellistan")


def test_fix_may_overwrite_playlist(tmp_path, capsys):
    f = tmp_path / "lista.m3u"
    f.write_bytes(EXAMPLE.read_bytes())
    assert main([str(f), "--fix", "-o", str(f)]) == 0
    assert run_checks(parse(f.read_text(encoding="utf-8"))) != []  # städad men har varningar kvar
    assert "ftp://" not in f.read_text(encoding="utf-8")


@pytest.mark.parametrize("extra", [["--format", "json"], ["--errors-only"]])
def test_fix_rejects_report_flags(extra, capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(EXAMPLE), "--fix", *extra])
    assert exc.value.code == 2
    assert "--fix" in capsys.readouterr().err


def test_closed_pipe_is_not_a_crash():
    # Som `m3u-check lista.m3u | head -c 0`: läsaren stänger pipen direkt.
    proc = subprocess.Popen(
        [sys.executable, "-m", "m3ucheck", str(EXAMPLE)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": str(SRC)},
    )
    proc.stdout.close()
    stderr = proc.stderr.read()
    assert proc.wait() == 1  # samma exit-kod som vanligt
    assert b"Traceback" not in stderr and b"Exception ignored" not in stderr
