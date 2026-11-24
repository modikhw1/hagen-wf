import bpy,json
s=bpy.context.scene
s['hagen_source_clip']='e-dialog-guacamole'
s['hagen_source_plan']='scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_data/plan.json'
s['hagen_provenance']='Camera and body samples transferred from existing estimated plan. Simplified room and joint mannequins. No invented acting. Lower-body estimates in shot 4 remain unreliable.'
s['hagen_export_limitation']='Hosted GLB exporter splits shared action into object clips; Blender scene has verified shared animation. Do not claim synchronized GLB playback verified.'
timeline=json.loads(s.get('blockingStudioTimeline','{}'))
camera_id=timeline['shots'][0]['cameraId']
timeline['duration']=299/30
timeline['shots']=[{'cameraId':camera_id,'start':a/30,'end':b/30} for a,b in [(0,88),(88,139),(139,190),(190,299)]]
s['blockingStudioTimeline']=json.dumps(timeline)
s.frame_set(30)
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=8;s.render.resolution_percentage=50
a=artifacts.file(name='guacamole-lit-f030.png',media_type='image/png')
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.filepath=str(a.path)
bpy.ops.render.render(write_still=True);a.publish()
s.render.engine='BLENDER_WORKBENCH';s.render.resolution_percentage=100
result={'shots':timeline['shots'],'frame':s.frame_current,'fps':s.render.fps,'known_limitation':s['hagen_export_limitation']}

