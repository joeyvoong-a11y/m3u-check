# m3u-check

Ett litet kommandoradsverktyg i Python som läser IPTV-spellistor (M3U/M3U8) och hittar fel och brister – innan de laddas in i en spelare som t.ex. [Hypnotix](https://github.com/linuxmint/hypnotix).

## Vad kontrolleras

| Kontroll | Nivå |
|---|---|
| Filen börjar inte med `#EXTM3U` | fel |
| `#EXTINF` utan URL, eller URL utan `#EXTINF` | fel |
| Ogiltig URL-typ (bara http/https/rtmp/rtsp/udp/rtp godkänns) | fel |
| Kanal saknar namn, `group-title`, `tvg-logo` eller `tvg-id` | varning |
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
rad    6  WARNING  'Exempel Film' saknar tvg-id
rad    6  ERROR    Ogiltig URL: ftp://example.com/film.ts
rad    8  WARNING  'Exempel Nyheter HD' saknar tvg-id
rad    8  WARNING  Dubblett av rad 2: https://example.com/live/news.m3u8
rad   10  ERROR    #EXTINF utan URL efter

4 kanaler, 2 fel, 5 varningar
```

## Flaggor

| Flagga | Vad den gör |
|---|---|
| `--errors-only` | Visa bara fel. Summeringen räknar ändå alla varningar. |
| `--format text\|json\|html` | Rapportens format. JSON passar för skript, HTML för att dela. |
| `--fix` | Skriv ut en städad spellista: dubbletter och ogiltiga URL:er tas bort, kanalerna sorteras per grupp. Attribut och `#EXTVLCOPT` behålls. |
| `-o FIL`, `--output FIL` | Skriv till en fil (UTF-8) i stället för till skärmen. |
| `--version` | Visa versionen. |

```bash
m3u-check lista.m3u --format html -o rapport.html
m3u-check lista.m3u --fix -o städad.m3u
```

Använd `-o` i stället för `>` i PowerShell, eftersom `>` där kan skriva filen som UTF-16.

Exit-kod: `0` inga fel, `1` fel hittades (varningar räknas inte), `2` filen kunde inte läsas eller skrivas. `--fix` ger `0` när den städade listan har skrivits.

## Struktur

```
src/m3ucheck/
  parser.py   # läser M3U till Channel-objekt
  checks.py   # kontrollerna
  report.py   # rapporten som text, JSON eller HTML
  fix.py      # --fix: städad spellista
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
- [x] **Vecka 2** – kontroll av `tvg-id`, rättade buggar (BOM, kommatecken i attribut, kanal utan namn, tom rad före header), åäö i utskrifter
- [ ] **Vecka 3** – `--online`: testa om strömmarna svarar (HTTP HEAD med timeout). *Bortprioriterad: nätverk gör demo och tester opålitliga.*
- [x] **Vecka 4** – export av rapport som JSON/HTML (`--format`, `-o`)
- [x] **Vecka 5** – `--fix`: skriv ut en städad spellista (utan dubbletter, sorterad per grupp)
- [ ] **Vecka 6** – dokumentation, buffert, presentation

## Licens

MIT
