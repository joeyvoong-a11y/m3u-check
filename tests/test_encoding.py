"""Utdata ska vara UTF-8 även när den går till en pipe (Hemuppgift 3, del A).

capsys fångar text och kodar den aldrig till bytes, så felet syns bara i en
riktig process.
"""

import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).parent.parent / "src"


def _run(*args: str) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    env["PYTHONPATH"] = str(SRC)
    return subprocess.run([sys.executable, "-m", "m3ucheck", *args], capture_output=True, env=env)


def test_stdout_is_utf8_in_pipe(tmp_path):
    f = tmp_path / "lista.m3u"
    f.write_text("#EXTINF:-1,Kanal\nhttps://example.com/1\n", encoding="utf-8")
    out = _run(str(f)).stdout
    assert "Filen börjar inte med #EXTM3U".encode("utf-8") in out


def test_stderr_is_utf8_in_pipe(tmp_path):
    proc = _run(str(tmp_path / "finns-inte.m3u"))
    assert proc.returncode == 2
    assert proc.stderr.startswith("Kunde inte läsa filen".encode("utf-8"))
