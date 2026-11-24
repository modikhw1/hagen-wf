"""Bygger en Blender-scen ur ingest-utdata: MHR-rigg per person i världsläge, trackad kamera, golv, ljud.
Körs headless:  blender -b --factory-startup --python scen/3d/ingest/mhr_rig.py -- <utmapp> <klipp.mp4> [--render] [--plan plan.json] [--ut byggmapp] [--ljud spar.wav]
En plan med nyckeln 'scener' (flera tagningar, se scen/3d/kontrakt) byggs scen för scen i en tidslinje; --ljud muxas då med ffmpeg till <byggmapp>/film.mp4.
Ingen retargeting: MHR:s 127 leder = FBX-riggens 127 ben (led i = ben i-1). Se scen/3d/klipp2/PROCESS.md.
"""
import sys, json, os, glob, time
import bpy, numpy as np
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kroppsstod import begransa
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kontrakt'))
from trostod import begransa as tro_begransa

F = np.diag([1.0, -1.0, -1.0])   # OpenCV-kamerarum = F @ MHR-modellrum
FBX = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'klipp2', 'sam3db', 'mhr', 'assets', 'lod3.fbx')
FARGER = ['#c9b7a5', '#8fa3b8', '#b89a8f', '#9fb48f', '#b0a0c0']


from metrisk import las as las_sekvens, registrera_dolda_fotter

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


def person(pid, S, G, Rw, Cw, farg, f0=0, dold_efter=False, Mp=None, stod=None, rapport=None, benlangder=None, skyddade_knan=None, handsyn=None):
    fore = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=FBX)
    nya = [o for o in bpy.data.objects if o not in fore]
    arm = next(o for o in nya if o.type == 'ARMATURE'); mesher = [o for o in nya if o.type == 'MESH']
    for o in [o for o in nya if o.type == 'EMPTY']: bpy.data.objects.remove(o)
    arm.name = f'person:{pid}'
    for o in mesher:
        o.name = f'person:{pid}:kropp'; o.data.materials.clear(); o.data.materials.append(_mat(farg))
    kroppsskala=float(S.get('dold_fot_skala',1.))
    if abs(kroppsskala-1.)>1e-12:
        scale=Matrix.Scale(kroppsskala,4);arm.data.transform(scale)
        for o in mesher:o.data.transform(scale)
        arm['dolda_fotter_status']='antagen';arm['dolda_fotter_faktor']=kroppsskala
    B = list(arm.data.bones); W = arm.matrix_world
    P = np.array([_tq(S['rest'][i + 1])[0] for i in range(len(B))]); Q = np.array([list(W @ b.head_local) for b in B])
    mp, mq = P.mean(0), Q.mean(0); X, Y = P - mp, Q - mq
    U, Sv, Vt = np.linalg.svd(X.T @ Y); d = np.sign(np.linalg.det(Vt.T @ U.T)); R = Vt.T @ np.diag([1, 1, d]) @ U.T
    Rc = Matrix(R.tolist())
    C = {b.name: (Rc @ _tq(S['rest'][i + 1])[1].to_matrix()).inverted() @ (W @ b.matrix_local).to_3x3().normalized() for i, b in enumerate(B)}
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    Wr_i = W.to_3x3().normalized().inverted(); Wi = W.inverted(); pose, camt, kand = S['pose'], S['cam_t'], S['kand']
    synlig_fore = None
    handkedja, handbank = {}, {}
    if handsyn:      # ben i handen per sida: handleden och allt under den
        for sida, rot in (('h', 'r_wrist'), ('v', 'l_wrist')):
            rb = next((b for b in B if b.name == rot or b.name.endswith(':' + rot)), None)
            if rb is not None and sida in handsyn:
                for b in [rb] + list(rb.children_recursive): handkedja[b.name] = sida; handbank[b.name] = []
    stodr = dict(person=pid,ankare=stod['id'] if stod else None,leder=[],rutor=[],skyddade_rutor=[],detaljer=None,overkropp_max_andring=0.)
    if f0 > 0:   # flerklipp: personen finns först i sin scens tidsfönster
        for o in [arm] + [c for c in arm.children]:
            o.hide_render = o.hide_viewport = True; o.keyframe_insert('hide_render', frame=f0 - 1); o.keyframe_insert('hide_viewport', frame=f0 - 1)
    for f in range(len(pose)):
        Q3 = G @ Rw[f] @ F; T = G @ (Cw[f] + Rw[f] @ camt[f])
        if Mp is not None: Q3 = Mp[:3, :3] @ Q3; T = Mp[:3, :3] @ T + Mp[:3, 3]   # platsens transform (plan['scener'][i]['till_plats'])
        P = pose[f]
        if stod is not None:
            flag = S['ben_synliga'][f] if 'ben_synliga' in S else None
            P, sr = tro_begransa(P,Q3,T,stod,flag,benlangder,skyddade_knan=skyddade_knan[f] if skyddade_knan is not None else None) if benlangder is not None else begransa(P,Q3,T,stod,flag)
            if sr['leder'] and S['inom'][f]:
                stodr['rutor'].append(f+f0); stodr['leder']=sr['leder']; stodr['detaljer']=sr
            elif S['inom'][f]: stodr['skyddade_rutor'].append(f+f0)
        Qm = Matrix(Q3.tolist())
        Marm = {}
        for i, b in enumerate(B):
            t, q = _tq(P[i + 1])
            Marm[b.name] = Matrix.Translation(Wi @ Vector((Q3 @ (t / 100.0) + T).tolist())) @ (Wr_i @ (Qm @ q.to_matrix() @ C[b.name])).to_4x4()
        for b in B:
            bas = ((b.matrix_local.inverted() @ b.parent.matrix_local) @ Marm[b.parent.name].inverted() @ Marm[b.name]) if b.parent else b.matrix_local.inverted() @ Marm[b.name]
            pb = arm.pose.bones[b.name]; pb.matrix_basis = bas
            if handkedja and b.name in handkedja: handbank[b.name].append((pb.location.copy(), pb.rotation_quaternion.copy()))
            pb.keyframe_insert('location', frame=f + f0); pb.keyframe_insert('rotation_quaternion', frame=f + f0); pb.keyframe_insert('scale', frame=f + f0)
        # dölj personen där den inte syns i källan (utanför tidsfönstret för första och sista detektering)
        syn = bool(S['inom'][f])
        if syn != synlig_fore:
            for o in [arm] + [c for c in arm.children]:
                o.hide_render = o.hide_viewport = not syn; o.keyframe_insert('hide_render', frame=f + f0); o.keyframe_insert('hide_viewport', frame=f + f0)
            synlig_fore = syn
    if handkedja: handvila(arm, handkedja, handbank, handsyn, f0, stodr)
    if dold_efter:
        for o in [arm] + [c for c in arm.children]:
            o.hide_render = o.hide_viewport = True; o.keyframe_insert('hide_render', frame=f0 + len(pose)); o.keyframe_insert('hide_viewport', frame=f0 + len(pose))
    if rapport is not None: rapport.append(stodr)
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


def bygg_planrum(plan):
    """Planens lådor är redan i Blender-världen; synlighet följer utdataklockan."""
    for item in plan['objekt']:
        if item['typ'] == 'cylinder': bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.5,depth=1)
        elif item['typ'] == 'plan': bpy.ops.mesh.primitive_plane_add(size=1)
        else: bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.active_object; obj.name = item['namn']; obj.location = item['pos_m']
        obj.dimensions = item['matt_m']; obj.rotation_euler = item['rotation_rad']
        if item['top_slope']:
            for vertex in obj.data.vertices:
                if vertex.co.z > 0: vertex.co.z += item['top_slope'] * vertex.co.x * item['matt_m'][0] / item['matt_m'][2]
        obj.data.materials.append(_mat(item['farg'])); obj['room_id'] = item['id']
        if item.get('fas_m'):
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            bevel=obj.modifiers.new('Mallfas','BEVEL');bevel.width=item['fas_m'];bevel.segments=2
        if item.get('status'): obj['ursprung']=item['status']
        a, b = item['synlig_ut']
        for f, dold in ((-1, True), (a, False), (b, True)):
            obj.hide_render = obj.hide_viewport = dold
            obj.keyframe_insert('hide_render', frame=f); obj.keyframe_insert('hide_viewport', frame=f)
    return next((p['golv_hojd_m'] for p in plan.get('plats',[])),next(o['pos_m'][2] for o in plan['objekt'] if o['id']=='golv'))


def _medel(qs):
    """Medelrotation av närliggande kvaternioner (tecknen riktas mot den första)."""
    v = np.array([list(q) for q in qs]); v[(v @ v[0]) < 0] *= -1; m = v.mean(0)
    return Quaternion((m / np.linalg.norm(m)).tolist())


def handvila(arm, kedja, bank, handsyn, f0, rapport=None, kort=12, toning=6, fonster=3):
    """Händer utan bildstöd (ingest/handsyn.py) är estimatorns gissning och rycker. De får inte spelas som mätning.

    Dold kort lucka (högst `kort` rutor, med synliga rutor på båda sidor): rotationerna interpoleras över luckan.
    Dold längre: handen hålls i luckans medelställning, med `toning` rutors övergång mot de synliga rutorna intill.
    Störd (synlig men delvis under inbränd text): glidande medel över ±`fonster` rutor.
    Bara handleden och fingrarna ändras, i benens egna lokala rotationer; underarmen följer läsningen."""
    n = len(next(iter(bank.values()))); andrade = {'h': 0, 'v': 0}
    for namn, sida in kedja.items():
        L = [x[0] for x in bank[namn]]; Q = [x[1] for x in bank[namn]]; hs = handsyn[sida]
        dold = [bool(x) for x in hs['dold'][:n]]; stord = [bool(x) for x in hs.get('stord', [False] * n)[:n]]; ny = {}
        i = 0
        while i < n:
            if not dold[i]: i += 1; continue
            j = i
            while j < n and dold[j]: j += 1
            va, ho = (i - 1 if i > 0 else None), (j if j < n else None)
            if j - i <= kort and va is not None and ho is not None:
                for f in range(i, j):
                    t = (f - va) / (ho - va); ny[f] = (L[va].lerp(L[ho], t), Q[va].slerp(Q[ho], t))
            else:
                qm = _medel(Q[i:j]); lm = sum(L[i:j], Vector((0, 0, 0))) / (j - i)
                for f in range(i, j):
                    q, l = qm.copy(), lm.copy()
                    if va is not None and f - i < toning: t = (f - i + 1) / (toning + 1); q = Q[va].slerp(qm, t); l = L[va].lerp(lm, t)
                    if ho is not None and j - f <= toning: t = (j - f) / (toning + 1); q = Q[ho].slerp(q, t); l = L[ho].lerp(l, t)
                    ny[f] = (l, q)
            i = j
        for f in range(n):
            if stord[f] and not dold[f]:
                gr = [g for g in range(max(0, f - fonster), min(n, f + fonster + 1)) if not dold[g]]
                ny[f] = (sum((L[g] for g in gr), Vector((0, 0, 0))) / len(gr), _medel([Q[g] for g in gr]))
        pb = arm.pose.bones[namn]
        for f, (l, q) in ny.items():
            pb.location = l; pb.rotation_quaternion = q; pb.keyframe_insert('location', frame=f + f0); pb.keyframe_insert('rotation_quaternion', frame=f + f0)
        if namn.endswith('wrist'): andrade[sida] = len(ny)
    if rapport is not None: rapport['handvila'] = dict(rutor_hoger=andrade['h'], rutor_vanster=andrade['v'], status='antagen', metod='händer utan bildstöd hålls lugna; se ingest/handsyn.py')


def fkurvor(action):
    """F-kurvor oavsett om Blender använder lager/kanalfack eller den äldre platta listan."""
    if hasattr(action, 'fcurves'):
        try: return list(action.fcurves)
        except Exception: pass
    return [k for lager in action.layers for remsa in lager.strips for fack in remsa.channelbags for k in fack.fcurves]


def ta_bort_kurva(action, kurva):
    if hasattr(action, 'fcurves'):
        try: action.fcurves.remove(kurva); return
        except Exception: pass
    for lager in action.layers:
        for remsa in lager.strips:
            for fack in remsa.channelbags:
                if kurva in list(fack.fcurves): fack.fcurves.remove(kurva); return


def bygg_flera(plan, byggut, render=False, ljud=None):
    """Flera tagningar i en tidslinje. Varje scen har egen varld.npz (kamera, gravitation), egna personsekvenser och eget rum
    (plan['objekt'] med synlig_ut). Renderkameran är en enda kamera med en nyckel per utdataruta (plan['renderkamera']).
    Färg per roll kommer från plan['personer'] och gäller i alla scener. Munnen följer inte ny text.
    Plats: har en scen till_plats (4x4, tagningens Blender-värld -> platsen) placeras personerna med den; objekten i plan['objekt'] ligger redan i platsen och byggs en gång."""
    t0 = time.time()
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    sc = bpy.context.scene; sc.name = 'ingest'; N = len(plan['kallrutor']); sc.frame_start, sc.frame_end = 0, N - 1
    u = plan['utdata']; sc.render.fps = u['fps_taljare']; sc.render.fps_base = u['fps_namnare']
    sc.render.resolution_x, sc.render.resolution_y = u['bredd'], u['hojd']
    cd = bpy.data.cameras.new('renderkamera'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = plan['renderkamera']['sensor_bredd_mm']; cd.clip_start = .05
    rc = bpy.data.objects.new('renderkamera', cd); sc.collection.objects.link(rc); sc.camera = rc
    for f, key in enumerate(plan['renderkamera']['nycklar']):
        rc.matrix_world = Matrix(key['matris']); cd.lens = key['lins_mm']
        rc.keyframe_insert('location', frame=f); rc.keyframe_insert('rotation_euler', frame=f); cd.keyframe_insert('lens', frame=f)
    farg = {p['id']: p['farg'] for p in plan['personer']}
    stodrapport=[]
    for d in plan['scener']:
        V = np.load(d['varld']); G = gravitation(V); a, b = d['ut']; idx = np.arange(d['lokal_start'], d['lokal_start'] + (b - a))
        Rw, Cw = V['kam_R'][idx], V['kam_C'][idx]
        for pm in d['personer']:
            # Närvaro (kontrakt/narvaro.py): en roll som inte är läst i scenen bär egen värld och egna källrutor ur en annan tagning.
            lan = pm.get('narvaro'); ip = np.array(pm['rutor'], dtype=int) if lan else idx
            if lan: Vp = np.load(pm['varld']); Gp, Rp, Cp = gravitation(Vp), Vp['kam_R'][ip], Vp['kam_C'][ip]
            else: Gp, Rp, Cp = G, Rw, Cw
            S = las_sekvens(pm['rorelse']); S = {n: S[n][ip] if n in ('pose', 'cam_t', 'kand', 'inom', 'ben_synliga') else S[n] for n in S.files}
            Mp=pm.get('till_plats',d.get('till_plats'))
            arm = person(pm['id'], S, Gp, Rp, Cp, farg.get(pm['id'], FARGER[0]), f0=a, dold_efter=True, Mp=np.array(Mp) if Mp is not None else None,stod=pm.get('stod'),rapport=stodrapport,benlangder=pm.get('benlangder_m'),
                   skyddade_knan=[pm.get('skyddade_knan',{}).get(str(int(i)),[False,False]) for i in ip], handsyn=pm.get('handsyn'))
            stodrapport[-1]['scen']=d['id']
            if lan:
                stodrapport[-1]['narvaro']=lan; arm['narvaro']=json.dumps(lan, ensure_ascii=False)
                if lan.get('kamerabarare'):      # finns i rummet och i vyn, men renderas inte: tagningens kamera står där rollens huvud är
                    for o in [arm] + [c for c in arm.children]:
                        if o.animation_data and o.animation_data.action:
                            for kurva in [k for k in fkurvor(o.animation_data.action) if k.data_path == 'hide_render']: ta_bort_kurva(o.animation_data.action, kurva)
                        o.hide_render = True
    bygg_planrum(plan)
    from prop_blender import bygg as bygg_props
    bygg_props(plan)
    if not sc.sequence_editor: sc.sequence_editor_create()
    if ljud: sc.sequence_editor.strips.new_sound('ljud', os.path.abspath(ljud), 1, 0)
    else:
        for i, delplan in enumerate(plan['tidskarta']):
            if not delplan['ljud'] or u['ljudpolicy'] == 'tyst': continue
            a, b = delplan['kalla']; start, slut = delplan['ut']
            s = sc.sequence_editor.strips.new_sound(f'ljud:{i}', plan['kallvideo'], 1, start - a); s.frame_final_start = start; s.frame_final_end = slut
    try: sc.render.engine = 'BLENDER_WORKBENCH'
    except TypeError: pass
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_shadows = True
    # Opak PNG med jämn bakgrund så att mp4 inte får svart genomskinlighet.
    sc.world = bpy.data.worlds.new('bakgrund'); sc.world.color = (.42, .44, .47)
    sc.render.film_transparent = False; sc.render.resolution_percentage = u['upplosning_procent']
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(f'{byggut}/scen.blend'))
    with open(os.path.join(byggut,'stod_rapport.json'),'w',encoding='utf-8') as fil:
        json.dump(dict(personer=stodrapport,utelamnade=[dict(x,scen=d['id']) for d in plan['scener'] for x in d.get('utelamnade',[])],
                       regel='Endast ben_synliga=false; rygg/armar/huvud kopieras i global pose. Synliga ben ändras aldrig.'),fil,ensure_ascii=False,indent=2)
    byggtid=time.time()-t0
    print(f'mhr_rig: {N} bildrutor i {len(plan["scener"])} scener, {time.time() - t0:.1f} s', flush=True)
    if render:
        renderstart=time.time()
        sc.render.filepath = os.path.abspath(f'{byggut}/render/f'); bpy.ops.render.render(animation=True)
        if ljud:
            import shutil, subprocess
            ff = shutil.which('ffmpeg')
            if not ff: print('mhr_rig: ffmpeg saknas på PATH, ingen mp4 muxad', flush=True); return
            film = os.path.abspath(f'{byggut}/film.mp4')
            subprocess.run([ff, '-v', 'error', '-y', '-framerate', f"{u['fps_taljare']}/{u['fps_namnare']}", '-start_number', '0', '-i', os.path.abspath(f'{byggut}/render/f%04d.png'),
                            '-i', os.path.abspath(ljud), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '160k', '-shortest', film], check=True)
            print('mhr_rig: film', film, flush=True)
        with open(os.path.join(byggut,'tider_mall.json'),'w',encoding='utf-8') as fil:
            json.dump(dict(bygg_s=byggtid,render_och_mux_s=time.time()-renderstart),fil,indent=2)


def bygg(ut, klipp, render=False, planfil=None, byggut=None, ljud=None):
    t0 = time.time()
    plan = json.load(open(planfil, encoding='utf-8')) if planfil else None
    registrera_dolda_fotter(plan.get('matning') if plan else None)
    if plan and plan['schema_version'] != 'plan/1': raise ValueError('Okänd planversion')
    if plan and plan.get('kvalitet',{}).get('bildtrohet',{}).get('flaggad'):
        print('VARNING: flaggad bildtrohet; se planens kvalitetsrapport.',flush=True)
        if render and '--tillat-flaggad' not in sys.argv:
            raise ValueError('Flaggad scen renderas inte tyst. Granska rapporten; använd --tillat-flaggad för diagnostisk render.')
    byggut = byggut or ut; os.makedirs(byggut, exist_ok=True)
    if plan and 'scener' in plan: return bygg_flera(plan, byggut, render, ljud)
    V = np.load(plan['matning']['kameror'][0]['spar_metrisk']['sokvag'] if plan else f'{ut}/varld.npz')
    G = gravitation(V); Rw, Cw = V['kam_R'], V['kam_C']; N = len(Rw)
    if plan:
        rutor = np.array(plan['kallrutor'], dtype=int)
        if not len(rutor) or np.any(rutor < 0) or np.any(rutor >= N): raise ValueError('Ogiltig tidskarta')
        Rw, Cw = Rw[rutor], Cw[rutor]; N = len(rutor)
    meta = json.load(open(f'{ut}/meta.json'))
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    sc = bpy.context.scene; sc.name = 'ingest'; sc.render.fps = round(meta['fps']); sc.frame_start, sc.frame_end = 0, N - 1
    sc.render.resolution_x, sc.render.resolution_y = meta['bredd'], meta['hojd']
    if plan:
        u = plan['utdata']; sc.render.fps = u['fps_taljare']; sc.render.fps_base = u['fps_namnare']
        sc.render.resolution_x, sc.render.resolution_y = u['bredd'], u['hojd']
    cd = bpy.data.cameras.new('kamera'); cam = bpy.data.objects.new('kamera', cd); sc.collection.objects.link(cam); sc.camera = cam
    sekvenser = [p['rorelse'] for p in plan['personer']] if plan else sorted(glob.glob(f'{ut}/sekvens_*.npz'))
    cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36; cd.lens = (float(np.load(sekvenser[0])['fokal']) if sekvenser else max(meta['bredd'], meta['hojd'])) * 36 / (plan['kallbild_bredd'] if plan else meta['bredd']); cd.clip_start = .05
    for f in range(N):
        M = Matrix((G @ Rw[f] @ F).tolist()).to_4x4(); M.translation = Vector((G @ Cw[f]).tolist()); cam.matrix_world = M
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    if plan:
        # Rekonstruktionskameran lämnas kvar. Kropparna använder alltid Rw/Cw ovan.
        rd = cd.copy(); rd.name = 'renderkamera'; rc = bpy.data.objects.new('renderkamera', rd)
        sc.collection.objects.link(rc); sc.camera = rc
        for f, key in enumerate(plan['renderkamera']['nycklar']):
            rc.matrix_world = Matrix(key['matris']); rd.lens = key['lins_mm']
            rc.keyframe_insert('location', frame=f); rc.keyframe_insert('rotation_euler', frame=f); rd.keyframe_insert('lens', frame=f)
    fotz = []
    for k, sf in enumerate(sekvenser):
        pid = os.path.basename(sf)[8:-4]; S = las_sekvens(sf)
        if plan:
            pid = plan['personer'][k]['id']
            S = {n: S[n][rutor] if n in ('pose', 'cam_t', 'kand', 'inom', 'ben_synliga') else S[n] for n in S.files}
        arm = person(pid, S, G, Rw, Cw, plan['personer'][k]['farg'] if plan else FARGER[k % len(FARGER)],stod=plan['personer'][k].get('stod') if plan else None,
                     benlangder=plan['personer'][k].get('benlangder_m') if plan else None)
        for f in range(0, N, 15):
            if S['inom'][f]:
                sc.frame_set(f); fotz += [(arm.matrix_world @ arm.pose.bones[n].head).z for n in ('l_ball', 'r_ball')]
    z = bygg_planrum(plan) if plan else bygg_rum(ut, G)
    if z is None:
        z = float(V['golv_h']) if 'golv_h' in V else (float(np.percentile(fotz, 5)) if fotz else 0.0)
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, z)); g = bpy.context.active_object; g.name = 'golv'; g.data.materials.append(_mat('#5a554e'))
    if not sc.sequence_editor: sc.sequence_editor_create()
    if plan:
        for i, delplan in enumerate(plan['tidskarta']):
            if not delplan['ljud'] or plan['utdata']['ljudpolicy'] == 'tyst': continue
            a, b = delplan['kalla']; start, slut = delplan['ut']
            ljud = sc.sequence_editor.strips.new_sound(f'ljud:{i}', plan['kallvideo'], 1, start - a)
            ljud.frame_final_start = start; ljud.frame_final_end = slut
    else: sc.sequence_editor.strips.new_sound('ljud', klipp, 1, 0)
    try: sc.render.engine = 'BLENDER_WORKBENCH'
    except TypeError: pass
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_shadows = True
    sc.render.film_transparent = True; sc.render.resolution_percentage = 50; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    if plan: sc.render.resolution_percentage = plan['utdata']['upplosning_procent']
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(f'{byggut}/scen.blend'))
    print(f'mhr_rig: {N} bildrutor, golv z={z:.3f}, {time.time() - t0:.1f} s', flush=True)
    if render:
        sc.render.filepath = os.path.abspath(f'{byggut}/render/f'); bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    bygg(a[0], a[1], '--render' in a, a[a.index('--plan') + 1] if '--plan' in a else None,
         a[a.index('--ut') + 1] if '--ut' in a else None, a[a.index('--ljud') + 1] if '--ljud' in a else None)
