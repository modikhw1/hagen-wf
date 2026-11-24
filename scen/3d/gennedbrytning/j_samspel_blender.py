"""0024 punkt 3, del 1 (körs i Blender): leder, skeden och disken i världen per ruta, ur en byggd scen. Läser bara, sparar inget i scenen.

  blender -b <scen.blend> --python scen/3d/gennedbrytning/j_samspel_blender.py -- <ut.json> [--rutor 0 155]
Ut: per ruta världskoordinater (Blender: Z upp, meter) för leder (huvud och svans på benen) och skedens mitt, och diskens
åtta hörn, mått och rotation. Personen är armaturen 'person:A' (S1); disken 'mall:disk_A'.
"""
import json, sys
import bpy

a = sys.argv[sys.argv.index('--') + 1:]; ut = a[0]
r0, r1 = (int(a[a.index('--rutor') + 1]), int(a[a.index('--rutor') + 2])) if '--rutor' in a else (0, 155)
LEDER = ['root', 'c_spine0', 'c_spine3', 'c_neck', 'c_head', 'l_upleg', 'r_upleg', 'l_foot', 'r_foot', 'l_ball', 'r_ball',
         'r_uparm', 'r_lowarm', 'r_wrist', 'r_index3', 'r_middle3', 'r_thumb3', 'l_uparm', 'l_lowarm', 'l_wrist', 'l_middle3']
sc = bpy.context.scene; arm = bpy.data.objects['person:A']; disk = bpy.data.objects.get('mall:disk_A') or bpy.data.objects['disk_A']   # 0027: s_scen döper om disken
sked = next((o for o in bpy.data.objects if o.name.startswith('A:hand:provsked')), None)
rutor = []
for f in range(r0, r1 + 1):
    sc.frame_set(f); M = arm.matrix_world; d = {}
    for n in LEDER:
        b = arm.pose.bones.get(n)
        if b: d[n] = dict(huvud=list(M @ b.head), svans=list(M @ b.tail))
    rutor.append(dict(ruta=f, leder=d, sked=list(sked.matrix_world.translation) if sked else None,
                      sked_R=[list(r) for r in sked.matrix_world.to_3x3().normalized()] if sked else None,   # 0027: fästets ram (sekvensens handled)
                      sked_synlig=bool(sked and not sked.hide_render and not sked.hide_get())))
hörn = [list(disk.matrix_world @ v.co) for v in disk.data.vertices]
json.dump(dict(scen=bpy.data.filepath, rutor=rutor, disk=dict(horn=hörn, mitt=list(disk.matrix_world.translation),
               matt=list(disk.dimensions), rotation_z=disk.rotation_euler.z, dold_i_render=disk.hide_render)), open(ut, 'w'), indent=0)
print('SAMSPEL_KLAR', ut, len(rutor))
