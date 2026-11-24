"""Deterministiska, snabba (<50 ms) operationer på hela scenen, tidslinjen och medielagren."""
from __future__ import annotations

import copy
import math
import time
from typing import Any

import numpy as np

from .k7_vakt import K7StoppError, kontrollera_operation, logga_k7
from .schema import MILJO_TEMAN, klona_scen_snabbt, kompilera_tillstand

_TEMA_ALIAS = {
    "kök": "kok",
    "kitchen": "kok",
    "kafe": "kafe",
    "kafé": "kafe",
    "cafe": "kafe",
    "café": "kafe",
    "ute": "uteservering",
    "terrass": "uteservering",
    "pizzeria": "matsal",
    "restaurang": "matsal",
    "bistro": "matsal",
    "truck": "foodtruck",
}

_PROP_MALLAR: dict[str, dict[str, Any]] = {
    "kaffemaskin": {"matt": [0.42, 0.38, 0.44], "farg": "#c4cbd4", "placering": "bord"},
    "spis": {"matt": [0.85, 0.65, 0.88], "farg": "#5f6875", "placering": "golv"},
    "disk": {"matt": [1.4, 0.54, 0.9], "farg": "#7d5b42", "placering": "golv"},
    "bank": {"matt": [1.3, 0.55, 0.88], "farg": "#8d96a3", "placering": "golv"},
    "skylt": {"matt": [0.76, 0.06, 0.34], "farg": "#1c2230", "placering": "hojd", "z": 1.68},
    "hylla": {"matt": [1.1, 0.26, 0.12], "farg": "#8b6d4c", "placering": "hojd", "z": 1.55},
    "parasoll": {"matt": [1.65, 1.65, 0.2], "farg": "#d46c44", "placering": "hojd", "z": 2.18},
    "lampa": {"matt": [0.3, 0.3, 0.24], "farg": "#ffe0a8", "placering": "hojd", "z": 2.12},
    "prop": {"matt": [0.18, 0.18, 0.11], "farg": "#d19a66", "placering": "bord"},
}

_MILJO_PROPS: dict[str, list[dict[str, Any]]] = {
    "kok": [
        {"typ": "spis", "etikett": "Spis & Stekhäll", "farg": "#697380"},
        {"typ": "bank", "etikett": "Rostfri prep-bänk", "farg": "#9aa3b0"},
        {"typ": "hylla", "etikett": "Kökshylla", "farg": "#8b94a0"},
        {"typ": "lampa", "etikett": "Värmelampa", "farg": "#ffdfb0"},
        {"typ": "skylt", "etikett": "KÖK · PREP", "farg": "#1e2736"},
    ],
    "bar": [
        {"typ": "disk", "etikett": "Barstation", "farg": "#4b3428"},
        {"typ": "hylla", "etikett": "Flaskhylla", "farg": "#6e4e37"},
        {"typ": "lampa", "etikett": "Barlampa", "farg": "#ffd28f"},
        {"typ": "skylt", "etikett": "BAR · COCKTAILS", "farg": "#1a1f2e"},
    ],
    "uteservering": [
        {"typ": "parasoll", "etikett": "Parasoll", "farg": "#d97248"},
        {"typ": "bank", "etikett": "Utebänk", "farg": "#7d6044"},
        {"typ": "skylt", "etikett": "UTESERVERING", "farg": "#274133"},
    ],
    "kafe": [
        {"typ": "kaffemaskin", "etikett": "Espressomaskin", "farg": "#c7ced6"},
        {"typ": "disk", "etikett": "Bakverksdisk", "farg": "#a8835e"},
        {"typ": "hylla", "etikett": "Kaffehylla", "farg": "#8a6849"},
        {"typ": "skylt", "etikett": "KAFÉ · KAFFE", "farg": "#2c221b"},
    ],
    "foodtruck": [
        {"typ": "disk", "etikett": "Serveringslucka", "farg": "#c96f3b"},
        {"typ": "spis", "etikett": "Stekhäll", "farg": "#565d68"},
        {"typ": "lampa", "etikett": "Lucklampa", "farg": "#ffe1a6"},
        {"typ": "skylt", "etikett": "FOODTRUCK", "farg": "#20242f"},
    ],
    "matsal": [
        {"typ": "bank", "etikett": "Serveringsstation", "farg": "#6b4f3a"},
        {"typ": "hylla", "etikett": "Vinhylla", "farg": "#7a5b44"},
        {"typ": "lampa", "etikett": "Matsalslampa", "farg": "#ffe0b3"},
        {"typ": "skylt", "etikett": "MATSAL · MENY", "farg": "#261f1b"},
    ],
}


def _mat_from_wxyz(q: list[float]) -> np.ndarray:
    w, x, y, z = [float(v) for v in q]
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )


def _wxyz_from_mat(R: np.ndarray) -> list[float]:
    tr = float(R[0, 0] + R[1, 1] + R[2, 2])
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    return [round(v / n, 5) for v in (w, x, y, z)]


def _rot_z(rad: float) -> np.ndarray:
    c, s = math.cos(rad), math.sin(rad)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)


def _rot_x(rad: float) -> np.ndarray:
    c, s = math.cos(rad), math.sin(rad)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=float)


def _klona_media_snabbt(media: dict[str, Any] | None) -> dict[str, Any]:
    if not media:
        return {"skarmtext": [], "tal": [], "musik": {"finns": False, "borttagen": False}}
    return {
        "skarmtext": [dict(x, stil=dict(x.get("stil") or {})) for x in media.get("skarmtext", [])],
        "tal": media.get("tal", []),
        "musik": dict(media.get("musik") or {}),
    }


def push_undo(session: dict[str, Any]) -> None:
    snap = {
        "working_scen": klona_scen_snabbt(session.get("working_scen")),
        "tagning_mods": {k: dict(v) for k, v in (session.get("tagning_mods") or {}).items()},
        "working_media": _klona_media_snabbt(session.get("working_media")),
        "miljo_tema": dict(session.get("miljo_tema") or {}),
        "ljud_lage": session.get("ljud_lage", "original"),
        "avsikt": session.get("avsikt", ""),
        "andringar": list(session.get("andringar") or []),
        "tidal_waves": list(session.get("tidal_waves") or []),
    }
    stack = session.setdefault("undo_stack", [])
    stack.append(snap)
    if len(stack) > 40:
        del stack[0]


def pop_undo(session: dict[str, Any]) -> dict[str, Any]:
    stack = session.get("undo_stack") or []
    if stack:
        snap = stack.pop()
        for k, v in snap.items():
            session[k] = v
        session["version"] = int(session.get("version", 1)) + 1
    return kompilera_tillstand(session)


def _rum_granser(scen: dict[str, Any]) -> tuple[float, float, float, float]:
    for o in scen.get("objekt", []):
        if o.get("typ") == "golv":
            px, py = float(o["pos"][0]), float(o["pos"][1])
            mx, my = float(o["matt"][0]) / 2.0, float(o["matt"][1]) / 2.0
            return (px - mx, px + mx, py - my, py + my)
    return (-2.5, 2.5, -2.5, 2.5)


def _hinder_xy(scen: dict[str, Any]) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]:
    """Returnerar (person_cirklar, kamera_cirklar) för kollisionsfri prop-placering."""
    pers_cirklar: list[tuple[float, float, float]] = []
    for spar in (scen.get("rorelse") or {}).values():
        for sp in spar:
            rutor = sp.get("rutor") or []
            if not rutor:
                continue
            mid = rutor[len(rutor) // 2]
            if len(mid) >= 4:
                pers_cirklar.append((mid[1] / 1000.0, mid[2] / 1000.0, 0.62))

    kam_cirklar: list[tuple[float, float, float]] = []
    for t in scen.get("tagningar", []):
        nyck = (t.get("kamera") or {}).get("nycklar") or []
        if nyck:
            k0 = nyck[0]
            kam_cirklar.append((float(k0[1]), float(k0[2]), 0.72))
    return pers_cirklar, kam_cirklar


def _ledig_plats(
    scen: dict[str, Any],
    typ: str,
    matt: list[float],
    nara: str | None = None,
    extra_upptagna: list[tuple[float, float, float]] | None = None,
) -> list[float]:
    """Hittar en ren 3D-position i rummet som varken krockar med personer eller kameran."""
    mall = _PROP_MALLAR.get(typ, _PROP_MALLAR["prop"])
    x0, x1, y0, y1 = _rum_granser(scen)
    pers_c, kam_c = _hinder_xy(scen)
    upptagna = list(pers_c) + list(kam_c) + list(extra_upptagna or [])

    # 1. Om nara anger ett objekt eller en person
    if nara:
        mal_obj = next((o for o in scen.get("objekt", []) if o.get("id") == nara), None)
        if mal_obj:
            px, py, pz = [float(v) for v in mal_obj["pos"]]
            mx, my, mz = [float(v) for v in mal_obj["matt"]]
            if mall.get("placering") == "hojd":
                z_hojd = float(mall.get("z", 1.68))
                return [round(px - 0.35, 3), round(py + 0.35, 3), round(z_hojd, 3)]
            if mall.get("placering") == "bord":
                # Placera vid ett hörn av bordet så bordsprops aldrig skymmer personens ansikte
                kand = [
                    (px - mx * 0.32, py + my * 0.18),
                    (px + mx * 0.32, py - my * 0.18),
                    (px - mx * 0.28, py - my * 0.18),
                ]
                cx, cy = max(
                    kand,
                    key=lambda pt: min(
                        (math.hypot(pt[0] - ux, pt[1] - uy) for ux, uy, _ in pers_c),
                        default=2.0,
                    ),
                )
                return [round(cx, 3), round(cy, 3), round(pz + mz / 2 + matt[2] / 2, 3)]
            return [round(px + 0.85, 3), round(py, 3), round(matt[2] / 2, 3)]
        for pid, spar in (scen.get("rorelse") or {}).items():
            if pid.lower() == str(nara).lower() and spar and spar[0].get("rutor"):
                r0 = spar[0]["rutor"][0]
                px, py = r0[1] / 1000.0, r0[2] / 1000.0
                z_val = float(mall.get("z", matt[2] / 2))
                return [round(px + 0.75, 3), round(py + 0.45, 3), round(z_val, 3)]

    # 2. Bordsplacerade objekt (t.ex. kaffemaskin): ställ ovanpå befintligt bord/disk
    if mall.get("placering") == "bord":
        bord_lista = [
            o for o in scen.get("objekt", []) if o.get("typ") in ("bord", "disk", "bank")
        ]
        if bord_lista:
            b = bord_lista[0]
            bx, by, bz = [float(v) for v in b["pos"]]
            bm_x, _, bm_z = [float(v) for v in b["matt"]]
            off_x = min(bm_x * 0.28, 0.35)
            return [round(bx + off_x, 3), round(by, 3), round(bz + bm_z / 2 + matt[2] / 2, 3)]

    # 3. Skanna ett glest rutnät innanför väggarna, välj första plats med god marginal
    z_val = float(mall.get("z", matt[2] / 2))
    margin_x = max(0.35, matt[0] / 2 + 0.12)
    margin_y = max(0.35, matt[1] / 2 + 0.12)
    xa, xb = x0 + margin_x, x1 - margin_x
    ya, yb = y0 + margin_y, y1 - margin_y
    if xa >= xb:
        xa, xb = -0.8, 0.8
    if ya >= yb:
        ya, yb = -0.8, 0.8

    bast_pos = [round((xa + xb) / 2, 3), round((ya + yb) / 2, 3), round(z_val, 3)]
    bast_min_dist = -1.0
    steg_x = np.linspace(xa, xb, 7)
    steg_y = np.linspace(ya, yb, 7)
    for cx in steg_x:
        for cy in steg_y:
            d_min = min(
                (math.hypot(float(cx) - ux, float(cy) - uy) - ur for ux, uy, ur in upptagna),
                default=2.0,
            )
            if d_min > bast_min_dist:
                bast_min_dist = d_min
                bast_pos = [round(float(cx), 3), round(float(cy), 3), round(z_val, 3)]
            if d_min >= 0.45:
                return [round(float(cx), 3), round(float(cy), 3), round(z_val, 3)]
    return bast_pos


def _synlig_intervall_for_tagningar(scen: dict[str, Any], tagningar: list[str] | None) -> list[list[int]]:
    n_tot = int((scen.get("tidsbas") or {}).get("antal_rutor") or 1)
    if not tagningar:
        return [[0, n_tot]]
    tagn_map = {t["id"]: t["ut"] for t in scen.get("tagningar", [])}
    iv = [list(tagn_map[tid]) for tid in tagningar if tid in tagn_map]
    return iv or [[0, n_tot]]


def _normalisera_tema(tema: str) -> str:
    t = (tema or "").strip().lower()
    t = _TEMA_ALIAS.get(t, t)
    if t not in MILJO_TEMAN:
        raise ValueError(f"Okänt miljötema '{tema}'. Tillgängliga: {', '.join(MILJO_TEMAN)}")
    return t


def _hitta_tagningar(session: dict[str, Any], tagning_id: str | None) -> list[str]:
    alla = [t["id"] for t in sorted(session["tagning_mods"].values(), key=lambda x: x["nr"])]
    if not tagning_id or tagning_id == "alla":
        return alla
    if tagning_id in session["tagning_mods"]:
        return [tagning_id]
    raise ValueError(f"Okänd tagning '{tagning_id}'.")


def _registrera_andring(
    session: dict[str, Any],
    op: str,
    params: dict[str, Any],
    beskrivning: str,
    kalla: str,
) -> None:
    lista = session.setdefault("andringar", [])
    lista.append(
        {
            "nr": len(lista) + 1,
            "op": op,
            "params": params,
            "beskrivning": beskrivning,
            "kalla": kalla,
            "tid": time.strftime("%H:%M:%S"),
        }
    )
    session["version"] = int(session.get("version", 1)) + 1


def utfor_operation(
    session: dict[str, Any],
    op: str,
    params: dict[str, Any] | None = None,
    *,
    kalla: str = "snabb",
    push_undo_snap: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Kör en deterministisk operation (<50 ms) med K7-spärr och K5-kontroll."""
    t0 = time.perf_counter()
    p = dict(params or {})
    op_namn = (op or "").strip()
    klipp_id = session["klipp"]["id"]
    sid = session["session_id"]

    # 1. K7-spärr
    try:
        kontrollera_operation(op_namn, p)
    except K7StoppError as exc:
        logga_k7("blockerad", sid, klipp_id, op_namn, p, ok=False, detalj=str(exc))
        raise

    if push_undo_snap:
        push_undo(session)

    har_3d = bool(session["klipp"].get("har_3d") and session.get("working_scen") is not None)
    scen = session.get("working_scen")
    beskrivning = ""

    try:
        if op_namn == "byt_miljo":
            tema_id = _normalisera_tema(str(p.get("tema") or "original"))
            tema_mall = copy.deepcopy(MILJO_TEMAN[tema_id])
            session["miljo_tema"] = tema_mall
            tagn_filter = p.get("tagningar")
            if har_3d and scen is not None:
                scen["objekt"] = [o for o in scen.get("objekt", []) if not str(o.get("id", "")).startswith("miljo_")]
                if tema_id != "original":
                    syn_iv = _synlig_intervall_for_tagningar(scen, tagn_filter)
                    extra_upptagna: list[tuple[float, float, float]] = []
                    for i, pr in enumerate(_MILJO_PROPS.get(tema_id, []), 1):
                        typ = pr["typ"]
                        mall = _PROP_MALLAR.get(typ, _PROP_MALLAR["prop"])
                        matt = list(mall["matt"])
                        pos = _ledig_plats(scen, typ, matt, extra_upptagna=extra_upptagna)
                        extra_upptagna.append((pos[0], pos[1], max(matt[0], matt[1]) * 0.55))
                        scen["objekt"].append(
                            {
                                "id": f"miljo_{tema_id}_{i}",
                                "bas": f"miljo_{typ}",
                                "typ": typ,
                                "etikett": pr["etikett"],
                                "pos": pos,
                                "rot": [0.0, 0.0, 0.0],
                                "matt": matt,
                                "farg": pr["farg"],
                                "status": "miljo_tema",
                                "rum": "gemensamt",
                                "synlig_ut": copy.deepcopy(syn_iv),
                            }
                        )
            beskrivning = f"Miljötema ändrat till {tema_mall['namn']}" + (
                f" ({', '.join(tagn_filter)})" if tagn_filter else ""
            )

        elif op_namn == "kamera_justera":
            if not har_3d or scen is None:
                raise ValueError("Klippet saknar 3D-scen för kamerajustering.")
            mal_ids = _hitta_tagningar(session, p.get("tagning_id"))
            zoom = p.get("zoom")
            pan_deg = float(p.get("pan_deg") or 0.0)
            tilt_deg = float(p.get("tilt_deg") or 0.0)
            stabilisera = bool(p.get("stabilisera"))
            hand_energi = p.get("handhallen_energi")

            R_delta_z = _rot_z(math.radians(pan_deg)) if abs(pan_deg) > 1e-4 else None
            R_delta_x = _rot_x(math.radians(tilt_deg)) if abs(tilt_deg) > 1e-4 else None

            for t in scen.get("tagningar", []):
                if t["id"] not in mal_ids:
                    continue
                kam = t["kamera"]
                nycklar = copy.deepcopy(kam["nycklar"])
                a0, b0 = t["ut"]

                # Om handhållen energi önskas på statisk kamera, expandera till täta nycklar
                if hand_energi is not None and float(hand_energi) > 0.0 and (kam.get("statisk") or len(nycklar) < 3):
                    bas_k = nycklar[0]
                    nycklar = [[u] + list(bas_k[1:]) for u in range(a0, b0, 2)]
                    if nycklar[-1][0] != b0 - 1:
                        nycklar.append([b0 - 1] + list(bas_k[1:]))
                    kam["statisk"] = False

                if zoom is not None:
                    zf = max(0.35, min(3.0, float(zoom)))
                    for k in nycklar:
                        k[8] = round(max(14.0, min(150.0, float(k[8]) * zf)), 2)

                if R_delta_z is not None or R_delta_x is not None:
                    for k in nycklar:
                        R = _mat_from_wxyz(k[4:8])
                        if R_delta_z is not None:
                            R = R_delta_z @ R
                        if R_delta_x is not None:
                            R = R @ R_delta_x
                        q_ny = _wxyz_from_mat(R)
                        k[4:8] = q_ny

                if stabilisera and len(nycklar) >= 3:
                    arr = np.array(nycklar, dtype=float)
                    sm = arr.copy()
                    w = min(9, len(arr))
                    halv = w // 2
                    for idx in range(len(arr)):
                        lo, hi = max(0, idx - halv), min(len(arr), idx + halv + 1)
                        sm[idx, 1:4] = arr[lo:hi, 1:4].mean(axis=0)
                        q_mean = arr[lo:hi, 4:8].mean(axis=0)
                        qn = float(np.linalg.norm(q_mean)) or 1.0
                        sm[idx, 4:8] = q_mean / qn
                    nycklar = [[int(row[0])] + [round(float(v), 5) for v in row[1:]] for row in sm]

                if hand_energi is not None and float(hand_energi) > 0.0:
                    e = max(0.0, min(1.0, float(hand_energi)))
                    seed = sum(ord(ch) for ch in t["id"]) * 0.7
                    for k in nycklar:
                        tt = (k[0] - a0) / max(1.0, float(scen["tidsbas"]["fps"]))
                        k[1] = round(k[1] + e * 0.016 * math.sin(tt * 3.1 + seed), 4)
                        k[2] = round(k[2] + e * 0.012 * math.cos(tt * 2.4 + seed), 4)
                        k[3] = round(k[3] + e * 0.010 * math.sin(tt * 4.3 + seed * 1.3), 4)
                        dp = math.radians(e * 1.2 * math.sin(tt * 2.9 + seed))
                        dt = math.radians(e * 0.9 * math.cos(tt * 3.7 + seed))
                        R = _rot_z(dp) @ _mat_from_wxyz(k[4:8]) @ _rot_x(dt)
                        k[4:8] = _wxyz_from_mat(R)

                kam["nycklar"] = nycklar

            delar = []
            if zoom is not None:
                delar.append(f"zoom {float(zoom):.2f}×")
            if abs(pan_deg) > 1e-3:
                delar.append(f"pan {pan_deg:+.1f}°")
            if abs(tilt_deg) > 1e-3:
                delar.append(f"tilt {tilt_deg:+.1f}°")
            if stabilisera:
                delar.append("stabiliserad")
            if hand_energi is not None:
                delar.append(f"handhållen {float(hand_energi):.2f}")
            beskrivning = f"Kamera {', '.join(mal_ids)}: {', '.join(delar) or 'justerad'}"

        elif op_namn == "objekt_lagg_till":
            if not har_3d or scen is None:
                raise ValueError("Klippet saknar 3D-scen för objektplacering.")
            typ = str(p.get("typ") or "prop").strip().lower()
            mall = _PROP_MALLAR.get(typ, _PROP_MALLAR["prop"])
            matt = [float(v) for v in (p.get("matt") or mall["matt"])]
            farg = str(p.get("farg") or mall["farg"])
            etikett = (p.get("etikett") or p.get("text") or typ.capitalize()).strip()
            pos = [float(v) for v in p["pos"]] if p.get("pos") else _ledig_plats(scen, typ, matt, nara=p.get("nara"))
            syn_iv = _synlig_intervall_for_tagningar(scen, p.get("tagningar"))
            existing_ids = {o["id"] for o in scen.get("objekt", [])}
            idx = 1
            while f"prop_{typ}_{idx}" in existing_ids:
                idx += 1
            ny_id = f"prop_{typ}_{idx}"
            scen["objekt"].append(
                {
                    "id": ny_id,
                    "bas": typ,
                    "typ": typ,
                    "etikett": etikett,
                    "pos": [round(v, 4) for v in pos],
                    "rot": [0.0, 0.0, 0.0],
                    "matt": [round(v, 4) for v in matt],
                    "farg": farg,
                    "status": "cm_tillagd",
                    "rum": "gemensamt",
                    "synlig_ut": syn_iv,
                }
            )
            beskrivning = f"Lade till {typ} '{etikett}' ({ny_id})"

        elif op_namn == "objekt_byt":
            if not har_3d or scen is None:
                raise ValueError("Klippet saknar 3D-scen.")
            oid = str(p.get("id") or "")
            obj = next((o for o in scen.get("objekt", []) if o.get("id") == oid), None)
            if not obj:
                raise ValueError(f"Objektet '{oid}' hittades inte.")
            if p.get("typ"):
                obj["typ"] = str(p["typ"]).lower()
            if p.get("etikett") is not None:
                obj["etikett"] = p["etikett"]
            if p.get("farg"):
                obj["farg"] = str(p["farg"])
            if p.get("matt"):
                obj["matt"] = [float(v) for v in p["matt"]]
            beskrivning = f"Uppdaterade objekt {oid}"

        elif op_namn == "objekt_ta_bort":
            if not har_3d or scen is None:
                raise ValueError("Klippet saknar 3D-scen.")
            oid = str(p.get("id") or "")
            fore_n = len(scen.get("objekt", []))
            scen["objekt"] = [o for o in scen.get("objekt", []) if o.get("id") != oid]
            if len(scen["objekt"]) == fore_n:
                raise ValueError(f"Objektet '{oid}' hittades inte.")
            beskrivning = f"Tog bort objekt {oid}"

        elif op_namn == "objekt_flytta":
            if not har_3d or scen is None:
                raise ValueError("Klippet saknar 3D-scen.")
            oid = str(p.get("id") or "")
            obj = next((o for o in scen.get("objekt", []) if o.get("id") == oid), None)
            if not obj:
                raise ValueError(f"Objektet '{oid}' hittades inte.")
            dx, dy, dz = float(p.get("dx") or 0.0), float(p.get("dy") or 0.0), float(p.get("dz") or 0.0)
            vrid = math.radians(float(p.get("vrid_deg") or 0.0))
            obj["pos"] = [round(obj["pos"][0] + dx, 4), round(obj["pos"][1] + dy, 4), round(obj["pos"][2] + dz, 4)]
            obj["rot"][2] = round(float(obj["rot"][2]) + vrid, 4)
            beskrivning = f"Flyttade {oid} ({dx:+.2f}, {dy:+.2f}, {dz:+.2f} m)"

        elif op_namn == "person_placering":
            if not har_3d or scen is None:
                raise ValueError("Klippet saknar 3D-scen.")
            pid = str(p.get("person_id") or "")
            if pid not in (scen.get("rorelse") or {}):
                raise ValueError(f"Personen '{pid}' finns inte i scenen.")
            tagn_filter = set(_hitta_tagningar(session, p.get("tagning_id")))
            dx, dy, dz = float(p.get("dx") or 0.0), float(p.get("dy") or 0.0), float(p.get("dz") or 0.0)
            vrid_rad = math.radians(float(p.get("vrid_deg") or 0.0))
            flytta_med_kam = bool(p.get("flytta_med_kamera", True))

            dx_mm, dy_mm, dz_mm = int(round(dx * 1000)), int(round(dy * 1000)), int(round(dz * 1000))
            flyttade_tagn: set[str] = set()
            ankare_xy: tuple[float, float] | None = None

            for sp in scen["rorelse"][pid]:
                if sp.get("tagning") not in tagn_filter:
                    continue
                flyttade_tagn.add(sp["tagning"])
                rutor = sp["rutor"]
                if not rutor:
                    continue
                arr = np.array(rutor, dtype=float)
                if abs(vrid_rad) > 1e-5:
                    cx = float(np.median(arr[:, 1]))
                    cy = float(np.median(arr[:, 2]))
                    ankare_xy = (cx / 1000.0, cy / 1000.0)
                    c, s = math.cos(vrid_rad), math.sin(vrid_rad)
                    n_j = (arr.shape[1] - 1) // 3
                    for j in range(n_j):
                        jx = arr[:, 1 + 3 * j] - cx
                        jy = arr[:, 2 + 3 * j] - cy
                        arr[:, 1 + 3 * j] = cx + c * jx - s * jy
                        arr[:, 2 + 3 * j] = cy + s * jx + c * jy
                arr[:, 1::3] += dx_mm
                arr[:, 2::3] += dy_mm
                arr[:, 3::3] += dz_mm
                sp["rutor"] = [[int(round(v)) for v in row] for row in arr]

            if flytta_med_kam and flyttade_tagn:
                R_z = _rot_z(vrid_rad) if abs(vrid_rad) > 1e-5 else None
                for t in scen.get("tagningar", []):
                    if t["id"] not in flyttade_tagn:
                        continue
                    for k in t["kamera"]["nycklar"]:
                        if R_z is not None and ankare_xy is not None:
                            vx, vy = k[1] - ankare_xy[0], k[2] - ankare_xy[1]
                            c, s = math.cos(vrid_rad), math.sin(vrid_rad)
                            k[1] = ankare_xy[0] + c * vx - s * vy
                            k[2] = ankare_xy[1] + s * vx + c * vy
                            k[4:8] = _wxyz_from_mat(R_z @ _mat_from_wxyz(k[4:8]))
                        k[1] = round(k[1] + dx, 4)
                        k[2] = round(k[2] + dy, 4)
                        k[3] = round(k[3] + dz, 4)

            # Flytta ev. associerad stol
            stol = next((o for o in scen.get("objekt", []) if o.get("id") == f"stol_{pid}"), None)
            if stol and flyttade_tagn:
                stol["pos"] = [round(stol["pos"][0] + dx, 4), round(stol["pos"][1] + dy, 4), round(stol["pos"][2] + dz, 4)]
                stol["rot"][2] = round(float(stol["rot"][2]) + vrid_rad, 4)

            beskrivning = f"Flyttade person {pid} ({dx:+.2f}, {dy:+.2f}, {dz:+.2f} m, vrid {float(p.get('vrid_deg') or 0):+.0f}°)"

        elif op_namn == "tidslinje_korta":
            tid = str(p.get("tagning_id") or "")
            if tid not in session["tagning_mods"]:
                raise ValueError(f"Okänd tagning '{tid}'.")
            tm = session["tagning_mods"][tid]
            oa, ob = tm["orig_fran_s"], tm["orig_till_s"]
            orig_dur = ob - oa
            fran_in = p.get("fran_s")
            till_in = p.get("till_s")
            ny_len = p.get("ny_langd_s")

            if ny_len is not None and fran_in is None and till_in is None:
                mal_dur = max(0.25, min(orig_dur, float(ny_len)))
                ny_a = tm["korta_fran_s"]
                ny_b = min(ob, ny_a + mal_dur)
                if ny_b - ny_a < mal_dur:
                    ny_a = max(oa, ny_b - mal_dur)
            else:
                if fran_in is not None:
                    f_val = float(fran_in)
                    ny_a = f_val if (oa > 0.4 and f_val >= oa - 0.05) else (oa + f_val)
                else:
                    ny_a = tm["korta_fran_s"]
                if till_in is not None:
                    t_val = float(till_in)
                    ny_b = t_val if (oa > 0.4 and t_val >= oa - 0.05) else (oa + t_val)
                else:
                    ny_b = tm["korta_till_s"]
                ny_a = max(oa, min(ob - 0.25, ny_a))
                ny_b = max(ny_a + 0.25, min(ob, ny_b))

            tm["korta_fran_s"] = round(ny_a, 4)
            tm["korta_till_s"] = round(ny_b, 4)
            beskrivning = f"Kortade {tid} till {ny_b - ny_a:.2f} s (källa {ny_a:.2f}–{ny_b:.2f} s)"

        elif op_namn == "tidslinje_stryk":
            tid = str(p.get("tagning_id") or "")
            if tid not in session["tagning_mods"]:
                raise ValueError(f"Okänd tagning '{tid}'.")
            tm = session["tagning_mods"][tid]
            ater = p.get("aterstall")
            ny_stryk = (not tm["stryk"]) if ater is None else (not bool(ater))
            aktiva = [t for t in session["tagning_mods"].values() if not t["stryk"]]
            if ny_stryk and len(aktiva) <= 1 and tm["id"] == aktiva[0]["id"]:
                raise ValueError("Kan inte stryka den sista aktiva tagningen i sekvensen.")
            tm["stryk"] = ny_stryk
            beskrivning = f"{'Återställde' if not ny_stryk else 'Strök'} tagning {tid}"

        elif op_namn == "tidslinje_tempo":
            mal_ids = _hitta_tagningar(session, p.get("tagning_id"))
            tempo = max(0.35, min(3.0, float(p.get("tempo") or 1.0)))
            for tid in mal_ids:
                session["tagning_mods"][tid]["tempo"] = round(tempo, 3)
            beskrivning = f"Tempo {tempo:.2f}× på {', '.join(mal_ids)}"

        elif op_namn == "tidslinje_paus":
            tid = str(p.get("tagning_id") or "")
            if tid not in session["tagning_mods"]:
                raise ValueError(f"Okänd tagning '{tid}'.")
            sek = max(0.0, min(5.0, float(p.get("sekunder") or 0.0)))
            session["tagning_mods"][tid]["paus_slut_s"] = round(sek, 3)
            beskrivning = f"Slutpaus på {tid}: {sek:.2f} s"

        elif op_namn == "skarmtext_byt":
            xid = str(p.get("id") or "")
            ny_txt = str(p.get("text") or "").strip()
            if not ny_txt:
                raise ValueError("Ny skärmtext får inte vara tom.")
            lista = session["working_media"]["skarmtext"]
            traff = next((x for x in lista if not x.get("borttagen") and x["id"] == xid), None)
            if not traff and xid.isdigit():
                idx_num = int(xid) - 1
                akt = [x for x in lista if not x.get("borttagen")]
                if 0 <= idx_num < len(akt):
                    traff = akt[idx_num]
            if not traff:
                raise ValueError(f"Skärmtext '{xid}' hittades inte.")
            traff["text"] = ny_txt
            traff["andrad"] = True
            beskrivning = f"Ändrade skärmtext {traff['id']} → \"{ny_txt}\""

        elif op_namn == "skarmtext_lagg_till":
            txt = str(p.get("text") or "").strip()
            if not txt:
                raise ValueError("Skärmtext får inte vara tom.")
            pos = str(p.get("position") or "mitt").lower()
            if pos not in ("ovre", "mitt", "nedre"):
                pos = "mitt"
            lista = session["working_media"]["skarmtext"]
            existing = {x["id"] for x in lista}
            idx = len(lista) + 1
            while f"ny_{idx}" in existing:
                idx += 1
            nid = f"ny_{idx}"
            tagn_id = p.get("tagning_id")
            fran_s = float(p.get("fran_s") or 0.0)
            till_s = max(fran_s + 0.25, float(p.get("till_s") or fran_s + 2.5))
            cy = 0.18 if pos == "ovre" else (0.78 if pos == "nedre" else 0.48)
            post = {
                "id": nid,
                "text": txt,
                "text_original": "",
                "fran_s": round(fran_s, 3),
                "till_s": round(till_s, 3),
                "box": [0.1, round(cy - 0.05, 3), 0.9, round(cy + 0.05, 3)],
                "typ": "overlag",
                "stil": {
                    "position": pos,
                    "glyffarg": "#ffffff",
                    "platta": False,
                    "bakgrund": None,
                    "kontur": "#000000",
                    "versaler": False,
                    "radhojd": 0.036,
                },
                "andrad": False,
                "ny": True,
                "manuell_ny_tid": True,
            }
            if tagn_id and tagn_id in session["tagning_mods"]:
                tm = session["tagning_mods"][tagn_id]
                post["tagning_id"] = tagn_id
                post["rel_fran_s"] = max(0.0, fran_s)
                post["rel_till_s"] = max(0.25, till_s - fran_s if p.get("fran_s") is not None and p.get("till_s") is not None else (tm["orig_till_s"] - tm["orig_fran_s"]))
            lista.append(post)
            beskrivning = f"Lade till skärmtext {nid}: \"{txt}\""

        elif op_namn == "skarmtext_ta_bort":
            xid = str(p.get("id") or "")
            lista = session["working_media"]["skarmtext"]
            traff = next((x for x in lista if not x.get("borttagen") and x["id"] == xid), None)
            if not traff:
                raise ValueError(f"Skärmtext '{xid}' hittades inte.")
            traff["borttagen"] = True
            beskrivning = f"Tog bort skärmtext {xid}"

        elif op_namn == "ljud_musik":
            lage = str(p.get("lage") or "original").strip().lower()
            if lage not in ("original", "tal", "tyst"):
                raise ValueError(f"Ogiltigt ljudläge '{lage}'. Välj original, tal eller tyst.")
            session["ljud_lage"] = lage
            if lage == "tal" and not session["klipp"].get("har_tal"):
                beskrivning = "Ljudläge satt till 'tal' (obs: separerat talspår saknas ännu för detta klipp)"
            else:
                beskrivning = f"Ljudläge satt till '{lage}'"

        elif op_namn == "manus_anteckning":
            mal_ids = _hitta_tagningar(session, p.get("tagning_id"))
            txt = (p.get("text") or "").strip()
            rep_ny = p.get("replik_ny")
            kansla = p.get("kansla")
            for tid in mal_ids:
                tm = session["tagning_mods"][tid]
                if txt:
                    tm["anteckning"] = txt
                if rep_ny is not None:
                    tm["replik_ny"] = str(rep_ny).strip() or None
                if kansla is not None:
                    tm["kansla"] = str(kansla).strip() or None
            beskrivning = f"Manusanteckning på {', '.join(mal_ids)}: {txt or rep_ny or kansla or 'uppdaterad'}"

        elif op_namn == "aterstall":
            session["working_scen"] = klona_scen_snabbt(session.get("orig_scen"))
            session["tagning_mods"] = {k: dict(v) for k, v in (session.get("orig_tagning_mods") or {}).items()}
            session["working_media"] = _klona_media_snabbt(session.get("orig_media"))
            session["miljo_tema"] = dict(MILJO_TEMAN["original"])
            session["ljud_lage"] = "original"
            session["andringar"] = []
            session["tidal_waves"] = []
            session["version"] = int(session.get("version", 1)) + 1
            beskrivning = "Återställde scen och tidslinje till 1:1 original"

        else:
            raise ValueError(f"Okänd operation '{op_namn}'.")
    except Exception:
        if push_undo_snap and session.get("undo_stack"):
            session["undo_stack"].pop()
        raise

    if op_namn != "aterstall":
        _registrera_andring(session, op_namn, p, beskrivning, kalla)

    tillstand = kompilera_tillstand(session)
    varn = next(
        (v for v in (tillstand.get("k5") or {}).get("varningar", []) if v.get("op") == op_namn),
        None,
    )
    ms = round((time.perf_counter() - t0) * 1000, 1)
    logga_k7(
        "operation",
        sid,
        klipp_id,
        op_namn,
        p,
        ok=True,
        detalj=beskrivning,
        extra={"kalla": kalla, "ms": ms, "k5_varning": varn},
    )
    return tillstand, {
        "ok": True,
        "op": op_namn,
        "beskrivning": beskrivning,
        "k5_varning": varn,
        "ms": ms,
    }
