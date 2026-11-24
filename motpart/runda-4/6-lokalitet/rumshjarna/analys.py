"""rumshjärna/1, analys: genererade varianter som variabler per scen, och jämförelse mellan scener.

Per tagning (mittrutan): V1 (pipe-vänlig förenkling), V2 (rum utan förgrund), V3 (essens).
- linjering: ECC (affin) mellan kantbilder av original och variant -> förflyttning/skala (variantens trohet mot utsnittet)
- lodlinje: samma L1-regel som lokaliteten på varianternas MoGe/OneFormer, mot originalets fuserade lutning
- etiketter: OneFormer-gruppandelar (original, V1, V2)
- viktighet: V3:s icke-grå pixlar -> andel kvar per originalinstans (väljarens rangordning)
- mellan scener: DINOv2-likhet (original och V2) + SIFT-inliers (original och V2) per par
Skriver ut/rumshjarna/<nyckel>/analys.json. Ingen variant ersätter observationer här; detta är beslutsunderlag.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; LOK = HERE.parent
sys.path.insert(0, str(LOK))
import lokalitet as L  # noqa: E402


def ladda_fil(fil, gk):
    z = np.load(fil); d = z['depth'].astype(np.float32); h, w = d.shape; K = z['intrinsics']
    X, Y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    P = np.stack([(X - K[0, 2]) / K[0, 0] * d, (Y - K[1, 2]) / K[1, 1] * d, d], -1)
    N = z['normal'].astype(np.float32) / 127.0; M = z['mask'] & (d > 0); Lb = z['labels']
    segl = json.loads(bytes(z['segment']).decode())
    G = np.full(Lb.shape, '', dtype=object)
    for i, g in gk.items():
        G[Lb == i] = g
    for s_ in segl:
        if s_['score'] < 0.75:
            G[z['instans'] == s_['id']] = ''
    nn = np.linalg.norm(N, axis=-1, keepdims=True); N = N / np.maximum(nn, 1e-6)
    return {'P': P, 'N': N, 'M': M & np.isfinite(P).all(-1), 'G': G, 'L': Lb, 'K': K, 'I': z['instans'],
            'segs': {s_['id']: s_['etikett'] for s_ in segl}, 'geo': json.loads(bytes(z['geocalib']).decode()) if 'geocalib' in z.files else {}}


def lutning(u):
    return round(math.degrees(math.asin(max(-1, min(1, float(u[2]))))), 1) if u is not None else None


def linjering(a, b):
    ea = cv2.GaussianBlur(cv2.Canny(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), 60, 160).astype(np.float32), (0, 0), 3)
    eb = cv2.GaussianBlur(cv2.Canny(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), 60, 160).astype(np.float32), (0, 0), 3)
    Wm = np.eye(2, 3, dtype=np.float32)
    try:
        cc, Wm = cv2.findTransformECC(ea, eb, Wm, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), None, 5)
    except cv2.error:
        return {'ok': False}
    return {'ok': True, 'ecc': round(float(cc), 3), 'forflyttning_px': [round(float(Wm[0, 2]), 1), round(float(Wm[1, 2]), 1)],
            'skala': round(float(math.sqrt(abs(np.linalg.det(Wm[:, :2])))), 3)}


def andelar(o):
    g = o['G'][o['M']]; t = max(1, len(g))
    return {k: round(float((g == k).sum() / t), 3) for k in ('golv', 'vagg', 'tak', 'bank', 'bord', 'spis', 'skap', 'mat', 'karl', 'person') if (g == k).sum() / t > 0.005}


def main(nyckel='duepiani'):
    d = LOK / 'ut' / 'rumshjarna' / nyckel; out = LOK / 'ut' / nyckel
    meta = json.loads((out / 'obs_gpu.json').read_text(encoding='utf-8')); gk = L.gruppkarta(meta['etiketter']); namn = {int(k): v for k, v in meta['etiketter'].items()}
    rep = json.loads((out / 'lokalitet.json').read_text(encoding='utf-8'))
    sids = sorted({p.name.split('_')[0] for p in d.glob('*_orig.png')}, key=lambda s: int(s[1:]))
    res = {'tagningar': {}, 'mellan': {}}
    bilder = {}
    for sid in sids:
        t = next(x for x in meta['tagningar'] if x['id'] == sid); u = t['nyckelrutor'][len(t['nyckelrutor']) // 2]
        org = cv2.imread(str(d / f'{sid}_orig.png')); bilder[(sid, 'orig')] = org
        oo = L.ladda(out, u, gk, 'obs_gpu'); oo['u'] = u
        r = {'ruta': u, 'L_lutning': rep['tagningar'][sid]['lutning_grader'], 'orig': {'andelar': andelar(oo), 'moge_lutning': lutning(L.lodlinje([oo], None)[0])}}
        for v in ('v1_pipe', 'v2_rum', 'v3_essens'):
            img = cv2.resize(cv2.imread(str(d / f'{sid}_{v}.png')), (org.shape[1], org.shape[0]), interpolation=cv2.INTER_AREA); bilder[(sid, v)] = img
            ov = ladda_fil(d / f'{sid}_{v}.obs.npz', gk)
            uv, kalla, _ = L.lodlinje([ov], None)
            gv = ov['geo'].get('gravity_vec3d')
            r[v] = {'linjering': linjering(org, img), 'andelar': andelar(ov), 'moge_lutning': lutning(uv), 'lodlinje_kalla': kalla,
                    'geocalib_lutning': lutning(np.array(gv) / np.linalg.norm(gv)) if gv else None}
        # viktighet ur V3: icke-grå pixlar, per originalinstans
        v3 = bilder[(sid, 'v3_essens')]; hsv = cv2.cvtColor(v3, cv2.COLOR_BGR2HSV)
        las = hsv[..., 1] < 18  # omättade pixlar; den platta grå tonen är typvärdet av deras ljushet
        mod = int(np.argmax(np.bincount(hsv[..., 2][las].ravel(), minlength=256))) if las.any() else 200
        gra = las & (np.abs(hsv[..., 2].astype(int) - mod) < 14)
        kvar = cv2.resize((~gra).astype(np.uint8), (oo['I'].shape[1], oo['I'].shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
        vikt = []
        for i_, lab in oo['segs'].items():
            m = oo['I'] == i_
            if m.sum() < 50:
                continue
            vikt.append({'instans': int(i_), 'etikett': namn.get(lab, '?').split(',')[0], 'andel_bild': round(float(m.mean()), 3), 'kvar_i_essens': round(float(kvar[m].mean()), 2)})
        r['viktighet'] = sorted(vikt, key=lambda x: -x['kvar_i_essens'])
        res['tagningar'][sid] = r
    # mellan scener: DINOv2 och SIFT
    from transformers import AutoImageProcessor, AutoModel
    import torch
    proc = AutoImageProcessor.from_pretrained('facebook/dinov2-small'); mdl = AutoModel.from_pretrained('facebook/dinov2-small').eval()
    def emb(img):
        with torch.inference_mode():
            o = mdl(**proc(images=cv2.cvtColor(img, cv2.COLOR_BGR2RGB), return_tensors='pt')).last_hidden_state[:, 0]
        return (o / o.norm()).numpy()[0]
    E = {k: emb(v) for k, v in bilder.items() if k[1] in ('orig', 'v2_rum')}
    sift = cv2.SIFT_create(3000); bf = cv2.BFMatcher()
    def sift_inl(a, b):
        ka, da = sift.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), None); kb, db = sift.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), None)
        if da is None or db is None:
            return 0
        mm = [m for m, n in bf.knnMatch(da, db, k=2) if m.distance < 0.75 * n.distance]
        if len(mm) < 15:
            return 0
        F, inl = cv2.findFundamentalMat(np.float32([ka[m.queryIdx].pt for m in mm]), np.float32([kb[m.trainIdx].pt for m in mm]), cv2.USAC_MAGSAC, 1.5, 0.999, 5000)
        return int(inl.sum()) if inl is not None else 0
    l7 = rep.get('rum_over_tagningar', {}).get('grupper', [])
    for i, a in enumerate(sids):
        for b in sids[i + 1:]:
            res['mellan'][f'{a}-{b}'] = {
                'dino_orig': round(float(E[(a, 'orig')] @ E[(b, 'orig')]), 3), 'dino_v2': round(float(E[(a, 'v2_rum')] @ E[(b, 'v2_rum')]), 3),
                'sift_orig': sift_inl(bilder[(a, 'orig')], bilder[(b, 'orig')]), 'sift_v2': sift_inl(bilder[(a, 'v2_rum')], bilder[(b, 'v2_rum')]),
                'L7_samma_rum': any(a in g and b in g for g in l7)}
    (d / 'analys.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    for sid, r in res['tagningar'].items():
        print(sid, 'L', r['L_lutning'], '| moge orig', r['orig']['moge_lutning'], 'v1', r['v1_pipe']['moge_lutning'], 'v2', r['v2_rum']['moge_lutning'],
              '| linjering v1', r['v1_pipe']['linjering'].get('forflyttning_px'), r['v1_pipe']['linjering'].get('skala'), 'v2', r['v2_rum']['linjering'].get('forflyttning_px'),
              '| viktigast', [(x['etikett'], x['kvar_i_essens']) for x in r['viktighet'][:5]], '| minst', [(x['etikett'], x['kvar_i_essens']) for x in r['viktighet'][-3:]])
    for k, v in res['mellan'].items():
        print(k, v)


if __name__ == '__main__':
    main(*(sys.argv[1:] or []))
