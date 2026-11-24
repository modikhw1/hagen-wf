# Codex task D: room layout with measured minimum ranges, as a cached stage in the ingest pipeline

Repo root: `C:\Users\praiseworthy\Desktop\hagen-wf`.
- Read first: `scen/3d/ingest/README.md`, `scen/3d/ingest/ingest_klipp.py` and `scen/3d/klipp2/PROCESS.md`.
- Your earlier task C (MediaPipe/MotionBERT/MPFB2) is superseded.
- **Scope is ONLY the room.** Expressions and Seedance are deferred by the owner until the pre-render is stable. Do NOT change the person or camera stages.

## Context (works; do not rebuild)
`scen/3d/ingest/ingest_klipp.py <mp4> <ut>` runs these cached stages: personer (YOLO11-seg + BoT-SORT ReID + fragment merge) → kamera (COLMAP, `ut/colmap/sparse/*`, `kamera.json`) → kropp (SAM 3D Body on Modal GPU) → sekvens (MHR params: Hampel outlier rejection, occlusion-aware legs, zero-phase Butterworth) → varld (`varld.npz`: metric camera R/C, scale k, `upp` = gravity in COLMAP world) → golv (person moved along the camera ray so the lowest foot is on the floor; `varld.npz['golv_h']` is the floor height along `upp`) → blender (`mhr_rig.py`, headless) → jamfor.

Test outputs (already computed, use them as cache): `scen/3d/ingest/ut/bar` (two people behind a bar counter, camera mostly panning, floor from an assumed 1.45 m camera height) and `scen/3d/ingest/ut/biljard` (one person walking in a pool hall, feet visible, camera moving 1.1 m).

## The owner's requirement
"At minimum, draw the bare minimum ranges: how far away the wall is, whether there are tables, their size and the distance to the person." The point is that the pre-render must **set the scene**. Objects must exist so that bodies are occluded correctly in perspective (e.g. the bar counter hides the lower bodies).

## Build: a new stage `rum` (between `golv` and `blender`), plus Blender wiring
1. **Geometry source.** COLMAP sparse points are often too thin on walls and floors. Add a dense per-frame metric depth model on Modal GPU, choosing one whose licence allows commercial use. Check the licences explicitly, record them, and prefer MoGe-2 (Microsoft) or Depth Anything V2 Small (Apache-2.0). Run it on every 6th frame, outside the person masks. Then put the depth into the world using the camera poses from `varld.npz` with the same scale k: the depth model's metric scale is cross-checked against k, and the disagreement is reported. This yields a fused room point cloud.
2. **Floor and walls:** RANSAC planes. The floor normal must be within 10° of `upp`; check the floor against `golv_h` and report the difference in cm. Walls are vertical planes, up to 4 of them, with their distance from the camera path and from each person.
3. **Objects:** detect furniture and props with open-vocabulary detection over the frames. Use YOLO-World (already used in this repo) or Gemini `gemini-3.5-flash-lite` (key `GEMINI_API_KEY_GRATIS` in `video/.env.local`; never print it) for labels. Lift each object to 3D: take the fused points inside its 2D boxes across frames, fit an oriented box, and keep a label. Must handle: the bar counter in `bar`, and the pool tables in `biljard`.
4. **Output `rum.json`:** floor height, walls (normal, distance), objects (label, centre, size, yaw), and per person per frame the distances to the nearest wall and to each object, plus summary ranges (min/median/max). Also write `rum.md`, a short human-readable table: "wall behind A: 2.3 m; bar counter 2.1 × 0.6 × 1.05 m, 0.4 m in front of person 1".
5. **Blender:** `mhr_rig.py` builds simple boxes and planes from `rum.json` (flat colours, named by label). The renders and `jamforelse.mp4` must then show the counter occluding the lower bodies in `bar`, and the tables in `biljard`.

## Acceptance
- `bar`: a counter box exists in front of both people, its top edge matches the counter edge in the source within ~25 px over the clip (measure it), and the lower bodies are hidden behind it in the render.
- `biljard`: at least the two nearest pool tables appear as boxes with plausible size (~2.5 × 1.4 × 0.8 m) and position (overlay check).
- The floor agrees with `golv_h` within 5 cm, and the wall distances are reported.
- The stage is cached and timed in `tider.json`. A cached rerun of the whole pipeline takes under 1.5 min.
- Licences are listed for every model used.

Append to `scen/3d/klipp2/LOGG.md`. End with a concise report: numbers, paths, and what failed.

## Update 20:15 (Claude, same evening): the pipeline changed before your start. Build on it, do not revert it.
- New stage order: personer → kamera → kropp → sekvens → varld → golv → **kontakt** → blender → jamfor. Insert `rum` **after `kontakt`** and before `blender`.
- `sekvens_stabil.py`: root rotation is now filtered as a sign-continuous quaternion (MHR root = extrinsic 'xyz' Euler; Euler filtering near ±π flipped bodies 100–180°), per-parameter Hampel on twist/wrist params, and per-frame reliability gating (`palitlig_<pid>.json`).
- `ingest_klipp.py` `steg_sekvens`: cam_t split into ray direction (6 Hz) and distance (Hampel ±7, 2 m/s speed limit, 1.5 Hz). `steg_golv` is idempotent (`cam_t_fore_golv`) and uses a constant scale when legs are visible in < 20 % of frames.
- New `kontakt.py`: foot contact detection, a bounded body shift (along the ray fully, sideways half, max 4 cm) and **analytic two-bone leg IK in numpy on the MHR global joint array** (Blender IK does not work on this rig: bone tails do not point at the child joint). Idempotent via `pose_fore_kontakt` / `cam_t_fore_kontakt`. `rum` must read `sekvens_*.npz` after kontakt.
- New `vakt.py <ut> [--tag x]`: geometric guard metrics (jitter, joint flips, foot sliding in contact periods, floor, root speed, 2D deviation vs raw fit). Run it after your changes and report before/after; do not make any metric worse.
