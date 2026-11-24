"""Del 1 (metod_mening_rubrik_latens.py):
1. Granskar reproducerbarheten i Claudes visuella rubrik (MENING.md:44-67):
   - Beräknar exakt överensstämmelse och Cohens kappa (oviktad + linjär/kvadratisk) mellan Claudes EGEN
     visuella bedömning (V) och Claudes EGEN automatiska rubrik (A) per kriterium (H, M, U, K).
   - Listar de exakta regelkonflikterna där V och A motsäger varandra (t.ex. svävande skiva i notan: A=1, V=2;
     spökkroppar i gelato S2 / asketch S3: A=2, V=0; dold disk i guacamole S1/S4: K=1/2 trots att disken saknas).
2. Mäter varm-process-latens i `forvarld_karna/mening_motor.py` på ledig dator (50 varma körningar efter 5 uppvärmningskörningar)
   med exakt steg-för-steg-profilering av vad som tar tid i `manipulera_scen`:
   - `copy.deepcopy(paket)` vs selektiv kopia av ändrad person/tagning
   - `extrahera_attitydprofil` (omberäknas i dag vid varje klick fast den redan räknats vid ingest!)
   - `_syntetisera_gang_med_attityd` / `_byt_hand_med_balvridning`
   - `_dra_in_dolda_ben_bakom_massiv_disk` (ren Python-tripploopen)
   - `fotkontakt`
   - `grindar.mat` (kör diagnostikgrindar synkront i live-klicket)
   - jämför med Claudes siffror från belastad dator (531-684 ms).

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\metod_mening_rubrik_latens.py
"""
from __future__ import annotations

import copy
import json
import pathlib
import statistics
import sys
import time

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
R1 = ROT / "motpart/runda-1-claude"

for p in (str(R1), str(ROT / "forvarld_karna"), str(ROT / "byggsten/brygga")):
    if p not in sys.path:
        sys.path.insert(0, p)

import grindar as G_ORIG  # noqa: E402
import mening_motor as MM  # noqa: E402
import scen_brygga as SB  # noqa: E402

# Exakta V/A-par direkt ur motpart/runda-1-claude/MENING.md rad 46-67 (21 person-tagningar + asketch S6)
# Format: (ruta, (Hv, Ha), (Mv, Ma), (Uv, Ua), (Kv, Ka))
MENING_VA = [
    ("guacamole S1 A", (0, 0), (0, 0), (1, 1), (0, 1)),
    ("guacamole S2 B", (1, 0), (1, 1), (1, 1), (1, 2)),
    ("guacamole S3 A", (0, 0), (1, 1), (1, 1), (2, 2)),
    ("guacamole S4 B", (0, 0), (0, 0), (1, 1), (0, 1)),
    ("guacamole S4 A", (0, 0), (0, 0), (1, 0), (0, 2)),
    ("gelato S1 A",    (1, 2), (1, 1), (0, 0), (1, 1)),
    ("gelato S2 A",    (0, 2), (0, 0), (0, 0), (0, 0)),
    ("asketch S1 A",   (1, 2), (0, 0), (1, 1), (0, 1)),
    ("asketch S2 B",   (2, 2), (1, None), (2, 2), (2, None)),
    ("asketch S3 B",   (0, 2), (0, None), (0, 0), (0, None)),
    ("asketch S4 B",   (1, 2), (1, None), (1, 2), (1, None)),
    ("asketch S5 B",   (2, 2), (1, 1), (1, 1), (1, 1)),
    ("asketch S6 -",   (None, None), (1, 0), (None, None), (None, None)),
    ("asketch S7 A",   (2, 2), (0, 0), (1, 1), (1, 1)),
    ("notan S1 A",     (1, 0), (2, 1), (2, 2), (1, 1)),
    ("notan S2 B",     (1, 0), (0, 0), (2, 2), (0, 1)),
    ("notan S3 A",     (1, 0), (2, 1), (2, 1), (1, 0)),
    ("notan S4 C",     (2, 2), (1, 0), (2, 2), (1, None)),
    ("notan S4 gast",  (2, 2), (0, 0), (1, 1), (0, None)),
    ("notan S5 B",     (1, 0), (2, 1), (2, 2), (1, 2)),
    ("notan S6 A",     (1, 0), (2, 1), (1, 1), (1, 2)),
    ("notan S7 B",     (2, 0), (1, 0), (0, 0), (2, 1)),
]


def cohen_kappa(ys_v: list[int], ys_a: list[int], cats=(0, 1, 2)) -> dict:
    n = len(ys_v)
    if n == 0:
        return dict(n=0, exact=None, kappa=None, qwk=None)
    k = len(cats)
    idx = {c: i for i, c in enumerate(cats)}
    M = np.zeros((k, k), dtype=float)
    for v, a in zip(ys_v, ys_a):
        M[idx[v], idx[a]] += 1.0
    p0 = float(np.trace(M) / n)
    pe = float(np.sum(M.sum(axis=1) * M.sum(axis=0)) / (n * n))
    kappa = (p0 - pe) / (1.0 - pe) if abs(1.0 - pe) > 1e-12 else 1.0
    # Kvadratiskt viktad kappa (QWK)
    W = np.array([[(i - j) ** 2 / ((k - 1) ** 2) for j in range(k)] for i in range(k)], dtype=float)
    E = np.outer(M.sum(axis=1), M.sum(axis=0)) / n
    qwk = 1.0 - float(np.sum(W * M) / np.sum(W * E)) if np.sum(W * E) > 1e-12 else 1.0
    return dict(
        n=n,
        exakt_traff=f"{int(np.trace(M))}/{n} ({p0*100:.1f}%)",
        avvikelse_2_steg=int(M[0, 2] + M[2, 0]),
        kappa=round(kappa, 3),
        qwk=round(qwk, 3),
        v_minus_a_medel=round(float(np.mean(np.array(ys_v) - np.array(ys_a))), 3),
    )


def granska_rubrik() -> dict:
    """Verifierar även att mening_rubrik_auto.json stämmer med A-kolumnen i MENING.md."""
    auto = json.loads((R1 / "mening_ut/mening_rubrik_auto.json").read_text(encoding="utf-8"))
    kriterier = ["H", "M", "U", "K"]
    ut = {}
    alla_v, alla_a = [], []
    motsagelser = []
    for ci, kn in enumerate(kriterier):
        vs, as_ = [], []
        n_v_bara = 0
        for rad in MENING_VA:
            ruta = rad[0]
            v, a = rad[ci + 1]
            if v is not None and a is not None:
                vs.append(v); as_.append(a)
                alla_v.append(v); alla_a.append(a)
                if v != a:
                    motsagelser.append(dict(ruta=ruta, kriterium=kn, V=v, A=a, diff=v - a))
            elif v is not None and a is None:
                n_v_bara += 1
        ut[kn] = dict(**cohen_kappa(vs, as_), antal_dar_A_saknas_men_V_satt=n_v_bara)
    ut["TOTALT_alla_par"] = cohen_kappa(alla_v, alla_a)
    # Kolla konkret: hur många av de 21 person-tagningarna har >=1 tvåstegs-motsägelse (V=0 vs A=2 eller V=2 vs A=0)?
    tva_steg = [m for m in motsagelser if abs(m["diff"]) == 2]
    # Kolla konkret: hur ofta sätter K betyg >= 1 trots att M=0 (bordet är DOLT i renderingen!)?
    k_trots_dolt_bord = []
    for rad in MENING_VA:
        ruta, _, (mv, ma), _, (kv, ka) = rad
        if ma == 0 and ka is not None and ka >= 1:
            k_trots_dolt_bord.append(dict(ruta=ruta, M_auto=ma, K_auto=ka, K_visuell=kv))
    return dict(
        overensstammelse=ut,
        antal_avvikelser_totalt=len(motsagelser),
        antal_tvastegs_motsagelser=len(tva_steg),
        tvastegs_motsagelser=tva_steg,
        k_betyg_trots_dolt_bord=k_trots_dolt_bord,
        auto_json_nycklar=len(auto),
    )


def tid_varm(fn, n_warm=5, n_meas=50) -> dict:
    for _ in range(n_warm):
        fn()
    t = []
    for _ in range(n_meas):
        t0 = time.perf_counter()
        fn()
        t.append((time.perf_counter() - t0) * 1000.0)
    t_sorted = sorted(t)
    return dict(
        min_ms=round(t_sorted[0], 2),
        p25_ms=round(float(np.percentile(t_sorted, 25)), 2),
        median_ms=round(statistics.median(t_sorted), 2),
        p90_ms=round(float(np.percentile(t_sorted, 90)), 2),
        max_ms=round(t_sorted[-1], 2),
    )


def profilera_manipulera_scen(paket: dict, op: str, pid: str, n_warm=3, n_meas=30) -> dict:
    """Delar upp exakt var millisekunderna går i oförändrad MM.manipulera_scen (varm process)."""
    prof_cache = MM.extrahera_attitydprofil(paket)

    def kor_en():
        dt = {}
        t0 = time.perf_counter()
        nytt = copy.deepcopy(paket)
        dt["deepcopy"] = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        profiler = MM.extrahera_attitydprofil(nytt)
        dt["extrahera_profil"] = (time.perf_counter() - t0) * 1000.0
        prof = profiler[pid]
        fps = float(nytt["tidsbas"]["fps"])

        t_op = t_dra = t_fot = t_ser = 0.0
        if op == "ga_med_attityd":
            nytt["objekt"] = [o for o in nytt["objekt"] if o["id"] != f"stol_{pid}"]
            for sp in nytt["rorelse"].get(pid, []):
                sid = sp["tagning"]
                R = sp["rutor"]
                U = [r[0] for r in R]
                X_orig = np.array([r[1:] for r in R], dtype=float).reshape(len(R), -1, 3) / 1000.0
                t_obj = next(t for t in nytt["tagningar"] if t["id"] == sid)
                max_d = 1.15 if len(t_obj["personer"]) == 1 else 0.52
                ts = time.perf_counter()
                X_ny, _ = MM._syntetisera_gang_med_attityd(X_orig, U, nytt["leder"], prof, fps, nytt.get("golv_z", 0.0), max_dist_m=max_d)
                t_op += (time.perf_counter() - ts) * 1000.0
                ts = time.perf_counter()
                for ob in nytt["objekt"]:
                    if ob["typ"] == "bord":
                        SB._dra_in_dolda_ben_bakom_massiv_disk(X_ny, nytt["leder"], ob, nytt.get("golv_z", 0.0))
                t_dra += (time.perf_counter() - ts) * 1000.0
                ts = time.perf_counter()
                SB.fotkontakt(X_ny, nytt["leder"], nytt.get("golv_z", 0.0))
                t_fot += (time.perf_counter() - ts) * 1000.0
                ts = time.perf_counter()
                sp["rutor"] = [[u] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U, X_ny)]
                t_ser += (time.perf_counter() - ts) * 1000.0
        else:
            for sp in nytt["rorelse"].get(pid, []):
                R = sp["rutor"]
                U = [r[0] for r in R]
                X_orig = np.array([r[1:] for r in R], dtype=float).reshape(len(R), -1, 3) / 1000.0
                ts = time.perf_counter()
                X_ny = MM._byt_hand_med_balvridning(X_orig, nytt["leder"])
                t_op += (time.perf_counter() - ts) * 1000.0
                ts = time.perf_counter()
                for ob in nytt["objekt"]:
                    if ob["typ"] == "bord":
                        SB._dra_in_dolda_ben_bakom_massiv_disk(X_ny, nytt["leder"], ob, nytt.get("golv_z", 0.0))
                t_dra += (time.perf_counter() - ts) * 1000.0
                ts = time.perf_counter()
                SB.fotkontakt(X_ny, nytt["leder"], nytt.get("golv_z", 0.0))
                t_fot += (time.perf_counter() - ts) * 1000.0
                ts = time.perf_counter()
                sp["rutor"] = [[u] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U, X_ny)]
                t_ser += (time.perf_counter() - ts) * 1000.0

        dt["operator_kinematik"] = t_op
        dt["dra_in_loop"] = t_dra
        dt["fotkontakt"] = t_fot
        dt["serialisering_rutor"] = t_ser
        t0 = time.perf_counter()
        G_ORIG.mat(nytt)
        dt["grindar_mat"] = (time.perf_counter() - t0) * 1000.0
        dt["summa_delar"] = sum(dt.values())
        return dt

    for _ in range(n_warm):
        kor_en()
    prover = [kor_en() for _ in range(n_meas)]
    delar = {k: round(statistics.median([p[k] for p in prover]), 2) for k in prover[0]}

    # Mät även oförändrad MM.manipulera_scen direkt (50 varma körningar)
    tot_oforandrad = tid_varm(lambda: MM.manipulera_scen(paket, op, pid), n_warm=5, n_meas=50)

    # Mät vad ren operator + selektiv kopia (utan onödig deepcopy av hela paketet och utan åter-extraktion av ingest-profil) tar!
    def snabb_selektiv():
        nytt = dict(paket)
        nytt["rorelse"] = dict(paket["rorelse"])
        nytt["rorelse"][pid] = [dict(sp) for sp in paket["rorelse"][pid]]
        prof = prof_cache[pid]
        fps = float(paket["tidsbas"]["fps"])
        for sp in nytt["rorelse"][pid]:
            R = sp["rutor"]
            U = [r[0] for r in R]
            X_orig = np.array([r[1:] for r in R], dtype=float).reshape(len(R), -1, 3) / 1000.0
            if op == "ga_med_attityd":
                X_ny, _ = MM._syntetisera_gang_med_attityd(X_orig, U, paket["leder"], prof, fps, paket.get("golv_z", 0.0), max_dist_m=1.15)
            else:
                X_ny = MM._byt_hand_med_balvridning(X_orig, paket["leder"])
            SB.fotkontakt(X_ny, paket["leder"], paket.get("golv_z", 0.0))
            sp["rutor"] = [[u] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U, X_ny)]
        return nytt

    tot_selektiv = tid_varm(snabb_selektiv, n_warm=5, n_meas=50)
    return dict(
        oforandrad_manipulera_scen_varm=tot_oforandrad,
        profilering_median_ms=delar,
        selektiv_kopia_och_cachad_profil_utan_dra_in_och_grindar=tot_selektiv,
    )


def main():
    rub = granska_rubrik()
    print("=== 1. RUBRIK-REPRODUCERBARHET (V vs A i MENING.md) ===")
    for k, v in rub["overensstammelse"].items():
        print(f"  {k:16s}: {v}")
    print(f"  Avvikelser totalt: {rub['antal_avvikelser_totalt']}, varav 2-stegs (0 vs 2): {rub['antal_tvastegs_motsagelser']}")
    for m in rub["tvastegs_motsagelser"]:
        print(f"    2-stegs: {m}")
    print(f"  K-betyg >= 1 trots att M_auto=0 (bord dolt!): {rub['k_betyg_trots_dolt_bord']}")

    print("\n=== 2. VARM-PROCESS-LATENS I MENING_MOTOR.PY (50 varma körningar) ===")
    lat = {}
    claude_att = json.loads((R1 / "mening_ut/mening_attityd.json").read_text(encoding="utf-8"))["tid"]
    for klipp, op in (("guacamole", "ga_med_attityd"), ("gelato", "byt_hand")):
        paket = json.loads((ROT / "forvarld_karna/ut" / klipp / "paket.json").read_text(encoding="utf-8"))
        prof_res = profilera_manipulera_scen(paket, op, "A")
        lat[klipp] = dict(
            claude_belastad_ms=claude_att[klipp]["manipulera_scen_totalt"],
            **prof_res,
        )
        print(f"\n  [{klipp} -> {op}]")
        print(f"    Claude (belastad dator): {claude_att[klipp]['manipulera_scen_totalt']}")
        print(f"    Vår varma körning (oförändrad kod): {prof_res['oforandrad_manipulera_scen_varm']}")
        print(f"    Steg-profil (median ms): {prof_res['profilering_median_ms']}")
        print(f"    Selektiv kopia + cachad profil: {prof_res['selektiv_kopia_och_cachad_profil_utan_dra_in_och_grindar']}")

    ut = dict(rubrik_reproducerbarhet=rub, latens_varm=lat)
    (HIT / "metod_mening_rubrik_latens.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nSparade:", HIT / "metod_mening_rubrik_latens.json")


if __name__ == "__main__":
    main()
