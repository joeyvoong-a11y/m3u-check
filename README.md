# m3u-check

[![tests](https://github.com/joeyvoong-a11y/m3u-check/actions/workflows/tests.yml/badge.svg)](https://github.com/joeyvoong-a11y/m3u-check/actions/workflows/tests.yml)
[![release](https://github.com/joeyvoong-a11y/m3u-check/actions/workflows/release.yml/badge.svg)](https://github.com/joeyvoong-a11y/m3u-check/actions/workflows/release.yml)
[![senaste version](https://img.shields.io/github/v/release/joeyvoong-a11y/m3u-check)](https://github.com/joeyvoong-a11y/m3u-check/releases/latest)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![licens: MIT](https://img.shields.io/badge/licens-MIT-green)](LICENSE)

Ett kommandoradsverktyg som hittar fel i IPTV-spellistor (M3U/M3U8) **innan** de laddas in i en spelare som [Hypnotix](https://github.com/linuxmint/hypnotix), VLC eller Kodi. Det kan också skriva ut en städad version av listan.

## Varför

IPTV-spellistor är ofta handskrivna, ihopklippta från flera källor eller exporterade av verktyg som inte följer formatet. En enda trasig rad kan få en spelare att hoppa över resten av listan, och det märks sällan förrän en kanal saknas. Spelarna säger sällan *vad* som är fel. m3u-check pekar ut raden och förklarar problemet på svenska.

## Funktioner

- **Kontrollerar** att `#EXTM3U`-headern finns, att varje `#EXTINF` har en URL, att URL:erna är giltiga, att kanalerna har namn, grupp, logga och `tvg-id`, och att inga strömmar förekommer två gånger.
- **Rapporterar** som text, JSON (för skript och CI) eller en fristående HTML-sida.
- **Städar** med `--fix`: dubbletter och ogiltiga URL:er tas bort och kanalerna sorteras per grupp. Övriga attribut och `#EXTVLCOPT` behålls oförändrade.
- **Tål verkliga filer**: BOM, Windows-1252-kodning, tomma rader och kommatecken i attributvärden.
- **Ger exit-koder** som går att använda i skript och pipelines.

### Vad kontrolleras

| Kontroll | Kod | Nivå |
|---|---|---|
| Filen är tom | `empty-file` | fel |
| Filen börjar inte med `#EXTM3U` | `missing-header` | fel |
| `#EXTINF` utan URL efter | `extinf-without-url` | fel |
| URL utan `#EXTINF` före | `url-without-extinf` | fel |
| Ogiltig URL-typ (bara http, https, rtmp, rtsp, udp och rtp godkänns) | `invalid-scheme`, `malformed-url` | fel |
| Spellistan innehåller inga kanaler | `no-channels` | varning |
| Kanalen saknar namn, `group-title`, `tvg-logo` eller `tvg-id` | `missing-name`, `missing-group`, `missing-logo`, `missing-tvg-id` | varning |
| Samma stream-URL förekommer flera gånger | `duplicate-url` | varning |

Koderna är stabila och finns med i JSON-rapporten, så skript kan filtrera på dem.

## Krav och externa beroenden

| Vad | Krävs för | Kommentar |
|---|---|---|
| Inget | det färdiga programmet (Windows, Linux, macOS) | Python finns inbyggt i programfilen. |
| Python 3.10 eller senare | installation med `pipx`/`pip` och utveckling | Bara standardbiblioteket används vid körning. |
| pytest | att köra testerna | Installeras med `pip install -e ".[dev]"`. |
| PyInstaller | att bygga programfilerna själv | Används bara i releasebygget (GitHub Actions). |

Verktyget anropar inga externa tjänster, API:er eller databaser. Det läser bara filen du anger och skriver bara dit du anger med `-o`.

## Installation

### Alternativ 1: Färdigt program (ingen Python behövs)

Ladda ner filen för ditt system från [Releases](https://github.com/joeyvoong-a11y/m3u-check/releases/latest):

| System | Fil |
|---|---|
| Windows | `m3u-check-windows.exe` |
| Linux | `m3u-check-linux`. Kör först `chmod +x m3u-check-linux`. |
| macOS | `m3u-check-macos`. Kör först `chmod +x m3u-check-macos`. |

På macOS kan Gatekeeper blockera programmet eftersom det inte är signerat. Högerklicka och välj *Öppna*, eller kör `xattr -d com.apple.quarantine m3u-check-macos`.

### Alternativ 2: Med Python

```bash
pipx install git+https://github.com/joeyvoong-a11y/m3u-check
```

`pipx` installerar verktyget isolerat och lägger kommandot `m3u-check` i PATH. Utan pipx fungerar `pip install git+https://github.com/joeyvoong-a11y/m3u-check`.

### Alternativ 3: Från källkoden

```bash
git clone https://github.com/joeyvoong-a11y/m3u-check
cd m3u-check
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Användning

```bash
m3u-check min-spellista.m3u
```

Exempel med [`examples/sample.m3u`](examples/sample.m3u):

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

### Vanliga kommandon

```bash
m3u-check lista.m3u --errors-only                    # bara fel, inga varningar
m3u-check lista.m3u --format html -o rapport.html    # rapport att dela
m3u-check lista.m3u --format json                    # för skript, t.ex. med jq
m3u-check lista.m3u --fix -o städad.m3u              # städad spellista
python -m m3ucheck lista.m3u                         # utan installerat kommando
```

### Flaggor

| Flagga | Vad den gör |
|---|---|
| `--errors-only` | Visa bara fel. Summeringen räknar ändå alla varningar. |
| `--format text\|json\|html` | Rapportens format. Standard är `text`. |
| `--fix` | Skriv ut en städad spellista i stället för en rapport. Kan inte kombineras med `--format` eller `--errors-only`. |
| `-o FIL`, `--output FIL` | Skriv till en fil (UTF-8) i stället för till skärmen. Vägrar skriva en rapport över själva spellistan. |
| `--version` | Visa versionen. |
| `-h`, `--help` | Visa hjälpen. |

### Exit-koder

| Kod | Betydelse |
|---|---|
| `0` | Inga fel (varningar räknas inte), eller `--fix` klar. |
| `1` | Minst ett fel i spellistan. |
| `2` | Filen kunde inte läsas eller skrivas, eller ogiltiga flaggor. |

Det gör det enkelt att stoppa en pipeline vid trasiga listor:

```bash
m3u-check lista.m3u --errors-only || echo "Spellistan har fel"
```

## Konfiguration

m3u-check har ingen konfigurationsfil och läser inga miljövariabler. Allt styrs med flaggorna ovan. Några beteenden är bra att känna till:

- **Teckenkodning:** filen läses som UTF-8, med eller utan BOM. Om det inte går läses den som Windows-1252, och en varning skrivs till stderr.
- **Utdata** är alltid UTF-8, även i en pipe och i Windows-programmet. Använd `-o` i stället för `>` i PowerShell, eftersom `>` där kan skriva filen som UTF-16.
- **Godkända URL-typer** (`http`, `https`, `rtmp`, `rtsp`, `udp`, `rtp`) är fasta i `VALID_SCHEMES` i [`checks.py`](src/m3ucheck/checks.py). Ändra där om du behöver fler.
- **Sammanfattningen** från `--fix` skrivs till stderr, så stdout innehåller bara spellistan och kan skickas vidare med en pipe.

## Utveckling

```bash
pytest                       # alla tester
pytest tests/test_golden.py  # bara golden-testerna (låser exakt utdata)
```

CI kör testerna på Python 3.10 och 3.13, på både Ubuntu och Windows, vid varje push och pull request. Arkitekturprinciperna (P1–P9) och övriga konventioner står i [`CLAUDE.md`](CLAUDE.md).

```
src/m3ucheck/
  parser.py   # läser M3U till Channel-objekt (ingen I/O)
  checks.py   # en funktion per kontroll, registrerade i CHECKS
  report.py   # rapporten som text, JSON eller HTML
  fix.py      # --fix: städad spellista
  cli.py      # kommandoraden: filer, flaggor, exit-koder
tests/        # pytest, inklusive golden-tester och processtester
examples/     # exempelspellista
packaging/    # startskript för PyInstaller-bygget
docs/         # kursdokumentation (felsökning, polering)
```

### Släppa en ny version

1. Höj `__version__` i `src/m3ucheck/__init__.py` och committa.
2. Tagga och pusha: `git tag v0.2.0 && git push origin v0.2.0`

[`release.yml`](.github/workflows/release.yml) kontrollerar att taggen matchar `__version__`, kör testerna, bygger programmen för Windows, Linux och macOS, provkör dem och lägger upp dem på en ny release.

## Hur projektet byggdes

m3u-check är ett kursprojekt (6 veckor) som byggts med agentdriven utveckling i [Claude Code](https://claude.com/claude-code). Jag skrev specifikationer och arkitekturprinciper ([`CLAUDE.md`](CLAUDE.md)), lät agenten planera och implementera, och granskade varje steg innan det committades. Processen finns dokumenterad i [`implementation.md`](implementation.md), [`docs/hemuppgift3-felsokning.md`](docs/hemuppgift3-felsokning.md) och [`docs/hemuppgift4-polering.md`](docs/hemuppgift4-polering.md).

### Plan

- [x] **Vecka 1** – repo, struktur, parser, grundkontroller, tester, CI
- [x] **Vecka 2** – kontroll av `tvg-id`, rättade buggar (BOM, kommatecken i attribut, kanal utan namn, tom rad före header), åäö i utskrifter
- [ ] **Vecka 3** – `--online`: testa om strömmarna svarar. *Bortprioriterad, eftersom nätverk gör demo och tester opålitliga.*
- [x] **Vecka 4** – export av rapporten som JSON och HTML
- [x] **Vecka 5** – `--fix`: städad spellista utan dubbletter, sorterad per grupp
- [ ] **Vecka 6** – dokumentation, buffert, presentation

## Licens

[MIT](LICENSE)
