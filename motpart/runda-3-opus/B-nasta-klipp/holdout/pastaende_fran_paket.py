"""Påstående i spår A:s format (`A-domare/holdout_facit/README.md`) ur B:s paket för hold-out-klippen.

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\holdout\\pastaende_fran_paket.py <ut.json>

För varje facitruta (videorutans index i originalet) i `A-domare/holdout_facit/*.facit.json`: tagningen i
`B-nasta-klipp/ut/<klipp-id>-tagningar/paket.json` vars `ut` = [a, b) innehåller rutan, kamerans z vid rutan
(`grindar.kamera_vid`, samma interpolation som Blender) minus `golv_z`, och `kamera.hojd.status`. Paketets rutindex
antas vara originalets (tagningsfilerna läggs efter varandra); paketets rutantal skrivs ut för kontroll.
Läser bara; ändrar varken paket eller kärna.
"""
from __future__ import annotations

import json
import pathlib
import sys

B = pathlib.Path(__file__).resolve().parents[1]
ROT = B.parents[2]
sys.path.insert(0, str(B / "karna"))
import grindar as G  # noqa: E402

FACIT = ROT / "motpart" / "runda-3-opus" / "A-domare" / "holdout_facit"


def main():
    ut = pathlib.Path(sys.argv[1])
    pas, info = {}, {}
    for f in sorted(FACIT.glob("*.facit.json")):
        F = json.loads(f.read_text(encoding="utf-8"))
        k = F["klipp"]
        pf = B / "ut" / f"{k}-tagningar" / "paket.json"
        if not pf.exists():
            info[k] = dict(paket="saknas")
            continue
        P = json.loads(pf.read_text(encoding="utf-8"))
        N_paket = P["tidsbas"]["antal_rutor"]
        rutor = {}
        for r in F["rutor"]:
            u = int(r["ruta"])
            t = next((t for t in P["tagningar"] if t["ut"][0] <= u < t["ut"][1]), None)
            if t is None:
                continue
            C, _, _ = G.kamera_vid(t, u)
            rutor[str(u)] = dict(kamera_hojd_m=round(float(C[2]) - float(P.get("golv_z", 0.0)), 3),
                                 kamera_hojd_status=t["kamera"]["hojd"]["status"],
                                 matt={"hojd_v": t["kamera"]["hojd"]["v"], "hojd_s": t["kamera"]["hojd"]["s"],
                                       "matt_andel": t["kamera"]["hojd"].get("matt_andel"), "tagning": t["id"],
                                       "ruta_i_tagning": u - t["ut"][0]})
        pas[k] = dict(rutor=rutor)
        info[k] = dict(paket=str(pf.relative_to(ROT)), antal_rutor_paket=N_paket, antal_rutor_facit_kalla=F.get("N") or None)
    ut.write_text(json.dumps(pas, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(pastaende=pas, info=info), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
