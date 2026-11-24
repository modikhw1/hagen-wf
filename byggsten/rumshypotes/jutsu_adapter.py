"""Jutsu-adaptern: recept (SceneTelemetry) till ett deterministiskt bpy-skript.

Samma recept ger samma skript tecken för tecken. Skriptet tar först bort allt med
egenskapen hagen_rh och bygger sedan om, så det kan köras igen på samma projekt.
Det går i Jutsu (scene_builder_3d_run_python) och i lokal Blender 5.2.

Visuell kodning efter källa:
- observed: blå, hel
- amodal_inferred: orange, hel
- relational_hypothesis: gul, halvgenomskinlig, med en zon (ZONE_) som visar osäkerheten

Konventioner enligt byggsten/jutsu/KONVENTIONER.md:
- Z upp, meter, rotation_mode XYZ
- sensor_fit HORIZONTAL
- en kamera och en markör per klipp, och blockingStudioTimeline
"""
from __future__ import annotations

import json
import uuid

from telemetri import Recept

FARG = {"observed": [0.18, 0.42, 0.85, 1.0], "amodal_inferred": [0.95, 0.55, 0.15, 1.0],
        "relational_hypothesis": [0.98, 0.82, 0.10, 0.45]}

KROPP = r'''
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
'''


def skript(recept: Recept, rendera: bool = True, upplosning=(288, 512)) -> str:
    d = recept.model_dump(mode="json", exclude={"logg", "regler"})
    d["_farg"] = FARG
    d["_rendera"] = rendera
    d["_upplosning"] = list(upplosning)
    d["_hf_id"] = {k.id: uuid.uuid5(uuid.NAMESPACE_URL, f"rumshypotes/{recept.klipp_id}/{k.id}").hex
                   for k in recept.kameror}
    data = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "# genererat av byggsten/rumshypotes/jutsu_adapter.py\nDATA = " + repr(data) + "\n" + KROPP
