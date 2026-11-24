"""Del 1 (metod_patch_p1_p4_3d.py):
Mäter vad Claudes patch P1-P4 (motpart/runda-1-claude/g7_scen_brygga.py) faktiskt gör med 3D-världen,
och kör Claudes EGNA härdade grindar (H-serien) samt mening_rubrik på de patchade paketen.

I G7.md:197-198 skrev Claude:
  "P1 ändrar kropparnas x,y i rummet. Avstånd, bordskontakt och G4/G6 behöver prövas om av rums- och grind-lanes.
   Här är bara grindsummorna kontrollerade: G1-G4 och G6 = 0 fel i alla fyra klipp med patchen."
Det är alltså Argons blinda G1-G6 som användes för att "kontrollera" P1-P4 - inte Claudes egen H-serie!

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\metod_patch_p1_p4_3d.py
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
import types

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
R1 = ROT / "motpart/runda-1-claude"

for p in (str(R1), str(ROT / "forvarld_karna"), str(ROT / "byggsten/brygga")):
    if p not in sys.path:
        sys.path.insert(0, p)

import g7_oberoende as G7  # noqa: E402
import g7_scen_brygga as G7SB  # noqa: E402
import grind_harda as GH  # noqa: E402
import grindar as G_ORIG  # noqa: E402
import mening_rubrik as MR  # noqa: E402
from schema import Observationer, Recept  # noqa: E402

PATCH_UT = HIT / "metod_patch_ut"


def _fotavtryck_dist(xy: np.ndarray, o: dict) -> np.ndarray:
    p = np.array(o["pos"][:2], float)
    m = np.array(o["matt"][:2], float) / 2.0
    rz = float(o["rot"][2])
    R = np.array([[math.cos(rz), -math.sin(rz)], [math.sin(rz), math.cos(rz)]])
    lok = (np.asarray(xy) - p) @ R
    d = np.maximum(np.abs(lok) - m, 0.0)
    return np.linalg.norm(d, axis=-1)


def mat_3d_geometri(paket: dict) -> dict:
    """Mäter 3D-geometri: A<->B avstånd per tagning/globalt, avstånd till bord, kamerahöjd mot bord, fot-z, djup."""
    L = {n: i for i, n in enumerate(paket["leder"])}
    bord = [o for o in paket["objekt"] if o["typ"] == "bord"]
    person_pos_med = {}
    per_spar = {}

    for pid, spl in paket["rorelse"].items():
        pts_all = []
        for sp in spl:
            sid = sp["tagning"]
            X = np.array([r[1:] for r in sp["rutor"]], float).reshape(len(sp["rutor"]), -1, 3) / 1000.0
            sp2 = X[:, L["c_spine2"]]
            sp0 = X[:, L["c_spine0"]]
            pts_all.append(np.median(sp2, axis=0))
            t_obj = next(t for t in paket["tagningar"] if t["id"] == sid)
            C0 = np.array(t_obj["kamera"]["nycklar"][0][1:4], float)
            djup_med = float(np.median(np.linalg.norm(sp2[:, :2] - C0[:2], axis=-1)))
            fot_z = float(np.median(np.minimum(X[:, L["l_foot"], 2], X[:, L["r_foot"], 2])))
            bord_info = {}
            for b in bord:
                d_b = float(np.median(_fotavtryck_dist(sp0[:, :2], b)))
                topp = b["pos"][2] + b["matt"][2] / 2.0
                w_z = float(np.median(np.minimum(X[:, L["l_wrist"], 2], X[:, L["r_wrist"], 2])))
                bord_info[b["id"]] = dict(dist_xy_m=round(d_b, 3), topp_z=round(topp, 3), wrist_minus_topp_m=round(w_z - topp, 3))
            per_spar[f"{sid}:{pid}"] = dict(
                sp2_xy=[round(float(v), 3) for v in np.median(sp2[:, :2], axis=0)],
                sp2_z=round(float(np.median(sp2[:, 2])), 3),
                fot_z_med=round(fot_z, 3),
                djup_cam_xy_m=round(djup_med, 3),
                kamera_z=round(float(C0[2]), 3),
                bord=bord_info,
            )
        if pts_all:
            person_pos_med[pid] = np.median(np.array(pts_all), axis=0)

    # Avstånd A<->B i gemensamma tagningar och globalt
    ab_glob = None
    if "A" in person_pos_med and "B" in person_pos_med:
        ab_glob = round(float(np.linalg.norm(person_pos_med["A"][:2] - person_pos_med["B"][:2])), 3)
    ab_per_tagn = {}
    for t in paket["tagningar"]:
        pids = [p["id"] for p in t["personer"]]
        if "A" in pids and "B" in pids:
            pa = np.array(per_spar[f"{t['id']}:A"]["sp2_xy"])
            pb = np.array(per_spar[f"{t['id']}:B"]["sp2_xy"])
            ab_per_tagn[t["id"]] = round(float(np.linalg.norm(pa - pb)), 3)

    # Kamerahöjd under bordsskiva (t.ex. notan s7)
    kam_under_bord = []
    for t in paket["tagningar"]:
        cz = float(t["kamera"]["nycklar"][0][3])
        cxy = np.array(t["kamera"]["nycklar"][0][1:3], float)
        for b in bord:
            topp = b["pos"][2] + b["matt"][2] / 2.0
            dist = float(_fotavtryck_dist(cxy[None, :], b)[0])
            if cz < topp and dist < 1.5:
                kam_under_bord.append(dict(tagning=t["id"], kamera_z=round(cz, 3), bord=b["id"], bord_topp_z=round(topp, 3),
                                           diff_m=round(cz - topp, 3), avstand_xy_m=round(dist, 3)))

    # Bord-dimensioner & synlighet
    bord_meta = {
        b["id"]: dict(pos=b["pos"], matt=b["matt"], topp_z=round(b["pos"][2] + b["matt"][2] / 2.0, 3), synlig_ut=b["synlig_ut"])
        for b in bord
    }
    return dict(ab_glob_m=ab_glob, ab_per_tagning_m=ab_per_tagn, kam_under_bord=kam_under_bord, bord=bord_meta, per_spar=per_spar)


def main():
    PATCH_UT.mkdir(parents=True, exist_ok=True)
    orig_sub = G7SB.subprocess
    G7SB.subprocess = types.SimpleNamespace(run=lambda *a, **k: None)

    rapport = {}
    try:
        for namn, ing_rel in G7.KLIPP.items():
            ut_orig = ROT / "forvarld_karna/ut" / namn
            obs_raw = json.loads((ut_orig / "obs.json").read_text(encoding="utf-8"))
            rec_raw = json.loads((ut_orig / "recept.json").read_text(encoding="utf-8"))
            obs = Observationer.model_validate(obs_raw)
            rec = Recept.model_validate(rec_raw)
            paket_orig = json.loads((ut_orig / "paket.json").read_text(encoding="utf-8"))

            pf_patch = G7SB.kompilera_scenpaket(namn, ROT / ing_rel, obs, rec, PATCH_UT / namn)
            paket_patch = json.loads(pf_patch.read_text(encoding="utf-8"))

            # Kör H-serien på BÅDE original och patchat paket!
            ktx = GH.las_kontext(namn)
            h_orig_r = GH.mat(paket_orig, ktx)
            h_patch_r = GH.mat(paket_patch, ktx)
            h_orig_s = GH.sammanfatta(h_orig_r)
            h_patch_s = GH.sammanfatta(h_patch_r)

            # Kör G1-G7 (per person) på båda
            g_orig_pp = G_ORIG.sammanfatta(G7.grindar_per_person(paket_orig))
            g_patch_pp = G_ORIG.sammanfatta(G7.grindar_per_person(paket_patch))

            # Detaljerade H-diffar (nya H-fel som patchen SKAPAR vs fel som patchen LÖSER)
            nya_h_fel, losta_h_fel = [], []
            h_orig_map = {(r["tagning"], r.get("person")): r for r in h_orig_r}
            for r in h_patch_r:
                key = (r["tagning"], r.get("person"))
                o = h_orig_map.get(key, {})
                for g in GH.H_GRINDAR:
                    ov = (o.get(g) or {}).get("ok")
                    pv = (r.get(g) or {}).get("ok")
                    if pv is False and ov is not False:
                        nya_h_fel.append(dict(tagning=key[0], person=key[1], grind=g, fore=o.get(g), efter=r.get(g)))
                    elif ov is False and pv is not False:
                        losta_h_fel.append(dict(tagning=key[0], person=key[1], grind=g, fore=o.get(g), efter=r.get(g)))

            # 3D-geometri före vs efter
            geo_orig = mat_3d_geometri(paket_orig)
            geo_patch = mat_3d_geometri(paket_patch)

            # Kroppsförskjutning (XY) i världen mellan original och patch per spår
            flytt_3d = {}
            for k_sp, v_p in geo_patch["per_spar"].items():
                v_o = geo_orig["per_spar"][k_sp]
                dxy = math.dist(v_p["sp2_xy"], v_o["sp2_xy"])
                dz_kam = round(v_p["kamera_z"] - v_o["kamera_z"], 3)
                ddjup = round(v_p["djup_cam_xy_m"] - v_o["djup_cam_xy_m"], 3)
                flytt_3d[k_sp] = dict(kropp_flytt_xy_m=round(dxy, 3), djup_fore_m=v_o["djup_cam_xy_m"],
                                      djup_efter_m=v_p["djup_cam_xy_m"], djup_delta_m=ddjup,
                                      kamera_z_fore=v_o["kamera_z"], kamera_z_efter=v_p["kamera_z"], kamera_z_delta=dz_kam)

            # R1-beslut före vs efter (döljer P1-P4 FLER eller FÄRRE bord?)
            r1_orig = [b for b in paket_orig["beslut"] if b["regel"].startswith("R1_")]
            r1_patch = [b for b in paket_patch["beslut"] if b["regel"].startswith("R1_")]

            rapport[namn] = dict(
                g_per_person_fore=g_orig_pp,
                g_per_person_efter=g_patch_pp,
                h_fore=h_orig_s,
                h_efter=h_patch_s,
                h_sum_fore=sum(h_orig_s.values()),
                h_sum_efter=sum(h_patch_s.values()),
                nya_h_fel=nya_h_fel,
                losta_h_fel=losta_h_fel,
                ab_glob_fore_efter=[geo_orig["ab_glob_m"], geo_patch["ab_glob_m"]],
                ab_per_tagning_fore_efter=[geo_orig["ab_per_tagning_m"], geo_patch["ab_per_tagning_m"]],
                kam_under_bord_efter=geo_patch["kam_under_bord"],
                r1_dolda_fore_efter=[len(r1_orig), len(r1_patch)],
                flytt_3d=flytt_3d,
                geo_fore=geo_orig,
                geo_efter=geo_patch,
            )
            print(f"\n=== {namn} ===")
            print(f"  G per person: före={g_orig_pp} -> efter={g_patch_pp}")
            print(f"  H-summa: före={sum(h_orig_s.values())} -> efter={sum(h_patch_s.values())}")
            print(f"  H före : { {k:v for k,v in h_orig_s.items() if v} }")
            print(f"  H efter: { {k:v for k,v in h_patch_s.items() if v} }")
            print(f"  NYA H-fel skapade av P1-P4 ({len(nya_h_fel)}):")
            for nf in nya_h_fel:
                print(f"    + {nf['tagning']}:{nf['person']} {nf['grind']}: {nf['efter']}")
            print(f"  Lösta H-fel ({len(losta_h_fel)}):")
            for lf in losta_h_fel:
                print(f"    - {lf['tagning']}:{lf['person']} {lf['grind']}")
            print(f"  A<->B glob: {geo_orig['ab_glob_m']} -> {geo_patch['ab_glob_m']} | per_tagn: {geo_orig['ab_per_tagning_m']} -> {geo_patch['ab_per_tagning_m']}")
            if geo_patch["kam_under_bord"]:
                print(f"  KAMERA UNDER BORDSSKIVA: {geo_patch['kam_under_bord']}")
            for k_sp, fv in flytt_3d.items():
                if fv["kropp_flytt_xy_m"] > 0.05 or abs(fv["kamera_z_delta"]) > 0.01:
                    print(f"    3D-flytt {k_sp}: xy={fv['kropp_flytt_xy_m']}m, djup={fv['djup_fore_m']}->{fv['djup_efter_m']} ({fv['djup_delta_m']:+.3f}m), kam_z={fv['kamera_z_fore']}->{fv['kamera_z_efter']}")
    finally:
        G7SB.subprocess = orig_sub

    (HIT / "metod_patch_p1_p4_3d.json").write_text(
        json.dumps(rapport, ensure_ascii=False, indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)),
        encoding="utf-8",
    )
    print("\nSparade:", HIT / "metod_patch_p1_p4_3d.json")


if __name__ == "__main__":
    main()
