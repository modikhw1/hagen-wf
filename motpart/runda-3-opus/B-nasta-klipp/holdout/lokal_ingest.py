"""Lokal, gratis del av ingesten för ett klipp som redan delats i tagningar (`ingest_flera.py --endast-dela`).

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\holdout\\lokal_ingest.py <ingestmapp>

Per tagning S<n> körs samma stegfunktioner som `scen/3d/ingest/ingest_klipp.py <S<n>.mp4> <ingestmapp>/S<n> --till kamera`
(och som `flera/ingest_flera.forsteg_personer`, 2 personer): `meta`, `steg_personer` (YOLO11-seg + BoT-SORT) och
`steg_kamera` (COLMAP). Två skillnader mot standardkommandot, båda för att inte skriva utanför `<ingestmapp>`:
`sakerhetskopiera(ut)` (som kopierar den nyss skapade, tomma mappen till `scen/3d/kontrakt/ut/fore_regler/`) och
`rensa_efter` (no-op i en ny mapp) anropas inte. Inget betalt: kroppssteget (SAM 3D Body på Modal) och rumssteget
(MoGe-2 på Modal) körs INTE. Skriptet räknar i stället vad de skulle kräva och skriver `<ingestmapp>/lokal_ingest.json`.

Utvärderingsverktyg för hold-out, inte en del av B:s frysta kärna (`../karna/`).
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

ROT = pathlib.Path(__file__).resolve().parents[4]
ING = ROT / "scen" / "3d" / "ingest"
sys.path.insert(0, str(ING))

import ingest_klipp as IK  # noqa: E402


def main():
    ut = pathlib.Path(sys.argv[1]).resolve()
    if ING / "ut" not in ut.parents:
        raise SystemExit(f"ingestmappen ska ligga under {ING / 'ut'}")
    # ingest_flera.py skriver med plattformens standardkodning (cp1252 på Windows); läs som den själv läser
    raw = (ut / "tagningar.json").read_bytes()
    try:
        plan = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        plan = json.loads((ut / "tagningar.json").read_text())
    sammanfattning = dict(klipp=plan.get("klipp"), N=plan["N"], tagningar=[])
    for s in plan["tagningar"]:
        sid = s["id"]
        klipp = ut / "klipp" / f"{sid}.mp4"
        d = ut / sid
        d.mkdir(parents=True, exist_ok=True)
        M = IK.meta(klipp, d)
        rad = dict(id=sid, rutor=M["N"], bredd=M["bredd"], hojd=M["hojd"], fps=M["fps"])
        if not (d / "personer.json").exists():
            t = time.time()
            r = IK.steg_personer(klipp, d, M, 2)
            IK.logg(d, "personer", time.time() - t, **r)
        P = json.loads((d / "personer.json").read_text(encoding="utf-8"))
        rad["personer"] = {k: len(v) for k, v in P.items()}
        rad["kroppsjobb_steg1"] = sum(len(v) for v in P.values())
        if not (d / "kamera.json").exists():
            t = time.time()
            r = IK.steg_kamera(klipp, d, M)
            IK.logg(d, "kamera", time.time() - t, **r)
        K = json.loads((d / "kamera.json").read_text(encoding="utf-8"))
        rad["kamera"] = dict(registrerade=K.get("registrerade"), av=K.get("av"), statisk=K.get("statisk"), fokal_px=K.get("fokal_px"))
        rad["saknas_for_B"] = ["sekvens_*.npz (kropp: SAM 3D Body, Modal-GPU)", "rum/depth/*.npz och rum.json (rum: MoGe-2, Modal-GPU)"]
        sammanfattning["tagningar"].append(rad)
        print(sid, json.dumps(rad, ensure_ascii=False), flush=True)
    sammanfattning["kroppsjobb_totalt"] = sum(r["kroppsjobb_steg1"] for r in sammanfattning["tagningar"])
    (ut / "lokal_ingest.json").write_text(json.dumps(sammanfattning, ensure_ascii=False, indent=1), encoding="utf-8")
    print("kroppsjobb totalt", sammanfattning["kroppsjobb_totalt"])


if __name__ == "__main__":
    main()
