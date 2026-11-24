"""Personidentitet över tagningar och hållning, utan deklaration, utan VLM-semantik och utan mappnamn (A6).

Ersätter `obs_motor._roller_ur_kalla`, som i praktiken hämtade Gemini-semantik via mappnamnets prefix (ett påhittat
klipp `a-…` fick ett annat klipps roller) och vars geometriska reserv gav fel identitet eller hållning på 5/5 klipp.

Signaler (alla ur ingestens egna filer för klippet, inga namnuppslag):
- utseende: HSV-histogram av överkroppen (YOLO-rutan i `personer.json`, personmasken i `masker.npy`, rutor ur
  `klipp/<tagning>.mp4`), medel över upp till 8 rutor;
- kroppsproportioner: SAM 3D Bodys benlängder (axelbredd, bål, överarm, underarm) i meter;
- bakgrund: tagningar som delar kameraplats enligt SIFT (`rum_grupper`) ger ett svagt tillägg för samma person.
Spår i samma tagning kan aldrig vara samma person (kan-inte-länka). Hierarkisk sammanslagning med medelavstånd och en
fast tröskel; varje identitet bär sin marginal till tröskeln, och små marginaler märks `antagen`.

Hållning (sittande/stående) ur lårets vinkel mot lodlinjen i kameraramen. När benen inte syns (`ben_synliga` < 30 %)
bygger hållningen på SAM:s gissade ben och märks `antagen`.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import numpy as np

F = np.diag([1.0, -1.0, -1.0])
TROSKEL = 0.62          # sammanslagningströskel (avstånd 0..~2); egen diagnos, inte krav
MARGINAL_SAKER = 0.12   # avstånd under TROSKEL - marginal räknas som säkrare
SIFT_BONUS = 0.20


def _hist(img_bgr, box, mask=None):
    H, W = img_bgr.shape[:2]
    x0, y0, x1, y1 = [float(v) for v in box]
    bw, bh = x1 - x0, y1 - y0
    if bw < 8 or bh < 8:
        return None
    a0, a1 = int(max(0, x0 + 0.2 * bw)), int(min(W, x1 - 0.2 * bw))
    b0, b1 = int(max(0, y0 + 0.15 * bh)), int(min(H, y0 + 0.55 * bh))
    if a1 - a0 < 4 or b1 - b0 < 4:
        return None
    patch = img_bgr[b0:b1, a0:a1]
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    m = None
    if mask is not None:
        mm = cv2.resize(mask.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)[b0:b1, a0:a1]
        if mm.sum() > 30:
            m = (mm * 255).astype(np.uint8)
    h = cv2.calcHist([hsv], [0, 1, 2], m, [12, 4, 4], [0, 180, 0, 256, 0, 256]).ravel()
    s = h.sum()
    return h / s if s > 0 else None


def _benlangder(q, IX):
    P = q["pose"][:, :, :3] / 100.0
    def L(a, b):
        return float(np.median(np.linalg.norm(P[:, IX[a]] - P[:, IX[b]], axis=1)))
    return np.array([
        L("l_uparm", "r_uparm"), L("c_spine0", "c_neck"),
        (L("l_uparm", "l_lowarm") + L("r_uparm", "r_lowarm")) / 2,
        (L("l_lowarm", "l_wrist") + L("r_lowarm", "r_wrist")) / 2,
    ])


def spar_i_klipp(ingest: Path, tagningar: list[str], IX: dict) -> list[dict]:
    """Alla personspår med sekvens: utseende, proportioner, längd och tagningens andel."""
    ut = []
    for S in tagningar:
        mapp = ingest / S
        pf = mapp / "personer.json"
        if not pf.exists():
            continue
        sp = json.loads(pf.read_text(encoding="utf-8"))
        meta = json.loads((mapp / "meta.json").read_text(encoding="utf-8"))
        N, W, H = meta["N"], meta["bredd"], meta["hojd"]
        mask = np.load(mapp / "masker.npy") if (mapp / "masker.npy").exists() else None
        mp4 = ingest / "klipp" / f"{S}.mp4"
        cap = cv2.VideoCapture(str(mp4)) if mp4.exists() else None
        rutor = {}
        for s, boxar in sp.items():
            if not (mapp / f"sekvens_{s}.npz").exists():
                continue
            q = np.load(mapp / f"sekvens_{s}.npz")
            nyckel = sorted(boxar, key=lambda k: int(k))
            urval = [nyckel[int(i)] for i in np.linspace(0, len(nyckel) - 1, min(8, len(nyckel)))] if nyckel else []
            hs = []
            for k in urval:
                fi = int(k)
                if cap is None:
                    break
                if fi not in rutor:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
                    ok, img = cap.read()
                    rutor[fi] = cv2.resize(img, (W, H)) if ok and img is not None else None
                img = rutor[fi]
                if img is None:
                    continue
                h = _hist(img, boxar[k], mask[fi] if mask is not None and fi < len(mask) else None)
                if h is not None:
                    hs.append(h)
            boxh = np.median([b[3] - b[1] for b in boxar.values()]) / H if boxar else 0.0
            ut.append(dict(
                tagning=S, spar=s, n=len(boxar), andel=len(boxar) / max(N, 1), box_hojd=float(boxh),
                hist=(np.mean(hs, 0) if hs else None), ben=_benlangder(q, IX),
                ben_synliga=float(q["ben_synliga"].mean()), kand=float(q["kand"].mean()),
            ))
        if cap is not None:
            cap.release()
    return ut


def _avst(a, b, sift_par: set):
    d = 0.0
    if a["hist"] is not None and b["hist"] is not None:
        bc = float(np.sum(np.sqrt(a["hist"] * b["hist"])))
        d_h = math.sqrt(max(0.0, 1.0 - bc))      # Hellinger 0..1
    else:
        d_h = 0.5
    rel = np.abs(a["ben"] - b["ben"]) / ((a["ben"] + b["ben"]) / 2 + 1e-6)
    d_b = float(np.clip(np.mean(rel) / 0.12, 0, 1.5))  # 12 % medelavvikelse ~ 1
    d = 1.2 * d_h + 0.5 * d_b
    if (a["tagning"], b["tagning"]) in sift_par or (b["tagning"], a["tagning"]) in sift_par:
        d -= SIFT_BONUS
    return d


def klustra(spar: list[dict], sift_koppling: dict[str, str]) -> tuple[list[int], list[dict]]:
    """Hierarkisk sammanslagning (medelavstånd) med kan-inte-länka inom tagning. Returnerar etikett per spår + logg."""
    sift_par = set()
    for a, b in sift_koppling.items():
        sift_par.add((a.upper(), b.upper()))
    # transitiv stängning av SIFT-grupper
    grupper: dict[str, str] = {}
    for a, b in sift_par:
        grupper[a] = grupper.get(b, b)
    sift_par |= {(a, c) for a, c in grupper.items()}
    n = len(spar)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            D[i, j] = D[j, i] = _avst(spar[i], spar[j], sift_par)
    kl = [[i] for i in range(n)]
    logg = []
    while True:
        bast = None
        for a in range(len(kl)):
            for b in range(a + 1, len(kl)):
                ta = {spar[i]["tagning"] for i in kl[a]}
                tb = {spar[i]["tagning"] for i in kl[b]}
                if ta & tb:
                    continue
                d = float(np.mean([D[i, j] for i in kl[a] for j in kl[b]]))
                if bast is None or d < bast[0]:
                    bast = (d, a, b)
        if bast is None or bast[0] > TROSKEL:
            if bast is not None:
                logg.append(dict(stoppade_vid=round(bast[0], 3)))
            break
        d, a, b = bast
        logg.append(dict(slog_ihop=[f"{spar[i]['tagning']}:{spar[i]['spar']}" for i in kl[a] + kl[b]], avstand=round(d, 3),
                         status="matt" if d < TROSKEL - MARGINAL_SAKER else "antagen"))
        kl[a] = kl[a] + kl[b]
        del kl[b]
    etik = [0] * n
    for k, medl in enumerate(kl):
        for i in medl:
            etik[i] = k
    return etik, logg


def hallning(q, IX, u_opencv: np.ndarray) -> tuple[str, float, str]:
    """Lårets vinkel mot lodlinjen (median över rutor). > 50° sittande, < 32° stående, däremellan oklar."""
    P = q["pose"][:, :, :3] / 100.0   # SAM:s pose i Blenders kameraorientering (y upp, z bakåt)
    ned = -(F @ u_opencv)
    v = []
    for s in ("l", "r"):
        lar = P[:, IX[f"{s}_lowleg"]] - P[:, IX[f"{s}_upleg"]]
        lar = lar / (np.linalg.norm(lar, axis=1, keepdims=True) + 1e-9)
        v.append(np.degrees(np.arccos(np.clip(lar @ ned, -1, 1))))
    vinkel = float(np.median(np.concatenate(v)))
    if vinkel > 50:
        pose = "sittande"
    elif vinkel < 32:
        pose = "staende"
    else:
        pose = "sittande" if vinkel >= 41 else "staende"
    status = "matt" if float(q["ben_synliga"].mean()) >= 0.3 and (vinkel > 50 or vinkel < 32) else "antagen"
    return pose, round(vinkel, 1), status
