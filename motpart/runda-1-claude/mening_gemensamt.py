"""Gemensamma hjälpfunktioner för Claudes runda 1 (lane A2 + A4 + Lager 4).

Läser bara från forvarld_karna/ och scen/3d/ingest/ut/ – skriver aldrig dit.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
KARNA = ROT / "forvarld_karna"
UT = HIT / "mening_ut"
UT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(KARNA))
sys.path.insert(0, str(ROT / "byggsten/brygga"))

import grindar  # noqa: E402
from rotation import quat_till_mat  # noqa: E402

KLIPP = ["guacamole", "gelato", "asketch", "notan"]
BORD_TYP = ("bord",)


def las_paket(klipp: str, manip: str | None = None) -> dict:
    f = KARNA / "ut" / klipp / (f"manip_{manip}" if manip else "") / "paket.json"
    return json.loads(f.read_text(encoding="utf-8"))


def las_obs(klipp: str) -> dict:
    return json.loads((KARNA / "ut" / klipp / "obs.json").read_text(encoding="utf-8"))


def ingest(paket: dict) -> pathlib.Path:
    return pathlib.Path(paket["klipp"]["video"])


def X_av(spar: dict) -> tuple[list[int], np.ndarray]:
    R = spar["rutor"]
    U = [r[0] for r in R]
    X = np.array([r[1:] for r in R], dtype=float).reshape(len(R), -1, 3) / 1000.0
    return U, X


def ix(paket: dict) -> dict[str, int]:
    return {n: i for i, n in enumerate(paket["leder"])}


def spar_for(paket: dict, pid: str, sid: str) -> dict | None:
    return next((s for s in paket["rorelse"].get(pid, []) if s["tagning"] == sid), None)


def tagning(paket: dict, sid: str) -> dict:
    return next(t for t in paket["tagningar"] if t["id"] == sid)


def kamera(paket: dict, sid: str, u: int):
    return grindar.kamera(tagning(paket, sid), u)


def proj(paket: dict, x: np.ndarray, kam) -> tuple[np.ndarray, np.ndarray]:
    W, H, S = paket["bild"]["bredd"], paket["bild"]["hojd"], paket["bild"]["sensor_mm"]
    return grindar.proj(x, kam, W, H, S)


def spar_id_for_person(paket: dict, sid: str, pid: str) -> str | None:
    """Samma koppling som scen_brygga.kompilera_scenpaket: personordning i tagningen ↔ spår sorterade på längd."""
    S_dir = ingest(paket) / sid.upper()
    p_fil = S_dir / "personer.json"
    if not p_fil.exists():
        return None
    sp_map = json.loads(p_fil.read_text(encoding="utf-8"))
    spar_lista = sorted(sp_map, key=lambda s: -len(sp_map[s]))
    t = tagning(paket, sid)
    ordning = [p["id"] for p in t["personer"]]
    if pid not in ordning:
        return None
    i = ordning.index(pid)
    return spar_lista[i] if i < len(spar_lista) else None


def detektorrutor(paket: dict, sid: str, spar_id: str) -> dict[int, np.ndarray]:
    """Oberoende 2D-evidens: personrutor från ingestens tracker (lokala rutindex i tagningen)."""
    f = ingest(paket) / sid.upper() / "personer.json"
    sp = json.loads(f.read_text(encoding="utf-8")).get(spar_id, {})
    return {int(k): np.array(v, dtype=float) for k, v in sp.items()}


def masker(paket: dict, sid: str) -> np.ndarray | None:
    f = ingest(paket) / sid.upper() / "masker.npy"
    return np.load(f, mmap_mode="r") if f.exists() else None


def kand(paket: dict, sid: str, spar_id: str) -> np.ndarray | None:
    f = ingest(paket) / sid.upper() / f"sekvens_{spar_id}.npz"
    return np.load(f)["kand"] if f.exists() else None


def bildruta(paket: dict, sid: str, lokal_f: int):
    import cv2
    v = ingest(paket) / "klipp" / f"{sid.upper()}.mp4"
    cap = cv2.VideoCapture(str(v))
    cap.set(cv2.CAP_PROP_POS_FRAMES, lokal_f)
    ok, fr = cap.read()
    cap.release()
    return fr if ok else None


def alla_bildrutor(paket: dict, sid: str):
    import cv2
    v = ingest(paket) / "klipp" / f"{sid.upper()}.mp4"
    cap = cv2.VideoCapture(str(v))
    ut = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        ut.append(fr)
    cap.release()
    return ut


def iou(a, b) -> float:
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    i = w * h
    ua = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1]) + max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1]) - i
    return i / ua if ua > 0 else 0.0


def klipp_box(b, W, H):
    return np.array([np.clip(b[0], 0, W), np.clip(b[1], 0, H), np.clip(b[2], 0, W), np.clip(b[3], 0, H)])


def vinkel(a, b, c) -> np.ndarray:
    """Vinkel vid b (grader) mellan b->a och b->c, radvis."""
    v1 = a - b
    v2 = c - b
    cos = (v1 * v2).sum(-1) / (np.linalg.norm(v1, axis=-1) * np.linalg.norm(v2, axis=-1) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def spara_json(namn: str, data) -> pathlib.Path:
    f = UT / namn
    f.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)),
                 encoding="utf-8")
    return f


def rx(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def ry(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def rz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def euler_xyz(rx_deg, ry_deg, rz_deg):
    """Samma konvention som scen_brygga._euler_xyz_till_mat (Rz @ Ry @ Rx)."""
    return rz(rz_deg) @ ry(ry_deg) @ rx(rx_deg)
