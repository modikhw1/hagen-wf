"""Verifieringsskript för Förvärldens Kärna (forvarld_karna).

Kör hela Lager 1 (obs_motor) + Lager 2 (rums_pussel) + Lager 3 (Blender/Jutsu-recept & 2D-kartor) på:
1. Guacamole (e-dialog-guacamole-tagningar, S1..S4: 2 personer vid bardisk, tvåpersonsvinkel i S4)
2. Gelato (kand-kennysgelato-tagningar, S1..S2: 1 person bakom glassdisk, 90° kameravinkelbyte)
3. A-sketch Servering (a-sketch-servering-tagningar, S1..S7: kund & personal över glasdisk + B-roll utan person i S6)
4. Notan (notan-tagningar, S1..S7: 2 bord, 3 personer, avslöjande vidvinkel i S7)
5. Syntetiska stresstestet (Absurdist Diner + Kontroll Delat Bord)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parent
sys.path.insert(0, str(HIT))
sys.path.insert(0, str(ROT / "byggsten/rumshypotes"))

import obs_motor  # noqa: E402
import rums_pussel  # noqa: E402
import scen_brygga  # noqa: E402
import syntet as gammal_syntet  # noqa: E402
from karta import rita, tidslinje  # noqa: E402
from schema import Observationer, Recept  # noqa: E402


def kor_ett_klipp(
    namn: str,
    ingest_rel: str,
    vlm_rel: str | None = None,
    djup_rel: str | None = None,
    bara_brygga: bool = False,
    utan_deklaration: bool = False,
):
    print("=" * 76)
    print(f"KLIPP: {namn} ({ingest_rel}){' [UTAN DEKLARATION.JSON]' if utan_deklaration else ''}")
    print("=" * 76)
    ingest = ROT / ingest_rel
    vlm = (ROT / vlm_rel) if vlm_rel else None
    djup = (ROT / djup_rel) if djup_rel else None
    ut = HIT / "ut" / namn
    ut.mkdir(parents=True, exist_ok=True)

    if bara_brygga and (ut / "obs.json").exists() and (ut / "recept.json").exists():
        obs = Observationer.model_validate_json((ut / "obs.json").read_text(encoding="utf-8"))
        recept = Recept.model_validate_json((ut / "recept.json").read_text(encoding="utf-8"))
    else:
        t0 = time.time()
        obs = obs_motor.bygg(ingest, vlm, djup, utan_deklaration=utan_deklaration)
        (ut / "obs.json").write_text(obs.model_dump_json(indent=1), encoding="utf-8")
        tid_obs = time.time() - t0

        print(f"[Lager 1: obs_motor] ({tid_obs:.1f} s) {len(obs.klipp)} tagningar:")
        for k in obs.klipp:
            dets_str = ", ".join(
                f"{d.id}:{d.nyckel}(d={d.djup_m.v:.2f}m"
                + (f",vid={d.vid}" if d.vid else "")
                + (f",pa={d.pa}" if d.pa else "")
                + ")"
                for d in k.detektioner
            )
            kam_del = f" [delar_kamera={k.delar_kamera_med}]" if k.delar_kamera_med else ""
            print(f"  {k.klipp} {k.rutor}{kam_del}: {dets_str}")

        t1 = time.time()
        hist = rums_pussel.kor(obs)
        tid_pussel = time.time() - t1
        rader = rums_pussel.logg(hist, obs)
        recept = rums_pussel.bygg_recept(hist, obs, rader)
        (ut / "recept.json").write_text(recept.model_dump_json(indent=1), encoding="utf-8")

        # Rita 2D-tidslinjekarta
        filer = []
        xs, ys = [], []
        for st in hist:
            hh = st.stråle[0]
            x0, x1, y0, y1 = hh.x["rum"][0]
            xs += [x0, x1] + [hh.x["cam"][k][0] for k in range(st.k + 1)]
            ys += [y0, y1] + [hh.x["cam"][k][1] for k in range(st.k + 1)]
        ram = (min(xs) - 0.8, max(xs) + 0.8, min(ys) - 0.8, max(ys) + 0.8)
        for st, rad in zip(hist, rader):
            K = st.k + 1
            h = next(c for c in st.stråle if rums_pussel.karna(c, obs, K) == rad["tro"])
            alt = next(
                (c for c, p in zip(st.stråle, st.sannolikhet) if p > 0.08 and rums_pussel.karna(c, obs, K) != rad["tro"]),
                None,
            )
            titel = f"{st.klipp}: {rad['tro']}\nP {rad['sannolikhet']:.2f}"
            fil = ut / f"karta_{st.klipp}.png"
            rita(h, obs, K, fil, titel, alt=alt, facit=None, ram=ram)
            filer.append(fil)
        tidslinje(filer, ut / "karta_tidslinje.png")

        print(f"\n[Lager 2: rums_pussel] ({tid_pussel:.1f} s) Sluttro: '{recept.tro}' (P={recept.sannolikhet:.2f})")
        for r in rader:
            print(f"  {r['klipp']}: {r['tro']} (P={r['sannolikhet']:.2f}) | {r['bidrag']}")
            if r["omprovning"]:
                print(f"     -> OMPRÖVNING: {r['omprovning']}")

    # --- Lager 3: Kompilera Scenpaket/2 + T1-kroppar + G1–G7 Grindar ---
    t2 = time.time()
    paket_fil = scen_brygga.kompilera_scenpaket(namn, ingest, obs, recept, ut)
    tid_brygga = time.time() - t2
    grind_data = json.loads((ut / "paket_grindar.json").read_text(encoding="utf-8"))
    print(f"\n[Lager 3: scen_brygga] ({tid_brygga:.1f} s) Scenpaket/2 + T1-armaturer + G1–G7:")
    print(f"  Paket: {paket_fil} ({paket_fil.stat().st_size // 1024} KB)")
    print(f"  Grindar sammanfattning (antal fel per grind): {grind_data['sammanfattning']}")
    print((ut / "GRINDAR.md").read_text(encoding="utf-8"))
    jamf_fil = scen_brygga.rendera_och_jamfor(ut, ingest)
    if jamf_fil:
        print(f"  Visuell jämförelse (Blender 5.2 mot original): {jamf_fil}")
    return recept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--klipp", default="nya", choices=["nya", "alla", "guacamole", "gelato", "asketch", "notan"])
    ap.add_argument("--bara-brygga", action="store_true", help="Kör bara Lager 3 på redan lösta obs.json + recept.json")
    ap.add_argument("--utan-deklaration", action="store_true", help="Ignorera handskriven deklaration.json och kör på modellbedömd semantik/1 + geometri")
    a = ap.parse_args()

    if a.klipp in ("nya", "alla", "guacamole"):
        kor_ett_klipp("guacamole", "scen/3d/ingest/ut/e-dialog-guacamole-tagningar", bara_brygga=a.bara_brygga, utan_deklaration=a.utan_deklaration)
    if a.klipp in ("nya", "alla", "gelato"):
        kor_ett_klipp("gelato", "scen/3d/ingest/ut/kand-kennysgelato-tagningar", bara_brygga=a.bara_brygga, utan_deklaration=a.utan_deklaration)
    if a.klipp in ("nya", "alla", "asketch"):
        kor_ett_klipp("asketch", "scen/3d/ingest/ut/a-sketch-servering-tagningar", bara_brygga=a.bara_brygga, utan_deklaration=a.utan_deklaration)
    if a.klipp in ("alla", "notan"):
        kor_ett_klipp(
            "notan",
            "scen/3d/ingest/ut/notan-tagningar",
            "byggsten/rumshypotes/ut/notan/vlm",
            "byggsten/rumshypotes/ut/notan/djup",
            bara_brygga=a.bara_brygga,
            utan_deklaration=a.utan_deklaration,
        )


if __name__ == "__main__":
    main()
