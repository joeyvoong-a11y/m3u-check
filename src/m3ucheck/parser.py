"""Läser M3U/M3U8-spellistor (IPTV) till en lista med kanaler."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Lookbehind: börja bara matcha i början av ett namn, annars blir långa rader kvadratiska.
ATTR_RE = re.compile(r'(?<![\w-])([\w-]+)="([^"]*)"')

BOM = "\ufeff"
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
    extinf: str = ""  # hela #EXTINF-raden som den stod i filen
    options: list[str] = field(default_factory=list)  # t.ex. #EXTVLCOPT mellan #EXTINF och URL

    @property
    def group(self) -> str:
        return self.attrs.get("group-title", "")

    @property
    def logo(self) -> str:
        return self.attrs.get("tvg-logo", "")

    @property
    def tvg_id(self) -> str:
        return self.attrs.get("tvg-id", "")


@dataclass
class ParseResult:
    channels: list[Channel]
    has_header: bool
    errors: list[ParseError]
    header: str = ""  # #EXTM3U-raden med ev. attribut (t.ex. url-tvg), annars tom
    is_empty: bool = False  # filen innehåller bara tomma rader (eller ingenting)


@dataclass
class _PendingExtinf:
    """En #EXTINF-rad som väntar på sin URL."""

    line: int
    name: str
    attrs: dict[str, str]
    extinf: str
    options: list[str] = field(default_factory=list)


def _extinf_without_url(line: int) -> ParseError:
    return ParseError(line, "extinf-without-url", EXTINF_WITHOUT_URL)


def _split_extinf(line: str) -> tuple[str, str]:
    """Dela #EXTINF-raden i (attributdel, namn) vid första kommatecknet utanför citattecken."""
    in_quotes = False
    for i, char in enumerate(line):
        if char == '"':
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            return line[:i], line[i + 1 :]
    return line, ""


def parse(text: str) -> ParseResult:
    lines = text.removeprefix(BOM).splitlines()
    # Tomma rader före #EXTM3U räknas inte som att headern saknas.
    first = next((line.strip() for line in lines if line.strip()), "")
    has_header = first.startswith("#EXTM3U")
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
            # Attributen står före första kommatecknet utanför citattecken, namnet
            # efter. Ett dubblerat attribut tar det sista värdet (dict av findall).
            head, name = _split_extinf(stripped)
            pending = _PendingExtinf(lineno, name.strip(), dict(ATTR_RE.findall(head)), stripped)
        elif stripped.startswith("#"):
            # Andra direktiv, t.ex. #EXTVLCOPT. De hör till kanalen de står i.
            if pending is not None:
                pending.options.append(stripped)
        elif pending is not None:
            channels.append(
                Channel(pending.name, stripped, pending.line, pending.attrs, pending.extinf, pending.options)
            )
            pending = None
        else:
            errors.append(ParseError(lineno, "url-without-extinf", URL_WITHOUT_EXTINF))

    if pending is not None:
        errors.append(_extinf_without_url(pending.line))
    return ParseResult(channels, has_header, errors, first if has_header else "", is_empty=not first)
