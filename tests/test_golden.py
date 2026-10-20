"""Golden-tester: låser CLI:ts exakta utdata och exit-koder.

Vissa fall låser medvetet nuvarande (felaktigt) beteende – BOM, komma i
attribut, tom rad före #EXTM3U, kanal utan namn, summeringen med
--errors-only. Ändra dem bara som ett medvetet beslut att ändra beteendet.
"""

from pathlib import Path

import pytest

from m3ucheck.cli import main

EXAMPLE = Path(__file__).parent.parent / "examples" / "sample.m3u"

GOOD = """#EXTM3U
#EXTINF:-1 tvg-logo="l.png" group-title="A",Kanal 1
https://example.com/1.m3u8
"""

SAMPLE_OUT = """\
rad    4  WARNING  'Exempel Sport' saknar tvg-logo
rad    6  WARNING  'Exempel Film' saknar group-title
rad    6  ERROR    Ogiltig URL: ftp://example.com/film.ts
rad    8  WARNING  Dubblett av rad 2: https://example.com/live/news.m3u8
rad   10  ERROR    #EXTINF utan URL efter

4 kanaler, 2 fel, 3 varningar
"""

SAMPLE_ERRORS_ONLY_OUT = """\
rad    6  ERROR    Ogiltig URL: ftp://example.com/film.ts
rad   10  ERROR    #EXTINF utan URL efter

4 kanaler, 2 fel, 0 varningar
"""


def test_sample(capsys):
    assert main([str(EXAMPLE)]) == 1
    assert capsys.readouterr().out == SAMPLE_OUT


def test_sample_errors_only(capsys):
    # Summeringen räknas efter filtreringen, därav "0 varningar".
    assert main([str(EXAMPLE), "--errors-only"]) == 1
    assert capsys.readouterr().out == SAMPLE_ERRORS_ONLY_OUT


def test_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "finns-inte.m3u")]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Kunde inte läsa filen:")


CASES = [
    ("good", GOOD, 0, "\n1 kanaler, 0 fel, 0 varningar\n"),
    (
        "no-header",
        GOOD.replace("#EXTM3U\n", ""),
        1,
        "rad    1  ERROR    Filen börjar inte med #EXTM3U\n\n1 kanaler, 1 fel, 0 varningar\n",
    ),
    (
        "url-without-extinf",
        "#EXTM3U\nhttps://example.com/x\n",
        1,
        "rad    2  ERROR    URL utan #EXTINF före\n\n0 kanaler, 1 fel, 0 varningar\n",
    ),
    (
        "nameless",
        '#EXTM3U\n#EXTINF:-1 tvg-logo="l.png",\nhttps://example.com/1.m3u8\n',
        0,
        "rad    2  WARNING  Kanalen saknar namn\n"
        "rad    2  WARNING  '' saknar group-title\n"
        "\n1 kanaler, 0 fel, 2 varningar\n",
    ),
    (
        # Ordningen inom en rad följer ordningen kontrollerna körs i.
        "same-line-order",
        '#EXTM3U\n#EXTINF:-1 tvg-logo="l.png" group-title="A",A\nftp://example.com/x\n'
        "#EXTINF:-1,B\nftp://example.com/x\n",
        1,
        "rad    2  ERROR    Ogiltig URL: ftp://example.com/x\n"
        "rad    4  WARNING  'B' saknar group-title\n"
        "rad    4  WARNING  'B' saknar tvg-logo\n"
        "rad    4  ERROR    Ogiltig URL: ftp://example.com/x\n"
        "rad    4  WARNING  Dubblett av rad 2: ftp://example.com/x\n"
        "\n2 kanaler, 2 fel, 3 varningar\n",
    ),
    (
        "bom",
        "﻿" + GOOD,
        1,
        "rad    1  ERROR    Filen börjar inte med #EXTM3U\n"
        "rad    1  ERROR    URL utan #EXTINF före\n"
        "\n1 kanaler, 2 fel, 0 varningar\n",
    ),
    (
        "comma-in-attribute",
        '#EXTM3U\n#EXTINF:-1 tvg-logo="l.png" group-title="Sport, HD",Kanal 1\n'
        "https://example.com/1.m3u8\n",
        0,
        "rad    2  WARNING  'HD\",Kanal 1' saknar group-title\n\n1 kanaler, 0 fel, 1 varningar\n",
    ),
    (
        "blank-line-before-header",
        "\n" + GOOD,
        1,
        "rad    1  ERROR    Filen börjar inte med #EXTM3U\n\n1 kanaler, 1 fel, 0 varningar\n",
    ),
]


@pytest.mark.parametrize("text,code,out", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_golden(tmp_path, capsys, text, code, out):
    f = tmp_path / "lista.m3u"
    f.write_text(text, encoding="utf-8")
    assert main([str(f)]) == code
    assert capsys.readouterr().out == out
