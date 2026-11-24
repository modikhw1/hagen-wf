---
id: 0031
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
**1. Låna.** [LANA.md](../../forvarld/liggare/LANA.md) beskriver var delarna kommer ifrån:
- The Sims (affordanser i föremålen)
- Smart Objects (platser och roller)
- GOAP, STRIPS och HTN (förvillkor, effekt och förlopp)
- FrameNet Giving (rollförrådet)
- motion warping och IK (nivå 1)
- MotionFix (nivå 2): data under CC BY 4.0, men kodens licens framgår inte och kroppen är SMPL, så den är inte mogen för produkten

**2. Schemat.** [liggare.schema.json](../../scen/3d/kontrakt/liggare.schema.json) har sex delar:
- entiteter med affordanser
- starttillstånd i predikat
- händelser (ram, roller, förvillkor, effekt)
- förlopp
- mening (bär, tillfälligt, ramar)
- frihetsgrader (domän, nivå, spridning, text till Jev, regi-mall)

**3. Gelatos liggare.** [liggare_0031.json](../../scen/3d/kontrakt/ut/kand-kennysgelato_n06-hand/liggare_0031.json) är skriven av mig som stark modell, enligt [prompten](../../forvarld/liggare/prompt_liggare.md). Prompten går att köra via API med `kor_liggare.py`.
- **Innehåll:** 17 entiteter. Glassprovet, tråget och kundsidan är egna entiteter, och varje hand är en egen. Dessutom 9 händelser, 2 förlopp (`f_servera` = luta, skopa, räta på sig, vända sig, räcka fram, ge; `f_egen`) och 13 frihetsgrader, varav tre utan regi: kundens hand, ett leende och en annan lokal.
- **Kontrollen** (`liggare_kontroll.py`) ger schema ok, 0 faktafel, 0 luckor, full täckning och 21 rader i Jev-ytan.
- **Källan:** `kalla_0031.json` (revision 7) pekar på liggaren och kontrollen.

| | Stark (jag) | Flash (78 s, 0,053 USD) |
|---|---|---|
| händelser och förlopp | 9 och 2 | 11 och 2, rimliga, men hittar på detaljer i S2 (vänster hand tar skopan) |
| schema | ok | bryts: ett negerat faktum `!i_hand(…)` |
| kontroll (efter att negationen strukits) | 0 luckor | 4 luckor (skeden aldrig tom i starten), 7 faktafel (egna rollnamn) |
| frihetsgrader | 13, regi-mallar som går att köra | 3, med regi i fel form, `antal` på en operation som inte finns |

**Flash räcker inte ensam.** Den ger rätt form på händelser och förlopp, men inte de lagliga ändringarna, som är det Jev behöver. Med kontrollen och ett nytt försök kan den bli ett första utkast.

**4. "Gör att kvinnan ger glassen med andra handen".**
- **Jev:** `fg_hand=vanster` i 5 av 5 körningar.
- **Spridningen,** ur liggaren mekaniskt: händelserna e2 (skopa), e5 (räcka fram) och e6 (ge); `i_hand(A_hand_h,sked) → i_hand(A_hand_v,sked)`; skedens fäste r_wrist → l_wrist.
- **Nivå 1:** den nya operationen `satt_frihetsgrad` speglar armarna över kroppens mittplan i S1. Rotationen blir −H·R; viloposen visar att MHR:s vänster- och högerben har axlar R_v = −H0·R_h, och konjugering gav vridna armar. Skeden flyttas till vänster handled, och planen märks `utförd_niva_1`. IK görs efter bygget mot högerhandens bana (`gennedbrytning/s_ik_blender.py`).
- **Film:** [andra_handen.mp4](../../forvarld/gelato/ut_0031/andra_handen.mp4), med original, före och efter, och remsan.
- **Rakt: det ser fel ut i räcka fram.**
  - I h3 når vänster hand ned i tråget, och det fungerar.
  - I h6–h8 viks vänster arm uppåt och bakåt i stället för att sträckas fram mot kunden, och skeden hamnar vid axeln.
  - Höger axel deformeras i hela scenen.
  - Speglingens plan och IK:s mål (högerhandens bana tvärs över kroppen) räcker inte. Armen behöver ett eget mål på vänster sida av kroppen, och de vridande lederna (`*_twist`) bör inte speglas som vanliga leder.
- **Nivå 3:** [vanster_hand/](../../scen/3d/gennedbrytning/d_video/dreamina-paket/vanster_hand/LAS-MIG.md) innehåller prompt, referensvideo och `svar/`. Kedjan tar vid när ägaren har kört Dreamina.

**5. Elva meningar × fem körningar** (`forvarld/gelato/ut_0031/`). "Med" är liggarens yta. "Utan" är 0029:s tillstånd med handlingsspår och relevans.

| # | Mening | Med liggare | Bild | Utan (0029-vägen) |
|---|---|---|---|---|
| 1 | Hoppa över skopandet | `fg_skopa_finns=nej` 5/5 | plan ✔ (varning: bär) | ta bort h3, 5/5 |
| 2 | Skopandet långsammare | `fg_tempo_skopa=2` 5/5 | plan ✔ | tempo h3, 5/5 |
| 3 | Två smakprov | `fg_antal=2` 5/5 | plan ✔, **h3–h8 som förlopp** | upprepa bara h8, 5/5 |
| 4 | Kaka i stället för glass | `fg_prov_sak=kaka` 5/5 | plan ✔ | **föremålet saknas**, 3/5 (två olika svar) |
| 5 | Ta bort disken | `fg_disk=nej` 5/5 | plan ✔ (varning: ramar) | samma, 5/5 |
| 6 | Stabilisera kameran | `fg_kamera=stilla` 5/5 | plan ✔, **s1** | stativ i **s2** (fel scen), 5/5 |
| 7 | En sekund längre | `fg_langd_slut=1` 5/5 | plan ✔ | samma, 5/5 |
| 8 | Hon ler efter | `fg_uttryck_efter=ler` 5/5, ingen regi | långsam väg: nej (mimik, generering) | ingen väg |
| 9 | Kunden med andra handen | `fg_kund_hand=vanster` 5/5, ingen regi | långsam väg: nej (kunden är platshållare) | **tar bort h8**, 5/5 |
| 10 | Foodtruck och stå still | `ingen_passar` 5/5 | långsam väg: nej (ingen mall, ingen rörelse) | glass_disk, avvisad |
| 11 | Andra handen | `fg_hand=vanster` 5/5 | **film**, nivå 1 (se ovan) | person.rorelse, avvisad |

- **Tillstånd och tid:** tillståndet med liggaren är 5 rader och 2 129 tecken. Mediantiden är 169 ms per val, med ett anrop per mening.
- **Variation:** 55 körningar gav ingen variation. Utan liggaren varierade m4.
- **Den långsamma vägen med Flash** tog 4,1, 5,3 och 8,7 s för m8, m9 och m10. Alla tre blev skälade nej (`ut_0031/langsam_vag_flash.json`).
- **Min egen bedömning stämmer.** m9 kunde bli regi först om kundens arm blir en prop som går att flytta (`flytta_prop`). I dag är den bara ett objekt i scenbygget.

**Bakåtkompatibelt** (tom cache, före-kod `fore_0031/kod/`): samma sha256 för åtta fall: Notan, Notan med lokalbyte, bar, guacamole, b-tilltal 0016, gelato gammal, gelato 0029 och b-tilltal 0030.

**Tester:** 240 prov, samma åtta fel som före (`forvarld/liggare/tester_efter_0031.log`).

## Bedömning
- **Ja, liggaren bär det ägaren frågade om.** Ett tillstånd före och efter, och något som förstår skillnaden, finns nu som data: händelsen ge med rollerna kroppsdel, sak och mottagare, och frihetsgraden `fg_hand`, som säger vad som följer med.
- **Jev behöver inte förstå,** bara välja: 11 av 11 meningar rätt, och stabilt.
- **Modellen skrev mening, förlopp, frihetsgrader och spridning.** Segmentgränser, hållning, handen i tråget, kontakten med kundens hand, rutorna och källans id kom ur mätning.
- **Flash klarar inte frihetsgraderna,** och det är där värdet ligger. Den starka modellen behövs vid ingest, inte live.
- **Den långsamma vägen** behövdes bara för tre av elva meningar, och svarade på 4–9 s.
- **Svagaste ledet nu är nivå 1.** Speglingen kräver ett eget mål för den nya handen och korrekt behandling av de vridande lederna. Annars blir nivå 3 (Dreamina) vägen för ändringar av armar.
- **Nästa:** liggaren blint på b-tilltal och guacamole (0032). Där prövas om schemat är allmänt.

## Ändrade eller nya filer
- **Kontrakt, nya:** `liggare.schema.json`, `liggare_kontroll.py`, `kalla_liggare.py`, `ut/kand-kennysgelato_n06-hand/liggare_0031*.json` och `kalla_0031.json`.
- **Kontrakt, ändrade** (före-kopior i `ut/fore_0031/kod/`): `kompilera.py` (`satt_frihetsgrad`, `spegla_armar`, handföremålet byter handled), `kalla.schema.json` (`semantik.liggare`) och `regi.schema.json`.
- **Gennedbrytning:** `s_ik_blender.py` och `d_video/dreamina-paket/vanster_hand/`.
- **Förvärld:**
  - `forvarld/liggare/`: `LANA.md`, prompten, `kor_liggare.py`, `langsam_vag.py`, `bakatkompatibel_0031.py`, utfall
  - `forvarld/gelato/`: `prov_liggare.mjs`, `meningar_0031.json`, `film_0031.py`, `ut_0031/`
  - `forvarld/gelato/prov.mjs` fick `UT` och `MENINGAR` som miljövariabler; frågorna är oförändrade
- `scen/3d/PIPE.md` och `NASTA.md`.

## Kontroll mot "Klart när"
- [x] LANA.md, schemat, liggaren, prompten, Flash-jämförelsen och kontrollen med utfall.
- [x] Andra handen: fem val, spridning, film och Dreamina-paket.
- [x] Tabell med elva meningar × fem körningar, med och utan liggare, och den långsamma vägen.
- [x] PIPE och NASTA.
- [x] Bedömning.

## Avvikelser
- **Liggarens yta och fråga skrevs före första körningen,** och ingenting ändrades efter svaren. Tillståndet "utan" är 0029:s slutliga form (med segmentfrågan i eget anrop).
- **Nivå 1 ser fel ut i räcka fram** (se ovan). Rutorna är ändå märkta `utförd_niva_1`, så att det går att se var.
- **Flash-liggarens negerade faktum** ströks i en kopia (`liggare_0031_flash_utan_negation.json`) för att kontrollen skulle kunna räkna luckor.
- **Kostnad:**
  - Jev cirka 0,01 USD
  - Flash 0,053 för liggaren och cirka 0,01 för den långsamma vägen, totalt under 0,20
  - Modal och Codex användes inte
- **Tid:** se tidsloggen.
