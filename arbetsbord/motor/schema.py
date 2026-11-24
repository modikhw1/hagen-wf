"""Datakontrakt (`arbetsbord/1`), miljöteman och tidsomräkning mellan källtid och ny redigerad tidslinje."""
from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any

ROT = Path(__file__).resolve().parents[2]
ARBETSBORD_DIR = ROT / "arbetsbord"
UT_DIR = ARBETSBORD_DIR / "ut"
DATA_DIR = ARBETSBORD_DIR / "data"
MEDIELAGER_ARBETSBORD_DIR = DATA_DIR / "medielager"
MEDIELAGER_FALLBACK_DIR = ROT / "motpart" / "runda-3-opus" / "D-medielager" / "lager"
MEDIELAGER_STAMMAR_CACHE = ROT / "motpart" / "runda-3-opus" / "D-medielager" / "_cache" / "stammar"
CACHE_AUDIO_DIR = DATA_DIR / "cache_audio"
CACHE_VIDEO_DIR = DATA_DIR / "cache_video"
REGR5_DIR = ROT / "motpart" / "runda-3-opus" / "B-nasta-klipp" / "ut" / "regr5"
FORVARLD_KARNA_DIR = ROT / "forvarld_karna" / "ut"
BARLISTOR_DIR = ROT / "motpart" / "runda-3-opus" / "C-cm-mening" / "ut" / "barlistor"
KLIPP_JSONL = ROT / "byggsten" / "hand" / "ut" / "klipp.jsonl"
ENV_LOCAL = ROT / "video" / ".env.local"

K7_LOGG_FIL = UT_DIR / "k7_logg.jsonl"
FEEDBACK_LOGG_FIL = UT_DIR / "feedback_logg.jsonl"

SCHEMA_VERSION = "arbetsbord/1"

UTVALDA_KUNDER = [
    "kappabar",
    "basso.social",
    "kennysgelato2.0",
    "fratelli.stockhol",
    "anettesrestaurang",
]

MILJO_TEMAN: dict[str, dict[str, Any]] = {
    "original": {
        "id": "original",
        "namn": "Original",
        "bakgrund": "#151820",
        "golv": None,
        "vagg": None,
        "ljus": {
            "nyckel_farg": "#fff8ee",
            "nyckel_styrka": 2.1,
            "fyll_farg": "#b8d0f5",
            "fyll_styrka": 0.75,
            "omgivning_farg": "#dce4f2",
            "omgivning_styrka": 0.85,
        },
        "dimma": None,
    },
    "kok": {
        "id": "kok",
        "namn": "Kök",
        "bakgrund": "#1a2029",
        "golv": "#575c64",
        "vagg": "#cfd6de",
        "ljus": {
            "nyckel_farg": "#ffffff",
            "nyckel_styrka": 2.35,
            "fyll_farg": "#cce2ff",
            "fyll_styrka": 0.9,
            "omgivning_farg": "#e8eff7",
            "omgivning_styrka": 0.95,
        },
        "dimma": None,
    },
    "bar": {
        "id": "bar",
        "namn": "Bar",
        "bakgrund": "#10131d",
        "golv": "#3e2d23",
        "vagg": "#2a3247",
        "ljus": {
            "nyckel_farg": "#ffdca8",
            "nyckel_styrka": 1.95,
            "fyll_farg": "#85a8f0",
            "fyll_styrka": 0.7,
            "omgivning_farg": "#9aa8c7",
            "omgivning_styrka": 0.65,
        },
        "dimma": {"farg": "#10131d", "nara": 9.0, "borta": 24.0},
    },
    "uteservering": {
        "id": "uteservering",
        "namn": "Uteservering",
        "bakgrund": "#273b4f",
        "golv": "#8e877a",
        "vagg": "#b9c7d4",
        "ljus": {
            "nyckel_farg": "#fff2d6",
            "nyckel_styrka": 2.55,
            "fyll_farg": "#b8dcff",
            "fyll_styrka": 0.95,
            "omgivning_farg": "#e3eef8",
            "omgivning_styrka": 1.05,
        },
        "dimma": {"farg": "#273b4f", "nara": 14.0, "borta": 38.0},
    },
    "kafe": {
        "id": "kafe",
        "namn": "Kafé",
        "bakgrund": "#201b17",
        "golv": "#7b6048",
        "vagg": "#dfd3c1",
        "ljus": {
            "nyckel_farg": "#ffe9c9",
            "nyckel_styrka": 2.15,
            "fyll_farg": "#d4dfff",
            "fyll_styrka": 0.8,
            "omgivning_farg": "#f2e7d8",
            "omgivning_styrka": 0.92,
        },
        "dimma": None,
    },
    "foodtruck": {
        "id": "foodtruck",
        "namn": "Foodtruck",
        "bakgrund": "#151923",
        "golv": "#353940",
        "vagg": "#c96f3b",
        "ljus": {
            "nyckel_farg": "#ffe6be",
            "nyckel_styrka": 2.3,
            "fyll_farg": "#96c2ff",
            "fyll_styrka": 0.8,
            "omgivning_farg": "#d8dfeb",
            "omgivning_styrka": 0.85,
        },
        "dimma": {"farg": "#151923", "nara": 11.0, "borta": 30.0},
    },
    "matsal": {
        "id": "matsal",
        "namn": "Matsal",
        "bakgrund": "#1a1614",
        "golv": "#6a4f38",
        "vagg": "#c6bbb0",
        "ljus": {
            "nyckel_farg": "#ffe4bc",
            "nyckel_styrka": 2.05,
            "fyll_farg": "#c2d4f0",
            "fyll_styrka": 0.78,
            "omgivning_farg": "#ebe0d2",
            "omgivning_styrka": 0.88,
        },
        "dimma": None,
    },
}


def slerp_wxyz(q0: list[float], q1: list[float], alpha: float) -> list[float]:
    """Sfärisk linjär interpolation av kvaternioner i ordningen [qw, qx, qy, qz]."""
    w0, x0, y0, z0 = q0
    w1, x1, y1, z1 = q1
    dot = w0 * w1 + x0 * x1 + y0 * y1 + z0 * z1
    if dot < 0.0:
        w1, x1, y1, z1 = -w1, -x1, -y1, -z1
        dot = -dot
    if dot > 0.9995:
        out = [
            w0 + alpha * (w1 - w0),
            x0 + alpha * (x1 - x0),
            y0 + alpha * (y1 - y0),
            z0 + alpha * (z1 - z0),
        ]
        n = math.sqrt(sum(c * c for c in out)) or 1.0
        return [round(c / n, 5) for c in out]
    dot = max(-1.0, min(1.0, dot))
    theta_0 = math.acos(dot)
    sin_0 = math.sin(theta_0)
    theta = theta_0 * alpha
    s0 = math.sin(theta_0 - theta) / sin_0
    s1 = math.sin(theta) / sin_0
    return [
        round(s0 * w0 + s1 * w1, 5),
        round(s0 * x0 + s1 * x1, 5),
        round(s0 * y0 + s1 * y1, 5),
        round(s0 * z0 + s1 * z1, 5),
    ]


def _interp_nycklar(nycklar: list[list[float]], u_orig: float) -> list[float]:
    """Interpolerar kameranyckel [u, x, y, z, qw, qx, qy, qz, lins_mm] vid källruta u_orig."""
    if len(nycklar) == 1 or u_orig <= nycklar[0][0]:
        return list(nycklar[0][1:])
    if u_orig >= nycklar[-1][0]:
        return list(nycklar[-1][1:])
    for i in range(len(nycklar) - 1):
        a, b = nycklar[i], nycklar[i + 1]
        if a[0] <= u_orig <= b[0]:
            span = b[0] - a[0]
            alpha = (u_orig - a[0]) / span if span > 1e-9 else 0.0
            pos = [round(a[j] + alpha * (b[j] - a[j]), 4) for j in (1, 2, 3)]
            quat = slerp_wxyz(a[4:8], b[4:8], alpha)
            lins = round(a[8] + alpha * (b[8] - a[8]), 3)
            return pos + quat + [lins]
    return list(nycklar[-1][1:])


def _interp_rorelse_rad(rutor: list[list[int]], u_orig: float) -> list[int]:
    """Linjär interpolation av skelettets hel-mm-leder vid godtycklig källruta."""
    if len(rutor) == 1 or u_orig <= rutor[0][0]:
        return list(rutor[0][1:])
    if u_orig >= rutor[-1][0]:
        return list(rutor[-1][1:])
    lo, hi = 0, len(rutor) - 1
    while lo + 1 < hi:
        mid = (lo + hi) >> 1
        if rutor[mid][0] <= u_orig:
            lo = mid
        else:
            hi = mid
    a, b = rutor[lo], rutor[hi]
    span = b[0] - a[0]
    alpha = (u_orig - a[0]) / span if span > 1e-9 else 0.0
    if alpha <= 1e-6:
        return list(a[1:])
    if alpha >= 1.0 - 1e-6:
        return list(b[1:])
    return [int(round(va + alpha * (vb - va))) for va, vb in zip(a[1:], b[1:])]


def _sla_ihop_intervall(iv_lista: list[list[int]]) -> list[list[int]]:
    if not iv_lista:
        return []
    sorterad = sorted((int(a), int(b)) for a, b in iv_lista if b > a)
    if not sorterad:
        return []
    ut = [[sorterad[0][0], sorterad[0][1]]]
    for a, b in sorterad[1:]:
        if a <= ut[-1][1]:
            ut[-1][1] = max(ut[-1][1], b)
        else:
            ut.append([a, b])
    return ut


def _avbilda_tid_segment(
    orig_fran: float,
    orig_till: float,
    spela_seg: list[dict[str, Any]],
) -> list[tuple[float, float]]:
    """Klipp och avbilda ett originaltidsintervall mot alla aktiva 'spela'-segment."""
    ut: list[tuple[float, float]] = []
    for seg in spela_seg:
        ov_a = max(orig_fran, seg["orig_fran_s"])
        ov_b = min(orig_till, seg["orig_till_s"])
        if ov_b - ov_a <= 0.02:
            continue
        tempo = max(0.05, float(seg["tempo"]))
        ny_a = seg["ny_fran_s"] + (ov_a - seg["orig_fran_s"]) / tempo
        ny_b = seg["ny_fran_s"] + (ov_b - seg["orig_fran_s"]) / tempo
        if ny_b > ny_a + 0.01:
            ut.append((round(ny_a, 4), round(ny_b, 4)))
    return ut


def berakna_k5_varningar(session: dict[str, Any], tagningar_ut: list[dict[str, Any]], media_ut: dict[str, Any]) -> list[dict[str, Any]]:
    """Beräknar aktuella K5-varningar utifrån bärlistan och tillståndets ändringar."""
    k5_poster = session.get("k5_poster") or []
    bar_poster = [p for p in k5_poster if p.get("roll") == "bar"]
    tagn_by_id = {t["id"]: t for t in tagningar_ut}
    aktiva_skarm = {x["id"]: x for x in media_ut.get("skarmtext", [])}
    orig_skarm = {x["id"]: x for x in (session.get("orig_media") or {}).get("skarmtext", [])}
    ljud_lage = session.get("ljud_lage", "original")
    varningar: list[dict[str, Any]] = []
    sedda: set[str] = set()

    def lagg_till(niva: str, text: str, op: str = "kontroll"):
        nyckel = f"{niva}:{text}"
        if nyckel not in sedda:
            sedda.add(nyckel)
            varningar.append({"niva": niva, "text": text, "op": op})

    # Kontrollera strukna eller hårt kortade tagningar som bär meningen
    for tg in tagningar_ut:
        sid = tg["id"]
        orig_dur = max(0.1, tg["orig_till_s"] - tg["orig_fran_s"])
        ny_dur = (tg["ny_till_s"] - tg["ny_fran_s"]) if tg["ny_fran_s"] is not None else 0.0
        for p in bar_poster:
            refs = p.get("tagningar") or []
            if sid not in refs:
                continue
            if tg["stryk"]:
                lagg_till(
                    "varning",
                    f"Tagning {sid} är struken men bär enligt K5 ('{p['namn']}': {p.get('varfor') or 'bärande del'}).",
                    "tidslinje_stryk",
                )
            elif p.get("typ") in ("scen", "handling", "takt") and ny_dur < orig_dur * 0.5:
                lagg_till(
                    "info",
                    f"Tagning {sid} är kortad till {ny_dur:.1f} s (från {orig_dur:.1f} s) — kontrollera att '{p['namn']}' hinner fram.",
                    "tidslinje_korta",
                )

    # Kontrollera borttagna/ändrade bärande skärmtexter
    for p in bar_poster:
        if p.get("typ") != "text":
            continue
        for mid in p.get("medie") or []:
            if mid in orig_skarm and mid not in aktiva_skarm:
                lagg_till(
                    "varning",
                    f"Skärmtext {mid} ('{orig_skarm[mid]['text']}') bär meningen men är dold/borttagen.",
                    "skarmtext_ta_bort",
                )

    # Kontrollera ljudläge mot dialog/musik
    if ljud_lage == "tyst":
        har_tal_bar = any(p.get("typ") in ("replik", "person", "text") for p in bar_poster) and bool(
            (session.get("orig_media") or {}).get("tal")
        )
        if har_tal_bar:
            lagg_till("varning", "Ljudet är satt till tyst trots att klippet bär talad dialog — skärmtext måste täcka replikerna.", "ljud_musik")
    elif ljud_lage == "tal":
        musik_bar = any("musik" in (p.get("namn", "") + " " + (p.get("varfor") or "")).lower() for p in bar_poster)
        if musik_bar:
            lagg_till("info", "Endast tal är aktivt: musiken är dämpad — kontrollera om rytm/vändning behöver ny musik.", "ljud_musik")

    # Kontrollera temaändring mot bärande miljö/möbel
    tema_id = (session.get("miljo_tema") or {}).get("id", "original")
    if tema_id != "original":
        mobel_bar = [p["namn"] for p in bar_poster if p.get("typ") in ("mobel", "bakgrund", "liggare") and any(k in p.get("namn", "").lower() for k in ("disk", "bord", "bar", "glass"))]
        if mobel_bar:
            lagg_till(
                "info",
                f"Miljön är ändrad till '{tema_id}'. Bärande rumsrelation ({', '.join(mobel_bar[:2])}) är bevarad i 3D-uppställningen.",
                "byt_miljo",
            )

    return varningar


def klona_scen_snabbt(scen: dict[str, Any] | None) -> dict[str, Any] | None:
    """Snabb kopia av scenpaket/2 (~0.2 ms) där oförändrade spår i `rorelse` delas via copy-on-write."""
    if scen is None:
        return None
    ut = dict(scen)
    ut["tidsbas"] = dict(scen.get("tidsbas") or {})
    ut["objekt"] = [
        {
            **o,
            "pos": list(o["pos"]),
            "rot": list(o["rot"]),
            "matt": list(o["matt"]),
            "synlig_ut": [list(iv) for iv in (o.get("synlig_ut") or [])],
        }
        for o in scen.get("objekt", [])
    ]
    ut["tagningar"] = [
        {
            **t,
            "ut": list(t["ut"]),
            "kamera": {
                "statisk": t["kamera"]["statisk"],
                "nycklar": [list(k) for k in t["kamera"]["nycklar"]],
            },
        }
        for t in scen.get("tagningar", [])
    ]
    ut["rorelse"] = {
        pid: [{**sp, "ut": list(sp["ut"])} for sp in spar]
        for pid, spar in (scen.get("rorelse") or {}).items()
    }
    return ut


def kompilera_tillstand(session: dict[str, Any]) -> dict[str, Any]:
    """Kompilerar intern sessionsdata till det spikade `arbetsbord/1`-kontraktet i NY tidslinje."""
    klipp_meta = session["klipp"]
    fps = float(klipp_meta["fps"]) or 30.0
    har_3d = bool(klipp_meta.get("har_3d"))
    orig_scen = session.get("working_scen")
    tagn_mods: dict[str, dict[str, Any]] = session["tagning_mods"]
    tema = dict(session.get("miljo_tema") or MILJO_TEMAN["original"])
    ljud_lage = session.get("ljud_lage", "original")
    k5_poster = session.get("k5_poster") or []

    # 1. Bygg ny tidsavbildning & nya tagningsintervall
    tidsavbildning: list[dict[str, Any]] = []
    tagn_ny_intervall_s: dict[str, tuple[float, float]] = {}
    tagn_ny_rutor: dict[str, tuple[int, int, int]] = {}  # sid -> (ny_a, ny_b_play, ny_b_total)
    cursor_s = 0.0
    cursor_u = 0

    tagn_ordnad = sorted(tagn_mods.values(), key=lambda x: x["nr"])
    for tm in tagn_ordnad:
        sid = tm["id"]
        if tm.get("stryk"):
            continue
        orig_fran = float(tm["korta_fran_s"])
        orig_till = max(orig_fran + 0.1, float(tm["korta_till_s"]))
        tempo = max(0.25, min(4.0, float(tm.get("tempo", 1.0))))
        play_dur = (orig_till - orig_fran) / tempo
        paus_s = max(0.0, float(tm.get("paus_slut_s", 0.0)))

        ny_fran = round(cursor_s, 4)
        ny_till_play = round(cursor_s + play_dur, 4)
        ny_till_total = round(ny_till_play + paus_s, 4)

        ny_a = cursor_u
        play_frames = max(1, int(round(play_dur * fps)))
        ny_b_play = ny_a + play_frames
        hold_frames = int(round(paus_s * fps)) if paus_s > 0.0 else 0
        ny_b_total = ny_b_play + hold_frames

        tidsavbildning.append(
            {
                "tagning": sid,
                "typ": "spela",
                "ny_fran_s": ny_fran,
                "ny_till_s": ny_till_play,
                "orig_fran_s": round(orig_fran, 4),
                "orig_till_s": round(orig_till, 4),
                "tempo": round(tempo, 3),
            }
        )
        if hold_frames > 0:
            hold_orig = round(max(orig_fran, orig_till - 1.0 / fps), 4)
            tidsavbildning.append(
                {
                    "tagning": sid,
                    "typ": "hall",
                    "ny_fran_s": ny_till_play,
                    "ny_till_s": ny_till_total,
                    "orig_fran_s": hold_orig,
                    "orig_till_s": hold_orig,
                    "tempo": 0.0,
                }
            )

        tagn_ny_intervall_s[sid] = (ny_fran, ny_till_total)
        tagn_ny_rutor[sid] = (ny_a, ny_b_play, ny_b_total)
        cursor_s = ny_till_total
        cursor_u = ny_b_total

    langd_ny_s = round(cursor_s, 3)
    antal_rutor_ny = cursor_u
    spela_seg = [seg for seg in tidsavbildning if seg["typ"] == "spela"]

    # 2. Omtidsatta 3D-scenen om 3D finns (snabb copy-on-write väg)
    scen_ut: dict[str, Any] | None = None
    if har_3d and orig_scen is not None:
        scen_ut = klona_scen_snabbt(orig_scen)
        assert scen_ut is not None
        scen_ut["tidsbas"] = {
            **orig_scen.get("tidsbas", {}),
            "fps": fps,
            "antal_rutor": antal_rutor_ny,
        }
        scen_ut["miljo_tema"] = tema

        nya_tagn = []
        orig_tagn_map = {t["id"]: t for t in orig_scen.get("tagningar", [])}
        for tm in tagn_ordnad:
            sid = tm["id"]
            if sid not in tagn_ny_rutor or sid not in orig_tagn_map:
                continue
            ot = dict(orig_tagn_map[sid])
            oa, _ = ot["ut"]
            ny_a, ny_b_play, ny_b_total = tagn_ny_rutor[sid]
            ot["ut"] = [ny_a, ny_b_total]

            kam = ot.get("kamera", {})
            orig_nycklar = kam.get("nycklar", [])
            if not orig_nycklar:
                continue
            tempo = max(0.25, float(tm.get("tempo", 1.0)))
            okortad = (
                abs(tempo - 1.0) < 1e-4
                and abs(float(tm["korta_fran_s"]) - float(tm["orig_fran_s"])) < 1e-4
                and abs(float(tm["korta_till_s"]) - float(tm["orig_till_s"])) < 1e-4
                and ny_b_total == ny_b_play
            )

            if kam.get("statisk") or len(orig_nycklar) == 1:
                k0 = list(orig_nycklar[0])
                k0[0] = ny_a
                ot["kamera"] = {"statisk": True, "nycklar": [k0]}
            elif okortad:
                shift = ny_a - oa
                ot["kamera"] = {
                    "statisk": False,
                    "nycklar": orig_nycklar if shift == 0 else [[k[0] + shift, *k[1:]] for k in orig_nycklar],
                }
            else:
                orig_sub_a = float(tm["korta_fran_s"]) * fps
                orig_sub_b = float(tm["korta_till_s"]) * fps
                play_len = max(1, ny_b_play - ny_a)
                steg = 2 if play_len > 6 else 1
                nya_k = []
                for du in range(0, play_len, steg):
                    u_ny = ny_a + du
                    u_orig = min(orig_sub_b - 1e-4, orig_sub_a + du * tempo)
                    nya_k.append([u_ny] + _interp_nycklar(orig_nycklar, u_orig))
                if nya_k[-1][0] != ny_b_play - 1:
                    u_orig_end = min(orig_sub_b - 1e-4, orig_sub_a + (play_len - 1) * tempo)
                    nya_k.append([ny_b_play - 1] + _interp_nycklar(orig_nycklar, u_orig_end))
                if ny_b_total > ny_b_play:
                    nya_k.append([ny_b_total - 1] + list(nya_k[-1][1:]))
                ot["kamera"] = {"statisk": False, "nycklar": nya_k}
            nya_tagn.append(ot)
        scen_ut["tagningar"] = nya_tagn

        ny_rorelse: dict[str, list[dict[str, Any]]] = {}
        for pid, spar_lista in (orig_scen.get("rorelse") or {}).items():
            ny_spar_lista = []
            for sp in spar_lista:
                sid = sp.get("tagning")
                if not sid or sid not in tagn_ny_rutor:
                    continue
                ny_a, ny_b_play, ny_b_total = tagn_ny_rutor[sid]
                tm = tagn_mods[sid]
                tempo = max(0.25, float(tm.get("tempo", 1.0)))
                rutor_orig = sp.get("rutor") or []
                if not rutor_orig:
                    continue
                oa = sp["ut"][0]
                okortad = (
                    abs(tempo - 1.0) < 1e-4
                    and abs(float(tm["korta_fran_s"]) - float(tm["orig_fran_s"])) < 1e-4
                    and abs(float(tm["korta_till_s"]) - float(tm["orig_till_s"])) < 1e-4
                    and ny_b_total == ny_b_play
                )
                if okortad:
                    shift = ny_a - oa
                    nya_rutor = rutor_orig if shift == 0 else [[r[0] + shift, *r[1:]] for r in rutor_orig]
                else:
                    orig_sub_a = float(tm["korta_fran_s"]) * fps
                    orig_sub_b = float(tm["korta_till_s"]) * fps
                    play_len = max(1, ny_b_play - ny_a)
                    nya_rutor = []
                    for du in range(play_len):
                        u_ny = ny_a + du
                        u_orig = min(orig_sub_b - 1e-4, orig_sub_a + du * tempo)
                        nya_rutor.append([u_ny] + _interp_rorelse_rad(rutor_orig, u_orig))
                    if ny_b_total > ny_b_play:
                        sista = nya_rutor[-1][1:]
                        nya_rutor.append([ny_b_play, *sista])
                        if ny_b_total - 1 > ny_b_play:
                            nya_rutor.append([ny_b_total - 1, *sista])
                ny_spar_lista.append({"tagning": sid, "ut": [ny_a, ny_b_total], "rutor": nya_rutor})
            if ny_spar_lista:
                ny_rorelse[pid] = ny_spar_lista
        scen_ut["rorelse"] = ny_rorelse

        nya_objekt = []
        n_orig_tot = int(orig_scen["tidsbas"]["antal_rutor"])
        for obj in orig_scen.get("objekt", []):
            orig_iv = obj.get("synlig_ut") or [[0, n_orig_tot]]
            ny_iv: list[list[int]] = []
            for t_orig in orig_scen.get("tagningar", []):
                sid = t_orig["id"]
                if sid not in tagn_ny_rutor:
                    continue
                ta, tb = t_orig["ut"]
                if any(min(tb, iv[1]) > max(ta, iv[0]) for iv in orig_iv):
                    na, _, nb_tot = tagn_ny_rutor[sid]
                    ny_iv.append([na, nb_tot])
            syn_samlad = _sla_ihop_intervall(ny_iv)
            if syn_samlad:
                o = dict(obj)
                o["synlig_ut"] = syn_samlad
                nya_objekt.append(o)
        scen_ut["objekt"] = nya_objekt

    # 3. Omtidsatta media (skarmtext + tal) till NY tidslinje
    orig_media = session.get("working_media") or session.get("orig_media") or {}
    ny_skarmtext: list[dict[str, Any]] = []
    for x in orig_media.get("skarmtext", []):
        if x.get("borttagen"):
            continue
        if x.get("manuell_ny_tid"):
            tid_a = float(x.get("fran_s", 0.0))
            tid_b = float(x.get("till_s", tid_a + 2.0))
            if x.get("tagning_id") and x["tagning_id"] in tagn_ny_intervall_s:
                sa, sb = tagn_ny_intervall_s[x["tagning_id"]]
                tid_a = max(sa, min(sb - 0.1, sa + float(x.get("rel_fran_s", 0.0))))
                tid_b = max(tid_a + 0.1, min(sb, sa + float(x.get("rel_till_s", sb - sa))))
            item = dict(x)
            item["fran_s"] = round(min(tid_a, langd_ny_s), 3)
            item["till_s"] = round(min(tid_b, langd_ny_s), 3)
            if item["till_s"] > item["fran_s"] + 0.05:
                ny_skarmtext.append(item)
            continue

        mapped = _avbilda_tid_segment(float(x["fran_s"]), float(x["till_s"]), spela_seg)
        for idx_m, (na, nb) in enumerate(mapped):
            item = dict(x)
            if idx_m > 0:
                item["id"] = f"{x['id']}__{idx_m + 1}"
            item["fran_s"] = na
            item["till_s"] = nb
            ny_skarmtext.append(item)

    ny_tal: list[dict[str, Any]] = []
    for seg in orig_media.get("tal", []):
        mapped = _avbilda_tid_segment(float(seg["fran_s"]), float(seg["till_s"]), spela_seg)
        for idx_m, (na, nb) in enumerate(mapped):
            s_copy = dict(seg)
            if idx_m > 0:
                s_copy["id"] = f"{seg['id']}__{idx_m + 1}"
            s_copy["fran_s"] = na
            s_copy["till_s"] = nb
            nya_ord = []
            for o in seg.get("ord", []):
                for oa, ob in _avbilda_tid_segment(float(o["fran_s"]), float(o["till_s"]), spela_seg):
                    if oa >= na - 0.05 and ob <= nb + 0.05:
                        nya_ord.append({"o": o["o"], "fran_s": oa, "till_s": ob})
            s_copy["ord"] = nya_ord
            ny_tal.append(s_copy)

    nyckel = klipp_meta["nyckel"]
    musik_meta = copy.deepcopy(orig_media.get("musik") or {"finns": False, "borttagen": False})
    musik_meta["borttagen"] = ljud_lage != "original"

    media_ut = {
        "video_url": f"/media/video/{nyckel}",
        "tal_url": f"/media/tal/{nyckel}" if klipp_meta.get("har_tal") else None,
        "ljud_lage": ljud_lage,
        "skarmtext": ny_skarmtext,
        "tal": ny_tal,
        "musik": musik_meta,
    }

    # 4. Bygg sammanfattande `tagningar` i kontraktet
    bar_per_tagning: dict[str, list[str]] = {}
    for p in k5_poster:
        if p.get("roll") == "bar":
            for sid in p.get("tagningar") or []:
                bar_per_tagning.setdefault(sid, []).append(p["namn"])

    tagningar_ut: list[dict[str, Any]] = []
    scen_tagn_map = {t["id"]: t for t in (scen_ut or {}).get("tagningar", [])}
    orig_scen_tagn_map = {t["id"]: t for t in (orig_scen or {}).get("tagningar", [])}
    for tm in tagn_ordnad:
        sid = tm["id"]
        ny_iv = tagn_ny_intervall_s.get(sid)
        st_info = scen_tagn_map.get(sid) or orig_scen_tagn_map.get(sid) or {}
        kam = st_info.get("kamera") or {}
        nycklar = kam.get("nycklar") or []
        lins_mm = round(float(nycklar[0][8]), 1) if nycklar else None
        kam_typ = "statisk" if kam.get("statisk", True) else "rörlig"
        pers = [p["id"] if isinstance(p, dict) else p for p in (st_info.get("personer") or tm.get("personer") or [])]

        if ny_iv is not None:
            rep_i_tagn = [
                s["text"]
                for s in ny_tal
                if min(ny_iv[1], s["till_s"]) - max(ny_iv[0], s["fran_s"]) > 0.1
            ]
        else:
            rep_i_tagn = [
                s["text"]
                for s in orig_media.get("tal", [])
                if min(tm["orig_till_s"], s["till_s"]) - max(tm["orig_fran_s"], s["fran_s"]) > 0.1
            ]

        tagningar_ut.append(
            {
                "id": sid,
                "nr": tm["nr"],
                "orig_fran_s": round(tm["orig_fran_s"], 3),
                "orig_till_s": round(tm["orig_till_s"], 3),
                "ny_fran_s": ny_iv[0] if ny_iv else None,
                "ny_till_s": ny_iv[1] if ny_iv else None,
                "stryk": bool(tm.get("stryk", False)),
                "tempo": round(float(tm.get("tempo", 1.0)), 3),
                "paus_slut_s": round(float(tm.get("paus_slut_s", 0.0)), 3),
                "korta_fran_s": round(float(tm["korta_fran_s"]), 3),
                "korta_till_s": round(float(tm["korta_till_s"]), 3),
                "personer": pers,
                "kamera_typ": kam_typ,
                "lins_mm": lins_mm,
                "repliker": rep_i_tagn,
                "k5_bar": bar_per_tagning.get(sid, []),
                "funktion": tm.get("funktion"),
                "syfte": tm.get("syfte"),
                "anteckning": tm.get("anteckning"),
                "replik_ny": tm.get("replik_ny"),
                "kansla": tm.get("kansla"),
            }
        )

    varningar = berakna_k5_varningar(session, tagningar_ut, media_ut)

    # 5. Live K6-manus
    from .manus import bygg_manus

    ut_tillstand = {
        "schema": SCHEMA_VERSION,
        "session_id": session["session_id"],
        "version": session.get("version", 1),
        "klipp": {
            "nyckel": nyckel,
            "id": klipp_meta["id"],
            "namn": klipp_meta["namn"],
            "har_3d": har_3d,
            "fps": fps,
            "bredd": int(klipp_meta["bredd"]),
            "hojd": int(klipp_meta["hojd"]),
            "langd_orig_s": round(float(klipp_meta["langd_orig_s"]), 3),
            "langd_s": langd_ny_s,
        },
        "kund": session.get("kund"),
        "avsikt": session.get("avsikt", ""),
        "scen": scen_ut,
        "tidsavbildning": tidsavbildning,
        "miljo_tema": tema,
        "media": media_ut,
        "tagningar": tagningar_ut,
        "manus": None,
        "k5": {
            "poster": k5_poster,
            "varningar": varningar,
        },
        "formatkort": session.get("formatkort"),
        "andringar": list(session.get("andringar") or []),
        "kan_angra": bool(session.get("undo_stack")),
        "tidal_waves": list(session.get("tidal_waves") or []),
        "k7": {
            "generativt": False,
            "spegling": False,
        },
    }
    ut_tillstand["manus"] = bygg_manus(ut_tillstand)
    return ut_tillstand
