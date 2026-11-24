"""Gör bpy-koden för 3D Jutsu ur ut/notan/notan_jutsu.json.

op1_rum_tidslinje.py : rum (lådor med synlighet), kamera, markörer, mening, ljus, kontrollbilder
op2_kroppar.py       : nivå 3 (hela rörelsen, 10 fps) och nivå 2 (poser per beat), dockor av leder
op3_animatik.py      : Workbench-MP4 av hela klippet (halv upplösning)
"""
import json
from pathlib import Path

HIT = Path(__file__).resolve().parent
D = json.loads((HIT / "ut/notan/notan_jutsu.json").read_text(encoding="utf-8"))
UT = HIT / "ut/notan/ops"; UT.mkdir(parents=True, exist_ok=True)
J = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":"))

# Komprimering: samma låda (id, läge inom 3 mm) i intilliggande scener slås ihop till ett intervall.
rum = []
for o in D["rum"]:
    prev = next((r for r in rum if r["id"] == o["id"] and r["s"][1] == o["s"][0]
                 and max(abs(a - b) for a, b in zip(r["p"], o["p"])) <= 0.003), None)
    if prev: prev["s"] = [prev["s"][0], o["s"][1]]
    else: rum.append(dict(o))
for r in rum:
    r["id"] = r["id"].replace("0.19999999999999998", "0.2").replace("0.5299999999999999", "0.53")
# Kameran står still inom tagningen: behåll bara nycklar där värdet ändras, plus scenens första och sista ruta.
kam = []
for k in D["kamera"]:
    if kam and k[1:] == kam[-1][1:]:
        if any(k[0] == s["ut"][1] - 1 for s in D["scener"]): kam.append(k)
        continue
    kam.append(k)
D["rum"], D["kamera"] = rum, kam
meta = dict(fps=D["fps"], n=D["antal_rutor"], w=D["bredd"], h=D["hojd"], sensor=D["sensor_mm"])
scener = [dict(id=s["id"], ut=s["ut"], personer=[p["id"] for p in s["personer"]],
               ankare=[p["ankare"] for p in s["personer"]]) for s in D["scener"]]

OP1 = r'''import bpy, json, math
M=json.loads(r"""__META__""")
RUM=json.loads(r"""__RUM__""")
KAM=json.loads(r"""__KAM__""")
SC=json.loads(r"""__SC__""")
REP=json.loads(r"""__REP__""")
PERS=json.loads(r"""__PERS__""")
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
'''

personer_data = {}
for sc in D["scener"]:
    for p in sc["personer"]:
        personer_data.setdefault(p["id"], []).append(dict(scen=sc["id"], ut=sc["ut"], rutor=p["rutor"]))
nyckel = {}
for sc in D["scener"]:
    a, b = sc["ut"]; k = {a, b - 1, (a + b) // 2}
    for r in D["repliker"]:
        if r["scen"] == sc["id"]:
            k |= {max(a, min(b - 1, r["a"])), max(a, min(b - 1, r["b"]))}
    nyckel[sc["id"]] = sorted(k)

OP2 = r'''import bpy, json, math
from mathutils import Vector
L=json.loads(r"""__LEDER__""")
P=json.loads(r"""__PDATA__""")
NY=json.loads(r"""__NYCKEL__""")
PERS=json.loads(r"""__PERS__""")
N=__N__
s=bpy.context.scene
IX={n:i for i,n in enumerate(L)}
BEN=[("c_spine0","c_spine2",.13),("c_spine2","c_neck",.12),("c_neck","c_head",.05),
("c_neck","l_uparm",.05),("c_neck","r_uparm",.05),("l_uparm","l_lowarm",.045),("l_lowarm","l_wrist",.035),
("r_uparm","r_lowarm",.045),("r_lowarm","r_wrist",.035),("c_spine0","l_upleg",.07),("c_spine0","r_upleg",.07),
("l_upleg","l_lowleg",.065),("l_lowleg","l_foot",.05),("l_foot","l_ball",.035),
("r_upleg","r_lowleg",.065),("r_lowleg","r_foot",.05),("r_foot","r_ball",.035)]
import bmesh
def cyl(namn):
    me=bpy.data.meshes.get(namn)
    if me: return me
    me=bpy.data.meshes.new(namn); bm=bmesh.new()
    bmesh.ops.create_cone(bm,cap_ends=True,segments=10,radius1=1,radius2=1,depth=1)
    bmesh.ops.rotate(bm,verts=bm.verts,cent=(0,0,0),matrix=__import__("mathutils").Matrix.Rotation(math.radians(-90),3,"X"))
    bmesh.ops.translate(bm,verts=bm.verts,vec=(0,0.5,0))
    bm.to_mesh(me); bm.free(); return me
def sfar():
    me=bpy.data.meshes.get("led_sfar_enhet")
    if me: return me
    me=bpy.data.meshes.new("led_sfar_enhet"); bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=1); bm.to_mesh(me); bm.free(); return me
def mat(h):
    nm="MP_"+h[1:]; m=bpy.data.materials.get(nm)
    if m: return m
    c=tuple((int(h[i:i+2],16)/255)**2.2 for i in (1,3,5))
    m=bpy.data.materials.new(nm); m.use_nodes=True; m.diffuse_color=(*c,1)
    b=next(x for x in m.node_tree.nodes if x.type=="BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value=(*c,1); return m
def synlighet(ob,intervall):
    ob.hide_render=True; ob.hide_viewport=True
    ob.keyframe_insert("hide_render",frame=0); ob.keyframe_insert("hide_viewport",frame=0)
    for a,b in intervall:
        for fr,dold in ((a,False),(b,True)):
            if fr>=N: continue
            ob.hide_render=dold; ob.hide_viewport=dold
            ob.keyframe_insert("hide_render",frame=fr); ob.keyframe_insert("hide_viewport",frame=fr)
def bygg(pid,niva,interp):
    bpy.context.preferences.edit.keyframe_new_interpolation_type=interp
    kol=bpy.data.collections.new(f"RIG_{pid}_{niva}"); s.collection.children.link(kol)
    kol["person"]=pid; kol["roll"]=PERS[pid]["roll"]; kol["niva"]=niva
    led={}
    for n in L:
        e=bpy.data.objects.new(f"RIG_{pid}_{niva}_{n}",None); e.empty_display_size=.03; kol.objects.link(e); led[n]=e
    ant=0
    for sp in P[pid]:
        rutor={r[0]:r[1:] for r in sp["rutor"]}
        fr_lista=sorted(rutor) if niva=="full" else [min(rutor,key=lambda u:abs(u-k)) for k in NY[sp["scen"]]]
        for u in sorted(set(fr_lista)):
            v=rutor[u]
            for n,i in IX.items():
                led[n].location=(v[3*i]/1000,v[3*i+1]/1000,v[3*i+2]/1000); led[n].keyframe_insert("location",frame=u)
            ant+=1
    for e in led.values():
        ad=e.animation_data
        fcs=ad.action.fcurves if ad and hasattr(ad.action,"fcurves") else []
        for fc in fcs:
            for kp in fc.keyframe_points: kp.interpolation=interp
    m=mat(PERS[pid]["farg"]); intervall=[sp["ut"] for sp in P[pid]]
    cm=bpy.data.meshes.get(f"led_cyl_{pid}")
    if cm is None:
        cm=cyl("led_cyl_enhet").copy(); cm.name=f"led_cyl_{pid}"; cm.materials.append(m)
    hm=bpy.data.meshes.get(f"led_sfar_{pid}")
    if hm is None:
        hm=sfar().copy(); hm.name=f"led_sfar_{pid}"; hm.materials.append(m)
    for a,b,r in BEN:
        ob=bpy.data.objects.new(f"RIG_{pid}_{niva}_ben_{a}_{b}",cm); kol.objects.link(ob)
        ob.scale=(r,1,r)
        cl=ob.constraints.new("COPY_LOCATION"); cl.target=led[a]
        st=ob.constraints.new("STRETCH_TO"); st.target=led[b]; st.rest_length=1.0; st.volume="NO_VOLUME"; st.keep_axis="PLANE_Z"
        synlighet(ob,intervall)
    h=bpy.data.objects.new(f"RIG_{pid}_{niva}_huvud",hm); kol.objects.link(h); h.scale=(.1,.1,.12)
    cl=h.constraints.new("COPY_LOCATION"); cl.target=led["c_head"]; cl.use_offset=False
    h.location=(0,0,0); synlighet(h,intervall)
    return kol,ant
ut={}
for pid in P:
    # Alternative rigs must live in a separate scene/file: GLB includes hidden collections.
    for niva,interp in (("full","LINEAR"),):
        kol,ant=bygg(pid,niva,interp); ut[f"{pid}_{niva}"]=ant
        if niva=="beat":
            kol.hide_render=True; kol.hide_viewport=True
s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.render.resolution_percentage=50
s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
for fr in (36,140,200,360):
    s.frame_set(fr); a=artifacts.file(name=f"kropp_f{fr:03d}.png",media_type="image/png"); s.render.filepath=str(a.path)
    bpy.ops.render.render(write_still=True); a.publish()
s.render.resolution_percentage=100
result={"nycklar":ut,"objekt":len(bpy.data.objects)}
'''

OP3 = r'''import bpy, time
s=bpy.context.scene; t=time.time()
s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.render.resolution_percentage=50
s.frame_start=__A__; s.frame_end=__B__
a=artifacts.file(name="animatik___A_____B__.mp4",media_type="video/mp4")
s.render.filepath=str(a.path)
s.render.image_settings.media_type="VIDEO"; s.render.image_settings.file_format="FFMPEG"
s.render.ffmpeg.format="MPEG4"; s.render.ffmpeg.codec="H264"; s.render.ffmpeg.constant_rate_factor="MEDIUM"
bpy.ops.render.render(animation=True); a.publish()
s.frame_start=0; s.frame_end=__N__-1; s.render.resolution_percentage=100
s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
result={"tid_s":round(time.time()-t,1)}
'''

op1 = (OP1.replace("__META__", J(meta)).replace("__RUM__", J(D["rum"])).replace("__KAM__", J(D["kamera"]))
       .replace("__SC__", J(scener)).replace("__REP__", J(D["repliker"])).replace("__PERS__", J(D["personer"])))
op2 = (OP2.replace("__LEDER__", J(D["leder"])).replace("__PDATA__", J(personer_data)).replace("__NYCKEL__", J(nyckel))
       .replace("__PERS__", J(D["personer"])).replace("__N__", str(D["antal_rutor"])))
(UT / "op1_rum_tidslinje.py").write_text(op1, encoding="utf-8")
(UT / "op2_kroppar.py").write_text(op2 + '\n' + (HIT/'export_gate.py').read_text(encoding='utf-8'), encoding="utf-8")
for a, b in ((0, 191), (192, D["antal_rutor"] - 1)):
    (UT / f"op3_animatik_{a}_{b}.py").write_text(OP3.replace("__A__", str(a)).replace("__B__", str(b)).replace("__N__", str(D["antal_rutor"])), encoding="utf-8")
for f in sorted(UT.iterdir()): print(f.name, f.stat().st_size)
