# Implementation – Hemuppgift 2, Del A

**Projekt:** [m3u-check](https://github.com/joeyvoong-a11y/m3u-check) · **Gren:** `refaktor-grund`
**Verktyg:** Claude Code i planeringsläget (`claude --permission-mode plan`). Varje filändring och varje kommando godkändes manuellt. Jag valde aldrig auto mode eller "don't ask again".

## Flöde

1. `/init` skapade `CLAUDE.md`. Jag rättade den innan den skrevs (se "Vad missade den?").
2. **Analys** i plan mode, med uttalat krav på "bara analys, ingen lösning".
3. **Plan** med kravet "Implementera ingenting. Jag vill se planen först." Utdata och exit-koder fick inte ändras.
4. **Granskning:** jag gav feedback med "Tell Claude what to change" och fick en reviderad plan.
5. **Implementation ett steg i taget.** Agenten stannade efter varje steg. Jag verifierade själv och committade själv.

## Vad identifierade agenten?

**Läsbarhet och teknisk skuld:**
- `Issue.level` var en fri sträng (`"error"`/`"warning"`), och `Issue` saknade stabil kod och kanalreferens. Testerna matchade därför på svensk text och skulle gå sönder om ett meddelande formulerades om.
- `run_checks` var en enda funktion med alla kontroller inline, vilket gör den svår att bygga ut.
- `cli.main` blandade utskrift, räkning och exit-kod. JSON/HTML-export (vecka 4) hade krävt att CLI:t skrevs om.
- Parsern använde anonyma tuplar (`pending`, `errors`), och meddelandet `"#EXTINF utan URL efter"` fanns på två ställen.
- Versionen fanns på två ställen (`pyproject.toml` och `__init__.py`), och CI körde bara Python 3.12 trots `requires-python >=3.10`.
- Testluckor: exit-kod 0 och 2, `--errors-only` och flera kantfall saknade tester.

**Befintliga buggar** (medvetet låsta med tester i stället för att rättas, eftersom de ändrar utdata):
- En fil med BOM hittar inte headern. *Under implementationen upptäckte agenten att det dessutom ger två fel på rad 1.*
- Kommatecken i ett attributvärde förstör kanalnamnet.
- En kanal utan namn ger meddelandet `'' saknar …`.
- `--errors-only` skriver alltid "0 varningar" i summeringen.

**Övrigt:** Agenten påpekade att PowerShells `>` skriver UTF-16, vilket påverkar jämförelsen mot `baseline.txt`. I steg 4 gjorde den på eget initiativ ett mutationstest: den flyttade en kontroll i minnet och bekräftade att golden-testerna då faller. Det bevisar att testerna faktiskt skyddar ordningen.

## Vad ville agenten göra som jag stoppade, och varför?

| Förslag | Beslut och motivering |
|---|---|
| **Steg 6: dokumentmodell för `--fix`** (fälten `duration`, `directives`, `url_line`, rå header) | **Struket.** Fälten skulle läggas till men inte användas av någon kod. Det är kod som skrivs i förväg för vecka 5, och den hör hemma tillsammans med `--fix`. |
| **Auto mode / "Yes, and don't ask again"** vid varje fråga | **Nekat varje gång.** Uppgiften är att styra agenten, inte låta den köra fritt. |
| **Commit och push** (agentens förslag i inmatningsraden) | **Gjort själv** efter min egen verifiering, så att varje commit är granskad av mig. |
| Steg 6–7 i den reviderade planen (version + CI-matris, uppdatera `CLAUDE.md`) | **Inte genomförda i den här omgången.** Jag höll omfattningen till det uppgiften krävde. *(Ändra den här raden om du gör dem.)* |

## Vad missade den?

- **Den virtuella miljön.** Första utkastet av `CLAUDE.md` och verifieringen använde `pytest` och `m3u-check` direkt, vilket inte fungerar här (Python i `C:\Python310` saknar skrivrättigheter). Jag fick lägga till `.venv\Scripts\python`.
- **Tom rad före `#EXTM3U`** ger felet "saknar header". Den fanns inte med i listan över kända fel förrän jag lade till den.
- **Verifieringen beskrev `baseline.txt` som UTF-16**, trots att jag redan hade gjort om den som UTF-8.
- **`python -m m3ucheck` fungerar inte**, eftersom `__main__.py` saknas. Man måste skriva `m3ucheck.cli`.
- **Exempelutdatan i README är hårdkodad** och blir fel så fort utdatan ändras.
- **`errors="replace"`** vid filinläsning döljer tyst teckenkodningsfel.
- Agenten försökte först köra ett skript via Git Bash, och sökvägen fungerade inte för Windows-Python. Den upptäckte och löste det själv.

## Implementerade steg

| Steg | Ändring | Commit | Tester | Utdata oförändrad |
|---|---|---|---|---|
| 1 | Golden-tester låser nuvarande beteende (11 fall) | `6c52151` | 18 ✅ | ✅ |
| 2 | `Level`-Enum, stabila koder och kanal på `Issue`; tester på kod i stället för text | `073f4fd` | 18 ✅ | ✅ |
| 3 | Typade parserfel (`ParseError`), duplicerad sträng borttagen | `987411a` | 19 ✅ | ✅ |
| 4 | `run_checks` uppdelad i `CHECKS`-lista, `find_duplicates` utbruten | `e8852aa` | 20 ✅ | ✅ |
| 5 | `report.py`: `Report` + `render_text`; `cli.main` från 13 till 4 rader | `5e0239f` | 21 ✅ | ✅ |

## Hur beteendet verifierades (efter varje steg, av mig själv)

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\python -m m3ucheck.cli examples/sample.m3u | Out-File -Encoding utf8 efter.txt
fc.exe baseline.txt efter.txt        # förväntat: "FC: no differences encountered"
```

`baseline.txt` togs innan något ändrades. Golden-testerna täcker det som baseline inte täcker: `--errors-only`, exit 0 och 2, samt kantfall. Agenten kontrollerade dessutom med `Get-FileHash` (byte-identisk), `Select-String` (att den duplicerade strängen var borta) och mutationstestet i steg 4.

## Är projektet körbart efter implementationen?

**Ja.** Alla 21 tester går igenom, CLI-utdatan är byte-identisk med före refaktoreringen, och exit-koderna 0, 1 och 2 fungerar. Det är testat lokalt på Python 3.10.1, och GitHub Actions kör testerna vid push.
