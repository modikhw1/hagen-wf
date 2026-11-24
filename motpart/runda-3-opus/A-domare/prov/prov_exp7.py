# -*- coding: utf-8 -*-
"""Prövning av Neons Exp 7 ("Blind C / Regelpipe v7 = 4,1 cm MAE").

Fem kontroller, alla körbara utan nya API-anrop:
  1. Facitets härkomst: var kommer varje facitvärde ifrån? (sök i runda-2 efter härledning)
  2. Systemvärdenas härkomst: är Argons värden i tabellen de som står i Argons filer?
  3. Finns regelpipen v6/v7 och de blinda agenternas svar som filer? (krävs för V5)
  4. Facitets egen osäkerhet: känslighet i den antropometriska härledningen av arbetsbänken
  5. Upplösning: ligger skillnaderna mellan "systemen" innanför facitets egna intervall?

Kör: python prov_exp7.py -> prov_exp7.json
"""
from __future__ import annotations

import itertools
import json
import re
from pathlib import Path

import numpy as np

HIT = Path(__file__).resolve().parent
ROT = HIT.parents[3]
R2 = ROT / "motpart/runda-2-neon"
FK = ROT / "forvarld_karna/ut"

GT = {"guac_worktop_m": 0.90, "guac_upper_bar_m": 1.11, "guac_barstool_m": 0.75, "guac_ab_m": 1.73,
      "gel_pan_deck_m": 0.88, "gel_sneeze_top_m": 1.20, "gel_cam_h_m": 1.38}
ARGON_I_TABELLEN = {"guac_worktop_m": 0.78, "guac_upper_bar_m": 0.78, "guac_barstool_m": 0.45, "guac_ab_m": 1.73,
                    "gel_pan_deck_m": 0.72, "gel_sneeze_top_m": 0.72, "gel_cam_h_m": 1.30}
BLIND = {
    "A_rabild": {"guac_worktop_m": 0.88, "guac_upper_bar_m": 1.13, "guac_barstool_m": 0.75, "guac_ab_m": 1.25,
                 "gel_pan_deck_m": 0.90, "gel_sneeze_top_m": 1.31, "gel_cam_h_m": 1.51},
    "B_v6": {"guac_worktop_m": 0.90, "guac_upper_bar_m": 1.10, "guac_barstool_m": 0.75, "guac_ab_m": 1.25,
             "gel_pan_deck_m": 0.95, "gel_sneeze_top_m": 1.26, "gel_cam_h_m": 1.45},
    "C_v7": {"guac_worktop_m": 0.89, "guac_upper_bar_m": 1.14, "guac_barstool_m": 0.78, "guac_ab_m": 1.57,
             "gel_pan_deck_m": 0.88, "gel_sneeze_top_m": 1.22, "gel_cam_h_m": 1.42},
}
# Neons egna intervall där de finns (djup_ground_truth_audit.py:276-277, 302-303)
NEON_INTERVALL = {"guac_worktop_m": (0.86, 0.94), "guac_upper_bar_m": (1.06, 1.16),
                  "gel_pan_deck_m": (0.85, 0.92), "gel_sneeze_top_m": (1.15, 1.25)}


def grep(monster: str, filer):
    ut = []
    for f in filer:
        for i, rad in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if re.search(monster, rad):
                ut.append(f"{f.relative_to(ROT).as_posix()}:{i}: {rad.strip()[:150]}")
    return ut


def main():
    filer = sorted(list(R2.glob("*.py")) + list(R2.glob("*.md")) + list(R2.glob("*.json")))
    ut = {}

    # 1. härkomst för facit
    sok = {"guac_worktop_m": r"0[.,]90\b|verklig_lag_arbetsbank", "guac_upper_bar_m": r"1[.,]11\b",
           "guac_barstool_m": r"0[.,]75\b.*(stol|säte|barstol)|barstol.*0[.,]75",
           "guac_ab_m": r"1[.,]73\b", "gel_pan_deck_m": r"0[.,]88\b|kantinkant",
           "gel_sneeze_top_m": r"1[.,]20\b|glasmonter_topp", "gel_cam_h_m": r"1[.,]38\b"}
    ut["1_facit_harkomst_traffar"] = {k: grep(m, filer)[:12] for k, m in sok.items()}
    ut["1_facit_klassning"] = {
        "guac_worktop_m": "härlett: B:s huvud 107 px, bänk 3,80 huvudhöjder under hjässan, ANTAGEN längd 1,75-1,85 m och 7,6 huvudhöjder (djup_ground_truth_audit.py:259-265)",
        "guac_upper_bar_m": "ögonmått: 'tydligt ~20-25 cm ovanför den vita arbetsbänken' (djup_ground_truth_audit.py:266); ingen beräkning",
        "guac_barstool_m": "antagande: 'A sitter på hög barstol (~0.75 m säte)' (djup_ground_truth_audit.py:266); ingen mätning",
        "guac_ab_m": "modellutdata ur gamla kedjans inpassning (scen/3d/PIPE.md:50, passa_deklaration), inte ett fysiskt ankare",
        "gel_pan_deck_m": "intervall [0.85, 0.88, 0.92] utan härledning (djup_ground_truth_audit.py:302)",
        "gel_sneeze_top_m": "intervall [1.15, 1.20, 1.25] utan härledning (djup_ground_truth_audit.py:301)",
        "gel_cam_h_m": "förekommer bara som konstant i djup_blind_eval.py:34; ingen härledning någonstans i runda 2",
    }

    # 2. Argons värden i tabellen mot Argons filer
    def topp(paket, oid):
        for o in paket["objekt"]:
            if o["id"] == oid:
                return round(o["pos"][2] + o["matt"][2] / 2, 3)
    pg = json.loads((FK / "guacamole/paket.json").read_text(encoding="utf-8"))
    pe = json.loads((FK / "gelato/paket.json").read_text(encoding="utf-8"))
    rg = json.loads((FK / "guacamole/recept.json").read_text(encoding="utf-8"))
    pers = {n["id"]: n for n in rg["noder"] if n.get("klass") == "person"}
    ab_recept = float(np.linalg.norm(np.array(pers["A"]["position"][:2]) - np.array(pers["B"]["position"][:2])))
    L = {n: i for i, n in enumerate(pg["leder"])}
    pos = {}
    for pid, spl in pg["rorelse"].items():
        for sp in spl:
            if sp["tagning"] == "s4":
                X = np.array(sp["rutor"][len(sp["rutor"]) // 2][1:], float).reshape(-1, 3) / 1000
                pos[pid] = X[L["c_spine0"]]
    ab_paket = float(np.linalg.norm(pos["A"][:2] - pos["B"][:2]))
    kam = {t["id"]: t["kamera"]["nycklar"][0][3] for t in pe["tagningar"]}
    argon_filer = {
        "guac_worktop_m": topp(pg, "bord_1"), "guac_upper_bar_m": topp(pg, "bord_1"),
        "guac_barstool_m": topp(pg, "stol_A"), "guac_ab_m": round(ab_recept, 3),
        "gel_pan_deck_m": topp(pe, "bord_1"), "gel_sneeze_top_m": topp(pe, "bord_1"),
        "gel_cam_h_m": round(kam["s1"], 3),
    }
    ut["2_argon_tabell_mot_filer"] = {
        k: {"tabell": ARGON_I_TABELLEN[k], "fil": argon_filer[k],
            "stammer": abs(ARGON_I_TABELLEN[k] - argon_filer[k]) < 0.015} for k in GT}
    ut["2_argon_ab_paket_s4"] = round(ab_paket, 3)
    ut["2_argon_kamera_per_tagning_gelato"] = {k: round(v, 3) for k, v in kam.items()}
    fel_tab = [abs(ARGON_I_TABELLEN[k] - GT[k]) * 100 for k in GT]
    fel_fil = [abs(argon_filer[k] - GT[k]) * 100 for k in GT]
    ut["2_argon_MAE_cm"] = {"enligt_tabellen": round(float(np.mean(fel_tab)), 1),
                            "med_varden_ur_filerna": round(float(np.mean(fel_fil)), 1)}

    # 3. finns regelpipen och de blinda svaren?
    alla = [p for p in R2.rglob("*") if p.is_file() and p.suffix in {".md", ".py", ".json", ".txt"}]
    ut["3_regelpipe"] = {
        "filer_som_namner_Regelpipe": sorted({t.split(':')[0] for t in grep(r"[Rr]egelpipe", alla)}),
        "traffar_Regel_1_till_4": grep(r"Regel [1-4]\b", alla)[:10],
        "filer_med_blinda_agentsvar": sorted({p.relative_to(ROT).as_posix() for p in alla if re.search(r"blind", p.name, re.I)}),
        "systemvarden_i_djup_blind_eval": "hårdkodade konstanter, djup_blind_eval.py:41-103 ('Exakta uppmätta / ordagranna blinda svar')",
    }

    # 4. känslighet i arbetsbänkens antropometri
    ratio = 3.80  # huvudhöjder från hjässa till bänk (Neons mätning)
    rader = []
    for Hm, k, luta in itertools.product(np.linspace(1.69, 1.92, 6), np.linspace(7.0, 8.0, 6), np.linspace(0.0, 0.10, 6)):
        rader.append((Hm - luta) - ratio * Hm / k)
    rader = np.array(rader)
    ut["4_arbetsbank_kanslighet"] = {
        "antaganden": "längd 1,69-1,92 m (svenska män ~p05-p95), 7,0-8,0 huvudhöjder per kropp, hjässan 0-10 cm lägre av framåtlutning (B lutar sig fram i S4, se prov/rutor/guac_S4_r244_rutnat.png)",
        "intervall_m": [round(float(rader.min()), 3), round(float(rader.max()), 3)],
        "p05_p95_m": [round(float(np.percentile(rader, 5)), 3), round(float(np.percentile(rader, 95)), 3)],
        "neons_intervall_m": [0.86, 0.94],
        "ej_medraknat": "perspektiv: hjässa och händer ligger på olika avstånd från en uppåtriktad kamera",
    }

    # 5. upplösning: ligger blindvärdena inom Neons egna facitintervall?
    res = {}
    for namn, v in BLIND.items():
        inne = {k: NEON_INTERVALL[k][0] <= v[k] <= NEON_INTERVALL[k][1] for k in NEON_INTERVALL}
        res[namn] = {"inom_neons_intervall": inne, "antal_inom": sum(inne.values())}
    ut["5_upplosning"] = res
    ut["5_skillnad_A_mot_C_cm"] = {k: round(abs(BLIND["A_rabild"][k] - BLIND["C_v7"][k]) * 100, 1) for k in GT}

    (HIT / "prov_exp7.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in ut.items() if not k.startswith("1_facit_harkomst")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
