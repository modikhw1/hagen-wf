import bpy
# Replace this project's previous authored blockout; earlier revision remains available.
for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
for collection in list(bpy.data.collections): bpy.data.collections.remove(collection)
for key in list(bpy.context.scene.keys()): del bpy.context.scene[key]
import bpy, json, math
M=json.loads(r"""{"fps":30.0,"n":299,"w":576,"h":1024,"sensor":36}""")
RUM=json.loads(r"""[{"id":"golv","p":[0.242,0.498,-0.04],"rz":0.0576,"m":[5.345,4.968,0.08],"f":"#a8a299","s":[0,299]},{"id":"vagg_bak","p":[0.099,2.978,1.35],"rz":0.0576,"m":[5.345,0.12,2.7],"f":"#e5ddc7","s":[0,299]},{"id":"vagg_sida","p":[2.91,0.652,1.35],"rz":0.0576,"m":[0.12,4.968,2.7],"f":"#e5ddc7","s":[0,299]},{"id":"stol_A","p":[0.0,0.0,0.723],"rz":-0.0333,"m":[0.48,0.48,0.055],"f":"#6d6252","s":[0,190]},{"id":"stol_A","p":[0.001,-0.006,0.723],"rz":-0.0333,"m":[0.48,0.48,0.055],"f":"#6d6252","s":[190,299]},{"id":"stol_A:ben:-0.185:-0.185","p":[-0.191,-0.178,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[0,88]},{"id":"stol_A:ben:-0.185:-0.185","p":[-0.19,-0.181,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[88,190]},{"id":"stol_A:ben:-0.185:-0.185","p":[-0.19,-0.184,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[190,299]},{"id":"stol_A:ben:-0.185:0.185","p":[-0.178,0.191,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[0,190]},{"id":"stol_A:ben:-0.185:0.185","p":[-0.178,0.185,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[190,299]},{"id":"stol_A:ben:0.185:-0.185","p":[0.179,-0.191,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[0,88]},{"id":"stol_A:ben:0.185:-0.185","p":[0.179,-0.194,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[88,190]},{"id":"stol_A:ben:0.185:-0.185","p":[0.18,-0.197,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[190,299]},{"id":"stol_A:ben:0.185:0.185","p":[0.191,0.179,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[0,88]},{"id":"stol_A:ben:0.185:0.185","p":[0.192,0.176,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[88,190]},{"id":"stol_A:ben:0.185:0.185","p":[0.192,0.173,0.347],"rz":-0.0333,"m":[0.045,0.045,0.695],"f":"#303537","s":[190,299]},{"id":"stol_A:rygg","p":[-0.007,-0.215,0.98],"rz":-0.0333,"m":[0.48,0.055,0.43],"f":"#6d6252","s":[0,190]},{"id":"stol_A:rygg","p":[-0.006,-0.22,0.98],"rz":-0.0333,"m":[0.48,0.055,0.43],"f":"#6d6252","s":[190,299]},{"id":"stol_A:ryggstod:-0.2","p":[-0.207,-0.208,0.85],"rz":-0.0333,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[0,88]},{"id":"stol_A:ryggstod:-0.2","p":[-0.206,-0.211,0.85],"rz":-0.0333,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[88,190]},{"id":"stol_A:ryggstod:-0.2","p":[-0.206,-0.214,0.85],"rz":-0.0333,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[190,299]},{"id":"stol_A:ryggstod:0.2","p":[0.193,-0.221,0.85],"rz":-0.0333,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[0,88]},{"id":"stol_A:ryggstod:0.2","p":[0.193,-0.224,0.85],"rz":-0.0333,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[88,190]},{"id":"stol_A:ryggstod:0.2","p":[0.194,-0.227,0.85],"rz":-0.0333,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[190,299]},{"id":"bardisk","p":[0.012,0.651,0.5],"rz":0.0576,"m":[2.8,0.65,1.0],"f":"#333638","s":[0,299]}]""")
KAM=json.loads(r"""[[0,-1.754,1.677,1.4,-0.3272,-0.3507,0.6416,0.5985,64.0],[87,-1.754,1.677,1.4,-0.3272,-0.3507,0.6416,0.5985,64.0],[88,1.03,0.39,1.4,0.6276,0.6298,0.3241,0.323,64.0],[138,1.03,0.39,1.4,0.6276,0.6298,0.3241,0.323,64.0],[139,-2.037,2.294,1.4,-0.2852,-0.2953,0.6559,0.6335,64.0],[189,-2.037,2.294,1.4,-0.2852,-0.2953,0.6559,0.6335,64.0],[190,2.244,2.476,1.4,0.3486,0.3534,0.6179,0.6097,64.0],[298,2.244,2.476,1.4,0.3486,0.3534,0.6179,0.6097,64.0]]""")
SC=json.loads(r"""[{"id":"s1","ut":[0,88],"personer":["A"],"ankare":["stol_A"]},{"id":"s2","ut":[88,139],"personer":["B"],"ankare":["staplats_B"]},{"id":"s3","ut":[139,190],"personer":["A"],"ankare":["stol_A"]},{"id":"s4","ut":[190,299],"personer":["B","A"],"ankare":["staplats_B","stol_A"]}]""")
REP=json.loads(r"""[{"id":"r1","talare":"A","text":"Ursäkta, kommer guacamolen av sig själv?","scen":"s1","a":0,"b":68},{"id":"r2","talare":"B","text":"Nej, nej, asså jag kommer ut med den","scen":"s2","a":86,"b":131},{"id":"r3","talare":"A","text":"Asså jag menar, kommer den med något annat?","scen":"s3","a":148,"b":185},{"id":"r4","talare":"B","text":"AAAAA! Jag trodde du var en sådan idiot, men nej, den kommer med nachos","scen":"s4","a":190,"b":264}]""")
PERS=json.loads(r"""{"A":{"roll":"customer","farg":"#c9b7a5"},"B":{"roll":"waiter","farg":"#8fa3b8"}}""")
s=bpy.context.scene
bpy.context.preferences.edit.keyframe_new_interpolation_type="LINEAR"
s.render.fps=int(M["fps"]); s.frame_start=0; s.frame_end=M["n"]-1
s.render.resolution_x=M["w"]; s.render.resolution_y=M["h"]
mats={}
def mat(h):
    if h in mats: return mats[h]
    c=tuple((int(h[i:i+2],16)/255)**2.2 for i in (1,3,5))
    m=bpy.data.materials.new("M_"+h[1:]); m.use_nodes=True; m.diffuse_color=(*c,1)
    b=next(x for x in m.node_tree.nodes if x.type=="BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value=(*c,1); b.inputs["Roughness"].default_value=0.7
    mats[h]=m; return m
import bmesh
me=bpy.data.meshes.new("lada_enhet"); bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1.0); bm.to_mesh(me); bm.free()
kol=bpy.data.collections.new("ENV_rum"); s.collection.children.link(kol)
roll={"golv":"ENV","vagg":"ENV"}
raknare={}
for o in RUM:
    bas=o["id"].split(":")[0]; pre=roll.get(bas.split("_")[0],"PRP")
    nm=f"{pre}_{o['id'].replace(':','_')}"; raknare[nm]=raknare.get(nm,0)+1
    if raknare[nm]>1: nm=f"{nm}__{raknare[nm]}"
    me_o=me.copy(); me_o.materials.append(mat(o["f"]))
    ob=bpy.data.objects.new(nm,me_o); kol.objects.link(ob)
    ob.location=o["p"]; ob.rotation_euler=(0,0,o["rz"]); ob.scale=o["m"]
    ob["deklaration_id"]=bas; ob["synlig_ut"]=o["s"]
    a,b=o["s"]
    if a>0 or b<M["n"]:
        bpy.context.preferences.edit.keyframe_new_interpolation_type="CONSTANT"
        for fr,dold in ((0,True),(a,False),(b,True)):
            if fr>=M["n"]: continue
            if fr==0 and a==0: continue
            ob.hide_render=dold; ob.hide_viewport=dold
            ob.keyframe_insert("hide_render",frame=fr); ob.keyframe_insert("hide_viewport",frame=fr)
bpy.context.preferences.edit.keyframe_new_interpolation_type="LINEAR"
cd=bpy.data.cameras.new("CAM_main"); cd.sensor_width=M["sensor"]; cd.sensor_fit="HORIZONTAL"
c=bpy.data.objects.new("CAM_main",cd); s.collection.objects.link(c); s.camera=c; c.rotation_mode="QUATERNION"
for k in KAM:
    fr,x,y,z,qw,qx,qy,qz,lens=k
    c.location=(x,y,z); c.rotation_quaternion=(qw,qx,qy,qz); cd.lens=lens
    c.keyframe_insert("location",frame=fr); c.keyframe_insert("rotation_quaternion",frame=fr); cd.keyframe_insert("lens",frame=fr)
for ad in (c.animation_data, cd.animation_data):
    for fc in ad.action.fcurves if hasattr(ad.action,"fcurves") else []:
        for kp in fc.keyframe_points: kp.interpolation="LINEAR"
for m_ in list(s.timeline_markers): s.timeline_markers.remove(m_)
for sc in SC:
    mk=s.timeline_markers.new(f"{sc['id']} {'+'.join(sc['personer'])}",frame=sc["ut"][0])
for r in REP:
    s.timeline_markers.new(f"{r['id']} {r['talare']}: {r['text']}"[:63],frame=r["a"])
s["hagen_scener"]=json.dumps(SC,ensure_ascii=False)
s["hagen_repliker"]=json.dumps(REP,ensure_ascii=False)
s["hagen_personer"]=json.dumps(PERS,ensure_ascii=False)
ld=bpy.data.lights.new("LGT_key","SUN"); ld.energy=2.5; l=bpy.data.objects.new("LGT_key",ld); s.collection.objects.link(l); l.rotation_euler=(math.radians(40),math.radians(-20),math.radians(60))
fd=bpy.data.lights.new("LGT_fill","POINT"); fd.energy=300; fd.shadow_soft_size=1.5; fl=bpy.data.objects.new("LGT_fill",fd); s.collection.objects.link(fl); fl.location=(-1.5,1.5,2.4)
s.world=s.world or bpy.data.worlds.new("World"); s.world.use_nodes=True
bg=next(x for x in s.world.node_tree.nodes if x.type=="BACKGROUND"); bg.inputs["Strength"].default_value=0.4
s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.render.resolution_percentage=50
s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
ut={}
for fr in (30,110):
    s.frame_set(fr); a=artifacts.file(name=f"rum_f{fr:03d}.png",media_type="image/png"); s.render.filepath=str(a.path)
    bpy.ops.render.render(write_still=True); a.publish()
s.render.resolution_percentage=100
result={"objekt":len(bpy.data.objects),"kamnycklar":len(KAM),"markorer":len(s.timeline_markers)}
