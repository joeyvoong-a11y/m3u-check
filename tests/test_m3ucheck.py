import time
from pathlib import Path

from m3ucheck.checks import Level, find_duplicates, run_checks
from m3ucheck.cli import main
from m3ucheck.parser import parse
from m3ucheck.report import Report, render_text

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


def test_long_extinf_line_without_attrs_parses_fast():
    text = "#EXTM3U\n#EXTINF:-1 " + "a" * 50_000 + "\n"
    start = time.perf_counter()
    r = parse(text)
    assert time.perf_counter() - start < 1
    assert [e.code for e in r.errors] == ["extinf-without-url"]


def test_good_playlist_has_no_issues():
    assert run_checks(parse(GOOD)) == []


def test_missing_header_is_error():
    issues = run_checks(parse(GOOD.replace("#EXTM3U\n", "")))
    assert any(i.level is Level.ERROR and i.code == "missing-header" for i in issues)


def test_extinf_without_url():
    r = parse("#EXTM3U\n#EXTINF:-1,Ensam\n")
    assert [(e.line, e.code) for e in r.errors] == [(2, "extinf-without-url")]


def test_url_without_extinf():
    r = parse("#EXTM3U\nhttps://example.com/x\n")
    assert [(e.line, e.code) for e in r.errors] == [(2, "url-without-extinf")]
    assert r.channels == []


def test_duplicate_url_is_warning():
    text = GOOD + '#EXTINF:-1 tvg-logo="l.png" group-title="A",Kopia\nhttps://example.com/1.m3u8\n'
    issues = run_checks(parse(text))
    dups = [i for i in issues if i.code == "duplicate-url"]
    assert len(dups) == 1
    assert dups[0].level is Level.WARNING
    assert dups[0].channel.name == "Kopia"


def test_find_duplicates_groups_in_file_order():
    text = (
        GOOD
        + '#EXTINF:-1,Kopia\nhttps://example.com/1.m3u8\n'
        + '#EXTINF:-1,Unik\nhttps://example.com/2.m3u8\n'
    )
    dups = find_duplicates(parse(text).channels)
    assert list(dups) == ["https://example.com/1.m3u8"]
    assert [ch.name for ch in dups["https://example.com/1.m3u8"]] == ["Kanal 1", "Kopia"]


def test_invalid_scheme_is_error():
    issues = run_checks(parse(GOOD.replace("https://", "ftp://")))
    assert any(i.level is Level.ERROR and i.code == "invalid-scheme" for i in issues)


def test_malformed_url_is_error_not_crash():
    issues = run_checks(parse(GOOD.replace("https://example.com/1.m3u8", "http://[abc/x")))
    assert [(i.level, i.code) for i in issues] == [(Level.ERROR, "malformed-url")]


def test_report_counts_and_errors_only():
    text = GOOD.replace("https://", "ftp://").replace(' group-title="A"', "")
    report = Report(1, run_checks(parse(text)))
    assert [i.code for i in report.errors] == ["invalid-scheme"]
    assert [i.code for i in report.warnings] == ["missing-group"]
    assert report.errors_only().issues == report.errors
    assert render_text(report.errors_only()).endswith("\n1 kanaler, 1 fel, 0 varningar\n")


def test_cli_on_example_returns_1(capsys):
    example = Path(__file__).parent.parent / "examples" / "sample.m3u"
    assert main([str(example)]) == 1
    assert "4 kanaler" in capsys.readouterr().out
