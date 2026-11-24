"""Steg 3: scenpaket -> ett bpy-skript som körs likadant i lokal Blender 5.2 och i 3D Jutsu (Blender 5.2).

  lokalt:  skriptet läser paketet från fil (full upplösning, ingen tokenkostnad)
  jutsu:   paketet bäddas in i skriptet (gallrat till --jutsu-steg för att hålla nere storleken)

Scenen som byggs:
  - en kollektion per rum (RUM_<id>) plus RUM_gemensamt; objekt med synlighetsnycklar ur paketet
  - en kamera per tagning (CAM_<tagning>), bunden till en markör: Blender byter kamera per tagning
  - blockingStudioTimeline med ett shot per tagning (Jutsus eget tidslinjeformat), hf_id på kamerorna
  - en docka per person (tomma objekt per led, cylindrar med Copy Location + Stretch To), synlig i sina tagningar
  - mening som scenegenskaper med prefix hagen_ (scenpaket-version, tagningar, rum, repliker, beslut, grindar)
  - kontrollbilder mitt i varje tagning, och valfritt en Workbench-film

Kör:  scen/.venv/Scripts/python.exe byggsten/brygga/emit_bpy.py byggsten/brygga/ut/notan/paket.json [--jutsu] [--jutsu-steg 3]
"""
import argparse, json
from pathlib import Path

KROPP = r'''
import bpy, json, math, os, sys, time, uuid
T0=time.time()
try:
    artifacts
except NameError:  # lokal värd: samma gränssnitt som Jutsus artifacts
    class _Mal:
        def __init__(s,p): s.path=p
        def publish(s): pass
    class _Art:
        def __init__(s,d): s.d=d; os.makedirs(d,exist_ok=True)
        def file(s,name,media_type=None): return _Mal(os.path.join(s.d,name))
    _argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    artifacts=_Art(_argv[1] if len(_argv)>1 else os.getcwd())
__DATA__
P=PAKET; s=bpy.context.scene
for o in list(bpy.data.objects):
    if o.name in ("Cube","Camera","Light"): bpy.data.objects.remove(o)
bpy.context.preferences.edit.keyframe_new_interpolation_type="LINEAR"
N=P["tidsbas"]["antal_rutor"]; FPS=P["tidsbas"]["fps"]
s.render.fps=int(round(FPS)); s.frame_start=0; s.frame_end=N-1
s.render.resolution_x=P["bild"]["bredd"]; s.render.resolution_y=P["bild"]["hojd"]
import bmesh
def mat(h,pre="M_"):
    nm=pre+h[1:]; m=bpy.data.materials.get(nm)
    if m: return m
    c=tuple((int(h[i:i+2],16)/255)**2.2 for i in (1,3,5))
    m=bpy.data.materials.new(nm); m.use_nodes=True; m.diffuse_color=(*c,1)
    b=next(x for x in m.node_tree.nodes if x.type=="BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value=(*c,1); b.inputs["Roughness"].default_value=0.7
    return m
def synlighet(ob,intervall):
    if intervall==[[0,N]]: return
    ob.hide_render=True; ob.hide_viewport=True
    ob.keyframe_insert("hide_render",frame=0); ob.keyframe_insert("hide_viewport",frame=0)
    for a,b in intervall:
        for fr,dold in ((a,False),(b,True)):
            if fr>=N: continue
            ob.hide_render=dold; ob.hide_viewport=dold
            ob.keyframe_insert("hide_render",frame=fr); ob.keyframe_insert("hide_viewport",frame=fr)
# --- rum och objekt ---
enhet=bpy.data.meshes.new("lada_enhet"); bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1.0); bm.to_mesh(enhet); bm.free()
kol={}
for rid in ["gemensamt"]+[r["id"] for r in P["rum"]]:
    k=bpy.data.collections.new("RUM_"+rid); s.collection.children.link(k); kol[rid]=k
    r=next((x for x in P["rum"] if x["id"]==rid),None)
    k["hagen_rum"]=rid; k["hagen_tagningar"]=json.dumps(r["tagningar"] if r else "alla"); k["hagen_huvudrum"]=(rid==P.get("huvudrum"))
pre={"golv":"ENV","vagg":"ENV"}; namn={}
for o in P["objekt"]:
    nm=f"{pre.get(o['typ'],'PRP')}_{o['id'].replace(':','_')}"; namn[nm]=namn.get(nm,0)+1
    if namn[nm]>1: nm=f"{nm}__{namn[nm]}"
    me=enhet.copy(); me.materials.append(mat(o["farg"]))
    ob=bpy.data.objects.new(nm,me); kol.get(o.get("rum","gemensamt"),kol["gemensamt"]).objects.link(ob)
    ob.location=o["pos"]; ob.rotation_euler=o["rot"]; ob.scale=o["matt"]
    ob["hagen_id"]=o["id"]; ob["hagen_bas"]=o["bas"]; ob["hagen_rum"]=o.get("rum","gemensamt"); ob["hagen_status"]=str(o.get("status"))
    synlighet(ob,o["synlig_ut"])
# --- kameror per tagning, markörer, Jutsus shots ---
from mathutils import Quaternion
for m_ in list(s.timeline_markers): s.timeline_markers.remove(m_)
kk=bpy.data.collections.new("CAM_tagningar"); s.collection.children.link(kk)
shots=[]
for t in P["tagningar"]:
    cd=bpy.data.cameras.new("CAM_"+t["id"]); cd.sensor_width=P["bild"]["sensor_mm"]; cd.sensor_fit="HORIZONTAL"
    c=bpy.data.objects.new("CAM_"+t["id"],cd); kk.objects.link(c); c.rotation_mode="QUATERNION"
    for k in t["kamera"]["nycklar"]:
        u,x,y,z,qw,qx,qy,qz,lins=k
        c.location=(x,y,z); c.rotation_quaternion=Quaternion((qw,qx,qy,qz)); cd.lens=lins
        if not t["kamera"]["statisk"]:
            c.keyframe_insert("location",frame=u); c.keyframe_insert("rotation_quaternion",frame=u); cd.keyframe_insert("lens",frame=u)
    c["hf_id"]=uuid.uuid4().hex; c["blockingStudioAspect"]=round(P["bild"]["bredd"]/P["bild"]["hojd"],4); c["hagen_tagning"]=t["id"]
    mk=s.timeline_markers.new(f"{t['id']} {'+'.join(p['id'] for p in t['personer'])}",frame=t["ut"][0]); mk.camera=c
    shots.append(dict(cameraId=c["hf_id"],start=round(t["ut"][0]/FPS,4),end=round(t["ut"][1]/FPS,4)))
s.camera=bpy.data.objects["CAM_"+P["tagningar"][0]["id"]]
s["blockingStudioTimeline"]=json.dumps(dict(version=1,duration=round(N/FPS,4),shots=shots))
for r in P["mening"].get("repliker",[]):
    s.timeline_markers.new(f"{r['id']} {r.get('talare')}: {r.get('text')}"[:63],frame=r["a"])
# --- personer ---
L=P["leder"]; IX={n:i for i,n in enumerate(L)}
BEN=[("c_spine0","c_spine2",.13),("c_spine2","c_neck",.12),("c_neck","c_head",.05),("c_neck","l_uparm",.05),("c_neck","r_uparm",.05),
("l_uparm","l_lowarm",.045),("l_lowarm","l_wrist",.035),("r_uparm","r_lowarm",.045),("r_lowarm","r_wrist",.035),
("c_spine0","l_upleg",.07),("c_spine0","r_upleg",.07),("l_upleg","l_lowleg",.065),("l_lowleg","l_foot",.05),("l_foot","l_ball",.035),
("r_upleg","r_lowleg",.065),("r_lowleg","r_foot",.05),("r_foot","r_ball",.035)]
def cyl():
    me=bpy.data.meshes.get("led_cyl_enhet")
    if me: return me
    me=bpy.data.meshes.new("led_cyl_enhet"); bm=bmesh.new()
    bmesh.ops.create_cone(bm,cap_ends=True,segments=10,radius1=1,radius2=1,depth=1)
    from mathutils import Matrix
    bmesh.ops.rotate(bm,verts=bm.verts,cent=(0,0,0),matrix=Matrix.Rotation(math.radians(-90),3,"X"))
    bmesh.ops.translate(bm,verts=bm.verts,vec=(0,0.5,0)); bm.to_mesh(me); bm.free(); return me
def sfar():
    me=bpy.data.meshes.get("led_sfar_enhet")
    if me: return me
    me=bpy.data.meshes.new("led_sfar_enhet"); bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=1); bm.to_mesh(me); bm.free(); return me
for pid,spar in P["rorelse"].items():
    info=P["personer"].get(pid,{}); farg=info.get("farg") or "#bbbbbb"
    k=bpy.data.collections.new(f"RIG_{pid}"); s.collection.children.link(k); k["hagen_person"]=pid; k["hagen_roll"]=str(info.get("roll"))
    led={}
    for n in L:
        e=bpy.data.objects.new(f"RIG_{pid}_{n}",None); e.empty_display_size=.03; k.objects.link(e); led[n]=e
    for sp in spar:
        for r in sp["rutor"]:
            u=r[0]; v=r[1:]
            for n,i in IX.items():
                led[n].location=(v[3*i]/1000,v[3*i+1]/1000,v[3*i+2]/1000); led[n].keyframe_insert("location",frame=u)
    cm=cyl().copy(); cm.name=f"led_cyl_{pid}"; cm.materials.append(mat(farg,"MP_"))
    hm=sfar().copy(); hm.name=f"led_sfar_{pid}"; hm.materials.append(mat(farg,"MP_"))
    iv=[sp["ut"] for sp in spar]
    for a,b,rr in BEN:
        if a not in led or b not in led: continue
        ob=bpy.data.objects.new(f"RIG_{pid}_ben_{a}_{b}",cm); k.objects.link(ob); ob.scale=(rr,1,rr)
        cl=ob.constraints.new("COPY_LOCATION"); cl.target=led[a]
        st=ob.constraints.new("STRETCH_TO"); st.target=led[b]; st.rest_length=1.0; st.volume="NO_VOLUME"; st.keep_axis="PLANE_Z"
        synlighet(ob,iv)
    h=bpy.data.objects.new(f"RIG_{pid}_huvud",hm); k.objects.link(h); h.scale=(.1,.1,.12)
    cl=h.constraints.new("COPY_LOCATION"); cl.target=led["c_head"]; synlighet(h,iv)
# --- ljus och värld ---
ld=bpy.data.lights.new("LGT_key","SUN"); ld.energy=2.5; l=bpy.data.objects.new("LGT_key",ld); s.collection.objects.link(l); l.rotation_euler=(math.radians(40),math.radians(-20),math.radians(60))
fd=bpy.data.lights.new("LGT_fill","POINT"); fd.energy=300; fd.shadow_soft_size=1.5; fl=bpy.data.objects.new("LGT_fill",fd); s.collection.objects.link(fl); fl.location=(-1.5,1.5,2.4)
s.world=s.world or bpy.data.worlds.new("World"); s.world.use_nodes=True
bg=next(x for x in s.world.node_tree.nodes if x.type=="BACKGROUND"); bg.inputs["Strength"].default_value=0.4
# --- mening och spårbarhet ---
s["hagen_scenpaket"]=P["schema"]; s["hagen_klipp"]=P["klipp"]["id"]; s["hagen_regler"]=P.get("regler","")
for nyckel in ("tagningar","rum"):
    s["hagen_"+nyckel]=json.dumps([{k:v for k,v in x.items() if k!="kamera"} for x in P[nyckel]],ensure_ascii=False)
s["hagen_mening"]=json.dumps({k:P["mening"].get(k) for k in ("repliker","roller","rum_relationer")},ensure_ascii=False)
s["hagen_beslut"]=json.dumps(P.get("beslut",[]),ensure_ascii=False)
s["hagen_proveniens"]=json.dumps(P.get("proveniens",{}),ensure_ascii=False)
BYGG_S=round(time.time()-T0,2)
# --- kontrollbilder ---
s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.render.resolution_percentage=__PROCENT__
s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
for t in P["tagningar"]:
    u=(t["ut"][0]+t["ut"][1])//2; s.frame_set(u)
    a=artifacts.file(name=f"kontroll_{t['id']}_{u:03d}.png",media_type="image/png"); s.render.filepath=str(a.path)
    bpy.ops.render.render(write_still=True); a.publish()
if __FILM__:
    a=artifacts.file(name="animatik.mp4",media_type="video/mp4"); s.render.filepath=str(a.path)
    s.render.image_settings.media_type="VIDEO"; s.render.image_settings.file_format="FFMPEG"
    s.render.ffmpeg.format="MPEG4"; s.render.ffmpeg.codec="H264"; s.render.ffmpeg.constant_rate_factor="MEDIUM"
    bpy.ops.render.render(animation=True); a.publish()
    s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
s.render.resolution_percentage=100
if "__SPARA__":
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(artifacts.d,"scen.blend")) if hasattr(artifacts,"d") else None
result={"bygg_s":BYGG_S,"tid_s":round(time.time()-T0,1),"objekt":len(bpy.data.objects),"kameror":len(P["tagningar"])}
print("RESULTAT",json.dumps(result))
'''


PERSONER_T1 = r'''# --- personer ---
# T1: armatur med fasta benlängder (median ur läsningen), riktad mot lederna och bakad till rotationsnycklar.
from mathutils import Vector, Matrix
L=P["leder"]; IX={n:i for i,n in enumerate(L)}
BEN1=[("backen","c_spine0","c_spine1",None,False,.12,"l_upleg"),("rygg1","c_spine1","c_spine2","backen",True,.125,None),
("rygg2","c_spine2","c_spine3","rygg1",True,.135,None),("brost","c_spine3","c_neck","rygg2",True,.14,"l_uparm"),
("nacke","c_neck","c_head","brost",True,.05,None),("huvud","c_head","huvud_upp","nacke",True,0,"nasa_mal")]
for sd in ("l","r"):
    BEN1+=[(f"nyckel_{sd}",f"{sd}_clavicle",f"{sd}_uparm","brost",False,.05,None),(f"overarm_{sd}",f"{sd}_uparm",f"{sd}_lowarm",f"nyckel_{sd}",True,.05,None),
    (f"underarm_{sd}",f"{sd}_lowarm",f"{sd}_wrist",f"overarm_{sd}",True,.04,None),(f"hand_{sd}",f"{sd}_wrist",f"{sd}_hand_mitt",f"underarm_{sd}",True,0,f"{sd}_index1"),
    (f"hoft_{sd}","c_spine0",f"{sd}_upleg","backen",False,.075,None),(f"lar_{sd}",f"{sd}_upleg",f"{sd}_lowleg",f"hoft_{sd}",True,.075,None),
    (f"skenben_{sd}",f"{sd}_lowleg",f"{sd}_foot",f"lar_{sd}",True,.055,None),(f"fot_{sd}",f"{sd}_foot",f"{sd}_ball",f"skenben_{sd}",True,0,None)]
BEN1=[b for b in BEN1 if b[1] in IX and b[2] in IX]
def kapsel(namn,L_,r):
    me=bpy.data.meshes.new(namn); bm=bmesh.new()
    bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=r)
    for v in bm.verts: v.co.y = v.co.y + (L_ if v.co.y>0 else 0)
    bm.to_mesh(me); bm.free(); return me
def lada(namn,sx,sy,sz,cy):
    me=bpy.data.meshes.new(namn); bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1.0)
    for v in bm.verts: v.co=Vector((v.co.x*sx,v.co.y*sy+cy,v.co.z*sz))
    bm.to_mesh(me); bm.free(); return me
def sfar_me(namn,r,c):
    me=bpy.data.meshes.new(namn); bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=14,v_segments=10,radius=r)
    for v in bm.verts: v.co=v.co+Vector(c)
    bm.to_mesh(me); bm.free(); return me

fotkoll={}
for pid,spar in P["rorelse"].items():
    info=P["personer"].get(pid,{}); farg=info.get("farg") or "#bbbbbb"; M_=mat(farg,"MP_")
    k=bpy.data.collections.new(f"RIG_{pid}"); s.collection.children.link(k); k["hagen_person"]=pid; k["hagen_roll"]=str(info.get("roll")); k["hagen_kropp"]="T1"
    rader=[(r[0],[Vector((r[1+3*i]/1000,r[2+3*i]/1000,r[3+3*i]/1000)) for i in range(len(L))]) for sp in spar for r in sp["rutor"]]
    rader.sort(key=lambda x:x[0]); U=[u for u,_ in rader]; ref=rader[0][1]
    langd={b[0]:sorted((x[IX[b[2]]]-x[IX[b[1]]]).length for _,x in rader)[len(rader)//2] for b in BEN1}
    ad=bpy.data.armatures.new(f"ARM_{pid}"); arm=bpy.data.objects.new(f"RIG_{pid}",ad); k.objects.link(arm)
    arm["hagen_person"]=pid; bpy.context.view_layer.objects.active=arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for namn,h,t,par,ans,rr,rulle in BEN1:
        eb=ad.edit_bones.new(namn)
        huvud=ad.edit_bones[par].tail.copy() if (par and ans) else ref[IX[h]].copy()
        rikt=(ref[IX[t]]-ref[IX[h]]).normalized(); eb.head=huvud; eb.tail=huvud+rikt*langd[namn]
        if par: eb.parent=ad.edit_bones[par]; eb.use_connect=ans
        if rulle and rulle in IX: eb.align_roll(ref[IX[rulle]]-huvud)
    bpy.ops.object.mode_set(mode="OBJECT")
    # mål: tomma objekt per led, nycklade vid läsningens rutor
    mal={}
    for n in L:
        e=bpy.data.objects.new(f"MAL_{pid}_{n}",None); k.objects.link(e); mal[n]=e
    for u,x in rader:
        for n in L: mal[n].location=x[IX[n]]; mal[n].keyframe_insert("location",frame=u)
    for namn,h,t,par,ans,rr,rulle in BEN1:
        pb=arm.pose.bones[namn]; pb.rotation_mode="QUATERNION"
        if par is None:
            c=pb.constraints.new("COPY_LOCATION"); c.target=mal[h]
        c=pb.constraints.new("DAMPED_TRACK"); c.target=mal[t]
        if rulle and rulle in mal:
            c=pb.constraints.new("LOCKED_TRACK"); c.target=mal[rulle]; c.track_axis="TRACK_Z"; c.lock_axis="LOCK_Y"
    # baka: läs posen med begränsningar, räkna fram lokala rotationer utan att lita på uppdateringsordning
    lagrat={}
    for u in U:
        s.frame_set(u); lagrat[u]={pb.name:pb.matrix.copy() for pb in arm.pose.bones}
    for pb in arm.pose.bones:
        for c in list(pb.constraints): pb.constraints.remove(c)
    forra={}
    for u in U:
        for namn,h,t,par,ans,rr,rulle in BEN1:
            pb=arm.pose.bones[namn]; Rb=pb.bone.matrix_local; Mb=lagrat[u][namn]
            if par: Rp=arm.pose.bones[par].bone.matrix_local; bas=(lagrat[u][par]@Rp.inverted()@Rb).inverted()@Mb
            else: bas=Rb.inverted()@Mb
            q=bas.to_quaternion()
            if namn in forra and forra[namn].dot(q)<0: q.negate()
            forra[namn]=q; pb.rotation_quaternion=q; pb.keyframe_insert("rotation_quaternion",frame=u)
            if par is None: pb.location=bas.to_translation(); pb.keyframe_insert("location",frame=u)
    for e in mal.values(): bpy.data.objects.remove(e)
    # kroppen: delar som sitter på benen (origo i benets huvud, Y längs benet)
    iv=[sp["ut"] for sp in spar]
    for namn,h,t,par,ans,rr,rulle in BEN1:
        Lb=arm.data.bones[namn].length
        if namn.startswith("huvud"):
            # huvudbenet pekar uppåt ur MHR-rotationen; Z-axeln mot näsan (LOCKED_TRACK)
            hc=Vector((0,Lb*.55,.015)); nc=Vector((0,Lb*.35,.105))
            me=sfar_me(f"me_{pid}_{namn}",.095,hc)
        elif namn.startswith("hand"): me=lada(f"me_{pid}_{namn}",.022,Lb*1.7,.085,Lb*.85)
        elif namn.startswith("fot"): me=lada(f"me_{pid}_{namn}",.09,Lb+.06,.06,Lb*.5)
        elif rr>0: me=kapsel(f"me_{pid}_{namn}",Lb,rr)
        else: continue
        me.materials.append(M_)
        ob=bpy.data.objects.new(f"RIG_{pid}_{namn}",me); k.objects.link(ob)
        ob.parent=arm; ob.parent_type="BONE"; ob.parent_bone=namn; ob.matrix_parent_inverse=Matrix.Translation((0,-Lb,0))
        synlighet(ob,iv)
        if namn.startswith("huvud"):
            me2=sfar_me(f"me_{pid}_nasa",.028,nc); me2.materials.append(mat("#d08060","MP_"))
            n2=bpy.data.objects.new(f"RIG_{pid}_nasa",me2); k.objects.link(n2)
            n2.parent=arm; n2.parent_type="BONE"; n2.parent_bone=namn; n2.matrix_parent_inverse=Matrix.Translation((0,-Lb,0)); synlighet(n2,iv)
    synlighet(arm,iv)
    # kontroll efter bygget: fotens lägsta höjd per tagning (golvlåset)
    for sp in spar:
        z=[]
        for u in [r[0] for r in sp["rutor"]][::3]:
            s.frame_set(u); z+=[(arm.matrix_world@arm.pose.bones[b].tail).z for b in ("fot_l","fot_r") if b in arm.pose.bones]
        fotkoll[f"{sp.get('tagning',sp.get('scen'))}:{pid}"]=round(min(z),3) if z else None
s["hagen_fotkoll"]=json.dumps(fotkoll)
'''


def tunna(p, tol_mm):
    """Behåll bara rutor där linjär interpolation mellan behållna rutor avviker mer än tol_mm (någon led)."""
    import numpy as np
    for spar in p["rorelse"].values():
        for sp in spar:
            R = sp["rutor"]
            if len(R) < 3: continue
            X = np.array([r[1:] for r in R], float); U = np.array([r[0] for r in R], float)
            keep = [0]
            i = 0
            while i < len(R) - 1:
                j = i + 2
                while j < len(R):
                    w = (U[i + 1:j] - U[i]) / (U[j] - U[i])
                    fel = np.abs(X[i] + w[:, None] * (X[j] - X[i]) - X[i + 1:j]).max()
                    if fel > tol_mm: break
                    j += 1
                i = j - 1; keep.append(i)
            sp["rutor"] = [R[k] for k in sorted(set(keep))]
    return p


def gallra(paket, steg):
    p = json.loads(json.dumps(paket))
    if steg == 0: p["rorelse"] = {}  # bara rum, kameror och mening (kroppen är redan bevisad i Jutsu)
    for spar in p["rorelse"].values():
        for sp in spar:
            a0, b0 = sp["ut"]
            sp["rutor"] = [r for r in sp["rutor"] if (r[0] - a0) % steg == 0 or r[0] == b0 - 1]
    p["mening"] = {k: p["mening"].get(k) for k in ("repliker", "roller", "rum_relationer")}
    p["beslut"] = [{k: b.get(k) for k in ("regel", "objekt", "person", "synlig_ut")} for b in p["beslut"]]
    p.pop("trohet", None)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paket"); ap.add_argument("--jutsu", action="store_true"); ap.add_argument("--jutsu-steg", type=int, default=3)
    ap.add_argument("--film", action="store_true"); ap.add_argument("--procent", type=int, default=50)
    ap.add_argument("--bara-kroppar", action="store_true", help="bara personerna, för en scen där rum och kameror redan finns")
    ap.add_argument("--kropp", default="t1", choices=["t0", "t1"], help="t0 = dockor av punkter, t1 = armatur")
    ap.add_argument("--jutsu-tol", type=float, default=0, help="mm: gallra kroppsrutor där linjär interpolation räcker")
    a = ap.parse_args()
    pk = Path(a.paket).resolve()
    if a.jutsu:
        p = gallra(json.loads(pk.read_text(encoding="utf-8")), a.jutsu_steg)
        if a.jutsu_tol > 0: p = tunna(p, a.jutsu_tol)
        data = 'PAKET=json.loads(r"""' + json.dumps(p, ensure_ascii=False, separators=(",", ":")) + '""")'
        ut = pk.with_name("jutsu_bygg.py")
    else:
        data = f'PAKET=json.load(open(_argv[0] if _argv else r"{pk}",encoding="utf-8"))'
        ut = pk.with_name("lokal_bygg.py")
    kropp = KROPP
    if a.kropp == "t1":
        i, j = kropp.index("# --- personer ---"), kropp.index("# --- ljus och värld ---")
        kropp = kropp[:i] + PERSONER_T1 + kropp[j:]
    kod = kropp.replace("__DATA__", data).replace("__PROCENT__", str(a.procent)).replace("__FILM__", "True" if a.film else "False")
    kod = kod.replace('if "__SPARA__":', "if True:" if not a.jutsu else "if False:")
    if a.bara_kroppar:
        # behåll huvudet (data, hjälpfunktioner), hoppa över rum, kameror, ljus och mening; behåll personer och kontrollbilder
        bort = [("# --- rum och objekt ---", "# --- personer ---"), ("# --- ljus och värld ---", "BYGG_S=")]
        for start, slut in bort:
            i, j = kod.index(start), kod.index(slut); kod = kod[:i] + kod[j:]
        kod = kod.replace('for o in list(bpy.data.objects):\n    if o.name in ("Cube","Camera","Light"): bpy.data.objects.remove(o)\n', "")
        kod = kod.replace('s.render.fps=int(round(FPS)); s.frame_start=0; s.frame_end=N-1\n', "")
        kod = kod.replace('s.render.resolution_x=P["bild"]["bredd"]; s.render.resolution_y=P["bild"]["hojd"]\n', "")
        ut = ut.with_name(ut.stem + "_kroppar.py")
    ut.write_text(kod, encoding="utf-8")
    print(ut, len(kod.encode()) // 1024, "KB")


if __name__ == "__main__":
    main()
