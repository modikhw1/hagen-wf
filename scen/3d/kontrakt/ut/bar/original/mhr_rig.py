"""Bygger en Blender-scen ur ingest-utdata: MHR-rigg per person i världsläge, trackad kamera, golv, ljud.
Körs headless:  blender -b --factory-startup --python scen/3d/ingest/mhr_rig.py -- <utmapp> <klipp.mp4> [--render]
Ingen retargeting: MHR:s 127 leder = FBX-riggens 127 ben (led i = ben i-1). Se scen/3d/klipp2/PROCESS.md.
"""
import sys, json, os, glob, time
import bpy, numpy as np
from mathutils import Matrix, Vector, Quaternion

F = np.diag([1.0, -1.0, -1.0])   # OpenCV-kamerarum = F @ MHR-modellrum
FBX = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'klipp2', 'sam3db', 'mhr', 'assets', 'lod3.fbx')
FARGER = ['#c9b7a5', '#8fa3b8', '#b89a8f', '#9fb48f', '#b0a0c0']


def _tq(x):
    return np.array(x[:3], float), Quaternion((float(x[6]), float(x[3]), float(x[4]), float(x[5])))


def _mat(hexf):
    h = hexf.lstrip('#'); rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    m = bpy.data.materials.new('farg_' + h); m.diffuse_color = (*rgb, 1)
    try:
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value = (*rgb, 1)
    except Exception:
        pass
    return m


def gravitation(V):
    u = V['upp'] / np.linalg.norm(V['upp']); z = np.array([0, 0, 1.0]); v = np.cross(u, z); c = float(np.dot(u, z))
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def person(pid, S, G, Rw, Cw, farg):
    fore = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=FBX)
    nya = [o for o in bpy.data.objects if o not in fore]
    arm = next(o for o in nya if o.type == 'ARMATURE'); mesher = [o for o in nya if o.type == 'MESH']
    for o in [o for o in nya if o.type == 'EMPTY']: bpy.data.objects.remove(o)
    arm.name = f'person:{pid}'
    for o in mesher:
        o.name = f'person:{pid}:kropp'; o.data.materials.clear(); o.data.materials.append(_mat(farg))
    B = list(arm.data.bones); W = arm.matrix_world
    P = np.array([_tq(S['rest'][i + 1])[0] for i in range(len(B))]); Q = np.array([list(W @ b.head_local) for b in B])
    mp, mq = P.mean(0), Q.mean(0); X, Y = P - mp, Q - mq
    U, Sv, Vt = np.linalg.svd(X.T @ Y); d = np.sign(np.linalg.det(Vt.T @ U.T)); R = Vt.T @ np.diag([1, 1, d]) @ U.T
    Rc = Matrix(R.tolist())
    C = {b.name: (Rc @ _tq(S['rest'][i + 1])[1].to_matrix()).inverted() @ (W @ b.matrix_local).to_3x3().normalized() for i, b in enumerate(B)}
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    Wr_i = W.to_3x3().normalized().inverted(); Wi = W.inverted(); pose, camt, kand = S['pose'], S['cam_t'], S['kand']
    synlig_fore = None
    for f in range(len(pose)):
        Q3 = G @ Rw[f] @ F; T = G @ (Cw[f] + Rw[f] @ camt[f]); Qm = Matrix(Q3.tolist())
        Marm = {}
        for i, b in enumerate(B):
            t, q = _tq(pose[f][i + 1])
            Marm[b.name] = Matrix.Translation(Wi @ Vector((Q3 @ (t / 100.0) + T).tolist())) @ (Wr_i @ (Qm @ q.to_matrix() @ C[b.name])).to_4x4()
        for b in B:
            bas = ((b.matrix_local.inverted() @ b.parent.matrix_local) @ Marm[b.parent.name].inverted() @ Marm[b.name]) if b.parent else b.matrix_local.inverted() @ Marm[b.name]
            pb = arm.pose.bones[b.name]; pb.matrix_basis = bas
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('scale', frame=f)
        # dölj personen där den inte syns i källan (utanför tidsfönstret för första och sista detektering)
        syn = bool(S['inom'][f])
        if syn != synlig_fore:
            for o in [arm] + [c for c in arm.children]:
                o.hide_render = o.hide_viewport = not syn; o.keyframe_insert('hide_render', frame=f); o.keyframe_insert('hide_viewport', frame=f)
            synlig_fore = syn
    return arm


def bygg_rum(ut, G):
    """Only room geometry. World-to-Blender rotation is shared with the existing rig."""
    path = os.path.join(ut, 'rum.json')
    if not os.path.exists(path): return None
    with open(path, encoding='utf-8') as f: room = json.load(f)
    floor = float(room['floor']['height'])
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, floor))
    g = bpy.context.active_object; g.name = 'golv'; g.data.materials.append(_mat('#5a554e'))
    for wall in room['walls']:
        centre = G @ np.array(wall['centre']); tangent = G @ np.array(wall['tangent'])
        up = np.array([0., 0., 1.]); half = tangent * wall['width'] / 2; vertical = up * wall['height'] / 2
        vertices = [centre - half - vertical, centre + half - vertical, centre + half + vertical, centre - half + vertical]
        mesh = bpy.data.meshes.new(wall['id']); mesh.from_pydata([v.tolist() for v in vertices], [], [(0, 1, 2, 3)]); mesh.update()
        obj = bpy.data.objects.new('rum:' + wall['id'], mesh); bpy.context.collection.objects.link(obj)
        obj.data.materials.append(_mat('#77716a'))
    for item in room['objects']:
        centre = G @ np.array(item['centre'])
        bpy.ops.mesh.primitive_cube_add(size=1, location=centre.tolist())
        obj = bpy.context.active_object; obj.name = 'rum:' + item['label'] + ':' + item['id']
        obj.dimensions = item['size']; obj.rotation_euler[2] = item['yaw']
        if item.get('top_slope'):
            # Keep the bottom on the floor; the measured upper rim can tilt relative to gravity.
            for vertex in obj.data.vertices:
                if vertex.co.z > 0: vertex.co.z += item['top_slope'] * vertex.co.x * item['size'][0] / item['size'][2]
        colour = '#347e77' if item['label'] == 'pool table' else '#a58b68' if item['label'] == 'bar counter' else '#777e87'
        obj.data.materials.append(_mat(colour)); obj['room_id'] = item['id']; obj['label'] = item['label']
    return floor


def bygg(ut, klipp, render=False):
    t0 = time.time()
    V = np.load(f'{ut}/varld.npz'); G = gravitation(V); Rw, Cw = V['kam_R'], V['kam_C']; N = len(Rw)
    meta = json.load(open(f'{ut}/meta.json'))
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    sc = bpy.context.scene; sc.name = 'ingest'; sc.render.fps = round(meta['fps']); sc.frame_start, sc.frame_end = 0, N - 1
    sc.render.resolution_x, sc.render.resolution_y = meta['bredd'], meta['hojd']
    cd = bpy.data.cameras.new('kamera'); cam = bpy.data.objects.new('kamera', cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36; cd.lens = float(np.load(sorted(glob.glob(f'{ut}/sekvens_*.npz'))[0])['fokal']) * 36 / meta['bredd']; cd.clip_start = .05
    for f in range(N):
        M = Matrix((G @ Rw[f] @ F).tolist()).to_4x4(); M.translation = Vector((G @ Cw[f]).tolist()); cam.matrix_world = M
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    fotz = []
    for k, sf in enumerate(sorted(glob.glob(f'{ut}/sekvens_*.npz'))):
        pid = os.path.basename(sf)[8:-4]; S = np.load(sf)
        arm = person(pid, S, G, Rw, Cw, FARGER[k % len(FARGER)])
        for f in range(0, N, 15):
            if S['inom'][f]:
                sc.frame_set(f); fotz += [(arm.matrix_world @ arm.pose.bones[n].head).z for n in ('l_ball', 'r_ball')]
    z = bygg_rum(ut, G)
    if z is None:
        z = float(V['golv_h']) if 'golv_h' in V else (float(np.percentile(fotz, 5)) if fotz else 0.0)
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, z)); g = bpy.context.active_object; g.name = 'golv'; g.data.materials.append(_mat('#5a554e'))
    if not sc.sequence_editor: sc.sequence_editor_create()
    sc.sequence_editor.strips.new_sound('ljud', klipp, 1, 0)
    try: sc.render.engine = 'BLENDER_WORKBENCH'
    except TypeError: pass
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_shadows = True
    sc.render.film_transparent = True; sc.render.resolution_percentage = 50; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(f'{ut}/scen.blend'))
    print(f'mhr_rig: {N} bildrutor, golv z={z:.3f}, {time.time() - t0:.1f} s', flush=True)
    if render:
        sc.render.filepath = os.path.abspath(f'{ut}/render/f'); bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    bygg(a[0], a[1], '--render' in a)
