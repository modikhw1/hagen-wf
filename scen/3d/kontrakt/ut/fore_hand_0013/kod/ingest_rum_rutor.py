"""Rutor per element och tagning ur segmenteraren, med tre kontroller (uppdrag 0010, punkt 3; ur ingest/rutprov/ från svar 0008).

    python rum_rutor.py <ingestmapp> <deklaration.json> --seg <seg.json> [--grupper <grupper.json>] [--ut <fil>]

`seg.json` kommer ur `modal_segmentera.py` (Grounding DINO + SAM 2 på Modal, Geminis elementnamn som prompt). Rutan tas ur SAM-masken, mediantagen över bildrutorna.
Kontroller, var och en med orsak i utdata; en ruta som faller i en kontroll förs inte vidare:
  1. överlapp mellan olika element: IoU >= OVERLAPP_IOU i samma tagning stoppar det elementet som segmenteraren var minst säker på,
  2. homografiöverföring inom kameragrupperna (grupper.json): rutan förs över till en annan tagning på samma plats och måste ha IoU >= HOM_IOU_MIN mot dess egen ruta,
  3. `null`: hittar segmenteraren inte elementet (poäng under MIN_POANG) ges ingen ruta.
Trösklarna är valda diagnostiska värden (OVERLAPP_IOU=0,7, HOM_IOU_MIN=0,25, MIN_POANG=0,25), inte härledda ur data.

Uppdrag 0012: varje ruta bär också `spridning_2d` (per kant, största minus minsta över bildrutorna, promille), `tyngdpunkt_2d` ([y, x] promille, maskens
tyngdpunkt, median), `bredd_2d`/`hojd_2d` (maskens bredd på tyngdpunktens rad och höjd, promille) och, med --grupper, `grupp` (den mätta kameragruppen,
annars tagningen själv). Med segmenterarens separata prompter (modal_segmentera.py, förval) väljs fynd på exakt prompt i stället för gemensamma ord,
så att 'butcher counter electronic scale' inte längre räknas som disk. Ett föremåls deklarerade `storlek_m` följer med i `bild.storlek_m_dekl`, eftersom
deklaration_till_hand.py bara för vidare `pa`, `halls_av`, `bild` och `bilder` (används av kontrakt/foremallyft.py för bredden ur masken).
"""
import argparse, itertools, json, statistics
from pathlib import Path

import numpy as np

OVERLAPP_IOU, HOM_IOU_MIN, MIN_POANG = .7, .25, .25


def iou(a, b):
    ix = max(0., min(a[3], b[3]) - max(a[1], b[1])); iy = max(0., min(a[2], b[2]) - max(a[0], b[0])); i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0.


def _per_mille(b, w, h): return [b[1] / h * 1000, b[0] / w * 1000, b[3] / h * 1000, b[2] / w * 1000]


def _valj(r, prompt, ord_):
    """Fyndet för prompten i en bildruta. Separata prompter: exakt prompt. Gemensam prompt (äldre seg.json): gemensamma ord. Högst poäng, sedan ruta (deterministiskt)."""
    if any(f.get('prompt') is not None for f in r['fynd']):
        kand = [f for f in r['fynd'] if f.get('prompt') == prompt and f['poang'] >= MIN_POANG]
    else:
        kand = [f for f in r['fynd'] if set(str(f['etikett']).lower().split()) & ord_ and f['poang'] >= MIN_POANG]
    return min(kand, key=lambda z: (-z['poang'], z['dino_box_px'])) if kand else None


def rutor_ur_seg(seg, prompter, tillatna=None):
    """{element: {tagning: dict(box_2d, poang, antal, spridning_2d, ...)}} ur seg.json (resultat per bildruta, id `S<n>_<ruta>`). `tillatna`: {element: set(tagningar)} (None = alla)."""
    ut = {}; null = []
    tagningar = sorted({r['id'].split('_')[0] for r in seg['resultat']}, key=lambda s: int(s[1:]))
    for el, prompt in prompter.items():
        ord_ = set(prompt.lower().replace('.', ' ').split())
        for t in tagningar:
            if tillatna and t not in tillatna.get(el, {t}): continue
            boxar, poang, tp, br, ho = [], [], [], [], []
            for r in sorted(seg['resultat'], key=lambda r: int(r['id'].split('_')[1])):
                if r['id'].split('_')[0] != t: continue
                f = _valj(r, prompt, ord_)
                if f is None: continue
                b = f.get('mask_box_px') or f['dino_box_px']
                boxar.append(_per_mille(b, r['bredd'], r['hojd'])); poang.append(f['poang'])
                if f.get('mask_tyngdpunkt_px'):
                    tp.append([f['mask_tyngdpunkt_px'][1] / r['hojd'] * 1000, f['mask_tyngdpunkt_px'][0] / r['bredd'] * 1000])
                    br.append(f['mask_bredd_px'] / r['bredd'] * 1000); ho.append(f['mask_hojd_px'] / r['hojd'] * 1000)
            if boxar:
                B = np.array(boxar)
                post = dict(box_2d=[round(float(v)) for v in np.median(B, axis=0)], poang=round(float(np.mean(poang)), 3), antal=len(boxar),
                            spridning_2d=[round(float(v)) for v in (B.max(axis=0) - B.min(axis=0))])
                if tp:
                    post.update(tyngdpunkt_2d=[round(float(v), 1) for v in np.median(np.array(tp), axis=0)],
                                bredd_2d=round(float(np.median(br)), 1), hojd_2d=round(float(np.median(ho)), 1))
                ut.setdefault(el, {})[t] = post
            else: null.append(dict(element=el, tagning=t, orsak='null: segmenteraren hittade inte elementet'))
    return ut, null


def kontrollera_overlapp(rutor, tak=OVERLAPP_IOU):
    """Stoppar, per tagning, det av två element som överlappar (IoU >= tak) och som segmenteraren var minst säker på."""
    stoppade = []
    for t in sorted({t for d in rutor.values() for t in d}, key=lambda s: int(s[1:])):
        for a, b in itertools.combinations([e for e in rutor if t in rutor[e]], 2):
            v = iou(rutor[a][t]['box_2d'], rutor[b][t]['box_2d'])
            if v >= tak:
                svag = a if rutor[a][t]['poang'] <= rutor[b][t]['poang'] else b; stark = b if svag == a else a
                stoppade.append(dict(element=svag, tagning=t, kontroll='overlapp', iou=round(v, 2), orsak=f'rutan sammanfaller med {stark} (IoU {v:.2f}); {svag} var minst säker'))
    return stoppade


def kontrollera_homografi(rutor, grupper, homografi, min_iou=HOM_IOU_MIN):
    """`homografi(a, b)` ger en 3x3-matris (bildpunkter i a -> b, i bildandelar 0-1000 omräknade av anroparen) eller None. Inom varje grupp förs varje rutpar över och jämförs."""
    stoppade = []; kontroller = []
    for g in grupper:
        for a, b in itertools.permutations(g, 2):
            H = homografi(a, b)
            if H is None: continue
            for el in rutor:
                if a not in rutor[el] or b not in rutor[el]: continue
                y0, x0, y1, x1 = rutor[el][a]['box_2d']; pts = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1], ]); hom = np.c_[pts, np.ones(4)] @ np.asarray(H).T; hom = hom[:, :2] / hom[:, 2:3]
                t = [float(np.clip(hom[:, 1].min(), 0, 1000)), float(np.clip(hom[:, 0].min(), 0, 1000)), float(np.clip(hom[:, 1].max(), 0, 1000)), float(np.clip(hom[:, 0].max(), 0, 1000))]
                v = iou(t, rutor[el][b]['box_2d']); kontroller.append(dict(element=el, fran=a, till=b, iou=round(v, 2)))
                if v < min_iou:
                    for tag in (a, b): stoppade.append(dict(element=el, tagning=tag, kontroll='homografi', iou=round(v, 2), orsak=f'rutan i {a} förd till {b} har IoU {v:.2f} mot dess egen ruta (under {min_iou})'))
    uniq = {(s['element'], s['tagning'], s['kontroll']): s for s in stoppade}
    return list(uniq.values()), kontroller


def tillampa(rutor, stoppade):
    stopp = {(s['element'], s['tagning']) for s in stoppade}
    return {el: {t: v for t, v in d.items() if (el, t) not in stopp} for el, d in rutor.items()}


EXTRA = ('spridning_2d', 'tyngdpunkt_2d', 'bredd_2d', 'hojd_2d')


def gruppnamn(t, grupper):
    """Den mätta kameragruppen för tagningen ('S8+S10'), annars tagningen själv."""
    g = next((g for g in (grupper or []) if t in g), None)
    return '+'.join(sorted(g, key=lambda x: int(x[1:]))) if g else t


def skriv_deklaration(D, rutor, stoppade, null, kalla, grupper=None):
    """Kopia av deklarationen där `bilder` (och `bild`) kommer ur de kontrollerade rutorna. Elementet utan ruta får tom lista (uttryckligt "inga rutor")."""
    D = json.loads(json.dumps(D))
    for el, mal in list(D['platser'].items()) + list((D.get('foremal') or {}).items()):
        if el not in rutor and not (isinstance(mal, dict) and ('bilder' in mal or 'bild' in mal)): continue
        r = rutor.get(el, {})
        mal['bilder'] = [dict(tagning=t, box_2d=v['box_2d'], **{k: v[k] for k in EXTRA if k in v}, **({'grupp': gruppnamn(t, grupper)} if grupper is not None else {}))
                         for t, v in sorted(r.items(), key=lambda kv: int(kv[0][1:]))]; mal['bilder_kalla'] = kalla
        if r:
            b = max(r.items(), key=lambda kv: (kv[1]['box_2d'][2] - kv[1]['box_2d'][0]) * (kv[1]['box_2d'][3] - kv[1]['box_2d'][1]))
            mal['bild'] = dict(tagning=b[0], box_2d=b[1]['box_2d'])
            if el in (D.get('foremal') or {}) and mal.get('storlek_m') is not None: mal['bild']['storlek_m_dekl'] = mal['storlek_m']
        else: mal.pop('bild', None)
    D['rutor_stoppade'] = stoppade; D['rutor_null'] = null
    return D


def _homografi_fran_bilder(ingest):
    import cv2
    I = Path(ingest); sift = cv2.SIFT_create(nfeatures=4000); clahe = cv2.createCLAHE(2., (8, 8)); bf = cv2.BFMatcher(cv2.NORM_L2); cache = {}

    def ruta(sid):
        if sid in cache: return cache[sid]
        cap = cv2.VideoCapture(str(I / 'klipp' / f'{sid}.mp4')); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.set(cv2.CAP_PROP_POS_FRAMES, n // 2); ok, img = cap.read()
        h, w = img.shape[:2]; fri = np.full((h, w), 255, np.uint8); mf = I / sid / 'masker.npy'
        if mf.exists():
            M = np.load(mf, allow_pickle=True)
            if len(M) == n: fri[cv2.dilate(cv2.resize(M[n // 2].astype(np.uint8) * 255, (w, h), interpolation=cv2.INTER_NEAREST), np.ones((25, 25), np.uint8)) > 0] = 0
        kp, d = sift.detectAndCompute(clahe.apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)), fri); cache[sid] = (kp, d, w, h); return cache[sid]

    def hom(a, b):
        ka, da, wa, ha = ruta(a); kb, db, wb, hb = ruta(b)
        m = [x[0] for x in bf.knnMatch(da, db, k=2) if len(x) == 2 and x[0].distance < .8 * x[1].distance]
        if len(m) < 20: return None
        p1 = np.float32([ka[x.queryIdx].pt for x in m]); p2 = np.float32([kb[x.trainIdx].pt for x in m])
        Hm, mask = cv2.findHomography(p1, p2, cv2.USAC_MAGSAC, 3.0)
        if Hm is None or mask.sum() < 40: return None
        # till bildandelar 0-1000 (x mot bredd, y mot höjd): H_andel = S_b^-1 H S_a
        Sa = np.diag([wa / 1000., ha / 1000., 1.]); Sb = np.diag([wb / 1000., hb / 1000., 1.]); return np.linalg.inv(Sb) @ Hm @ Sa
    return hom


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('ingest'); a.add_argument('deklaration'); a.add_argument('--seg', required=True); a.add_argument('--grupper'); a.add_argument('--ut'); x = a.parse_args()
    D = json.loads(Path(x.deklaration).read_text(encoding='utf-8')); seg = json.loads(Path(x.seg).read_text(encoding='utf-8')); prompter = seg['prompter']
    tillatna = {k: set(v.get('tagningar_i_bild') or []) for k, v in list(D['platser'].items()) + list((D.get('foremal') or {}).items()) if k in prompter}
    rutor, null = rutor_ur_seg(seg, prompter, {k: v for k, v in tillatna.items() if v})
    stopp = kontrollera_overlapp(rutor); kontr = []; grupper = None
    if x.grupper:
        grupper = json.loads(Path(x.grupper).read_text(encoding='utf-8'))['delar_plats']; s2, kontr = kontrollera_homografi(rutor, grupper, _homografi_fran_bilder(x.ingest)); stopp += s2
    kvar = tillampa(rutor, stopp)
    ut = Path(x.ut) if x.ut else Path(x.deklaration).with_name(Path(x.deklaration).stem + '_segment.json')
    ut.write_text(json.dumps(skriv_deklaration(D, kvar, stopp, null, 'rum_rutor.py: Grounding DINO + SAM 2, median över bildrutorna, efter kontroller', grupper), ensure_ascii=False, indent=2), encoding='utf-8')
    (ut.with_suffix('.kontroller.json')).write_text(json.dumps(dict(rutor_fore=rutor, stoppade=stopp, null=null, homografi=kontr, troskel=dict(overlapp_iou=OVERLAPP_IOU, hom_iou_min=HOM_IOU_MIN, min_poang=MIN_POANG)), ensure_ascii=False, indent=1), encoding='utf-8')
    for el, d in kvar.items(): print(f'{el:<10}', ' '.join(f"{t}:{v['box_2d']}" for t, v in sorted(d.items(), key=lambda kv: int(kv[0][1:]))) or 'inga rutor')
    print('stoppade:', [(s['element'], s['tagning'], s['kontroll']) for s in stopp], '| null:', len(null), '->', ut)
