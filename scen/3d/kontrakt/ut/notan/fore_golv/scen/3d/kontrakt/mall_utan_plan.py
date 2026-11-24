"""Bygg gammal/ny mhr_rig utan plan och spara numeriska scenprov."""
import json
import sys
from pathlib import Path
import bpy

HIT=Path(__file__).resolve().parent;ROOT=HIT.parents[2]
a=sys.argv[sys.argv.index('--')+1:];version=a[0];ut=HIT/'ut/notan/mall_utan_plan'/version;ut.mkdir(parents=True,exist_ok=True)
current=HIT.parent/'ingest/mhr_rig.py'
script=HIT/'ut/notan/fore_mall/scen/3d/ingest/mhr_rig.py' if version=='fore' else current
sys.path.insert(0,str(current.parent));sys.argv=[str(current),'--',str(HIT.parent/'ingest/ut/notan-tagningar/S1'),str(ROOT/'scen/klipp/d-dialog-notan.mp4'),'--ut',str(ut)]
exec(compile(script.read_text(encoding='utf-8'),str(current),'exec'),{'__name__':'__main__','__file__':str(current)})
sc=bpy.context.scene;rows=[]
for f in (0,36,72):
    sc.frame_set(f)
    rows.append(dict(ruta=f,kameramatris=[list(r) for r in sc.camera.matrix_world],
                     ben={o.name:{b.name:[list(r) for r in b.matrix] for b in o.pose.bones} for o in bpy.data.objects if o.type=='ARMATURE'},
                     objekt=sorted(o.name for o in bpy.data.objects)))
(ut/'prov.json').write_text(json.dumps(rows,indent=1),encoding='utf-8')
