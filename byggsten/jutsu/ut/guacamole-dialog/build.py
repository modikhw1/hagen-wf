import bpy, math, json
from mathutils import Vector
s=bpy.context.scene
s.unit_settings.system='METRIC'
s.render.engine='BLENDER_EEVEE'
s.render.resolution_x=360
s.render.resolution_y=640
s.render.resolution_percentage=100
s.render.fps=30
s.frame_start=0
s.frame_end=298
def mat(n,c):
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=.65
 return m
cream=mat('Warm plaster',(.65,.59,.43)); floor=mat('Stone',(.25,.23,.20)); wood=mat('Counter walnut',(.24,.105,.04)); dark=mat('Charcoal',(.055,.065,.07)); teal=mat('Staff teal',(.06,.26,.25)); skin=mat('Neutral mannequin',(.65,.43,.26))
def box(n,p,d,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p); o=bpy.context.object; o.name=n; o.dimensions=d; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m); return o
def ball(n,p,r,m,scale=(1,1,1)):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=r,location=p); o=bpy.context.object;o.name=n;o.scale=scale;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def rod(n,a,b,r,m):
 a,b=Vector(a),Vector(b);d=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.name=n;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(m)
 return o
box('ENV_floor',(-.4,.465,-.04),(3.2,4.93,.08),floor)
box('ENV_back_wall',(-.4,2.93,1.35),(3.2,.12,2.7),cream)
box('ENV_side_wall',(1.2,.465,1.35),(.12,4.93,2.7),cream)
box('PRP_counter_base',(0,.65,.5),(2.8,.65,1),dark)
box('PRP_counter_top',(0,.65,1.025),(2.86,.71,.05),wood)
box('PRP_stool_seat',(0,0,.72),(.48,.48,.06),wood)
for x in [-.18,.18]:
 for y in [-.18,.18]:rod('PRP_stool_leg',(x,y,.02),(x,y,.70),.022,dark)
# Authored neutral poses at the declared anchors, not captured motion.
ball('HERO_A_torso',(0,0,1.12),1,dark,(.23,.15,.34))
ball('HERO_A_head',(0,.035,1.61),.135,skin,(.85,1,1.15))
for x in [-.14,.14]:
 rod('HERO_A_thigh',(x,0,.79),(x,.27,.70),.075,dark)
 rod('HERO_A_shin',(x,.27,.70),(x,.30,.12),.055,dark)
 box('HERO_A_shoe',(x,.36,.055),(.13,.25,.11),dark)
 rod('HERO_A_upperarm',(x*1.6,0,1.35),(x*1.7,.25,1.10),.055,skin)
 rod('HERO_A_forearm',(x*1.7,.25,1.10),(x*.5,.48,1.12),.045,skin)
box('PRP_phone',(0,.48,1.15),(.075,.13,.015),dark)
ball('HERO_B_torso',(.4,1.50,1.17),1,teal,(.25,.17,.36))
ball('HERO_B_head',(.4,1.48,1.68),.135,skin,(.85,1,1.15))
for x in [.25,.55]:
 rod('HERO_B_leg',(x,1.5,.9),(x,1.5,.12),.075,dark)
 box('HERO_B_shoe',(x,1.43,.055),(.14,.27,.11),dark)
 rod('HERO_B_upperarm',(x+(-.09 if x<.4 else .09),1.5,1.4),(x+(-.12 if x<.4 else .12),1.35,1.12),.055,teal)
 rod('HERO_B_forearm',(x+(-.12 if x<.4 else .12),1.35,1.12),(x,1.02,1.11),.045,skin)
for i,c in enumerate([(.55,.12,.025),(.035,.26,.14),(.65,.38,.035)]):
 box('ENV_color_panel_'+str(i),(-1.35+i*.8,2.85,1.6),(.65,.025,1.65),mat('Panel'+str(i),c))
bpy.ops.object.camera_add(location=(-3.7,-3.2,2.75))
cam=bpy.context.object;cam.name='CAM_main';cam.rotation_euler=(Vector((0,.65,1.05))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=43;s.camera=cam
bpy.ops.object.light_add(type='SUN',location=(-3,-2,5));key=bpy.context.object;key.name='LGT_key';key.rotation_euler=(.45,-.5,-.4);key.data.energy=2;key.data.angle=.3
bpy.ops.object.light_add(type='POINT',location=(-1,.5,2.5));fill=bpy.context.object;fill.name='LGT_fill';fill.data.energy=120;fill.data.shadow_soft_size=1
s.world=bpy.data.worlds.new('World_ambient');s.world.color=(.18,.18,.18)
for frame,label in [(0,'s1 Kunden frågar'),(88,'s2 Personalen svarar'),(139,'s3 Kunden förtydligar'),(190,'s4 Slutpoäng')]:s.timeline_markers.new(label,frame=frame)
s['hagen_source_clip']='e-dialog-guacamole'
s['hagen_source_sha256']='114226c39491c068404eee6bea6ced968703ac30c2cbf62dd91e97c6402d4700'
s['hagen_assumptions']='Static storyboard blockout. Dimensions from rumsmall/1. Neutral authored poses, overview camera and simplified materials. Not motion capture or exact source reconstruction.'
s.frame_set(0)
bpy.context.view_layer.update()
target=artifacts.file(name='guacamole-overview.png',media_type='image/png')
s.render.filepath=str(target.path);s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
bpy.ops.render.render(write_still=True);target.publish()
result={'objects':len(s.objects),'camera':s.camera.name,'counter_dimensions':list(bpy.data.objects['PRP_counter_base'].dimensions),'markers':len(s.timeline_markers),'static_blockout':True}

