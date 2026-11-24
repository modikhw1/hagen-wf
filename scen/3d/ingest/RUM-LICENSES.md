# Model licences checked for task D — 2026-11-09

The room stage uses **MoGe-2 ViT-L Normal** for metric depth and **Gemini 3.5 Flash Lite** for open-vocabulary furniture labels/boxes. No noncommercial-only depth checkpoint is used. Model licences are distinct from the accuracy of metric estimates.

| Model / component | Actual use | Licence / conditions | Primary evidence |
|---|---|---|---|
| `Ruicheng/moge-2-vitl-normal` | New room depth, Modal GPU | MIT checkpoint; permits commercial use with copyright/licence notices | [Checkpoint licence metadata](https://huggingface.co/Ruicheng/moge-2-vitl-normal), [Microsoft licence](https://github.com/microsoft/MoGe/blob/74fbce054ebed49800de42d0ad0e83495065719a/LICENSE) |
| MoGe-2 code | New room inference | MIT, with bundled Apache-2.0 components | Same Microsoft licence; code pinned to `74fbce054ebed49800de42d0ad0e83495065719a` |
| DINOv2 ViT-L backbone | Included in MoGe-2 weights | Apache-2.0; commercial use allowed subject to its notice/patent terms | [Meta DINOv2 licence](https://github.com/facebookresearch/dinov2/blob/main/LICENSE) |
| `gemini-3.5-flash-lite` | New room labels and 2D boxes via the explicitly requested free key | Proprietary hosted API, Google APIs terms and Gemini API Additional Terms; not an open-source weight licence; commercial API applications subject to those terms | [Gemini API terms](https://ai.google.dev/gemini-api/terms), [Google API terms](https://developers.google.com/terms) |
| `yolov8s-worldv2.pt` | Evaluated for room boxes; insufficient recall on both fixtures, retained as optional detector | Ultralytics implementation/checkpoint distribution: AGPL-3.0 or commercial Enterprise licence; original YOLO-World code GPL-3.0. **Do not describe this as permissively licensed for closed-source commercial deployment.** | [Ultralytics licence](https://www.ultralytics.com/license), [weight provenance](https://docs.ultralytics.com/models/yolo-world), [original licence](https://github.com/AILab-CVC/YOLO-World/blob/master/LICENSE) |
| OpenAI CLIP ViT-B/32 | YOLO-World text encoder during evaluation | MIT | [CLIP licence](https://github.com/openai/CLIP/blob/main/LICENSE) |
| `yolo11n-seg.pt` | Existing cached person masks; no retraining/rerun in task D | Ultralytics AGPL-3.0 / Enterprise; same deployment conditions as above | [Ultralytics licence](https://www.ultralytics.com/license) |
| BoT-SORT / automatic ReID | Existing tracking cache; `spar.yaml` uses `model: auto` (detector features, no new ReID checkpoint) | Original tracker MIT; the actual Ultralytics integration is AGPL-3.0 / Enterprise | [Original tracker licence](https://github.com/NirAharon/BoT-SORT/blob/main/LICENSE), Ultralytics licence above |
| `facebook/sam-3d-body-vith` | Existing cached body fits only | Meta SAM License (local checkpoint licence dated 2025-11-19); permits use and derivatives subject to its restrictions and redistribution terms; not OSI open source | [Checkpoint](https://huggingface.co/facebook/sam-3d-body-vith), local `../klipp2/sam3db/ckpt-vith/LICENSE` |
| MHR model and `lod3.fbx` | Existing body rig, rendered unchanged | Apache-2.0 | [MHR](https://github.com/facebookresearch/MHR), local `../klipp2/sam3db/mhr/assets/LICENSE.txt` |

MoGe checkpoint revision: `cb0e8bbd6b1e243589717c78e750b1ba4c093acf`. `modal_rum.py` pins both code and weights and caches weights in Modal volume `rum-moge2-vikter`. Its `utils3d-moge` utility is pinned to `62f09d58509485564e24d5d9f6aac9ee9ebc0c37`; it is a geometry utility, not another learned model.

Depth Anything V2 Small was considered (Apache-2.0) but **not run**. The relative-depth Small checkpoint is not by itself metric depth. Large / Base noncommercial checkpoints, SAM 3, SMPL, face/expression models and Seedance were not introduced by this task.

No credentials are stored in these reports, command lines, request URLs or model caches. Gemini uses the `x-goog-api-key` header, read directly from `video/.env.local`.
