"""0024 punkt 1: nyckelbilder med skeden i handen, i den kamerafria ramen. Körs när ägarens GPT-bilder finns (luma-agaren/gpt/NASTA-BILDER.md).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/e3_sked.py
För ruta 0 och 55: luma-agaren/gpt/0024/sked_<ruta>/3_isolerad_med_sked.png passas mot originalrutan (passa.passa, överkroppen i
ingestens mask), följs av rutans avbildning A (kamerafri/avbildning.json), och läggs på jämn grå duk som kamerafri_k2/nyckel/kf_<ruta>_sked.png.
d2_video.py k2sn tar dem i stället för kf_<ruta>.png när de finns.
"""
import json
from pathlib import Path
import cv2, numpy as np
from passa import passa, omask, personmask

HIT = Path(__file__).resolve().parent; GRA = 200
ORIG = {0: HIT / 'luma-agaren/2_ruta_000_start.png', 55: HIT / 'nyckel/ruta_055.png'}


def main():
    avb = json.loads((HIT / 'kamerafri/avbildning.json').read_text(encoding='utf-8'))['rutor']; rap = {}
    for r, o in ORIG.items():
        f = HIT / f'luma-agaren/gpt/0024/sked_{r:03d}/3_isolerad_med_sked.png'
        if not f.exists(): print('saknas', f); continue
        iso = cv2.imdecode(np.fromfile(str(f), np.uint8), cv2.IMREAD_COLOR); orig = cv2.imread(str(o))
        pm = cv2.GaussianBlur(personmask(iso).astype(np.float32), (7, 7), 0)[..., None]; iso = (iso * pm + GRA * (1 - pm)).astype(np.uint8)
        _, _, p = passa(iso, orig, omask(r))
        s, th = p['skala'], np.radians(p['rotation_grader']); tx, ty = p['forskjutning_px']
        P = np.array([[s * np.cos(th), -s * np.sin(th), tx], [s * np.sin(th), s * np.cos(th), ty], [0, 0, 1]])
        T = (np.vstack([np.array(avb[r]['A'], float), [0, 0, 1]]) @ P)[:2]
        kf = cv2.warpAffine(iso, T, (1080, 1920), borderMode=cv2.BORDER_CONSTANT, borderValue=(GRA, GRA, GRA))
        cv2.imwrite(str(HIT / f'kamerafri_k2/nyckel/kf_{r:03d}_sked.png'), kf); rap[r] = p; print(r, json.dumps(p, ensure_ascii=False))
    (HIT / 'kamerafri_k2/nyckel/sked.json').write_text(json.dumps(rap, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__': main()
