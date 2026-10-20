"""Läser M3U/M3U8-spellistor (IPTV) till en lista med kanaler."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Lookbehind: börja bara matcha i början av ett namn, annars blir långa rader kvadratiska.
ATTR_RE = re.compile(r'(?<![\w-])([\w-]+)="([^"]*)"')

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
    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#EXTM3U"):
            continue
        if stripped.startswith("#EXTINF"):
            if pending is not None:
                errors.append(_extinf_without_url(pending.line))
            # Format: #EXTINF:-1 tvg-id="x" group-title="Y",Kanalnamn
            # Attributen står före första kommatecknet, namnet efter. Ett dubblerat
            # attribut tar det sista värdet (dict av findall).
            head, _, name = stripped.partition(",")
            pending = _PendingExtinf(lineno, name.strip(), dict(ATTR_RE.findall(head)))
        elif stripped.startswith("#"):
            continue  # andra direktiv, t.ex. #EXTVLCOPT
        elif pending is not None:
            channels.append(Channel(name=pending.name, url=stripped, line=pending.line, attrs=pending.attrs))
            pending = None
        else:
            errors.append(ParseError(lineno, "url-without-extinf", URL_WITHOUT_EXTINF))

    if pending is not None:
        errors.append(_extinf_without_url(pending.line))
    return ParseResult(channels, has_header, errors)
