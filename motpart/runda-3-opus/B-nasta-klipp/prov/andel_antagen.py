"""Andel `antagen` per paket: leder, kamera (höjd, lodlinje, fokal), objekt och antaganden. Utvärdering, inte kärnkod.

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\prov\\andel_antagen.py <utmapp> [<utmapp> ...] [--json fil]

Läser bara `paket.json` i varje utmapp. Skriver en rad per paket och, med --json, alla siffror till filen.
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter


def en(mapp: pathlib.Path) -> dict:
    P = json.loads((mapp / "paket.json").read_text(encoding="utf-8"))
    led = Counter()
    for v in P["synlighet"].values():
        led.update(v["led_status"].values())
    n_led = sum(led.values()) or 1
    tagn = P["tagningar"]
    hojd = Counter(t["kamera"]["hojd"]["status"] for t in tagn)
    lod = Counter(t["kamera"]["lodlinje"]["status"] for t in tagn)
    fok = Counter(t["kamera"].get("fokal_status") for t in tagn)
    epi = Counter(o.get("epistemik") for o in P["objekt"])
    till = Counter(v["tillstand"] for v in P["synlighet"].values())
    return dict(
        mapp=mapp.name, tagningar=len(tagn), person_tagningar=len(P["synlighet"]),
        leder=dict(led), andel_leder_antagen=round(led.get("antagen", 0) / n_led, 3),
        andel_leder_sedd=round(led.get("sedd", 0) / n_led, 3),
        kamerahojd=dict(hojd), lodlinje=dict(lod), fokal=dict(fok),
        andel_kamerahojd_antagen=round(hojd.get("antagen", 0) / max(1, len(tagn)), 3),
        objekt_epistemik=dict(epi), antaganden=len(P["antaganden"]), tillstand=dict(till),
    )


def main():
    args = sys.argv[1:]
    ut_json = None
    if "--json" in args:
        i = args.index("--json")
        ut_json = pathlib.Path(args[i + 1])
        args = args[:i] + args[i + 2:]
    res = [en(pathlib.Path(a)) for a in args]
    for r in res:
        print(json.dumps(r, ensure_ascii=False))
    if ut_json:
        ut_json.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
