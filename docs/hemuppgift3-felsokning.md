# Hemuppgift 3, del A – Felsökning: "Kunde inte l�sa filen"

## Problemet
När jag hade paketerat m3u-check som en fristående exe med PyInstaller och körde den mot en fil som inte finns, blev felmeddelandet `Kunde inte l�sa filen: [Errno 2] …`. "ä" i "läsa" visades som `�`. Exit-koden (2) och resten av texten var rätt.

## Hur jag beskrev det för agenten
Jag berättade vad som hade ändrats (exe-paketering samma dag), var det kördes (Git Bash, Windows 11), den exakta utskriften, att stdout "såg rätt ut" och att jag inte hade testat `python -m` eller PowerShell. Agenten påpekade direkt två svagheter i min beskrivning. Stdout såg bara rätt ut för att den utskriften råkade vara ren ASCII. Felet syntes heller inte i ett konsolfönster utan i fångad utdata via en pipe.

## Agentens hypoteser
1. **Kodning vid pipe:** Python skriver stderr som cp1252 när utdatan går till en pipe i stället för en konsol, och mottagaren läser bytes som UTF-8.
2. **Exe-specifikt:** PyInstallers inbäddade tolk väljer annan kodning än vanlig Python, så paketeringen har infört felet.
3. **Trasig sträng:** "ä" är sparat med fel kodning i `cli.py` och är fel redan innan det skrivs ut.

## Vilken jag valde och varför
Jag valde **hypotes 2**, fast agenten rankade den som nummer två. Felet syntes precis efter exe-paketeringen, och hypotesen kan avgöras med ett enda jämförande test: samma kommando med `python -m m3ucheck.cli` och med exe-filen.

## Vad som faktiskt var fel
- Båda varianterna skrev exakt samma byte, `0xE4` (cp1252), i stället för UTF-8 `0xC3 0xA4`. **Hypotes 2 föll.** Felet fanns redan före exe-filen.
- `sys.stderr.encoding` var `cp1252` vid pipe. Med `PYTHONUTF8=1` blev `python -m` rätt. **Hypotes 1 bekräftades.**
- Källfilen innehöll korrekt UTF-8. **Hypotes 3 föll.**
- Felet är större än jag trodde: **stdout** går också sönder (`Filen b�rjar inte med #EXTM3U`), och även kanalnamn med åäö påverkas.
- Testsviten kunde aldrig hitta felet. Den använder `capsys`, som fångar text i minnet utan att koda den till bytes.

## Vad agenten fick rätt och vad den missade
**Rätt:** Rätt rotorsak låg överst. Agenten såg att "stdout ser rätt ut" inte bevisade något och kopplade felet till fler meddelanden med åäö. Den förklarade också varför testerna inte fångade felet och gav verifieringssteg som gick att köra direkt.

**Vilseledande eller missat:** Agenten var osäker på hur PyInstaller hanterar miljövariabler och sa det öppet. Testet visade att exe-filen **ignorerar** `PYTHONUTF8=1`, medan `python -m` respekterar den. Hypotes 2 var alltså fel som rotorsak men pekade på en verklig skillnad: en fix via miljövariabel fungerar inte för exe-filen. Fixen måste ligga i koden, till exempel `sys.stdout.reconfigure(encoding="utf-8")` i `cli.main()`. Agenten hade dessutom själv sett felet i en tidigare del av samma session, vilket gör analysen mindre "blind" än den ser ut.

**Inte verifierat:** beteendet i ett riktigt PowerShell- eller cmd-fönster utan pipe.

## Lärdom
Den mest misstänkta ändringen (exe-paketeringen) var inte orsaken, bara när felet blev synligt. Ett billigt jämförande test som kunde fälla en hypotes var värt mer än att lita på rangordningen.
