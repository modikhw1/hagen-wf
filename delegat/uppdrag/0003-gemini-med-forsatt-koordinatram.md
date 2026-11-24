---
id: 0003
titel: Prov: Gemini läser läge i en försatt koordinatram (rutnät i bilden) i stället för att hitta på geometri
status: redo
från: orkestratorn (Fable, ägarens session 12 nov kväll)
datum: 2026-11-12
följer:
tillåten_skrivning: [scen/3d/ingest/ramprov/]
---

## Mål
Det ska vara känt om Gemini placerar kameror, möbler och föremål bättre när rummet redan är satt i koordinater och visas i bilden, än när modellen får hitta på geometrin fritt. Idén är ägarens: sätt rummet i rymden först, och fråga sedan modellen hur det ser ut, var kameran står och vad som går att sluta sig till om miljön.

## Bakgrund
Läs `scen/3d/PIPE.md`, Öppet punkt 6, särskilt stycket om varianten `scen3d` och stycket "Bildrutor provade". Det som är känt:
- Fri 3D-utdata från Gemini (`rum_video.py --variant scen3d`) gav 75–108 px medianfel i x och upp till 1 375 px när kameran pekade fel. Geometrin bärs av lösaren, inte av modellen.
- Gemini är däremot stabil på semantik och topologi, och ger användbara 2D-rutor.
- Kvar att lösa: var möbler står när golvkontakten inte syns, var föremål står på en möbel, och avståndet mellan rummets delar.

Hypotesen är att modellen är bättre på att läsa av ett rutnät den ser än på att uppfinna koordinater. Två armar provas på `b-tilltal-ravara`.

**Arm A, plankarta.** Rita konsensusdeklarationens rum uppifrån som en bild: rutnät i meter med axeletiketter, platserna A/B/C, möbler med id, och de lösta kamerorna som numrerade pilar. Ge Gemini kartan och en nyckelbild per tagning. Fråga per tagning: vilken pil är den här kameran, stämmer dess riktning, och var på kartan (x, y) står det som syns i bild men saknas på kartan.

**Arm B, golvrutnät i originalbilden.** Projicera ett golvrutnät (0,5 m, med koordinatetiketter) och diskens ovansida som ett andra rutnät in i originalets nyckelbild genom tagningens lösta kamera. Fråga Gemini: på vilken rutnätskoordinat står diskens framkant, vågen, köttbiten och personens fötter; och ser rutnätet ut att ligga rätt på golvet eller är det förskjutet eller lutat, och åt vilket håll.

Arm B gör dessutom modellen till granskare av kameralösningen, vilket inte finns i dag.

## Underlag
- Konsensusdeklaration och uppsättning: `scen/3d/ingest/ut/b-tilltal-ravara-tagningar/brief/` (`uppsattning3/deklaration_n06_detekterad.json` är senast)
- Lösta kameror och planer: `scen/3d/kontrakt/ut/b-tilltal-ravara_n06-mobel2/`, kameran kommer ur `scen/3d/kontrakt/bildkamera.py`
- Anrop, schema och reparationsvarv att efterlikna: `scen/3d/ingest/rum_video.py`. Mätning genom projektion: `scen/3d/ingest/rum_video_mat.py`. Konsensus: `scen/3d/ingest/rum_konsensus.py`.
- Jämförelsetal: `kvalitet.foremal_lyft` och `kvalitet.mobel_lyft` i planen, samt facit v0.3 i `ingest/ut/b-tilltal-ravara-tagningar/plats/deklaration.json`.

## Gränser
- Bara nya filer i `tillåten_skrivning`. Importera gärna befintliga moduler, men ändra dem inte.
- **Nätverksanropen kräver ägarens godkännande enligt `REGLER.md`.** Bygg först allt som går utan anrop (kartan, rutnätsbilderna, prompterna, schemat, mätskriptet) och visa ett exempel av varje bild. Sätt sedan status `blockerat` med frågan "får jag köra N anrop mot gatewayen för högst X dollar", om ägaren inte redan har godkänt det i din session.
- Kostnadstak när det är godkänt: 0,60 dollar totalt (krediten är 2,07 dollar). Modell `google/gemini-2.5-flash`. Fem körningar per arm.
- Nyckeln läses via miljövariabeln `AI_GATEWAY_NYCKELFIL`. Skriv aldrig ut den, och lägg den inte i någon fil.
- Geminis svar är hypotes. Inget svar skrivs in i någon deklaration i det här uppdraget.

## Klart när
- Exempelbilder finns: en plankarta, och en rutnätsbild för minst tagningarna S6, S10 och S11.
- Utan anrop: en egen kontroll av att rutnätet projiceras rätt (golvpunkter vid personens fötter hamnar där ingestens fotleder ligger).
- Efter godkända anrop, per arm: spridning mellan de fem körningarna (meter) och avstånd till dagens lösta läge för `disk_A`, `disk_C` och vågen, bredvid motsvarande tal för fri `scen3d`-utdata ur PIPE.
- Arm B: vad modellen säger om rutnätets passning i de tagningar där 0001 eller loggen pekar ut kameran som avvikande (S5 har en misstänkt läsning på 3,67 m, S6 och S8 har stora boxresidualer). Hittar den samma tagningar?
- En bedömning i högst fem rader: ska en försatt ram bli ett steg i kedjan, i vilken arm, och var (före lösaren, eller efter som granskning).

## Leveransform
`delegat/svar/0003-gemini-med-forsatt-koordinatram.md` enligt mallen, högst cirka 80 rader. Skript, bilder och råsvar i `scen/3d/ingest/ramprov/`.
