"""Lokal HTTP-server för Förvärld Arbetsbord (`127.0.0.1:5199`) med Range-stöd (`206 Partial Content`) och API."""
from __future__ import annotations

import argparse
import datetime
import json
import mimetypes
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

# Säkerställ att repo-roten ligger på sys.path vid direktkörning
_HERE = Path(__file__).resolve().parent
_ROT = _HERE.parent
if str(_ROT) not in sys.path:
    sys.path.insert(0, str(_ROT))

from arbetsbord.motor.k7_vakt import K7StoppError  # noqa: E402
from arbetsbord.motor.ladda import (  # noqa: E402
    hitta_tal_fil,
    hitta_video,
    ladda_klipp,
    lista_klipp,
    lista_kunder,
)
from arbetsbord.motor.llm_regi import regissera  # noqa: E402
from arbetsbord.motor.operationer import pop_undo, utfor_operation  # noqa: E402
from arbetsbord.motor.schema import (  # noqa: E402
    ARBETSBORD_DIR,
    CACHE_AUDIO_DIR,
    CACHE_VIDEO_DIR,
    FEEDBACK_LOGG_FIL,
    ROT,
    kompilera_tillstand,
)

WEB_DIR = ARBETSBORD_DIR / "web"
THREE_VENDOR_DIR = ROT / "scen" / "3d" / "vendor"

SESSIONS: dict[str, dict[str, Any]] = {}

_MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".mp3": "audio/mpeg",
}


def _mime_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in _MIME_MAP:
        return _MIME_MAP[ext]
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def _saker_sokvag(bas: Path, rel_path: str) -> Path | None:
    ren = unquote(rel_path).lstrip("/")
    if not ren or ".." in Path(ren).parts:
        return None
    mal = (bas / ren).resolve()
    try:
        mal.relative_to(bas.resolve())
    except ValueError:
        return None
    return mal if mal.is_file() else None


def _konvertera_tal_till_wav(nyckel: str, kalla: Path) -> Path:
    """Om talspåret inte är .wav (t.ex. Demucs .flac), koda cachad .wav för exakt Chromium-skrubb."""
    if kalla.suffix.lower() == ".wav":
        return kalla
    CACHE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ut = CACHE_AUDIO_DIR / f"{nyckel}_tal.wav"
    if ut.exists() and ut.stat().st_mtime >= kalla.stat().st_mtime and ut.stat().st_size > 1000:
        return ut
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(kalla),
        "-c:a",
        "pcm_s16le",
        str(ut),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not ut.exists():
        # Fallback till originalfil om ffmpeg skulle saknas/fallera
        return kalla
    return ut


_VIDEO_H264_CACHE: dict[Path, Path] = {}


def _konvertera_video_till_h264(nyckel: str, kalla: Path) -> Path:
    """Transkoda HEVC/H.265-klipp on-demand till H.264-proxy i cache så Chromium <video> alltid kan visa bilden."""
    if kalla in _VIDEO_H264_CACHE and _VIDEO_H264_CACHE[kalla].exists():
        return _VIDEO_H264_CACHE[kalla]
    try:
        pr = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "csv=p=0",
                str(kalla),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if pr.stdout.strip().lower() == "h264":
            _VIDEO_H264_CACHE[kalla] = kalla
            return kalla
    except Exception:
        return kalla

    CACHE_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    ut = CACHE_VIDEO_DIR / f"{nyckel}_h264.mp4"
    if ut.exists() and ut.stat().st_mtime >= kalla.stat().st_mtime and ut.stat().st_size > 10000:
        _VIDEO_H264_CACHE[kalla] = ut
        return ut
    tmp = CACHE_VIDEO_DIR / f"{nyckel}_h264.tmp.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(kalla),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "19",
        "-g",
        "15",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not tmp.exists():
        tmp.unlink(missing_ok=True)
        return kalla
    tmp.replace(ut)
    _VIDEO_H264_CACHE[kalla] = ut
    return ut


class ArbetsbordHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _send_json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, code: int, data: bytes, content_type: str, cache: str = "no-store") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _send_file_range(self, path: Path, content_type: str) -> None:
        total = path.stat().st_size
        range_hdr = self.headers.get("Range")
        start = 0
        end = total - 1
        status = 200

        if range_hdr:
            m = re.match(r"bytes=(\d*)-(\d*)", range_hdr.strip())
            if not m:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{total}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            g0, g1 = m.group(1), m.group(2)
            if g0 and g1:
                start, end = int(g0), min(int(g1), total - 1)
            elif g0:
                start, end = int(g0), total - 1
            elif g1:
                suffix = int(g1)
                start = max(0, total - suffix)
                end = total - 1
            if start > end or start >= total or total == 0:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{total}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            status = 206

        length = max(0, end - start + 1)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        if self.command == "HEAD":
            return

        chunk_size = 256 * 1024
        try:
            with path.open("rb") as f:
                f.seek(start)
                kvar = length
                while kvar > 0:
                    buf = f.read(min(chunk_size, kvar))
                    if not buf:
                        break
                    self.wfile.write(buf)
                    kvar -= len(buf)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def _serve_get_or_head(self) -> None:
        u = urlparse(self.path)
        p = u.path

        if p == "/favicon.ico":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if p == "/":
            idx = WEB_DIR / "index.html"
            if not idx.exists():
                self._send_json(404, {"fel": "arbetsbord/web/index.html saknas"})
                return
            self._send_bytes(200, idx.read_bytes(), "text/html; charset=utf-8")
            return

        if p.startswith("/three/"):
            rel = p[len("/three/") :]
            f = _saker_sokvag(THREE_VENDOR_DIR, rel)
            if not f:
                self._send_json(404, {"fel": f"Three-fil saknas: {rel}"})
                return
            self._send_bytes(200, f.read_bytes(), _mime_for(f), cache="public, max-age=3600")
            return

        if p.startswith("/media/video/"):
            nyckel = unquote(p[len("/media/video/") :]).strip("/")
            try:
                vid = hitta_video(nyckel)
            except KeyError as e:
                self._send_json(404, {"fel": str(e)})
                return
            if not vid or not vid.exists():
                self._send_json(404, {"fel": f"Video saknas för '{nyckel}'"})
                return
            vid_h264 = _konvertera_video_till_h264(nyckel, vid)
            self._send_file_range(vid_h264, "video/mp4")
            return

        if p.startswith("/media/tal/"):
            nyckel = unquote(p[len("/media/tal/") :]).strip("/")
            try:
                tal_fil = hitta_tal_fil(nyckel)
            except KeyError as e:
                self._send_json(404, {"fel": str(e)})
                return
            if not tal_fil or not tal_fil.exists():
                self._send_json(404, {"fel": f"Separerat talspår saknas för '{nyckel}'"})
                return
            wav_fil = _konvertera_tal_till_wav(nyckel, tal_fil)
            self._send_file_range(wav_fil, _mime_for(wav_fil))
            return

        if p == "/api/klipp":
            self._send_json(200, lista_klipp())
            return

        if p == "/api/kunder":
            self._send_json(200, lista_kunder())
            return

        # Övriga statiska filer under arbetsbord/web/ (t.ex. /scen3d.js, /app.js, /styles.css)
        web_fil = _saker_sokvag(WEB_DIR, p)
        if web_fil:
            self._send_bytes(200, web_fil.read_bytes(), _mime_for(web_fil))
            return

        self._send_json(404, {"fel": f"Okänd sökväg: {p}"})

    def do_HEAD(self) -> None:
        self._serve_get_or_head()

    def do_GET(self) -> None:
        self._serve_get_or_head()

    def do_POST(self) -> None:
        p = urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._send_json(400, {"fel": "Ogiltig JSON-kropp"})
            return

        try:
            if p == "/api/ladda":
                klipp = body.get("klipp") or "guacamole"
                kund = body.get("kund") or None
                session, tillstand = ladda_klipp(klipp, kund)
                SESSIONS[session["session_id"]] = session
                self._send_json(200, {"session_id": session["session_id"], "tillstand": tillstand})
                return

            sid = body.get("session_id")
            if not sid or sid not in SESSIONS:
                self._send_json(400, {"fel": "Ogiltig eller saknad session_id. Ladda in ett klipp först."})
                return
            session = SESSIONS[sid]

            if p == "/api/operation":
                op = body.get("op") or ""
                params = body.get("params") or {}
                tillstand, utford = utfor_operation(session, op, params, kalla="snabb")
                self._send_json(200, {"tillstand": tillstand, "utford": utford})
                return

            if p == "/api/regi":
                text = (body.get("text") or "").strip()
                if not text:
                    self._send_json(400, {"fel": "Regitext får inte vara tom."})
                    return
                avsikt = body.get("avsikt")
                modell = body.get("modell")
                res = regissera(session, text, avsikt=avsikt, modell=modell)
                self._send_json(200, res)
                return

            if p == "/api/angra":
                tillstand = pop_undo(session)
                self._send_json(200, {"tillstand": tillstand})
                return

            if p == "/api/avsikt":
                session["avsikt"] = str(body.get("avsikt") if body.get("avsikt") is not None else (body.get("text") or "")).strip()
                session["version"] = int(session.get("version", 1)) + 1
                self._send_json(200, {"tillstand": kompilera_tillstand(session)})
                return

            if p == "/api/feedback":
                fb_id = str(body.get("feedback_id") or "")
                dom = str(body.get("dom") or "").strip()
                kommentar = str(body.get("kommentar") or "").strip()
                if not dom:
                    self._send_json(400, {"fel": "Saknar dom i feedback."})
                    return
                FEEDBACK_LOGG_FIL.parent.mkdir(parents=True, exist_ok=True)
                hist = (session.get("feedback_history") or {}).get(fb_id)
                post = {
                    "tid": datetime.datetime.now().isoformat(timespec="seconds"),
                    "session_id": sid,
                    "klipp": session["klipp"]["id"],
                    "kund": (session.get("kund") or {}).get("konto"),
                    "feedback_id": fb_id,
                    "dom": dom,
                    "kommentar": kommentar,
                    "kontext": hist,
                }
                with FEEDBACK_LOGG_FIL.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(post, ensure_ascii=False) + "\n")
                self._send_json(200, {"ok": True})
                return

            self._send_json(404, {"fel": f"Okänd POST-endpoint: {p}"})
        except K7StoppError as exc:
            self._send_json(400, {"fel": str(exc)})
        except (KeyError, ValueError) as exc:
            self._send_json(400, {"fel": str(exc)})
        except Exception as exc:
            self._send_json(500, {"fel": f"{type(exc).__name__}: {exc}"})


def starta_server(port: int = 5199, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer((host, port), ArbetsbordHandler)
    return srv


def main() -> None:
    parser = argparse.ArgumentParser(description="Förvärld Arbetsbord HTTP-server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5199")))
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    srv = starta_server(args.port, args.host)
    print(f"Arbetsbordet kör på http://{args.host}:{args.port} (klipp: {len(lista_klipp())}, kunder: {len(lista_kunder())})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
