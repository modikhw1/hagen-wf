"""Bygg reproducerbara före/efter-planer för dolda fötter och rekvisita.

Körs från projektroten med scenens venv. Skriver bara under
kontrakt/ut/dolda_fotter/; ingestdata och banker är läsande underlag.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KONTRAKT = HERE.parent
ROT = KONTRAKT.parents[2]
sys.path.insert(0, str(KONTRAKT))

from kompilera import kompilera


def skriv(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def tom_regi(folder: Path, out: Path) -> Path:
    source = json.loads((folder / "regi.json").read_text(encoding="utf-8"))
    source["edits"] = []
    source["ramar"]["bevara_beats"] = []
    source["ramar"]["bevara_klippoffset_s"] = None
    path = out / "regi_tom.json"
    skriv(path, source)
    return path


def sammanfatta(plan: dict) -> dict:
    props = []
    for row in plan.get("kvalitet", {}).get("props", []):
        errors = [x["centrumfel_px"] for x in row.get("jamforelse", []) if x.get("centrumfel_px") is not None]
        props.append(dict(
            scen=row["scen"], prop=row["prop"], lage=row["lage"], yta=row.get("yta"),
            centrumfel_px=errors, max_centrumfel_px=max(errors) if errors else None,
            antaganden=row.get("antaganden", []),
        ))
    objects = [dict(id=o["id"], scen=o.get("scen"), pos_m=o.get("pos_m"),
                    matt_m=o.get("matt_m"), synlig_ut=o.get("synlig_ut"))
               for o in plan.get("objekt", [])
               if o["id"].startswith(("stol_", "bord_", "sits_"))]
    people = [dict(scen=s["id"], personer=copy.deepcopy(s.get("personer", [])))
              for s in plan.get("scener", [])]
    return dict(props=props, mobler=objects, personer=people,
                hojdpassning=plan.get("kvalitet", {}).get("hojdpassning", []))


def bygg(namn: str, phase: str) -> dict:
    folder = KONTRAKT / "exempel" / namn
    out = KONTRAKT / "ut" / "dolda_fotter" / phase / namn
    out.mkdir(parents=True, exist_ok=True)
    plan = kompilera(folder / "kalla.json", tom_regi(folder, out), snabb=True)
    skriv(out / "plan.json", plan)
    summary = sammanfatta(plan)
    skriv(out / "matning.json", summary)
    return summary


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("användning: dolda_fotter_mat.py FAS")
    phase = sys.argv[1]
    result = {name: bygg(name, phase) for name in ("notan", "bar")}
    skriv(KONTRAKT / "ut" / "dolda_fotter" / phase / "sammanfattning.json", result)
    for name, data in result.items():
        print(name, "props", [(x["scen"], x["prop"], x["max_centrumfel_px"]) for x in data["props"]])


if __name__ == "__main__":
    main()
