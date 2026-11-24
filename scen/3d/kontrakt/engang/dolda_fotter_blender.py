"""Bygg ordinarie Blender-scen och rendera provvyer för S3/S4/S7."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KONTRAKT = HERE.parent
ROOT = KONTRAKT.parents[2]


def launch(phase: str) -> int:
    blender = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    out = KONTRAKT / "ut/dolda_fotter" / phase / "blender"
    out.mkdir(parents=True, exist_ok=True)
    cmd = [str(blender), "-b", "--factory-startup", "-t", "8", "--python-exit-code", "1",
           "--python", str(Path(__file__).resolve()), "--", "--blender", phase]
    with (out / "blender.log").open("wb") as log:
        result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    print("Blender", phase, "exit", result.returncode)
    if result.returncode:
        print((out / "blender.log").read_text(encoding="utf-8", errors="replace")[-6000:])
    return result.returncode


def render(phase: str) -> None:
    import bpy
    import numpy as np
    from mathutils import Matrix, Vector

    sys.path[:0] = [str(ROOT / "scen/3d/ingest"), str(KONTRAKT)]
    import mhr_rig

    base = KONTRAKT / "ut/dolda_fotter" / phase
    plan_path = base / "notan/plan.json"
    out = base / "blender"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    mhr_rig.bygg(str(ROOT / "scen/3d/ingest/ut/notan-tagningar/S1"),
                  str(ROOT / "scen/klipp/d-dialog-notan.mp4"),
                  planfil=str(plan_path), byggut=str(out))
    sc = bpy.context.scene
    sc.render.resolution_percentage = 50
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 8
    original = sc.camera
    moved_data = original.data.copy()
    moved_data.animation_data_clear()
    moved = bpy.data.objects.new("dolda_fotter_flyttad", moved_data)
    sc.collection.objects.link(moved)
    rows = []
    for scene in plan["scener"]:
        if scene["id"] not in ("s3", "s4", "s7"):
            continue
        a, b = scene["ut"]
        frame = (a + b) // 2
        sc.frame_set(frame)
        sc.camera = original
        bpy.context.view_layer.update()
        sc.render.filepath = str(out / f"{scene['id']}_{frame:03d}_original.png")
        bpy.ops.render.render(write_still=True)
        matrix = np.array(original.matrix_world)
        target = matrix[:3, 3] - matrix[:3, 2] * 3.0
        position = matrix[:3, 3] + .5 * matrix[:3, 0] + np.array([0., 0., .3])
        rotation = (Vector(target) - Vector(position)).to_track_quat("-Z", "Y")
        moved.matrix_world = Matrix.Translation(Vector(position)) @ rotation.to_matrix().to_4x4()
        moved_data.lens = original.data.lens
        sc.camera = moved
        sc.render.filepath = str(out / f"{scene['id']}_{frame:03d}_flyttad.png")
        bpy.ops.render.render(write_still=True)
        rows.append(dict(scen=scene["id"], ut=frame, position_m=position.tolist(), target_m=target.tolist()))
    sc.camera = original
    (out / "vyer.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args and args[0] == "--blender":
        render(args[1])
    else:
        raise SystemExit(launch(args[0] if args else "rekvisita_passad2"))
