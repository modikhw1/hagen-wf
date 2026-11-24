# Codex-uppdrag: scenbriefen som eget steg (12 nov 2026)

About 40 % of the five-hour quota is left on this account. Work in the order below, write progress to `SCENBRIEF-LOGG.md` after each part so a new session can continue from disk, and stop cleanly between parts rather than leave half-edited files. This task is additive: do not change the compiler's behaviour.

Working directory: `scen/3d` in `C:\Users\praiseworthy\Desktop\hagen-wf` (Windows, no git). Python 3.12 venv in `scen/.venv`. Code, comments, logs and report in Swedish, matching existing style.

## Read first
- `PIPE.md`: "Steg 2: scenbriefen", "Deklarationen som allmän mekanism" and "Öppet".
- The two existing declarations and how they are consumed: `ingest/ut/notan-tagningar/plats/deklaration.json`, `ingest/ut/e-dialog-guacamole-tagningar/plats/deklaration.json`, `ingest/deklaration_till_hand.py`, `ingest/passa_deklaration.py`.
- `GUACAMOLE-LOGG.md`, only the headings and today's sections, to see which declared values had to be corrected after reading (A–B distance, counter height, camera height).

## Background
Step 2 of the pipeline is the only step still done by hand: someone writes `deklaration.json` (floor, places, cameras, roles, presence, relevance in three levels) before the compiler runs. The plan is that an LLM that sees all shots' key frames at once proposes it, the readings correct it, and the owner approves it in chat. The format question was left open "until after the experiment". Yesterday's work made the declaration binding through the whole compiler and showed which values a first guess gets wrong.

## Task

**Part 1: brief package.** New `ingest/scenbrief.py` with a command that, for an ingested clip, builds a self-contained package in `ingest/ut/<klipp>/brief/`:
- one contact sheet per shot (a few key frames, labelled with shot id and frame number) plus one overview sheet with all shots;
- `lasning.json`: what the readings already know per shot (person tracks, standing/sitting, eye height, hip-to-camera distance, visible feet, detected furniture/objects from the room step, on-screen text, speech timing). Reuse cached ingest output only;
- `uppdrag.md`: the instruction to the LLM. It must ask for the room hypothesis (which shots share room and camera set-up, which persons are the same across shots, how they stand relative to each other when only one is visible) and relevance in three levels, and require every numeric value to be marked as `antagen` (guess), `last` (from `lasning.json`, with source) or `deklarerad` (stated by the owner). Guessed values must be given as `[min, max]` intervals where the format allows, never as hard numbers;
- the JSON schema of the declaration, generated from what `deklaration_till_hand.py` actually accepts today (format 0.8).

**Part 2: validator.** A command that takes a proposed `deklaration.json` and reports: schema errors, places or roles referenced but not defined, shots without a camera, numeric values without a marking, guessed hard numbers, and then runs `deklaration_till_hand.py` on it in a scratch folder to confirm that it translates. Output a short `granskning.md` listing what the owner has to approve (the guessed values, the role identities, the relevance levels), written so it can be pasted into chat.

**Part 3: first experiment.** Run the package for `a-sketch-servering-tagningar` and for guacamole. Then act as the LLM yourself: look at the contact sheets and `lasning.json`, write a proposal `brief/forslag_deklaration.json` for each, without looking at the existing hand-written declarations for those clips first. Run the validator. Then compare your proposal against the existing declaration field by field and report where they agree, where they differ and which of the two the readings support. Do not replace any existing declaration and do not compile plans from the proposals.

**Part 4 (only if quota allows): feedback loop.** A command that takes a declaration and the registration/diagnostic output of a compiled plan (`plan.kvalitet.deklaration`, `registrering`, `mobelintervall`) and writes the suggested corrections as a diff the owner can approve: e.g. a place moved to the read distance and marked `last`. It only proposes; it never edits the declaration.

## Limits
- No model jobs (Modal, SAM, MoGe, Gemini or any other API). If a cache is missing, say so in the package instead of computing it. No Blender.
- Do not change `kontrakt/` or the behaviour of existing `ingest/` modules. New files only, plus tests.
- Never swap or temporarily replace source files to run tests.
- Do not touch `kontrakt/ut/fore_*`, `app/` or `video/`.
- Leave no background processes running.

## Verification
- Tests for the package builder and the validator (`ingest/test_scenbrief.py`), including that the two existing declarations pass the validator apart from missing markings, which are listed.
- `ingest/test_deklaration.py` and `ingest/test_rum.py` still green.

## Output
- Update `PIPE.md`: step 2 in the table and the "Öppet" list, briefly.
- Final report (Swedish, max ~30 lines): what the package contains, what the validator catches, the field-by-field comparison for both clips (agree / differ / what the readings support), what an LLM cannot know from the frames and must ask the owner, absolute paths to the packages and proposals, tests, and what is unsolved.
