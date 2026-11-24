# -*- coding: utf-8 -*-
"""Bygger facit per hold-out-klipp ur ankarfilerna i ankare/.

Två slags ankare:
  1. Metrologi (rumsskala.py): horisont + referenser med fot på golvet. Varje "vertikal_varianter"
     körs för sig och facit = UNIONEN av variantenas 90 %-intervall (min p05, max p95). Så blir facit
     robust mot det antagande om lodrät flyktpunkt som märkaren inte kunde avgöra.
  2. Ordningsgränser ("typ": "ordning"): när golvet inte syns går kamerahöjden inte att mäta ur pixlar.
     Då ger facit bara gränser som syns direkt (en yta ses ovanifrån => kameran är högre än ytan) och
     epistemiken: "kamera_hojd_matbar": false.

FACIT ÄR EN UPPSKATTNING. Inget är uppmätt på plats. Standardstorlekar (personlängd) är intervall.

  python bygg_facit.py            # skriver <klipp>.facit.json och facit_alla.json
"""
import json
import sys
from pathlib import Path

HAR = Path(__file__).resolve().parent
sys.path.insert(0, str(HAR.parent / "matt"))
import rumsskala as RS  # noqa: E402

ROT = HAR.parents[3]
LISTA = HAR.parent / "holdout_lista.txt"
N = 4000


def metrologi(ank: dict) -> dict:
    var = ank.get("vertikal_varianter") or [{"namn": "standard", "vertikal": ank.get("vertikal")}]
    res = []
    for i, v in enumerate(var):
        a = dict(ank)
        a["vertikal"] = v["vertikal"]
        e = RS.skatta(a, n=N, seed=100 + i)
        res.append({"namn": v["namn"], "grund": v.get("grund"), "kamera_hojd_m": e["kamera_hojd_m"],
                    "matt": e["matt"], "per_referens": e["kamera_hojd_per_referens"],
                    "referenser_konsekventa": e["referenser_konsekventa"]})

    def union(vals):
        vals = [x for x in vals if x]
        if not vals:
            return None
        lo, hi = min(x["p05"] for x in vals), max(x["p95"] for x in vals)
        p50 = sorted(x["p50"] for x in vals)[len(vals) // 2]
        return {"p05": lo, "p50": p50, "p95": hi, "bredd_cm": round((hi - lo) * 100, 1)}
    namn_m = sorted({k for r in res for k in r["matt"]})
    return {
        "ruta": ank["ruta"], "golv_synligt": True, "kamera_hojd_matbar": True,
        "metod": "enkelbildsmetrologi (Criminisi m.fl.), union över antaganden om lodrät flyktpunkt",
        "kamera_hojd_m": union([r["kamera_hojd_m"] for r in res]),
        "matt": {k: union([r["matt"].get(k) for r in res]) for k in namn_m},
        "varianter": res,
        "referenser": [{"namn": r["namn"], "hojd_m": r["hojd_m"], "kalla": r.get("kalla")} for r in ank["referenser"]],
        "horisont_anm": ank.get("horisont_anm"), "ej_matbart": ank.get("ej_matbart"),
        "marknad_av": ank.get("marknad_av"),
    }


def main():
    klipp = LISTA.read_text(encoding="utf-8").split()
    per = {k: {"klipp": k, "video": f"data/format/kontroll/klipp/{k}.mp4", "rutor": []} for k in klipp}
    for f in sorted((HAR / "ankare").glob("*.json")):
        ank = json.loads(f.read_text(encoding="utf-8"))
        if ank.get("ersatt_av"):
            continue
        k = ank["klipp"]
        if ank.get("typ") == "ordning":
            for r in ank["rutor"]:
                r = dict(r); r["ankarfil"] = f"ankare/{f.name}"
                per[k]["rutor"].append(r)
        else:
            r = metrologi(ank); r["ankarfil"] = f"ankare/{f.name}"
            per[k]["rutor"].append(r)
    for k, v in per.items():
        v["rutor"].sort(key=lambda r: r["ruta"])
        v["facit_ar_uppskattning"] = (
            "Facit är en uppskattning ur egen märkning i originalpixlar och standardstorlekar med intervall. "
            "Det är inte uppmätt på plats. Intervallen är 90 % (p05-p95) under märkarens antaganden; "
            "ett felaktigt antagande (t.ex. att personen står rak) flyttar facit.")
        v["status"] = ("metrologi" if any(r.get("kamera_hojd_matbar") for r in v["rutor"])
                       else ("bara_ordningsgranser" if v["rutor"] else "saknas"))
        (HAR / f"{k}.facit.json").write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    (HAR / "facit_alla.json").write_text(json.dumps(list(per.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in per.items():
        for r in v["rutor"]:
            kh = r.get("kamera_hojd_m")
            g = r.get("kamera_hojd_granser_m")
            print(f"{k:45s} ruta {r['ruta']:4d}  matbar={r.get('kamera_hojd_matbar')}  "
                  + (f"kamera {kh['p05']:.2f}-{kh['p95']:.2f} (p50 {kh['p50']:.2f})" if kh else f"gränser {g}")
                  + ("  " + ", ".join(f"{n}:{x['p05']:.2f}-{x['p95']:.2f}" for n, x in (r.get('matt') or {}).items() if x)))
            for vv in r.get("varianter", []):
                print(f"{'':50s}{vv['namn']:16s} {vv['kamera_hojd_m']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
