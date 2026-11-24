"""Mått på den byggda kroppen som inte hänger på kroppsestimatorns egna 2D-punkter: silhuett mot källans personmask,
darr (jitter) och täckning.

Silhuetten är MHR:s hudnät (lod1, 18 439 hörn, samma kropp som renderingens lod3) skinnat med de byggda lederna i numpy och
projicerat i den spårade kameran. Vikterna kommer ur lod1.fbx (`tro_export_hud.py`); skinningen är kontrollerad mot modellens egen
utdata (medelfel < 1 mm, `kontrollera_hud`). Masken kommer från YOLO11-seg (en annan modell än kroppsestimatorn) och är en union av
alla personer i rutan (256x144 eller liknande); varje person jämförs inom sin egen spårruta, utan de pixlar där en annan byggd
person ligger.

Känd skevhet (masken och kroppen mäter inte exakt samma sak):
- masken har kläder, hår, hattar och hållna föremål; kroppsnätet är en naken standardkropp. Det ger en undre gräns för IoU även
  när placeringen är perfekt (`iou_estimator` visar var den ligger för estimatorns egna hörn).
- masken stannar vid skymmande föremål (disk, bord). Därför redovisas IoU även med nätet klippt vid maskens nedersta rad (`iou_synlig`).
- YOLO-masken är grov (4 px per maskpixel i 576x1024) och kan sakna fingrar och fotleder.
- Nätet har inga korrigerande blendshapes: upp till ~2 cm lokalt fel mot modellens utdata.
"""
from pathlib import Path
import cv2
import numpy as np

HIT = Path(__file__).resolve().parent
NH = 18439   # modellens hörn; lod1.fbx har åtta extra hörn (en kub) sist
F = np.diag([1., -1., -1.])
_HUD = {}
_HUD_SIGNATUR = None


def rotation(q):
    q = np.asarray(q, float); q = q / np.linalg.norm(q, axis=-1, keepdims=True)
    x, y, z, w = np.moveaxis(q, -1, 0)
    return np.stack([1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w), 2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w),
                     2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)], axis=-1).reshape(q.shape[:-1] + (3, 3))


def hud():
    global _HUD_SIGNATUR
    file=HIT/'tro_hud.npz';st=file.stat();stamp=(str(file),st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    if stamp!=_HUD_SIGNATUR:
        _HUD.clear();_HUD_SIGNATUR=stamp
    if not _HUD:
        with np.load(file) as source:d=dict(source)
        v = d['verts_fbx'][:NH].astype(float)
        f = d['faces']; f = f[(f < NH).all(1)]
        _HUD.update(v0=100 * np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1), faces=f, wi=d['vikt_led'][:NH].astype(int), ww=d['vikt'][:NH].astype(float),
                    s0=d['vila_led'].astype(float))
        _HUD['r0'] = rotation(_HUD['s0'][:, 3:7])
        _HUD['rel0'] = _HUD['v0'][:, None, :] - _HUD['s0'][_HUD['wi'], :3]
    return _HUD


def skapa_hud_vila():
    """Engångssteg: skriv standardkroppens vilopose (kroppsmodellen med formparametrar 0) i tro_hud.npz. Kräver torch och modellen."""
    import torch
    m = torch.jit.load(str(HIT.parent / 'klipp2/sam3db/ckpt-vith/assets/mhr_model.pt'), map_location='cpu')
    with torch.no_grad(): _, s = m(torch.zeros(1, 45), torch.zeros(1, 204), torch.zeros(1, 72))
    d = dict(np.load(HIT / 'tro_hud.npz')); d['vila_led'] = s[0].numpy().astype(np.float32)
    np.savez_compressed(HIT / 'tro_hud.npz', **d)


def hudhorn(pose):
    """Hörnen (cm, modellrum) för en byggd pose (127, 8): linjär skinning mot standardkroppens vila, som Blender gör."""
    h = hud(); pose = np.asarray(pose, float)
    rel = np.einsum('jab,jcb->jac', rotation(pose[:, 3:7]), h['r0'])
    out = np.einsum('vkab,vkb->vka', rel[h['wi']], h['rel0']) + pose[h['wi'], :3]
    return (out * h['ww'][:, :, None]).sum(1)


def kontrollera_hud(pose, hornmodell):
    """Skillnad (cm) mellan numpy-skinningen och modellens egna hörn för samma pose: (medel, max)."""
    e = np.linalg.norm(hudhorn(pose) - hornmodell, axis=1); return float(e.mean()), float(e.max())


def projicera_mask(x, key, w, h, mw, mh, sensor=36.):
    m = np.array(key['matris']); c = (np.asarray(x) - m[:3, 3]) @ m[:3, :3]
    fok = key['lins_mm'] / sensor * w
    uv = c[..., :2] / (-c[..., 2:3]) * [fok, -fok] + [w / 2, h / 2]
    return uv * [mw / w, mh / h]


def fyll(uv, faces, mw, mh):
    """Fyll nätets trianglar i en bool-bild (mh, mw)."""
    img = np.zeros((mh, mw), np.uint8)
    if not np.isfinite(uv).all(): return img.astype(bool)
    pts = np.round(uv[faces] * 8).astype(np.int32)
    ok = (np.abs(pts) < 8 * 20000).all(axis=(1, 2)); pts = pts[ok]
    if len(pts): cv2.fillPoly(img, list(pts), 1, lineType=cv2.LINE_8, shift=3)
    return img.astype(bool)


def siluett(x_varld, key, w, h, mw, mh):
    """x_varld: nätets hörn i planens värld (m). Bool-bild i maskupplösning. None om hörn ligger bakom kameran (rutan är oanvändbar)."""
    m = np.array(key['matris']); c = (np.asarray(x_varld) - m[:3, 3]) @ m[:3, :3]
    if (c[:, 2] > -0.05).mean() > .02: return None
    return fyll(projicera_mask(x_varld, key, w, h, mw, mh), hud()['faces'], mw, mh)


def jitter(X):
    """Medel av andra differensens norm (cm/ruta²) över leder och rutor. X: (N, J, 3) i cm med NaN där rutan saknas.
    Bara trippler av tre intilliggande giltiga rutor räknas."""
    X = np.asarray(X, float); d = X[:-2] - 2 * X[1:-1] + X[2:]
    n = np.linalg.norm(d, axis=-1); ok = ~np.isnan(n).any(axis=1)
    return float(n[ok].mean()) if ok.any() else float('nan')


def jamfor_mask(sil, mask, box, mw, mh, andra=None, marginal=.08, min_mask=30):
    """Jämför en byggd silhuett med källmasken inom personens egen ruta. None om masken är för liten i rutan.
    andra: bool-bild med övriga byggda personer, som utesluts. box: [x0,y0,x1,y1] i maskpixlar."""
    bw, bh = box[2] - box[0], box[3] - box[1]
    x0 = int(max(0, np.floor(box[0] - marginal * bw))); x1 = int(min(mw, np.ceil(box[2] + marginal * bw)))
    y0 = int(max(0, np.floor(box[1] - marginal * bh))); y1 = int(min(mh, np.ceil(box[3] + marginal * bh)))
    reg = np.zeros((mh, mw), bool); reg[y0:y1, x0:x1] = True
    if andra is not None: reg &= ~andra
    m = mask & reg; s = sil & reg
    if m.sum() < min_mask: return None
    ys = np.nonzero(m.any(1))[0]; botten = ys.max()
    sk = s.copy(); sk[botten + 2:] = False

    def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))

    def tyngd(a):
        yy, xx = np.nonzero(a); return (np.array([xx.mean(), yy.mean()]) if len(xx) else None)

    def ut(a):
        r = np.nonzero(a.any(1))[0]; return (r.max() - r.min() + 1) if len(r) else 0
    r = dict(iou=iou(s, m), iou_synlig=iou(sk, m))
    a, b = tyngd(sk), tyngd(m)
    r['tyngdpunkt_bildhojdandel'] = float(np.linalg.norm(a - b) / mh) if a is not None else 1.0
    r['hojd_bildhojdandel'] = float((ut(sk) - ut(m)) / mh)
    r['byggd_pixlar'] = int(s.sum()); r['mask_pixlar'] = int(m.sum())
    return r


def sammanfatta(r):
    """r: lista av jamfor_mask-resultat (utan None)."""
    if not r: return dict(rutor=0)
    g = lambda k: np.array([x[k] for x in r])
    return dict(rutor=len(r), iou_median=float(np.median(g('iou'))), iou_p10=float(np.percentile(g('iou'), 10)),
                iou_synlig_median=float(np.median(g('iou_synlig'))), iou_synlig_p10=float(np.percentile(g('iou_synlig'), 10)),
                tyngdpunkt_median=float(np.median(g('tyngdpunkt_bildhojdandel'))), tyngdpunkt_p90=float(np.percentile(g('tyngdpunkt_bildhojdandel'), 90)),
                hojd_median_abs=float(np.median(np.abs(g('hojd_bildhojdandel')))))


def estimator_silhuett(raw, w, h, mw, mh):
    """Estimatorns egna hörn (pred_vertices + pred_cam_t, kamerarum) i maskupplösning: referens för hur högt IoU kan bli med detta mått."""
    x = raw['pred_vertices'].astype(float) + raw['pred_cam_t'].astype(float)
    if (x[:, 2] < .05).mean() > .02: return None
    f = float(raw['focal_length']); uv = x[:, :2] / x[:, 2:3] * f + [w / 2, h / 2]
    return fyll(uv * [mw / w, mh / h], hud()['faces'], mw, mh)


def _matt_plan_utan_cache(plan, stod=True):
    """Per scen och person: täckning, oberoende silhuettmått (alla rutor med mask), darr för byggd/stabil/rå pose och bildskyddets andel.
    Mätkameran (före regins kameraedits) används. Värden i planens värld, cm."""
    import json
    from trohet import ruta_pose, gravitation, las_sekvens
    w = plan['kallbild_bredd']; h = plan.get('kallbild_hojd', round(w * plan['utdata']['hojd'] / plan['utdata']['bredd']))
    scener = plan.get('scener') or plan.get('matkamera', {}).get('scener'); rader = []
    for d in scener:
        n_scen = d['ut'][1] - d['ut'][0]; lager = []
        for pm in d['personer']:
            folder = Path(pm['rorelse']).parent; pid = pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]
            s = las_sekvens(pm['rorelse']); v = dict(np.load(d['varld']))
            lager.append(dict(pm=pm, folder=folder, pid=str(pid), s=s, v=v, pal=json.loads((folder / f'palitlig_{pid}.json').read_text()) if (folder / f'palitlig_{pid}.json').exists() else {},
                              mask=np.load(folder / 'masker.npy'), boxar=json.loads((folder / 'personer.json').read_text()).get(str(pid), {}), sil={}, X={'byggd': {}, 'stabil': {}, 'ra': {}},
                              skipp=dict(ej_i_bild=0, opalitlig=0, ravdata_saknas=0), res=[], ref=[], bildskydd=None))
            bs = folder / f'bildskydd_{pid}.json'
            if bs.exists():
                r = json.loads(bs.read_text()).get('rutor', []); lager[-1]['bildskydd'] = float(np.median([x['stabil_andel'] for x in r])) if r else 1.0
        for u in range(*d['ut']):
            f = d['lokal_start'] + u - d['ut'][0] if plan.get('scener') else plan['kallrutor'][u]; key = plan.get('matkamera', plan['renderkamera'])['nycklar'][u]
            for L in lager:
                s = L['s']; L['sil'][u] = None
                if not s['inom'][f]: L['skipp']['ej_i_bild'] += 1; continue
                raw = L['folder'] / 'kropp' / L['pid'] / f'{f:04d}.npz'
                pose, q, t = ruta_pose(d, L['pm'], f, stod, (s, L['v']))
                mh, mw = L['mask'].shape[1:]
                L['sil'][u] = siluett(hudhorn(pose) / 100 @ q.T + t, key, w, h, mw, mh)
                if not raw.exists(): L['skipp']['ravdata_saknas'] += 1; continue
                if not L['pal'].get(str(f), True): L['skipp']['opalitlig'] += 1; continue
                with np.load(raw) as b:
                    rp = b['pred_joint_coords'].astype(float) @ F * 100; rt = b['pred_cam_t'].astype(float)
                    if L['ref'] is not None and str(f) in L['boxar']:
                        es = estimator_silhuett(b, w, h, mw, mh)
                        if es is not None:
                            box = np.array(L['boxar'][str(f)]) * [mw / w, mh / h, mw / w, mh / h]; rr = jamfor_mask(es, L['mask'][f], box, mw, mh)
                            if rr: L['ref'].append(rr)
                qf = q @ F
                # världskoordinater (cm) för darr: modell -> värld, sedan rå/stabil cam_t via t-förskjutning
                tw = t
                L['X']['byggd'][u] = (pose[:, :3] / 100 @ q.T + tw) * 100
                # GOLV2: golvsteget flyttar inte cam_t, så stabil och byggd delar translation.
                L['X']['stabil'][u] = (s['pose'][f][:, :3] / 100 @ q.T + tw) * 100
                L['X']['ra'][u] = (rp / 100 @ q.T + tw + qf @ (rt - s['cam_t'][f])) * 100
        for L in lager:
            mh, mw = L['mask'].shape[1:]; ovr = {}
            for u in range(*d['ut']):
                f = d['lokal_start'] + u - d['ut'][0] if plan.get('scener') else plan['kallrutor'][u]
                sil = L['sil'].get(u)
                if sil is None or str(f) not in L['boxar']: continue
                andra = None
                for M2 in lager:
                    if M2 is not L and M2['sil'].get(u) is not None: andra = M2['sil'][u] if andra is None else andra | M2['sil'][u]
                box = np.array(L['boxar'][str(f)]) * [mw / w, mh / h, mw / w, mh / h]
                r = jamfor_mask(sil, L['mask'][f], box, mw, mh, andra)
                if r: L['res'].append(r)
            us = sorted(L['X']['byggd']); jit = {}
            for namn in ('byggd', 'stabil', 'ra'):
                A = np.full((range(*d['ut']).stop - d['ut'][0], 127, 3), np.nan)
                for u in us: A[u - d['ut'][0]] = L['X'][namn][u]
                jit[namn] = jitter(A)
            sk = L['skipp']; bedomda = len(us)
            rader.append(dict(scen=d['id'], person=L['pm']['id'], ruta_antal=n_scen, passning_bedomda=bedomda, ej_i_bild=sk['ej_i_bild'], opalitliga=sk['opalitlig'], ravdata_saknas=sk['ravdata_saknas'],
                              tackning=bedomda / max(n_scen, 1), mask=sammanfatta(L['res']), mask_rutor_av=n_scen - sk['ej_i_bild'],
                              referens_estimator=sammanfatta(L['ref']), darr_cm_per_ruta2=jit, bildskydd_stabil_andel=L['bildskydd']))
    return rader


# Källfiler, geometri, tidsurval och mätkamera ingår i nyckeln. Färg och props
# påverkar inte kroppsmåttet. Bara små sammanfattningar cachas, aldrig hudnät.
_MATT_CACHE = {}

def _matt_nyckel(plan, stod):
    import hashlib
    import json
    scener = plan.get('scener') or plan.get('matkamera', {}).get('scener') or []
    sources = {HIT.parent/'ingest/metrisk.py', HIT/'tro_hud.npz', HIT/'tro_fothud.npz', HIT/'tro_rigg.json'}; geometry = []
    for sc in scener:
        ds = {k: sc[k] for k in ('id','ut','lokal_start','till_plats','varld') if k in sc}
        ds['personer'] = []
        sources.add(str(sc['varld']))
        for pm in sc['personer']:
            ds['personer'].append({k: pm[k] for k in ('id','ingest_id','rorelse','stod','benlangder_m','skyddade_knan','till_plats') if k in pm})
            file = Path(pm['rorelse']); folder = file.parent; pid = str(pm.get('ingest_id') or file.stem[8:])
            sources.add(str(file))
            sources.update(str(folder / n) for n in ('masker.npy','personer.json',f'palitlig_{pid}.json',f'bildskydd_{pid}.json'))
            sources.update(str(p) for p in (folder/'kropp'/pid).glob('*.npz'))
        geometry.append(ds)
    stamps=[]
    for name in sorted(sources,key=str):
        p=Path(name)
        stat=p.stat() if p.exists() else None
        stamps.append((str(name), stat.st_mtime_ns if stat else None, stat.st_size if stat else None, stat.st_ctime_ns if stat else None))
    from datacache import kodnyckel
    kod=kodnyckel([HIT/n for n in ('kroppmatt.py','datacache.py','trohet.py','trostod.py','trosula.py','tro_hud.npz','tro_fothud.npz','tro_rigg.json')]+[HIT.parent/'ingest/kroppsstod.py'])
    key=dict(kod=kod,scener=geometry, filer=stamps, stod=stod, flerklipp=bool(plan.get('scener')),
             kallrutor=plan['kallrutor'], kamera=plan.get('matkamera',plan.get('renderkamera')),
             bredd=plan['kallbild_bredd'], hojd=plan.get('kallbild_hojd'), utdata=plan['utdata'])
    return hashlib.sha256(json.dumps(key,sort_keys=True,allow_nan=False).encode('utf-8')).hexdigest()

def matt_plan(plan, stod=True):
    """Fulla mått med processlokal och beständig cache av samma sammanfattning."""
    import copy
    from datacache import hamta, spara
    key=_matt_nyckel(plan,stod)
    if key not in _MATT_CACHE:
        result=hamta('kroppmatt',key)
        if result is None:
            result=_matt_plan_utan_cache(plan,stod)
            spara('kroppmatt',key,result)
        if len(_MATT_CACHE)>=32: _MATT_CACHE.pop(next(iter(_MATT_CACHE)))
        _MATT_CACHE[key]=copy.deepcopy(result)
    return copy.deepcopy(_MATT_CACHE[key])
