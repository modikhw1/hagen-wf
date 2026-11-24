---
id: 0035
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
**1. Vad 1:1 betyder.** Fem mått, varav fyra finns redan:
1. synliga leder mot originalet i promille (`h_kontroll.py`)
2. hela kroppen i bild, och huvudet avskuret (`h_kontroll.py`, `h2_extra.py`)
3. tid som vändpunkter och rotens hopp (`t_tid.py`, `h_kontroll.py`)
4. kamerans glidning, fotlinjen i px (`h2_extra.py`)
5. inga påhittade föremål: för ögat i remsan, inget mått än

Måtten står i [ATERSKAPNING.md](../../scen/3d/gennedbrytning/ATERSKAPNING.md) och i receptet.

**2. Kartan** ([ATERSKAPNING.md](../../scen/3d/gennedbrytning/ATERSKAPNING.md)) jämför Dreamina/Seedance 2.0, Luma Ray 3.2, Kling 3.0 Motion Control, Runway Act-Two/Aleph och Wan 2.2 Animate/VACE. Per väg: videoreferens, nyckelbilder på tid, mask, exakt längd, åtkomst, pris och licens.
- **Bäst styrning:** Ray 3.2 (exakt längd, nyckelbilder på tid).
- **Bäst helkropp hittills:** Dreamina.
- **Mest kontrollerbar:** Wan VACE med mask, men den kräver egen hosting, som ägaren har sagt nej till.
- **Kling och Runway Act-Two** tar video som rörelsereferens med exakt längd och kan prövas, mot betalning.

**3. Prövat.**
- **Gelato S1:** fem genereringar mätta i samma tabell (ATERSKAPNING.md). Ingen klarar kontrollen.
  - **Dreamina:** hela kroppen i alla 148 rutor, men 43 rutor med avskuret huvud, ett rothopp på 13 cm, och 193 rutor som måste tidspassas.
  - **Ray k:** hela kroppen och bäst rotstabilitet, men överkroppens p90 är 80 promille.
- **Dreamina genom kedjan (0030)** ger samma mått, så kedjan är reproducerbar.
- **Gelato omgång 2 och guacamole S1:** `svar/` är tomt. Konfigarna i `kedja/` väntar (`VÄNTAR`).

**4. Huvudet och det som är utanför bild** (utan ny generering):
- **Den kamerafria källan** har huvudet alltid inne i bilden, minst 330 px från kanten (`kamerafri/huvudmarginal.json`).
- **I k2-källan,** som Dreamina fick och där originalets pixlar följer med, skär originalets överkant huvudet i källrutorna 58–77 (`kamerafri/kanten_skar_huvudet.json`).
- **Dreamina skar 22–69:** den ärver kanten, och skär dessutom själv när hon lutar sig mot kameran.
- **Receptet:** ge generatorn huvudrum, alltså källan skalad (0,82, fötterna fasta, grå yta ovanför), plus en rad i prompten. Paketet ligger i [omgang3_huvudrum/](../../scen/3d/gennedbrytning/d_video/dreamina-paket/omgang3_huvudrum/LAS-MIG.md). Avbildningen måste då ta med skalningen; det är samma mekanism som guacamoles 62 %, och den saknas fortfarande i `g_forvarld`.

**5. Receptet** står i `STRATEGI.md` ("Recept för återskapning 1:1"):
- källa med huvudrum
- Ray med nyckelbilder när saldo finns, annars Dreamina följt av tidspassning
- prompt som borttagning, en generering per tagning
- kontroll efteråt mot de fem måtten (trösklarna är diagnos)

## Bedömning
- **Den största återstående felkällan är tiden och huvudet,** inte kroppens form. Exakt längd och huvudrum i källan löser mer än en bättre generator.
- **Nästa steg:**
  - ägarens omgång 2, och omgång 3 med huvudrum
  - ett Ray-försök med nyckelbilder, när saldo finns
  - `g_forvarld` med invers för skalade källor, vilket behövs för huvudrum och för guacamole

## Ändrade eller nya filer
- `scen/3d/gennedbrytning/ATERSKAPNING.md` och `STRATEGI.md` (receptet).
- `scen/3d/gennedbrytning/kamerafri/huvudmarginal.json` och `kanten_skar_huvudet.json`.
- `scen/3d/gennedbrytning/d_video/dreamina-paket/omgang3_huvudrum/` (källa, prompt, LAS-MIG, `svar/`).
- `scen/3d/NASTA.md`.

## Kontroll mot "Klart när"
- [x] Måtten, kartan, utfallet på de tagningar som finns, och receptet.
- [x] Paket för ägarens nästa omgång (omgång 3, huvudrum). Omgång 2 och guacamole väntar.

## Avvikelser
- **Bara en tagning är mätt.** Omgång 2 och guacamole har inga svar än.
- **Ingen generering och ingen kostnad.** Priserna i kartan kommer från återförsäljare och guider, inte från officiella prislistor.
