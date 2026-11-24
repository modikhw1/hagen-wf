"""Lokal klient för att ladda upp källklipp (en gång), köra O-lager och mäta M1/M2/M3/M6 på Modal.

Användning:
    python infra/modal_klient.py ladda-upp          # laddar upp 200 klipp + metadata en gång till volymen
    python infra/modal_klient.py bygg-200           # bygger O-lagret för alla 200 klipp parallellt (M3 batch)
    python infra/modal_klient.py m6                 # mäter varm vs kall anropstid (M6)
    python infra/modal_klient.py m1                 # mäter lästid per klipp i O-lagret (M1)
    python infra/modal_klient.py m3-url             # mäter 1 nytt klipp från URL -> komplett O-lager (M3)
    python infra/modal_klient.py m2-olager          # kör hela steg 2 från O-lager + varianter i RAM (M2)
    python infra/modal_klient.py m2-omrakning       # kör hela steg 2 från grunden inkl. 144 R i RAM (M2)
    python infra/modal_klient.py synka-json         # hämtar kompakta JSON-lager (~6 MB) lokalt till data/olager_json/
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

import modal

ROT = Path(__file__).resolve().parents[1]
if str(ROT) not in sys.path:
    sys.path.insert(0, str(ROT))

from infra.olager import ladda_repo_metadata

APP_NAMN = "hagen-infra"
VOL_NAMN = "hagen-olager"
KALLOR_LOKAL = Path.home() / "Downloads" / "letrend-r4"


def cmd_ladda_upp() -> dict:
    t0 = time.monotonic()
    vol = modal.Volume.from_name(VOL_NAMN, create_if_missing=True)
    mp4s = sorted(KALLOR_LOKAL.glob("*.mp4"))
    ids = {p.stem for p in mp4s}

    # Kontrollera vilka som redan finns i volymen så vi inte laddar upp i onödan
    bef: set[str] = set()
    try:
        for entry in vol.listdir("/kallor"):
            bef.add(Path(entry.path).name)
    except Exception:
        pass

    nya = [p for p in mp4s if p.name not in bef]
    meta_map = ladda_repo_metadata(ids)
    urval_fil = ROT / "motpart/runda-4/2-invarians/urval_las.json"

    with tempfile.TemporaryDirectory(prefix="hagen_meta_") as td:
        meta_fil = Path(td) / "repo_meta.json"
        meta_fil.write_text(json.dumps(meta_map, ensure_ascii=False), encoding="utf-8")
        with vol.batch_upload(force=True) as batch:
            batch.put_file(str(meta_fil), "/meta/repo_meta.json")
            batch.put_file(str(urval_fil), "/meta/urval_las.json")
            for p in nya:
                batch.put_file(str(p), f"/kallor/{p.name}")

    return {
        "totalt_mp4": len(mp4s),
        "redan_i_volym": len(bef),
        "uppladdade_nu": len(nya),
        "sek": round(time.monotonic() - t0, 2),
    }


def cmd_m6() -> dict:
    Arb = modal.Cls.from_name(APP_NAMN, "VarmArbetare")
    arb = Arb()
    t0 = time.perf_counter()
    r1 = arb.ping.remote()
    w1 = round(time.perf_counter() - t0, 3)

    t1 = time.perf_counter()
    r2 = arb.ping.remote()
    w2 = round(time.perf_counter() - t1, 3)

    t2 = time.perf_counter()
    r3 = arb.ping.remote()
    w3 = round(time.perf_counter() - t2, 3)

    return {
        "anrop_1": {"vaggtid_sek": w1, **r1},
        "anrop_2_varm": {"vaggtid_sek": w2, **r2},
        "anrop_3_varm": {"vaggtid_sek": w3, **r3},
    }


def cmd_bygg_200(force: bool = False) -> dict:
    fn = modal.Function.from_name(APP_NAMN, "orkestrera_olager_200")
    t0 = time.monotonic()
    r = fn.remote(chunk_storlek=8, force=force, med_c_ref=True)
    r["klient_vaggtid_sek"] = round(time.monotonic() - t0, 2)
    return r


def cmd_m1() -> dict:
    Arb = modal.Cls.from_name(APP_NAMN, "VarmArbetare")
    return Arb().mat_m1.remote()


def cmd_m3_url(url: str, clip_id: str) -> dict:
    Arb = modal.Cls.from_name(APP_NAMN, "VarmArbetare")
    t0 = time.monotonic()
    r = Arb().ingest_url.remote(url, clip_id, force=True)
    r["klient_vaggtid_sek"] = round(time.monotonic() - t0, 2)
    return r


def cmd_m2(fran_olager: bool) -> dict:
    fn = modal.Function.from_name(APP_NAMN, "orkestrera_steg2")
    t0 = time.monotonic()
    r = fn.remote(fran_olager=fran_olager, ref_chunk_storlek=6)
    r["klient_vaggtid_sek"] = round(time.monotonic() - t0, 2)
    return r


def cmd_synka_json() -> dict:
    """Hämtar en kompakt JSON-sammanfattning av alla 200 O-lager-klipp till lokal disk (~2 MB)."""
    vol = modal.Volume.from_name(VOL_NAMN)
    ut_dir = ROT / "data" / "olager_index"
    ut_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    Arb = modal.Cls.from_name(APP_NAMN, "VarmArbetare")
    sam = Arb().sammanfatta.remote()
    (ut_dir / "sammanfattning.json").write_text(json.dumps(sam, ensure_ascii=False, indent=2), encoding="utf-8")
    # Hämta sparade steg 2-resultat om de finns
    for namn in ("steg2_olager.json", "steg2_omrakning.json"):
        try:
            data = b"".join(vol.read_file(f"/resultat/{namn}"))
            (ut_dir / namn).write_bytes(data)
        except Exception:
            pass
    return {"sammanfattning": sam, "ut_dir": str(ut_dir), "sek": round(time.monotonic() - t0, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ladda-upp", "bygg-200", "m6", "m1", "m3-url", "m2-olager", "m2-omrakning", "synka-json"])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--url", default=None)
    ap.add_argument("--id", dest="clip_id", default=None)
    a = ap.parse_args()

    if a.cmd == "ladda-upp":
        res = cmd_ladda_upp()
    elif a.cmd == "bygg-200":
        res = cmd_bygg_200(force=a.force)
    elif a.cmd == "m6":
        res = cmd_m6()
    elif a.cmd == "m1":
        res = cmd_m1()
    elif a.cmd == "m3-url":
        # Default: ett verkligt kort klipp ur manifest.jsonl så vi testar riktig TikTok-hämtning -> O-lager
        url = a.url or "https://www.tiktok.com/@krogcompanyvarnamo/video/7442013966571801879"
        cid = a.clip_id or "m3test-krogcompanyvarnamo-7442013966571801879"
        res = cmd_m3_url(url, cid)
    elif a.cmd == "m2-olager":
        res = cmd_m2(fran_olager=True)
    elif a.cmd == "m2-omrakning":
        res = cmd_m2(fran_olager=False)
    else:
        res = cmd_synka_json()

    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
