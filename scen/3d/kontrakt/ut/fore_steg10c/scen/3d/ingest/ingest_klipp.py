"""Ett kommando per klipp: källklipp -> Blender-förrendering (personer i MHR-rigg, trackad kamera, golv) + jämförelsevideo.

Kör:  scen/.venv/Scripts/python.exe scen/3d/ingest/ingest_klipp.py <klipp.mp4> <utmapp> [--personer 2] [--steg 1] [--om <steg>]

Steg (vart och ett cachas i utmappen och hoppas över om utdata finns; --om <steg> tvingar omkörning från det steget):
  personer  YOLO11-seg + ByteTrack: ruta per person och bildruta (ID), personmasker för COLMAP
  kamera    COLMAP (pycolmap) på var 3:e bildruta i halv upplösning, personerna maskade -> pose + fokal.
            Faller tillbaka på stillastående kamera om under 30 % av rutorna registreras.
  kropp     SAM 3D Body (ViT-H) på Modal-GPU, en körning per person och bildruta
  sekvens   MHR-skelett per person (identiteten låst, luckor fylls med slerp)
  varld     metrisk värld: COLMAP-skalan väljs så att personernas rotbanor blir jämnast; gravitationen från ryggarna
  blender   headless Blender: riggar, kamera, golv, ljud -> scen.blend + Workbench-rendering
  jamfor    källa | överlägg | rendering med originalljud (H.264 Main, AAC stereo, faststart)
Allt motiveras i scen/3d/klipp2/PROCESS.md.
"""
import sys, os, json, time, subprocess, shutil, argparse, hashlib
from pathlib import Path
import numpy as np, cv2
from sakra_filer import sakerhetskopiera, arkivera
from regler import kamerabeslut, kort_kamerabana, overkropp, kamerabana_rimlig, skala_bestamd

HIT = Path(__file__).resolve().parent; SCEN = HIT.parent.parent
PY = SCEN / '.venv/Scripts/python.exe'; PY_SAM = SCEN / '3d/klipp2/sam3db/.venv/Scripts/python.exe'
MODAL = SCEN / '.venv/Scripts/modal.exe'; BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
YOLO = SCEN / 'py/modeller/yolo11n-seg.pt'; MHR = SCEN / '3d/klipp2/sam3db/ckpt-vith/assets/mhr_model.pt'
STEG = ['personer', 'kamera', 'kropp', 'sekvens', 'varld', 'golv', 'kontakt', 'rum', 'blender', 'jamfor']
F = np.diag([1., -1., -1.])
# Maskprompt till SAM 3D Body (personmasker.py) prövades 9 nov på barklippet och gav SÄMRE resultat (2D-avvikelse 1,9 -> 16 %,
# bålskak p95 1,8 -> 8,9 cm). Av som standard; slå på med --maskprompt för nya försök.
MASKPROMPT = False


def logg(ut, steg, sek, **x):
    p = ut / 'tider.json'; d = json.loads(p.read_text()) if p.exists() else {}
    d[steg] = dict(sek=round(sek, 1), **x); p.write_text(json.dumps(d, indent=1)); print(f'[{steg}] {sek:.1f} s', x, flush=True)
    if steg in ('sekvens', 'varld', 'golv', 'kontakt', 'jamn_omkorning'):
        from kallstatus import varna
        varna(ut)


def meta(klipp, ut):
    cap = cv2.VideoCapture(str(klipp)); m = dict(fps=cap.get(cv2.CAP_PROP_FPS), bredd=int(cap.get(3)), hojd=int(cap.get(4)), N=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    # Äldre rum-cache hashar hela meta.json. Lägg inte till fält i en oförändrad
    # äldre körning: då skulle rum och efterföljande steg köras om enbart för proveniens.
    p = ut / 'meta.json'
    try: fore = json.loads(p.read_text()) if p.exists() else None   # tom/trasig fil (avbruten skrivning) räknas som saknad
    except (ValueError, OSError): fore = None
    if isinstance(fore, dict) and 'kallvideo' not in fore and all(fore.get(k) == v for k, v in m.items()): return m
    try:
        with klipp.open('rb') as f:
            h = hashlib.sha256()
            for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
        m.update(kallvideo=str(klipp.resolve()), kallvideo_sha256=h.hexdigest())
    except OSError: pass   # saknad video: som förr, meta utan proveniens (ingen krasch här)
    tmp = p.with_suffix('.tmp'); tmp.write_text(json.dumps(m)); tmp.replace(p); return m


def sla_ihop(rutor, M, max_lucka=45):
    """Knyt ihop spårfragment: ett fragment som börjar efter att ett annat slutat (ingen tidsöverlapp),
    inom max_lucka bildrutor och med närliggande ruta (mitt-avstånd < 0,6 ruthöjd, liknande storlek), slås ihop. Girigt, längsta först."""
    fr = {t: (min(d), max(d)) for t, d in rutor.items()}
    def mitt(b): return np.array([(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]), b[3] - b[1]
    ordning = sorted(rutor, key=lambda t: -len(rutor[t])); bytt = True
    while bytt:
        bytt = False
        for a in ordning:
            if a not in rutor: continue
            for b in sorted(rutor, key=lambda t: fr[t][0]):
                if b == a or b not in rutor: continue
                if fr[b][0] <= fr[a][1] or fr[b][0] - fr[a][1] > max_lucka: continue
                (ca, ha), (cb, hb) = mitt(rutor[a][fr[a][1]]), mitt(rutor[b][fr[b][0]])
                if np.linalg.norm(ca - cb) < .6 * max(ha, hb) and .6 < hb / ha < 1.6:
                    rutor[a].update(rutor.pop(b)); fr[a] = (fr[a][0], fr[b][1]); bytt = True
    return rutor


def steg_personer(klipp, ut, M, n_personer):
    from ultralytics import YOLO as Y
    mod = Y(str(YOLO)); rutor = {}; ms = 4; mask = np.zeros((M['N'], M['hojd'] // ms, M['bredd'] // ms), bool)
    for i, r in enumerate(mod.track(str(klipp), classes=[0], conf=.3, persist=True, tracker=str(HIT / 'spar.yaml'), retina_masks=False, stream=True, verbose=False)):
        if r.boxes is None or r.boxes.id is None: continue
        for b, tid in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.id.cpu().numpy().astype(int)):
            rutor.setdefault(int(tid), {})[i] = [float(x) for x in b]
        if r.masks is not None:
            for mm in r.masks.data.cpu().numpy():
                mask[i] |= cv2.resize(mm.astype(np.uint8), (M['bredd'] // ms, M['hojd'] // ms), interpolation=cv2.INTER_NEAREST) > 0
    rutor = sla_ihop(rutor, M)
    # välj de mest närvarande och största personerna
    poang = {t: len(d) * np.median([(b[2] - b[0]) * (b[3] - b[1]) for b in d.values()]) for t, d in rutor.items() if len(d) >= .2 * M['N']}
    valda = sorted(poang, key=lambda t: -poang[t])[:n_personer]
    mask = np.stack([cv2.dilate(m.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0 for m in mask])
    np.save(ut / 'masker.npy', mask)
    (ut / 'personer.json').write_text(json.dumps({str(t): rutor[t] for t in valda}))
    return dict(id=valda, alla_id=len(rutor), narvaro={str(t): len(rutor[t]) for t in valda})


def steg_kamera(klipp, ut, M):
    import pycolmap
    d = ut / 'colmap'; arkivera(d); (d / 'bilder').mkdir(parents=True); (d / 'masker').mkdir()
    mask = np.load(ut / 'masker.npy'); cap = cv2.VideoCapture(str(klipp)); w, h = M['bredd'] // 2, M['hojd'] // 2
    for i in range(M['N']):
        ok, f = cap.read()
        if not ok: break
        if i % 3 == 0 and f.mean() > 8:      # hoppa över svarta rutor
            cv2.imwrite(str(d / f'bilder/{i:04d}.jpg'), cv2.resize(f, (w, h)), [cv2.IMWRITE_JPEG_QUALITY, 92])
            cv2.imwrite(str(d / f'masker/{i:04d}.jpg.png'), np.where(cv2.resize(mask[i].astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0, 0, 255).astype(np.uint8))
    db = d / 'db.db'; eo = pycolmap.FeatureExtractionOptions(); eo.sift.max_num_features = 4000
    ro = pycolmap.ImageReaderOptions(); ro.mask_path = str(d / 'masker'); ro.camera_model = 'SIMPLE_RADIAL'
    pycolmap.extract_features(db, d / 'bilder', camera_mode=pycolmap.CameraMode.SINGLE, reader_options=ro, extraction_options=eo)
    po = pycolmap.SequentialPairingOptions(); po.overlap = 12; pycolmap.match_sequential(db, pairing_options=po)
    (d / 'sparse').mkdir(); recs = pycolmap.incremental_mapping(db, d / 'bilder', d / 'sparse')
    antal = len(list((d / 'bilder').iterdir()))
    if not recs:
        x = dict(registrerade=0, av=antal, fel_px=None, fokal_px=None, statisk=True)
        x['beslut'] = kamerabeslut(x, M)
        (ut / 'kamera.json').write_text(json.dumps(x))
        return x
    rec = max(recs.values(), key=lambda r: r.num_reg_images()); cam = list(rec.cameras.values())[0]
    pose = {}
    for im in rec.images.values():
        T = im.cam_from_world() if callable(im.cam_from_world) else im.cam_from_world
        Rcw = np.array(T.rotation.matrix()); pose[int(im.name[:4])] = (Rcw.T.tolist(), (-Rcw.T @ np.array(T.translation)).tolist())
    reg = rec.num_reg_images(); statisk = reg < .3 * antal
    x = dict(registrerade=reg, av=antal, fel_px=round(rec.compute_mean_reprojection_error(), 3), fokal_px=float(cam.params[0]) * 2, statisk=statisk, pose=pose)
    x['beslut'] = kamerabeslut(x, M)
    x['statisk'] = statisk or x['beslut']['kalla'] != 'COLMAP'
    (ut / 'kamera.json').write_text(json.dumps(x)); x.pop('pose'); return x


def steg_kropp(klipp, ut, M, steg):
    P = json.loads((ut / 'personer.json').read_text()); K = json.loads((ut / 'kamera.json').read_text()) if (ut / 'kamera.json').exists() else {}
    beslut = kamerabeslut(K, M)
    fokal = beslut['fokal_px']     # utan COLMAP: grov gissning (SAM 3D Body tål det)
    jobb = [[int(i), pid, b] for pid, d in P.items() for i, b in d.items() if int(i) % steg == 0]
    (ut / 'kropp_indata.json').write_text(json.dumps(dict(kamera=beslut, personrutor=len(jobb), personer=list(P))))
    (ut / 'jobb.json').write_text(json.dumps(jobb))
    if not jobb:
        (ut / 'kropp').mkdir(exist_ok=True)
        (ut / 'kropp/timing.json').write_text(json.dumps(dict(jobb=0, status='uppmatt', orsak='Inga personer; inget GPU-anrop.')))
        return dict(jobb=0)
    r = subprocess.run([str(MODAL), 'run', str(HIT / 'modal_sam3db.py'), '--klipp', str(klipp), '--jobb', str(ut / 'jobb.json'), '--ut', str(ut / 'kropp'), '--fokal', str(fokal)] + (['--masker', str(ut / 'personmasker')] if MASKPROMPT and (ut / 'personmasker').exists() else []),
                       capture_output=True, text=True, encoding='utf-8', errors='replace', env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUNBUFFERED': '1'})
    (ut / 'modal.log').write_text(r.stdout + r.stderr, encoding='utf-8')
    if r.returncode: raise SystemExit('modal: ' + (r.stdout + r.stderr)[-1500:])
    return json.loads((ut / 'kropp/timing.json').read_text())


def synlighet(ut, M, pid):
    """Benen räknas som synliga om minst ett knä (MHR70 13–14) ligger i bild OCH inom personmasken. Vristerna krävs inte,
    eftersom de ofta är beskurna och modellen härleder underbenet väl från låret. Skymda knän (t.ex. bakom en bardisk) -> hållna ben."""
    mask = np.load(ut / 'masker.npy'); ms = M['bredd'] / mask.shape[2]; ut_ = {}
    for f in sorted((ut / 'kropp' / pid).glob('*.npz')):
        i = int(f.stem); k = np.load(f)['pred_keypoints_2d'][13:15]; n = 0
        for x, y in k:
            if 0 <= x < M['bredd'] and 0 <= y < M['hojd'] and mask[i, int(y / ms), int(x / ms)]: n += 1
        ut_[i] = n >= 1
    return ut_


def palitlighet(ut, M, pid, min_bild=.35, min_mask=.15):
    """En anpassning är tillförlitlig om minst 35 % av kroppens 21 första MHR70-punkter ligger i bild och minst 15 % inom
    personmaskerna. Under det (personen går ut ur bild, skyms nästan helt) gissar modellen; barklippet ruta 182–201 gav
    skräpkroppar som flög (vakt: rot 7 m/s, 2D-avvikelse 87 %)."""
    mask = np.load(ut / 'masker.npy'); ms = M['bredd'] / mask.shape[2]; ut_ = {}
    for f in sorted((ut / 'kropp' / pid).glob('*.npz')):
        i = int(f.stem); k = np.load(f)['pred_keypoints_2d'][:21]
        ib = [0 <= x < M['bredd'] and 0 <= y < M['hojd'] for x, y in k]
        im = [b and mask[i, int(y / ms), int(x / ms)] for b, (x, y) in zip(ib, k)]
        ut_[i] = bool(np.mean(ib) >= min_bild and np.mean(im) >= min_mask)
    return ut_


def steg_sekvens(ut, M):
    from scipy.signal import savgol_filter
    P = json.loads((ut / 'personer.json').read_text()); x = {}
    for pid in P:
        syn = synlighet(ut, M, pid); (ut / f'synlighet_{pid}.json').write_text(json.dumps(syn))
        (ut / f'palitlig_{pid}.json').write_text(json.dumps(palitlighet(ut, M, pid)))
        s = ut / f'sekvens_{pid}.npz'
        r = subprocess.run([str(PY_SAM), str(HIT / 'sekvens_stabil.py'), str(ut / 'kropp' / pid), str(ut / f'synlighet_{pid}.json'), str(s), str(M['N']), str(M['fps']),
                            str(ut / f'palitlig_{pid}.json')],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode: raise SystemExit('sekvens: ' + r.stderr[-1500:])
        x[pid] = json.loads(r.stdout.strip().splitlines()[-1])
        x[pid]['utsnitt'] = overkropp(x[pid])
        # Knän krävs inne i både egen personruta och bild. Maskunion ensam räcker inte.
        knan = []
        for raw in (ut / 'kropp' / pid).glob('*.npz'):
            f = str(int(raw.stem)); box = P[pid].get(f)
            if box is None: continue
            kp = np.load(raw)['pred_keypoints_2d'][11:13]
            knan.append(any(0 <= xx < M['bredd'] and 0 <= yy < M['hojd'] and box[0] <= xx <= box[2] and box[1] <= yy <= box[3] for xx, yy in kp))
        if knan and np.mean(knan) < .1:
            x[pid]['utsnitt'].update(endast_overkropp=True, knan_i_egen_ruta_andel=float(np.mean(knan)), orsak='Under 10 % rutor med skattat knä i bild och egen personruta; underkroppen saknar bildstöd.')
        (ut / f'utsnitt_{pid}.json').write_text(json.dumps(x[pid]['utsnitt']))
        # cam_t utjämnas nu i sekvens_stabil.py (siktlinje + log-avstånd, rör-utjämning); det gamla Hampel/Butterworth-blocket och bildskyddet är borta (10 nov)
        S = dict(np.load(s))
        np.savez(s, **S)
    return x


def steg_golv(ut, M, kamerahojd=1.45):
    """Golvkontakt: personen flyttas längs kamerans siktlinje (cam_t·s), vilket inte ändrar var den syns i bild, tills
    lägsta foten står på golvet. Golvet tas från rutor där benen syns, och annars från antagen kamerahöjd."""
    from scipy.signal import butter, filtfilt
    V = np.load(ut / 'varld.npz'); R, C, u = V['kam_R'], V['kam_C'], V['upp']; N = len(R)
    FOT = [4, 8, 20, 24]                                   # l_foot, l_ball, r_foot, r_ball (led = ben + 1)
    seq = {p.stem[8:]: dict(np.load(p)) for p in sorted(ut.glob('sekvens_*.npz'))}
    for S in seq.values():                                 # idempotent: utgå alltid från cam_t före golv- och kontaktstegen
        if 'cam_t_fore_golv' in S: S['cam_t'] = S['cam_t_fore_golv'].copy()
        else: S['cam_t_fore_golv'] = S['cam_t'].copy()
        S.pop('cam_t_fore_kontakt', None)
    def fothojd(S, i, sk=1.0):
        X = np.array([C[i] + R[i] @ (F @ (S['pose'][i, j, :3] / 100) + sk * S['cam_t'][i]) for j in FOT]); h = X @ u
        return h.min(), FOT[int(h.argmin())]
    synliga = [fothojd(S, i)[0] for S in seq.values() for i in range(N) if S['inom'][i] and S['ben_synliga'][i]]
    kam_h = float(np.median(C @ u))
    golv = float(np.percentile(synliga, 10)) if len(synliga) >= 10 else kam_h - kamerahojd
    kalla = 'synliga fötter' if len(synliga) >= 10 else f'antagen kamerahöjd {kamerahojd} m'
    x = dict(golv_h=round(golv, 3), kamerahojd_over_golv=round(kam_h - golv, 2), kalla=kalla)
    for pid, S in seq.items():
        utsnitt = json.loads((ut / f'utsnitt_{pid}.json').read_text()) if (ut / f'utsnitt_{pid}.json').exists() else {}
        if utsnitt.get('endast_overkropp'):
            S['golv_skala'] = np.ones(N)
            np.savez(ut / f'sekvens_{pid}.npz', **S)
            x[pid] = dict(status='saknas', orsak='Endast överkropp; golvkontakt används inte.')
            continue
        sk = np.ones(N)
        for i in np.nonzero(S['inom'])[0]:
            _, j = fothojd(S, i); bas = (C[i] + R[i] @ (F @ (S['pose'][i, j, :3] / 100))) @ u; d = (R[i] @ S['cam_t'][i]) @ u
            if abs(d) > .08 * np.linalg.norm(S['cam_t'][i]): sk[i] = np.clip((golv - bas) / d, .5, 2.0)
        ii = np.nonzero(S['inom'])[0]
        if S['ben_synliga'][ii].mean() < .2:
            # benen syns nästan aldrig (bakom disk, utanför bild): fothöjden är modellens gissning, så en skala per ruta
            # bara för vidare gissningsbruset till djupet (barklippet: ×1,6 på 5 rutor). En konstant skala behåller kroppen på golvet i snitt.
            sk[ii] = np.median(sk[ii])
        elif len(ii) > 12:
            b, a = butter(2, 1.5 / (M['fps'] / 2)); sk[ii[0]:ii[-1] + 1] = filtfilt(b, a, sk[ii[0]:ii[-1] + 1])
        S['cam_t'] = S['cam_t'] * sk[:, None]; S['golv_skala'] = sk
        np.savez(ut / f'sekvens_{pid}.npz', **S)
        efter = [fothojd(S, i)[0] - golv for i in ii]
        x[pid] = dict(skala_median=round(float(np.median(sk[ii])), 3), fot_over_golv_cm_median=round(float(np.median(efter)) * 100, 1),
                      p90_abs_cm=round(float(np.percentile(np.abs(efter), 90)) * 100, 1))
    V = dict(V); V['golv_h'] = golv; np.savez(ut / 'varld.npz', **V)
    return x


def steg_varld(ut, M):
    from scipy.spatial.transform import Rotation as Ro, Slerp
    N = M['N']; K = json.loads((ut / 'kamera.json').read_text()) if (ut / 'kamera.json').exists() else {}
    seq = {p.stem[8:]: np.load(p) for p in sorted(ut.glob('sekvens_*.npz'))}
    kb = kamerabeslut(K, M)
    if K.get('pose') and not K.get('statisk') and kb['kalla'] == 'COLMAP':
        pose = {int(i): (np.array(r), np.array(c)) for i, (r, c) in K['pose'].items()}; idx = sorted(pose)
        def ip(i):
            if i in pose: return pose[i]
            a = max([j for j in idx if j < i], default=idx[0]); b = min([j for j in idx if j > i], default=idx[-1])
            if a == b: return pose[a]
            t = (i - a) / (b - a); return Slerp([0, 1], Ro.from_matrix([pose[a][0], pose[b][0]]))(t).as_matrix(), (1 - t) * pose[a][1] + t * pose[b][1]
        RC = [ip(i) for i in range(N)]; R = np.stack([r for r, _ in RC]); C = np.stack([c for _, c in RC])
    else:
        R = np.repeat(np.eye(3)[None], N, 0); C = np.zeros((N, 3))
    rot = {p: np.stack([F @ (S['pose'][i, 1, :3] / 100) + S['cam_t'][i] for i in range(N)]) for p, S in seq.items()}
    nacke = {p: np.stack([F @ (S['pose'][i, 110, :3] / 100) + S['cam_t'][i] for i in range(N)]) for p, S in seq.items()}
    def ojamn(k):
        return sum(np.abs(np.diff(np.stack([k * C[i] + R[i] @ rot[p][i] for i in range(N)])[seq[p]['inom']], 2, axis=0)).mean() for p in seq)
    obestamd = False
    if np.allclose(C, 0): k = 1.0
    else:
        ks = np.exp(np.linspace(np.log(1e-4), np.log(1e3), 800)); oj = np.array([ojamn(k) for k in ks]); k = float(ks[int(np.argmin(oj))])
        # kenny S2 (10 nov): kameran stod still medan personen syntes, så ojämnheten var platt över alla k och minimum blev slumpmässigt (k = 785,
        # kamerabana 11,7 km). En platt kurva betyder att skalan inte går att bestämma ur denna tagning.
        obestamd = not skala_bestamd(oj)
    skalbeslut = dict(status='uppmatt', **{a: b for a, b in kamerabana_rimlig(k * C, M['fps']).items() if a in ('p90_fart_m_s', 'max_fart_m_s', 'vag_m', 'granser', 'skal')}, grans_m_s=5.)
    if obestamd:
        skalbeslut.update(status='antagen', orsak='Skalan oidentifierbar: rotbanans ojämnhet är platt över k (kameran stod still medan personen syntes). Translation avvisad, rotation behålls.')
        C = np.zeros_like(C); k = 1.0
    elif skalbeslut['skal']:
        skalbeslut.update(status='antagen', orsak='Metrisk translation avvisad, fysiskt orimlig bana för handhållen mobil: ' + '; '.join(skalbeslut['skal']) + '. Rotation behålls, kamera utan känd translation.')
        C = np.zeros_like(C); k = 1.0
    bana = kort_kamerabana(k * C)
    if bana['statisk']:
        # Kort translation säger inget om kamerans rotation.
        C = np.zeros((N, 3)); k = 1.0
    upp = np.mean([R[i] @ ((nacke[p][i] - rot[p][i]) / np.linalg.norm(nacke[p][i] - rot[p][i])) for p in seq for i in range(N) if seq[p]['inom'][i]], 0) if seq else np.array([0., -1., 0.])
    np.savez(ut / 'varld.npz', kam_R=R, kam_C=k * C, k=k, upp=upp / np.linalg.norm(upp), metriskt_skalbeslut=np.array(json.dumps(skalbeslut)), metrisk_translation_avvisad=skalbeslut['status']=='antagen')
    vag = float(np.linalg.norm(np.diff(k * C, axis=0), axis=1).sum())
    return dict(skala=round(k, 4), ojamnhet_cm=round(ojamn(k) * 100, 3), kamerans_vag_m=round(vag, 2), kamerabeslut=kb, banbeslut=bana, skalbeslut=skalbeslut, upp_kalla='kroppsmodell' if seq else 'antagen: lodrät kamera utan personer')


def steg_blender(klipp, ut):
    arkivera(ut / 'render')
    r = subprocess.run([BLENDER, '-b', '--factory-startup', '--python', str(HIT / 'mhr_rig.py'), '--', str(ut), str(klipp), '--render'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    (ut / 'blender.log').write_text(r.stdout[-20000:] + r.stderr[-5000:], encoding='utf-8')
    if r.returncode or not (ut / 'scen.blend').exists(): raise SystemExit('blender: ' + (r.stdout + r.stderr)[-1500:])
    return dict(rutor=len(list((ut / 'render').glob('*.png'))))


def steg_jamfor(klipp, ut, M):
    w, h = 540, int(540 * M['hojd'] / M['bredd']) // 2 * 2
    f = (f"[0:v]scale={w}:{h},setsar=1,split[a1][a2];[1:v]scale={w}:{h},format=rgba,split[r1][r2];[r1]colorchannelmixer=aa=0.55[r1a];"
         f"[a2][r1a]overlay[o];color=c=0x3a3a3a:s={w}x{h}:r={round(M['fps'])}[bg];[bg][r2]overlay=shortest=1[ren];[a1][o][ren]hstack=3[v]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(klipp), '-framerate', str(M['fps']), '-start_number', '0', '-i', str(ut / 'render/f%04d.png'),
                    '-filter_complex', f, '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-profile:v', 'main', '-pix_fmt', 'yuv420p', '-crf', '20',
                    '-c:a', 'aac', '-ac', '2', '-ar', '48000', '-movflags', '+faststart', '-shortest', str(ut / 'jamforelse.mp4')], check=True)
    return dict(fil=str(ut / 'jamforelse.mp4'))


ARTEFAKTER = dict(personer=['personer.json', 'masker.npy'], kamera=['kamera.json', 'colmap'], kropp=['kropp', 'jobb.json', 'modal.log'],
                  sekvens=['sekvens.klar', 'sekvens_*.npz', 'palitlig_*.json'], varld=['varld.npz'], golv=['golv.klar'], kontakt=['kontakt.klar', 'kontakt_*.json'],
                  rum=['rum.json', 'rum.md', 'rum/cache.json', 'rum/cloud.npz', 'rum/overlay.jpg'],
                  blender=['scen.blend', 'scen.blend1', 'render', 'blender.log'], jamfor=['jamforelse.mp4'])


def rensa_efter(ut, steg):
    for s in STEG[STEG.index(steg):]:
        for m in ARTEFAKTER[s]:
            for p in ut.glob(m):
                arkivera(p)


def main():
    a = argparse.ArgumentParser(); a.add_argument('klipp'); a.add_argument('ut'); a.add_argument('--personer', type=int, default=2)
    a.add_argument('--steg', type=int, default=1); a.add_argument('--maskprompt', action='store_true'); a.add_argument('--om', default=None); a.add_argument('--till', choices=STEG); x = a.parse_args()
    global MASKPROMPT; MASKPROMPT = x.maskprompt
    klipp, ut = Path(x.klipp).resolve(), Path(x.ut).resolve(); ut.mkdir(parents=True, exist_ok=True)
    sakerhetskopiera(ut)
    M = meta(klipp, ut); fran = STEG.index(x.om) if x.om else len(STEG)
    klart = dict(personer=ut / 'personer.json', kamera=ut / 'kamera.json', kropp=ut / 'kropp/timing.json', sekvens=ut / 'sekvens.klar',
                 varld=ut / 'varld.npz', golv=ut / 'golv.klar', kontakt=ut / 'kontakt.klar', rum=ut / 'rum.json', blender=ut / 'scen.blend', jamfor=ut / 'jamforelse.mp4')
    T0 = time.time(); cached = []
    for i, s in enumerate(STEG):
        if x.till and i > STEG.index(x.till): break
        valid = klart[s].exists()
        if s == 'kamera' and not valid and (ut / 'tider.json').exists():
            # Noll registrerade rutor är också ett färdigt kameraresultat.
            k = json.loads((ut / 'tider.json').read_text()).get('kamera', {})
            valid = k.get('statisk') is True and k.get('registrerade') == 0 and (ut / 'varld.npz').exists()
        if s == 'rum' and valid:
            from rum import cache_valid
            valid = cache_valid(klipp, ut)
        if valid and i < fran:
            print(f'[{s}] cachad', flush=True); cached.append(s); continue
        t = time.time()
        rensa_efter(ut, s)   # ett omkört steg gör alla senare steg ogiltiga: ta bort deras utdata
        if s == 'personer': r = steg_personer(klipp, ut, M, x.personer)
        elif s == 'kamera': r = steg_kamera(klipp, ut, M)
        elif s == 'kropp': r = steg_kropp(klipp, ut, M, x.steg)
        elif s == 'sekvens': r = steg_sekvens(ut, M); klart[s].write_text('ok')
        elif s == 'varld': r = steg_varld(ut, M)
        elif s == 'golv': r = steg_golv(ut, M); klart[s].write_text('ok')
        elif s == 'kontakt':
            from kontakt import steg_kontakt
            r = steg_kontakt(ut, M); klart[s].write_text('ok')
        elif s == 'rum':
            from rum import steg_rum
            r = steg_rum(klipp, ut, M)
        elif s == 'blender': r = steg_blender(klipp, ut)
        else: r = steg_jamfor(klipp, ut, M)
        logg(ut, s, time.time() - t, **r); fran = min(fran, i)   # ett omkört steg tvingar alla senare steg
    logg(ut, 'senaste_korning', time.time() - T0, cachade_steg=cached)
    print(f'klart på {time.time() - T0:.1f} s -> {ut}', flush=True)


if __name__ == '__main__':
    main()
