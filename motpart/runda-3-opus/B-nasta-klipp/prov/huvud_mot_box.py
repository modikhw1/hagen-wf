import json, sys, pathlib
import numpy as np
B = pathlib.Path(r"C:\Users\praiseworthy\Desktop\hagen-wf\motpart\runda-3-opus\B-nasta-klipp")
sys.path.insert(0, str(B / "karna"))
import grindar as G
# Diagnos (eget mått): huvudets projektion (paketets kamera) mot YOLO-rutans mitt och topp, per (tagning, person).
# Körs: huvud_mot_box.py <utmapp> <ingestmapp>
ut, ing = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
P = json.loads((ut / "paket.json").read_text(encoding="utf-8"))
W, H, S = P["bild"]["bredd"], P["bild"]["hojd"], P["bild"]["sensor_mm"]
L = {n: i for i, n in enumerate(P["leder"])}
for pid, spl in P["rorelse"].items():
    for sp in spl:
        t = next(t for t in P["tagningar"] if t["id"] == sp["tagning"])
        boxar = json.loads((ing / t["id"].upper() / "personer.json").read_text(encoding="utf-8")).get(str(sp.get("spar")), {})
        du, dv, bw = [], [], []
        for r in sp["rutor"]:
            b = boxar.get(str(r[0] - t["ut"][0]))
            if not b: continue
            X = np.array(r[1:], float).reshape(-1, 3) / 1000
            uv, d = G.proj(X[[L["c_head"], L["c_neck"]]], G.kamera_vid(t, r[0]), W, H, S)
            du.append(uv[0, 0] - (b[0] + b[2]) / 2); bw.append(b[2] - b[0])
            dv.append(uv[0, 1] - b[1])
        if du:
            print(f"{sp['tagning']} {pid} n={len(du)} huvud_x - boxmitt = {np.median(du)/W:+.3f} W (boxbredd {np.median(bw)/W:.2f} W), huvud_y - boxtopp = {np.median(dv)/H:+.3f} H")
