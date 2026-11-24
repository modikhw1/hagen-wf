"""0027 punkt 1: var uppstår rotens fel? Överkroppens leder projiceras i originalets bild i varje steg och jämförs med dagens 2D-läsning av originalet.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/r_fel.py <g_forvarld-variant> <samspel.json> [--las <d_video-variant>]
Steg (promille av bildhöjden, median per segment, och storlek = axelbredd i bild / originalets):
  A  läsningen i genereringens bild, förd till originalets ram genom inversen (avbildningens skala, genereringens kamera, tidspassning)
  B  kroppsfilerna efter rotformeln i g_forvarld (pred_joint_coords + nya pred_cam_t, ingestens fokal): inversens rot
  C  den byggda scenen: lederna i världen (j_samspel_blender) genom planens renderkamera: sekvensen, stödet och planens kamera
Skillnaden B−A är rotformelns del, C−B sekvensens, stödets och kamerans. Fötternas glidning i världen redovisas för C.
Ut: g_forvarld/<variant>/fel.json.
"""
import json, sys
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; DAG = ING / 'ut/kand-kennysgelato-tagningar/S1/kropp/1'
N = json.loads((ING / 'mhr_ledernamn.json').read_text()); OVER = ['c_head', 'c_neck', 'l_uparm', 'r_uparm', 'l_lowarm', 'r_lowarm', 'l_wrist', 'r_wrist']; OFFS = 7


def proj_npz(z, W=1080, H=1920, s=1.0):
    k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
    return np.array([[fl * k[N.index(n), 0] / k[N.index(n), 2] + W / 2, fl * k[N.index(n), 1] / k[N.index(n), 2] + H / 2] for n in OVER]) * s


def proj_varld(le, K, lins):
    K = np.array(K); R, C = K[:3, :3], K[:3, 3]; f = lins / 36 * 1080; ut = []
    for n in OVER:
        x = R.T @ (np.array(le[n]['huvud']) - C); ut.append([f * x[0] / -x[2] + 540, -f * x[1] / -x[2] + 960])
    return np.array(ut)


def jamfor(p, q):
    syn = (q[:, 0] >= 0) & (q[:, 0] < 1080) & (q[:, 1] >= 0) & (q[:, 1] < 1920)
    d = np.linalg.norm(p - q, axis=1)[syn] / 1920 * 1000; bw = lambda x: np.linalg.norm(x[2] - x[3])
    return (float(np.median(d)) if d.size else np.nan), bw(p) / max(bw(q), 1e-6)


def main():
    v, spf = sys.argv[1], sys.argv[2]; las = sys.argv[sys.argv.index('--las') + 1] if '--las' in sys.argv else v
    G = HIT / 'g_forvarld' / v; plan = json.loads((G / 'plan.json').read_text(encoding='utf-8')); nk = plan['renderkamera']['nycklar']
    sp = {r['ruta']: r for r in json.loads(Path(spf).read_text())['rutor']}
    avb = json.loads((HIT / 'kamerafri/avbildning.json').read_text(encoding='utf-8'))['rutor']
    seg = {s['id']: s['rutor_plan'] for s in json.loads((HIT / 'handling/S1/handling.json').read_text(encoding='utf-8'))['segment']}
    D = HIT / 'd_video' / las / 'las/1'; rader = {}
    for u in range(OFFS, 155):
        o = DAG / f'{u:04d}.npz'
        if not o.exists(): continue
        q = proj_npz(np.load(o)); r = {}
        a = D / f'{u - OFFS:04d}.npz'
        if a.exists():
            z = np.load(a); W = 720 if 'dreamina' in las else 540; p = proj_npz(z, W, int(W * 16 / 9), 1080 / W)
            p = np.c_[p, np.ones(len(p))] @ np.array(avb[u - OFFS]['invers']).T; r['A'] = jamfor(p, q)
        b = G / 'kropp' / f'{u:04d}.npz'
        if b.exists(): r['B'] = jamfor(proj_npz(np.load(b)), q)
        if u in sp: r['C'] = jamfor(proj_varld(sp[u]['leder'], nk[u]['matris'], nk[u]['lins_mm']), q)
        rader[u] = r
    def sammanfatta(a, b):
        ut = {}
        for st in 'ABC':
            x = [rader[u][st] for u in range(a, b + 1) if u in rader and st in rader[u]]
            if x: ut[st] = dict(promille=round(float(np.nanmedian([y[0] for y in x])), 1), storlek=round(float(np.median([y[1] for y in x])), 2))
        return ut
    fot = np.array([(np.array(sp[u]['leder']['l_foot']['huvud']) + np.array(sp[u]['leder']['r_foot']['huvud'])) / 2 for u in sorted(sp)])
    res = dict(variant=v, h3_h4=sammanfatta(seg['h3'][0], seg['h4'][1]), h6_h9=sammanfatta(seg['h6'][0], seg['h9'][1]), hela=sammanfatta(OFFS, 154),
               fotter_i_varlden=dict(glidning_xy_m=round(float(np.ptp(fot[:, 0]) + np.ptp(fot[:, 1])), 2), hojd_spann_m=round(float(np.ptp(fot[:, 2])), 2)),
               per_ruta={u: {k: [round(x, 1) if not np.isnan(x) else None for x in (vv[0], vv[1])] for k, vv in r.items()} for u, r in rader.items()})
    (G / 'fel.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: res[k] for k in ('h3_h4', 'h6_h9', 'hela', 'fotter_i_varlden')}, ensure_ascii=False))


if __name__ == '__main__': main()
