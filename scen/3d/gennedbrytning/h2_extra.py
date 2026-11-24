"""0026 punkt 2: tre extra mått för en generering. Huvudet avskuret, kamerans glidning, och handens djup mot originalets läsning.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/h2_extra.py <variant>   (variant = rå generering, t.ex. dreamina; tidspassningen ur tid.json)
- Huvudet: personmasken (f_las.personmask) i genereringens alla rutor. Avskuret = maskens översta rad är en rak kant bredare än 6 % av
  bildbredden (ett huvud slutar i en rundning). Redovisas i genereringens rutor och, genom tid.json, i källans.
- Kameran: maskens höjd och fotlinje (nedersta raden) per ruta i de rutor där hon står upprätt (bålens lutning < 25°). Glider kameran
  ändras storlek och fotlinje fast hon står still.
- Handens djup: höger handled under höften, längs kamerans lodaxel, i meter (läsningens 3D), minsta värdet i h3–h4, mot dagens läsning ur originalet.
  Säger hur långt ned handen går; originalets tråg stoppar den högre upp.
- Vad läsaren gör där huvudet saknas: huvud- och halsledernas hopp per ruta i de avskurna rutorna mot övriga.
Ut: d_video/<variant>/extra.json.
"""
import json, sys
from pathlib import Path
import cv2, numpy as np
from f_las import personmask

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; DAG = ING / 'ut/kand-kennysgelato-tagningar/S1/kropp/1'
N = json.loads((ING / 'mhr_ledernamn.json').read_text())


def k3(f):
    z = np.load(f); return (z['pred_joint_coords'] + z['pred_cam_t']).astype(float)


def main():
    v = sys.argv[1]; d = HIT / 'd_video' / v; tid = json.loads((d / 'tid.json').read_text(encoding='utf-8')); w = np.array(tid['avbildning'])
    c = cv2.VideoCapture(str(d / 'isolerad.mp4')); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    W = F[0].shape[1]; G = len(F); cut, hojd, fot, lut = [], [], [], []
    for j, f in enumerate(F):
        m = personmask(f); ys, xs = np.nonzero(m); y0 = ys.min()
        topprad = m[y0 + 1]; cut.append(bool(topprad.sum() > .06 * W)); hojd.append(int(ys.max() - y0)); fot.append(int(ys.max()))
        k = k3(d / 'las/1' / f'{j:04d}.npz'); b = k[N.index('c_neck')] - k[N.index('root')]; lut.append(float(np.degrees(np.arctan2(-b[2], -b[1]))))
    cut = np.array(cut); lut = np.array(lut); upp = lut < 25
    def strackor(x):
        s, a = [], None
        for i, v_ in enumerate(list(x) + [False]):
            if v_ and a is None: a = i
            if not v_ and a is not None: s.append([a, i - 1]); a = None
        return s
    kalla_cut = sorted({i for i, j in enumerate(w) if cut[j]})
    # läsarens beteende där huvudet saknas: huvudets hopp per ruta (pixlar i bilden)
    hp = []
    for j in range(G):
        z = np.load(d / 'las/1' / f'{j:04d}.npz'); hp.append(z['pred_keypoints_2d'][0])
    hp = np.array(hp); dh = np.r_[0, np.linalg.norm(np.diff(hp, axis=0), axis=1)]
    # handens djup: handled under höften (kamerans y nedåt), h3–h4
    H = {s['id']: s['rutor_klipp'] for s in json.loads((HIT / 'handling/S1/handling.json').read_text(encoding='utf-8'))['segment']}
    a, b = H['h3'][0], H['h4'][1]
    def under(k): return float(k[N.index('r_wrist')][1] - (k[N.index('l_upleg')][1] + k[N.index('r_upleg')][1]) / 2)
    ny = [under(k3(d / 'las/1' / f'{w[i]:04d}.npz')) for i in range(a, b + 1)]
    dag = [under(k3(DAG / f'{i + 7:04d}.npz')) for i in range(a, b + 1) if (DAG / f'{i + 7:04d}.npz').exists()]
    uj = np.nonzero(upp)[0]
    res = dict(variant=v, huvud_avskuret=dict(generering_strackor=strackor(cut), generering_rutor=int(cut.sum()), av=G,
                                              kalla_rutor=dict(antal=len(kalla_cut), forsta=kalla_cut[0] if kalla_cut else None, sista=kalla_cut[-1] if kalla_cut else None),
                                              huvudpunktens_hopp_px=dict(avskurna_median=round(float(np.median(dh[cut])), 1) if cut.any() else None, ovriga_median=round(float(np.median(dh[~cut])), 1))),
               kamera=dict(upprat_rutor=int(upp.sum()), hojd_px_forsta_upprat=hojd[uj[0]], hojd_px_sista_upprat=hojd[uj[-1]], hojd_andring=round(hojd[uj[-1]] / hojd[uj[0]] - 1, 3),
                           fotlinje_px_forsta=fot[uj[0]], fotlinje_px_sista=fot[uj[-1]], fotlinje_spann_px=int(np.ptp(np.array(fot)[uj])),
                           hojd_per_sekund=[int(np.mean([hojd[j] for j in uj if int(j / 24.07) == s] or [0])) for s in range(int(G / 24.07) + 1)]),
               handens_djup_h3_h4=dict(handled_under_hoften_max_m=dict(generering=round(max(ny), 3), dagens_lasning=round(max(dag), 3)),
                                       not_='positiv = handleden under höften längs kamerans lodaxel; originalets tråg stoppar handen'))
    (d / 'extra.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__': main()
