---
id: 0019
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

> **13 nov:** det som återstår (0017 del G, 0018 punkterna 4–6, 0019 varianterna b och c) redovisas i `delegat/svar/0021-kamerafri-kalla-och-in-i-forvarlden.md`.

## Resultat
Variant (a) är körd, läst och mätt. Kroppen ur den isolerade videon är klart jämnare än dagens läsning. Nyckelbilderna för mittrutorna lyckades inte, eftersom Codex inte ger någon isolerad person, så (b) och (c) är inte körda.

**Codex för bild:** omslaget är `scen/3d/gennedbrytning/codex_bild.py`, med ny `codex exec`-session per bild och kvot före och efter i `<bild>.codex.json`.
- **Steg A (tom scen) fungerar:** rutorna 55, 112 och 146 tog cirka 70 s per bild. Text, kundens hand och skeden står dock kvar.
- **Steg B gav ingen isolerad person** i åtta försök, se 0020.
- **Veckokvot:** 93 → 97 %. Ägaren godkände fler bilder.

**Nyckelrutor:** valda ur högra handledens bana i dagens läsning (`nyckel/handledsbana.json`).
- Ruta 55: handen som lägst, hon lutar sig ned i disken.
- Ruta 94: vändpunkt, handen som högst.
- Ruta 136–146: kameran som närmast.
- Ruta 112 ligger mellan vändpunkten och slutet.

Ingen av mittrutorna gav en isolerad person som håller position eller identitet efter passningen. De stryks enligt 0019 (`nyckel/oversikt.jpg`). Kameran är dessutom så nära där att hela kroppen inte får plats i ramen.

**Stillbildsläsning, ruta 0** (ägarens GPT-isolering, passad):
- Överkroppens leder ligger 7,5 promille från dagens läsning (median), max 61.
- Ben mot överkropp är 1,68, mot 1,65 i dagens läsning.
- Lår 0,44 m, underben 0,39 m, samma på båda sidor.

**Variant (a):** Luma Ray 3.2 v2v, startbild = passad GPT-ruta 0, ägarens STEP 2-prompt, 540p, 0,15 USD, 222 s. Videon ligger i `d_video/a/isolerad.mp4` och översikten i `oversikt.jpg`.

| | Dagens läsning | Isolerad (a) |
|---|---|---|
| Synk | — | 148 rutor, 29,97 fps, alltså 1:1 |
| Lästa rutor | 146 av 148 | 148 av 148 |
| Bål: hopp >15°, största hopp, median | 0, 7,3°, 0,76° | 0, 2,9°, 0,38° |
| Höft: hopp >15°, största hopp, median | 0, 8,9°, 1,16° | 0, 3,8°, 0,51° |
| Rot: hopp per ruta, median och max; rutor >10 cm | 2,2 cm, 16,5 cm; 7 | 1,2 cm, 4,1 cm; 0 |
| Benlängd, median (spridning) | 0,75 m (4,8 %) | 0,82 m (6,6 %) |
| Överkroppens leder mot dagens, i originalets rutor | — | median 16, p90 62 promille |
| Hennes mask mot originalets | — | median 0,94, min 0,63 |
| Avstånd till nyckelbilden vid ruta 0 | — | startbilden låst; inga fler nyckelbilder |

**Vad som syns i videon:**
- **Rätt:** samma kvinna och samma rörelse med samma tid (hon lutar sig ned, rätar på sig och räcker fram handen). Hela kroppen syns i början.
- **Fel:**
  - Källans zoom och tippning följer med, så underkroppen klipps från cirka ruta 80.
  - Kundens hand står kvar i slutet.
  - Hon håller något i handen trots "hands empty".
  - Benen är lite längre än i dagens läsning, och spridningen ökar när de klipps.

**Inte gjort:** varianterna (b) och (c), eftersom det saknas giltiga nyckelbilder. Förvärlden med den nya kroppen, del G i 0017, är inte heller gjord. Kroppen ur `d_video/a/las/1/*.npz` måste först bli en sekvens (`sekvens_*.npz` via ingestens sekvenssteg) i en kopia av gelatos plan. Det är nästa steg. Den tomma scenen som platta bakom blocken är inte heller provad.

**Kostnad och väggtid per tagning med det som fungerar:**
- Bild: Codex steg A cirka 70 s och ägarens GPT-bild för steg B.
- Passning: under 1 s.
- Video: fal cirka 0,15 USD och 4 min.
- Läsning: Modal cirka 2 min.

Det blir cirka 0,15 USD i fal plus Modal per tagning, och cirka 1,70 USD för elva tagningar. Codex: cirka 1 procentenhet av veckan per bild.

## Bedömning
- **Det som håller:** en isolerad startbild, med passningen i efterhand som lås, och sedan Ray 3.2 v2v. Det ger en kropp som är tydligt jämnare och fortfarande trogen överkroppen.
- **Steg B:** bör tills vidare köras av ägaren i GPT (ny kontext, två bilder). Codex gör det inte.
- **Nyckelbilder:** behövs mest där kameran är nära och kroppen klipps. Där krävs en annan ram (helbild eller utvidgning), inte källans.
- **Före förvärlden saknas:** stilla kamera i lager 2, att kundens hand och föremål tas bort, och sekvenssteget för den nya läsningen.
- **Innan det går att lita på utan att någon tittar:** en automatisk kontroll av främmande händer och objekt, och av benlängder i rutor där kroppen klipps.

## Ändrade eller nya filer
Allt nytt under `scen/3d/gennedbrytning/`:
- Skript: `codex_bild.py`, `passa.py`, `las_stillbild.py`, `d_video.py`, `f_las.py`.
- Mappar och resultat: `nyckel/`, `d_video/a/`, `kostnad.json`.
- `STRATEGI.md`: arbetsfördelning, efterbehandling, Öppet och Prövat.

## Avvikelser
- **Två körningar gav ingenting:** Codex B-körningarna hängde först i 15 minuter, eftersom stdin inte var stängd och ingen session startade. Det är rättat.
- **Tomma B-bilder:** fyra B-varianter gav kvitto eller fel bild. De sparas som `*.forsok*.codex.json`.
- **Fal totalt:** 0,165 USD av cirka 1,85.
