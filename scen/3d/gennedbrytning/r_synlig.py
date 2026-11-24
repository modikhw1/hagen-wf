"""0028 punkt 3: syns armen och tråget? Andel synliga handpunkter och andel synligt tråggolv per ruta, genom planens renderkamera.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/r_synlig.py <plan.json med objekten> <samspel.json> [--kamera <plan.json med kameran>] [--rutor 45 70]
Synlig = inom bilden (1080 × 1920) och strålen från kameran till punkten skär ingen låda i planen (diskens bas och kanter, kunden,
bänken), utom den låda punkten själv ligger på. Lådor med synlig_ut utanför rutan räknas inte. Väggar och golv räknas inte (de skymmer
inte disken från kundens sida). Ingen rendering: ren geometri mot planens lådor, så måttet går att räkna för en kamera före bygget.
Handpunkter: r_wrist, r_index3, r_middle3, r_thumb3 (svansen, alltså fingertopparna) och skeden.
Tråget: 5 × 4 punkter på tråggolvets ovansida (disk_A:trag), inom ±0,35 m längs disken från handledens läge i rutan (karet hon skopar i).
Ut: utskrift (json); --ut <fil> sparar.
"""
import json, math, sys
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent
HAND = ['r_wrist', 'r_index3', 'r_middle3', 'r_thumb3']
SKIPPA = {'golv', 'vagg_bak', 'vagg_sida'}
GLAS = set(sys.argv[sys.argv.index('--glas') + 1].split(',')) if '--glas' in sys.argv else set()   # 0028: genomskinliga lådor (montrens glasfront) skymmer inte


def _arg(n, f): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else f


def lador(plan, u):
    ut = []
    for o in plan['objekt']:
        if o['id'] in SKIPPA or o['id'] in GLAS or o.get('typ') not in ('lada', 'cylinder'): continue
        a, b = o.get('synlig_ut') or (0, 10 ** 6)
        if not a <= u < b: continue
        y = o['rotation_rad'][2]; p = o['rotation_rad'][1]; c = np.array(o['pos_m'])
        Rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
        Ry = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
        ut.append((o['id'], c, Rz @ Ry, np.array(o['matt_m']) / 2))
    return ut


def traffar(C, P, lada, eps=1e-3):
    """Skär sträckan C -> P lådan (före P)? Slab-test i lådans ram."""
    _, c, R, h = lada; o = R.T @ (C - c); d = R.T @ (P - C); t0, t1 = 0., 1. - eps
    for i in range(3):
        if abs(d[i]) < 1e-12:
            if abs(o[i]) > h[i]: return False
            continue
        a, b = (-h[i] - o[i]) / d[i], (h[i] - o[i]) / d[i]
        if a > b: a, b = b, a
        t0, t1 = max(t0, a), min(t1, b)
        if t0 > t1: return False
    return True


def i_bild(P, M, lins):
    R, C = M[:3, :3], M[:3, 3]; x = (P - C) @ R
    if x[2] >= 0: return False
    f = lins / 36 * 1080; u = f * x[0] / -x[2] + 540; v = -f * x[1] / -x[2] + 960
    return 0 <= u < 1080 and 0 <= v < 1920


def synlig(P, M, lins, lad, egen=None):
    if not i_bild(P, M, lins): return False, 'utanför bild'
    for l in lad:
        if l[0] == egen: continue
        if traffar(M[:3, 3], P, l): return False, l[0]
    return True, None


def main():
    plan = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')); kam = json.loads(Path(_arg('--kamera', sys.argv[1])).read_text(encoding='utf-8'))
    sp = {r['ruta']: r for r in json.loads(Path(sys.argv[2]).read_text())['rutor']}
    a, b = int(_arg('--rutor', '45')), int(sys.argv[sys.argv.index('--rutor') + 2]) if '--rutor' in sys.argv else 70
    nk = kam['renderkamera']['nycklar']; tr = next(o for o in plan['objekt'] if o['id'] == 'disk_A:trag')
    th = tr['rotation_rad'][2]; ex, ey = np.array([math.cos(th), math.sin(th), 0]), np.array([-math.sin(th), math.cos(th), 0])
    c = np.array(tr['pos_m']) + [0, 0, tr['matt_m'][2] / 2 + .002]
    rader, skym = [], {}
    for u in range(a, b + 1):
        if u not in sp: continue
        M = np.array(nk[u]['matris']); L = nk[u]['lins_mm']; lad = lador(plan, u); r = sp[u]
        hx = (np.array(r['leder']['r_wrist']['huvud']) - c) @ ex
        trag = [c + ex * (hx + (i / 4 - .5) * .7) + ey * (j / 3 - .5) * tr['matt_m'][1] * .9 for i in range(5) for j in range(4)]
        pk = [np.array(r['leder'][j]['svans' if j != 'r_wrist' else 'huvud']) for j in HAND] + ([np.array(r['sked'])] if r.get('sked') else [])
        hs = [synlig(p, M, L, lad) for p in pk]; ts = [synlig(p, M, L, lad, 'disk_A:trag') for p in trag]
        for _, k in hs + ts:
            if k: skym[k] = skym.get(k, 0) + 1
        rader.append(dict(ruta=u, hand=round(sum(h for h, _ in hs) / len(hs), 2), trag=round(sum(t for t, _ in ts) / len(ts), 2)))
    res = dict(rutor=[a, b], hand_synlig_andel=round(float(np.mean([r['hand'] for r in rader])), 2), trag_synlig_andel=round(float(np.mean([r['trag'] for r in rader])), 2),
               rutor_med_hela_handen=sum(r['hand'] == 1 for r in rader), av=len(rader), skyms_av=skym, per_ruta=rader)
    if '--ut' in sys.argv: Path(_arg('--ut', '')).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in res.items() if k != 'per_ruta'}, ensure_ascii=False))


if __name__ == '__main__': main()
