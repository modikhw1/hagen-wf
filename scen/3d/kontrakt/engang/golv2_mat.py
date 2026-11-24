"""GOLV2 före/efter: bildtrohet och 3D-konsistens för notan och b, plus bilder med flyttad kamera.

Bara sparade data, numpy-skinning och snabb kompilering. Ingen inferens, ingen Blender.
    scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/golv2_mat.py efter
    scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/golv2_mat.py fore --kod <kopia av backupträdet>
--kod pekar på en mapp som innehåller scen/3d/{kontrakt,ingest}; före-mätningen kör den gamla
koden därifrån (utan att arbetsträdet ändras). Utdata: scen/3d/kontrakt/ut/golv2/<fas>/.
"""
import sys, json, time, copy, argparse
from pathlib import Path
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parents[4]
ap = argparse.ArgumentParser(); ap.add_argument('fas'); ap.add_argument('--kod', default=str(ROOT)); ap.add_argument('--klipp', default='notan,b'); ap.add_argument('--bara-bilder', action='store_true')
A = ap.parse_args()
KOD = Path(A.kod).resolve() / 'scen/3d'
sys.path[:0] = [str(KOD/'kontrakt'), str(KOD/'ingest')]
sys.dont_write_bytecode = True
import kompilera, trohet, kroppmatt
from golvmatning import fotkontroll
assert Path(kompilera.__file__).resolve().is_relative_to(KOD), kompilera.__file__
LAS = getattr(trohet, 'las_sekvens', None) or (lambda p: dict(np.load(p)))
OUT = ROOT/'scen/3d/kontrakt/ut/golv2'/A.fas
OUT.mkdir(parents=True, exist_ok=True)
FOT = [4, 8, 20, 24]   # l_foot, l_ball, r_foot, r_ball
IX = trohet.IX


def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def golvniva(plan, sc):
    return next((float(p.get('golv_hojd_m', 0.)) for p in plan.get('plats') or [] if p['id'] == sc.get('plats_id')), 0.)


def rumskamera(sc, V, f):
    M = np.array(sc.get('till_plats', np.eye(4))); g = M[:3, :3] @ trohet.gravitation(V)
    return g @ V['kam_C'][f] + M[:3, 3], g, M


def rita(plan, sc, fas, vid=1.):
    """Snabb projektion (inte Blender): golvrutnät, lådor, hud och benlinjer från en kamera 0,5 m åt sidan och 0,3 m upp.

    vid>1 delar brännvidden (samma läge och mål) för en översikt; utelämnade spår ritas grå med fasens placeringsregel."""
    u = (sc['ut'][0] + sc['ut'][1]) // 2; f = sc['lokal_start'] + u - sc['ut'][0]
    key = copy.deepcopy(plan['matkamera']['nycklar'][u]); m = np.array(key['matris'])
    target = m[:3, 3] - m[:3, 2] * 3
    if sc['personer']: target = trohet.ruta(sc, sc['personer'][0], f)[IX['c_spine2']]
    pos = m[:3, 3] + .5 * m[:3, 0] + [0, 0, .3]
    key['matris'] = kompilera.sikta(pos, target); key['lins_mm'] = key['lins_mm'] / vid
    w, h = 576, 1024; img = np.full((h, w, 3), 235, np.uint8)
    R = np.array(key['matris'])[:3, :3]
    def framfor(x): return bool((((np.atleast_2d(x) - pos) @ R)[:, 2] < -.05).all())
    def linje(x, c, th=1):
        if not framfor(x): return
        uv = trohet.projicera(np.array(x), key, w, h)
        if np.isfinite(uv).all() and np.abs(uv).max() < 30000: cv2.polylines(img, [uv.astype(np.int32)], False, c, th, cv2.LINE_AA)
    golv = golvniva(plan, sc)
    for a in np.arange(-3, 3.01, .5):
        linje([[target[0]-3, target[1]+a, golv], [target[0]+3, target[1]+a, golv]], (190, 190, 190))
        linje([[target[0]+a, target[1]-3, golv], [target[0]+a, target[1]+3, golv]], (190, 190, 190))
    for o in plan['objekt']:
        if o['typ'] == 'plan' or o['id'].startswith(('golv', 'vagg')): continue
        su = o.get('synlig_ut')
        if su and not (su[0] <= u < su[1]): continue
        sz = np.array(o['matt_m']) / 2; po = np.array(o['pos_m']); yaw = o.get('rotation_rad', [0, 0, 0])[2]
        Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
        pts = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]) * sz @ Rz.T + po
        for i in range(8):
            for bit in (1, 2, 4):
                j = i ^ bit
                if i < j: linje(pts[[i, j]], (110, 130, 150), 2)
    for n, pm in enumerate(sc['personer']):
        pose, q, t = trohet.ruta_pose(sc, pm, f); x = kroppmatt.hudhorn(pose) / 100 @ q.T + t
        sil = kroppmatt.siluett(x, key, w, h, w, h)
        if sil is not None: img[sil] = (95, 150, 190) if n == 0 else (130, 180, 100)
        j = pose[:, :3] / 100 @ q.T + t
        for namn in [('root', 'c_spine2', 'c_head'), ('l_upleg', 'l_lowleg', 'l_foot', 'l_ball'), ('r_upleg', 'r_lowleg', 'r_foot', 'r_ball')]:
            linje(j[[IX[k] for k in namn]], (30, 50, 60), 2)
        fot = j[FOT]; lag = fot[np.argmin(fot[:, 2])]
        linje([lag, [lag[0], lag[1], golv]], (0, 0, 220), 2)   # röd lodlinje: fot till golv
    V = dict(np.load(sc['varld'])); folder = Path(sc['varld']).parent
    iplan = {str(pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]) for pm in sc['personer']}
    for fil in sorted(folder.glob('sekvens_*.npz')):
        pid = fil.stem[8:]
        if pid in iplan: continue
        s = LAS(fil)
        if not s['inom'][f]: continue
        rc, g, M = rumskamera(sc, V, f); q = g @ V['kam_R'][f] @ trohet.F; t = g @ (V['kam_C'][f] + V['kam_R'][f] @ s['cam_t'][f]) + M[:3, 3]
        j = s['pose'][f][:, :3] / 100 @ q.T + t
        for namn in [('root', 'c_spine2', 'c_head'), ('l_upleg', 'l_lowleg', 'l_foot', 'l_ball'), ('r_upleg', 'r_lowleg', 'r_foot', 'r_ball'),
                     ('c_spine2', 'l_uparm', 'l_lowarm', 'l_wrist'), ('c_spine2', 'r_uparm', 'r_lowarm', 'r_wrist')]:
            if all(k in IX for k in namn): linje(j[[IX[k] for k in namn]], (120, 120, 120), 3)
        fot = j[FOT]; lag = fot[np.argmin(fot[:, 2])]; linje([lag, [lag[0], lag[1], golv]], (0, 0, 220), 2)
    cv2.putText(img, f'{fas} {sc["id"]} +0,5 m sida / +0,3 m upp' + (f' vid x{vid:g}' if vid != 1 else ''), (15, 30), cv2.FONT_HERSHEY_SIMPLEX, .6, (10, 10, 10), 2)
    fil = OUT/f'{plan["_klipp"]}_{sc["id"]}_flyttad{"_vid" if vid != 1 else ""}.png'; cv2.imwrite(str(fil), img)
    return dict(bild=str(fil.relative_to(ROOT)), kamera=key, mal=np.asarray(target).tolist(), golv_m=golv)


def personrad(plan, sc, pm, pid, folder, meta, V, bild):
    """3D-rest för en person; pm=None betyder spår som planen utelämnar (placeras med samma regel som koden i fasen).

    sula_*: lägsta punkt på riggens fothud (trosula, FBX-benvikter) över golvet, modellpose respektive byggd pose."""
    import trosula
    s = LAS(folder/f'sekvens_{pid}.npz'); vis = fotkontroll(folder, pid, meta)
    sides = {v['ruta']: (v['sidor'] if v['anvandbar'] else [False, False]) for v in vis['per_ruta']}
    ref = LAS_ORIG(folder/f'sekvens_{pid}.npz')
    golv = golvniva(plan, sc); r = dict(fot=[], synlig=[], byggd=[], hoft=[], huvud=[], gap=[], kamh=[], rot=[], sula=[], sula_byggd=[])
    for u in range(*sc['ut']):
        f = sc['lokal_start'] + u - sc['ut'][0]
        if not s['inom'][f]: continue
        rc, g, M = rumskamera(sc, V, f); key = plan['matkamera']['nycklar'][u]; c = np.array(key['matris'])[:3, 3]
        r['gap'].append(float(np.linalg.norm(c - rc))); r['kamh'].append(float(c[2] - golv))
        if pm is not None:
            pose, q, t = trohet.ruta_pose(sc, pm, f, stod=False, data=(s, V)); x = pose[:, :3] / 100 @ q.T + t
            pb, qb, tb = trohet.ruta_pose(sc, pm, f, data=(s, V)); xb = pb[:, :3] / 100 @ qb.T + tb
            r['byggd'].append(float(xb[FOT, 2].min() - golv)); r['sula_byggd'].append(trosula.lagsta(pb, qb, tb) - golv)
            # rotpunkt mot kroppens egen projektion i originalkameran (skattad kamerarumsposition, före golv)
            o = ref['pose'][f, 1, :3] / 100 @ trohet.F + ref['cam_t'][f]
            uv = o[:2] / o[2] * float(ref['fokal']) + [meta['bredd'] / 2, meta['hojd'] / 2]
            r['rot'].append(float(np.linalg.norm(trohet.projicera(x[1:2], key, meta['bredd'], meta['hojd'])[0] - uv)))
        else:
            q = g @ V['kam_R'][f] @ trohet.F; t = g @ (V['kam_C'][f] + V['kam_R'][f] @ s['cam_t'][f]) + M[:3, 3]
            pose = s['pose'][f]; x = pose[:, :3] / 100 @ q.T + t
        r['sula'].append(trosula.lagsta(pose, q, t) - golv)
        fz = float(x[FOT, 2].min() - golv); r['fot'].append(fz)
        sd = sides.get(int(f), [False, False])
        seen = [float(x[[FOT[2*k], FOT[2*k+1]], 2].min() - golv) for k in range(2) if sd[k]]
        if seen: r['synlig'].append(min(seen))
        r['hoft'].append(float(x[IX['root'], 2] - golv)); r['huvud'].append(float(x[IX['c_head'], 2] - golv))
    med = lambda v: float(np.median(v)) if v else None
    rad = dict(scen=sc['id'], tagning=folder.name, ingest_id=pid, person=pm['id'] if pm else None, i_plan=pm is not None,
               kamerahojd_m=med(r['kamh']), kamera_rum_avstand_m=med(r['gap']), modellfotrest_m=med(r['fot']),
               synliga_fotrutor=len(r['synlig']), synlig_fotrest_m=med(r['synlig']), fotrest_byggd_m=med(r['byggd']),
               sula_modell_m=med(r['sula']), sula_byggd_m=med(r['sula_byggd']),
               hoft_over_golv_m=med(r['hoft']), huvud_over_golv_m=med(r['huvud']), rot_px=med(r['rot']))
    if bild: rad.update(median_px=bild.get('median_px'), p90_px=bild.get('p90_px'))
    return rad


def LAS_ORIG(p):
    # Kroppens skattade kamerarumsrörelse: cam_t före golv- och kontaktsteg, pose före kontakt.
    with np.load(p) as d: d = dict(d)
    if int(d.get('golv_version', 0)) < 2:
        d['cam_t'] = d.get('cam_t_fore_golv', d.get('cam_t_fore_kontakt', d['cam_t'])); d['pose'] = d.get('pose_fore_kontakt', d['pose'])
    return d


KALLOR = dict(notan=ROOT/'forvarld/varld/pipeline/kalla.json', b=ROOT/'scen/3d/kontrakt/ut/b/kalla_prop.json')
resultat = {}
for klipp in A.klipp.split(','):
    kalla = KALLOR[klipp]; k = json.loads(kalla.read_text(encoding='utf-8'))
    regi = json.loads((ROOT/'forvarld/varld/pipeline/base-regi.json').read_text(encoding='utf-8'))
    regi['edits'] = []; regi['kalla'] = dict(klipp_id=k['klipp']['id'], sha256=k['klipp']['sha256'], revision=k['revision']); regi['ramar']['bevara_beats'] = []
    rf = OUT/f'{klipp}_regi.json'; save(rf, regi)
    t0 = time.perf_counter(); p = kompilera.kompilera(kalla, rf, snabb=True); tk = time.perf_counter() - t0
    p['_klipp'] = klipp
    if A.bara_bilder:
        if klipp == 'notan':
            for sc in p['scener']: rita(p, sc, A.fas); rita(p, sc, A.fas, vid=2.)
        continue
    bild = trohet.mat(p); kropp = kroppmatt.matt_plan(p)
    rader = []; bilder = []
    for sc in p['scener']:
        V = dict(np.load(sc['varld'])); folder = Path(sc['varld']).parent; meta = json.loads((folder/'meta.json').read_text(encoding='utf-8'))
        iplan = {str(pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]): pm for pm in sc['personer']}
        for fil in sorted(folder.glob('sekvens_*.npz')):
            pid = fil.stem[8:]; pm = iplan.get(pid)
            b = next((x for x in bild['personer'] if pm and x['scen'] == sc['id'] and x['person'] == pm['id']), None)
            rad = personrad(p, sc, pm, pid, folder, meta, V, b)
            if pm:
                mk = next(x for x in kropp if x['scen'] == sc['id'] and x['person'] == pm['id'])
                rad['iou'] = mk['mask'].get('iou_median')
            rader.append(rad)
        if klipp == 'notan': bilder.append(rita(p, sc, A.fas)); rita(p, sc, A.fas, vid=2.)
    q = p['kvalitet']
    platsobjekt = [dict(id=o['id'], topp_m=float(o['pos_m'][2] + o['matt_m'][2] / 2), xy=o['pos_m'][:2]) for o in p['objekt']
                   if o['id'] in ('stol_A', 'stol_B', 'bord_A', 'bord_B', 'disk', 'bardisk') or o.get('deltyp') in ('bardisk',) and ':' not in o['id']]
    resultat[klipp] = dict(kompilering_s=round(tk, 2), personer=rader, bilder=bilder, objekt=platsobjekt,
                           hojdpassning=q.get('hojdpassning'), golv=q.get('golv_skala'), kamerakalibrering=q.get('kamerakalibrering'))
    p.pop('_klipp'); save(OUT/f'{klipp}_plan.json', p)
    print(klipp, round(tk, 1), 's', flush=True)
if not A.bara_bilder: save(OUT/'matning.json', resultat)
