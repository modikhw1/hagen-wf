# GEM-X evaluation projectors

Download the two files for Body Pose and Body Motion evaluation:

```bash
hf download nvidia/GEM-X --include 'evaluation/projectors_v1/*' --local-dir weights
```

| File | Use |
| --- | --- |
| `emdb_projector.pt` | Shared EMDB SMPL24 joints; also includes the mesh mapping for Motion PVE and foot sliding |
| `3dpw_projector.pt` | Body Pose and Motion 3DPW joint protocols; the evaluator selects the appropriate layout |

Both files accept SOMA MID meshes with 18,056 vertices in metres. Body Pose
uses its matching geometry profile; Motion evaluates MID geometry without pose
correctives. The 3DPW protocols have different joint and pelvis definitions;
sharing the file does not interchange those definitions.

Use `BodyJointProjector.from_asset` for Pose and `SomaJointRegressor` for Motion.
For Motion mesh metrics, pass `emdb_projector.pt` to `SomaMeshProjector` as well;
there is no separate mesh directory to download.

Datasets, SMPL models and prepared ground truth are obtained separately by each
user. Setup and evaluation instructions are in [GEM-X PR #34](https://github.com/NVlabs/GEM-X/pull/34)
and the repository's [Body Pose](https://github.com/NVlabs/GEM-X/blob/main/docs/BODY_BENCHMARKS.md)
and [Motion](https://github.com/NVlabs/GEM-X/blob/main/docs/MOTION_BENCHMARKS.md) guides.
