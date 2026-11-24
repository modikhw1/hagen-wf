"""Snabb steg 2-körning (FORREGISTRERING.md A) i RAM (/dev/shm) med varma extraktorer och delad rangtransform.

Exakt samma ffmpeg-recept som motpart/runda-4/2-invarians/recept.py och exakt samma
A3/A4-dom som analys.py, men:
  1. Varianter byggs i RAM (/dev/shm på Linux, annars tempkatalog) och raderas direkt efter mätning.
  2. Silero VAD och YOLOv8n hålls laddade i minnet (VarmExtraktor) -> 0 kallstart per variant.
  3. E28-bilaga och E30-VAD extraheras i samma pass (ingen dubbel avkodning).
  4. Använder den gemensamma FrystECDFTransform ur infra/rang.py.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from infra.extraktorer import VarmExtraktor, _ffmpeg_bin
from infra.rang import FrystECDFTransform

# Fältregister identiskt med motpart/runda-4/2-invarians/falt.py
FALT: dict[str, tuple[str, float, float | None, str | None]] = {
    "e28.langd": ("Ttid", 0.10, 0.8, None),
    "e28.skott_median": ("Ttid", 0.10, 0.8, "e28.byten"),
    "e28.skott_max": ("Ttid", 0.10, 0.8, "e28.byten"),
    "e28.forsta_byte": ("Ttid", 0.10, 0.8, "e28.byten"),
    "e28.forsta_ljud": ("Ttid", 0.10, 0.8, "e28.pauser"),
    "e30.langd": ("Ttid", 0.10, 0.8, None),
    "e30.forsta_tal": ("Ttid", 0.10, 0.8, "e30.tal_segment"),
    "e28.takt": ("Ttat", 0.02, 1.25, "e28.byten"),
    "e30.tal_per_s": ("Ttat", 0.005, 1.25, "e30.tal_segment"),
    "e28.rorelse": ("Tq", 0.20, None, None),
    "e28.rorelse_2s": ("Tq", 0.20, None, None),
    "e28.rorelse_kvot": ("Tq", 0.10, None, None),
    "e28.byten": ("Gr", 0.0, None, None),
    "e28.pauser": ("Gr", 0.0, None, None),
    "e30.tal_segment": ("Gr", 0.0, None, None),
    "e28.skott_max_andel": ("Ga", 0.02, None, None),
    "e28.skott_cv": ("Ga", 0.05, None, None),
    "e28.ljud_andel": ("Ga", 0.02, None, None),
    "e30.tal_andel": ("Ga", 0.02, None, None),
    "e28.byten_3s": ("Gf", 0.0, None, None),
    "e28.lufs": ("L", 0.5, None, None),
    "e28.lra": ("L", 0.5, None, None),
    **{f"e37.antal{k}": ("Gp", 0.0, None, None) for k in range(6)},
    "e37.personer_medel": ("Gp", 0.0, None, None),
    "e37.andel_minst_en": ("Gp", 0.0, None, None),
    "e37.andel_minst_tva": ("Gp", 0.0, None, None),
    "e37.personer_max": ("Gp", 0.0, None, None),
}

T2_19 = [
    "e28.langd", "e28.takt", "e28.skott_median", "e28.skott_max_andel", "e28.skott_cv",
    "e28.forsta_byte", "e28.rorelse", "e28.rorelse_kvot", "e28.ljud_andel", "e28.pauser",
    "e28.lufs", "e28.lra", "e30.tal_andel", "e30.tal_segment", "e30.tal_per_s",
    "e30.forsta_tal", "e37.personer_medel", "e37.andel_minst_en", "e37.andel_minst_tva",
]

ORDNING = ["O", "C", "C2", "Cr", "N0", "N0r", "N1", "N2", "N3", "N4", "N5", "N6", "P"]
NN = ["N1", "N2", "N3", "N4", "N5"]

SUFFIX = {
    "N0": ["-c", "copy"],
    "N1": ["-c:v", "libx264", "-preset", "medium", "-crf", "28", "-pix_fmt", "yuv420p", "-threads:v", "1", "-c:a", "copy", "-fps_mode", "passthrough"],
    "N2": ["-vf", "scale=w='max(2,trunc(iw/4)*2)':h='max(2,trunc(ih/4)*2)':flags=lanczos,setsar=1", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "copy", "-fps_mode", "passthrough"],
    "N3": ["-af", "volume=-6dB", "-c:v", "copy", "-c:a", "pcm_s24le"],
    "N4": ["-af", "volume=-12dB", "-c:v", "copy", "-c:a", "pcm_s24le"],
    "N5": ["-vf", "fps=fps=15:start_time=0:round=near", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "copy", "-fps_mode", "passthrough"],
    "N6": ["-vf", "crop=iw-4:ih-4:2:2,pad=iw+4:ih+4:2:2:black,setsar=1", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "copy", "-fps_mode", "passthrough"],
    "P": ["-vf", "setpts=(PTS-STARTPTS)/1.25,fps=fps=30:start_time=0:round=near", "-af", "atempo=1.25", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "pcm_s24le", "-fps_mode", "passthrough"],
}


def _ram_tmp_rot() -> str | None:
    shm = Path("/dev/shm")
    if shm.is_dir() and os.access(str(shm), os.W_OK):
        return str(shm)
    return None


def c_cmd(o: Path, c: Path) -> list[str]:
    return [
        _ffmpeg_bin(), "-nostdin", "-hide_banner", "-loglevel", "warning", "-y",
        "-i", str(o), "-map", "0:v:0", "-map", "0:a:0?", "-map_metadata", "-1", "-map_chapters", "-1",
        "-vf", "fps=fps=30:start_time=0:round=near,pad=ceil(iw/2)*2:ceil(ih/2)*2:0:0,setsar=1",
        "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p", "-c:a", "pcm_s24le",
        "-fps_mode", "passthrough", str(c),
    ]


def var_cmd(namn: str, c: Path, out: Path) -> list[str]:
    key = "N0" if namn == "N0r" else namn
    return [
        _ffmpeg_bin(), "-nostdin", "-hide_banner", "-loglevel", "warning", "-y",
        "-i", str(c), "-map", "0:v:0", "-map", "0:a:0?", "-map_metadata", "-1", "-map_chapters", "-1",
        *SUFFIX[key], str(out),
    ]


def _kor_ff(argv: list[str]) -> tuple[int, str]:
    r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    return r.returncode, r.stderr


def mat_ref_c_klipp(clip_id: str, video_fil: Path, extraktor: VarmExtraktor) -> dict[str, Any]:
    """Bygger C i RAM (/dev/shm), mäter E28/E30/E37 med varm extraktor och frigör direkt."""
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="s2ref_", dir=_ram_tmp_rot()) as td:
        c_fil = Path(td) / "C.mkv"
        rc, err = _kor_ff(c_cmd(video_fil, c_fil))
        if rc != 0 or not c_fil.exists():
            return {"id": clip_id, "konto": clip_id.rsplit("-", 1)[0], "variant": "C", "c_rc": rc, "fel": err[-400:]}
        storlek = c_fil.stat().st_size
        ut, tider = extraktor.mat_alla(c_fil, f"{clip_id}~C", med_bilaga=True)
        return {
            "id": clip_id,
            "konto": clip_id.rsplit("-", 1)[0],
            "variant": "C",
            "c_rc": 0,
            "c_storlek": storlek,
            "e28": ut["e28"],
            "e30": ut["e30"],
            "e37": ut["e37"],
            "extraktor_sek": tider,
            "total_sek": round(time.monotonic() - t0, 3),
        }


def mat_test_klipp(clip_id: str, video_fil: Path, extraktor: VarmExtraktor) -> dict[str, Any]:
    """Kör alla 13 varianter (O, C, C2, Cr, N0, N0r, N1..N6, P) i RAM (/dev/shm) för ett testklipp."""
    t0 = time.monotonic()
    rader: list[dict[str, Any]] = []
    konto = clip_id.rsplit("-", 1)[0]
    with tempfile.TemporaryDirectory(prefix="s2tst_", dir=_ram_tmp_rot()) as td:
        d = Path(td)
        c_fil = d / "C.mkv"
        for namn in ORDNING:
            tv = time.monotonic()
            stage: Path | None = None
            rc, err = 0, ""
            if namn == "O":
                stage = video_fil
            elif namn == "C":
                stage = c_fil
                rc, err = _kor_ff(c_cmd(video_fil, stage))
            elif namn == "C2":
                stage = c_fil
            elif namn == "Cr":
                stage = d / "Cr.mkv"
                rc, err = _kor_ff(c_cmd(video_fil, stage))
            else:
                stage = d / f"{namn}.mkv"
                rc, err = _kor_ff(var_cmd(namn, c_fil, stage))

            bygg_sek = round(time.monotonic() - tv, 3)
            try:
                if rc != 0 or stage is None or not stage.exists():
                    rader.append({"id": clip_id, "konto": konto, "variant": namn, "rc": rc, "fel": err[-400:]})
                    continue
                storlek = stage.stat().st_size
                ut, tider = extraktor.mat_alla(stage, f"{clip_id}~{namn}", med_bilaga=True)
                rader.append({
                    "id": clip_id,
                    "konto": konto,
                    "variant": namn,
                    "rc": 0,
                    "storlek": storlek,
                    "bygg_sek": bygg_sek,
                    "e28": ut["e28"],
                    "e30": ut["e30"],
                    "e37": ut["e37"],
                    "extraktor_sek": tider,
                })
            finally:
                if namn not in ("O", "C", "C2") and stage is not None and stage != c_fil and stage.exists():
                    stage.unlink()
    return {"id": clip_id, "total_sek": round(time.monotonic() - t0, 3), "rader": rader}


def _num(x: Any) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if (np.isnan(v) or np.isinf(v)) else v


def uttag(row: dict[str, Any]) -> tuple[dict[str, float | None], dict[str, int]]:
    v: dict[str, float | None] = {k: None for k in FALT}
    e28, e30, e37 = row.get("e28"), row.get("e30"), row.get("e37")
    if e28:
        for k in (
            "langd", "byten", "takt", "skott_median", "skott_max", "skott_max_andel",
            "skott_cv", "forsta_byte", "byten_3s", "rorelse", "rorelse_2s", "rorelse_kvot",
            "ljud_andel", "pauser", "forsta_ljud", "lufs", "lra",
        ):
            v[f"e28.{k}"] = _num(e28.get(k))
    if e30:
        for k in ("langd", "tal_andel", "tal_segment", "tal_per_s", "forsta_tal"):
            v[f"e30.{k}"] = _num(e30.get(k))
    n = 0
    if e37 and e37.get("antal") is not None:
        a = e37["antal"]
        n = len(a)
        for k in range(6):
            v[f"e37.antal{k}"] = float(a[k]) if k < n else None
        if n:
            v["e37.personer_medel"] = float(np.mean(a))
            v["e37.andel_minst_en"] = float(np.mean([x >= 1 for x in a]))
            v["e37.andel_minst_tva"] = float(np.mean([x >= 2 for x in a]))
            v["e37.personer_max"] = float(max(a))
    return v, {"e37_rutor": n}


def kor_analys(ref_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]], test_ids: list[str]) -> dict[str, Any]:
    """Kör komplett A3/A4-analys med delad FrystECDFTransform ur infra/rang.py."""
    ref = []
    for r in ref_rows:
        if r.get("c_rc", 0) != 0 or not r.get("e28"):
            continue
        v, st = uttag(r)
        ref.append({"id": r["id"], "konto": r["konto"], "v": v, "st": st})

    T = FrystECDFTransform(ref, FALT.keys())
    V: dict[str, dict[str, dict[str, float | None]]] = defaultdict(dict)
    st_map: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    rader = []
    for t in test_rows:
        v, s = uttag(t)
        V[t["id"]][t["variant"]] = v
        st_map[t["id"]][t["variant"]] = s
        rader.append({"id": t["id"], "variant": t["variant"], "v": v})

    # Identitetstest
    brott, n_id = [], 0
    for i in test_ids:
        for a, b in [("N0", "C"), ("C2", "C"), ("Cr", "C"), ("N0r", "N0")]:
            if a in V[i] and b in V[i]:
                n_id += 1
                for j in FALT:
                    if V[i][a].get(j) != V[i][b].get(j):
                        brott.append({"id": i, "par": f"{a} vs {b}", "falt": j, a: V[i][a].get(j), b: V[i][b].get(j)})

    ft = T.fortest(ref, rader, n_perm=100, seed=202611204)

    def dom_T(j: str) -> dict[str, Any]:
        klass, eps, fakt, hf = FALT[j]
        per = {}
        for i in test_ids:
            v = V[i]
            c, p = v.get("C", {}).get(j), v.get("P", {}).get(j)
            ns = {n: v.get(n, {}).get(j) for n in NN}
            giltigN = all(x is not None for x in ns.values()) and c is not None
            t_val = max(abs(x - c) for x in ns.values()) if giltigN else None
            pp = abs(p - c) if (p is not None and c is not None) else None
            q = (t_val / pp) if (t_val is not None and pp is not None and pp > eps) else None
            tecken_fel, storlek_fel = False, False
            if pp is not None and pp > eps and klass in ("Ttid", "Ttat"):
                ok = (p - c) < 0 if klass == "Ttid" else (p - c) > 0
                tecken_fel = not ok
                stabilt = True if hf is None else (v.get("C", {}).get(hf) is not None and v.get("C", {}).get(hf) == v.get("P", {}).get(hf))
                if stabilt and ok and fakt is not None:
                    storlek_fel = abs(p - fakt * c) > max(eps, 0.10 * abs(c * (fakt - 1)))
            per[i] = {
                "C": c, "P": p, **ns, "t": t_val, "p": pp, "q": q,
                "teknisk_over_eps": bool(t_val is not None and t_val > eps),
                "tecken_fel": tecken_fel, "storlek_fel": storlek_fel,
                "giltig_for_grind": bool(giltigN and pp is not None and pp > eps and not tecken_fel and not storlek_fel),
            }
        gil = [r for r in per.values() if r["giltig_for_grind"]]
        qs = [r["q"] for r in per.values() if r["q"] is not None]
        c4 = sum(
            1 for i in test_ids
            if any(V[i].get(x, {}).get(j) is None and V[i].get("C", {}).get(j) is not None for x in NN + ["P"])
            or (j.startswith("e37") and any(st_map[i].get(x, {}).get("e37_rutor", 6) < 6 for x in ["C"] + NN))
        )
        v1 = len(gil) < 8
        v2 = (len(qs) > 0 and float(np.median(qs)) >= 0.5) or sum(1 for q in qs if q >= 1) >= 3
        v3 = sum(1 for r in per.values() if r["teknisk_over_eps"]) >= 3 or sum(1 for r in per.values() if r["tecken_fel"]) >= 3
        v4 = c4 >= 2
        dom = "FÄLLD" if (v2 or v3 or v4) else ("FÄLLD (villkor 1)" if v1 else "KLARAD")
        return {
            "klass": klass, "eps": eps, "n_giltiga": len(gil),
            "median_q": round(float(np.median(qs)), 4) if qs else None,
            "n_teknisk_over_eps": sum(1 for r in per.values() if r["teknisk_over_eps"]),
            "dom": dom,
        }

    def dom_G(j: str) -> dict[str, Any]:
        klass, eps, _, _ = FALT[j]
        gil, union = 0, 0
        perN = {n: 0 for n in NN}
        for i in test_ids:
            v = V[i]
            c = v.get("C", {}).get(j)
            if c is not None and all(v.get(n, {}).get(j) is not None for n in NN):
                gil += 1
            hit = False
            for n in NN:
                x = v.get(n, {}).get(j)
                if c is not None and x is not None and abs(x - c) > eps:
                    perN[n] += 1
                    hit = True
            if hit:
                union += 1
        if gil < 8:
            return {"klass": klass, "eps": eps, "n_giltiga": gil, "dom": "EJ PRÖVAT"}
        return {"klass": klass, "eps": eps, "n_giltiga": gil, "over_eps_union": union, "over_eps_per_N": perN,
                "dom": "FÄLLD" if (union >= 3 or any(x >= 3 for x in perN.values())) else "KLARAD"}

    def dom_L(j: str) -> dict[str, Any]:
        eps = FALT[j][1]
        gil, union = 0, 0
        perN = {n: 0 for n in NN}
        for i in test_ids:
            v = V[i]
            c = v.get("C", {}).get(j)
            if c is not None and all(v.get(n, {}).get(j) is not None for n in NN):
                gil += 1
            hit = False
            for n in NN:
                x = v.get(n, {}).get(j)
                if c is None or x is None:
                    continue
                avv = abs((x - c) - (-6.0 if n == "N3" else -12.0)) > eps if (j == "e28.lufs" and n in ("N3", "N4")) else abs(x - c) > eps
                if avv:
                    perN[n] += 1
                    hit = True
            if hit:
                union += 1
        if gil < 8:
            return {"klass": "L", "eps": eps, "n_giltiga": gil, "dom": "EJ PRÖVAT"}
        return {"klass": "L", "eps": eps, "n_giltiga": gil, "avviker_union": union, "avviker_per_N": perN,
                "dom": "FÄLLD" if (union >= 3 or any(x >= 3 for x in perN.values())) else "KLARAD"}

    domar = {}
    for j, (klass, *_) in FALT.items():
        domar[j] = dom_T(j) if klass in ("Ttid", "Ttat", "Tq") else (dom_L(j) if klass == "L" else dom_G(j))

    # Grannar (T2_19)
    ok_f = [j for j in T2_19 if T.par[j].get("kalibrerad")]
    med_z = {j: float(np.median([T.z(j, r["v"][j]) for r in ref if r["v"].get(j) is not None])) for j in ok_f}

    def vec(v: dict[str, float | None]) -> tuple[np.ndarray, np.ndarray]:
        z, ind = [], []
        for j in T2_19:
            val = v.get(j) if j in ok_f else None
            zz = T.z(j, val) if val is not None else None
            z.append(med_z.get(j, 0.0) if zz is None else zz)
            ind.append(1.0 if zz is None else 0.0)
        return np.array(z), np.array(ind)

    R_vecs = [(r["id"], *vec(r["v"])) for r in ref]

    def nn5(vz: np.ndarray, vi: np.ndarray) -> list[str]:
        d = sorted(((float(np.linalg.norm(np.concatenate([vz - rz, vi - ri]))), rid) for rid, rz, ri in R_vecs), key=lambda x: (x[0], x[1]))
        return [x[1] for x in d[:5]]

    gr_union = 0
    for i in test_ids:
        if "C" not in V[i]:
            continue
        gc = set(nn5(*vec(V[i]["C"])))
        if any(n in V[i] and len(set(nn5(*vec(V[i][n]))) & gc) <= 2 for n in NN):
            gr_union += 1

    return {
        "n_ref_klipp": len(ref),
        "n_ref_konton": T.nk,
        "n_test_klipp": len(test_ids),
        "fortest": ft,
        "identitet": {"jamforelser": n_id, "antal_brott": len(brott), "brott": brott[:10]},
        "stopp_instrument": (not ft["permutation_ok"]) or (not ft["tillagg_kopia_ok"]) or bool(brott),
        "dom": domar,
        "grannar": {
            "klipp_med_minst_3_bytta_union": gr_union,
            "dom": "FÄLLD som stabilt granninstrument" if gr_union >= 3 else "KLARAD (ej fälld)",
        },
    }
