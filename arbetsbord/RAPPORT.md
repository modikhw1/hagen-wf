# Slutrapport: Arbetsbord, Spår D (Medielager), Kimodo-Kontrast & Utforskning

Sammanställning av leveranser och empiriska resultat från samtliga fyra arbetsspår i `hagen-wf` (slutfört 20 nov 2026), inklusive oberoende läsgranskning (`read-only`) av **revisor (`gemini-4-argon-high`) -> SLUTDOM: GODKÄND**.

---

## 1. Spår 1 — `D-medielager` (`motpart/runda-3-opus/D-medielager/`)

Fullständig rapport: [`motpart/runda-3-opus/D-medielager/RAPPORT.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/RAPPORT.md)

- **Kodfrysning & Integritet:** Alla 17 källfiler hashas i [`FRYST_KOD.txt`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/FRYST_KOD.txt) (`17/17` SHA256-verifierade före och efter `holdout` + utvecklingsingest).
- **K8 Urval (20 klipp, 80 ops) & Hold-out (4 obekanta klipp, 16 ops):**
  - Urval (`ok` / `syns_ej` / `rest_andr` / `nej` / `motfraga` / `fel`): `skarmtext` `8/2/1/2/2/5`, `ljud` `7/8/2/3/0/0`, `broll` `0/0/1/19/0/0`, `montage` `1/3/4/12/0/0`. Ingest median `17.2 s` (cachad via `forbered.py`), max `76.7 s`.
  - Hold-out: `skarmtext` `1/0/0/1/2/0`, `ljud` `1/2/0/1/0/0`, `broll` `0/0/0/4/0/0`, `montage` `1/0/1/2/0/0`. **0 krascher**, ocachad ingest `79.1–138.0 s` (median `93.8 s`).
  - **`rätt hanterat*` = `0/0` i [`SAMMANSTALLNING.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/k8/SAMMANSTALLNING.md):** Beror på att `k8/facit_mitt.json` saknas för automatisk facitjämförelse; bedömning har gjorts via JSONL-mått och visuell inspektion av 9 kontaktkartor i `granskning/`.
  - **Felinjektion & K7:** **`32/32` (`100 %`)** injektioner larmade; **0 generativa anrop** över samtliga `96` operationer; operationstid (43 utförda) median **2.5 s**, max **18.5 s**.
  - **Känd bugg i fryst kod inför v2:** 5 `skarmtext`-krascher i urvalet (`ffmpeg d_boxblur_2 ... -22`) orsakas av att [`operationer.py:126`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/motpart/runda-3-opus/D-medielager/medielager/operationer.py#L120-L130) klampade `rad` mot `w//2` och `h//2` men inte `yuv420p`-krominansplanet (`w//4, h//4`) på smala textrutor.
- **Utvecklingsingest för Arbetsbordet (`arbetsbord/data/medielager/`):**
  - Alla 5 klipp ingestade: `d-dialog-notan` (`125.9 s`), `e-dialog-guacamole` (`66.3 s`), `kand-kennysgelato2.0-7596403003901381910` (`165.6 s`), `a-sketch-servering` (`133.0 s`), `b-tilltal-ravara` (`181.2 s`).

---

## 2. Spår 2 — Förvärldens Arbetsbord (`arbetsbord/`)

Three.js 9:16-regibord (`Z`-upp, exakt `scenpaket/2`-kamera och `BEN1`-armatur), DAW-tidslinje, 17 snabba deterministiska operationer, Smart Kontext-LLM (`gemini-3.5-flash` / `gemini-3-flash-preview` / `codex` fallback), live K6-manus och K7-spärr:

- **UI- & Funktionsverifiering ([`ui_check/rapport.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/ui_check/rapport.json)):**
  - Alla 5 utvecklingsklipp (`notan`, `guacamole`, `gelato`, `asketch` med `har_3d=true`; `btilltal` med `har_3d=false`) laddade utan fel; `0` console-, page- eller HTTP `>=400`-fel.
  - 9:16-canvas (`390x694`, `aspect=0.5607`, `nonBgFrac=0.71–0.89`), deterministiska snabboperationer `1 278 ms` för hela testsviten inkl. Ångra/Återställ, samt 3 skarpa `/api/regi`-körningar (`guacamole -> kok`, `notan -> kafe`, `gelato -> bar`).
  - **Feedback & K7:** **`8` poster** i [`feedback_logg.jsonl`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/feedback_logg.jsonl) och **`100` poster / `0` brott** (`91` utförda + `9` korrekt blockerade spärrtester mot `byt_hand`/`spegla`/`generera_video`) i [`k7_logg.jsonl`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/k7_logg.jsonl).
- **Ljudspår & Webbläsarvideo ([`media_check.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/ui_check/media_check.json)):**
  - Uppdaterade [`ladda.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/motor/ladda.py#L176-L185) att söka i `arbetsbord/data/medielager/lager/`.
  - `/api/ladda` returnerar nu aktiv `media.tal_url` för samtliga `5/5` klipp.
  - Range `206 Partial Content` med giltigt `RIFF....WAVE`-huvud verifierad på `/media/tal/guacamole` (`1 765 702 B`) och `/media/tal/notan` (`2 249 030 B`).
  - On-demand H.264-proxy i [`server.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/server.py#L115-L181) löser HEVC-avkodningen i headless Chrome: `guacamole_h264.mp4` (`3 163 166 B`), verifierad i [`guacamole_bredvid.png`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/ui_check/guacamole_bredvid.png) (`readyState=4`, `576x1024`, `mean=102.02`, `std=44.93`).
- **Soundoverlay-videor ([`soundoverlay_rapport.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/soundoverlay_rapport.json)):**
  - Renderade och visuellt granskade i 30 fps 9:16 sida-vid-sida med ljud: [`soundoverlay_notan.mp4`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/soundoverlay_notan.mp4) (`383` rutor, `3 083 077 B`), [`soundoverlay_guacamole_orig.mp4`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/soundoverlay_guacamole_orig.mp4) (`299` rutor, `1 917 653 B`) och [`soundoverlay_guacamole_kok.mp4`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/soundoverlay_guacamole_kok.mp4) (`299` rutor, `1 952 542 B`) med tillhörande kontaktkartor.

---

## 3. Spår 3 — Kimodo-SOMA-RP Kontrastprov ([`DOM.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/DOM.md))

**Slutlig dom: KILL för 1:1-regering, känsloregi och halvkropps-/diskscener.**

Kört i en cachad Modal A10G-körning (`load_s = 46.76 s`, `wall_s = 114.41 s`, total kostnad `$0.0247`, data sparat i [`matning.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/matning.json)) med lokal Three.js + soundoverlay-rendering ([`render_logg.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/render_logg.json)):

1. **Fall 1 (runda hörn, `guacamole s4 B`, `ben_synliga=0.0`):** `10.61 s` (`$0.0068`). Träffar `root2d`-mål tätt (`2.72–2.96 cm`), men ger `102.07–151.69 cm` fotglidning, förstörd talsynk (`speed_corr_0 = -0.19..+0.16`) och bänkgenomträngning i [`kontakt_fall1.png`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/kontakt_fall1.png).
2. **Fall 2 (vänster hand +15 cm utan spegling, `gelato s1 A`, `ben_synliga=0.95`):** `9.51 s` (`$0.0065`). **`spegling_misstankt = false` (4/4)**, `7.15 cm` handmålfel, låg glidning (`7.10–11.95 cm`), men svagare talsynk (`0.05–0.40`) och diskkollision i [`kontakt_fall2.png`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/kontakt_fall2.png).
3. **Fall 3 (känslokontrast `s=1.0` vs SDEdit `s=0.55` via `model.denoising_step`, `45` hoppade / `55` körda DDIM-steg):**
   - `s=1.0` (`8.91 s`, `$0.0063`): `14.67–19.06 cm` ledändring men död talsynk (`-0.31..+0.21`) och höjt huvud (`-3.60..+0.45 cm`).
   - SDEdit `s=0.55` (`5.07 s`, `$0.0051`): **`speed_corr_0 = 0.9111–0.9324` (`lag=0`)**, men nästan osynlig attitydskillnad (`4.10–4.52 cm`) kombinerad med **`34.57–46.58 cm`** fotglidning ([`kontakt_fall3.png`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/ut/kontakt_fall3.png)).
- **Ersättning:** Kinematiska attitydlager + lokal 2-leds-/CCD-IK ovanpå `T1` (`< 5 ms`, `$0`, `0` fotglidning, `G1–G7` kollisionskontroll).

---

## 4. Spår 4 — Utforskning & Noter (`arbetsbord/utforskning/`)

- [`IMAGEGEN_MALL_PILOT.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/IMAGEGEN_MALL_PILOT.md): OpenAI image-gen (`codex_bild.py`, `56.0–80.5 s`/ruta) reducerade bruskanter med **`90.6 %` (`guacamole_s1`)**, **`63.2 %` (`asketch_s7`)** och **`72.3 %` (`gelato_s1`)** vid sub-pixel/`1.6 px` förskjutning, tog bort diskreflektioner och fyllde i skymd underkropp bakom klarglas i `gelato_s1` (flaggat som syntetiserad prior, ej mätt ground truth).
- [`LATT_INGEST_V2.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/LATT_INGEST_V2.md): Lättviktsarkitektur utan Blender i produktion (tung engångs-ingest -> `scenpaket/2` + `medielager/1` + H.264/WAV -> blixtsnabb Three.js-redigering).
- [`JEV_SLUTSPURT.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/JEV_SLUTSPURT.md): Varför Smart Kontext-LLM (`6.2–27.1 s`) + `feedback_logg.jsonl` samlar *happy paths* först och kompilerar Jev (`< 250 ms`) först när modulerna under är låsta.
- [`STADNING_OCH_HAGEN_UI.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/STADNING_OCH_HAGEN_UI.md): Diskinventering (~67.7 GB vid mättidpunkt, dominerat av `scen/` ~55.9 GB och `forvarld/` ~8.1 GB + 4 tomma mojibake-kataloger) samt integrationsgräns mot `../hagen-ui`. *(Efter slutrenderingar/dev ingest är `arbetsbord/` `64.0 MB / 237 filer` och `motpart/` `1 505.5 MB / 21 665 filer` enligt `revisor`s slutkontroll.)*

---

## 5. Oberoende Revision & Driftsättning

- **Revisor (`gemini-4-argon-high`):** Verifierade `17/17` SHA256-hashar i `FRYST_KOD.txt`, rekursiva mtimes över samtliga skrivskyddade kataloger/filer (`0` skrivskyddsbrott), K7 (`0` brott över `100` rader), samt varenda citerad siffra och filstorlek (`0` räknefel/sakfel -> **SLUTDOM: GODKÄND**).
- **Starta arbetsbordet lokalt vid behov** (testservern på `:5199` avslutades rent vid avlämning):
  ```powershell
  $env:PYTHONIOENCODING="utf-8"
  .\scen\.venv\Scripts\python.exe -X utf8 arbetsbord\server.py --port 5199
  ```
