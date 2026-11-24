"""Motprov A6 (klippspecifik kod): före (forvarld_karna) och efter (B-nasta-klipp/karna).

1. Grep efter klippnamn och märken i koden.
2. Originalets namnberoende: `_fokal` och `_modell_semantik` anropas med påhittade mappnamn som inte finns på disk.
   Ett svar som inte är None kommer då bara från namnet.
3. B:s kedja körs (Lager 1) på en kopia av ingestens filer under ett annat mappnamn (i den här mappen) och jämförs
   med körningen under det riktiga namnet. Allt utom `klipp_id` ska vara lika.

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\prov\\a6_namnprov.py <ingestmapp> <ord att söka> ...
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys

HIT = pathlib.Path(__file__).resolve().parent
B = HIT.parent
ROT = B.parents[2]


def grep(mapp: pathlib.Path, ord_: list[str]):
    traff = []
    for f in sorted(mapp.glob("*.py")):
        for i, rad in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for o in ord_:
                if re.search(re.escape(o), rad, re.IGNORECASE):
                    traff.append(dict(fil=str(f.relative_to(ROT)), rad=i, ord=o, text=rad.strip()[:140]))
    return traff


def main():
    ingest = pathlib.Path(sys.argv[1]).resolve()
    ord_ = sys.argv[2:]
    res = dict(grep_fore=grep(ROT / "forvarld_karna", ord_), grep_efter=grep(B / "karna", ord_))
    # 2. originalets namnberoende
    spec = importlib.util.spec_from_file_location("om_orig", ROT / "forvarld_karna/obs_motor.py")
    om = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROT / "forvarld_karna"))
    spec.loader.exec_module(om)
    falska = ["notan-tagningar-v2", "bonotanical-tagningar", "kennys-burgare-tagningar", "a-dialog-kafe-tagningar",
              "e-ny-dialog-tagningar", "z-helt-okant-tagningar"]
    namn = []
    for f in falska:
        p = ROT / "scen/3d/ingest/ut" / f
        fk = om._fokal(p)
        sem = om._modell_semantik(p)
        namn.append(dict(pahittat_namn=f, finns_pa_disk=p.exists(), fokal_ur_tabell=(fk[0] if fk else None),
                         semantik_personer=(len(sem.get("personer", [])) if sem else None)))
    res["namnberoende_fore"] = namn
    # 3. B:s Lager 1 under annat namn
    # kopia (inte länk) av de filer kedjan läser, under ett namn utan ledtrådar
    import shutil
    lank = HIT / "namnprov" / "zz-omdopt-utan-ledtradar"
    if not lank.exists():
        for f in ingest.rglob("*"):
            rel = f.relative_to(ingest)
            behov = (rel.parts[0] == "klipp" and f.suffix == ".mp4") or (
                rel.parts[0][:1] == "S" and (f.name in ("meta.json", "rum.json", "personer.json", "masker.npy")
                                            or f.name.startswith("sekvens_") or (len(rel.parts) == 4 and rel.parts[1:3] == ("rum", "depth"))))
            if f.is_file() and behov:
                (lank / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, lank / rel)
    py = str(ROT / "scen/.venv/Scripts/python.exe")
    kod = (
        "import sys,json,pathlib; sys.path.insert(0, r'%s'); import obs_motor; "
        "o,m=obs_motor.bygg(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])); "
        "pathlib.Path(sys.argv[3]).write_text(o.model_dump_json(indent=1), encoding='utf-8')"
    ) % str(B / "karna")
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8")
    ut1 = HIT / "namnprov" / "obs_riktigt_namn.json"
    ut2 = HIT / "namnprov" / "obs_omdopt.json"
    subprocess.run([py, "-c", kod, str(ingest), str(HIT / "namnprov/cache_riktigt"), str(ut1)], check=True, env=env)
    subprocess.run([py, "-c", kod, str(lank), str(HIT / "namnprov/cache_omdopt"), str(ut2)], check=True, env=env)
    a = json.loads(ut1.read_text(encoding="utf-8"))
    b = json.loads(ut2.read_text(encoding="utf-8"))
    a.pop("klipp_id"); b.pop("klipp_id")
    res["efter_omdopt_lika"] = a == b
    res["efter_omdopt_antal_tagningar"] = len(a["klipp"])
    (HIT / "a6_namnprov.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(grep_fore=len(res["grep_fore"]), grep_efter=len(res["grep_efter"]), namn=namn,
                          omdopt_lika=res["efter_omdopt_lika"]), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
