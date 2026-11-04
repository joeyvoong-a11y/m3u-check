"""--fix: bygger en städad spellista av en tolkad spellista."""

from __future__ import annotations

from dataclasses import dataclass

from .checks import find_duplicates, url_problem
from .parser import Channel, ParseResult


@dataclass
class FixResult:
    text: str
    kept: int
    removed_duplicates: int
    removed_invalid: int


def fix_playlist(result: ParseResult) -> FixResult:
    """Ta bort dubbletter och ogiltiga URL:er och sortera per grupp.

    Första förekomsten av en dubblett behålls. Kanaler sorteras på group-title
    (kanaler utan grupp sist), och inom en grupp behålls filordningen.
    #EXTINF-raderna och direktiven skrivs ut som de stod, så inga attribut tappas.
    Rader som inte hörde till någon kanal (t.ex. URL utan #EXTINF) tas bort.
    """
    duplicates = {id(ch) for dups in find_duplicates(result.channels).values() for ch in dups[1:]}
    invalid = [ch for ch in result.channels if url_problem(ch.url)]
    invalid_ids = {id(ch) for ch in invalid}
    kept = [ch for ch in result.channels if id(ch) not in duplicates and id(ch) not in invalid_ids]
    kept.sort(key=lambda ch: (not ch.group, ch.group.casefold()))

    lines = [result.header or "#EXTM3U"]
    for ch in kept:
        lines += _channel_lines(ch)
    return FixResult(
        text="\n".join(lines) + "\n",
        kept=len(kept),
        removed_duplicates=len(duplicates - invalid_ids),
        removed_invalid=len(invalid),
    )


def _channel_lines(ch: Channel) -> list[str]:
    return [ch.extinf, *ch.options, ch.url]
