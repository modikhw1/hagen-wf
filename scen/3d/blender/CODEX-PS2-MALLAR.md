# Codex task B: PS2 character templates and per-shot keyframes (image generation)

Repo root: `C:\Users\praiseworthy\Desktop\hagen-wf`. Work only under `scen/3d/blender/ps2/` (new). Use your **built-in image generation**. Python is `scen/.venv/Scripts/python.exe` and ffmpeg is available.

## Context
We are building a previs-to-generation chain:
- Blender (`scen/3d/blender/`) renders a blockout with exact cameras, timing and motion of a real 12.8 s clip (`scen/klipp/d-dialog-notan.mp4`, 7 shots, a restaurant dialogue about who pays the bill).
- A video model (Seedance 2.5 via Higgsfield, or Kling) will render the final look from **a start image per shot + motion reference video + original audio**.
- The target look is the viral "PS2-era game cutscene" style. Read the full spec in `scen/3d/unemployed_corp/spar/ps2_viral_sop.txt` (section 2 "PS2 VISUAL WORLD", "POLISHED PS2 — NOT UGLY PS2"). For visual references, see the contact sheets in `scen/3d/unemployed_corp/ramar/`, for example `2026-11-07_21-27-06_UTC.jpg` and `2026-11-01_17-19-58_UTC.jpg`.
- Inputs per shot in `scen/3d/blender/ut/`: `forsta_<S>.png` (blockout first frame, exact layout), `djup_<S>.png` (depth), `tagning_<S>.mp4`. The source frame at the same time can be extracted with ffmpeg from the source clip, using `scen/3d/blender/tagningslista.json` (`kalla_s`).
- **Rule: no likeness.** The source people are real. Templates must be **generic PS2 characters** that keep only role, approximate build, hairstyle category, clothing colours and seating. A is a young woman with long brown hair and a dark top. B is a young man with short light-brown hair and a navy zip sweater. C is a male staff member with a black cap and a black t-shirt with a red logo patch; use a generic logo. Do not reproduce faces or identities. Do not copy unemployed_corp's characters, logo or text either; only the rendering era and style.

## Build
1. **Character templates** (`ps2/mallar/`): one sheet per role (A, B, C) with front, three-quarter and side views, neutral pose, on a plain background, in a consistent PS2 style across all three. These are the reusable "IMAGE 1 = MAIN CHARACTER REFERENCE" assets. Add a short `mallar/README.md` with the exact prompts you used.
2. **Environment style frame** (`ps2/miljo.png`): the restaurant (dark tables, white walls, window wall, pendant lamps, counter), in the same PS2 style, from the S4 wide angle.
3. **Keyframes per shot** (`ps2/forsta_<S>.png`, 576×1024 portrait or the same aspect): a PS2 rendering of exactly the blockout composition.
   - Same camera framing, the same people in the same places and poses, and the same objects (cup, can, burger box, tray, fries) where they appear in `forsta_<S>.png` and the source frame.
   - Use the templates for identity consistency across shots.
   - Edit-from-image is preferred (the blockout and/or source frame as input) over pure text.
   - Keep the food and packaging as PS2 assets, not photos.
4. **Check each keyframe** (`ps2/kontroll.json` + `ps2/kontroll_<S>.jpg` triptych: source | blockout | PS2):
   - layout agreement with the blockout: person-mask IoU (YOLO-seg on the PS2 image vs the blockout actor mask; you can render actor-only masks from Blender or threshold the blockout) and an object position check by eye;
   - template consistency across shots;
   - absence of likeness.

   Regenerate at most 3 times per shot. Report the remaining failures honestly.

## Acceptance
- 3 templates, 1 environment frame, and 7 keyframes.
- Person-mask IoU vs the blockout ≥ 0.7 per keyframe, or explained.
- One consistent PS2 style.
- No real likeness, logos or text.
- A short report: the prompts, the IoUs per shot, what failed, and the paths.

Append to `scen/3d/blender/LOGG.md` under a heading "PS2-mallar".
