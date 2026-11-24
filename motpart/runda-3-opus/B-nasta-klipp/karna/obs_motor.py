"""Lager 1, allmän version: observationer per tagning ur ingestmappen, utan deklaration, VLM eller klippnamn.

Ändringar mot `forvarld_karna/obs_motor.py` (källhash i `../original_kopia/SHA256_kalla.txt`):
- A6: ingen fokaltabell per klippnamn (`_fokal`), ingen semantik via mappnamn (`_modell_semantik`), ingen deklaration,
  ingen VLM-mapp. Fokal ur försvinningspunkter + telefonprior (`fokal.py`), identitet ur utseende + proportioner
  (`identitet.py`).
- Lodlinjen kläms inte (pitch <= 18°, roll <= 8° var införd för ett klipp); vertikal försvinningspunkt + normalläge,
  med prior och flagga (`fokal.bestam_upp`).
- Fokalbyte bevarar bildläget: SAM:s och MoGe:s djup skalas med kappa = f/f_kedja längs optiska axeln, sidoläget i meter
  är oförändrat (C1, samma princip som runda 1:s P1).
- Kamerahöjd ur fysiska priorer med osäkerhet: synliga fötter mot golvet, MoGe-golvplan, sittande bäckenhöjd,
  telefonhöjd. Ingen klämning (0,86 m vid bord) och ingen fast axelhöjd per hållning. Andelen mätt mot antagen redovisas.
- Bord/diskar ur MoGe-ytnormaler som sammanhängande vågräta skivor (flera per tagning, relativa pixelgränser), med
  uppmätt skivhöjd över golvet. Inga VLM-föremål, dörrar eller ljus (finns inte för ett nytt klipp utan betalda anrop).
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
from collections import Counter

import cv2
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))
from schema import M, Detektion, Kamera, KlippObs, Observationer, Stralar, Vagg  # noqa: E402
import fokal as FOK  # noqa: E402
import identitet as ID  # noqa: E402

ROT = HIT.parents[3]
F = np.diag([1.0, -1.0, -1.0])
PRIOR_KAMERAHOJD = (1.35, 0.35)      # telefon i hand/stativ (m)
PRIOR_SITT_BACKEN = (0.55, 0.15)     # sittande bäckenled över golvet (stol 0,45 + ~0,1); täcker barstol vid 2 sigma
STATUR_SKALA = (0.88, 1.12)          # tillåten personlig strålskala (≈ ±2 sigma på vuxen kroppslängd)
SKIVA_MIN_ANDEL = 0.015              # sammanhängande vågrät skiva >= 1,5 % av djupkartan


def _n(v):
    return v / (np.linalg.norm(v) + 1e-12)


def leder():
    namn = json.loads((ROT / "scen/3d/kontrakt/tro_rigg.json").read_text(encoding="utf-8"))["namn"]
    return {n: i for i, n in enumerate(namn)}


def tagningar_i(ingest: pathlib.Path) -> list[str]:
    t = [p.name for p in ingest.iterdir() if p.is_dir() and p.name[:1] == "S" and p.name[1:].isdigit()
         and (p / "meta.json").exists() and list((p / "rum/depth").glob("*.npz"))]
    return sorted(t, key=lambda s: int(s[1:]))


def kamerapunkter(q, kappa: float, s: float = 1.0) -> np.ndarray:
    """SAM-leder i Blenders kameraram (x höger, y upp, z bakåt), meter. Djupet längs optiska axeln skalas med kappa
    (fokalbyte med bevarat bildläge för bålen) och hela personen med s kring kamerans centrum (bildläget bevaras)."""
    IXs = leder()
    pose_b = q["pose"][:, :, :3] / 100.0
    ct_b = q["cam_t_ra"] @ F.T
    sp2 = IXs["c_spine2"]
    bal = pose_b[:, sp2] + ct_b
    bal_k = bal * np.array([1.0, 1.0, kappa])
    return s * (pose_b - pose_b[:, sp2:sp2 + 1]) + s * bal_k[:, None, :]


class Tagning:
    """En tagnings mätningar i en vågrät ram (OpenCV-kameraram: x höger, y ned, z fram)."""

    def __init__(self, ingest: pathlib.Path, S: str, f_px: float):
        self.S = S
        self.mapp = mapp = ingest / S
        self.meta = json.loads((mapp / "meta.json").read_text(encoding="utf-8"))
        self.W, self.H, self.N = self.meta["bredd"], self.meta["hojd"], self.meta["N"]
        self.rum = json.loads((mapp / "rum.json").read_text(encoding="utf-8")) if (mapp / "rum.json").exists() else {}
        filer = sorted((mapp / "rum/depth").glob("*.npz"))
        df = min(filer, key=lambda f: abs(int(f.stem) - self.N // 2))
        self.ruta = int(df.stem)
        z = np.load(df)
        K = z["intrinsics"]
        self.f_kedja = float(K[0, 0] * self.W)
        self.f = float(f_px)
        self.kappa = self.f / self.f_kedja
        self.D = z["depth"].astype(float) * self.kappa
        self.Nm = z["normal"].astype(float)
        hd, wd = self.D.shape
        fx = self.f * wd / self.W
        cx, cy = K[0, 2] * wd, K[1, 2] * hd
        v, u = np.mgrid[0:hd, 0:wd]
        self.P = np.stack([(u - cx) / fx * self.D, (v - cy) / fx * self.D, self.D], -1)
        self.giltig = np.isfinite(self.D) & (self.D > 0.05)
        self.uv = (fx, fx, cx, cy, wd, hd)
        self.mask = np.load(mapp / "masker.npy") if (mapp / "masker.npy").exists() else None
        self.mp4 = ingest / "klipp" / f"{S}.mp4"
        self.bild = FOK.las_ruta(self.mp4, self.ruta, self.W, self.H) if self.mp4.exists() else None
        pm = self.mask[self.ruta] if self.mask is not None and self.ruta < len(self.mask) else None
        self.lod = FOK.bestam_upp(self.bild, pm, self.Nm, self.giltig, self.f, self.W, self.H)
        self.u = self.lod["u"]
        self.fh = _n(np.array([0, 0, 1.0]) - self.u[2] * self.u)
        self.rh = _n(np.cross(self.fh, self.u))
        self.pitch, self.roll = self.lod["pitch"], self.lod["roll"]

    def hor(self, p):
        x, z = float(p @ self.rh), float(p @ self.fh)
        return math.degrees(math.atan2(x, z)), math.hypot(x, z)

    def hor_xy(self, p):
        return np.array([float(p @ self.rh), float(p @ self.fh)])

    def golvplan(self):
        """Lägsta dominerande vågräta plan i MoGe-djupet (höjd relativt kameran, längs upp), eller None."""
        ok = self.giltig & ((self.Nm @ self.u) > math.cos(math.radians(15)))
        h = self.P[ok] @ self.u
        d = self.D[ok]
        sel = h < -0.5
        if sel.sum() < 0.02 * self.giltig.sum():
            return None
        h, d = h[sel], d[sel]
        hist, kant = np.histogram(h, bins=np.arange(-3.0, -0.45, 0.05))
        if hist.sum() == 0:
            return None
        tro = hist >= max(0.15 * hist.max(), 0.01 * self.giltig.sum())
        if not tro.any():
            return None
        i = int(np.argmax(tro))  # lägsta tröga band
        band = (h >= kant[i] - 0.05) & (h <= kant[i] + 0.10)
        if band.sum() < 0.01 * self.giltig.sum():
            return None
        spann = float(np.percentile(d[band], 90) - np.percentile(d[band], 10))
        if spann < 0.8:
            return None
        hv = float(np.median(h[band]))
        return dict(h_rel=hv, djup=float(np.median(d[band])), andel=float(band.sum() / self.giltig.sum()), spann=spann)

    def skivor(self, pers_djup: float, golv_rel: float | None):
        """Sammanhängande vågräta skivor under kameran och över golvet (bord, diskar, bänkar), höjd relativt kameran."""
        hor = self.giltig & ((self.Nm @ self.u) > math.cos(math.radians(25)))
        hrel = np.where(self.giltig, (self.P @ self.u), np.nan)
        lagst = (golv_rel + 0.30) if golv_rel is not None else -1.65
        kand = hor & (hrel > lagst) & (hrel < 0.15) & (self.D < pers_djup + 1.2)
        if kand.sum() < SKIVA_MIN_ANDEL * self.giltig.sum():
            return []
        n, lab, stats, _ = cv2.connectedComponentsWithStats(kand.astype(np.uint8), connectivity=8)
        ut = []
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < SKIVA_MIN_ANDEL * self.giltig.sum():
                continue
            m = lab == i
            pts = self.P[m]
            hr = hrel[m]
            ut.append(dict(p=np.median(pts, 0), rel=float(np.median(hr)), rel_s=float(max(0.03, np.std(hr))),
                           andel=float(area / self.giltig.sum()),
                           bredd=float(np.percentile(pts @ self.rh, 90) - np.percentile(pts @ self.rh, 10)),
                           djup_spann=float(np.percentile(pts @ self.fh, 90) - np.percentile(pts @ self.fh, 10))))
        return sorted(ut, key=lambda s: -s["andel"])[:3]


def _vaggar(t: Tagning, pers_djup: float):
    vaggar = []
    dmax = float(np.percentile(t.D[t.giltig], 98)) * 1.1 if t.giltig.any() else 6.0
    for w in t.rum.get("walls", []):
        n = np.array(w["normal"], dtype=float)
        n2 = _n(n)
        d2 = float(w["distance"]) * t.kappa
        if abs(n2 @ t.u) > 0.25:
            continue
        b, avst = t.hor(d2 * n2)
        if 0.3 < avst < dmax:
            vaggar.append((b, avst, "rum.json"))
    bak = pers_djup + 0.1
    n = t.Nm[t.giltig]
    P = t.P[t.giltig]
    vert = np.abs(n @ t.u) < 0.15
    dist = np.hypot(P @ t.rh, P @ t.fh)
    urval = vert & (dist > bak) & (dist < dmax)
    if urval.sum() > 0.03 * len(P):
        ang = np.degrees(np.arctan2(n[urval] @ t.rh, n[urval] @ t.fh))
        hist, kant = np.histogram(ang, bins=36, range=(-180, 180))
        topp = kant[np.argmax(hist)] + 5
        nara = np.abs((ang - topp + 180) % 360 - 180) < 15
        if nara.sum() > 0.02 * len(P):
            nn = _n(np.median(n[urval][nara], 0))
            off = float(np.median(P[urval][nara] @ nn))
            b, avst = t.hor(off * nn)
            if 0.3 < avst < dmax and not any(abs((b - v[0] + 180) % 360 - 180) < 20 for v in vaggar):
                vaggar.append((b, avst, "ytor bakom personen"))
    return vaggar


def _manhattan(t: Tagning):
    n = t.Nm[t.giltig]
    P = t.P[t.giltig]
    vert = np.abs(n @ t.u) < 0.15
    if vert.sum() < 1000:
        return None
    psi = np.arctan2(n[vert] @ t.rh, n[vert] @ t.fh)
    w = np.hypot(P[vert] @ t.rh, P[vert] @ t.fh) ** 2
    c = np.sum(w * np.exp(4j * psi)) / np.sum(w)
    m = math.degrees(np.angle(c) / 4)
    R = abs(c)
    if R < 0.6:
        return None
    s = math.degrees(math.sqrt(max(-2 * math.log(max(R, 1e-6)), 0)) / 4)
    return M(v=round(m, 2), s=round(min(max(s, 2.0), 25.0), 2))


def _stralar(t: Tagning, hfov, pers):
    P = t.P[t.giltig]
    n = t.Nm[t.giltig]
    h = P @ t.u
    band = (h > -0.40) & (h < 0.9) & (np.abs(n @ t.u) < 0.7)
    b = np.degrees(np.arctan2(P[band] @ t.rh, P[band] @ t.fh))
    d = np.hypot(P[band] @ t.rh, P[band] @ t.fh)
    halv = hfov / 2 - 2
    bear, fri = [], []
    for bb in np.linspace(-halv, halv, 11):
        sel = np.abs(b - bb) < 1.5
        v = float(np.percentile(d[sel], 10)) if sel.sum() > 20 else 12.0
        for p in pers:
            pb, pd = t.hor(p["p"])
            if abs(math.radians(bb - pb)) * pd < 0.25:
                v = min(v, pd - 0.2)
        bear.append(round(float(bb), 2))
        fri.append(round(max(v, 0.3), 3))
    return Stralar(bearing_deg=bear, fri_m=fri)


def _takhojd(t: Tagning, hcam):
    n = t.Nm[t.giltig]
    P = t.P[t.giltig]
    h = P @ t.u
    tak = (n @ t.u < -0.85) & (h > 0.3)
    if tak.sum() < 0.01 * len(P):
        return None
    return M(v=round(float(np.median(h[tak])) + hcam, 3), s=0.35)


def fokal_for_klipp(ingest: pathlib.Path, tagn: list[str]) -> dict:
    kand_alla, per = [], {}
    W = None
    for S in tagn:
        meta = json.loads((ingest / S / "meta.json").read_text(encoding="utf-8"))
        W, H = meta["bredd"], meta["hojd"]
        mp4 = ingest / "klipp" / f"{S}.mp4"
        mask = np.load(ingest / S / "masker.npy") if (ingest / S / "masker.npy").exists() else None
        k_s = []
        for q in (0.2, 0.5, 0.8):
            ix = int(q * (meta["N"] - 1))
            img = FOK.las_ruta(mp4, ix, W, H) if mp4.exists() else None
            if img is None:
                continue
            pm = mask[ix] if mask is not None and ix < len(mask) else None
            k_s += FOK.fokal_kandidater(FOK.forsvinningspunkter(img, pm), W, H)
        per[S] = k_s
        kand_alla += k_s
    klipp = FOK.bestam_fokal(kand_alla, W)
    per_tagn = {}
    for S, k_s in per.items():
        egen = FOK.bestam_fokal(k_s, W) if len(k_s) >= 6 else None
        # egen fokal bara vid tydlig avvikelse med eget stöd (zoom); annars klippets värde
        if egen and egen["status"] == "matt" and abs(math.log(egen["v"] / klipp["v"])) > 0.30:
            per_tagn[S] = dict(egen, kalla="egen tagning (avviker > 35 % från klippet): " + egen["kalla"])
        else:
            per_tagn[S] = dict(klipp)
    return dict(klipp=klipp, tagningar=per_tagn)


def _sift_kameragrupper(ingest: pathlib.Path, cache: pathlib.Path | None = None) -> dict[str, str]:
    """SIFT/MAGSAC-grupper ur `scen/3d/ingest/rum_grupper.py` (allmän; cachen skrivs bara i utmappen)."""
    sys.path.insert(0, str(ROT / "scen/3d/ingest"))
    try:
        cf = cache / "sift_grupper.json" if cache else None
        if cf is not None and cf.exists():
            res = json.loads(cf.read_text(encoding="utf-8"))
        else:
            import rum_grupper
            res = rum_grupper.mat_grupper(ingest)
            if cf is not None:
                cf.parent.mkdir(parents=True, exist_ok=True)
                cf.write_text(json.dumps(res, ensure_ascii=False, default=str), encoding="utf-8")
        koppling = {}
        for grp in res.get("delar_plats", []):
            if len(grp) >= 2:
                bas = grp[0].lower()
                for medlem in grp[1:]:
                    koppling[medlem.lower()] = bas
        return koppling
    except Exception as e:  # noqa: BLE001
        print("  SIFT-gruppering misslyckades:", e)
        return {}


MOBELKLASS = {"matbord": (0.75, 0.03, 0.45), "disk": (0.92, 0.04, 0.27), "bardisk": (1.08, 0.05, 0.18),
              "monter": (1.22, 0.06, 0.10)}  # höjd, sigma, prior (monter = kyl-/glasdisk med glasöverbyggnad)
SITT = {"stol": (0.55, 0.07), "barstol": (0.85, 0.07)}       # bäckenled över golvet
STA_BACKEN = (0.97, 0.08)                                    # stående vuxens bäckenled över golvet
BACKEN_MOT_SKIVA = {"sitter": (-0.20, 0.09), "star": (-0.05, 0.18)}  # bäcken minus skivans topp, när personen är vid skivan


def _gauss_marginal(led):
    """led: [(x, s)] för samma okända h. Returnerar (h, sigma, logL), logL = log av integralen av produkten av N(x_i; h, s_i)."""
    w = np.array([1 / s ** 2 for _, s in led])
    x = np.array([v for v, _ in led])
    h = float((w * x).sum() / w.sum())
    logL = -0.5 * float((w * (x - h) ** 2).sum()) + 0.5 * math.log(1 / w.sum()) - float(np.log([s for _, s in led]).sum())
    return h, math.sqrt(1 / w.sum()), logL


def hojd_och_hallning(t: Tagning, personer: list[dict], skivor: list[dict], golv: dict | None, fixerad: dict | None = None) -> dict:
    """Kamerahöjd, hållning för personer utan synliga ben och möbelklass, prövade tillsammans.

    Fysiska priorer (med osäkerhet, inga konstanter per klipp): möbelklasser med kända höjder (matbord 0,75, disk 0,92,
    bardisk 1,08 m), sittande bäcken på stol (0,55) eller barstol (0,85), stående med fötter på golvet, telefonens höjd.
    Mätningar: MoGe-golvplan, synliga fötter, skivornas höjd relativt kameran och bäckenets höjd relativt skivan
    (oberoende av kamerahöjden). Alla kombinationer av diskreta val prövas; vinnaren och dess sannolikhet redovisas."""
    import itertools
    bas = [("telefonprior", PRIOR_KAMERAHOJD[0], PRIOR_KAMERAHOJD[1], False)]
    if golv is not None:
        bas.append(("MoGe-golvplan", -golv["h_rel"], 0.05 + 0.04 * golv["djup"], True))
    fria = []
    for i, p in enumerate(personer):
        if p["fot_synlig"] >= 0.3:
            bas.append((f"synliga fötter ({p['spar']})", -p["fot_rel"], 0.04 + 0.03 * p["djup"], True))
        else:
            fria.append(i)
    nara = {}
    for i, p in enumerate(personer):
        best = None
        for j, sk in enumerate(skivor):
            d = float(np.linalg.norm(t.hor_xy(sk["p"]) - t.hor_xy(p["p_hor"])))
            if d < 1.2 and (best is None or d < best[1]):
                best = (j, d)
        if best:
            nara[i] = best[0]
    val_person = [("star",), ("sitter", "stol"), ("sitter", "barstol")]
    def nyckel(v):
        return v[0] if len(v) == 1 else f"{v[0]}:{v[1]}"
    alternativ = []
    for i in fria:
        fx = (fixerad or {}).get(personer[i].get("roll"))
        alternativ.append([v for v in val_person if fx is None or nyckel(v) == fx])
    hyp = []
    for pv in itertools.product(*alternativ):
        for kv in itertools.product(list(MOBELKLASS), repeat=len(skivor)):
            led = list(bas)
            logp = 0.0
            for i, v in zip(fria, pv):
                p = personer[i]
                if v[0] == "star":
                    led.append((f"stående, fötterna gissade ({p['spar']})", -p["fot_rel"], 0.15, False))
                    # stående kräver också att bäckenet står i stående höjd: gissade ben som är kortare än en stående
                    # persons ben (sittande ben) ger då motstridiga ledtrådar och straffas
                    led.append((f"stående bäcken ({p['spar']})", STA_BACKEN[0] - p["backen_rel"], STA_BACKEN[1], False))
                    logp += math.log(0.5)
                else:
                    mu, sg = SITT[v[1]]
                    led.append((f"sittande på {v[1]} ({p['spar']})", mu - p["backen_rel"], sg, False))
                    logp += math.log(0.25)
            for j, k in enumerate(kv):
                mu, sg, pr = MOBELKLASS[k]
                led.append((f"skiva {j + 1} som {k}", mu - skivor[j]["rel"], math.hypot(sg, skivor[j]["rel_s"]), False))
                logp += math.log(pr)
            for i, p in enumerate(personer):
                if i not in nara:
                    continue
                v = pv[fria.index(i)][0] if i in fria else ("sitter" if p["pose"] == "sittande" else "star")
                mu, sg = BACKEN_MOT_SKIVA[v]
                dd = p["backen_rel"] - skivor[nara[i]]["rel"]
                logp += -0.5 * ((dd - mu) / sg) ** 2 - math.log(sg)
            h, sh, logL = _gauss_marginal([(x, sx) for _, x, sx, _ in led])
            hyp.append((logp + logL, h, sh, pv, kv, led))
    hyp.sort(key=lambda x: -x[0])
    lv = np.array([x[0] for x in hyp])
    post = np.exp(lv - lv.max())
    post /= post.sum()
    _, h, sh, pv, kv, led = hyp[0]
    w = np.array([1 / x[2] ** 2 for x in led])
    matt_andel = float(sum(wi for wi, x in zip(w, led) if x[3]) / w.sum())
    pose_ut = {}
    for i, p in enumerate(personer):
        if i in fria:
            v = pv[fria.index(i)]
            pm = float(sum(pp for pp, x in zip(post, hyp) if x[3][fria.index(i)][0] == v[0]))
            pose_ut[i] = ("sittande" if v[0] == "sitter" else "staende", v[1] if len(v) > 1 else None, round(pm, 3), "antagen")
        else:
            pose_ut[i] = (p["pose"], None, 1.0, "matt (benen syns)")
    flaggor = [f"avviker:{n}:{x:.2f}" for n, x, sx, m in led if m and abs(x - h) > 2.5 * math.hypot(sx, sh)]
    per_val = {}
    for i in fria:
        r = personer[i].get("roll")
        if r is None:
            continue
        d = {}
        for x, l in zip(hyp, lv):
            k = nyckel(x[3][fria.index(i)])
            d[k] = np.logaddexp(d.get(k, -np.inf), l)
        tot = np.logaddexp.reduce(list(d.values()))
        per_val[r] = {k: float(v - tot) for k, v in d.items()}
    return dict(v=round(h, 3), s=round(sh, 3), status="matt" if matt_andel >= 0.5 else "antagen", matt_andel=round(matt_andel, 2),
                p_vinnare=round(float(post[0]), 3), antal_hypoteser=len(hyp),
                ledtradar=[dict(namn=n, v=round(x, 3), s=round(sx, 3), matt=m) for n, x, sx, m in led],
                mobelklass=[dict(skiva=j + 1, klass=k, p=round(float(sum(pp for pp, x in zip(post, hyp) if x[4][j] == k)), 3))
                            for j, k in enumerate(kv)],
                pose=pose_ut, flaggor=flaggor, per_val=per_val)


def bygg(ingest: pathlib.Path, cache: pathlib.Path | None = None) -> tuple[Observationer, dict]:
    IX = leder()
    tagn = tagningar_i(ingest)
    ff = cache / "fokal.json" if cache else None
    if ff is not None and ff.exists():
        fok = json.loads(ff.read_text(encoding="utf-8"))
    else:
        fok = fokal_for_klipp(ingest, tagn)
        if ff is not None:
            ff.parent.mkdir(parents=True, exist_ok=True)
            ff.write_text(json.dumps(fok, ensure_ascii=False), encoding="utf-8")
    sift = _sift_kameragrupper(ingest, cache)

    # --- identitet över tagningar (utseende + proportioner + SIFT-bakgrund) ---
    spar = ID.spar_i_klipp(ingest, tagn, IX)
    etik, idlogg = ID.klustra(spar, sift)
    forsta = {}
    for sp, e in zip(spar, etik):
        forsta.setdefault(e, (int(sp["tagning"][1:]), -sp["andel"]))
    viktig = {}
    for sp, e in zip(spar, etik):
        if sp["andel"] >= 0.3 or sp["box_hojd"] >= 0.25:
            viktig[e] = True
    ordning = sorted([e for e in forsta if viktig.get(e)], key=lambda e: forsta[e])
    roll_av = {e: chr(ord("A") + i) for i, e in enumerate(ordning)}
    spar_roll = {(sp["tagning"], sp["spar"]): roll_av.get(e) for sp, e in zip(spar, etik)}

    matning: dict = dict(fokal=fok, identitet=dict(logg=idlogg, spar={f"{k[0]}:{k[1]}": v for k, v in spar_roll.items()}),
                         tagningar={})
    fixerad: dict = {}
    for pass_ in ("forhand", "slutlig"):
      ut, start = [], 0
      seq_roller = []
      poang: dict = {}
      for S in tagn:
        fS = fok["tagningar"][S]["v"]
        t = Tagning(ingest, S, fS)
        hfov = 2 * math.degrees(math.atan(t.W / 2 / t.f))
        hfov_s = hfov * fok["tagningar"][S]["s"] / t.f
        u_b = F @ t.u

        # --- personer: kamerapunkter, hållning, fötter, bäcken ---
        pf = t.mapp / "personer.json"
        sp_map = json.loads(pf.read_text(encoding="utf-8")) if pf.exists() else {}
        pers = []
        for s in sorted(sp_map, key=lambda s: -len(sp_map[s])):
            fil = t.mapp / f"sekvens_{s}.npz"
            if not fil.exists():
                continue
            q = np.load(fil)
            J = kamerapunkter(q, t.kappa)
            kand = q["kand"].astype(bool) if "kand" in q.files else np.ones(len(J), bool)
            Jk = J[kand] if kand.any() else J
            hrel = Jk @ u_b
            fot = np.min(hrel[:, [IX[n] for n in ("l_foot", "r_foot", "l_ball", "r_ball")]], axis=1)
            pose, larvinkel, pose_status = ID.hallning(q, IX, t.u)
            bal_b = np.median((Jk[:, IX["c_spine0"]] + Jk[:, IX["c_spine2"]]) / 2.0, axis=0)
            bal_cv = F @ bal_b
            mid = Jk[len(Jk) // 2]
            l_cv, r_cv = F @ mid[IX["l_uparm"]], F @ mid[IX["r_uparm"]]
            fram = _n(np.cross(l_cv - r_cv, t.u))
            roll = spar_roll.get((S, s))
            pers.append(dict(spar=s, roll=roll, p=bal_cv, p_hor=F @ np.median(Jk[:, IX["c_spine0"]], axis=0), fram=fram, pose=pose,
                             pose_status=pose_status, larvinkel=larvinkel,
                             fot_rel=float(np.median(fot)), backen_rel=float(np.median(hrel[:, IX["c_spine0"]])),
                             fot_synlig=float(q["ben_synliga"].mean()), djup=float(-bal_b[2]), n=len(sp_map[s])))
        golv = t.golvplan()
        pd0 = max([p["djup"] for p in pers], default=1.6)
        skivor = t.skivor(pd0, golv["h_rel"] if golv else None)
        huvud = [p for p in pers if p["roll"] is not None] or pers
        kh = hojd_och_hallning(t, huvud, skivor, golv, fixerad if pass_ == "slutlig" else None)
        if pass_ == "forhand":
            for r, d in kh["per_val"].items():
                for k, v in d.items():
                    poang.setdefault(r, {}).setdefault(k, 0.0)
                    poang[r][k] += v
            continue
        h_c = kh["v"]
        for i, p in enumerate(huvud):
            pose, typ, pm, st = kh["pose"][i]
            p["pose"], p["pose_status"], p["pose_p"], p["sate"] = pose, st, pm, typ
        for sk, kl in zip(skivor, kh["mobelklass"]):
            sk["topp"] = h_c + sk["rel"]
            sk["topp_s"] = sk["rel_s"]
            sk["klass"] = kl
        kh["pose"] = {huvud[i]["spar"]: v for i, v in kh["pose"].items()}
        # personlig strålskala: stående med fötter mot golvet inom statursprior; sittande 1
        for p in pers:
            s_i, st = 1.0, "ingen"
            if p["pose"] == "staende" and p["fot_rel"] < -0.3:
                s_raw = h_c / (-p["fot_rel"])
                s_i = float(np.clip(s_raw, *STATUR_SKALA))
                st = "fötter mot golvet" + (" (klämd vid statursprior, antagen)" if abs(s_raw - s_i) > 1e-6 else "")
            p["s"], p["s_kalla"] = round(s_i, 4), st
            p["p"] = p["p"] * s_i
        pd_max = max([t.hor(p["p"])[1] for p in pers], default=1.6)

        # --- bord/diskar: vågräta skivor i djupet (höjd relativt kameran + kamerahöjd) ---
        bord = []
        for sk in skivor:
            if any(np.linalg.norm(t.hor_xy(sk["p"]) - t.hor_xy(q2["p"])) < 0.4 for q2 in bord):
                continue
            bord.append(sk)

        ankare = {}
        huvud_pers = [pp for pp in pers if pp["roll"] is not None]
        if len(huvud_pers) >= 2 and len(bord) == 1 and float(huvud_pers[0]["fram"] @ huvud_pers[1]["fram"]) < -0.3:
            # två personer som vänder sig mot varandra över en skiva: skivan mellan dem
            ankare[0] = (huvud_pers[0]["p"] + huvud_pers[1]["p"]) / 2.0
        else:
            for pp in pers:
                if pp["pose"] != "sittande":
                    continue
                pb, pdd = t.hor(pp["p"])
                kand = [i for i, q2 in enumerate(bord) if i not in ankare and abs(t.hor(q2["p"])[0] - pb) < 35
                        and t.hor(q2["p"])[1] < pdd + 1.0]
                if kand:
                    i = min(kand, key=lambda i: abs(t.hor(bord[i]["p"])[1] - (pdd - 0.55)))
                    fram_hor = _n(pp["fram"] - (pp["fram"] @ t.u) * t.u)
                    sikt_hor = -_n(pp["p"] - (pp["p"] @ t.u) * t.u)
                    rikt = fram_hor if float(fram_hor @ sikt_hor) > -0.2 else sikt_hor
                    ankare[i] = pp["p"] + 0.55 * rikt

        dets, bord_id = [], {}
        for i, sk in enumerate(bord):
            did = f"{S}:t{i + 1}"
            p = ankare.get(i, sk["p"])
            b, d = t.hor(p)
            bord_id[did] = p
            dets.append(Detektion(
                id=did, klass="bord", nyckel="bord",
                bearing_deg=M(v=round(b, 2), s=3.0),
                djup_m=M(v=round(d, 3), s=round(0.25 if i in ankare else 0.35 * d, 3)),
                amodal=d < 1.6,
                hojd_m=M(v=round(sk["topp"], 3), s=round(math.hypot(sk["topp_s"], kh["s"]), 3)),
                status=dict(lage="R15 framför sittande (antagen)" if i in ankare else "skivans synliga del (matt)",
                            hojd=f"MoGe-skiva + kamerahöjd ({kh['status']})", klass=sk.get("klass")),
            ))

        flera_huvud = len([p for p in pers if p["roll"] is not None]) >= 2
        for i, pp in enumerate(pers):
            b, d = t.hor(pp["p"])
            fb = math.degrees(math.atan2(float(pp["fram"] @ t.rh), float(pp["fram"] @ t.fh)))
            vid = None
            if bord_id:
                kand = min(bord_id, key=lambda k: np.linalg.norm(t.hor_xy(bord_id[k]) - t.hor_xy(pp["p"])))
                avst = np.linalg.norm(t.hor_xy(bord_id[kand]) - t.hor_xy(pp["p"]))
                if pp["pose"] == "sittande" and avst < 1.6:
                    vid = kand
                elif pp["roll"] is not None and (not any(p2["pose"] == "sittande" for p2 in pers) or flera_huvud) and avst < 1.35:
                    vid = kand
            dets.append(Detektion(
                id=f"{S}:p{i + 1}", klass="person", nyckel=f"person:{pp['roll']}" if pp["roll"] else "person:okand",
                unik=bool(pp["roll"]),
                bearing_deg=M(v=round(b, 2), s=1.5),
                djup_m=M(v=round(d, 3), s=round(0.14 * d, 3)),
                vridning_deg=M(v=round(fb, 1), s=20.0),
                pose=pp["pose"], vid=vid, spar=pp["spar"],
                status=dict(hallning=pp["pose_status"], larvinkel_deg=pp["larvinkel"], skala=pp["s"], skala_kalla=pp["s_kalla"],
                            identitet="utseende+proportioner (antagen om marginalen är liten)"),
            ))
        seq_roller.append(next((p["roll"] for p in pers if p["roll"]), None))

        vaggar = [Vagg(bearing_deg=M(v=round(b, 1), s=6.0),
                       avstand_m=M(v=round(a, 3), s=round((0.6 if a > 2 * pd_max else 0.4) * a, 3)), nyckel=k)
                  for b, a, k in _vaggar(t, pd_max)]

        kam = Kamera(
            bild_px=(t.W, t.H),
            hfov_deg=M(v=round(hfov, 2), s=round(max(hfov_s, 1.0), 2)),
            hojd_m=M(v=round(h_c, 3), s=kh["s"]),
            pitch_deg=M(v=round(t.pitch, 2), s=t.lod["sigma"]),
            roll_deg=M(v=round(t.roll, 2), s=t.lod["sigma"]),
        )
        ut.append(KlippObs(
            klipp=S.lower(), rutor=(start, start + t.N), kamera=kam, detektioner=dets, vaggar=vaggar,
            manhattan_deg=_manhattan(t), ljus_bearing_deg=None, takhojd_m=_takhojd(t, h_c),
            rumsnycklar={}, stralar=_stralar(t, hfov, pers), djupgrid=None, skala=None,
            delar_kamera_med=sift.get(S.lower()),
        ))
        matning["tagningar"][S] = dict(
            f_px=t.f, f_kedja=t.f_kedja, kappa=round(t.kappa, 4), ref_ruta=t.ruta,
            lodlinje=dict(u_opencv=[round(float(x), 5) for x in t.u], pitch=round(t.pitch, 2), roll=round(t.roll, 2),
                          sigma=t.lod["sigma"], kalla=t.lod["kalla"], status=t.lod["status"], flaggor=t.lod["flaggor"]),
            kamerahojd=kh,
            personer=[dict(spar=p["spar"], roll=p["roll"], pose=p["pose"], pose_status=p["pose_status"], larvinkel=p["larvinkel"],
                           pose_p=p.get("pose_p"), sate=p.get("sate"),
                           s=p["s"], s_kalla=p["s_kalla"], fot_synlig=round(p["fot_synlig"], 2)) for p in pers],
            skivor=[dict(topp=round(s["topp"], 3), rel=round(s["rel"], 3), andel=round(s["andel"], 3), klass=s.get("klass")) for s in skivor],
            golv=golv,
        )
        start += t.N

      if pass_ == "forhand":
          for r, d in poang.items():
              fixerad[r] = max(d, key=d.get)
          matning["hallning_per_identitet"] = {r: dict(val=fixerad[r], logpoang={k: round(v, 2) for k, v in d.items()},
                                                    status="antagen (samma hållning i alla tagningar)") for r, d in poang.items()}

    # dialogpar för blickriktning (roller som växlar i motbilder)
    par = Counter(tuple(sorted((a, b))) for a, b in zip(seq_roller, seq_roller[1:]) if a and b and a != b)
    dialog = [p for p, n in par.items() if n >= 2]
    partner = {}
    for a, b in dialog:
        partner.setdefault(a, b)
        partner.setdefault(b, a)
    for k in ut:
        for d in k.detektioner:
            if d.klass == "person" and d.unik:
                r = d.nyckel.split(":")[1]
                if r in partner:
                    d.blick_mot = f"person:{partner[r]}"

    obs = Observationer(klipp_id=ingest.name, fps=float(json.loads((ingest / tagn[0] / "meta.json").read_text())["fps"]), klipp=ut)
    return obs, matning
