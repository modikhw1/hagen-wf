import bpy, sys, math
from mathutils import Vector
ut = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
print('RUTOR', sc.frame_start, sc.frame_end, 'ARM', [(o.name, 'narvaro' in o.keys()) for o in bpy.data.objects if o.type == 'ARMATURE'])
try: sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError as e: print('MOTOR', e)
sc.render.resolution_x, sc.render.resolution_y = 1000, 800
sc.render.film_transparent = False
for o in bpy.data.objects:
    if o.type == 'MESH' and ('vagg' in o.name.lower() or 'lampa' in o.name.lower() or 'tak' in o.name.lower()): o.hide_render = True
def kam(namn, loc, mot, ortho=None):
    c = bpy.data.cameras.new(namn); o = bpy.data.objects.new(namn, c); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(mot) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho: c.type = 'ORTHO'; c.ortho_scale = ortho
    else: c.lens = 28
    return o
ovan = kam('ovan', (0.3, 1.6, 12), (0.3, 1.6, 0), 7.5); sned = kam('sned', (-5.2, -3.2, 3.4), (0, 1.4, 0.7))
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)   # markörer kan binda kameror per tagning
for namn, f in (('S1', 36), ('S2', 93), ('S4', 213), ('S6', 300), ('S7', 345)):
    sc.frame_set(f)
    for o in bpy.data.objects:      # närvaropersoner som döljs för tagningens kamera ska synas i översikten
        rot = o if o.type == 'ARMATURE' else o.parent
        if rot is not None and 'narvaro' in rot.keys(): o.hide_render = o.hide_viewport
    for k, o in (('ovan', ovan), ('sned', sned)):
        sc.camera = o; sc.render.filepath = f'{ut}/oversikt_{k}_{namn}.png'; bpy.ops.render.render(write_still=True)
