"""Kontroller som körs på en tolkad spellista."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from .parser import Channel, ParseResult

VALID_SCHEMES = {"http", "https", "rtmp", "rtsp", "udp", "rtp"}


class Level(str, Enum):
    # Inte StrEnum (kräver 3.11). Formatera via .value – format() ger annars
    # "Level.ERROR" i nyare Python.
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Issue:
    level: Level
    line: int
    message: str
    code: str  # stabil identifierare, t.ex. "invalid-scheme"
    channel: Channel | None = None


def find_duplicates(channels: list[Channel]) -> dict[str, list[Channel]]:
    """URL -> kanaler med den URL:en, i filordning. Bara URL:er som förekommer flera gånger."""
    by_url: dict[str, list[Channel]] = defaultdict(list)
    for ch in channels:
        by_url[ch.url].append(ch)
    return {url: chans for url, chans in by_url.items() if len(chans) > 1}


def check_header(result: ParseResult) -> Iterator[Issue]:
    if not result.has_header:
        yield Issue(Level.ERROR, 1, "Filen börjar inte med #EXTM3U", "missing-header")


def check_parse_errors(result: ParseResult) -> Iterator[Issue]:
    for err in result.errors:
        yield Issue(Level.ERROR, err.line, err.message, err.code)


def check_name(result: ParseResult) -> Iterator[Issue]:
    for ch in result.channels:
        if not ch.name:
            yield Issue(Level.WARNING, ch.line, "Kanalen saknar namn", "missing-name", ch)


def check_group(result: ParseResult) -> Iterator[Issue]:
    for ch in result.channels:
        if not ch.group:
            yield Issue(Level.WARNING, ch.line, f"'{ch.name}' saknar group-title", "missing-group", ch)


def check_logo(result: ParseResult) -> Iterator[Issue]:
    for ch in result.channels:
        if not ch.logo:
            yield Issue(Level.WARNING, ch.line, f"'{ch.name}' saknar tvg-logo", "missing-logo", ch)


def _invalid_url(ch: Channel, code: str) -> Issue:
    return Issue(Level.ERROR, ch.line, f"Ogiltig URL: {ch.url}", code, ch)


def check_scheme(result: ParseResult) -> Iterator[Issue]:
    for ch in result.channels:
        try:
            scheme = urlparse(ch.url).scheme.lower()
        except ValueError:  # t.ex. "http://[abc/x" (ogiltig IPv6-adress)
            yield _invalid_url(ch, "malformed-url")
            continue
        if scheme not in VALID_SCHEMES:
            yield _invalid_url(ch, "invalid-scheme")


def check_duplicates(result: ParseResult) -> Iterator[Issue]:
    for url, (first, *dups) in find_duplicates(result.channels).items():
        for dup in dups:
            yield Issue(
                Level.WARNING, dup.line, f"Dubblett av rad {first.line}: {url}", "duplicate-url", dup
            )


# Ordningen styr utdata: issues på samma rad visas i den ordning kontrollerna
# körs (sorteringen på rad är stabil). Ändra den inte utan att ändra golden-testerna.
CHECKS: list[Callable[[ParseResult], Iterable[Issue]]] = [
    check_header,
    check_parse_errors,
    check_name,
    check_group,
    check_logo,
    check_scheme,
    check_duplicates,
]


def run_checks(result: ParseResult) -> list[Issue]:
    issues = [issue for check in CHECKS for issue in check(result)]
    return sorted(issues, key=lambda i: i.line)
