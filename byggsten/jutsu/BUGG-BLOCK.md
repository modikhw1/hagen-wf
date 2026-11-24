# Uppgift 2: blocken mitt i scenen

14 nov 2026. Gäller animatiken `ut/notan/tidslinje/notan_original_mot_jutsu.mp4` (projekt `byggsten-jutsu-notan-tidslinje`, revision 4).

## Svar i korthet
**Blocken kommer från kedjans plan, inte från Jutsu.** Deklarationen delar notan i två rum: det berättade rummet (S1–S6) och det avslöjade (S7). Planen bygger ändå båda rummens möbler i alla sju tagningar. Möbler ur fel rum syns därför mitt i bild:

- **S2 och S5** (motbilden mot B): `bord_2` och `stol_B_avslojad` står direkt bakom B, på 2,0–2,5 m respektive 3,2–3,7 m djup. Tillsammans täcker de cirka 22–25 % av bilden. I originalet finns där inget bord, bara fönster och vägg.
- **S7** (avslöjandet): berättelsens `stol_B` står mitt i bilden, 1,4 m från kameran, mellan A:s bord och B:s eget bord. Den täcker cirka 33 % av bilden. Ryggstödet är en massiv skiva på 0,48 × 0,43 m som vetter mot kameran. I originalet är mitten fri.

Bevis: `ut/notan/bugg/oversikt.png` och en bild per scen i `ut/notan/bugg/` visar lådorna projicerade som konturer över originalets bild mitt i varje tagning. Siffrorna står i `ut/notan/bugg/bugg_block.json`, och skriptet är `bugg_block.py`.

## Vad deklarationen säger
`scen/3d/ingest/ut/notan-tagningar/plats/deklaration.json`:
- `berattat_rum.galler_tagningar = [S1…S6]`, platser `bord_1, stol_A, stol_B, staplats_C`.
- `avslojat_rum.galler_tagningar = [S7]`, platser `bord_2, stol_B_avslojad`.
- Regeln för S7: "B flyttas i den tagningen till bord_2; A och bord_1 står kvar."

## Vad planen gör
`scen/3d/kontrakt/ut/notan_berattat/skymning/plan.json`, `objekt[].synlig_ut`:

| möbel | synlig_ut i planen | borde vara |
|---|---|---|
| `bord_2` (5 delar) | [0, 383], alla tagningar | [337, 383], bara S7 |
| `stol_B_avslojad` (8 delar) | [0, 383] | [337, 383] |
| `stol_B` (7 kopior × 8 delar) | en kopia per tagning, **också S7** [337, 383] | S1–S6 [0, 337] |
| `bord_1`, `stol_A` | alla tagningar | alla tagningar (A:s bord står kvar i S7) |

`scener[].utelamnade` är tom i alla sju tagningar, så renderingen stryker ingenting heller.

## Var felet uppstår
- `galler_tagningar` läses bara av `scen/3d/ingest/scenbrief.py:468`, och där bara för validering.
- `scen/3d/ingest/deklaration_till_hand.py:197–198` använder `berattat_rum` för layouttext och stolsavstånd, men inte rummets tagningar. `avslojat_rum` läses inte alls.
- Kompilatorn (`scen/3d/kontrakt/kompilera.py:125–133`) delar objekt per tagning ur `synlig_ut`, men får aldrig något intervall för rummen. Därför blir möblerna synliga i [0, N].
- Kopian av `stol_B` per tagning kommer från scenpassningen (en kopia per scen och person-ankare). Den vet inte heller om rummen.

Min Jutsu-export (`notan_export.py`) tog `synlig_ut` rakt ur planen och ärvde därför felet. Samma plan driver kedjans egen Blender-rendering, så felet bör synas där också. Kedjans film för `skymning` finns inte i mappen, så det är inte kontrollerat i bild.

## Samma tagning, per möbel (mitt i tagningen)
| scen | person (djup) | möbler i bild, närmast först | fel |
|---|---|---|---|
| s1 | A (1,24 m) | bord_1 0,69, stol_A 1,35, golv, vagg_sida | inget |
| s2 | B (1,72 m) | bord_1 1,14, stol_B 1,99, **bord_2 2,53**, **stol_B_avslojad 3,71**, vagg_bak | bord_2 och stol_B_avslojad |
| s3 | A (1,26 m) | bord_1, stol_A, golv, vagg_sida | inget |
| s4 | C (1,78 m) | bara golv | inga väggar på C:s sida (se nedan) |
| s5 | B (1,27 m) | bord_1, stol_B, **bord_2 2,04**, **stol_B_avslojad 3,21**, vagg_bak | bord_2 och stol_B_avslojad |
| s6 | A (1,24 m) | bord_1, stol_A, golv, vagg_sida | inget |
| s7 | B (3,30 m) | bord_1 0,68, **stol_B 1,38 (framför B)**, bord_2 2,08, stol_B_avslojad 3,27, vagg_bak | stol_B |

## Andra saker som ser ut som block, men har andra orsaker
1. **Ryggstöden är massiva skivor.** Mallstolen har ryggen `rygg` som en låda på 0,48 × 0,055 × 0,43 m. Bakifrån eller i motljus läses den som ett block. Det är formen, inte läget, som är fel.
2. **`vagg_bak` täcker 60–73 % av bilden i s2, s5 och s7** som en platt vägg, där originalet har fönster och ett ljust rum. Det är rätt plats men fel innehåll, eftersom väggar är mallvärden.
3. **s4 har inga väggar.** C:s kamera ser bara golv (24 %), och resten är tomrum. Deklarationen har bara `vagg_bak` och `vagg_sida`, och ingen vägg på servitörens sida av rummet.
4. **s7: B:s fötter ligger cirka 0,2 m under golvet.** Det kommer från läsningen och syns i filmen som att benen skärs av golvet.

## Utanför videon
Projektet har efter animatiken gått från revision 4 till 7 (sekvens 11). Det skedde i webbgränssnittet och inte via MCP. Det som ändrades där finns inte i videon.

## Förslag till rättning (inte gjord)
Två nivåer. Den första hör till kedjan, och `byggsten/` rör inte `scen/`, så den kräver ditt beslut eller ett uppdrag:
1. **I kedjan (rätt ställe):** `deklaration_till_hand.py` bör föra varje rums `galler_tagningar` vidare som tagningsintervall på rummets platser och möbler. Kompilatorn ska då sätta `synlig_ut` på dem, eller lägga dem i `scener[].utelamnade` för tagningar utanför rummet. Det är allmänt, eftersom varje klipp med berättat mot avslöjat rum (en klassisk avslöjning) har samma struktur.
2. **I byggstenen (snabbt, bara för Jutsu-provet):** `notan_export.py` läser deklarationens rum och klipper `synlig_ut` själv. Det rättar animatiken men inte kedjan.
