import bpy, json, math
M=json.loads(r"""{"fps":30.0,"n":383,"w":576,"h":1024,"sensor":36}""")
RUM=json.loads(r"""[{"id":"golv","p":[-1.173,1.41,-0.04],"rz":-0.0121,"m":[4.76,6.805,0.08],"f":"#a8a299","s":[0,383]},{"id":"vagg_bak","p":[-1.132,4.813,1.35],"rz":-0.0121,"m":[4.76,0.12,2.7],"f":"#e5ddc7","s":[0,383]},{"id":"vagg_sida","p":[1.207,1.382,1.35],"rz":-0.0121,"m":[0.12,6.805,2.7],"f":"#e5ddc7","s":[0,383]},{"id":"bord_1","p":[-0.0,0.829,0.677],"rz":-0.0121,"m":[0.59,1.17,0.045],"f":"#333638","s":[0,383]},{"id":"bord_1:ben:-0.24:-0.53","p":[-0.246,0.302,0.327],"rz":-0.0121,"m":[0.045,0.045,0.655],"f":"#303537","s":[0,383]},{"id":"bord_1:ben:-0.24:0.53","p":[-0.234,1.362,0.327],"rz":-0.0121,"m":[0.045,0.045,0.655],"f":"#303537","s":[0,383]},{"id":"bord_1:ben:0.24:-0.53","p":[0.234,0.296,0.327],"rz":-0.0121,"m":[0.045,0.045,0.655],"f":"#303537","s":[0,383]},{"id":"bord_1:ben:0.24:0.53","p":[0.246,1.356,0.327],"rz":-0.0121,"m":[0.045,0.045,0.655],"f":"#303537","s":[0,383]},{"id":"stol_A","p":[-0.0,-0.0,0.422],"rz":0.0,"m":[0.48,0.48,0.055],"f":"#6d6252","s":[0,383]},{"id":"stol_A:ben:-0.185:-0.185","p":[-0.185,-0.185,0.198],"rz":0.0,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_A:ben:-0.185:0.185","p":[-0.185,0.185,0.198],"rz":0.0,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_A:ben:0.185:-0.185","p":[0.185,-0.185,0.198],"rz":0.0,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_A:ben:0.185:0.185","p":[0.185,0.185,0.198],"rz":0.0,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_A:rygg","p":[-0.0,-0.215,0.68],"rz":0.0,"m":[0.48,0.055,0.43],"f":"#6d6252","s":[0,383]},{"id":"stol_A:ryggstod:-0.2","p":[-0.2,-0.215,0.55],"rz":0.0,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[0,383]},{"id":"stol_A:ryggstod:0.2","p":[0.2,-0.215,0.55],"rz":0.0,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[0,383]},{"id":"stol_B","p":[0.0,1.67,0.422],"rz":-3.1416,"m":[0.48,0.48,0.055],"f":"#6d6252","s":[0,383]},{"id":"stol_B:ben:-0.185:-0.185","p":[0.185,1.855,0.198],"rz":-3.1416,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_B:ben:-0.185:0.185","p":[0.185,1.485,0.198],"rz":-3.1416,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_B:ben:0.185:-0.185","p":[-0.185,1.855,0.198],"rz":-3.1416,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_B:ben:0.185:0.185","p":[-0.185,1.485,0.198],"rz":-3.1416,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_B:rygg","p":[0.0,1.885,0.68],"rz":-3.1416,"m":[0.48,0.055,0.43],"f":"#6d6252","s":[0,383]},{"id":"stol_B:ryggstod:-0.2","p":[0.2,1.885,0.55],"rz":-3.1416,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[0,383]},{"id":"stol_B:ryggstod:0.2","p":[-0.2,1.885,0.55],"rz":-3.1416,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[0,383]},{"id":"stol_B_avslojad","p":[0.034,3.598,0.422],"rz":-3.1537,"m":[0.48,0.48,0.055],"f":"#6d6252","s":[0,383]},{"id":"stol_B_avslojad:ben:-0.185:-0.185","p":[0.221,3.781,0.198],"rz":-3.1537,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_B_avslojad:ben:-0.185:0.185","p":[0.216,3.411,0.198],"rz":-3.1537,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_B_avslojad:ben:0.185:-0.185","p":[-0.149,3.786,0.198],"rz":-3.1537,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_B_avslojad:ben:0.185:0.185","p":[-0.154,3.416,0.198],"rz":-3.1537,"m":[0.045,0.045,0.395],"f":"#303537","s":[0,383]},{"id":"stol_B_avslojad:rygg","p":[0.036,3.813,0.68],"rz":-3.1537,"m":[0.48,0.055,0.43],"f":"#6d6252","s":[0,383]},{"id":"stol_B_avslojad:ryggstod:-0.2","p":[0.236,3.811,0.55],"rz":-3.1537,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[0,383]},{"id":"stol_B_avslojad:ryggstod:0.2","p":[-0.164,3.816,0.55],"rz":-3.1537,"m":[0.035,0.035,0.35],"f":"#6d6252","s":[0,383]},{"id":"bord_2","p":[0.023,2.764,0.718],"rz":-0.0121,"m":[0.59,1.17,0.045],"f":"#333638","s":[0,383]},{"id":"bord_2:ben:-0.24:-0.53","p":[-0.223,2.236,0.347],"rz":-0.0121,"m":[0.045,0.045,0.695],"f":"#303537","s":[0,383]},{"id":"bord_2:ben:-0.24:0.53","p":[-0.21,3.296,0.347],"rz":-0.0121,"m":[0.045,0.045,0.695],"f":"#303537","s":[0,383]},{"id":"bord_2:ben:0.24:-0.53","p":[0.257,2.231,0.347],"rz":-0.0121,"m":[0.045,0.045,0.695],"f":"#303537","s":[0,383]},{"id":"bord_2:ben:0.24:0.53","p":[0.27,3.291,0.347],"rz":-0.0121,"m":[0.045,0.045,0.695],"f":"#303537","s":[0,383]}]""")
KAM=json.loads(r"""[[0,-0.245,1.401,1.2,-0.0816,-0.069,0.642,0.7592,64.0],[72,-0.245,1.401,1.2,-0.0816,-0.069,0.642,0.7592,64.0],[73,0.15,-0.253,1.2,0.7396,0.6707,0.038,0.0419,97.9],[113,0.15,-0.253,1.2,0.7396,0.6707,0.038,0.0419,97.9],[114,-0.323,1.414,1.2,-0.1069,-0.091,0.6417,0.754,64.0],[170,-0.323,1.414,1.2,-0.1069,-0.091,0.6417,0.754,64.0],[171,0.134,0.25,1.27,0.5788,0.5839,0.4043,0.4008,64.0],[255,0.134,0.25,1.27,0.5788,0.5839,0.4043,0.4008,64.0],[256,0.217,0.235,1.2,0.7494,0.6527,0.0728,0.0836,73.1],[280,0.217,0.235,1.2,0.7494,0.6527,0.0728,0.0836,73.1],[281,-0.112,1.39,1.2,-0.0476,-0.0392,0.6351,0.77,64.0],[336,-0.112,1.39,1.2,-0.0476,-0.0392,0.6351,0.77,64.0],[337,0.192,0.248,1.2,0.7622,0.6453,0.0331,0.0391,64.0],[382,0.192,0.248,1.2,0.7622,0.6453,0.0331,0.0391,64.0]]""")
SC=json.loads(r"""[{"id":"s1","ut":[0,73],"personer":["A"],"ankare":["stol_A"]},{"id":"s2","ut":[73,114],"personer":["B"],"ankare":["stol_B"]},{"id":"s3","ut":[114,171],"personer":["A"],"ankare":["stol_A"]},{"id":"s4","ut":[171,256],"personer":["C"],"ankare":["staplats_C"]},{"id":"s5","ut":[256,281],"personer":["B"],"ankare":["stol_B"]},{"id":"s6","ut":[281,337],"personer":["A"],"ankare":["stol_A"]},{"id":"s7","ut":[337,383],"personer":["B"],"ankare":[null]}]""")
REP=json.loads(r"""[{"id":"r1","talare":"A","text":"Men vadå, menar du att du inte ska betala notan?","scen":"s1","a":0,"b":65},{"id":"r2","talare":"B","text":"varför skulle jag ta notan?","scen":"s2","a":71,"b":107},{"id":"r3","talare":"A","text":"för det är ju så gentlemen gör","scen":"s3","a":115,"b":154},{"id":"r4","talare":"A","text":"eller liksom betala halva åtminstone?","scen":"s4","a":184,"b":227},{"id":"r5","talare":"B","text":"varför skulle jag betala halva?","scen":"s4","a":235,"b":272},{"id":"r6","talare":"A","text":"för jag trodde du var en riktig man","scen":"s6","a":280,"b":327},{"id":"r7","talare":"B","text":"men jag känner inte ens dig?","scen":"s7","a":335,"b":365}]""")
PERS=json.loads(r"""{"A":{"roll":"customer","farg":"#c9b7a5"},"B":{"roll":"customer","farg":"#8fa3b8"},"C":{"roll":"waiter","farg":"#b89a8f"}}""")
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
        for fr,dold in ((0,True),(a,False),(b,True)):
            if fr>=M["n"]: continue
            if fr==0 and a==0: continue
            ob.hide_render=dold; ob.hide_viewport=dold
            ob.keyframe_insert("hide_render",frame=fr); ob.keyframe_insert("hide_viewport",frame=fr)
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
for fr in (36,200):
    s.frame_set(fr); a=artifacts.file(name=f"rum_f{fr:03d}.png",media_type="image/png"); s.render.filepath=str(a.path)
    bpy.ops.render.render(write_still=True); a.publish()
s.render.resolution_percentage=100
result={"objekt":len(bpy.data.objects),"kamnycklar":len(KAM),"markorer":len(s.timeline_markers)}
