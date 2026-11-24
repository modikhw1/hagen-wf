"""Brännvidd och lodlinje ur bilden själv, utan tabell per klipp.

Ersätter `obs_motor._fokal` (som slog upp fokalen i en tabell med fyra namngivna klipp, A6) och lodlinjeklämman
(pitch <= 18°, roll <= 8°) som infördes för ett enskilt klipps lutande glas.

Metod (allmän):
- Försvinningspunkter ur LSD-linjer (samma metod som `scen/3d/ingest/fokal_klipp.vp_kandidater`, kopierad hit så att
  inget utanför mappen behöver ändras). Varje ortogonalt par ger en fokalkandidat.
- En telefonprior: 9:16-video från huvudkameran (26 mm ekv. på 4:3-sensor, 16:9-utsnitt, ev. stabiliseringsbeskärning)
  ger fokal/kortsida i [1.25, 1.75], median ~1.45. Den används som svag prior (sigma 0.15 i log) och bär resultatet
  ensam när linjerna inte räcker; då märks fokalen `antagen`.
- Lodlinjen: den vertikala försvinningspunkten (linjer nära bildens y-axel) när den finns, annars läget (mode) bland
  MoGe-normaler nära kamerans upp-prior. Ingen klämning; i stället en prior på telefonens lutning med sigma, och en
  flagga när mätningen ligger långt från priorn.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

PRIOR_F_KVOT = 1.45        # fokal / bildens kortsida (bredd i 9:16)
PRIOR_F_LOGSIGMA = 0.15
VP_INTERVALL = (0.6, 3.0)  # kandidater utanför dessa kvoter av kortsidan kastas (0.6 ~ 80° hfov, 3.0 ~ 19° hfov)
PRIOR_PITCH = (-8.0, 20.0)  # grader (medel, sigma); negativ = tittar nedåt
PRIOR_ROLL = (0.0, 8.0)


def _n(v):
    return v / (np.linalg.norm(v) + 1e-12)


def las_ruta(mp4: Path, ix: int, bredd: int, hojd: int):
    cap = cv2.VideoCapture(str(mp4))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(ix))
    ok, img = cap.read()
    cap.release()
    if not ok or img is None:
        return None
    if img.shape[1] != bredd or img.shape[0] != hojd:
        img = cv2.resize(img, (bredd, hojd))
    return img


def _linjer(img, personmask=None):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    fri = np.full((h, w), 255, np.uint8)
    if personmask is not None:
        pm = cv2.resize(personmask.astype(np.uint8) * 255, (w, h), interpolation=cv2.INTER_NEAREST)
        fri[cv2.dilate(pm, np.ones((25, 25), np.uint8)) > 0] = 0
    L = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(g)[0]
    if L is None:
        return np.zeros((0, 4))
    L = L.reshape(-1, 4)
    mx = ((L[:, 0] + L[:, 2]) / 2).astype(int).clip(0, w - 1)
    my = ((L[:, 1] + L[:, 3]) / 2).astype(int).clip(0, h - 1)
    ln = np.hypot(L[:, 2] - L[:, 0], L[:, 3] - L[:, 1])
    return L[(fri[my, mx] > 0) & (ln > 0.034 * h)]


def _vp_ransac(l, mid, rng, iter=1500, tol_deg=1.8):
    best = None
    for _ in range(iter):
        i, j = rng.choice(len(l), 2, replace=False)
        v = np.cross(l[i], l[j])
        if abs(v[2]) < 1e-9:
            v = v.copy()
        dm = (v[:2] / v[2] if abs(v[2]) > 1e-9 else v[:2] * 1e6) - mid[:, :2]
        ang = np.degrees(np.arccos(np.clip(np.abs(np.sum(
            dm / (np.linalg.norm(dm, axis=1, keepdims=True) + 1e-9) * np.c_[-l[:, 1], l[:, 0]], axis=1)), 0, 1)))
        inl = ang < tol_deg
        if best is None or inl.sum() > best[1].sum():
            best = (v, inl)
    return best


def forsvinningspunkter(img, personmask=None, seed=1, min_inl=12):
    """Upp till tre försvinningspunkter (homogena, bildkoordinater) med antal stödlinjer."""
    rng = np.random.default_rng(seed)
    L = _linjer(img, personmask)
    if len(L) < 25:
        return []
    p1 = np.c_[L[:, 0:2], np.ones(len(L))]
    p2 = np.c_[L[:, 2:4], np.ones(len(L))]
    l = np.cross(p1, p2)
    l /= np.linalg.norm(l[:, :2], axis=1, keepdims=True) + 1e-9
    mid = (p1 + p2) / 2
    vps, rest = [], np.arange(len(l))
    for _ in range(3):
        if len(rest) < 12:
            break
        b = _vp_ransac(l[rest], mid[rest], rng)
        if b is None or b[1].sum() < min_inl:
            break
        vps.append((b[0], int(b[1].sum())))
        rest = rest[~b[1]]
    return vps


def fokal_kandidater(vps, W, H):
    C = np.array([W / 2.0, H / 2.0])
    ut = []
    fin = [(v[:2] / v[2], n) for v, n in vps if abs(v[2]) > 1e-9]
    for a in range(len(fin)):
        for b in range(a + 1, len(fin)):
            f2 = -float((fin[a][0] - C) @ (fin[b][0] - C))
            if f2 > 0:
                f = math.sqrt(f2)
                if VP_INTERVALL[0] * W <= f <= VP_INTERVALL[1] * W:
                    ut.append(f)
    return ut


def bestam_fokal(kandidater: list[float], W: int) -> dict:
    """Robust fusion: median av linjekandidaterna (log), viktad mot telefonpriorn. Returnerar värde, sigma, status, källa."""
    prior = math.log(PRIOR_F_KVOT * W)
    if len(kandidater) >= 4:
        lk = np.log(np.array(kandidater))
        med = float(np.median(lk))
        iqr = float(np.percentile(lk, 75) - np.percentile(lk, 25))
        s_m = max(iqr / 1.35, 0.04) / math.sqrt(max(1, len(lk) / 4))
        w_m, w_p = 1 / s_m ** 2, 1 / PRIOR_F_LOGSIGMA ** 2
        lf = (med * w_m + prior * w_p) / (w_m + w_p)
        s = math.sqrt(1 / (w_m + w_p))
        andel_matt = w_m / (w_m + w_p)
        return dict(v=round(math.exp(lf), 1), s=round(math.exp(lf) * s, 1), status="matt" if andel_matt >= 0.5 else "antagen",
                    kalla=f"försvinningspunkter ({len(kandidater)} kandidater, median {math.exp(med):.0f} px) + telefonprior "
                          f"{PRIOR_F_KVOT:.2f}·bredd; mätandel {andel_matt:.2f}",
                    kandidater=[round(k, 1) for k in kandidater])
    return dict(v=round(math.exp(prior), 1), s=round(math.exp(prior) * PRIOR_F_LOGSIGMA, 1), status="antagen",
                kalla=f"telefonprior {PRIOR_F_KVOT:.2f}·bredd (för få linjekandidater: {len(kandidater)})",
                kandidater=[round(k, 1) for k in kandidater])


def upp_ur_vp(vps, f, W, H):
    """Uppvektorn i OpenCV-kameraram (x höger, y ned, z fram) ur den vertikala försvinningspunkten, eller None."""
    best = None
    for v, n in vps:
        d = np.array([v[0] - v[2] * W / 2.0, v[1] - v[2] * H / 2.0, v[2] * f])
        d = _n(d)
        if d[1] > 0:
            d = -d  # uppåt = negativ y i bilden
        vinkel = math.degrees(math.acos(min(1.0, abs(d[1]))))
        if vinkel < 35 and (best is None or n > best[1]):
            best = (d, n, vinkel)
    return best


def upp_ur_normaler(Nm: np.ndarray, giltig: np.ndarray, prior_upp: np.ndarray):
    """Läget (mode) bland horisontella ytnormaler nära priorn, med medelvärdesförskjutning (10°-fönster)."""
    n = Nm[giltig]
    if len(n) > 60000:
        n = n[np.linspace(0, len(n) - 1, 60000).astype(int)]
    nara = n[(n @ prior_upp) > math.cos(math.radians(35))]
    if len(nara) < 1500:
        return None
    u = _n(np.median(nara, 0))
    for _ in range(12):
        sel = nara[(nara @ u) > math.cos(math.radians(10))]
        if len(sel) < 500:
            break
        u2 = _n(sel.mean(0))
        if float(u2 @ u) > math.cos(math.radians(0.05)):
            u = u2
            break
        u = u2
    stod = int(((nara @ u) > math.cos(math.radians(10))).sum())
    return u, stod, len(nara)


def pitch_roll(u):
    pitch = math.degrees(math.asin(float(np.clip(u[2], -1, 1))))
    roll = -math.degrees(math.asin(float(np.clip(u[0], -1, 1))))
    return pitch, roll


def bestam_upp(img, personmask, Nm, giltig, f, W, H) -> dict:
    """Lodlinje: vertikal försvinningspunkt först, annars normalläge; prior-avvikelse flaggas, kläms inte."""
    prior = np.array([0.0, -math.cos(math.radians(8)), -math.sin(math.radians(8))])
    vp = upp_ur_vp(forsvinningspunkter(img, personmask), f, W, H) if img is not None else None
    nm = upp_ur_normaler(Nm, giltig, prior) if Nm is not None else None
    kandidater = []
    if vp is not None and vp[1] >= 15:
        kandidater.append(("vertikal försvinningspunkt", vp[0], 2.0, vp[1]))
    if nm is not None and nm[1] >= 1500:
        kandidater.append(("MoGe-normalernas läge", nm[0], 3.5, nm[1]))
    flaggor = []
    if len(kandidater) == 2:
        vinkel = math.degrees(math.acos(min(1.0, float(kandidater[0][1] @ kandidater[1][1]))))
        if vinkel <= 6.0:
            w0, w1 = 1 / kandidater[0][2] ** 2, 1 / kandidater[1][2] ** 2
            u = _n(kandidater[0][1] * w0 + kandidater[1][1] * w1)
            kalla, sigma, status = f"VP + normaler (överens, {vinkel:.1f}°)", 1.8, "matt"
        else:
            u, kalla, sigma, status = kandidater[0][1], f"vertikal försvinningspunkt (normalläget avviker {vinkel:.1f}°)", 3.0, "matt"
            flaggor.append(f"lodlinje_konflikt_{vinkel:.0f}deg")
    elif len(kandidater) == 1:
        u, kalla, sigma, status = kandidater[0][1], kandidater[0][0], kandidater[0][2] + 1.0, "matt"
    else:
        u, kalla, sigma, status = prior, "telefonprior (ingen mätning)", 10.0, "antagen"
    p, r = pitch_roll(u)
    if abs(p - PRIOR_PITCH[0]) > 3 * PRIOR_PITCH[1] or abs(r - PRIOR_ROLL[0]) > 3 * PRIOR_ROLL[1]:
        flaggor.append("lutning_utanfor_prior_3sigma")
    return dict(u=u, pitch=p, roll=r, sigma=sigma, kalla=kalla, status=status, flaggor=flaggor,
                vp_stod=(vp[1] if vp else 0), normal_stod=(nm[1] if nm else 0))
