"""MHR-sekvens (från skelett_sekvens.py) -> nycklad MHR-FBX-rigg i Blender + kamera med källans utsnitt (1:1).

Världen är "kamerafast": kameran står still i origo och personen placeras med SAM 3D Bodys cam_t per bildruta.
Utsnittet blir då identiskt med källan. Världsplacering med COLMAP-kameran är ett separat steg.
Ingen retargeting: MHR:s 127 leder är riggens 127 ben (led i = ben i-1, led 0 = armaturen).

Via MCP:
    ns = runpy.run_path(r'...\\mhr_blender.py')
    ns['importera'](fbx, sekvens_npz)   # rigg + kamera + korrektion (en gång)
    ns['nyckla'](0, 120); ns['nyckla'](120, 240); ...   # i omgångar (MCP timeout ~2 min)
"""
import bpy, numpy as np
from mathutils import Matrix, Vector, Quaternion

NS = bpy.app.driver_namespace
F = np.diag([1.0, -1.0, -1.0])     # OpenCV-kamerarum = F @ MHR-modellrum (verifierat mot pred_vertices, fel 3e-8)


def _tq(x):
    return np.array(x[:3], float), Quaternion((float(x[6]), float(x[3]), float(x[4]), float(x[5])))


def importera(fbx, sekvens, namn='mhr', bredd=1080, hojd=1920, fps=30, dolda_fotter=None):
    # GOLV2: läs genom den metriska läsgränsen (cam_t före historiskt golv/kontakt).
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ingest'))
    from metrisk import las
    S = las(sekvens,dolda_fotter)
    sc = bpy.data.scenes.get(namn) or bpy.data.scenes.new(namn); bpy.context.window.scene = sc
    sc.render.fps = fps; sc.render.resolution_x, sc.render.resolution_y = bredd, hojd
    sc.frame_start, sc.frame_end = 0, len(S['pose']) - 1
    fore = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx)
    for o in [o for o in bpy.data.objects if o not in fore and o.type == 'EMPTY']: bpy.data.objects.remove(o)
    arm = next(o for o in bpy.data.objects if o not in fore and o.type == 'ARMATURE')
    mesher=[o for o in bpy.data.objects if o not in fore and o.type=='MESH']
    kroppsskala=float(S.get('dold_fot_skala',1.))
    if abs(kroppsskala-1.)>1e-12:
        scale=Matrix.Scale(kroppsskala,4);arm.data.transform(scale)
        for o in mesher:o.data.transform(scale)
        arm['dolda_fotter_status']='antagen';arm['dolda_fotter_faktor']=kroppsskala
    B = list(arm.data.bones); W = arm.matrix_world
    # MHR-modellrum (cm, Y upp) -> Blender-världen (m, Z upp): Kabsch på vilans ledpositioner
    P = np.array([_tq(S['rest'][i + 1])[0] for i in range(len(B))]); Q = np.array([list(W @ b.head_local) for b in B])
    mp, mq = P.mean(0), Q.mean(0); X, Y = P - mp, Q - mq
    U, Sv, Vt = np.linalg.svd(X.T @ Y); d = np.sign(np.linalg.det(Vt.T @ U.T)); R = Vt.T @ np.diag([1, 1, d]) @ U.T; s = Sv.sum() / (X ** 2).sum()
    Rc = Matrix(R.tolist())
    C = {b.name: (Rc @ _tq(S['rest'][i + 1])[1].to_matrix()).inverted() @ (W @ b.matrix_local).to_3x3().normalized() for i, b in enumerate(B)}
    # kamera i origo (i modellrummet): lokala X, Y, Z = modellens X, Y, Z
    cd = bpy.data.cameras.new(namn + '_kam'); cam = bpy.data.objects.new(namn + '_kam', cd); sc.collection.objects.link(cam)
    cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36; cd.lens = float(S['fokal']) * 36 / bredd; cd.clip_start = .05
    M = Rc.to_4x4(); M.translation = Vector((s * (R @ (np.zeros(3) - mp)) + mq).tolist()); cam.matrix_world = M; sc.camera = cam
    NS['mhr'] = dict(arm=arm.name, R=R, s=s, mp=mp, mq=mq, C=C, S=dict(pose=S['pose'], cam_t=S['cam_t']))
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    return arm.name, len(B), len(S['pose'])


def nyckla(f0, f1):
    k = NS['mhr']; arm = bpy.data.objects[k['arm']]; B = list(arm.data.bones); W = arm.matrix_world
    R, s, mp, mq, C = k['R'], k['s'], k['mp'], k['mq'], k['C']; Rc = Matrix(R.tolist())
    Wr_i = W.to_3x3().normalized().inverted(); Wi = W.inverted(); pose, camt = k['S']['pose'], k['S']['cam_t']
    for f in range(f0, min(f1, len(pose))):
        skift = F @ camt[f] * 100.0          # personen flyttas framför den stillastående kameran (cm, modellrum)
        Marm = {}
        for i, b in enumerate(B):
            t, q = _tq(pose[f][i + 1])
            rot = Wr_i @ (Rc @ q.to_matrix() @ C[b.name])
            pos = Wi @ Vector((s * (R @ (t + skift - mp)) + mq).tolist())
            Marm[b.name] = Matrix.Translation(pos) @ rot.to_4x4()
        for b in B:
            if b.parent:
                bas = (b.matrix_local.inverted() @ b.parent.matrix_local) @ Marm[b.parent.name].inverted() @ Marm[b.name]
            else:
                bas = b.matrix_local.inverted() @ Marm[b.name]
            pb = arm.pose.bones[b.name]; pb.matrix_basis = bas
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('scale', frame=f)
    return f1


def varld(varldfil, namn_kam='mhr_varldkam'):
    """Byt till världsläge: COLMAP-kamerans bana (metrisk via k) + personen i samma värld. Upp-axeln roteras till +Z.
    Anropa efter importera(); sedan nyckla_varld(f0, f1) i omgångar."""
    V = np.load(varldfil); k = NS['mhr']
    u = V['upp'] / np.linalg.norm(V['upp']); z = np.array([0, 0, 1.0])
    v = np.cross(u, z); c = float(np.dot(u, z)); vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    G = np.eye(3) + vx + vx @ vx / (1 + c)          # roterar upp -> +Z
    # flytta så att personens första position står i origo på golvet (x, y), behåll höjden
    k['G'] = G; k['V'] = dict(R=V['kam_R'], C=V['kam_C'])
    sc = bpy.context.scene; cam = bpy.data.objects[sc.camera.name]
    k['kam'] = cam.name
    return np.round(G, 3).tolist()


def nyckla_varld(f0, f1):
    k = NS['mhr']; arm = bpy.data.objects[k['arm']]; B = list(arm.data.bones); W = arm.matrix_world
    C = k['C']; G = k['G']; Rw, Cw = k['V']['R'], k['V']['C']; pose, camt = k['S']['pose'], k['S']['cam_t']
    Wr_i = W.to_3x3().normalized().inverted(); Wi = W.inverted(); cam = bpy.data.objects[k['kam']]
    for f in range(f0, min(f1, len(pose))):
        Q = G @ Rw[f] @ F; T = G @ (Cw[f] + Rw[f] @ camt[f])           # modell (m) -> Blender-värld
        Qm = Matrix(Q.tolist())
        Marm = {}
        for i, b in enumerate(B):
            t, q = _tq(pose[f][i + 1])
            rot = Wr_i @ (Qm @ q.to_matrix() @ C[b.name])
            Marm[b.name] = Matrix.Translation(Wi @ Vector((Q @ (t / 100.0) + T).tolist())) @ rot.to_4x4()
        for b in B:
            bas = ((b.matrix_local.inverted() @ b.parent.matrix_local) @ Marm[b.parent.name].inverted() @ Marm[b.name]) if b.parent else b.matrix_local.inverted() @ Marm[b.name]
            pb = arm.pose.bones[b.name]; pb.matrix_basis = bas
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('scale', frame=f)
        M = Matrix((G @ Rw[f] @ F).tolist()).to_4x4(); M.translation = Vector((G @ Cw[f]).tolist())
        cam.matrix_world = M; cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    return f1
