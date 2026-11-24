> **STOPPAD 20 nov 2026 av ägaren.** Läs `STOPP_V2.md` innan något här återupptas.

# Exit Notes — Arbetsbord v2 (Överlämning)

**Tidpunkt:** `2026-11-20T19:41+01:00`  
**Orsak till avrundning:** Coordinator-fönstret nådde ~9 % kvarvarande kvot (`gemini-flash-worker-agy`, återställs `2026-11-20T21:38:41Z`). Samtliga swarm-arbetare stängdes rent (`hydrogen-motor`, `neon-kreativ`, `opus-arkitekt` är `killed`; inga bakgrundsjobb eller servrar körs). Opus (`34 %`) och Argon (`20 %`) har kvarvarande kvot för nästa agent/granskning.

---

## 1. Vad som är KLART och verifierat

### A. Tidigare v1-leverans (helt färdig & godkänd)
- [`arbetsbord/RAPPORT.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/RAPPORT.md), [`D-medielager/RAPPORT.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/D-medielager/RAPPORT.md), [`kimodo_kontrast/DOM.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/kimodo_kontrast/DOM.md)
- Utvecklingsnoter: [`IMAGEGEN_MALL_PILOT.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/IMAGEGEN_MALL_PILOT.md), [`LATT_INGEST_V2.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/LATT_INGEST_V2.md), [`JEV_SLUTSPURT.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/JEV_SLUTSPURT.md), [`STADNING_OCH_HAGEN_UI.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/STADNING_OCH_HAGEN_UI.md)
- K7-logg: [`arbetsbord/ut/k7_logg.jsonl`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ut/k7_logg.jsonl) (`100` poster, **`0` överträdelser**).

### B. v2 Steg 0 — Matematisk arkitekturspecifikation (Opus)
`opus-arkitekt` (#14 på boarden) fastställde kraven som styr motor & ingest:
- **Bålram**: Gram-Schmidt med `det = +1` (fallback till `upleg`-par om `spine0..3` är kollineära).
- **Ryggrads-FK**: viktfördelning `0.15 / 0.25 / 0.30 / 0.30` över `c_spine0..3` i float-meter, rotera **hela överträdet** (`clavicle..index1`, `neck..head..huvud_upp/nasa_mal`) stelt, runda till hel-mm sist och återprojicera på personens medianbenlängder (ingen kordaförkortning). `nasa_mal` delas `40 % neck / 60 % head`, kläms yaw `±70°` och pitch `±40°`.
- **2-bens arm-IK + G4**: `acos` klämd i `[-1, 1]`, nyckelbensstöd `≤ 15–20°` och soft-IK ovan `0.97*(L1+L2)`, polvektor ur originalarmbågen, stel hand-offset efter IK. G4-kollisioner mot bord/andra kapslar löses genom att **flytta IK-målet**, inte bryta benlängder.
- **`speed_corr_0`**: additivt delta-lager med 6–10 rutors tidsramp på originalbanan; ingen tidsomsampling; strikt K7 (ingen `l↔r`-spegling).
- **`tilltro` & lokalt kamera-`u`**: per-led-och-ruta `tilltro` (`observerad` / `harledd_mall` / `skymd_antagen`, värsta ändled ärvs), lokal kamerakurva `u ∈ [0,1]` efter retime.

### C. v2 Steg 2 — Frontend v2 (Färdig på disk, webbläsarverifiering kvar)
Skapad av `neon-kreativ` (#17), verifierad med `node --check` (exit `0` på både `scen3d.js` och `app.js`):
- [`arbetsbord/web/scen3d.js`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/web/scen3d.js) (`64,302 B`):
  - Vektoriserade mat-primitiver (`mat_tallrik`, `mat_skal`, `mat_bricka`) med `CanvasTexture` från `o.farg_palett` + garnityr.
  - `setShowTilltro(bool)` & `setKroppsKontrakt(k)` + 3:e argument i `loadScene(ts.scen, tema, ts.kropps_kontrakt || null)`: solid rendering för `observerad`, halvtransparent (`opacity: 0.28`) + cyan wireframe (`#4dd6ff`) för `harledd_mall` / `skymd_antagen`.
  - `_updateLabelsForCamera` klampar 3D-etiketter mot FOV/avstånd (max `34 %` bredd, mjuktonar ut vid `< 1.1 m`).
- [`arbetsbord/web/app.js`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/web/app.js) (`71,418 B`), [`index.html`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/web/index.html) (`16,964 B`), [`styles.css`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/web/styles.css) (`30,007 B`):
  - `#tilltroToggleBtn` i verktygsraden + `window.__arbetsbordDebug.{setShowTilltro, provaOrakel}` och `showTilltro` i `getState()`.
  - Panel **`Kroppsorakel & Kinematik`**: `#orakelPersonSelect`, reglage `#orakelSlapphet` (`-0.4..0.4`), `#orakelLutning` (`-12..12°`), `#orakelGest` (`0.4..1.6`), `#orakelProvaBtn`, `#orakelAppliceraBtn`, `#orakelHandIkBtn` (`hand: 'vanster', dz: 0.15`), `#orakelResultat`.
  - Panel **`Matshot & Rytm`**: `#matshotForm`, `#matshotTagningSelect`, `#matshotRattInput`, `#matshotStilSelect`, `#matshotKameraSelect`, `#matshotUpdateBtn`.
  - Regi-kort: renderar `llm_svar.orakel_granskning` (eller `res.orakel_granskning`).

**Exakt API-kontrakt som frontend (`app.js`) förväntar sig:**
- `POST /api/ladda` -> `tillstand.kropps_kontrakt` (`{ personer: { A: ... }, ... }`, vid behov även exponera `duepiani` och `spanjorskan` i `/api/klipp` / `lista_klipp()`).
- `POST /api/orakel/prova` med payload `{ session_id, op, params }` -> JSON `{ orakel: { dom: "rimlig"|"delvis_rimlig"|"orimlig", ms: float, poang: { fysisk, kontext, rytm }, tilltro_notis?, forslag_justering?, flaggor?: [] } }` (alternativt fälten direkt i rot-JSON).
- `POST /api/op` (via `runQuickOp`) måste stödja:
  - `kropp_attityd`
  - `kropp_hand_ik` (`{ person_id, hand: "vanster", dz: 0.15, tagning_id }`)
  - `matshot_uppdatera` (`{ tagning_id, ratt_namn, stil, kamera_rorelse }`)
- `/api/regi` -> `llm_svar.orakel_granskning`: lista med `{ op, dom: "rimlig"|"delvis_rimlig"|"orimlig", godkand?: bool, poang?: { total?, fysisk, kontext, rytm }, tilltro_notis?, forslag_justering? }`.

### D. v2 Steg 3 — Modal L4 GPU-Ingest v2 (Körd skarpt & dokumenterad)
- Skript: [`arbetsbord/ingest_v2/modal_ingest_v2.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ingest_v2/modal_ingest_v2.py) (`53,706 B`, `py_compile` OK) körd på **NVIDIA L4** (`rum-moge2-vikter`, `sam3db-vikter`, `hagen-ingest-v2-cache`) för 2 riktiga klipp:
  - **`spanjorskan`** (`13.72 s`, `411` rutor, `3` tagningar, `33` SAM3DB-anrop): `total_ingest_s = 30.28 s` (`sam3d_och_pchip = 23.36 s`, `wall_inkl_natverk_s = 79.12 s`, `var_varm = false`, `est_marginal_usd = $0.0067`), paket **`2,567,955 B` (`2.449 MB`)** (`2.450 MB` inkl. rapport).
  - **`duepiani`** (`19.44 s`, `583` rutor, `12` tagningar, `73` SAM3DB-anrop): `total_ingest_s = 62.94 s` (`sam3d_och_pchip = 48.32 s`, `wall_inkl_natverk_s = 67.34 s`, `var_varm = true`, `est_marginal_usd = $0.0140`), paket **`3,752,619 B` (`3.579 MB`)** (`3.580 MB` inkl. rapport).
- Data finns i [`arbetsbord/data/ingest_v2/`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/data/ingest_v2/ingest_v2_benchmark.json) (`spanjorskan/` och `duepiani/` med `paket.json`, `tidslinje.json`, `proxy_h264.mp4`, `tal.wav`, `ingest_rapport.json`).
- Rapport skriven: [`arbetsbord/ingest_v2/SKALNING_RAPPORT.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/ingest_v2/SKALNING_RAPPORT.md) (`7,560 B`) inklusive ärlig rotfelsanalys av:
  1. `spanjorskan s1` PCHIP-spik (`median = 289.2 mm, p90 = 3057.7 mm`) orsakad av att person `A` har `4.1 m` djupsprång (`py = [1199, 5300] mm`) p.g.a. hopkopplad spårning, medan stabila `duepiani s1` (`py = [1079, 1355] mm`) gav `median = 14.0 mm, p90 = 31.9 mm`.
  2. `duepiani mat_s10` hamnade på `z = 1.682 m` (beskuren närbild `pz = [1573, 1898] mm`) + `5` person-ID:n (`A..E`) p.g.a. enkel histogram-ReID.
  3. Överklassning av `person_med_mat` (skapade `mat_*`-objekt på `11/12` tagningar i `duepiani`).

---

## 2. Vad som är HALVKLART (Steg 1 — avbrutet för kvotskydd)

- **Klar ny modul:** [`arbetsbord/motor/kinematik.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/motor/kinematik.py) (`40,655 B`, `1004` rader, `py_compile` OK) skapades av `hydrogen-motor`.
  - Toppnivåfunktioner i AST: `led_index`, `normalisera_hand_sida`, `mat_from_wxyz`, `wxyz_from_mat`, `rot_axis`, `rot_from_vecs`, `_norm_vec`, `bygg_balram`, `rotera_subtrad`, `berakna_person_median_segment`, `kvantisera_med_medianlangder`, `max_benlangdsdrift_mm`, `speed_corr_0`, `punkt_i_obb`, `dist_till_obb`, `ray_traffar_silhuett_obb`, `sampla_kamera_vid_ruta`, `kamera_basvektorer`, `projicera_punkter`, `_smoothstep`, `_moving_average_1d`, `applicera_kropp_attityd_pa_sp`, `_arm_ik_2ben`, `_resolve_g4_target`, `applicera_kropp_hand_ik_pa_sp`, `hitta_matshot_placering`, `applicera_kamerakurva_pa_tagning`.
- **Återstår i Steg 1 (ej skrivna än):**
  1. `arbetsbord/motor/kropp_orakel.py`: `extrahera_kropps_kontrakt(scen, media)` + `prova_forslag(scen, kontrakt, op, params, media=None)` (< 10 ms: fysiska gränser/OBB-kollision/benlängdsbevaring, kontextuell G4+frustum/tilltro, rytmisk `speed_corr_0`).
  2. Uppdatera [`operationer.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/motor/operationer.py) med `kropp_attityd`, `kropp_hand_ik`, `matshot_uppdatera` (baserat på funktionerna i `kinematik.py`, med bibehållen K7-spärr & per-led `tilltro`).
  3. Uppdatera [`schema.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/motor/schema.py), [`ladda.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/motor/ladda.py) (exponera `spanjorskan` & `duepiani` från `arbetsbord/data/ingest_v2/` inklusive proxyvideo/tal.wav och initial `kropps_kontrakt`), [`llm_regi.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/motor/llm_regi.py) (`orakel_granskning` innan mutering), och [`server.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/server.py) (`POST /api/orakel/prova` samt `/media/video/<nyckel>` & `/media/tal/<nyckel>` för `ingest_v2`).
  4. Skriv och kör `arbetsbord/prov/test_kropp_orakel.py` -> spara `arbetsbord/ut/kropp_orakel_benchmark.json` (verifiera `< 10 ms`, `< 1 mm` benlängdsdrift, `0 cm` fotglid, `speed_corr_0 >= 0.90`, `"orimlig"` hinderavvisning, `asketch s6` matshot-uppdatering, `duepiani`/`spanjorskan`-laddning, samt kontrast mot `kimodo_kontrast/DOM.md`).

---

## 3. Vad som ÅTERSTÅR för nästa agent (Steg 4 & 5)

1. **Slutför & testa Steg 1** ovan (`py_compile` + `.\scen\.venv\Scripts\python.exe -X utf8 arbetsbord/prov/test_kropp_orakel.py`).
2. **Starta daemon:** `.\scen\.venv\Scripts\python.exe -X utf8 arbetsbord/server.py --port 5199`.
3. **Skriv & kör visuell/UI-verifiering v2** (Playwright + SwiftShader, spara och granska ALLA bilder med `read_file` per `AGENTS.md`):
   - `arbetsbord/prov/rendera_v2_kontrast.mjs` -> side-by-side (`Original` + `3D v2`) kontaktkartor:
     - `arbetsbord/ut/kontakt_v2_guacamole_attityd.png` (`guacamole s4` + `kropp_attityd`)
     - `arbetsbord/ut/kontakt_v2_gelato_hand_ik.png` (`gelato s1` + `kropp_hand_ik`)
     - `arbetsbord/ut/kontakt_v2_asketch_matshot.png` (`asketch s5–s7` + `matshot_uppdatera` `s6`)
     - `arbetsbord/ut/kontakt_v2_duepiani_ingest.png` (`duepiani` GPU-ingest vs `data/format/kontroll/klipp/duepiani-7650849186912406806.mp4`)
   - `arbetsbord/prov/verifiera_v2_ui.mjs` -> `arbetsbord/ut/ui_check/v2_ui_check.json` + `v2_tilltro.png`, `v2_orakel_och_matshot.png`, `v2_regi_orakel.png` (inkl. `duepiani`/`spanjorskan` med `206` media & icke-svart canvas).
   - Kör om `node arbetsbord/prov/verifiera_ui.mjs` och `node arbetsbord/prov/verifiera_media_och_video.mjs` mot ev. regressionsfel.
4. **Skriv korta utforskningsnoter** (med verifierade tal):
   - `arbetsbord/utforskning/KROPPSORAKEL_OCH_JEV_BRO.md`
   - `arbetsbord/utforskning/MALL_UTZOOMNING_TILLTRO.md`
5. **Slutlig oberoende audit (Opus / Argon)**, åtgärda fynd + omkör tester, stäng `:5199`-servern och skriv [`arbetsbord/RAPPORT_V2.md`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/RAPPORT_V2.md).

---

## 4. Skydd & Regler som inte får brytas
- **Skrivskyddade ytor** (konstaterat orörda vid överlämning): `forvarld_karna/`, `motpart/`, `app/`, `video/`, `scen/`, `CLAUDE.md`, `LAGE.md`. All kod och utdata hålls inom `arbetsbord/`.
- **K7**: Noll generativ bild/video/röst, noll spegling (`byt_hand`).
- **`AGENTS.md`**: Lyckad kodkörning/rendering gäller inte som godkänd förrän renderingar/screenshots är visuellt granskade med `read_file` och avvikelser (t.ex. `duepiani mat_s10`) är ärligt redovisade.
