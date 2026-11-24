# -*- coding: utf-8 -*-
"""2D-trohet (mått b): systemets 2D-leder mot en OBEROENDE 2D-detektion i originalrutorna.

Oberoende källa: MediaPipe PoseLandmarker (BlazePose, `scen/py/modeller/pose_landmarker_full.task`).
Den används inte i forvarld_karna eller dess ingest (där promptas SAM 3D Body med YOLO-rutor, se
runda 2 `metod_yolo_oberoende.py`). Den jämförs därför mot pixlarna i videon, inte mot projektionen
av systemets egna 3D-punkter.

Indata (systemets påstående), generiskt format:
  {"video": "sökväg.mp4", "bild": [W, H],            # koordinatsystemet för lederna nedan
   "rutor": [{"ruta": <bildindex i videon>,
              "personer": [{"id": "A", "leder": {"v_axel": [x, y], "h_armbage": [x, y], ...}}]}]}
Lednamn: huvud, v_axel, h_axel, v_armbage, h_armbage, v_handled, h_handled, v_hoft, h_hoft,
         v_kna, h_kna, v_fotled, h_fotled   (v = personens vänster).
Led som systemet anser skymd kan utelämnas.

Mått per (person, ruta): median över gemensamma leder av |system - detektion| / bålmått, där
bålmåttet tas ur DETEKTIONEN (axelmitt till höftmitt, annars 2 x axelbredd). Personer paras
per ruta med ungersk tilldelning. Per person: median över rutor och andel rutor över gränsen.

Gräns: ingen ägargräns finns. Standardgränsen 0,30 bål är satt ur brusgolvet mellan två
oberoende detektorer (YOLO11n-pose mot MediaPipe) på klipp som INTE är hold-out; se
--kalibrera. Den är diagnos, inte krav.

Körning:
  python trohet2d.py --pastaende sys2d.json [--logg ut.json] [--grans 0.30]
  python trohet2d.py --kalibrera video1.mp4 [video2.mp4 ...]   # brusgolv + felinjektion
  python trohet2d.py --adapter-paket paket.json --ingest <ingestmapp> --video klipp.mp4 --ut sys2d.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROT = Path(__file__).resolve().parents[4]
MODELL = ROT / "scen/py/modeller/pose_landmarker_full.task"
CACHE = Path(__file__).resolve().parent / "cache"
LEDER = ["huvud", "v_axel", "h_axel", "v_armbage", "h_armbage", "v_handled", "h_handled",
         "v_hoft", "h_hoft", "v_kna", "h_kna", "v_fotled", "h_fotled"]
MP_IX = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]       # MediaPipe BlazePose 33
COCO_IX = [0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]           # YOLO-pose (COCO-17)
GRANS = 0.30


# ------------------------------------------------------------------ oberoende detektion (MediaPipe)
class Detektor:
    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks import python as mpp
        from mediapipe.tasks.python import vision
        opt = vision.PoseLandmarkerOptions(
            base_options=mpp.BaseOptions(model_asset_path=str(MODELL)),
            running_mode=vision.RunningMode.IMAGE, num_poses=4,
            min_pose_detection_confidence=0.4, min_pose_presence_confidence=0.4)
        self.lm = vision.PoseLandmarker.create_from_options(opt)
        self.mp = mp

    def __call__(self, bgr) -> list[np.ndarray]:
        h, w = bgr.shape[:2]
        img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        res = self.lm.detect(img)
        ut = []
        for pose in res.pose_landmarks:
            a = np.array([[p.x * w, p.y * h, getattr(p, "visibility", 1.0) or 0.0] for p in pose])
            ut.append(a[MP_IX])
        return ut


def las_rutor(video: str, index: list[int]) -> dict[int, np.ndarray]:
    cap = cv2.VideoCapture(str(video))
    ut, want = {}, sorted(set(index))
    i, j = 0, 0
    while j < len(want):
        ok, fr = cap.read()
        if not ok:
            break
        if i == want[j]:
            ut[i] = fr
            j += 1
        i += 1
    cap.release()
    return ut


def detektera(video: str, index: list[int]) -> dict[int, list[np.ndarray]]:
    CACHE.mkdir(exist_ok=True)
    nyckel = CACHE / (Path(video).stem + ".mp_pose.json")
    cache = json.loads(nyckel.read_text()) if nyckel.exists() else {}
    saknas = [i for i in index if str(i) not in cache]
    if saknas:
        det = Detektor()
        for i, fr in las_rutor(video, saknas).items():
            cache[str(i)] = [p.tolist() for p in det(fr)]
        nyckel.write_text(json.dumps(cache))
    return {i: [np.array(p) for p in cache.get(str(i), [])] for i in index}


# ------------------------------------------------------------------ mått
def balmatt(d: np.ndarray) -> float | None:
    v = d[:, 2] > 0.5
    L = {n: d[k] for k, n in enumerate(LEDER)}
    if v[1] and v[2] and v[7] and v[8]:
        return float(np.linalg.norm((L["v_axel"][:2] + L["h_axel"][:2]) / 2 - (L["v_hoft"][:2] + L["h_hoft"][:2]) / 2))
    if v[1] and v[2]:
        return 2.0 * float(np.linalg.norm(L["v_axel"][:2] - L["h_axel"][:2]))
    return None


GRUPPER = {"huvud_axlar": ["huvud", "v_axel", "h_axel"],
           "armar": ["v_armbage", "h_armbage", "v_handled", "h_handled"],
           "hofter": ["v_hoft", "h_hoft"],
           "ben": ["v_kna", "h_kna", "v_fotled", "h_fotled"]}
# Gränser per komponent (diagnos, inte ägarkrav). Satta ur brusgolvet YOLO11n-pose mot MediaPipe på
# fem klipp som INTE är hold-out (se trohet2d_kalibrering.json). Regel: minst 1,3 x största rena värdet.
# Huvud/axlar, armar och ben är satta generösare än regeln (systemets leddefinition skiljer sig mer än två
# 2D-detektorers). Höfterna har högt brusgolv (COCO- och BlazePose-höfter är olika definierade), så
# höftgruppen är svag. Videogränsen för skala följer regeln exakt (1,3 x 0,068 = 0,09), och marginalen
# mot kappa-injektionen är liten (minsta injicerade |ln| = 0,095). Se RAPPORT.md.
GRUPP_GRANS = {"huvud_axlar": 0.30, "armar": 0.60, "hofter": 0.85, "ben": 0.60}
SKALA_GRANS_PERSON = 0.25   # |ln(spridning system/detektion)| per person: grova storleksfel
SKALA_GRANS_VIDEO = 0.09    # median över personer i videon: systematiskt storleksfel (t.ex. fel brännvidd)
SKALA_UTAN = {"v_hoft", "h_hoft"}   # höfterna ingår inte i spridningen (definitionsskillnad)
MIN_RUTOR_GRUPP = 3


def fel(sysled: dict, d: np.ndarray, W: int, H: int):
    """Fel för en (person, ruta) i bålmått ur DETEKTIONEN:
      alla    = median över alla gemensamma synliga leder (används för parning),
      grupper = median per ledgrupp med >= 2 gemensamma leder (fångar fel i bara benen),
      lnskala = ln(spridning kring tyngdpunkt, system / detektion) över gemensamma leder
                (fångar fel storlek, t.ex. fel brännvidd, som en medianavvikelse inte ser)."""
    s = balmatt(d)
    if not s or s < 5:
        return None
    e, ps, pd = {}, [], []
    for k, n in enumerate(LEDER):
        if n in sysled and d[k, 2] > 0.5 and 0 <= d[k, 0] < W and 0 <= d[k, 1] < H:
            a = np.asarray(sysled[n], float)
            e[n] = float(np.linalg.norm(a - d[k, :2]) / s)
            if n not in SKALA_UTAN:
                ps.append(a); pd.append(d[k, :2])
    if len(e) < 3:
        return None
    g = {gn: float(np.median([e[n] for n in ln if n in e])) for gn, ln in GRUPPER.items()
         if sum(n in e for n in ln) >= 2}
    ps, pd = np.array(ps), np.array(pd)
    rs = float(np.sqrt(((ps - ps.mean(0)) ** 2).sum(1).mean()))
    rd = float(np.sqrt(((pd - pd.mean(0)) ** 2).sum(1).mean()))
    lns = float(np.log(rs / rd)) if (rd > 1 and rs > 1 and len(ps) >= 4) else None
    return {"alla": float(np.median(list(e.values()))), "grupper": g, "lnskala": lns}


def _sammanfatta(st: dict, grans: float) -> dict:
    f = np.array([x["alla"] for x in st["fel"]])
    med = float(np.median(f)) if f.size else None
    grp = {}
    for gn in GRUPPER:
        v = [x["grupper"][gn] for x in st["fel"] if gn in x["grupper"]]
        if len(v) >= MIN_RUTOR_GRUPP:
            grp[gn] = round(float(np.median(v)), 3)
    ls = [x["lnskala"] for x in st["fel"] if x["lnskala"] is not None]
    lns = round(float(np.median(ls)), 3) if len(ls) >= MIN_RUTOR_GRUPP else None
    orsak = []
    if med is not None and med > grans:
        orsak.append("alla")
    orsak += [f"grupp:{gn}" for gn, v in grp.items() if v > GRUPP_GRANS[gn]]
    if lns is not None and abs(lns) > SKALA_GRANS_PERSON:
        orsak.append("skala")
    if st["ej_parad"] > 0.5 * st["rutor"]:
        orsak.append("ej_parad")
    return {"rutor": st["rutor"], "parade": int(f.size), "ej_parade": st["ej_parad"],
            "median_fel_bal": None if med is None else round(med, 3),
            "andel_rutor_over_grans": None if med is None else round(float((f > grans).mean()), 3),
            "grupp_median_bal": grp, "ln_skala_median": lns,
            "flagga": bool(orsak), "orsak": orsak}


def mat(pas: dict, grans: float = GRANS, det: dict | None = None) -> dict:
    from scipy.optimize import linear_sum_assignment
    W0, H0 = pas["bild"]
    cap = cv2.VideoCapture(str(pas["video"]))
    W, H = int(cap.get(3)), int(cap.get(4))
    cap.release()
    sx, sy = W / W0, H / H0
    index = [r["ruta"] for r in pas["rutor"]]
    det = det if det is not None else detektera(pas["video"], index)
    per = {}
    for r in pas["rutor"]:
        ds = det.get(r["ruta"], [])
        pers = [{"id": p["id"], "leder": {k: [v[0] * sx, v[1] * sy] for k, v in p["leder"].items()}}
                for p in r["personer"]]
        if not pers:
            continue
        C = np.full((len(pers), max(len(ds), 1)), 9.0)
        F = {}
        for i, p in enumerate(pers):
            for j, d in enumerate(ds):
                e = fel(p["leder"], d, W, H)
                if e is not None:
                    C[i, j] = e["alla"]; F[(i, j)] = e
        rad, kol = linear_sum_assignment(C)
        tilldelad = {i: j for i, j in zip(rad, kol) if C[i, j] < 9.0}
        for i, p in enumerate(pers):
            st = per.setdefault(p["id"], {"fel": [], "ej_parad": 0, "rutor": 0})
            st["rutor"] += 1
            if i in tilldelad:
                st["fel"].append(F[(i, tilldelad[i])])
            else:
                st["ej_parad"] += 1
    ut = {pid: _sammanfatta(st, grans) for pid, st in per.items()}
    ls = [v["ln_skala_median"] for v in ut.values() if v["ln_skala_median"] is not None and v["parade"] >= 5]
    video_ln = round(float(np.median(ls)), 3) if ls else None
    video_larm = video_ln is not None and abs(video_ln) > SKALA_GRANS_VIDEO
    return {"matt": "2D-trohet mot MediaPipe (oberoende)", "grans_bal": grans,
            "grupp_grans_bal": GRUPP_GRANS, "skala_grans_ln": {"person": SKALA_GRANS_PERSON, "video": SKALA_GRANS_VIDEO},
            "personer": ut, "video_ln_skala": video_ln, "video_skala_larm": video_larm,
            "utfall": "larm" if (any(v["flagga"] for v in ut.values()) or video_larm) else "inom"}


# ------------------------------------------------------------------ kalibrering och felinjektion
def yolo_som_system(video: str, index: list[int]) -> dict:
    from ultralytics import YOLO
    m = YOLO(str(ROT / "scen/py/modeller/yolo11n-pose.pt"))
    rut = las_rutor(video, index)
    H, W = next(iter(rut.values())).shape[:2]
    rutor = []
    for i, fr in rut.items():
        r = m.predict(fr, verbose=False, conf=0.4)[0]
        pers = []
        if r.keypoints is not None and len(r.keypoints):
            kp = r.keypoints.data.cpu().numpy()
            for j, k in enumerate(kp):
                led = {n: [float(k[c, 0]), float(k[c, 1])] for n, c in zip(LEDER, COCO_IX) if k[c, 2] > 0.5}
                if len(led) >= 4:
                    pers.append({"id": f"y{j}", "leder": led})
        rutor.append({"ruta": i, "personer": pers})
    return {"video": video, "bild": [W, H], "rutor": rutor}


def _stabila_id(pas: dict) -> dict:
    """Ge YOLO-personerna stabila id per video genom närmaste-granne över rutor (bara för kalibrering)."""
    forra = {}
    nasta_id = 0
    for r in pas["rutor"]:
        ny = {}
        for p in r["personer"]:
            c = np.mean([v for v in p["leder"].values()], axis=0)
            best, bd = None, 1e9
            for pid, c0 in forra.items():
                d = np.linalg.norm(c - c0)
                if d < bd and pid not in ny:
                    best, bd = pid, d
            if best is None or bd > 150:
                best = f"P{nasta_id}"; nasta_id += 1
            p["id"] = best
            ny[best] = c
        forra = ny or forra
    return pas


def injicera(pas: dict, typ: str) -> dict:
    import copy
    W, H = pas["bild"]
    p2 = copy.deepcopy(pas)
    for r in p2["rutor"]:
        for p in r["personer"]:
            L = p["leder"]
            pts = np.array(list(L.values()))
            if typ == "sidled_0.5bal":
                ax = [v for k, v in L.items() if "axel" in k]; hf = [v for k, v in L.items() if "hoft" in k]
                s = np.linalg.norm(np.mean(ax, 0) - np.mean(hf, 0)) if ax and hf else 0.15 * H
                for k in L:
                    L[k] = [L[k][0] + 0.5 * s, L[k][1]]
            elif typ == "kappa_0.85":
                for k in L:
                    L[k] = [W / 2 + 0.85 * (L[k][0] - W / 2), H / 2 + 0.85 * (L[k][1] - H / 2)]
            elif typ == "huk_ben":
                c = pts.mean(0)
                for k in L:
                    if any(t in k for t in ("kna", "fotled", "hoft")):
                        L[k] = [L[k][0], c[1] + 0.35 * (L[k][1] - c[1])]
            elif typ == "byt_vanster_hoger":
                nyL = {}
                for k, v in L.items():
                    k2 = k.replace("v_", "X_").replace("h_", "v_").replace("X_", "h_") if k[:2] in ("v_", "h_") else k
                    nyL[k2] = v
                p["leder"] = nyL
    return p2


def _yolo_cachad(video: str, idx: list[int]) -> dict:
    CACHE.mkdir(exist_ok=True)
    p = CACHE / (Path(video).stem + ".yolo_pose.json")
    if p.exists():
        c = json.loads(p.read_text(encoding="utf-8"))
        if c.get("index") == idx:
            return c["pas"]
    pas = yolo_som_system(video, idx)
    p.write_text(json.dumps({"index": idx, "pas": pas}), encoding="utf-8")
    return pas


INJ = ("sidled_0.5bal", "kappa_0.85", "huk_ben", "byt_vanster_hoger")


def kalibrera(videor: list[str], n_rutor: int = 40) -> dict:
    """Brusgolv (två oberoende detektorer på samma pixlar) och felinjektion per komponent.
    Bara personer med >= 5 parade rutor räknas."""
    ut = {"videor": [], "obs": "System = YOLO11n-pose (oberoende av MediaPipe). Rent = brusgolv; inj = felinjektion. "
                              "Klippen är inte hold-out."}
    rena = []
    larm = {t: [0, 0] for t in INJ}
    orsaker = {t: {} for t in INJ}
    huk_obs = [0, 0]
    for v in videor:
        cap = cv2.VideoCapture(v); N = int(cap.get(7)); cap.release()
        idx = sorted(set(np.linspace(0, N - 1, n_rutor).astype(int).tolist()))
        pas = _stabila_id(_yolo_cachad(v, idx))
        det = detektera(v, idx)
        ren = mat(pas, det=det)
        ok = {k: x for k, x in ren["personer"].items() if x["parade"] >= 5}
        rena += list(ok.values())
        # videoutfall räknas bara på personer med >= 5 parade rutor (YOLO-fragment är kalibreringsartefakter)
        rad = {"video": v, "ren": ok, "ren_video_ln": ren["video_ln_skala"],
               "ren_utfall": "larm" if (any(x["flagga"] for x in ok.values()) or ren["video_skala_larm"]) else "inom"}
        for t in INJ:
            r = mat(injicera(pas, t), det=det)
            pp = {k: x for k, x in r["personer"].items() if k in ok}
            larm[t][0] += sum(1 for x in pp.values() if x["flagga"])
            larm[t][1] += len(pp)
            for x in pp.values():
                for o in x["orsak"]:
                    orsaker[t][o] = orsaker[t].get(o, 0) + 1
            rad[t + "_utfall"] = "larm" if (any(x["flagga"] for x in pp.values()) or r["video_skala_larm"]) else "inom"
            rad[t + "_video_ln"] = r["video_ln_skala"]
            if t == "huk_ben":
                for k, x in pp.items():
                    if "ben" in ok[k]["grupp_median_bal"]:
                        huk_obs[1] += 1; huk_obs[0] += int(x["flagga"])
            rad[t] = {k: {"median_fel_bal": x["median_fel_bal"], "grupp": x["grupp_median_bal"],
                          "ln_skala": x["ln_skala_median"], "orsak": x["orsak"]} for k, x in pp.items()}
        ut["videor"].append(rad)

    def fordelning(vals):
        vals = [x for x in vals if x is not None]
        if not vals:
            return None
        return {"n": len(vals), "p50": round(float(np.median(vals)), 3),
                "p95": round(float(np.percentile(vals, 95)), 3), "max": round(float(np.max(vals)), 3)}
    ut["brusgolv"] = {
        "alla_median_fel_bal": fordelning([x["median_fel_bal"] for x in rena]),
        "grupper": {gn: fordelning([x["grupp_median_bal"].get(gn) for x in rena]) for gn in GRUPPER},
        "abs_ln_skala": fordelning([abs(x["ln_skala_median"]) for x in rena if x["ln_skala_median"] is not None]),
    }
    ut["granser"] = {"alla": GRANS, "grupper": GRUPP_GRANS, "abs_ln_skala_person": SKALA_GRANS_PERSON,
                     "abs_ln_skala_video": SKALA_GRANS_VIDEO}
    ut["video_ln_skala_rena"] = [v["ren_video_ln"] for v in ut["videor"]]
    ut["videolarm_rena"] = f"{sum(1 for v in ut['videor'] if v['ren_utfall'] == 'larm')}/{len(ut['videor'])}"
    ut["videolarm_per_injektion"] = {t: f"{sum(1 for v in ut['videor'] if v[t + '_utfall'] == 'larm')}/{len(ut['videor'])}"
                                     for t in INJ}
    ut["huk_ben_observerbar"] = f"{huk_obs[0]}/{huk_obs[1]} personer med synliga ben larmar (övriga har inga ben i bild att jämföra)"
    ut["falsklarm_rena"] = f"{sum(1 for x in rena if x['flagga'])}/{len(rena)}"
    ut["falsklarm_orsaker"] = [x["orsak"] for x in rena if x["flagga"]]
    ut["larm_per_injektion"] = {t: f"{a}/{b}" for t, (a, b) in larm.items()}
    ut["larm_orsaker_per_injektion"] = orsaker
    return ut


# ------------------------------------------------------------------ adapter: forvarld_karna scenpaket/2
def adapter_paket(paket_p: str, video: str, ut_p: str, start: int = 0):
    """Projicerar paketets T1-leder genom paketets egen kamera (som emit_bpy) till sys2d-formatet.
    `start` = videons bildindex för paketets ruta u=0 (tagningsstarten ligger redan i u)."""
    sys.path.insert(0, str(ROT / "motpart/runda-1-claude"))
    import g7_oberoende as G
    paket = json.loads(Path(paket_p).read_text(encoding="utf-8"))
    W, H = paket["bild"]["bredd"], paket["bild"]["hojd"]
    LI = {n: i for i, n in enumerate(paket["leder"])}
    namn = {"huvud": "c_head", "v_axel": "l_uparm", "h_axel": "r_uparm", "v_armbage": "l_lowarm",
            "h_armbage": "r_lowarm", "v_handled": "l_wrist", "h_handled": "r_wrist", "v_hoft": "l_upleg",
            "h_hoft": "r_upleg", "v_kna": "l_lowleg", "h_kna": "r_lowleg", "v_fotled": "l_foot", "h_fotled": "r_foot"}
    rutor = {}
    for t in paket["tagningar"]:
        for p in t["personer"]:
            sp = next(x for x in paket["rorelse"][p["id"]] if x["tagning"] == t["id"])
            for r in sp["rutor"]:
                u = r[0]
                X = np.array(r[1:], float).reshape(-1, 3) / 1000.0
                C, R, lins = G.kamera_vid(t, u)
                uv, d = G.proj(X, C, R, lins, W, H)
                led = {k: uv[LI[v]].tolist() for k, v in namn.items() if v in LI and d[LI[v]] > 0}
                rutor.setdefault(start + u, []).append({"id": p["id"], "leder": led})
    out = {"video": video, "bild": [W, H], "rutor": [{"ruta": k, "personer": v} for k, v in sorted(rutor.items())]}
    Path(ut_p).write_text(json.dumps(out), encoding="utf-8")
    print(f"skrev {ut_p}: {len(out['rutor'])} rutor")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pastaende")
    ap.add_argument("--grans", type=float, default=GRANS)
    ap.add_argument("--logg")
    ap.add_argument("--kalibrera", nargs="+")
    ap.add_argument("--adapter-paket"); ap.add_argument("--video"); ap.add_argument("--ut")
    ap.add_argument("--start", type=int, default=0)
    a = ap.parse_args()
    if a.adapter_paket:
        adapter_paket(a.adapter_paket, a.video, a.ut, a.start)
        return
    if a.kalibrera:
        r = kalibrera(a.kalibrera)
        p = Path(__file__).with_name("trohet2d_kalibrering.json")
        p.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({k: v for k, v in r.items() if k != "videor"}, ensure_ascii=False, indent=1))
        return
    pas = json.loads(Path(a.pastaende).read_text(encoding="utf-8"))
    r = mat(pas, a.grans)
    txt = json.dumps(r, ensure_ascii=False, indent=1)
    if a.logg:
        Path(a.logg).write_text(txt, encoding="utf-8")
    print(txt)
    sys.exit(0 if r["utfall"] == "inom" else 3)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
