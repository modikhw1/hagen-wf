"""Rena 3D-kinematik-, geometri- och frustumfunktioner i float-meter (mm endast vid scenpaket-I/O)."""
from __future__ import annotations

import math
from typing import Any

import numpy as np

BEN1_LEDER: list[str] = [
    "c_spine0", "c_spine1", "c_spine2", "c_spine3", "c_neck", "c_head",
    "huvud_upp", "nasa_mal",
    "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
    "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    "l_upleg", "l_lowleg", "l_foot", "l_ball",
    "r_upleg", "r_lowleg", "r_foot", "r_ball",
]

# Topologiskt ordnade kanter för överkropp (rot = c_spine0)
OVERKROPP_KANTER: list[tuple[str, str]] = [
    ("c_spine0", "c_spine1"),
    ("c_spine1", "c_spine2"),
    ("c_spine2", "c_spine3"),
    ("c_spine3", "c_neck"),
    ("c_neck", "c_head"),
    ("c_head", "huvud_upp"),
    ("c_head", "nasa_mal"),
    ("c_spine3", "l_clavicle"),
    ("l_clavicle", "l_uparm"),
    ("l_uparm", "l_lowarm"),
    ("l_lowarm", "l_wrist"),
    ("l_wrist", "l_hand_mitt"),
    ("l_wrist", "l_index1"),
    ("c_spine3", "r_clavicle"),
    ("r_clavicle", "r_uparm"),
    ("r_uparm", "r_lowarm"),
    ("r_lowarm", "r_wrist"),
    ("r_wrist", "r_hand_mitt"),
    ("r_wrist", "r_index1"),
]

UNDERKROPP_KANTER: list[tuple[str, str]] = [
    ("c_spine0", "l_upleg"),
    ("l_upleg", "l_lowleg"),
    ("l_lowleg", "l_foot"),
    ("l_foot", "l_ball"),
    ("c_spine0", "r_upleg"),
    ("r_upleg", "r_lowleg"),
    ("r_lowleg", "r_foot"),
    ("r_foot", "r_ball"),
]

ALLA_KANTER: list[tuple[str, str]] = OVERKROPP_KANTER + UNDERKROPP_KANTER

RYGG_VIKTER: tuple[tuple[str, float], ...] = (
    ("c_spine0", 0.15),
    ("c_spine1", 0.25),
    ("c_spine2", 0.30),
    ("c_spine3", 0.30),
)

SPINE_DESC: dict[str, list[str]] = {
    "c_spine0": [
        "c_spine1", "c_spine2", "c_spine3", "c_neck", "c_head", "huvud_upp", "nasa_mal",
        "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
        "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    ],
    "c_spine1": [
        "c_spine2", "c_spine3", "c_neck", "c_head", "huvud_upp", "nasa_mal",
        "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
        "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    ],
    "c_spine2": [
        "c_spine3", "c_neck", "c_head", "huvud_upp", "nasa_mal",
        "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
        "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    ],
    "c_spine3": [
        "c_neck", "c_head", "huvud_upp", "nasa_mal",
        "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
        "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
    ],
    "c_neck": ["c_head", "huvud_upp", "nasa_mal"],
    "c_head": ["huvud_upp", "nasa_mal"],
}

ARM_KEDJOR: dict[str, list[str]] = {
    "l": ["l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1"],
    "r": ["r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1"],
}

HINDER_TYPER = {"bord", "disk", "bank", "spis"}
ALLA_SOLIDA_TYPER = {
    "bord", "disk", "bank", "spis", "kaffemaskin", "kyl", "hylla",
    "mat_tallrik", "mat_skal", "mat_bricka",
}

MATSHOT_PALETTER: dict[str, list[str]] = {
    "tallrik": ["#d95338", "#f2c14e", "#4f9452"],
    "skal": ["#d96c32", "#f4d378", "#3e8c54"],
    "bricka": ["#c87b42", "#e9be69", "#56944e"],
}


def led_index(scen: dict[str, Any] | None = None) -> dict[str, int]:
    leder = (scen or {}).get("leder") or BEN1_LEDER
    return {str(n): i for i, n in enumerate(leder)}


def normalisera_hand_sida(hand: str | None) -> str:
    """Normaliserar handsida strikt till 'l' eller 'r'; kastar ValueError vid ogiltigt värde."""
    h = (hand or "vanster").strip().lower().replace("ä", "a").replace("ö", "o")
    if h in ("vanster", "v", "l", "left", "left_hand", "lefthand"):
        return "l"
    if h in ("hoger", "h", "r", "right", "right_hand", "righthand"):
        return "r"
    raise ValueError(f"Ogiltig handsida '{hand}': måste vara 'vanster' eller 'hoger' (aldrig spegling).")


def mat_from_wxyz(q: list[float] | np.ndarray) -> np.ndarray:
    w, x, y, z = [float(v) for v in q]
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def wxyz_from_mat(R: np.ndarray) -> list[float]:
    tr = float(R[0, 0] + R[1, 1] + R[2, 2])
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = float(R[2, 1] - R[1, 2]) / s
        y = float(R[0, 2] - R[2, 0]) / s
        z = float(R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(max(1e-12, 1.0 + float(R[0, 0] - R[1, 1] - R[2, 2]))) * 2.0
        w = float(R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = float(R[0, 1] + R[1, 0]) / s
        z = float(R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(max(1e-12, 1.0 + float(R[1, 1] - R[0, 0] - R[2, 2]))) * 2.0
        w = float(R[0, 2] - R[2, 0]) / s
        x = float(R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = float(R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(max(1e-12, 1.0 + float(R[2, 2] - R[0, 0] - R[1, 1]))) * 2.0
        w = float(R[1, 0] - R[0, 1]) / s
        x = float(R[0, 2] + R[2, 0]) / s
        y = float(R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    return [round(v / n, 5) for v in (w, x, y, z)]


def rot_axis(axis: np.ndarray, angle_rad: float) -> np.ndarray:
    """Rodrigues rotationsmatris (3x3, det == +1)."""
    if abs(angle_rad) < 1e-10:
        return np.eye(3, dtype=np.float64)
    n = float(np.linalg.norm(axis))
    if n < 1e-9:
        return np.eye(3, dtype=np.float64)
    k = axis / n
    kx, ky, kz = float(k[0]), float(k[1]), float(k[2])
    K = np.array([[0.0, -kz, ky], [kz, 0.0, -kx], [-ky, kx, 0.0]], dtype=np.float64)
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.eye(3, dtype=np.float64) + s * K + (1.0 - c) * (K @ K)


def rot_from_vecs(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Minimal rotationsmatris (det == +1) som avbildar enhetsvektorn a mot b."""
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-9 or nb < 1e-9:
        return np.eye(3, dtype=np.float64)
    va = a / na
    vb = b / nb
    dot = max(-1.0, min(1.0, float(np.dot(va, vb))))
    if dot > 1.0 - 1e-9:
        return np.eye(3, dtype=np.float64)
    if dot < -1.0 + 1e-7:
        orth = np.array([1.0, 0.0, 0.0]) if abs(va[0]) < 0.85 else np.array([0.0, 1.0, 0.0])
        ax = np.cross(va, orth)
        return rot_axis(ax, math.pi)
    v = np.cross(va, vb)
    c = dot
    K = np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]], dtype=np.float64)
    return np.eye(3, dtype=np.float64) + K + (K @ K) / (1.0 + c)


def _norm_vec(v: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-7:
        return fallback.copy()
    return v / n


def bygg_balram(pos_m: np.ndarray, ix: dict[str, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Ortonormal Gram-Schmidt bålram `(e_fwd, e_left, e_up)` med `det([e_fwd, e_left, e_up]) == +1`."""
    sp0 = pos_m[ix["c_spine0"]]
    sp3 = pos_m[ix["c_spine3"]]
    raw_up = sp3 - sp0
    e_up = _norm_vec(raw_up, np.array([0.0, 0.0, 1.0], dtype=np.float64))

    raw_lat = pos_m[ix["l_clavicle"]] - pos_m[ix["r_clavicle"]]
    lat_orth = raw_lat - float(np.dot(raw_lat, e_up)) * e_up
    if float(np.linalg.norm(lat_orth)) < 0.05:
        raw_hip = pos_m[ix["l_upleg"]] - pos_m[ix["r_upleg"]]
        lat_orth = raw_hip - float(np.dot(raw_hip, e_up)) * e_up
    if float(np.linalg.norm(lat_orth)) < 1e-5:
        alt = np.array([0.0, 1.0, 0.0]) if abs(e_up[1]) < 0.85 else np.array([1.0, 0.0, 0.0])
        lat_orth = alt - float(np.dot(alt, e_up)) * e_up
    e_left = lat_orth / max(1e-9, float(np.linalg.norm(lat_orth)))
    e_fwd = _norm_vec(np.cross(e_left, e_up), np.array([1.0, 0.0, 0.0]))
    e_left = _norm_vec(np.cross(e_up, e_fwd), e_left)

    # K7/orienteringsspärr: garantera högerhänt bas det == +1
    basis = np.column_stack([e_fwd, e_left, e_up])
    if float(np.linalg.det(basis)) < 0.0:
        raise ValueError("K7/matfel: Bålramen fick negativ determinant (oavsiktlig spegling).")
    return e_fwd, e_left, e_up


def rotera_subtrad(
    pts: np.ndarray,
    pivot_idx: int,
    desc_indices: list[int],
    R: np.ndarray,
) -> None:
    """Roterar ett underträd av leder stelt runt pivot-leden in-place."""
    if not desc_indices:
        return
    piv = pts[pivot_idx].copy()
    pts[desc_indices] = piv + (pts[desc_indices] - piv) @ R.T


def berakna_person_median_segment(
    spar_lista: list[dict[str, Any]],
    ix: dict[str, int],
) -> tuple[dict[tuple[str, str], float], dict[str, float]]:
    """Mäter exakta median-benlängder i mm över personens samtliga rutor i klippet."""
    rader: list[list[int | float]] = []
    for sp in spar_lista or []:
        rader.extend(sp.get("rutor") or [])
    if not rader:
        return {}, {}
    arr = np.asarray(rader, dtype=np.float64)[:, 1:].reshape(len(rader), len(ix), 3)
    seg_mm: dict[tuple[str, str], float] = {}
    for p_n, c_n in ALLA_KANTER:
        if p_n in ix and c_n in ix:
            d = np.linalg.norm(arr[:, ix[c_n], :] - arr[:, ix[p_n], :], axis=-1)
            seg_mm[(p_n, c_n)] = round(float(np.median(d)), 3)

    s01 = seg_mm.get(("c_spine0", "c_spine1"), 130.0)
    s12 = seg_mm.get(("c_spine1", "c_spine2"), 130.0)
    s23 = seg_mm.get(("c_spine2", "c_spine3"), 130.0)
    sammanfattning = {
        "rygg_langd": round(s01 + s12 + s23, 2),
        "l_overarm": round(seg_mm.get(("l_uparm", "l_lowarm"), 280.0), 2),
        "l_underarm": round(seg_mm.get(("l_lowarm", "l_wrist"), 260.0), 2),
        "r_overarm": round(seg_mm.get(("r_uparm", "r_lowarm"), 280.0), 2),
        "r_underarm": round(seg_mm.get(("r_lowarm", "r_wrist"), 260.0), 2),
        "l_lar": round(seg_mm.get(("l_upleg", "l_lowleg"), 420.0), 2),
        "l_skenben": round(seg_mm.get(("l_lowleg", "l_foot"), 390.0), 2),
        "r_lar": round(seg_mm.get(("r_upleg", "r_lowleg"), 420.0), 2),
        "r_skenben": round(seg_mm.get(("r_lowleg", "r_foot"), 390.0), 2),
    }
    return seg_mm, sammanfattning


def kvantisera_med_medianlangder(
    pos_m: np.ndarray,
    orig_row_mm: np.ndarray,
    ix: dict[str, int],
    seg_mm: dict[tuple[str, str], float],
    kanter: list[tuple[str, str]],
) -> np.ndarray:
    """En enda konvertering float-meter -> hel-mm med hierarkisk återprojicering mot median-mm."""
    out_mm = np.asarray(orig_row_mm, dtype=np.int64).copy()
    for p_n, c_n in kanter:
        if p_n not in ix or c_n not in ix:
            continue
        pi, ci = ix[p_n], ix[c_n]
        dv = pos_m[ci] - pos_m[pi]
        n = float(np.linalg.norm(dv))
        l_target = seg_mm.get((p_n, c_n))
        if n > 1e-8 and l_target is not None:
            dir_v = dv / n
            out_mm[ci] = np.rint(out_mm[pi].astype(np.float64) + dir_v * float(l_target)).astype(np.int64)
        else:
            out_mm[ci] = np.rint(pos_m[ci] * 1000.0).astype(np.int64)
    return out_mm


def max_benlangdsdrift_mm(
    arr_rutor: np.ndarray,
    ix: dict[str, int],
    seg_mm: dict[tuple[str, str], float],
    kanter: list[tuple[str, str]],
) -> float:
    """Maximal segmentlängdsdrift i mm mot personens median-mm över alla givna rutor."""
    if len(arr_rutor) == 0:
        return 0.0
    pts = arr_rutor[:, 1:].reshape(len(arr_rutor), len(ix), 3).astype(np.float64)
    worst = 0.0
    for p_n, c_n in kanter:
        if (p_n, c_n) not in seg_mm or p_n not in ix or c_n not in ix:
            continue
        d = np.linalg.norm(pts[:, ix[c_n], :] - pts[:, ix[p_n], :], axis=-1)
        err = float(np.max(np.abs(d - float(seg_mm[(p_n, c_n)]))))
        if err > worst:
            worst = err
    return round(worst, 3)


def speed_corr_0(pts_cand_m: np.ndarray, pts_orig_m: np.ndarray, ix: dict[str, int]) -> float:
    """Hastighetskorrelation vid lag 0 (samma leder som Kimodo-DOM: vänster hand, höger hand, huvud)."""
    j_idx = [ix[n] for n in ("l_wrist", "r_wrist", "c_head") if n in ix]
    n = min(len(pts_cand_m), len(pts_orig_m))
    if n < 3 or not j_idx:
        return 1.0
    vc = np.linalg.norm(np.diff(pts_cand_m[:n, j_idx, :], axis=0), axis=-1).mean(axis=1)
    vo = np.linalg.norm(np.diff(pts_orig_m[:n, j_idx, :], axis=0), axis=-1).mean(axis=1)
    if float(np.std(vc)) < 1e-8 or float(np.std(vo)) < 1e-8:
        return 1.0
    return round(float(np.corrcoef(vc, vo)[0, 1]), 4)


def punkt_i_obb(
    pt_m: np.ndarray,
    obj: dict[str, Any],
    marginal: float = 0.0,
) -> tuple[bool, float]:
    """Returnerar (inne, penetrationsdjup_m) för punkt mot roterad möbel-OBB runt Z."""
    px, py, pz = float(obj["pos"][0]), float(obj["pos"][1]), float(obj["pos"][2])
    mx, my, mz = float(obj["matt"][0]), float(obj["matt"][1]), float(obj["matt"][2])
    hx, hy, hz = mx * 0.5 + marginal, my * 0.5 + marginal, mz * 0.5 + marginal
    rz = float((obj.get("rot") or [0.0, 0.0, 0.0])[2])
    c, s = math.cos(-rz), math.sin(-rz)
    dx, dy, dz = float(pt_m[0]) - px, float(pt_m[1]) - py, float(pt_m[2]) - pz
    lx = c * dx - s * dy
    ly = s * dx + c * dy
    signed_x = abs(lx) - hx
    signed_y = abs(ly) - hy
    signed_z = abs(dz) - hz
    mx_signed = max(signed_x, signed_y, signed_z)
    return (mx_signed < 0.0), float(-mx_signed if mx_signed < 0.0 else 0.0)


def dist_till_obb(pt_m: np.ndarray, obj: dict[str, Any]) -> float:
    """Minsta euklidiska avstånd (m) från punkt till OBB (0.0 om inuti)."""
    px, py, pz = float(obj["pos"][0]), float(obj["pos"][1]), float(obj["pos"][2])
    hx, hy, hz = float(obj["matt"][0]) * 0.5, float(obj["matt"][1]) * 0.5, float(obj["matt"][2]) * 0.5
    rz = float((obj.get("rot") or [0.0, 0.0, 0.0])[2])
    c, s = math.cos(-rz), math.sin(-rz)
    dx, dy, dz = float(pt_m[0]) - px, float(pt_m[1]) - py, float(pt_m[2]) - pz
    lx = abs(c * dx - s * dy)
    ly = abs(s * dx + c * dy)
    lz = abs(dz)
    qx = max(0.0, lx - hx)
    qy = max(0.0, ly - hy)
    qz = max(0.0, lz - hz)
    return math.sqrt(qx * qx + qy * qy + qz * qz)


def ray_traffar_silhuett_obb(
    cam_pos: np.ndarray,
    pt_m: np.ndarray,
    obj: dict[str, Any],
) -> bool:
    """Testar om siktlinjen kamera->led skär möbelns golv-till-ovansida OBB (t ∈ (0.02, 0.99))."""
    px, py, pz = float(obj["pos"][0]), float(obj["pos"][1]), float(obj["pos"][2])
    mx, my, mz = float(obj["matt"][0]), float(obj["matt"][1]), float(obj["matt"][2])
    z_top = pz + mz * 0.5
    z_bot = min(0.0, pz - mz * 0.5) if obj.get("typ") in HINDER_TYPER else (pz - mz * 0.5)
    cz = (z_bot + z_top) * 0.5
    hz = max(0.01, (z_top - z_bot) * 0.5)
    hx, hy = max(0.01, mx * 0.5), max(0.01, my * 0.5)

    rz = float((obj.get("rot") or [0.0, 0.0, 0.0])[2])
    c, s = math.cos(-rz), math.sin(-rz)

    def _to_local(p: np.ndarray) -> tuple[float, float, float]:
        dx, dy, dz = float(p[0]) - px, float(p[1]) - py, float(p[2]) - cz
        return (c * dx - s * dy, s * dx + c * dy, dz)

    o = _to_local(cam_pos)
    e = _to_local(pt_m)
    d = (e[0] - o[0], e[1] - o[1], e[2] - o[2])
    tmin, tmax = 0.02, 0.99
    for oi, di, hi in ((o[0], d[0], hx), (o[1], d[1], hy), (o[2], d[2], hz)):
        if abs(di) < 1e-8:
            if oi < -hi or oi > hi:
                return False
        else:
            t1 = (-hi - oi) / di
            t2 = (hi - oi) / di
            if t1 > t2:
                t1, t2 = t2, t1
            tmin = max(tmin, t1)
            tmax = min(tmax, t2)
            if tmin > tmax:
                return False
    return tmin <= tmax


def sampla_kamera_vid_ruta(kamera: dict[str, Any], u: float) -> tuple[np.ndarray, np.ndarray, float]:
    """Returnerar (cam_pos, R_world_from_cam, lins_mm) vid ruta u."""
    nyck = kamera.get("nycklar") or []
    if not nyck:
        return np.zeros(3), np.eye(3), 50.0
    if kamera.get("statisk") or len(nyck) == 1 or u <= nyck[0][0]:
        k = nyck[0]
        return np.array(k[1:4], dtype=np.float64), mat_from_wxyz(k[4:8]), float(k[8])
    if u >= nyck[-1][0]:
        k = nyck[-1]
        return np.array(k[1:4], dtype=np.float64), mat_from_wxyz(k[4:8]), float(k[8])
    lo, hi = 0, len(nyck) - 1
    while lo + 1 < hi:
        mid = (lo + hi) >> 1
        if nyck[mid][0] <= u:
            lo = mid
        else:
            hi = mid
    a, b = nyck[lo], nyck[hi]
    span = b[0] - a[0]
    alpha = (u - a[0]) / span if span > 1e-9 else 0.0
    pos = (1.0 - alpha) * np.array(a[1:4], dtype=np.float64) + alpha * np.array(b[1:4], dtype=np.float64)
    qa = np.array(a[4:8], dtype=np.float64)
    qb = np.array(b[4:8], dtype=np.float64)
    if float(np.dot(qa, qb)) < 0.0:
        qb = -qb
    q = (1.0 - alpha) * qa + alpha * qb
    lins = (1.0 - alpha) * float(a[8]) + alpha * float(b[8])
    return pos, mat_from_wxyz(q), lins


def kamera_basvektorer(R: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returnerar (right, up, forward) i världskoordinater (Three.js/Blender: -Z = fram)."""
    return R[:, 0], R[:, 1], -R[:, 2]


def projicera_punkter(
    pts_m: np.ndarray,
    cam_pos: np.ndarray,
    R_cam: np.ndarray,
    lins_mm: float,
    bild: dict[str, Any] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Projicerar (K, 3) punkter till (ndc_x, ndc_y, inside_bool) i 9:16-frustum (sensor_fit=HORIZONTAL)."""
    sensor_mm = float((bild or {}).get("sensor_mm") or 36.0)
    w = float((bild or {}).get("bredd") or 576)
    h = float((bild or {}).get("hojd") or 1024)
    safe_lens = max(8.0, float(lins_mm))
    tan_hx = sensor_mm / (2.0 * safe_lens)
    tan_hy = tan_hx * (h / max(1.0, w))

    right, up, fwd = kamera_basvektorer(R_cam)
    rel = pts_m - cam_pos
    depth = rel @ fwd
    safe_d = np.where(depth > 0.05, depth, 0.05)
    nx = (rel @ right) / (safe_d * tan_hx)
    ny = (rel @ up) / (safe_d * tan_hy)
    inne = (depth > 0.05) & (np.abs(nx) <= 1.0) & (np.abs(ny) <= 1.0)
    return nx, ny, inne


def _smoothstep(s: float) -> float:
    x = max(0.0, min(1.0, float(s)))
    return x * x * (3.0 - 2.0 * x)


def _moving_average_1d(arr: np.ndarray, win: int) -> np.ndarray:
    if len(arr) <= 2 or win <= 1:
        return arr.copy()
    w = min(win, len(arr))
    if w % 2 == 0:
        w = max(1, w - 1)
    pad = w // 2
    kernel = np.ones(w, dtype=np.float64) / w
    padded = np.pad(arr, ((pad, pad), (0, 0), (0, 0)), mode="edge")
    out = np.empty_like(arr)
    for j in range(arr.shape[1]):
        for c in range(3):
            out[:, j, c] = np.convolve(padded[:, j, c], kernel, mode="valid")[: len(arr)]
    return out


def applicera_kropp_attityd_pa_sp(
    rutor: list[list[int | float]],
    ix: dict[str, int],
    seg_mm: dict[tuple[str, str], float],
    slapphet_delta: float = 0.0,
    lutning_delta_deg: float = 0.0,
    gest_skala: float = 1.0,
    blick_yaw_deg: float = 0.0,
    blick_pitch_deg: float = 0.0,
) -> tuple[list[list[int]], dict[str, float]]:
    """Deterministisk överkropps-FK + blick + gestskalning med <1 mm bendrift och 0 cm fotglidning."""
    if not rutor:
        return [], {"head_sankning_cm": 0.0, "speed_corr_0": 1.0, "max_drift_mm": 0.0, "fotglidning_cm": 0.0}

    if gest_skala < 0.0:
        raise ValueError("K7-spärr: Negativ gest_skala är förbjuden.")

    arr_orig = np.asarray(rutor, dtype=np.float64)
    u_col = arr_orig[:, 0]
    orig_mm = np.rint(arr_orig[:, 1:]).astype(np.int64).reshape(len(arr_orig), len(ix), 3)
    pts_orig_m = arr_orig[:, 1:].reshape(len(arr_orig), len(ix), 3) / 1000.0
    pts = pts_orig_m.copy()
    T = len(pts)

    # Tidsramp: 6–10 rutor in-/uttoning så ändringar aldrig skapar hård hopp-skarv
    ramp = min(8, max(2, T // 5)) if T < 36 else min(10, max(6, T // 8))
    weights = np.ones(T, dtype=np.float64)
    if T >= 4:
        for t in range(T):
            w_in = _smoothstep(t / max(1, ramp)) if t < ramp else 1.0
            w_out = _smoothstep((T - 1 - t) / max(1, ramp)) if (T - 1 - t) < ramp else 1.0
            weights[t] = min(w_in, w_out)

    # Förberäkna bålramar & skulder-relativa arm/handbanor för lokal gest_skala
    frames_basis = [bygg_balram(pts_orig_m[t], ix) for t in range(T)]
    arm_joints = [ix[n] for n in ("l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
                                  "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1") if n in ix]
    need_gest = abs(float(gest_skala) - 1.0) > 1e-4 and T >= 3
    if need_gest:
        # Lokal offset i bålram runt skuldra (l_uparm/r_uparm)
        rel_local = np.zeros((T, len(arm_joints), 3), dtype=np.float64)
        for t in range(T):
            ef, el, eu = frames_basis[t]
            B = np.column_stack([ef, el, eu])  # B.T @ v_world -> v_local
            sh_l = pts_orig_m[t, ix["l_uparm"]]
            sh_r = pts_orig_m[t, ix["r_uparm"]]
            for k, ji in enumerate(arm_joints):
                sh = sh_l if k < 5 else sh_r
                rel_local[t, k] = (pts_orig_m[t, ji] - sh) @ B
        base_local = _moving_average_1d(rel_local, min(19, max(5, T // 5)))

    spine_desc_ix = {k: [ix[n] for n in vs if n in ix] for k, vs in SPINE_DESC.items()}
    sh_l_sub = [ix[n] for n in ("l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1") if n in ix]
    sh_r_sub = [ix[n] for n in ("r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1") if n in ix]
    arm_l_sub = [ix[n] for n in ("l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1") if n in ix]
    arm_r_sub = [ix[n] for n in ("r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1") if n in ix]

    pitch_total_deg = max(-28.0, min(32.0, float(lutning_delta_deg) + float(slapphet_delta) * 20.0))
    slouch_drop_m = max(-0.04, min(0.05, float(slapphet_delta) * 0.045))
    slouch_arm_pitch_rad = math.radians(max(-12.0, min(14.0, float(slapphet_delta) * 10.0)))
    # Klampa total blick inom ±70° yaw och ±40° pitch
    yaw_rad = math.radians(max(-70.0, min(70.0, float(blick_yaw_deg))))
    gaze_pitch_rad = math.radians(max(-40.0, min(40.0, float(blick_pitch_deg) + float(slapphet_delta) * 10.0)))

    prev_head_fwd: np.ndarray | None = None
    nya_rutor: list[list[int]] = []

    for t in range(T):
        w = float(weights[t])
        ef, el, eu = frames_basis[t]
        B = np.column_stack([ef, el, eu])

        # 0. Gestskalning runt lokal axelbaslinje före stel ryggrotation
        if need_gest:
            scale = 1.0 + w * (float(gest_skala) - 1.0)
            sh_l = pts[t, ix["l_uparm"]].copy()
            sh_r = pts[t, ix["r_uparm"]].copy()
            for k, ji in enumerate(arm_joints):
                sh = sh_l if k < 5 else sh_r
                delta_loc = base_local[t, k] + scale * (rel_local[t, k] - base_local[t, k])
                pts[t, ji] = sh + B @ delta_loc

        # 1. Additiv framåtriktad rygg-FK runt c_spine0..3 med (0.15, 0.25, 0.30, 0.30)
        tot_rad = math.radians(pitch_total_deg * w)
        if abs(tot_rad) > 1e-6:
            cur_axis = el.copy()
            for sp_n, vikt in RYGG_VIKTER:
                if sp_n not in ix:
                    continue
                R_sp = rot_axis(cur_axis, tot_rad * vikt)
                rotera_subtrad(pts[t], ix[sp_n], spine_desc_ix[sp_n], R_sp)

        # 2. Hängande axlar vid ökad slapphet
        if abs(slouch_drop_m * w) > 1e-5:
            ef2, el2, eu2 = bygg_balram(pts[t], ix)
            drop_vec = (-slouch_drop_m * w) * eu2 + (0.30 * slouch_drop_m * w) * ef2
            pts[t, sh_l_sub] += drop_vec
            pts[t, sh_r_sub] += drop_vec
            if abs(slouch_arm_pitch_rad * w) > 1e-5:
                R_ar = rot_axis(el2, slouch_arm_pitch_rad * w)
                rotera_subtrad(pts[t], ix["l_uparm"], arm_l_sub[1:], R_ar)
                rotera_subtrad(pts[t], ix["r_uparm"], arm_r_sub[1:], R_ar)

        # 3. Blickriktning (40 % c_neck, 60 % c_head) med singularitetsskydd längs upp-axeln
        if abs(yaw_rad * w) > 1e-6 or abs(gaze_pitch_rad * w) > 1e-6:
            ef3, el3, eu3 = bygg_balram(pts[t], ix)
            # Om nasa_mal är nästan kollineär med eu3, använd föregående rutor
            nose_dir = pts[t, ix["nasa_mal"]] - pts[t, ix["c_head"]]
            nose_orth = nose_dir - float(np.dot(nose_dir, eu3)) * eu3
            if float(np.linalg.norm(nose_orth)) < 0.02 and prev_head_fwd is not None:
                ef3 = prev_head_fwd
                el3 = _norm_vec(np.cross(eu3, ef3), el3)
            else:
                prev_head_fwd = ef3.copy()
            R_neck = rot_axis(eu3, yaw_rad * w * 0.40) @ rot_axis(el3, gaze_pitch_rad * w * 0.40)
            rotera_subtrad(pts[t], ix["c_neck"], spine_desc_ix["c_neck"], R_neck)
            R_head = rot_axis(eu3, yaw_rad * w * 0.60) @ rot_axis(el3, gaze_pitch_rad * w * 0.60)
            rotera_subtrad(pts[t], ix["c_head"], spine_desc_ix["c_head"], R_head)

        # 4. En enda mm-konvertering + återprojicering av hela modifierade överkroppen mot L_med
        row_mm = kvantisera_med_medianlangder(pts[t], orig_mm[t], ix, seg_mm, OVERKROPP_KANTER)
        nya_rutor.append([int(round(u_col[t]))] + [int(v) for v in row_mm.reshape(-1)])

    arr_ny = np.asarray(nya_rutor, dtype=np.float64)
    pts_ny_m = arr_ny[:, 1:].reshape(T, len(ix), 3) / 1000.0
    head_sank_cm = float((pts_orig_m[:, ix["c_head"], 2].mean() - pts_ny_m[:, ix["c_head"], 2].mean()) * 100.0)
    sc0 = speed_corr_0(pts_ny_m, pts_orig_m, ix)
    drift = max_benlangdsdrift_mm(arr_ny, ix, seg_mm, OVERKROPP_KANTER)

    foot_idx = [ix[n] for n in ("l_foot", "r_foot", "l_ball", "r_ball") if n in ix]
    fot_diff_cm = float(np.max(np.linalg.norm((pts_ny_m[:, foot_idx] - pts_orig_m[:, foot_idx]) * 100.0, axis=-1)))

    return nya_rutor, {
        "head_sankning_cm": round(head_sank_cm, 2),
        "speed_corr_0": sc0,
        "max_drift_mm": drift,
        "fotglidning_cm": round(fot_diff_cm, 3),
    }


def _arm_ik_2ben(
    S: np.ndarray,
    G: np.ndarray,
    L1: float,
    L2: float,
    pole_dir: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Analytisk 2-bens-IK med klampad cosinussats och mjuk soft-IK-dämpning över 0.97*(L1+L2)."""
    vec = G - S
    d_raw = float(np.linalg.norm(vec))
    u_dir = _norm_vec(vec, np.array([1.0, 0.0, 0.0]))
    r_tot = L1 + L2
    r_soft = 0.97 * r_tot
    r_max = 0.999 * r_tot
    if d_raw > r_soft:
        overshoot = d_raw - r_soft
        span = max(1e-4, r_max - r_soft)
        d = r_soft + span * math.tanh(overshoot / max(1e-4, r_tot * 0.08))
    else:
        d = max(abs(L1 - L2) + 0.015, d_raw)

    # Ortogonal polvektor vinkelrät mot S->G
    p_orth = pole_dir - float(np.dot(pole_dir, u_dir)) * u_dir
    if float(np.linalg.norm(p_orth)) < 1e-6:
        alt = np.array([0.0, 0.0, -1.0]) if abs(u_dir[2]) < 0.85 else np.array([-1.0, 0.0, 0.0])
        p_orth = alt - float(np.dot(alt, u_dir)) * u_dir
    p_dir = _norm_vec(p_orth, np.array([0.0, 0.0, -1.0]))

    cos_a = max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / max(1e-9, 2.0 * L1 * d)))
    sin_a = math.sqrt(max(0.0, 1.0 - cos_a * cos_a))
    E = S + (L1 * cos_a) * u_dir + (L1 * sin_a) * p_dir
    W_dir = _norm_vec(S + d * u_dir - E, u_dir)
    W = E + L2 * W_dir
    return E, W


def _resolve_g4_target(
    goal: np.ndarray,
    shoulder: np.ndarray,
    hinder_objs: list[dict[str, Any]],
    max_reach: float,
    max_iter: int = 12,
) -> tuple[np.ndarray, bool]:
    """Flyttar IK-målet upp/utåt ur ev. bänk-/bords-OBB (max N iterationer, annars G4-flagga)."""
    g = goal.copy()
    for _ in range(max_iter):
        krock = None
        best_depth = 0.0
        for obj in hinder_objs:
            inne, depth = punkt_i_obb(g, obj, marginal=0.045)
            if inne and depth > best_depth:
                best_depth = depth
                krock = obj
        if krock is None:
            return g, False
        top_z = float(krock["pos"][2]) + float(krock["matt"][2]) * 0.5 + 0.06
        cand_up = np.array([g[0], g[1], max(g[2] + 0.08, top_z)], dtype=np.float64)
        if float(np.linalg.norm(cand_up - shoulder)) <= max_reach * 1.02:
            g = cand_up
        else:
            away = _norm_vec(np.array([shoulder[0] - float(krock["pos"][0]),
                                       shoulder[1] - float(krock["pos"][1]),
                                       0.25]), np.array([0.0, 0.0, 1.0]))
            g = g + away * (best_depth + 0.06)

    still_hit = any(punkt_i_obb(g, o, marginal=0.03)[0] for o in hinder_objs)
    return g, still_hit


def applicera_kropp_hand_ik_pa_sp(
    rutor: list[list[int | float]],
    ix: dict[str, int],
    seg_mm: dict[tuple[str, str], float],
    sida: str,
    mal_pos_m: np.ndarray | None = None,
    delta_m: tuple[float, float, float] = (0.0, 0.0, 0.0),
    fran_andel: float = 0.15,
    till_andel: float = 0.85,
    hinder_objs: list[dict[str, Any]] | None = None,
) -> tuple[list[list[int]], dict[str, Any]]:
    """Strikt envald 2-bens arm-IK + clavicle-assist + polvektor + kubisk in-/utblendning."""
    if not rutor:
        return [], {"max_drift_mm": 0.0, "hand_traj_diff_mm": 0.0, "other_hand_diff_mm": 0.0, "g4_varning": False}
    if sida not in ("l", "r"):
        raise ValueError(f"K7-spärr: Ogiltig sida '{sida}'.")

    clav_n = f"{sida}_clavicle"
    sh_n = f"{sida}_uparm"
    el_n = f"{sida}_lowarm"
    wr_n = f"{sida}_wrist"
    hm_n = f"{sida}_hand_mitt"
    in_n = f"{sida}_index1"
    other = "r" if sida == "l" else "l"
    arm_edges = [
        ("c_spine3", clav_n),
        (clav_n, sh_n),
        (sh_n, el_n),
        (el_n, wr_n),
        (wr_n, hm_n),
        (wr_n, in_n),
    ]

    arr_orig = np.asarray(rutor, dtype=np.float64)
    u_col = arr_orig[:, 0]
    orig_mm = np.rint(arr_orig[:, 1:]).astype(np.int64).reshape(len(arr_orig), len(ix), 3)
    pts_orig_m = arr_orig[:, 1:].reshape(len(arr_orig), len(ix), 3) / 1000.0
    pts = pts_orig_m.copy()
    T = len(pts)

    L_clav_sh = float(seg_mm.get((clav_n, sh_n), 150.0)) / 1000.0
    L1 = float(seg_mm.get((sh_n, el_n), 275.0)) / 1000.0
    L2 = float(seg_mm.get((el_n, wr_n), 260.0)) / 1000.0

    a = max(0.0, min(0.95, float(fran_andel)))
    b = max(a + 0.02, min(1.0, float(till_andel)))
    span = b - a
    ramp = min(0.18, max(0.04, 0.30 * span))

    dx, dy, dz = float(delta_m[0]), float(delta_m[1]), float(delta_m[2])
    delta_arr = np.array([dx, dy, dz], dtype=np.float64)
    hinder = hinder_objs or []

    prev_pole: np.ndarray | None = None
    g4_unresolved = False
    goal_errs_mm: list[float] = []
    nya_rutor: list[list[int]] = []

    for t in range(T):
        u_t = t / max(1, T - 1) if T > 1 else 0.5
        if u_t < a or u_t > b:
            w = 0.0
        elif u_t < a + ramp:
            w = _smoothstep((u_t - a) / ramp)
        elif u_t > b - ramp:
            w = _smoothstep((b - u_t) / ramp)
        else:
            w = 1.0

        C = pts[t, ix[clav_n]].copy()
        S_orig = pts[t, ix[sh_n]].copy()
        # Justera C och S till exakt medianlängd ut från c_spine3 innan IK löses så handledsträffen blir <2 mm
        sp3_mm = orig_mm[t, ix["c_spine3"]].astype(np.float64)
        l_s3_cl = seg_mm.get(("c_spine3", clav_n))
        if l_s3_cl is not None:
            dc = C - sp3_mm / 1000.0
            nc = float(np.linalg.norm(dc))
            if nc > 1e-7:
                C = (np.rint(sp3_mm + (dc / nc) * float(l_s3_cl)) / 1000.0)
        l_cl_sh = seg_mm.get((clav_n, sh_n))
        if l_cl_sh is not None:
            ds = pts[t, ix[sh_n]] - pts[t, ix[clav_n]]
            ns = float(np.linalg.norm(ds))
            if ns > 1e-7:
                S_orig = np.rint(C * 1000.0 + (ds / ns) * float(l_cl_sh)) / 1000.0

        E_orig = pts[t, ix[el_n]].copy()
        W_orig = pts[t, ix[wr_n]].copy()
        hm_orig = pts[t, ix[hm_n]].copy()
        in_orig = pts[t, ix[in_n]].copy()

        G_full = (mal_pos_m + delta_arr) if mal_pos_m is not None else (W_orig + delta_arr)
        if w > 1e-6 and hinder:
            G_full, g4_hit = _resolve_g4_target(G_full, S_orig, hinder, L1 + L2)
            if g4_hit:
                g4_unresolved = True
        W_target = (1.0 - w) * W_orig + w * G_full

        # Clavicle-assist upp till <= 18° vid räckvidd > 0.97*(L1+L2)
        S = S_orig
        dist_raw = float(np.linalg.norm(W_target - S_orig))
        if dist_raw > 0.97 * (L1 + L2) and w > 1e-6:
            reach_dir = _norm_vec(W_target - C, np.array([1.0, 0.0, 0.0]))
            clav_dir_orig = _norm_vec(S_orig - C, reach_dir)
            dot_c = max(-1.0, min(1.0, float(np.dot(clav_dir_orig, reach_dir))))
            ang = math.acos(dot_c)
            if ang > 1e-5:
                max_ang = math.radians(18.0) * w
                rot_ang = min(ang, max_ang)
                ax = np.cross(clav_dir_orig, reach_dir)
                R_cl = rot_axis(ax, rot_ang)
                clav_vec_new = R_cl @ (clav_dir_orig * L_clav_sh)
                S = C + clav_vec_new
                if l_cl_sh is not None:
                    ds2 = S - C
                    ns2 = float(np.linalg.norm(ds2))
                    if ns2 > 1e-7:
                        S = np.rint(C * 1000.0 + (ds2 / ns2) * float(l_cl_sh)) / 1000.0

        # Polvektor ur originalarmbågen projicerad ortogonalt mot axeln S->W_target
        ax_sw = _norm_vec(W_target - S, np.array([1.0, 0.0, 0.0]))
        raw_pole = E_orig - pts[t, ix[sh_n]]
        pole_orth = raw_pole - float(np.dot(raw_pole, ax_sw)) * ax_sw
        if float(np.linalg.norm(pole_orth)) > 0.03:
            pole_dir = pole_orth / float(np.linalg.norm(pole_orth))
            prev_pole = pole_dir.copy()
        elif prev_pole is not None:
            p2 = prev_pole - float(np.dot(prev_pole, ax_sw)) * ax_sw
            if float(np.linalg.norm(p2)) > 1e-4:
                pole_dir = p2 / float(np.linalg.norm(p2))
            else:
                ef, _, eu = bygg_balram(pts_orig_m[t], ix)
                pole_dir = _norm_vec(-0.7 * eu - 0.7 * ef, np.array([0.0, 0.0, -1.0]))
        else:
            ef, _, eu = bygg_balram(pts_orig_m[t], ix)
            pole_dir = _norm_vec(-0.7 * eu - 0.7 * ef, np.array([0.0, 0.0, -1.0]))

        E_new, W_new = _arm_ik_2ben(S, W_target, L1, L2, pole_dir)

        # Stel handoffset i underarmsram (rot_from_vecs mellan original & nytt armplan)
        fore_orig = _norm_vec(W_orig - E_orig, np.array([1.0, 0.0, 0.0]))
        fore_new = _norm_vec(W_new - E_new, fore_orig)
        n_orig = np.cross(E_orig - pts[t, ix[sh_n]], fore_orig)
        n_new = np.cross(E_new - S, fore_new)
        if float(np.linalg.norm(n_orig)) > 1e-4 and float(np.linalg.norm(n_new)) > 1e-4:
            n_o = n_orig / float(np.linalg.norm(n_orig))
            n_n = n_new / float(np.linalg.norm(n_new))
            R_o = np.column_stack([fore_orig, n_o, np.cross(fore_orig, n_o)])
            R_n = np.column_stack([fore_new, n_n, np.cross(fore_new, n_n)])
            R_hand = R_n @ R_o.T
        else:
            R_hand = rot_from_vecs(fore_orig, fore_new)

        pts[t, ix[clav_n]] = C
        pts[t, ix[sh_n]] = S
        pts[t, ix[el_n]] = E_new
        pts[t, ix[wr_n]] = W_new
        pts[t, ix[hm_n]] = W_new + R_hand @ (hm_orig - W_orig)
        pts[t, ix[in_n]] = W_new + R_hand @ (in_orig - W_orig)

        row_mm = kvantisera_med_medianlangder(pts[t], orig_mm[t], ix, seg_mm, arm_edges)
        nya_rutor.append([int(round(u_col[t]))] + [int(v) for v in row_mm.reshape(-1)])

        if w > 0.95:
            w_mm_pos = row_mm[ix[wr_n]].astype(np.float64)
            goal_errs_mm.append(float(np.linalg.norm(w_mm_pos - G_full * 1000.0)))

    arr_ny = np.asarray(nya_rutor, dtype=np.float64)
    ny_pts_mm = arr_ny[:, 1:].reshape(T, len(ix), 3)
    other_ix = [ix[n] for n in ARM_KEDJOR[other] if n in ix]
    other_diff_mm = float(np.max(np.abs(ny_pts_mm[:, other_ix] - orig_mm[:, other_ix]))) if other_ix else 0.0
    drift = max_benlangdsdrift_mm(arr_ny, ix, seg_mm, arm_edges)

    return nya_rutor, {
        "max_drift_mm": drift,
        "other_hand_diff_mm": round(other_diff_mm, 3),
        "goal_err_median_mm": round(float(np.median(goal_errs_mm)), 2) if goal_errs_mm else 0.0,
        "g4_varning": g4_unresolved,
    }


def hitta_matshot_placering(
    scen: dict[str, Any],
    tagning_id: str,
) -> tuple[list[float], str]:
    """Beräknar bords- eller kameracentrumpunkt i meter för matshot-primitiv i given tagning."""
    tagn = next((t for t in scen.get("tagningar", []) if t.get("id") == tagning_id), None)
    if tagn and (tagn.get("kamera") or {}).get("nycklar"):
        a0, b0 = int(tagn["ut"][0]), int(tagn["ut"][1])
        u_mid = 0.5 * (a0 + max(a0, b0 - 1))
        cam_pos, R_cam, lins = sampla_kamera_vid_ruta(tagn["kamera"], u_mid)
        _, _, fwd = kamera_basvektorer(R_cam)
    else:
        cam_pos = np.array([0.0, -1.5, 1.45], dtype=np.float64)
        R_cam = np.eye(3, dtype=np.float64)
        lins = 50.0
        fwd = np.array([0.0, 1.0, -0.35], dtype=np.float64)
        fwd = fwd / float(np.linalg.norm(fwd))

    bild = scen.get("bild") or {"bredd": 576, "hojd": 1024, "sensor_mm": 36.0}
    bord = [o for o in scen.get("objekt", []) if o.get("typ") in ("bord", "disk", "bank")]
    bast_bord = None
    bast_score = 1e9
    for o in bord:
        op = np.array(o["pos"], dtype=np.float64)
        nx, ny, inne = projicera_punkter(op[None, :], cam_pos, R_cam, lins, bild)
        dist = float(np.linalg.norm(op[:2] - cam_pos[:2]))
        sc = dist + (0.0 if bool(inne[0]) else 2.5) + 0.4 * float(abs(nx[0]))
        if sc < bast_score:
            bast_score = sc
            bast_bord = o

    if bast_bord is not None:
        bx, by, bz = [float(v) for v in bast_bord["pos"]]
        top_z = bz + float(bast_bord["matt"][2]) * 0.5
        # Snitta kamerastrålen mot bordsplanets z = top_z och klampa till bordets horisontella utsträckning
        px, py = bx, by
        if abs(float(fwd[2])) > 0.08:
            t_hit = (top_z - float(cam_pos[2])) / float(fwd[2])
            if 0.25 < t_hit < 5.0:
                hx = float(cam_pos[0] + t_hit * fwd[0])
                hy = float(cam_pos[1] + t_hit * fwd[1])
                rz = float((bast_bord.get("rot") or [0.0, 0.0, 0.0])[2])
                c, s = math.cos(-rz), math.sin(-rz)
                lx = c * (hx - bx) - s * (hy - by)
                ly = s * (hx - bx) + c * (hy - by)
                lim_x = max(0.05, float(bast_bord["matt"][0]) * 0.36)
                lim_y = max(0.05, float(bast_bord["matt"][1]) * 0.36)
                lx = max(-lim_x, min(lim_x, lx))
                ly = max(-lim_y, min(lim_y, ly))
                cw, sw = math.cos(rz), math.sin(rz)
                px = bx + cw * lx - sw * ly
                py = by + sw * lx + cw * ly
        return [round(px, 3), round(py, 3), round(top_z + 0.035, 3)], str(bast_bord["id"])

    # Fallback framför kamerans centrum
    p = cam_pos + 1.05 * fwd
    p[2] = max(0.75, min(1.25, float(p[2])))
    return [round(float(v), 3) for v in p], "kameracentrum"


def applicera_kamerakurva_pa_tagning(
    tagning: dict[str, Any],
    kamera_rorelse: str,
    styrka: float = 1.0,
) -> None:
    """Applicerar deterministisk lokal u ∈ [0,1] kamerarörelse inom fasta tagningsgränser [a,b)."""
    kam = tagning.get("kamera")
    if not kam or not kam.get("nycklar"):
        return
    if "_bas_nycklar" not in kam:
        kam["_bas_nycklar"] = [list(k) for k in kam["nycklar"]]
        kam["_bas_statisk"] = bool(kam.get("statisk", True))

    bas_nyck = kam["_bas_nycklar"]
    mode = (kamera_rorelse or "behall").strip().lower()
    if mode == "behall":
        kam["nycklar"] = [list(k) for k in bas_nyck]
        kam["statisk"] = bool(kam["_bas_statisk"])
        return

    a0, b0 = int(tagning["ut"][0]), int(tagning["ut"][1])
    span = max(1, b0 - 1 - a0)
    steg = max(1, min(2, span))
    u_lista = list(range(a0, b0, steg))
    if u_lista[-1] != b0 - 1:
        u_lista.append(b0 - 1)

    s_val = max(0.1, min(2.0, float(styrka)))
    nyck_ut: list[list[float]] = []
    bas_kam_wrap = {"statisk": kam["_bas_statisk"], "nycklar": bas_nyck}

    for u in u_lista:
        t_norm = (u - a0) / max(1, span)
        ease = _smoothstep(t_norm)
        pos, R, lins = sampla_kamera_vid_ruta(bas_kam_wrap, float(u))
        right, up, fwd = kamera_basvektorer(R)

        if mode in ("inakning", "slowmo_in"):
            pos = pos + fwd * (0.28 * s_val * ease)
            lins = min(135.0, lins * (1.0 + 0.14 * s_val * ease))
        elif mode == "pan_hoger":
            ang = -math.radians(7.5 * s_val * (ease - 0.5))
            R = rot_axis(up, ang) @ R
        elif mode == "ovre_ned":
            pos = pos + up * (0.22 * s_val * (1.0 - ease)) - fwd * (0.08 * (1.0 - ease))
            tilt = -math.radians(10.0 * s_val * (1.0 - ease))
            R = rot_axis(right, tilt) @ R

        q_wxyz = wxyz_from_mat(R)
        nyck_ut.append(
            [int(u)]
            + [round(float(v), 4) for v in pos]
            + q_wxyz
            + [round(float(lins), 2)]
        )

    kam["nycklar"] = nyck_ut
    kam["statisk"] = False
