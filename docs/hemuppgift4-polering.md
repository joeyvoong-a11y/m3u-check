# Hemuppgift 4, steg 3 – Polering

**Gren:** `hemuppgift4-implementation`. Agenten fick prompten från uppgiften och gick igenom alla moduler. Den testade också misstankarna mot det riktiga programmet (tom fil, mapp, Latin-1-fil, `-o` till indatafilen, stängd pipe) innan den listade dem. Radnumren gäller koden efter åtgärderna.

## Fynd

✅ = åtgärdat i den här omgången, ⏸ = medvetet inte åtgärdat (skäl i tabellen).

### 1. Felhantering för externa anrop (här: fil-I/O, inget nätverk eller databas)

| | Fil:rad | Fynd | Åtgärd |
|---|---|---|---|
| ✅ | `cli.py:112` | **`-o` med samma fil som indata skrev över spellistan med rapporten.** Testat: `sample.m3u` förstördes. Dataförlust. | CLI:t vägrar med exit 2 om `-o` pekar på indatafilen. `--fix -o samma.m3u` är tillåtet, eftersom det är en avsiktlig städning på plats. |
| ✅ | `cli.py:74` | Stängd pipe (`m3u-check lista.m3u \| head`) gav `Exception ignored … OSError` och exit 120. | `_print_stdout` fångar `BrokenPipeError`/`OSError` och leder om stdout till devnull. Exit-koden blir som vanligt. |
| ⏸ | `cli.py:120` | Hela filen läses in i minnet. | Ingen åtgärd. Spellistor är sällan större än några MB, och parsern behöver ändå alla rader. |

### 2. Otydliga felmeddelanden

| | Fil:rad | Fynd | Åtgärd |
|---|---|---|---|
| ✅ | `cli.py:41` | `Kunde inte läsa filen: [Errno 2] No such file or directory: '…'` blandade svenska och engelska och visade Python-intern text. En mapp gav `[Errno 13] Permission denied`, vilket är missvisande. | `_describe_os_error` ger svenska skäl: "filen eller mappen finns inte", "det är en mapp" och "åtkomst nekad (är det en mapp …?)". Sökvägen står först. Samma sak gäller skrivfel. |
| ✅ | `checks.py:43` | En tom fil gav "Filen börjar inte med #EXTM3U". Det är sant men hjälper inte. | Nytt fel `empty-file`: "Filen är tom". |
| ✅ | `cli.py:111` | `--fix --format json` och `--fix --errors-only` ignorerade de andra flaggorna utan att säga något. | `argparse`-fel med en förklaring (exit 2). |

### 3. Edge cases

| | Fil:rad | Fynd | Åtgärd |
|---|---|---|---|
| ✅ | `cli.py:53` | **En fil som inte är UTF-8 (vanligt för Latin-1/Windows-1252-listor) gick igenom tyst.** `errors="replace"` gjorde `ÅÄÖ` till `���`, och rapporten sa "0 fel". | Strikt UTF-8 först. Annars läses filen som cp1252, med en varning på stderr som anger bytepositionen. |
| ✅ | `checks.py:48` | En spellista med bara `#EXTM3U` gav "0 kanaler, 0 fel, 0 varningar" och exit 0, som om allt var bra. | Ny varning `no-channels`. Den ges inte när ett annat fel redan förklarar det, t.ex. `#EXTINF` utan URL. |
| ⏸ | `parser.py:74` | Ett ensamt `"` i en `#EXTINF`-rad gör att resten av raden räknas som citat, så kanalen blir namnlös. | Ingen åtgärd. Det ger varningen "Kanalen saknar namn", vilket är rimligt för en trasig rad. |
| ⏸ | `checks.py:36` | Dubbletter jämförs exakt: `http://a/x` och `http://A/x/` räknas som olika. | Ingen åtgärd. Att normalisera URL:er kan ge falska dubbletter (sökvägar är skiftlägeskänsliga). |

### 4. Dokumentation i komplex kod

| | Fil:rad | Fynd | Åtgärd |
|---|---|---|---|
| ✅ | `fix.py:27` | Det var oklart varför `id(ch)` användes i stället för kanalerna själva. | Kommentar: två kanaler kan ha identiskt innehåll men vara olika rader. |
| ✅ | `cli.py:16` | Exit-koderna `0/1/2` var magiska tal på flera ställen, och `--help` nämnde dem inte. | Konstanterna `EXIT_OK`, `EXIT_ERRORS` och `EXIT_IO` med kommentarer. Exit-koderna står nu i `--help` (epilog). |
| ⏸ | `parser.py:9` | `ATTR_RE` har redan en kommentar om lookbehinden (ReDoS-fixen). | Räcker. |

### 5. Hårdkodade värden

| | Fil:rad | Fynd | Åtgärd |
|---|---|---|---|
| ✅ | `cli.py:22` | Reservkodningen behövdes i fynd 3. | Konstanten `FALLBACK_ENCODING`, med en kommentar om varför just cp1252. |
| ⏸ | `checks.py:13` | `VALID_SCHEMES` går inte att ändra från kommandoraden. | Ingen åtgärd ännu. Ingen användare har bett om det, och en flagga måste föras genom `run_checks` (P2). Det är en kandidat till `--allow-scheme`. |
| ⏸ | `report.py:82` | Färgerna i HTML-rapporten är hårdkodade. | Ingen åtgärd. Det är presentation och hör hemma i `report.py` (P6). |

### 6. Egna preferenser

| | Fil:rad | Fynd | Åtgärd |
|---|---|---|---|
| ✅ | `.github/workflows/tests.yml` | CI körde bara Python 3.12 på Linux, fast `requires-python = ">=3.10"` och `cli.py` har Windows-specifik kod (UTF-8, `PermissionError` för mappar). | Testmatris: Python 3.10 och 3.13 × Ubuntu och Windows. |
| ⏸ | `release.yml:29` | Releasebygget använder bara 3.12. | Räcker. Exe-filen har sin egen tolk, så användarens Python spelar ingen roll. |

## Verifiering

- **Tester:** alla 49 går igenom. Den nya filen `tests/test_polish.py` har ett test per åtgärdat fynd.
- **Mutationstest av pipetestet:** med den gamla `print` faller testet, och med `_print_stdout` går det igenom.
- **Golden-testet `test_missing_file`:** uppdaterat (P8), eftersom felmeddelandet har ändrats medvetet.
- **Manuell kontroll:** alla fall ovan kördes igen mot det riktiga CLI:t efter åtgärderna.
