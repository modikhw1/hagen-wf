"""rumshjärna: andra rösten om 'samma plats' mellan tagningar, på rummet utan förgrund (V2).

Röster per par:
- geometri på V2 (SIFT + MAGSAC, fundamentalmatris): inliers på rummet när personerna är borta
- utseende (DINOv2 CLS) på V2 och original
- L7 (geometriska bevis på originalen, lokalitet.py)
Cirkularitet: ett par där den ena genererats MOT den andra (eller båda mot samma ankare) har likhet som hjärnan själv
skapat; dess röst räknas inte.
Beslut (konservativt, utseende ensamt länkar aldrig):
- 'trolig_samma_plats_utan_bevis': ej L7, ej betingat, geometri på V2 >= 25 inliers -> kandidat, renderas utan koppling
- 'lika_utseende_utan_geometri': ej L7, DINO >= 0.85, geometri < 25 -> renderas utan koppling (t.ex. matnärbilder)
- 'L7_men_olika_utseende': L7, ej betingat, DINO < 0.4 -> konflikt att granska
usage: python likhet.py <nyckel>
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; LOK = HERE.parent
GEO_MIN = 25


def main(nyckel):
    d = LOK / 'ut' / 'rumshjarna' / nyckel; fyll = d / 'fyllnad'
    plan = json.loads((d / 'plan.json').read_text(encoding='utf-8')); tag = plan['tagningar']
    rep = json.loads((LOK / 'ut' / nyckel / 'lokalitet.json').read_text(encoding='utf-8'))
    grupper = rep.get('rum_over_tagningar', {}).get('grupper', [])
    bild = {s: cv2.imread(str(fyll / f'{s}_v2.png' if (fyll / f'{s}_v2.png').is_file() else d / f'{s}_orig.png')) for s in tag}
    orig = {s: cv2.imread(str(d / f'{s}_orig.png')) for s in tag}
    from transformers import AutoImageProcessor, AutoModel
    import torch
    proc = AutoImageProcessor.from_pretrained('facebook/dinov2-small'); mdl = AutoModel.from_pretrained('facebook/dinov2-small').eval()
    def emb(im):
        with torch.inference_mode():
            o = mdl(**proc(images=cv2.cvtColor(im, cv2.COLOR_BGR2RGB), return_tensors='pt')).last_hidden_state[:, 0]
        return (o / o.norm()).numpy()[0]
    E = {s: emb(b) for s, b in bild.items()}; E0 = {s: emb(b) for s, b in orig.items()}
    sift = cv2.SIFT_create(4000); bf = cv2.BFMatcher(); kd = {s: sift.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), None) for s, b in bild.items()}
    def geo(x, y):
        (ka, da), (kb, db) = kd[x], kd[y]
        if da is None or db is None or len(ka) < 20 or len(kb) < 20:
            return 0
        mm = [m for m, n in bf.knnMatch(da, db, k=2) if m.distance < 0.75 * n.distance]
        if len(mm) < 15:
            return 0
        F, inl = cv2.findFundamentalMat(np.float32([ka[m.queryIdx].pt for m in mm]), np.float32([kb[m.trainIdx].pt for m in mm]), cv2.USAC_MAGSAC, 1.5, 0.999, 5000)
        return int(inl.sum()) if inl is not None else 0
    def betingat(x, y):
        ax, ay = tag[x].get('ankare'), tag[y].get('ankare')
        return bool(ax and ax == ay and (tag[x]['behov'] or tag[y]['behov']))
    ids = sorted(tag, key=lambda s: int(s[1:])); par = []
    for i, x in enumerate(ids):
        for y in ids[i + 1:]:
            par.append({'par': f'{x}-{y}', 'L7': any(x in g and y in g for g in grupper), 'betingat': betingat(x, y),
                        'geo_rum': geo(x, y), 'dino_rum': round(float(E[x] @ E[y]), 3), 'dino_orig': round(float(E0[x] @ E0[y]), 3)})
    fri = [p for p in par if not p['L7'] and not p['betingat']]
    res = {'par': par, 'geo_min': GEO_MIN,
           'trolig_samma_plats_utan_bevis': [p['par'] for p in fri if p['geo_rum'] >= GEO_MIN],
           'lika_utseende_utan_geometri': [p['par'] for p in fri if p['dino_rum'] >= 0.85 and p['geo_rum'] < GEO_MIN],
           'L7_men_olika_utseende': [p['par'] for p in par if p['L7'] and not p['betingat'] and p['dino_rum'] < 0.4],
           'L7_geo_rum': {p['par']: p['geo_rum'] for p in par if p['L7']}}
    (d / 'likhet.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print(nyckel, json.dumps({k: v for k, v in res.items() if k != 'par'}, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])
