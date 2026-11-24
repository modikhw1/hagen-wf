"""Plockar 2 bildrutor per tagning ur jamforelse.mp4 (1/3 och 2/3 in) till <utmapp>/granska/S<n>_a.jpg, S<n>_b.jpg, och en kontaktbild per klipp.
Kör: scen/.venv/Scripts/python.exe scen/3d/ingest/flera/granska.py <utmapp>"""
import sys, cv2, numpy as np
from pathlib import Path
ut = Path(sys.argv[1]); g = ut / 'granska'; g.mkdir(exist_ok=True)
for d in sorted(ut.glob('S[0-9]*'), key=lambda p: int(p.name[1:])):
    v = d / 'jamforelse.mp4'
    if not v.exists(): continue
    cap = cv2.VideoCapture(str(v)); n = int(cap.get(7)); rows = []
    for tag, f in (('a', n // 3), ('b', 2 * n // 3)):
        cap.set(1, f); ok, im = cap.read()
        if not ok: continue
        cv2.imwrite(str(g / f'{d.name}_{tag}.jpg'), im); rows.append(cv2.resize(im, (im.shape[1] * 2 // 3, im.shape[0] * 2 // 3)))
    if rows:
        s = np.vstack(rows); cv2.putText(s, d.name, (5, 25), 0, .9, (0, 255, 0), 2); cv2.imwrite(str(g / f'{d.name}_kontakt.jpg'), s)

# översiktsbilder: tre kontaktbilder bredvid varandra, halv storlek
ks = sorted(g.glob('S*_kontakt.jpg'), key=lambda p: int(p.name.split('_')[0][1:]))
for i in range(0, len(ks), 3):
    ims = [cv2.imread(str(k)) for k in ks[i:i + 3]]; ims = [cv2.resize(m, (m.shape[1] // 2, m.shape[0] // 2)) for m in ims]
    h = max(m.shape[0] for m in ims); ims = [cv2.copyMakeBorder(m, 0, h - m.shape[0], 0, 0, cv2.BORDER_CONSTANT) for m in ims]
    cv2.imwrite(str(g / f'oversikt_{i // 3 + 1}.jpg'), np.hstack(ims))
