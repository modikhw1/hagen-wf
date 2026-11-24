"""0024 punkt 2: mät disklagret och rummet utan disk mot originalet. Körs när ägarens GPT-bilder finns (luma-agaren/gpt/NASTA-BILDER.md).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/k_disk.py
Bara disken (0024/disk_bara/3_bara_disken.png): diskens yta = allt som inte är jämnt grått. Kanter (Canny) i den ytan mot originalets
  kanter i samma yta: avstånd från varje kantpixel i resultatet till närmaste i originalet, i promille av bildhöjden (median, p90).
  Ligger disken kvar på sin plats blir avstånden små. Diskens ovankant (översta raden i ytan per kolumn) redovisas också.
Rummet utan disk (0024/rum_utan_disk/2_rum_utan_disk.png): utanför diskens yta ska inget ändras (median absolut skillnad mot tom scen,
  och kantavstånd). Inom diskens yta är allt nytt och märks antagen: golvet, bakre bänkens nedre del, avståndet disk–bänk.
Ut: disk_lager/matt.json och disk_lager/jamfor.jpg (original | tom scen | bara disken | rum utan disk).
"""
import json
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; G = HIT / 'luma-agaren/gpt/0024'; UT = HIT / 'disk_lager'


def las(p):
    b = cv2.imdecode(np.fromfile(str(p), np.uint8), cv2.IMREAD_COLOR)
    return cv2.resize(b, (1080, 1920), interpolation=cv2.INTER_AREA) if b is not None and b.shape[:2] != (1920, 1080) else b


def kantavstand(a, b, yta):
    ka = cv2.Canny(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), 60, 160) > 0; kb = cv2.Canny(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), 60, 160) > 0
    dt = cv2.distanceTransform((~(kb & yta)).astype(np.uint8), cv2.DIST_L2, 5); d = dt[ka & yta] / 1920 * 1000
    return dict(median=round(float(np.median(d)), 1), p90=round(float(np.percentile(d, 90)), 1), kantpixlar=int(d.size)) if d.size else None


def main():
    UT.mkdir(exist_ok=True); o = las(G / 'disk_bara/1_original_ruta000.png'); t = las(G / 'disk_bara/2_tom_scen_ruta000.png')
    bd = G / 'disk_bara/3_bara_disken.png'; ru = G / 'rum_utan_disk/2_rum_utan_disk.png'; r = {}
    if not bd.exists() and not ru.exists(): print('inga GPT-bilder än'); return
    yta = None
    if bd.exists():
        d = las(bd); hsv = cv2.cvtColor(d, cv2.COLOR_BGR2HSV); yta = ~((hsv[..., 1] < 25) & (hsv[..., 2] > 150))
        yta = cv2.morphologyEx(yta.astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 9), np.uint8)) > 0
        cols = [int(np.nonzero(yta[:, x])[0].min()) for x in range(0, 1080, 54) if yta[:, x].any()]
        r['bara_disken'] = dict(kanter_mot_originalet_promille=kantavstand(d, o, yta), yta_andel=round(float(yta.mean()), 3),
                                ovankant_y_px_var_54e_kolumn=cols, antagen=['diskens framsida under bildkanten', 'diskens höjd från golvet'])
    if ru.exists():
        u = las(ru); ute = ~yta if yta is not None else np.ones((1920, 1080), bool)
        r['rum_utan_disk'] = dict(utanfor_disken_median_abs_skillnad=round(float(np.median(np.abs(u.astype(int) - t.astype(int)).mean(2)[ute])), 1),
                                  kanter_utanfor_disken_promille=kantavstand(u, t, ute),
                                  antagen=['golvytan där disken stod', 'bakre bänkens nedre del', 'avståndet från disken till bakre bänken'])
    (UT / 'matt.json').write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
    tom = np.full((1920, 1080, 3), 200, np.uint8)
    cv2.imwrite(str(UT / 'jamfor.jpg'), np.hstack([cv2.resize(x, (360, 640)) for x in [o, t, las(bd) if bd.exists() else tom, las(ru) if ru.exists() else tom]]))
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == '__main__': main()
