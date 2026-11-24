# Ingest v2 — Skalnings- och Benchmarkrapport (Singel-GPU L4, 0 Blender)

Detta dokument redovisar uppmätt körning av [`arbetsbord/ingest_v2/modal_ingest_v2.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ingest_v2/modal_ingest_v2.py) på **NVIDIA L4** (Modal, listpris `$0.80 / h`, dvs. `0.80 / 3600` USD/s) mot två riktiga tal+mat-klipp från kontrollbiblioteket. Inget Blender-steg och inga generativa bild-/videomodeller används i kedjan.

## 1. Benchmarkresultat (Verklig Modal L4-körning)

Körning: sekventiellt anrop i samma uppvärmda container (`container_load_s = 29.82 s`, `whisper_device = "cuda"`), sparat i [`arbetsbord/data/ingest_v2/ingest_v2_benchmark.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/data/ingest_v2/ingest_v2_benchmark.json).

| Mätetal | Klipp 1 (`spanjorskan`, kallt första anrop) | Klipp 2 (`duepiani`, varm container) |
| --- | --- | --- |
| Källvideo | `spanjorskansthlm-7474263274415082774.mp4` | `duepiani-7650849186912406806.mp4` |
| Videolängd / Rutor | `13.72 s` / `411` rutor | `19.44 s` / `583` rutor |
| Detekterade tagningar | `3` (`t1` person+mat, `t2` mat, `t3` person+mat) | `12` (`t8` mat, 11 `person_med_mat`) |
| Antal `SAM 3D Body`-anrop | `33` (`~3 fps` + kanter + ablation) | `73` (`~3 fps` + kanter + ablation) |
| **GPU-ingesttid (`total_ingest_s`)** | **`30.28 s`** | **`62.94 s`** |
| Väggtid inkl. nätverksöverföring (`wall_inkl_natverk_s`) | `79.12 s` (`var_varm: false`) | `67.34 s` (`var_varm: true`) |
| `ffmpeg_proxy_och_klipp` | `1.25 s` | `1.90 s` |
| `demucs_och_whisper` | `1.91 s` | `1.00 s` |
| `yolo_och_ocr` | `3.01 s` | `9.25 s` |
| `moge_homografi_tracking` | `0.76 s` | `2.46 s` |
| **`sam3d_och_pchip`** (flaskhals) | **`23.36 s`** (`77.1%` av GPU-tid) | **`48.32 s`** (`76.8%` av GPU-tid) |
| Estimerad marginalkostnad (`$0.80/h`) | **`$0.0067` / klipp** | **`$0.0140` / klipp** |
| Paketstorlek (`paket` + `tidslinje` + `proxy` + `tal.wav`) | **`2,567,955 B` (`2.449 MB`)** | **`3,752,619 B` (`3.579 MB`)** |
| Paketstorlek på disk inkl. `ingest_rapport.json` | `2,568,880 B` (`2.450 MB`) | `3,753,525 B` (`3.580 MB`) |
| PCHIP-ablation på `s1` (4 mellanhållna rutor) | **`median = 289.2 mm, p90 = 3057.7 mm`** (avvikelse, se §3) | **`median = 14.0 mm, p90 = 31.9 mm`** |

### Exakt filuppdelning per paket

- **`spanjorskan`**: `paket.json` `179,470 B`, `tidslinje.json` `3,459 B`, `proxy_h264.mp4` `1,945,102 B`, `tal.wav` `439,924 B`, `ingest_rapport.json` `925 B`.
- **`duepiani`**: `paket.json` `297,630 B`, `tidslinje.json` `18,068 B`, `proxy_h264.mp4` `2,814,209 B`, `tal.wav` `622,712 B`, `ingest_rapport.json` `906 B`.

Båda klippen ligger väl under kravet på **`< 5 MB / klipp`**. Hela **0 Blender**-pipelinen exklusive `SAM 3D Body` (dvs. `ffmpeg` + `Demucs` + `Whisper` + `YOLO11n-seg` + `RapidOCR` + `MoGe-2` + homografi) tar endast **`6.93 s`** på `spanjorskan` och **`14.61 s`** på `duepiani`.

---

## 2. Skalning till 100+ Klipp (Ekonomi & Genomsättning)

Vid skalning mot `100` klipp i samma storleksordning (`~14–20 s`, blanding av glesa `3`-tagningsklipp och täta `12`-tagningsklipp) på för-värmd Modal-pool av L4:

- **En varm L4-container (sekventiell)**: ~`30–63 s` per klipp -> **`50–105 min`** för `100` klipp.
- **10 parallella L4-workers (`modal .map()` med delade Read-Only viktvolymer `rum-moge2-vikter` + `sam3db-vikter`)**: **`~6–11 minuter`** total väggtid för `100` klipp.
- **Marginal GPU-kostnad för 100 klipp**: **`~$0.67 – $1.40` totalt** (plus ~$0.066 totalt för `29.82 s` kallstart utslaget per container vid $0.80/h).
- **Diskutrymme för 100 klipp**: **`~245 – 358 MB`** totalt lokalt lagringsutrymme (jämfört med tunga Blender-scenpaket och okomprimerade PNG/EXR-sekvenser).

---

## 3. Ärliga fel, begränsningar och avvikelser i benchmarken

Körningen blottlade tre konkreta kvalitetsproblem som måste adresseras före skarp produktionskörning på hela biblioteket:

### A. `spanjorskan s1` PCHIP-ablation spikar till `median = 289.2 mm, p90 = 3057.7 mm`
- **Orsak verifierad i `paket.json`**: Person `A` i `spanjorskan` har i `s1` (`0..168`) höftkoordinater `py = [1199, 5300] mm` (dvs. **`4.1 m` djupsprång**) med `max_step_mm = 750.2 mm/ruta`, medan person `B` i samma tagning är stabil (`py = [2840, 3087]`, `max_step_mm = 28.1 mm/ruta`).
- Den enkla RGB-histogram- och centeravstånds-spåraren (`local_tracks`, rad 576–604 i `modal_ingest_v2.py`) kopplade ihop skilda/delvis beskurna personer i för- och bakgrund under samma `pid = "A"`, så `SAM 3D Body` returnerade olika `pred_cam_t`-djup (`~1.2 m` vs `~5.3 m`). Ablationen mätte därmed **spårnings-/djupsprång (> 3 m)** och inte PCHIP-interpolationens artikulationsfel. På den stabilt spårade personen i `duepiani s1` (`py = [1079, 1355]`, `max_step_mm = 15.4 mm`) blev PCHIP-felet **`median = 14.0 mm, p90 = 31.9 mm`**.

### B. `duepiani mat_s10` hamnar på `z = 1.682 m` (och många person-ID:n `A..E`)
- **Orsak verifierad i `modal_ingest_v2.py` (rad 826–837) & `paket.json`**: I `duepiani s10` har spårad person `C` höfthöjd `pz = [1573, 1898] mm` och `ben_skymda = True` (bara överkropp nära kamera). Eftersom rad 754 endast jordar fotled till `FOTLED_OVER_GOLV` när `not is_sitting`, flyttades inte höga beskurna närbilder ner, och rad 830 satte bordskandidaten från `arm_z` (`~1.66 m`) -> `mat_s10` landade på `z = 1.682 m` i stället för normal bords-/diskhöjd (`0.72–1.05 m`).
- Samma klipp producerade även `5` person-ID:n (`A..E`) över `12` tagningar eftersom kors-tagnings-ReID enbart jämför ett 16×16-torsogram (`g_sim > 0.65`, rad 589–594) utan ansikts-/proportionell normalisering eller ByteTrack.

### C. `mat`-klassning och tagningsgränser jämfört med finjusterad `D-medielager`
- `ffmpeg`-tröskeln `scene > 0.3` detekterade `3` tagningar på `spanjorskan` och `12` på `duepiani`.
- Rad 543 klassar tagningar där både person och mat syns i YOLO som `person_med_mat`, vilket genererade ett `mat_*`-objekt på nästan alla tagningar (`11/12` i `duepiani`, `2/3` i `spanjorskan`), även när maten bara skymtar i förgrunden medan `mat` B-roll enbart var `t2` (`spanjorskan`) resp. `t8` (`duepiani`). För ren regigruppering bör `mat_tallrik`/`mat_skal`-primitivet i första hand bindas till renodlade `mat`-tagningar (eller synas tydligt kopplat till ett `bord`-ankare).

---

## 4. Konkreta optimeringssteg mot `< 20 s` per klipp

Eftersom `sam3d_och_pchip` står för **`77 %`** av GPU-tiden (`23.36 s` / `48.32 s`) ger följande ändringar störst direkt effekt utan nya GPU-typer:

1. **Kör `SAM 3D Body` på ~`2 fps` (eller adaptiva nyckelrutor efter handleds-/bålhastighet)** i stället för fast `3 fps` (~33 % färre framåtkörningar, sparar ~`8–16 s`/klipp) och hoppa över `pchip_ablation` i produktion (sparar 4 anrop).
2. **Sätt lägre personstorlekströskel för `SAM 3D Body`** (t.ex. `area > 0.04` så bakgrundsgäster inte körs) och **klipp-ByteTrack / ansikts-embedding** -> eliminerar felspårningar som `spanjorskan A` och falska extra anrop på bakgrundsstatister (`duepiani D/E`).
3. **`torch.compile` / BF16 autocast runt `SAM 3D Body` + `MoGe-2`** och batching av detekterade kroppar per bildruta i `process_one_image` i stället för sekventiell loop.
4. **Rigg-jordning per kropp + bords-klamp `[0.68, 1.12] m`**: klampa `bord_counter_candidates` `z` till rimlig bords-/diskhöjd och ankra delvis beskurna överkroppar till uppmätt bords-/golvnivå i stället för rå `SAM3DB` `pred_cam_t` i z-led.
