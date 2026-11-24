"""Körs bara i en egen bakgrunds-Blender. Skriv bygg-, render- och scenbevis."""
import importlib.util
import json
import sys
import time
from pathlib import Path
import bpy
import numpy as np

sys.dont_write_bytecode = True
HIT = Path(__file__).resolve().parent
ROT = HIT.parents[2]
UT = HIT/'ut/bar'
a = sys.argv[sys.argv.index('--')+1:]
lage = a[0]; ut = UT/lage; ut.mkdir(parents=True, exist_ok=True)
planfil = Path(a[1]).resolve() if len(a)>1 else (UT/'plan.json' if lage=='plan' else None)
fil = UT/'original/mhr_rig.py' if lage == 'original' else HIT.parent/'ingest/mhr_rig.py'
spec = importlib.util.spec_from_file_location('rigg', fil); rigg = importlib.util.module_from_spec(spec); spec.loader.exec_module(rigg)
rigg.FBX = str(HIT.parent/'klipp2/sam3db/mhr/assets/lod3.fbx')
video = ROT/'scen/klipp/kand-interpooluppsala-7601244778935766294.mp4'
t = time.perf_counter()
if lage == 'original': rigg.bygg(str(ut), str(video))
else: rigg.bygg(str(HIT.parent/'ingest/ut/bar'), str(video), planfil=str(planfil) if planfil else None, byggut=str(ut))
bygg_s = time.perf_counter()-t
sc=bpy.context.scene
rapport=dict(lage=lage,bygg_s=bygg_s,antal_rutor=sc.frame_end-sc.frame_start+1,
             objekt=sorted(o.name for o in sc.objects),aktiv_kamera=sc.camera.name,
             kameror=sorted(o.name for o in sc.objects if o.type=='CAMERA'),
             upplosning=[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],
             ljud=[dict(namn=s.name,start=s.frame_final_start,slut=s.frame_final_end,kallstart=s.frame_offset_start) for s in sc.sequence_editor.strips])
armar=sorted((o for o in sc.objects if o.type=='ARMATURE'),key=lambda o:o.name)
poser=[]
for f in range(sc.frame_start,sc.frame_end+1):
    sc.frame_set(f)
    poser.append([[np.array(arm.matrix_world @ b.matrix).tolist() for b in arm.pose.bones] for arm in armar])
np.save(ut/'poser.npy',np.array(poser))
if planfil:
    fore=np.array(poser[-1]); cam=sc.camera; plats=cam.location.copy(); cam.location.x+=5; bpy.context.view_layer.update()
    efter=np.array([[np.array(arm.matrix_world @ b.matrix).tolist() for b in arm.pose.bones] for arm in armar])
    rapport['renderkamera_flytt_max_kroppsskillnad']=float(np.max(np.abs(fore-efter))); cam.location=plats
    rapport['farger']={o.name:list(o.data.materials[0].diffuse_color) for o in sc.objects if o.type=='MESH' and o.data.materials}
t=time.perf_counter(); sc.render.filepath=str(ut/'render/f')
if '--ruta' in a:
    f=int(a[a.index('--ruta')+1]); sc.frame_set(f); sc.render.filepath=str(ut/f'render/f{f:04d}.png'); bpy.ops.render.render(write_still=True)
else: bpy.ops.render.render(animation=True)
rapport['render_s']=time.perf_counter()-t
rapport['png_antal']=len(list((ut/'render').glob('*.png')))
(ut/'rapport.json').write_text(json.dumps(rapport,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('VERIFIERAT',json.dumps(rapport,ensure_ascii=False))
