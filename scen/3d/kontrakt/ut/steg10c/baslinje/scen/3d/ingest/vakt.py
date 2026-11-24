"""vakt: mätbara spärrar på en färdig ingest-körning. Ingen modell, bara geometri. Under 10 s per klipp.

Kör:  scen/.venv/Scripts/python.exe scen/3d/ingest/vakt.py <utmapp> [--tag namn]
Läser sekvens_*.npz, varld.npz, kropp/<pid>/*.npz, meta.json. Skriver vakt[_tag].json och vakt[_tag].png.

Mått per person (led = MHR-led, se mhr_ledernamn.json):
  skak_bal_cm / skak_cm (lemmar)  högfrekvent rest: |X - Savitzky-Golay(X, 9, 2)| per led och bildruta (verklig rörelse tas bort, skakningen blir kvar)
  ledhopp_grad global rotationsändring per bildruta; > 25° på en kroppsled = flip/snapp
  fotglidning  horisontell fothastighet (cm/ruta) när foten har kontakt (höjd < 6 cm över golvet och vertikal fart < 1 cm/ruta)
  golv         fot under golvet (< -2 cm) och svävande kropp (lägsta fot > 8 cm när benen syns)
  rot_fart     rotens horisontella fart (m/s); > 3 m/s i ett samtalsklipp = flyger
  avvik_2d     projicerade leder (slutlig sekvens) mot SAM 3D Bodys råa anpassning samma bildruta, i % av personens höjd i bild.
               Mäter hur mycket utjämning, skymningslogik och golvsteg flyttar kroppen bort från det modellen såg.
Flaggade bildrutor slås ihop till intervall (lucka <= 2 rutor).
"""
import sys, json, glob, os, argparse
from pathlib import Path
import numpy as np
from scipy.signal import savgol_filter

HIT = Path(__file__).resolve().parent
NAMN = json.load(open(HIT / 'mhr_ledernamn.json'))
F = np.diag([1., -1., -1.])
KROPP = [NAMN.index(n) for n in ('root', 'l_upleg', 'l_lowleg', 'l_foot', 'l_ball', 'r_upleg', 'r_lowleg', 'r_foot', 'r_ball', 'c_spine0', 'c_spine1',
                                 'c_spine2', 'c_spine3', 'r_clavicle', 'r_uparm', 'r_lowarm', 'r_wrist', 'l_clavicle', 'l_uparm', 'l_lowarm', 'l_wrist', 'c_neck', 'c_head')]
BEN = [NAMN.index(n) for n in ('l_upleg', 'l_lowleg', 'l_foot', 'l_ball', 'r_upleg', 'r_lowleg', 'r_foot', 'r_ball')]
FOTTER = {'vänster': [NAMN.index('l_foot'), NAMN.index('l_ball')], 'höger': [NAMN.index('r_foot'), NAMN.index('r_ball')]}
GRANS = dict(skak_bal_cm=0.5, skak_cm=1.5, ledhopp_grad=25.0, glid_cm=1.0, under_cm=-2.0, svav_cm=8.0, rot_fart=3.0, avvik_proc=6.0)


def intervall(mask, varde, namn, lucka=2):
    ut, i, n = [], 0, len(mask)
    while i < n:
        if not mask[i]: i += 1; continue
        j = i
        while j + 1 < n and (mask[j + 1] or (j + lucka + 1 < n and mask[j + 1:j + lucka + 2].any())): j += 1
        while not mask[j]: j -= 1
        ut.append(dict(typ=namn, start=int(i), slut=int(j), max=round(float(np.nanmax(varde[i:j + 1])), 2))); i = j + 1
    return ut


def quat(x):  # MHR: (tx,ty,tz, qx,qy,qz,qw, s)
    q = x[..., 3:7]; return q / np.linalg.norm(q, axis=-1, keepdims=True)


def vinkel(q1, q2):
    d = np.abs(np.sum(q1 * q2, -1)).clip(0, 1); return np.degrees(2 * np.arccos(d))


def matt(ut, pid, S, V, M):
    N = len(S['pose']); R, C, u = V['kam_R'], V['kam_C'], V['upp']; golv = float(V['golv_h']) if 'golv_h' in V.files else None
    inom = S['inom'].astype(bool); ii = np.nonzero(inom)[0]; fps = M['fps']
    kam = np.einsum('ij,ntj->nti', F, S['pose'][:, :, :3] / 100) + S['cam_t'][:, None]          # kamerarum, meter
    X = C[:, None] + np.einsum('nij,ntj->nti', R, kam)                                          # värld
    h = X @ u; hor = X - h[..., None] * u
    r = {}; flaggor = []
    # skak: högfrekvent rest på kroppsleder
    sk = np.zeros((N, len(KROPP)))
    a, b = ii[0], ii[-1] + 1
    if b - a >= 11:
        Y = X[a:b][:, KROPP]; sk[a:b] = np.linalg.norm(Y - savgol_filter(Y, 9, 2, axis=0), axis=-1) * 100
    BAL = [k for k, j in enumerate(KROPP) if NAMN[j] in ('root', 'c_spine0', 'c_spine1', 'c_spine2', 'c_spine3', 'c_neck', 'c_head')]
    skb = sk[:, BAL].max(1); r['skak_bal_cm'] = dict(median=round(float(np.median(skb[ii])), 3), p95=round(float(np.percentile(skb[ii], 95)), 3), max=round(float(skb.max()), 2))
    flaggor += intervall(skb > GRANS['skak_bal_cm'], skb, 'skak_bal')
    skr = sk.max(1); r['skak_cm'] = dict(median=round(float(np.median(sk[ii])), 3), p95=round(float(np.percentile(sk[ii], 95)), 3), max=round(float(skr.max()), 2),
                                          varst=NAMN[KROPP[int(np.argmax(sk.max(0)))]])
    flaggor += intervall(skr > GRANS['skak_cm'], skr, 'skak_lem')
    # ledhopp
    q = quat(S['pose'][:, KROPP]); lh = np.zeros((N, len(KROPP))); lh[1:] = vinkel(q[1:], q[:-1]); lh[~inom] = 0; lh[1:][~inom[:-1]] = 0
    lhr = lh.max(1); r['ledhopp_grad'] = dict(p95=round(float(np.percentile(lhr[ii], 95)), 1), max=round(float(lhr.max()), 1), rutor_over=int((lhr > GRANS['ledhopp_grad']).sum()),
                                                varst=NAMN[KROPP[int(np.argmax(lh.max(0)))]])
    flaggor += intervall(lhr > GRANS['ledhopp_grad'], lhr, 'ledhopp')
    # fötter
    if golv is not None:
        fot = {}
        for sida, J in FOTTER.items():
            fh = (h[:, J].min(1) - golv) * 100; fv = np.zeros(N); fv[1:] = np.abs(np.diff(h[:, J].min(1))) * 100
            fhv = np.zeros(N); fhv[1:] = np.linalg.norm(np.diff(hor[:, J].mean(1), axis=0), axis=-1) * 100
            kontakt = inom & (fh < 6) & (fv < 1.0); glid = np.where(kontakt, fhv, 0)
            fot[sida] = dict(kontakt_rutor=int(kontakt.sum()), glid_cm_per_ruta_median=round(float(np.median(fhv[kontakt])) if kontakt.any() else 0, 2),
                             glid_p90=round(float(np.percentile(fhv[kontakt], 90)) if kontakt.any() else 0, 2), glidrutor=int((glid > GRANS['glid_cm']).sum()))
            flaggor += intervall(glid > GRANS['glid_cm'], glid, f'fotglidning_{sida}')
        kf = ut / f'kontakt_{pid}.json'
        if kf.exists():                                   # glidning inom kontaktstegets perioder (det IK ska ha låst)
            K = json.loads(kf.read_text()); gl = []
            for sida, J in (('l', FOTTER['vänster']), ('r', FOTTER['höger'])):
                for p in K['fotter'].get(sida, {}).get('lista', []):
                    gl += list(np.linalg.norm(np.diff(hor[p['start']:p['slut'] + 1, J[0]], axis=0), axis=1) * 100)
            fot['i_kontaktperioder'] = dict(rutor=len(gl), glid_cm_median=round(float(np.median(gl)), 3) if gl else None, glid_cm_p90=round(float(np.percentile(gl, 90)), 3) if gl else None)
        r['fotter'] = fot
        lagst = (h[:, [j for J in FOTTER.values() for j in J]].min(1) - golv) * 100
        ben = S['ben_synliga'].astype(bool) & inom
        r['golv'] = dict(under_rutor=int((inom & (lagst < GRANS['under_cm'])).sum()), svav_rutor=int((ben & (lagst > GRANS['svav_cm'])).sum()),
                         lagsta_fot_cm_p10_p90=[round(float(np.percentile(lagst[ii], 10)), 1), round(float(np.percentile(lagst[ii], 90)), 1)])
        flaggor += intervall(inom & (lagst < GRANS['under_cm']), -lagst, 'under_golv') + intervall(ben & (lagst > GRANS['svav_cm']), lagst, 'svavar')
    # rotens fart
    rf = np.zeros(N); rf[1:] = np.linalg.norm(np.diff(hor[:, NAMN.index('root')], axis=0), axis=-1) * fps; rf[~inom] = 0; rf[1:][~inom[:-1]] = 0
    r['rot_fart_ms'] = dict(median=round(float(np.median(rf[ii])), 2), max=round(float(rf.max()), 2))
    flaggor += intervall(rf > GRANS['rot_fart'], rf, 'rot_flyger')
    # 2D mot rå anpassning
    fok = float(S['fokal']); W, H = M['bredd'], M['hojd']
    def proj(P): return np.c_[fok * P[:, 0] / P[:, 2] + W / 2, fok * P[:, 1] / P[:, 2] + H / 2]
    av = np.full(N, np.nan); avben = np.full(N, np.nan)
    palf = ut / f'palitlig_{pid}.json'; pal = json.loads(palf.read_text()) if palf.exists() else {}
    for f in sorted(glob.glob(str(ut / 'kropp' / pid / '*.npz'))):
        i = int(Path(f).stem)
        if not pal.get(str(i), True): continue          # underkänd anpassning: att avvika från den är meningen
        d = np.load(f)
        raw = proj(d['pred_joint_coords'] + d['pred_cam_t']); fin = proj(kam[i])
        hojd = np.ptp(raw[KROPP, 1]) + 1e-6; e = np.linalg.norm(raw - fin, axis=1) / hojd * 100
        ovre = [j for j in KROPP if j not in BEN]; av[i] = np.median(e[ovre]); avben[i] = np.median(e[BEN])
    ok = ~np.isnan(av)
    r['avvik_2d_proc'] = dict(overkropp_median=round(float(np.median(av[ok])), 2), overkropp_p95=round(float(np.percentile(av[ok], 95)), 2),
                              ben_median=round(float(np.nanmedian(avben)), 2), ben_p95=round(float(np.nanpercentile(avben, 95)), 2))
    av0 = np.nan_to_num(av); flaggor += intervall(av0 > GRANS['avvik_proc'], av0, 'avvik_2d_overkropp')
    serier = dict(skak=skb, ledhopp=lhr, rot_fart=rf, avvik=av0)
    if golv is not None: serier['lagsta_fot'] = lagst
    return r, sorted(flaggor, key=lambda x: x['start']), serier


def main():
    a = argparse.ArgumentParser(); a.add_argument('ut'); a.add_argument('--tag', default=''); x = a.parse_args()
    ut = Path(x.ut).resolve(); M = json.loads((ut / 'meta.json').read_text()); V = np.load(ut / 'varld.npz')
    res = dict(granser=GRANS, personer={}); alla = {}
    for sf in sorted(ut.glob('sekvens_*.npz')):
        pid = sf.stem[8:]; r, fl, se = matt(ut, pid, np.load(sf), V, M)
        r['flaggor'] = fl; r['flaggade_rutor'] = {t: int(sum(f['slut'] - f['start'] + 1 for f in fl if f['typ'] == t)) for t in sorted({f['typ'] for f in fl})}
        res['personer'][pid] = r; alla[pid] = se
    namn = f'vakt{"_" + x.tag if x.tag else ""}'
    (ut / f'{namn}.json').write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8')
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        k = ['skak', 'ledhopp', 'lagsta_fot', 'rot_fart', 'avvik']; g = dict(skak=GRANS['skak_cm'], ledhopp=GRANS['ledhopp_grad'], rot_fart=GRANS['rot_fart'], avvik=GRANS['avvik_proc'])
        fig, ax = plt.subplots(len(k), 1, figsize=(12, 9), sharex=True)
        for pid, se in alla.items():
            for a_, kk in zip(ax, k):
                if kk in se: a_.plot(se[kk], lw=.8, label=f'person {pid}')
        for a_, kk in zip(ax, k):
            a_.set_ylabel(kk, fontsize=8)
            if kk in g: a_.axhline(g[kk], color='r', lw=.6, ls='--')
            if kk == 'lagsta_fot': [a_.axhline(v, color='r', lw=.6, ls='--') for v in (GRANS['under_cm'], GRANS['svav_cm'])]
        ax[0].legend(fontsize=7); ax[-1].set_xlabel('bildruta'); fig.suptitle(f'vakt {ut.name} {x.tag}'); fig.tight_layout(); fig.savefig(ut / f'{namn}.png', dpi=80)
    except ImportError:
        pass
    for pid, r in res['personer'].items():
        print(pid, json.dumps({k: v for k, v in r.items() if k != 'flaggor'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
