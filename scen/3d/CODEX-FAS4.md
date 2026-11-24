# Phase 4: neutral plug-and-play avatars + motion stabilization (no flapping arms)

Context: read `scen/3d/README.md` and `scen/3d/LOGG.md` first (Phases 1–3 are done; Phase 3 was finished by Claude). The owner's verdict on the current state: "moving in the right direction". The procedural rounded characters have **arms that flap around**, and the owner wants **neutral, simple, more plug-and-play models**, explicitly NOT the anime VRoid avatar.

Product rules from the hagen-ui wiki (binding):
- **No synthetic likeness of the source creators.** Characters must be neutral, role-labeled (e.g. "Ägaren", "Kassören"), not lookalikes. Today's procedural characters copy hair and clothes of the real people; the new default must not.
- **No lip-sync of the original creator; designed voices instead.** The mouth must be drivable by an arbitrary per-frame `jawOpen` curve. Claude will produce those curves from designed voices. Keep MediaPipe blendshapes only as a fallback.
- **No photorealism. Live composition, not rendered video.**

## Ownership while you work
- You own `player.js`, `meshes.js`, any new avatar or stabilization files, `verifiera.py`/`capture.mjs` changes, and new data files under `data/` that you create.
- Claude is working at the same time on `op.py`, dialogue word timing, camera motion and voices, and stores results in separate data files that are merged later.
- **Do not regenerate or restructure `scen3d.json`.** You may add fields, such as `actor.avatar` and `actor.look`, through a small migration function that is idempotent. Never run `fas2.py`, because it would overwrite the calibrated scene.

## Part A: motion stabilization (do this first, measure before/after)
Arms flap because the procedural limbs connect MediaPipe **world** landmarks, whose depth is noisy. Build `data/motion-3.json` with stabilized joints:
1. **2D-anchored.** Each joint lies on the ray from the shot's **source camera** (`shot.source.camera` in `scen3d.json`) through its MediaPipe **image** landmark, so the reprojection in the source view is exact for visible joints.
2. **Constant bone lengths per actor**: median of metric world-landmark lengths, with left/right symmetry. Choose depth along the ray to satisfy the bone length from the parent joint. Of the two solutions, pick the one closest to MediaPipe's relative z with temporal continuity.
3. **Temporal smoothing**: One-Euro filter, or Savitzky–Golay with confidence weights. Tune it so gestures stay readable and do not get mushy.
4. **Low visibility** (occluded hands under or behind the table, legs): hold the last good value, blend to a rest pose, and never invent gestures.
5. **Metrics**, computed for the old and new tracks:
   - temporal jitter: median and p90 of |2nd difference| of elbow/wrist positions in 3D (m/frame²) and in 2D (px/frame²),
   - reprojection median px,
   - a short "flap index" = share of frames where an elbow moves > 8 cm between consecutive frames.

   Target: flap index down by at least 70% with reprojection ≤ the Phase 2 values.

## Part B: neutral plug-and-play avatars (A/B test, pick a default)
Candidates, all must run offline from `vendor/`/`modeller/`:
1. **Mixamo mannequins from the three.js examples (r170)**: `Xbot.glb` (and `Michelle.glb` if a second body type is useful), from `https://raw.githubusercontent.com/mrdoob/three.js/r170/examples/models/gltf/`. These are skinned, standard humanoid rigs, neutral, with no face. Note the license as it stands: Mixamo terms allow use in projects but not redistribution as standalone assets. Record that in `modeller/licenses.json`.
2. **A CC0 option, if you can fetch one without a login**, for example Kenney's modular characters (kenney.nl, CC0). Skip it if a login or payment is required, and say so.
3. **Baseline**: the current procedural characters.

Retarget the stabilized joints to the skinned rig, using direction-based bone alignment or `kalidokit` (MIT, npm) if it helps.
- Calibrate the rest/bind pose properly. A T-pose versus A-pose mismatch is the classic failure.
- Use joint limits or a soft constraint for elbows and knees.
- Seated actors: stable seated legs.
- Hands: if the rig has finger bones, drive them from hand landmarks when visible; otherwise use a relaxed hand.
- Head: drive from the face orientation relative to the source camera (as today).
- **Face for the faceless rigs.** Add a minimal neutral face parented to the head bone: eyes, brows and a mouth whose opening follows a per-frame `jawOpen`. Expose a hook so the player can feed `jawOpen` from either MediaPipe or an external curve:
  ```
  actor.voice = { mouthTrack: "data/mun-<id>.json" }   // { fps, values: [...] }
  ```
- **Role styling instead of likeness**: neutral skin tone and a role color/accent (apron or shirt tint) per actor. A floating role label can be toggled in the UI (casting: "A → Ägaren").

## Part C: verify and choose
- Run the existing verifier for each variant (joint error, silhouette IoU, S1–S6 acceptance), plus your Part A jitter and flap metrics on the rendered joints.
- Contact sheets: source | procedural | Xbot (| CC0 option), for 3 frames per shot, and a short strip of 10 consecutive frames in S1 and S3 (A gesturing) to show the flapping before and after.
- Make the winner the default (`defaultAvatar`), and keep the others selectable in the player dropdown.
- Append the decisions and numbers to `LOGG.md`, and write `verifiering/fas4/` images.

## Acceptance
- Flap index reduced ≥ 70%.
- Median joint error ≤ 0.04 H in S1–S6.
- Silhouette IoU ≥ 0.5 in S1–S6.
- The default avatar is neutral (no likeness), skinned, and readable.
- The mouth is drivable by an external curve.
- Zero page errors over a full-timeline sweep.

Report honestly where it fails.
