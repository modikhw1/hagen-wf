"""Del 2 (svar_c3_och_btilltal.py):
1. Prövar Claudes påstående C3 (MENING.md:207):
   "Lutning mätt i kameraramen mot gravitation varierar < 3° mellan tagningar för samma person (guacamole A: S1/S3/S4)."
   Vi mäter rygglutningen direkt i SAM:s kameraram mot `varld.npz["upp"]` (gravitationen i ingesten) OCH mot
   MoGe-golvnormalen (obs_motor.Tagning.u) för samma person över tagningar i guacamole (A: s1/s3/s4, B: s2/s4),
   notan (A: s1/s3/s6, B: s2/s5/s7), asketch (A: s1/s7, B: s2/s4/s5) och b-tilltal (A: s1/s2, B: s3/s4, C: s5..s11).
2. Utreder exakt varför hold-out `b-tilltal s5:C` fick `led_med = 0.1272` i G7-oberoende (är det R25, kappa eller _dra_in?).
3. Kontrollerar `gelato` diskhöjd mot Claudes P2 kamerahöjd (0.711 m).

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\svar_c3_och_btilltal.py
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
R1 = ROT / "motpart/runda-1-claude"

for p in (str(R1), str(ROT / "forvarld_karna"), str(ROT / "byggsten/brygga")):
    if p not in sys.path:
        sys.path.insert(0, p)

import g7_oberoende as G7  # noqa: E402
import obs_motor as OM  # noqa: E402

TRO_IX = {n: i for i, n in enumerate(json.loads((ROT / "scen/3d/kontrakt/tro_rigg.json").read_text(encoding="utf-8"))["namn"])}
F = np.diag([1.0, -1.0, -1.0])


def testa_c3() -> dict:
    """Mäter rygglutning (c_spine0 -> c_neck) direkt i SAM:s kameraram mot:
    (a) varld.npz["upp"] (ingestens gravitationsvektor i OpenCV-ram -> omvandlad via F till Blender-kameraram)
    (b) obs_motor.Tagning.u (MoGe golvnormal i OpenCV-ram)
    (c) paketets lutning (nivellerad kamera).
    """
    klipp_map = {**G7.KLIPP, "btilltal": "scen/3d/ingest/ut/b-tilltal-ravara-tagningar"}
    ut = {}
    sp0, neck = TRO_IX["c_spine0"], TRO_IX["c_neck"]

    for namn, ing_rel in klipp_map.items():
        ingest = ROT / ing_rel
        paket = json.loads((HIT / "metod_btilltal_ut/paket.json" if namn == "btilltal" else ROT / "forvarld_karna/ut" / namn / "paket.json").read_text(encoding="utf-8"))
        obs = json.loads((R1 / "rum_ut/med_dekl/btilltal/obs.json" if namn == "btilltal" else ROT / "forvarld_karna/ut" / namn / "obs.json").read_text(encoding="utf-8"))
        L_pak = {n: i for i, n in enumerate(paket["leder"])}
        per_person = {}

        for t in paket["tagningar"]:
            sid = t["id"]
            if not t["personer"]:
                continue
            S_dir = ingest / sid.upper()
            ok_obs = next(k for k in obs["klipp"] if k["klipp"] == sid)
            tg = G7.Tagning(ingest, ok_obs, t, paket["leder"])

            # Gravitationsvektor ur varld.npz (om den finns)
            varld_fil = S_dir / "varld.npz"
            upp_varld_cv = None
            if varld_fil.exists():
                vz = np.load(varld_fil)
                if "upp" in vz.files:
                    u = vz["upp"].astype(float).ravel()
                    upp_varld_cv = u / (np.linalg.norm(u) + 1e-9)

            # MoGe golvnormal ur obs_motor.Tagning (OpenCV-ram: x höger, y ned, z fram; u pekar uppåt -> y < 0)
            try:
                fk_om = OM._fokal(ingest)
                tag_om = OM.Tagning(S_dir, fk_om[0] if fk_om else None)
                upp_moge_cv = tag_om.u.astype(float)
                upp_moge_cv = upp_moge_cv / (np.linalg.norm(upp_moge_cv) + 1e-9)
            except Exception:
                upp_moge_cv = None

            # Konvertera gravitationsvektorer till SAM:s Blender-kameraram (F = diag(1, -1, -1)):
            # I Blender-kameraram är +Y uppåt; i OpenCV är -Y uppåt. Så F @ upp_cv har +Y > 0.
            upp_varld_bl = (F @ upp_varld_cv) if upp_varld_cv is not None else None
            if upp_varld_bl is not None and upp_varld_bl[1] < 0:
                upp_varld_bl = -upp_varld_bl
            upp_moge_bl = (F @ upp_moge_cv) if upp_moge_cv is not None else None
            if upp_moge_bl is not None and upp_moge_bl[1] < 0:
                upp_moge_bl = -upp_moge_bl

            for p in t["personer"]:
                pid = p["id"]
                spar = tg.spar_for[pid]
                q = tg.seq(spar)
                pose = q["pose"][:, :, :3] / 100.0  # Blender-kameraram (+X höger, +Y upp, -Z fram)
                rygg = pose[:, neck] - pose[:, sp0]
                rygg_u = rygg / (np.linalg.norm(rygg, axis=-1, keepdims=True) + 1e-9)

                # Lutning mot ren kamera-+Y (nivellerad)
                lut_kam_y = float(np.median(np.degrees(np.arccos(np.clip(rygg_u[:, 1], -1, 1)))))
                lut_varld = float(np.median(np.degrees(np.arccos(np.clip(rygg_u @ upp_varld_bl, -1, 1))))) if upp_varld_bl is not None else None
                lut_moge = float(np.median(np.degrees(np.arccos(np.clip(rygg_u @ upp_moge_bl, -1, 1))))) if upp_moge_bl is not None else None

                # Paketets lutning mot världens +Z
                sp_p = next(x for x in paket["rorelse"][pid] if x["tagning"] == sid)
                Xp = np.array([r[1:] for r in sp_p["rutor"]], float).reshape(len(sp_p["rutor"]), -1, 3) / 1000.0
                rv = Xp[:, L_pak["c_neck"]] - Xp[:, L_pak["c_spine0"]]
                lut_pak = float(np.median(np.degrees(np.arccos(np.clip(rv[:, 2] / (np.linalg.norm(rv, axis=-1) + 1e-9), -1, 1)))))

                per_person.setdefault(pid, {})[sid] = dict(
                    lut_paket=round(lut_pak, 1),
                    lut_kam_y=round(lut_kam_y, 1),
                    lut_varld_upp=round(lut_varld, 1) if lut_varld is not None else None,
                    lut_moge_u=round(lut_moge, 1) if lut_moge is not None else None,
                )

        # Beräkna spann per person över tagningar (minst 2 tagningar)
        spann = {}
        for pid, d in per_person.items():
            if len(d) < 2:
                continue
            spann[pid] = {}
            for m in ("lut_paket", "lut_varld_upp", "lut_moge_u"):
                vals = [v[m] for v in d.values() if v[m] is not None]
                if len(vals) >= 2:
                    spann[pid][m] = dict(min=min(vals), max=max(vals), spann_deg=round(max(vals) - min(vals), 1), per_tagn={s: v[m] for s, v in d.items()})
        ut[namn] = spann
    return ut


def utred_btilltal_s5_och_gelato_disk() -> dict:
    bt = json.loads((HIT / "metod_btilltal_ut/paket.json").read_text(encoding="utf-8"))
    s5_g7 = next(r for r in json.loads((HIT / "metod_g7_holdout_och_loco.json").read_text(encoding="utf-8"))["btilltal_holdout"]["g7_oberoende"] if r["tagning"] == "s5")
    s5_beslut = [b for b in bt["beslut"] if b.get("tagning") == "s5"]
    t5 = next(t for t in bt["tagningar"] if t["id"] == "s5")
    # Kolla om s5 hade _dra_in eller kappa eller R25
    # Kolla gelato diskhöjd i P1-P4-patchen
    gel_patch = json.loads((HIT / "metod_patch_ut/gelato/paket.json").read_text(encoding="utf-8"))
    gel_bord = [dict(id=o["id"], topp_z=round(o["pos"][2] + o["matt"][2] / 2, 3), botten_z=round(o["pos"][2] - o["matt"][2] / 2, 3))
                for o in gel_patch["objekt"] if o["typ"] == "bord"]
    gel_kam = {t["id"]: t["kamera"]["nycklar"][0][3] for t in gel_patch["tagningar"]}
    return dict(
        btilltal_s5_g7=dict(led_med=s5_g7["led_med"], bal_skift_mat=s5_g7["bal_skift_mat"],
                            bal_skift_kappa=s5_g7["bal_skift_kappa"], rest_efter_kappa=s5_g7["rest_efter_kappa"],
                            rest_vertikal=s5_g7["rest_vertikal"], kamera_z=s5_g7["kamera_z"]),
        btilltal_s5_beslut=s5_beslut,
        btilltal_s5_kam_statisk=t5["kamera"]["statisk"],
        btilltal_s5_antal_kamnycklar=len(t5["kamera"]["nycklar"]),
        gelato_patch_bord=gel_bord,
        gelato_patch_kam_z=gel_kam,
    )


def main():
    c3 = testa_c3()
    print("=== C3-MOTPROV (lutning i kameraram mot varld.npz['upp'] och MoGe-u) ===")
    for klipp, d in c3.items():
        print(f"  [{klipp}]")
        for pid, m in d.items():
            print(f"    {pid}: {json.dumps(m, ensure_ascii=False)}")
    ex = utred_btilltal_s5_och_gelato_disk()
    print("\n=== B-TILLTAL S5 & GELATO P2 KAMERA VS DISK ===")
    print(json.dumps(ex, ensure_ascii=False, indent=2))
    (HIT / "svar_c3_och_btilltal.json").write_text(json.dumps(dict(c3=c3, extra=ex), ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
