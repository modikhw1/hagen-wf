# PS2-mallar — report

Created with the built-in image generator: **3 character sheets, 1 environment frame and 7 keyframes**. All keyframes/environment are 576×1024; sheets are 1536×1024. All seven final person-mask IoUs meet 0.70. Visual review found a consistent PS2 treatment and no obvious source likeness, real logos or text in the generated assets. Exact composition still has the deviations below.

| Shot | IoU | Regenerations | Remaining layout/prop deviations |
|---|---:|---:|---|
| S1 | 0.724421 | 1 | Elbows and hair extend farther sideways than the mannequin; hair and fabric fill the mannequin waist gaps. Fries extend above their blockout box; packaging outlines and sauce position are approximate. |
| S2 | 0.762899 | 1 | Sweater torso is straighter and forearm thicker than the mannequin. Cup/carton/fries boundaries differ by several pixels; carton is open to expose food. |
| S3 | 0.838825 | 2 | Shoulders intentionally broadened to approach mannequin silhouette, so build is bulkier than neutral template. Rear wrapping becomes a kraft bag; carton lid and sauce placement remain approximate. |
| S4 | 0.796401 | 1 | Terminal is larger and rotated relative to the thin blockout slab. Staff arm/leg widths and background guest pose differ from mannequin. YOLO instance count is not a reliable physical-person count. |
| S5 | 0.706580 | 2 | Held carton lid extends above blockout footprint and hand is simplified. Forearm/torso outlines drift; IoU is only slightly above threshold. |
| S6 | 0.778841 | 1 | Head tilt and neck/shoulder proportions differ slightly. Table edge and foreground package height drift; window remains opaque blue-grey unlike detailed backgrounds in S1/S3. |
| S7 | 0.708546 | 1 | Legs are straighter and slimmer than mannequin; small head/arm outlines differ. Can is wider and starts slightly lower than blockout; small prop spacing differs. IoU is close to threshold. |

**Prompts:** exact character prompts in [mallar/README.md](mallar/README.md); every initial and revision prompt in [prompter/](prompter/), with ordered input references in [generation_manifest.json](generation_manifest.json). 20 image-generation calls total; no shot exceeded two regenerations.

**Paths:** `mallar/A.png`, `B.png`, `C.png`; `miljo.png`; `forsta_S1.png`–`forsta_S7.png`; [kontroll.json](kontroll.json); `kontroll_S1.jpg`–`kontroll_S7.jpg` (source | blockout | PS2); `masker/` contains both masks and overlap images.

**Verification:** Blender 5.2 Workbench renders the visible `bakade_aktorer` collection white, with set/prop occluders black, using each shot camera and first frame from `scen.blend`. YOLO `yolo11n-seg.pt`, person class 0, confidence 0.25, image size 1024, retina masks; union IoU, no alignment/dilation/manual correction. Model and image SHA-256 hashes, mask areas and raw detections are recorded. The mapped source frames are 0, 73, 114, 171, 256, 281 and 337, matching `kalla_s` at 30 fps.

**Remaining failures/limits:** exact silhouette/pose/prop geometry is not achieved; the table lists drift. S5/S7 pass narrowly. The environment frame interprets the empty S4 room; S6 glazing differs from S1/S3. Generic identity and absence of branding were checked visually, not biometrically. Raw YOLO detections can overlap or split a visible person. Source-reference files and source panels retain original people, logos and captions for comparison only.

**Reproduce checks from repo root:**
```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b scen/3d/blender/scen.blend --python scen/3d/blender/ps2/render_masks.py
scen/.venv/Scripts/python.exe scen/3d/blender/ps2/check_masks.py
scen/.venv/Scripts/python.exe scen/3d/blender/ps2/finalize.py
```
