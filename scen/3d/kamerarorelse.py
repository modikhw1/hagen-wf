"""Kamerarörelse inom tagningarna (handhållen mobil): bildruta för bildruta, som rotation av källkameran.

Metod: hörnpunkter i BAKGRUNDEN (personer maskade med posens bildpunkter, utvidgade) följs med Lucas–Kanade mellan
bildrutor; RANSAC-likformighet (dx, dy, rotation, skala) per steg; ackumuleras inom tagningen och centreras kring
tagningens median (PnP-kameran i layouten är löst över hela tagningen, alltså ungefär medianläget).
Översättning till kamera: liten rotation  pan = atan(dx/f), tilt = atan(dy/f), roll = rotationen; skala -> fov-ändring
(zoom/dolly kan inte skiljas från en bild utan djup; skalan bokförs som fov-faktor).
Ut: data/kamera-3.json  {fps, f_px, shots:{S1:{frames:[n...], pan_deg, tilt_deg, roll_deg, fov_scale, inliers}}, summary}
Kör: scen/.venv/Scripts/python.exe -B scen/3d/kamerarorelse.py
"""
import json, math
from pathlib import Path
import numpy as np, cv2
ROOT = Path(__file__).resolve().parent
W, H = 576, 1024
spec = json.loads((ROOT / 'scen3d.bas.json').read_text(encoding='utf-8'))
M = json.loads((ROOT / 'data/motion-2.json').read_text(encoding='utf-8'))['frames']
f_px = (H / 2) / math.tan(math.radians(68) / 2)
cap = cv2.VideoCapture(str(ROOT.parent / 'klipp/d-dialog-notan.mp4'))
bilder = []
while True:
    ok, im = cap.read()
    if not ok: break
    bilder.append(cv2.cvtColor(cv2.resize(im, (W, H)), cv2.COLOR_BGR2GRAY))
def mask_för(n):
    m = np.full((H, W), 255, np.uint8)
    if n < len(M):
        I = np.array(M[n]['image']); pts = (I[:, :2] * [W, H]).astype(int)
        x0, y0 = pts.min(0); x1, y1 = pts.max(0)
        cv2.rectangle(m, (max(0, x0 - 70), max(0, y0 - 110)), (min(W, x1 + 70), H), 0, -1)   # personen + under (bord/händer)
        for h in M[n].get('hands', []):
            hp = (np.array(h['image'])[:, :2] * [W, H]).astype(int); cv2.rectangle(m, tuple(hp.min(0) - 30), tuple(hp.max(0) + 30), 0, -1)
    m[int(H * .78):, :] = 0      # undertexter/förgrund nertill
    return m
ut = {'fps': 30, 'f_px': round(f_px, 1), 'method': 'LK-flöde på bakgrund (personer maskade), RANSAC-likformighet per steg, ackumulerat och centrerat på tagningens median', 'shots': {}}
for sh in spec['shots']:
    a, b = round(sh['source']['inSec'] * 30), round(sh['source']['outSec'] * 30)
    b = min(b, len(bilder)); dx = [0.]; dy = [0.]; rot = [0.]; sk = [1.]; inl = [1.]
    for n in range(a + 1, b):
        g0, g1 = bilder[n - 1], bilder[n]
        p0 = cv2.goodFeaturesToTrack(g0, 400, .01, 8, mask=mask_för(n - 1))
        if p0 is None or len(p0) < 12: dx.append(dx[-1]); dy.append(dy[-1]); rot.append(rot[-1]); sk.append(sk[-1]); inl.append(0); continue
        p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, winSize=(21, 21), maxLevel=3)
        ok = st.ravel() == 1; A, inliers = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.5)
        if A is None: dx.append(dx[-1]); dy.append(dy[-1]); rot.append(rot[-1]); sk.append(sk[-1]); inl.append(0); continue
        s = math.hypot(A[0, 0], A[1, 0]); r = math.atan2(A[1, 0], A[0, 0])
        # bildens förflyttning av bakgrunden kring bildens mitt
        c = np.array([W / 2, H / 2]); c2 = A[:, :2] @ c + A[:, 2]; d = c2 - c
        dx.append(dx[-1] + d[0]); dy.append(dy[-1] + d[1]); rot.append(rot[-1] + r); sk.append(sk[-1] * s); inl.append(float(inliers.mean()))
    dx, dy, rot, sk = map(np.array, (dx, dy, rot, sk))
    dx -= np.median(dx); dy -= np.median(dy); rot -= np.median(rot); sk /= np.median(sk)
    # bakgrunden flyttas åt höger i bilden när kameran panorerar åt vänster: pan = -atan(dx/f); bakgrund nedåt = kamera tiltar upp
    pan = -np.degrees(np.arctan(dx / f_px)); tilt = np.degrees(np.arctan(dy / f_px)); roll = -np.degrees(rot)
    ut['shots'][sh['id']] = dict(frames=[a, b], pan_deg=pan.round(3).tolist(), tilt_deg=tilt.round(3).tolist(), roll_deg=roll.round(3).tolist(),
                                fov_scale=(1 / sk).round(4).tolist(), inliers=np.round(inl, 2).tolist(),
                                range=dict(pan=round(float(np.ptp(pan)), 2), tilt=round(float(np.ptp(tilt)), 2), roll=round(float(np.ptp(roll)), 2), fov=round(float(np.ptp(1 / sk)), 4)),
                                px_range=dict(dx=round(float(np.ptp(dx)), 1), dy=round(float(np.ptp(dy)), 1)))
    r = ut['shots'][sh['id']]['range']; pr = ut['shots'][sh['id']]['px_range']
    print(f"{sh['id']}: pan {r['pan']:.2f}° tilt {r['tilt']:.2f}° roll {r['roll']:.2f}° fov×{1 + r['fov']:.3f}  (bakgrund {pr['dx']:.0f}/{pr['dy']:.0f} px)  inliers {np.mean(inl):.2f}")
(ROOT / 'data/kamera-3.json').write_text(json.dumps(ut), encoding='utf-8')
print('-> data/kamera-3.json')
