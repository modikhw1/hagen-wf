## 2026-11-09 — CODEX-BAKA completed

Built `baka.mjs`, the read-only `dump.js` player hook, `importera_bake.py`,
`verifiera_bake.py`, and `compare_masks.py`. Integration/schema/commands: `BAKE.md`.

Decisions:

- Bake the existing evaluated X Bot, including all 67 bones per actor, root
  transforms, proportion changes, all five face ellipsoids, actor visibility,
  hand-attached prop world transforms, camera, projected joints and original-audio
  mouth values. Do not reproduce the retarget.
- Export the player-modified bind geometry/weights (clothing volume and hair)
  once into `bake-assets.json`; animation is in `bake.json`. Chunk the 38.9 MB
  asset export across CDP to avoid large-response disconnects.
- Match the scene builder: Blender frame i is scene time i/30, starting at frame
  0. All transform and viewport/render visibility channels have a key on every
  frame; constant interpolation preserves cuts.
- Import Xbot.glb once per actor, retain the importer's rest axes, derive
  C_b = (conv M_gl_bind)^-1 M_bl_rest and apply conv M_gl_pose C_b in armature
  space. Use linear skinning, the original inverse bind matrices, and
  bone-parented ellipsoids with the bone-tail offset cancelled.
- Actor root names are actor:A/B/C/guest. Use look.shirt colours with a region
  material palette so both Workbench and shader renderers display them. The
  public importera(bake_path, scen_path) adds actors only.
- The player mask uses black depth-tested room/prop occluders and only the main
  actor is white. Verification builds exact black occluders temporarily; none
  are created by importera or saved into the actor-only bake.blend.

Acceptance results: **PASS**. Both requested commands completed successfully.
`bygg_scen.py --utan-ljud --spara .../verifiering/integration.blend` also completed;
all 20 set roots, 15 prop roots, seven cameras, frames 0–382 and Workbench shirt
palettes were checked after reopening that file.

383 contiguous frames at 30 fps = 12.766666666667 s. Shot spans: S1 0–72,
S2 73–113, S3 114–170, S4 171–255, S5 256–280, S6 281–336, S7 337–382.
Every first/last frame and all player shotAt probes agree. Source-time/audio-time
mapping error = 0 s; frame count and mapping agree with mvp_render.py --original.

Compared evaluated Blender joint positions, mouth scale/aperture, all face world
transforms and keyed visibility on **all 383 frames**, including the guest in S4.
Also checked every bone head and projected main joints. Compared native Blender
576×1024 Workbench masks to the unchanged player at first+2, middle and last−2 in
each shot (21 renders). These are per-shot all-frame joint statistics and the
minimum/mean of the three IoUs:

| Shot | Frames | Joint median mm | Joint max mm | IoU min | IoU mean | Mouth aperture max error m | Image |
|---|---:|---:|---:|---:|---:|---:|---|
| S1 | 73 | 0.000744 | 0.002718 | 0.994740 | 0.994778 | 2.545e-9 | [S1](verifiering/S1-comparison.png) |
| S2 | 41 | 0.000825 | 0.002857 | 0.995382 | 0.995467 | 1.306e-9 | [S2](verifiering/S2-comparison.png) |
| S3 | 57 | 0.000730 | 0.002668 | 0.995598 | 0.996219 | 2.486e-9 | [S3](verifiering/S3-comparison.png) |
| S4 | 85 | 0.000773 | 0.003025 | 0.995747 | 0.995839 | 6.634e-10 | [S4](verifiering/S4-comparison.png) |
| S5 | 25 | 0.000745 | 0.002882 | 0.994819 | 0.995045 | 1.345e-9 | [S5](verifiering/S5-comparison.png) |
| S6 | 56 | 0.000731 | 0.002730 | 0.995440 | 0.995897 | 1.851e-9 | [S6](verifiering/S6-comparison.png) |
| S7 | 46 | 0.000788 | 0.002863 | 0.985302 | 0.985721 | 6.697e-10 | [S7](verifiering/S7-comparison.png) |

Maximum projected-joint error: 0.003290 px. Visibility errors: 0. Mouth
local-scale error ≤ 1.273e-9; mouthOpen scalar error ≤ 1.383e-8. Last full
verification took 81.0 s.

Player visual regression: **42/42 PNGs pixel-identical** (21 normal + 21 mask),
served from the same source with the hook enabled vs removed. No external
requests or page errors. All seven comparison sheets were visually inspected.

Limits and uncertainty:

- This verifies transfer fidelity to the player, not ground-truth anatomy,
  camera calibration or the original MediaPipe estimates. The untracked
  background guest remains exactly the player's guest.
- Native renderers differ slightly at silhouette edges; the smallest S7 figure
  has the lowest IoU (0.985302), still above 0.9 in every sampled frame.
- ffprobe reports source-audio.m4a duration 12.746009 s: the existing source ends
  **20.658 ms** before the mapped scene end. The final sampled audio time is
  12.733333 s, inside the source. No motion or audio retiming was introduced.
- mvp_render.py uses linear source intervals; future piecewise source.knots that
  disagree with that mux are explicitly flagged by verification.

Artifacts: `bake.json`, `bake-assets.json`, `bake.blend`, `verifiering-bake.json`,
`verifiering/S1-comparison.png` through `S7-comparison.png`, and the optional
builder integration snapshot `verifiering/integration.blend`.

## PS2-mallar

2026-11-09. Built-in image generation produced three generic character sheets
(`ps2/mallar/A.png`, `B.png`, `C.png`), `ps2/miljo.png`, and seven 576x1024
keyframes (`ps2/forsta_S1.png` through `forsta_S7.png`). Twenty generation calls;
regenerations S1–S7: 1, 1, 2, 1, 2, 1, 1 (maximum allowed: 3 per shot).

Final raw person-mask IoUs against visible Blender actor masks:

| Shot | IoU |
|---|---:|
| S1 | 0.724421 |
| S2 | 0.762899 |
| S3 | 0.838825 |
| S4 | 0.796401 |
| S5 | 0.706580 |
| S6 | 0.778841 |
| S7 | 0.708546 |

All seven exceed 0.70. YOLO11n-seg, person class, confidence 0.25, image size
1024, retina masks; union IoU with no mask alignment or manual correction.
Blender masks retain set/prop occlusion. All eleven PNG assets decoded and
dimensions/hashes were verified; seven source/blockout/PS2 triptychs were
visually inspected. Consistent PS2 art treatment; no obvious real-person
likeness, real branding or text observed in generated assets. Source panels
retain original people/branding/captions solely for comparison.

Remaining failures: exact pose, object-edge placement and environment
continuity are not achieved. Terminal/carton proportions, limbs and table
edges drift; S6 glazing differs from S1/S3. S5/S7 pass narrowly. The environment
frame interprets S4's empty room, rather than reproducing calibrated geometry.
These limitations are detailed per shot, not counted as exact-layout passes.

Report: [ps2/RAPPORT.md](ps2/RAPPORT.md). Exact template prompts:
[ps2/mallar/README.md](ps2/mallar/README.md); all prompts and ordered references:
`ps2/prompter/`, `ps2/generation_manifest.json`. Checks:
[ps2/kontroll.json](ps2/kontroll.json), `ps2/kontroll_S1.jpg`–`kontroll_S7.jpg`,
`ps2/masker/`. Reproduction commands are in the report.
