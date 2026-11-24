"""Motprov för felen C1, C2, A2, A3, C3 (A6 har eget skript): samma mätsticka på originalets paket (före) och B:s (efter).

Före = Argons lagrade paket i `forvarld_karna/ut/<namn>/paket.json` (läses, ändras inte), med obs/recept därifrån för att
återskapa vilket personspår varje person byggdes ur (samma ordning som `forvarld_karna/scen_brygga.py:276–281`).
Efter = `B-nasta-klipp/ut/<ingestmapp>/paket.json`.

    scen\\.venv\\Scripts\\python.exe motpart\\runda-3-opus\\B-nasta-klipp\\prov\\motprov.py <namn>=<ingestmapp> ...

Utvärderingsskript: klippnamnen ges som argument; kärnkoden i `../karna/` innehåller inga klippnamn.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import math
import pathlib
import sys

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
B = HIT.parent
ROT = B.parents[2]
sys.path.insert(0, str(B / "karna"))
import grindar as G_ny  # noqa: E402
import mutation  # noqa: E402
from rotation import quat_till_mat  # noqa: E402

F = np.diag([1.0, -1.0, -1.0])


def _ladda_original_grindar():
    spec = importlib.util.spec_from_file_location("grindar_original", ROT / "byggsten/brygga/grindar.py")
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROT / "byggsten/brygga"))
    spec.loader.exec_module(m)
    return m


def lagg_till_spar(paket: dict, obs: dict, recept: dict, ingest: pathlib.Path):
    """Originalpaketen bär inte spår-id; återskapa det med originalets egen ordning (p_dets[i] <-> spar_lista[i])."""
    for k in obs["klipp"]:
        sid = k["klipp"]
        pf = ingest / sid.upper() / "personer.json"
        if not pf.exists():
            continue
        sp_map = json.loads(pf.read_text(encoding="utf-8"))
        spar_lista = sorted(sp_map, key=lambda s: -len(sp_map[s]))
        p_dets = [d for d in k["detektioner"] if d["klass"] == "person"]
        for i, d in enumerate(p_dets):
            if i >= len(spar_lista):
                break
            pid = d["nyckel"].split(":")[-1] if d.get("nyckel") and ":" in d["nyckel"] else d["id"]
            if pid == "okand":
                nod = next((n for n in recept["noder"] if n["klass"] == "person" and not str(n.get("nyckel")).endswith((":A", ":B", ":C"))
                            and sid in n["evidence_shots"]), None)
                pid = nod["id"] if nod else f"gast_{sid}"
            for sp in paket["rorelse"].get(pid, []):
                if sp["tagning"] == sid:
                    sp["spar"] = spar_lista[i]


def bal_offset(paket: dict, ingest: pathlib.Path) -> list[dict]:
    """C1: bålens (c_spine2) läge genom paketets kamera mot SAM:s egen bildprojektion (pose + cam_t_ra, SAM:s fokal)."""
    W, H, S = paket["bild"]["bredd"], paket["bild"]["hojd"], paket["bild"]["sensor_mm"]
    L = {n: i for i, n in enumerate(paket["leder"])}
    IX = {n: i for i, n in enumerate(json.loads((ROT / "scen/3d/kontrakt/tro_rigg.json").read_text(encoding="utf-8"))["namn"])}
    ut = []
    for pid, spl in paket["rorelse"].items():
        for sp in spl:
            if not sp.get("spar"):
                continue
            t = next(t for t in paket["tagningar"] if t["id"] == sp["tagning"])
            q = np.load(ingest / sp["tagning"].upper() / f"sekvens_{sp['spar']}.npz")
            fs = float(q["fokal"])
            a0 = t["ut"][0]
            d_u, d_v = [], []
            for r in sp["rutor"]:
                u = r[0]
                fi = min(u - a0, len(q["pose"]) - 1)
                X = np.array(r[1:], float).reshape(-1, 3) / 1000
                kam = G_ny.kamera_vid(t, u)
                uv, _ = G_ny.proj(X[L["c_spine2"]][None], kam, W, H, S)
                Jcv = F @ (q["pose"][fi, IX["c_spine2"], :3] / 100.0) + q["cam_t_ra"][fi]
                nu = fs * Jcv[0] / Jcv[2] + W / 2
                nv = fs * Jcv[1] / Jcv[2] + H / 2
                d_u.append(uv[0, 0] - nu)
                d_v.append(uv[0, 1] - nv)
            kam0 = t["kamera"]["nycklar"][0]
            ut.append(dict(tagning=sp["tagning"], person=pid, du_bildhojd=round(float(np.median(d_u)) / H, 4),
                           dv_bildhojd=round(float(np.median(d_v)) / H, 4),
                           fel_bildhojd=round(float(np.median(np.hypot(d_u, d_v))) / H, 4),
                           kamera_z=round(kam0[3], 3), lins_mm=kam0[8], f_sam=fs, f_paket=round(kam0[8] / S * W, 1)))
    return ut


def kameralutning(paket: dict) -> list[dict]:
    """C2: kamerornas pitch/roll i paketet (ur kvaternionen)."""
    ut = []
    for t in paket["tagningar"]:
        R = quat_till_mat(t["kamera"]["nycklar"][0][4:8])
        fram = -R[:, 2]
        upp = R[:, 1]
        pitch = math.degrees(math.asin(float(np.clip(fram[2], -1, 1))))
        hoger = R[:, 0]
        roll = math.degrees(math.asin(float(np.clip(hoger[2], -1, 1))))
        ut.append(dict(tagning=t["id"], pitch=round(pitch, 2), roll=round(roll, 2)))
    return ut


def main():
    par = [a.split("=", 1) for a in sys.argv[1:]]
    G_orig = _ladda_original_grindar()
    resultat = {}
    for namn, ing in par:
        ingest = (ROT / ing).resolve() if not pathlib.Path(ing).is_absolute() else pathlib.Path(ing)
        fore_dir = ROT / "forvarld_karna/ut" / namn
        efter_fil = B / "ut" / ingest.name / "paket.json"
        fore = json.loads((fore_dir / "paket.json").read_text(encoding="utf-8"))
        obs = json.loads((fore_dir / "obs.json").read_text(encoding="utf-8"))
        rec = json.loads((fore_dir / "recept.json").read_text(encoding="utf-8"))
        lagg_till_spar(fore, obs, rec, ingest)
        efter = json.loads(efter_fil.read_text(encoding="utf-8")) if efter_fil.exists() else None
        r = dict()
        # C3: rader per (tagning, person)
        person_tagn = sum(len(v) for v in fore["rorelse"].values())
        r["C3"] = dict(person_tagningar_fore=person_tagn, rader_original_grindar=len(G_orig.mat(fore)),
                       rader_nya_grindar_pa_fore=len([x for x in G_ny.mat(fore, ingest, g8_g9=False) if x.get("person")]))
        if efter:
            r["C3"]["person_tagningar_efter"] = sum(len(v) for v in efter["rorelse"].values())
            r["C3"]["rader_nya_grindar_pa_efter"] = len([x for x in G_ny.mat(efter, ingest, g8_g9=False) if x.get("person")])
        # C1: bålens bildläge mot SAM
        r["C1_fore"] = bal_offset(fore, ingest)
        r["C1_efter"] = bal_offset(efter, ingest) if efter else None
        # C2: lutning
        r["C2_fore"] = kameralutning(fore)
        r["C2_efter"] = kameralutning(efter) if efter else None
        # A2 + G7/G8/G9 med nya (oberoende) grindar på båda
        rad_f = G_ny.mat(fore, ingest)
        r["grindar_fore"] = G_ny.sammanfatta(rad_f)
        r["rader_fore"] = rad_f
        r["R25_fore"] = [b for b in fore.get("beslut", []) if b.get("regel") == "R25_separera_kamerarorelse"]
        if efter:
            rad_e = G_ny.mat(efter, ingest)
            r["grindar_efter"] = G_ny.sammanfatta(rad_e)
            r["rader_efter"] = rad_e
        # A3: felinjektion. Originalets grindar och nya grindar på före-paketet; nya grindar på efter-paketet
        r["A3_orig_grindar_pa_fore"] = mutation.kor(fore, lambda p: [dict(x, person=x.get("person")) for x in G_orig.mat(p)])
        r["A3_nya_grindar_pa_fore"] = mutation.kor(fore, lambda p: G_ny.mat(p, ingest))
        if efter:
            r["A3_nya_grindar_pa_efter"] = mutation.kor(efter, lambda p: G_ny.mat(p, ingest))
        resultat[namn] = r
        print(namn, "klar", r["grindar_fore"], r.get("grindar_efter"))
    (HIT / "motprov.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=1,
                                                 default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)), encoding="utf-8")


if __name__ == "__main__":
    main()
