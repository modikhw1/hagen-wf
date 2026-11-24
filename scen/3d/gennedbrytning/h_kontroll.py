"""0023 punkt 4–5: mått och kontroll per generering. Säger ja eller nej, med skäl, om en generering duger som enda källa för kroppen.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/h_kontroll.py <variant> [<variant> ...]
Läser d_video/<variant>/las/1/*.npz (läsningen ur den genererade videon, f_las.py) och dagens läsning ur originalet (ingest kropp/1, ruta+7).
Varianter med kamerafri källa (alla utom a) förs tillbaka till originalets rutor genom inversen i kamerafri/avbildning.json.

Mått:
- hela kroppen i bild: båda fotlederna och huvudet inom bilden (pred_keypoints_2d)
- benlängd (median, spridning), rotens hopp per ruta, bålens och höftens vridhopp (f_las.stat)
- överkroppens leder i originalets ram mot dagens läsning (promille av bildhöjden; median, p90), totalt och i rutorna 40–70 och 95–146
- bålens lutning framåt per ruta: vinkeln mellan roten->halsen och kamerans lodaxel i kamerans y-z-plan, positiv mot kameran.
  Den kamerafria källan är originalets pixlar skalade och förskjutna utan vridning, så perspektivet är originalets och vinklarna jämförbara.
  Jämförs med dagens läsning: median |skillnad|, och största lutning i rutorna 40–70 (där hon lutar sig ned i disken).
Kontrollen: trösklar i GRANS. De är diagnos, inte ägarens krav.
"""
import json, sys
from pathlib import Path
import cv2, numpy as np
from f_las import serie, stat
from f_trohet import proj

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; from tagning import DAG, OFFS, AVBILDNING   # 0030
N = json.loads((ING / 'mhr_ledernamn.json').read_text())
GRANS = dict(hela_kroppen_andel_min=0.95, benlangd_cv_max=0.03, rot_max_hopp_m=0.05, bal_storsta_hopp_max=6.0,
             overkropp_p90_promille_max=60.0, lutning_korrelation_min=0.8, lutning_40_70_andel_min=0.6)


def lutning(z):
    k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); d = k[N.index('c_neck')] - k[N.index('root')]
    return float(np.degrees(np.arctan2(-d[2], -d[1])))


def matt(v):
    d = HIT / 'd_video' / v; kf = v != 'a'
    c = cv2.VideoCapture(str(d / 'isolerad.mp4')); W, H, n = int(c.get(3)), int(c.get(4)), int(c.get(7)); s = 1080 / W
    avb = json.loads(AVBILDNING.read_text(encoding='utf-8'))['rutor'] if kf else None
    filer = [d / 'las/1' / f'{i:04d}.npz' for i in range(n)]
    hel, dist, d4070, d95, lut = 0, [], [], [], []
    for i, f in enumerate(filer):
        if not f.exists(): lut.append((i, None, None)); continue
        z = np.load(f); kp = z['pred_keypoints_2d']
        if all(0 <= x < W and 0 <= y < H for x, y in kp[13:15]) and 0 <= kp[0][1] < H: hel += 1
        o = DAG / f'{i + OFFS:04d}.npz'
        if not o.exists(): lut.append((i, lutning(z), None)); continue
        zo = np.load(o); p = proj(z, W, H) * s
        if kf: p = np.c_[p, np.ones(len(p))] @ np.array(avb[i]['invers']).T
        dd = list(np.linalg.norm(p - proj(zo, 1080, 1920), axis=1) / 1920 * 1000); dist += dd
        if 40 <= i <= 70: d4070 += dd
        if i >= 95: d95 += dd
        lut.append((i, lutning(z), lutning(zo)))
    st = stat(serie(filer), H)
    par = [(a, b) for _, a, b in lut if a is not None and b is not None]
    ny_l = np.array([a for a, _ in par]); dag_l = np.array([b for _, b in par])
    mid = [(a, b) for i, a, b in lut if 40 <= i <= 70 and a is not None and b is not None]
    r = dict(variant=v, kamerafri=kf, rutor=n, hela_kroppen_i_bild=hel, benlangd=st['benlangd_m'], rot_hopp_m=st['rot_hopp_m'], bal=st['bal'], hoft=st['hoft'],
             overkropp_promille=dict(median=round(float(np.median(dist)), 1), p90=round(float(np.percentile(dist, 90)), 1),
                                     r40_70_median=round(float(np.median(d4070)), 1) if d4070 else None, r95_146_median=round(float(np.median(d95)), 1) if d95 else None),
             lutning_grader=dict(median_diff_mot_dagens=round(float(np.median(np.abs(ny_l - dag_l))), 1),
                                 korrelation=round(float(np.corrcoef(ny_l, dag_l)[0, 1]), 2),
                                 max_40_70_ny=round(max(a for a, _ in mid), 1), max_40_70_dagens=round(max(b for _, b in mid), 1)),
             lutning_per_ruta=[[i, None if a is None else round(a, 1), None if b is None else round(b, 1)] for i, a, b in lut])
    return r


def kontroll(r):
    g = GRANS; skal = []
    if r['hela_kroppen_i_bild'] < g['hela_kroppen_andel_min'] * r['rutor']: skal.append(f"hela kroppen i bild bara i {r['hela_kroppen_i_bild']} av {r['rutor']} rutor")
    if r['benlangd']['spridning_cv'] > g['benlangd_cv_max']: skal.append(f"benlängden sprider {r['benlangd']['spridning_cv'] * 100:.1f} %")
    if r['rot_hopp_m']['max'] > g['rot_max_hopp_m']: skal.append(f"roten hoppar {r['rot_hopp_m']['max'] * 100:.0f} cm")
    if r['bal']['storsta_hopp_grader'] > g['bal_storsta_hopp_max']: skal.append(f"bålen vrids {r['bal']['storsta_hopp_grader']}° på en ruta")
    if r['overkropp_promille']['p90'] > g['overkropp_p90_promille_max']: skal.append(f"överkroppen p90 {r['overkropp_promille']['p90']} promille från originalet")
    l = r['lutning_grader']
    # medianskillnaden har en fast förskjutning även i (a), som följer originalet; formen på kurvan (korrelationen) är måttet
    if l['korrelation'] < g['lutning_korrelation_min']: skal.append(f"lutningen följer inte originalets (korrelation {l['korrelation']})")
    if l['max_40_70_ny'] < g['lutning_40_70_andel_min'] * l['max_40_70_dagens']: skal.append(f"lutar bara {l['max_40_70_ny']}° i rutorna 40–70 (dagens {l['max_40_70_dagens']}°)")
    return dict(duger=not skal, skal=skal or ['alla mått inom gränserna'])


def main():
    alla = {}
    for v in sys.argv[1:]:
        r = matt(v); r['kontroll'] = kontroll(r); alla[v] = r
        (HIT / 'd_video' / v / 'kontroll.json').write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
        print(v, 'JA' if r['kontroll']['duger'] else 'NEJ', '|', '; '.join(r['kontroll']['skal']))
        print('   hel', r['hela_kroppen_i_bild'], 'ben', r['benlangd'], 'rot', r['rot_hopp_m'], 'bal', r['bal']['storsta_hopp_grader'], 'hoft', r['hoft']['storsta_hopp_grader'])
        print('   overkropp', r['overkropp_promille'], 'lutning', r['lutning_grader'])
    (HIT / 'kontroll_gransar.json').write_text(json.dumps(GRANS, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__': main()
