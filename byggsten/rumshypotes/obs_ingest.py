"""Fas 1–2 ur kedjans ingest: observationer per tagning (telemetri.Observationer).

Allmänt för varje klipp som gått genom scen/3d/ingest/ingest_klipp.py. Bara mätningar inom en
tagning används. Deklarationens rum (bord, platser, kameror) används inte. Ur deklarationen tas
bara vem som syns i vilken tagning och om personen sitter eller står.

Källa per observation:
- fokal: klippets försvinningspunkter (fyra_klipp.json), annars tagningens egen
- lodlinje och kamerans lutning: normaler på horisontella ytor (bordsskivor, golv) ur MoGe
- personer: SAM 3D Body, rå translation, rättad för fokal; kroppens storlek är skalankaret.
  Vändningen räknas ur axlarna, kamerahöjden ur axelhöjden.
- bord: rum.json (MoGe, enkelvy), dubbletter sammanslagna. Stor sigma: MoGe:s skala är inte förankrad.
- väggar: rum.json och vertikala ytor bakom personen
- Manhattan: vertikala ytors normaler modulo 90°
- fri yta: närmaste punkt i ögonhöjdsbandet längs strålen, personerna inräknade
- ljus (bara sidan), rumsnycklar, föremål och dörrar: VLM (las_vlm.py)
- blick: personer i motbilder (A, B, A, B …) ser på varandra

    scen/.venv/Scripts/python.exe byggsten/rumshypotes/obs_ingest.py scen/3d/ingest/ut/notan-tagningar \
        --vlm byggsten/rumshypotes/ut/notan/vlm --ut byggsten/rumshypotes/ut/notan/obs.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import pathlib
import sys
from collections import Counter

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))
from telemetri import M, Detektion, Djupgrid, Kamera, KlippObs, Observationer, Stralar, Vagg  # noqa: E402

ROT = HIT.parents[1]
F = np.diag([1.0, -1.0, -1.0])
FARGKLASS = {"vit": "ljus", "beige": "ljus", "gra": "ljus", "mork": "mork", "tra": "varm", "tegel": "varm",
             "glas": "glas"}
AXELHOJD = {"sittande": 1.05, "staende": 1.42}


def _n(v):
    return v / (np.linalg.norm(v) + 1e-12)


def _leder():
    namn = json.loads((ROT / "scen/3d/kontrakt/tro_rigg.json").read_text(encoding="utf-8"))["namn"]
    return {n: i for i, n in enumerate(namn)}


def _fokal(ingest: pathlib.Path):
    """Klippets fokal (px) och sigma ur försvinningspunkterna, eller None."""
    fil = ROT / "scen/3d/kontrakt/ut/fore_fokal_0009/fyra_klipp.json"
    if not fil.exists():
        return None
    d = json.loads(fil.read_text(encoding="utf-8"))
    namn = next((k for k in d if ingest.name.startswith(k)), None)
    if namn is None:
        return None
    k = d[namn]["klipp"]
    lo, hi = k["spridning_px"]
    return float(k["fokal_px"]), float(hi - lo) / 2.7, float(d[namn]["dim"])


class Tagning:
    """En tagnings mätningar i en vågrät ram: bearing (grader, positiv åt höger) och vågrätt avstånd."""

    def __init__(self, mapp: pathlib.Path, f_sann: float, djupmapp: pathlib.Path | None = None):
        self.mapp = mapp
        self.meta = json.loads((mapp / "meta.json").read_text(encoding="utf-8"))
        self.W, self.H, self.N = self.meta["bredd"], self.meta["hojd"], self.meta["N"]
        self.rum = json.loads((mapp / "rum.json").read_text(encoding="utf-8"))
        filer = sorted(glob.glob(str(mapp / "rum/depth/*.npz")))
        df = min(filer, key=lambda f: abs(int(pathlib.Path(f).stem) - self.N // 2))
        self.ruta = int(pathlib.Path(df).stem)
        z = np.load(df)
        K = z["intrinsics"]
        self.f_kedja = float(K[0, 0] * self.W)                 # fokal som kedjan använde (px vid bildbredd W)
        self.f = f_sann
        self.a = self.f_kedja / self.f                         # kedjans MoGe-punkter: sidled skalas, djupet står kvar
        self.kappa = self.f / self.f_kedja                     # SAM: hela translationen skalas
        self.skala, self.skift = 1.0, 0.0                      # djupets skala och förskjutning, sätts av kalibrera()
        self.omaskat = False
        egen = djupmapp / f"{mapp.name}.npz" if djupmapp else None
        if egen is not None and egen.exists():                 # MoGe med personerna kvar, klippets fokal
            z = np.load(egen)
            K = z["intrinsics"]
            self.omaskat = True
        self.D = z["depth"].astype(float)
        self.Nm = z["normal"].astype(float)
        hd, wd = self.D.shape
        fx, fy, cx, cy = self.f * wd / self.W, self.f * wd / self.W, K[0, 2] * wd, K[1, 2] * hd
        v, u = np.mgrid[0:hd, 0:wd]
        self.P = np.stack([(u - cx) / fx * self.D, (v - cy) / fy * self.D, self.D], -1)
        self.giltig = np.isfinite(self.D) & (self.D > 0.05)
        self.uv = (fx, fy, cx, cy, wd, hd)
        self._lodlinje()

    def _lodlinje(self):
        kropp = _n(np.load(self.mapp / "varld.npz")["upp"].astype(float))
        n = self.Nm[self.giltig]
        hor = n[(n @ kropp) > math.cos(math.radians(40))]
        if len(hor) > 2000:
            self.u, self.u_sigma = _n(np.median(hor, 0)), 3.0
        else:
            self.u, self.u_sigma = kropp, 10.0
        self.fh = _n(np.array([0, 0, 1.0]) - self.u[2] * self.u)
        self.rh = _n(np.cross(self.fh, self.u))
        self.pitch = math.degrees(math.asin(np.clip(self.u[2], -1, 1)))
        self.roll = -math.degrees(math.asin(np.clip(self.u[0], -1, 1)))

    def kalibrera(self, punkter, hcam=None):
        """Skalan mot kroppen: SAM-ledernas djup (kroppens storlek) mot MoGe:s djup på samma ställe i bilden."""
        if not self.omaskat or not punkter:
            return None
        fx, fy, cx, cy, wd, hd = self.uv
        kvot = []
        for p in punkter:
            if p[2] < 0.2:
                continue
            ui, vi = int(round(p[0] / p[2] * fx + cx)), int(round(p[1] / p[2] * fy + cy))
            if 3 <= ui < wd - 3 and 3 <= vi < hd - 3:
                blk = self.D[vi - 3:vi + 4, ui - 3:ui + 4]
                blk = blk[np.isfinite(blk)]
                if len(blk) > 10:
                    kvot.append((p[2] - 0.10) / float(np.median(blk)))   # ledens djup minus kroppens yta
        if len(kvot) < 2:
            return None
        s = float(np.clip(np.median(kvot), 0.4, 2.5))
        a, b = s, 0.0
        if hcam is not None:
            # R21: två ankare. Kroppen ger djupet nära; vågräta ytor med känd höjd (bordsskiva 0,74 m,
            # golv 0) ger en andra ekvation. Djupet rättas affint: d' = a·d + b (MoGe trycker ihop avstånd).
            ok = self.giltig & ((self.Nm @ self.u) > math.cos(math.radians(15)))
            d = self.D[ok]
            ru = (self.P[ok] @ self.u) / d                     # strålens höjdkomponent per meter djup
            sel = ru < -0.03
            d, ru = d[sel], ru[sel]
            if len(d) > 4000:
                i = np.linspace(0, len(d) - 1, 4000).astype(int)
                d, ru = d[i], ru[i]
            kropp = [(p[2] - 0.10, k) for p, k in zip([q for q in punkter if q[2] >= 0.2], kvot)]
            golv = np.abs(s * d * ru + hcam) < 0.25
            dg = d[golv]
            if golv.sum() >= 300 and np.percentile(dg, 90) - np.percentile(dg, 10) >= 1.0:
                # golvet har samma höjd på alla avstånd: det bestämmer lutningen; kroppen väger lika mycket
                A = list(np.c_[d[golv] * ru[golv], ru[golv]])
                y = [-hcam] * int(golv.sum())
                w = [1.0 / golv.sum()] * int(golv.sum())
                for t_m, k in kropp:
                    A.append([t_m / k, 1.0])
                    y.append(t_m)
                    w.append(1.0 / len(kropp))
                A, y, w = np.array(A), np.array(y), np.sqrt(np.array(w))
                sol = np.linalg.lstsq(A * w[:, None], y * w, rcond=None)[0]
                if 0.3 < sol[0] < 3.0 and abs(sol[1]) < 1.5:      # fit i gränsen = golvet ljuger, behåll ren skala
                    a, b = float(sol[0]), float(sol[1])
        self.skala, self.skift = a, b
        nyD = a * self.D + b
        self.P = self.P * (nyD / self.D)[..., None]
        self.D = nyD
        return a

    def djupgrid(self, rader=32, kolumner=18):
        hd, wd = self.D.shape
        v = []
        for r in range(rader):
            for c in range(kolumner):
                blk = self.D[r * hd // rader:(r + 1) * hd // rader, c * wd // kolumner:(c + 1) * wd // kolumner]
                blk = blk[np.isfinite(blk)]
                v.append(round(float(np.median(blk)), 3) if len(blk) > 4 else -1.0)
        return Djupgrid(rader=rader, kolumner=kolumner, varden=v)

    def hor(self, p):
        x, z = float(p @ self.rh), float(p @ self.fh)
        return math.degrees(math.atan2(x, z)), math.hypot(x, z)

    def moge(self, p_kedja):
        """En punkt i kedjans kameraram ur MoGe (fokal f_kedja) till rättad fokal."""
        p = np.array(p_kedja, dtype=float)
        return np.array([p[0] * self.a, p[1] * self.a, p[2]]) * self.skala

    def djup_vid(self, x_andel, y_andel, ruta=6):
        fx, fy, cx, cy, wd, hd = self.uv
        ui, vi = int(np.clip(x_andel * wd, 0, wd - 1)), int(np.clip(y_andel * hd, 0, hd - 1))
        blk = self.P[max(0, vi - ruta):vi + ruta + 1, max(0, ui - ruta):ui + ruta + 1].reshape(-1, 3)
        ok = np.isfinite(blk[:, 2]) & (blk[:, 2] > 0.05)
        return np.median(blk[ok], 0) if ok.sum() >= 3 else None


def _personer(t: Tagning, IX, roll_huvud, pose_huvud):
    sp = json.loads((t.mapp / "personer.json").read_text(encoding="utf-8"))
    spar = sorted(sp, key=lambda s: -len(sp[s]))
    ut = []
    for i, s in enumerate(spar):
        f = t.mapp / f"sekvens_{s}.npz"
        if not f.exists():
            continue
        q = np.load(f)
        ct = np.median(q["cam_t_ra"], 0) * t.kappa
        m = min(t.ruta, len(q["cam_t_ra"]) - 1)               # samma ruta som djupet
        J = q["pose"][m][:, :3] / 100.0 @ F.T + q["cam_t_ra"][m] * t.kappa
        l, r = J[IX["l_uparm"]], J[IX["r_uparm"]]
        fram = _n(np.cross(l - r, t.u))
        axel_rel = float(((l + r) / 2) @ t.u)
        huvud = i == 0 and roll_huvud is not None
        pose = pose_huvud if huvud else "sittande"
        kal = [J[IX[n]] for n in ("l_uparm", "r_uparm", "l_clavicle", "r_clavicle") if n in IX]
        ut.append(dict(spar=s, roll=roll_huvud if huvud else None, p=ct, fram=fram, axel_rel=axel_rel, pose=pose,
                       kal=kal))
    return ut


def _vaggar(t: Tagning, pers):
    vaggar = []
    for w in (t.rum.get("walls", []) if not t.omaskat else []):   # kedjans väggar bara utan eget kalibrerat djup
        n = np.array(w["normal"], dtype=float)
        n2 = np.array([n[0] / t.a, n[1] / t.a, n[2]])
        s = np.linalg.norm(n2)
        n2, d2 = n2 / s, float(w["distance"]) / s * t.skala
        if abs(n2 @ t.u) > 0.25:
            continue
        b, avst = t.hor(d2 * n2)
        if avst > 0.3:
            vaggar.append((b, avst, "rum.json"))
    # vertikala ytor bakom personen
    bak = max([t.hor(p["p"])[1] for p in pers], default=0.0) + 0.1
    n = t.Nm[t.giltig]
    P = t.P[t.giltig]
    vert = np.abs(n @ t.u) < 0.15
    dist = np.hypot(P @ t.rh, P @ t.fh)
    urval = vert & (dist > bak)
    if urval.sum() > 0.03 * len(P):
        ang = np.degrees(np.arctan2(n[urval] @ t.rh, n[urval] @ t.fh))
        hist, kant = np.histogram(ang, bins=36, range=(-180, 180))
        topp = kant[np.argmax(hist)] + 5
        nara = np.abs((ang - topp + 180) % 360 - 180) < 15
        if nara.sum() > 0.02 * len(P):
            nn = _n(np.median(n[urval][nara], 0))
            off = float(np.median(P[urval][nara] @ nn))
            b, avst = t.hor(off * nn)
            if avst > 0.3 and not any(abs((b - v[0] + 180) % 360 - 180) < 20 for v in vaggar):
                vaggar.append((b, avst, "ytor bakom personen"))
    return vaggar


def _manhattan(t: Tagning):
    """Vertikala ytors normaler modulo 90°, viktade efter yta (avstånd i kvadrat). Sigma ur koncentrationen R:
    en kamera som tittar diagonalt ser båda väggarna snett och ger låg R, alltså en svag ledtråd."""
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
    if R < 0.6:                                   # ingen tydlig rät vinkel i bild: ingen läsning
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
    golv = (n @ t.u > 0.85) & (h < -0.8)
    if tak.sum() < 500:
        return None
    hc = float(np.median(h[tak]))
    if golv.sum() > 500:
        return M(v=round(hc - float(np.median(h[golv])), 3), s=0.25)
    return M(v=round(hc + hcam, 3), s=0.35)


def bygg(ingest: pathlib.Path, vlm_mapp: pathlib.Path, djupmapp: pathlib.Path | None = None) -> Observationer:
    IX = _leder()
    dekl = json.loads((ingest / "plats/deklaration.json").read_text(encoding="utf-8"))
    roller = {r: v for r, v in dekl.get("roller", {}).items() if isinstance(v, dict)}
    roll_av = {S: r for r, v in roller.items() for S in v.get("tagningar", [])}
    pose_av = {r: ("staende" if str(v.get("lage", "")).startswith("st") else "sittande") for r, v in roller.items()}
    tagn = sorted(p.name for p in ingest.iterdir() if p.is_dir() and p.name[:1] == "S" and p.name[1:].isdigit())
    tagn.sort(key=lambda s: int(s[1:]))
    fk = _fokal(ingest)
    # blick: par som växlar i motbilder
    seq = [roll_av.get(S) for S in tagn]
    par = Counter(tuple(sorted((a, b))) for a, b in zip(seq, seq[1:]) if a and b and a != b)
    dialog = [p for p, n in par.items() if n >= 2]
    partner = {}
    for a, b in dialog:
        partner.setdefault(a, b)
        partner.setdefault(b, a)
    ut, start = [], 0
    for S in tagn:
        mapp = ingest / S
        meta = json.loads((mapp / "meta.json").read_text(encoding="utf-8"))
        f_sann, f_sig = (fk[0] * meta["bredd"] / meta["bredd"], fk[1]) if fk else (None, None)
        q1 = np.load(sorted(mapp.glob("sekvens_*.npz"))[0])
        if f_sann is None:
            f_sann, f_sig = float(q1["fokal"]), float(q1["fokal"]) * 0.15
        t = Tagning(mapp, f_sann, djupmapp)
        hfov = 2 * math.degrees(math.atan(t.W / 2 / t.f))
        hfov_s = hfov * f_sig / t.f
        vlm = json.loads((vlm_mapp / f"{S}.json").read_text(encoding="utf-8")) if (vlm_mapp / f"{S}.json").exists() else {}
        roll = roll_av.get(S)
        pers = _personer(t, IX, roll, pose_av.get(roll, "sittande"))
        dets = []
        # kamerahöjd ur huvudpersonens axlar, annars bordsskivan
        hcam, hcam_s = 1.2, 0.3
        if pers:
            p0 = pers[0]
            hcam, hcam_s = AXELHOJD[p0["pose"]] - p0["axel_rel"], 0.12
        # R18: ser kameran ett bord på nära håll (skivan ovanifrån) står den över skivan
        nara_bord = [o for o in t.rum.get("objects", []) if o.get("label") == "table" and float(o["centre"][2]) < 1.8]
        if nara_bord and hcam < 0.86:
            hcam, hcam_s = 0.86, 0.12
        skala = t.kalibrera(pers[0]["kal"], hcam) if pers else None
        # bord
        bord = []
        for o in t.rum.get("objects", []):
            if o.get("label") != "table":
                continue
            p = t.moge(o["centre"])
            if any(np.linalg.norm(p - q) < 0.4 for q in bord):
                continue
            bord.append(p)
        # R15: bordet närmast framför en sittande person förankras i personens djup (MoGe:s skala är oförankrad)
        ankare = {}
        for pp in pers:
            if pp["pose"] != "sittande":
                continue
            pb, pd = t.hor(pp["p"])
            kand = [i for i, q in enumerate(bord) if i not in ankare and abs(t.hor(q)[0] - pb) < 15
                    and t.hor(q)[1] < pd + 1.0]
            if kand:
                i = min(kand, key=lambda i: abs(t.hor(bord[i])[1] - (pd - 0.55)))
                ankare[i] = pp["p"] - 0.55 * _n(pp["p"] - (pp["p"] @ t.u) * t.u)
        bord_id = {}
        for i, p in enumerate(bord):
            did = f"{S}:t{i + 1}"
            if i in ankare:
                p = ankare[i]
            b, d = t.hor(p)
            bord_id[did] = p
            s_d = 0.25 if i in ankare else 0.35 * d
            dets.append(Detektion(id=did, klass="bord", nyckel="bord", bearing_deg=M(v=round(b, 2), s=3.0),
                                  djup_m=M(v=round(d, 3), s=round(s_d, 3)), amodal=d < 1.5))
        # personer
        for i, pp in enumerate(pers):
            b, d = t.hor(pp["p"])
            fb = math.degrees(math.atan2(float(pp["fram"] @ t.rh), float(pp["fram"] @ t.fh)))
            did = f"{S}:p{i + 1}"
            vid = None
            if pp["pose"] == "sittande" and bord_id:
                kand = min(bord_id, key=lambda k: np.linalg.norm((bord_id[k] - pp["p"]) - ((bord_id[k] - pp["p"]) @ t.u) * t.u))
                v = bord_id[kand] - pp["p"]
                if np.linalg.norm(v - (v @ t.u) * t.u) < 2.0:
                    vid = kand
            nyckel = f"person:{pp['roll']}" if pp["roll"] else "person:okand"
            dets.append(Detektion(id=did, klass="person", nyckel=nyckel, unik=bool(pp["roll"]),
                                  bearing_deg=M(v=round(b, 2), s=1.5), djup_m=M(v=round(d, 3), s=round(0.14 * d, 3)),
                                  vridning_deg=M(v=round(fb, 1), s=20.0), pose=pp["pose"],
                                  blick_mot=(f"person:{partner[pp['roll']]}" if pp["roll"] in partner else None),
                                  vid=vid))
        # föremål och dörrar ur VLM
        alla_nycklar = Counter()
        for S2 in tagn:
            fil = vlm_mapp / f"{S2}.json"
            if fil.exists():
                for fo in json.loads(fil.read_text(encoding="utf-8")).get("foremal", []):
                    if fo.get("distinkt"):
                        alla_nycklar[fo["nyckel"]] += 1
        for i, fo in enumerate(vlm.get("foremal", [])):
            if not (fo.get("distinkt") and fo.get("pa_bord") and alla_nycklar[fo["nyckel"]] >= 2):
                continue
            p = t.djup_vid(fo["x_andel"], fo["y_andel"])
            if p is None:
                continue
            b, d = t.hor(p)
            pa = None
            if bord_id:
                kand = min(bord_id, key=lambda k: np.linalg.norm(bord_id[k] - p))
                if np.linalg.norm(bord_id[kand] - p) < 1.0:
                    pa = kand
            dets.append(Detektion(id=f"{S}:f{i + 1}", klass="foremal", nyckel=f"foremal:{fo['nyckel']}",
                                  bearing_deg=M(v=round(b, 2), s=2.0), djup_m=M(v=round(d, 3), s=round(0.35 * d, 3)),
                                  pa=pa))
        for i, x in enumerate(vlm.get("dorrar_x_andel", [])):
            p = t.djup_vid(x, 0.45, ruta=10)
            if p is None:
                continue
            b, d = t.hor(p)
            dets.append(Detektion(id=f"{S}:d{i + 1}", klass="dorr", nyckel="dorr", bearing_deg=M(v=round(b, 2), s=3.0),
                                  djup_m=M(v=round(d, 3), s=round(0.4 * d, 3)), pa_vagg=True))
        pd0 = t.hor(pers[0]["p"])[1] if pers else 1.5
        vaggar = [Vagg(bearing_deg=M(v=round(b, 1), s=6.0),
                       avstand_m=M(v=round(a, 3), s=round((0.6 if a > 2 * pd0 else 0.4) * a, 3)),  # MoGe:s fel växer med avståndet
                       nyckel=k) for b, a, k in _vaggar(t, pers)]
        ljus = None
        lf = vlm.get("ljus_fran")
        if lf == "hoger":
            ljus = M(v=60.0, s=45.0)
        elif lf == "vanster":
            ljus = M(v=-60.0, s=45.0)
        elif lf == "bakom_kameran":
            ljus = M(v=180.0, s=45.0)
        elif lf == "framfor_i_bild":
            x = vlm.get("ljus_x_andel", -1)
            ljus = M(v=round(math.degrees(math.atan((x - 0.5) * t.W / t.f)), 1), s=25.0) if x >= 0 else M(v=0.0, s=45.0)
        nycklar = {}
        if vlm.get("vagg") in FARGKLASS:
            nycklar["vagg"] = FARGKLASS[vlm["vagg"]]
        if vlm.get("tak") and vlm["tak"] != "syns_ej":
            nycklar["tak"] = vlm["tak"]
        kam = Kamera(bild_px=(t.W, t.H), hfov_deg=M(v=round(hfov, 2), s=round(max(hfov_s, 1.0), 2)),
                     hojd_m=M(v=round(hcam, 3), s=hcam_s), pitch_deg=M(v=round(t.pitch, 2), s=t.u_sigma),
                     roll_deg=M(v=round(t.roll, 2), s=t.u_sigma))
        ut.append(KlippObs(klipp=S.lower(), rutor=(start, start + t.N), kamera=kam, detektioner=dets, vaggar=vaggar,
                           manhattan_deg=_manhattan(t), ljus_bearing_deg=ljus,
                           takhojd_m=_takhojd(t, hcam) if "tak" in nycklar else None,
                           rumsnycklar=nycklar, stralar=_stralar(t, hfov, pers),
                           djupgrid=t.djupgrid() if t.omaskat else None,
                           skala=round(skala, 3) if skala else None))
        start += t.N
    return Observationer(klipp_id=ingest.name, fps=float(json.loads((ingest / tagn[0] / "meta.json").read_text())["fps"]),
                         klipp=ut)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ingest")
    ap.add_argument("--vlm", required=True)
    ap.add_argument("--ut", required=True)
    ap.add_argument("--djup", default=None, help="MoGe med personerna kvar (modal_djup.py)")
    a = ap.parse_args()
    obs = bygg(pathlib.Path(a.ingest), pathlib.Path(a.vlm), pathlib.Path(a.djup) if a.djup else None)
    pathlib.Path(a.ut).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.ut).write_text(obs.model_dump_json(indent=1), encoding="utf-8")
    for k in obs.klipp:
        print(k.klipp, k.rutor, f"skala {k.skala} hfov {k.kamera.hfov_deg.v} höjd {k.kamera.hojd_m.v} pitch {k.kamera.pitch_deg.v}",
              "| man", k.manhattan_deg.v if k.manhattan_deg else None, "| ljus", k.ljus_bearing_deg.v if k.ljus_bearing_deg else None,
              "| väggar", [(w.bearing_deg.v, w.avstand_m.v) for w in k.vaggar])
        for d in k.detektioner:
            print("   ", d.id, d.klass, d.nyckel, "b", d.bearing_deg.v, "d", d.djup_m.v,
                  "vr", d.vridning_deg.v if d.vridning_deg else None, "vid", d.vid, "pa", d.pa, "blick", d.blick_mot)
