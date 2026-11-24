"""rum_verifiera.py — kopia av forvarld_karna/verifiera.py (Argon, 19 nov 00:57) med egen utmapp.

Syfte (motpart runda 1, lane A5): köra om Lager 1 (obs_motor) + Lager 2 (rums_pussel) utan att
skriva över Argons lagrade utdata i forvarld_karna/ut/.

Ändringar mot originalet (allt annat är ordagrant samma anropskedja):
1. Kärnmodulerna importeras från <rot>/forvarld_karna (filen ligger i motpart/runda-1-claude/).
   sys.path-ordningen är densamma som i originalet (forvarld_karna, sedan byggsten/rumshypotes först).
2. Utdata skrivs till --ut (standard motpart/runda-1-claude/rum_ut/<läge>/<klipp>/).
3. Lager 3 (scen_brygga) körs bara med --lager3, Blender-rendering bara med --rendera.
4. 2D-kartorna ritas bara med --kartor (de påverkar inte obs.json/recept.json).
5. --klipp btilltal (hold-out: scen/3d/ingest/ut/b-tilltal-ravara-tagningar) är tillagt.
6. Tider, sluttro och modulsökvägar skrivs till <ut>/<klipp>/rum_korning.json.

    $env:PYTHONIOENCODING="utf-8"
    scen\\.venv\\Scripts\\python.exe motpart\\runda-1-claude\\rum_verifiera.py --klipp alla --utan-deklaration
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
KARNA = ROT / "forvarld_karna"
sys.path.insert(0, str(KARNA))
sys.path.insert(0, str(ROT / "byggsten/rumshypotes"))

import obs_motor  # noqa: E402
import regler  # noqa: E402
import rums_pussel  # noqa: E402
from schema import Observationer, Recept  # noqa: E402

KLIPP = {
    "guacamole": ("scen/3d/ingest/ut/e-dialog-guacamole-tagningar", None, None),
    "gelato": ("scen/3d/ingest/ut/kand-kennysgelato-tagningar", None, None),
    "asketch": ("scen/3d/ingest/ut/a-sketch-servering-tagningar", None, None),
    "notan": (
        "scen/3d/ingest/ut/notan-tagningar",
        "byggsten/rumshypotes/ut/notan/vlm",
        "byggsten/rumshypotes/ut/notan/djup",
    ),
    "btilltal": ("scen/3d/ingest/ut/b-tilltal-ravara-tagningar", None, None),
}


def kor_ett_klipp(namn, ingest_rel, vlm_rel, djup_rel, ut_rot: pathlib.Path, utan_deklaration: bool,
                  lager3: bool, rendera: bool, kartor: bool):
    print("=" * 76)
    print(f"KLIPP: {namn} ({ingest_rel}){' [UTAN DEKLARATION.JSON]' if utan_deklaration else ''}")
    print("=" * 76)
    ingest = ROT / ingest_rel
    vlm = (ROT / vlm_rel) if vlm_rel else None
    djup = (ROT / djup_rel) if djup_rel else None
    ut = ut_rot / namn
    ut.mkdir(parents=True, exist_ok=True)

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
    print(f"\n[Lager 2: rums_pussel] ({tid_pussel:.1f} s) Sluttro: '{recept.tro}' (P={recept.sannolikhet:.2f})")
    for r in rader:
        print(f"  {r['klipp']}: {r['tro']} (P={r['sannolikhet']:.2f}) | {r['bidrag']}")
        if r["omprovning"]:
            print(f"     -> OMPRÖVNING: {r['omprovning']}")

    if kartor:
        from karta import rita, tidslinje  # noqa: E402  (byggsten/rumshypotes/karta.py, som i originalet)
        filer, xs, ys = [], [], []
        for st in hist:
            hh = st.stråle[0]
            x0, x1, y0, y1 = hh.x["rum"][0]
            xs += [x0, x1] + [hh.x["cam"][k][0] for k in range(st.k + 1)]
            ys += [y0, y1] + [hh.x["cam"][k][1] for k in range(st.k + 1)]
        ram = (min(xs) - 0.8, max(xs) + 0.8, min(ys) - 0.8, max(ys) + 0.8)
        for st, rad in zip(hist, rader):
            K = st.k + 1
            h = next(c for c in st.stråle if rums_pussel.karna(c, obs, K) == rad["tro"])
            alt = next((c for c, p in zip(st.stråle, st.sannolikhet)
                        if p > 0.08 and rums_pussel.karna(c, obs, K) != rad["tro"]), None)
            fil = ut / f"karta_{st.klipp}.png"
            rita(h, obs, K, fil, f"{st.klipp}: {rad['tro']}\nP {rad['sannolikhet']:.2f}", alt=alt, facit=None, ram=ram)
            filer.append(fil)
        tidslinje(filer, ut / "karta_tidslinje.png")

    korning = dict(
        klipp=namn, ingest=ingest_rel, utan_deklaration=utan_deklaration,
        tid_obs_s=round(tid_obs, 2), tid_pussel_s=round(tid_pussel, 2),
        tro=recept.tro, sannolikhet=recept.sannolikhet,
        moduler={m: str(pathlib.Path(sys.modules[m].__file__).resolve())
                 for m in ("obs_motor", "rums_pussel", "regler", "schema")},
        regler_R_vid_avstand_m=regler.R["vid_avstand_m"],
    )
    if lager3:
        import scen_brygga  # noqa: E402
        t2 = time.time()
        paket_fil = scen_brygga.kompilera_scenpaket(namn, ingest, obs, recept, ut)
        grind = json.loads((ut / "paket_grindar.json").read_text(encoding="utf-8"))
        korning["tid_brygga_s"] = round(time.time() - t2, 2)
        korning["grindar"] = grind.get("sammanfattning")
        print(f"\n[Lager 3] {paket_fil} grindar: {grind.get('sammanfattning')}")
        if rendera:
            scen_brygga.rendera_och_jamfor(ut, ingest)
    (ut / "rum_korning.json").write_text(json.dumps(korning, ensure_ascii=False, indent=1), encoding="utf-8")
    return recept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--klipp", default="alla", choices=["alla", "guacamole", "gelato", "asketch", "notan", "btilltal"])
    ap.add_argument("--utan-deklaration", action="store_true")
    ap.add_argument("--ut", default=None, help="utrot (standard rum_ut/<med|utan>_dekl)")
    ap.add_argument("--lager3", action="store_true")
    ap.add_argument("--rendera", action="store_true")
    ap.add_argument("--kartor", action="store_true")
    a = ap.parse_args()
    ut_rot = pathlib.Path(a.ut) if a.ut else HIT / "rum_ut" / ("utan_dekl" if a.utan_deklaration else "med_dekl")
    ordning = ["guacamole", "gelato", "asketch", "notan"] if a.klipp == "alla" else [a.klipp]
    for n in ordning:
        ing, v, d = KLIPP[n]
        kor_ett_klipp(n, ing, v, d, ut_rot, a.utan_deklaration, a.lager3, a.rendera, a.kartor)


if __name__ == "__main__":
    main()
