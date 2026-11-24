# genererat av byggsten/rumshypotes/jutsu_adapter.py
DATA = '{"_farg":{"amodal_inferred":[0.95,0.55,0.15,1.0],"observed":[0.18,0.42,0.85,1.0],"relational_hypothesis":[0.98,0.82,0.1,0.45]},"_hf_id":{"CAM_s1":"c2b1282ea298546ca064543487ba35c6","CAM_s2":"f4af1b6e97345c55876dacfca3d32d2a","CAM_s3":"c651bacacd6f5f0c8dc57af001fb34cc","CAM_s4":"fe1d786e0d885ed1a8c6c0c8fec7c325","CAM_s5":"994a0253108b58098a072e8dfefd859b","CAM_s6":"63c132e356cf54bab647370b718ff582","CAM_s7":"020bd349b1415616bfd0ed20b2ea96e3"},"_rendera":true,"_upplosning":[288,512],"fps":30.0,"kameror":[{"bild_px":[576,1024],"confidence_score":0.99,"hfov_deg":49.1,"id":"CAM_s1","klipp":"s1","position":[-0.2855,2.4688,1.089],"position_variance":[0.0,0.0,0.0064],"rotation":[84.4,0.0,0.989],"rutor":[0,60],"yaw_sigma_deg":0.06},{"bild_px":[576,1024],"confidence_score":0.455,"hfov_deg":48.7,"id":"CAM_s2","klipp":"s2","position":[0.1376,-1.94,1.124],"position_variance":[0.09108,0.22138,0.0064],"rotation":[83.2,0.0,-179.632],"rutor":[60,115],"yaw_sigma_deg":2.47},{"bild_px":[576,1024],"confidence_score":0.901,"hfov_deg":50.6,"id":"CAM_s3","klipp":"s3","position":[-0.241,2.4501,1.196],"position_variance":[0.00074,0.00376,0.0064],"rotation":[85.5,0.0,-1.444],"rutor":[115,170],"yaw_sigma_deg":2.21},{"bild_px":[576,1024],"confidence_score":0.02,"hfov_deg":56.5,"id":"CAM_s4","klipp":"s4","position":[0.5181,0.151,1.681],"position_variance":[0.09783,300.06642,0.0064],"rotation":[86.2,0.0,-92.852],"rutor":[170,215],"yaw_sigma_deg":2.97},{"bild_px":[576,1024],"confidence_score":0.455,"hfov_deg":50.1,"id":"CAM_s5","klipp":"s5","position":[-0.0119,-1.9997,1.082],"position_variance":[0.09091,0.22111,0.0064],"rotation":[82.6,0.0,-179.678],"rutor":[215,265],"yaw_sigma_deg":2.47},{"bild_px":[576,1024],"confidence_score":0.952,"hfov_deg":51.0,"id":"CAM_s6","klipp":"s6","position":[-0.3073,2.4953,1.146],"position_variance":[0.00053,0.00087,0.0064],"rotation":[83.3,0.0,1.577],"rutor":[265,310],"yaw_sigma_deg":2.2},{"bild_px":[576,1024],"confidence_score":0.873,"hfov_deg":65.1,"id":"CAM_s7","klipp":"s7","position":[-0.5461,3.9197,1.231],"position_variance":[0.00329,0.00661,0.0064],"rotation":[86.6,0.0,-177.397],"rutor":[310,400],"yaw_sigma_deg":2.83}],"klipp_id":"syntet_diner","ljus":{"azimut_deg":175.44,"hojd_deg":35.0,"sigma_deg":7.62},"noder":[{"confidence_score":0.911,"dimensions":[0.5,0.5,1.3],"evidence_shots":["s1","s3","s6"],"geometry_source":"observed","giltig_i":null,"id":"A","klass":"person","nyckel":"person:A","pose":"sittande","position":[-0.1703,3.6212,0.65],"position_variance":[0.00055,0.00313,0.0009],"rotation":[0.0,0.0,-189.53],"zon":null},{"confidence_score":0.455,"dimensions":[0.5,0.5,1.3],"evidence_shots":["s2","s5","s7"],"geometry_source":"observed","giltig_i":null,"id":"B","klass":"person","nyckel":"person:B","pose":"sittande","position":[0.0531,-3.0009,0.65],"position_variance":[0.09142,0.22138,0.0009],"rotation":[0.0,0.0,2.7],"zon":null},{"confidence_score":0.02,"dimensions":[0.5,0.35,1.75],"evidence_shots":["s4"],"geometry_source":"relational_hypothesis","giltig_i":null,"id":"C","klass":"person","nyckel":"person:C","pose":"staende","position":[2.2434,-0.041,0.875],"position_variance":[0.11748,300.06174,0.0009],"rotation":[0.0,0.0,84.05],"zon":{"centrum":[2.2434,0.0,0.875],"matt":[1.371,10.0908,1.75]}},{"confidence_score":0.936,"dimensions":[1.2,0.6,0.74],"evidence_shots":["s1","s3","s6","s7"],"geometry_source":"amodal_inferred","giltig_i":null,"id":"bord_1","klass":"bord","nyckel":"bord:tra","pose":null,"position":[-0.1804,2.8794,0.37],"position_variance":[0.00017,0.0015,0.0009],"rotation":[0.0,0.0,0.0],"zon":null},{"confidence_score":0.455,"dimensions":[1.2,0.6,0.74],"evidence_shots":["s2","s5","s7"],"geometry_source":"observed","giltig_i":null,"id":"bord_2","klass":"bord","nyckel":"bord:tra","pose":null,"position":[0.0549,-2.2939,0.37],"position_variance":[0.09062,0.22072,0.0009],"rotation":[0.0,0.0,180.0],"zon":null},{"confidence_score":0.942,"dimensions":[0.07,0.07,0.12],"evidence_shots":["s1","s6","s7"],"geometry_source":"observed","giltig_i":null,"id":"burk_A","klass":"foremal","nyckel":"foremal:burk_A","pose":null,"position":[-0.4839,2.9324,0.8],"position_variance":[0.00027,0.00117,0.0009],"rotation":[0.0,0.0,0.0],"zon":null},{"confidence_score":0.02,"dimensions":[0.9,0.08,2.05],"evidence_shots":["s4"],"geometry_source":"relational_hypothesis","giltig_i":null,"id":"dorr_1","klass":"dorr","nyckel":"dorr:tra","pose":null,"position":[3.1178,-0.1092,1.025],"position_variance":[0.07747,300.06608,0.0009],"rotation":[0.0,0.0,90.0],"zon":{"centrum":[2.7865,0.0,1.025],"matt":[0.9,10.0908,2.05]}}],"ram":"blender: meter, z upp, golv z=0, euler XYZ i grader","rum":{"granser":[-3.1118,3.1118,-5.1454,5.1454],"rumsnycklar":{"golv":"tra","tak":"betong","vagg":"beige"},"takhojd_m":3.28,"takhojd_sigma_m":0.106,"vaggar":[{"evidence_shots":["s7"],"geometry_source":"observed","lage_m":-3.1118,"sida":"W","sigma_m":0.22},{"evidence_shots":["s4","s7"],"geometry_source":"observed","lage_m":3.1118,"sida":"E","sigma_m":0.274},{"evidence_shots":["s2","s5","s7"],"geometry_source":"observed","lage_m":-5.1454,"sida":"S","sigma_m":0.474},{"evidence_shots":["s1","s3","s6"],"geometry_source":"observed","lage_m":5.1454,"sida":"N","sigma_m":0.123}]},"rutor":400,"sannolikhet":0.9012,"schema_id":"rumshypotes.recept/1","tro":"2 bord; A vid bord_1; B vid bord_2"}'

import bpy, bmesh, json, math
from mathutils import Vector
D = json.loads(DATA)
S = bpy.context.scene
for ob in [o for o in bpy.data.objects if o.get("hagen_rh")]:
    bpy.data.objects.remove(ob, do_unlink=True)
for samling in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
    for d in [d for d in samling if d.users == 0]:
        samling.remove(d)
F = D["_farg"]


def koll(n):
    c = bpy.data.collections.get(n)
    if c is None:
        c = bpy.data.collections.new(n)
        S.collection.children.link(c)
    return c


def mat(namn, rgba):
    m = bpy.data.materials.get(namn) or bpy.data.materials.new(namn)
    m.diffuse_color = rgba
    try:
        m.use_nodes = True
    except Exception:
        pass
    if m.node_tree is not None:
        p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if p is not None:
            p.inputs["Base Color"].default_value = rgba
            p.inputs["Alpha"].default_value = rgba[3]
    if rgba[3] < 1:
        m.surface_render_method = "BLENDED"
    return m


def nytt(namn, data, k, rgba, egen):
    ob = bpy.data.objects.new(namn, data)
    koll(k).objects.link(ob)
    ob.color = rgba
    ob["hagen_rh"] = 1
    for a, b in egen.items():
        ob[a] = b
    if data is not None and hasattr(data, "materials"):
        data.materials.append(mat("RH_" + namn, rgba))
    return ob


def lada(namn, c, dims, rot, rgba, k, egen):
    me = bpy.data.meshes.new(namn)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = nytt(namn, me, k, rgba, egen)
    ob.location = c
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = [math.radians(a) for a in rot]
    ob.scale = dims
    return ob


def person(namn, c, dims, rot, rgba, k, egen):
    w, d, h = dims
    me = bpy.data.meshes.new(namn)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=w / 2, radius2=w / 2 * 0.8, depth=h - 0.25)
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0, 0, -0.125))
    r = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.11)
    bmesh.ops.translate(bm, verts=r["verts"], vec=(0, 0, h / 2 - 0.11))
    n = bmesh.ops.create_cube(bm, size=0.07)
    bmesh.ops.translate(bm, verts=n["verts"], vec=(0, 0.12, h / 2 - 0.11))
    bm.to_mesh(me)
    bm.free()
    ob = nytt(namn, me, k, rgba, egen)
    ob.location = c
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def text(namn, s, c, k):
    cu = bpy.data.curves.new(namn, "FONT")
    cu.body = s
    cu.size = 0.22
    cu.align_x = "CENTER"
    ob = nytt(namn, cu, k, (0.08, 0.08, 0.08, 1.0), {})
    ob.location = c
    return ob


x0, x1, y0, y1 = D["rum"]["granser"]
T = D["rum"]["takhojd_m"]
me = bpy.data.meshes.new("ENV_golv")
me.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], [], [(0, 1, 2, 3)])
me.update()
nytt("ENV_golv", me, "RH_RUM", (0.80, 0.80, 0.78, 1.0), {"hagen_telemetry": json.dumps(D["rum"], sort_keys=True)})
VFARG = {"observed": (0.76, 0.79, 0.86, 1.0), "amodal_inferred": (0.93, 0.83, 0.72, 1.0)}
for v in D["rum"]["vaggar"]:
    s, L = v["sida"], v["lage_m"]
    if s in ("W", "E"):
        c, dims = (L + (-0.05 if s == "W" else 0.05), (y0 + y1) / 2, T / 2), (0.1, y1 - y0 + 0.2, T)
    else:
        c, dims = ((x0 + x1) / 2, L + (-0.05 if s == "S" else 0.05), T / 2), (x1 - x0 + 0.2, 0.1, T)
    lada("ENV_vagg_" + s, c, dims, (0, 0, 0), VFARG[v["geometry_source"]], "RH_RUM",
         {"hagen_telemetry": json.dumps(v, sort_keys=True)})
tak = lada("ENV_tak", ((x0 + x1) / 2, (y0 + y1) / 2, T + 0.03), (x1 - x0 + 0.2, y1 - y0 + 0.2, 0.06), (0, 0, 0),
           (0.90, 0.90, 0.90, 1.0), "RH_TAK", {"geometry_source": "amodal_inferred"})
PREFIX = {"person": "HERO_", "bord": "PRP_", "foremal": "PRP_", "stol": "PRP_", "dorr": "ENV_", "fonster": "ENV_"}
for n in D["noder"]:
    rgba = F[n["geometry_source"]]
    egen = {"hagen_telemetry": json.dumps(n, sort_keys=True)}
    namn = PREFIX.get(n["klass"], "PRP_") + n["id"].replace("@", "_")
    koll_namn = "RH_" + n["geometry_source"].upper()
    if n["klass"] == "person":
        person(namn, n["position"], n["dimensions"], n["rotation"], rgba, koll_namn, egen)
    else:
        lada(namn, n["position"], n["dimensions"], n["rotation"], rgba, koll_namn, egen)
    if n.get("zon"):
        z = n["zon"]
        lada("ZONE_" + n["id"].replace("@", "_"), z["centrum"], z["matt"], (0, 0, 0), (0.98, 0.82, 0.10, 0.22),
             "RH_ZON", {"hagen_telemetry": json.dumps(z, sort_keys=True)})
    text("LBL_" + n["id"].replace("@", "_"), "%s %.2f" % (n["id"], n["confidence_score"]),
         (n["position"][0], n["position"][1], 2.3), "RH_ETIKETT")
fps = D["fps"]
S.render.fps = int(round(fps))
S.render.fps_base = round(fps) / fps
S.frame_start, S.frame_end = 0, D["rutor"] - 1
for m in list(S.timeline_markers):
    if m.name.startswith("RH "):
        S.timeline_markers.remove(m)
shots = []
W, H = D["kameror"][0]["bild_px"] if D["kameror"] else (576, 1024)
for c in D["kameror"]:
    cd = bpy.data.cameras.new(c["id"])
    cd.sensor_width = 36.0
    cd.sensor_fit = "HORIZONTAL"
    cd.lens = 18.0 / math.tan(math.radians(c["hfov_deg"]) / 2)
    ob = nytt(c["id"], cd, "RH_KAMERA", (0.2, 0.2, 0.2, 1.0), {"hagen_telemetry": json.dumps(c, sort_keys=True)})
    ob.location = c["position"]
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = [math.radians(a) for a in c["rotation"]]
    ob["hf_id"] = D["_hf_id"][c["id"]]
    ob["blockingStudioAspect"] = round(c["bild_px"][0] / c["bild_px"][1], 4)
    mk = S.timeline_markers.new("RH " + c["klipp"], frame=c["rutor"][0])
    mk.camera = ob
    shots.append(dict(cameraId=ob["hf_id"], start=round(c["rutor"][0] / fps, 4), end=round(c["rutor"][1] / fps, 4)))
S["blockingStudioTimeline"] = json.dumps(dict(version=1, duration=round(D["rutor"] / fps, 4), shots=shots))
S["hagen_rumshypotes"] = json.dumps({k: D[k] for k in ("schema_id", "klipp_id", "tro", "sannolikhet", "ram")},
                                    sort_keys=True)
S.render.resolution_x, S.render.resolution_y, S.render.resolution_percentage = W, H, 100
if D["kameror"]:
    S.camera = bpy.data.objects[D["kameror"][0]["id"]]
if D.get("ljus"):
    a, e = math.radians(D["ljus"]["azimut_deg"]), math.radians(D["ljus"]["hojd_deg"])
    sol = nytt("LGT_key", bpy.data.lights.new("LGT_key", "SUN"), "RH_LJUS", (1, 1, 1, 1), {})
    sol.data.energy = 3.0
    sol.rotation_mode = "QUATERNION"
    sol.rotation_quaternion = Vector((-math.cos(e) * math.cos(a), -math.cos(e) * math.sin(a), -math.sin(e))).to_track_quat("-Z", "Y")
if S.world is None:
    S.world = bpy.data.worlds.new("WORLD")
S.world.color = (0.25, 0.25, 0.25)
bpy.context.view_layer.update()
result = {"objekt": len([o for o in bpy.data.objects if o.get("hagen_rh")]), "kameror": len(D["kameror"])}

if D["_rendera"]:
    import time
    sh = S.display.shading
    sh.light = "STUDIO"
    sh.color_type = "OBJECT"
    S.display.render_aa = "FXAA"
    S.view_settings.view_transform = "Standard"
    S.render.engine = "BLENDER_WORKBENCH"
    tider = {}

    def rendera(namn, kam, w, h):
        t = time.time()
        a = artifacts.file(name=namn, media_type="image/png")
        S.camera = kam
        S.render.resolution_x, S.render.resolution_y = w, h
        S.render.filepath = str(a.path)
        S.render.image_settings.media_type = "IMAGE"
        S.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
        a.publish()
        tider[namn] = round(time.time() - t, 2)

    bundna = [(m, m.camera) for m in S.timeline_markers]   # markörer styr annars kameran vid rendering
    for m, _ in bundna:
        m.camera = None
    td = bpy.data.cameras.new("RH_CAM_topp")
    td.type = "ORTHO"
    bredd, djup = x1 - x0 + 1.0, y1 - y0 + 1.0
    td.ortho_scale = max(bredd, djup)
    topp = nytt("RH_CAM_topp", td, "RH_KAMERA", (0.2, 0.2, 0.2, 1.0), {})
    topp.location = ((x0 + x1) / 2, (y0 + y1) / 2, T + 10.0)
    tw = 512
    th_ = int(round(tw * djup / bredd / 2)) * 2 if djup > bredd else tw
    tak.hide_render = True
    for ob in koll("RH_ETIKETT").objects:
        ob.hide_render = False
    rendera("topp.png", topp, tw if djup > bredd else int(round(tw * bredd / djup / 2)) * 2, th_)
    tak.hide_render = False
    for ob in koll("RH_ETIKETT").objects:
        ob.hide_render = True
    uw, uh = D["_upplosning"]
    for c in D["kameror"][:7]:
        rendera(c["klipp"] + ".png", bpy.data.objects[c["id"]], uw, uh)
    for ob in koll("RH_ETIKETT").objects:
        ob.hide_render = False
    for m, c in bundna:
        m.camera = c
    S.camera = bpy.data.objects[D["kameror"][0]["id"]] if D["kameror"] else S.camera
    S.render.resolution_x, S.render.resolution_y = W, H
    result["render_s"] = tider
