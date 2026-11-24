# Codex task D: package the new pre-render pipeline (SAM 3D Body + MHR + COLMAP) into one command, and add face, room and a second clip

Repo root: `C:\Users\praiseworthy\Desktop\hagen-wf`. **Read `scen/3d/klipp2/PROCESS.md` first.** It records what was tried, what won and why. Your earlier task C (MediaPipe/MotionBERT/MPFB2) is superseded and is not to be continued.

## What exists and works (do not rebuild)
- Camera: COLMAP via `pycolmap` (`scen/3d/klipp2/colmap/kor.py`). It runs on every 3rd frame at 540×960, with YOLO person masks → 1.0 px.
- Body, hands and face parameters: **SAM 3D Body (ViT-H) on Modal GPU**: `scen/3d/klipp2/sam3db/modal_sam3db.py` (`scen/.venv/Scripts/modal.exe run ...`; volume `sam3db-vikter`, secret `huggingface`). It runs 365 frames in about 2 min. The local CPU venv `scen/3d/klipp2/sam3db/.venv` is only for MHR forward passes (fast).
- Sequence: `sam3db/skelett_sekvens.py` → `sekvens.npz` (MHR skeleton states, cam_t, expr, identity locked).
- World: `scen/3d/klipp2/varld.py` → `varld.npz` (metric COLMAP camera; scale chosen by smoothest person root; gravity from the spine).
- Blender: `scen/3d/blender/mhr_blender.py` (`importera`, `nyckla` camera-locked, `varld` + `nyckla_varld` world mode). It uses MHR's own `lod3.fbx` (Apache-2.0); the 127 joints equal the 127 bones, so **there is no retargeting**. 369 frames are keyed in 25 s.
- Results: `scen/3d/blender/gen/klipp2/jamforelse_mhr.mp4`, `scen/3d/klipp2/mhr_varld.blend`.

## Build (glue only; reuse the above)
1. ~~One command per clip~~ **Claude has built `scen/3d/ingest/ingest_klipp.py` (stages personer→kamera→kropp→sekvens→varld→blender→jamfor; multi-person with BoT-SORT ReID and fragment merging; Blender build in `scen/3d/ingest/mhr_rig.py`; tested on the bar clip, outputs in `scen/3d/ingest/ut/bar`). Do NOT rebuild it; extend it with items 2, 3 and 5 as new cached stages (uttryck, rum, seedance).** Original spec, for reference: `scen/3d/ingest_klipp.py <mp4> <utmapp> [--personer N]`. It runs YOLO-seg masks → COLMAP → Modal SAM 3D Body → sequence → world → a Blender `.blend` (world mode, floor plane at the lowest foot contact, camera keyed) → a Workbench render → `jamforelse.mp4` (source | overlay | render, with the source audio; H.264 **Main**, yuv420p, AAC stereo 48 kHz, `+faststart`). Cache every stage, so that it is skipped when its output exists. Log the time per stage.
2. **Face:** map SAM 3D Body `expr_params` (72) onto the FBX shape keys. First find out what the 118 shape keys of `lod3.fbx` are and whether the 72 MHR face expression coefficients correspond to a subset (check the MHR repo `docs/face-expressions.md`). If no direct mapping exists, use the MHR mesh with expressions from the model forward pass as a shape-key-per-frame (or a mesh cache) instead. The visible goal is that talking, mouth and brows read in the render.
   **Expression layer (owner's direction, from studying @unemployed_corp, `scen/3d/unemployed_corp/uttryck/ark.jpg`):** their faces are *directed archetypes held per beat* (smug half-lidded smirk, proud grin, bored look), not captured micro-motion. Implement `uttryck` as an ingest stage: (a) measure: MediaPipe FaceLandmarker 52 ARKit blendshapes per person per frame (local, CPU; reuse `scen/3d/klipp2/mediapipe.json` code if useful) plus the SAM 3D Body expr params; (b) interpret: segment per line/beat (use word timings if available, else 0.5–2 s windows of speech energy) and classify the dominant expression into a small archetype set (irritated, smug/smirk, proud, surprised, bored, neutral) with simple blendshape rules; (c) amplify: in the blockout, scale the leading shapes ×1.5–2 within each beat (smoothly ramped) so the expression reads at blockout resolution; (d) write `uttryck.json` per person: [{start, slut, arketyp, styrka, text_for_prompt}], e.g. "slightly irritated, raises eyebrows on 'jobb'". This JSON is what feeds the Seedance prompt's performance direction.

3. **Room:** from the COLMAP points (`colmap/sparse/1`, transformed with the same scale and gravity as `varld.py`), fit the floor plane (check it against the foot height) and the dominant wall planes (RANSAC). Put simple box proxies on dense clusters (the pool tables). Keep it crude and fast.
4. ~~Second clip, two people~~ (Claude does this in ingest_klipp.py). Original spec, for reference: `scen/klipp/kand-interpooluppsala-7601244778935766294.mp4` (two people behind a bar). Extend tracking to N people: YOLO IDs across frames (ByteTrack in ultralytics), one SAM 3D Body run per person box, one MHR rig per person. Report identity switches.
5. **Seedance-ready outputs** per clip, matching `scen/3d/blender/rendera.py` conventions: the blockout video with the original audio, the first frame per cut (this clip has none; the bar clip may), and a depth pass.

## Acceptance
- `ingest_klipp.py` reproduces klipp2 end-to-end from scratch, and the cached rerun takes under 1 min.
- The face visibly moves with speech in the klipp2 render (show 4 stills at speech frames).
- The floor plane agrees with the foot contacts within 5 cm.
- Bar clip: both people tracked with consistent IDs (or report the switches) and rendered.
- The time and cost (Modal seconds) per stage are reported.

Append to `scen/3d/klipp2/LOGG.md`. End with a concise report: numbers, paths, and what failed.
