"""Tester för funktionerna från Hemuppgift 4: tvg-id och rättade buggar."""

from m3ucheck.checks import run_checks
from m3ucheck.cli import main
from m3ucheck.parser import parse

GOOD = """#EXTM3U
#EXTINF:-1 tvg-id="k1" tvg-logo="l.png" group-title="A",Kanal 1
https://example.com/1.m3u8
"""


def test_missing_tvg_id_is_warning():
    issues = run_checks(parse(GOOD.replace(' tvg-id="k1"', "")))
    assert [(i.level.value, i.code) for i in issues] == [("warning", "missing-tvg-id")]


def test_bom_file_on_disk(tmp_path, capsys):
    f = tmp_path / "bom.m3u"
    f.write_bytes(b"\xef\xbb\xbf" + GOOD.encode("utf-8"))
    assert main([str(f)]) == 0
    assert capsys.readouterr().out == "\n1 kanaler, 0 fel, 0 varningar\n"
