# Orchestrator review of Phase 1 → do Phase 1b before Phase 2

Good work. The body measurement holds: projected skeletons sit on the people in all 21 overlays. The room geometry does not hold yet, for three reasons. Fix them as **Phase 1b**, using the same files with new versions `*-1b.*`, and keep the old ones for comparison.

## 1. Field of view is not identifiable from the pose, so don't let it float per shot

I re-ran solvePnP on `data/ra` `varld`/`lm`, visible joints only, median over each shot. The error curve against vertical FOV is nearly flat while the distance scales ~1/tan:

| vFOV | 30° | 40° | 50° | 60° | 70° | 80° | 90° |
|---|---|---|---|---|---|---|---|
| S1 err×H / dist | .0125/2.9m | .0128/2.2m | .0137/1.8m | .0160/1.5m | .0172/1.3m | .0185/1.1m | .0216/1.0m |
| S2 | .0124/2.5m | .0133/1.9m | .0150/1.5m | .0167/1.3m | .0208/1.1m | .0232/1.0m | .0285/0.9m |
| S4 | .0126/3.0m | .0132/2.3m | .0138/1.8m | .0145/1.5m | .0145/1.3m | .0147/1.1m | .0157/1.0m |
| S7 | .0050/5.8m | .0049/4.4m | .0050/3.5m | .0055/2.8m | .0057/2.4m | .0064/2.0m | .0069/1.7m |

MediaPipe world-landmark depth is compressed, so lower FOV always "wins" by a hair. Your per-shot choices (73°, 62°, 57°, 40°, 44°, 57°, 40°) are fitting noise:
- S1, S3 and S6 are the same setup but got 73°, 57° and 57°.
- S4 and S7 sit on the 40° bound.

A naive vanishing-point estimate (LSD + RANSAC) was also inconsistent (21–57°), so don't rely on that either.

**Do this:** one shared intrinsic for the whole clip (same phone). Use a prior of iPhone 1× main camera, 9:16 portrait video, vertical FOV ≈ 65–70°. You may optimize the shared value within 58–75° jointly with the scene constraints below. Report how the A–B distance and the camera heights change across that range.

## 2. Shots that share a setup should share a camera

S1, S3 and S6 are the same framing of A, and S2 and S5 are the same framing of B. Solve one camera per setup, jointly over all frames of its shots, unless the data clearly shows the camera moved. In that case report how much it moved.

## 3. Table size is wrong, so make it a measured parameter

In S7 the near (front) edge of B's table spans ≈ 342 px, from x≈155 to 497 at y≈553 (your `S7-layout-overlay.jpg` cyan line). B's shoulder landmark distance in S7 is ≈ 105 px (median of 15 frames). The table edge is ~0.5 m nearer than B's shoulders. That makes the table ≈ 1.0–1.1 m wide for any plausible distance, not 0.70 m.

A's table in S1/S3/S6 also looks like a wide black table. **Estimate table width and depth** from visible edges (S1/S3/S6: front edge of A's table; S2/S5: B's table edge; S7: B's table front edge and the foreground table). Use `cv2.HoughLinesP`/LSD restricted to the table region, or the YOLO/EfficientDet "dining table" boxes. Then make table dims per-table parameters in `layout.json`.

## 4. The waiter shot S4 sits on the bounds (0.90 m height, 40° FOV)

Re-solve S4 with the shared FOV. Place C consistently with what is visible behind him: seated guests and tables. Report his distance from A's and B's tables, and flag what is assumed.

## Acceptance for 1b

- Shared FOV, with the justification and the sensitivity table.
- Per-setup cameras.
- Median joint error ≤ 0.04×H for S1–S6, and report the change from Phase 1.
- S7: B's table front edge reprojects within ≈15 px of the observed edge, and the foreground can is consistent.
- Camera heights 0.9–1.7 m and not on bounds, or explain.

**Outputs:**
- `data/layout-1b.json`, which becomes the layout Phase 2 uses. Also update `layout.json` to point to or equal it.
- `verifiering/fas1b.jpg`, `verifiering/plan-1b.png` and `verifiering/S7-layout-overlay-1b.jpg`.
- Append to `LOGG.md`.

Then stop and report. Do not start Phase 2.
