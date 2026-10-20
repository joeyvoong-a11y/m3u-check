"""Läser M3U/M3U8-spellistor (IPTV) till en lista med kanaler."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')

EXTINF_WITHOUT_URL = "#EXTINF utan URL efter"
URL_WITHOUT_EXTINF = "URL utan #EXTINF före"


@dataclass
class ParseError:
    line: int  # 1-baserat
    code: str  # stabil identifierare, samma som Issue.code
    message: str


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
    errors: list[ParseError]


@dataclass
class _PendingExtinf:
    """En #EXTINF-rad som väntar på sin URL."""

    line: int
    name: str
    attrs: dict[str, str]


def _extinf_without_url(line: int) -> ParseError:
    return ParseError(line, "extinf-without-url", EXTINF_WITHOUT_URL)


def parse(text: str) -> ParseResult:
    lines = text.splitlines()
    has_header = bool(lines) and lines[0].strip().startswith("#EXTM3U")
    channels: list[Channel] = []
    errors: list[ParseError] = []

    pending: _PendingExtinf | None = None
    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF"):
            if pending is not None:
                errors.append(_extinf_without_url(pending.line))
            head, _, name = line.partition(",")
            pending = _PendingExtinf(i, name.strip(), dict(ATTR_RE.findall(head)))
        elif line.startswith("#"):
            continue  # andra direktiv, t.ex. #EXTVLCOPT
        elif pending is not None:
            channels.append(Channel(name=pending.name, url=line, line=pending.line, attrs=pending.attrs))
            pending = None
        else:
            errors.append(ParseError(i, "url-without-extinf", URL_WITHOUT_EXTINF))

    if pending is not None:
        errors.append(_extinf_without_url(pending.line))
    return ParseResult(channels, has_header, errors)
