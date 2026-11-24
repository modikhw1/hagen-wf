"""Ett kommando: ingestmapp -> obs.json, recept.json, paket.json (scenpaket/2), grindar, Blender-rutor och kontaktkarta.

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\karna\\kor.py --ingest <ingestmapp> [--ut <mapp>]

Inget klippnamn finns i koden. Utmappen heter som ingestmappen (bestäms vid körning). Inga betalda anrop: allt läses
ur ingestens cache (SAM 3D Body-sekvenser, MoGe-djup, YOLO-rutor och masker, videon) och räknas lokalt.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[3]
sys.path.insert(0, str(HIT))

import obs_motor  # noqa: E402
import rums_pussel  # noqa: E402
import scen_brygga  # noqa: E402
import kontaktkarta  # noqa: E402
from schema import Observationer, Recept  # noqa: E402

BLENDER = pathlib.Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")


def kor(ingest: pathlib.Path, ut: pathlib.Path, rendera: bool = True, bara_brygga: bool = False) -> dict:
    ut.mkdir(parents=True, exist_ok=True)
    cache = ut / "cache"
    tider = {}
    t0 = time.time()
    if bara_brygga and (ut / "obs.json").exists() and (ut / "recept.json").exists():
        obs = Observationer.model_validate_json((ut / "obs.json").read_text(encoding="utf-8"))
        recept = Recept.model_validate_json((ut / "recept.json").read_text(encoding="utf-8"))
        matning = json.loads((ut / "matning.json").read_text(encoding="utf-8"))
    else:
        obs, matning = obs_motor.bygg(ingest, cache)
        (ut / "obs.json").write_text(obs.model_dump_json(indent=1), encoding="utf-8")
        (ut / "matning.json").write_text(json.dumps(matning, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        tider["lager1_s"] = round(time.time() - t0, 1)
        t1 = time.time()
        hist = rums_pussel.kor(obs)
        rader = rums_pussel.logg(hist, obs)
        recept = rums_pussel.bygg_recept(hist, obs, rader)
        (ut / "recept.json").write_text(recept.model_dump_json(indent=1), encoding="utf-8")
        tider["lager2_s"] = round(time.time() - t1, 1)
        print(f"[Lager 2] sluttro '{recept.tro}' (P={recept.sannolikhet:.2f})")
    t2 = time.time()
    paket_fil = scen_brygga.kompilera_scenpaket(ingest, obs, recept, matning, ut, cache=cache)
    tider["lager3_s"] = round(time.time() - t2, 1)
    if rendera and BLENDER.exists():
        t3 = time.time()
        lokal = ut / "lokal"
        lokal.mkdir(exist_ok=True)
        subprocess.run([str(BLENDER), "-b", "--factory-startup", "--python", str(ut / "lokal_bygg.py"), "--", str(paket_fil), str(lokal)],
                       cwd=str(ROT), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tider["blender_s"] = round(time.time() - t3, 1)
        # Blender avslutar med 0 även när en rendering inte skrivs; räkna kontrollrutorna så att felet syns
        P = json.loads(paket_fil.read_text(encoding="utf-8"))
        vantade = [f"kontroll_{t['id']}_{u:04d}.png" for t in P["tagningar"]
                   for u in sorted({t["ut"][0] + int(round(.1 * (t["ut"][1] - t["ut"][0] - 1))), (t["ut"][0] + t["ut"][1]) // 2,
                                    t["ut"][0] + int(round(.9 * (t["ut"][1] - t["ut"][0] - 1)))})]
        tider["kontrollrutor_saknas"] = [f for f in vantade if not (lokal / f).exists()]
        if tider["kontrollrutor_saknas"]:
            print(f"VARNING: {len(tider['kontrollrutor_saknas'])} av {len(vantade)} kontrollrutor saknas efter Blender")
        kontaktkarta.bygg(paket_fil, ingest, lokal, ut / "kontaktkarta.png")
    (ut / "tider.json").write_text(json.dumps(tider, indent=1), encoding="utf-8")
    print("tider", tider)
    return tider


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest", required=True)
    ap.add_argument("--ut", default=None)
    ap.add_argument("--utan-render", action="store_true")
    ap.add_argument("--bara-brygga", action="store_true")
    a = ap.parse_args()
    ingest = pathlib.Path(a.ingest).resolve()
    # absolut: Blender skriver inte kontrollrutor till en relativ render.filepath (tyst fel, rättat 20 nov)
    ut = (pathlib.Path(a.ut) if a.ut else HIT.parent / "ut" / ingest.name).resolve()
    os.environ.setdefault("PYTHONHASHSEED", "0")
    kor(ingest, ut, rendera=not a.utan_render, bara_brygga=a.bara_brygga)


if __name__ == "__main__":
    main()
