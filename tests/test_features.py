"""Tester för funktionerna från Hemuppgift 4: tvg-id, --format, -o och --fix."""

import json

from m3ucheck.checks import run_checks
from m3ucheck.cli import main
from m3ucheck.fix import fix_playlist
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


def test_directives_belong_to_channel():
    ch = parse(MESSY).channels[0]
    assert ch.options == ["#EXTVLCOPT:http-user-agent=Test"]
    assert ch.extinf == '#EXTINF:-1 tvg-id="s" group-title="Sport",Sport'


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
    err = capsys.readouterr().err
    assert err == f"Kunde inte skriva filen {target}: filen eller mappen finns inte\n"


def test_fix_playlist():
    fixed = fix_playlist(parse(MESSY))
    assert fixed.text == (
        '#EXTM3U url-tvg="https://example.com/epg.xml"\n'
        '#EXTINF:-1 tvg-id="n" group-title="Nyheter",Nyheter\n'
        "https://example.com/news\n"
        '#EXTINF:-1 tvg-id="s" group-title="Sport",Sport\n'
        "#EXTVLCOPT:http-user-agent=Test\n"
        "https://example.com/sport\n"
        "#EXTINF:-1,Utan grupp\n"
        "https://example.com/ingen\n"
    )
    assert (fixed.kept, fixed.removed_duplicates, fixed.removed_invalid) == (3, 1, 1)


def test_fix_result_is_clean_of_errors():
    fixed = fix_playlist(parse(MESSY))
    again = run_checks(parse(fixed.text))
    assert [i for i in again if i.level.value == "error"] == []
    assert fix_playlist(parse(fixed.text)).text == fixed.text  # idempotent


def test_fix_adds_missing_header():
    assert fix_playlist(parse("#EXTINF:-1,A\nhttps://example.com/a\n")).text.startswith("#EXTM3U\n")


def test_cli_fix(tmp_path, capsys):
    target = tmp_path / "städad.m3u"
    assert main([str(_write(tmp_path, MESSY)), "--fix", "-o", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == fix_playlist(parse(MESSY)).text
    assert "3 kanaler kvar, 1 dubbletter och 1 ogiltiga URL:er borttagna" in capsys.readouterr().err


def test_bom_file_on_disk(tmp_path, capsys):
    f = tmp_path / "bom.m3u"
    f.write_bytes(b"\xef\xbb\xbf" + GOOD.encode("utf-8"))
    assert main([str(f)]) == 0
    assert capsys.readouterr().out == "\n1 kanaler, 0 fel, 0 varningar\n"
