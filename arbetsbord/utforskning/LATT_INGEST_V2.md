# Utforskning: Lätt 3D-Ready Ingest v2 (Utan Blender i Produktion)

Anteckning över hur ett uppladdat 9:16-klipp kan brytas ner till en lätt, redigerbar **Förvärld** (`scenpaket/2` + `medielager/1`) utan att behöva Blender, Jutsu eller GB-stora mappar i produktionsdrift — baserat på verifierade körningar i `forvarld_karna/`, `D-medielager/`, `arbetsbord/` och `mall_pilot/`.

---

## 1. Princip: Tung engångs-ingest vid uppladdning -> Lätt CM-runtime

För CM i webbläsaren (`arbetsbord/web/scen3d.js`) behövs aldrig rå video per ruta i 3D-motorn eller en Blender-process:
1. **Råa ingester körs asynkront en gång per källklipp** och kokas ner till kompakta webbtillgångar:
   - `paket.json` (`scenpaket/2`): kameranycklar per tagning (`pos`, `rot`, brännvidd/FOV, sensor, statisk vs rörlig), rumsobjekt (`bord`, `disk`, `skylt`, `prop` med synlighetsintervall) och 28-/26-leders kroppsrörelser.
   - `tidslinje.json` (`medielager/1`): tagningar, OCR-skärmtexter med koordinatrutor, tal-/musiksegment (`k7`), matklassning samt `tider_s`.
   - `tal.wav` / Demucs-stammar + H.264-webbproxy (behövs eftersom fyra av fem testade råklipp — `guacamole`, `gelato`, `asketch`, `btilltal` — ligger i HEVC som huvudlös Chromium inte avkodar direkt i `<video>`).
2. **CM-loopen körs helt i Three.js + ren Python/TS-kompilator** (`arbetsbord/motor/`):
   - WebGL i webbläsaren (`Scen3DRenderer`) hanterar snabb scrub, miljöteman (`original`, `kok`, `kafe`, `bar` m.fl.), kameraomlänkning (`kamera_justera`), tidsförkortning/pauser och 3D-rekvisita direkt utan Blender-renderingskö.
   - I denna arbetsfas tog en enda hel UI-verifierad omregi-cykel med snabba operationer `1 278 ms` för 5 steg + ångra/återställ (`arbetsbord/ut/ui_check/rapport.json`), och `0` K7-brott över 100 loggade operationer (`k7_logg.jsonl`).

---

## 2. Rekommenderad Pipeline för Lätt Ingest v2 (4 Steg)

1. **Steg A — Deterministisk medieanalys & separation (lokalt/worker):**
   - `ffprobe` + scenklippdetektering (`DEFAULT_SCENE_THRESHOLD = 0.3` i `app/analys/tolka.mjs`, eller `D-medielager` scenklipp + nyckelrutor).
   - OCR (`steg_text.py`) för pålagda texter och tidsfönster (`tidslinje.json:skarmtext`).
   - Demucs-källseparation (`steg_separation.py`) -> sparar ren röststam `tal.wav` + musiksänkningsmått i förväg så ljudreglage i arbetsbordet (`Tal`, `Original`) inte kräver någon generativ modell vid redigering.
   - Transkodning av HEVC-original till snabb webbläsarvänlig H.264-cache (`_konvertera_video_till_h264` i `arbetsbord/server.py`) så sida-vid-sida-uppspelning alltid fungerar.
2. **Steg B — Valfritt "Mall"-städningsspår för svåra vinklar (`mall_pilot`):**
   - Endast om monokulär djup-/pose-pipeline misslyckas p.g.a. spegelreflexer, tät text eller hängande bråte (t.ex. `guacamole_s1` med 90.6 % kantreduktion eller `asketch_s7` utan spegelbild i svart disk) körs image-gen-förenkling på **1 nyckelruta per svår tagning** som geometrisk referensram.
   - Om image-gen fyller i skymd anatomi (`gelato_s1` bakom disken) ska dessa leder markeras som syntetiserad prior, inte rå observerad position.
3. **Steg C — Rumspussel & Kameraseparation (`forvarld_karna/`):**
   - MoGe djup/normaler + kroppsspårning + rumspussel (`obs_motor.py` -> `rums_pussel.py` -> `scen_brygga.py`), inklusive separering av kamerarörelse från kroppsrörelse (`R25_separera_kamerarorelse`) och grindvalidering (`G1–G7`).
   - Resultatet fryses i `scenpaket/2` så allt kamerautsnitt, klipp, kropp och synlighet ärvs 1:1 som default.
4. **Steg D — Rollout utan Blender i produktion:**
   - **Blender / `emit_bpy.py`** behålls endast som intern referens-/verifieringsbänk vid utveckling av ingest mot `jamforelse.png`.
   - **Three.js (`Scen3DRenderer`)** är både det interaktiva regibordet för CM och den visuella sketchen som levereras vidare (tillsammans med soundoverlay-tidslinje och manus) eller matar eventuell slutrendering.

---

## 3. Identifierade Luckor inför v2

- **Klipp utan `scenpaket/2` (t.ex. `b-tilltal-ravara`):** I nuläget saknar `btilltal` eget 3D-paket (`har_3d: false` i `ui_check/rapport.json`) och föll bara tillbaka på 2D-video + tidslinje/manus i UI:t. Lätt Ingest v2 måste hantera både fullt 3D-paket och degradera graciöst när djup/pose bara finns delvis.
- **CPU-kostnad i `D-medielager`:** Demucs på CPU gjorde 5-klipps-ingesten långsam (exempelvis `125.9 s` enbart för `d-dialog-notan`); i produktion ska Demucs köras på GPU-worker asynkront direkt vid uppladdning.
- **Frysbugg i skärmtext (`d_boxblur_2`):** `kor_k8.py` visade 5 krascher i `D-medielager` på `skarmtext` p.g.a. att `boxblur`-radien inte var klampad mot små OCR-rutor (`Failed to evaluate filter params: -22`). Den fixa bör göras vid v2-lyftet från fryst K8-kod.
