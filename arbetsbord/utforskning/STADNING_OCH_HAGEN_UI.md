# Utforskning: Repostädning, Arkivgränser & Integration mot `hagen-ui`

Sammanställning av faktisk diskanvändning mätt 20 nov 2026 samt rekommenderad gräns mellan aktiva kärnor, frysta referensexperiment och målsystemet **LeTrend (`../hagen-ui`)**. Inga filer har raderats automatiskt.

---

## 1. Faktisk Diskinventering per Rotkatalog

| Katalog | Storlek (MB) | Filer | Status enligt `CLAUDE.md` / `LAGE.md` | Rekommendation |
|---|---:|---:|---|---|
| `scen` | 55 870.1 | 191 325 | **Blandad**: äldre `scen/3d/`-kedja ersatt av `forvarld_karna/`, MEN innehåller aktiv `scen/.venv` + aktiv rå ingest-cache `scen/3d/ingest/ut/*` samt källklipp `scen/klipp/` | **Dela upp före städning**: behåll `scen/.venv`, `scen/klipp/` och `scen/3d/ingest/ut/` (`depth`, `sekvens_*.npz`, `semantik.json`); arkivera/rensa tunga temporära renderingar och dubblettvideor efter inventering |
| `forvarld` | 8 097.1 | 26 191 | **Forskningsarkiv**: SOMA/Kimodo-experiment (`forvarld/kropp/`), äldre världspaket | Frys som referensarkiv; flytta ev. tunga modellvikter/mellansteg ur git/arbetsyta vid diskstädning |
| `data` | 1 734.7 | 57 331 | **Aktiv delad bas**: `data/format/` (1 480 formatkort m.m.), delad med `../hagen-ui` | **Behåll**; undvik att lagra tunga temporära renderdump här |
| `motpart` | 1 499.1 | 21 634 | **Runda 1–3**: frysta spår `A–C` + ny körning `D-medielager/` (`_cache/`, `forhands/`, `granskning/`, `k8/`) | Behåll kod, `k8/` och `RAPPORT.md`; `D-medielager/_cache/` (Demucs/OCR-råfiler) och `forhands/` kan återskapas vid behov |
| `byggsten` | 398.3 | 1 727 | **Aktiv hjälpmodul + experiment**: `brygga/` (`grindar.py`, `emit_bpy.py`) och `hand/` är aktiva; `jutsu/` & `rumshypotes/` konsoliderade | Behåll `brygga/` och `hand/`; markera äldre `rumshypotes/` som historik |
| `weights` | 337.6 | 1 | Modellvikt (`Weights`) | Behåll lokalt eller samla med modellcache utanför kodträdet |
| `arbetsbord` | 43.4 | 182 | **Aktiv leverans i denna fas**: Three.js + Smart Kontext-LLM + Soundoverlay + Kontrastprov + Utforskning | **Primär kandidat att lyfta/porta in i `../hagen-ui`** (utan `.venv`/tunga caches) |
| `video` | 31.4 | 309 | **Aktiv**: videovertikaler och kalibrering (`localhost:5181`) | Behåll oförändrad tills migrering till `../hagen-ui` |
| `app` | 30.9 | 114 | **Fryst**: tidig CM-wireframe `#1..#6` (`localhost:5180`) | Frys som referens |
| `forvarld_karna` | 25.2 | 110 | **Aktiv verifierad 4-lagerskärna** (`obs_motor.py`, `rums_pussel.py`, `scen_brygga.py`, `mening_motor.py`) | **Behåll som huvudpipen för 3D-ingest & `scenpaket/2`** |
| `karta` | 17.2 | 75 | CM-vyer och arbetssätt | Behåll som specifikation |
| `exports` | 10.9 | 56 | Äldre exporter | Arkivera eller flytta vid städning |
| `delegat` | 0.4 | 97 | Tidigare agentkörningar | Arkivera |
| `_utkast`, `scratch` | 0.2 | 8 | Första HTML-utkast (`cm-flode.html`), tillfälliga filer | Arkiv/rensa vid tillfälle |
| `탖ላ\ue702㿾`, `쮈უǧ`, `襗\uefbc嘢㿥`, `ʰ蒑醢㿾` | 0.0 | 0 | **4 tomma mojibake-kataloger i roten** (teckenkodningsrester) | **Säkra att ta bort** (0 filer, 0 byte) efter bekräftelse med användaren |

*(Totalt ~67.7 GB, dominerat av `scen/` ~55.9 GB och `forvarld/` ~8.1 GB).*

---

## 2. Gränssnitt & Kontrakt mot `../hagen-ui`

Sökning efter `hagen-ui`-kopplingar i koden (`app/`, `video/`, `CLAUDE.md`, `LAGE.md`) visar vilka exakta kontrakt som redan delas mellan `hagen-wf` och produktrepot:
1. **Ingest-mätning (`artifacts/api-server/src/lib/ingest-v2/measure.ts`):** `app/analys/{verktyg,tolka,mat}.mjs` och `video/analys/` delar samma ffmpeg/ffprobe-mått och scengräns-tröskel (`DEFAULT_SCENE_THRESHOLD = 0.3`).
2. **LLM-anrop (`artifacts/api-server/src/lib/vertex-gemini.ts` & `evals/metrics.ts`):** Vertex AI / Gemini-anrop och tokenprissättning speglar produktionskontraktet.

### Vad som ska lyftas vs inte lyftas till `../hagen-ui`
- **Lyft in som renodlat CM-gränssnitt (`arbetsbord/` + `forvarld_karna/`-kontrakt):**
  - Klient: **`arbetsbord/web/scen3d.js`** + regibordets tidslinje-, skärmtext-, kamera-, ljud- och 2D/3D-jämförelsevy (`scenpaket/2`-läsare utan tunga beroenden).
  - Backend-motor: **`arbetsbord/motor/{schema,k7_vakt,operationer,manus,llm_regi}.py`** översatta eller exponerade bakom `hagen-ui` API-rutter så all live CM-redigering är icke-generativ (`K7 OK`), spårbar och ångerbar (`push_undo`).
  - Ljud- & medieoperationer: **`D-medielager/medielager/`** som separata jobb (Demucs-stammar + icke-destruktiva ffmpeg/Pillow-filter för skärmtext, b-roll från kundens eget material, montagekortning).
- **Lämna utanför `../hagen-ui`:**
  - Blender/Jutsu-rendering (`emit_bpy.py` förblir utvecklings-/verifieringsverktyg offline, aldrig prod-runtime i webbapp).
  - Per-klipp-skript i `scen/3d/`, experiment under `forvarld/kropp/`, samt GB-stora råcacher (`scen/3d/ingest/ut/` bakas ner till lätta JSON-paket + strömmade H.264/WAV-tillgångar i objektlagring).
