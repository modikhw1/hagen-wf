# Codex task: first new clip through the declared chain fails (b-tilltal-ravara, 12 nov 2026)

Phase 1 is READ-ONLY diagnosis: a long test (`kontrakt/test_flode.Plats`) is running against this code, so do not edit, create or delete any file and do not write to `kontrakt/ut/cache`. You may run Python that only reads (import modules, load npz/json, call pure functions). Report in Swedish as your final message. Phase 2 (the fix) will be sent later in the same session.

Working directory: `C:\Users\praiseworthy\Desktop\hagen-wf\scen\3d` (Windows, no git). Python 3.12: `C:\Users\praiseworthy\Desktop\hagen-wf\scen\.venv\Scripts\python.exe`.

## Context
- Read `PIPE.md` (steps, "Deklarationen som allmän mekanism") and `NASTA.md`.
- The clip `b-tilltal-ravara` (11 shots, one person per shot, montage in one butcher's shop) is the first clip that got a declaration through the scene-brief step instead of by hand: `ingest/ut/b-tilltal-ravara-tagningar/plats/deklaration.json` (version 0.3). It places all cameras in one shared frame: A and B (S1–S4, roles A and B on the same standing place at (0, 1.159)), and a counter corner about 3 m away (S5–S11, role C at (3.0, 1.641) and (3.185, 1.465)). Camera positions are in `platser.kamera_*` with `pos_m`; cameras reference them through `kameror.<S>.kamera_vid`.
- Chain: `klipp_kor.py b-tilltal-ravara prepare` (handsyn, deklaration_till_hand, plats, kalla_bygg, kor_klipp, narvaro). Logs and outputs in `kontrakt/ut/b-tilltal-ravara/`. `plats` and `kalla` pass; compilation fails.

## Failure
`kompilera` → `bildkamera.los` → `_observationer` → `trohet.ruta` → `trostod.begransa`: `AssertionError: ('Sula under golvet', -1.29, 0.0)` in scene s3, role B, frame 21. The body translation T there is about [-0.08, 1.36, -1.34]: the whole body sits about 1.3 m below the floor, while the pelvis is protected so the sole pass cannot lift it.

Observations so far:
- `ingest/ut/b-tilltal-ravara-tagningar/plats_berattat/plats.md`: every shot S1–S11 is registered with method `identitet`, scale 1.0. The anchors come out at staplats_A (0.00, 1.17), staplats_B (0.05, 1.43), staplats_C (0.11, 1.72), so the declared camera positions (B at (0, -0.253), the counter corner at x ≈ 3) are not applied and every shot sits in its own camera-at-origin frame.
- `hand.json` has kamerahojd_m 1.3 and person_pos_m per shot as declared. `S*/sekvens_1.npz` cam_t has y ≈ 1.26–1.48 in all shots (camera frame), and golv_skala is 1.04 in S3 and 1.09 in S4.
- Two undocumented conventions had to be found by hand before this point: role ids must be A/B/C in order of appearance (plats.py names roles itself), and a role's home place must be named `staplats_<roll>`/`stol_<roll>` so that `rumsmall.passa` can match anchors. Note them in your report if they matter for the fix.

## Questions
1. Why is every shot registered as `identitet`, and why are the declared camera positions/person positions not used to place shots in the shared frame? Which branch in `ingest/plats.py` decides this, and what would the declared notan/guacamole runs have done differently (they have dialogue pairs; this clip has one person per shot)?
2. Why does S3/B end up 1.3 m below the floor while S1/S2 (same camera height 1.3) apparently do not? Trace the z of T for S1 and S3 through the chain (ingest golv, plats transform, kalla, compiler's floor). Find the first place the two diverge.
3. Is the assert in `trostod.begransa` the right failure here, or should an earlier step reject or correct this?
4. Propose the minimal general fix (it must hold for all clips, including montage clips with one person per shot and clips with dialogue pairs, and leave the notan/guacamole outputs byte-for-byte unchanged). Give the patch as a diff in your report; do not apply it.

Max 35 lines: answers 1–4 with file:line evidence, the proposed diff, and what phase 2 should verify.

---

# Phase 2: apply the fix (sent 12 nov after phase 1)

`test_flode.Plats` is no longer running; you may now edit code. Write progress to `kontrakt/ut/b-tilltal-ravara/CODEX-LOGG.md` after each step so the work can be resumed from disk. Never swap or temporarily replace source files to run tests. No model jobs (Modal, SAM, MoGe, Gemini, API). Blender only in step 4.

Already changed by the orchestrator today (do not revert): `kontrakt/datacache.py` (`lokala_moduler`), `kontrakt/kvalitet.py` (planbeslut key now hashes all transitively imported local modules), `kontrakt/test_snabb.py`. `ingest/scenbrief.py` is being edited in parallel by the orchestrator; do not touch it.

1. Apply your phase-1 diff (declared montage branch in `ingest/plats.py`), adjusted as needed. It must leave the dialogue branch and every existing declared clip unchanged.
2. Verify on b-tilltal: `M.z = 1.30` per shot, S3 `T.z ≈ 0`, cameras near declared positions, low anchor residual. The prior outputs in `kontrakt/ut/b-tilltal-ravara/` came from the broken run: move `kalla.json`, `kalla.textmatning.json`, `tom/` and the `*.log` files into `kontrakt/ut/b-tilltal-ravara/fore_montage/` (do not delete), then run `scen/.venv/Scripts/python.exe scen/3d/klipp_kor.py b-tilltal-ravara prepare` from the repo root `C:\Users\praiseworthy\Desktop\hagen-wf`. Fix further failures in the same general way (montage clips, one person per shot) and log each one.
3. Byte-for-byte check that notan and guacamole are unchanged: re-run `ingest/plats.py` for both declared clips into a scratch output folder (`--ut` to a new folder under `kontrakt/ut/kontroll_montage/`) and compare `plats.json` with the existing `ingest/ut/notan-tagningar/plats_berattat/plats.json` and the guacamole equivalent. Then run `ingest/test_deklaration.py`, `ingest/test_rum.py`, `ingest/test_scenbrief.py`, `kontrakt/test_snabb.py`.
4. If 2 and 3 are clean: `scen/.venv/Scripts/python.exe scen/3d/klipp_kor.py b-tilltal-ravara render` (Blender, film, comparison sheets). Leave `test_flode.Plats` to the orchestrator.

Final report in Swedish, max 25 lines: what changed (file:line), per-step result, the b-tilltal numbers (M.z, T.z, camera positions vs declared, anchor residual), byte comparison, tests, the absolute path to the film/comparison, and anything unsolved.
