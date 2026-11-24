# Konventionsprov i 3D Jutsu (Blender 5.2), test 04, 17 nov 2026.
# Körs som scene_builder_3d_run_python mot projektet byggsten-jutsu-konventioner-hello.
# Prövar: axlar och enheter, rotationsordning, kamerans projektion för 9:16
# (sensor_fit AUTO mot HORIZONTAL), projektion mot renderade pixlar, genomskinlig
# osäkerhetszon, etikett, egenskaper (hagen_*) och vad glTF-exporten bär.
import bpy, bmesh, json, math, os, struct, tempfile, time
import numpy as np
from mathutils import Matrix, Vector, Euler
from bpy_extras.object_utils import world_to_camera_view

t0 = time.time()
scene = bpy.context.scene
vl = bpy.context.view_layer
res = {}


def koll(namn):
    c = bpy.data.collections.get(namn)
    if c is None:
        c = bpy.data.collections.new(namn)
        scene.collection.children.link(c)
    return c


def material(namn, rgba, blandad=False):
    m = bpy.data.materials.get(namn) or bpy.data.materials.new(namn)
    m.diffuse_color = rgba
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    if nt is not None:
        p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p is not None:
            p.inputs['Base Color'].default_value = rgba
            p.inputs['Alpha'].default_value = rgba[3]
    if blandad:
        m.surface_render_method = 'BLENDED'
    return m


def lada(namn, matt, pos, rgba, koll_namn, rot_z_grad=0.0, blandad=False, egenskaper=None):
    me = bpy.data.meshes.new(namn)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(namn, me)
    koll(koll_namn).objects.link(ob)
    ob.location = pos
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = (0.0, 0.0, math.radians(rot_z_grad))
    ob.scale = matt
    ob.color = rgba
    me.materials.append(material('MAT_' + namn, rgba, blandad))
    for k, v in (egenskaper or {}).items():
        ob[k] = v
    return ob


# --- rum: golv (z = 0), bord, osäkerhetszon, axelmarkörer, etikett
me = bpy.data.meshes.new('ENV_golv')
me.from_pydata([(-4, -1, 0), (4, -1, 0), (4, 9, 0), (-4, 9, 0)], [], [(0, 1, 2, 3)])
me.update()
golv = bpy.data.objects.new('ENV_golv', me)
koll('ENV').objects.link(golv)
golv.color = (0.55, 0.55, 0.55, 1.0)
me.materials.append(material('MAT_golv', (0.55, 0.55, 0.55, 1.0)))

bord = lada('PRP_bord_hello', (1.0, 0.6, 0.75), (0.5, 3.0, 0.375), (1.0, 0.0, 0.0, 1.0), 'PRP',
            rot_z_grad=30.0,
            egenskaper={'hagen_telemetry': json.dumps({
                'klass': 'bord', 'geometry_source': 'observed', 'confidence': 0.9,
                'evidence_shots': ['s1'], 'dimensions_wdh': [1.0, 0.6, 0.75]})})
zon = lada('ZONE_hypotes_hello', (1.2, 1.2, 1.8), (-1.0, 4.5, 0.9), (1.0, 0.85, 0.0, 0.25), 'ZONE',
           blandad=True,
           egenskaper={'hagen_telemetry': json.dumps({
               'klass': 'person_zon', 'geometry_source': 'relational_hypothesis', 'confidence': 0.3})})
G = Vector((-1.5, 1.5, 0.0))
for namn, d, rgba in (('AX_x', (0.5, 0, 0.06), (1, 0, 1, 1)), ('AX_y', (0, 0.5, 0.06), (0, 1, 0, 1)),
                      ('AX_z', (0, 0, 0.5), (0, 0, 1, 1))):
    lada(namn, (0.12, 0.12, 0.12), G + Vector(d), rgba, 'HJALP')

cu = bpy.data.curves.new('LBL_bord_hello', 'FONT')
cu.body = 'bord_1 obs 0.9'
cu.size = 0.15
cu.align_x = 'CENTER'
lbl = bpy.data.objects.new('LBL_bord_hello', cu)
koll('HJALP').objects.link(lbl)
lbl.location = (0.5, 3.0, 1.1)
lbl.rotation_euler = (math.radians(90), 0, 0)
lbl.color = (0.1, 0.1, 0.1, 1)

# --- ljus
sol = bpy.data.objects.new('LGT_key', bpy.data.lights.new('LGT_key', 'SUN'))
sol.data.energy = 3.0
sol.rotation_euler = (math.radians(50), 0, math.radians(30))
koll('LGT').objects.link(sol)
fyll = bpy.data.objects.new('LGT_fill', bpy.data.lights.new('LGT_fill', 'POINT'))
fyll.data.energy = 200.0
fyll.location = (2.0, 1.0, 2.5)
koll('LGT').objects.link(fyll)
if scene.world is None:
    scene.world = bpy.data.worlds.new('WORLD')
scene.world.color = (0.2, 0.2, 0.2)

# --- kameror
camd = bpy.data.cameras.new('CAM_hello')
camd.lens = 26.0
camd.sensor_width = 36.0
cam = bpy.data.objects.new('CAM_hello', camd)
koll('CAM').objects.link(cam)
cam.location = (0.0, 0.0, 1.3)
mal = Vector((0.5, 3.0, 0.375))
cam.rotation_euler = (mal - cam.location).to_track_quat('-Z', 'Y').to_euler('XYZ')

topd = bpy.data.cameras.new('CAM_top')
topd.type = 'ORTHO'
topd.ortho_scale = 10.0
top = bpy.data.objects.new('CAM_top', topd)
koll('CAM').objects.link(top)
top.location = (0.0, 3.0, 15.0)
top.rotation_euler = (0, 0, 0)

scene['hagen_schema'] = 'hagen_scene_telemetry/0 konventionsprov'
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 576, 1024, 100
r.pixel_aspect_x = r.pixel_aspect_y = 1.0
scene.camera = cam
vl.update()

# --- rotationsordning: XYZ-euler mot Rz@Ry@Rx och Rx@Ry@Rz
rx, ry, rz = map(math.radians, (30.0, 20.0, 10.0))
tst = bpy.data.objects.new('TEST_rot', None)
scene.collection.objects.link(tst)
tst.rotation_euler = (rx, ry, rz)
vl.update()
M = tst.matrix_world.to_3x3()
Rx, Ry, Rz = (Matrix.Rotation(a, 3, ax) for a, ax in ((rx, 'X'), (ry, 'Y'), (rz, 'Z')))
diff = lambda A, B: max(abs(A[i][j] - B[i][j]) for i in range(3) for j in range(3))
res['rotation'] = {'mode': tst.rotation_mode, 'diff_RzRyRx': diff(M, Rz @ Ry @ Rx),
                   'diff_RxRyRz': diff(M, Rx @ Ry @ Rz)}
bpy.data.objects.remove(tst)
vl.update()


def projicera(ob):
    W, H = r.resolution_x, r.resolution_y
    pts = []
    for c in ob.bound_box:
        v = world_to_camera_view(scene, cam, ob.matrix_world @ Vector(c))
        pts.append((round(v.x * W, 3), round((1 - v.y) * H, 3), round(v.z, 4)))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return {'bbox': [min(xs), min(ys), max(xs), max(ys)], 'horn': pts}


proj = {}
for fit in ('AUTO', 'HORIZONTAL', 'VERTICAL'):
    camd.sensor_fit = fit
    vl.update()
    proj[fit] = {'angle_x': round(math.degrees(camd.angle_x), 3), 'angle_y': round(math.degrees(camd.angle_y), 3),
                 'bord': projicera(bord)['bbox']}
camd.sensor_fit = 'HORIZONTAL'
vl.update()
res['projektion'] = proj
res['bord_horn_px_horizontal'] = projicera(bord)['horn']
res['cam_matrix_world'] = [[round(cam.matrix_world[i][j], 6) for j in range(4)] for i in range(4)]
res['cam'] = {'lens': camd.lens, 'sensor_width': camd.sensor_width, 'sensor_fit': camd.sensor_fit,
              'shift': [camd.shift_x, camd.shift_y], 'res': [r.resolution_x, r.resolution_y]}
res['bord_horn_varld'] = [[round(x, 6) for x in (bord.matrix_world @ Vector(c))] for c in bord.bound_box]


# --- renderingar
def rendera(namn, kamera, w, h, motor):
    t = time.time()
    m = artifacts.file(name=namn, media_type='image/png')
    scene.camera = kamera
    r.engine = motor
    r.resolution_x, r.resolution_y = w, h
    r.filepath = str(m.path)
    r.image_settings.media_type = 'IMAGE'
    r.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    m.publish()
    return str(m.path), round(time.time() - t, 2)


sh = scene.display.shading
sh.light = 'FLAT'
sh.color_type = 'OBJECT'
for attr in ('show_shadows', 'show_cavity', 'show_object_outline', 'show_specular_highlight'):
    if hasattr(sh, attr):
        setattr(sh, attr, False)
scene.display.render_aa = 'OFF'
scene.view_settings.view_transform = 'Standard'

tider = {}
wb_path, tider['wb_576x1024'] = rendera('hello_cam_wb.png', cam, 576, 1024, 'BLENDER_WORKBENCH')
_, tider['wb_top_512'] = rendera('hello_top_wb.png', top, 512, 512, 'BLENDER_WORKBENCH')
scene.eevee.taa_render_samples = 4
_, tider['eevee_288x512'] = rendera('hello_cam_eevee.png', cam, 288, 512, 'BLENDER_EEVEE')
res['render_s'] = tider

# röda pixlar (bordet) i Workbench-bilden, rad 0 överst
img = bpy.data.images.load(wb_path, check_existing=False)
W, H = img.size
buf = np.empty(W * H * 4, dtype=np.float32)
img.pixels.foreach_get(buf)
px = buf.reshape(H, W, 4)[::-1]
mask = (px[..., 0] > 0.8) & (px[..., 1] < 0.2) & (px[..., 2] < 0.2)
ys, xs = np.nonzero(mask)
res['bord_px_render'] = ([int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
                         if xs.size else None)
res['bord_px_antal'] = int(xs.size)
bpy.data.images.remove(img)

# --- glTF: vad exporten bär (axlar, extras, alpha, kamera, etikett)
tmp = os.path.join(tempfile.gettempdir(), 'konv_probe.glb')
try:
    bpy.ops.export_scene.gltf(filepath=tmp, export_format='GLB', export_extras=True,
                              export_cameras=True, export_lights=True)
    with open(tmp, 'rb') as f:
        data = f.read()
    L = struct.unpack('<I', data[12:16])[0]
    gj = json.loads(data[20:20 + L])
    noder = {}
    for n in gj.get('nodes', []):
        noder[n.get('name')] = {k: n[k] for k in ('translation', 'rotation', 'scale', 'camera', 'mesh', 'extras')
                                if k in n}
    res['gltf'] = {
        'generator': gj.get('asset', {}).get('generator'),
        'noder': {k: noder[k] for k in noder if k in ('PRP_bord_hello', 'ZONE_hypotes_hello', 'CAM_hello',
                                                      'LBL_bord_hello', 'AX_z', 'LGT_key')},
        'alla_noder': sorted(noder),
        'material': [{'namn': m.get('name'), 'alphaMode': m.get('alphaMode', 'OPAQUE')}
                     for m in gj.get('materials', [])],
        'kameror': gj.get('cameras'),
        'scen_extras': (gj.get('scenes') or [{}])[0].get('extras'),
    }
except Exception as e:
    res['gltf'] = {'fel': repr(e)[:300]}

# återställ leveransläget
scene.camera = cam
r.engine = 'BLENDER_EEVEE'
r.resolution_x, r.resolution_y = 576, 1024
res['tid_s'] = round(time.time() - t0, 2)
result = res
