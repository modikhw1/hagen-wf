# Phase 2 — rendered reconstruction and verification

Built the real 3D set, three rounded procedural actors, editable scene JSON and offline player. **S1–S6 numeric acceptance: PASS.** S6 hand-gesture fidelity cannot be verified because the input contains no detected hands. S7 mouth movement is weak. Phase 3 has not been started.

## Measured results

576 × 1024 captures, actual Three.js WebGL rendering in headless Chrome/SwiftShader. Three frames per shot: start, middle, last frame before the cut. Joint error is the pooled median of visible anatomical joint centers on the rendered body versus the source MediaPipe landmarks, divided by 1024. Nose/ears are head mesh anchors; fingertips are rendered finger joints. The visibility mask is the Phase 1b mask (confidence ≥ .65; seated wrist/tips require independent detected hands). No image-space silhouette warp is used.

YOLO11n-seg, 1024 input, person class, CPU, retina masks. The main person is selected by containing the tracked nose and nearest box center; detection confidence and masks are saved per frame. IoU uses the visible main-actor render, including set/prop occlusion, against this automatic source mask. This is detector agreement, not manually labeled ground truth. We apply the 0.5 limit to **every** sampled S1–S6 frame, stricter than a shot mean.

| Shot | Frames | Median joint px | Error / H | IoU start / middle / end | Mean IoU |
|---|---|---:|---:|---|---:|
| S1 | 0, 36, 72 | 18.14 | 0.01772 | 0.558 / 0.673 / 0.605 | 0.612 |
| S2 | 73, 93, 113 | 24.32 | 0.02375 | 0.679 / 0.697 / 0.719 | 0.698 |
| S3 | 114, 142, 170 | 29.94 | 0.02924 | 0.591 / 0.666 / 0.681 | 0.646 |
| S4 | 171, 213, 255 | 19.03 | 0.01858 | 0.829 / 0.840 / 0.795 | 0.822 |
| S5 | 256, 268, 280 | 24.62 | 0.02405 | 0.589 / 0.616 / 0.579 | 0.595 |
| S6 | 281, 308, 336 | 40.00 | 0.03906 | 0.717 / 0.728 / 0.701 | 0.715 |
| S7 | 337, 359, 382 | 12.66 | 0.01236 | 0.481 / 0.421 / 0.498 | 0.467 |

The criterion is a per-shot median, not a bound on each frame or joint. Sample frame medians over 51.2px: S3 f114 (54.2px), S6 f336 (53.1px). Individual elbows/fingers can deviate more. S7 is reported but is outside the numeric S1–S6 criterion; its inferred legs reduce whole-person IoU.

## Alternatives and decisions

- **Procedural versus VRM:** both run locally, use the same smoothed motion, cameras and hand-wrist fusion, and are captured at identical times. VRM uses pinned `@pixiv/three-vrm@3.3.3` and `kalidokit@1.1.5`; Three.js is pinned to `0.170.0`. The default is procedural: measured positions remain controllable, A’s forward lean and gestures read better, and costume/hair match the roles. The CC0 sample VRMs have different proportions, blue hair and school clothing, which also affect IoU. This is a comparison of these implementations/assets, not a claim that VRM cannot fit the clip.

- **Rig coordinate alternatives:** tested unchanged Kalidokit, unmirrored left/right plus reflected Y/Z rotations, X/Z basis inversion, and both. The unmirrored mapping gives the lowest mean midpoint joint error across seven shots and is retained. The camera-to-head basis was separately corrected so the model faces the camera. Candidate numbers are in `data/vrm-retarget-candidates-2.json`. The remaining solver does not reconstruct A’s measured forward lean reliably; fixed rig lengths and clamped rotations produce misplaced arms.

| Shot | Procedural px / IoU mean | VRM px / IoU mean |
|---|---:|---:|
| S1 | 18.14 / 0.612 | 127.62 / 0.363 |
| S2 | 24.32 / 0.698 | 50.03 / 0.591 |
| S3 | 29.94 / 0.646 | 113.94 / 0.413 |
| S4 | 19.03 / 0.822 | 37.79 / 0.678 |
| S5 | 24.62 / 0.595 | 91.17 / 0.461 |
| S6 | 40.00 / 0.715 | 125.98 / 0.426 |
| S7 | 12.66 / 0.467 | 23.36 / 0.499 |

- **Body shape:** compared the initial rounded-box torso with an ellipsoid torso, anatomically higher ears/cranium, continuous long hair and narrower B sleeves. The latter is the default. Initial midpoint data/image are preserved in `data/verification-2-baseline.json` and `verifiering/fas2/baseline-procedural.jpg`. This is a stylized volume model, not a recovered body surface.

- **A table occlusion:** the Phase 1b seat-side edge clipped the lower torso/arms too early. Shortened the weak depth prior from 1.064 to 0.800 m while retaining the measured S7 far edge and yaw exactly. A pilot raised S1-start IoU 0.487→0.556 and S3-start 0.462→0.594. This refinement exists only in `scen3d.json`; `data/layout.json` remains byte-identical to `layout-1b.json`. All seven measured 68° cameras and B’s 0.593 × 1.174 m table are unchanged. The orchestrator’s former wide-table guess is superseded by the measured narrow/deep table.

- **S7 dressing:** moved the unmeasured empty table by [.40,0,-.10] m and added a second empty table to make the intervening row visible; these are declared layout priors, not new measurements. S7 hides A’s cup/food/tray that are absent from the source crop; the registered foreground can remains.

- **Hand anchoring:** first compared raw pose-wrist attachment (hands too low or under the tabletop) with independent HandLandmarker wrist-image rays at the original pose-wrist camera-depth. Selected the latter for detected hands, for both avatar routes. The 21-point hand geometry remains metric. Five-frame/order-two Savitzky–Golay filtering is bounded by shot and contiguous detection runs. Missing hands receive relaxed fingers; no hand motion is invented for S6. Raw motion is preserved alongside `poseFused`. Hand depth and metric size remain inferred.

| Shot | Detected hand samples | Median anchor shift cm | Maximum shift cm | Rendered wrist/image median px | jawOpen min–max |
|---|---:|---:|---:|---:|---|
| S1 | 145 | 4.84 | 22.52 | 0.83 | 0.0000–0.3927 |
| S2 | 50 | 5.16 | 13.30 | 3.74 | 0.0000–0.1710 |
| S3 | 57 | 12.53 | 17.77 | 2.14 | 0.0000–0.4005 |
| S4 | 111 | 3.91 | 7.74 | 0.25 | 0.0000–0.0262 |
| S5 | 25 | 4.82 | 12.07 | 2.05 | 0.0000–0.2647 |
| S6 | 0 | n/a | n/a | n/a | 0.0000–0.3356 |
| S7 | 21 | 5.44 | 7.14 | 0.70 | 0.0041–0.0335 |

The wrist/image comparison is a fit diagnostic because those observations drive the anchors. Maximum corrections (up to 22.5 cm) expose inconsistent monocular pose/hand estimates, not measured physical hand travel. The procedural limbs can stretch with noisy measurements. Face rotation uses the measured camera-relative matrix/quaternion; jaw, brows, smile and blinks drive mesh parameters. All 383 frames were rendered for the temporal audit. S7 jaw amplitude produces only about a pixel of visible movement at that distance, so distant lip readability remains uncertain.

## Player and reproducibility

Set: 20 semantic objects; props: 12; actors: A/B/C plus one neutral untracked background guest in S4. Real floor/walls/window/ceiling, pendants, counter, tables/chairs; nine mesh factories including the pizza slice. JSON uses meters, seconds and degrees, includes actor looks and motion intensity/references, per-shot placements/yaw, camera keyframes, dialogue/audio ranges and an edit log. Burger/fry/terminal attachments follow hands. Seated legs use stable inferred geometry.

The player provides sequential playback, captions (including off-screen speakers), optional local source audio, orbit inspection and an avatar comparison selector. It polls JSON every second, validates a replacement before rebuilding, and keeps playback time. Camera keyframes interpolate position/target/up/FOV. `#t=1.2&mode=mask&cam=S1` freezes the frame; `&capture=1` hides the UI for 576×1024 screenshots. Mask mode renders the tracked main actor white with depth-correct black occluders.

Browser checks: 0 uncaught errors; 0 external page requests. Frozen hash screenshot byte-identical: True. Play advanced time: True. JSON hot reload changed revision and the rendered can position, then restored the original file: `{'revision': 2, 'can': 0.24005973306517575, 'renderedCan': 0.24005973306517575, 'before': 1}`. Local audio duration: 12.746009 s (video 12.7667 s). All runtime modules/models/audio are local. Model metadata in `modeller/licenses-vrm.json` says `licenseName: CC0`, `commercialUssageName: Allow` for both models; archive/member hashes and licenses are retained.

```powershell
scen/.venv/Scripts/python.exe -B scen/3d/fas2.py
scen/.venv/Scripts/python.exe -B scen/3d/verifiera.py
scen/.venv/Scripts/python.exe -m http.server 8000 --directory scen/3d
```

Open `http://localhost:8000/`. The preparation stage rebuilds generated motion and scene JSON from Phase 1b inputs; retain any deliberate scene edits separately before rerunning it. No build step. First preparation downloads pinned public dependencies/models; subsequent preparation and all playback/verification run from local files. Verification requires the stated Windows Chrome path, Node and the existing Python venv.

Measured repeat runtimes: preparation 0.83 s with downloads cached; verification 116.60 s with source segmentations cached, including both avatar routes, screenshots, all 383 temporal frames and browser checks. The first download/segmentation pass and exploratory iterations are not included. Model files and source/verification image dimensions are retained for reruns.

## Verification images and limits

- [Seven-shot source/render/overlay overview](verifiering/fas2/fas2-procedural.jpg). Full three-frame sheets: [S1](verifiering/fas2/S1-procedural.jpg), [S2](verifiering/fas2/S2-procedural.jpg), [S3](verifiering/fas2/S3-procedural.jpg), [S4](verifiering/fas2/S4-procedural.jpg), [S5](verifiering/fas2/S5-procedural.jpg), [S6](verifiering/fas2/S6-procedural.jpg), [S7](verifiering/fas2/S7-procedural.jpg). Green contours = source mask; magenta = render.
- [VRM comparison](verifiering/fas2/fas2-vrm.jpg).
- [Mouth extremes](verifiering/fas2/mouths.jpg), [prop factories](verifiering/fas2/props-catalog.png), [player](verifiering/fas2/player.png).
- Free-camera renders: [room/B](verifiering/fas2/orbit.png), [A](verifiering/fas2/orbit-A.png), [C](verifiering/fas2/orbit-C.png). Individual source, normal render and binary-mask PNG/JPG files are alongside the sheets.

Remaining limits: S6 hand fidelity is unverified; S7 whole-person IoU is below 0.5 and the far mouth is barely readable; legs/hidden anatomy, room bounds, the waiter’s global placement and added furniture are priors. Forearm/finger alignment, face likeness, grasp contacts and occasional clothing/table intersections are approximate. A’s table depth refinement is an occlusion fit, not a new physical size measurement. Automatic source masks and monocular metric scale remain uncertain. The numerical close-shot pass does not establish complete reconstruction accuracy or guarantee every frame meets every threshold.

## Final browser/visual review

Audio was actually played in muted headless Chrome (readyState 4, paused=False, rate=1); measured audio/scene difference 76.4 ms, within the player's 120 ms correction threshold. The final player screenshot uses the corrected responsive viewport and readable status text. This UI-only follow-up is recorded in `data/player-check-2.json`; the full render-run metadata is in `data/capture-2-full.json`. Its additional runtime is excluded from the full-render runtime above.
