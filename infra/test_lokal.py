"""Lokal verifiering av rang.py, kor.py (M4), extraktorer.py (paritet) och O-lager (M1).

Skriver bara små testfiler (~15 MB) så C:-disken hålls säkert över 7 GB.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROT = Path(__file__).resolve().parents[1]
if str(ROT) not in sys.path:
    sys.path.insert(0, str(ROT))

from infra.extraktorer import VarmExtraktor, kor_oforandrade
from infra.kor import GrindStopp, JobbKorare, JobbSpec, maskin_granser
from infra.olager import OLager, bygg_klipp, ladda_repo_metadata
from infra.rang import FrystECDFTransform, medelrang_z


def test_rang() -> dict:
    """Verifierar infra/rang.py mot T3-codex/robusthet.py och 2-invarians/ref_mat.jsonl."""
    # 1. Medelrang-invarians mot radordning med många lika värden
    rng = np.random.default_rng(20261120)
    A = np.column_stack([
        rng.integers(0, 5, size=200).astype(float),
        rng.normal(size=200),
        np.ones(200),  # konstant kolumn
    ])
    Z0 = medelrang_z(A)
    perm = rng.permutation(len(A))
    Z1 = np.empty_like(Z0)
    Z1[perm] = medelrang_z(A[perm])
    max_diff_medelrang = float(np.max(np.abs(Z0 - Z1)))
    assert max_diff_medelrang < 1e-12, f"medelrang bröt radordningsinvarians: {max_diff_medelrang}"
    assert float(np.max(np.abs(Z0[:, 2]))) == 0.0, "konstant kolumn ska vara 0.0"

    # 2. FrystECDFTransform mot verkliga ref_mat.jsonl (144 klipp, 72 konton)
    sys.path.insert(0, str(ROT / "motpart/runda-4/2-invarians"))
    import analys as steg2_analys
    from falt import FALT

    ref = steg2_analys.ladda_ref()
    T_ny = FrystECDFTransform(ref, FALT.keys())
    T_gam = steg2_analys.Transform(ref)
    max_vs_analys = 0.0
    for r in ref:
        for j in FALT:
            a, b = T_ny.z(j, r["v"].get(j)), T_gam.z(j, r["v"].get(j))
            assert (a is None) == (b is None), (j, a, b)
            if a is not None:
                max_vs_analys = max(max_vs_analys, abs(a - b))
    assert max_vs_analys <= 1e-12, f"Avvikelse mot analys.Transform: {max_vs_analys}"

    ft = T_ny.fortest(ref, ref[:12], n_perm=100, seed=202611204)
    assert ft["permutation_ok"] and ft["tillagg_kopia_ok"], ft
    return {
        "medelrang_perm_max_diff": max_diff_medelrang,
        "fryst_ecdf_vs_analys_max_diff": max_vs_analys,
        "fortest": ft,
        "n_ref": len(ref),
    }


def test_kor() -> dict:
    """Verifierar M4 (provlopp + ETA-grind + 1.5x tak + FRAMSTEG.json + mänsklig grind + återupptagning)."""
    with tempfile.TemporaryDirectory(prefix="hagen_kor_test_") as td:
        mapp = Path(td) / "jobb1"
        ordning: list[str] = []

        def mg():
            ordning.append("mansklig_grind")
            return {"panel_url": "http://127.0.0.1:5191/pass/demo", "klar": True}

        def enhet_fn(e):
            ordning.append(f"enhet:{e}")
            time.sleep(0.05)
            return {"ok": True}

        spec = JobbSpec(jobb_id="test_m4", mapp=mapp, beskrivning="Test av M4", provlopp_antal=2, min_ledigt_disk_gb=1.0)
        k = JobbKorare(spec)
        res = k.kor(["a", "b", "c", "d"], enhet_fn, mansklig_grind_fn=mg)
        assert ordning[0] == "mansklig_grind", f"Mänsklig grind kördes inte först: {ordning}"
        grind = json.loads((mapp / "GRIND.json").read_text(encoding="utf-8"))
        framsteg = json.loads((mapp / "FRAMSTEG.json").read_text(encoding="utf-8"))
        assert grind["provlopp_utfort"] is True
        assert framsteg["n"] == 4 and framsteg["N"] == 4 and framsteg["status"] == "klar"

        # Återupptagning: kör igen -> ska inte köra enheter om igen
        ordning.clear()
        res2 = k.kor(["a", "b", "c", "d"], enhet_fn)
        assert len(ordning) == 0 and res2["status"] == "klar"

        # Testa väggtidstak (1.5x ETA)
        mapp_tak = Path(td) / "jobb_tak"
        spec_tak = JobbSpec(jobb_id="test_tak", mapp=mapp_tak, provlopp_antal=1, tak_sek_explicit=0.12, min_ledigt_disk_gb=1.0)
        k_tak = JobbKorare(spec_tak)
        stoppad_kod = None
        try:
            k_tak.kor(["1", "2", "3", "4", "5"], lambda e: (time.sleep(0.08), {"ok": True})[1])
        except GrindStopp as gs:
            stoppad_kod = gs.kod
        assert stoppad_kod == "stoppad_tak_tid", f"Väntade stoppad_tak_tid, fick {stoppad_kod}"

        # Testa > 5 min grind med krav på godkännande
        mapp_5m = Path(td) / "jobb_5m"
        spec_5m = JobbSpec(
            jobb_id="test_5m", mapp=mapp_5m, provlopp_antal=1,
            krav_godkannande_over_5min=True, min_ledigt_disk_gb=1.0,
        )
        k_5m = JobbKorare(spec_5m)
        res_5m = k_5m.kor([str(i) for i in range(4000)], lambda e: (time.sleep(0.1), {})[1])
        assert res_5m["status"] == "vantar_godkannande" and res_5m["grind"]["over_5min"] is True

        return {
            "mansklig_grind_forst": True,
            "provlopp_och_eta_loggad": True,
            "framsteg_json_ok": True,
            "aterupptagning_ok": True,
            "vaggtidstak_ok": True,
            "grind_over_5min_pausar": True,
            "maskin_granser": maskin_granser(),
        }


def test_paritet_och_m1() -> dict:
    """Verifierar exakt paritet mot oförändrade E28/E30/E37 samt M1 (< 50 ms) på lokalt O-lager."""
    src_dir = Path.home() / "Downloads/letrend-r4"
    # Välj 3 korta klipp (5-12 s) ur manifest.jsonl så testet går snabbt och tar < 10 MB
    man = [json.loads(l) for l in (ROT / "motpart/runda-4/1-datagrund/manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    korta = sorted(man, key=lambda r: r["langd_s"])[:3]
    ids = [r["id"] for r in korta]
    meta_map = ladda_repo_metadata(set(ids))

    extr = VarmExtraktor()
    olager_lokal = ROT / "data/olager_prov"

    bygg_res = []
    for cid in ids:
        bygg_res.append(bygg_klipp(cid, src_dir / f"{cid}.mp4", olager_lokal, extr, extra_meta=meta_map.get(cid), force=True))

    # Paritet på första klippet mot repots oförändrade e28-tek.mjs, e30_tal.py, e37_personer.py
    cid0 = ids[0]
    ofor = kor_oforandrade({cid0: src_dir / f"{cid0}.mp4"})[cid0]
    varm_e28 = json.loads((olager_lokal / cid0 / "e28.json").read_text(encoding="utf-8"))
    varm_e30 = json.loads((olager_lokal / cid0 / "e30.json").read_text(encoding="utf-8"))
    varm_e37 = json.loads((olager_lokal / cid0 / "e37.json").read_text(encoding="utf-8"))

    e28_diff = {k: (varm_e28.get(k), ofor["e28"].get(k)) for k in ofor["e28"] if k != "skott" and varm_e28.get(k) != ofor["e28"].get(k)}
    e30_diff = {k: (varm_e30.get(k), ofor["e30"].get(k)) for k in ofor["e30"] if varm_e30.get(k) != ofor["e30"].get(k)}
    e37_diff = {"antal": (varm_e37.get("antal"), ofor["e37"].get("antal"))} if varm_e37.get("antal") != ofor["e37"].get("antal") else {}

    # M1-mätning: lästid per klipp (disk kall/varm + 6 dekodade rutor + RAM-cache)
    ol = OLager(olager_lokal)
    t_disk_meta_ljud = []
    t_disk_med_6_rutor = []
    for _ in range(10):
        for cid in ids:
            t0 = time.perf_counter()
            kl = ol.las_klipp(cid, ladda_ljud=True, ladda_jpack_bytes=False)
            t_disk_meta_ljud.append((time.perf_counter() - t0) * 1000.0)

            n_r = kl["rutor_index"]["n_rutor"]
            urval_idx = [int(x) for x in np.linspace(0, max(n_r - 1, 0), min(6, n_r))]
            t0 = time.perf_counter()
            ol.las_klipp(cid, ladda_ljud=True, dekoda_rutor=urval_idx)
            t_disk_med_6_rutor.append((time.perf_counter() - t0) * 1000.0)

    ol.forladda_i_minnet(ids, med_jpack=True)
    t_ram = []
    for _ in range(20):
        for cid in ids:
            t0 = time.perf_counter()
            ol.las_klipp(cid, anvand_cache=True)
            t_ram.append((time.perf_counter() - t0) * 1000.0)

    return {
        "extraktor_laddtid_sek": extr.laddtid_sek,
        "klipp": bygg_res,
        "paritet_klipp": cid0,
        "paritet_e28_avvikelser": e28_diff,
        "paritet_e30_avvikelser": e30_diff,
        "paritet_e37_avvikelser": e37_diff,
        "m1_disk_meta_e_ljud_ms": {
            "median": round(float(np.median(t_disk_meta_ljud)), 2),
            "p95": round(float(np.percentile(t_disk_meta_ljud, 95)), 2),
            "max": round(float(np.max(t_disk_meta_ljud)), 2),
        },
        "m1_disk_inkl_6_rutor_dekod_ms": {
            "median": round(float(np.median(t_disk_med_6_rutor)), 2),
            "p95": round(float(np.percentile(t_disk_med_6_rutor, 95)), 2),
            "max": round(float(np.max(t_disk_med_6_rutor)), 2),
        },
        "m1_ram_cache_ms": {
            "median": round(float(np.median(t_ram)), 4),
            "max": round(float(np.max(t_ram)), 4),
        },
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ut = {
        "rang": test_rang(),
        "kor_m4": test_kor(),
        "paritet_och_m1": test_paritet_och_m1(),
    }
    print(json.dumps(ut, ensure_ascii=False, indent=2))
