"""Strukturstatistik ur bankklippen: scenlängder, antal scener, klipplängd. Samma kalibrering som rörelserna:
score = 100 * (1 - 0.2 * |x - median| / q90), där q90 = 90:e percentilen av |x - median| i banken (log-skala)."""
import json, glob
from pathlib import Path
import numpy as np
ROT = Path(__file__).resolve().parent.parent
L, N, K = [], [], []
for f in glob.glob(str(ROT / "data" / "bank" / "*" / "spar.json")):
    s = json.load(open(f))["scener"]
    L += [max(0.2, x["slut"] - x["start"]) for x in s]; N.append(len(s)); K.append(s[-1]["slut"])
def kal(x):
    lx = np.log(np.array(x)); m = float(np.median(lx)); q = float(np.percentile(np.abs(lx - m), 90)); return {"median_log": round(m, 4), "q90": round(q, 4), "median": round(float(np.exp(m)), 2), "p10": round(float(np.percentile(x, 10)), 2), "p90": round(float(np.percentile(x, 90)), 2)}
ut = {"scenlangd": kal(L), "antal_scener": kal(N), "klipplangd": kal(K), "klipp": len(N), "scener": len(L)}
json.dump(ut, open(ROT / "data" / "bibliotek" / "struktur.json", "w"), indent=1)
print(ut)
