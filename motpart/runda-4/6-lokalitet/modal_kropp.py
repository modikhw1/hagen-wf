"""Steg 2: kroppsspår för klipp som saknar dem, via befintlig ingest_v2 (SAM 3D Body m.m.) på Modal.

Återanvänder app och klass ur arbetsbord/ingest_v2/modal_ingest_v2.py utan att köra dess hårdkodade main().
Skriver ENDAST till motpart/runda-4/6-lokalitet/ut/<nyckel>/ingest_v2/ (paket.json, tidslinje.json, ingest_rapport.json).
Kör: PYTHONUTF8=1 scen/.venv/Scripts/modal.exe run motpart/runda-4/6-lokalitet/modal_kropp.py::kropp --klipp "namn:nyckel,..."
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "arbetsbord" / "ingest_v2"))
from modal_ingest_v2 import app, IngestV2Worker  # noqa: E402


@app.local_entrypoint()
def kropp(klipp: str):
    t0 = time.perf_counter(); jobb = []
    w = IngestV2Worker()
    for spec in klipp.split(","):
        namn, nyckel = spec.split(":")
        data = (ROOT / "data/format/kontroll/klipp" / (namn + ".mp4")).read_bytes()
        jobb.append((nyckel, w.ingest_klipp.spawn(data, namn, nyckel), time.perf_counter()))
        print(f"skickat {nyckel}", flush=True)
    for nyckel, fc, ts in jobb:
        res = fc.get(timeout=1200)
        ut = HERE / "ut" / nyckel / "ingest_v2"; ut.mkdir(parents=True, exist_ok=True)
        for fil, nyck in (("paket.json", "paket_bytes"), ("tidslinje.json", "tidslinje_bytes")):
            tmp = ut / (fil + ".tmp"); tmp.write_bytes(res[nyck]); tmp.replace(ut / fil)
        rap = dict(res["rapport"], wall_inkl_natverk_s=round(time.perf_counter() - ts, 1))
        (ut / "ingest_rapport.json").write_text(json.dumps(rap, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"klar {nyckel}: tagningar {rap['antal_tagningar']}, sam3d-anrop {rap['antal_sam3db_anrop']}, gpu {rap['tider_s']['total_ingest_s']} s, est {rap['est_marginal_usd']} USD", flush=True)
    print(f"totalt {round(time.perf_counter() - t0, 1)} s väggtid", flush=True)
