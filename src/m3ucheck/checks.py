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
    # En tom fil får ett eget fel i stället för det missvisande "saknar #EXTM3U".
    if result.is_empty:
        yield Issue(Level.ERROR, 1, "Filen är tom", "empty-file")
    elif not result.has_header:
        yield Issue(Level.ERROR, 1, "Filen börjar inte med #EXTM3U", "missing-header")


def check_has_channels(result: ParseResult) -> Iterator[Issue]:
    # Bara när inget annat fel förklarar det (t.ex. att alla #EXTINF saknar URL).
    if not result.is_empty and not result.channels and not result.errors:
        yield Issue(Level.WARNING, 1, "Spellistan innehåller inga kanaler", "no-channels")


def check_parse_errors(result: ParseResult) -> Iterator[Issue]:
    for err in result.errors:
        yield Issue(Level.ERROR, err.line, err.message, err.code)


def check_name(result: ParseResult) -> Iterator[Issue]:
    for ch in result.channels:
        if not ch.name:
            yield Issue(Level.WARNING, ch.line, "Kanalen saknar namn", "missing-name", ch)


def _label(ch: Channel) -> str:
    return f"'{ch.name}'" if ch.name else "Kanal utan namn"


def _missing_attr(ch: Channel, attr: str, code: str) -> Issue:
    return Issue(Level.WARNING, ch.line, f"{_label(ch)} saknar {attr}", code, ch)


def check_group(result: ParseResult) -> Iterator[Issue]:
    for ch in result.channels:
        if not ch.group:
            yield _missing_attr(ch, "group-title", "missing-group")


def check_logo(result: ParseResult) -> Iterator[Issue]:
    for ch in result.channels:
        if not ch.logo:
            yield _missing_attr(ch, "tvg-logo", "missing-logo")


def check_tvg_id(result: ParseResult) -> Iterator[Issue]:
    # Utan tvg-id kan spelaren inte koppla kanalen till programguiden (EPG).
    for ch in result.channels:
        if not ch.tvg_id:
            yield _missing_attr(ch, "tvg-id", "missing-tvg-id")


def url_problem(url: str) -> str | None:
    """Felkoden för en ogiltig URL, eller None om den är giltig."""
    try:
        scheme = urlparse(url).scheme.lower()
    except ValueError:  # t.ex. "http://[abc/x" (ogiltig IPv6-adress)
        return "malformed-url"
    return None if scheme in VALID_SCHEMES else "invalid-scheme"


def check_scheme(result: ParseResult) -> Iterator[Issue]:
    for ch in result.channels:
        code = url_problem(ch.url)
        if code:
            yield Issue(Level.ERROR, ch.line, f"Ogiltig URL: {ch.url}", code, ch)


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
    check_has_channels,
    check_parse_errors,
    check_name,
    check_group,
    check_logo,
    check_tvg_id,
    check_scheme,
    check_duplicates,
]


def run_checks(result: ParseResult) -> list[Issue]:
    issues = [issue for check in CHECKS for issue in check(result)]
    return sorted(issues, key=lambda issue: issue.line)
