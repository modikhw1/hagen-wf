# Codex task C: natural, source-faithful human motion in Blender (new clip)

Repo root: `C:\Users\praiseworthy\Desktop\hagen-wf`. Work under `scen/3d/klipp2/` (new).
- Python: `scen/.venv/Scripts/python.exe` (3.12; torch CPU, scipy, mediapipe, ultralytics, opencv). **No GPU.**
- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` (headless `-b --python`).
- Read first: `scen/3d/blender/README.md`, `scen/3d/blender/LOGG.md` (your earlier tasks), and `C:\Users\praiseworthy\.claude\projects\C--Users-praiseworthy-Desktop-hagen-wf\memory\feedback-forrendering-1till1.md` (the owner's verdict).

## Owner's verdict and the goal
The previous chain (MediaPipe world landmarks → custom three.js retarget → X Bot → Blender) gives **wobbly, unnatural** dolls that do not capture the essence of the clip (a woman talking slightly irritated into the camera with natural hand gestures looked "off"). The owner wants the Blender pre-render **1:1 faithful to the source** (asymmetry is fine), natural human motion, and a tracked camera. It is fed to Seedance as the motion reference, so its quality caps the final result. Fast iteration is still the goal: Blender steps may cost more, but routine edits must stay quick.

## Clip
`scen/klipp/kand-interpooluppsala-7599643065644551446.mp4`: 12.3 s, 1080×1920, 30 fps, 369 frames. A woman walks toward a moving handheld camera in a pool hall, talking to camera with expressive hand gestures, full body visible.
- Person masks per frame: `scen/3d/klipp2/masker/*.png` (YOLO-seg, dilated) and `masker.npy` (369×480×270 bool).
- **Camera:** Claude is solving it in Blender (libmv) in parallel. The output will be `scen/3d/klipp2/kamera.json`: per-frame camera world matrix (Blender Z-up), focal length mm, sensor width, solve error, plus `kamera.blend`. If it is missing when you need it, use a per-frame camera from your own solution and say so.

## Build
1. **Motion source bake-off** (CPU only, licences that allow commercial use; **no SMPL/SMPL-X**, which is non-commercial and gated). Compare at least:
   - (a) the current approach: MediaPipe Pose world landmarks plus hands;
   - (b) **RTMW / RTMW3D whole-body** via `rtmlib` or ONNX (OpenMMLab, Apache-2.0): 133 keypoints including hands and face;
   - (c) one temporal 3D lifter with a permissive licence (e.g. MotionBERT, or a similar one; check its licence) applied to the best 2D keypoints.

   Metrics: 2D reprojection error vs the best 2D detections, jitter (mean |acceleration|), bone-length stability, foot sliding while a foot is planted, and a visual side-by-side. Pick per body part if that is better.
2. **Retarget by rotations onto a good rig, using Blender's own tooling rather than our custom IK.**
   - Character: Mixamo X Bot is fine to start. Better if you find a **commercially usable, natural-looking rigged human with ARKit-style face blendshapes** (e.g. MPFB2/MakeHuman CC0 assets, or another CC0/CC-BY source). Report the licence.
   - Use bone rotations from a fitted skeleton, not position-chasing IK. Use Blender constraints and NLA where useful.
   - Add **mocap clean-up that preserves timing**: zero-phase filtering per channel, foot locking (contact detection from velocity + height), floor contact, no knee pops, hand orientation smoothing. Peaks may move at most ±1 frame.
   - **Face:** drive jaw, mouth, brows, blinks and head from MediaPipe FaceLandmarker blendshapes (52 ARKit names) onto the character's shape keys, so the irritated expression and talking read clearly.
   - **World placement:** put the person in the solved camera's world. Root trajectory from the 2D foot contacts + ground plane + camera, so she actually walks toward the camera across the floor. Scale from body height ~1.65 m.
3. **Scene:** a simple room blockout matching the pool hall (floor plane, back wall, 2–3 pool tables as boxes in their tracked positions if you can estimate them from the camera solve; the tracked 3D points of the solve are available in the Blender file).
4. **Render** with the solved camera at source resolution/2 and 30 fps, original audio underneath. Produce `klipp2/jamforelse.mp4`: source | Blender render (H.264 **Main**, yuv420p, AAC stereo 48 kHz, `+faststart`; the owner's Windows player fails otherwise).
5. **Speed:** report how long each stage takes, and which stages are one-time ingest and which are per-edit. The per-edit path (e.g. change the camera, swap the character, move an object) must stay fast (seconds).

## Acceptance
- Visual: in the side-by-side the character's walk, gestures, head and expression read as **the same performance** as the source, without wobble. Be honest; include 6 still triptychs at key gesture frames.
- Numbers per metric for each candidate source, the chosen combination, and before (method a) vs after.
- Licences listed for every model and asset used.

Append decisions and numbers to `scen/3d/klipp2/LOGG.md`. End with a concise report: what you built, the numbers, what you compared and why, what failed, and the paths.
