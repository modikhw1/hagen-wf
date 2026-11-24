"""One-time CC0 MakeHuman build. Blender 5.2, no external user prefs written."""
import bpy,sys,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
start=time.perf_counter()
sys.path.insert(0,str(HERE/'deps/mpfb2-master/src'))
# Isolate MPFB caches and downloaded assets inside this task workspace.
bpy.utils.extension_path_user=lambda *a,**kw:str(HERE/'deps/mpfb-user')
bpy.utils.user_resource=lambda *a,**kw:str(HERE/'deps/mpfb-user/blender')
import mpfb
bpy.context.preferences.addons.new().module='mpfb'
original_preference=mpfb.get_preference
mpfb.get_preference=lambda name,*a,**kw:str(HERE/'deps/mpfb-user') if name=='mpfb_user_data' else original_preference(name,*a,**kw)
mpfb.register()
from mpfb.services import HumanService,TargetService,FaceService
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
macro=TargetService.get_default_macro_info_dict();macro.update(gender=0.0,age=.35,muscle=.4,weight=.55,height=.5)
human=HumanService.create_human(macro_detail_dict=macro)
human.name='PerformerMesh'
FaceService.load_targets(human,load_microsoft_visemes=False,load_meta_visemes=False,load_arkit_faceunits=True)
rig=HumanService.add_builtin_rig(human,'mixamo');rig.name='PerformerRig'
bpy.context.view_layer.update()
info=dict(macro=macro,bones={b.name:dict(head=list(b.head_local),tail=list(b.tail_local),matrix=[list(r) for r in b.matrix_local],parent=b.parent.name if b.parent else None) for b in rig.data.bones},shape_keys=[k.name for k in human.data.shape_keys.key_blocks],seconds=time.perf_counter()-start)
(HERE/'character-info.json').write_text(json.dumps(info,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'character.blend'))
print('CHARACTER DONE',info['seconds'])
