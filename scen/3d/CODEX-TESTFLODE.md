# Codex task: two failures in test_flode.Plats (12 nov 2026)

Working directory `C:\Users\praiseworthy\Desktop\hagen-wf\scen\3d` (Windows, no git). Python 3.12: `C:\Users\praiseworthy\Desktop\hagen-wf\scen\.venv\Scripts\python.exe`. About 55 % of the five-hour quota is left; keep the task bounded and write progress to `kontrakt/ut/testflode_logg/LOGG.md` after each step so it can be resumed from disk. Report in Swedish.

## Situation
`kontrakt/test_flode.py` class `Plats` had not been run since seven pipeline steps were added on the night of 11–12 nov (see `NASTA.md` table, steps 1–7, and the baselines `kontrakt/ut/fore_*`, which hold code copies under `kod/`). Today additional changes were made (top of `NASTA.md`, "Dagen 12 nov"): `kontrakt/datacache.py` + `kontrakt/kvalitet.py` (planbeslut cache key now hashes all transitively imported modules), `ingest/plats.py` (declared montage branch, around line 373), `kontrakt/narvaro.py` (brief presence format), `ingest/scenbrief.py`. The whole class took 96 min; 9 of 11 tests pass. Two fail:

1. `test_bar_identitet_ger_samma_plan` (line ~365): `plan['renderkamera']` differs slightly from the reference (e.g. 0.052347 vs 0.052506).
2. `test_planen_har_ett_rum_och_ar_deterministisk` (line ~411): `bord_A.synlig_ut` is `[[0,73],[73,114],[114,171],[256,281],[281,337],[337,383]]` instead of `[[0,171],[256,383]]`: same coverage, adjacent intervals no longer merged.

Full output: `C:\Users\PRAISE~1\AppData\Local\Temp\claude\242ae36db01b5008\d040e4fd-62aa-4ac1-a52e-a2aa01a60f41\scratchpad\test_flode_plats2.log`.

## Task
1. For each failure, find the change that caused it: which night step (1–7) or which of today's changes, with file:line evidence. Use the `fore_*/kod/` copies to compare behaviour (import them from their own folder in a separate process; never copy them over the live files). Run single tests only (`python -m unittest test_flode.Plats.<name>`), not the whole class.
2. Decide per failure whether the new behaviour is a bug or an intended consequence:
   - a bug (e.g. intervals that should be merged): fix it in the code, generally, not just for this test;
   - intended (e.g. the bildkamera/trohet steps deliberately changed the render camera): update the test's reference or expectation, and write in the log exactly why, with the step that made the change.
3. Re-run the two tests, then `ingest/test_deklaration.py`, `ingest/test_rum.py`, `ingest/test_scenbrief.py`, `kontrakt/test_snabb.py`.

## Limits
Never swap or temporarily replace source files to run tests. No model jobs (Modal, SAM, MoGe, Gemini, API), no Blender. Do not touch `ingest/rum_video.py`, `ingest/rum_konsensus.py`, `ingest/rum_uppsattning.py`, `ingest/deklaration_till_hand.py` or anything under `ingest/ut/b-tilltal-ravara-tagningar/brief/` (being edited in parallel). Do not delete anything under `kontrakt/ut/`.

## Report (max 20 lines)
Cause of each failure (step, file:line), bug or intended, what you changed, test results.
