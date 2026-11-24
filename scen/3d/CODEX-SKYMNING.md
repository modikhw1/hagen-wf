# Codex task: the occlusion check drops furniture the original shows (12 nov 2026)

Same rules as `CODEX-FOREMAL.md`: Swedish, progress in `kontrakt/ut/skymning_logg/LOGG.md`, **no long tests or compiles/renders** (the orchestrator runs `klipp_kor.py` and `test_flode.Plats`), fast tests only, never swap source files, no model jobs, no Blender. Do not touch `ingest/rum_*.py` or `ingest/ut/*/brief/`.

## Situation
Read first: `PIPE.md` "Öppet" item 6, the "Föremål i kompileringen" and "Hinder" bullets; `kontrakt/ut/foremal_logg/LOGG.md`; and the warning in `NASTA.md` (11–12 nov) that an old `skymning.py` once poisoned three runs. The correct skymning baseline is `kontrakt/ut/fore_vaggar/omkord_ratt_skymning/`.

In `kontrakt/ut/b-tilltal-ravara_n06-mobel2/narvaro/plan.json` the counters are placed where the original shows them (`kvalitet.mobel_lyft`, clamped to camera–counter–person). Projected through the render camera at s11 frame 439, the counter top's back edge is at y 864/1024 and the scale on it is in frame, as in the original. But `kvalitet.skymning.atgarder` drops `disk_A` (s1–s4) and `disk_C` (s5–s11) in every scene ("Minst 2 % av synliga maskprov skyms..."), and the objects on them go with them. In the original the counter does hide the lower body; the visible hands and the meat are above the counter top.

## Task
1. Find exactly why the samples count as occluded: which mask samples (body part, pixel rows), which depth they get (nearest MHR70 keypoint?), and why a box whose top is below the hands is judged to be in front of them. File:line evidence, with numbers for s11 frame 439.
2. Fix the measure so that occlusion is decided in 3D: a sample is occluded only if the ray from the camera through that pixel hits the furniture box before it reaches the body point that explains the sample (use the body point's real 3D position, not only its depth). Keep the per-part limits and the 2 % rule as they are; only the occlusion test changes.
3. Furniture whose position is confirmed by the original's box (`kvalitet.mobel_lyft` status `flyttad`) must not be dropped silently: if it still occludes after the fix, adjust it within its declared interval as `mobelintervall` does, and only record a conflict (`granskonflikt`) if no allowed value works.
4. Byte-identical results for notan, guacamole and bar unless the old measure was wrong for them too; if their skymning results change, list exactly which actions change and why (do not run their full compiles yourself; give the orchestrator the commands).
5. Unit tests with a synthetic camera, body point and box: hand above a counter top is not occluded; hip behind the counter front is occluded.

## Report (Swedish, max 15 lines)
Cause with numbers, what changed (file:line), tests, the commands the orchestrator should run (b-tilltal variant `n06-skymning` with `--deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`, plus notan/guacamole checks), and what is left.
