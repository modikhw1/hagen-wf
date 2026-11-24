# Codex task: fit furniture and objects to boxes from all shots (12 nov 2026, follow-up to CODEX-MOBELLYFT.md and CODEX-SKYMNING.md)

Same rules as before: Swedish, progress appended to `kontrakt/ut/foremal_logg/LOGG.md`, **no long tests or compiles/renders** (the orchestrator runs them), fast tests only, never swap source files, no model jobs, no Blender, byte-identical for plans without the new data. Do not touch `ingest/rum_*.py` or `ingest/ut/*/brief/`.

## Why
After the skymning fix the counter and the scale are kept and rendered, but in `kontrakt/ut/b-tilltal-ravara_n06-skymning/narvaro/blad/s11.png` the scale is a large block in the middle of the frame right in front of the camera, while in the original it stands at the lower left. The counter was lifted from a single shot (S9) and clamped (`granskonflikt` true); a position that fits S9 lands in front of the camera in S11, because the solved cameras of different set-ups differ.

## New data
Boxes per shot now come from image detection on each shot's key frame (`ingest/rum_detektera.py`, median of 3 runs, only shots where the element is expected): `platser.<bord>.bilder` and `foremal.<id>.bilder`, each a list of `{tagning, box_2d [ymin,xmin,ymax,xmax] 0-1000}`; `bild` is kept as the largest one. File: `ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning3/deklaration_n06_detekterad.json`. Example: `disk_C` has boxes in S6, S7, S8, S9, S11; `vag` in S8–S11; `kottbit` in ten shots; `disk_A` none.

## Task
1. Carry `bilder` the same way as `bild` (hand.json → plats.json → plan).
2. In `kontrakt/mobellyft.py`, fit each furniture piece to all its boxes at once: unknowns are the horizontal position (x, y) with size, height and yaw fixed; for every shot use a frame of that shot and its final render camera; residual per shot = the pixel distance between the box edges that are inside the frame (left/right always when not cut by the frame edge, bottom only when `ymax` < 990, top edge against the top plane) and the projected box of the furniture. Robust least squares (e.g. soft-L1 / Huber) so one bad box does not dominate. Keep the clamp to camera–furniture–person, applied for every shot's camera. Record per shot residuals before/after, which edges were used, and the final position in `kvalitet.mobel_lyft`.
3. Same for objects on furniture in the object lift: fit (x, y) on the support's top plane to all the object's boxes, clamped to the support top.
4. Fall back to the single-box behaviour when only one box exists, and leave things untouched with a recorded reason when none exists.
5. Unit tests with two synthetic cameras that disagree with a single-box solution but agree on the fitted one; a test where one outlier box is down-weighted.

## Report (Swedish, max 12 lines)
What changed (file:line), tests, the per-shot residuals you can compute without a full compile (if any), and the verify commands (variant `n06-fler`, `--deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning3/deklaration_n06_detekterad.json`).

---

# Follow-up (same session), verified by the orchestrator on b-tilltal `n06-fler`
`kvalitet.mobel_lyft` for `disk_C` and `foremal_lyft` for `disk_C:pa:vag`: status `bevarad`, orsak "lådan ligger i eller bakom kameran"; the whole fit was abandoned, the counter stayed at the fallback, and skymning dropped it in s11. `kottbit` was not built: its `pa` is "inslagspapper", which is not an element (broken support chain).
1. A shot where the furniture/object (at the start position or during the fit) lies in or behind that shot's camera must be excluded from the residual for that iteration (or given a large bounded penalty), not abort the whole fit. Choose the start position so it is in front of all the shots' cameras (e.g. from the shot with the most reliable box, clamped to camera–furniture–person). Record per shot whether it was used.
2. When an object's support id does not exist, put it on the nearest existing support in the chain (the furniture it ultimately stands on, or the furniture of its `ankare`/declared place) and record the substitution.
3. Unit tests for both. Same limits (no long runs). Report in max 8 lines.
