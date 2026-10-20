"""Kontroller som körs på en tolkad spellista."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import urlparse

from .parser import ParseResult

VALID_SCHEMES = {"http", "https", "rtmp", "rtsp", "udp", "rtp"}


@dataclass
class Issue:
    level: str  # "error" eller "warning"
    line: int
    message: str


def run_checks(result: ParseResult) -> list[Issue]:
    issues: list[Issue] = []

    if not result.has_header:
        issues.append(Issue("error", 1, "Filen börjar inte med #EXTM3U"))

    for lineno, msg in result.errors:
        issues.append(Issue("error", lineno, msg))

    by_url: dict[str, list[int]] = defaultdict(list)
    for ch in result.channels:
        if not ch.name:
            issues.append(Issue("warning", ch.line, "Kanalen saknar namn"))
        if not ch.group:
            issues.append(Issue("warning", ch.line, f"'{ch.name}' saknar group-title"))
        if not ch.logo:
            issues.append(Issue("warning", ch.line, f"'{ch.name}' saknar tvg-logo"))
        if urlparse(ch.url).scheme.lower() not in VALID_SCHEMES:
            issues.append(Issue("error", ch.line, f"Ogiltig URL: {ch.url}"))
        by_url[ch.url].append(ch.line)

    for url, lines in by_url.items():
        for dup in lines[1:]:
            issues.append(Issue("warning", dup, f"Dubblett av rad {lines[0]}: {url}"))

    return sorted(issues, key=lambda i: i.line)
