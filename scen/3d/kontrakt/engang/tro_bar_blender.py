"""Tre barprov i egen bakgrundsprocess, tom regi. Ingen öppen Blender."""
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HIT=Path(__file__).resolve().parent;sys.path.insert(0,str(HIT.parent/'ingest'));sys.path.insert(0,str(HIT))
from mhr_rig import bygg
from trohet import LED,NAMN,ruta,projicera
d=HIT/'ut/notan/tro_bar';p=json.loads((d/'plan.json').read_text(encoding='utf-8'))
bygg(str(HIT.parent/'ingest/ut/bar'),p['kallvideo'],planfil=str(d/'plan.json'),byggut=str(d))
sc=bpy.context.scene;sc.render.film_transparent=False;rows=[]
s=dict(varld=p['matning']['kameror'][0]['spar_metrisk']['sokvag'])
for f in (0,70,150):
    sc.frame_set(f);sc.render.filepath=str((d/f'bar_{f:04d}.png').resolve());bpy.ops.render.render(write_still=True)
    for pm in p['personer']:
        seq=np.load(pm['rorelse'])
        if not seq['inom'][f]:continue
        arm=bpy.data.objects['person:'+pm['id']];x=ruta(s,pm,f)
        uv=projicera(x[LED],p['renderkamera']['nycklar'][f],p['kallbild_bredd'],p['kallbild_hojd']);actual=[]
        for j in LED:
            v=world_to_camera_view(sc,sc.camera,arm.matrix_world@arm.pose.bones[NAMN[j]].head)
            actual.append([v.x*p['kallbild_bredd'],(1-v.y)*p['kallbild_hojd']])
        err=float(np.linalg.norm(np.array(actual)-uv,axis=1).max());rows.append(dict(ruta=f,person=pm['id'],max_px=err));assert err<.02,err
(d/'byggkontroll.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('Bar: numpy/Blender max',max(r['max_px'] for r in rows),'px')
