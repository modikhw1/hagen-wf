# Codex task: furniture placed from the original's bounding box, against the solved camera (12 nov 2026, follow-up to CODEX-FOREMAL.md)

Same rules as `CODEX-FOREMAL.md`: Swedish, progress in `kontrakt/ut/foremal_logg/LOGG.md` (append a new section), **no long tests or compiles/renders** (the orchestrator runs them), fast tests only, never swap source files, no model jobs, no Blender, byte-identical behaviour for plans without the new data. Do not touch `ingest/rum_*.py` or `ingest/ut/*/brief/`.

## Why
Your Part B works: `kvalitet.foremal_lyft` moved the scale using the final render camera. But in `kontrakt/ut/b-tilltal-ravara_n06-foremal/narvaro/blad/s11.png` neither the counter nor the scale is visible, while in the original both fill the lower part of the frame. Cause: the counter `disk_C` is placed by a consensus rule (`framfor` the person, i.e. 0.4–0.9 m from the camera), so with the 53° vertical FOV it sits below the frame; the scale's ray hits the counter plane outside the counter and is clamped back onto the misplaced counter. The furniture position is a guess (`status: antagen`); the original should decide.

## Data
The declaration now gives furniture a box too: `platser.<id>.bild = {tagning, box_2d [ymin, xmin, ymax, xmax] 0-1000}`, e.g. in `ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`: `disk_C` → S9 `[550, 0, 1000, 1000]`, `disk_A` → S1 `[669, 0, 885, 638]`.

## Task
1. Carry `bild` of `bord` places through the same path as `foremal` (`hand.json.deklarerat` → `plats.json.deklarerat` → `plan.plats[].deklarerat`).
2. In `kontrakt/kompilera.py`, after the cameras are final and before your object lift, move each furniture piece that has `bild`, using the render camera of a frame in that shot:
   - If the box's bottom edge is inside the frame (`ymax` < 990): the ray through the bottom-centre meets the floor (z = floor) at the furniture's front-bottom edge; place the furniture so that its front face (the side facing the camera) lies there.
   - If the bottom is cut by the frame (`ymax` >= 990, as for `disk_C`): use the top edge (`ymin`) with the plane z = furniture's chosen height; that is the back edge of the top surface.
   - Move only along the camera's horizontal viewing direction (depth) and sideways to the box centre; keep size, height and yaw. Children with `:pa:` follow (reuse your Part A logic). Record before/after, which edge was used and why in `plan['kvalitet']['mobel_lyft']`; if anything is missing, leave it and record why.
   - Then run the existing object lift (objects now land on the moved furniture).
3. Unit tests with a synthetic camera: bottom-edge case, top-edge case, and a child following.

## Report (Swedish, max 15 lines)
What changed (file:line), tests, and the verify commands for the orchestrator (variant name `n06-mobel`).

---

# Follow-up (same session): clamp to the declared order camera – furniture – person

Verified on b-tilltal (`kontrakt/ut/b-tilltal-ravara_n06-mobel/`): `mobel_lyft` moved `disk_C` from y 0.73 to 1.70 and `disk_A` from 0.86 to 2.95, i.e. *behind* the persons (C at y 1.36, A/B at 1.37). A box without visible floor contact does not fix depth. The declaration does say the furniture stands in front of its person (`framfor: <person place>`; check that this reaches the plan, carry it like `bild` if not).
Fix in `kontrakt/mobellyft.py`: when the furniture has a `framfor` person place, clamp the lifted depth (along the shot camera's horizontal viewing direction) so that the back face is at least 0.10 m in front of that person place and the front face at least 0.30 m beyond the camera; record `klamd: true` and the bound used in `kvalitet.mobel_lyft`. Unit test for the clamp. Same limits as above (no long runs). Report in max 8 lines.
