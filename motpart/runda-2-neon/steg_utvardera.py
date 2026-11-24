"""Del 3 (steg_utvardera.py):
Kör vår förregistrerade prototyp `steg_scen_brygga.py` (S1-S5) + `steg_manus_och_media.py` på samtliga 5 klipp
(guacamole, gelato, asketch, notan + osedda 11-tagningars hold-out b-tilltal), mäter resultatet med:
  - Claudes G7-oberoende
  - Claudes H-serie (grind_harda.py)
  - Claudes automatiska rubrik (mening_rubrik.py)
  - Våra 4 nya mått N1-N4 (med felinjektionsprov!)
  - Blender 5.2-rendering + 2D-överlägg för visuell kontroll av guacamole, gelato, notan och asketch
och jämför utfallet ärligt mot de förregistrerade förutsägelserna i `steg_forutsagelse.json`.

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\steg_utvardera.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import types

import cv2
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
R1 = ROT / "motpart/runda-1-claude"

for p in (str(HIT), str(R1), str(ROT / "forvarld_karna"), str(ROT / "byggsten/brygga")):
    if p not in sys.path:
        sys.path.insert(0, p)

# 1. Generera steg_scen_brygga.py och steg_scen_brygga.diff
subprocess.run([sys.executable, str(HIT / "steg_bygg_patch.py")], check=True)

import g7_oberoende as G7  # noqa: E402
import grind_harda as GH  # noqa: E402
import mening_gemensamt as MG  # noqa: E402
import mening_rubrik as MR  # noqa: E402
import steg_manus_och_media as SM  # noqa: E402
import steg_scen_brygga as SSB  # noqa: E402
from schema import Observationer, Recept  # noqa: E402

STEG_UT = HIT / "steg_ut"

KLIPP_SPEC = {
    "guacamole": (
        ROT / "scen/3d/ingest/ut/e-dialog-guacamole-tagningar",
        ROT / "forvarld_karna/ut/guacamole",
        ROT / "scen/3d/ingest/ut/e-dialog-guacamole-tagningar/semantik/semantik.json",
    ),
    "gelato": (
        ROT / "scen/3d/ingest/ut/kand-kennysgelato-tagningar",
        ROT / "forvarld_karna/ut/gelato",
        ROT / "scen/3d/kontrakt/semantik/ut/kenny/semantik.json",
    ),
    "asketch": (
        ROT / "scen/3d/ingest/ut/a-sketch-servering-tagningar",
        ROT / "forvarld_karna/ut/asketch",
        ROT / "scen/3d/kontrakt/semantik/ut/a/semantik.json",
    ),
    "notan": (
        ROT / "scen/3d/ingest/ut/notan-tagningar",
        ROT / "forvarld_karna/ut/notan",
        ROT / "scen/3d/kontrakt/semantik/ut/notan/semantik.json",
    ),
    "btilltal": (
        ROT / "scen/3d/ingest/ut/b-tilltal-ravara-tagningar",
        R1 / "rum_ut/med_dekl/btilltal",
        ROT / "scen/3d/kontrakt/semantik/ut/b/semantik.json",
    ),
}


def kor_rubrik_auto(paket: dict, obs: dict) -> dict:
    """Kör Claudes mening_rubrik.py (H, M, U, K) på ett kompilerat paket."""
    ut = {}
    for t in paket["tagningar"]:
        sid = t["id"]
        a0, b0 = t["ut"]
        mitt = (a0 + b0) // 2
        rad_m = MR.mobel(paket, obs, sid, mitt)
        if not t["personer"]:
            ut[f"{sid}:-"] = dict(H=None, M=rad_m["poang"], U=None, K=None)
            continue
        for p in t["personer"]:
            pid = p["id"]
            sp = MG.spar_for(paket, pid, sid)
            if sp is None:
                continue
            U, X = MG.X_av(sp)
            h = MR.hallning(paket, X, U, sid, pid)
            etikett = paket["personer"][pid].get("pose", "staende")
            hp = MR.h_poang(h["klass"], etikett)
            up = MR.utsnitt(paket, X, U, sid, pid)["poang"]
            kp = MR.kontakt(paket, obs, X, sid, pid)["poang"]
            ut[f"{sid}:{pid}"] = dict(H=hp, H_klass=h["klass"], M=rad_m["poang"], U=up, K=kp)
    return ut


def main():
    STEG_UT.mkdir(parents=True, exist_ok=True)
    forutsag = json.loads((HIT / "steg_forutsagelse.json").read_text(encoding="utf-8"))["forutsagelser"]

    # Rendera de 4 ursprungliga klippen i Blender 5.2 (b-tilltal körs utan emit/Blender för att spara tid men ritar 2D-överlägg)
    resultat = {}
    g7_4_fel = 0
    g7_bt_fel = 0
    h_4_sum = 0
    h_tot = {g: 0 for g in GH.H_GRINDAR}
    rub_nollor = dict(H=0, M=0, U=0)
    rub_bas_nollor = dict(H=0, M=0, U=0)
    n1_fel_tot = 0
    n2_all_ok = True
    n3_all_ok = True
    k7_brott_tot = 0

    for namn, (ingest, bas_ut, sem_fil) in KLIPP_SPEC.items():
        obs_raw = json.loads((bas_ut / "obs.json").read_text(encoding="utf-8"))
        rec_raw = json.loads((bas_ut / "recept.json").read_text(encoding="utf-8"))
        obs = Observationer.model_validate(obs_raw)
        rec = Recept.model_validate(rec_raw)
        ut_k = STEG_UT / namn
        ut_k.mkdir(parents=True, exist_ok=True)

        # För b-tilltal hoppar vi över emit_bpy-subprocessen (ingen Blender-render där), för övriga 4 körs full emit_bpy + Blender 5.2!
        orig_sub = SSB.subprocess
        if namn == "btilltal":
            SSB.subprocess = types.SimpleNamespace(run=lambda *a, **k: None)
        try:
            pf = SSB.kompilera_scenpaket(namn, ingest, obs, rec, ut_k, semantik_fil=sem_fil)
        finally:
            SSB.subprocess = orig_sub

        paket = json.loads(pf.read_text(encoding="utf-8"))
        gr_sam = json.loads((ut_k / "paket_grindar.json").read_text(encoding="utf-8"))["sammanfattning"]

        # Rendera i lokal Blender 5.2 för de 4 klippen så att vi kan inspektera bilderna visuellt!
        jamf_bild = None
        if namn != "btilltal":
            jamf_bild = SSB.rendera_och_jamfor(ut_k, ingest)

        # 1. Claudes G7-oberoende
        g7_r = G7.mat_paket(namn, paket, obs_raw, ingest=ingest)
        n_g7_fel = sum(r["flaggad"] for r in g7_r)
        if namn == "btilltal":
            g7_bt_fel = n_g7_fel
        else:
            g7_4_fel += n_g7_fel

        # 2. Claudes H-serien
        spar2d = {}
        for k in obs_raw["klipp"]:
            fp = ingest / k["klipp"].upper() / "personer.json"
            spar2d[k["klipp"]] = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
        ktx = dict(klipp=namn, obs=obs_raw, recept=rec_raw, spar2d=spar2d)
        h_r = GH.mat(paket, ktx)
        h_s = GH.sammanfatta(h_r)
        if namn != "btilltal":
            h_4_sum += sum(h_s.values())
        for g in GH.H_GRINDAR:
            h_tot[g] += h_s[g]

        # 3. Claudes mening_rubrik (auto) före och efter för de 4 klippen
        rub_ny = kor_rubrik_auto(paket, obs_raw) if namn != "btilltal" else None
        if rub_ny is not None:
            for v in rub_ny.values():
                for k_c in ("H", "M", "U"):
                    if v[k_c] == 0:
                        rub_nollor[k_c] += 1
            p_orig = json.loads((bas_ut / "paket.json").read_text(encoding="utf-8"))
            rub_bas = kor_rubrik_auto(p_orig, obs_raw)
            for v in rub_bas.values():
                for k_c in ("H", "M", "U"):
                    if v[k_c] == 0:
                        rub_bas_nollor[k_c] += 1

        # 4. Nya mått N1-N4 + manus (K6) + medielager-redigering (K5, K7, K8) + felinjektion!
        manus = SM.bygg_manus(paket)
        (ut_k / "manus.json").write_text(json.dumps(manus, ensure_ascii=False, indent=2), encoding="utf-8")
        (ut_k / "manus.md").write_text(SM.manus_till_markdown(manus), encoding="utf-8")

        n1 = SM.mat_n1_kam_over_bord(paket)
        n2 = SM.mat_n2_antagen_tackning(paket)
        n3 = SM.mat_n3_manus_k6(paket, manus)
        fi = SM.felinjektion_n1_n4(paket)

        # K5 + K7 + K8 redigeringstester
        edit_st = SM.redigera_medielager(paket, "byt_skarmtext", None, "Kundens nya rubrik")
        edit_rep = SM.redigera_medielager(paket, "byt_replik", None, "Kundens nya replik")
        # Hitta en bärande tagning om den finns och pröva borttagning -> ska ge K5-varning!
        bar_sc = next((s["tagning"] for s in paket["mening"].get("scener", []) if s.get("barande")), None)
        edit_bar = SM.redigera_medielager(paket, "ta_bort_tagning", bar_sc) if bar_sc else None

        n1_fel_tot += n1["antal_brott"]
        n2_all_ok = n2_all_ok and n2["ok"]
        n3_all_ok = n3_all_ok and n3["ok"]
        for ed in (edit_st, edit_rep, edit_bar):
            if ed is not None:
                k7_brott_tot += int(ed["k7_logg"]["generativa_anrop"] > 0 or ed["k7_logg"]["spegling_anvand"])

        resultat[namn] = dict(
            grindar_per_person=gr_sam,
            g7_oberoende_fel=n_g7_fel,
            g7_oberoende=[{k: r[k] for k in ("tagning", "person", "led_med", "i_box", "i_mask", "spok_andel", "kamera_z", "flaggad", "skal")} for r in g7_r],
            h_sammanfattning=h_s,
            h_summa=sum(h_s.values()),
            h_fel_detaljer={f"{r['tagning']}:{r.get('person')}": {kk: {x: y for x, y in r[kk].items() if x != "ok"} for kk in GH.H_GRINDAR if r.get(kk, {}).get("ok") is False}
                            for r in h_r if any(r.get(kk, {}).get("ok") is False for kk in GH.H_GRINDAR)},
            rubrik_auto=rub_ny,
            N1_kam_over_bord=n1,
            N2_antagen=n2,
            N3_manus_k6=n3,
            N4_edits=dict(
                byt_skarmtext=dict(status=edit_st["status"], varningar=edit_st["varningar"]),
                byt_replik=dict(status=edit_rep["status"], varningar=edit_rep["varningar"]),
                ta_bort_barande_tagning=dict(tagning=bar_sc, status=edit_bar["status"], varningar=edit_bar["varningar"]) if edit_bar else None,
            ),
            felinjektion_N1_N4=fi,
            jamforelse_bild=str(jamf_bild.relative_to(ROT)) if jamf_bild else None,
            manus_md=str((ut_k / "manus.md").relative_to(ROT)),
        )
        print(f"\n=== {namn} ===")
        print(f"  G7-oberoende fel: {n_g7_fel}/{len(g7_r)} -> {[(r['tagning']+':'+r['person'], r['led_med'], r['skal']) for r in g7_r if r['flaggad']]}")
        print(f"  H-serien ({sum(h_s.values())} fel): { {k: v for k, v in h_s.items() if v} }")
        print(f"  N1={n1['ok']}({n1['antal_brott']}) N2={n2['tackning_pct']}% N3={n3['scener_ok']} FI={fi}")
        print(f"  N4 byt_text={edit_st['status']}({len(edit_st['varningar'])} varn), byt_replik={edit_rep['status']}({len(edit_rep['varningar'])} varn), ta_bort_bar({bar_sc})={edit_bar['varningar'] if edit_bar else None}")

    # Jämför förutsägelser mot faktiskt utfall!
    gel_rep_nej = resultat["gelato"]["N4_edits"]["byt_replik"]["status"] == "nekad_saknat_lager"
    k5_varn_ok = all(
        bool(resultat[k]["N4_edits"]["ta_bort_barande_tagning"] and resultat[k]["N4_edits"]["ta_bort_barande_tagning"]["varningar"])
        for k in KLIPP_SPEC
    )
    utfall_vs_forutsagelse = [
        ("G7-oberoende 4 klipp (<= 2 fel)", f"<= {forutsag['G7_oberoende_4_klipp_fel_max']}", g7_4_fel, g7_4_fel <= forutsag["G7_oberoende_4_klipp_fel_max"]),
        ("G7-oberoende hold-out b-tilltal (0 fel)", forutsag["G7_oberoende_btilltal_holdout_fel"], g7_bt_fel, g7_bt_fel == 0),
        ("H-serien 4 klipp summa (<= 22)", f"<= {forutsag['H_serien_4_klipp_summa_max']}", h_4_sum, h_4_sum <= forutsag["H_serien_4_klipp_summa_max"]),
        ("H1_objekt alla 5 klipp (0)", forutsag["H1_objekt_alla_5_klipp"], h_tot["H1_objekt"], h_tot["H1_objekt"] == 0),
        ("H3_hallning alla 5 klipp (<= 2)", f"<= {forutsag['H3_hallning_alla_5_klipp_max']}", h_tot["H3_hallning"], h_tot["H3_hallning"] <= 2),
        ("H7_2d alla 5 klipp (0)", forutsag["H7_2d_alla_5_klipp"], h_tot["H7_2d"], h_tot["H7_2d"] == 0),
        ("H10_kamera alla 5 klipp (<= 6)", f"<= {forutsag['H10_kamera_alla_5_klipp_max']}", h_tot["H10_kamera"], h_tot["H10_kamera"] <= 6),
        ("H4_genom kvar (>= 6, ärligt ej dolt)", f">= {forutsag['H4_genom_alla_5_klipp_min_kvar']}", h_tot["H4_genom"], h_tot["H4_genom"] >= 6),
        ("H5_ibild guacamole (= 2, 1:1 kantbeskärning)", forutsag["H5_ibild_guacamole_okning_forvantad"], resultat["guacamole"]["h_sammanfattning"]["H5_ibild"], resultat["guacamole"]["h_sammanfattning"]["H5_ibild"] == 2),
        ("Rubrik H nollor (<= 2)", f"<= {forutsag['rubrik_H_nollor_max']} (bas {rub_bas_nollor['H']})", rub_nollor["H"], rub_nollor["H"] <= 2),
        ("Rubrik M nollor (<= 4)", f"<= {forutsag['rubrik_M_nollor_max']} (bas {rub_bas_nollor['M']})", rub_nollor["M"], rub_nollor["M"] <= 4),
        ("Rubrik U nollor (<= 2)", f"<= {forutsag['rubrik_U_nollor_max']} (bas {rub_bas_nollor['U']})", rub_nollor["U"], rub_nollor["U"] <= 2),
        ("N1 kamera över bord (0 fel)", 0, n1_fel_tot, n1_fel_tot == 0),
        ("N2 antagen-täckning (100%)", "100%", "100%" if n2_all_ok else "<100%", n2_all_ok),
        ("N3 manus K6 kompletthet (100%)", "100%", "100%" if n3_all_ok else "<100%", n3_all_ok),
        ("N4 K5-varning på bärande (5/5)", True, k5_varn_ok, k5_varn_ok),
        ("N4 K8 ärligt nej på gelato replik", True, gel_rep_nej, gel_rep_nej),
        ("K7 spärr (0 generativt, 0 spegling)", 0, k7_brott_tot, k7_brott_tot == 0),
    ]

    print("\n================ FÖRUTSÄGELSE VS UTFALL (DEL 3) ================")
    for namn_p, pred, utfall, traff in utfall_vs_forutsagelse:
        print(f"  [{'TRÄFF' if traff else 'MISS '}] {namn_p:46s} | pred={str(pred):16s} | utfall={utfall}")

    rapport = dict(
        sammanfattning=dict(
            g7_4_klipp_fel=g7_4_fel,
            g7_btilltal_fel=g7_bt_fel,
            h_4_klipp_summa=h_4_sum,
            h_alla_5_klipp=h_tot,
            rubrik_nollor_bas=rub_bas_nollor,
            rubrik_nollor_steg=rub_nollor,
            n1_fel_tot=n1_fel_tot,
            n2_all_ok=n2_all_ok,
            n3_all_ok=n3_all_ok,
            k5_varn_ok=k5_varn_ok,
            gel_rep_nej=gel_rep_nej,
            k7_brott_tot=k7_brott_tot,
        ),
        forutsagelse_vs_utfall=[dict(matt=a, pred=b, utfall=c, traff=d) for a, b, c, d in utfall_vs_forutsagelse],
        per_klipp=resultat,
    )
    (HIT / "steg_utvardering.json").write_text(
        json.dumps(rapport, ensure_ascii=False, indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)),
        encoding="utf-8",
    )
    print("\nSparade:", HIT / "steg_utvardering.json")


if __name__ == "__main__":
    main()
