"""Brännvidd per klipp med redovisad källa (uppdrag 0009).

Tagningar ur samma klipp är filmade med samma telefon. Ett COLMAP-värde från en enskild, ofta nästan statisk tagning kan vara fel med
en faktor två eller mer (b-tilltal S5: 2 335 px mot cirka 1 000 px i resten), så värdet per tagning prövas mot klippets spridning.

    skatta_klipp(ingestmapp)  -> kandidater per tagning (COLMAP rå, försvinningspunkter) ur bilderna och kamera.json
    bestam(tagningar, dim)    -> fokal_px, fokal_status (matt | skattad | antagen) och fokal_kalla per tagning (rena tal, utan bilder)

Egna trösklar (diagnos, inte krav): se konstanterna nedan.
"""
import json, math
from pathlib import Path

import numpy as np

VP_INTERVALL = (.3, 3.)          # kandidater utanför dessa kvoter av längsta sidan kastas
MIN_KANDIDATER = 6               # färre än så ger inget klippvärde
MIN_TAGNINGAR = 2                # kandidater måste komma från minst så många tagningar
ZOOM_MATCH = .15                 # egen försvinningspunkts-median och COLMAP inom 15 % = oberoende bekräftelse av tagningens eget värde
ZOOM_AVVIK = .35                 # avvikelse från klippvärdet över 35 % kan vara en riktig zoomändring


def _kvartiler(v):
    return float(np.percentile(v, 25)), float(np.percentile(v, 50)), float(np.percentile(v, 75))


def bestam(tagningar, dim, marginal=1.0):
    """tagningar: {id: dict(colmap=<px|None>, colmap_godkand=<bool>, vp=[px, ...])}. Returnerar (klipp, per_tagning).

    - Klippvärde = median av alla försvinningspunktskandidater (och COLMAP-värden inom spridningen), med kvartilerna som spridning.
    - En tagnings COLMAP-värde godtas (`matt`) bara om det ligger inom klippets spridning; annars får tagningen klippvärdet (`skattad`).
    - Rörlig zoom: avviker tagningen från klippvärdet över ZOOM_AVVIK men dess egna försvinningspunkter och COLMAP stämmer med varandra
      (ZOOM_MATCH), behåller tagningen sitt eget värde (`matt`) och avvikelsen loggas. Annars klippvärdet, och avvikelsen loggas.
    - Saknas allt: `max(bredd, höjd)`, `antagen` (som i dag).
    """
    lo, hi = VP_INTERVALL[0] * dim, VP_INTERVALL[1] * dim
    pool = []; tag_med_kand = set()
    for t, d in tagningar.items():
        for f in d.get('vp') or []:
            if lo <= f <= hi: pool.append(float(f)); tag_med_kand.add(t)
    klipp = dict(antal_kandidater=len(pool), antal_tagningar=len(tag_med_kand), dim=dim)
    if len(pool) >= MIN_KANDIDATER and len(tag_med_kand) >= MIN_TAGNINGAR:
        q1, med, q3 = _kvartiler(pool); klipp.update(fokal_px=round(med, 1), spridning_px=[round(q1 / marginal, 1), round(q3 * marginal, 1)], kalla='försvinningspunkter (median)')
    per = {}
    for t, d in tagningar.items():
        c = d.get('colmap'); ok = bool(d.get('colmap_godkand')); eget = [f for f in (d.get('vp') or []) if lo <= f <= hi]
        post = dict(fokal_px=float(dim), fokal_status='antagen', fokal_kalla='bildens längsta sida', colmap_px=c)
        if 'fokal_px' in klipp:
            s0, s1 = klipp['spridning_px']; post.update(fokal_px=klipp['fokal_px'], fokal_status='skattad', fokal_kalla=f"klippets median ({klipp['antal_kandidater']} kandidater, spridning {s0:.0f}–{s1:.0f} px)")
            if c is not None and ok and s0 <= c <= s1:
                post.update(fokal_px=float(c), fokal_status='matt', fokal_kalla='COLMAP, inom klippets spridning')
            elif c is not None and ok:
                ev = float(np.median(eget)) if len(eget) >= 3 else None
                zoom = ev is not None and abs(ev - c) / c <= ZOOM_MATCH and abs(c - klipp['fokal_px']) / klipp['fokal_px'] > ZOOM_AVVIK
                if zoom:
                    post.update(fokal_px=float(c), fokal_status='matt', fokal_kalla='COLMAP bekräftad av egna försvinningspunkter (rörlig zoom)')
                post['avvikelse'] = dict(colmap_px=c, klippvarde_px=klipp['fokal_px'], kvot=round(c / klipp['fokal_px'], 2), egen_vp_median_px=ev,
                                         utfall='eget värde behålls (rörlig zoom)' if zoom else 'klippets värde används; COLMAP-värdet ligger utanför spridningen')
        elif c is not None and ok:
            post.update(fokal_px=float(c), fokal_status='matt', fokal_kalla='COLMAP (inget klippvärde att pröva mot)')
        per[t] = post
    return klipp, per


# ---- Ur bilder: försvinningspunkter (samma metod som kontrakt/ut/diag_0004/vp.py) ----
def _segment(cv2, klipp_mp4, masker_npy, q, bredd, hojd, overlay):
    cap = cv2.VideoCapture(str(klipp_mp4)); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); f = int(q * (n - 1)); cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ok, img = cap.read()
    if not ok: return np.zeros((0, 4))
    img = cv2.resize(img, (bredd, hojd)); g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fri = np.full((hojd, bredd), 255, np.uint8)
    if masker_npy and Path(masker_npy).exists():
        M = np.load(masker_npy, allow_pickle=True)
        if len(M) == n: fri[cv2.dilate(cv2.resize(M[f].astype(np.uint8) * 255, (bredd, hojd), interpolation=cv2.INTER_NEAREST), np.ones((25, 25), np.uint8)) > 0] = 0
    if overlay: fri[int(overlay[1] * hojd):int(overlay[3] * hojd), int(overlay[0] * bredd):int(overlay[2] * bredd)] = 0
    L = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(g)[0]
    if L is None: return np.zeros((0, 4))
    L = L.reshape(-1, 4); mx = ((L[:, 0] + L[:, 2]) / 2).astype(int).clip(0, bredd - 1); my = ((L[:, 1] + L[:, 3]) / 2).astype(int).clip(0, hojd - 1)
    ln = np.hypot(L[:, 2] - L[:, 0], L[:, 3] - L[:, 1]); return L[(fri[my, mx] > 0) & (ln > .034 * hojd)]


def _vp_ransac(l, mid, rng, iter=1500, tol_deg=1.8):
    best = None
    for _ in range(iter):
        i, j = rng.choice(len(l), 2, replace=False); v = np.cross(l[i], l[j])
        if abs(v[2]) < 1e-9: continue
        dm = v[:2] / v[2] - mid[:, :2]
        ang = np.degrees(np.arccos(np.clip(np.abs(np.sum(dm / (np.linalg.norm(dm, axis=1, keepdims=True) + 1e-9) * np.c_[-l[:, 1], l[:, 0]], axis=1)), 0, 1)))
        inl = ang < tol_deg
        if best is None or inl.sum() > best[1].sum(): best = (v, inl)
    return best


def vp_kandidater(klipp_mp4, masker_npy=None, bredd=576, hojd=1024, overlay=None, q=(.2, .5, .8), min_inl=12, seed=1):
    """Fokalkandidater (px, vid bildbredden `bredd`x`hojd`) ur ortogonala par av försvinningspunkter."""
    import cv2
    rng = np.random.default_rng(seed); C = np.array([bredd / 2., hojd / 2.]); ut = []
    for qq in q:
        L = _segment(cv2, klipp_mp4, masker_npy, qq, bredd, hojd, overlay)
        if len(L) < 25: continue
        p1 = np.c_[L[:, 0:2], np.ones(len(L))]; p2 = np.c_[L[:, 2:4], np.ones(len(L))]; l = np.cross(p1, p2); l /= np.linalg.norm(l[:, :2], axis=1, keepdims=True) + 1e-9
        mid = (p1 + p2) / 2; vps = []; rest = np.arange(len(l))
        for _ in range(3):
            if len(rest) < 12: break
            b = _vp_ransac(l[rest], mid[rest], rng)
            if b is None or b[1].sum() < min_inl: break
            vps.append((b[0] / b[0][2], int(b[1].sum()))); rest = rest[~b[1]]
        for a in range(len(vps)):
            for b_ in range(a + 1, len(vps)):
                f2 = -float((vps[a][0][:2] - C) @ (vps[b_][0][:2] - C))
                if f2 > 0 and min(vps[a][1], vps[b_][1]) >= min_inl: ut.append(math.sqrt(f2))
    return ut


def skatta_klipp(ingest, overlay=None):
    """Kandidater per tagning ur ingestmappen (kamera.json, sekvensfilerna och klippen). Skriver inget.

    COLMAP-värdet är `beslut.colmap_fokal_px` eller, i äldre kamera.json utan `beslut`, `fokal_px`. Godkänt = klarar dagens `regler.kamerabeslut`.
    `idag_fokal_px` är värdet som faktiskt ligger i kroppsläsningen (`sekvens_*.npz`), annars beslutet."""
    import regler
    I = Path(ingest); ut = {}
    for m in sorted(I.glob('S*/meta.json'), key=lambda p: int(p.parent.name[1:])):
        sid = m.parent.name; meta = json.loads(m.read_text(encoding='utf-8', errors='replace')); kj = m.parent / 'kamera.json'
        kam = json.loads(kj.read_text(encoding='utf-8', errors='replace')) if kj.exists() else {}; b = kam.get('beslut') or {}
        besl = b or (regler.kamerabeslut(kam, meta) if kam else {})
        colmap = b.get('colmap_fokal_px') or (kam.get('fokal_px') if not b else None) or None
        sek = sorted(m.parent.glob('sekvens_*.npz')); idag = besl.get('fokal_px')
        if sek:
            with np.load(sek[0], allow_pickle=True) as z: idag = float(z['fokal'])
        film = I / 'klipp' / f'{sid}.mp4'
        vp = vp_kandidater(film, m.parent / 'masker.npy', bredd=int(meta.get('bredd') or 576), hojd=int(meta.get('hojd') or 1024), overlay=overlay) if film.exists() else []
        ut[sid] = dict(colmap=colmap, colmap_godkand=besl.get('kalla') == 'COLMAP', vp=[round(v, 1) for v in vp], idag_fokal_px=idag,
                       bredd=meta.get('bredd'), hojd=meta.get('hojd'))
    return ut


if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser(description='Skriver <ingestmapp>/fokal_klipp.json (fokal per tagning med status och källa). Läses av ingest_klipp.steg_kropp.')
    a.add_argument('ingest'); a.add_argument('--overlay', help='x0,y0,x1,y1 som andel av bilden (överlägg att maska)'); x = a.parse_args()
    tag = skatta_klipp(x.ingest, [float(v) for v in x.overlay.split(',')] if x.overlay else None)
    dim = max(max(int(t.get('bredd') or 0), int(t.get('hojd') or 0)) for t in tag.values())
    klipp, per = bestam({t: dict(colmap=d['colmap'], colmap_godkand=d['colmap_godkand'], vp=d['vp']) for t, d in tag.items()}, dim)
    (Path(x.ingest) / 'fokal_klipp.json').write_text(json.dumps(dict(klipp=klipp, tagningar=per), ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(klipp, ensure_ascii=False)); [print(t, p['fokal_px'], p['fokal_status'], p['fokal_kalla']) for t, p in per.items()]
