"""Observationslagret (O-lager): beräkna en gång, läs många gånger (INFRA.md §1, M1, M3).

Struktur per klipp under <rot>/<konto>-<videoid>/:
  - meta.json               källa (URL), sha256, ffprobe, klipp.jsonl-meta, formatkort, versioner
  - rutor_540p_5fps.jpack   sammanhängande JPEG-lager (540px kortsida, 5 fps, q=78; konfigurerbart)
  - rutor_index.json        offsets, längder, tidsstämplar, upplösning och fps
  - ljud_16k_mono.wav       16 kHz mono s16le (direkt läsbar för Silero VAD / ASR)
  - ljud_orig.<ext>         originalljudet utan omkodning (-vn -c:a copy)
  - e28.json                E28 (skott, scen/tystnadsbilaga, lufs, lra)
  - e30.json                E30 (tal + VAD-intervall)
  - e37.json                E37 (6 rutor antal + personaggregat)
  - c_ref.json              (valfritt) kanonisk 30 fps C-referensmätning för steg 2
  - lager/                  framtida valfria/versionerade lager (ASR, inbäddningar, externa diagnoser)

Designad för < 50 ms läsning per klipp (M1) både från disk (utan filsystemskaos med 200 småfiler)
och < 1 ms vid RAM-cachat lager.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from infra.extraktorer import (
    VERSIONER as EXTR_VERSIONER,
    VarmExtraktor,
    _ffmpeg_bin,
    ffprobe_json,
    las_wav_16k_float,
    sha256_fil,
)

ROT = Path(__file__).resolve().parents[1]
OLAGER_SCHEMA = "olager/1"
STANDARD_FPS = 5
STANDARD_KORTSIDA = 540
STANDARD_JPEG_Q = 5  # ffmpeg mjpeg qscale 2..31 (5 ≈ JPEG q~82, skarpt men kompakt)

LAGER_VERSIONER = {
    "meta": 1,
    "rutor": f"540p_{STANDARD_FPS}fps_jpack_v1",
    "ljud": "wav16k+orig_v1",
    **EXTR_VERSIONER,
}

YTDLP_CMD = ["uvx", "--from", "yt-dlp[default,curl-cffi]==2026.10.26", "yt-dlp"]


def _iso_nu() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _atomisk_json(fil: Path, data: Any) -> None:
    fil.parent.mkdir(parents=True, exist_ok=True)
    tmp = fil.with_suffix(fil.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, fil)


def _atomisk_bytes(fil: Path, data: bytes) -> None:
    fil.parent.mkdir(parents=True, exist_ok=True)
    tmp = fil.with_suffix(fil.suffix + f".tmp.{os.getpid()}")
    tmp.write_bytes(data)
    os.replace(tmp, fil)


def ladda_repo_metadata(clip_ids: set[str] | None = None) -> dict[str, dict[str, Any]]:
    """Läser metadata ur klipp.jsonl, bibliotek-v6.json och 1-datagrund/manifest.jsonl."""
    meta: dict[str, dict[str, Any]] = {}

    klipp_fil = ROT / "byggsten/hand/ut/klipp.jsonl"
    if klipp_fil.exists():
        with klipp_fil.open("r", encoding="utf-8") as fh:
            for rad in fh:
                if not rad.strip():
                    continue
                r = json.loads(rad)
                cid = r.get("id")
                if not cid or (clip_ids is not None and cid not in clip_ids):
                    continue
                meta.setdefault(cid, {})["klipp_jsonl"] = r

    bib_fil = ROT / "data/format/harness/bibliotek-v6.json"
    if bib_fil.exists():
        bib = json.loads(bib_fil.read_text(encoding="utf-8"))
        for hylla, kort in (bib.get("hyllor") or {}).items():
            for k in kort:
                cid = k.get("id")
                if not cid or (clip_ids is not None and cid not in clip_ids):
                    continue
                meta.setdefault(cid, {})["formatkort"] = {
                    "hylla": k.get("hylla_v6") or hylla,
                    "strategi": k.get("strategi"),
                    "kantighet": k.get("kantighet"),
                    "person": k.get("person"),
                    "krok_rutnat": k.get("krok_rutnat"),
                    "karna": k.get("karna"),
                    "mall": k.get("mall"),
                    "villkor": k.get("villkor"),
                    "letrend_varde": k.get("letrend_varde"),
                    "nytta_v62": k.get("nytta_v62"),
                }

    man_fil = ROT / "motpart/runda-4/1-datagrund/manifest.jsonl"
    if man_fil.exists():
        for rad in man_fil.read_text(encoding="utf-8").splitlines():
            if not rad.strip():
                continue
            r = json.loads(rad)
            cid = r.get("id")
            if not cid or (clip_ids is not None and cid not in clip_ids):
                continue
            meta.setdefault(cid, {})["manifest_r4"] = {
                "typ": r.get("typ"),
                "utfall": r.get("utfall"),
                "langdklass": r.get("langdklass"),
                "urval": r.get("urval"),
            }

    return meta


def _splitta_mjpeg(data: bytes) -> list[bytes]:
    """Splittar sammanhängande MJPEG-ström på JPEG SOI (FFD8) / EOI (FFD9) utan temporära filer."""
    rutor: list[bytes] = []
    pos = 0
    n = len(data)
    while pos < n:
        s = data.find(b"\xff\xd8", pos)
        if s < 0:
            break
        e = data.find(b"\xff\xd9", s + 2)
        if e < 0:
            break
        rutor.append(data[s : e + 2])
        pos = e + 2
    return rutor


def extrahera_jpack(
    video: Path,
    ut_mapp: Path,
    *,
    fps: int = STANDARD_FPS,
    kortsida: int = STANDARD_KORTSIDA,
    qscale: int = STANDARD_JPEG_Q,
    threads: int | None = None,
) -> dict[str, Any]:
    """Extraherar nedskalat JPEG-lager i ett enda ffmpeg-pipe-anrop (inga lösa bildfiler)."""
    ff = _ffmpeg_bin()
    # Kortsida = min(w, h) -> 540px, jämna pixlar, behåll bildförhållande
    scale = f"scale='if(lt(iw,ih),min({kortsida},iw),-2)':'if(lt(iw,ih),-2,min({kortsida},ih))':flags=lanczos"
    argv = [ff, "-nostdin", "-hide_banner", "-loglevel", "error"]
    if threads is not None:
        argv += ["-threads", str(threads)]
    argv += [
        "-i", str(video),
        "-map", "0:v:0",
        "-vf", f"fps=fps={fps}:start_time=0:round=near,{scale}",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-q:v", str(qscale),
        "-",
    ]
    proc = subprocess.run(argv, capture_output=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg jpack fel: {proc.stderr.decode('utf-8', 'replace')[-500:]}")

    rutor = _splitta_mjpeg(proc.stdout)
    if not rutor:
        raise RuntimeError(f"Inga JPEG-rutor extraherades ur {video}")

    # Läs dimension från första rutan
    arr0 = cv2.imdecode(np.frombuffer(rutor[0], dtype=np.uint8), cv2.IMREAD_COLOR)
    h, w = (int(arr0.shape[0]), int(arr0.shape[1])) if arr0 is not None else (0, 0)

    offsets: list[int] = []
    lengths: list[int] = []
    pos = 0
    blob = bytearray()
    for r in rutor:
        offsets.append(pos)
        lengths.append(len(r))
        blob.extend(r)
        pos += len(r)

    jpack_namn = f"rutor_{kortsida}p_{fps}fps.jpack"
    _atomisk_bytes(ut_mapp / jpack_namn, bytes(blob))
    index = {
        "version": f"{kortsida}p_{fps}fps_jpack_v1",
        "fil": jpack_namn,
        "fps": fps,
        "width": w,
        "height": h,
        "n_rutor": len(rutor),
        "tidsstamplar": [round(i / fps, 4) for i in range(len(rutor))],
        "offsets": offsets,
        "lengths": lengths,
        "total_bytes": len(blob),
    }
    _atomisk_json(ut_mapp / "rutor_index.json", index)
    return index


def extrahera_ljud(video: Path, ut_mapp: Path, probe: dict[str, Any]) -> dict[str, Any]:
    """Extraherar ljud_16k_mono.wav + originalljudet (-c:a copy) i ett lätt steg."""
    ff = _ffmpeg_bin()
    audio_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
    if not audio_streams:
        return {"har_ljud": False, "wav_fil": None, "orig_fil": None}

    wav_fil = ut_mapp / "ljud_16k_mono.wav"
    r1 = subprocess.run(
        [ff, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
         "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav_fil)],
        capture_output=True, text=True, timeout=180,
    )
    if r1.returncode != 0:
        raise RuntimeError(f"ffmpeg wav16k fel: {r1.stderr[-400:]}")

    codec = (audio_streams[0].get("codec_name") or "").lower()
    ext = "m4a" if codec in ("aac", "alac") else ("mp3" if codec == "mp3" else "mka")
    orig_fil = ut_mapp / f"ljud_orig.{ext}"
    r2 = subprocess.run(
        [ff, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
         "-map", "0:a:0", "-vn", "-c:a", "copy", str(orig_fil)],
        capture_output=True, text=True, timeout=180,
    )
    if r2.returncode != 0:
        # Fallback till matroska audio-container som tar alla kodekar utan omkodning
        orig_fil = ut_mapp / "ljud_orig.mka"
        subprocess.run(
            [ff, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
             "-map", "0:a:0", "-vn", "-c:a", "copy", str(orig_fil)],
            capture_output=True, text=True, timeout=180, check=True,
        )

    return {
        "har_ljud": True,
        "codec": codec,
        "sample_rate": audio_streams[0].get("sample_rate"),
        "channels": audio_streams[0].get("channels"),
        "wav_fil": wav_fil.name,
        "wav_bytes": wav_fil.stat().st_size,
        "orig_fil": orig_fil.name,
        "orig_bytes": orig_fil.stat().st_size,
    }


def hamta_fran_url(url: str, ut_fil: Path, ytdlp_cmd: list[str] | None = None) -> Path:
    """Hämtar ett nytt klipp från TikTok-URL med fast yt-dlp-version (M3)."""
    ut_fil.parent.mkdir(parents=True, exist_ok=True)
    cmd = list(ytdlp_cmd or YTDLP_CMD)
    tmpl = str(ut_fil.with_suffix(".%(ext)s"))
    fmt = "bv*[height<=1080]+ba/b[height<=1080]/b"
    proc = subprocess.run(
        cmd + [
            "-f", fmt,
            "--merge-output-format", "mp4",
            "--no-progress",
            "--no-write-comments",
            "--socket-timeout", "30",
            "-o", tmpl,
            url,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if proc.returncode != 0 or not ut_fil.exists() or ut_fil.stat().st_size == 0:
        raise RuntimeError(f"yt-dlp misslyckades för {url}: {(proc.stderr or proc.stdout)[-500:]}")
    return ut_fil


def _sammanfatta_ffprobe(probe: dict[str, Any]) -> dict[str, Any]:
    vs = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
    aus = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
    v = vs[0] if vs else {}
    a = aus[0] if aus else {}
    fps_str = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
    try:
        num, den = fps_str.split("/")
        fps_val = round(float(num) / float(den), 3) if float(den) > 0 else 0.0
    except Exception:
        fps_val = 0.0
    return {
        "duration_s": float(probe.get("format", {}).get("duration") or v.get("duration") or 0.0),
        "size_bytes": int(probe.get("format", {}).get("size") or 0),
        "video": {
            "codec": v.get("codec_name"),
            "width": v.get("width"),
            "height": v.get("height"),
            "fps": fps_val,
            "r_frame_rate": v.get("r_frame_rate"),
            "avg_frame_rate": v.get("avg_frame_rate"),
            "pix_fmt": v.get("pix_fmt"),
            "sar": v.get("sample_aspect_ratio"),
            "color_transfer": v.get("color_transfer"),
        },
        "audio": {
            "codec": a.get("codec_name"),
            "sample_rate": a.get("sample_rate"),
            "channels": a.get("channels"),
            "bit_rate": a.get("bit_rate"),
        } if a else None,
    }


def bygg_klipp(
    clip_id: str,
    video_fil: Path,
    olager_rot: Path,
    extraktor: VarmExtraktor,
    *,
    url: str | None = None,
    extra_meta: dict[str, Any] | None = None,
    fps: int = STANDARD_FPS,
    kortsida: int = STANDARD_KORTSIDA,
    force: bool = False,
    ffmpeg_threads: int | None = None,
) -> dict[str, Any]:
    """Bygger (eller uppdaterar versionsstyrt) O-lagret för ett klipp."""
    t0 = time.monotonic()
    ut_mapp = Path(olager_rot) / clip_id
    ut_mapp.mkdir(parents=True, exist_ok=True)
    (ut_mapp / "lager").mkdir(exist_ok=True)

    meta_fil = ut_mapp / "meta.json"
    bef = json.loads(meta_fil.read_text(encoding="utf-8")) if meta_fil.exists() else {}
    bef_ver = bef.get("lager_versioner", {})
    orig_hash = sha256_fil(video_fil)
    samma_kalla = (bef.get("original_sha256") == orig_hash) and not force

    konto, videoid = clip_id.rsplit("-", 1) if "-" in clip_id else ("okand", clip_id)
    kalla_url = url or f"https://www.tiktok.com/@{konto}/video/{videoid}"

    tider: dict[str, float] = {}
    probe = ffprobe_json(video_fil)
    probe_sum = _sammanfatta_ffprobe(probe)

    # 1. Rutor (JPEG-lager)
    rutor_ver = f"{kortsida}p_{fps}fps_jpack_v1"
    rutor_idx_fil = ut_mapp / "rutor_index.json"
    if not (samma_kalla and bef_ver.get("rutor") == rutor_ver and rutor_idx_fil.exists()):
        ta = time.monotonic()
        rutor_info = extrahera_jpack(video_fil, ut_mapp, fps=fps, kortsida=kortsida, threads=ffmpeg_threads)
        tider["rutor"] = round(time.monotonic() - ta, 3)
    else:
        rutor_info = json.loads(rutor_idx_fil.read_text(encoding="utf-8"))
        tider["rutor"] = 0.0

    # 2. Ljud (16 kHz mono WAV + originalljud)
    wav_fil = ut_mapp / "ljud_16k_mono.wav"
    if not (samma_kalla and bef_ver.get("ljud") == LAGER_VERSIONER["ljud"] and (wav_fil.exists() or not probe_sum["audio"])):
        ta = time.monotonic()
        ljud_info = extrahera_ljud(video_fil, ut_mapp, probe)
        tider["ljud"] = round(time.monotonic() - ta, 3)
    else:
        ljud_info = bef.get("ljud", {"har_ljud": wav_fil.exists(), "wav_fil": wav_fil.name})
        tider["ljud"] = 0.0

    # 3. E28, E30 (direkt från ljud_16k_mono.wav!), E37
    if not (samma_kalla and bef_ver.get("e28") == EXTR_VERSIONER["e28"] and (ut_mapp / "e28.json").exists()):
        ta = time.monotonic()
        e28 = extraktor.e28(video_fil, clip_id, med_bilaga=True, threads=ffmpeg_threads)
        _atomisk_json(ut_mapp / "e28.json", e28)
        tider["e28"] = round(time.monotonic() - ta, 3)
    else:
        tider["e28"] = 0.0

    if not (samma_kalla and bef_ver.get("e30") == EXTR_VERSIONER["e30"] and (ut_mapp / "e30.json").exists()):
        ta = time.monotonic()
        e30 = extraktor.e30(video_fil, clip_id, wav_16k=wav_fil if wav_fil.exists() else None, med_bilaga=True)
        _atomisk_json(ut_mapp / "e30.json", e30)
        tider["e30"] = round(time.monotonic() - ta, 3)
    else:
        tider["e30"] = 0.0

    if not (samma_kalla and bef_ver.get("e37") == EXTR_VERSIONER["e37"] and (ut_mapp / "e37.json").exists()):
        ta = time.monotonic()
        e37 = extraktor.e37(video_fil, clip_id)
        _atomisk_json(ut_mapp / "e37.json", e37)
        tider["e37"] = round(time.monotonic() - ta, 3)
    else:
        tider["e37"] = 0.0

    # 4. Meta
    meta = {
        "schema": OLAGER_SCHEMA,
        "id": clip_id,
        "konto": konto,
        "videoid": videoid,
        "url": kalla_url,
        "original_sha256": orig_hash,
        "original_storlek": video_fil.stat().st_size,
        "ffprobe": probe_sum,
        "ljud": ljud_info,
        "rutor": {
            "version": rutor_ver,
            "fil": rutor_info["fil"],
            "fps": rutor_info["fps"],
            "width": rutor_info["width"],
            "height": rutor_info["height"],
            "n_rutor": rutor_info["n_rutor"],
            "total_bytes": rutor_info["total_bytes"],
        },
        "lager_versioner": {
            "meta": LAGER_VERSIONER["meta"],
            "rutor": rutor_ver,
            "ljud": LAGER_VERSIONER["ljud"],
            **EXTR_VERSIONER,
        },
        "uppdaterad": _iso_nu(),
    }
    if extra_meta:
        meta["repo_meta"] = extra_meta
    elif "repo_meta" in bef:
        meta["repo_meta"] = bef["repo_meta"]

    _atomisk_json(meta_fil, meta)
    total_bytes = sum(p.stat().st_size for p in ut_mapp.rglob("*") if p.is_file())
    return {
        "id": clip_id,
        "sek": round(time.monotonic() - t0, 3),
        "tider": tider,
        "n_rutor": rutor_info["n_rutor"],
        "olager_bytes": total_bytes,
    }


class OLager:
    """Snabb läsare för O-lagret (M1: < 50 ms per klipp från disk, < 1 ms från RAM-cache)."""

    def __init__(self, rot: Path) -> None:
        self.rot = Path(rot)
        self._ram_cache: dict[str, dict[str, Any]] = {}

    def lista_klipp(self) -> list[str]:
        if not self.rot.exists():
            return []
        return sorted(p.name for p in self.rot.iterdir() if p.is_dir() and (p / "meta.json").exists())

    def las_klipp(
        self,
        clip_id: str,
        *,
        ladda_ljud: bool = True,
        ladda_jpack_bytes: bool = False,
        dekoda_rutor: list[int] | None = None,
        anvand_cache: bool = False,
    ) -> dict[str, Any]:
        """Läser ett klipp ur O-lagret. Designad för < 50 ms på lokal NVMe/SSD."""
        if anvand_cache and clip_id in self._ram_cache:
            post = self._ram_cache[clip_id]
        else:
            d = self.rot / clip_id
            post = {
                "id": clip_id,
                "meta": json.loads((d / "meta.json").read_bytes()),
                "e28": json.loads((d / "e28.json").read_bytes()) if (d / "e28.json").exists() else None,
                "e30": json.loads((d / "e30.json").read_bytes()) if (d / "e30.json").exists() else None,
                "e37": json.loads((d / "e37.json").read_bytes()) if (d / "e37.json").exists() else None,
                "rutor_index": json.loads((d / "rutor_index.json").read_bytes()) if (d / "rutor_index.json").exists() else None,
                "c_ref": json.loads((d / "c_ref.json").read_bytes()) if (d / "c_ref.json").exists() else None,
            }
            if ladda_ljud:
                wav = d / "ljud_16k_mono.wav"
                post["ljud_16k"] = las_wav_16k_float(wav) if wav.exists() else None
            if ladda_jpack_bytes and post["rutor_index"]:
                jp = d / post["rutor_index"]["fil"]
                post["jpack_bytes"] = jp.read_bytes() if jp.exists() else None
            if anvand_cache:
                self._ram_cache[clip_id] = post

        if dekoda_rutor is not None and post.get("rutor_index"):
            idx = post["rutor_index"]
            d = self.rot / clip_id
            raw = post.get("jpack_bytes")
            rutor_arr: list[np.ndarray] = []
            if raw is not None:
                for i in dekoda_rutor:
                    off, ln = idx["offsets"][i], idx["lengths"][i]
                    rutor_arr.append(cv2.imdecode(np.frombuffer(raw[off : off + ln], dtype=np.uint8), cv2.IMREAD_COLOR))
            else:
                with (d / idx["fil"]).open("rb") as fh:
                    for i in dekoda_rutor:
                        fh.seek(idx["offsets"][i])
                        buf = fh.read(idx["lengths"][i])
                        rutor_arr.append(cv2.imdecode(np.frombuffer(buf, dtype=np.uint8), cv2.IMREAD_COLOR))
            post = dict(post, dekodade_rutor=rutor_arr)
        return post

    def forladda_i_minnet(self, clip_ids: list[str] | None = None, med_jpack: bool = False) -> dict[str, Any]:
        """Laddar O-lagret i RAM på varm maskin (64 GB RAM håller lätt 1 000+ klipp)."""
        t0 = time.monotonic()
        ids = clip_ids or self.lista_klipp()
        for cid in ids:
            self.las_klipp(cid, ladda_ljud=True, ladda_jpack_bytes=med_jpack, anvand_cache=True)
        return {"antal": len(ids), "sek": round(time.monotonic() - t0, 3), "med_jpack": med_jpack}

    def spara_valfritt_lager(
        self,
        clip_id: str,
        namn: str,
        version: str,
        data: dict[str, Any],
        *,
        ar_diagnos: bool = False,
    ) -> Path:
        """Lagrar ett valfritt/versionerat lager (t.ex. ASR, inbäddning, extern diagnos) separat från mätlagren."""
        d = self.rot / clip_id / "lager"
        d.mkdir(parents=True, exist_ok=True)
        fil = d / f"{namn}.json"
        post = {
            "lager": namn,
            "version": version,
            "kategori": "diagnos" if ar_diagnos else "valfritt_lager",
            "uppdaterad": _iso_nu(),
            "data": data,
        }
        _atomisk_json(fil, post)
        return fil
