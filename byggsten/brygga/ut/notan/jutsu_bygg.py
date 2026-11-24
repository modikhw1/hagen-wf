
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
PAKET=json.loads(r"""{"schema":"scenpaket/1","klipp":{"id":"notan","video":"scen/klipp/d-dialog-notan.mp4"},"tidsbas":{"fps":30.0,"antal_rutor":383,"regel":"Rutor är sanning; sekunder = ruta / fps. Intervall [a, b)."},"bild":{"bredd":576,"hojd":1024,"sensor_mm":36},"koordinater":"Blender: Z upp, meter; kvaternion (w,x,y,z); kroppens leder i heltal mm.","golv_z":0.0,"rum":[{"id":"berattat_rum","tagningar":["s1","s2","s3","s4","s5","s6"],"ut":[[0,73],[73,114],[114,171],[171,256],[256,281],[281,337]],"platser":["bord_1","stol_A","stol_B","staplats_C"],"status":"agare","beskrivning":"Rummet som tittaren uppfattar i S1–S6: A och B sitter mitt emot varandra vid ett gemensamt bord och grälar om notan. C står vid bordet och tittar på dem båda.","regel":null},{"id":"avslojat_rum","tagningar":["s7"],"ut":[[337,383]],"platser":["bord_2","stol_B_avslojad"],"status":"sedd","beskrivning":"S7 är poängen: B sitter vid ett eget bord en bit bort och känner inte A. Bilden är tagen från A:s bord med hennes burk i förgrunden.","regel":"S7 bryter det berättade rummet med avsikt. B flyttas i den tagningen till bord_2; A och bord_1 står kvar. Tagningen får inte användas som bevis för var B sitter i S1–S6."}],"huvudrum":"berattat_rum","objekt":[{"id":"golv","bas":"golv","typ":"golv","pos":[-1.1731,1.4105,-0.04],"rot":[0.0,0.0,-0.0121],"matt":[4.76,6.805,0.08],"farg":"#a8a299","status":"mall","rum":"gemensamt","synlig_ut":[[0,383]]},{"id":"vagg_bak","bas":"vagg_bak","typ":"vagg","pos":[-1.1318,4.8127,1.35],"rot":[0.0,0.0,-0.0121],"matt":[4.76,0.12,2.7],"farg":"#e5ddc7","status":"mall","rum":"gemensamt","synlig_ut":[[0,383]]},{"id":"vagg_sida","bas":"vagg_sida","typ":"vagg","pos":[1.2068,1.3816,1.35],"rot":[0.0,0.0,-0.0121],"matt":[0.12,6.805,2.7],"farg":"#e5ddc7","status":"mall","rum":"gemensamt","synlig_ut":[[0,383]]},{"id":"bord_1","bas":"bord_1","typ":"bord","pos":[-0.0,0.8287,0.6775],"rot":[0.0,0.0,-0.0121],"matt":[0.59,1.17,0.045],"farg":"#333638","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"bord_1:ben:-0.24:-0.53","bas":"bord_1","typ":"bord","pos":[-0.2465,0.3016,0.3275],"rot":[0.0,0.0,-0.0121],"matt":[0.045,0.045,0.655],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"bord_1:ben:-0.24:0.53","bas":"bord_1","typ":"bord","pos":[-0.2336,1.3616,0.3275],"rot":[0.0,0.0,-0.0121],"matt":[0.045,0.045,0.655],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"bord_1:ben:0.24:-0.53","bas":"bord_1","typ":"bord","pos":[0.2335,0.2958,0.3275],"rot":[0.0,0.0,-0.0121],"matt":[0.045,0.045,0.655],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"bord_1:ben:0.24:0.53","bas":"bord_1","typ":"bord","pos":[0.2464,1.3557,0.3275],"rot":[0.0,0.0,-0.0121],"matt":[0.045,0.045,0.655],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_A","bas":"stol_A","typ":"stol","pos":[-0.0003,-0.0004,0.4225],"rot":[0.0,0.0,0.0],"matt":[0.48,0.48,0.055],"farg":"#6d6252","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_A:ben:-0.185:-0.185","bas":"stol_A","typ":"stol","pos":[-0.1853,-0.1854,0.1975],"rot":[0.0,0.0,0.0],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_A:ben:-0.185:0.185","bas":"stol_A","typ":"stol","pos":[-0.1853,0.1846,0.1975],"rot":[0.0,0.0,0.0],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_A:ben:0.185:-0.185","bas":"stol_A","typ":"stol","pos":[0.1847,-0.1854,0.1975],"rot":[0.0,0.0,0.0],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_A:ben:0.185:0.185","bas":"stol_A","typ":"stol","pos":[0.1847,0.1846,0.1975],"rot":[0.0,0.0,0.0],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_A:rygg","bas":"stol_A","typ":"stol","pos":[-0.0003,-0.2154,0.68],"rot":[0.0,0.0,0.0],"matt":[0.48,0.055,0.43],"farg":"#6d6252","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_A:ryggstod:-0.2","bas":"stol_A","typ":"stol","pos":[-0.2003,-0.2154,0.55],"rot":[0.0,0.0,0.0],"matt":[0.035,0.035,0.35],"farg":"#6d6252","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_A:ryggstod:0.2","bas":"stol_A","typ":"stol","pos":[0.1997,-0.2154,0.55],"rot":[0.0,0.0,0.0],"matt":[0.035,0.035,0.35],"farg":"#6d6252","status":"mall","rum":"berattat_rum","synlig_ut":[[0,383]]},{"id":"stol_B","bas":"stol_B","typ":"stol","pos":[0.0005,1.67,0.4225],"rot":[0.0,0.0,-3.1416],"matt":[0.48,0.48,0.055],"farg":"#6d6252","status":"mall","rum":"berattat_rum","synlig_ut":[[0,337]]},{"id":"stol_B:ben:-0.185:-0.185","bas":"stol_B","typ":"stol","pos":[0.1855,1.855,0.1975],"rot":[0.0,0.0,-3.1416],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,337]]},{"id":"stol_B:ben:-0.185:0.185","bas":"stol_B","typ":"stol","pos":[0.1855,1.485,0.1975],"rot":[0.0,0.0,-3.1416],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,337]]},{"id":"stol_B:ben:0.185:-0.185","bas":"stol_B","typ":"stol","pos":[-0.1845,1.855,0.1975],"rot":[0.0,0.0,-3.1416],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,337]]},{"id":"stol_B:ben:0.185:0.185","bas":"stol_B","typ":"stol","pos":[-0.1845,1.485,0.1975],"rot":[0.0,0.0,-3.1416],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"berattat_rum","synlig_ut":[[0,337]]},{"id":"stol_B:rygg","bas":"stol_B","typ":"stol","pos":[0.0005,1.885,0.68],"rot":[0.0,0.0,-3.1416],"matt":[0.48,0.055,0.43],"farg":"#6d6252","status":"mall","rum":"berattat_rum","synlig_ut":[[0,337]]},{"id":"stol_B:ryggstod:-0.2","bas":"stol_B","typ":"stol","pos":[0.2005,1.885,0.55],"rot":[0.0,0.0,-3.1416],"matt":[0.035,0.035,0.35],"farg":"#6d6252","status":"mall","rum":"berattat_rum","synlig_ut":[[0,337]]},{"id":"stol_B:ryggstod:0.2","bas":"stol_B","typ":"stol","pos":[-0.1995,1.885,0.55],"rot":[0.0,0.0,-3.1416],"matt":[0.035,0.035,0.35],"farg":"#6d6252","status":"mall","rum":"berattat_rum","synlig_ut":[[0,337]]},{"id":"stol_B_avslojad","bas":"stol_B_avslojad","typ":"stol","pos":[0.0336,3.5985,0.4225],"rot":[0.0,0.0,-3.1537],"matt":[0.48,0.48,0.055],"farg":"#6d6252","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"stol_B_avslojad:ben:-0.185:-0.185","bas":"stol_B_avslojad","typ":"stol","pos":[0.2208,3.7812,0.1975],"rot":[0.0,0.0,-3.1537],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"stol_B_avslojad:ben:-0.185:0.185","bas":"stol_B_avslojad","typ":"stol","pos":[0.2163,3.4113,0.1975],"rot":[0.0,0.0,-3.1537],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"stol_B_avslojad:ben:0.185:-0.185","bas":"stol_B_avslojad","typ":"stol","pos":[-0.1492,3.7857,0.1975],"rot":[0.0,0.0,-3.1537],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"stol_B_avslojad:ben:0.185:0.185","bas":"stol_B_avslojad","typ":"stol","pos":[-0.1537,3.4157,0.1975],"rot":[0.0,0.0,-3.1537],"matt":[0.045,0.045,0.395],"farg":"#303537","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"stol_B_avslojad:rygg","bas":"stol_B_avslojad","typ":"stol","pos":[0.0362,3.8135,0.68],"rot":[0.0,0.0,-3.1537],"matt":[0.48,0.055,0.43],"farg":"#6d6252","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"stol_B_avslojad:ryggstod:-0.2","bas":"stol_B_avslojad","typ":"stol","pos":[0.2362,3.811,0.55],"rot":[0.0,0.0,-3.1537],"matt":[0.035,0.035,0.35],"farg":"#6d6252","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"stol_B_avslojad:ryggstod:0.2","bas":"stol_B_avslojad","typ":"stol","pos":[-0.1638,3.8159,0.55],"rot":[0.0,0.0,-3.1537],"matt":[0.035,0.035,0.35],"farg":"#6d6252","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"bord_2","bas":"bord_2","typ":"bord","pos":[0.0234,2.7635,0.7175],"rot":[0.0,0.0,-0.0121],"matt":[0.59,1.17,0.045],"farg":"#333638","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"bord_2:ben:-0.24:-0.53","bas":"bord_2","typ":"bord","pos":[-0.223,2.2365,0.3475],"rot":[0.0,0.0,-0.0121],"matt":[0.045,0.045,0.695],"farg":"#303537","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"bord_2:ben:-0.24:0.53","bas":"bord_2","typ":"bord","pos":[-0.2101,3.2964,0.3475],"rot":[0.0,0.0,-0.0121],"matt":[0.045,0.045,0.695],"farg":"#303537","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"bord_2:ben:0.24:-0.53","bas":"bord_2","typ":"bord","pos":[0.257,2.2307,0.3475],"rot":[0.0,0.0,-0.0121],"matt":[0.045,0.045,0.695],"farg":"#303537","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]},{"id":"bord_2:ben:0.24:0.53","bas":"bord_2","typ":"bord","pos":[0.2699,3.2906,0.3475],"rot":[0.0,0.0,-0.0121],"matt":[0.045,0.045,0.695],"farg":"#303537","status":"mall","rum":"avslojat_rum","synlig_ut":[[337,383]]}],"tagningar":[{"id":"s1","ut":[0,73],"personer":[{"id":"A","ankare":"stol_A"}],"kamera":{"statisk":true,"nycklar":[[0,-0.2453,1.4013,1.2,-0.08156,-0.06898,0.64203,0.7592,64.0]]}},{"id":"s2","ut":[73,114],"personer":[{"id":"B","ankare":"stol_B"}],"kamera":{"statisk":true,"nycklar":[[73,0.1499,-0.2534,1.2,0.73956,0.67071,0.03803,0.04193,97.89]]}},{"id":"s3","ut":[114,171],"personer":[{"id":"A","ankare":"stol_A"}],"kamera":{"statisk":true,"nycklar":[[114,-0.323,1.414,1.2,-0.10692,-0.09099,0.6417,0.754,64.0]]}},{"id":"s4","ut":[171,256],"personer":[{"id":"C","ankare":"staplats_C"}],"kamera":{"statisk":true,"nycklar":[[171,0.1341,0.2502,1.27,0.5788,0.58387,0.40429,0.40078,64.0]]}},{"id":"s5","ut":[256,281],"personer":[{"id":"B","ankare":"stol_B"}],"kamera":{"statisk":true,"nycklar":[[256,0.2167,0.2355,1.2,0.74943,0.65273,0.07282,0.0836,73.07]]}},{"id":"s6","ut":[281,337],"personer":[{"id":"A","ankare":"stol_A"}],"kamera":{"statisk":true,"nycklar":[[281,-0.1123,1.3904,1.2,-0.04758,-0.03924,0.63507,0.76999,64.0]]}},{"id":"s7","ut":[337,383],"personer":[{"id":"B","ankare":"stol_B_avslojad"}],"kamera":{"statisk":true,"nycklar":[[337,0.1922,0.2476,1.2,0.76223,0.64528,0.03307,0.03906,64.0]]}}],"personer":{"A":{"roll":"customer","farg":"#c9b7a5","hemplats":"stol_A"},"B":{"roll":"customer","farg":"#8fa3b8","hemplats":"stol_B"},"C":{"roll":"waiter","farg":"#b89a8f","hemplats":"staplats_C"}},"leder":["c_spine0","c_spine2","c_neck","c_head","l_uparm","l_lowarm","l_wrist","r_uparm","r_lowarm","r_wrist","l_upleg","l_lowleg","l_foot","r_upleg","r_lowleg","r_foot","l_ball","r_ball"],"rorelse_steg":1,"rorelse":{},"mening":{"repliker":[{"id":"r1","talare":"A","text":"Men vadå, menar du att du inte ska betala notan?","tagning":"s1","a":0,"b":65},{"id":"r2","talare":"B","text":"varför skulle jag ta notan?","tagning":"s2","a":71,"b":107},{"id":"r3","talare":"A","text":"för det är ju så gentlemen gör","tagning":"s3","a":115,"b":154},{"id":"r4","talare":"A","text":"eller liksom betala halva åtminstone?","tagning":"s4","a":184,"b":227},{"id":"r5","talare":"B","text":"varför skulle jag betala halva?","tagning":"s4","a":235,"b":272},{"id":"r6","talare":"A","text":"för jag trodde du var en riktig man","tagning":"s6","a":280,"b":327},{"id":"r7","talare":"B","text":"men jag känner inte ens dig?","tagning":"s7","a":335,"b":365}],"roller":{"A":{"beskrivning":"kvinna, långt brunt hår, svart kofta med vita knappar","tagningar":["S1","S3","S6"],"lage":"sitter"},"B":{"beskrivning":"man, mörkblå tröja med krage","tagningar":["S2","S5","S7"],"lage":"sitter"},"C":{"beskrivning":"servitör, svart keps (framåt), svart t-shirt med röd logotyp, mörka byxor","tagningar":["S4"],"lage":"står","hofthojd_m":0.93,"hofthojd_kalla":"Läst ur Lumas breddade S4 (synliga fötter)."},"regel":"Alla tre finns i rummet i alla tagningar S1–S6, även när bara en syns i bild."},"rum_relationer":{"berattat_rum":[{"vem":"A","mot":"B","relation":"mitt emot, över bordet","status":"agare"},{"vem":"C","mot":"bord_1","relation":"står vid bordets långsida, cirka 1,3 m från bordskanten, lika långt från A och B","status":"agare"},{"vem":"C","mot":["A","B"],"relation":"tittar växelvis på båda medan de grälar","status":"agare"}],"avslojat_rum":null}},"beslut":[{"regel":"plats_ur_deklaration","objekt":null,"person":"B","synlig_ut":null},{"regel":"R2_hemplats_ledig","objekt":"stol_B","person":"B","synlig_ut":[[0,337]]},{"regel":"R1_rum_per_tagning","objekt":"stol_B_avslojad","person":null,"synlig_ut":[[337,383]]},{"regel":"R1_rum_per_tagning","objekt":"bord_2","person":null,"synlig_ut":[[337,383]]}],"regler":"R1_rum_per_tagning, R2_hemplats_ledig","proveniens":{"skapad":"2026-11-14T13:26:43","av":"byggsten/brygga/samla.py","filer":{"plan":{"sokvag":"scen/3d/kontrakt/ut/notan_berattat/skymning/plan.json","sha256":"574e6193283d79e27c99539b8227772881b055c6ad78761a5f8645c34f3329f8"},"kalla":{"sokvag":"scen/3d/kontrakt/ut/notan_berattat/kalla_mobelintervall.json","sha256":"c57ca47293abfd8fe22357b474adfb1cb8c7e14696257bd3c44cecb8a03b631d"},"deklaration":{"sokvag":"scen/3d/ingest/ut/notan-tagningar/plats/deklaration.json","sha256":"377ce959dd4ca6c9a4e68da21421edc568adc53a6047ccdbca05d5d2f89cfe8d"}}}}""")
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
s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.render.resolution_percentage=50
s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
for t in P["tagningar"]:
    u=(t["ut"][0]+t["ut"][1])//2; s.frame_set(u)
    a=artifacts.file(name=f"kontroll_{t['id']}_{u:03d}.png",media_type="image/png"); s.render.filepath=str(a.path)
    bpy.ops.render.render(write_still=True); a.publish()
if False:
    a=artifacts.file(name="animatik.mp4",media_type="video/mp4"); s.render.filepath=str(a.path)
    s.render.image_settings.media_type="VIDEO"; s.render.image_settings.file_format="FFMPEG"
    s.render.ffmpeg.format="MPEG4"; s.render.ffmpeg.codec="H264"; s.render.ffmpeg.constant_rate_factor="MEDIUM"
    bpy.ops.render.render(animation=True); a.publish()
    s.render.image_settings.media_type="IMAGE"; s.render.image_settings.file_format="PNG"
s.render.resolution_percentage=100
if False:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(artifacts.d,"scen.blend")) if hasattr(artifacts,"d") else None
result={"bygg_s":BYGG_S,"tid_s":round(time.time()-T0,1),"objekt":len(bpy.data.objects),"kameror":len(P["tagningar"])}
print("RESULTAT",json.dumps(result))
