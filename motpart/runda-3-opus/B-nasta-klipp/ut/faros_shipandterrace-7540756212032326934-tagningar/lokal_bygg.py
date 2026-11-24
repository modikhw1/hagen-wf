
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
PAKET=json.load(open(_argv[0] if _argv else r"C:\Users\praiseworthy\Desktop\hagen-wf\motpart\runda-3-opus\B-nasta-klipp\ut\faros_shipandterrace-7540756212032326934-tagningar\paket.json",encoding="utf-8"))
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
    SYN=P.get("synlighet",{}); M_G=mat("#9a9a9a","MG_")
    def del_iv(h,t,grå):
        """Per ruta ur synlighetsmasken: färgad del där båda lederna har bildstöd; grå där de saknar stöd men bålen syns
        (DEL/HEL); dold där varken delen eller bålen syns (EXTREMITET/UTANFOR)."""
        ut=[]
        KX=[IX[n] for n in ("c_head","c_neck","l_uparm","r_uparm","c_spine2") if n in IX]
        for sp in spar:
            rle=sp.get("synlig_bitmask_rle")
            if not rle:
                if not grå: ut.append(sp["ut"])
                continue
            a0,b0=sp["ut"]
            for j,(u,bits) in enumerate(rle):
                slut=rle[j+1][0] if j+1<len(rle) else b0
                sedd=((bits>>IX[h])&1)==1 and ((bits>>IX.get(t,IX[h]))&1)==1
                bal=(((bits>>IX["c_head"])&1) or ((bits>>IX["c_neck"])&1)) and sum((bits>>k)&1 for k in KX)>=2
                visa=sedd if not grå else ((not sedd) and bal)
                if visa:
                    if ut and ut[-1][1]==u: ut[-1][1]=slut
                    else: ut.append([u,slut])
        return ut
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
        me2=me.copy(); me.materials.append(M_); me2.materials.append(M_G)
        ob=bpy.data.objects.new(f"RIG_{pid}_{namn}",me); k.objects.link(ob)
        ob.parent=arm; ob.parent_type="BONE"; ob.parent_bone=namn; ob.matrix_parent_inverse=Matrix.Translation((0,-Lb,0))
        synlighet(ob,del_iv(h,t,False) or [[N,N]])
        ob2=bpy.data.objects.new(f"RIG_{pid}_{namn}_antagen",me2); k.objects.link(ob2); ob2["hagen_status"]="antagen"
        ob2.parent=arm; ob2.parent_type="BONE"; ob2.parent_bone=namn; ob2.matrix_parent_inverse=Matrix.Translation((0,-Lb,0))
        synlighet(ob2,del_iv(h,t,True) or [[N,N]])
        if namn.startswith("huvud"):
            me2=sfar_me(f"me_{pid}_nasa",.028,nc); me2.materials.append(mat("#d08060","MP_"))
            n2=bpy.data.objects.new(f"RIG_{pid}_nasa",me2); k.objects.link(n2)
            n2.parent=arm; n2.parent_type="BONE"; n2.parent_bone=namn; n2.matrix_parent_inverse=Matrix.Translation((0,-Lb,0)); synlighet(n2,del_iv(h,t,False) or [[N,N]])
    synlighet(arm,iv)
    # kontroll efter bygget: fotens lägsta höjd per tagning (golvlåset)
    for sp in spar:
        z=[]
        for u in [r[0] for r in sp["rutor"]][::3]:
            s.frame_set(u); z+=[(arm.matrix_world@arm.pose.bones[b].tail).z for b in ("fot_l","fot_r") if b in arm.pose.bones]
        fotkoll[f"{sp.get('tagning',sp.get('scen'))}:{pid}"]=round(min(z),3) if z else None
s["hagen_fotkoll"]=json.dumps(fotkoll)
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
s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.render.resolution_percentage=50
s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
for t in P["tagningar"]:
    a0_,b0_=t["ut"]; T_=b0_-a0_
    for u in sorted({a0_+int(round(.1*(T_-1))),(a0_+b0_)//2,a0_+int(round(.9*(T_-1)))}):
        s.frame_set(u); s.camera=bpy.data.objects["CAM_"+t["id"]]
        a=artifacts.file(name=f"kontroll_{t['id']}_{u:04d}.png",media_type="image/png"); s.render.filepath=str(a.path)
        bpy.ops.render.render(write_still=True); a.publish()
if False:
    a=artifacts.file(name="animatik.mp4",media_type="video/mp4"); s.render.filepath=str(a.path)
    s.render.image_settings.media_type="VIDEO"; s.render.image_settings.file_format="FFMPEG"
    s.render.ffmpeg.format="MPEG4"; s.render.ffmpeg.codec="H264"; s.render.ffmpeg.constant_rate_factor="MEDIUM"
    bpy.ops.render.render(animation=True); a.publish()
    s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
s.render.resolution_percentage=100
if True:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(artifacts.d,"scen.blend")) if hasattr(artifacts,"d") else None
result={"bygg_s":BYGG_S,"tid_s":round(time.time()-T0,1),"objekt":len(bpy.data.objects),"kameror":len(P["tagningar"])}
print("RESULTAT",json.dumps(result))
