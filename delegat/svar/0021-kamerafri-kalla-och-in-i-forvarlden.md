---
id: 0021
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

> **13 nov:** klart. Fortsätter i `delegat/svar/0023-en-generering-som-foljer-originalet.md` (0022 är återkallat).

## Läge
Punkterna 1–5 är gjorda, och den nya kroppen står i förvärlden för både (a) och k. Punkt 6 (rummet ur den tomma scenen) och punkt 7 (nyckelbilder i den kamerafria ramen) är inte gjorda. Fal totalt: 0,315 USD av cirka 1,85.

**1–2. Kamerafri, förgrundsfri källa** (`scen/3d/gennedbrytning/e_kamerafri.py`; film i `kamerafri/kamerafri.mp4`, översikt i `kamerafri/oversikt.jpg`, avbildningen med invers per ruta i `kamerafri/avbildning.json`).
- **Avbildningen:** likformig (skala och förskjutning, utan vridning) ur dagens 2D-leder (huvud, hals, axlar), utjämnad (Savitzky–Golay, 15 rutor).
  - Skalan går från 1,06 till 0,53. Kameran zoomar alltså nästan till dubbel storlek.
  - Skalskaket gick från 0,017 till 0,007 per ruta (log).
- **Masken:** ingestens personmask (270×480, uppskalad).
  - Kundens hand togs bort i 21 rutor, eftersom maskdelen kom in från bildkanten.
  - I 10 rutor (123–142) sitter handen ihop med hennes arm och står kvar.
  - Vit skärmtext inom hennes mask följer med ("Vs", "vi ger"), och kanterna är trappiga.

**3. Generering på den källan:** Ray 3.2 med samma startbild som (a) och en kort prompt (variant k, 0,15 USD). Videon ligger i `d_video/k/isolerad.mp4` och översikten i `oversikt.jpg`. Maskad video (VACE) är inte körd.

**4. Läsning och mått** (`f_las.py`, `f_trohet.py`):

| | Dagens | (a) källan som den är | k kamerafri källa |
|---|---|---|---|
| Synk | — | 148 rutor, 1:1 | 148 rutor, 1:1 |
| Hela kroppen i bild | — | 48 av 148 | 148 av 148 |
| Bål: största hopp, median | 7,3°, 0,76° | 2,9°, 0,38° | 3,1°, 0,41° |
| Höft: största hopp, median | 8,9°, 1,16° | 3,8°, 0,51° | 2,4°, 0,47° |
| Rot: hopp per ruta, median och max; rutor >10 cm | 2,2 cm, 16,5 cm; 7 | 1,2 cm, 4,1 cm; 0 | 0,5 cm, 2,0 cm; 0 |
| Benlängd, median (spridning) | 0,75 m (4,8 %) | 0,82 m (6,6 %) | 0,82 m (1,8 %) |
| Överkropp i originalets ram, median och p90 | — | 16 och 62 promille | 15 och 80 promille (genom inversen) |
| Främmande händer eller föremål (sett i videon) | — | kundens hand i slutet; föremål i hennes hand | ingen främmande hand; en svart rund form från cirka ruta 30 som växer |

**5. In i förvärlden** (`g_forvarld.py`). Gjort i en kopia av planen, där bara S1:s rörelse byts, och med oförändrad kod i `sekvens_stabil.py` och `mhr_rig.py`. För k förs roten tillbaka till originalets kamera genom inversen. Den första renderingen utan inversen ligger kvar i `g_forvarld/k_utan_invers/`.

Filmerna, med original, dagens förvärld och ny kropp:
- [g_forvarld/a/tre_bredvid.mp4](../../scen/3d/gennedbrytning/g_forvarld/a/tre_bredvid.mp4)
- [g_forvarld/k/tre_bredvid.mp4](../../scen/3d/gennedbrytning/g_forvarld/k/tre_bredvid.mp4)

Rutbilder finns i `tre_bredvid_rutor.jpg`.

**Vad som syns:**
- **Dagens förvärld** sitter på huk i början, med benen påhittade bakom disken.
- **(a)** står rakt och lutar sig ned och räcker fram som i originalet. I slutet, där benen klipptes i videon, blir benen tjocka och ett knä dras upp.
- **k** har raka, rimliga ben i alla rutor och lugnast rot.
  - Lutningen ned i disken (rutorna 40–70) är borta. Hon står upprätt med händerna kring den påhittade svarta formen.
  - Kring ruta 100 sträcker hon armen åt sidan i stället för upp mot ansiktet.
  - Antagandet är alltså rimligt för benen men hittar på för armarna och föremålet.

**Rummet (punkt 6):** inte gjort. Den inverterade avbildningen ger bara zoom och förskjutning i bild, inte kamerans läge i rummet. Rummet har redan en löst kamerabana i planen, och den används för både (a) och k.

## Bedömning
- **Ingeststeget blir:** kamerafri, förgrundsfri källa, sedan Ray 3.2 med passad startbild, och sedan läsning tillbaka genom inversen. Det ger hela kroppen, stabila ben och lugn rot.
- **Det som måste till:** masken får inte ha luckor där hon räcker ned i disken. Annars hittar modellen på något där, som den svarta formen.
- **Bästa nästa steg:** maskad video eller nyckelbilder (punkt 7) som binder armarna.
- **Kostnad:** cirka 0,15 USD i fal plus cirka 2 min Modal per tagning, alltså cirka 1,70 USD för elva tagningar. Bildsteg B görs tills vidare av ägaren i GPT.
- **Innan ett helt klipp:** bättre mask (segmenteraren i full upplösning), borttagning av skärmtext, och en automatisk kontroll av påhittade föremål och av lutningen mot originalet.

## Ändrade eller nya filer
Allt nytt under `scen/3d/gennedbrytning/`:
- Skript: `e_kamerafri.py`, `g_forvarld.py`, `f_trohet.py`, och variant k i `d_video.py`.
- Mappar: `kamerafri/`, `d_video/k/`, `g_forvarld/a/`, `g_forvarld/k/`, `g_forvarld/k_utan_invers/`.
- `STRATEGI.md`.

## Avvikelser
- Punkterna 6 och 7 är inte gjorda, och maskad video (VACE) är inte körd.
- Variant k renderades först utan invers (fel kamera för kroppen). Det rättades och renderades om.
