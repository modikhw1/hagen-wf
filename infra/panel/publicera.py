"""Publicerar ett blint bedömningspass till den stående ägarpanelen på < 1 min (INFRA.md §4, M5).

Stödjer:
  1. --importera-k2       Importerar det befintliga passet i motpart/runda-4/A-domare/panel/ (orört!)
  2. --spec <fil.json>    Bygger nytt blint pass med O-lager-id + varianter, strippar all metadata,
                          slumpar p_<hex>/m_<hex> och laddar upp via API till stående tjänst.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

ROT = Path(__file__).resolve().parents[2]


def _ffmpeg_blind_video(kalla: Path, ut: Path, *, vf: str = "", af: str = "", w: int = 540, h: int = 960) -> None:
    """Kodar om till enhetligt 540x960 H.264/AAC utan metadata (identiskt med A-domare/panel/bygg_panel.py)."""
    filt = [f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"]
    if vf:
        filt.append(vf)
    filt.append("format=yuv420p")
    argv = [
        "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(kalla),
        "-map", "0:v:0", "-map", "0:a:0?",
        "-map_metadata", "-1", "-map_chapters", "-1",
        "-vf", ",".join(filt),
    ]
    if af:
        argv += ["-af", af]
    argv += [
        "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-movflags", "+faststart", "-fflags", "+bitexact",
        str(ut),
    ]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg fel för {kalla}: {r.stderr[-400:]}")


def _http_post(url: str, data: bytes, content_type: str, token: str | None) -> dict[str, Any]:
    hdrs = {"Content-Type": content_type}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def publicera_k2(base_url: str, pass_id: str, token: str | None) -> dict[str, Any]:
    """Publicerar befintliga A-domare/panel/ (K2) till den stående tjänsten utan att ändra originalmappen."""
    t0 = time.monotonic()
    k2 = ROT / "motpart/runda-4/A-domare/panel"
    par_data = json.loads((k2 / "par.json").read_text(encoding="utf-8"))
    nyckel = json.loads((k2 / "nyckel.json").read_text(encoding="utf-8"))
    media_dir = k2 / "media"

    # Skriv om medie-URL:er till passets väg
    par_lista = []
    filer_att_skicka: list[Path] = []
    sedda: set[str] = set()
    for p in par_data["par"]:
        p2 = json.loads(json.dumps(p))
        for m in (p2.get("media") or {}).values():
            namn = Path(m["url"]).name
            m["url"] = f"/pass/{pass_id}/media/{namn}"
            if namn not in sedda and (media_dir / namn).is_file():
                sedda.add(namn)
                filer_att_skicka.append(media_dir / namn)
        par_lista.append(p2)

    base = base_url.rstrip("/")
    import concurrent.futures

    def _ladda(f: Path) -> None:
        _http_post(f"{base}/api/publicera/{pass_id}/media/{f.name}?commit=0", f.read_bytes(), "application/octet-stream", token)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_ladda, filer_att_skicka))

    payload = {
        "pass_id": pass_id,
        "titel": "K2 — Ägarpanelen (26 par)",
        "lage": "k2",
        "beskrivning": "Importerad från motpart/runda-4/A-domare/panel/ (blind ordning och kontrollpar oförändrade).",
        "par": par_lista,
        "nyckel": nyckel,
    }
    res = _http_post(f"{base}/api/publicera", json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json", token)
    return {
        "ok": True,
        "pass_id": pass_id,
        "antal_par": len(par_lista),
        "antal_media": len(filer_att_skicka),
        "vaggtid_sek": round(time.monotonic() - t0, 2),
        "svar": res,
    }


def publicera_spec(base_url: str, spec_fil: Path, token: str | None) -> dict[str, Any]:
    """Bygger ett blint pass från spec JSON (med olager_id + variant) och publicerar via API."""
    t0 = time.monotonic()
    spec = json.loads(spec_fil.read_text(encoding="utf-8"))
    pass_id = spec["pass_id"]
    fro = int(spec.get("fro", 20261120))
    rng = random.Random(fro)
    base = base_url.rstrip("/")

    publika: list[dict[str, Any]] = []
    nycklar: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="hagen_pub_") as td:
        tmp = Path(td)
        for post in spec["par"]:
            pid = f"p_{secrets.token_hex(5)}"
            media_ut: dict[str, dict[str, str]] = {}
            nyckel_media: dict[str, dict[str, Any]] = {}
            for roll, kalla_spec in post["media"].items():
                kalla = Path(kalla_spec["fil"])
                if not kalla.is_absolute():
                    kalla = (ROT / kalla).resolve()
                ext = kalla_spec.get("ext", "mp4")
                namn = f"m_{secrets.token_hex(8)}.{ext}"
                ut_fil = tmp / namn
                if ext == "mp4":
                    _ffmpeg_blind_video(kalla, ut_fil, vf=kalla_spec.get("vf", ""), af=kalla_spec.get("af", ""))
                else:
                    shutil.copyfile(kalla, ut_fil)
                _http_post(f"{base}/api/publicera/{pass_id}/media/{namn}?commit=0", ut_fil.read_bytes(), "application/octet-stream", token)
                media_ut[roll] = {"url": f"/pass/{pass_id}/media/{namn}", "typ": "video" if ext == "mp4" else "bild"}
                nyckel_media[roll] = {
                    "url": f"/pass/{pass_id}/media/{namn}",
                    "olager_id": kalla_spec.get("olager_id"),
                    "variant": kalla_spec.get("variant"),
                }

            publika.append({
                "id": pid,
                "lage": post.get("lage", spec.get("lage", "invarians")),
                "sektion": post.get("sektion", "invarians"),
                "rubrik": post.get("rubrik", ""),
                "mening": post.get("mening", ""),
                "etiketter": post.get("etiketter", {}),
                "media": media_ut,
                "synk": post.get("synk", True),
                "tillat_gain_komp": bool(post.get("tillat_gain_komp", False)),
            })
            nycklar.append({
                "id": pid,
                "olager_id": post.get("olager_id"),
                "variant": post.get("variant"),
                "kontroll": post.get("kontroll"),
                "forvantat": post.get("forvantat"),
                "media": nyckel_media,
            })

    ordn = list(range(len(publika)))
    rng.shuffle(ordn)
    publika_ord = []
    nycklar_ord = []
    for nr, idx in enumerate(ordn, 1):
        p = publika[idx]
        p["nr"] = nr
        publika_ord.append(p)
        nycklar_ord.append(nycklar[idx])

    payload = {
        "pass_id": pass_id,
        "titel": spec.get("titel", pass_id),
        "lage": spec.get("lage", "invarians"),
        "beskrivning": spec.get("beskrivning", ""),
        "par": publika_ord,
        "nyckel": {"fro": fro, "ordning": [p["id"] for p in publika_ord], "par": nycklar_ord},
    }
    res = _http_post(f"{base}/api/publicera", json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json", token)
    return {
        "ok": True,
        "pass_id": pass_id,
        "antal_par": len(publika_ord),
        "vaggtid_sek": round(time.monotonic() - t0, 2),
        "svar": res,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Publicera nytt bedömningspass till den stående ägarpanelen")
    ap.add_argument("--url", default=os.environ.get("PANEL_URL", "http://127.0.0.1:5191"))
    ap.add_argument("--token", default=os.environ.get("PANEL_TOKEN"))
    ap.add_argument("--importera-k2", action="store_true")
    ap.add_argument("--pass-id", default="k2-runda4")
    ap.add_argument("--spec", type=Path, default=None)
    a = ap.parse_args()

    if a.importera_k2:
        res = publicera_k2(a.url, a.pass_id, a.token)
    elif a.spec:
        res = publicera_spec(a.url, a.spec, a.token)
    else:
        raise SystemExit("Ange --importera-k2 eller --spec <fil.json>")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
