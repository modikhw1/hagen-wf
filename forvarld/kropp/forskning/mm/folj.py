"""FORSKNING (0039): följer kontrollern referensen? Råutdata från kor_mm mot referensens kroppar, led för led.

  scen/.venv/Scripts/python.exe forvarld/kropp/forskning/mm/folj.py <raw.npz> <ref.npz>
Simsteg i jämförs med referensruta i+1 (som efter_mm.tillbaka). Miljöns xy-förskjutning och golvskiftet dras bort ur första steget.
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); import mhr_smpl as M

d = dict(np.load(sys.argv[1], allow_pickle=True)); r = dict(np.load(sys.argv[2], allow_pickle=True))
S = M.fk_smpl(r['G'].astype(float), r['rot'].astype(float)); pos = d['pos'].astype(float); k = min(len(pos), len(S) - 1)
P = pos[:k] - d['skift'][None, None]; R = S[1:1 + k]; off = np.r_[(P[0, 0] - R[0, 0])[:2], 0.]; P = P - off
e = np.linalg.norm(P - R, axis=-1) * 100
ut = dict(steg=int(len(pos)), jamforda=int(k), starttid=float(d['starttid']) if 'starttid' in d else None, forskjutning_xy_m=off[:2].round(2).tolist(),
          medelfel_cm_per_led=round(float(e.mean()), 1), median_cm=round(float(np.median(e)), 1), storsta_cm=round(float(e.max()), 1),
          backen_cm=dict(medel=round(float(e[:, 0].mean()), 1), sista=round(float(e[-1, 0]), 1)),
          rothojd_m=[round(float(P[0, 0, 2]), 3), round(float(P[-1, 0, 2]), 3)], ref_rothojd_m=[round(float(R[0, 0, 2]), 3), round(float(R[-1, 0, 2]), 3)],
          per_kropp_cm={n: round(float(e[:, M.SN.index(n)].mean()), 1) for n in ('Pelvis', 'L_Ankle', 'R_Ankle', 'L_Hand', 'R_Hand', 'Head') if n in M.SN},
          fel_over_tid_cm=[round(float(x), 1) for x in e.mean(1)[::max(1, k // 8)]])
print(json.dumps(ut, ensure_ascii=False, indent=1))
