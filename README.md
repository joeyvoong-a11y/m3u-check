# m3u-check

Ett litet kommandoradsverktyg i Python som läser IPTV-spellistor (M3U/M3U8) och hittar fel och brister – innan de laddas in i en spelare som t.ex. [Hypnotix](https://github.com/linuxmint/hypnotix).

## Vad kontrolleras

| Kontroll | Nivå |
|---|---|
| Filen börjar inte med `#EXTM3U` | fel |
| `#EXTINF` utan URL, eller URL utan `#EXTINF` | fel |
| Ogiltig URL-typ (bara http/https/rtmp/rtsp/udp/rtp godkänns) | fel |
| Kanal saknar namn, `group-title` eller `tvg-logo` | varning |
| Samma stream-URL förekommer flera gånger | varning |

## Ladda ner (utan Python)

Färdiga program för Windows, Linux och macOS finns under [Releases](https://github.com/joeyvoong-a11y/m3u-check/releases/latest). Ladda ner filen för ditt system och kör den direkt:

```bash
m3u-check-windows.exe min-spellista.m3u      # Windows
./m3u-check-linux min-spellista.m3u          # Linux (kör först: chmod +x m3u-check-linux)
```

På macOS kan Gatekeeper blockera programmet eftersom det inte är signerat. Högerklicka och välj *Öppna*, eller kör `xattr -d com.apple.quarantine m3u-check-macos`.

## Installera med Python

```bash
pipx install git+https://github.com/joeyvoong-a11y/m3u-check
m3u-check min-spellista.m3u
```

## Utveckling

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

m3u-check examples/sample.m3u
pytest
```

Exempel på utdata:

```
rad    4  WARNING  'Exempel Sport' saknar tvg-logo
rad    6  WARNING  'Exempel Film' saknar group-title
rad    6  ERROR    Ogiltig URL: ftp://example.com/film.ts
rad    8  WARNING  Dubblett av rad 2: https://example.com/live/news.m3u8
rad   10  ERROR    #EXTINF utan URL efter

4 kanaler, 2 fel, 3 varningar
```

Flaggor: `--errors-only` visar bara fel. Exit-kod är `1` om fel hittades, annars `0`.

## Struktur

```
src/m3ucheck/
  parser.py   # läser M3U till Channel-objekt
  checks.py   # kontrollerna
  cli.py      # kommandoraden
tests/        # pytest
examples/     # exempelspellista
packaging/    # startskript för PyInstaller-bygget
```

## Släppa en ny version

1. Höj `__version__` i `src/m3ucheck/__init__.py` och committa.
2. Tagga och pusha: `git tag v0.1.0 && git push origin v0.1.0`

GitHub Actions (`.github/workflows/release.yml`) kör testerna, bygger programmen för alla tre systemen och lägger upp dem på en ny release.

## Plan (kursens 6 veckor)

- [x] **Vecka 1** – repo, struktur, parser, grundkontroller, tester, CI
- [ ] **Vecka 2** – fler kontroller (t.ex. saknat `tvg-id`, tomma grupper), bättre felmeddelanden
- [ ] **Vecka 3** – `--online`: testa om strömmarna svarar (HTTP HEAD med timeout)
- [ ] **Vecka 4** – export av rapport som JSON/HTML
- [ ] **Vecka 5** – `--fix`: skriv ut en städad spellista (utan dubbletter, sorterad per grupp)
- [ ] **Vecka 6** – dokumentation, buffert, presentation

## Licens

MIT
