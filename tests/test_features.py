"""Tester för funktionerna från Hemuppgift 4: tvg-id, --format och -o."""

import json

from m3ucheck.checks import run_checks
from m3ucheck.cli import main
from m3ucheck.parser import parse

GOOD = """#EXTM3U
#EXTINF:-1 tvg-id="k1" tvg-logo="l.png" group-title="A",Kanal 1
https://example.com/1.m3u8
"""

MESSY = """#EXTM3U url-tvg="https://example.com/epg.xml"
#EXTINF:-1 tvg-id="s" group-title="Sport",Sport
#EXTVLCOPT:http-user-agent=Test
https://example.com/sport
#EXTINF:-1 tvg-id="n" group-title="Nyheter",Nyheter
https://example.com/news
#EXTINF:-1,Utan grupp
https://example.com/ingen
#EXTINF:-1 tvg-id="f" group-title="Film",Film
ftp://example.com/film
#EXTINF:-1 tvg-id="n2" group-title="Nyheter",Nyheter kopia
https://example.com/news
https://example.com/lös-url
"""


def _write(tmp_path, text):
    f = tmp_path / "lista.m3u"
    f.write_text(text, encoding="utf-8")
    return f


def test_missing_tvg_id_is_warning():
    issues = run_checks(parse(GOOD.replace(' tvg-id="k1"', "")))
    assert [(i.level.value, i.code) for i in issues] == [("warning", "missing-tvg-id")]


def test_json_format(tmp_path, capsys):
    assert main([str(_write(tmp_path, MESSY)), "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["channels"] == 5
    assert data["errors"] == 2
    codes = [i["code"] for i in data["issues"]]
    assert "invalid-scheme" in codes and "duplicate-url" in codes
    assert all(set(i) == {"line", "level", "code", "message", "channel"} for i in data["issues"])


def test_json_errors_only_keeps_counts(tmp_path, capsys):
    main([str(_write(tmp_path, MESSY)), "--format", "json", "--errors-only"])
    data = json.loads(capsys.readouterr().out)
    assert data["warnings"] > 0
    assert {i["level"] for i in data["issues"]} == {"error"}


def test_html_format_escapes(tmp_path, capsys):
    text = GOOD.replace("https://example.com/1.m3u8", "ftp://example.com/<script>")
    assert main([str(_write(tmp_path, text)), "--format", "html"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("<!doctype html>")
    assert "&lt;script&gt;" in out and "<script>" not in out


def test_output_file(tmp_path, capsys):
    target = tmp_path / "rapport.html"
    assert main([str(_write(tmp_path, GOOD)), "--format", "html", "-o", str(target)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "rapport.html" in captured.err
    assert "1 kanaler, 0 fel, 0 varningar" in target.read_text(encoding="utf-8")


def test_output_file_unwritable(tmp_path, capsys):
    target = tmp_path / "finns-inte" / "rapport.txt"
    assert main([str(_write(tmp_path, GOOD)), "-o", str(target)]) == 2
    assert capsys.readouterr().err.startswith("Kunde inte skriva filen:")


def test_bom_file_on_disk(tmp_path, capsys):
    f = tmp_path / "bom.m3u"
    f.write_bytes(b"\xef\xbb\xbf" + GOOD.encode("utf-8"))
    assert main([str(f)]) == 0
    assert capsys.readouterr().out == "\n1 kanaler, 0 fel, 0 varningar\n"
