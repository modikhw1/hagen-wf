---
id: 0042
titel: Signaturerna i rörelse: marginal, överlapp och uppmärksamhet mot fart
status: redo
från: orkestratorn (Opus 5.5), efter ägarens utmaning 14 nov
datum: 2026-11-14
följer: –
tillåten_skrivning: [byggsten/hjarna/prov/0042/]
---

**Läs först:** `byggsten/hjarna/UTMANING.md` (P2, P4, A11, S6) och ägarens minne om rörlighet som iscensättning (`karta/videoforandring/README.md`, `kalibrering.md`).

## Varför
Avsiktsriggen säger att ett tillstånd som stress inte syns som fart. Det syns som tre mönster i hur kroppen löser uppgiften:
- **Marginalen krymper:** genar, sätter ned foten utan att titta, håller litet avstånd till hinder.
- **Handlingar överlappar:** handen sträcks mot målet innan kroppen är framme.
- **Uppmärksamheten smalnar:** blicken stannar på målet och sveper inte runt i rummet.

Ägaren har sagt samma sak om rörlighet (iscensättning, inte skak). Om signaturerna går att mäta i våra egna rörelser och inte bara följer farten, får hjärnan ett språk mellan sinne och kropp som inte är etiketter. Annars är P4 och S6 bara ord.

## Att göra
1. **Underlag:**
   - MHR-sekvenserna i `scen/3d/kroppsbank/` och `scen/3d/ingest/ut/*/S*/sekvens_*.npz` för notan, b-tilltal, guacamole, sketch och gelato.
   - Bryggans paket (`byggsten/brygga/ut/notan/paket.json`, ledsetet `t1` med huvudrotation).
   - Läs kropparna i världen med kedjans `kontrakt/trohet.ruta()` eller bryggans `samla.py`.
2. **Definiera och räkna, per person och tagning:**
   - **Fart:** rotens och handledernas fart, och rörelseenergi.
   - **Marginal:** minsta avstånd från händer och fötter till möblernas lådor; fotens placering mot huvudets riktning (sätts foten ned där blicken inte är?).
   - **Överlapp:** tid mellan att handen börjar röra sig mot ett mål och att roten stannar. Mål ur liggarens händelser där de finns.
   - **Uppmärksamhet:** spridning i huvudets riktning (MHR:s huvudrotation, framåtaxeln), och andelen tid med blicken mot kameran.
3. **Pröva:** är marginal, överlapp och uppmärksamhet korrelerade med fart (rho), eller bär de egen information? Rangordna tagningarna på var och en och visa de tre som ligger högst och lägst på varje mått, med en remsa per tagning.
4. **Lås före jämförelsen** en prognos över vilka tagningar ägaren skulle kalla "stressade, ivriga" mot "lugna" (`prognos.json`). Lägg remsorna som ett blint underlag för ägaren i `byggsten/hjarna/prov/0042/agare/`. Fråga inte ägaren själv. Orkestratorn för underlaget vidare.

## Gränser
- Inga modellanrop. Bara befintliga sekvenser och kedjans läsfunktioner.
- Rör inte `scen/`, `forvarld/`, `app/` eller `video/`.

## Klart när
- Måtten är definierade (formel, enhet, leder) och räknade för alla tagningar som har kropp.
- Korrelationstabellen mot fart finns.
- Remsorna och den låsta prognosen finns.
- En bedömning i högst sex rader: finns signaturerna i vårt material, och bär de något som farten inte bär?

## Leveransform
`delegat/svar/0042-signaturerna-i-rorelse.md`, högst cirka 50 rader.
