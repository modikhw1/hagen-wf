"""Kontrollera de byggda riggarnas skyddade leder och fötter, utan GUI."""
import json
import re
import sys
from pathlib import Path
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'scen/3d/ingest'))
from mhr_rig import gravitation,F
from kroppsstod import NAMN,IX

d=Path(sys.argv[sys.argv.index('--')+1]).resolve();p=json.loads((d/'plan.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(d/'scen.blend'));sc=bpy.context.scene;nr={};rows=[]
for s in p['scener']:
    V=np.load(s['varld']);G=gravitation(V);x,y=s['ut']
    for pm in s['personer']:
        id=pm['id'];i=nr.get(id,0);nr[id]=i+1;name='person:'+id+('' if i==0 else f'.{i:03d}')
        arm=bpy.data.objects[name];S=np.load(pm['rorelse']);Mp=np.array(pm.get('till_plats',s['till_plats']))
        for frame in (x+(y-x)//3,x+2*(y-x)//3):
            f=frame-x+s['lokal_start'];sc.frame_set(frame)
            Q=Mp[:3,:3]@G@V['kam_R'][f]@F;T=Mp[:3,:3]@G@(V['kam_C'][f]+V['kam_R'][f]@S['cam_t'][f])+Mp[:3,3]
            wanted=S['pose'][f,:,:3]/100@Q.T+T
            err=max(float(np.linalg.norm(np.array(arm.matrix_world@arm.pose.bones[NAMN[j]].head)-wanted[j])) for j in range(34,len(NAMN)))
            feet=[float((arm.matrix_world@arm.pose.bones[side+'_foot'].head).z) for side in 'lr']
            hip=float((arm.matrix_world@arm.pose.bones['root'].head).z)
            dg=bpy.context.evaluated_depsgraph_get();zmin=min((ch.matrix_world@v.co).z for ch in arm.children if ch.type=='MESH' for v in ch.evaluated_get(dg).data.vertices)
            rows.append(dict(scen=s['id'],person=id,ut_ruta=frame,kallruta=p['kallrutor'][frame],overkropp_maxfel_m=err,fotled_z_m=feet,backen_z_m=hip,mesh_min_z_m=zmin))
            assert err<1e-5,(name,frame,err)
report=dict(rutor=rows,max_overkroppsfel_m=max(r['overkropp_maxfel_m'] for r in rows),mesh_min_z_m=min(r['mesh_min_z_m'] for r in rows),
            anmarkning='Ledcentrum skyddat i global pose. Hud kan påverkas av skinnvikter nära höften. Synliga ben prövas separat i unittest; notan har inga ben_synliga-rutor.')
(d/'byggkontroll.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='rutor'},ensure_ascii=False))
