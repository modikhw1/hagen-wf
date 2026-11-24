"""Läs bara en egen sparad scen: kontrollera kamera, leder, benmått och hudgolv."""
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view

HIT=Path(__file__).resolve().parent;sys.path.insert(0,str(HIT))
from trohet import NAMN,LED,ruta,projicera
from trostod import BEN,FORALDER
d=Path(sys.argv[sys.argv.index('--')+1]);p=json.loads((d/'plan.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str((d/'scen.blend').resolve()));sc=bpy.context.scene
counter={};rows=[];skin=[]
cd=bpy.data.cameras.new('kontroll_matkamera');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36
co=bpy.data.objects.new('kontroll_matkamera',cd);sc.collection.objects.link(co)
for s in p['scener']:
    for pm in s['personer']:
        pid=pm['id'];i=counter.get(pid,0);counter[pid]=i+1
        arm=bpy.data.objects['person:'+pid+('' if i==0 else f'.{i:03d}')]
        seq=np.load(pm['rorelse']);frames=range(*s['ut'])
        for u in frames:
            f=s['lokal_start']+u-s['ut'][0];sc.frame_set(u)
            if not seq['inom'][f]:continue
            dg=bpy.context.evaluated_depsgraph_get()
            minimum=min((ch.matrix_world@v.co).z for ch in arm.children if ch.type=='MESH' for v in ch.evaluated_get(dg).data.vertices)
            skin.append(dict(scen=s['id'],person=pid,ut=u,min_z_m=float(minimum)))
            if u not in (s['ut'][0]+(s['ut'][1]-s['ut'][0])//3,s['ut'][0]+2*(s['ut'][1]-s['ut'][0])//3):continue
            x=np.zeros((127,3))
            for j in range(1,127):x[j]=arm.matrix_world@arm.pose.bones[NAMN[j]].head
            expected=ruta(s,pm,f);upper=float(np.linalg.norm(x[34:]-expected[34:],axis=1).max())
            lengths=np.array(pm.get('benlangder_m',[]))
            protected=pm.get('skyddade_knan',{}).get(str(f),[False,False])
            for side,flag in zip('lr',protected):
                if flag:
                    for j in BEN:
                        if NAMN[j].startswith(side+'_upleg') or NAMN[j]==side+'_lowleg':
                            lengths[j]=np.linalg.norm(expected[j]-expected[FORALDER[j]])
            bone=max(abs(np.linalg.norm(x[j]-x[FORALDER[j]])-lengths[j]) for j in BEN) if len(lengths) else None
            key=p['matkamera']['nycklar'][u];co.matrix_world=Matrix(key['matris']);cd.lens=key['lins_mm'];sc.view_layers.update()
            w,h=p['kallbild_bredd'],p['kallbild_hojd'];buv=[]
            for j in LED:
                v=world_to_camera_view(sc,co,Vector(x[j]));buv.append([v.x*w,(1-v.y)*h])
            nuv=projicera(expected[LED],key,w,h)
            diff=float(np.linalg.norm(np.array(buv)-nuv,axis=1).max())
            # Den verkliga renderkameran kontrolleras också, även vid CM-ändring.
            kr=p['renderkamera']['nycklar'][u];want=projicera(expected[LED],kr,w,h);actual=[]
            for j in LED:
                v=world_to_camera_view(sc,sc.camera,Vector(x[j]));actual.append([v.x*w,(1-v.y)*h])
            renderdiff=float(np.linalg.norm(np.array(actual)-want,axis=1).max())
            rows.append(dict(scen=s['id'],person=pid,ut=u,numpy_blender_max_px=diff,renderkamera_max_px=renderdiff,
                             overkropp_max_m=upper,benlangd_maxfel_m=bone,mesh_min_z_m=float(minimum)))
            assert diff<.02 and renderdiff<.02,(s['id'],diff,renderdiff)
            assert upper<1e-5,(s['id'],upper)
            if bone is not None:assert bone<1e-5,(s['id'],bone)
report=dict(rutor=rows,hudgolv=skin,mesh_min_z_m=min(v['min_z_m'] for v in skin),
            max_numpy_blender_px=max(v['numpy_blender_max_px'] for v in rows),
            max_benlangdsfel_m=max(v['benlangd_maxfel_m'] for v in rows if v['benlangd_maxfel_m'] is not None))
(d/'byggkontroll.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('rutor','hudgolv')}))
assert report['mesh_min_z_m']>=-1e-5,report['mesh_min_z_m']
