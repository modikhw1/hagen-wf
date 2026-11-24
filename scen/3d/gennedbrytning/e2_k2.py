"""0023 punkt 1–2: källa k2 och nyckelbilder i den kamerafria ramen.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/e2_k2.py
k2: samma avbildning per ruta som k (kamerafri/avbildning.json), men hela originalrutan följer med: disk, glas, rum och hennes arm
    bakom glaset ligger kvar. Bara kundens hand (maskdelar ur ingestens personmask som rör bildkanten och inte är den största) målas grå.
    Det som hamnar utanför originalets bild blir grått.
Nyckelbilder: Codex-isoleringarna i nyckel2/B_<ruta>.png förs in i den kamerafria ramen genom passningen mot originalrutan
    (nyckel2/B_<ruta>_passad.json: skala, rotation, förskjutning) följd av rutans avbildning A. Hela kroppen följer med, eftersom
    benen inte längre klipps av originalets bildkant. Grå duk (200).
Ut: kamerafri_k2/k2.mp4, oversikt.jpg, nyckel/kf_<ruta>.png, nyckel/oversikt.jpg, nyckel/nyckel.json.
"""
import json
from pathlib import Path
import cv2, numpy as np
from passa import personmask

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; S1 = ING / 'ut/kand-kennysgelato-tagningar/S1'
UT = HIT / 'kamerafri_k2'; GRA = 200; W, H, R0 = 1080, 1920, 7
RUTOR = [0, 30, 55, 80, 94, 112, 136, 146]


def kanthand(lo):
    """kundens hand: maskdelar som rör bildkanten och inte är den största."""
    nk, lab, st, _ = cv2.connectedComponentsWithStats(lo); ut = np.zeros_like(lo)
    if nk > 2:
        stor = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); hm, wm = lo.shape
        for c in range(1, nk):
            x0, y0, ww, hh = st[c, :4]
            if c != stor and (x0 == 0 or y0 == 0 or x0 + ww >= wm or y0 + hh >= hm): ut[lab == c] = 1
    return ut


def main():
    UT.mkdir(exist_ok=True); (UT / 'nyckel').mkdir(exist_ok=True)
    avb = json.loads((HIT / 'kamerafri/avbildning.json').read_text(encoding='utf-8'))['rutor']
    cap = cv2.VideoCapture(str(HIT / 'luma-agaren/1_kalla_gelato_S1.mp4')); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(f)
    M = np.load(S1 / 'masker.npy'); vw = cv2.VideoWriter(str(UT / 'k2.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 29.97, (W, H))
    K = []; handrutor = []
    for i, f in enumerate(F):
        h = kanthand(M[min(i + R0, len(M) - 1)].astype(np.uint8))
        b = f.copy()
        if h.any():
            handrutor.append(i)
            hm = cv2.resize(h, (W, H), interpolation=cv2.INTER_NEAREST); hm = cv2.dilate(hm, np.ones((41, 41), np.uint8))
            b[hm > 0] = GRA
        A = np.array(avb[i]['A'], float)
        k = cv2.warpAffine(b, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(GRA, GRA, GRA))
        vw.write(k); K.append(k)
    vw.release()
    cv2.imwrite(str(UT / 'oversikt.jpg'), np.hstack([np.vstack([cv2.resize(F[r], (180, 320)), cv2.resize(K[r], (180, 320))]) for r in RUTOR]))
    # nyckelbilder
    info = []; vis = []
    for r in RUTOR:
        p = json.loads((HIT / f'nyckel2/B_{r:03d}_passad.json').read_text(encoding='utf-8'))
        s, th = p['skala'], np.radians(p['rotation_grader']); tx, ty = p['forskjutning_px']
        P = np.array([[s * np.cos(th), -s * np.sin(th), tx], [s * np.sin(th), s * np.cos(th), ty], [0, 0, 1]])
        A = np.vstack([np.array(avb[r]['A'], float), [0, 0, 1]]); T = (A @ P)[:2]
        iso = cv2.imdecode(np.fromfile(str(HIT / f'nyckel2/B_{r:03d}.png'), np.uint8), cv2.IMREAD_COLOR)
        # Codex-dukens grå är inte 200: ersätt allt utom personen med jämn grå, så att nyckelbilden inte får en synlig rektangel
        pm = cv2.GaussianBlur(personmask(iso).astype(np.float32), (7, 7), 0)[..., None]
        iso = (iso * pm + GRA * (1 - pm)).astype(np.uint8)
        kf =cv2.warpAffine(iso, T, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(GRA, GRA, GRA))
        cv2.imwrite(str(UT / f'nyckel/kf_{r:03d}.png'), kf)
        info.append(dict(ruta=r, passning=p, T=T.round(5).tolist(), rest_huvud_px_i_originalet=p['rest_px']['huvud']))
        mix = cv2.addWeighted(K[r], 0.5, kf, 0.5, 0)
        vis.append(np.vstack([cv2.resize(K[r], (180, 320)), cv2.resize(kf, (180, 320)), cv2.resize(mix, (180, 320))]))
    cv2.imwrite(str(UT / 'nyckel/oversikt.jpg'), np.hstack(vis))
    (UT / 'nyckel/nyckel.json').write_text(json.dumps(dict(metod=__doc__.split('\n')[6].strip(), rutor=info), ensure_ascii=False, indent=1), encoding='utf-8')
    (UT / 'k2.json').write_text(json.dumps(dict(kundhand_gra_rutor=handrutor), ensure_ascii=False), encoding='utf-8')
    print('k2 klar, kundhand grå i', len(handrutor), 'rutor')


if __name__ == '__main__': main()
