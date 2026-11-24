"""Render visible actor masks from scen.blend, retaining prop/set occlusion."""
import bpy, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'
sc.use_nodes = False
if hasattr(sc, 'compositing_node_group'): sc.compositing_node_group = None
sh = sc.display.shading
sh.light = 'FLAT'
sh.color_type = 'OBJECT'
sh.show_shadows = False
sh.show_cavity = False
sh.show_specular_highlight = False
sh.show_object_outline = False
sh.background_type = 'WORLD'
sc.world.color = (0, 0, 0)
sc.world.use_nodes = False
sc.display.render_aa = '8'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0
sc.view_settings.gamma = 1
actors = bpy.data.collections.get('bakade_aktorer')
if actors is None: raise RuntimeError('Actor collection missing')
actor_names = {o.name for o in actors.all_objects}
for o in sc.objects: o.color = (1,1,1,1) if o.name in actor_names else (0,0,0,1)
for s in json.loads((HERE.parent/'tagningslista.json').read_text(encoding='utf-8'))['tagningar']:
    sc.frame_set(s['bildrutor'][0])
    sc.camera = bpy.data.objects['kam:'+s['id']]
    sc.render.filepath = str(HERE/'masker'/f"blockout_{s['id']}.png")
    bpy.ops.render.render(write_still=True)
print('MASKS_DONE', len(actor_names))
