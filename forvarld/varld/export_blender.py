"""Read-only .blend extraction. Run only via export.py's process guard."""
import bpy, sys, json, time
from pathlib import Path
import numpy as np
from mathutils import Matrix

OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT))
from body_source import load_body_source
P=load_body_source()
sc=bpy.context.scene
result=[]
for s in P['scener']:
    a,b=s['ut']; sc.frame_set((a+b)//2)
    meshes=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('person:') and not o.hide_render]
    for o in meshes:
        arm=next(m.object for m in o.modifiers if m.type=='ARMATURE')
        for m in o.modifiers:
            if m.type=='ARMATURE': m.show_viewport=False
        if o.data.shape_keys:
            mixed=o.shape_key_add(name='export_current_shape',from_mix=True)
            coords=[v.co.copy() for v in mixed.data]
            o.shape_key_clear()
            for v,co in zip(o.data.vertices,coords):v.co=co
        # Collapse in rest pose, before skinning; skeleton and keys are untouched.
        dec=o.modifiers.new('PS2 offline reduction','DECIMATE')
        dec.ratio=min(1,1800/max(1,sum(len(p.vertices)-2 for p in o.data.polygons)))
        bpy.context.view_layer.objects.active=o; o.select_set(True)
        bpy.ops.object.modifier_apply(modifier=dec.name)
        o.data.calc_loop_triangles()
        bones=list(arm.data.bones); bi={x.name:i for i,x in enumerate(bones)}
        X=arm.matrix_world.inverted()@o.matrix_world
        pos=np.array([list(X@v.co) for v in o.data.vertices],np.float32)
        ids=np.zeros((len(pos),4),np.uint16); weights=np.zeros((len(pos),4),np.float32)
        for v in o.data.vertices:
            w=sorted([(g.weight,bi[o.vertex_groups[g.group].name]) for g in v.groups if o.vertex_groups[g.group].name in bi],reverse=True)[:4]
            if not w:w=[(1,0)]
            total=sum(x[0] for x in w)
            for k,(weight,j) in enumerate(w):ids[v.index,k]=j;weights[v.index,k]=weight/total
        tri=np.array([list(t.vertices) for t in o.data.loop_triangles],np.uint32)
        mats=[];visible=[]
        for f in range(a,b):
            sc.frame_set(f)
            mats.append([np.array(arm.matrix_world@arm.pose.bones[x.name].matrix@x.matrix_local.inverted()).T for x in bones])
            visible.append(not o.hide_render)
        stem=f"{s['id']}-{s['personer'][0]['id']}"
        np.savez(OUT/'paket/notan'/f'{stem}-raw.npz',pos=pos,ids=ids,weights=weights,tri=tri,matrices=np.asarray(mats,np.float32),visible=visible)
        skeleton=[dict(name=x.name,parent=bi[x.parent.name] if x.parent else -1,restMatrixColumnMajor=np.array(x.matrix_local).T.flatten().tolist(),restHead=list(x.head_local),restTail=list(x.tail_local)) for x in bones]
        result.append(dict(scene=s['id'],person=s['personer'][0]['id'],stem=stem,triangles=len(tri),vertices=len(pos),bones=len(bones),frames=b-a,skeleton=skeleton))
        print('EXPORTED',s['id'],len(tri),'triangles',len(bones),'unchanged bones',flush=True)
(OUT/'paket/notan/meshes.json').write_text(json.dumps(result),encoding='utf8')
