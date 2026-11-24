# Codex-uppdrag: bildtrohet i slutplanen (11 nov 2026, natt)

Working directory: `scen/3d` in `C:\Users\praiseworthy\Desktop\hagen-wf` (Windows, no git). Python 3.12 venv in `scen/.venv`. Write code, comments, logs and the report in Swedish, matching existing style.

## Read first
- `PIPE.md` (all of it)
- `GUACAMOLE-LOGG.md`: "Problem som det nya klippet blottlägger" and the last four sections (bindande deklaration, flerrollsregistrering, möbelintervall, väggar), all from today.

## State
The pipeline builds a 3D pre-world per clip. The room is declared in `ingest/ut/<klipp>/plats/deklaration.json`; `ingest/plats.py` registers each shot on the declared places; `kontrakt/` compiles `plan.json`; Blender renders. Today the declaration became binding (floor, seat height, camera height), multi-role shots register against all visible roles, furniture has declared intervals, and generated walls no longer block cameras.

Latest guacamole result: `kontrakt/ut/e-dialog-guacamole/vaggar_narvaro/` (`plan.json`, `film_utan_text.mp4`, `jamforelse.mp4`, `stillbilder/`). Correct baseline plans: `kontrakt/ut/fore_vaggar/omkord_ratt_skymning/`.

## The problem (visible in `stillbilder/jamforelse_f0120.png` and `_f0230.png`)
Poses and timing are recognisable, but the framing does not match the original:
- s2: B sits far right and is cropped by the frame edge; in the original he is centre-right with his whole upper body in frame.
- s4: B is much larger/closer than in the original and A sits lower in frame; their relative placement is only roughly right.
- The bar counter is a thin slab on four legs; in the original it is a solid counter.

Nothing in the plan diagnostics measures this. Existing body measures compare the body's projection against the mask in the ingest camera, not the final render camera in the declared room.

## Task
General solution, not guacamole-specific. Work in this order and stop after each part with numbers written to the log, so the work can be resumed from disk.

**Part 1: measure.** Add a plan diagnostic `plan.kvalitet.bildtrohet`: per scene and visible role, project the role's joints through the FINAL plan camera (the one Blender renders with) and compare with the original 2D reading for the same frames (the ingest keypoints / person mask already cached). Report per scene and role: mean 2D offset (px and % of frame height), scale ratio (projected body height / original), and bounding-box IoU. Warn above a threshold you propose and justify. Run it on the current guacamole and notan (bindande väg) plans and record the numbers before changing anything.

**Part 2: find where framing is lost.** Trace why the final camera differs from the original framing: declared camera height and position, yaw from role positions, pitch/roll, field of view, per-shot depth scale. Report which of these carries the error in s2 and s4.

**Part 3: fix within the declaration's rules.** The declared floor, places, seat heights and camera height stay binding. The remaining camera freedom (yaw, pitch, roll, focal length, and camera xy where the declaration gives none or gives an interval) should be solved so the roles land where they are in the original frame. Do not move bodies individually to hide a residual. If the declaration itself is what prevents a match (as with the A–B distance today), do not edit it: report what the reading says, as input for the owner.

**Part 4 (only if quota allows): solid counter.** Let the declaration mark a piece of furniture as solid (`massiv: true` or similar); build it as a box down to the floor in the room template and in Blender. Guacamole's counter gets it; notan's table does not.

## Verification (mandatory)
- Before changing code: copy the touched files and current plans to `kontrakt/ut/fore_bildtro/`.
- Guacamole: bildtrohet per scene and role before/after. New subfolders, existing measurement cache, never overwrite results.
- Notan (bindande väg): every difference against the baseline listed as expected or regression. Old path (`kalla_jamn_golv.json`) and clips without a declaration: 0 differences.
- Tests: `ingest/test_deklaration.py`, `ingest/test_rum.py`, `kontrakt/test_rumsmall.py`, `test_steg11`, `test_regler`, `test_kroppmatt`, `test_props`, `test_handelser`, `test_text_disk`, `test_snabb`, `test_flode` except the `Plats` class (takes over 50 minutes, do not run it). Add tests for the new code.
- Finish by rendering guacamole (walls on, no text layer) with the side-by-side comparison and stills for f0030, f0100, f0120, f0230, in a new folder. Look at the stills and judge them honestly.
- `ut/cache/planbeslut` gave stale decisions earlier today although it is keyed on code content. If you see cached decisions that do not match a fresh-cache compile, find the cause and report it; compile the verification runs with a fresh cache folder.

## Limits
- No model jobs (Modal, SAM, MoGe, Gemini). If a cache is invalid, stop and report. Blender locally is fine.
- Never swap or temporarily replace source files to run tests (that corrupted three runs today). Do not touch `kontrakt/skymning.py` thresholds or other quality thresholds.
- Do not touch `kontrakt/ut/fore_*` archives other than your own, nor `app/` or `video/`.
- Leave the text layer (problem 5) alone.
- Leave no background processes running.

## Output
- Update `PIPE.md` briefly and append a section to `GUACAMOLE-LOGG.md`.
- Write progress after each part to `BILDTRO-LOGG.md` (what is done, numbers, what remains), so a new session can continue.
- Final report (Swedish, max ~40 lines): where framing was lost (file:line), changed files one line each, before/after table per scene and role, notan and old-path differences, test results, absolute paths to film, comparison and stills with your judgement per still, and what is unsolved.
