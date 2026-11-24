"""Spår A:s mått b (2D-trohet mot MediaPipe, `A-domare/matt/trohet2d.py`) på B:s paket, en video per tagning.

A:s egen adapter antar en sammanhängande video; B:s paket har en video per tagning (`klipp/S*.mp4`). Här skrivs
sys2d-filer per tagning i A:s format, i två varianter:
  - `sedda`: bara leder som paketet märker `sedd` i rutan (A:s format tillåter att skymda leder utelämnas);
  - `alla`: alla leder som ligger framför kameran (inget utelämnat).
Sedan körs A:s skript oförändrat (`--pastaende`). Resultat: `prov/a_trohet2d/<ingestmapp>/`.

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\prov\\a_trohet2d.py <utmapp-för-paket> <ingestmapp>
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
B = HIT.parent
ROT = B.parents[2]
sys.path.insert(0, str(B / "karna"))
import grindar as G  # noqa: E402

NAMN = {"huvud": "c_head", "v_axel": "l_uparm", "h_axel": "r_uparm", "v_armbage": "l_lowarm", "h_armbage": "r_lowarm",
        "v_handled": "l_wrist", "h_handled": "r_wrist", "v_hoft": "l_upleg", "h_hoft": "r_upleg", "v_kna": "l_lowleg",
        "h_kna": "r_lowleg", "v_fotled": "l_foot", "h_fotled": "r_foot"}


def main():
    utmapp, ingest = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    P = json.loads((utmapp / "paket.json").read_text(encoding="utf-8"))
    W, H, S = P["bild"]["bredd"], P["bild"]["hojd"], P["bild"]["sensor_mm"]
    LI = {n: i for i, n in enumerate(P["leder"])}
    dest = HIT / "a_trohet2d" / ingest.name
    dest.mkdir(parents=True, exist_ok=True)
    py = str(ROT / "scen/.venv/Scripts/python.exe")
    skript = ROT / "motpart/runda-3-opus/A-domare/matt/trohet2d.py"
    res = {}
    for t in P["tagningar"]:
        a0 = t["ut"][0]
        for variant in ("sedda", "alla"):
            rutor = {}
            for p in t["personer"]:
                sp = next(x for x in P["rorelse"][p["id"]] if x["tagning"] == t["id"])
                sedd = G._sedd_matris(sp, len(P["leder"]), [r[0] for r in sp["rutor"]])
                for k, r in enumerate(sp["rutor"]):
                    u = r[0]
                    X = np.array(r[1:], float).reshape(-1, 3) / 1000.0
                    uv, d = G.proj(X, G.kamera_vid(t, u), W, H, S)
                    led = {}
                    for kn, ln in NAMN.items():
                        j = LI[ln]
                        if d[j] <= 0:
                            continue
                        if variant == "sedda" and (sedd is None or not sedd[k, j]):
                            continue
                        led[kn] = [round(float(uv[j, 0]), 1), round(float(uv[j, 1]), 1)]
                    if led:
                        rutor.setdefault(u - a0, []).append({"id": p["id"], "leder": led})
            sys2d = dict(video=str(ingest / "klipp" / f"{t['id'].upper()}.mp4"), bild=[W, H],
                         rutor=[{"ruta": k, "personer": v} for k, v in sorted(rutor.items())])
            f = dest / f"sys2d_{t['id']}_{variant}.json"
            f.write_text(json.dumps(sys2d), encoding="utf-8")
            logg = dest / f"logg_{t['id']}_{variant}.json"
            pr = subprocess.run([py, str(skript), "--pastaende", str(f), "--logg", str(logg)], capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
            res[f"{t['id']}:{variant}"] = dict(rc=pr.returncode, ut=pr.stdout[-1500:], fel=pr.stderr[-800:])
            print(t["id"], variant, pr.returncode, pr.stdout[-600:].strip())
    (dest / "sammanfattning.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
