# Orchestrator review of Phase 2 → fix these first in Phase 3, then do Phase 3

Phase 2 is accepted. It is the right direction: a real room, rounded characters driven by measured motion, and a free camera. The procedural default over VRM was the right call, because the CC0 VRoid avatars read as an anime schoolgirl and don't resemble the actors.

Fix before or while doing Phase 3:

1. **Prop scale is not calibrated.**
   - In S1/S3/S6 the burger renders ~2× larger than in the source, and the cup is somewhat too large. Calibrate every visible prop against its source box: EfficientDet/YOLO-World `saker` in `data/ra`, or Gemini on source frames, within the free budget.
   - Acceptance: the projected 2D box of each main prop is within ±25% of the source box in width and height, and its centre is within 30 px, in the close shots where it is visible.
   - Report a small table per prop. If a source box is ambiguous, say so instead of forcing it.
2. **Wrapping.** In the source, burgers sit in paper wrap or an open box, and the fries are in a carton box. Add a simple paper or box mesh so that "swap burger → pizza" later swaps the food, not the packaging.
3. **B's hair** reads as two buns or ears on top in S2/S5. Make it short, swept, side-parted brown hair as one rounded volume.

Then do Phase 3 exactly as specified in `CODEX-PROMPT.md`, with these clarifications:

- **Semantic selectors** must survive a rebuild, because ids may change. Support role (`A`), shot-scoped label (`S1:burger`), owner-scoped label (`table:A`, `A:cup`), and plain object id.
- **The orchestrator (Claude) will drive `op.py` after you are done**, so make `python scen/3d/op.py --help` self-explanatory. Also provide `op.py list` (all addressable ids and labels per shot) and `op.py show <selector>`.
- **Every demonstration edit** must be a replayable script line in `scen/3d/demo-andringar.sh`. Keep the base `scen3d.json` untouched as `scen3d.bas.json` so the edits can be replayed from scratch.
- **For edit 5** (the orbit around B's table), render a short sequence: at least 5 frames across the orbit in one contact sheet, so we can see that the room is consistent from new angles. No pixels from the source may be needed.
