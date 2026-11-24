"""Lager 1 (obs_motor.py): Extraherar metriskt kalibrerade observationer per tagning.

Allmänna mekanismer för inläst inomhusvideo:
1. Vågrät 2D-projektion i (rh, fh)-planet vid kontroll av `pa` (föremål på bord) och `vid` (person vid bord/disk).
2. Geometrisk bords-/diskdetektion direkt ur MoGe-ytnormaler när YOLO i `rum.json` missat bardisk/glasdisk/glassdisk.
3. Flerpersons-identifikation per tagning (t.ex. Guacamole S4 där både A och B syns i samma bildruta).
4. Robust hantering av personlösa detaljtagningar / B-roll (t.ex. A-sketch S6 där bara maten på disken syns).
5. SIFT/MAGSAC-baserad kameragruppering (`delar_kamera_med`) för tagningar som delar exakt samma bakgrund/stativ.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import pathlib
import sys
from collections import Counter

import cv2
import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))
from schema import M, Detektion, Djupgrid, Kamera, KlippObs, Observationer, Stralar, Vagg  # noqa: E402

ROT = HIT.parent
F = np.diag([1.0, -1.0, -1.0])
FARGKLASS = {
    "vit": "ljus", "beige": "ljus", "gra": "ljus",
    "mork": "mork", "tra": "varm", "tegel": "varm", "glas": "glas",
}
AXELHOJD = {"sittande": 1.05, "staende": 1.42}
BORD_ETIKETTER = {"table", "bar counter", "counter", "desk", "dining table", "kitchen island"}


def _n(v):
    return v / (np.linalg.norm(v) + 1e-12)


def _hor_xy(t: "Tagning", p: np.ndarray) -> np.ndarray:
    """Vågrät 2D-position (x_höger, z_framåt) i meter i kamerans horisontella ram."""
    return np.array([float(p @ t.rh), float(p @ t.fh)])


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


def _sift_kameragrupper(ingest: pathlib.Path) -> dict[str, str]:
    """Returnerar {tagning_lower: tidigare_tagning_lower} för par med SIFT-verifierad delad kameravy."""
    sys.path.insert(0, str(ROT / "scen/3d/ingest"))
    try:
        import rum_grupper
        cache_fil = ingest / "grupper.json"
        if cache_fil.exists():
            res = json.loads(cache_fil.read_text(encoding="utf-8"))
        else:
            res = rum_grupper.mat_grupper(ingest)
        koppling = {}
        for grp in res.get("delar_plats", []):
            if len(grp) >= 2:
                bas = grp[0].lower()
                for medlem in grp[1:]:
                    koppling[medlem.lower()] = bas
        return koppling
    except Exception:
        return {}


class Tagning:
    """En tagnings mätningar i en vågrät ram: bearing (grader, positiv åt höger) och vågrätt avstånd."""

    def __init__(self, mapp: pathlib.Path, f_sann: float | None, djupmapp: pathlib.Path | None = None):
        self.mapp = mapp
        self.meta = json.loads((mapp / "meta.json").read_text(encoding="utf-8"))
        self.W, self.H, self.N = self.meta["bredd"], self.meta["hojd"], self.meta["N"]
        self.rum = json.loads((mapp / "rum.json").read_text(encoding="utf-8"))
        filer = sorted(glob.glob(str(mapp / "rum/depth/*.npz")))
        df = min(filer, key=lambda f: abs(int(pathlib.Path(f).stem) - self.N // 2))
        self.ruta = int(pathlib.Path(df).stem)
        z = np.load(df)
        K = z["intrinsics"]
        self.f_kedja = float(K[0, 0] * self.W)
        self.f = f_sann if f_sann is not None else self.f_kedja
        self.a = self.f_kedja / self.f
        self.kappa = self.f / self.f_kedja
        self.skala, self.skift = 1.0, 0.0
        self.omaskat = False
        egen = djupmapp / f"{mapp.name}.npz" if djupmapp else None
        if egen is not None and egen.exists():
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
        self.bild = self._las_nyckelbild()

    def _las_nyckelbild(self):
        for kand in (
            self.mapp / f"frames/{self.ruta:04d}.jpg",
            self.mapp / f"frames/{self.ruta:04d}.png",
            self.mapp / "nyckelbild.jpg",
            self.mapp / "nyckelbild.png",
        ):
            if kand.exists():
                im = cv2.imread(str(kand))
                if im is not None:
                    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        return None

    def farg_vid(self, x_andel: float, y_andel: float, radie_px: int = 12) -> list[float] | None:
        if self.bild is None:
            return None
        bh, bw = self.bild.shape[:2]
        cx, cy = int(np.clip(x_andel * bw, 0, bw - 1)), int(np.clip(y_andel * bh, 0, bh - 1))
        patch = self.bild[max(0, cy - radie_px):min(bh, cy + radie_px + 1),
                          max(0, cx - radie_px):min(bw, cx + radie_px + 1)]
        if patch.size == 0:
            return None
        med = np.median(patch.reshape(-1, 3), axis=0) / 255.0
        return [round(float(c), 3) for c in med]

    def _lodlinje(self):
        v_fil = self.mapp / "varld.npz"
        if v_fil.exists():
            kropp = _n(np.load(v_fil)["upp"].astype(float))
        else:
            kropp = np.array([0.0, -1.0, 0.0])
        n = self.Nm[self.giltig]
        hor = n[(n @ kropp) > math.cos(math.radians(30))]
        if len(hor) > 2000:
            u_raw = _n(np.median(hor, 0))
            self.u_sigma = 3.0
        else:
            u_raw, self.u_sigma = kropp, 10.0
        # Skydda mot lutande glasdiskar (t.ex. välvt frontglas på glassdisk/kebabdisk):
        # kamerans verkliga pitch/roll i 9:16-dialog överstiger sällan 18° respektive 8°.
        u_clamp = np.array([
            np.clip(u_raw[0], -math.sin(math.radians(8)), math.sin(math.radians(8))),
            min(u_raw[1], -math.cos(math.radians(18))),
            np.clip(u_raw[2], -math.sin(math.radians(18)), math.sin(math.radians(18))),
        ])
        self.u = _n(u_clamp)
        self.fh = _n(np.array([0, 0, 1.0]) - self.u[2] * self.u)
        self.rh = _n(np.cross(self.fh, self.u))
        self.pitch = math.degrees(math.asin(np.clip(self.u[2], -1, 1)))
        self.roll = -math.degrees(math.asin(np.clip(self.u[0], -1, 1)))

    def kalibrera(self, punkter, hcam=None):
        """R19: Skalan mot kroppen — SAM-ledernas djup mot MoGe:s djup på samma pixlar."""
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
                    kvot.append((p[2] - 0.10) / float(np.median(blk)))
        if len(kvot) < 2:
            return None
        s = float(np.clip(np.median(kvot), 0.4, 2.5))
        a, b = s, 0.0
        if hcam is not None:
            ok = self.giltig & ((self.Nm @ self.u) > math.cos(math.radians(15)))
            d = self.D[ok]
            ru = (self.P[ok] @ self.u) / d
            sel = ru < -0.03
            d, ru = d[sel], ru[sel]
            if len(d) > 4000:
                i = np.linspace(0, len(d) - 1, 4000).astype(int)
                d, ru = d[i], ru[i]
            kropp = [(p[2] - 0.10, k) for p, k in zip([q for q in punkter if q[2] >= 0.2], kvot)]
            golv = np.abs(s * d * ru + hcam) < 0.25
            dg = d[golv]
            if golv.sum() >= 300 and np.percentile(dg, 90) - np.percentile(dg, 10) >= 1.0:
                A = list(np.c_[d[golv] * ru[golv], ru[golv]])
                y = [-hcam] * int(golv.sum())
                w = [1.0 / golv.sum()] * int(golv.sum())
                for t_m, k in kropp:
                    A.append([t_m / k, 1.0])
                    y.append(t_m)
                    w.append(1.0 / len(kropp))
                A, y, w = np.array(A), np.array(y), np.sqrt(np.array(w))
                sol = np.linalg.lstsq(A * w[:, None], y * w, rcond=None)[0]
                if 0.3 < sol[0] < 3.0 and abs(sol[1]) < 1.5:
                    a, b = float(sol[0]), float(sol[1])
        self.skala, self.skift = a, b
        nyD = a * self.D + b
        self.P = self.P * (nyD / self.D)[..., None]
        self.D = nyD
        return a

    def horisontell_skiva_framfor(self, pers: list[dict]) -> np.ndarray | None:
        """Hittar bords-/diskskiva direkt i MoGe-ytnormalerna när YOLO i rum.json missat möbeln."""
        _, _, _, _, wd, hd = self.uv
        v, _ = np.mgrid[0:hd, 0:wd]
        hor_mask = self.giltig & ((self.Nm @ self.u) > math.cos(math.radians(32)))
        pd = max([self.hor(p["p"])[1] for p in pers], default=1.6)
        nedre = (v > hd * 0.38) & hor_mask & (self.D < pd + 0.25) & (self.D > 0.25)
        # Kräv en rejäl sammanhängande horisontell yta (> 25 000 px, ca 4.5% av bilden)
        if nedre.sum() < 25000:
            return None
        pts = self.P[nedre]
        # Kontrollera att ytan ligger i bords-/diskhöjd under/nära kameran, inte golvet
        h_rel = pts @ self.u
        skiva_mask = (h_rel > -0.95) & (h_rel < 0.25)
        if skiva_mask.sum() < 15000:
            return None
        return np.median(pts[skiva_mask], axis=0)

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
        p = np.array(p_kedja, dtype=float)
        return np.array([p[0] * self.a, p[1] * self.a, p[2]]) * self.skala

    def djup_vid(self, x_andel, y_andel, ruta=6):
        fx, fy, cx, cy, wd, hd = self.uv
        ui, vi = int(np.clip(x_andel * wd, 0, wd - 1)), int(np.clip(y_andel * hd, 0, hd - 1))
        blk = self.P[max(0, vi - ruta):vi + ruta + 1, max(0, ui - ruta):ui + ruta + 1].reshape(-1, 3)
        ok = np.isfinite(blk[:, 2]) & (blk[:, 2] > 0.05)
        return np.median(blk[ok], 0) if ok.sum() >= 3 else None


def _roll_och_pose_for_spar(
    S: str,
    spar_lista: list[str],
    roller_i_tagning: list[str],
    pose_av: dict[str, str],
    kam_info: dict,
    lasning_tagn: dict,
) -> dict[str, tuple[str | None, str]]:
    """Tilldelar (roll, pose) till varje spår i tagningen S, även när flera kända roller syns i samma bild."""
    ut: dict[str, tuple[str | None, str]] = {}
    if not spar_lista:
        return ut

    # 1. Om bara en känd roll finns i tagningen hör den till huvudspåret (eller kam_info.spar_id)
    huvud_spar = str(kam_info.get("spar_id", spar_lista[0]))
    huvud_roll = kam_info.get("huvudroll") or (roller_i_tagning[0] if roller_i_tagning else None)

    if len(roller_i_tagning) <= 1:
        for i, s in enumerate(spar_lista):
            if (s == huvud_spar or i == 0) and huvud_roll is not None and not ut:
                ut[s] = (huvud_roll, pose_av.get(huvud_roll, "sittande"))
            else:
                ut[s] = (None, "sittande")
        return ut

    # 2. Flera kända roller i samma tagning (t.ex. Guacamole S4 med både A och B!)
    anvanda_roller = set()
    spar_map_direkt = kam_info.get("spar_map", {}) if isinstance(kam_info, dict) else {}
    for s in spar_lista:
        if s in spar_map_direkt and spar_map_direkt[s] in roller_i_tagning:
            r = spar_map_direkt[s]
            ut[s] = (r, pose_av.get(r, "sittande"))
            anvanda_roller.add(r)

    if not ut and huvud_spar in spar_lista and huvud_roll in roller_i_tagning:
        ut[huvud_spar] = (huvud_roll, pose_av.get(huvud_roll, "sittande"))
        anvanda_roller.add(huvud_roll)

    # Kontrollera brief/lasning.json om den har modellbedömd hallning ("sitter"/"star") per spår
    las_map = {}
    for p in lasning_tagn.get("personspar", []):
        sid = str(p.get("spar_id"))
        ih = p.get("identitet_och_hallning", {})
        hall = ih.get("hallning")
        if hall:
            las_map[sid] = "staende" if str(hall).startswith("st") else "sittande"

    kvar_roller = [r for r in roller_i_tagning if r not in anvanda_roller]
    for s in spar_lista:
        if s in ut:
            continue
        if kvar_roller:
            # Om lasning.json anger pose för spåret, matcha roll med samma pose först
            sp_pose = las_map.get(s)
            match = next((r for r in kvar_roller if pose_av.get(r) == sp_pose), kvar_roller[0])
            ut[s] = (match, pose_av.get(match, sp_pose or "sittande"))
            kvar_roller.remove(match)
        else:
            ut[s] = (None, las_map.get(s, "sittande"))
    return ut


def _personer(t: Tagning, IX, spar_till_roll: dict[str, tuple[str | None, str]]):
    p_fil = t.mapp / "personer.json"
    if not p_fil.exists():
        return []
    sp = json.loads(p_fil.read_text(encoding="utf-8"))
    spar = sorted(sp, key=lambda s: -len(sp[s]))
    ut = []
    for s in spar:
        f = t.mapp / f"sekvens_{s}.npz"
        if not f.exists():
            continue
        q = np.load(f)
        m = min(t.ruta, len(q["cam_t_ra"]) - 1)
        # Använd median-translationen över tagningen men med bålens faktiska 3D-ledoffset (c_spine0/c_spine2)
        # istället för MHR-fotorigot cam_t_ra (som ligger ~1.3 m under kameran och ger fel horisontellt djup vid kamerapitch!)
        ct_med = np.median(q["cam_t_ra"], 0) * t.kappa
        J = q["pose"][m][:, :3] / 100.0 @ F.T + ct_med
        bal_p = (J[IX["c_spine0"]] + J[IX["c_spine2"]]) / 2.0
        l, r = J[IX["l_uparm"]], J[IX["r_uparm"]]
        fram = _n(np.cross(l - r, t.u))
        axel_rel = float(((l + r) / 2) @ t.u)
        roll, pose = spar_till_roll.get(s, (None, "sittande"))
        kal = [J[IX[n]] for n in ("l_uparm", "r_uparm", "l_clavicle", "r_clavicle") if n in IX]
        ut.append(dict(spar=s, roll=roll, p=bal_p, fram=fram, axel_rel=axel_rel, pose=pose, kal=kal))
    return ut


def _vaggar(t: Tagning, pers):
    vaggar = []
    for w in (t.rum.get("walls", []) if not t.omaskat else []):
        n = np.array(w["normal"], dtype=float)
        n2 = np.array([n[0] / t.a, n[1] / t.a, n[2]])
        s = np.linalg.norm(n2)
        n2, d2 = n2 / s, float(w["distance"]) / s * t.skala
        if abs(n2 @ t.u) > 0.25:
            continue
        b, avst = t.hor(d2 * n2)
        # Filtrera bort degenererade MoGe-plan på orimligt avstånd (t.ex. 14 000 m i asketch)
        if 0.3 < avst < 6.5:
            vaggar.append((b, avst, "rum.json"))
    bak = max([t.hor(p["p"])[1] for p in pers], default=0.0) + 0.1
    n = t.Nm[t.giltig]
    P = t.P[t.giltig]
    vert = np.abs(n @ t.u) < 0.15
    dist = np.hypot(P @ t.rh, P @ t.fh)
    urval = vert & (dist > bak) & (dist < 6.5)
    if urval.sum() > 0.03 * len(P):
        ang = np.degrees(np.arctan2(n[urval] @ t.rh, n[urval] @ t.fh))
        hist, kant = np.histogram(ang, bins=36, range=(-180, 180))
        topp = kant[np.argmax(hist)] + 5
        nara = np.abs((ang - topp + 180) % 360 - 180) < 15
        if nara.sum() > 0.02 * len(P):
            nn = _n(np.median(n[urval][nara], 0))
            off = float(np.median(P[urval][nara] @ nn))
            b, avst = t.hor(off * nn)
            if 0.3 < avst < 6.5 and not any(abs((b - v[0] + 180) % 360 - 180) < 20 for v in vaggar):
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
    golv = (n @ t.u > 0.85) & (h < -0.8)
    if tak.sum() < 500:
        return None
    hc = float(np.median(h[tak]))
    if golv.sum() > 500:
        return M(v=round(hc - float(np.median(h[golv])), 3), s=0.25)
    return M(v=round(hc + hcam, 3), s=0.35)


def _modell_semantik(ingest: pathlib.Path) -> dict | None:
    """Läser modellbedömd semantik/1 (från ingest eller scen/3d/kontrakt/semantik/ut/) utan handskriven deklaration."""
    kand = [ingest / "semantik/semantik.json"]
    sem_ut = ROT / "scen/3d/kontrakt/semantik/ut"
    if sem_ut.exists():
        namn = ingest.name.lower()
        # Sortera så att längre/specifikare mappnamn ('notan', 'kenny') provas före enbokstavsnamn ('a', 'b')!
        for m in sorted(sem_ut.iterdir(), key=lambda p: -len(p.name)):
            if not m.is_dir():
                continue
            mn = m.name.lower()
            if namn.startswith(mn + "-") or namn == mn or (len(mn) >= 3 and mn in namn):
                kand.append(m / "semantik.json")
    for fil in kand:
        if fil.exists():
            try:
                return json.loads(fil.read_text(encoding="utf-8")).get("data")
            except Exception:
                pass
    return None


def _geometrisk_reid_och_pose(ingest: pathlib.Path, tagn: list[str], sift_koppling: dict[str, str], IX: dict[str, int]) -> tuple[dict, dict, dict]:
    """Ren geometrisk reserv-inferens (SIFT-kameragrupper + 3D-knäböjning) om varken semantik.json eller deklaration finns."""
    # 1. Gruppera tagningar via SIFT-delad kameravy eller varannan-tagning-dialog
    kluster_till_roll: dict[str, str] = {}
    roller_per_tagn: dict[str, list[str]] = {}
    pose_per_roll: dict[str, list[str]] = {}
    kam_info: dict[str, dict] = {}
    roll_bokstaver = ["A", "B", "C", "D"]
    nasta_r = 0

    for S in tagn:
        mapp = ingest / S
        p_fil = mapp / "personer.json"
        sp_map = json.loads(p_fil.read_text(encoding="utf-8")) if p_fil.exists() else {}
        if not sp_map:
            continue
        spar_lista = sorted(sp_map, key=lambda s: -len(sp_map[s]))
        huvud_s = spar_lista[0]

        bas_s = sift_koppling.get(S.lower(), S.lower())
        if bas_s not in kluster_till_roll:
            kluster_till_roll[bas_s] = roll_bokstaver[min(nasta_r, len(roll_bokstaver) - 1)]
            nasta_r += 1
        r = kluster_till_roll[bas_s]
        roller_per_tagn[S] = [r]
        kam_info[S] = dict(spar_id=huvud_s, huvudroll=r)

        # Bedöm sittande vs stående ur 3D-skelettets knä-/höftvinkel
        seq_fil = mapp / f"sekvens_{huvud_s}.npz"
        if seq_fil.exists():
            q = np.load(seq_fil)
            J = np.median(q["pose"][:, :, :3], axis=0) / 100.0
            v_lar = J[IX["l_lowleg"]] - J[IX["l_upleg"]]
            v_vad = J[IX["l_foot"]] - J[IX["l_lowleg"]]
            cos_kna = float(np.dot(v_lar, v_vad) / ((np.linalg.norm(v_lar) * np.linalg.norm(v_vad)) + 1e-9))
            pose_per_roll.setdefault(r, []).append("sittande" if cos_kna < 0.65 else "staende")

    pose_av = {
        r: ("sittande" if l.count("sittande") >= l.count("staende") else "staende")
        for r, l in pose_per_roll.items()
    }
    return roller_per_tagn, pose_av, kam_info


def _roller_ur_kalla(
    ingest: pathlib.Path,
    tagn: list[str],
    sift_koppling: dict[str, str],
    IX: dict[str, int],
    utan_deklaration: bool = False,
) -> tuple[dict[str, dict], dict[str, list[str]], dict[str, str], dict[str, dict], str]:
    """Hämtar (roller, roller_per_tagn, pose_av, kameror_dekl, kalla_etikett).
    Prioritet när `utan_deklaration=True` (eller när deklaration.json saknas):
      1. Modellbedömd `semantik/1` (`P1 -> A`, `P2 -> B`, `P3 -> C` + `placeringar.hallning`)
      2. Ren geometrisk SIFT + 3D-skelett-fallback (`_geometrisk_reid_och_pose`).
    """
    dekl_fil = ingest / "plats/deklaration.json"
    kons_fil = ingest / "brief/konsensus/konsensus.json"
    sem = _modell_semantik(ingest)

    if not utan_deklaration and (dekl_fil.exists() or kons_fil.exists()):
        dekl = json.loads(dekl_fil.read_text(encoding="utf-8")) if dekl_fil.exists() else json.loads(kons_fil.read_text(encoding="utf-8"))
        roller = {
            r: v for r, v in dekl.get("roller", {}).items()
            if isinstance(v, dict) and r not in ("kameraman", "disk") and v.get("tagningar")
        }
        if roller:
            roller_per_tagn: dict[str, list[str]] = {}
            for r, v in roller.items():
                for S in v.get("tagningar", []):
                    roller_per_tagn.setdefault(S, []).append(r)
            pose_av = {r: ("staende" if str(v.get("lage", "")).startswith("st") else "sittande") for r, v in roller.items()}
            kameror_dekl = dekl.get("kameror", {})
            return roller, roller_per_tagn, pose_av, kameror_dekl, "deklaration.json"

    if sem and sem.get("personer"):
        # Mappa P1 -> A, P2 -> B, P3 -> C automatiskt ur den modellbedömda semantik/1-filen!
        p_lista = sem.get("personer", [])
        pid_till_roll = {p["id"]: chr(ord("A") + i) for i, p in enumerate(p_lista)}
        hall_map = {}
        for pl in sem.get("placeringar", []):
            hall_map[pl.get("person")] = "staende" if str(pl.get("hallning", "")).startswith("st") else "sittande"

        roller = {}
        roller_per_tagn = {}
        pose_av = {}
        kameror_dekl = {}
        for p in p_lista:
            r = pid_till_roll[p["id"]]
            pose = hall_map.get(p["id"], "staende")
            pose_av[r] = pose
            t_lista = []
            for sp in p.get("spar", []):
                S = sp["tagning"]
                sid = str(sp["spar_id"])
                t_lista.append(S)
                roller_per_tagn.setdefault(S, []).append(r)
                # Första nämnda rollen i tagningen eller spår 1 blir tagningens huvudroll
                if S not in kameror_dekl or sid == "1":
                    kameror_dekl[S] = dict(spar_id=sid, huvudroll=r, spar_map={})
                kameror_dekl.setdefault(S, {}).setdefault("spar_map", {})[sid] = r
            roller[r] = dict(beskrivning=p.get("beskrivning", ""), tagningar=t_lista, lage=pose)
        return roller, roller_per_tagn, pose_av, kameror_dekl, "semantik/1 (modellbedömd, deklarationsfri)"

    roller_per_tagn, pose_av, kameror_dekl = _geometrisk_reid_och_pose(ingest, tagn, sift_koppling, IX)
    roller = {
        r: dict(tagningar=[S for S, rl in roller_per_tagn.items() if r in rl], lage=pose_av.get(r, "staende"))
        for r in pose_av
    }
    return roller, roller_per_tagn, pose_av, kameror_dekl, "geometrisk_sift_reid (deklarationsfri)"


def bygg(
    ingest: pathlib.Path,
    vlm_mapp: pathlib.Path | None = None,
    djupmapp: pathlib.Path | None = None,
    utan_deklaration: bool = False,
) -> Observationer:
    IX = _leder()
    las_fil = ingest / "brief/lasning.json"
    lasning = json.loads(las_fil.read_text(encoding="utf-8")).get("tagningar", {}) if las_fil.exists() else {}

    tagn = sorted(p.name for p in ingest.iterdir() if p.is_dir() and p.name[:1] == "S" and p.name[1:].isdigit())
    tagn.sort(key=lambda s: int(s[1:]))
    fk = _fokal(ingest)
    sift_koppling = _sift_kameragrupper(ingest)

    roller, roller_per_tagn, pose_av, kameror_dekl, roll_kalla = _roller_ur_kalla(
        ingest, tagn, sift_koppling, IX, utan_deklaration=utan_deklaration
    )

    # Blickpar: roller som växlar i motbilder eller delar scen i dialog
    seq = [roller_per_tagn.get(S, [None])[0] for S in tagn]
    par = Counter(tuple(sorted((a, b))) for a, b in zip(seq, seq[1:]) if a and b and a != b)
    dialog = [p for p, n in par.items() if n >= 2]
    if not dialog and len(roller) == 2:
        dialog = [tuple(sorted(roller.keys()))]
    partner = {}
    for a, b in dialog:
        partner.setdefault(a, b)
        partner.setdefault(b, a)

    alla_nycklar = Counter()
    if vlm_mapp and vlm_mapp.exists():
        for S2 in tagn:
            fil = vlm_mapp / f"{S2}.json"
            if fil.exists():
                for fo in json.loads(fil.read_text(encoding="utf-8")).get("foremal", []):
                    if fo.get("distinkt"):
                        alla_nycklar[fo["nyckel"]] += 1

    ut, start = [], 0
    for S in tagn:
        mapp = ingest / S
        f_sann, f_sig = (fk[0], fk[1]) if fk else (None, None)
        seqs = sorted(mapp.glob("sekvens_*.npz"))
        if f_sann is None and seqs:
            q1 = np.load(seqs[0])
            f_sann, f_sig = float(q1["fokal"]), float(q1["fokal"]) * 0.15
        t = Tagning(mapp, f_sann, djupmapp)
        if f_sig is None:
            f_sig = t.f * 0.15
        hfov = 2 * math.degrees(math.atan(t.W / 2 / t.f))
        hfov_s = hfov * f_sig / t.f
        vlm = {}
        if vlm_mapp and (vlm_mapp / f"{S}.json").exists():
            vlm = json.loads((vlm_mapp / f"{S}.json").read_text(encoding="utf-8"))

        p_fil = mapp / "personer.json"
        sp_map = json.loads(p_fil.read_text(encoding="utf-8")) if p_fil.exists() else {}
        spar_lista = sorted(sp_map, key=lambda s: -len(sp_map[s]))
        kam_info = kameror_dekl.get(S, {}) if isinstance(kameror_dekl.get(S), dict) else {}
        spar_till_roll = _roll_och_pose_for_spar(
            S, spar_lista, roller_per_tagn.get(S, []), pose_av, kam_info, lasning.get(S, {})
        )
        pers = _personer(t, IX, spar_till_roll)
        dets = []

        hcam, hcam_s = 1.2, 0.3
        if pers:
            p0 = pers[0]
            hcam, hcam_s = AXELHOJD[p0["pose"]] - p0["axel_rel"], 0.12
        nara_bord = [
            o for o in t.rum.get("objects", [])
            if str(o.get("label", "")).lower() in BORD_ETIKETTER and float(o["centre"][2]) < 1.8
        ]
        if nara_bord and hcam < 0.86:
            hcam, hcam_s = 0.86, 0.12
        skala = t.kalibrera(pers[0]["kal"], hcam) if pers else None

        # --- Bord och diskar (ur rum.json + geometrisk fallback ur MoGe-ytnormaler) ---
        bord = []
        for o in t.rum.get("objects", []):
            if str(o.get("label", "")).lower() not in BORD_ETIKETTER:
                continue
            p = t.moge(o["centre"])
            if any(np.linalg.norm(_hor_xy(t, p) - _hor_xy(t, q)) < 0.4 for q in bord):
                continue
            bord.append(p)

        # Geometrisk möbeldetektion när rum.json saknar bord men MoGe visar en tydlig bords-/diskskiva
        if not bord:
            skiva_pt = t.horisontell_skiva_framfor(pers)
            if skiva_pt is not None:
                bord.append(skiva_pt)

        # R15: Bordet/disken framför en person ligger framför personens bröstkorg (pp["fram"]),
        # eller mitt emellan två samtalspartners som står på varsin sida om samma disk (t.ex. Guacamole S4).
        ankare = {}
        huvud_pers = [pp for pp in pers if pp["roll"] is not None]
        if len(huvud_pers) >= 2 and len(bord) == 1:
            ankare[0] = (huvud_pers[0]["p"] + huvud_pers[1]["p"]) / 2.0
        else:
            for pp in pers:
                if pp["pose"] != "sittande" and not (pp["roll"] is not None and len(bord) == 1):
                    continue
                pb, pd = t.hor(pp["p"])
                kand = [
                    i for i, q in enumerate(bord)
                    if i not in ankare and (abs(t.hor(q)[0] - pb) < 35 or len(bord) == 1) and t.hor(q)[1] < pd + 1.0
                ]
                if kand:
                    i = min(kand, key=lambda i: abs(t.hor(bord[i])[1] - (pd - 0.55)))
                    fram_hor = _n(pp["fram"] - (pp["fram"] @ t.u) * t.u)
                    sikt_hor = -_n(pp["p"] - (pp["p"] @ t.u) * t.u)
                    # Om bröstkorgen vänder sig snett/framåt, placera bordet framför bröstkorgen (stabilt vid sidovyer!)
                    rikt = fram_hor if float(fram_hor @ sikt_hor) > -0.2 else sikt_hor
                    ankare[i] = pp["p"] + 0.55 * rikt

        bord_id = {}
        for i, p in enumerate(bord):
            did = f"{S}:t{i + 1}"
            if i in ankare:
                p = ankare[i]
            b, d = t.hor(p)
            bord_id[did] = p
            s_d = 0.25 if i in ankare else 0.35 * d
            dets.append(Detektion(
                id=did, klass="bord", nyckel="bord",
                bearing_deg=M(v=round(b, 2), s=3.0),
                djup_m=M(v=round(d, 3), s=round(s_d, 3)),
                amodal=d < 1.6,
            ))

        # --- Personer ---
        # Sittande personer knyts alltid till sitt bord. Stående huvudroller knyts till en disk framför dem
        # om inget sittande spår i samma tagning redan är en fristående restauranggäst vid ett annat bord.
        har_sittande_och_staende_huvudroller = (
            len([p for p in pers if p["roll"] is not None]) >= 2
        )
        for i, pp in enumerate(pers):
            b, d = t.hor(pp["p"])
            fb = math.degrees(math.atan2(float(pp["fram"] @ t.rh), float(pp["fram"] @ t.fh)))
            did = f"{S}:p{i + 1}"
            vid = None
            if bord_id:
                if pp["pose"] == "sittande":
                    kand = min(bord_id, key=lambda k: np.linalg.norm(_hor_xy(t, bord_id[k]) - _hor_xy(t, pp["p"])))
                    if np.linalg.norm(_hor_xy(t, bord_id[kand]) - _hor_xy(t, pp["p"])) < 1.6:
                        vid = kand
                elif pp["roll"] is not None and (
                    not any(p2["pose"] == "sittande" for p2 in pers) or har_sittande_och_staende_huvudroller
                ):
                    kand = min(bord_id, key=lambda k: np.linalg.norm(_hor_xy(t, bord_id[k]) - _hor_xy(t, pp["p"])))
                    if np.linalg.norm(_hor_xy(t, bord_id[kand]) - _hor_xy(t, pp["p"])) < 1.35:
                        vid = kand
            nyckel = f"person:{pp['roll']}" if pp["roll"] else "person:okand"
            dets.append(Detektion(
                id=did, klass="person", nyckel=nyckel, unik=bool(pp["roll"]),
                bearing_deg=M(v=round(b, 2), s=1.5),
                djup_m=M(v=round(d, 3), s=round(0.14 * d, 3)),
                vridning_deg=M(v=round(fb, 1), s=20.0),
                pose=pp["pose"],
                blick_mot=(f"person:{partner[pp['roll']]}" if pp["roll"] in partner else None),
                vid=vid,
            ))

        # --- Föremål och dörrar ur VLM ---
        for i, fo in enumerate(vlm.get("foremal", [])):
            if not (fo.get("distinkt") and fo.get("pa_bord") and alla_nycklar[fo["nyckel"]] >= 2):
                continue
            p = t.djup_vid(fo["x_andel"], fo["y_andel"])
            if p is None:
                continue
            b, d = t.hor(p)
            pa = None
            if bord_id:
                kand = min(bord_id, key=lambda k: np.linalg.norm(_hor_xy(t, bord_id[k]) - _hor_xy(t, p)))
                if np.linalg.norm(_hor_xy(t, bord_id[kand]) - _hor_xy(t, p)) < 0.95:
                    pa = kand
            dets.append(Detektion(
                id=f"{S}:f{i + 1}", klass="foremal", nyckel=f"foremal:{fo['nyckel']}",
                bearing_deg=M(v=round(b, 2), s=2.0),
                djup_m=M(v=round(d, 3), s=round(0.35 * d, 3)),
                pa=pa,
                farg_signatur=t.farg_vid(fo["x_andel"], fo["y_andel"]),
            ))

        for i, x in enumerate(vlm.get("dorrar_x_andel", [])):
            p = t.djup_vid(x, 0.45, ruta=10)
            if p is None:
                continue
            b, d = t.hor(p)
            dets.append(Detektion(
                id=f"{S}:d{i + 1}", klass="dorr", nyckel="dorr",
                bearing_deg=M(v=round(b, 2), s=3.0),
                djup_m=M(v=round(d, 3), s=round(0.4 * d, 3)),
                pa_vagg=True,
            ))

        pd0 = t.hor(pers[0]["p"])[1] if pers else 1.5
        vaggar = [
            Vagg(
                bearing_deg=M(v=round(b, 1), s=6.0),
                avstand_m=M(v=round(a, 3), s=round((0.6 if a > 2 * pd0 else 0.4) * a, 3)),
                nyckel=k,
            )
            for b, a, k in _vaggar(t, pers)
        ]

        ljus = None
        lf = vlm.get("ljus_fran")
        if lf == "hoger":
            ljus = M(v=85.0, s=40.0)
        elif lf == "vanster":
            ljus = M(v=-85.0, s=40.0)
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

        kam = Kamera(
            bild_px=(t.W, t.H),
            hfov_deg=M(v=round(hfov, 2), s=round(max(hfov_s, 1.0), 2)),
            hojd_m=M(v=round(hcam, 3), s=hcam_s),
            pitch_deg=M(v=round(t.pitch, 2), s=t.u_sigma),
            roll_deg=M(v=round(t.roll, 2), s=t.u_sigma),
        )
        ut.append(KlippObs(
            klipp=S.lower(), rutor=(start, start + t.N), kamera=kam, detektioner=dets, vaggar=vaggar,
            manhattan_deg=_manhattan(t), ljus_bearing_deg=ljus,
            takhojd_m=_takhojd(t, hcam) if "tak" in nycklar else None,
            rumsnycklar=nycklar, stralar=_stralar(t, hfov, pers),
            djupgrid=t.djupgrid() if t.omaskat else None,
            skala=round(skala, 3) if skala else None,
            delar_kamera_med=sift_koppling.get(S.lower()),
        ))
        start += t.N

    return Observationer(
        klipp_id=ingest.name,
        fps=float(json.loads((ingest / tagn[0] / "meta.json").read_text())["fps"]),
        klipp=ut,
    )
