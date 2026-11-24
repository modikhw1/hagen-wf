"""G7 oberoende – 2D-trohet för slutliga `forvarld_karna/ut/<klipp>/paket.json` mot ingestens egna 2D-observationer.

Motpart runda 1 (Claude), lane A1 + G7. Ändrar inget i `forvarld_karna/` eller `scen/`; läser bara.

Vad som jämförs (per tagning, person och bildruta):
  paketets 3D-leder (efter ALL efterbehandling: R25, fotkontakt, disk-skjutning, z-skift) projiceras genom paketets
  egen kamera (linjär interpolation mellan nycklar, som `emit_bpy.py` ställer in i Blender) och jämförs med
  (1) SAM 3D Body `pred_keypoints_2d` (rå, per ruta, `kropp/<spår>/<ruta>.npz`)       – svag oberoendegrad (samma modell som 3D-lyftet)
  (2) YOLO11n-seg + ByteTrack personruta (`personer.json`)                           – annan modell (stark), men SAM promptas med rutan
  (3) YOLO11n-seg personmask, union av alla personer, 1/4 upplösning, dilaterad 7x7 (`masker.npy`) – annan modell (stark)
  Referens "nativ": samma T1-leder ur `sekvens_<spår>.npz` projicerade med SAM:s egen fokal (före scen_brygga).
  Den visar vad ett korrekt placerat skelett når mot (2)–(3) och isolerar scen_bryggas kedjefel från SAM:s utjämning.

Mått per (tagning, person):
  led_med / led_p90  median/p90 av |paket − SAM-2D| / bildhöjd över parade leder (axlar, armbågar, handleder, hals;
                     höfter och knän bara när ingesten säger att benen syns). Gräns 0,03 (ärvd: Argons `_trohet_mot_2d`
                     och gamla `scen/3d/kontrakt/trohet.py` GRANS_SLUTBILD).
  i_box              andel av överkroppsleder (som nativt ligger i bild) vars paketprojektion ligger i personens YOLO-ruta
                     (+5 % marginal). Korrekt placering ⇒ ≈ 1. Gräns 0,80.
  iou                median box-IoU mellan paketets ledruta (synliga leder, klippt till bild) och YOLO-rutan; `iou_ref` är
                     samma mått för det nativa skelettet (tak för ledruta mot silhuettruta).
  i_mask             som i_box men mot YOLO-masken (rapporteras; ingen egen grind eftersom masken är en union).
  id                 vilket YOLO-spår paketpersonens ruta överlappar mest; i flerpersonstagningar måste det vara det spår
                     som paketet byggde personen ur.
  FLAGGA = led_med > 0,03  ELLER  i_box < 0,80  ELLER  fel id.

Kör (PowerShell, från repo-roten):
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-1-claude\\g7_oberoende.py              # mät de fyra slutpaketen
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-1-claude\\g7_oberoende.py --kalibrera  # felinjektion + Argons G7 på samma paket
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-1-claude\\g7_oberoende.py --a1         # uppströmsinjektion via scen_brygga
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-1-claude\\g7_oberoende.py --bilder     # överlägg i g7_bilder/
Utdata: motpart/runda-1-claude/g7_resultat.json (+ g7_kalibrering.json, g7_a1.json, g7_bilder/*.png)
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import pathlib
import sys
import tempfile

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parent.parent
sys.path.insert(0, str(ROT / "byggsten/brygga"))
from rotation import quat_till_mat, quat_xyzw  # noqa: E402

KLIPP = {
    "guacamole": "scen/3d/ingest/ut/e-dialog-guacamole-tagningar",
    "gelato": "scen/3d/ingest/ut/kand-kennysgelato-tagningar",
    "asketch": "scen/3d/ingest/ut/a-sketch-servering-tagningar",
    "notan": "scen/3d/ingest/ut/notan-tagningar",
}
F = np.diag([1.0, -1.0, -1.0])
SENSOR = 36.0
# T1-led -> MHR70-index. Parens 3D-avstånd i SAM:s egen ruta är verifierat i G7.md (axlar/höfter/handleder < 1 cm,
# armbågar ≈ 2 cm, hals ≈ 3 cm). Knän/vrister skiljer 30–45 cm när benen är skymda (sekvensen nollställer då benen).
PAR_OVER = [("l_uparm", 5), ("r_uparm", 6), ("l_lowarm", 7), ("r_lowarm", 8), ("l_wrist", 62), ("r_wrist", 41), ("c_neck", 69)]
PAR_BEN = [("l_upleg", 9), ("r_upleg", 10), ("l_lowleg", 11), ("r_lowleg", 12)]
OVER = ["c_spine2", "c_spine3", "c_neck", "c_head", "huvud_upp", "l_clavicle", "r_clavicle", "l_uparm", "r_uparm",
        "l_lowarm", "r_lowarm", "l_wrist", "r_wrist", "l_hand_mitt", "r_hand_mitt"]
# Kärna för i_box/i_mask: huvud, hals och axlar. Händer/underarmar är ofta bakom disk/tallrik (asketch s5, gelato) och
# ligger då legitimt utanför YOLO-rutan även för det nativa skelettet; de ingår därför bara i iou och led-måttet.
KARNA = ["c_head", "huvud_upp", "c_neck", "c_spine3", "l_clavicle", "r_clavicle", "l_uparm", "r_uparm"]
BEN = ["c_spine0", "c_spine1", "l_upleg", "r_upleg", "l_lowleg", "r_lowleg", "l_foot", "r_foot", "l_ball", "r_ball"]
HARLEDD = {"l_hand_mitt": ("l_index1", "l_pinky1"), "r_hand_mitt": ("r_index1", "r_pinky1")}
GRANS = dict(led_med=0.03, i_box=0.80, i_mask=0.80, ref_giltig=0.90, spok_andel=0.20, marginal=0.05)


# ----------------------------------------------------------------------------------------------- hjälpare
def las_json(p: pathlib.Path, standard=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else standard


def kamera_vid(t: dict, u: float):
    """Kamera (C, R, lins_mm) i ruta u. Linjär interpolation mellan nycklar (emit_bpy sätter LINEAR i Blender)."""
    ks = t["kamera"]["nycklar"]
    if len(ks) == 1 or u <= ks[0][0]:
        k = ks[0]
        return np.array(k[1:4], float), quat_till_mat(k[4:8]), float(k[8])
    if u >= ks[-1][0]:
        k = ks[-1]
        return np.array(k[1:4], float), quat_till_mat(k[4:8]), float(k[8])
    for a, b in zip(ks, ks[1:]):
        if a[0] <= u <= b[0]:
            w = (u - a[0]) / max(b[0] - a[0], 1e-9)
            C = (1 - w) * np.array(a[1:4], float) + w * np.array(b[1:4], float)
            qa, qb = np.array(a[4:8], float), np.array(b[4:8], float)
            if qa @ qb < 0:
                qb = -qb
            q = (1 - w) * qa + w * qb
            return C, quat_till_mat(q / np.linalg.norm(q)), (1 - w) * a[8] + w * b[8]
    raise ValueError("kamera_vid")


def proj(X, C, R, lins, W, H):
    c = (np.asarray(X) - C) @ R
    d = -c[..., 2]
    f = lins / SENSOR * W
    return c[..., :2] / np.maximum(d[..., None], 1e-6) * [f, -f] + [W / 2, H / 2], d


def ruta(uv):
    return np.array([uv[:, 0].min(), uv[:, 1].min(), uv[:, 0].max(), uv[:, 1].max()])


def iou(a, b):
    lo = np.maximum(a[:2], b[:2]); hi = np.minimum(a[2:], b[2:])
    inter = float(np.maximum(hi - lo, 0).prod())
    uni = float(np.maximum(a[2:] - a[:2], 0).prod() + np.maximum(b[2:] - b[:2], 0).prod() - inter)
    return inter / max(uni, 1e-9)


def klipp_till_bild(uv, W, H):
    return np.column_stack([np.clip(uv[:, 0], 0, W), np.clip(uv[:, 1], 0, H)])


# ----------------------------------------------------------------------------------------------- ingest per tagning
class Tagning:
    """Allt oberoende 2D-underlag för en tagning, plus spårtilldelningen som scen_brygga gör (ordningsbaserad)."""

    def __init__(self, ingest: pathlib.Path, obs_klipp: dict, paket_t: dict, leder: list[str]):
        self.sid = paket_t["id"]
        self.S = ingest / self.sid.upper()
        self.meta = las_json(self.S / "meta.json")
        self.spar = las_json(self.S / "personer.json", {})
        self.sem = (las_json(self.S / "semantik_beslut.json", {}) or {}).get("roller") or {}
        mf = self.S / "masker.npy"
        self.mask = np.load(mf, mmap_mode="r") if mf.exists() else None
        self.leder = leder
        # Exakt som scen_brygga.kompilera_scenpaket rad 266–284: i:te personen i obs <-> i:te längsta spåret.
        p_dets = [d for d in obs_klipp["detektioner"] if d["klass"] == "person"]
        spar_lista = sorted(self.spar, key=lambda s: -len(self.spar[s]))
        anvanda = []
        for i, _ in enumerate(p_dets):
            if i >= len(spar_lista):
                break
            if (self.S / f"sekvens_{spar_lista[i]}.npz").exists():
                anvanda.append(spar_lista[i])
        pids = [p["id"] for p in paket_t["personer"]]
        assert len(pids) == len(anvanda), (self.sid, pids, anvanda)
        self.spar_for = dict(zip(pids, anvanda))
        self._seq, self._raw, self._pal = {}, {}, {}

    def seq(self, spar):
        if spar not in self._seq:
            self._seq[spar] = dict(np.load(self.S / f"sekvens_{spar}.npz"))
        return self._seq[spar]

    def raw(self, spar, f):
        k = (spar, f)
        if k not in self._raw:
            p = self.S / "kropp" / spar / f"{f:04d}.npz"
            if p.exists():
                z = np.load(p)
                self._raw[k] = dict(kp2=z["pred_keypoints_2d"].astype(float), bbox=z["bbox"].astype(float),
                                    fokal=float(z["focal_length"]))
            else:
                self._raw[k] = None
        return self._raw[k]

    def palitlig(self, spar, f):
        if spar not in self._pal:
            self._pal[spar] = las_json(self.S / f"palitlig_{spar}.json", {})
        return bool(self._pal[spar].get(str(f), True))

    def yolo(self, spar, f):
        b = self.spar.get(spar, {}).get(str(f))
        return None if b is None else np.array(b, float)

    def nativ_t1(self, spar, f, W, H):
        """T1-lederna ur sekvensen i SAM:s kameraram, projicerade med SAM:s egen fokal (ingen kappa, ingen rumskamera)."""
        q = self.seq(spar)
        n = len(q["pose"])
        fi = min(f, n - 1)
        IX = TRO_IX
        c = q["pose"][fi][:, :3] / 100.0 + F @ q["cam_t_ra"][fi]
        hi = IX["c_head"]
        Mh = quat_xyzw(q["pose"][fi][hi, 3:7]) @ quat_xyzw(q["rest"][hi, 3:7]).T
        pts = []
        for nm in self.leder:
            if nm == "huvud_upp":
                pts.append(c[hi] + Mh @ np.array([0.0, 0.10, 0.0]))
            elif nm == "nasa_mal":
                pts.append(c[hi] + Mh @ np.array([0.0, 0.03, 0.12]))
            else:
                pts.append(c[[IX[k] for k in HARLEDD.get(nm, (nm,))]].mean(axis=0))
        pts = np.array(pts)
        fo = float(q["fokal"])
        uv = pts[:, :2] / np.maximum(-pts[:, 2:3], 1e-6) * [fo, -fo] + [W / 2, H / 2]
        return uv, bool(q["ben_synliga"][fi]), fo

    def maskvarde(self, uv, W, H):
        if self.mask is None:
            return np.zeros(len(uv), bool)
        m = self.mask
        f_idx = self._mask_f
        mh, mw = m.shape[1:]
        x = np.clip((uv[:, 0] / W * mw).astype(int), 0, mw - 1)
        y = np.clip((uv[:, 1] / H * mh).astype(int), 0, mh - 1)
        inne = (uv[:, 0] >= 0) & (uv[:, 0] < W) & (uv[:, 1] >= 0) & (uv[:, 1] < H)
        return inne & np.asarray(m[f_idx])[y, x]


TRO_IX = {n: i for i, n in enumerate(json.loads((ROT / "scen/3d/kontrakt/tro_rigg.json").read_text(encoding="utf-8"))["namn"])}


# ----------------------------------------------------------------------------------------------- mätning
def mat_paket(namn: str, paket: dict, obs: dict | None = None, per_ruta: bool = False,
              ingest: pathlib.Path | None = None, tagningar: set | None = None) -> list[dict]:
    ingest = pathlib.Path(ingest) if ingest else ROT / KLIPP[namn]
    obs = obs or las_json(ROT / "forvarld_karna/ut" / namn / "obs.json")
    W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
    L = paket["leder"]
    LI = {n: i for i, n in enumerate(L)}
    over_ix = [LI[n] for n in OVER]
    karna_ix = [LI[n] for n in KARNA]
    ben_ix = [LI[n] for n in BEN]
    rader = []
    for t in paket["tagningar"]:
        if not t["personer"] or (tagningar and t["id"] not in tagningar):
            continue
        a0, b0 = t["ut"]
        ok = next(k for k in obs["klipp"] if k["klipp"] == t["id"])
        tg = Tagning(ingest, ok, t, L)
        for p in t["personer"]:
            pid = p["id"]
            spar = tg.spar_for[pid]
            sp = next(x for x in paket["rorelse"][pid] if x["tagning"] == t["id"])
            led_fel, kedja_fel, ious, ious_ref, ibox, ibox_ref, imask, imask_ref = [], [], [], [], [], [], [], []
            ibox_over, ibox_over_ref = [], []
            skift_mat, skift_pred, rest_v, rest_abs = [], [], [], []
            id_iou: dict[str, list[float]] = {s: [] for s in tg.spar}
            utan_obs, spok = 0, 0
            n_raw = n_yolo = 0
            rader_ruta = []
            for r in sp["rutor"]:
                u = r[0]
                f = u - a0
                X = np.array(r[1:], float).reshape(-1, 3) / 1000.0
                C, R, lins = kamera_vid(t, u)
                uv, d = proj(X, C, R, lins, W, H)
                uv_nat, ben, f_sam = tg.nativ_t1(spar, f, W, H)
                tg._mask_f = min(f, (tg.mask.shape[0] - 1) if tg.mask is not None else 0)
                raw = tg.raw(spar, f)
                yb = tg.yolo(spar, f)
                pal = tg.palitlig(spar, f)
                # referensmängd: överkroppsleder som nativt ligger i bild
                def i_bild(pp):
                    return (pp[:, 0] >= 0) & (pp[:, 0] < W) & (pp[:, 1] >= 0) & (pp[:, 1] < H)
                nat_in = i_bild(uv_nat[over_ix])
                nat_in_k = i_bild(uv_nat[karna_ix])
                # kedjefel (scen_brygga mot nativ), överkropp
                kedja_fel += list(np.linalg.norm(uv[over_ix] - uv_nat[over_ix], axis=1)[nat_in] / H)
                # förutsagt kappa-skift för bålen: (f_px/f_sam − 1)·(bål_nativ − mitt); rest = mätt − förutsagt
                kap = (lins / SENSOR * W) / f_sam
                sp2 = LI["c_spine2"]
                pred = (kap - 1.0) * (uv_nat[sp2] - [W / 2, H / 2])
                mat = uv[sp2] - uv_nat[sp2]
                skift_pred.append(np.linalg.norm(pred) / H)
                skift_mat.append(np.linalg.norm(mat) / H)
                rest_v.append(float((mat - pred)[1]) / H)
                rest_abs.append(float(np.linalg.norm(mat - pred)) / H)
                rad_r = dict(u=u, f=f)
                if raw is not None and pal:
                    n_raw += 1
                    par = PAR_OVER + (PAR_BEN if ben else [])
                    e = []
                    for nm, k in par:
                        x, y = raw["kp2"][k]
                        if 0 <= x < W and 0 <= y < H and d[LI[nm]] > 0:
                            e.append(float(np.linalg.norm(uv[LI[nm]] - raw["kp2"][k]) / H))
                    led_fel += e
                    rad_r["led_med"] = float(np.median(e)) if e else None
                if yb is not None:
                    n_yolo += 1
                    synl = over_ix + (ben_ix if ben else [])
                    vis = [j for j in synl if d[j] > 0]
                    b_p = ruta(klipp_till_bild(uv[vis], W, H)) if vis else np.zeros(4)
                    b_n = ruta(klipp_till_bild(uv_nat[synl], W, H))
                    ious.append(iou(b_p, yb)); ious_ref.append(iou(b_n, yb))
                    m = GRANS["marginal"] * (yb[3] - yb[1])
                    ybm = yb + [-m, -m, m, m]
                    def i_ruta(pp):
                        return (pp[:, 0] >= ybm[0]) & (pp[:, 0] <= ybm[2]) & (pp[:, 1] >= ybm[1]) & (pp[:, 1] <= ybm[3])
                    if nat_in_k.any():
                        ok_p = i_ruta(uv[karna_ix]) & (d[karna_ix] > 0)
                        ibox.append(float(ok_p[nat_in_k].mean()))
                        ibox_ref.append(float(i_ruta(uv_nat[karna_ix])[nat_in_k].mean()))
                        imask.append(float(tg.maskvarde(uv[karna_ix], W, H)[nat_in_k].mean()))
                        imask_ref.append(float(tg.maskvarde(uv_nat[karna_ix], W, H)[nat_in_k].mean()))
                    if nat_in.any():
                        ibox_over.append(float((i_ruta(uv[over_ix]) & (d[over_ix] > 0))[nat_in].mean()))
                        ibox_over_ref.append(float(i_ruta(uv_nat[over_ix])[nat_in].mean()))
                    for s in tg.spar:
                        bs = tg.yolo(s, f)
                        if bs is not None:
                            id_iou[s].append(iou(b_p, bs))
                    rad_r.update(iou=ious[-1], i_box=ibox[-1] if ibox else None)
                else:
                    utan_obs += 1
                    # spöknärvaro: paketet visar överkroppen i bild där YOLO-masken (alla personer) är tom
                    inb = (uv[over_ix, 0] >= 0) & (uv[over_ix, 0] < W) & (uv[over_ix, 1] >= 0) & (uv[over_ix, 1] < H) & (d[over_ix] > 0)
                    if inb.mean() >= 0.5 and tg.maskvarde(uv[over_ix], W, H)[inb].mean() < 0.2:
                        spok += 1
                if per_ruta:
                    rader_ruta.append(rad_r)
            id_med = {s: float(np.median(v)) for s, v in id_iou.items() if v}
            basta = max(id_med, key=id_med.get) if id_med else None
            led_med = float(np.median(led_fel)) if led_fel else None
            ib = float(np.mean(ibox)) if ibox else None
            ib_ref = float(np.mean(ibox_ref)) if ibox_ref else None
            im = float(np.mean(imask)) if imask else None
            im_ref = float(np.mean(imask_ref)) if imask_ref else None
            spok_andel = spok / max(len(sp["rutor"]), 1)
            skal = []
            # G7a (svag oberoendegrad): parade leder mot SAM:s råa 2D
            if led_med is not None and led_med > GRANS["led_med"]:
                skal.append(f"G7a led_med {led_med:.3f} > {GRANS['led_med']}")
            # G7b/G7c (stark): YOLO-ruta/-mask. Gäller bara när ett korrekt placerat skelett (nativ ref) klarar testet.
            if ib is not None and ib_ref is not None and ib_ref >= GRANS["ref_giltig"] and ib < GRANS["i_box"]:
                skal.append(f"G7b i_box {ib:.2f} < {GRANS['i_box']} (ref {ib_ref:.2f})")
            if im is not None and im_ref is not None and im_ref >= GRANS["ref_giltig"] and im < GRANS["i_mask"]:
                skal.append(f"G7c i_mask {im:.2f} < {GRANS['i_mask']} (ref {im_ref:.2f})")
            # G7d (stark): identitet i flerpersonstagningar
            if len(id_med) >= 2 and basta != spar:
                skal.append(f"G7d id: överlappar spår {basta}, byggd ur spår {spar}")
            # G7e (stark): närvaro i rutor där YOLO inte ser någon person på paketets plats
            if spok_andel > GRANS["spok_andel"]:
                skal.append(f"G7e spök {spok}/{len(sp['rutor'])} rutor")
            matbar = dict(G7a=led_med is not None,
                          G7b=ib_ref is not None and ib_ref >= GRANS["ref_giltig"],
                          G7c=im_ref is not None and im_ref >= GRANS["ref_giltig"],
                          G7d=len(id_med) >= 2, G7e=True)
            rad = dict(
                klipp=namn, tagning=t["id"], person=pid, spar=spar, semantik_roll=tg.sem.get(spar),
                rutor=len(sp["rutor"]), rutor_sam=n_raw, rutor_yolo=n_yolo, rutor_utan_obs=utan_obs, spok_rutor=spok,
                spok_andel=round(spok_andel, 3), matbar=matbar,
                led_med=None if led_med is None else round(led_med, 4),
                led_p90=None if not led_fel else round(float(np.percentile(led_fel, 90)), 4),
                kedja_med=round(float(np.median(kedja_fel)), 4) if kedja_fel else None,
                bal_skift_mat=round(float(np.median(skift_mat)), 4), bal_skift_kappa=round(float(np.median(skift_pred)), 4),
                rest_efter_kappa=round(float(np.median(rest_abs)), 4), rest_vertikal=round(float(np.median(rest_v)), 4),
                kamera_z=round(float(t["kamera"]["nycklar"][0][3]), 3),
                i_box_overkropp=round(float(np.mean(ibox_over)), 3) if ibox_over else None,
                i_box_overkropp_ref=round(float(np.mean(ibox_over_ref)), 3) if ibox_over_ref else None,
                iou=round(float(np.median(ious)), 3) if ious else None,
                iou_ref=round(float(np.median(ious_ref)), 3) if ious_ref else None,
                i_box=None if ib is None else round(ib, 3),
                i_box_ref=round(float(np.mean(ibox_ref)), 3) if ibox_ref else None,
                i_mask=round(float(np.mean(imask)), 3) if imask else None,
                i_mask_ref=round(float(np.mean(imask_ref)), 3) if imask_ref else None,
                id_iou={s: round(v, 3) for s, v in id_med.items()}, id_basta=basta,
                flaggad=bool(skal), skal=skal,
                argon_g7=paket.get("trohet", {}).get(f"{t['id']}:{pid}"),
            )
            if per_ruta:
                rad["per_ruta"] = rader_ruta
            rader.append(rad)
    return rader


# ----------------------------------------------------------------------------------------------- felinjektion
def _personens_spar(paket, sid, pid):
    return next(x for x in paket["rorelse"][pid] if x["tagning"] == sid)


def _forandra(paket, sid, pid, fn):
    t = next(t for t in paket["tagningar"] if t["id"] == sid)
    sp = _personens_spar(paket, sid, pid)
    ny = []
    for r in sp["rutor"]:
        X = np.array(r[1:], float).reshape(-1, 3) / 1000.0
        X = fn(X, kamera_vid(t, r[0]), paket["leder"])
        ny.append([r[0]] + [int(round(c * 1000)) for c in X.reshape(-1)])
    sp["rutor"] = ny


def inj_lateral(X, kam, L, m=0.5):
    _, R, _ = kam
    h = R[:, 0].copy(); h[2] = 0.0; h /= np.linalg.norm(h)        # kamerans högerriktning i golvplanet
    return X + m * h


def inj_djup(X, kam, L, m=0.5):
    _, R, _ = kam
    v = -R[:, 2].copy(); v[2] = 0.0; v /= np.linalg.norm(v)       # kamerans blickriktning i golvplanet
    return X + m * v


def inj_huk(X, kam, L):
    LI = {n: i for i, n in enumerate(L)}
    Y = X.copy()
    fot = {LI[n] for n in ("l_foot", "r_foot", "l_ball", "r_ball")}
    kna = {LI[n] for n in ("l_lowleg", "r_lowleg")}
    for j in range(len(L)):
        if j in fot:
            continue
        Y[j, 2] -= 0.20 if j in kna else 0.45
    return Y


INJEKTIONER = {
    "lateral_0.5m": inj_lateral,
    "djup_0.5m": inj_djup,
    "huk_0.45m": inj_huk,
}


def byt_ab(paket, sid):
    t = next(t for t in paket["tagningar"] if t["id"] == sid)
    a, b = [p["id"] for p in t["personer"]][:2]
    sa, sb = _personens_spar(paket, sid, a), _personens_spar(paket, sid, b)
    sa["rutor"], sb["rutor"] = sb["rutor"], sa["rutor"]
    return a, b


def argons_g7(paket):
    """Kör byggsten/brygga/grindar.mat oförändrad på (injicerat) paket och returnerar G7-raderna."""
    import grindar
    return [(r["tagning"], r.get("person"), r.get("G7_trohet", {}).get("ok")) for r in grindar.mat(paket)]


def grindar_per_person(paket):
    """P4: grindar.mat skriver över raden per person (rad per tagning, sista personen vinner). Här körs den oförändrade
    grindar.mat på en vy per person, så att varje (tagning, person) får en egen rad."""
    import grindar
    rader = []
    for pid in paket["rorelse"]:
        vy = dict(paket)
        vy["rorelse"] = {pid: paket["rorelse"][pid]}
        vy["tagningar"] = [dict(t, personer=[p for p in t["personer"] if p["id"] == pid]) for t in paket["tagningar"]
                           if any(p["id"] == pid for p in t["personer"])]
        rader += grindar.mat(vy)
    return sorted(rader, key=lambda r: (r["tagning"], r.get("person", "")))


def _yolo_bara(skal):
    return [s for s in skal if not s.startswith("G7a")]


def kalibrera() -> dict:
    ut = {"injektioner": [], "original": {}}
    for namn in KLIPP:
        paket = las_json(ROT / "forvarld_karna/ut" / namn / "paket.json")
        obs = las_json(ROT / "forvarld_karna/ut" / namn / "obs.json")
        bas = {(r["tagning"], r["person"]): r for r in mat_paket(namn, paket, obs)}
        ut["original"][namn] = {f"{k[0]}:{k[1]}": dict(flaggad=v["flaggad"], skal=v["skal"], led_med=v["led_med"])
                                for k, v in bas.items()}

        def rad(sid, pid, inj, r, g7a):
            o = bas[(sid, pid)]
            return dict(klipp=namn, tagning=sid, person=pid, injektion=inj, flaggad=r["flaggad"], skal=r["skal"],
                        flaggad_yolo_bara=bool(_yolo_bara(r["skal"])), led_med=r["led_med"], i_box=r["i_box"],
                        i_mask=r["i_mask"], iou=r["iou"], original_flaggad=o["flaggad"], original_skal=o["skal"],
                        original_led_med=o["led_med"], original_i_box=o["i_box"], original_i_mask=o["i_mask"],
                        argon_g7_ok=g7a)
        for (sid, pid) in bas:
            for inj, fn in INJEKTIONER.items():
                p2 = copy.deepcopy(paket)
                _forandra(p2, sid, pid, fn)
                r = next(x for x in mat_paket(namn, p2, obs, tagningar={sid}) if x["person"] == pid)
                g7a = [ok for (s, pp, ok) in argons_g7(p2) if s == sid]
                ut["injektioner"].append(rad(sid, pid, inj, r, g7a))
        for t in paket["tagningar"]:
            if len(t["personer"]) >= 2:
                p2 = copy.deepcopy(paket)
                a, b = byt_ab(p2, t["id"])
                g7a = [ok for (s, pp, ok) in argons_g7(p2) if s == t["id"]]
                for r in mat_paket(namn, p2, obs, tagningar={t["id"]}):
                    ut["injektioner"].append(rad(t["id"], r["person"], f"byt_{a}_{b}", r, g7a))
    # Tröskelsvep för G7a på de original som inte larmar (av något skäl) och på injektionerna i just dem.
    rena = {(n, k) for n, d in ut["original"].items() for k, v in d.items() if not v["flaggad"]}
    orig_led = [v["led_med"] for n, d in ut["original"].items() for k, v in d.items()
                if (n, k) in rena and v["led_med"] is not None]
    inj_rena = [r for r in ut["injektioner"] if (r["klipp"], f"{r['tagning']}:{r['person']}") in rena]
    svep = []
    for tr in (0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.075):
        svep.append(dict(troskel=tr, original_larm=sum(v > tr for v in orig_led), original_n=len(orig_led),
                         **{inj: f"{sum(1 for r in inj_rena if r['injektion'].startswith(inj) and r['led_med'] is not None and r['led_med'] > tr)}"
                                 f"/{sum(1 for r in inj_rena if r['injektion'].startswith(inj) and r['led_med'] is not None)}"
                            for inj in ("lateral", "djup", "huk", "byt")}))
    ut["svep_G7a"] = svep
    ut["sammanfattning"] = dict(
        original_utan_larm=sorted(f"{n}:{k}" for n, k in rena),
        injektioner_i_rena=len(inj_rena),
        larm_i_rena=sum(r["flaggad"] for r in inj_rena),
        larm_i_rena_yolo_bara=sum(r["flaggad_yolo_bara"] for r in inj_rena),
        per_typ={inj: dict(n=sum(1 for r in inj_rena if r["injektion"].startswith(inj)),
                           larm=sum(1 for r in inj_rena if r["injektion"].startswith(inj) and r["flaggad"]),
                           larm_yolo_bara=sum(1 for r in inj_rena if r["injektion"].startswith(inj) and r["flaggad_yolo_bara"]))
                 for inj in ("lateral", "djup", "huk", "byt")},
        argon_g7_larm=sum(1 for r in ut["injektioner"] if any(ok is False for ok in r["argon_g7_ok"])),
        injektioner_totalt=len(ut["injektioner"]),
    )
    return ut


def kor_patch() -> dict:
    """Genererar g7_scen_brygga.py (P1–P4), kompilerar om alla fyra klipp till en tillfällig mapp och mäter."""
    import subprocess
    subprocess.run([sys.executable, str(HIT / "g7_lag_patch.py")], check=True)
    sys.path.insert(0, str(HIT))
    sys.path.insert(0, str(ROT / "forvarld_karna"))
    import g7_scen_brygga
    from schema import Observationer, Recept
    ut = {}
    for namn in KLIPP:
        ut_k = ROT / "forvarld_karna/ut" / namn
        obs = Observationer.model_validate_json((ut_k / "obs.json").read_text(encoding="utf-8"))
        rec = Recept.model_validate_json((ut_k / "recept.json").read_text(encoding="utf-8"))
        orig = las_json(ut_k / "paket.json")
        with tempfile.TemporaryDirectory() as tmp:
            pf = g7_scen_brygga.kompilera_scenpaket(namn, ROT / KLIPP[namn], obs, rec, pathlib.Path(tmp) / namn)
            paket = json.loads(pf.read_text(encoding="utf-8"))
            gr = json.loads((pf.parent / "paket_grindar.json").read_text(encoding="utf-8"))
        rader = mat_paket(namn, paket, las_json(ut_k / "obs.json"))
        ut[namn] = dict(
            grindar_patch=gr["sammanfattning"],
            grindar_original_per_person=__import__("grindar").sammanfatta(grindar_per_person(orig)),
            grindrader_patch=len(gr["rader"]),
            r18_konflikter=[b for b in paket["beslut"] if b["regel"] == "R18_kamerahojd_konflikt"],
            g7=[{k: r[k] for k in ("tagning", "person", "led_med", "kedja_med", "rest_efter_kappa", "i_box", "i_mask",
                                   "iou", "spok_andel", "flaggad", "skal", "kamera_z")} for r in rader],
        )
    return ut


# ----------------------------------------------------------------------------------------------- A1: uppströmsinjektion
def a1_uppstroms(namn="guacamole", sid="s1", dx_m=0.5) -> dict:
    """Flyttar kroppen dx_m i SAM:s kameraram (cam_t_ra x) INNAN scen_brygga räknar X och X_RA_2D, kompilerar om till
    en tillfällig mapp och jämför Argons G7 (paket.trohet + grindar) med G7-oberoende. Rör inga filer i forvarld_karna/."""
    sys.path.insert(0, str(ROT / "forvarld_karna"))
    import scen_brygga
    from schema import Observationer, Recept
    ut_k = ROT / "forvarld_karna/ut" / namn
    obs = Observationer.model_validate_json((ut_k / "obs.json").read_text(encoding="utf-8"))
    rec = Recept.model_validate_json((ut_k / "recept.json").read_text(encoding="utf-8"))
    ingest = ROT / KLIPP[namn]
    mal = str((ingest / sid.upper()).resolve()).lower()
    orig_load = np.load
    resultat = {}
    for etikett, dx in (("omkompilerad_utan_injektion", 0.0), (f"cam_t_ra_x_plus_{dx_m}m", dx_m)):
        def load(p, *a, **k):
            z = orig_load(p, *a, **k)
            ps = str(pathlib.Path(p).resolve()).lower()
            if dx and ps.startswith(mal) and pathlib.Path(p).name.startswith("sekvens_"):
                d = dict(z)
                d["cam_t_ra"] = d["cam_t_ra"].copy()
                d["cam_t_ra"][:, 0] += dx
                return d
            return z
        np.load = load
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pf = scen_brygga.kompilera_scenpaket(namn, ingest, obs, rec, pathlib.Path(tmp) / namn)
                paket = json.loads(pf.read_text(encoding="utf-8"))
                gr = json.loads((pf.parent / "paket_grindar.json").read_text(encoding="utf-8"))
        finally:
            np.load = orig_load
        rader = mat_paket(namn, paket, las_json(ut_k / "obs.json"))
        resultat[etikett] = dict(
            argon_trohet=paket["trohet"],
            argon_sammanfattning=gr["sammanfattning"],
            g7_oberoende=[{k: r[k] for k in ("tagning", "person", "led_med", "i_box", "iou", "flaggad", "skal")} for r in rader],
        )
    return resultat


# ----------------------------------------------------------------------------------------------- överlägg
def bilder(namn: str, paket: dict, ut_mapp: pathlib.Path, rutor_per=3):
    import cv2
    ingest = ROT / KLIPP[namn]
    obs = las_json(ROT / "forvarld_karna/ut" / namn / "obs.json")
    W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
    L = paket["leder"]; LI = {n: i for i, n in enumerate(L)}
    BEN_PAR = [("c_spine0", "c_spine1"), ("c_spine1", "c_spine2"), ("c_spine2", "c_spine3"), ("c_spine3", "c_neck"),
               ("c_neck", "c_head"), ("c_head", "huvud_upp"), ("c_spine3", "l_clavicle"), ("l_clavicle", "l_uparm"),
               ("l_uparm", "l_lowarm"), ("l_lowarm", "l_wrist"), ("c_spine3", "r_clavicle"), ("r_clavicle", "r_uparm"),
               ("r_uparm", "r_lowarm"), ("r_lowarm", "r_wrist"), ("c_spine0", "l_upleg"), ("l_upleg", "l_lowleg"),
               ("l_lowleg", "l_foot"), ("c_spine0", "r_upleg"), ("r_upleg", "r_lowleg"), ("r_lowleg", "r_foot")]
    ut_mapp.mkdir(parents=True, exist_ok=True)
    filer = []
    for t in paket["tagningar"]:
        if not t["personer"]:
            continue
        a0, b0 = t["ut"]
        tg = Tagning(ingest, next(k for k in obs["klipp"] if k["klipp"] == t["id"]), t, L)
        cap = cv2.VideoCapture(str(ingest / "klipp" / f"{t['id'].upper()}.mp4"))
        kol = []
        for f in np.linspace(0, b0 - a0 - 1, rutor_per).astype(int):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(f))
            ok, im = cap.read()
            if not ok:
                im = np.zeros((H, W, 3), np.uint8)
            im = cv2.resize(im, (W, H))
            if tg.mask is not None and f < tg.mask.shape[0]:
                mk = cv2.resize(np.asarray(tg.mask[f]).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
                cnt, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(im, cnt, -1, (0, 140, 0), 1)
            for p in t["personer"]:
                pid = p["id"]; spar = tg.spar_for[pid]
                sp = next(x for x in paket["rorelse"][pid] if x["tagning"] == t["id"])
                r = next((rr for rr in sp["rutor"] if rr[0] == a0 + f), None)
                if r is None:
                    continue
                X = np.array(r[1:], float).reshape(-1, 3) / 1000.0
                uv, d = proj(X, *kamera_vid(t, a0 + f), W, H)
                uv_nat, ben, _ = tg.nativ_t1(spar, f, W, H)
                yb = tg.yolo(spar, f)
                if yb is not None:
                    cv2.rectangle(im, (int(yb[0]), int(yb[1])), (int(yb[2]), int(yb[3])), (0, 255, 0), 2)
                raw = tg.raw(spar, f)
                if raw is not None:
                    for k in [k for _, k in PAR_OVER + PAR_BEN] + [0]:
                        x, y = raw["kp2"][k]
                        cv2.circle(im, (int(x), int(y)), 5, (0, 255, 255), -1)
                for a, b in BEN_PAR:
                    pa, pb = uv_nat[LI[a]], uv_nat[LI[b]]
                    cv2.line(im, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), (255, 200, 0), 1)
                for a, b in BEN_PAR:
                    pa, pb = uv[LI[a]], uv[LI[b]]
                    cv2.line(im, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), (255, 0, 255), 3)
                cv2.putText(im, f"{pid} (spar {spar})", (int(uv[LI['huvud_upp']][0]) - 30, int(uv[LI['huvud_upp']][1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            cv2.putText(im, f"{namn} {t['id']} f={f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            kol.append(cv2.resize(im, (int(W * 512 / H), 512)))
        cap.release()
        fil = ut_mapp / f"g7_{namn}_{t['id']}.png"
        cv2.imwrite(str(fil), np.hstack(kol))
        filer.append(fil)
    return filer


# ----------------------------------------------------------------------------------------------- utskrift
def tabell(rader):
    print("| klipp | tagn | person | spår (sem.) | rutor SAM/YOLO/alla | led_med | led_p90 | i_box kärna (ref) | iou (ref) | i_mask (ref) | id | Argon G7 (iou) | G7-oberoende |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rader:
        a = r["argon_g7"] or {}
        print(f"| {r['klipp']} | {r['tagning']} | {r['person']} | {r['spar']} ({r['semantik_roll'] or '–'}) | "
              f"{r['rutor_sam']}/{r['rutor_yolo']}/{r['rutor']} | {r['led_med']} | {r['led_p90']} | {r['i_box']} ({r['i_box_ref']}) | "
              f"{r['iou']} ({r['iou_ref']}) | {r['i_mask']} ({r['i_mask_ref']}) | {r['id_basta']} | "
              f"{'ok' if a and not a.get('flaggad') else 'FEL'} ({a.get('iou')}) | {'**FEL** ' + '; '.join(r['skal']) if r['flaggad'] else 'ok'} |")
    print()
    print("| klipp | tagn | person | kedja_med | bålskift mätt | kappa-förutsagt | rest efter kappa (vertikal) | kamera z | i_box överkropp (ref) | rutor utan obs / spök |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rader:
        print(f"| {r['klipp']} | {r['tagning']} | {r['person']} | {r['kedja_med']} | {r['bal_skift_mat']} | {r['bal_skift_kappa']} | "
              f"{r['rest_efter_kappa']} ({r['rest_vertikal']:+.4f}) | {r['kamera_z']} | {r['i_box_overkropp']} ({r['i_box_overkropp_ref']}) | "
              f"{r['rutor_utan_obs']} / {r['spok_rutor']} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--klipp", default="alla", choices=["alla"] + list(KLIPP))
    ap.add_argument("--kalibrera", action="store_true")
    ap.add_argument("--a1", action="store_true")
    ap.add_argument("--bilder", action="store_true")
    ap.add_argument("--patch", action="store_true", help="kompilera om med g7_scen_brygga.py (P1–P4) och mät")
    a = ap.parse_args()
    namnen = list(KLIPP) if a.klipp == "alla" else [a.klipp]
    if a.patch:
        res = kor_patch()
        (HIT / "g7_patch.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        for namn, v in res.items():
            print(f"## {namn}: grindar (patch, en rad per person) = {v['grindar_patch']}")
            print(f"   grindar (original, en rad per person)         = {v['grindar_original_per_person']}")
            print(f"   R18-konflikter: {[(b['tagning'], b['kamera_z']) for b in v['r18_konflikter']]}")
            for r in v["g7"]:
                print(f"   {r['tagning']}:{r['person']} led_med={r['led_med']} kedja={r['kedja_med']} rest={r['rest_efter_kappa']} "
                      f"i_box={r['i_box']} i_mask={r['i_mask']} spök={r['spok_andel']} kam_z={r['kamera_z']} "
                      f"{'FEL ' + '; '.join(r['skal']) if r['flaggad'] else 'ok'}")
        return
    if a.a1:
        res = a1_uppstroms()
        (HIT / "g7_a1.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        for k, v in res.items():
            print(f"## {k}\n  Argons trohet s1:A = {v['argon_trohet'].get('s1:A')}\n  Argons grindsammanfattning = {v['argon_sammanfattning']}")
            for r in v["g7_oberoende"]:
                print(f"  G7-oberoende {r['tagning']}:{r['person']}: led_med={r['led_med']} i_box={r['i_box']} iou={r['iou']} flaggad={r['flaggad']} {r['skal']}")
        return
    if a.kalibrera:
        res = kalibrera()
        (HIT / "g7_kalibrering.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print("| klipp | tagn | person | injektion | led_med (orig) | i_box (orig) | i_mask (orig) | G7-oberoende | varav YOLO-bara | Argons G7 ok |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for r in res["injektioner"]:
            print(f"| {r['klipp']} | {r['tagning']} | {r['person']} | {r['injektion']} | {r['led_med']} ({r['original_led_med']}) | "
                  f"{r['i_box']} ({r['original_i_box']}) | {r['i_mask']} ({r['original_i_mask']}) | "
                  f"{'LARM' if r['flaggad'] else 'tyst'}{' (orig. redan larm)' if r['original_flaggad'] else ''} | "
                  f"{'LARM' if r['flaggad_yolo_bara'] else 'tyst'} | {r['argon_g7_ok']} |")
        print("\nTröskelsvep G7a (led_med) på original utan larm och deras injektioner:")
        for s in res["svep_G7a"]:
            print("  ", s)
        print("\nSammanfattning:", json.dumps(res["sammanfattning"], ensure_ascii=False, indent=1))
        return
    alla = []
    for namn in namnen:
        paket = las_json(ROT / "forvarld_karna/ut" / namn / "paket.json")
        alla += mat_paket(namn, paket)
        if a.bilder:
            for fil in bilder(namn, paket, HIT / "g7_bilder"):
                print("bild:", fil)
    (HIT / "g7_resultat.json").write_text(json.dumps(dict(granser=GRANS, rader=alla), ensure_ascii=False, indent=1), encoding="utf-8")
    tabell(alla)


if __name__ == "__main__":
    main()
