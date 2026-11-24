"""Diagnos köttbit: person:B:s rot/huvud/händer i världen, i bild och relativt roten (rotens ram), ruta för ruta.
  blender -b <scen.blend> --python las_kropp.py -- <ut.json> a b"""
import bpy, sys, json
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index('--') + 1:]; ut = a[0]; f0, f1 = int(a[1]), int(a[2])
sc = bpy.context.scene; kam = sc.camera; arm = bpy.data.objects['person:B']; R = {}
def pb(n): return next(b for b in arm.pose.bones if b.name == n or b.name.endswith(':' + n))
for f in range(f0, f1):
    sc.frame_set(f); r = {}
    Mr = arm.matrix_world @ pb('root').matrix
    for n in ('root', 'c_spine3', 'c_head', 'r_uparm', 'r_lowarm', 'r_wrist', 'l_wrist'):
        M = arm.matrix_world @ pb(n).matrix; v = world_to_camera_view(sc, kam, M.translation)
        r[n] = dict(varld=[round(x, 4) for x in M.translation], bild=[round(v.x, 3), round(v.y, 3)],
                    i_rot=[round(x, 4) for x in (Mr.inverted() @ M).translation], rot_quat_i_rot=[round(x, 4) for x in (Mr.inverted() @ M).to_quaternion()])
    r['kamera'] = [round(x, 4) for x in kam.matrix_world.translation]
    R[f] = r
json.dump(R, open(ut, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('KLAR', ut)
