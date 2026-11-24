# Scen3D: a real, editable 3D reconstruction of one sketch clip

You are working in `C:\Users\praiseworthy\Desktop\hagen-wf`. Write ONLY inside `scen/3d/` (create subfolders as needed). Everything else is read-only input. Never print, copy or log API keys.

## Why this exists

LeTrend helps restaurant staff remake proven short-video formats. We want an engine where an example clip becomes a **3D scene spine**: a room with real objects, rounded stylized characters driven by the clip's own motion, real 3D cameras, timing and dialogue. An orchestrator (Claude) then edits the scene semantically by editing JSON, for example "swap the burger for pizza", "dolly in on her punchline", "the waiter turns toward her", "orbit around his table". The browser replays the result instantly. **Photorealism is not a goal.** Clean, low-poly, readable 3D is.

Two earlier attempts were rejected by the owner as useless, and you must not repeat them:
- 2D keypoint tracks drawn as stick figures.
- 2.5D cut-out layers from AI line-art keyframes with parallax. Image-bound, flat characters, no real camera freedom.

This attempt must be real 3D: furniture and props as 3D objects with semantic ids in one consistent room, characters as 3D bodies whose limbs follow the clip's measured 3D pose, and cameras as 3D cameras that reproduce each shot's framing and can be moved anywhere afterwards.

## The clip

`scen/klipp/d-dialog-notan.mp4`: 576×1024 portrait, 30 fps, 12.77 s, with audio, in Swedish. It is a shot/reverse-shot sketch in a fast-food restaurant. Cuts are frame-accurate from our earlier analysis:

| Shot | In–out (s) | On screen | Framing / camera | Beat |
|---|---|---|---|---|
| S1 | 0.000–2.433 | A, woman seated at her table, facing camera, gesturing | medium shot, static | hook |
| S2 | 2.433–3.800 | B, man seated at HIS table (white wall behind), holding a fry | medium shot, static | build-up |
| S3 | 3.800–5.700 | A, same setup as S1 | medium, static | build-up |
| S4 | 5.700–8.533 | C, waiter standing in the room (black cap backwards, black tee, black trousers, card terminal in hand), background guests seated | medium-full, static | turn |
| S5 | 8.533–9.367 | B, same setup as S2, holding burger | medium, static | reaction |
| S6 | 9.367–11.233 | A, same setup as S1 | medium, static | punchline |
| S7 | 11.233–12.767 | wide: B alone at a table FAR away, empty tables between; a drink can (Bonaqua) in the foreground = A's table | wide, static | payoff, the reveal that they are not even at the same table |

Characters:
- **A** is a woman with long brown hair, black cardigan with white buttons, seated.
- **B** is a man with short brown hair, dark navy zip polo, seated.
- **C** is a waiter, standing.

Props visible:
- **A's table:** paper cup with logo, drink can, burger in paper and box, fries, sauce cup, tray.
- **B's table:** paper cup, burger, fries in a box, sauce.

Dialogue (time = start in s, speaker):
- 0.0 A: "Men vadå, menar du att du inte ska betala notan?"
- 2.3 B: "Varför skulle jag ta notan?"
- 3.7 A: "För det är ju så gentlemen gör."
- 5.8 A (off-screen, over S4): "Eller liksom betala halva åtminstone?"
- 7.9 B (off-screen): "Varför skulle jag betala halva?"
- 9.3 A: "För jag trodde du var en riktig man."
- 11.1 B: "Men jag känner inte ens dig?"

## Existing local data (read-only; use it, don't redo it unless you need better quality)

| Path | Content |
|---|---|
| `data/ra/hampuslundgren_-1779375226505.json` | MediaPipe at 10 fps. `sett.ramar[]`: `t`; `personer[]` with `lm` (33×[x,y,vis], image-normalized), **`varld` (33×[x,y,z] metric world landmarks, hip-centered)**, `bbox`; `hander[]` (2D hand landmarks, flattened); `saker[]` (EfficientDet objects: k, s, b=[x0,y0,x1,y1]); `ansikten[]`; `kamera` (per-frame camera motion dx, dy, rot, scale) |
| `data/analys/hampuslundgren_-1779375226505.json` | Analysis v13: cuts (`klipp`), per-scene objects, framing, camera words ("stilla" = static) |
| `scen/data/d-dialog-notan/spar.json` | YOLO11-pose tracks at 10 fps (17 COCO keypoints, boxes, track ids) and YOLO-World objects |
| `scen/data/d-dialog-notan/ss-gemini-3.8-flash-fps5.json` | Gemini semantic pass: roles, appearance, actions, dialogue |
| `scen/luma/d-dialog-notan/tagningslista.json` | Shot list (roles, framing, actions, dialogue) |
| `scen/luma/d-dialog-notan/gemini_skikt/S1..S7.json` | Gemini boxes (`box_2d` = [ymin,xmin,ymax,xmax] 0–1000) for props, furniture and room parts, on AI line-art keyframes of each shot (geometry ≈ source for A and C shots, offset for B shots). S7 is on the source frame at 12.0 s. |

## Tools available (CPU only, no CUDA)

- **Python venv:** `scen/.venv/Scripts/python.exe` (3.12). Installed: ultralytics 8.4 (YOLO11 pose/seg, SAM 2.1 via `ultralytics.SAM`, models in `scen/py/modeller/`), mediapipe 1.2.2, opencv 5.0, numpy 2.5, scipy, torch 2.15 CPU, transformers 5.22 (Depth Anything V2 Small: `depth-anything/Depth-Anything-V2-Small-hf`), pillow 13.
  - mediapipe 1.2.2 has **no `mp.solutions`**. Use the Tasks API (`mediapipe.tasks.python.vision`). `scen/py/modeller/pose_landmarker_full.task` exists. Download `hand_landmarker.task` and `face_landmarker.task` from `storage.googleapis.com/mediapipe-models/...` into `scen/3d/modeller/` if you need them.
  - Installing `simple-lama-inpainting` downgrades numpy and pillow and breaks transformers. Don't, or restore afterwards. Install anything new into this venv only, and check that existing imports still work.
- **Node 24**, and **Chrome** at `C:\Program Files\Google\Chrome\Application\chrome.exe` (`--headless=new --screenshot=...` works). You may install Playwright into the venv if you need more control.
- **ffmpeg** is on PATH.
- **Gemini, free tier only:** `node scen/sprak/gemini_bild.mjs <image.jpg> --ut <out.json> [--kontext "..."]` returns labeled boxes for one image. Use it at most ~15 times in total, and only if you need semantic boxes on source frames. No other paid or cloud APIs. Luma is unavailable.
- **three.js** must be **pinned** (e.g. `three@0.170.0`). Vendor the module files into `scen/3d/vendor/` so the page works offline (ES modules + importmap, no build step).

## Plan: three phases. Do ONLY the phase you are asked to do, verify it, then stop and report.

### Phase 1: measurement → per-shot camera + placement solve (no rendering of characters yet)

1. **Extraction.** At ≥ 15 fps for the whole clip (30 fps preferred), get per frame for the main actor of each shot:
   - pose image landmarks and **world landmarks**,
   - hand world landmarks (MediaPipe HandLandmarker), when hands are visible,
   - face blendshapes (FaceLandmarker: at least `jawOpen`, `mouthSmile*`, `browDown*`, `browInnerUp`, `eyeBlink*`) and head orientation (from the facial transformation matrix).

   Save to `scen/3d/data/sparning.json`, with per-shot actor assignment. The main actor is the largest and most central person. Ignore background guests in S4, and in S7 the actor is B, small and far. Reuse `data/ra` where its 10 fps is enough.
2. **Camera intrinsics + extrinsics per shot.** Use `cv2.solvePnP` between the metric world landmarks (visible joints only) and image landmarks.
   - Choose the vertical FOV per shot by minimizing reprojection error over candidates in 40–85°. A phone main camera in portrait is typically ~65–75° vertical. Report the chosen FOV and the error.
   - Use the median over the shot, since the cameras are static.
   - The result is the camera pose relative to the actor's hip frame.
3. **Compare with a second method.** Place actor and camera using Depth Anything V2 depth on a keyframe, scaled by the actor's known body size. Compare the two methods on plausibility (camera height above floor, distance to actor, horizon) and reprojection error. Pick one per shot, or combine them, and document why.
4. **One consistent restaurant layout** in meters: y up, floor y = 0, table height 0.75 m, tables 0.7×0.7 m.
   - Place A's seat and table, B's seat and table (far away, consistent with S7, which is filmed from A's table toward B), and the waiter's standing spot.
   - Compute each shot's camera in world coordinates.
   - Unproject visible furniture and props (from `data/ra` `saker`, Gemini boxes, YOLO-World) onto the table plane or floor to get their 3D positions.
5. **Verify.** For each shot, project the actor's 3D skeleton (placed in the world) through the solved world camera back onto the source frame. Draw it over 3 frames per shot (start, middle, end) in a contact sheet `scen/3d/verifiering/fas1.jpg`, and give the per-shot median joint error, normalized by frame height.

   Also render a top-down **floor plan** image (`scen/3d/verifiering/plan.png`) showing tables, seats, actors and every shot's camera frustum.
6. **Report** in `scen/3d/LOGG.md`, appended as you go, with decisions, numbers, and what failed. Write `scen/3d/data/layout.json` (room, furniture, props, actors' placements, cameras per shot).

**Phase 1 acceptance:** median reprojection error ≤ 0.04 × frame height for the main actor in S1–S6, cameras at plausible heights (0.9–1.7 m), and the plan view consistent with S7. If you cannot reach this, report honestly what blocks it.

### Phase 2: the 3D set + rounded characters + player

1. **Parametric set from `layout.json`.** Floor, walls, the window wall (A's background), the white wall behind B, ceiling with pendant lamps, black tables and chairs, counter, plus props as simple meshes with semantic ids: paper cup (tapered cylinder with lid), drink can, burger (stacked rounded cylinders), pizza slice, fries box, tray, sauce cup and card terminal.
2. **Rounded stylized characters**, built procedurally (capsules, spheres, rounded boxes) and parameterized per actor: height, build, skin, hair (A long brown, B short brown, C black cap backwards), and clothing colors. They are driven per frame by the 3D pose: limbs follow joint positions, the head follows face orientation, the mouth follows `jawOpen`, and brows and smile follow blendshapes for mood. Hands follow the hand landmarks when visible and a relaxed default otherwise. Seated actors whose legs are occluded get stable seated legs.
   - Smooth over time with One-Euro or Savitzky–Golay.
   - **A/B test:** a rigged avatar via `@pixiv/three-vrm` + `kalidokit` with a permissively licensed VRM model, but only if the license allows it and it runs offline. Compare robustness and readability against the procedural characters, keep the better one as default, and document both.
3. **Scene spec `scen/3d/scen3d.json`** in meters and seconds, human- and LLM-editable:
   - set objects (id, type, semantic label, transform, dims, color),
   - actors (id, role, look, motion-track ref, motion intensity),
   - props (id, type, transform or `attach` to an actor's hand),
   - shots (id, source in/out, duration, actors present with placement/yaw overrides, camera keyframes [pos, target, fov], beat, dialogue line, audio range),
   - an edit log.
4. **Player `scen/3d/index.html`.**
   - Plays the shots in order with captions, optionally synced to the source audio, and has a free-orbit inspection toggle.
   - Polls `scen3d.json` every 1 s and hot-reloads without a page refresh.
   - The URL hash `#t=<sec>`, `&mode=mask` (actor silhouettes only) and `&cam=<shot>` give deterministic frames for screenshots, with no running clock.
5. **Verify** (`scen/3d/verifiera.py`). Per shot, at 3 timestamps, render normal and mask frames headless, then compute:
   - the 2D joint reprojection error of the rendered character against the source landmarks,
   - silhouette IoU between the rendered actor mask and the source person mask (YOLO11-seg on the source frame),
   - a contact sheet: source | render | overlay.

   Write `scen/3d/rapport.md`.

**Phase 2 acceptance:**
- median joint error ≤ 0.05 × height in S1–S6,
- silhouette IoU ≥ 0.5 in S1–S6,
- S7 shows B small at a far table with empty tables between, and the can in the foreground,
- readable gestures (A's hand gestures in S1/S3/S6 visibly follow the clip),
- mouths move when the actor speaks.

### Phase 3: semantic edit operations + demonstration

1. **`scen/3d/op.py`.** Small, logged, undoable operations on `scen3d.json`, each ≤ 50 ms, with semantic selectors (`A`, `S1:cup`, `table:A`).
   - Objects: move, rotate, swap prop type, hide or show.
   - Camera: set, dolly, orbit, zoom.
   - Shots: retime, duplicate, remove, reorder.
   - Actors: add an actor to a shot at a placement, turn an actor toward a target, mirror a performance, motion intensity, look or mood change.
2. **Demonstrate.** Apply each change below, render before/after sheets, and check visually that it reads correctly:
   1. Burger → pizza on A's table.
   2. Slow dolly-in on A's face in S6.
   3. The waiter turns toward A and S4 is shortened to 1.6 s.
   4. Remove the can and move the cup closer to A in S1.
   5. A new final shot S8: the camera orbits 90° around B's table. This must work because the room is real 3D.
   6. Add the waiter standing behind A in S6, at correct depth and scale.
   7. "A should feel more stressed": higher gesture intensity plus shorter shots.
3. **Final README.** `scen/3d/README.md` in **Swedish**: how to run, schema, ops, results (numbers), what was compared and chosen, compute time per stage, and limitations.

## Working rules

- Work sequentially. Verify each step with numbers or images before building on it, and look at your own images.
- Don't fake results. If something doesn't meet acceptance, report it with the actual numbers and what you tried.
- Prefer packaged, well-maintained dependencies over hand-rolled math, but keep the stack small.
- Keep everything reproducible: one command per stage. Note runtimes.

## Notes from the orchestrator for Phase 2 (added while you were rate-limited)

- **CC0 VRM models for the rigged-avatar A/B test.** VRoid's own sample models are released under CC0 and mirrored on OpenGameArt, at https://opengameart.org/content/vroid-studio-cc0-models. Direct zips: `https://opengameart.org/sites/default/files/base_male.zip`, `.../base_female.zip`, and `avatarsample_d_0.zip` / `_e` / `_f` / `_g`. They are anime-styled, so use them only for the A/B comparison and keep the procedural rounded characters as the stylistic default unless the rigged route is clearly better. Before using a model, check its VRM meta (`licenseName`, `commercialUsage`).
- **Table B in S7.** Your Phase 1b measurement (front edge 157→497 px, std < 2 px) suggests a narrow, deep table seen from its short end. That is better evidence than the orchestrator's 1.0–1.1 m width guess, which assumed the edge was only ~0.5 m in front of B. Trust the measurement.
