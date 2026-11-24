"""Bygger en guidebild där personen ligger kvar på sin plats i originalrutan.

Överkroppen är originalets pixlar (ingestens personmask). Underkroppen lånas ur
Lumas genererade helkroppsbild, skalad och lagd under originalets midja.
Allt annat blir jämnt grått.

Kör: scen/.venv/Scripts/python.exe bygg_guide.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

HAR = Path(__file__).resolve().parent
INGEST = HAR.parents[1] / "ingest" / "ut" / "kand-kennysgelato-tagningar" / "S1"
RUTA = 7  # 0,25 s bortklippt i början av källan, 29,97 fps
GRA = (186, 186, 186)

orig = cv2.imread(str(HAR / "2_ruta_000_start.png"))
H, W = orig.shape[:2]
mask_lag = np.load(INGEST / "masker.npy")[RUTA].astype(np.uint8)
mask = cv2.resize(mask_lag, (W, H), interpolation=cv2.INTER_LINEAR)
mask = cv2.erode(mask, np.ones((5, 5), np.uint8))
mjuk = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 3)[..., None]

ys, xs = np.nonzero(mask)
y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
# Bålens bredd strax ovanför där disken skär av henne. Armarna sticker ut åt
# sidan, så bredden tas ur den längsta sammanhängande raden kring mittlinjen.
rad = int(y1 - 0.06 * (y1 - y0))
kol = np.nonzero(mask[rad])[0]
bal_x0, bal_x1 = kol.min(), kol.max()
if len(sys.argv) > 2:
    bal_x0, bal_x1 = int(sys.argv[1]), int(sys.argv[2])
bal_b = bal_x1 - bal_x0
bal_mitt = (bal_x0 + bal_x1) / 2

gen_namn = sorted((HAR / "steg1").glob("*Grey_Studio*.jpg"))[0]
gen = cv2.imread(str(gen_namn))
gh, gw = gen.shape[:2]
gra = cv2.cvtColor(gen, cv2.COLOR_BGR2GRAY)
mork = (gra < 70).astype(np.uint8)  # svarta byxor och skor; vattenstämpeln är ljus
mork = cv2.morphologyEx(mork, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, stat, _ = cv2.connectedComponentsWithStats(mork)
storst = 1 + np.argmax(stat[1:, cv2.CC_STAT_AREA])
kropp = (lab == storst).astype(np.uint8)
gy = np.nonzero(kropp.any(axis=1))[0]
g_top, g_bot = gy.min(), gy.max()
# Midjan i den genererade bilden: där tröjan slutar, ungefär 38 % ned i det mörka fältet.
g_midja = int(g_top + 0.36 * (g_bot - g_top))
gk = np.nonzero(kropp[g_midja])[0]
g_b = gk.max() - gk.min()
g_mitt = (gk.max() + gk.min()) / 2

s = bal_b / g_b
ny = cv2.resize(gen, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
ny_m = cv2.resize(kropp, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
ny_m[: int(g_midja * s)] = 0  # bara underkroppen

duk = np.full((H, W, 3), GRA, np.uint8)
dx = int(round(bal_mitt - g_mitt * s))
dy = int(round(rad - g_midja * s))
h2, w2 = ny.shape[:2]
ya, yb = max(0, dy), min(H, dy + h2)
xa, xb = max(0, dx), min(W, dx + w2)
bit = ny[ya - dy : yb - dy, xa - dx : xb - dx]
bm = cv2.GaussianBlur(ny_m[ya - dy : yb - dy, xa - dx : xb - dx].astype(np.float32), (0, 0), 1.5)[..., None]
duk[ya:yb, xa:xb] = (bm * bit + (1 - bm) * duk[ya:yb, xa:xb]).astype(np.uint8)

ut = (mjuk * orig + (1 - mjuk) * duk).astype(np.uint8)
(HAR / "steg1").mkdir(exist_ok=True)
cv2.imwrite(str(HAR / "steg1" / "guidebild_last_position.png"), ut)
sida = np.hstack([orig, ut])
cv2.imwrite(str(HAR / "steg1" / "jamfor_original_guide.jpg"), cv2.resize(sida, None, fx=0.4, fy=0.4))
print("bål", bal_x0, bal_x1, "rad", rad, "skala", round(s, 3), "fötter y", dy + int(g_bot * s), "av", H)
