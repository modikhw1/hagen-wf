# Codex task: bake the Scen3D motion (X Bot) frame-exactly into Blender

Repo root: `C:\Users\praiseworthy\Desktop\hagen-wf`. Work only under `scen/3d/`. Python: `scen/.venv/Scripts/python.exe` (3.12). Blender 5.2.3 LTS: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` (use `-b --factory-startup --python <script> -- args`). Node is available. Read `scen/3d/README.md` first.

## Why
The three.js player (`scen/3d/index.html`, `player.js`, `avatar_xbot.js`) drives Mixamo X Bot dolls from measured MediaPipe motion (`data/motion-2.json`/`motion-3.json`) with a custom, verified retarget: proportions, arm IK and stabilisation, hands, head/look-at, and a face made of ellipsoids (eyes, brows, mouth driven by `jawOpen`). **Do not reimplement the retarget.** Bake what the player computes.

Blender becomes the **previs/blockout** stage. Its renders, a blockout video plus first frames, depth and pose, are fed to a video model (Seedance/Kling) as structure and motion reference. **Hard rule from the owner:** the original source audio (`data/source-audio.m4a`, mapped per shot through `audioRange`/`source.knots`) must still fit the bodies and mouths. So the motion has to be continuous and frame-exact over each shot's full duration, start to end, at scene time `t`, including cuts at the exact same times as the player. Generic poses per shot are not enough.

## Build
1. **`scen/3d/blender/baka.mjs`** (reuse the CDP approach in `scen/3d/capture.mjs`; serve `scen/3d` over http like `verifiera_fas4.py`/`mvp_render.py` do). Add a small read-only hook to `player.js` if needed (e.g. `window.__SCEN3D__.dump()`), without changing any visual behaviour. For every frame `i = 0 .. N-1`, where `N = round(sum(shot.duration) * 30)`, call `setFrame(i/30, {variant:'xbot'})` with the **original** audio mode (`#ljud=original`, so the mouth = MediaPipe jawOpen of the source). Record:
   - per visible X Bot actor (A, B, C, plus `guest` in S4): the root world transform, and for **every bone** the local position, quaternion and scale (bone positions change because of the proportion solve);
   - the local transforms and visibility of the face parts (eyes, brows, mouth) relative to their parent bone;
   - visibility per actor;
   - props: world position, quaternion and visibility (props can be attached to hands);
   - the active shot id;
   - camera world position, quaternion and fov;
   - `window.__frame.joints` (projected 2D joints) and `mouthOpen`, for verification.

   Write it to `scen/3d/blender/bake.json`, or a compact binary plus JSON index if large.
2. **`scen/3d/blender/importera_bake.py`** (runs inside Blender). Import `modeller/Xbot.glb` once per actor and apply the baked transforms as keyframes on every frame. Account for glTF→Blender axis conversion: Y-up → Z-up, and bone-axis correction from the importer's bone heuristic. A robust way: compute a per-bone correction `C_b = (conv · M_gl_rest)^-1 · M_bl_rest` at rest, then set `pose_bone.matrix` from `conv · M_gl_pose · C_b`. Any method is fine if it verifies. Recreate the face parts as simple ellipsoid meshes parented to the head bone with the baked transforms. Name the objects `actor:A`, `actor:B`, `actor:C`, `actor:guest`, and the face parts `actor:A:mouth` etc. Show and hide actors per frame, with keyed visibility for viewport and render. Use roll colours from `scen3d.json` actors' `look.shirt`. Do NOT create the room, props or cameras; `bygg_scen.py` (written by Claude in parallel) does that. Expose a function `importera(bake_path, scen_path)` so it can be called from that script, and also make it runnable standalone.
3. **`scen/3d/blender/verifiera_bake.py`**. For at least 3 frames per shot (start+2 frames, middle, end−2 frames):
   - (a) the world positions of the main joints in Blender (shoulders, elbows, wrists, hips, head) vs three.js within **≤ 5 mm**;
   - (b) the mouth part's scale/aperture in Blender equal to the baked one;
   - (c) a render with Blender's own camera (built from the baked camera) per shot, with the actor silhouette compared to the player's mask render (`#mode=mask`): IoU **≥ 0.9** per shot. Mask-render Blender with Workbench flat white actor on black.

   Also check the frame count `N`, the first and last frame of each shot (cut frames identical to the player's `shotAt`), and the total duration vs the audio mapping in `mvp_render.py`. Write `scen/3d/blender/verifiering-bake.json` and a side-by-side image per shot in `scen/3d/blender/verifiering/`.

## Acceptance
- `bake.json` covers all N frames with no gaps. The cut frames match the player.
- The joint error is ≤ 5 mm (report median and max per shot), the silhouette IoU is ≥ 0.9 per shot, and the mouth matches.
- The whole chain runs end-to-end with one command each: `node scen/3d/blender/baka.mjs` and `blender -b --python scen/3d/blender/verifiera_bake.py`.
- No visual change to the three.js player.

Append decisions and numbers to `scen/3d/blender/LOGG.md`. End with a concise report: what you built, the numbers per shot, what you compared and why, what is uncertain, and the paths to the verification images.
