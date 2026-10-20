"""Kontroller som körs på en tolkad spellista."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from .parser import Channel, ParseResult

VALID_SCHEMES = {"http", "https", "rtmp", "rtsp", "udp", "rtp"}

# Tillfällig koppling från parserns meddelanden till koder (ersätts i steg 3).
PARSER_ERROR_CODES = {
    "#EXTINF utan URL efter": "extinf-without-url",
    "URL utan #EXTINF före": "url-without-extinf",
}


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


def run_checks(result: ParseResult) -> list[Issue]:
    issues: list[Issue] = []

    if not result.has_header:
        issues.append(Issue(Level.ERROR, 1, "Filen börjar inte med #EXTM3U", "missing-header"))

    for lineno, msg in result.errors:
        issues.append(Issue(Level.ERROR, lineno, msg, PARSER_ERROR_CODES[msg]))

    by_url: dict[str, list[Channel]] = defaultdict(list)
    for ch in result.channels:
        if not ch.name:
            issues.append(Issue(Level.WARNING, ch.line, "Kanalen saknar namn", "missing-name", ch))
        if not ch.group:
            issues.append(
                Issue(Level.WARNING, ch.line, f"'{ch.name}' saknar group-title", "missing-group", ch)
            )
        if not ch.logo:
            issues.append(
                Issue(Level.WARNING, ch.line, f"'{ch.name}' saknar tvg-logo", "missing-logo", ch)
            )
        if urlparse(ch.url).scheme.lower() not in VALID_SCHEMES:
            issues.append(Issue(Level.ERROR, ch.line, f"Ogiltig URL: {ch.url}", "invalid-scheme", ch))
        by_url[ch.url].append(ch)

    for url, chans in by_url.items():
        first = chans[0]
        for dup in chans[1:]:
            issues.append(
                Issue(
                    Level.WARNING,
                    dup.line,
                    f"Dubblett av rad {first.line}: {url}",
                    "duplicate-url",
                    dup,
                )
            )

    return sorted(issues, key=lambda i: i.line)
