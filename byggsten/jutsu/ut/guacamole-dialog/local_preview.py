from pathlib import Path
from types import SimpleNamespace
import bpy
OUT=Path(__file__).resolve().parent
PREVIEW=OUT/'preview'; PREVIEW.mkdir(exist_ok=True)
class Artifacts:
    def file(self,name,media_type): return SimpleNamespace(path=PREVIEW/name,publish=lambda:None)
for name in ('op1_rum_tidslinje.py','op2_kroppar.py'):
    scope={'artifacts':Artifacts()}
    exec(compile((OUT/'ops'/name).read_text(encoding='utf-8'),name,'exec'),scope)
    print(name,scope.get('result'),flush=True)
bpy.context.scene.frame_set(30)
bpy.ops.wm.save_as_mainfile(filepath=str(PREVIEW/'scene.blend'))
