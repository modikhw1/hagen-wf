"""Läs riggens hierarki i en egen Blender-bakgrundsprocess. Ingen GUI."""
import json
from pathlib import Path
import bpy
import numpy as np

HIT = Path(__file__).resolve().parent
namn = json.loads((HIT.parent/'ingest/mhr_ledernamn.json').read_text(encoding='utf-8'))
bpy.ops.import_scene.fbx(filepath=str(HIT.parent/'klipp2/sam3db/mhr/assets/lod3.fbx'))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
parents = [-1] + [namn.index(b.parent.name) if b.parent else -1 for b in arm.data.bones]
(HIT/'tro_rigg.json').write_text(json.dumps(dict(status='uppmatt', kalla='lod3.fbx: benens föräldrar, inga gissade kopplingar', namn=namn, foralder=parents), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('Exporterade', len(parents), 'föräldrar')
seq=np.load(HIT.parent/'ingest/ut/notan-tagningar/S1/sekvens_1.npz')
P=seq['rest'][1:,:3];B=list(arm.data.bones)
heads=np.array([list(arm.matrix_world@b.head_local) for b in B])
X=P-P.mean(0);Y=heads-heads.mean(0);U,_,Vt=np.linalg.svd(X.T@Y)
R=Vt.T@np.diag([1,1,np.sign(np.linalg.det(Vt.T@U.T))])@U.T
vertices=[];vertex_indices=[];joints=[];weights=[]
for mesh in [o for o in arm.children if o.type=='MESH']:
    groups={g.index:namn.index(g.name) for g in mesh.vertex_groups if g.name in namn}
    for v in mesh.data.vertices:
        co=np.array(mesh.matrix_world@v.co)
        if co[2]>.25:continue  # Hud kring fötter/vader, väl under knäet.
        index=len(vertices);vertices.append(co)
        valid=[g for g in v.groups if g.group in groups]
        total=sum(g.weight for g in valid)
        for g in valid:
            vertex_indices.append(index);joints.append(groups[g.group]);weights.append(g.weight/total)
np.savez_compressed(HIT/'tro_fothud.npz',vertices=vertices,vertex_index=vertex_indices,joints=joints,weights=weights,
                    rest_heads=heads,rest=seq['rest'],rigg_rotation=R)
print('Mätt fothud',len(vertices),'hörn, ursprung lod3.fbx; inga antagna sulmått')
