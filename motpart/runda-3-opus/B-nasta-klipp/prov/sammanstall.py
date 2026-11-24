"""Sammanställning per paket i `B-nasta-klipp/ut/*/`: tillstånd, synlighet, mätt mot antaget, kamerarörelse, grindar.

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\prov\\sammanstall.py [mapp ...]
Skriver `prov/sammanstallning.json` och skriver ut en markdowntabell.
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

B = pathlib.Path(__file__).resolve().parent.parent


def en(mapp: pathlib.Path) -> dict:
    P = json.loads((mapp / "paket.json").read_text(encoding="utf-8"))
    m = json.loads((mapp / "matning.json").read_text(encoding="utf-8"))
    g = json.loads((mapp / "paket_grindar.json").read_text(encoding="utf-8"))
    r = json.loads((mapp / "recept.json").read_text(encoding="utf-8"))
    till = Counter(v["tillstand"] for v in P["synlighet"].values())
    sedd = [sum(1 for s in v["led_status"].values() if s == "sedd") / len(v["led_status"]) for v in P["synlighet"].values()]
    rorliga = [t["id"] for t in P["tagningar"] if not t["kamera"]["statisk"]]
    hojd = {t["id"]: (t["kamera"]["hojd"]["v"], t["kamera"]["hojd"]["status"]) for t in P["tagningar"]}
    lod = {t["id"]: (t["kamera"]["lodlinje"]["pitch"], t["kamera"]["lodlinje"]["roll"], t["kamera"]["lodlinje"]["status"]) for t in P["tagningar"]}
    bord = [(o["id"], round(o["pos"][2] + o["matt"][2] / 2, 3), o["status"]) for o in P["objekt"] if o["typ"] == "bord"]
    return dict(
        klipp=P["klipp"]["id"], tagningar=len(P["tagningar"]), personer=sorted(P["personer"]), person_tagningar=len(P["synlighet"]),
        tillstand=dict(till), andel_leder_sedda_median=round(sorted(sedd)[len(sedd) // 2], 2) if sedd else None,
        fokal=dict(v=m["fokal"]["klipp"]["v"], status=m["fokal"]["klipp"]["status"]),
        kamerahojd=hojd, lodlinje=lod, rorliga_kameror=rorliga, bord_topp=bord,
        sluttro=r["tro"], sannolikhet=r["sannolikhet"], identitet=m["identitet"]["spar"],
        hallning=m.get("hallning_per_identitet"), antaganden=len(P["antaganden"]), grindar=g["sammanfattning"],
        storlek_kb=round((mapp / "paket.json").stat().st_size / 1024),
    )


def main():
    mappar = [pathlib.Path(a) for a in sys.argv[1:]] or sorted(p.parent for p in (B / "ut").glob("*/paket.json"))
    res = [en(m) for m in mappar]
    (B / "prov" / "sammanstallning.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in res:
        print(json.dumps(x, ensure_ascii=False))


if __name__ == "__main__":
    main()
