# Codex task: objects on furniture, placed against the solved camera (12 nov 2026)

Working directory `C:\Users\praiseworthy\Desktop\hagen-wf\scen\3d` (Windows, no git). Python 3.12: `C:\Users\praiseworthy\Desktop\hagen-wf\scen\.venv\Scripts\python.exe`. Code, comments and report in Swedish, matching existing style. Write progress to `kontrakt/ut/foremal_logg/LOGG.md` after each part so the work can be resumed from disk.

**Do not run long tests.** Never run `test_flode.Plats` or any compile/render that takes more than a few minutes; do not wait on long processes (waiting burns quota). The orchestrator runs the chain and renders afterwards. Fast tests only: `ingest/test_deklaration.py`, `ingest/test_rum.py`, `ingest/test_scenbrief.py`, `kontrakt/test_snabb.py`, plus new unit tests you write. Never swap or temporarily replace source files. No model jobs, no Blender.

## Background (read `PIPE.md` "Öppet" item 6, the sub-bullets on "Uppsättning och nivå" and "Bildrutor provade")
A video model now judges which elements of a clip matter (`ingest/rum_uppsattning.py`, ladder 0–1). Objects up to the chosen level go into the declaration as `foremal`: `{id: {kategori, pa: <furniture place id> | halls_av: <role>, storlek_m: [[lo,hi]x3], bild: {tagning, box_2d [ymin,xmin,ymax,xmax] 0-1000}, ...}}`. Example: `ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json` (the scale `vag` on `disk_C`).
Today `ingest/deklaration_till_hand.py` builds an object on furniture as a massive box in the room template with id `<furniture>:pa:<object>` (see `rumsmall()` and `lyft_bildruta()`), placed by lifting the bounding box against the *declared* camera. Two problems, visible in `kontrakt/ut/b-tilltal-ravara_n06b/narvaro/blad/s10.png`:
1. `kontrakt/mobelintervall.py` chooses the furniture's height/centre within its declared interval, but the `:pa:` object does not follow, so the scale floats ~7 cm above the counter (template height 0.895, chosen 0.82–0.9).
2. The lift uses the declared camera, while the render uses the camera solved later (`kontrakt/bildkamera.py`, `plan['renderkamera']`), so the scale lands out of frame in S10, where in the original it is large in the foreground.

## Task
**Part A.** In `kontrakt/mobelintervall.py`, objects in a furniture group whose id contains `:pa:` must follow the furniture: z moves by (chosen top height − template top height); x/y move with the chosen centre shift. Keep the size. Add a unit test in `kontrakt/test_snabb.py` (synthetic plan; no compile).

**Part B.** Place objects that have a `bild` against the solved camera, after the cameras are final in `kontrakt/kompilera.py` (after `bildkamera.los`, `mobelintervall` and `vaggar`). Carry the needed data through the chain without breaking strict schemas (the room template schema rejects unknown fields; find a legal path, e.g. via `hand.json`/`plats.json` `deklarerat`, or a separate field the compiler already passes through, and say which you chose). For each such object: take the render camera for a frame inside the object's shot (the shot's `ut` range in the plan), cast the ray through the bottom-centre of `box_2d`, intersect with the supporting furniture's top plane (its chosen height), clamp to the furniture top, and move the object there; record before/after and the method in `plan['kvalitet']` (e.g. `foremal_lyft`). If anything is missing, leave the object where it is and record why. Unit test with a synthetic camera and box.

**Part C (only if quota allows).** An object on another object (`pa` = an object id, e.g. meat on the scale) is built on top of that object, following it. Objects held by a role (`halls_av`) are out of scope: list in the log what would be needed (hand joint per frame in the plan, attachment in `ingest/mhr_rig.py`).

## Limits
Keep behaviour byte-identical for every plan without `foremal` (notan, guacamole, bar). Do not touch `ingest/rum_video.py`, `ingest/rum_konsensus.py`, `ingest/rum_uppsattning.py`, `ingest/rum_fokus.py`, `ingest/rum_jamfor.py` or anything under `ingest/ut/*/brief/`. Do not delete anything under `kontrakt/ut/`.

## Report (Swedish, max 20 lines)
What changed (file:line), the data path chosen for Part B, tests run and results, what the orchestrator should run to verify on b-tilltal (`klipp_kor.py b-tilltal-ravara prepare|render --variant <name> --deklaration <file>`), and what is left.
