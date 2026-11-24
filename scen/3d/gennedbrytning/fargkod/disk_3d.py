"""0025 del B "In i 3D": diskens bildruta ur en färgmask eller segmenterarens mask, matad genom dagens möbelplacering
(kontrakt/mobellyft.los, oförändrad) i en kopia av planen n06-hand. Kedjans kod och planfil ändras inte.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/fargkod/disk_3d.py
Möbellyftet tar bildrutan från tagningens mittruta. För att pröva ruta r sätts S1:s ut-intervall i kopian till [r, r+2], så att mittrutan blir r.
box_2d = [ymin, xmin, ymax, xmax] i promille av bilden. Är botten beskuren används ovankantens bakre kant mot diskens höjd (0,9 m).
Källor per ruta: segmenterarens mask (seg/gelato_<r>__disk_A.png), och färgmasker ur V1, V2 och V3 (codex/), skalade till originalets storlek.
Ut: fargkod/disk_3d.json med diskens läge före och efter, och skillnaden mot n06-hand och mot samspelet ur 0024 (disken 0,15–0,4 m närmare henne).
"""
import copy, json, sys
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; GEN = HIT.parent; KON = GEN.parent / 'kontrakt'; sys.path.insert(0, str(KON))
import mobellyft
PLAN = KON / 'ut/kand-kennysgelato_n06-hand/narvaro/plan.json'
PAL = json.loads((HIT / 'palett.json').read_text(encoding='utf-8'))
HEX = lambda s: np.array([int(s.split('#')[1][i:i + 2], 16) for i in (4, 2, 0)], float)


def mask(kalla, r):
    o = cv2.imread(str(HIT / f'rutor/gelato_{r:03d}.png')); st = o.shape[1::-1]
    if kalla == 'seg':
        p = HIT / f'seg/gelato_{r:03d}__disk_A.png'; return cv2.resize(cv2.imread(str(p), 0), st) > 127 if p.exists() else None
    p = HIT / f'codex/{kalla}_gelato_{r:03d}.png'
    if not p.exists(): return None
    b = cv2.resize(cv2.imdecode(np.fromfile(str(p), np.uint8), 1), st)
    if kalla.startswith('V3'):
        hsv = cv2.cvtColor(b, cv2.COLOR_BGR2HSV); m = ~((hsv[..., 1] < 25) & (hsv[..., 2] > 150))
    else:
        m = np.linalg.norm(b.astype(float) - HEX(dict((i, t) for i, _, t in PAL['gelato'])['disk_A']), axis=2) < 70
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, stt, _ = cv2.connectedComponentsWithStats(m)
    return (lab == 1 + int(np.argmax(stt[1:, cv2.CC_STAT_AREA]))) if n > 1 else None


def main():
    P0 = json.loads(PLAN.read_text(encoding='utf-8')); fore = next(o for o in P0['objekt'] if o['id'] == 'disk_A')['pos_m']; ut = []
    for r in (0, 55, 112):
        for kalla in ('seg', 'V1', 'V2', 'V3disk'):
            m = mask(kalla, r)
            if m is None or not m.any(): ut.append(dict(ruta=r, kalla=kalla, status='mask saknas')); continue
            ys, xs = np.nonzero(m); h, w = m.shape
            box = [round(1000 * ys.min() / h, 1), round(1000 * xs.min() / w, 1), round(1000 * (ys.max() + 1) / h, 1), round(1000 * (xs.max() + 1) / w, 1)]
            P = copy.deepcopy(P0); s1 = next(s for s in P['scener'] if s['id'] == 's1'); s1['ut'] = [r, r + 2]
            P['plats'][0]['deklarerat']['mobler']['disk_A']['bild'] = dict(tagning='s1', box_2d=box)
            rap = mobellyft.los(P) or []; post = next((x for x in rap if x.get('mobel') == 'disk_A'), {})
            efter = next(o for o in P['objekt'] if o['id'] == 'disk_A')['pos_m']
            d = np.array(efter[:2]) - np.array(fore[:2]); th = next(o for o in P0['objekt'] if o['id'] == 'disk_A')['rotation_rad'][2]
            mot_henne = float(d @ np.array([-np.sin(th), np.cos(th)]))   # diskens lokala +y = mot staplatsen
            ut.append(dict(ruta=r, kalla=kalla, box_2d=box, status=post.get('status'), kant=post.get('kant'), orsak=post.get('orsak'), klamd=post.get('klamd'),
                           fore_pos_m=[round(x, 3) for x in fore], efter_pos_m=[round(float(x), 3) for x in efter], flytt_m=round(float(np.linalg.norm(d)), 3),
                           flytt_mot_henne_m=round(mot_henne, 3)))
            print(r, kalla, box, post.get('status'), post.get('kant'), 'flytt', round(float(np.linalg.norm(d)), 3), 'mot henne', round(mot_henne, 3), post.get('orsak') or '')
    (HIT / 'disk_3d.json').write_text(json.dumps(dict(plan=str(PLAN.relative_to(GEN.parent)), samspel_0024='disken 0,15–0,4 m närmare henne', rader=ut), ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__': main()
