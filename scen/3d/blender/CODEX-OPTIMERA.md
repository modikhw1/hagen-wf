# Codex task A: optimize the motion against the source (analysis by synthesis in Blender)

Repo root: `C:\Users\praiseworthy\Desktop\hagen-wf`. Work under `scen/3d/blender/opt/` (new). You may read everything. Change the existing files only through new versions or flags; the current chain must keep working.
- Python: `scen/.venv/Scripts/python.exe` (3.12; torch CPU, scipy, mediapipe and ultralytics are installed). **No GPU.**
- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`.
- Read first: `scen/3d/README.md`, `scen/3d/blender/README.md`, `BAKE.md`, `LOGG.md`.

## Context
`scen/3d/blender/` holds a previs. `bygg_scen.py` builds the room, props and per-shot cameras from `scen3d.json`. Your previous task baked the X Bot motion from the three.js player into `bake.json` and `importera_bake.py`. `rendera.py` renders `ut/blockout.mp4` with the original audio. It is meant to be fed to a generative video model (Seedance/Kling) as layout and motion reference.

The transfer is exact, but the **underlying tracking** is not:
- the median joint reprojection error vs the source is 14–39 px per shot at 576×1024 (`scen/3d/README.md`);
- arms needed stabilising, the lower body is often occluded, and hands are uncertain;
- objects in hands are approximate.

**Owner's rule:** the original audio (`blender/ljud-original.wav`) must still fit bodies and mouths over the full duration of every shot. Do not shift gesture timing. Optimise what a video model actually sees: silhouette, gesture timing, contacts (sitting, hands on table or food, holding objects) and head/gaze direction. Image-space and timing metrics count; millimetres in 3D do not.

## Build
1. **Ground truth from the source** (`scen/klipp/d-dialog-notan.mp4`, 383 frames at 30 fps; per-shot `source.inSec`/`outSec` in `scen3d.json`), cached under `opt/gt/`:
   - **2D keypoints per frame** for the visible actor: body plus hands. Use the best CPU-feasible detector. Compare at least MediaPipe 2D image landmarks against one top-down 2D pose model (RTMPose/ViTPose via ultralytics or similar) on a few hand-labelled checks, and pick per joint by confidence.
   - **Person masks per frame**: SAM 2.1 (it was used before in `scen/luma/d-dialog-notan/`; reuse that environment or install CPU wheels) or YOLO-seg as a fallback. Report which you used.
   - **Events and contacts from Gemini**: model `gemini-3.5-flash-lite`, key `GEMINI_API_KEY_GRATIS` from `video/.env.local`. Never print or save the key. See `scen/3d/gemini_source3.mjs` for the call pattern. Ask for a JSON list of time-stamped contacts and events per shot, for example "B holds burger in right hand 8.53–9.37", "A seated whole shot", "C stands, left hand on hip", "A looks at B". Gemini is for **semantics and time windows only, never coordinates**. Spot-check its times against the keypoints and record the disagreements.
2. **Optional stronger 3D source:** try **one** of GVHMR, WHAM or TRAM (world-grounded SMPL with camera) on CPU for one shot. If it runs in reasonable time (≤ 15 min per shot), compare its reprojection error and temporal smoothness against the current MediaPipe-based motion. Do not spend more than about 25 % of your budget here. Report what happened either way.
3. **Optimisation in Blender** (`opt/optimera.py`, headless):
   - **Variables:** the root transform per frame, plus the rotations of spine, neck, head, shoulders, arms, forearms and hands. Alternatively use IK targets with constraints.
   - **Objective:** 2D keypoint reprojection through the existing per-shot source camera (`shots[].source.camera`; do not move the cameras, that was tried and rejected), plus mask IoU or silhouette distance, plus Gemini contacts as hard or soft constraints. Contact examples: hand–object distance under 3 cm while holding, pelvis on the seat while seated, feet on the floor.
   - **Regularisation:** temporal smoothness that **preserves gesture peaks**. Do not low-pass the timing away. Velocity extrema must stay within ±1 frame of the current bake, measured on the wrists and head.
   - **Mouth/face:** keep it as is (it is already exact against MediaPipe and the audio).
   - **Output:** `opt/bake-opt.json` in the same schema as `bake.json`, so `importera_bake.py` and `bygg_scen.py` can use it via a flag or path; add the flag. Hand-held props must follow the hands.
4. **Verification** (`opt/verifiera_opt.py`). Per shot, compare before (`bake.json`) and after (`bake-opt.json`):
   - median and 90th-percentile keypoint reprojection error (px);
   - mask IoU vs the source;
   - a jitter index (mean absolute acceleration);
   - gesture-peak timing shift (frames);
   - contact satisfaction (% of frames inside the Gemini windows).

   Render a side-by-side video: source | before | after, with the original audio, at `opt/jamforelse-opt.mp4`. Use H.264 **Main** profile, yuv420p, AAC stereo 48 kHz and `+faststart`; the owner's Windows player failed on other settings.

## Acceptance
- The median reprojection error per shot drops clearly, aiming for ≤ 10 px in S1–S6. Report honestly if it does not.
- Jitter does not increase. Gesture peaks stay within ±1 frame. Contacts hold in ≥ 90 % of the window frames.
- The mask IoU per shot does not drop.
- `bygg_scen.py` + `rendera.py` run end-to-end with the optimised bake.

Append decisions and numbers to `scen/3d/blender/LOGG.md`. End with a concise report: the numbers per shot before and after, what you compared and why, what failed, and the paths.
