# Jutsus konventioner

Prövade 17 nov 2026 (test 04) med [hello_konventioner.py](hello_konventioner.py) i projektet `byggsten-jutsu-konventioner-hello` (id `5cadca4b-9f72-446e-84f8-5be3b16a4845`), revision 1. Kostnad 0 credits. Bilder i [ut/hello/](ut/hello/).

## Ramen
| sak | konvention | belägg |
|---|---|---|
| bpy-ramen | högerhänt, **Z upp**, meter (`METRIC`, `scale_length` 1,0) | toppvyn: X åt höger, Y uppåt i bild |
| editorn och glTF | högerhänt, **Y upp**. Blender `(x, y, z)` → glTF `(x, z, −y)`. Skala `(sx, sy, sz)` → `(sx, sz, sy)` | bordet `(0,5; 3,0; 0,375)` blev `(0,5; 0,375; −3)` |
| `import_asset.transform` | editorns ram: meter, Y upp, kvaternion XYZW | verktygets schema |
| rotation | `rotation_mode` är `XYZ` som standard och betyder **R = Rz·Ry·Rx** (avvikelse 1e-7; Rx·Ry·Rz ger 0,18). Kvaternion finns. 30° kring Blenders Z blev glTF-kvaternionen (0; 0,259; 0; 0,966) kring +Y | |
| vinklar | bpy tar radianer; gränssnittet visar grader | |
| tid | 24 fps som standard | |

## Kameran
- Kameran tittar längs sin lokala **−Z**, och uppåt är lokal **+Y**. Ingen förskjutning som standard, så bildens mitt är `(W/2, H/2)`.
- Pinhole med `sensor_fit = 'HORIZONTAL'`: `f_px = lins / sensorbredd · W`. 26 mm och 36 mm på 576×1024 ger `f_px` 416, horisontell FOV 69,39° och vertikal 101,81°.
- **Fälla för 9:16:** standardvärdet `sensor_fit = 'AUTO'` lägger sensorbredden längs den längre sidan, alltså höjden i stående format. Samma lins ger då en smalare bild: bordet blev 278 px brett i stället för 156. Adaptern måste alltid sätta `HORIZONTAL` (eller räkna om).
- **Fälla:** `camera.angle_x` och `angle_y` räknas ur sensorns mått (36 × 24 mm) och inte ur upplösningen. `angle_y` visade 49,55° när den verkliga vertikala FOV:en var 101,81°. Läs aldrig FOV därifrån.
- glTF-kameran får `yfov` 1,7770 rad (101,81°) och `aspectRatio` 0,5625, vilket stämmer med pinhole. Ortografiska kamerors `xmag` och `ymag` följer scenens upplösning när exporten körs.

## Projektion (avgörande för Fas 5)
| jämförelse | avvikelse |
|---|---|
| egen numpy-pinhole mot Blenders `world_to_camera_view`, 8 hörn | 0,0007 px |
| projicerad låda mot renderade pixlar (Workbench, kantutjämning av) | under 1 px: [207,7 452,0 364,1 590,1] mot [208 452 364 590] |

Följd: reprojektionen kan räknas lokalt i numpy med samma kamera som Jutsu använder. Rendering behövs bara för att titta, inte i optimeringsslingan.

## Vad scenen bär
| behov | fungerar så | glTF |
|---|---|---|
| lådor och plan | mesh via `bmesh` eller `from_pydata`; mått som objektets skala på en enhetskub | nod med skala |
| etiketter | textobjekt (`FONT`) | exporteras som mesh |
| osäkerhetszon | Principled Alpha och `surface_render_method = 'BLENDED'` | `alphaMode: BLEND` |
| metadata | `objekt["hagen_…"] = json-sträng` och `scene["hagen_…"]` | nodens och scenens `extras` |
| grupper | kollektioner (`ENV`, `PRP`, `ZONE`, `CAM`, `LGT`, `HJALP`) | noder; kollektionerna syns inte |
| ljus | Sun, Point, Spot. Area-ljus faller bort i editorn och GLB | `KHR_lights_punctual` |
| kameror | perspektiv och ortografisk | `cameras[]` |

## Rendering
| läge | tid på Jutsus CPU | används till |
|---|---|---|
| Workbench 576×1024, första bilden | 4,5 s (inklusive uppstart) | geometri och projektion |
| Workbench 512×512, därefter | 0,2 s | toppvy, kontrollbilder |
| EEVEE 288×512, 4 samples | 48 s | ljus och genomskinlighet, sällan |

- Workbench visar objektets alfa, så zoner syns halvgenomskinliga utan EEVEE.
- Exakta färger kräver `color_type = 'OBJECT'`, `light = 'FLAT'` och `view_transform = 'Standard'`. Standardvärdet är `Khronos PBR Neutral`.

## Gränser (ur LOGG.md, oförändrade)
- 300 s per operation, 256 KiB kod, högst 8 bilder eller filmer per operation, inget nätverk.
- En ändring i taget per projekt. `run_python` kräver `revision` och `expectedSceneSequence` ur senaste query.
- Editorn kan skriva om scenen när en människa öppnar den. Läs därför om före varje ändring.
- Egna modeller kan inte komma in via MCP, bara katalogens.

## MCP
- Verktygen `scene_builder_3d_*` kommer från Higgsfield-kopplingen i claude.ai, som fungerar. Den lokala servern `higgsfield` kräver inloggning via `/mcp` men behövs inte för detta.
- Scenarbete kostar 0 credits. Bara `generate_angles` och `generate_video` kostar, och saldot är 0.

## Följder för en scenadapter
- Skriv bpy i Blenders ram (Z upp, meter) med uttrycklig `rotation_mode`. Räkna fram glTF-ramen vid export, och lagra den inte.
- Sätt `sensor_fit = 'HORIZONTAL'` och räkna FOV ur `f_px`.
- Namnge efter roll: `ENV_`, `PRP_`, `HERO_`, `CAM_`, `LGT_`. Lägg till egna prefix för osäkerhet (`ZONE_`), etiketter (`LBL_`) och ankare (`ANK_`).
- Lägg telemetrin som JSON i `hagen_*`-egenskaper, så att den följer med i GLB:n.
