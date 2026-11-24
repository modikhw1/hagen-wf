# -*- coding: utf-8 -*-
"""Gemensamma hjälpare för medielagren: sökvägar, ffprobe/ffmpeg, JSON.

Ingen klippspecifik kod. Allt som rör ett klipp tar klippets videosökväg som indata.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

D = Path(__file__).resolve().parents[1]           # motpart/runda-3-opus/D-medielager
ROT = D.parents[2]                                 # repo-roten
SCEN_PY = ROT / "scen" / ".venv" / "Scripts" / "python.exe"   # används, ändras inte
CACHE = D / "_cache"           # återskapbart: egen venv, råa OCR-/separationsfiler
EGEN_PY = CACHE / "venv" / "Scripts" / "python.exe"            # rapidocr + demucs
_UT = Path(os.environ.get("MEDIELAGER_UT", str(D)))
LAGER = _UT / "lager"            # en mapp per klipp: tidslinje.json, stammar, rutor
FORHANDS = _UT / "forhands"      # korta förhandsvisningar per operation
WHISPER_SMALL = ROT / "scen/3d/cache/whisper/models--KBLab--kb-whisper-small/snapshots"
CLIP_VIKT = ROT / "scen/weights/clip/ViT-B-32.pt"
YOLO_SEG = ROT / "scen/py/modeller/yolo11n-seg.pt"

SCHEMA = "medielager/1"


def las(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def skriv(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def rel(p):
    """Sökväg relativt repo-roten, med snedstreck framåt."""
    try:
        return Path(p).resolve().relative_to(ROT).as_posix()
    except ValueError:
        return Path(p).as_posix()


def abs_(p):
    p = Path(p)
    if p.is_absolute():
        return p
    return (ROT / p) if (ROT / p).exists() else p.resolve()


def sha16(p, n=1 << 22):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        h.update(f.read(n))
    return h.hexdigest()[:16]


def probe(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate,nb_frames,sample_rate,channels:format=duration",
                        "-of", "json", str(video)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s.get("codec_type") == "video"), {})
    a = next((s for s in j["streams"] if s.get("codec_type") == "audio"), None)
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    return dict(langd=float(j["format"]["duration"]), bredd=int(v.get("width", 0)), hojd=int(v.get("height", 0)),
                fps=round(float(num) / float(den or 1), 3), ljud=a is not None,
                ljud_hz=int(a["sample_rate"]) if a else None)


def ff(*args, tyst=True):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-800:])
    return r


def ljud_wav(video, ut, hz=16000, mono=True):
    """Avkoda klippets ljud till wav (16 kHz mono som standard)."""
    ut = Path(ut)
    ut.parent.mkdir(parents=True, exist_ok=True)
    ff("-i", video, "-vn", "-ac", 1 if mono else 2, "-ar", hz, "-c:a", "pcm_s16le", ut)
    return ut


def kor_egen(modul, *args):
    """Kör ett steg i den egna venv:en (rapidocr, demucs) som delprocess."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    cmd = [str(EGEN_PY), "-X", "utf8", "-m", f"medielager.{modul}", *map(str, args)]
    r = subprocess.run(cmd, cwd=str(D), capture_output=True, text=True, encoding="utf-8", env=env)
    if r.returncode != 0:
        raise RuntimeError(f"{modul}: {r.stderr[-1500:]}")
    return r.stdout


def las_rutor(video, tider, bredd=None):
    """Läs rutor vid givna tider i ett sekventiellt pass (grab/retrieve), utan sökning.

    Returnerar en lista i samma ordning som tider; None där rutan saknas.
    """
    import cv2
    ordning = sorted(range(len(tider)), key=lambda i: tider[i])
    ut = [None] * len(tider)
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    mal = [min(max(0, int(round(tider[i] * fps))), max(0, n - 1)) for i in ordning]
    j, ruta = 0, -1
    while j < len(mal):
        if not cap.grab():
            break
        ruta += 1
        while j < len(mal) and mal[j] == ruta:
            ok, f = cap.retrieve()
            if ok and bredd:
                h, w = f.shape[:2]
                f = cv2.resize(f, (bredd, int(round(bredd * h / w))), interpolation=cv2.INTER_AREA)
            ut[ordning[j]] = f if ok else None
            j += 1
    cap.release()
    return ut


def klipp_id(video):
    return Path(video).stem
