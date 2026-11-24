---
id: 0003
status: klart
av: uppdragstagaren (Claude-appen, Sonnet 5.5)
datum: 2026-11-12
---

## Resultat
Plankartan (arm A) fungerar som hypotesgenerator, rutnätet i bilden (arm B) fungerar inte som granskare. Gemini identifierar rätt kamerapil i 51 av 52 tolkbara svar (3 av 55 kunde inte tolkas) och placerar bord och våg inom 0,3–0,7 m från planen. När den får ett projicerat rutnät i bilden läser den däremot koordinater sämre (spridning 0,8–1,1 m) och säger "förskjutet" också i tagningar där kameran inte pekats ut som fel. Allt är Geminis hypotes, och inget skrevs till någon deklaration.

Ägaren bekräftade de nya reglerna i min chatt, och nätanropen kördes mot gatewayen med `google/gemini-2.5-flash`, fem körningar per tagning och arm (11 tagningar). Nyckeln lästes via `AI_GATEWAY_NYCKELFIL` och skrevs aldrig ut.

### Utan anrop: kontroll att rutnätet projiceras rätt
Golvpunkten vid personplatsen projicerad genom den lösta kameran jämfört med ingestens ankelleder (MHR70 13/14), `kontroll_projektion.json`: 9 av 11 tagningar inom 0,01–0,15 m (10–106 px), **S5 0,24 m och S9 0,33 m** (294 px). Ankelleden ligger utanför bild i alla tagningar (extrapolerade av kroppsmodellen), så kontrollen visar konsistens med samma lösning och inte ett oberoende sanningsvärde. Rutnätet ser rätt ut i S6: bordsytans rutnät hamnar där bordskanten syns i nyckelbilden.

### Efter anrop (`summering.md`)
| | arm A plankarta | arm B rutnät |
|---|---|---|
| anrop, kostnad | 55, 0,032 USD | 55, 0,028 USD |
| rätt kamerapil | 51/52 tolkbara (S1 4/5) | – |
| pilens riktning stämmer | 100 % | – |
| bord, framkant: spridning mellan körningar (median över tagningar) | **0,28 m** | 0,78 m |
| bord: avstånd till dagens lösta läge | 0,43 m | 0,62 m |
| våg: spridning | **0,15 m** | 1,08 m |
| våg: avstånd till dagens läge | 0,68 m | 0,57 m |
| fötter: spridning / avstånd | – | 0,35 / 1,04 m |
| rutnätet "rätt" (`yes`/`aligned`) i | – | 0–60 % per tagning |

Bredvid fri `scen3d`-utdata ur PIPE: 75–108 px median i x och upp till 1 375 px när kameran pekade fel. Tal i px och m går inte att jämföra rakt av (meterrättningen beror på djupet), men spridningen i arm A är liten.

Per tagning (arm A, bordets framkant): närmast planen S5 och S8 (0,08 m), S9 (0,23 m) och S2 (0,33 m). S5 har dock stor spridning (0,83 m). Sämst S1, S3 och S4: 0,66–1,21 m ifrån. **Vågen "hittas" också i S3 och S4**, där den inte syns (2,5–2,8 m från planen). Modellen hittar på i stället för att svara null.

Arm B, rutnätets passning enligt modellen (`yes`/`shifted`/`unclear`):
- Kameror som 0001 pekade ut: **S9 0/5 rätt (5/5 förskjutet)** och S6 0/5 rätt. Det stämmer med 0001. **S5 2/5 rätt, S8 3/5 rätt**, alltså inte utpekade.
- Men också S1 (0/5), S2 (0/5), S3 (0/2) och S7 (0/5) bedöms förskjutna. S1–S4 har bara rosa kakel att bedöma golvet mot, och SIFT bekräftade deras kameror. Granskaren skiljer alltså inte rätt från fel.

Tänkandevariant (budget 1 024 tokens, S6, S10, S11, 3 körningar): arm A något bättre (bord 0,22 m, våg 0,10 m spridning; avstånd 0,37/0,30 m), arm B sämre (bord 1,18 m, våg 0,79 m; avstånd 1,74/1,16 m). Litet underlag.

## Bedömning (högst fem rader)
1. **Arm A kan bli ett steg före lösaren**: för kamerapil och riktning (tillförlitlig) och för grov placering. Behåll bara avläsningar med spridning under cirka 0,3 m och be modellen svara `null` för det som inte syns (vågen i S3/S4).
2. **Arm B ska inte vara granskare** (för många falska "förskjutet"). Rutnätet i bilden är däremot bra för ägarens ögon: gör det som bildlager efter lösaren.
3. Placeringen kräver fortfarande en geometrisk kontroll efteråt (se 0008), eftersom avståndet till planen är 0,4–0,7 m.

## Ändrade eller nya filer
`scen/3d/ingest/ramprov/`: `ram.py` (kartor, rutnät, kontroll, anrop), `summera.py`, `bilder/` (`A_karta.png`, `B_S1..S11.jpg`, nyckelbilder), `svar/` (råsvar, loggar, `forsok1_*` för det misslyckade första försöket), `summering.md/json`, `summering_tanke.md/json`, `kontroll_projektion.json`.

## Kontroll mot "Klart när"
- [x] Exempelbilder: plankarta och rutnätsbilder för alla tagningar (minst S6, S10, S11).
- [x] Egen kontroll av projektionen utan anrop (ovan).
- [x] Per arm: spridning och avstånd till lösta läget för bord och våg. `disk_A` jämförs bara för S1–S4 (framkant), och modellen gav då 0,33–1,21 m.
- [x] Arm B: hittar den samma avvikande tagningar? Ja för S9 och S6, men den flaggar också rätta tagningar.
- [x] Bedömning i högst fem rader.

## Avvikelser
- **Kostnad:** 0,444 USD totalt av taket 0,60. Det första försöket (0,337 USD) gav tomma svar, eftersom modellens tänkande åt upp `max_tokens`. Jag körde om med tänkandebudget 0 (0,060 USD) och gjorde därefter tänkandevarianten (0,048 USD). Det första försökets rådata ligger kvar som `svar/forsok1_*`.
- Arm A visar inte möbler, våg och köttbit på kartan (det är dem modellen ska placera). "Avstånd till dagens läge" gäller bordets framkant (`disk_A` för S1–S4, `disk_C` för S5–S11) och vågens mittpunkt. Dagens läge är självt en uppskattning och inte facit.
- Modellen svarade `aligned` i stället för `yes` i några körningar. Båda räknas som "rätt".
