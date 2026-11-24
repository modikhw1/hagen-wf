"""0025 del B: mått för färgkodningens varianter, och ett kontaktblad per ruta.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/fargkod/matt.py
Per bild codex/<V>_<klipp>_<ruta>.png (skalad till originalrutans storlek):
- Färgen avläst: pixlar nära paletttonen (RGB-avstånd < TON) blir en mask per id. Mått: andel av bilden, antal delar (> 0,1 % av bilden),
  största delens andel av masken (1 = ett sammanhängande fält).
- Mot segmenteraren (fargkod/seg, samma id): IoU, andel av färgmasken utanför segmenterarens mask (påhittat eller kompletterat där
  något skymde) och andel av segmenterarens mask som färgen inte täcker.
- Bilden kvar (V1 mot originalet, V4 mot den tomma scenen): utanför färgmaskerna (vidgade 15 px) medelavvikelse per pixel, andel pixlar
  som ändrats mer än 40 nivåer, och kantavstånd (Canny) från resultatets kanter till indatats, i promille av bildhöjden.
- V3: allt som inte är jämnt grått är föremålet; IoU och kompletterad andel mot segmenterarens mask.
- Över rutor: medelton per id och yta gånger kamerans skala i kvadrat (kamerafri/avbildning.json), alltså ytan i ruta 0:s skala.
Trösklar är diagnos. Ut: fargkod/matt.json, matt.md, blad_<klipp>_<ruta>.jpg.
"""
import json
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; GEN = HIT.parent; TON = 70
PAL = json.loads((HIT / 'palett.json').read_text(encoding='utf-8'))
HEX = lambda s: np.array([int(s.split('#')[1][i:i + 2], 16) for i in (4, 2, 0)], float)   # BGR
RUTOR = [('gelato', 0), ('gelato', 55), ('gelato', 112), ('guac', 0)]


def las(p, storlek=None):
    b = cv2.imdecode(np.fromfile(str(p), np.uint8), cv2.IMREAD_COLOR) if Path(p).exists() else None
    return cv2.resize(b, storlek, interpolation=cv2.INTER_AREA) if b is not None and storlek and b.shape[1::-1] != storlek else b


def tonmask(b, hx):
    return np.linalg.norm(b.astype(float) - HEX(hx), axis=2) < TON


def delar(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8)); a = st[1:, cv2.CC_STAT_AREA]; tot = m.sum()
    return dict(andel=round(float(m.mean()), 4), delar=int((a > 0.001 * m.size).sum()), storsta_andel=round(float(a.max() / tot), 3) if tot else None)


def kant(a, b, yta):
    ka = cv2.Canny(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), 60, 160) > 0; kb = cv2.Canny(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), 60, 160) > 0
    dt = cv2.distanceTransform((~(kb & yta)).astype(np.uint8), cv2.DIST_L2, 5); d = dt[ka & yta] / a.shape[0] * 1000
    return dict(median=round(float(np.median(d)), 1), p90=round(float(np.percentile(d, 90)), 1)) if d.size else None


def segmask(k, r, id_, st):
    p = HIT / 'seg' / f"{k}_{r:03d}__{id_.replace(':', '-')}.png"
    return (las(p, st)[..., 0] > 127) if p.exists() else None


def mot_seg(m, s):
    if s is None or not s.any(): return None
    return dict(iou=round(float((m & s).sum() / max(1, (m | s).sum())), 3), farg_utanfor_seg=round(float((m & ~cv2.dilate(s.astype(np.uint8), np.ones((15, 15))).astype(bool)).sum() / max(1, m.sum())), 3),
                seg_otackt=round(float((s & ~m).sum() / s.sum()), 3))


def main():
    avb = json.loads((GEN / 'kamerafri/avbildning.json').read_text(encoding='utf-8'))['rutor']; res = {}
    for k, r in RUTOR:
        o = cv2.imread(str(HIT / f'rutor/{k}_{r:03d}.png')); st = o.shape[1::-1]; A = las(HIT / f'rutor/{k}_{r:03d}_A.png', st) if k == 'gelato' else las(HIT / 'codex/A_guac_000.png', st)
        rad = {}; blad = [o]
        for V in ['V1', 'V2', 'V3disk' if k == 'gelato' else 'V3bar', 'V4']:
            b = las(HIT / f'codex/{V}_{k}_{r:03d}.png', st); blad.append(b if b is not None else np.full_like(o, 200))
            if b is None: continue
            m = {}
            if V.startswith('V3'):
                hsv = cv2.cvtColor(b, cv2.COLOR_BGR2HSV); f = ~((hsv[..., 1] < 25) & (hsv[..., 2] > 150))
                f = cv2.morphologyEx(f.astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 9), np.uint8)) > 0
                id_ = 'disk_A' if k == 'gelato' else 'bardisk'; m[id_] = dict(**delar(f), mot_seg=mot_seg(f, segmask(k, r, id_, st)))
                rad[V] = m; continue
            alla = np.zeros(o.shape[:2], bool)
            for id_, _, ton in PAL[k] + ([('person', '', PAL['person'])] if V == 'V2' else []):
                if V == 'V4' and id_ in ('A:hand:provsked', 'foremal_i_hand_A'): continue
                t = tonmask(b, ton); alla |= t
                m[id_] = dict(**delar(t), mot_seg=mot_seg(t, segmask(k, r, id_, st)), medelton_bgr=[int(x) for x in b[t].mean(0)] if t.any() else None,
                              yta_i_ruta0_skala=round(float(t.mean() * avb[r]['skala'] ** 2), 4) if k == 'gelato' else None)
            if V in ('V1', 'V4'):
                ref = o if V == 'V1' else A
                if ref is not None:
                    ute = ~cv2.dilate(alla.astype(np.uint8), np.ones((15, 15))).astype(bool); d = np.abs(b.astype(int) - ref.astype(int)).mean(2)
                    m['bilden_kvar'] = dict(mot='original' if V == 'V1' else 'tom scen', medelavvikelse=round(float(d[ute].mean()), 1), andel_andrad_40=round(float((d[ute] > 40).mean()), 3),
                                            kant_promille=kant(b, ref, ute), andel_utanfor_farg=round(float(ute.mean()), 3))
            if V == 'V2':
                hsv = cv2.cvtColor(b, cv2.COLOR_BGR2HSV); m['gratt_andel'] = round(float(((hsv[..., 1] < 25) & (np.abs(hsv[..., 2].astype(int) - 128) < 30)).mean()), 3)
            rad[V] = m
        res[f'{k}_{r:03d}'] = rad
        h = 640; w = int(h * st[0] / st[1]); t = ['original', 'V1 ton på plats', 'V2 id-karta', 'V3 ett föremål', 'V4 ton + tom scen']
        rader = []
        for b, n in zip(blad, t):
            x = cv2.resize(b, (w, h)); cv2.rectangle(x, (0, 0), (w, 26), (0, 0, 0), -1); cv2.putText(x, n.replace('å', 'a').replace('ö', 'o'), (6, 19), cv2.FONT_HERSHEY_SIMPLEX, .55, (255, 255, 255), 1, cv2.LINE_AA); rader.append(x)
        cv2.imwrite(str(HIT / f'blad_{k}_{r:03d}.jpg'), np.hstack(rader))
    (HIT / 'matt.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    # tabell
    L = ['| Ruta | Variant | Id | Andel | Delar | Största delen | IoU mot seg | Färg utanför seg | Seg otäckt | Bilden kvar: avvikelse, ändrad > 40, kant p90 (promille) |', '|' + '---|' * 10]
    for ruta, rad in res.items():
        for V, m in rad.items():
            bk = m.get('bilden_kvar'); bks = f"{bk['medelavvikelse']}, {bk['andel_andrad_40']}, {(bk['kant_promille'] or {}).get('p90')}" if bk else ''
            for id_, x in m.items():
                if not isinstance(x, dict) or 'andel' not in x: continue
                s = x.get('mot_seg') or {}
                L.append(f"| {ruta} | {V} | {id_} | {x['andel']} | {x['delar']} | {x['storsta_andel']} | {s.get('iou', '—')} | {s.get('farg_utanfor_seg', '—')} | {s.get('seg_otackt', '—')} | {bks} |"); bks = ''
    (HIT / 'matt.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); print('\n'.join(L))


if __name__ == '__main__': main()
