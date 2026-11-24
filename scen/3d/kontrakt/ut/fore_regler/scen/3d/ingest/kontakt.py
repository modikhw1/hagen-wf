"""Steg `kontakt`: fotkontakt -> stående fot står still (tyngd), utan att flytta kroppen synligt i bild.

Standardteknik i mocap-städning (WHAM/GVHMR: kontaktsannolikhet + rotbana; Blender-tillägg som Foot Flow: plant + IK).
  1. Kontakt per fot (MHR-lederna *_foot och *_ball): höjd över golvet < 7 cm OCH horisontell fart < 2 cm/ruta, hysteres
     (släpps vid 10 cm / 3 cm/ruta), luckor <= 2 rutor stängs, perioder < 5 rutor tas bort. Bara rutor där benen syns
     (eller hålls från en synlig ruta) och personen finns.
  2. Ankare per kontaktperiod = fotens medianläge (horisontellt) under perioden, på golvhöjd.
  3. Kroppsförskjutning Δ(t) = ankare − fot(t) för stående fötter (medel om båda står), interpolerad mellan perioder och
     lågpassad (3 Hz). Δ delas i siktlinjens riktning (osynlig i bild: bara storleken ändras marginellt) som tas helt, och
     sidled som tas till hälften och begränsas till 4 cm, så att överlägget mot källan inte glider. Korrigeringen är begränsad
     per period och kan inte driva över klippet.
  4. Kontaktperioderna och ankarna sparas i kontakt_<pid>.json. mhr_rig.py lägger ben-IK mot ankarna (kvarvarande glidning) och bakar.
cam_t före steget sparas som cam_t_fore_kontakt, så att en omkörning alltid utgår från samma data.
"""
import json
from pathlib import Path
import numpy as np
from scipy.signal import butter, filtfilt

NAMN = json.load(open(Path(__file__).resolve().parent / 'mhr_ledernamn.json'))
F = np.diag([1., -1., -1.])
FOT = {'l': [NAMN.index('l_foot'), NAMN.index('l_ball')], 'r': [NAMN.index('r_foot'), NAMN.index('r_ball')]}


def perioder(mask, min_len=5, lucka=2):
    m = mask.copy(); n = len(m); i = 0
    while i < n:                                   # stäng korta luckor
        if not m[i]:
            j = i
            while j < n and not m[j]: j += 1
            if 0 < i and j < n and j - i <= lucka: m[i:j] = True
            i = j
        else: i += 1
    ut, i = [], 0
    while i < n:
        if m[i]:
            j = i
            while j + 1 < n and m[j + 1]: j += 1
            if j - i + 1 >= min_len: ut.append((i, j))
            i = j + 1
        else: i += 1
    return ut


def varldsleder(S, V):
    R, C = V['kam_R'], V['kam_C']
    kam = np.einsum('ij,ntj->nti', F, S['pose'][:, :, :3] / 100) + S['cam_t'][:, None]
    return C[:, None] + np.einsum('nij,ntj->nti', R, kam)


from scipy.spatial.transform import Rotation as Rot
_FAR = json.load(open(Path(__file__).resolve().parent.parent / 'klipp2' / 'sam3db' / 'mhr_skelett.json'))['parents']


def _under(j):
    ut, st = [], [j]
    while st:
        k = st.pop(); c = [i for i, p in enumerate(_FAR) if p == k]; ut += c; st += c
    return ut


BENKEDJA = {}
for _s in 'lr':
    up, low, fot = NAMN.index(f'{_s}_upleg'), NAMN.index(f'{_s}_lowleg'), NAMN.index(f'{_s}_foot')
    fotgren = [fot] + _under(fot); lowgren = [low] + [j for j in _under(low) if j not in fotgren]
    upgren = [up] + [j for j in _under(up) if j not in lowgren and j not in fotgren]
    BENKEDJA[_s] = (up, low, fot, upgren, lowgren, fotgren)


def _rikta(a, b):
    """Minsta rotation som vrider riktning a till riktning b."""
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); ax = np.cross(a, b); s = np.linalg.norm(ax); c = float(a @ b)
    if s < 1e-9: return Rot.identity()
    return Rot.from_rotvec(ax / s * np.arctan2(s, c))


def ik_ben(P, sida, mal):
    """Analytisk tvåbens-IK på MHR:s globala ledlägen (P: 127 x [t(3), q(xyzw), s], modellrum cm). Höften står kvar, knät
    hamnar i planet höft–mål–originalknä (samma böjriktning), vristen på målet. Lår- och vadgrenarna (inkl. vridleder) roteras
    med sina ben; fotgrenen flyttas utan att vridas, så att en stående fot står plant. Blenders IK fungerar inte här: MHR-benens
    svansar pekar inte mot nästa led (vadens svans ligger ~30 cm från vristen), så lösaren räknar fel geometri."""
    up, low, fot, upg, lowg, fotg = BENKEDJA[sida]; P = P.copy()
    h, k, a_ = P[up, :3], P[low, :3], P[fot, :3]; la, lb = np.linalg.norm(k - h), np.linalg.norm(a_ - k)
    d = mal - h; L = np.clip(np.linalg.norm(d), abs(la - lb) + 1e-3, .999 * (la + lb)); dh = d / np.linalg.norm(d); mal = h + dh * L
    n = (k - h) - ((k - h) @ dh) * dh
    if np.linalg.norm(n) < 1e-6: return P
    n /= np.linalg.norm(n); ca = (la ** 2 + L ** 2 - lb ** 2) / (2 * la * L); k2 = h + la * (ca * dh + np.sqrt(max(0., 1 - ca ** 2)) * n)
    Rup = _rikta(k - h, k2 - h); a1 = h + Rup.apply(a_ - h); Rlow = _rikta(a1 - k2, mal - k2) * Rup
    for j in upg: P[j, :3] = h + Rup.apply(P[j, :3] - h); P[j, 3:7] = (Rup * Rot.from_quat(P[j, 3:7])).as_quat()
    for j in lowg: P[j, :3] = k2 + Rlow.apply(P[j, :3] - k); P[j, 3:7] = (Rlow * Rot.from_quat(P[j, 3:7])).as_quat()
    for j in fotg: P[j, :3] = P[j, :3] + (mal - a_)
    return P


def steg_kontakt(ut, M, sid_andel=.5, sid_max=.04, ramp=3):
    ut = Path(ut); V = np.load(ut / 'varld.npz'); u = V['upp']; golv = float(V['golv_h']); R, C = V['kam_R'], V['kam_C']; fps = M['fps']
    x = {}
    for sf in sorted(ut.glob('sekvens_*.npz')):
        pid = sf.stem[8:]; S = dict(np.load(sf))
        if 'cam_t_fore_kontakt' in S: S['cam_t'] = S['cam_t_fore_kontakt'].copy()
        else: S['cam_t_fore_kontakt'] = S['cam_t'].copy()
        N = len(S['pose']); inom = S['inom'].astype(bool)
        # benen räknas bara där de syns eller ligger inom 10 rutor från en synlig ruta (hållna ben längre bort är gissning)
        bs = S['ben_synliga'].astype(bool); nara = np.zeros(N, bool)
        for i in np.nonzero(bs)[0]: nara[max(0, i - 10):i + 11] = True
        giltig = inom & nara
        X = varldsleder(S, V); res = dict(fotter={}); D = np.full((N, 3), np.nan); vikt = np.zeros(N)
        Dsum = np.zeros((N, 3))
        for sida, J in FOT.items():
            P = X[:, J].mean(1); h = X[:, J].min(1) @ u - golv
            v = np.zeros(N); hor = P - (P @ u)[:, None] * u; v[1:] = np.linalg.norm(np.diff(hor, axis=0), axis=1)
            k = np.zeros(N, bool); pa = False
            for i in range(N):                          # hysteres
                if not giltig[i]: pa = False; continue
                pa = (h[i] < .10 and v[i] < .03) if pa else (h[i] < .07 and v[i] < .02); k[i] = pa
            per = perioder(k); lista = []
            for a, b in per:
                ank = np.median(hor[a:b + 1], 0) + golv * u     # horisontellt medianläge, på golvet
                lista.append(dict(start=int(a), slut=int(b), ankare=ank.tolist()))
                for i in range(a, b + 1):
                    d = ank - (P[i] - (P[i] @ u) * u + golv * u); d -= (d @ u) * u   # bara horisontellt
                    Dsum[i] += d; vikt[i] += 1
            res['fotter'][sida] = dict(perioder=len(per), rutor=int(sum(b - a + 1 for a, b in per)), lista=lista)
        har = vikt > 0
        if har.sum() >= 2:
            D[har] = Dsum[har] / vikt[har, None]; r_ = np.arange(N)
            for c in range(3): D[:, c] = np.interp(r_, r_[har], D[har, c])
            ii = np.nonzero(inom)[0]; a, b = ii[0], ii[-1] + 1
            if b - a > 12:
                bb, aa = butter(2, 3.0 / (fps / 2)); D[a:b] = filtfilt(bb, aa, D[a:b], axis=0, padtype='even')
            D[~inom] = 0
            # dela upp: siktlinje (från kameran till roten, horisontellt) helt, sidled till hälften och högst sid_max
            rot = X[:, NAMN.index('root')]; s = rot - C; s -= (s @ u)[:, None] * u; s /= np.linalg.norm(s, axis=1, keepdims=True) + 1e-9
            langs = (D * s).sum(1)[:, None] * s; sid = D - langs
            sn = np.linalg.norm(sid, axis=1, keepdims=True); sid = sid * sid_andel * np.minimum(1, sid_max / (sn * sid_andel + 1e-9))
            Dt = langs + sid
            S['cam_t'] = S['cam_t'] + np.einsum('nji,nj->ni', R, Dt)        # värld -> kamerarum: R^T Δ
            res['korr_cm'] = dict(langs_median=round(float(np.median(np.linalg.norm(langs[inom], axis=1))) * 100, 1),
                                  sid_median=round(float(np.median(np.linalg.norm(sid[inom], axis=1))) * 100, 1),
                                  max=round(float(np.linalg.norm(Dt, axis=1).max()) * 100, 1))
        # ankarna räknas om efter korrigeringen, och benen dras dit med analytisk tvåbens-IK (se ik_ben)
        if 'pose_fore_kontakt' in S: S['pose'] = S['pose_fore_kontakt'].copy()
        else: S['pose_fore_kontakt'] = S['pose'].copy()
        X2 = varldsleder(S, V); pose = S['pose'].copy()
        for sida, J in FOT.items():
            w = np.zeros(N); ank = np.full((N, 3), np.nan)
            for p in res['fotter'][sida]['lista']:
                a, b = p['start'], p['slut']; P = X2[a:b + 1, J[0]]; hor = P - (P @ u)[:, None] * u
                A = np.median(hor, 0) + np.median(P @ u) * u; p['ankare_vrist'] = A.tolist()   # vristleden (*_foot)
                for i in range(max(0, a - ramp), min(N, b + ramp + 1)):
                    wi = 1.0 if a <= i <= b else 1 - (a - i if i < a else i - b) / (ramp + 1)
                    if wi > w[i]: w[i] = wi; ank[i] = A
            for i in np.nonzero(w > 0)[0]:
                m = F @ (R[i].T @ (ank[i] - C[i]) - S['cam_t'][i]) * 100                # värld -> modellrum (cm)
                fot = pose[i, J[0], :3]; pose[i] = ik_ben(pose[i], sida, fot + w[i] * (m - fot))
        S['pose'] = pose
        X3 = varldsleder(S, V); gl = []
        for sida, J in FOT.items():
            for p in res['fotter'][sida]['lista']:
                gl += list(np.linalg.norm(np.diff(X3[p['start']:p['slut'] + 1, J[0]], axis=0), axis=1))
        res['efter_ik'] = dict(glid_cm_median=round(float(np.median(gl)) * 100, 3) if gl else None, glid_cm_p90=round(float(np.percentile(gl, 90)) * 100, 3) if gl else None)
        np.savez(sf, **S); (ut / f'kontakt_{pid}.json').write_text(json.dumps(res))
        x[pid] = {k: v for k, v in res.items() if k != 'fotter'} | {s: {k: v for k, v in f.items() if k != 'lista'} for s, f in res['fotter'].items()}
    return x
