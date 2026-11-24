# Logg: 3D Jutsu

## Test 01, 14 nov 2026
**Projekt:** `byggsten-jutsu-test-01`, id `c43763c8-7fa1-4e90-ad31-c5745d6a13e5`, https://higgsfield.ai/3d-jutsu/c43763c8-7fa1-4e90-ad31-c5745d6a13e5

**Saldo:** 0 credits, gratisplan. Det var oförändrat efter alla operationer, och inga nya transaktioner tillkom. **Att skapa projekt, köra query och run, rendera och exportera GLB eller blend kostar inget.** Bara `generate_angles` och `generate_video` kostar, och de kan inte köras med 0 credits.

### Miljön (query `q-miljo-01`)
- Blender 5.2.0 LTS, Python 3.13.13.
- **2 processorkärnor (AMD EPYC), ingen GPU.** Cycles har bara CPU.
- Moduler: `numpy` och `requests` finns. `scipy`, `torch`, `cv2` och `trimesh` saknas.
- Tillägg: gltf2, fbx, bvh och pose_library. **BVH-import finns**, vilket är relevant för ledbanor.
- Nätet är stängt: namnuppslag misslyckas.
- Ett tomt projekt startar som en tom scen: EEVEE, 24 fps, metriskt.

### Ändring (run `blockout-ledbana-01`, revision 0 till 1)
- Golv, disk (`PRP_disk`), kamera, solljus och punktljus. Därtill 24 leder × 60 rutor som tal direkt i koden (1 440 nycklar).
- Hela operationen tog 25 s från start till slut. Själva renderingen var **18,8 s för en ruta 640×360 i EEVEE med 8 samples, på CPU**.
- Varje ändring sparar automatiskt `session.blend` (1,0 MB) och `preview.glb` (37 KB).
- **GLB:n bär animationen:** 29 noder, 23 animationer. Leden utan rörelse föll bort.
- Bilden: `ut/test-01/blockout_f15.png`. Kedjan av leder står framför disken, och skuggan faller rätt.

### Gränser som prövades
| gräns | uppgiven | utfall |
|---|---|---|
| tid per operation | cirka 5 min | **300 s exakt**: `EXECUTION_TIMEOUT`, "exceeded the 300000ms limit". Inget sparas. Gäller även query. |
| rendering | | cirka 19 s per ruta i 640×360 EEVEE, vilket ger **högst cirka 15 rutor per operation**. En film måste delas upp, renderas med Workbench, eller renderas lokalt ur `.blend`. |
| nätverk | inget | bekräftat |
| egen modell in | inte via MCP | `import_asset` tar bara katalog-id. Katalogen har 994 föremål (inredning, skyltar, fordon) och **inga människor**. |
| data in via kod | 256 KiB | inte prövat till gränsen. **Den egentliga gränsen är att all data i koden passerar agentens utdata.** En MHR-sekvens (cirka 127 leder × 300 rutor) är för stor för att skrivas in. Små ledbanor (24 leder × 60 rutor) går bra. |
| kostnad | okänd | 0 credits för scenarbete |

### Kroppar
- `animation_actions` består av Meshys bibliotek, med 678 klipp som "Talk_with_Left_Hand_Raised" och "Wave_One_Hand".
- De används med `generate_3d` med `enable_animation` (bild till riggad figur), som kostar credits.
- Det är färdiga klipp. Det finns ingen målstyrning.

### Vad det betyder för oss
- **Det fungerar:** en hostad Blender som vi kan styra gratis, med versionshistorik. En ändring är en revision, och GLB och blend kommer ut automatiskt efter varje revision. Det motsvarar vår lokala Blender plus MCP, med historik på köpet.
- **Det fungerar inte:**
  - Vår egen kropp och vårt rum kommer inte in via MCP.
  - Renderingen på CPU är för långsam för film inom en operation.
  - Det finns inga människor i katalogen.
- **Öppen fråga:** kan en GLB som ägaren importerar i webbgränssnittet läsas och ändras via MCP efteråt? I så fall kommer förvärlden in den vägen.

## Test 02: notans rum, 14 nov 2026
**Projekt:** `byggsten-jutsu-notan-rum`, id `bf83112b-7251-49b5-a8cc-a6962ad7ac1a`.

**Källa:** `scen/3d/kontrakt/rumsmall/dekl_notan-tagningar.json` (deklaration 0.7). Den har 8 delar: golv, två väggar, två bord och tre stolar. Kameran är ungefärlig och sitter i gången. Den lästes inte ur originalets kamera, eftersom den ligger i COLMAP-ram och skulle kräva en omräkning.

| steg | tid |
|---|---|
| hitta deklarationen och läsa den (agenten, lokalt) | cirka 1,5 min |
| skriva koden (agenten) | cirka 30 s |
| bygget i Blender (45 objekt) | 0,04 s |
| EEVEE-render 640×360, 8 samples | 18,2 s |
| sparande av blend och GLB plus kö | cirka 6 s |
| **hela operationen på servern** | **25 s** |
| hämta och granska bilden | cirka 10 s |

**Ändring** (`bord_2` och dess stol 0,5 m bort, Workbench-render):
- Servern tog **2,0 s totalt**, varav renderingen 0,66 s.
- Från beslut till granskad bild tog det cirka 15 s, och det mesta av den tiden var agentens anrop.

**Bild:** `ut/notan/notan_rum_rev1.png` och `notan_flytt_rev2.png`. Stolarna vänder sig rätt mot borden enligt deklarationen.

**Brist:** i Workbench blir materialen grå. Viewport-färgen (`diffuse_color`) måste sättas om man vill ha färg där.

## Test 03: notan som tidslinje med kroppar, 14 nov 2026
**Projekt:** `byggsten-jutsu-notan-tidslinje`, id `36700078-20b3-4e6b-ba69-eda9a7461151`.

**Källa:**
- Planen `scen/3d/kontrakt/ut/notan_berattat/skymning/plan.json`: 7 tagningar, 383 rutor, kamera per ruta i Blender-koordinater.
- Mening (repliker) ur `kalla_mobelintervall.json`.
- Lederna kommer ur kedjans egen `kontrakt/trohet.ruta()` (adaptern `notan_export.py`), så de hamnar där kedjans Blender lägger dem.

**Data in:**
- Kompakt JSON, 56 KB: 18 leder i heltal mm, 10 fps.
- Komprimerad till 10 KB (op1) och 36 KB (op2), eftersom kameran står still inom varje tagning och stolarnas kopior per tagning var identiska.
- Koden genereras av `notan_ops.py` till `ut/notan/ops/`.

| operation | vad | tid i Jutsu |
|---|---|---|
| op1 | rum (37 lådor), kamera (14 nycklar, klipp mellan tagningar), 7 scenmarkörer, 7 replikmarkörer, mening som scenegenskaper (`hagen_scener`, `hagen_repliker`, `hagen_personer`), 2 kontrollbilder | 7,6 s |
| op2 | 3 personer × 2 nivåer: `full` (alla rutor, 10 fps, linjär) och `beat` (poser vid scenstart, repliker och slut, Bezier, dold som standard). Dockor av 17 cylindrar och ett huvud, styrda av 18 tomma objekt. Synlighet per tagning. 4 kontrollbilder. | 8,4 s |
| op3 | Workbench-MP4 i 288×512, rutorna 0–191 och 192–382, som läsoperationer (ingen ny revision) | 34 s + 45 s (cirka 0,2 s per ruta) |

**Bild:** `ut/notan/tidslinje/kropp_kontroll.png` (originalet ovanför, Jutsu under).
- Rutorna 36, 140, 200 och 360 stämmer: A gestikulerar vid bordet, servitören C står med handen på höften, och B vid det avslöjade bordet lyfter höger arm.

**Fynd: Higgsfields editor skriver om scenen.** Mellan op1 och op2 gick projektet från revision 1 till 3 utan oss, troligen när scenen öppnades i webbgränssnittet:
- Kameran bakades till en nyckel per ruta, och klippen finns kvar.
- Den fick en egen rigg: `Path_CAM_main`, `Aim_CAM_main` och waypoints `WP_1`–`WP_7`, en per tagning.
- Scenen fick egenskapen `blockingStudioTimeline` = `{"version":1,"duration":12.73,"shots":[{"cameraId":...,"start":0,"end":12.73}]}`, alltså **ett** shot. Deras modell är shots med kamera, start och slut i sekunder.
- Varje objekt fick ett `hf_id`. En markör "Shot 001" lades till.
- **Våra markörer och vår mening låg kvar.**

Följden: en agent som skriver måste läsa revisionen på nytt före varje ändring. Vår op2 avvisades först med `REVISION_CONFLICT`.

**Kö:** två läsoperationer på samma projekt körs inte parallellt. Den andra hamnar i kö (`queued`).

**Brister:**
- s7: B:s fötter ligger cirka 0,2 m under golvet. Det kommer från kedjans läsning och inte från Jutsu.
- Huvudet är en sfär utan riktning, så blicken syns inte.

**Animatiken:**
- `ut/notan/tidslinje/notan_original_mot_jutsu.mp4` visar originalet med ljud till vänster och Jutsu till höger, 12,7 s.
- Kontaktbladet ligger i `kontaktblad.png`. Klippen, personerna och gesterna följer originalet tagning för tagning.
- Nivå 2 (`RIG_*_beat`) ligger i scenen men är dold. Den slås på genom att visa kollektionen.

**Tidsåtgång, helheten:** cirka 15 min från ägarens "allt" till färdig animatik. Det mesta var att hitta rätt plan och skriva adaptern. Själva Jutsu-tiden var 7,6 + 8,4 + 79 s.

## Test 04: konventioner och projektion, 17 nov 2026
**Projekt:** `byggsten-jutsu-konventioner-hello`, id `5cadca4b-9f72-446e-84f8-5be3b16a4845`. Skript: [hello_konventioner.py](hello_konventioner.py). Kostnad 0 credits.
- Scenen har ett bord (1,0 × 0,6 × 0,75 m, vridet 30°), en halvgenomskinlig zon, axelmarkörer, en etikett, två ljus, en 9:16-kamera och en toppkamera.
- Hela operationen tog 54 s, varav EEVEE 48 s och Workbench 4,7 s.
- **Projektionen stämmer.** Egen pinhole mot Blender: 0,0007 px. Mot renderade pixlar: under 1 px.
- **Fällor:** `sensor_fit = 'AUTO'` i stående format, och `camera.angle_y`, som inte följer upplösningen.
- Allt står i [KONVENTIONER.md](KONVENTIONER.md). Bilderna ligger i `ut/hello/`.
