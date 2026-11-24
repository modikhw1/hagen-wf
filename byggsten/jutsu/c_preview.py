"""Run the generated Jutsu operations in local Blender for visual QA."""
from pathlib import Path
from types import SimpleNamespace
import bpy

OUT = Path(__file__).resolve().parent / 'ut/c-sketch-tre'
PREVIEW = OUT / 'preview'
PREVIEW.mkdir(exist_ok=True)


class Artifacts:
    def file(self, name, media_type):
        return SimpleNamespace(path=PREVIEW / name, publish=lambda: None)


bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for name in ('op1', 'op2'):
    context = dict(artifacts=Artifacts())
    exec(compile((OUT / f'ops/{name}.py').read_text(encoding='utf-8'), name, 'exec'), context)
    print(name, context.get('result'), flush=True)
detail = OUT.parents[1] / 'c_detail.py'
if detail.exists():
    context=dict(artifacts=Artifacts())
    exec(compile(detail.read_text(encoding='utf-8'),str(detail),'exec'),context)
    print('detail',context.get('result'),flush=True)
bpy.context.scene.frame_set(200)
exec(compile((OUT.parents[1]/'export_gate.py').read_text(encoding='utf-8'),'export_gate','exec'),{})
bpy.ops.wm.save_as_mainfile(filepath=str(PREVIEW / 'scene.blend'))
