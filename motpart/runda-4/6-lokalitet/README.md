# Lokalitet/1: allmän ingest av rum per tagning

Mål: en pålitlig och abstraherad nollpunkt (0.0) före all modifiering. Samma kod körs på alla klipp utan manuell inmatning och utan klippkonstanter. Varje mått bär sin källa: uppmätt, skattat eller antaget.

Kedja (lokal CPU, 0 USD):

1. `observera.py <klipp> --nyckel <namn>` läser tre nyckelrutor per tagning. MoGe-2 ViT-S ger punkter, normaler och fokal. SegFormer-B2 ADE20K ger 150 etiketter. Resultatet cachas per källhash och modellversion. Tagningar tas ur ingest_v2-paketet om det finns, annars ur klippdetektorn.
2. `pose2d.py <klipp>` (körs med `scen/.venv`) ger 2D-led ur originalet för kamerans registrering.
3. `lokalitet.py <nyckel>` tillämpar reglerna L1–L6 (se docstring) och skriver `ut/<nyckel>/paket_L.json` (scenpaket/2) och `ut/<nyckel>/lokalitet.json`.
4. `server.py` på port 5206 visar original | A | (B) | L per klipp. Bedömningar sparas i `ut/svar.jsonl`.
5. `node fanga.cjs <nyckel>` skriver rutor ur varje tagning till `ut/<nyckel>/qa/`.

Kedjan nu (22 nov):

1. `modal_obs.py` kör MoGe-2 ViT-L, OneFormer och GeoCalib på Modal-GPU.
2. `pose2d.py` kör yolo11n-pose lokalt.
3. `modal_kropp2.py` bygger spår per tagning och kör SAM3D.
4. `lokalitet.py` tillämpar reglerna L1–L9, L3b–L3e och L8.
5. `server.py` visar resultatet på port 5206.

6. `rumshjarna/hjarna.py <klipp>` tar fram genererat rum utan förgrund som hypotes. Lokaliteten släpper bara igenom det efter grind 1b. Se `rumshjarna/RUMSHJARNA.md`.

Oberoende vittnen: `vittne_vp.py` (vertikaler), plus `vittne_ellips.py` och `vittne_plan.py` (negativa resultat för bilder ovanifrån, inte inkopplade). Grindar: `test_grindar.py`.

Externa granskare: Codex (`CODEX_KONTROLL.md` → `ut/codex/`) och Gemini via agy (`AGY_GRANSKNING*.md` → `ut/agy/`). Överblick i `RAPPORT.md`.

`kor_obs.sh` kör steg 1 för provets fem klipp: Due Piani och Spanjorskan (med kroppsspår) samt 08burgerkebab, babasburgers och kennysgelato2.0 (hold-out, bara rum).

Isolerad miljö: `.venv` (torch CPU, MoGe, transformers). `scen/.venv` rörs inte.
