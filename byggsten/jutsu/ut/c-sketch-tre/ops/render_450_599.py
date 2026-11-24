import bpy, time
s=bpy.context.scene; t=time.time()
s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.render.resolution_percentage=50
s.frame_start=450; s.frame_end=599
a=artifacts.file(name="animatik_450_599.mp4",media_type="video/mp4")
s.render.filepath=str(a.path)
s.render.image_settings.media_type="VIDEO"; s.render.image_settings.file_format="FFMPEG"
s.render.ffmpeg.format="MPEG4"; s.render.ffmpeg.codec="H264"; s.render.ffmpeg.constant_rate_factor="MEDIUM"
bpy.ops.render.render(animation=True); a.publish()
s.frame_start=0; s.frame_end=819-1; s.render.resolution_percentage=100
s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
result={"tid_s":round(time.time()-t,1)}
