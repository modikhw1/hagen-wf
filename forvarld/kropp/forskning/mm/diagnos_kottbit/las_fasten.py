"""Diagnos köttbit: läser Child Of-fästet, köttbitens och handledernas världsläge/orientering och bildläge (kamera) i en byggd scen.
  blender -b <scen.blend> --python las_fasten.py -- <ut.json> [rutor...]"""
import bpy, sys, json, math
from mathutils import Matrix
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index('--') + 1:]; ut = a[0]; rutor = [int(x) for x in a[1:]] or [110, 129, 140]
sc = bpy.context.scene; kam = sc.camera; R = {'kamera': kam.name if kam else None, 'foremal': {}, 'rutor': {}}
obs = [o for o in bpy.data.objects if 'hand:kottbit' in o.name]
for o in obs:
    c = next((c for c in o.constraints if c.type == 'CHILD_OF'), None)
    R['foremal'][o.name] = dict(target=c.target.name if c else None, subtarget=c.subtarget if c else None,
        inverse_ar_identitet=bool(c and all(abs(c.inverse_matrix[i][j] - (i == j)) < 1e-9 for i in range(4) for j in range(4))),
        set_inverse_pending=getattr(c, 'set_inverse_pending', None), influence=c.influence if c else None,
        matrix_basis=[list(r) for r in o.matrix_basis], lokal_forskjutning_m=list(o.matrix_basis.translation), parent=o.parent.name if o.parent else None)
def bild(p):
    v = world_to_camera_view(sc, kam, p); return [round(v.x, 3), round(v.y, 3), round(v.z, 3)]
for f in rutor:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); r = {}
    for o in obs:
        if not o.name.endswith(':s3'): continue
        oe = o.evaluated_get(dg); p = oe.matrix_world.translation
        r[o.name] = dict(varld=[round(x, 4) for x in p], bild=bild(p), dold=o.hide_render)
    for an in ('person:B', 'person:B.001'):
        arm = bpy.data.objects.get(an)
        if not arm: continue
        for ben in ('r_wrist', 'l_wrist', 'r_lowarm', 'l_lowarm'):
            pb = next((b for b in arm.pose.bones if b.name == ben or b.name.endswith(':' + ben)), None)
            if not pb: continue
            M = arm.matrix_world @ pb.matrix; q = M.to_quaternion()
            r[f'{an}/{ben}'] = dict(varld=[round(x, 4) for x in M.translation], bild=bild(M.translation), quat=[round(x, 4) for x in q],
                                    axlar={k: [round(x, 3) for x in M.to_3x3().normalized().col[i]] for i, k in enumerate('xyz')}, dold=arm.hide_render)
    # rendrerad hand: kroppsmeshens vertexar som vägs mest mot r_wrist, deformerade
    me = bpy.data.objects.get('person:B:kropp')
    if me:
        vg = next((g for g in me.vertex_groups if g.name.endswith('r_wrist')), None)
        if vg:
            idx = [v.index for v in me.data.vertices if any(g.group == vg.index and g.weight > .5 for g in v.groups)]
            mm = me.evaluated_get(dg).to_mesh(); W = me.matrix_world
            ps = [W @ mm.vertices[i].co for i in idx]; m = sum(ps, ps[0] * 0) / len(ps)
            r['mesh_r_wrist_medel'] = dict(varld=[round(x, 4) for x in m], bild=bild(m), n=len(idx)); me.evaluated_get(dg).to_mesh_clear()
    R['rutor'][f] = r
json.dump(R, open(ut, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('KLAR', ut)
