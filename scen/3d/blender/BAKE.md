# Frame-exact X Bot bake

From the repository root:

```powershell
node scen/3d/blender/baka.mjs
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b --python scen/3d/blender/verifiera_bake.py
```

The first command starts its own local HTTP server and headless Chrome, evaluates
the existing player at every `i/30` in `#ljud=original`, writes the bake and player
reference images, and checks that removing the read-only export hook leaves 42
reference images pixel-identical. Geometry is transferred in chunks to avoid
Chrome DevTools' large-response failure. No npm dependencies are needed.

The second command imports and keys all four actors, saves `bake.blend`, checks
every frame, renders three mask frames per shot using Blender Workbench, and
writes `verifiering-bake.json` plus `verifiering/S1-comparison.png` through
`S7-comparison.png`. It exits nonzero on failure. It uses the existing
`scen/.venv/Scripts/python.exe` for OpenCV image comparison and `ffprobe` for the
source audio duration. If there is no bake yet, it runs the first command itself;
if source fingerprints changed, it fails with a request to rebake.

## Integration contract

```python
from importera_bake import importera
actors = importera(bake_path, scen_path)
```

This adds only the actor collection, meshes, rigs, face parts, materials and
animation. It preserves the scene builder's room, props, cameras and audio.
Each `actors[id]` exposes `root`, `armature`, `bones`, `face`, `parts`, `meshes`,
`objects` and the per-bone `corrections`. Objects are named `actor:A`,
`actor:A:rig`, `actor:A:mouth`, `actor:A:eyeL`, etc.; similarly B, C and guest.
Shirt colours come from `scen3d.json`'s `look.shirt`, including a Workbench
material palette. The guest uses the player's guest shirt specification.

**Frame 0 is scene time 0.** There are 383 frames (0–382) at 30 fps, matching
`bygg_scen.py`. Every root/bone/face channel and object visibility is keyed at
every frame with constant interpolation. Inactive actors hold a pose while
hidden. Import into a scene without existing `actor:*` roots; duplicates fail
explicitly. Standalone import can also save another file:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b --factory-startup --python scen/3d/blender/importera_bake.py -- --output scen/3d/blender/bake.blend
```

## Data

- `bake.json`: schema `scen3d-bake/1`, fps, N, duration, input hashes, shot
  boundaries and independent player `shotAt` probes, reference-image regression,
  then `frames[i]`. Each frame contains scene/source/audio time, shot, actor
  visibility, root world transform, all 67 bones' local TRS **and evaluated world
  matrices**, the head-relative face group and each ellipsoid's local TRS,
  `jointsWorld`, `mouthOpen`, projected `joints`, all prop world transforms and
  visibility, and camera world transform, vertical fov and clipping planes.
- `bake-assets.json`: the player's actual modified skin geometry, clothing
  volume, hair, skin weights, inverse bind matrices, face sphere geometry and
  colours. Also contains static black occluder geometry used only by verification.
- Coordinates in both JSON files are three.js Y-up metres. Quaternions are
  `[x,y,z,w]`; matrices are column-major. Blender converts `(x,y,z)` to `(x,-z,y)`.
  The importer uses `C_b = (conv * M_gl_bind)^-1 * M_bl_rest` and applies
  `conv * M_gl_pose * C_b` in the appropriate root/armature space. This retains
  Blender's imported bone axes while preserving the player's proportion edits.
- `frames[i].props[id]` includes hand-attached prop movement. The scene builder
  can key existing semantic prop objects from these values without rerunning IK.
  `frames[i].camera` similarly provides the exact evaluated camera.

## What acceptance means

Joint and face comparisons use Blender's evaluated dependency graph after
`scene.frame_set(i)`, rather than the values just assigned during import. All
frames, including both sides of every cut, are checked. Shoulders, elbows,
wrists, hips and head must be within 5 mm; every bone head and projected main
joints are also measured. Mouth local scales, aperture, `mouthOpen`, all face
world transforms, and viewport/render visibility are checked separately.

At first+2, middle and last−2 frames of each shot, native 576×1024 Workbench
renders are compared to the original player's `#mode=mask` output, thresholded
at 127. Every sampled IoU must be at least 0.9. That player mode renders the main
actor white and everything else black with depth testing, so verification adds
exact black set/prop occluders temporarily. These are excluded from `importera`
and from the saved actor-only `bake.blend`. Comparison sheets show player,
Blender and overlap (orange = player only, blue = Blender only).

This proves transfer fidelity to the player. It does not establish accuracy of
the original MediaPipe estimates, assumed proportions or background guest.
The current source M4A ends 20.658 ms before the mapped scene end, after the last
sampled frame. No timing is changed. Current audio mappings match
`mvp_render.py --original` exactly; future nonlinear `source.knots` that disagree
with that script's linear mux are reported as failures.
