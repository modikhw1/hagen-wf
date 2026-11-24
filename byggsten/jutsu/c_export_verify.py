"""Round-trip the actual export; gate failure returns a nonzero Blender exit."""
import bpy
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from glb_gate import read_glb,audit_gltf,file_hash
import json
OUT=HERE/'ut/c-sketch-tre'
exec(compile((HERE/'export_gate.py').read_text(encoding='utf-8'),'export_gate','exec'),{})
bpy.context.scene.frame_set(200)
expected={}
for frame in (0,200,600,818):
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    expected[frame]={o.name: list(o.matrix_world.translation) for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render}
bpy.context.scene.frame_set(200)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'preview/scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'preview/delivery.glb'),export_format='GLB',export_extras=True,export_cameras=True)
report=audit_gltf(read_glb(OUT/'preview/delivery.glb'))
report.update(blend_sha256=file_hash(OUT/'preview/scene.blend'),glb_sha256=file_hash(OUT/'preview/delivery.glb'),roundtrip_passed=False)
(OUT/'glb_local_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert report['passed'],report['errors']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUT/'preview/delivery.glb'))
s=bpy.context.scene
s.camera=bpy.data.objects.get('CAM_main')
assert s.camera is not None
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='MATERIAL'
s.render.resolution_x=288;s.render.resolution_y=512;s.render.resolution_percentage=100
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
for frame in (0,200,600,818):
    s.frame_set(frame);bpy.context.view_layer.update()
    for name,position in expected[frame].items():
        actual=bpy.data.objects[name].matrix_world.translation
        assert max(abs(a-b) for a,b in zip(actual,position))<.002,(frame,name,list(actual),position)
    s.render.filepath=str(OUT/f'preview/glb_roundtrip_f{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
print('GLB_ROUNDTRIP_PASS',report,flush=True)
report.update(roundtrip_passed=True,roundtrip_frames=[0,200,600,818],position_tolerance_m=.002)
(OUT/'glb_local_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
