"""0018 punkt 1: lås positionen i efterhand. En isolerad person passas mot originalets synliga överkropp med likformig skala och förskjutning
(ORB-träffar inom ingestens personmask, RANSAC, estimateAffinePartial2D), och läggs på grå duk i originalets format.
Princip 3 blir ett efterbehandlingssteg som alltid körs, oavsett vad bildmodellen gjorde.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/passa.py <isolerad.png> <ut.png> [--ruta 0] [--original <png>]
Mått: skala och förskjutning (resultatets ram -> originalets), överlapp och IoU på den del som syns i originalet, rest i huvud och axlar.
Personens mask i den isolerade bilden: allt som inte är jämnt ljusgrått (HSV), öppnat.
"""
import argparse, json
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent
GRA = (200, 200, 200)


def omask(ruta):
    m = np.load(HIT.parent / 'ingest/ut/kand-kennysgelato-tagningar/S1/masker.npy')[7 + ruta].astype(np.uint8) * 255
    return cv2.resize(m, (1080, 1920), interpolation=cv2.INTER_NEAREST)


def personmask(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); bak = (g[..., 1] < 28) & (g[..., 2] > 140)
    pm = (~bak).astype(np.uint8); pm = cv2.morphologyEx(pm, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pm)
    if n > 1: pm = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    return pm


def passa(iso, orig, m):
    o = cv2.ORB_create(6000)
    ka, da = o.detectAndCompute(cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY), cv2.dilate(m, np.ones((15, 15), np.uint8)))
    pm = personmask(iso)
    kb, db = o.detectAndCompute(cv2.cvtColor(iso, cv2.COLOR_BGR2GRAY), cv2.dilate(pm * 255, np.ones((15, 15), np.uint8)))
    mt = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db), key=lambda x: x.distance)[:500]
    A = np.float32([ka[x.queryIdx].pt for x in mt]); B = np.float32([kb[x.trainIdx].pt for x in mt])
    H, inl = cv2.estimateAffinePartial2D(B, A, method=cv2.RANSAC, ransacReprojThreshold=5.0, maxIters=5000)
    metod = 'ORB på överkroppen'
    if H is None or inl.sum() < 15:
        # reserv: passa maskernas överkant och bredd vid axlarna (silhuett), ingen textur
        def kant(mm):
            ys, xs = np.nonzero(mm); top = ys.min(); y = top + int(0.18 * (ys.max() - top)); r = xs[np.abs(ys - y) < 3]
            return np.float32([[xs[ys == top].mean(), top], [r.min(), y], [r.max(), y]])
        H, inl = cv2.estimateAffinePartial2D(kant(pm), kant(m > 0)); inl = np.ones(3); metod = 'silhuett (huvud, axlar)'
    s = float(np.hypot(H[0, 0], H[1, 0]))
    ut = cv2.warpAffine(iso, H, (orig.shape[1], orig.shape[0]), borderMode=cv2.BORDER_CONSTANT, borderValue=GRA)
    pmu = cv2.warpAffine(pm, H, (orig.shape[1], orig.shape[0]), flags=cv2.INTER_NEAREST)
    vis = m > 0; ny = (pmu > 0)
    # rest i huvud och axlar: originalets mätpunkter mot samma punkter i den passade masken
    hv = int(0.18 * (np.nonzero(vis)[0].max() - np.nonzero(vis)[0].min()))   # axelraden: samma pixelavstånd under hjässan i båda (originalets synliga höjd)
    def punkter(mm):
        ys, xs = np.nonzero(mm); top = ys.min(); y = top + hv; r = xs[np.abs(ys - y) < 3]
        return np.float32([[xs[ys == top].mean(), top], [r.min(), y], [r.max(), y]])
    rest = np.linalg.norm(punkter(ny) - punkter(vis), axis=1)
    botten = np.nonzero(vis)[0].max()
    inom = ny[:botten + 1]; v = vis[:botten + 1]
    return ut, pmu, dict(metod=metod, traffar=int(inl.sum()), skala=round(s, 4), rotation_grader=round(float(np.degrees(np.arctan2(H[1, 0], H[0, 0]))), 2),
                         forskjutning_px=[round(float(H[0, 2]), 1), round(float(H[1, 2]), 1)],
                         overlapp_synlig=round(float(ny[vis].mean()), 3), iou_ovan_disken=round(float((inom & v).sum() / max(1, (inom | v).sum())), 3),
                         rest_px=dict(huvud=round(float(rest[0]), 1), v_axel=round(float(rest[1]), 1), h_axel=round(float(rest[2]), 1)),
                         kropp_under_disken_px=int(ny[botten + 1:].sum()))


def main():
    a = argparse.ArgumentParser(); a.add_argument('iso'); a.add_argument('ut'); a.add_argument('--ruta', type=int, default=0); a.add_argument('--original'); x = a.parse_args()
    orig = cv2.imread(x.original or str(HIT / 'luma-agaren/2_ruta_000_start.png')); m = omask(x.ruta)
    iso = cv2.imdecode(np.fromfile(x.iso, np.uint8), cv2.IMREAD_COLOR)
    ut, pmu, r = passa(iso, orig, m)
    cv2.imwrite(x.ut, ut); cv2.imwrite(x.ut.replace('.png', '_mask.png'), pmu * 255)
    kontroll = orig.copy(); kontroll[pmu > 0] = (0.5 * kontroll[pmu > 0] + 0.5 * np.array([0, 0, 255])).astype(np.uint8)
    cnt, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(kontroll, cnt, -1, (0, 255, 0), 3)
    cv2.imwrite(x.ut.replace('.png', '_kontroll.jpg'), np.hstack([cv2.resize(kontroll, (540, 960)), cv2.resize(ut, (540, 960))]))
    Path(x.ut.replace('.png', '.json')).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__': main()
