"""Jämför utjämningsmetoder för kroppssekvensen på de sparade rå-estimaten (kropp/). Ingen betald körning, inga nya kroppsanrop.

    scen/.venv/Scripts/python.exe scen/3d/ingest/jamn_utvardera.py <ingestmapp>/<tagning> [...] [--ut tabell.json]

Per metod mäts (alla i tagningens egen kamera, före golv- och kontaktstegen, så att metoderna är jämförbara):
- px: avvikelse mot estimatorns egna 2D-punkter (median/p90, bara pålitliga rutor). INTE oberoende: bildskyddet passar mot samma punkter.
- IoU: byggd kropp (hudnätets silhuett) mot YOLO-masken inom personens ruta, på alla rutor där masken finns (oberoende modell). `synlig` = nätet klippt vid maskens nedersta rad.
- darr: medel andra differens av ledpositionerna (cm/ruta²), kamerarum, pålitliga rutor, hela 127 leder.
- täckning: rutor som bedömts / rutor i tagningen (inom).
Metoder: raw (estimatorn), gammal (Hampel + 6 Hz lågpass, som före 10 nov), bildskydd (gammal + ruta-för-ruta-blandning mot estimatet),
sg (Savitzky-Golay 9/3 på estimatet), oneeuro (dubbelriktad), whittaker (utan rör), samt rör-utjämning med olika fc och k.
"""
import sys, os, json, glob
from pathlib import Path
import numpy as np
import torch
from scipy.signal import butter, filtfilt, savgol_filter
from scipy.spatial.transform import Rotation as Rot

HIT = Path(__file__).resolve().parent
sys.path[:0] = [str(HIT), str(HIT.parent / 'kontrakt')]
import sekvens_jamn as J
import kroppmatt as KM
from trohet import KP, LED

F = np.diag([1., -1., -1.])
SAM = HIT.parent / 'klipp2' / 'sam3db'
NAMN = json.load(open(SAM / 'mhr_parametrar.json'))
BEN = np.array([i for i, n in enumerate(NAMN) if any(k in n for k in ('upleg', 'knee', 'lowleg', 'foot')) and not n.startswith('scale')])
HAND = np.array([i for i, n in enumerate(NAMN) if any(k in n for k in ('thumb', 'index', 'middle', 'ring', 'pinky', 'wrist'))])
ROT = [NAMN.index(n) for n in ('root_rx', 'root_ry', 'root_rz')]
VRID = np.array([i for i, n in enumerate(NAMN) if ('twist' in n or 'wrist' in n or 'lowarm' in n) and not n.startswith('scale')])
BEDOM = np.setdiff1d(np.arange(208), np.concatenate([BEN, HAND, ROT])); QK = np.arange(204, 208)
_M = []
KOMBOS = None
HANDVARIANTER = False


def modell():
    if not _M: _M.append(torch.jit.load(str(SAM / 'ckpt-vith/assets/mhr_model.pt'), map_location='cpu'))
    return _M[0]


def fk(shape, P, E):
    out = []
    with torch.no_grad():
        for b in np.array_split(np.arange(len(P)), max(1, len(P) // 64)):
            out.append(modell()(torch.tensor(shape[b]).float(), torch.tensor(P[b]).float(), torch.tensor(E[b]).float())[1].numpy())
    return np.concatenate(out).astype(float)


def las(folder, pid, N):
    D = {int(os.path.basename(f)[:4]): np.load(f) for f in sorted(glob.glob(f'{folder}/kropp/{pid}/*.npz'))}
    idx = sorted(D); R = dict(idx=idx)
    for k, key in dict(P='mhr_model_params', E='expr_params', T='pred_cam_t', S='shape_params', KP='pred_keypoints_2d', FOC='focal_length', BB='bbox').items():
        X = np.full((N,) + np.asarray(D[idx[0]][key]).shape, np.nan)
        for i in idx: X[i] = D[i][key]
        R[k] = X
    return R


# ---------- det gamla (före 10 nov), kopierat ur sekvens_stabil.py/ingest_klipp.py för jämförelse ----------
def hampel(X, k=4, n=3.0):
    X = X.copy(); cnt = 0
    for i in range(len(X)):
        a, b = max(0, i - k), min(len(X), i + k + 1); med = np.median(X[a:b], 0); mad = 1.4826 * np.median(np.abs(X[a:b] - med), 0) + 1e-6
        dev = (np.abs(X[i] - med) / mad)[BEDOM]
        if (dev > n).mean() > .15 or (np.abs(X[i, QK] - med[QK]) / mad[QK]).max() > n * 2: X[i] = med; cnt += 1
    return X, cnt


def hampel_komp(X, cols, k=3, n=3.0, golv=.35):
    X = X.copy()
    for i in range(len(X)):
        a, b = max(0, i - k), min(len(X), i + k + 1); med = np.median(X[a:b, cols], 0); mad = 1.4826 * np.median(np.abs(X[a:b, cols] - med), 0)
        byt = (np.abs(X[i, cols] - med) > np.maximum(n * mad, golv)); X[i, cols[byt]] = med[byt]
    return X


def fartgrans(X, cols, m=.3):
    F_ = X[:, cols].copy(); B_ = X[:, cols].copy()
    for i in range(1, len(X)): F_[i] = np.clip(F_[i], F_[i - 1] - m, F_[i - 1] + m)
    for i in range(len(X) - 2, -1, -1): B_[i] = np.clip(B_[i], B_[i + 1] - m, B_[i + 1] + m)
    X = X.copy(); X[:, cols] = (F_ + B_) / 2; return X


def fyll(X, N):
    X = X.copy(); r = np.arange(N); ok = ~np.isnan(X[:, 0])
    for j in range(X.shape[1]): X[:, j] = np.interp(r, r[ok], X[ok, j])
    return X


def gemensam_forberedelse(R, syn, pal, N):
    """Delen som alla metoder delar: pålitliga rutor, kvaternionsrot, benhållning från närmaste ruta med synliga ben."""
    idx = list(R['idx']); kand = np.zeros(N, bool); kand[idx] = True
    inom = np.zeros(N, bool); inom[idx[0]:idx[-1] + 1] = True
    otillf = [i for i in idx if not pal.get(str(i), True)]
    if len(otillf) < len(idx) - 2: idx = [i for i in idx if pal.get(str(i), True)]
    P = np.full((N, 204), np.nan); E = np.full((N, 72), np.nan); Q = np.full((N, 4), np.nan)
    for i in idx: P[i] = R['P'][i]; E[i] = R['E'][i]
    Q[idx] = Rot.from_euler('xyz', P[idx][:, ROT]).as_quat()
    Q = J.kvaternion_kontinuerlig(Q, ~np.isnan(Q[:, 0]))
    benvis = np.array([bool(syn.get(str(i), False)) for i in range(N)]) & kand
    return dict(idx=idx, kand=kand, inom=inom, P=P, E=E, Q=Q, benvis=benvis, giltig=~np.isnan(P[:, 0]))


def till_euler(P, Q):
    Qf = Q / np.linalg.norm(Q, axis=1, keepdims=True); P = P[:, :204].copy(); P[:, ROT] = Rot.from_quat(Qf).as_euler('xyz'); return P


def gammal_stab(G, N, fps):
    P, E, Q = fyll(G['P'], N), fyll(G['E'], N), fyll(G['Q'], N); P = P.copy(); P[:, ROT] = 0; P = np.concatenate([P, Q], 1)
    P, _ = hampel(P); P = hampel_komp(P, VRID); P = fartgrans(P, VRID)
    inom, benvis = G['inom'], G['benvis']
    if benvis.any():
        sl = np.nonzero(benvis)[0]
        for i in np.nonzero(inom & ~benvis)[0]: P[i, BEN] = P[sl[np.argmin(np.abs(sl - i))], BEN]
    else: P[:, BEN] = 0.0
    idx = G['idx']

    def lp(X, fc):
        b, a = butter(2, fc / (fps / 2)); Y = X.copy(); a0, a1 = idx[0], idx[-1] + 1
        if a1 - a0 > 12: Y[a0:a1] = filtfilt(b, a, X[a0:a1], axis=0)
        return Y
    ovr = np.setdiff1d(np.arange(208), HAND); P[:, ovr] = lp(P[:, ovr], 6.0); P[:, HAND] = lp(P[:, HAND], 8.0); E = lp(E, 8.0)
    return till_euler(P, P[:, QK]), E


def gammal_t(T, G, N, fps):
    """cam_t som ingest_klipp.steg_sekvens utjämnade det."""
    T = fyll(T, N); ram = np.nonzero(G['inom'])[0]; a, b = ram[0], ram[-1] + 1
    if b - a <= 20: return T
    S = T[a:b]; d = np.linalg.norm(S, axis=1); r = S / d[:, None]; dm = d.copy()
    for i in range(len(d)):
        lo, hi = max(0, i - 7), min(len(d), i + 8); med = np.median(d[lo:hi]); mad = 1.4826 * np.median(np.abs(d[lo:hi] - med)) + 1e-3
        if abs(d[i] - med) > 3 * mad: dm[i] = med
    steg = 2.0 / fps; ank = int(np.argmin(np.abs(dm - np.median(dm))))
    for i in range(ank + 1, len(dm)): dm[i] = np.clip(dm[i], dm[i - 1] - steg, dm[i - 1] + steg)
    for i in range(ank - 1, -1, -1): dm[i] = np.clip(dm[i], dm[i + 1] - steg, dm[i + 1] + steg)
    for i in range(len(r)):
        lo, hi = max(0, i - 7), min(len(r), i + 8); med = np.median(r[lo:hi], 0); mad = 1.4826 * np.median(np.abs(r[lo:hi] - med), 0) + 2e-3
        if (np.abs(r[i] - med) > 3 * mad).any(): r[i] = med
    bb, aa = butter(2, 1.5 / (fps / 2)); dm = filtfilt(bb, aa, dm, padtype='even')
    bb, aa = butter(2, 6.0 / (fps / 2)); r = filtfilt(bb, aa, r, axis=0, padtype='even'); r /= np.linalg.norm(r, axis=1, keepdims=True)
    T = T.copy(); T[a:b] = r * dm[:, None]; return T


# ---------- nya metoder ----------
def spar(G):
    """Spårmatrisen för utjämning: alla parametrar utom rotens Euler, plus rotens kvaternion. Vikter per spår."""
    Y = np.concatenate([np.nan_to_num(G['P']), np.nan_to_num(G['Q'])], 1); Y[:, ROT] = 0.0
    w = np.repeat(G['giltig'][:, None].astype(float), 208, 1)
    return Y, w


def utanfor_giltigt(X, giltig):
    """Utanför första/sista giltiga rutan hålls värdet från närmaste giltiga ruta (ingen linjär extrapolation)."""
    ix = np.nonzero(giltig)[0]; X = X.copy(); X[:ix[0]] = X[ix[0]]; X[ix[-1] + 1:] = X[ix[-1]]; return X


def ben_vikter(G, w):
    """Ben: rutor där benen inte syns får vikt 0 på benparametrarna (utjämnaren överbryggar dem mjukt). Syns benen aldrig: neutral hållning."""
    if G['benvis'].any(): w[:, BEN] = (w[:, BEN] * G['benvis'][:, None]); return True
    return False


def ny_stab(G, N, fps, fc=4.0, k=2.0, d=2, trasiga=True, rorbredd=True, ut=None):
    Y, w = spar(G)
    # vrid/handled: tvetydiga vrid hoppar; samma fartgräns som förr (utan medianbyte)
    Yf = Y.copy(); gl = G['giltig']; ix = np.nonzero(gl)[0]
    for j in VRID: Yf[:, j] = np.interp(np.arange(N), ix, Y[ix, j])
    Yf = fartgrans(Yf, VRID); Y[:, VRID] = Yf[:, VRID]
    benfinns = ben_vikter(G, w)
    if not benfinns: w[:, BEN] = 1.0; Y[:, BEN] = 0.0
    fel = np.zeros(N, bool)
    if trasiga:
        fel = J.hitta_trasiga(Y, w[:, 0], fps, BEDOM, fc=fc, d=d)
        w[fel, :] = 0.0
    X, sigma, eps = J.utjamna(Y, w, fps, fc=fc, k=k, d=d, rorbredd=rorbredd)
    X = utanfor_giltigt(X, gl & ~fel)
    # E: uttryck, samma metod, grövre rör
    Ye = np.nan_to_num(G['E']); we = np.repeat((gl & ~fel)[:, None].astype(float), 72, 1)
    Xe, _, _ = J.utjamna(Ye, we, fps, fc=8.0, k=k, d=d); Xe = utanfor_giltigt(Xe, gl & ~fel)
    if ut is not None: ut.update(trasiga_rutor=int(fel.sum()), sigma_median=float(np.median(sigma)), eps=eps)
    return till_euler(X, X[:, QK]), Xe


def sg_stab(G, N, fps, fonster=9, ordning=3):
    Y, w = spar(G); gl = G['giltig']; ix = np.nonzero(gl)[0]
    Yf = np.stack([np.interp(np.arange(N), ix, Y[ix, j]) for j in range(208)], 1)
    benvis = G['benvis']
    if benvis.any():
        sl = np.nonzero(benvis)[0]
        for i in range(N):
            if not benvis[i]: Yf[i, BEN] = Yf[sl[np.argmin(np.abs(sl - i))], BEN]
    else: Yf[:, BEN] = 0
    a, b = ix[0], ix[-1] + 1; X = Yf.copy()
    if b - a >= fonster: X[a:b] = savgol_filter(Yf[a:b], fonster, ordning, axis=0, mode='interp')
    Ef = np.stack([np.interp(np.arange(N), ix, np.nan_to_num(G['E'])[ix, j]) for j in range(72)], 1)
    return till_euler(X, X[:, QK]), Ef


def oneeuro_riktad(y, fps, mincut=1.0, beta=.5, dcut=1.0):
    """Ett-euro-filter (Casiez m.fl.), framåt. y: (N, J)."""
    def alfa(fc): tau = 1 / (2 * np.pi * fc); return 1 / (1 + tau * fps)
    x = y.copy(); dx = np.zeros_like(y); xh = y[0].copy(); dxh = np.zeros(y.shape[1]); x[0] = y[0]
    for t in range(1, len(y)):
        d = (y[t] - xh) * fps; dxh = dxh + alfa(dcut) * (d - dxh)
        fc = mincut + beta * np.abs(dxh); a = np.array([alfa(f) for f in fc]) if np.ndim(fc) else alfa(fc)
        xh = xh + a * (y[t] - xh); x[t] = xh
    return x


def oneeuro_stab(G, N, fps, mincut=1.0, beta=.5):
    Y, w = spar(G); gl = G['giltig']; ix = np.nonzero(gl)[0]
    Yf = np.stack([np.interp(np.arange(N), ix, Y[ix, j]) for j in range(208)], 1)
    benvis = G['benvis']
    if benvis.any():
        sl = np.nonzero(benvis)[0]
        for i in range(N):
            if not benvis[i]: Yf[i, BEN] = Yf[sl[np.argmin(np.abs(sl - i))], BEN]
    else: Yf[:, BEN] = 0
    a, b = ix[0], ix[-1] + 1; X = Yf.copy()
    skala = np.maximum(Yf[a:b].std(0), 1e-3)         # parametrarna har olika enhet: hastigheten normaliseras per spår
    Z = Yf[a:b] / skala; f = oneeuro_riktad(Z, fps, mincut, beta); bk = oneeuro_riktad(Z[::-1], fps, mincut, beta)[::-1]
    X[a:b] = (f + bk) / 2 * skala
    Ef = np.stack([np.interp(np.arange(N), ix, np.nan_to_num(G['E'])[ix, j]) for j in range(72)], 1)
    return till_euler(X, X[:, QK]), Ef


# ---------- mått ----------
def kamerasil(pose, T, fok, w, h, mw, mh):
    v = KM.hudhorn(pose) / 100 @ F + T
    if (v[:, 2] < .05).mean() > .02: return None
    uv = v[:, :2] / v[:, 2:3] * fok + [w / 2, h / 2]
    return KM.fyll(uv * [mw / w, mh / h], KM.hud()['faces'], mw, mh)


def matt(pose, T, R, meta, mask, boxar, pal, syn, inom, N, G, med_iou=True):
    """px (pålitliga rutor), IoU (alla rutor med mask i rutan), darr (pålitliga rutor), täckning."""
    w, h = meta['bredd'], meta['hojd']; mh, mw = mask.shape[1:]
    rel = np.array([bool(syn.get(str(i), False)) for i in range(N)])
    fr = [f for f in R['idx'] if pal.get(str(f), True)]; err = []
    for f in fr:
        x = (pose[f][LED, :3] / 100) @ F + T[f]; uv = x[:, :2] / x[:, 2:] * R['FOC'][f] + [w / 2, h / 2]
        d = np.linalg.norm(uv - R['KP'][f][KP], axis=1)
        if not rel[f]: d = d[[0, 1]]
        err.append(d)
    err = np.concatenate(err) if err else np.array([np.nan])
    res = [] ; ious = []
    if med_iou:
        for f in np.nonzero(inom)[0]:
            if str(f) not in boxar: continue
            sil = kamerasil(pose[f], T[f], R['FOC'][f] if not np.isnan(R['FOC'][f]) else R['FOC'][R['idx'][0]], w, h, mw, mh)
            if sil is None: continue
            box = np.array(boxar[str(f)]) * [mw / w, mh / h, mw / w, mh / h]
            r = KM.jamfor_mask(sil, mask[f], box, mw, mh)
            if r: ious.append(r)
    sm = KM.sammanfatta(ious)
    # darr: kamerarummets ledpositioner, trippler av intilliggande pålitliga rutor
    X = np.full((N,) + (pose.shape[1], 3), np.nan)
    for f in fr: X[f] = pose[f][:, :3] @ F + 100 * T[f]
    return dict(px_median=float(np.median(err)), px_p90=float(np.percentile(err, 90)), iou=sm.get('iou_median', np.nan), iou_synlig=sm.get('iou_synlig_median', np.nan),
                tyngdpunkt=sm.get('tyngdpunkt_median', np.nan), darr=KM.jitter(X), tackning_px=len(fr) / max(int(inom.sum()), 1), tackning_iou=len(ious) / max(int(inom.sum()), 1))


def kor_tagning(folder, pid, metoder=None):
    meta = json.load(open(f'{folder}/meta.json')); N = meta['N']; fps = meta['fps']
    R = las(folder, pid, N); pal = json.load(open(f'{folder}/palitlig_{pid}.json')); syn = json.load(open(f'{folder}/synlighet_{pid}.json'))
    mask = np.load(f'{folder}/masker.npy'); boxar = json.load(open(f'{folder}/personer.json'))[pid]
    G = gemensam_forberedelse(R, syn, pal, N); T0 = fyll(R['T'], N)
    shape = np.nan_to_num(R['S'])[R['idx'][0]][None].repeat(N, 0)   # formparametrarna är lika i alla rutor (verifierat: rå = låst identitet)
    rows = []

    def rad(namn, pose, T, extra=None):
        m = matt(pose, T, R, meta, mask, boxar, pal, syn, G['inom'], N, G); m['metod'] = namn
        if extra: m.update(extra)
        rows.append(m); return m
    Praw = fk(np.nan_to_num(R['S']), np.nan_to_num(R['P']), np.nan_to_num(R['E']))
    rad('raw', Praw, np.nan_to_num(R['T']))
    Pg, Eg = gammal_stab(G, N, fps); Tg = gammal_t(R['T'], G, N, fps)
    pg = fk(shape, Pg, Eg); rad('gammal', pg, Tg)
    # bildskydd som det kördes: på den gamla stabiliseringen
    from bildskydd import skydda
    S = dict(pose=pg.copy(), cam_t=Tg.copy(), inom=G['inom'], ben_synliga=G['benvis'])
    lg = skydda(S, folder, pid)['rutor']; ande = np.median([x['stabil_andel'] for x in lg]) if lg else 1.0
    rad('bildskydd', S['pose'], S['cam_t'], dict(stabil_andel=float(ande)))
    P_, E_ = sg_stab(G, N, fps); rad('sg9/3', fk(shape, P_, E_), Tg)
    P_, E_ = oneeuro_stab(G, N, fps); rad('oneeuro', fk(shape, P_, E_), Tg)
    for fc, k, d, rb, tr in (KOMBOS if KOMBOS else ((4., 2., 2, False, True), (4., 2., 2, True, True), (4., 1., 2, True, True), (4., 3., 2, True, True), (3., 2., 3, True, True), (6., 2., 2, True, True))):
        ex = {}; P_, E_ = ny_stab(G, N, fps, fc, k, d, tr, rb, ex)
        nm = f'{"ror" if rb else "whitt"} fc{fc:g} k{k:g} d{d}'
        rad(nm + ' T-gammal', fk(shape, P_, E_), Tg, dict(trasiga=ex['trasiga_rutor']))
        if (fc, k, d, rb) == (4., 2., 2, True):
            Tn = utjamna_t_ruta(R['T'], G, N, fps); rad(nm + ' T-ny', fk(shape, P_, E_), Tn, dict(trasiga=ex['trasiga_rutor']))
    if HANDVARIANTER:
        Tn = utjamna_t_ruta(R['T'], G, N, fps)
        for nm, kw in (('rör hand fc8 k3', dict(fc_hand=8., k_hand=3.)), ('rör hand fc6 k4', dict(fc_hand=6., k_hand=4.)), ('rör k3 hand fc8 k4', dict(k=3., fc_hand=8., k_hand=4.)), ('rör fc3 k2 hand fc6 k3', dict(fc=3., fc_hand=6., k_hand=3.))):
            ex = {}; P_, E_ = J.stabilisera(G['P'], G['E'], G['giltig'], G['benvis'], fps, NAMN, ut=ex, **kw)
            rad(nm + ' T-ny', fk(shape, P_, E_), Tn, dict(trasiga=ex['trasiga_rutor']))
    return rows, dict(N=N, fps=fps, inom=int(G['inom'].sum()), pal=len([i for i in R['idx'] if pal.get(str(i), True)]))


def utjamna_t_ruta(T, G, N, fps):
    w = (G['giltig']).astype(float); Tf = fyll(T, N)
    Tn = J.utjamna_t(Tf, w, fps); return utanfor_giltigt(Tn, G['giltig'])


def main():
    global KOMBOS, HANDVARIANTER
    argv = sys.argv[1:]; utfil = None
    if '--ut' in argv: i = argv.index('--ut'); utfil = argv[i + 1]; del argv[i:i + 2]
    if '--bara-hand' in argv: argv.remove('--bara-hand'); KOMBOS = [(4., 2., 2, True, True)]; HANDVARIANTER = True
    a = [x for x in argv if not x.startswith('--')]; out = {}
    for sp in a:
        folder = str(Path(sp).resolve())
        for pid in json.load(open(folder + '/personer.json')):
            rows, info = kor_tagning(folder, pid); out[f'{sp}:{pid}'] = dict(info=info, rader=rows)
            print(f'\n{sp} person {pid}  {info}')
            print('%-26s %7s %7s %6s %6s %6s %7s %6s %6s' % ('metod', 'pxmed', 'pxp90', 'IoU', 'IoUsyn', 'tyngd', 'darr', 'täckpx', 'täckIoU'))
            for r in rows:
                print('%-26s %7.2f %7.2f %6.3f %6.3f %6.3f %7.2f %6.2f %6.2f %s' % (r['metod'], r['px_median'], r['px_p90'], r['iou'], r['iou_synlig'], r['tyngdpunkt'], r['darr'], r['tackning_px'], r['tackning_iou'],
                                                                                   ('andel %.2f' % r['stabil_andel']) if 'stabil_andel' in r else ('trasiga %d' % r['trasiga']) if 'trasiga' in r else ''))
    if utfil:
        Path(utfil).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
