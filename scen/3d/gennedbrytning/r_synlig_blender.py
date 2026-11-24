"""0028 punkt 3 (körs i Blender): andel synliga handpunkter och tråggolv i den byggda scenen, med strålar mot all geometri.

  blender -b <scen.blend> --python scen/3d/gennedbrytning/r_synlig_blender.py -- <ut.json> [--rutor 45 70]
Till skillnad från r_synlig.py (lådorna i planen) räknas här också kroppen själv: bålen och axeln kan skymma underarmen.
Synlig = inom kamerans bild och första träffen längs strålen är punkten själv (inom 3 cm) eller kroppens egen hand/arm nära punkten.
Objekt märkta glas (s_glas_blender.py) passeras. Handpunkter: r_wrist (huvudet), r_index3, r_middle3, r_thumb3 (svansen).
Tråget: 5 × 4 punkter på tråggolvet kring handledens läge längs disken (±0,35 m).
"""
import json, math, sys
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]; ut = a[0]
r0, r1 = (int(a[a.index('--rutor') + 1]), int(a[a.index('--rutor') + 2])) if '--rutor' in a else (45, 70)
sc = bpy.context.scene; cam = sc.camera; arm = bpy.data.objects['person:A']
glas = {o.name for o in bpy.data.objects if str(o.get('ursprung', '')).startswith('glas')}
tr = next(o for o in bpy.data.objects if o.get('room_id') == 'disk_A:trag')


def synlig(P, dg):
    v = world_to_camera_view(sc, cam, P)
    if not (0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0): return False, 'utanför bild'
    C = cam.matrix_world.translation.copy(); d = (P - C); L = d.length; d.normalize(); o = C
    for _ in range(6):
        hit, loc, nor, idx, ob, M = sc.ray_cast(dg, o, d, distance=L - (o - C).length)
        if not hit: return True, None
        if (loc - P).length < .03: return True, None
        if ob.name in glas: o = loc + d * 1e-3; continue
        if ob.name.startswith('person:A') and (loc - P).length < .08: return True, None
        return False, ob.name
    return False, 'för många lager'


rader, skym = [], {}
for f in range(r0, r1 + 1):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    pb = arm.pose.bones; M = arm.matrix_world
    pk = [M @ pb['r_wrist'].head] + [M @ pb[b].tail for b in ('r_index3', 'r_middle3', 'r_thumb3') if b in pb]
    th = tr.matrix_world.to_euler().z; ex, ey = Vector((math.cos(th), math.sin(th), 0)), Vector((-math.sin(th), math.cos(th), 0))
    c = tr.matrix_world.translation + Vector((0, 0, tr.dimensions.z / 2 + .003)); hx = (pk[0] - c).dot(ex)
    tp = [c + ex * (hx + (i / 4 - .5) * .7) + ey * (j / 3 - .5) * tr.dimensions.y * .9 for i in range(5) for j in range(4)]
    e, w = M @ pb['r_lowarm'].head, pk[0]; ap = [e + (w - e) * t for t in (.1, .3, .5, .7)]   # underarmen, armbåge -> handled
    hs = [synlig(p, dg) for p in pk]; ts = [synlig(p, dg) for p in tp]; As = [synlig(p, dg) for p in ap]
    for _, k in hs + ts + As:
        if k: skym[k] = skym.get(k, 0) + 1
    rader.append(dict(ruta=f, hand=round(sum(h for h, _ in hs) / len(hs), 2), trag=round(sum(t for t, _ in ts) / len(ts), 2), underarm=round(sum(t for t, _ in As) / len(As), 2)))
res = dict(rutor=[r0, r1], hand_synlig_andel=round(sum(r['hand'] for r in rader) / len(rader), 2), trag_synlig_andel=round(sum(r['trag'] for r in rader) / len(rader), 2), underarm_synlig_andel=round(sum(r['underarm'] for r in rader) / len(rader), 2),
           rutor_med_hela_handen=sum(r['hand'] == 1 for r in rader), av=len(rader), skyms_av=skym, glas=sorted(glas), per_ruta=rader)
json.dump(res, open(ut, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('SYNLIG', json.dumps({k: v for k, v in res.items() if k != 'per_ruta'}, ensure_ascii=False))
