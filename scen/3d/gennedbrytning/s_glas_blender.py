"""0028 (körs i Blender): gör montrens front till glas i en byggd scen. Kedjans kod (mhr_rig.py) oförändrad.

  blender -b <scen.blend> --python scen/3d/gennedbrytning/s_glas_blender.py -- <room_id>[,<room_id>...] [--alfa 0.18]
Originalet visar en glasmonter: kunden ser trågen och hennes arm genom och över glaset. En massiv framkant skymmer det som
handlingsspåret påstår (handen i tråget, h3). Lådorna med angivna room_id får ett eget material med alfa < 1 (Workbench ritar det
genomskinligt), ljust blågrått. Antagen form: glas, inte mätt. Sparar scen.blend på plats.
"""
import sys
import bpy

a = sys.argv[sys.argv.index('--') + 1:]; ids = set(a[0].split(',')); alfa = float(a[a.index('--alfa') + 1]) if '--alfa' in a else .18
m = bpy.data.materials.new('glas'); m.diffuse_color = (.80, .88, .92, alfa)
for attr, val in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
    try: setattr(m, attr, val)
    except Exception: pass
n = 0
for o in bpy.data.objects:
    if o.get('room_id') in ids and o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(m); o['ursprung'] = 'glas (antagen, 0028)'; n += 1
bpy.ops.wm.save_mainfile()
print('GLAS_KLAR', n, sorted(ids))
