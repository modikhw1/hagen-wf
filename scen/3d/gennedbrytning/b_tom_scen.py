"""0017 del B: tom scen som bild ur gelato S1 ruta 0 (ingestens ruta 7).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/b_tom_scen.py
B1 maskad: fal-ai/object-removal/mask med ingestens personmask, vidgad 24 px i 1080x1920 (före fal:s egen expansion 15 px).
B2 promptad: luma/agent/uni-1/v1/edit med STEP A ur luma-agaren/PROMPT-AB.txt (oförändrad text).
Mått: andel pixlar utanför (vidgad) mask som ändrats > 12 gråvärden, och medelfel utanför.
"""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent / 'fal'))
import falapi

HIT = Path(__file__).resolve().parent; LA = HIT / 'luma-agaren'; UT = HIT / 'b_tom'
ORIG = LA / '2_ruta_000_start.png'; RUTA0 = 7   # klippets ruta 0 = ingestens ruta 7 (LAS-MIG.md, uppdraget)


def mask(ruta, vidga=24):
    m = np.load(HIT.parent / 'ingest/ut/kand-kennysgelato-tagningar/S1/masker.npy')[ruta].astype(np.uint8) * 255
    m = cv2.resize(m, (1080, 1920), interpolation=cv2.INTER_NEAREST)
    return cv2.dilate(m, np.ones((2 * vidga + 1, 2 * vidga + 1), np.uint8))


def matt(res, m):
    a = cv2.imread(str(ORIG)).astype(np.int16); b = cv2.imread(str(res))
    if b.shape[:2] != a.shape[:2]: b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    d = np.abs(a - b.astype(np.int16)).max(2); ute = m == 0
    return dict(storlek_ut=list(cv2.imread(str(res)).shape[:2][::-1]), andel_andrad_utanfor=round(float((d[ute] > 12).mean()), 4),
                medelfel_utanfor=round(float(d[ute].mean()), 2), andel_andrad_innanfor=round(float((d[~ute] > 12).mean()), 4))


def main():
    UT.mkdir(exist_ok=True); m = mask(RUTA0); cv2.imwrite(str(UT / 'mask_ruta0_vidgad.png'), m)
    res = {}
    if not (UT / 'B1_maskad.png').exists():
        s = falapi.kor('fal-ai/object-removal/mask', dict(image_url=falapi.data_uri(ORIG), mask_url=falapi.data_uri(UT / 'mask_ruta0_vidgad.png'), model='best_quality', mask_expansion=15),
                       UT / 'B1', 'B tom scen maskad', 0.006, 'pris 0.006 USD/bild (api.fal.ai/v1/models/pricing)')
        falapi.hamta(s['images'][0]['url'] if 'images' in s else s['image']['url'], UT / 'B1_maskad.png')
    res['B1_maskad'] = matt(UT / 'B1_maskad.png', m)
    if not (UT / 'B2_promptad.png').exists():
        txt = (LA / 'PROMPT-AB.txt').read_text(encoding='utf-8')
        p = txt.split('STEP A — EMPTY PLATE (input: 2_ruta_000_start.png)')[1].split('Save as:')[0].strip()
        (UT / 'B2_prompt.txt').write_text(p, encoding='utf-8')
        s = falapi.kor('luma/agent/uni-1/v1/edit', dict(image_url=falapi.ladda_upp(ORIG), prompt=p), UT / 'B2', 'B tom scen promptad', 0.003, 'pris 0.003 USD/bild')
        falapi.hamta(s['images'][0]['url'] if 'images' in s else s['image']['url'], UT / 'B2_promptad.png')
    res['B2_promptad'] = matt(UT / 'B2_promptad.png', m)
    (UT / 'matt.json').write_text(json.dumps(res, indent=1), encoding='utf-8'); print(json.dumps(res, indent=1)); print(falapi.summa().get('summa_fal_usd'))


if __name__ == '__main__': main()
