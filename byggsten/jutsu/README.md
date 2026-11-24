# jutsu: Higgsfield 3D Jutsu

## Obligatoriskt vid ny scen från biblioteksklipp

Följ reglerna i `../../AGENTS.md`. Standardleveransen följer originalklippets kameror, tagningar, rörelser och synlighet via befintlig plan/ingest. En rumsmall ensam räcker inte. Notan och C-sketch har klippspecifika adaptrar, inte en färdig generell pipeline; anpassa adaptern till det nya klippet och verifiera mot originalrutor före leverans. Egen översiktskamera och stillastående dockor kräver en uttrycklig sådan beställning.

Lärdom 2026-11-16: Guacamole-projektets första revision använde inte den befintliga planen med fyra scener och 299 kameranycklar. Det var ett avsteg från tidigare arbetssätt, inte ett renderingsfel. Korrigeringen ska utgå från scenplanen och dess rörelse-/världsfiler, inte bara vrida den manuellt skapade kameran.

Experiment sedan 14 nov 2026. Frågan är vad 3D Jutsu kan göra för förvärlden och var gränserna går.

## Vad det är (ur Higgsfields egen instruktion `/3d-jutsu`, läst 14 nov)
- **Blender 5.2** körs headless på Higgsfields server. Varje scen är ett projekt med versionshistorik (`revision`).
- **Läsa** gör man med `scene_builder_3d_query_python` (bpy). Det sparar inget.
- **Ändra** gör man med `scene_builder_3d_run_python` (bpy). Ändringen ska ange exakt `revision` och `expectedSceneSequence`. En ändring i taget per projekt.
- Bilder och video lämnar en operation bara via `artifacts.file(...)` och `publish()`. Högst 8 PNG, JPEG eller MP4 per operation.
- **Ut:**
  - `.blend` (`get_blend`): hela scenen med animation.
  - `.glb` (`get_glb`): procedurella material, världsljus och area-ljus följer inte med.
  - Koordinater: Blender har z uppåt, glTF och editorn y uppåt.
- **In:** bara katalogmodeller via `search_assets` och `import_asset`. Egna filer går inte enligt instruktionen.
- **Kroppar:** 678 färdiga riggade animationer (`animation_actions`). Det finns ingen målstyrd kontroller.
- **Mening:** inget semantiskt lager i datan. Meningen bärs av namn efter roll (`HERO_`, `ENV_`, `PRP_`, `CAM_`, `LGT_`) och ett "scenpass" i agentens resonemang.
- **Betalt:**
  - `generate_angles`: AI-bild ur en render (Seedream).
  - `generate_video`: Seedance 2.5 med renderingen som startbild, 4–30 s.
  - Om själva scenarbetet kostar är oklart.
- **Närmast oss:** referensen `location-new-angles` återskapar en plats ur en bild med kalibrerad källkamera, och dold geometri märks som antagen.

## Uppgivna gränser (att pröva)
| gräns | uppgiven | prövad |
|---|---|---|
| tid per operation | cirka 5 min | 300 s exakt (test 01) |
| kodstorlek | 256 KiB | utdata från agenten är den egentliga gränsen |
| nätverk från bpy | inget | bekräftat |
| egen modell in | inte via MCP | bekräftat, och katalogen har inga människor |
| artefakter | 8 per operation, 512 MiB styck | |
| kostnad för query och run | okänd | 0 credits (test 01) |
| rendering | | CPU med 2 kärnor, cirka 19 s per ruta i 640×360 |

Utfallet står i [LOGG.md](LOGG.md).

## Rapporter
- [AUDIT-AVSTAND.md](AUDIT-AVSTAND.md): avståndet mellan vår förvärld och Jutsu, begrepp för begrepp, och hur Jutsu som mall hade sett ut.
- [BUGG-BLOCK.md](BUGG-BLOCK.md): varför block syns mitt i scenen i notans animatik. Orsaken är rummen per tagning i kedjans plan.
- [KONVENTIONER.md](KONVENTIONER.md): ramar, kamera, projektion och vad scenen bär, prövat 17 nov (test 04).
