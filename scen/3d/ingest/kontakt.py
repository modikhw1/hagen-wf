"""GOLV2: mät kontakt; ändra aldrig kroppens kameraposition eller benlängd."""
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
    """Kontakt är diagnostik. Varken cam_t eller pose flyttas av kontakt."""
    import sys
    from metrisk import las
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'kontrakt'))
    from golvmatning import fotkontroll
    ut=Path(ut);v=dict(np.load(ut/'varld.npz'));u=v['upp'];floor=float(v['golv_h']);result={}
    for file in sorted(ut.glob('sekvens_*.npz')):
        pid=file.stem[8:];s=las(file);x=varldsleder(s,v)
        vis=fotkontroll(ut,pid,M);visible={r['ruta']:(r['sidor'] if r['anvandbar'] else [False,False]) for r in vis['per_ruta']}
        record=dict(status='modellbedomd',metod='Synlig låg fot med låg fart: kontaktkandidat. Kropp och kamera flyttas inte.',fotter={})
        for side,J in FOT.items():
            h=(x[:,J]@u).min(1)-floor;p=x[:,J].mean(1)
            speed=np.r_[np.inf,np.linalg.norm(np.diff(p,axis=0),axis=1)]
            valid=np.array([visible.get(i,[False,False])['lr'.index(side)] for i in range(len(h))])&s['inom']
            mask=valid&(np.abs(h)<.07)&(speed<.02)
            spans=perioder(mask,lucka=0)
            record['fotter'][side]=dict(perioder=len(spans),rutor=int(mask.sum()),lista=[dict(start=a,slut=b,ankare=np.median(p[a:b+1],axis=0).tolist()) for a,b in spans],
                rest_m_median=float(np.median(h[valid])) if valid.any() else None)
        record['kontakt_kand']=any(f['rutor'] for f in record['fotter'].values())
        record['korr_cm']=dict(max=0.,langs_median=0.,sid_median=0.)
        (ut/f'kontakt_{pid}.json').write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
        result[pid]=record
    return result
