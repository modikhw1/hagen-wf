"""Del 1 (metod_grind_mutation_audit.py):
Granskar Claudes GRINDAR-MUTATION.md, grind_mutation.py och H-serien (grind_harda.py):
1. Kvantifierar F-nämnarkrympningen i H-serien (hur 29-52% av baslinjen kastas ut som F innan
   känsligheten mäts, t.ex. H3_hallning F11/21, H4_genom F10/21, H10_kamera F11/21).
2. Provar REALISTISKA / MJUKA varianter av mutationerna (istället för specialkonstruerade fel):
   - Mjuk partiell sänkning (cosinus-ramp i första 40% av rutorna, inte ett 0.4 m hack i en enda ruta!)
     -> slutar H12_kontinuitet (som gav 21/21 på Claudes skarpa stegfunktion) helt att larma?
   - Uppströms systematiskt SAM-djupfel (+25% / +0.5 m i både obs och paket, dvs. före obs_motor):
     -> är H9, H14 och H15 lika blinda mot uppströms SAM-fel som Argons G7 var?
   - Mindre, realistiska felstorlekar (sänk 15 cm, vrid 35°, kamera 0.35 m i sidled, teleportering 0.25 m)
     -> hur ser H-seriens faktiska detektionskurva ut mot Claudes extrema (0.4-3.0 m, 180°)?
3. Analyserar falsklarm / blinda fläckar för H-serien på hold-out-klippet `b-tilltal` (11 tagningar)
   och jämför med G7-oberoende (t.ex. b-tilltal s5:C där G7-oberoende ger FEL 0.127 men H7_2d = OK!).

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\metod_grind_mutation_audit.py
"""
from __future__ import annotations

import copy
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

import grind_harda as GH  # noqa: E402
import grind_mutation as GM  # noqa: E402
import grindar as G_ORIG  # noqa: E402


def analysera_f_krympning() -> dict:
    """Läser runda-1-claude/grind_resultat.json och redovisar exakt hur stor andel av målen som kastas som F i H-serien."""
    data = json.loads((R1 / "grind_resultat.json").read_text(encoding="utf-8"))
    ut = {}
    for lage in ("a", "b"):
        rr = [r for r in data["resultat"] if r["lage"] == lage and not r.get("fel")]
        m_h = GM.matris(rr, GH.H_GRINDAR, "H")
        # Ta kroppsmutationerna (n=21) som referens
        kropps_f = {}
        for g in GH.H_GRINDAR:
            c = m_h["sank_04"][g]
            kropps_f[g] = dict(F=c["F"], n=c["n"], andel_F_pct=round(100.0 * c["F"] / c["n"], 1))
        ut[f"lage_{lage}_sank_04_F"] = {k: v for k, v in kropps_f.items() if v["F"] > 0}
        # Räkna hur många totala (mut, mål, grind)-celler som är F i H vs G
        h_f_tot = sum(1 for r in rr for g, v in r["H"].items() if v == "F")
        h_tot = sum(len(r["H"]) for r in rr)
        g_f_tot = sum(1 for r in rr for g, v in r["G"].items() if v == "F")
        g_tot = sum(len(r["G"]) for r in rr)
        ut[f"lage_{lage}_totalt"] = dict(
            H_F_celler=f"{h_f_tot}/{h_tot} ({100.0*h_f_tot/h_tot:.1f}%)",
            G_F_celler=f"{g_f_tot}/{g_tot} ({100.0*g_f_tot/g_tot:.1f}%)",
        )
    return ut


def testa_mjuka_och_mindre_mutationer() -> dict:
    """Kör realistiska varianter mot G1-G7 och H-serien i läge a på alla 21 spår i de 4 klippen."""
    klipp_lista = list(GH.INGEST)
    paket_map = {k: GM.las_paket(k) for k in klipp_lista}
    ktx_map = {k: GH.las_kontext(k) for k in klipp_lista}
    bas_g = {k: GM.g_status(paket_map[k])[0] for k in klipp_lista}
    bas_h = {k: GM.h_status(paket_map[k], ktx_map[k])[0] for k in klipp_lista}

    # Test 1: Mjuk partiell sänkning (-0.4 m i första 40% av rutorna men med 10-rutors cosinus-ramp -> inget oändligt hack)
    # Test 2: Mildare sänkning (-0.15 m i alla rutor)
    # Test 3: Vridning 45° (istället för 180°)
    # Test 4: Mjuk drift 0.25 m i sidled under andra halvan (istället för 1.5 m omedelbar teleportering)
    # Test 5: Uppströms korrelerat djupfel (+0.45 m i kamerans blickriktning BÅDE i paket och i obs["djup_m"] -> testar om H14/H9/H15 är blinda!)
    scenarier = [
        "sank_04_mjuk_ramp_40pct",
        "sank_015_alla",
        "vand_45_deg",
        "drift_025_mjuk_halv",
        "uppstroms_sam_djup_plus_045m",
    ]
    resultat = {s: dict(n=0, nagon_G=0, nagon_H=0, H_per_grind={g: 0 for g in GH.H_GRINDAR}, F_per_grind={g: 0 for g in GH.H_GRINDAR}) for s in scenarier}

    for k in klipp_lista:
        p0 = paket_map[k]
        ktx0 = ktx_map[k]
        L = {n: i for i, n in enumerate(p0["leder"])}
        for pid, spl in p0["rorelse"].items():
            for i_sp, sp0 in enumerate(spl):
                sid = sp0["tagning"]
                t_obj = GM.tagning(p0, sid)
                _, R_kam = GM.kam_axlar_paket(t_obj)
                kam_x = GM.horisontell(R_kam[:, 0])
                kam_fram = GM.horisontell(-R_kam[:, 2])
                X0, U = GM.spar_X(sp0)
                T = len(U)
                mal = dict(mut="custom", tagning=sid, pid=pid)

                for sc in scenarier:
                    pm = copy.deepcopy(p0)
                    ktx_m = ktx0
                    X = X0.copy()
                    if sc == "sank_04_mjuk_ramp_40pct":
                        # Sänkt 0.4 m i början, mjuk cosinus-ramp tillbaka till 0 före mittrutan (ruta 0.45*T)
                        cut = max(3, int(0.32 * T))
                        ramp = max(4, int(0.13 * T))
                        w = np.zeros(T)
                        w[:cut] = 1.0
                        if cut + ramp <= T:
                            w[cut:cut + ramp] = 0.5 * (1.0 + np.cos(np.linspace(0, math.pi, ramp)))
                        X[:, :, 2] -= 0.40 * w[:, None]
                    elif sc == "sank_015_alla":
                        X[:, :, 2] -= 0.15
                    elif sc == "vand_45_deg":
                        piv = X[:, L["c_spine2"]:L["c_spine2"] + 1, :]
                        M = GM.Rz(math.radians(45.0))
                        X = (X - piv) @ M.T + piv
                    elif sc == "drift_025_mjuk_halv":
                        ramp = np.linspace(0.0, 1.0, T - T // 2)
                        shift = np.zeros((T, 3))
                        shift[T // 2:] = (0.25 * ramp)[:, None] * kam_x[None, :]
                        X = X + shift[:, None, :]
                    elif sc == "uppstroms_sam_djup_plus_045m":
                        # Simulerar ett systematiskt SAM-djupfel på +0.45 m som kommer IN före både obs_motor och scen_brygga!
                        X = X + 0.45 * kam_fram[None, None, :]
                        ktx_m = copy.deepcopy(ktx0)
                        for kl in ktx_m["obs"]["klipp"]:
                            if kl["klipp"] == sid:
                                for d in kl["detektioner"]:
                                    if d["klass"] == "person" and (d["nyckel"] == f"person:{pid}" or d["nyckel"] == "person:okand"):
                                        d["djup_m"]["v"] = round(d["djup_m"]["v"] + 0.45, 3)

                    GM.skriv_X(pm["rorelse"][pid][i_sp], X, U)
                    gm, _ = GM.g_status(pm)
                    hm, _ = GM.h_status(pm, ktx_m)
                    jg = GM.jamfor(bas_g[k], gm, GM.G_GRINDAR, mal)
                    jh = GM.jamfor(bas_h[k], hm, GH.H_GRINDAR, mal)
                    rec = resultat[sc]
                    rec["n"] += 1
                    if any(v == "L" for v in jg.values()):
                        rec["nagon_G"] += 1
                    if any(v == "L" for v in jh.values()):
                        rec["nagon_H"] += 1
                    for g in GH.H_GRINDAR:
                        if jh[g] == "L":
                            rec["H_per_grind"][g] += 1
                        elif jh[g] == "F":
                            rec["F_per_grind"][g] += 1

    # Komprimera utskriften
    kompakt = {}
    for sc, rec in resultat.items():
        kompakt[sc] = dict(
            n=rec["n"],
            nagon_G=f"{rec['nagon_G']}/{rec['n']}",
            nagon_H=f"{rec['nagon_H']}/{rec['n']}",
            H_aktiva={g: f"{rec['H_per_grind'][g]}/{rec['n'] - rec['F_per_grind'][g]} (F{rec['F_per_grind'][g]})"
                      for g in GH.H_GRINDAR if rec["H_per_grind"][g] > 0 or g in ("H2_golv", "H7_2d", "H12_kontinuitet", "H14_djup", "H15_vridning")},
        )
    return kompakt


def granska_btilltal_h_blinda_flackar() -> dict:
    """Kontrollerar exakt varför H7_2d missade b-tilltal s5:C (där G7-oberoende gav led_med=0.1272!)
    och varför H4_genom gav 6 fel medan H1_objekt gav 0 fel på b-tilltal."""
    bt_data = json.loads((HIT / "metod_g7_holdout_och_loco.json").read_text(encoding="utf-8"))["btilltal_holdout"]
    s5_g7 = next(r for r in bt_data["g7_oberoende"] if r["tagning"] == "s5")
    s5_h = next(r for r in bt_data["h_rader_full"] if r["tagning"] == "s5")
    # Kolla vilka tagningar varje bord har i receptet för b-tilltal
    rec = json.loads((R1 / "rum_ut/med_dekl/btilltal/recept.json").read_text(encoding="utf-8"))
    bord_ev = {n["id"]: n.get("evidence_shots") for n in rec["noder"] if n["klass"] == "bord"}
    paket = json.loads((HIT / "metod_btilltal_ut/paket.json").read_text(encoding="utf-8"))
    r1_beslut = [b for b in paket["beslut"] if b["regel"].startswith("R1_")]
    return dict(
        s5_g7=dict(led_med=s5_g7["led_med"], i_mask=s5_g7["i_mask"], i_box=s5_g7["i_box"], flaggad=s5_g7["flaggad"], skal=s5_g7["skal"]),
        s5_H7_2d=s5_h["H7_2d"],
        s5_H1_objekt=s5_h["H1_objekt"],
        s5_H4_genom=s5_h["H4_genom"],
        btilltal_bord_evidence_shots=bord_ev,
        btilltal_r1_beslut=r1_beslut,
    )


def main():
    f_res = analysera_f_krympning()
    print("=== 1. F-NÄMNARKRYMPNING I H-SERIEN ===")
    print(json.dumps(f_res, ensure_ascii=False, indent=2))

    mjuk = testa_mjuka_och_mindre_mutationer()
    print("\n=== 2. REALISTISKA / MJUKA MUTATIONER MOT G1-G7 OCH H-SERIEN ===")
    print(json.dumps(mjuk, ensure_ascii=False, indent=2))

    bt_h = granska_btilltal_h_blinda_flackar()
    print("\n=== 3. H-SERIENS BLINDA FLÄCKAR OCH KONFLIKTER PÅ HOLD-OUT B-TILLTAL ===")
    print(json.dumps(bt_h, ensure_ascii=False, indent=2))

    out = dict(f_krympning=f_res, mjuka_mutationer=mjuk, btilltal_h=bt_h)
    (HIT / "metod_grind_mutation_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nSparade:", HIT / "metod_grind_mutation_audit.json")


if __name__ == "__main__":
    main()
