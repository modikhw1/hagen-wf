"""K7-spärr och loggning: noll generativ bild/video/röst och noll spegling (`byt_hand`) i CM:s ändringsled."""
from __future__ import annotations

import datetime
import json
import re
from typing import Any

from .schema import K7_LOGG_FIL

FORBJUDNA_OPS = {
    "byt_hand",
    "spegla",
    "spegling",
    "mirror",
    "flip_x",
    "generera_bild",
    "generera_video",
    "generera_rost",
    "klona_rost",
    "syntetisk_rost",
    "tts",
    "voice_clone",
    "image_gen",
    "video_gen",
    "deepfake",
    "face_swap",
}

FORBJUDNA_NYCKLAR = {"spegla", "spegling", "mirror", "flip_x", "byt_hand", "generativ", "generativt"}

# Mönster för tydliga K7-förbjudna önskemål i CM-text (negeringar som "inte spegla" släpps igenom)
_GEN_VERBS = re.compile(
    r"\b(generera|skapa\s+ai|ai-?generera|syntetisera|klona|deepfake|byt\s+hand|spegelvänd|spegla)\b",
    re.IGNORECASE,
)
_GEN_OBJS = re.compile(
    r"\b(video|bild|bakgrundsbild|röst|tal|ansikte|hand|högerhand|vänsterhand|vänsterhänt|högerhänt)\b",
    re.IGNORECASE,
)
_NEGERING = re.compile(r"\b(inte|ej|utan|aldrig|noll)\b", re.IGNORECASE)


class K7StoppError(ValueError):
    """Kastas när en begäran eller operation bryter mot K7-spärren."""


def kontrollera_operation(op: str, params: dict[str, Any] | None = None) -> None:
    """Kastar K7StoppError om operationen innebär spegling eller generativ media."""
    op_norm = (op or "").strip().lower()
    if op_norm in FORBJUDNA_OPS:
        raise K7StoppError(
            f"K7-spärr: Operationen '{op}' är otillåten i CM:s ändringsled (noll generativ media, noll byt_hand/spegling)."
        )
    p = params or {}
    for k, v in p.items():
        kl = str(k).lower()
        if kl in FORBJUDNA_NYCKLAR and v:
            raise K7StoppError(
                f"K7-spärr: Parametern '{k}={v}' bryter mot förbudet mot spegling/generering."
            )
        if kl in ("scale_x", "skala_x") and isinstance(v, (int, float)) and v < 0:
            raise K7StoppError("K7-spärr: Negativ skalning (spegling) är förbjuden.")
        if kl == "vrid_deg" and isinstance(v, str) and "speg" in v.lower():
            raise K7StoppError("K7-spärr: Spegling är förbjuden.")


def kontrollera_cm_text(text: str) -> str | None:
    """Returnerar K7-feltext om CM explicit ber om generativ bild/video/röst eller byt_hand/spegling."""
    t = (text or "").strip()
    if not t:
        return None
    if re.search(r"\bbyt_hand\b|\bbyt\s+hand\b|\bspegelvänd\b", t, re.IGNORECASE):
        if not _NEGERING.search(t):
            return (
                "K7-spärr: CM:s ändringsled tillåter aldrig `byt_hand` eller spegling av kropp/video. "
                "Vrid i stället hela personen (`person_placering`) eller flytta kameran."
            )
    if re.search(r"\b(klona\s+röst|röstklon|tts|text\s+till\s+tal|deepfake|face\s*swap)\b", t, re.IGNORECASE):
        return (
            "K7-spärr: Generativ röst/dubbning är förbjuden. Ändra i stället replikanteckningen i K6-manuset "
            "(`manus_anteckning`) eller skärmtexten (`skarmtext_byt`)."
        )
    if _GEN_VERBS.search(t) and _GEN_OBJS.search(t) and not _NEGERING.search(t):
        # Tillåt "skapa ny miljö / kök" (3D-block) men stoppa explicit "generera video/bild/röst"
        if re.search(r"\b(generera|syntetisera|ai-?generera)\s+(en\s+|ny\s+)?(video|bild|röst|ljud|bakgrundsbild)\b", t, re.IGNORECASE):
            return (
                "K7-spärr: Generativ bild, video eller röst är förbjuden. Arbetsbordet bygger i stället enkla 3D-block, "
                "byter belysning/miljötema och uppdaterar skärmtext och K6-manus."
            )
    return None


def logga_k7(
    typ: str,
    session_id: str,
    klipp: str,
    op: str,
    params: dict[str, Any] | None = None,
    ok: bool = True,
    detalj: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    """Skriver en rad till `arbetsbord/ut/k7_logg.jsonl` för full spårbarhet."""
    K7_LOGG_FIL.parent.mkdir(parents=True, exist_ok=True)
    post = {
        "tid": datetime.datetime.now().isoformat(timespec="seconds"),
        "typ": typ,
        "session_id": session_id,
        "klipp": klipp,
        "op": op,
        "params": params or {},
        "ok": bool(ok),
        "generativt": False,
        "spegling": False,
        "detalj": detalj,
    }
    if extra:
        post.update(extra)
    with K7_LOGG_FIL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(post, ensure_ascii=False) + "\n")
