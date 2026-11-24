# Phase 1 work log

## Scope and initial inspection — 2026-11-07

Read the complete CODEX-PROMPT.md, including context and Phases 2–3. Implement Phase 1 only: measurements, camera alternatives, shared metric layout, diagnostic skeleton overlays and floor plan. No character renderer, player, semantic operations, or Phase 2/3 assets.

Source confirmed: 576 × 1024, 30 fps, 383 frames, 12.766667 s. No applicable AGENTS.md found in workspace/ancestor checks. All new files and model/cache writes confined to scen/3d/. No dependency installation, API keys, or paid/cloud inference used.

Viewed all seven source keyframes. Existing Gemini S1–S6 boxes come from altered line-art images (including erroneous pizza labels); they must not be treated as source truth. Prefer source-frame YOLO/RA objects; use S7 source Gemini boxes with provenance and uncertainty. The video alone does not determine true metric room scale, hidden furniture, absolute yaw, or gravity. State anthropometric and layout priors explicitly and retain unmodified model landmarks.

Commands (from repository root):

```powershell
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py extract
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py depth
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py solve
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py verify
```

## Extraction — 30 fps
Runtime: 44.1 s. All 383 decoded source frames; exact cut frame indices [0, 73, 114, 171, 256, 281, 337, 383]. Temporal pose state reset at cuts. Largest central torso selected; hands matched to its wrists; face matched to its nose. Missing detections are null, never fabricated or interpolated.

Coverage (frames / pose / face / frames with >=1 hand):

- S1: 73 / 73 / 73 / 73
- S2: 41 / 41 / 41 / 39
- S3: 57 / 57 / 57 / 57
- S4: 85 / 85 / 28 / 85
- S5: 25 / 25 / 25 / 25
- S6: 56 / 56 / 56 / 0
- S7: 46 / 46 / 0 / 21

## Extraction — 30 fps
Runtime: 47.3 s. All 383 decoded source frames; exact cut frame indices [0, 73, 114, 171, 256, 281, 337, 383]. Temporal pose state reset at cuts. Largest central torso selected; hands matched to its wrists; face matched to its nose. Missing detections are null, never fabricated or interpolated.

Coverage (frames / pose / face / frames with >=1 hand):

- S1: 73 / 73 / 73 / 73
- S2: 41 / 41 / 41 / 39
- S3: 57 / 57 / 57 / 57
- S4: 85 / 85 / 85 / 85
- S5: 25 / 25 / 25 / 25
- S6: 56 / 56 / 56 / 0
- S7: 46 / 46 / 46 / 21

## Depth inference
Seven source keyframes, CPU, 17.5 s. Reused cached Depth Anything V2 Small weights read-only. Relative inverse-depth maps retained as .npy; scale and shift are not metric observations. Official sources: https://github.com/DepthAnything/Depth-Anything-V2 and https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python .

## Final Phase 1 verification (serialized layout read-back)

All 383 frames are extracted at 30 fps. Pose and required face channels: 383/383. 103 face frames use a head ROI (57 in S4, 46 in S7); matrices retain that ROI camera convention. S6 hands are hidden behind the table and have no detections; S2 has 2 frames and S7 has 25 frames without detected hands. This is missing data, not neutral hand motion.

### Camera methods and selection

1. **Unconstrained PnP:** SQPnP + iterative solvePnP for each frame/FOV, then component medians of small rotation vectors and translations per static shot. FOV candidates: every degree from 40 to 85. All unconstrained camera heights fail the 0.9 m minimum under the stated hip/floor prior.
2. **Depth Anything V2:** seven measured relative inverse-depth keyframes; backproject with 40/55/70/85-degree FOV and zero / 10%-median inverse-depth offsets; scale by shot-median MediaPipe shoulder width, rigid Kabsch fit to pose (no nonrigid warp or PnP in this branch). The absolute body size is NOT known from a tape measure. Offsets, scale and gravity remain assumptions. Depth generally has higher joint error and implausible heights.
3. **Height-only PnP refinement:** a single rigid static camera per shot initialized by the median; soft-L1 joint residual and camera height bounds [0.9,1.7] m. This passes the numerical tests but places all seven cameras at the lower bound and does not reconcile shared table props.
4. **Selected:** static PnP refinement plus shared can/cup bottom/top anchors on y=.75 m, with declared .168 m can / .18 m cup height priors, for S1/S2/S3/S5/S6/S7. For S4 retain height-only PnP because no shared stationary prop is reliable. Choose lowest visible-joint median among FOV candidates with <=12 px maximum anchor error and successful optimizer convergence. Per-frame pose landmarks, hip positions and world cameras are never adjusted during verification.
Placement alternatives were inspected before selection. A-can local z=.55 caused 58.3/91.4/128.7 px in S1/S3/S6 when anchors were enforced. At z=.75, coarse-FOV trials gave 33.2/46.9/53.8 px; z=.95 gave 25.9/31.4/33.8 px but leaves no can-radius margin at the table edge; z=1.15 lies outside the .70 m table. Selected z=.90 leaves a .05 m center-to-edge margin. B-cup z=.477 from an unconstrained S7 prop fit gave 42.7 px in S2; z=.55/.65/.80/.90 were compared (coarse best S2 errors 31.6/25.2/25.1/19.9 px). Selected z=.80 leaves room for the cup footprint; S7 was refitted with that shared location. These are explicit geometric priors selected for a consistent editable hypothesis, not independently recovered coordinates.
A first shared-prop trial applied robust loss to the already weighted anchor residuals, allowing 25–148 px anchor misses. Rejected. The final implementation robustifies joints only and keeps anchor residuals quadratic; failed prior trials are reported here, not silently promoted to success.
| Shot | FOV | median px | median / H | P90 px | camera y m | hip distance m | horizon y px | YOLO crosscheck px |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | 73 | 26.090 | 0.02548 | 79.99 | 1.147 | 1.508 | 372.6 | 54.80 |
| S2 | 62 | 19.783 | 0.01932 | 51.41 | 1.045 | 1.333 | 454.0 | 48.68 |
| S3 | 63 | 33.213 | 0.03243 | 62.09 | 1.188 | 1.537 | 261.7 | 58.53 |
| S4 | 40 | 18.367 | 0.01794 | 31.41 | 0.900 | 2.322 | 734.9 | 18.47 |
| S5 | 45 | 22.448 | 0.02192 | 46.11 | 1.073 | 1.651 | 399.7 | 39.22 |
| S6 | 63 | 36.688 | 0.03583 | 81.34 | 1.172 | 1.569 | 244.9 | 39.23 |
| S7 | 40 | 10.873 | 0.01062 | 22.66 | 1.042 | 4.728 | 392.6 | 13.12 |

| Shot | raw PnP FOV / px / height m | depth FOV / px / height m / distance m / horizon px | selected anchor max px |
|---|---|---|---:|
| S1 | 40 / 20.64 / 0.636 | 85 / 35.95 / 0.772 / 1.269 / 601.5 | 0.285 |
| S2 | 40 / 17.00 / 0.779 | 70 / 29.87 / 1.054 / 1.175 / 451.9 | 0.152 |
| S3 | 42 / 15.56 / 0.681 | 70 / 56.61 / 0.233 / 0.986 / 1357.8 | 0.993 |
| S4 | 40 / 17.75 / 0.779 | 85 / 32.56 / 0.989 / 0.944 / 672.3 | n/a |
| S5 | 40 / 17.84 / 0.881 | 85 / 55.06 / 0.783 / 0.736 / 643.9 | 0.410 |
| S6 | 40 / 22.63 / 0.660 | 85 / 75.47 / 0.514 / 0.959 / 858.3 | 1.160 |
| S7 | 40 / 8.77 / 0.522 | 85 / 47.15 / 0.522 / 1.593 / 615.8 | 0.853 |

### Acceptance and practical limits
Computed acceptance: `{'joint_errors_S1_S6': True, 'heights_all_shots': True, 'S7_plan_ordering': True}`. Distances: `{'actor_A_B_m': 4.9286183810451, 'S7_to_A_table_m': 0.4174268744725172, 'S7_to_B_hip_m': 4.727733702670395, 'empty_tables_between': 2}`.
The error is the median Euclidean pixel distance over all evaluated joints/frames, divided by 1024. Visible anatomical joints only: nose, ears, shoulders/elbows/wrists/hand pose tips; standing hips/legs when visibility and presence >=.65 and within frame. Seated hips and legs behind tables, redundant eye/mouth points, low-confidence and out-of-frame landmarks are excluded. This is an in-sample 2D consistency check of MediaPipe 3D against MediaPipe 2D. The YOLO column is a separate-detector crosscheck at original 10 fps timestamps; it is not manual ground truth.
The floor plan has separate A/B tables, A/B seats, waiter spot, two empty tables between, and every camera frustum. S7 starts at A’s table with the can in front and B farther away. Empty table coordinates, room walls and C’s cross-shot yaw/position are qualitative priors. Inspect S7-layout-overlay.jpg: the mandatory .70 m square tables do not fully reproduce source tabletop boundaries. Thus qualitative S7 plan ordering passes; precise furniture reconstruction is unresolved.
S4 camera height is constraint-limited at .900 m. S4/S7 FOVs hit the 40-degree search bound; focal length, hip/floor scale and depth are not uniquely calibrated. No camera sensor data or measured actor heights are available. Depth cannot resolve scale/shift by itself. A can/cup height or seat placement error changes the metric result.
All ray-plane observations, including rejected and off-table positions, remain in layout.json with provenance. Source YOLO/RA detections are preferred. S1/S4 Gemini art boxes are approximate only; S7 boxes are source-based. Prop priors are explicit where detections do not support a location; handheld terminal uses a measured wrist attachment. No false claim of recovered occluded geometry, hands, or metric room truth.
### Reproduction, runtimes and artifacts
```powershell
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py extract
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py depth
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py solve
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py layout
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py verify
```
For image/layout iteration without refitting: `... fas1.py layout --reuse`, then `... fas1.py verify`.
Latest runtimes (CPU): extraction 47.26 s; depth 17.49 s; PnP/depth comparison 33.54 s; shared-prop refinement 14.93 s; assembly 0.05 s; verification/images 4.06 s. Runtimes exclude exploratory retries.
- `data/sparning.json`: complete per-frame motion, face and hand measurements, shot assignment, coverage and model hashes.
- `data/layout.json`: room, actors, furniture, semantic props, static cameras and all placement observations.
- `data/camera-comparison.json`, `data/layout-comparison.json`: full FOV grids, alternate methods, per-frame errors and priors.
- `data/verification.json`: read-back projection metrics, per-joint errors, acceptance checks and plan distances.
- `verifiering/fas1.jpg`: 21 overlays (start / middle / final source frame of each shot).
- `verifiering/plan.png`: all cameras/frusta, tables, seats and actors in one room.
- `verifiering/S1-overlay.jpg` … `S7-overlay.jpg`: full-resolution shot sheets; `S*-frame-*.jpg`: individual frames.
- `verifiering/extraction.jpg`: actor/hand/face extraction audit; `S*-depth.jpg`: source versus relative depth.
- `verifiering/S7-layout-overlay.jpg`: table-wireframe diagnostic exposing unresolved furniture edges.
Only Phase 1 implemented. No Three.js, character renderer, player, semantic edit operations, or Phase 2/3 artifacts.

## Visual review and occlusion refinement
Viewed all 21 source/3D overlays, the extraction sheet, S7 depth, floor plan and S7 furniture overlay. Large elbow residuals and individual failing frames remain despite passing shot medians. S7 tabletop footprint does not match the source. The 0.7 m square-table prior and monocular pose/scale do not determine true room geometry.

Pose visibility was overconfident for hidden hands (especially S6). Refitting now excludes seated wrist/tip joints unless matched by HandLandmarker; raw measurements are retained. Numerical tables ABOVE this entry are the pre-refinement run. Tables appended BELOW are the authoritative final run. The prior-placement exploration numbers remain historical, before this mask correction.

## Final Phase 1 verification (serialized layout read-back)

All 383 frames are extracted at 30 fps. Pose and required face channels: 383/383. 103 face frames use a head ROI (57 in S4, 46 in S7); matrices retain that ROI camera convention. S6 hands are hidden behind the table and have no detections; S2 has 2 frames and S7 has 25 frames without detected hands. This is missing data, not neutral hand motion.

### Camera methods and selection

1. **Unconstrained PnP:** SQPnP + iterative solvePnP for each frame/FOV, then component medians of small rotation vectors and translations per static shot. FOV candidates: every degree from 40 to 85. Unconstrained heights outside the required range under the stated hip/floor prior: S1, S2, S3, S4, S5.
2. **Depth Anything V2:** seven measured relative inverse-depth keyframes; backproject with 40/55/70/85-degree FOV and zero / 10%-median inverse-depth offsets; scale by shot-median MediaPipe shoulder width, rigid Kabsch fit to pose (no nonrigid warp or PnP in this branch). The absolute body size is NOT known from a tape measure. Offsets, scale and gravity remain assumptions. Depth generally has higher joint error and implausible heights.
3. **Height-only PnP refinement:** a single rigid static camera per shot initialized by the median; soft-L1 joint residual and camera height bounds [0.9,1.7] m. This passes the numerical tests but places all seven cameras at the lower bound and does not reconcile shared table props.
4. **Selected:** static PnP refinement plus shared can/cup bottom/top anchors on y=.75 m, with declared .168 m can / .18 m cup height priors, for S1/S2/S3/S5/S6/S7. For S4 retain height-only PnP because no shared stationary prop is reliable. Choose lowest visible-joint median among FOV candidates with <=12 px maximum anchor error and successful optimizer convergence. Per-frame pose landmarks, hip positions and world cameras are never adjusted during verification.
Placement alternatives were inspected before selection. A-can local z=.55 caused 58.3/91.4/128.7 px in S1/S3/S6 when anchors were enforced. At z=.75, coarse-FOV trials gave 33.2/46.9/53.8 px; z=.95 gave 25.9/31.4/33.8 px but leaves no can-radius margin at the table edge; z=1.15 lies outside the .70 m table. Selected z=.90 leaves a .05 m center-to-edge margin. B-cup z=.477 from an unconstrained S7 prop fit gave 42.7 px in S2; z=.55/.65/.80/.90 were compared (coarse best S2 errors 31.6/25.2/25.1/19.9 px). Selected z=.80 leaves room for the cup footprint; S7 was refitted with that shared location. These are explicit geometric priors selected for a consistent editable hypothesis, not independently recovered coordinates.
A first shared-prop trial applied robust loss to the already weighted anchor residuals, allowing 25–148 px anchor misses. Rejected. The final implementation robustifies joints only and keeps anchor residuals quadratic; failed prior trials are reported here, not silently promoted to success.
| Shot | FOV | median px | median / H | P90 px | camera y m | hip distance m | horizon y px | YOLO crosscheck px |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | 73 | 26.012 | 0.02540 | 80.17 | 1.147 | 1.508 | 372.4 | 54.91 |
| S2 | 62 | 19.510 | 0.01905 | 48.88 | 1.043 | 1.335 | 457.0 | 43.70 |
| S3 | 57 | 31.203 | 0.03047 | 71.14 | 1.208 | 1.630 | 243.7 | 49.80 |
| S4 | 40 | 18.367 | 0.01794 | 31.41 | 0.900 | 2.322 | 734.9 | 18.47 |
| S5 | 44 | 20.133 | 0.01966 | 42.85 | 1.073 | 1.674 | 400.4 | 28.48 |
| S6 | 57 | 30.454 | 0.02974 | 62.42 | 1.189 | 1.664 | 231.6 | 37.40 |
| S7 | 40 | 10.942 | 0.01069 | 22.90 | 1.042 | 4.711 | 392.3 | 11.92 |

| Shot | raw PnP FOV / px / height m | depth FOV / px / height m / distance m / horizon px | selected anchor max px |
|---|---|---|---:|
| S1 | 40 / 20.59 / 0.636 | 85 / 35.87 / 0.772 / 1.269 / 601.5 | 0.281 |
| S2 | 40 / 15.63 / 0.787 | 70 / 29.60 / 1.054 / 1.175 / 451.9 | 0.181 |
| S3 | 41 / 16.28 / 0.738 | 85 / 53.11 / 0.354 / 0.802 / 1229.4 | 0.681 |
| S4 | 40 / 17.75 / 0.779 | 85 / 32.56 / 0.989 / 0.944 / 672.3 | n/a |
| S5 | 43 / 15.71 / 0.837 | 85 / 66.68 / 0.698 / 0.645 / 772.9 | 0.287 |
| S6 | 64 / 22.78 / 0.927 | 85 / 64.97 / 0.435 / 0.834 / 1109.3 | 0.622 |
| S7 | 75 / 7.81 / 0.977 | 70 / 36.12 / 1.059 / 2.329 / 416.0 | 1.075 |

### Acceptance and practical limits
Computed acceptance: `{'joint_errors_S1_S6': True, 'heights_all_shots': True, 'S7_plan_ordering': True}`. Distances: `{'actor_A_B_m': 4.914694998955542, 'S7_to_A_table_m': 0.41352192206690375, 'S7_to_B_hip_m': 4.711236094207354, 'empty_tables_between': 2}`.
The error is the median Euclidean pixel distance over all evaluated joints/frames, divided by 1024. Visible anatomical joints only: nose, ears, shoulders/elbows/wrists/hand pose tips; standing hips/legs when visibility and presence >=.65 and within frame. Seated hips and legs behind tables, seated wrists/tips without independently detected matching hands, redundant eye/mouth points, low-confidence and out-of-frame landmarks are excluded. This is an in-sample 2D consistency check of MediaPipe 3D against MediaPipe 2D. The YOLO column is a separate-detector crosscheck at original 10 fps timestamps; it is not manual ground truth.
The floor plan has separate A/B tables, A/B seats, waiter spot, two empty tables between, and every camera frustum. S7 starts at A’s table with the can in front and B farther away. Empty table coordinates, room walls and C’s cross-shot yaw/position are qualitative priors. Inspect S7-layout-overlay.jpg: the mandatory .70 m square tables do not fully reproduce source tabletop boundaries. Thus qualitative S7 plan ordering passes; precise furniture reconstruction is unresolved.
S4 camera height is constraint-limited at .900 m. Search-bound FOVs: S4, S7. focal length, hip/floor scale and depth are not uniquely calibrated. No camera sensor data or measured actor heights are available. Depth cannot resolve scale/shift by itself. A can/cup height or seat placement error changes the metric result.
All ray-plane observations, including rejected and off-table positions, remain in layout.json with provenance. Source YOLO/RA detections are preferred. S1/S4 Gemini art boxes are approximate only; S7 boxes are source-based. Prop priors are explicit where detections do not support a location; handheld terminal uses a measured wrist attachment. No false claim of recovered occluded geometry, hands, or metric room truth.
### Reproduction, runtimes and artifacts
```powershell
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py extract
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py depth
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py solve
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py layout
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py verify
```
For image/layout iteration without refitting: `... fas1.py layout --reuse`, then `... fas1.py verify`.
Latest runtimes (CPU): extraction 47.26 s; depth 17.49 s; PnP/depth comparison 26.13 s; shared-prop refinement 13.09 s; assembly 0.03 s; verification/images 4.44 s. Runtimes exclude exploratory retries.
- `data/sparning.json`: complete per-frame motion, face and hand measurements, shot assignment, coverage and model hashes.
- `data/layout.json`: room, actors, furniture, semantic props, static cameras and all placement observations.
- `data/camera-comparison.json`, `data/layout-comparison.json`: full FOV grids, alternate methods, per-frame errors and priors.
- `data/verification.json`: read-back projection metrics, per-joint errors, acceptance checks and plan distances.
- `verifiering/fas1.jpg`: 21 overlays (start / middle / final source frame of each shot).
- `verifiering/plan.png`: all cameras/frusta, tables, seats and actors in one room.
- `verifiering/S1-overlay.jpg` … `S7-overlay.jpg`: full-resolution shot sheets; `S*-frame-*.jpg`: individual frames.
- `verifiering/extraction.jpg`: actor/hand/face extraction audit; `S*-depth.jpg`: source versus relative depth.
- `verifiering/S7-layout-overlay.jpg`: table-wireframe diagnostic exposing unresolved furniture edges.
Only Phase 1 implemented. No Three.js, character renderer, player, semantic edit operations, or Phase 2/3 artifacts.

## Final Phase 1 verification (serialized layout read-back)

All 383 frames are extracted at 30 fps. Pose and required face channels: 383/383. 103 face frames use a head ROI (57 in S4, 46 in S7); matrices retain that ROI camera convention. S6 hands are hidden behind the table and have no detections; S2 has 2 frames and S7 has 25 frames without detected hands. This is missing data, not neutral hand motion.

### Camera methods and selection

1. **Unconstrained PnP:** SQPnP + iterative solvePnP for each frame/FOV, then component medians of small rotation vectors and translations per static shot. FOV candidates: every degree from 40 to 85. Unconstrained heights outside the required range under the stated hip/floor prior: S1, S2, S3, S4, S5.
2. **Depth Anything V2:** seven measured relative inverse-depth keyframes; backproject with 40/55/70/85-degree FOV and zero / 10%-median inverse-depth offsets; scale by shot-median MediaPipe shoulder width, rigid Kabsch fit to pose (no nonrigid warp or PnP in this branch). The absolute body size is NOT known from a tape measure. Offsets, scale and gravity remain assumptions. Depth generally has higher joint error and implausible heights.
3. **Height-only PnP refinement:** a single rigid static camera per shot initialized by the median; soft-L1 joint residual and camera height bounds [0.9,1.7] m. This passes the numerical tests but places all seven cameras at the lower bound and does not reconcile shared table props.
4. **Selected:** static PnP refinement plus shared can/cup bottom/top anchors on y=.75 m, with declared .168 m can / .18 m cup height priors, for S1/S2/S3/S5/S6/S7. For S4 retain height-only PnP because no shared stationary prop is reliable. Choose lowest visible-joint median among FOV candidates with <=12 px maximum anchor error and successful optimizer convergence. Per-frame pose landmarks, hip positions and world cameras are never adjusted during verification.
Placement alternatives were inspected before selection. A-can local z=.55 caused 58.3/91.4/128.7 px in S1/S3/S6 when anchors were enforced. At z=.75, coarse-FOV trials gave 33.2/46.9/53.8 px; z=.95 gave 25.9/31.4/33.8 px but leaves no can-radius margin at the table edge; z=1.15 lies outside the .70 m table. Selected z=.90 leaves a .05 m center-to-edge margin. B-cup z=.477 from an unconstrained S7 prop fit gave 42.7 px in S2; z=.55/.65/.80/.90 were compared (coarse best S2 errors 31.6/25.2/25.1/19.9 px). Selected z=.80 leaves room for the cup footprint; S7 was refitted with that shared location. These are explicit geometric priors selected for a consistent editable hypothesis, not independently recovered coordinates.
A first shared-prop trial applied robust loss to the already weighted anchor residuals, allowing 25–148 px anchor misses. Rejected. The final implementation robustifies joints only and keeps anchor residuals quadratic; failed prior trials are reported here, not silently promoted to success.
| Shot | FOV | median px | median / H | P90 px | camera y m | hip distance m | horizon y px | YOLO crosscheck px |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | 73 | 26.012 | 0.02540 | 80.17 | 1.147 | 1.508 | 372.4 | 54.91 |
| S2 | 62 | 19.510 | 0.01905 | 48.88 | 1.043 | 1.335 | 457.0 | 43.70 |
| S3 | 57 | 31.203 | 0.03047 | 71.14 | 1.208 | 1.630 | 243.7 | 49.80 |
| S4 | 40 | 18.367 | 0.01794 | 31.41 | 0.900 | 2.322 | 734.9 | 18.47 |
| S5 | 44 | 20.133 | 0.01966 | 42.85 | 1.073 | 1.674 | 400.4 | 28.48 |
| S6 | 57 | 30.454 | 0.02974 | 62.42 | 1.189 | 1.664 | 231.6 | 37.40 |
| S7 | 40 | 10.942 | 0.01069 | 22.90 | 1.042 | 4.711 | 392.3 | 11.92 |

| Shot | raw PnP FOV / px / height m | depth FOV / px / height m / distance m / horizon px | selected anchor max px |
|---|---|---|---:|
| S1 | 40 / 20.59 / 0.636 | 85 / 35.87 / 0.772 / 1.269 / 601.5 | 0.281 |
| S2 | 40 / 15.63 / 0.787 | 70 / 29.60 / 1.054 / 1.175 / 451.9 | 0.181 |
| S3 | 41 / 16.28 / 0.738 | 85 / 53.11 / 0.354 / 0.802 / 1229.4 | 0.681 |
| S4 | 40 / 17.75 / 0.779 | 85 / 32.56 / 0.989 / 0.944 / 672.3 | n/a |
| S5 | 43 / 15.71 / 0.837 | 85 / 66.68 / 0.698 / 0.645 / 772.9 | 0.287 |
| S6 | 64 / 22.78 / 0.927 | 85 / 64.97 / 0.435 / 0.834 / 1109.3 | 0.622 |
| S7 | 75 / 7.81 / 0.977 | 70 / 36.12 / 1.059 / 2.329 / 416.0 | 1.075 |

### Acceptance and practical limits
Computed acceptance: `{'joint_errors_S1_S6': True, 'heights_all_shots': True, 'S7_plan_ordering': True}`. Distances: `{'actor_A_B_m': 4.914694998955542, 'S7_to_A_table_m': 0.41352192206690375, 'S7_to_B_hip_m': 4.711236094207354, 'empty_tables_between': 2}`.
The error is the median Euclidean pixel distance over all evaluated joints/frames, divided by 1024. Visible anatomical joints only: nose, ears, shoulders/elbows/wrists/hand pose tips; standing hips/legs when visibility and presence >=.65 and within frame. Seated hips and legs behind tables, seated wrists/tips without independently detected matching hands, redundant eye/mouth points, low-confidence and out-of-frame landmarks are excluded. This is an in-sample 2D consistency check of MediaPipe 3D against MediaPipe 2D. The YOLO column is a separate-detector crosscheck at original 10 fps timestamps; it is not manual ground truth.
The floor plan has separate A/B tables, A/B seats, waiter spot, two empty tables between, and every camera frustum. S7 starts at A’s table with the can in front and B farther away. Empty table coordinates, room walls and C’s cross-shot yaw/position are qualitative priors. Inspect S7-layout-overlay.jpg: the mandatory .70 m square tables do not fully reproduce source tabletop boundaries. Thus qualitative S7 plan ordering passes; precise furniture reconstruction is unresolved.
S4 camera height is constraint-limited at .900 m. Search-bound FOVs: S4, S7. focal length, hip/floor scale and depth are not uniquely calibrated. No camera sensor data or measured actor heights are available. Depth cannot resolve scale/shift by itself. A can/cup height or seat placement error changes the metric result.
All ray-plane observations, including rejected and off-table positions, remain in layout.json with provenance. Source YOLO/RA detections are preferred. S1/S4 Gemini art boxes are approximate only; S7 boxes are source-based. Prop priors are explicit where detections do not support a location; handheld terminal uses a measured wrist attachment. No false claim of recovered occluded geometry, hands, or metric room truth.
### Reproduction, runtimes and artifacts
```powershell
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py extract
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py depth
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py solve
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py layout
scen/.venv/Scripts/python.exe -B scen/3d/fas1.py verify
```
For image/layout iteration without refitting: `... fas1.py layout --reuse`, then `... fas1.py verify`.
Latest runtimes (CPU): extraction 47.26 s; depth 17.49 s; PnP/depth comparison 26.13 s; shared-prop refinement 13.09 s; assembly 0.03 s; verification/images 4.54 s. Runtimes exclude exploratory retries.
- `data/sparning.json`: complete per-frame motion, face and hand measurements, shot assignment, coverage and model hashes.
- `data/layout.json`: room, actors, furniture, semantic props, static cameras and all placement observations.
- `data/camera-comparison.json`, `data/layout-comparison.json`: full FOV grids, alternate methods, per-frame errors and priors.
- `data/verification.json`: read-back projection metrics, per-joint errors, acceptance checks and plan distances.
- `verifiering/fas1.jpg`: 21 overlays (start / middle / final source frame of each shot).
- `verifiering/plan.png`: all cameras/frusta, tables, seats and actors in one room.
- `verifiering/S1-overlay.jpg` … `S7-overlay.jpg`: full-resolution shot sheets; `S*-frame-*.jpg`: individual frames.
- `verifiering/extraction.jpg`: actor/hand/face extraction audit; `S*-depth.jpg`: source versus relative depth.
- `verifiering/S7-layout-overlay.jpg`: table-wireframe diagnostic exposing unresolved furniture edges.
Only Phase 1 implemented. No Three.js, character renderer, player, semantic edit operations, or Phase 2/3 artifacts.

## Final visual sign-off and remaining failures
Viewed the regenerated 21 overlays (all seven full-resolution shot sheets), fas1.jpg, extraction.jpg, plan.png and S7-layout-overlay.jpg after the occlusion refit. The source actor assignments are correct. Verification assertions pass for 383 frame records, required face channels, 21-point hands, orthonormal rotations, matrix inverses, positive joint depth, ray-plane roundtrips, and agreement between solved and serialized-camera projection.

All written numerical acceptance checks pass under the documented priors; the S7 plan ordering is consistent, with A/B separated 4.915 m and S7 0.414 m from A table center. This is a conditional metric layout hypothesis, not a fully validated room reconstruction.

Independent YOLO crosscheck exceeds 40.96 px in S1 (54.91), S2 (43.70), S3 (49.80). Source-table front corners in S7 miss by 69.92 and 61.36 px (manual reference approximately +/-4 px, excluded from fitting). These remain failures/uncertainties rather than hidden acceptance evidence.

| Shot | core nose/shoulder/elbow/wrist median px | P90 px | worst-frame median px |
|---|---:|---:|---:|
| S1 | 38.32 | 80.17 | 65.11 |
| S2 | 24.09 | 48.88 | 35.37 |
| S3 | 32.11 | 71.14 | 71.86 |
| S4 | 17.85 | 31.41 | 22.27 |
| S5 | 19.37 | 42.85 | 34.75 |
| S6 | 37.42 | 62.42 | 58.66 |
| S7 | 11.10 | 22.90 | 20.05 |

A-side elbow discrepancies and S3/S6 individual-frame drift remain visible. Monocular scale, packaging dimensions and seated hip heights are assumed; the camera bounds do not independently measure height. Face orientation on 103 frames is crop-relative. Hand gaps are retained and not filled. Furniture box-base unprojection is approximate and some small props/empty furniture use explicit priors. No Phase 2 work started.

Input SHA-256 hashes and dependency versions: data/provenance.json. Final metrics: data/verification.json.

## Phase 1b — source measurements
Preserving Phase 1 images and measurements. Reusing all 383 motion frames. LSD runs on the source table regions; YOLO/EfficientDet clipped table boxes provide lower bounds, not exact edges. S7 B front/side lines and A foreground far-edge segment are retained with detection spread. Runtime 4.51 s.

{"B_front": {"segment_px": [[156.86595153808594, 556.0354614257812], [496.8739929199219, 554.3021850585938]], "samples": 15, "endpoint_std_px": [[1.2714244260546228, 0.09146881154283507], [0.7449559658513322, 0.15953463151955266]]}, "B_left": {"segment_px": [[153.28952026367188, 557.0914306640625], [253.41432189941406, 481.05186462402344]], "samples": 14, "endpoint_std_px": [[0.4404114258107335, 0.31130451312438173], [6.701916526138741, 5.031859726607379]]}, "B_right": {"segment_px": [[458.70465087890625, 501.9063720703125], [495.2115173339844, 553.4315185546875]], "samples": 15, "endpoint_std_px": [[0.4666364873979459, 0.8686889957488564], [0.43999876845380415, 0.4258089929499692]]}, "A_far": {"segment_px": [[309.4280090332031, 706.8433227539062], [419.4217224121094, 712.157958984375]], "samples": 7, "endpoint_std_px": [[0.5507521389053621, 0.22274062923750582], [0.5566185853311971, 0.15232631338033567]]}}


## Phase 1b — completed shared-intrinsic / camera-movement refinement

Scope: Phase 1b only, per granskning-fas1.md and the follow-up instruction to test per-shot extrinsics. Existing 383-frame motion reused unchanged. No Phase 2 code or assets. Old layout preserved as data/layout-phase1.json; layout.json now equals layout-1b.json byte-for-byte. Original Phase1 images, motion and verification JSON checked unchanged by SHA-256.

**Intrinsic choice:** 68 degrees vertical for all seven shots, fx=fy=759.071 px, centered principal point, zero lens distortion. This is the requested 65–70-degree main-camera prior, not a claimed phone identification or pose-only calibration. The shared FOV was not changed to improve a particular shot; sensitivity refits the same constraints from 58–75 degrees.

**Camera alternatives:** one camera per A/B setup was explicitly fit first (data/solve-1b.json). At 68 degrees it fails S3/S5/S6. Per-shot constant cameras, with the same intrinsic and shared physical can/cup/table, reduce those errors. A background SIFT+RANSAC shows about 20/78 px motion in S3/S6 versus S1; the fits have subpixel median registration residuals. B has only two reliable background matches on the blank wall, so its 3D movement is less certain: stable cup detections change from shot to shot, and a shared camera fails. Per-shot B is selected as the supported reconstruction hypothesis, not proof that the cup stayed fixed. Data/movement evidence is stored in solve-shots-1b.json and verification-1b.json.

| Shot | median px | median/H | Phase1 delta px | shared-setup px | camera y m | camera distance m | from setup mean cm | rotation from mean deg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | 26.002 | 0.02539 | -0.011 | 26.87 | 1.149 | 1.570 | 5.27 | 3.61 |
| S2 | 23.917 | 0.02336 | +4.407 | 30.78 | 1.041 | 1.177 | 3.36 | 4.14 |
| S3 | 32.631 | 0.03187 | +1.428 | 42.91 | 1.156 | 1.488 | 4.35 | 2.29 |
| S4 | 21.171 | 0.02067 | +2.804 | 21.17 | 1.137 | 1.343 | n/a | n/a |
| S5 | 26.001 | 0.02539 | +5.868 | 45.24 | 1.051 | 1.213 | 3.36 | 4.14 |
| S6 | 31.644 | 0.03090 | +1.190 | 64.52 | 1.137 | 1.507 | 3.24 | 2.92 |
| S7 | 12.356 | 0.01207 | +1.414 | 12.86 | 1.025 | 2.712 | n/a | n/a |

Pairwise camera movements (meters): `{"A": {"max_pair_distance_m": 0.09108523749298264, "pair_distances_m": {"S1-S3": 0.09108523749298264, "S1-S6": 0.07594875070150436, "S3-S6": 0.055706634228336716}}, "B": {"max_pair_distance_m": 0.06727059022775064, "pair_distances_m": {"S2-S5": 0.06727059022775064}}}`. Translations are conditional on the original MediaPipe scale and floor/hip priors.

### Shared-FOV sensitivity — all seven cameras and scene constraints refit
| vFOV | A–B m | S1 y | S2 y | S3 y | S4 y | S5 y | S6 y | S7 y | B width m | B depth m |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 58 | 3.785 | 1.165 | 1.044 | 1.182 | 1.063 | 1.052 | 1.159 | 1.029 | 0.595 | 1.388 |
| 62 | 3.568 | 1.158 | 1.043 | 1.171 | 1.091 | 1.052 | 1.150 | 1.028 | 0.594 | 1.295 |
| 65 | 3.422 | 1.154 | 1.042 | 1.164 | 1.113 | 1.052 | 1.144 | 1.026 | 0.593 | 1.232 |
| 68 | 3.288 | 1.149 | 1.041 | 1.156 | 1.137 | 1.051 | 1.137 | 1.025 | 0.593 | 1.174 |
| 70 | 3.205 | 1.146 | 1.041 | 1.152 | 1.153 | 1.050 | 1.133 | 1.024 | 0.592 | 1.138 |
| 75 | 3.014 | 1.138 | 1.040 | 1.140 | 1.189 | 1.049 | 1.122 | 1.021 | 0.591 | 1.056 |

### Tables: measured parameters and unresolved metric scale
LSD finds B front endpoints [[156.86595153808594, 556.0354614257812], [496.8739929199219, 554.3021850585938]] across 15 source frames (~340px). Final endpoint errors are 0.30/0.52px; against the older manually read 154/497 at y553: 4.27/0.79px. Foreground can base/top errors: 1.62/1.50px, on A table.
B table is a fitted 0.593 × 1.174m rectangle, y=.75m, yaw -0.95deg. Width and depth are no longer hard-coded .70m. Front and side source edges constrain them; back edge has a weak .20m seat-clearance and .85m depth prior because rear corners are occluded. **This metric estimate differs from the review's 1.0–1.1m expectation. It must not be presented as independently measured true size.** The review's approximate .5m shoulder-to-front offset is not directly observed in the video.
Alternative forcing the .5m front offset gives B 0.610 × 0.890m, back edge z=-0.139m (overlaps the seated hip plane), and S7 error 27.59px. Rejected as worse geometry/body fit. Alternative using 1.05±.10m width prior gives 0.965 × 1.800m (depth reaches 1.8m bound), S7 body error 65.95px, front errors 15.89/13.41px. Rejected. Resolving the physical width requires an independent body/package/room measurement or revisiting the model metric scale; raw pose points were not scaled/deformed to manufacture the requested width.
A table estimate is 1.050 × 1.064m. Its foreground far-edge position/yaw comes from S7 LSD. S1/S3/S6 and foreground S7 table boxes are clipped; they support only width ≥ 0.547m. Width therefore explicitly uses the review 1.05m prior above this lower bound; depth uses measured far edge and assumed .20m near-seat clearance. Food-box edge lines in close shots were inspected and rejected as table edges. No claim of exact A width/depth recovery.

### Waiter and background context
S4 refit at 68deg: camera height 1.137m, actor distance 1.343m; no bound hit. C horizontal distances to table centers: `{"table:A": 3.634198164258477, "table:B": 2.828349579763428, "table:guest:S4": 1.9045743272637534}`. C room spot [2.8,.98,.4] and yaw90 are assumed because cuts supply no shared registration landmarks. The observed left guest table is source-box unprojected to y=.75, behind C in the S4 camera; its seat is placed behind it. Guest table/seat dimensions and the remaining empty table are priors. S4-layout-overlay-1b.jpg exposes this context.

### Acceptance, limits and reproduction
Checks: `{"shared_68deg_intrinsic": true, "per_shot_movement_exception": true, "joint_error_S1_S6": true, "S7_B_edge_15px": true, "S7_can_15px": true, "heights_strictly_inside_bounds": true, "furniture_absolute_metric_size_independently_verified": false}`. The requested numerical camera/skeleton/edge criteria pass. Per-setup camera equality is replaced by the explicitly permitted movement exception; B movement has weaker independent evidence. The physical room/table metric scale remains unresolved; full geometry accuracy is not claimed.
Verification reads layout-1b.json back, checks rigid transforms/inverses, shared intrinsics, positive skeleton depth, agreement with optimizer metrics, table-supported foreground can, 21 sample overlays, and old-file preservation. Pose medians use the same visible-joint mask as Phase1 (including independent hand evidence for seated wrist/tips); not new ground truth. See per-joint errors, P90, core joints and independent YOLO crosscheck in verification-1b.json.
A first per-shot attempt initialized the wide camera from pose-only PnP and landed in a wrong behind-plane/local-minimum branch at high FOVs (S7 >100px, camera-height/table bounds). Rejected; initializing from the already verified shared-setup scene solution resolves the branch. All final fits report optimizer success; no acceptance exception is hidden.
```powershell
scen/.venv/Scripts/python.exe -B scen/3d/fas1b.py measure
scen/.venv/Scripts/python.exe -B scen/3d/fas1b.py solve
scen/.venv/Scripts/python.exe -B scen/3d/fas1b.py refine
scen/.venv/Scripts/python.exe -B scen/3d/fas1b.py verify
# Or all four stages:
scen/.venv/Scripts/python.exe -B scen/3d/fas1b.py all
```
Runtimes CPU: measurements 4.51s; shared-setup sensitivity 6.00s; per-shot sensitivity/alternatives/evidence 13.08s; verification/layout/images 2.77s. Exploratory rejected retries excluded.
Outputs: data/layout-1b.json (active data/layout.json equal); data/layout-phase1.json (archive); data/solve-shots-1b.json; data/verification-1b.json; verifiering/fas1b.jpg; verifiering/plan-1b.png; verifiering/S7-layout-overlay-1b.jpg; verifiering/S4-layout-overlay-1b.jpg; verifiering/S1-overlay-1b.jpg … S7-overlay-1b.jpg; per-shot edge audits.

## Phase 1b final visual review and handoff
Viewed all seven full-resolution overlay sheets (21 frames), fas1b.jpg, plan-1b.png, S7-layout-overlay-1b.jpg, S4-layout-overlay-1b.jpg, and the source edge audit. S7 front/side wireframes now visibly coincide with B table; foreground table edge/can align. A-side elbow discrepancies and first/last-frame drift remain visible. The diagnostic table wireframe is drawn through source people/props and is not an occlusion-correct render.

Final independent YOLO medians (px): S1 53.37, S2 33.11, S3 48.37, S4 18.49, S5 32.77, S6 35.55, S7 13.39. S1/S3 exceed 40.96px on this independent detector; the requested MediaPipe shot medians still pass. Worst per-frame medians exceed 40.96px in S1/S3/S6; acceptance is per-shot median, not every frame.

Confirmed all requested outputs exist; active layout.json equals layout-1b.json byte-for-byte; original layout archived; original motion and Phase1 diagnostics unchanged by SHA-256. All refined A/B solver groups converged.

Remaining unresolved items: true B table width under monocular/model scale (fitted 0.593m versus review estimate 1.0?1.1m), A full width/hidden depth, B camera motion versus moved cup, and C global room registration. These are explicitly flagged in the JSON and report. No Phase 2 started.


## Phase 2 ? completed implementation and verification (2026-11-07)

Only Phase 2 implemented. Built index.html, player.js, meshes.js, rigged.js, fas2.py, verifiera.py and scen3d.json; report in rapport.md. 20 semantic set objects, 12 prop instances / nine mesh factories, A/B/C rounded characters, an untracked background guest, smoothed 383-frame motion, measured face/fingers, seated-leg defaults, editable camera keyframes/actor looks/motion intensity, captions/audio, orbit, one-second JSON reload, deterministic timestamp/camera/mask captures. All dependencies/models/audio local and pinned. No Phase 3 op.py or edit demonstrations.

Acceptance: every S1?S6 shot median joint error passes 0.05H and every one of the 18 sampled close-shot silhouettes passes IoU >= .5. S7 shows B at the distant table, intervening empty tables and the registered foreground can. S6 hand gestures remain unverified (zero detected hands); S7 mouth signal is weak. These limits prevent an unqualified all-criteria claim.

Numbers below: pooled median visible rendered-joint error over start/middle/end; height=1024. IoU is mean (minimum) of three YOLO11n-seg person-mask comparisons. Rig numbers use the best tested coordinate mapping.

| Shot | Procedural px | Error/H | IoU mean (min) | VRM px | VRM IoU mean |
|---|---:|---:|---:|---:|---:|
| S1 | 18.14 | 0.01772 | 0.612 (0.558) | 127.62 | 0.363 |
| S2 | 24.32 | 0.02375 | 0.698 (0.679) | 50.03 | 0.591 |
| S3 | 29.94 | 0.02924 | 0.646 (0.591) | 113.94 | 0.413 |
| S4 | 19.03 | 0.01858 | 0.822 (0.795) | 37.79 | 0.678 |
| S5 | 24.62 | 0.02405 | 0.595 (0.579) | 91.17 | 0.461 |
| S6 | 40.00 | 0.03906 | 0.715 (0.701) | 125.98 | 0.426 |
| S7 | 12.66 | 0.01236 | 0.467 (0.421) | 23.36 | 0.499 |

Alternatives/decisions: retained procedural over CC0 VRoid base female/male with @pixiv/three-vrm 3.3.3 + kalidokit 1.1.5 (Three.js 0.170.0). Embedded licenseName=CC0 and commercialUssageName=Allow checked before use; licenses and hashes in modeller/licenses-vrm.json and vendor/manifest.json. Four rig mappings compared: unchanged, unmirrored Y/Z + left/right, X/Z inversion, combined. Unmirrored is best overall; camera/head basis corrected. Remaining rig performance loses the measured forward lean and hand gestures, and blue-haired school-uniform assets differ in silhouette/style. This is a baseline comparison, not a general limitation of VRM.

Compared rounded-box versus ellipsoid torso, initial versus anatomically higher head/ears, raw pose wrist anchors versus HandLandmarker image-ray wrist anchors at unchanged pose camera-depth. Selected ellipsoid/anatomy correction and fused wrist anchors; both avatar routes use the same fused data. 5-frame, order-2 Savitzky?Golay, bounded by shot and detection runs; face quaternions normalized. A S1/S3 temporal wrist/image median errors 0.74/2.07px over 145/57 hand samples. This is fit consistency, not independent ground truth. Hand-anchor 3D shifts median 4.84/5.16/12.53/3.91/4.82/n.a./5.44 cm by S1?S7; maximum 22.52 cm, exposing depth/pose uncertainty. Raw sparning.json retained.

Table decision: active layout.json remains byte-identical to layout-1b.json; all camera extrinsics and shared 68-degree FOV unchanged. Trust B measured narrow/deep .593 x 1.174 m table per new orchestrator note; the previous width guess is superseded. In scen3d.json only, A weak depth prior 1.064 -> .800 m, retaining the measured far edge/yaw exactly. Pilot source-body occlusion IoU improved S1-start .487 -> .556 and S3-start .462 -> .594. Empty table 1 moved [.40,0,-.10]m and a second empty table added as explicit unmeasured dressing priors. S7 hides foreground A food/cup/tray absent from the source crop.

Failures/uncertainty: S3 f114 median 54.21px and S6 f336 53.08px exceed the per-frame threshold although their shot medians pass. S7 silhouette mean .467/min .421, largely from inferred seated legs/proportions; S7 has no numeric IoU requirement. Its jawOpen range .0041?.0335 yields barely visible far-mouth motion. S6 has no measured hands: relaxed finger fallback, no invented gesture. Model body scale, hidden limbs, C global registration and room dressing remain priors; forearms can stretch, finger/prop contacts and cloth/table intersections are approximate. YOLO masks are automatic, not labeled truth.

Verification: 21 normal + 21 mask images per avatar; all 383 procedural frames rendered for temporal audit; six speaking-shot mouth min/max pairs; prop catalog; three free-camera views; player screenshot. Inspected all seven procedural three-frame source/render/overlay sheets, the VRM comparison, mouth/prop sheets, orbit views and UI. Main geometry is fully volumetric from side/back.

Browser: zero uncaught errors and zero external page requests. Frozen hash captures byte-identical; play advances. JSON mutation changed both spec and rendered can x .11706 -> .24006 m, then original JSON restored. Actual muted headless audio played at rate1, readyState4; drift76.4ms within120ms sync threshold. Responsive player viewport clipping and status encoding found visually and corrected.

Warm-cache runtimes: preparation 0.83s; full verification 116.60s (CPU SwiftShader, cached source masks), excluding initial downloads/segmentation, exploratory alternatives and final UI-only follow-up. The first headless attempt failed because the GPU sandbox could not start; the local isolated-profile software-render configuration succeeded.

Run preparation: scen/.venv/Scripts/python.exe -B scen/3d/fas2.py. Verify: scen/.venv/Scripts/python.exe -B scen/3d/verifiera.py. Serve: scen/.venv/Scripts/python.exe -m http.server 8000 --directory scen/3d; open http://localhost:8000/. Preparation rebuilds generated scen3d.json.

Verification images: verifiering/fas2/fas2-procedural.jpg; S1-procedural.jpg through S7-procedural.jpg in that directory; fas2-vrm.jpg; mouths.jpg; props-catalog.png; orbit.png; orbit-A.png; orbit-C.png; player.png. Per-frame normal/mask/source/comparison files alongside. Machine results: data/verification-2.json, temporal-verification-2.json, hand-anchor-2.json, phase2-status.json, provenance-2.json, capture-2-full.json and player-check-2.json. Full report: rapport.md.

Phase 2 work stopped here.

## Phase 3: completed by the orchestrator (Claude) after Codex hit its usage limit (7 Nov, 20:21)
Codex had started Phase 3. It measured props on source frames with Gemini Flash-Lite (7 free calls, `data/props-source-S*-3.json`), added `food_box`/`paper_wrap` meshes and B's single-volume hair to `meshes.js`, and wrote `scene_runtime.js`, which was not yet wired in. Claude did the rest:

- **Prop calibration** (`kalibrera_rekvisita.py`): least squares for x, z, width and height per prop over all shots where it is visible, with each shot's own camera. Wraps were added as separate props: `A:burger_wrap`, `A:rear_wrap`, `B:burger_wrap`. Before calibration props were 1.2–2.4× too large, and B:burger was 661 px off. After it, can, cup, sauce and B's burger, box and fries are within ±25% and 30 px. A's burger, fries, tray and rear wrap stay 25–72 px off in some shots (partly occluded, plus per-shot camera pitch uncertainty). Report: `data/kalibrering-3.json`.
- **Camera refinement against props** (`forfina_kameror.py`): tested and **rejected**.
  - Props only: the S3 body error rose from 27 to 37 px.
  - Body plus props, with S1 as anchor or all cameras free: the cameras hit the bounds (−3° pitch, −6 cm) and the body error moved around rather than shrank.
  - Free table height (`testa_bordshojd.py`): 0.745 m, no gain.
  - Kept: body-derived Phase 1b cameras. Quick-verify medians: S1 16 px / IoU .68, S2 23/.69, S3 27/.67, S4 14/.84, S5 36/.68, S6 39/.73, S7 18/.43.
- **Player** (`player.js`), now using `scene_runtime.js`:
  - camera keyframes and orbit,
  - per-shot actor transform keyframes,
  - motion intensity, mirror and mood per shot,
  - a frozen per-shot source camera (`source.camera`), so the edited view camera never distorts the measured pose,
  - actors added to other shots loop their own shot's motion with their own source camera.

  Also fixed a frame-boundary rounding bug (`floor(t*30)` → `+1e-5`).
- **`op.py`**: semantic selectors, `list`/`show`/`--help`, 19 operations, history and undo. Each op takes 3–14 ms; the first op that needs a head point builds `data/huvudpunkter.json` once (~100 ms).
- **Demo** (`demo-andringar.sh`, `demo_render.py`): all seven requested edits applied and rendered (`verifiering/fas3/demo/`). Three issues were found visually and fixed:
  - The dolly ended inside A's hair: the head point is now the posed nose in world space.
  - The added waiter stood outside the window wall: actors are now clamped inside the walls.
  - B was missing at the first S8 frame: the boundary rounding bug above.
- **Timeline sweep:** 69 frames over the edited 13.6 s, 0 page errors, the main actor present in every frame.
- **Remaining:**
  - "Turn toward" rotates the whole measured pose; a head-only "look at" is missing.
  - The waiter added in S6 is cropped by the tight framing.
  - Type swaps are global, not per shot.

## Phase 4 (7 Nov 2026, Claude; Codex was out of credits): neutral avatars, stable arms, word timing, designed voices

- **Stabilization** (`stabilisera.py` → `data/motion-3.json`):
  - Shoulders, elbows and wrists are placed on rays from the source camera through their image landmarks, at constant per-actor bone lengths. Of the two sphere solutions, the one closest to MediaPipe depth blended with the previous frame wins. When the ray misses the sphere, the point on the sphere nearest the ray keeps the bone length.
  - Occluded joints hold and decay toward the shot's rest pose. A One-Euro filter (fc 1.2, beta 0.25) runs last.
  - Results: flap index 0.0027 → 0, 3D jitter median 0.021 → 0.004 m, 2D jitter median 6.2 → 1.3 px (p90 22 → 5), reprojection median 24.4 → 10.4 px.
- **Avatar** (`avatar_xbot.js`): Mixamo X Bot from three.js r170, the new `defaultAvatar`.
  - Retargeting:
    - Each bone has an anatomical frame measured in the model's rest pose, and its world rotation is `frame(target)·frame(rest)⁻¹·rest`, so no T-pose or A-pose guessing is needed.
    - The spine is slerped between hips and chest, with a correction that puts the shoulder midpoint on the target.
    - Limbs chase target points from the actual joint position (clavicle → shoulder, upper arm → elbow, forearm → wrist), and the hand basis and fingers come from the hand landmarks.
    - The neck turns and stretches (±20 %) so the nose lands on the measured nose; the head orientation is unchanged.
  - Proportions: child bone offsets are scaled per actor to `look.proportions`, measured from motion-3.
  - Face:
    - The eyes, brows and mouth are placed by skinned raycasts onto the head surface, cast from outside inward because front faces are culled.
    - They are kept level in the anatomical head frame.
    - A per-actor `motion.faceBaseline` (20th percentile) is subtracted; without it A's resting `browInnerUp` of 0.475 made every face look worried.
  - Look:
    - Per-vertex region colour from the dominant skin weight: role-coloured top, dark trousers and shoes, and one neutral skin tone for head and hands. No hair and no clothing copied.
    - Clothing volume along the normals: 13 mm on the torso, less on the limbs; `look.klädvolym` multiplies it.
- **Verification** (`verifiera_fas4.py`, `data/verification-4.json`, `verifiering/fas4/kontaktark.jpg`, `remsa-S1-xbot.jpg`), 3 frames per shot:

  | Shot | X Bot joints | X Bot IoU | Procedural joints | Procedural IoU |
  |---|---|---|---|---|
  | S1 | 0.020 H | 0.46 | 0.019 H | 0.62 |
  | S2 | 0.015 H | 0.62 | 0.012 H | 0.72 |
  | S3 | 0.025 H | 0.61 | 0.020 H | 0.68 |
  | S4 | 0.018 H | 0.78 | 0.018 H | 0.83 |
  | S5 | 0.017 H | 0.57 | 0.019 H | 0.65 |
  | S6 | 0.037 H | 0.60 | 0.031 H | 0.74 |
  | S7 | 0.007 H | 0.53 | 0.006 H | 0.52 |

  - **The S1 silhouette misses** (0.46 < 0.5). The doll lies inside the source mask (1–2 % excess); what is missing is the hair halo and the loose jacket. Even 2.6× clothing volume reaches only 0.45–0.52, so this is a known deviation from the no-likeness rule, not a placement error.
  - Rendered arm jitter: X Bot median 1.39 px, p90 4.14 px, the same as procedural.
  - A 0.1 s sweep over the timeline: 0 page errors.
  - Chrome/SwiftShader crashes sporadically on long runs (CDP 1006, memory stable at ~75 MB). The verifier now runs chunks of 60 frames with retry and split.
  - `capture.mjs` now uses a fresh profile on every run; a cached profile had served stale JS.
- **Word timing** (`ordtider.py`):
  - Model: KBLab kb-whisper-medium via faster-whisper, int8 on CPU, 134 s; the known lines are the prompt; match ratio 0.978.
  - Lines now carry `words[]` and their real start and end. All speakers were checked by F0: A 211–262 Hz, B 151–199 Hz. "Eller liksom…" is A, off-screen over the waiter shot.
  - PyAV in the venv lacks faster-whisper's `metadata_errors` argument, so the audio is decoded with ffmpeg instead.
- **Cut grammar** (`kamera_ingest.py` → `shots[].ingest`, `data/kamera-ingest.json`):
  - In-shot camera motion is below 1° (≤ 10 px, `kamerarorelse.py` → `data/kamera-3.json`): the camera is on a tripod. The angle mismatches come from the per-shot solve, not from motion.
  - Shot sizes are MCU/CU at 0.8–1.1 m plus one MS at 2.5 m, with a lens equivalent to 26.7 mm.
  - Every cut is a J-cut 0.05–0.07 s after the next speaker starts, except the waiter insert, which runs 0.71 s.
- **Dialogue-safe `langd`** (`op.py`, `source.knots`):
  - Default mode `replik`: pauses shrink first, then speech may go up to ×1.15; words are never cut.
  - If the target cannot be reached, the op stops at the shortest safe length and says why.
  - The player follows the time map for motion, audio (`playbackRate`, `preservesPitch`) and captions.
  - In the demo, `S4 1.6 → 2.12 s`, `S1 1.9 → 2.10 s` and `S3 1.5 → 1.65 s` stop where words would otherwise be cut.
  - Duplicated shots are silent: no line, no captions, closed mouth.
- **Designed voices** (`roster.py`):
  - Piper, local: alma (CC BY 4.0) for A and nst (CC0) for B. Alma won the round-trip test against lisa and nst on word error (0.069 vs 0.082/0.090).
  - Each line is fitted into its word-time slot (length_scale, then atempo); all seven lines land within ±0.02 s.
  - Mouth curves `data/mun-A.json` and `data/mun-B.json` come from the RMS envelope.
  - The player has a sound mode, designed (default) or original; in designed mode the mouth follows the voice.
- **Captions:** word by word (teleprompter), following the word times.
- **Preview:** `mvp_render.py` → `verifiering/fas4/mvp-xbot.mp4` (X Bot, designed voices, captions). This is for review only; the product plays live.
- **Docs:** `SYFTE.md` (purpose, wiki rules, scene-plan verbs mapped to ops), `FRON-1.5.md` (next-scene pipeline seeds).

### Phase 4, continued (7 Nov, late)
- **`titta`** (head-only look-at): `titta S4 C --mot A [--mangd .85] [--fran s] [--ramp s]` writes `shots[].actors[].motion.lookAt`. The player eases it in (smoothstep), and both avatars turn only the head, capped at 80° from the measured gaze. The op warns when more is needed: C→A in S4 needs 143°, so use `vand` for the rest.
- **`replik`** (own lines): new text in the same word-time slot. Word times are estimated by word length, a designed voice fits the slot, and the teleprompter shows the new words. The rail flags a line that needs more than 15 % higher speed than the original in that slot; a 19-word replacement for line 7 was flagged at ×4.15.
- **`casting`**: role name (shown before the line in the captions, also off-screen), voice and shirt colour. The doll is rebuilt when its look key changes.
- **Voice speed:** a Piper voice load costs 5.2 s, which is ONNX session creation in onnxruntime 1.31; optimisation levels, threads and prepacking made no difference. Two fixes:
  - a per-line cache, so an unchanged line takes 0 s;
  - `rostserver.py` (warm, port 5193), which brings a changed line to 0.64 s and a voice swap to 0.35–0.46 s. Without the server `op.py` falls back to a subprocess (~6 s).
- **Player:** mouth tracks are refetched on every rebuild, the designed mix carries a version query (`audioVersion`), and the speaker with the latest-started line wins the caption, which fixed A's line lingering over B's J-cut.
- **The background guest in S4** is now a neutral doll too.

### Phase 4, closing (7 Nov, late): silhouette, full audio verification
- **Hair:** the doll's own head surface, inflated 8 mm along seam-averaged normals, kept above a backward-tilted hairline (55° from the crown at the front, 120° at the back). It is a skinned mesh on the same skeleton, identical for every doll, so no hairstyle is copied. An analytic ellipsoid cap was tried first and rejected: it did not fit the X Bot head and the skin poked through.
- **Loose garment volume, the same for all:** torso 30 mm, shoulders 22 mm, arms 18 mm, legs 6 mm along the normals.

  | Shot | IoU before (mean / min) | IoU after (mean / min) |
  |---|---|---|
  | S1 | 0.464 / 0.428 | 0.515 / 0.474 |
  | S2 | 0.620 / 0.619 | 0.667 / 0.665 |
  | S3 | 0.606 / 0.595 | 0.642 / 0.640 |
  | S4 | 0.784 / 0.775 | 0.807 / 0.803 |
  | S5 | 0.573 / 0.549 | 0.613 / 0.596 |
  | S6 | 0.595 / 0.577 | 0.651 / 0.631 |
  | S7 | 0.526 / 0.523 | 0.556 / 0.555 |

  Joints and jitter are unchanged.
  - **The one frame still under 0.5** is S1 frame 0 (0.474). 17k of the missing pixels are above the shoulders (her long hair) and 67k below (her large knit jacket).
  - A long-hair casting option (a hair curtain down to the shoulders) reached only 0.482 and looked like thin strands seen edge-on, so it was rejected and removed.
- **`verifiera_ljud.py` (`data/verification-ljud.json`), all passing:**
  - **A, base, one frame per word:** all 46 words appear in the captions with the correct speaker and the correct said-count (teleprompter). The on-screen speaker's mouth is open in 100 % of word mid-frames, with median jawOpen 0.52. Mouths are closed in the pauses between lines (max 0.021). The mix holds −11.8 to −17.1 dBFS in every line and is silent between lines.
  - **B, edited:** demo-andringar.sh plus titta, replik and casting, swept every 0.1 s.
    - 145 frames, 0 page errors, the main actor in every frame.
    - Source time is monotonic within every shot.
    - 30 silent copy frames with no caption and a closed mouth.
    - Every caption carries a role name, and the new line shows.
  - **Test-definition fixes:** Whisper gave zero-length words, so the said-count now counts words whose start is ≤ t. The pauses inside a line belong to the designed voice's own rhythm and are no longer measured; only pauses between lines are.
- **`titta` fix:** the gaze estimate now includes the shot's `vand` yaw. After `vand S4 C --mot A` the remaining head turn is 17°, not 157°.
- **The MVP preview was re-rendered** with the new look.
