"""0017 del C: isolerad person som bild, och låsningsmått.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/c_isolerad.py [C1 C2 C3 ...]
C1 luma/agent/uni-1/v1/edit, STEP B (PROMPT-AB.txt, utan bild 3): original + tom scen (B2, registrerad) som referens.
C2 luma/agent/uni-1/v1/edit, STEP 1 VERSION 3 (PROMPT.txt) på luma-agaren/steg1/guidebild_last_position.png.
C3 fal-ai/nano-banana-pro/edit, STEP B, bild 1 och 2, aspect_ratio 9:16.
Mått (låsning): resultatet registreras mot originalet på hennes synliga överkropp (ORB inom ingestens mask, homografi). Skala och förskjutning
av huvud (maskens topp) och axlar ger hur mycket hon flyttats. Överlapp: hennes mask i resultatet (allt som inte är jämnt grått) mot originalets
mask, inom originalets synliga del.
"""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent / 'fal'))
import falapi

HIT = Path(__file__).resolve().parent; LA = HIT / 'luma-agaren'; UT = HIT / 'c_isolerad'
ORIG = LA / '2_ruta_000_start.png'; TOM = HIT / 'b_tom/B2_promptad_reg.png'


def omask():
    m = np.load(HIT.parent / 'ingest/ut/kand-kennysgelato-tagningar/S1/masker.npy')[7].astype(np.uint8) * 255
    return cv2.resize(m, (1080, 1920), interpolation=cv2.INTER_NEAREST)


def prompt(namn):
    if namn in ('C1', 'C3'):
        t = (LA / 'PROMPT-AB.txt').read_text(encoding='utf-8').split('STEP B — ISOLATE HER')[1].split('Save as:')[0]
        t = t.split('\n', 1)[1].strip()
        return '\n'.join(r for r in t.split('\n') if not r.startswith('If image 3 is attached')).strip()
    t = (LA / 'PROMPT.txt').read_text(encoding='utf-8')
    return t.split('STEP 1, VERSION 3 — CLEAN-UP OF A READY COMPOSITE (use this one, on steg1/guidebild_last_position.png)')[1].split('STEP 1, VERSION 2')[0].strip()


def generera(namn):
    d = UT / namn; png = UT / f'{namn}.png'
    if png.exists(): return png
    p = prompt(namn); d.mkdir(parents=True, exist_ok=True); (d / 'prompt.txt').write_text(p, encoding='utf-8')
    if namn == 'C1':
        s = falapi.kor('luma/agent/uni-1/v1/edit', dict(image_url=falapi.ladda_upp(ORIG), reference_image_urls=[falapi.ladda_upp(TOM)], prompt=p), d / 'anrop', 'C isolerad uni-1 STEP B', 0.003, '0.003 USD/bild')
    elif namn == 'C2':
        s = falapi.kor('luma/agent/uni-1/v1/edit', dict(image_url=falapi.ladda_upp(LA / 'steg1/guidebild_last_position.png'), prompt=p), d / 'anrop', 'C städa komposit uni-1', 0.003, '0.003 USD/bild')
    elif namn == 'C3':
        s = falapi.kor('fal-ai/nano-banana-pro/edit', dict(image_urls=[falapi.ladda_upp(ORIG), falapi.ladda_upp(TOM)], prompt=p, aspect_ratio='9:16', resolution='2K', num_images=1),
                       d / 'anrop', 'C isolerad nano-banana-pro STEP B', 0.15, '0.15 USD/bild')
    falapi.hamta(s['images'][0]['url'] if 'images' in s else s['image']['url'], png)
    return png


def matt(png):
    a = cv2.imread(str(ORIG)); m = omask(); r = cv2.imread(str(png))
    res = dict(storlek=list(r.shape[:2][::-1]))
    # registrering på hennes synliga överkropp
    o = cv2.ORB_create(4000)
    ka, da = o.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), m); kb, db = o.detectAndCompute(cv2.cvtColor(r, cv2.COLOR_BGR2GRAY), None)
    H = None
    if da is not None and db is not None:
        mt = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db), key=lambda x: x.distance)[:400]
        if len(mt) >= 8:
            A = np.float32([ka[x.queryIdx].pt for x in mt]); B = np.float32([kb[x.trainIdx].pt for x in mt])
            H, inl = cv2.estimateAffinePartial2D(B, A, method=cv2.RANSAC, ransacReprojThreshold=4.0)
            res['inliers'] = int(inl.sum()) if inl is not None else 0
    if H is None or res.get('inliers', 0) < 12:
        # ingen registrering: anta att hela bilden är samma ram (skala till originalets storlek)
        w = cv2.resize(r, (1080, 1920)); res['registrering'] = 'ingen (för få träffar); bilden skalad till ramen'
    else:
        s = float(np.hypot(H[0, 0], H[1, 0])); res.update(registrering='likformig på överkroppen', skala_mot_original=round(1 / s, 3), rotation_grader=round(float(np.degrees(np.arctan2(H[1, 0], H[0, 0]))), 2))
        w = cv2.warpAffine(r, H, (1080, 1920), borderValue=(200, 200, 200))
        # hur långt ifrån identitet ligger huvud och axlar (mätpunkter ur originalets mask)
        ys, xs = np.nonzero(m); topp = (float(xs[ys == ys.min()].mean()), float(ys.min()))
        axl_y = ys.min() + 0.18 * (ys.max() - ys.min()); rad = xs[np.abs(ys - axl_y) < 3]
        pts = np.float32([topp, (rad.min(), axl_y), (rad.max(), axl_y)])
        Hi = cv2.invertAffineTransform(H); i_res = (np.c_[pts, np.ones(3)] @ Hi.T)
        # i_res = var punkterna ligger i resultatbilden; skala resultatet till originalets ram för att jämföra i samma pixlar
        sx, sy = 1080 / r.shape[1], 1920 / r.shape[0]
        res['forskjutning_px'] = dict(zip(['huvud', 'v_axel', 'h_axel'], [round(float(np.hypot(p[0] * sx - q[0], p[1] * sy - q[1])), 1) for p, q in zip(i_res, pts)]))
    g = cv2.cvtColor(cv2.resize(r, (1080, 1920)), cv2.COLOR_BGR2HSV)
    bakgrund = (g[..., 1] < 25) & (g[..., 2] > 150)   # jämn ljusgrå
    pm = (~bakgrund).astype(np.uint8); pm = cv2.morphologyEx(pm, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    vis = m > 0
    res['overlapp_synlig_del'] = round(float((pm[vis] > 0).mean()), 3)
    res['iou_synlig_del'] = round(float(((pm > 0) & vis).sum() / max(1, ((pm > 0) & (np.arange(1920)[:, None] <= np.nonzero(vis)[0].max())).sum() + vis.sum() - ((pm > 0) & vis).sum())), 3)
    cv2.imwrite(str(UT / f'{Path(png).stem}_mask.png'), pm * 255)
    return res


def main():
    UT.mkdir(exist_ok=True); namn = sys.argv[1:] or ['C1', 'C2', 'C3']; alla = {}
    if (UT / 'matt.json').exists(): alla = json.loads((UT / 'matt.json').read_text(encoding='utf-8'))
    for n in namn:
        try: alla[n] = matt(generera(n))
        except Exception as e: alla[n] = dict(fel=str(e)[:500])
        print(n, json.dumps(alla[n], ensure_ascii=False), flush=True)
    (UT / 'matt.json').write_text(json.dumps(alla, ensure_ascii=False, indent=1), encoding='utf-8')
    ims = [cv2.resize(cv2.imread(str(p)), (360, 640)) for p in [ORIG] + [UT / f'{n}.png' for n in alla if (UT / f'{n}.png').exists()]]
    cv2.imwrite(str(UT / 'jamfor_C.jpg'), np.hstack(ims)); print('fal', falapi.summa().get('summa_fal_usd'))


if __name__ == '__main__': main()
