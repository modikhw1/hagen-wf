"""Blender: rendera kontrollager, blockout och djup från en scen/0.1-fil.

Körs med källans redan byggda scen.blend öppen:
  blender -b <Sx/scen.blend> -P rendera.py -- S1
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

HIT = Path(__file__).resolve().parent


def material(name, color, emission=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color[:3], color[3] if len(color) > 3 else 1.0)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    if emission:
        sh = n.new("ShaderNodeEmission")
        sh.inputs["Color"].default_value = m.diffuse_color
        sh.inputs["Strength"].default_value = 1.0
    else:
        sh = n.new("ShaderNodeBsdfDiffuse")
        sh.inputs["Color"].default_value = m.diffuse_color
        sh.inputs["Roughness"].default_value = 1.0
    m.node_tree.links.new(sh.outputs[0], out.inputs["Surface"])
    return m


def depth_material():
    m = bpy.data.materials.new("djup_nara_ljust")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    cam = n.new("ShaderNodeCameraData")
    mp = n.new("ShaderNodeMapRange")
    mp.inputs["From Min"].default_value = 0.25
    mp.inputs["From Max"].default_value = 8.0
    mp.inputs["To Min"].default_value = 1.0
    mp.inputs["To Max"].default_value = 0.02
    mp.clamp = True
    em = n.new("ShaderNodeEmission")
    l.new(cam.outputs["View Distance"], mp.inputs["Value"])
    l.new(mp.outputs["Result"], em.inputs["Color"])
    l.new(em.outputs[0], out.inputs["Surface"])
    return m


def set_mat(obj, mat):
    if obj.type != "MESH":
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def cube(name, centre_json, size_json, h, mat, yaw=0.0):
    x, y, z = centre_json
    sx, sy, sz = size_json
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, z, y - h))
    o = bpy.context.object
    o.name = name
    o.dimensions = (sx, sz, sy)
    o.rotation_euler[2] = math.radians(-yaw)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    set_mat(o, mat)
    return o


def line(name, a, b, z, mat, width=0.006):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = width
    cu.bevel_resolution = 0
    sp = cu.splines.new("POLY")
    sp.points.add(1)
    sp.points[0].co = (a[0], a[1], z, 1)
    sp.points[1].co = (b[0], b[1], z, 1)
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def evaluated_copy(obj, name):
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = bpy.data.meshes.new_from_object(ev)
    o = bpy.data.objects.new(name, mesh)
    o.matrix_world = obj.matrix_world.copy()
    return o


def satt_raw_huvudkropp(obj, key, cam_matrix):
    """Byt den historiskt golvskalade kroppen mot exakt keyframe-mesh.

    S4 använder Wan A-meshen (synliga ben) rigidpassad på original-SAM:s 13
    överkroppsleder. Därmed kommer benen från Wan utan att Wan-rummet används.
    """
    root = HIT.parents[2]
    orig = np.load(root / f"scen/3d/lasformat/luma-paket/poang/kropp/p/{0 if key == 'S1' else 1:04d}.npz")
    if key == "S4":
        src = np.load(root / "scen/3d/lasformat/ut/A/kropp/1/0042.npz")
        A = src["pred_keypoints_3d"][:13] + src["pred_cam_t"]
        B = orig["pred_keypoints_3d"][:13] + orig["pred_cam_t"]
        aa, bb = A - A.mean(0), B - B.mean(0)
        U, _, Vt = np.linalg.svd(aa.T @ bb)
        R = U @ Vt
        if np.linalg.det(R) < 0:
            U[:, -1] *= -1
            R = U @ Vt
        t = B.mean(0) - A.mean(0) @ R
        points = (src["pred_vertices"] + src["pred_cam_t"]) @ R + t
    else:
        points = orig["pred_vertices"] + orig["pred_cam_t"]
    # Den inbyggda FBX:en är LOD3 (4 899 hörn), medan SAM sparar 18 439.
    # Behåll därför LOD3-topologin/posen men passa dess robusta 3D-omfång till
    # den råa SAM-meshen. Det tar bort den historiska golvskalningen utan att
    # kräva en ny modellkörning eller en okänd vertexmappning mellan LOD:er.
    inv = cam_matrix.inverted()
    source = []
    for vert in obj.data.vertices:
        local = inv @ (obj.matrix_world @ vert.co)
        source.append([local.x, -local.y, -local.z])
    source = np.asarray(source)
    slo, shi = np.quantile(source, [0.002, 0.998], axis=0)
    tlo, thi = np.quantile(points, [0.002, 0.998], axis=0)
    scale = float(np.median((thi - tlo) / np.maximum(shi - slo, 1e-6)))
    cs, ct = (slo + shi) / 2, (tlo + thi) / 2
    fitted = (source - cs) * scale + ct
    print("RAW_FIT", key, "lod", len(source), "raw", len(points), "scale", round(scale, 5), "center_shift", np.round(ct - cs, 4).tolist())
    for vert, p in zip(obj.data.vertices, fitted):
        # OpenCV (x höger, y ned, z fram) -> Blender-kameralokalt
        # (x höger, y upp, kameran tittar längs -z) -> värld.
        vert.co = cam_matrix @ Vector((float(p[0]), float(-p[1]), float(-p[2])))
    obj.matrix_world = Matrix.Identity(4)


def configure_render(cam):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 576
    sc.render.resolution_y = 1024
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.film_transparent = False
    sc.camera = cam
    sc.render.use_file_extension = True
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.color_depth = "8"
    cam.data.clip_start = 0.04
    cam.data.clip_end = 50.0
    # Enkel, neutral blockoutbelysning.
    world = bpy.data.worlds.new("varld") if not sc.world else sc.world
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.09, 0.09, 0.09, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    ld = bpy.data.lights.new("stor_area", "AREA")
    ld.energy = 650
    ld.shape = "DISK"
    ld.size = 5.0
    lo = bpy.data.objects.new("stor_area", ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (0, -1.0, 3.0)
    lo.rotation_euler = (math.radians(18), 0, 0)


def render(path, film_transparent=False):
    sc = bpy.context.scene
    sc.render.film_transparent = film_transparent
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("RENDER", path)


def main(key):
    original = json.loads((HIT / f"{key}.json").read_text(encoding="utf-8"))
    changed = json.loads((HIT / f"{key}_andrad.json").read_text(encoding="utf-8"))
    local = original["kalla"]["lokal_ruta"]
    h = original["kamera"]["position"][1]
    sc = bpy.context.scene
    sc.frame_set(local)

    old_cam = sc.camera
    cam_matrix = old_cam.matrix_world.copy()
    cam_data = old_cam.data.copy()
    main_src = bpy.data.objects.get("person:1:kropp")
    if main_src is None:
        raise RuntimeError("Hittar inte person:1:kropp")
    body_meshes = [("huvudperson", evaluated_copy(main_src, "kropp:huvudperson"))]
    satt_raw_huvudkropp(body_meshes[0][1], key, cam_matrix)
    second_src = bpy.data.objects.get("person:4:kropp")
    if second_src is not None:
        body_meshes.append(("gast_vanster", evaluated_copy(second_src, "kropp:gast_vanster")))

    keep = {obj for _, obj in body_meshes}
    for obj in list(bpy.data.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    for _, obj in body_meshes:
        sc.collection.objects.link(obj)
    cam = bpy.data.objects.new("kamera", cam_data)
    sc.collection.objects.link(cam)
    cam.matrix_world = cam_matrix
    configure_render(cam)

    mats = {
        "body": material("kropp_ljusgra", (0.78, 0.78, 0.78, 1)),
        "body2": material("kropp_bakgrund", (0.52, 0.52, 0.52, 1)),
        "furniture": material("mobel_gra", (0.33, 0.35, 0.37, 1)),
        "prop": material("foremal_gra", (0.57, 0.59, 0.61, 1)),
        "wall": material("vagg_gra", (0.42, 0.43, 0.44, 1)),
        "floor": material("golv_gra", (0.47, 0.48, 0.49, 1)),
        "grid": material("rutnat_morkt", (0.075, 0.075, 0.075, 1)),
        "white": material("silhuett_vit", (1, 1, 1, 1), emission=True),
        "black": material("silhuett_skymmare", (0, 0, 0, 1), emission=True),
    }
    set_mat(body_meshes[0][1], mats["body"])
    if len(body_meshes) > 1:
        set_mat(body_meshes[1][1], mats["body2"])

    objects = {"body": [x[1] for x in body_meshes], "furniture": [], "props": [], "walls": [], "floor": [], "grid": [], "lights": []}
    for m in original["mobler"]:
        objects["furniture"].append(cube("mobel:" + m["id"], m["centrum"], m["storlek"], h, mats["furniture"], m.get("vridning_grader", 0)))
    for p in original["foremal"]:
        objects["props"].append(cube("foremal:" + p["id"], p["centrum"], p["storlek"], h, mats["prop"], p.get("vridning_grader", 0)))
    for w in original["vaggar"]:
        objects["walls"].append(cube("vagg:" + w["id"], w["centrum"], w["storlek"], h, mats["wall"], w.get("vridning_grader", 0)))
    objects["floor"].append(cube("golv", [0, -0.025, 3.0], [8.0, 0.05, 10.0], h, mats["floor"]))
    for x2 in [i * 0.5 for i in range(-8, 9)]:
        objects["grid"].append(line(f"grid_x_{x2:+.1f}", (x2, -2), (x2, 8), -h + 0.006, mats["grid"]))
    for y2 in [i * 0.5 for i in range(-4, 17)]:
        objects["grid"].append(line(f"grid_z_{y2:+.1f}", (-4, y2), (4, y2), -h + 0.006, mats["grid"]))
    objects["lights"] = [o for o in bpy.data.objects if o.type == "LIGHT"]
    all_visible = [o for v in objects.values() for o in v]
    base_matrices = {o.name: o.matrix_world.copy() for o in objects["body"]}
    regular_mats = {o.name: o.data.materials[0] for o in all_visible if o.type == "MESH" and len(o.data.materials)}
    guide = HIT / "guide"
    tmp = HIT / "_tmp"
    guide.mkdir(exist_ok=True)
    tmp.mkdir(exist_ok=True)

    def show_all():
        for o in all_visible:
            o.hide_render = False

    def regular():
        for o in all_visible:
            if o.type == "MESH" and o.name in regular_mats:
                set_mat(o, regular_mats[o.name])
        sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.09, 0.09, 0.09, 1)
        sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7

    def original_state():
        cam.matrix_world = cam_matrix.copy()
        for o in objects["body"]:
            o.matrix_world = base_matrices[o.name].copy()

    def changed_state():
        original_state()
        cam.matrix_world.translation += Vector((0, -1.0, 0))
        hip = changed["andring"]["huvudperson"]["pivot"]
        hp = original["personer"][0][hip]
        pivot = Vector((hp[0], hp[2], hp[1] - h))
        a = math.radians(-changed["andring"]["huvudperson"]["rotation_grader"])
        R = Matrix.Rotation(a, 4, "Z")
        objects["body"][0].matrix_world = Matrix.Translation(pivot) @ R @ Matrix.Translation(-pivot) @ base_matrices[objects["body"][0].name]

    # Originalkamera: referensblockout och referensdjup.
    show_all(); regular(); original_state()
    render(guide / f"{key}_blockout_orig.png")
    dm = depth_material()
    for o in all_visible:
        if o.type == "MESH": set_mat(o, dm)
    for o in objects["grid"] + objects["lights"]: o.hide_render = True
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    render(guide / f"{key}_djup_orig.png")

    # Ny kamera och vriden huvudperson.
    show_all(); regular(); changed_state()
    render(guide / f"{key}_blockout.png")
    for o in all_visible:
        if o.type == "MESH": set_mat(o, dm)
    for o in objects["grid"] + objects["lights"]: o.hide_render = True
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    render(guide / f"{key}_djup.png")

    # Kontrollager från originalkameran: ingen täckande golv/vägg, men kropp, lådor och rutnät.
    show_all(); regular(); original_state()
    for o in objects["floor"] + objects["walls"] + objects["lights"]: o.hide_render = True
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    render(tmp / f"kontroll_lager_{key}.png", film_transparent=True)

    # Binär huvudpersons-silhuett för IoU.
    for o in all_visible: o.hide_render = True
    objects["body"][0].hide_render = False
    set_mat(objects["body"][0], mats["white"])
    for o in objects["furniture"] + objects["props"]:
        o.hide_render = False
        set_mat(o, mats["black"])
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    render(tmp / f"silhuett_{key}.png")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1 or args[0] not in {"S1", "S4"}:
        raise SystemExit("Använd: ... -P rendera.py -- S1|S4")
    main(args[0])
