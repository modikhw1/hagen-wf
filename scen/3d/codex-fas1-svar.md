Implemented **Phase 1 only**: 383-frame pose/hand/face extraction, camera comparisons, shared layout, and verification images. Decisions, alternatives, runtimes, and failures are appended to [LOGG.md](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/LOGG.md).

| Shot | FOV | Median error px / H | Camera height | Actor distance |
|---|---:|---:|---:|---:|
| S1 | 73° | 26.01 / 0.02540 | 1.147 m | 1.508 m |
| S2 | 62° | 19.51 / 0.01905 | 1.043 m | 1.335 m |
| S3 | 57° | 31.20 / 0.03047 | 1.208 m | 1.630 m |
| S4 | 40° | 18.37 / 0.01794 | 0.900 m | 2.322 m |
| S5 | 44° | 20.13 / 0.01966 | 1.073 m | 1.674 m |
| S6 | 57° | 30.45 / 0.02974 | 1.189 m | 1.664 m |
| S7 | 40° | 10.94 / 0.01069 | 1.042 m | 4.711 m |

**Numerical criteria pass under documented assumptions:** S1–S6 medians ≤0.04H, plausible camera heights, and qualitative S7 layout ordering. A/B are 4.91 m apart.

Compared unconstrained PnP, body-scaled Depth Anything V2, height-constrained PnP, and shared-prop refinement. Selected shared-prop PnP for joint/prop consistency; S4 uses height-constrained PnP. Depth generally produced larger errors.

**Remaining problems:** precise furniture geometry is unresolved—S7 table corners miss by 61–70 px. Independent YOLO checks exceed 0.04H in S1–S3. Some individual frames fail; scale and prop dimensions remain assumptions, and occluded hands remain missing.

Files: [motion data](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/data/sparning.json), [layout](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/data/layout.json).

Verification images: [21-frame overlays](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/verifiering/fas1.jpg), [floor plan](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/verifiering/plan.png), [S7 furniture mismatch](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/verifiering/S7-layout-overlay.jpg).