# Codex-uppdrag: textlagret i S4 (12 nov 2026)

Small, narrow task. About 20 % of the five-hour quota is left: keep exploration short, write progress to `TEXT-LOGG.md` after each step so a new session can continue from disk, and stop cleanly rather than leave half-edited files.

Working directory: `scen/3d` in `C:\Users\praiseworthy\Desktop\hagen-wf` (Windows, no git). Python 3.12 venv in `scen/.venv`. Code, comments, log and report in Swedish, matching existing style.

## Read first
- `GUACAMOLE-LOGG.md`: the paragraph starting "**Ytterligare visuell brist:**" and the last section.
- The text modules in `kontrakt/`: `skarmtext.py`, `textenheter.py`, `textmalning.py`, `textarbete.py` (only as far as needed).

## The problem (problem 5)
In the guacamole clip the text step puts several long S4 on-screen texts on top of each other and outside the frame. In the original each subtitle is shown alone, centred, wrapped to two short lines, and replaced by the next. Compare `kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/film.mp4` (text on) with the left half of `jamforelse.mp4` in the same folder.

## Task
1. Find why the S4 texts overlap in time and overflow the frame (text unit timing, grouping, wrapping, or placement). Report file:line.
2. Fix it generally, not for guacamole only: a text unit is visible only during its own source interval, long text wraps inside the frame's safe area, and two units that occupy the same screen area never overlap in time unless the source shows them together.
3. Add a plan diagnostic that warns when a text unit extends outside the frame or when two units overlap in both time and screen area without source support.

## Verification (mandatory)
- Before changing code: copy the touched files and the current plan to `kontrakt/ut/fore_text_s4/`.
- Guacamole: recompile to a new subfolder with a fresh cache folder, render with text on, and build the side-by-side comparison. Extract stills at four S4 frames where the text was wrong before, look at them and judge honestly.
- Notan (bindande väg): text units and their timing/placement unchanged unless a real overlap existed; list every difference. Old path (`kalla_jamn_golv.json`): 0 differences.
- Tests: `kontrakt/test_text_disk.py`, `test_snabb`, `test_regler`, `test_steg11`, `test_handelser`, `test_flode` except the `Plats` class (do not run it). Add tests for the new behaviour.

## Limits
- No model jobs (Modal, SAM, MoGe, Gemini, OCR services). If a cache is invalid, stop and report. Blender locally is fine.
- Never swap or temporarily replace source files to run tests. Do not change quality thresholds.
- Do not touch `kontrakt/ut/fore_*` archives other than your own, nor `app/` or `video/`.
- Leave no background processes running.

## Output
- Append a section to `GUACAMOLE-LOGG.md`; update `PIPE.md` only if a listed gap is closed.
- Final report (Swedish, max ~25 lines): cause (file:line), changed files, before/after for the S4 texts, notan and old-path differences, test results, absolute paths to film, comparison and stills with your judgement, and what is unsolved.
