"""Inladdning av utvecklingsklippen (scenpaket/2 + medielager/1 + K5 + formatkort) och kundprofiler."""
from __future__ import annotations

import copy
import json
import subprocess
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from .schema import (
    BARLISTOR_DIR,
    FORVARLD_KARNA_DIR,
    KLIPP_JSONL,
    MEDIELAGER_ARBETSBORD_DIR,
    MEDIELAGER_FALLBACK_DIR,
    MEDIELAGER_STAMMAR_CACHE,
    MILJO_TEMAN,
    REGR5_DIR,
    ROT,
    UTVALDA_KUNDER,
    kompilera_tillstand,
)

KLIPP_KATALOG: list[dict[str, Any]] = [
    {
        "nyckel": "notan",
        "id": "d-dialog-notan",
        "namn": "Notan (dialog på restaurang)",
        "ingest": "notan-tagningar",
        "paket": [
            REGR5_DIR / "notan-tagningar" / "paket.json",
            FORVARLD_KARNA_DIR / "notan" / "paket.json",
        ],
        "kalla": ROT / "scen" / "3d" / "kontrakt" / "ut" / "notan" / "kalla_handelser.json",
        "barlista": BARLISTOR_DIR / "notan.json",
        "video": [
            ROT / "scen" / "klipp" / "d-dialog-notan.mp4",
            ROT / "forvarld" / "varld" / "paket" / "notan" / "source.mp4",
        ],
        "tidslinje_nycklar": ["d-dialog-notan", "notan", "notan-tagningar"],
        "har_3d": True,
    },
    {
        "nyckel": "guacamole",
        "id": "e-dialog-guacamole",
        "namn": "Guacamole (dialog i bar)",
        "ingest": "e-dialog-guacamole-tagningar",
        "paket": [
            REGR5_DIR / "e-dialog-guacamole-tagningar" / "paket.json",
            FORVARLD_KARNA_DIR / "guacamole" / "paket.json",
        ],
        "kalla": ROT / "scen" / "3d" / "kontrakt" / "ut" / "e-dialog-guacamole_grupp" / "kalla_0032.json",
        "barlista": BARLISTOR_DIR / "guacamole.json",
        "video": [ROT / "scen" / "klipp" / "e-dialog-guacamole.mp4"],
        "tidslinje_nycklar": ["e-dialog-guacamole", "guacamole", "e-dialog-guacamole-tagningar"],
        "har_3d": True,
    },
    {
        "nyckel": "gelato",
        "id": "kennysgelato2.0-7596403003901381910",
        "namn": "Gelato (smakprov-sketch)",
        "ingest": "kand-kennysgelato-tagningar",
        "paket": [
            REGR5_DIR / "kand-kennysgelato-tagningar" / "paket.json",
            FORVARLD_KARNA_DIR / "gelato" / "paket.json",
        ],
        "kalla": ROT / "scen" / "3d" / "kontrakt" / "ut" / "kand-kennysgelato_n06-hand" / "kalla_0033.json",
        "barlista": BARLISTOR_DIR / "gelato.json",
        "video": [ROT / "scen" / "klipp" / "kand-kennysgelato2.0-7596403003901381910.mp4"],
        "tidslinje_nycklar": [
            "kand-kennysgelato2.0-7596403003901381910",
            "kennysgelato2.0-7596403003901381910",
            "gelato",
            "kand-kennysgelato-tagningar",
        ],
        "har_3d": True,
    },
    {
        "nyckel": "asketch",
        "id": "a-sketch-servering",
        "namn": "A-sketch (servering för 3 kr)",
        "ingest": "a-sketch-servering-tagningar",
        "paket": [
            REGR5_DIR / "a-sketch-servering-tagningar" / "paket.json",
            FORVARLD_KARNA_DIR / "asketch" / "paket.json",
        ],
        "kalla": ROT / "scen" / "3d" / "kontrakt" / "ut" / "a" / "kalla_prop.json",
        "barlista": BARLISTOR_DIR / "asketch.json",
        "video": [ROT / "scen" / "klipp" / "a-sketch-servering.mp4"],
        "tidslinje_nycklar": ["a-sketch-servering", "asketch", "a-sketch-servering-tagningar"],
        "har_3d": True,
    },
    {
        "nyckel": "btilltal",
        "id": "b-tilltal-ravara",
        "namn": "B-tilltal (slaktaren / gissa vikten)",
        "ingest": "b-tilltal-ravara-tagningar",
        "paket": [],
        "kalla": ROT / "scen" / "3d" / "kontrakt" / "ut" / "b-tilltal-ravara_n06-hand" / "kalla_0032.json",
        "barlista": BARLISTOR_DIR / "btilltal.json",
        "video": [ROT / "scen" / "klipp" / "b-tilltal-ravara.mp4"],
        "tidslinje_nycklar": ["b-tilltal-ravara", "btilltal", "b-tilltal-ravara-tagningar"],
        "har_3d": False,
    },
]

_KLIPP_BY_NYCKEL = {c["nyckel"]: c for c in KLIPP_KATALOG}
_VIDEO_PROBE_CACHE: dict[str, dict[str, Any]] = {}
_KUND_CACHE: list[dict[str, Any]] | None = None
_FORMATKORT_CACHE: dict[str, dict[str, Any]] | None = None


def _las_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _hitta_spec(nyckel: str) -> dict[str, Any]:
    k = (nyckel or "").strip().lower()
    if k in _KLIPP_BY_NYCKEL:
        return _KLIPP_BY_NYCKEL[k]
    for c in KLIPP_KATALOG:
        if k in (c["id"].lower(), c["ingest"].lower()):
            return c
    raise KeyError(f"Okänt klipp '{nyckel}'. Tillgängliga: {', '.join(_KLIPP_BY_NYCKEL)}")


def hitta_video(nyckel: str) -> Path | None:
    spec = _hitta_spec(nyckel)
    for p in spec["video"]:
        if p.exists():
            return p
    return None


def _probe_video(video_path: Path | None) -> dict[str, Any]:
    if not video_path or not video_path.exists():
        return {"langd_s": 0.0, "bredd": 576, "hojd": 1024, "fps": 30.0}
    key = str(video_path.resolve())
    if key in _VIDEO_PROBE_CACHE:
        return _VIDEO_PROBE_CACHE[key]
    try:
        r = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,width,height,r_frame_rate:format=duration",
                "-of",
                "json",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        j = json.loads(r.stdout)
        v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
        num, den = (v.get("r_frame_rate") or "30/1").split("/")
        fps = round(float(num) / float(den or 1), 3)
        res = {
            "langd_s": round(float(j["format"]["duration"]), 4),
            "bredd": int(v.get("width", 576)),
            "hojd": int(v.get("height", 1024)),
            "fps": fps,
        }
    except Exception:
        res = {"langd_s": 0.0, "bredd": 576, "hojd": 1024, "fps": 30.0}
    _VIDEO_PROBE_CACHE[key] = res
    return res


def _hitta_tidslinje(spec: dict[str, Any]) -> tuple[dict[str, Any] | None, Path | None]:
    for bas in (MEDIELAGER_ARBETSBORD_DIR / "lager", MEDIELAGER_ARBETSBORD_DIR, MEDIELAGER_FALLBACK_DIR):
        if not bas.exists():
            continue
        for namn in spec["tidslinje_nycklar"]:
            cand = bas / namn / "tidslinje.json"
            if cand.exists():
                return _las_json(cand), cand
    return None, None


def hitta_tal_fil(nyckel: str) -> Path | None:
    """Letar upp separerat talspår (Demucs/medielager) för ett klipp, om det finns."""
    spec = _hitta_spec(nyckel)
    tl, tl_path = _hitta_tidslinje(spec)
    if tl:
        stam = ((tl.get("musik") or {}).get("stammar") or {}).get("tal")
        if stam:
            for cand in (
                (tl_path.parent / stam) if tl_path else None,
                ROT / stam,
            ):
                if cand and cand.exists():
                    return cand
    for bas in (MEDIELAGER_ARBETSBORD_DIR, MEDIELAGER_STAMMAR_CACHE):
        if not bas.exists():
            continue
        for namn in spec["tidslinje_nycklar"]:
            for ext in ("tal.wav", "tal.flac", "tal.mp3"):
                cand = bas / namn / ext
                if cand.exists():
                    return cand
    return None


def _ladda_klipp_jsonl() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    global _KUND_CACHE, _FORMATKORT_CACHE
    if _KUND_CACHE is not None and _FORMATKORT_CACHE is not None:
        return _KUND_CACHE, _FORMATKORT_CACHE

    formatkort: dict[str, dict[str, Any]] = {}
    per_konto: dict[str, list[dict[str, Any]]] = {}

    if KLIPP_JSONL.exists():
        with KLIPP_JSONL.open("r", encoding="utf-8") as f:
            for rad in f:
                if not rad.strip():
                    continue
                r = json.loads(rad)
                konto = r.get("konto") or r["id"].rsplit("-", 1)[0]
                per_konto.setdefault(konto, []).append(r)
                if "l4" in r and r["id"] in {c["id"] for c in KLIPP_KATALOG}:
                    l4 = r["l4"] or {}
                    l2 = r.get("l2") or {}
                    formatkort[r["id"]] = {
                        "karna": l4.get("karna"),
                        "handling": l4.get("handling"),
                        "typ": l2.get("typ"),
                        "beats": [
                            {
                                "funktion": b.get("funktion") or "takt",
                                "vad": b.get("vad") or "",
                                "bar": b.get("bar"),
                            }
                            for b in (l4.get("beats") or [])
                        ],
                    }

    # Bygg kundprofiler (utvalda först, sedan toppkonton efter antal klipp)
    kunder_map: dict[str, dict[str, Any]] = {}
    for konto, rader in per_konto.items():
        if konto not in UTVALDA_KUNDER and len(rader) < 12:
            continue
        l4s = [r["l4"] for r in rader if "l4" in r]
        l2s = [r["l2"] for r in rader if "l2" in r]
        typer = Counter(l.get("typ") for l in l2s if l.get("typ"))
        rum = Counter(x for l in l4s for x in ((l.get("krav") or {}).get("lokal") or []))
        produkter = Counter(
            pl["har"].strip()
            for l in l4s
            for pl in (l.get("platser") or [])
            if pl.get("typ") == "produkt" and pl.get("har")
        )
        kunder_map[konto] = {
            "konto": konto,
            "antal_klipp": len(rader),
            "typer": [t for t, _ in typer.most_common(5)],
            "rum": [rm for rm, _ in rum.most_common(5)],
            "produkter": [pr for pr, _ in produkter.most_common(8)],
        }

    utvalda = [kunder_map[k] for k in UTVALDA_KUNDER if k in kunder_map]
    ovriga = sorted(
        (v for k, v in kunder_map.items() if k not in UTVALDA_KUNDER),
        key=lambda x: (-x["antal_klipp"], x["konto"]),
    )[:20]

    _KUND_CACHE = utvalda + ovriga
    _FORMATKORT_CACHE = formatkort
    return _KUND_CACHE, _FORMATKORT_CACHE


def lista_kunder() -> list[dict[str, Any]]:
    kunder, _ = _ladda_klipp_jsonl()
    return kunder


def hamta_kund(konto: str | None) -> dict[str, Any] | None:
    if not konto:
        return None
    for k in lista_kunder():
        if k["konto"] == konto:
            return copy.deepcopy(k)
    return {"konto": konto, "antal_klipp": 0, "typer": [], "rum": [], "produkter": []}


def lista_klipp() -> list[dict[str, Any]]:
    ut: list[dict[str, Any]] = []
    for spec in KLIPP_KATALOG:
        paket_fil = next((p for p in spec["paket"] if p.exists()), None)
        vid = hitta_video(spec["nyckel"])
        probe = _probe_video(vid)
        har_tal = hitta_tal_fil(spec["nyckel"]) is not None
        paket_info = None
        if paket_fil and spec["har_3d"]:
            p = _las_json(paket_fil)
            fps = float(p["tidsbas"]["fps"])
            n_rutor = int(p["tidsbas"]["antal_rutor"])
            paket_info = (fps, round(n_rutor / fps, 3), len(p["tagningar"]))
        kalla_scener = 0
        if not paket_info and spec["kalla"].exists():
            k = _las_json(spec["kalla"])
            kalla_scener = len((k.get("semantik") or {}).get("scener") or [])

        fps = paket_info[0] if paket_info else probe["fps"]
        langd_s = paket_info[1] if paket_info else probe["langd_s"]
        antal_tagn = paket_info[2] if paket_info else kalla_scener
        ut.append(
            {
                "nyckel": spec["nyckel"],
                "id": spec["id"],
                "namn": spec["namn"],
                "har_3d": bool(spec["har_3d"] and paket_fil is not None),
                "har_video": vid is not None,
                "har_tal": har_tal,
                "langd_s": langd_s,
                "fps": fps,
                "antal_tagningar": antal_tagn,
            }
        )
    return ut


def _normalisera_kalla_skarmtext(
    items: list[dict[str, Any]],
    bredd: int,
    hojd: int,
) -> list[dict[str, Any]]:
    ut: list[dict[str, Any]] = []
    w = max(1.0, float(bredd))
    h = max(1.0, float(hojd))
    for i, x in enumerate(items, 1):
        box = x.get("box")
        nb = None
        cy = 0.5
        if isinstance(box, (list, tuple)) and len(box) == 4:
            bx, by, bw, bh = [float(v) for v in box]
            # Om pixlar (>1.5), normalisera [x, y, w, h] -> [x0, y0, x1, y1]
            if max(abs(bx), abs(by), abs(bw), abs(bh)) > 1.5:
                x0 = max(0.0, min(1.0, bx / w))
                y0 = max(0.0, min(1.0, by / h))
                x1 = max(x0 + 0.02, min(1.0, (bx + bw) / w))
                y1 = max(y0 + 0.02, min(1.0, (by + bh) / h))
                nb = [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)]
            else:
                nb = [round(bx, 4), round(by, 4), round(bw, 4), round(bh, 4)]
            cy = (nb[1] + nb[3]) / 2.0

        pos = "ovre" if cy < 0.34 else ("nedre" if cy > 0.67 else "mitt")
        st = x.get("stil") or {}
        kontur_px = float(st.get("kontur_px") or 0.0)
        glyf = st.get("farg") or "#ffffff"
        radh = round(max(0.024, min(0.08, float(st.get("storlek_px") or 28.0) / h)), 4)

        ut.append(
            {
                "id": x.get("id") or f"st{i}",
                "text": x.get("text") or "",
                "text_original": x.get("text") or "",
                "fran_s": round(float(x.get("start_s", 0.0)), 3),
                "till_s": round(float(x.get("slut_s", 0.0)), 3),
                "box": nb,
                "typ": "overlag",
                "stil": {
                    "position": pos,
                    "glyffarg": glyf,
                    "platta": False,
                    "bakgrund": None,
                    "kontur": (st.get("kontur_farg") or "#000000") if kontur_px > 0 else None,
                    "versaler": False,
                    "radhojd": radh,
                },
                "andrad": False,
                "ny": False,
            }
        )
    return ut


def _normalisera_medielager_skarmtext(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ut: list[dict[str, Any]] = []
    for i, x in enumerate(items, 1):
        st = dict(x.get("stil") or {})
        kontur = st.get("kontur")
        if kontur is True:
            kontur = "#000000"
        elif kontur is False:
            kontur = None
        st["kontur"] = kontur
        st.setdefault("position", "mitt")
        st.setdefault("glyffarg", "#ffffff")
        st.setdefault("platta", False)
        st.setdefault("bakgrund", None)
        st.setdefault("versaler", False)
        st.setdefault("radhojd", st.get("radhojd_rel") or 0.034)
        ut.append(
            {
                "id": x.get("id") or f"x{i}",
                "text": x.get("text") or "",
                "text_original": x.get("text") or "",
                "fran_s": round(float(x.get("fran", 0.0)), 3),
                "till_s": round(float(x.get("till", 0.0)), 3),
                "box": x.get("box"),
                "typ": x.get("typ") or "overlag",
                "stil": st,
                "andrad": False,
                "ny": False,
            }
        )
    return ut


def _bygg_tal(tl: dict[str, Any] | None, kalla: dict[str, Any] | None) -> list[dict[str, Any]]:
    kalla_rep = ((kalla or {}).get("semantik") or {}).get("repliker") or []
    tl_seg = ((tl or {}).get("tal") or {}).get("segment") or []

    def matcha_talare(a: float, b: float) -> str | None:
        bast_t, bast_ov = None, 0.0
        for r in kalla_rep:
            ov = min(b, float(r.get("slut_s", 0.0))) - max(a, float(r.get("start_s", 0.0)))
            if ov > bast_ov:
                bast_ov = ov
                bast_t = r.get("talare")
        return bast_t if bast_ov > 0.08 else None

    if tl_seg:
        ut = []
        for i, s in enumerate(tl_seg, 1):
            a = round(float(s.get("fran", 0.0)), 3)
            b = round(float(s.get("till", 0.0)), 3)
            ord_lista = [
                {
                    "o": o.get("o") or o.get("ord") or "",
                    "fran_s": round(float(o.get("fran", a)), 3),
                    "till_s": round(float(o.get("till", b)), 3),
                }
                for o in (s.get("ord") or [])
            ]
            ut.append(
                {
                    "id": f"tal_{i}",
                    "talare": matcha_talare(a, b),
                    "text": (s.get("text") or "").strip(),
                    "fran_s": a,
                    "till_s": b,
                    "ord": ord_lista,
                }
            )
        return ut

    # Fallback direkt ur kalla.semantik.repliker
    ut = []
    for i, r in enumerate(kalla_rep, 1):
        a = round(float(r.get("start_s", 0.0)), 3)
        b = round(float(r.get("slut_s", 0.0)), 3)
        ord_lista = [
            {
                "o": o.get("ord") or o.get("o") or "",
                "fran_s": round(float(o.get("start_s", a)), 3),
                "till_s": round(float(o.get("slut_s", b)), 3),
            }
            for o in (r.get("ord") or [])
        ]
        ut.append(
            {
                "id": r.get("id") or f"r{i}",
                "talare": r.get("talare"),
                "text": (r.get("text") or "").strip(),
                "fran_s": a,
                "till_s": b,
                "ord": ord_lista,
            }
        )
    return ut


def _ladda_k5(spec: dict[str, Any], tagn_meta: list[dict[str, Any]], fps: float) -> list[dict[str, Any]]:
    bar_fil = spec["barlista"]
    if not bar_fil.exists():
        return []
    raw = _las_json(bar_fil)
    ut = []
    for p in raw.get("poster", []):
        ref = p.get("ref") or {}
        tags = list(ref.get("tagningar") or [])
        if not tags and ref.get("rutor"):
            for ra, rb in ref["rutor"]:
                ta, tb = ra / fps, rb / fps
                for tm in tagn_meta:
                    if min(tb, tm["orig_till_s"]) - max(ta, tm["orig_fran_s"]) > 0.05:
                        if tm["id"] not in tags:
                            tags.append(tm["id"])
        ut.append(
            {
                "id": p.get("id"),
                "namn": p.get("namn"),
                "typ": p.get("typ"),
                "roll": p.get("roll"),
                "varfor": p.get("varfor"),
                "tagningar": tags,
                "medie": list(ref.get("medie") or []),
            }
        )
    return ut


def ladda_klipp(klipp_nyckel: str, kund_konto: str | None = None, session_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Laddar ett klipp till intern session + kompilerat `arbetsbord/1`-tillstånd."""
    spec = _hitta_spec(klipp_nyckel)
    vid = hitta_video(spec["nyckel"])
    probe = _probe_video(vid)

    paket_fil = next((p for p in spec["paket"] if p.exists()), None) if spec["har_3d"] else None
    paket = _las_json(paket_fil) if paket_fil else None
    kalla = _las_json(spec["kalla"]) if spec["kalla"].exists() else None
    tl, _ = _hitta_tidslinje(spec)

    if paket:
        fps = float(paket["tidsbas"]["fps"]) or probe["fps"]
        bredd = int(paket["bild"]["bredd"])
        hojd = int(paket["bild"]["hojd"])
        langd_orig_s = round(int(paket["tidsbas"]["antal_rutor"]) / fps, 4)
    else:
        fps = probe["fps"]
        bredd = probe["bredd"]
        hojd = probe["hojd"]
        langd_orig_s = probe["langd_s"]

    # Bygg per-tagning basdata
    kalla_scener = {
        s["id"]: s for s in ((kalla or {}).get("semantik") or {}).get("scener") or []
    }
    tagning_mods: dict[str, dict[str, Any]] = {}
    if paket:
        for nr, t in enumerate(paket["tagningar"], 1):
            sid = t["id"]
            a0, b0 = t["ut"]
            oa_s = round(a0 / fps, 4)
            ob_s = round(b0 / fps, 4)
            ks = kalla_scener.get(sid) or {}
            pers = [p["id"] if isinstance(p, dict) else p for p in t.get("personer", [])]
            tagning_mods[sid] = {
                "id": sid,
                "nr": nr,
                "orig_fran_s": oa_s,
                "orig_till_s": ob_s,
                "korta_fran_s": oa_s,
                "korta_till_s": ob_s,
                "stryk": False,
                "tempo": 1.0,
                "paus_slut_s": 0.0,
                "personer": pers or list(ks.get("personer") or []),
                "funktion": ks.get("funktion"),
                "syfte": ks.get("syfte"),
                "anteckning": None,
                "replik_ny": None,
                "kansla": None,
            }
    elif kalla_scener:
        for nr, ks in enumerate(kalla_scener.values(), 1):
            sid = ks["id"]
            oa_s = round(float(ks["start_s"]), 4)
            ob_s = round(float(ks["slut_s"]), 4)
            tagning_mods[sid] = {
                "id": sid,
                "nr": nr,
                "orig_fran_s": oa_s,
                "orig_till_s": ob_s,
                "korta_fran_s": oa_s,
                "korta_till_s": ob_s,
                "stryk": False,
                "tempo": 1.0,
                "paus_slut_s": 0.0,
                "personer": list(ks.get("personer") or []),
                "funktion": ks.get("funktion"),
                "syfte": ks.get("syfte"),
                "anteckning": None,
                "replik_ny": None,
                "kansla": None,
            }

    # Medielager (skarmtext, tal, musik)
    skarm_tl = _normalisera_medielager_skarmtext(tl.get("skarmtext") or []) if tl else []
    skarm_kalla = _normalisera_kalla_skarmtext(((kalla or {}).get("semantik") or {}).get("skarmtext") or [], bredd, hojd)
    skarmtext = skarm_tl if skarm_tl else skarm_kalla

    tal = _bygg_tal(tl, kalla)
    musik_raw = (tl or {}).get("musik") or {}
    ljud_kalla = ((kalla or {}).get("semantik") or {}).get("ljud") or {}
    musik_finns = bool(musik_raw.get("finns") if "finns" in musik_raw else ljud_kalla.get("musik"))
    har_tal = hitta_tal_fil(spec["nyckel"]) is not None

    orig_media = {
        "skarmtext": skarmtext,
        "tal": tal,
        "musik": {"finns": musik_finns, "borttagen": False},
    }

    _, formatkort_map = _ladda_klipp_jsonl()
    formatkort = formatkort_map.get(spec["id"])
    k5_poster = _ladda_k5(spec, list(tagning_mods.values()), fps)
    kund = hamta_kund(kund_konto)

    sid_gen = session_id or uuid.uuid4().hex[:12]
    session: dict[str, Any] = {
        "session_id": sid_gen,
        "version": 1,
        "klipp": {
            "nyckel": spec["nyckel"],
            "id": spec["id"],
            "namn": spec["namn"],
            "har_3d": bool(paket is not None),
            "har_tal": har_tal,
            "fps": fps,
            "bredd": bredd,
            "hojd": hojd,
            "langd_orig_s": langd_orig_s,
        },
        "kund": kund,
        "avsikt": "",
        "orig_scen": copy.deepcopy(paket),
        "working_scen": copy.deepcopy(paket),
        "orig_tagning_mods": copy.deepcopy(tagning_mods),
        "tagning_mods": tagning_mods,
        "orig_media": copy.deepcopy(orig_media),
        "working_media": copy.deepcopy(orig_media),
        "miljo_tema": copy.deepcopy(MILJO_TEMAN["original"]),
        "ljud_lage": "original",
        "k5_poster": k5_poster,
        "formatkort": formatkort,
        "andringar": [],
        "tidal_waves": [],
        "undo_stack": [],
        "feedback_history": {},
    }
    return session, kompilera_tillstand(session)
