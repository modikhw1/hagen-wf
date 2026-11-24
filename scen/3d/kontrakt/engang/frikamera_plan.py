"""Renderar hela tidslinjen i en byggd scen.blend från en fri kamera, så att alla i rummet syns (även närvaropersoner som döljs för tagningens egen kamera).
   blender -b <scen.blend> --python frikamera_plan.py -- <utmapp> [x y z  mx my mz]"""
import bpy, sys
from mathutils import Vector
arg = sys.argv[sys.argv.index('--') + 1:]; ut = arg[0]
loc = tuple(map(float, arg[1:4])) if len(arg) >= 7 else (-3.4, -1.9, 2.3); mot = tuple(map(float, arg[4:7])) if len(arg) >= 7 else (0.0, 1.1, 0.75)
sc = bpy.context.scene
try: sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError: pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 720, 100
for o in bpy.data.objects:
    if o.type == 'MESH' and any(n in o.name.lower() for n in ('vagg', 'lampa', 'tak')): o.hide_render = True
c = bpy.data.cameras.new('fri'); k = bpy.data.objects.new('fri', c); sc.collection.objects.link(k); k.location = loc; c.lens = 30
k.rotation_euler = (Vector(mot) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
dolda = [o for o in bpy.data.objects if (o if o.type == 'ARMATURE' else o.parent) is not None and 'narvaro' in (o if o.type == 'ARMATURE' else o.parent).keys()]
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f)
    for o in dolda: o.hide_render = o.hide_viewport
    sc.camera = k; sc.render.filepath = f'{ut}/{f:04d}.png'; bpy.ops.render.render(write_still=True)
