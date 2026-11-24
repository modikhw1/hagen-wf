"""Audit and render the local editable scene to a 30 fps comparison animatic."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector

OUT=Path(__file__).resolve().parent/'ut/c-sketch-tre'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from glb_gate import require_current_export,file_hash
export_report=require_current_export(OUT)
s=bpy.context.scene
s.render.engine='BLENDER_WORKBENCH'
s.display.shading.color_type='MATERIAL'
s.render.resolution_percentage=50
s.render.image_settings.media_type='IMAGE'
s.render.image_settings.file_format='PNG'
audit={}
for frame in (0,90,414,480,600,818):
    s.frame_set(frame); bpy.context.view_layer.update()
    visible=[pid for pid in ('1','2','3') if not bpy.data.objects[f'RIG_{pid}_full_huvud'].hide_render]
    expected=['1'] if frame==0 else (['1','3'] if frame>=600 else ['1','2','3'])
    assert visible==expected,(frame,visible,expected)
    audit[str(frame)]={'visible_roles':visible,'tray':list(bpy.data.objects['RIG_tray'].location)}
    s.render.filepath=str(OUT/f'preview/final_f{frame:03d}.png')
    bpy.ops.render.render(write_still=True)

# An orthographic view exposes bench/table heights and floating geometry.
original_camera=s.camera
cd=bpy.data.cameras.new('CAM_audit_side'); camera=bpy.data.objects.new('CAM_audit_side',cd)
s.collection.objects.link(camera); cd.type='ORTHO'; cd.ortho_scale=7.5
camera.location=(6,3,1.4)
camera.rotation_euler=(Vector((.3,3,-.5))-camera.location).to_track_quat('-Z','Y').to_euler()
s.camera=camera; s.frame_set(600)
s.render.filepath=str(OUT/'preview/side_audit.png'); bpy.ops.render.render(write_still=True)
s.camera=original_camera
bpy.data.objects.remove(camera,do_unlink=True)
(OUT/'visual_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
s.frame_start=0; s.frame_end=818
s.render.image_settings.media_type='VIDEO'; s.render.image_settings.file_format='FFMPEG'
s.render.ffmpeg.format='MPEG4'; s.render.ffmpeg.codec='H264'; s.render.ffmpeg.constant_rate_factor='MEDIUM'
s.render.filepath=str(OUT/'animatik_silent.mp4')
bpy.ops.render.render(animation=True)
(OUT/'render_manifest.json').write_text(json.dumps({'blend_sha256':export_report['blend_sha256'],'glb_sha256':export_report['glb_sha256'],'video_sha256':file_hash(OUT/'animatik_silent.mp4')},indent=2),encoding='utf-8')
print('ANIMATIC_COMPLETE',flush=True)
