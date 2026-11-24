"""Belägg för två baslinjefynd i GRINDAR-MUTATION.md.

1. z-normaliseringen i scen_brygga.py:329–344 flyttar kroppen OCH kameran; när kameran slår i
   golvet 0.92 m (max(0.92, ...)) flyttas kroppen relativt kameran (z_kropp != 0) och 2D-projektionen
   bryts, men G7 jämför mot en referens som redan innehåller samma flytt.
   Raderna nedan räknar om stegen med samma formler som scen_brygga.py:317–344 (ingen kod där ändras).
2. Överlägg: projicerade T1-leder (rött, huvud = gul ring) mot ingestens 2D-spår (grönt) i tre rutor
   för de tagningar där H7_2d larmar på baslinjen, plus en kontrolltagning.

Kör: scen/.venv/Scripts/python.exe motpart/runda-1-claude/grind_bevis.py
Skriver motpart/runda-1-claude/grind_bevis_h7.png
"""
from __future__ import annotations

import glob
import json
import pathlib
import sys

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
for p in (HIT, ROT / "forvarld_karna", ROT / "byggsten/brygga"):
    sys.path.insert(0, str(p))
import grindar as G  # noqa: E402
import grind_harda as GH  # noqa: E402
from grind_mutation import spar_karta  # noqa: E402


def z_normalisering(klipp):
    import scen_brygga as sb
    import obs_motor
    ut = ROT / "forvarld_karna/ut" / klipp
    obs = json.loads((ut / "obs.json").read_text(encoding="utf-8"))
    rec = json.loads((ut / "recept.json").read_text(encoding="utf-8"))
    paket = json.loads((ut / "paket.json").read_text(encoding="utf-8"))
    ingest = ROT / "scen/3d/ingest/ut" / GH.INGEST[klipp]
    IX = {n: i for i, n in enumerate(json.loads((ROT / "scen/3d/kontrakt/tro_rigg.json").read_text(encoding="utf-8"))["namn"])}
    karta = spar_karta(ingest, obs, rec)
    W = obs["klipp"][0]["kamera"]["bild_px"][0]
    fk = obs_motor._fokal(ingest)
    sitt = {}
    rader = []
    for k in obs["klipp"]:
        sid = k["klipp"]; a0, b0 = k["rutor"]
        cam = next(c for c in rec["kameror"] if c["klipp"] == sid)
        Rc = sb._euler_xyz_till_mat(90.0, 0.0, cam["rotation"][2]); C = np.array(cam["position"], float)
        K = np.load(sorted(glob.glob(str(ingest / sid.upper() / "rum/depth/*.npz")))[0])["intrinsics"]
        kappa = (fk[0] if fk else K[0, 0] * W) / (K[0, 0] * W)
        dets = [d for d in k["detektioner"] if d["klass"] == "person"]
        pids = [p for (s, p) in karta if s == sid]
        for idx, pid in enumerate(pids):
            q = np.load(ingest / sid.upper() / f"sekvens_{karta[(sid, pid)]}.npz")
            n = len(q["pose"]); fot, bak = [], []
            for u in range(a0, b0):
                f = min(u - a0, n - 1); pose = q["pose"][f]; bal = pose[IX["c_spine2"], :3] / 100.0
                c = (pose[:, :3] / 100.0 - bal) + kappa * (bal + q["cam_t_ra"][f] @ sb.F.T)
                w = c @ Rc.T + C
                fot.append(min(w[IX["l_foot"], 2], w[IX["r_foot"], 2])); bak.append(w[IX["c_spine0"], 2])
            mf, mb = float(np.median(fot)), float(np.median(bak))
            pose_lbl = dets[idx]["pose"]
            zs = 0.0
            if pose_lbl == "staende" and mf > 0.08:
                zs = -(mf - sb.FOTLED_OVER_GOLV)
            elif pose_lbl == "sittande":
                mal = sitt.get(pid, 0.55)
                if abs(mb - mal) > 0.08:
                    zs = mal - mb
            if idx == 0:
                ny = max(0.92, C[2] + zs); zk = zs - (ny - C[2]); C = C.copy(); C[2] = ny
            else:
                zk = zs
            if pose_lbl == "sittande" and pid not in sitt:
                sp = next(s for s in paket["rorelse"][pid] if s["tagning"] == sid)
                X = np.array([r[1:] for r in sp["rutor"]], float).reshape(len(sp["rutor"]), -1, 3) / 1000
                sitt[pid] = float(np.median(X[:, paket["leder"].index("c_spine0"), 2]))
            rader.append(dict(klipp=klipp, tagning=sid, person=pid, pose=pose_lbl, ra_fot_z=round(mf, 3), ra_backen_z=round(mb, 3),
                              z_skift=round(zs, 3), kamera_z_recept=cam["position"][2], kamera_z_paket=round(float(C[2]), 3),
                              kropp_mot_kamera_m=round(zk, 3)))
    return rader


def overlagg():
    import cv2
    bilder = []
    for klipp, sid, pid in (("notan", "s7", "B"), ("gelato", "s1", "A"), ("notan", "s1", "A")):
        p = json.loads((ROT / "forvarld_karna/ut" / klipp / "paket.json").read_text(encoding="utf-8"))
        W, H, S = p["bild"]["bredd"], p["bild"]["hojd"], p["bild"]["sensor_mm"]
        L = {n: i for i, n in enumerate(p["leder"])}
        t = next(t for t in p["tagningar"] if t["id"] == sid); a0 = t["ut"][0]
        sp = next(s for s in p["rorelse"][pid] if s["tagning"] == sid)
        X = np.array([r[1:] for r in sp["rutor"]], float).reshape(len(sp["rutor"]), -1, 3) / 1000; U = [r[0] for r in sp["rutor"]]
        ing = ROT / "scen/3d/ingest/ut" / GH.INGEST[klipp]
        spar = json.loads((ing / sid.upper() / "personer.json").read_text(encoding="utf-8"))
        cap = cv2.VideoCapture(str(ing / "klipp" / f"{sid.upper()}.mp4"))
        for i in (len(U) // 5, len(U) // 2, 4 * len(U) // 5):
            u = U[i]; cap.set(cv2.CAP_PROP_POS_FRAMES, u - a0); ok, fr = cap.read()
            if not ok:
                continue
            fr = cv2.resize(fr, (W, H)); s = W / 576
            for v in spar.values():
                if str(u - a0) in v:
                    b = [int(x) for x in v[str(u - a0)]]; cv2.rectangle(fr, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), int(3 * s))
            uv, _ = G.proj(X[i], G.kamera(t, u), W, H, S)
            for q in uv:
                cv2.circle(fr, (int(q[0]), int(q[1])), int(4 * s), (0, 0, 255), -1)
            h = uv[L["c_head"]]; cv2.circle(fr, (int(h[0]), int(h[1])), int(14 * s), (0, 255, 255), int(3 * s))
            cv2.putText(fr, f"{klipp} {sid} {pid} ruta {u}", (int(10 * s), int(40 * s)), cv2.FONT_HERSHEY_SIMPLEX, 0.9 * s, (255, 255, 255), int(2 * s))
            bilder.append(cv2.resize(fr, (288, 512)))
        cap.release()
    ut = HIT / "grind_bevis_h7.png"
    cv2.imwrite(str(ut), np.hstack(bilder))
    return ut


if __name__ == "__main__":
    for k in ("guacamole", "gelato", "asketch", "notan"):
        for r in z_normalisering(k):
            print(json.dumps(r, ensure_ascii=False))
    print(overlagg())
