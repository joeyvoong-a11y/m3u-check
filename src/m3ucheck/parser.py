"""Läser M3U/M3U8-spellistor (IPTV) till en lista med kanaler."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


@dataclass
class Channel:
    name: str
    url: str
    line: int  # radnummer för #EXTINF-raden (1-baserat)
    attrs: dict[str, str] = field(default_factory=dict)

    @property
    def group(self) -> str:
        return self.attrs.get("group-title", "")

    @property
    def logo(self) -> str:
        return self.attrs.get("tvg-logo", "")


@dataclass
class ParseResult:
    channels: list[Channel]
    has_header: bool
    errors: list[tuple[int, str]]  # (radnummer, meddelande)


def parse(text: str) -> ParseResult:
    lines = text.splitlines()
    has_header = bool(lines) and lines[0].strip().startswith("#EXTM3U")
    channels: list[Channel] = []
    errors: list[tuple[int, str]] = []

    pending: tuple[int, str, dict[str, str]] | None = None
    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF"):
            if pending:
                errors.append((pending[0], "#EXTINF utan URL efter"))
            head, _, name = line.partition(",")
            pending = (i, name.strip(), dict(ATTR_RE.findall(head)))
        elif line.startswith("#"):
            continue  # andra direktiv, t.ex. #EXTVLCOPT
        elif pending:
            lineno, name, attrs = pending
            channels.append(Channel(name=name, url=line, line=lineno, attrs=attrs))
            pending = None
        else:
            errors.append((i, "URL utan #EXTINF före"))

    if pending:
        errors.append((pending[0], "#EXTINF utan URL efter"))
    return ParseResult(channels, has_header, errors)
