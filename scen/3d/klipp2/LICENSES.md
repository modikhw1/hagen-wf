# Model and asset provenance — 2026-11-09

No SMPL, SMPL-X, mesh-recovery checkpoint, GPU inference or paid generation service was used.

| Component actually used | Licence / evidence | Scope |
|---|---|---|
| Google MediaPipe PoseLandmarker Full | Apache-2.0; [BlazePose GHUM model card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf), [MediaPipe licence](https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE) | Existing `scen/py/modeller/pose_landmarker_full.task`; body detector and landmark bundle. |
| Google HandLandmarker | Apache-2.0, explicitly in [official model card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Hand%20Tracking%20(Lite_Full)%20with%20Fairness%20Oct%202021.pdf) | Existing `scen/3d/modeller/hand_landmarker.task`; palm detector and hand landmarks. |
| Google FaceLandmarker | Apache-2.0; [Face Mesh model card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Face%20Mesh%20V2.pdf), [blendshape model card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Blendshape%20V2.pdf) | Existing `face_landmarker.task`, including facial transform and expression inference. |
| MotionBERT pose-only `FT_MB_release_MB_ft_h36m/best_epoch.bin` | Apache-2.0 in the author's [model repository licence](https://huggingface.co/walterzhu/MotionBERT/blob/main/LICENSE) and [code repository](https://github.com/Walter0807/MotionBERT/blob/main/LICENSE) | Code and checkpoint fetched from the author's model repository. Exact download URLs and SHA-256 in `motionbert-download.json`. No training datasets downloaded; the checkpoint uses H36M training and is not a guarantee about third-party dataset rights. |
| MakeHuman base mesh, macro targets, Mixamo-compatible skeleton and skin weights | CC0 graphical assets; [official licence](https://www.makehumancommunity.org/about/license.html), local `deps/mpfb2-master/LICENSE.md` | Created locally via MPFB. This is MakeHuman's named compatible rig, not an Adobe Mixamo character. X Bot and VRoid were inspected but are not used in the output. |
| ARKit faceunits01, Mika Suominen | CC0 per each of the 52 records in `deps/mpfb-user/data/packs/faceunits01.json`; [official pack](https://static.makehumancommunity.org/assets/assetpacks/faceunits01.html) | Real matching shape targets loaded onto the MakeHuman mesh; 51 non-neutral MediaPipe names are driven. MediaPipe has `_neutral` instead of `tongueOut`; tongue remains zero. |
| MPFB tooling | GPL-3.0 source; asset exception CC0, local `deps/mpfb2-master/LICENSE.md` | Runs during character creation only. The saved scene does not require the add-on. |
| Room, three tables, eyes, hair and flat materials | Task-authored procedural geometry/materials | No third-party textures or scene assets. Table positions are estimates, not tracked measurements. |
| Source video and original audio | User-supplied reference; original rights retained | Used for requested analysis and side-by-side. No assertion that the source media itself is CC0. |
| Supplied person masks | User-supplied YOLO-seg-derived masks | Used to exclude the performer from camera tracking; no YOLO model was executed in this task. The task does not identify the precise upstream checkpoint. |

Runtime libraries: NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), PyTorch (BSD-style),
OpenCV (Apache-2.0 for modern versions), MediaPipe (Apache-2.0), Python (PSF).
Blender is GPL; FFmpeg's local build and libx264 have their own distribution
licences. This task uses those applications locally and does not distribute
their binaries. Installed versions are recorded in `manifest.json`.

## RTMW exclusion is a failed bake-off requirement

The task assumes Apache-2.0 means the RTMW whole-body pretrained weights are
commercially cleared. The [rtmlib README](https://github.com/Tau-J/rtmlib)
explicitly separates the Apache-2.0 code from model-weight training-data terms.
The [maintainer discussion](https://github.com/Tau-J/rtmlib/issues/65) records
COCO-WholeBody's commercial permission issue. Accordingly RTMW/RTMW3D was not
executed or silently substituted with RTMPose body-only. Its metrics are **N/A**,
not zeros. A question asking whether a research-only comparison was acceptable
was sent; absent an answer the original commercial-use constraint was retained.

This is a provenance record of published terms, not a claim that Apache-2.0
licences erase independent dataset or source-video rights.
