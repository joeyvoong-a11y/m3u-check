from pathlib import Path

from m3ucheck.checks import Level, run_checks
from m3ucheck.cli import main
from m3ucheck.parser import parse

GOOD = """#EXTM3U
#EXTINF:-1 tvg-logo="l.png" group-title="A",Kanal 1
https://example.com/1.m3u8
"""


def test_parse_reads_name_url_and_attrs():
    r = parse(GOOD)
    assert r.has_header
    assert len(r.channels) == 1
    ch = r.channels[0]
    assert ch.name == "Kanal 1"
    assert ch.url == "https://example.com/1.m3u8"
    assert ch.group == "A"
    assert ch.line == 2


def test_good_playlist_has_no_issues():
    assert run_checks(parse(GOOD)) == []


def test_missing_header_is_error():
    issues = run_checks(parse(GOOD.replace("#EXTM3U\n", "")))
    assert any(i.level is Level.ERROR and i.code == "missing-header" for i in issues)


def test_extinf_without_url():
    r = parse("#EXTM3U\n#EXTINF:-1,Ensam\n")
    assert r.errors == [(2, "#EXTINF utan URL efter")]


def test_duplicate_url_is_warning():
    text = GOOD + '#EXTINF:-1 tvg-logo="l.png" group-title="A",Kopia\nhttps://example.com/1.m3u8\n'
    issues = run_checks(parse(text))
    dups = [i for i in issues if i.code == "duplicate-url"]
    assert len(dups) == 1
    assert dups[0].level is Level.WARNING
    assert dups[0].channel.name == "Kopia"


def test_invalid_scheme_is_error():
    issues = run_checks(parse(GOOD.replace("https://", "ftp://")))
    assert any(i.level is Level.ERROR and i.code == "invalid-scheme" for i in issues)


def test_cli_on_example_returns_1(capsys):
    example = Path(__file__).parent.parent / "examples" / "sample.m3u"
    assert main([str(example)]) == 1
    assert "4 kanaler" in capsys.readouterr().out
