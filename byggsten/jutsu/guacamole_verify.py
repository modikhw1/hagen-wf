"""Verify camera transfer and GLB round trip at shot boundaries and key poses."""
import bpy, json, sys
from pathlib import Path
from mathutils import Matrix
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from glb_gate import read_glb,audit_gltf,file_hash
OUT=HERE/'ut/guacamole-dialog'
plan=json.loads((HERE.parents[1]/'scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_data/plan.json').read_text(encoding='utf-8'))
s=bpy.context.scene
frames=[0,30,87,88,110,138,139,165,189,190,245,298]
expected={}
camera_error=0
for frame in range(299):
    s.frame_set(frame); bpy.context.view_layer.update()
    target=Matrix(plan['renderkamera']['nycklar'][frame]['matris'])
    camera_error=max(camera_error,max(abs(s.camera.matrix_world[i][j]-target[i][j]) for i in range(4) for j in range(4)))
assert camera_error < .002,camera_error
for frame in frames:
    s.frame_set(frame); bpy.context.view_layer.update()
    expected[frame]={o.name:{'position':list(o.matrix_world.translation),'visible':not o.hide_render} for o in s.objects if o.type=='MESH'}
s.frame_set(30)
bpy.ops.export_scene.gltf(filepath=str(OUT/'preview/delivery.glb'),export_format='GLB',export_extras=True,export_cameras=True)
report=audit_gltf(read_glb(OUT/'preview/delivery.glb'))
assert report['passed'],report['errors']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUT/'preview/delivery.glb'))
s=bpy.context.scene;s.camera=bpy.data.objects['CAM_main']
for frame in frames:
    s.frame_set(frame);bpy.context.view_layer.update()
    for name,ref in expected[frame].items():
        obj=bpy.data.objects[name]
        if ref['visible']:
            assert max(abs(a-b) for a,b in zip(obj.matrix_world.translation,ref['position']))<.002,(frame,name,'position')
        else:
            assert max(obj.matrix_world.to_scale())<1e-5,(frame,name,'visibility')
report.update(roundtrip_passed=True,roundtrip_frames=frames,camera_max_matrix_error=camera_error,camera_frames_verified=299,blend_sha256=file_hash(OUT/'preview/scene.blend'),glb_sha256=file_hash(OUT/'preview/delivery.glb'))
(OUT/'glb_local_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('GUACAMOLE_ROUNDTRIP_PASS',camera_error,flush=True)
