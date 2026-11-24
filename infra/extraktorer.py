"""Varma extraktorer (E28, E30, E37) utan kallstart per klipp + adapter för oförändrade skript.

Design:
  - Laddar Silero VAD (ONNX) och YOLOv8n en gång i minnet (M6: noll kallstart vid normal iteration).
  - Algoritmiskt och avrundningsmässigt identisk med repots E28 (e28-tek.mjs), E30 (e30_tal.py)
    och E37 (e37_personer.py), samtidigt som scen-/tystnadslogg och VAD-intervall extraheras
    i samma pass utan dubbel avkodning.
  - Kan verifieras byte-/värde-för-värde mot de oförändrade skripten via kor_oforandrade().
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROT = Path(__file__).resolve().parents[1]

VERSIONER = {
    "e28": "e28-tek-v1",
    "e30": "e30-tal-v1",
    "e37": "e37-personer-v1",
}


def _js_round2(x: float) -> float:
    """Matchar JavaScripts Math.round(x * 100) / 100 (halvor upp mot +inf)."""
    if math.isnan(x) or math.isinf(x):
        return x
    return math.floor(x * 100.0 + 0.5) / 100.0


def _js_med(vals: list[float]) -> float:
    """Matchar e28-tek.mjs: s[Math.floor(s.length / 2)]."""
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[len(s) // 2]


def _ffmpeg_bin() -> str:
    return os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg") or "ffmpeg"


def _ffprobe_bin() -> str:
    return os.environ.get("FFPROBE_PATH") or shutil.which("ffprobe") or "ffprobe"


def sha256_fil(fil: Path) -> str:
    h = hashlib.sha256()
    with fil.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ffprobe_json(fil: Path) -> dict[str, Any]:
    p = subprocess.run(
        [_ffprobe_bin(), "-v", "error", "-show_format", "-show_streams", "-of", "json", str(fil)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return json.loads(p.stdout)


def e28_kor(fil: Path, clip_id: str, med_bilaga: bool = True, threads: int | None = None) -> dict[str, Any]:
    """Kör exakt samma ffmpeg-filtergraf som video/format/e28-tek.mjs i ett enda pass."""
    ff = _ffmpeg_bin()
    argv = [ff, "-nostdin", "-hide_banner", "-nostats"]
    if threads is not None:
        argv += ["-threads", str(threads)]
    argv += [
        "-i", str(fil),
        "-vf", "select='gte(scene,0)',metadata=print",
        "-af", "silencedetect=n=-35dB:d=0.3,ebur128=framelog=quiet",
        "-f", "null", "-",
    ]
    proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    log = proc.stderr

    # Exakt samma regex och slice(1) som video/format/e28-tek.mjs:25-38
    t = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", log)][1:]
    sc = [float(m) for m in re.findall(r"lavfi\.scene_score=([0-9.]+)", log)][1:]
    m_dur = re.search(r"Duration: (\d+):(\d+):([0-9.]+)", log)
    if m_dur:
        dur = float(m_dur.group(1)) * 3600.0 + float(m_dur.group(2)) * 60.0 + float(m_dur.group(3))
    else:
        dur = (t[-1] if t else 0.0) + 0.5
    if dur <= 0:
        dur = (t[-1] if t else 0.0) + 0.5

    n_min = min(len(t), len(sc))
    t = t[:n_min]
    sc = sc[:n_min]
    byten = [t[i] for i in range(n_min) if sc[i] > 0.3]
    gr = [0.0, *byten, dur]
    skott = [gr[i + 1] - gr[i] for i in range(len(gr) - 1) if gr[i + 1] - gr[i] > 0]

    tyst = [[float(a), float(b)] for a, b in re.findall(r"silence_start: ([0-9.]+)[\s\S]*?silence_end: ([0-9.]+)", log)]
    tyst_tid = sum(max(0.0, min(b, dur) - a) for a, b in tyst)
    forsta_ljud = tyst[0][1] if (tyst and tyst[0][0] < 0.05) else 0.0

    idx_lu = log.rfind("Integrated loudness")
    sum_txt = log[idx_lu:] if idx_lu >= 0 else ""
    m_i = re.search(r"I:\s+(-?[0-9.]+) LUFS", sum_txt)
    m_lra = re.search(r"LRA:\s+([0-9.]+) LU", sum_txt)
    lufs = float(m_i.group(1)) if m_i else None
    lra = float(m_lra.group(1)) if m_lra else None

    rorelse = (sum(sc) / len(sc)) if sc else 0.0
    tidig = [sc[i] for i in range(n_min) if t[i] < 2.0]
    sen = [sc[i] for i in range(n_min) if t[i] >= 2.0]

    skott_max = max(skott) if skott else 0.0
    if len(skott) > 1:
        skott_mean = sum(skott) / len(skott)
        skott_std = math.sqrt(sum((v - skott_mean) ** 2 for v in skott) / len(skott))
        skott_cv = skott_std / (dur / len(skott))
    else:
        skott_cv = 0.0

    if sen and rorelse:
        rorelse_kvot = (sum(tidig) / max(1, len(tidig))) / (sum(sen) / len(sen))
    else:
        rorelse_kvot = 1.0

    ut: dict[str, Any] = {
        "id": clip_id,
        "langd": _js_round2(dur),
        "byten": len(byten),
        "takt": _js_round2(len(byten) / dur),
        "skott_median": _js_round2(_js_med(skott)),
        "skott_max": _js_round2(skott_max),
        "skott_max_andel": _js_round2(skott_max / dur),
        "skott_cv": _js_round2(skott_cv),
        "forsta_byte": _js_round2(byten[0] if byten else dur),
        "byten_3s": sum(1 for x in byten if x < 3.0),
        "rorelse": _js_round2(rorelse * 100.0),
        "rorelse_2s": _js_round2(100.0 * sum(tidig) / len(tidig)) if tidig else 0.0,
        "rorelse_kvot": _js_round2(rorelse_kvot),
        "ljud_andel": _js_round2(1.0 - tyst_tid / dur),
        "pauser": len(tyst),
        "forsta_ljud": _js_round2(forsta_ljud),
        "lufs": lufs,
        "lra": lra,
        "skott": skott,
    }
    if med_bilaga:
        ut["bilaga"] = {
            "dur": dur,
            "byten_t": byten,
            "tystnad": tyst,
            "scen_antal": len(sc),
        }
    return ut


def las_wav_16k_float(wav_fil: Path) -> np.ndarray:
    """Läser 16 kHz mono s16le WAV rakt till float32 [-1, 1] utan ffmpeg."""
    with wave.open(str(wav_fil), "rb") as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == 16000
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


class VarmExtraktor:
    """Håller Silero VAD (ONNX) och YOLOv8n laddade i minnet mellan anrop (M6)."""

    def __init__(self, yolo_vikter: Path | None = None, torch_threads: int = 2) -> None:
        t0 = time.monotonic()
        os.environ.setdefault("YOLO_OFFLINE", "1")
        os.environ.setdefault("ULTRALYTICS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")

        import torch
        from silero_vad import get_speech_timestamps, load_silero_vad
        from ultralytics import YOLO

        torch.set_num_threads(torch_threads)
        self._torch = torch
        self._get_speech_timestamps = get_speech_timestamps
        self.silero = load_silero_vad(onnx=True)

        vikter = yolo_vikter or (ROT / "data" / "format" / "e37" / "yolov8n.pt")
        if not vikter.exists():
            raise FileNotFoundError(f"Saknar YOLOv8n-vikter: {vikter}")
        self.yolo_vikter = vikter
        self.yolo = YOLO(str(vikter))
        self.laddtid_sek = round(time.monotonic() - t0, 3)

    def e28(self, fil: Path, clip_id: str, med_bilaga: bool = True, threads: int | None = None) -> dict[str, Any]:
        return e28_kor(fil, clip_id, med_bilaga=med_bilaga, threads=threads)

    def e30_fran_pcm(self, x: np.ndarray, clip_id: str, med_bilaga: bool = True) -> dict[str, Any]:
        dur = len(x) / 16000.0
        if dur < 0.5:
            ut: dict[str, Any] = {
                "id": clip_id,
                "langd": dur,
                "tal_andel": 0,
                "tal_segment": 0,
                "tal_per_s": 0,
                "forsta_tal": None,
            }
            if med_bilaga:
                ut["vad"] = []
            return ut
        seg = self._get_speech_timestamps(
            self._torch.from_numpy(x),
            self.silero,
            sampling_rate=16000,
            return_seconds=True,
            min_silence_duration_ms=300,
        )
        tal = sum(s["end"] - s["start"] for s in seg)
        ut = {
            "id": clip_id,
            "langd": round(dur, 2),
            "tal_andel": round(tal / dur, 3),
            "tal_segment": len(seg),
            "tal_per_s": round(len(seg) / dur, 3),
            "forsta_tal": round(seg[0]["start"], 2) if seg else None,
        }
        if med_bilaga:
            ut["vad"] = [[s["start"], s["end"]] for s in seg]
        return ut

    def e30(self, fil: Path, clip_id: str, wav_16k: Path | None = None, med_bilaga: bool = True) -> dict[str, Any]:
        if wav_16k is not None and wav_16k.exists():
            x = las_wav_16k_float(wav_16k)
        else:
            raw = subprocess.run(
                [_ffmpeg_bin(), "-v", "quiet", "-i", str(fil), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                capture_output=True,
                timeout=120,
            ).stdout
            x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
        return self.e30_fran_pcm(x, clip_id, med_bilaga=med_bilaga)

    def e37_fran_rutor(self, rutor: list[np.ndarray], clip_id: str) -> dict[str, Any]:
        ant = (
            [
                int(sum(1 for b in r.boxes if int(b.cls) == 0 and float(b.conf) >= 0.4))
                for r in self.yolo(rutor, verbose=False, imgsz=320)
            ]
            if rutor
            else []
        )
        ut: dict[str, Any] = {"id": clip_id, "antal": ant}
        if ant:
            ut["personer_medel"] = float(np.mean(ant))
            ut["andel_minst_en"] = float(np.mean([x >= 1 for x in ant]))
            ut["andel_minst_tva"] = float(np.mean([x >= 2 for x in ant]))
            ut["personer_max"] = int(max(ant))
        return ut

    def e37(self, fil: Path, clip_id: str) -> dict[str, Any]:
        cap = cv2.VideoCapture(str(fil))
        N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        rutor: list[np.ndarray] = []
        for t in np.linspace(0.05, 0.95, 6):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * max(N - 1, 0)))
            ok, f = cap.read()
            if ok:
                rutor.append(f)
        cap.release()
        return self.e37_fran_rutor(rutor, clip_id)

    def mat_alla(
        self,
        fil: Path,
        clip_id: str,
        *,
        wav_16k: Path | None = None,
        med_bilaga: bool = True,
        ffmpeg_threads: int | None = None,
    ) -> tuple[dict[str, Any], dict[str, float]]:
        t0 = time.monotonic()
        r28 = self.e28(fil, clip_id, med_bilaga=med_bilaga, threads=ffmpeg_threads)
        t1 = time.monotonic()
        r30 = self.e30(fil, clip_id, wav_16k=wav_16k, med_bilaga=med_bilaga)
        t2 = time.monotonic()
        r37 = self.e37(fil, clip_id)
        t3 = time.monotonic()
        return (
            {"e28": r28, "e30": r30, "e37": r37},
            {"e28": round(t1 - t0, 3), "e30": round(t2 - t1, 3), "e37": round(t3 - t2, 3)},
        )


def kor_oforandrade(filer: dict[str, Path]) -> dict[str, dict[str, Any]]:
    """Tunn adapter som kör repots oförändrade e28-tek.mjs, e30_tal.py och e37_personer.py (för paritetskontroll)."""
    skript = {
        "e28": ROT / "video/format/e28-tek.mjs",
        "e30": ROT / "video/format/e30_tal.py",
        "e37": ROT / "video/format/e37_personer.py",
    }
    verktyg = ROT / "video/analys/verktyg.mjs"
    vikter = ROT / "data/format/e37/yolov8n.pt"
    stubb = (
        "import path from 'node:path'\n"
        "import { fileURLToPath } from 'node:url'\n"
        "export const DATA = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../data')\n"
    )
    py = sys.executable

    with tempfile.TemporaryDirectory(prefix="hagen_paritet_") as td:
        rot = Path(td)
        t = rot / "tree"
        (t / "video/format").mkdir(parents=True)
        (t / "video/analys").mkdir(parents=True)
        (t / "data/format/e37").mkdir(parents=True)
        for p in skript.values():
            shutil.copyfile(p, t / "video/format" / p.name)
        shutil.copyfile(verktyg, t / "video/analys/verktyg.mjs")
        (t / "video/analys/pipeline.mjs").write_text(stubb, encoding="utf-8")
        shutil.copyfile(vikter, t / "data/format/e37/yolov8n.pt")

        home = rot / "home"
        dd = home / "Downloads/letrend-e13"
        dd.mkdir(parents=True)
        for s, p in filer.items():
            try:
                os.link(p, dd / f"{s}.mp4")
            except OSError:
                shutil.copyfile(p, dd / f"{s}.mp4")

        env = dict(
            os.environ,
            USERPROFILE=str(home),
            HOME=str(home),
            PYTHONIOENCODING="utf-8",
            PYTHONUTF8="1",
            YOLO_OFFLINE="1",
            ULTRALYTICS_OFFLINE="1",
            HF_HUB_OFFLINE="1",
        )
        for cmd in (
            ["node", str(t / "video/format/e28-tek.mjs"), "--par", "1"],
            [py, "-I", "-X", "utf8", "-u", str(t / "video/format/e30_tal.py")],
            [py, "-I", "-X", "utf8", "-u", str(t / "video/format/e37_personer.py")],
        ):
            r = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(t))
            if r.returncode != 0:
                raise RuntimeError(f"Oförändrat skript misslyckades ({cmd}): {r.stderr[-600:]}")

        ut = {s: {} for s in filer}
        for k, fn in (("e28", "tek.jsonl"), ("e30", "tal.jsonl"), ("e37", "personer.jsonl")):
            f = t / "data/format" / k / fn
            if f.exists():
                for l in f.read_text(encoding="utf-8").splitlines():
                    if l.strip():
                        r = json.loads(l)
                        if r["id"] in ut:
                            ut[r["id"]][k] = r
        return ut
