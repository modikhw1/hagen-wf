"""Export Guacamole's existing plan through the Notan adapter, preserving all frames."""
import json
from pathlib import Path
import notan_export

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'ut/guacamole-dialog'
notan_export.PLAN = ROOT / 'scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_data/plan.json'
notan_export.KALLA = ROOT / 'scen/3d/kontrakt/ut/e-dialog-guacamole/kalla_mobelintervall.json'
notan_export.UT = OUT / 'guacamole_jutsu.json'
notan_export.STEG = 1
notan_export.main()

# Use the shared operation generator without changing Notan's files or outputs.
source = (HERE / 'notan_ops.py').read_text(encoding='utf-8')
source = source.replace('ut/notan/notan_jutsu.json', 'ut/guacamole-dialog/guacamole_jutsu.json')
source = source.replace('ut/notan/ops', 'ut/guacamole-dialog/ops')
source = source.replace('(36,140,200,360)', '(30,110,165,245)')
source = source.replace('(36,200)', '(30,110)')
source = source.replace('def synlighet(ob,intervall):', 'def synlighet(ob,intervall):\n    bpy.context.preferences.edit.keyframe_new_interpolation_type="CONSTANT"')
# Room visibility is also a discrete switch; camera/body movement remains linear.
source = source.replace('    if a>0 or b<M["n"]:', '    if a>0 or b<M["n"]:\n        bpy.context.preferences.edit.keyframe_new_interpolation_type="CONSTANT"')
source = source.replace('cd=bpy.data.cameras.new', 'bpy.context.preferences.edit.keyframe_new_interpolation_type="LINEAR"\ncd=bpy.data.cameras.new')
exec(compile(source, str(HERE / 'notan_ops.py'), 'exec'), {'__file__': str(HERE / 'notan_ops.py')})

op1 = OUT / 'ops/op1_rum_tidslinje.py'
text = op1.read_text(encoding='utf-8')
reset = '''import bpy
# Replace this project's previous authored blockout; earlier revision remains available.
for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
for collection in list(bpy.data.collections): bpy.data.collections.remove(collection)
for key in list(bpy.context.scene.keys()): del bpy.context.scene[key]
'''
op1.write_text(reset + text, encoding='utf-8')

preview = '''from pathlib import Path
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
'''
(OUT / 'local_preview.py').write_text(preview, encoding='utf-8')
data=json.loads(notan_export.UT.read_text(encoding='utf-8'))
assert len(data['kamera']) == 299
assert len(data['scener']) == 4
assert all(len(p['rutor']) == s['ut'][1]-s['ut'][0] for s in data['scener'] for p in s['personer'])
print('Verified: 299 camera samples, four shots, body samples on every frame.')
