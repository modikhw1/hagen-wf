# -*- coding: utf-8 -*-
"""Ägarpanelen (K2): lokal server, bara stdlib.

Start (från repo-roten):
    .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-4\\A-domare\\panel\\server.py
Öppna sedan http://127.0.0.1:5190/

Serverar index.html, /api/par (par.json), /media/m_<hex>.(mp4|png) med Range-stöd.
POST /api/svar lägger till ett svar i svar.json (växande lista, skrivs atomärt; tidigare svar
skrivs aldrig över) och i svar.logg.jsonl (ren append). nyckel.json serveras aldrig.
Miljövariabel PANEL_SVARFIL byter svarsfil (används vid verifiering: svar_test.json).
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PANEL = Path(__file__).resolve().parent
MEDIA = PANEL / "media"
SVAR = PANEL / os.environ.get("PANEL_SVARFIL", "svar.json")
LOGG = SVAR.with_suffix(".logg.jsonl")
PORT = int(os.environ.get("PANEL_PORT", "5190"))
MEDIA_RE = re.compile(r"^/media/(m_[0-9a-f]{16}\.(mp4|png))$")
LAS = threading.Lock()
TYP = {"mp4": "video/mp4", "png": "image/png"}


def spara_svar(post: dict) -> int:
    with LAS:
        lista = []
        if SVAR.exists():
            lista = json.loads(SVAR.read_text(encoding="utf-8") or "[]")
        lista.append(post)
        tmp = SVAR.with_suffix(".tmp")
        tmp.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, SVAR)
        with LOGG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(post, ensure_ascii=False) + "\n")
        return len(lista)


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if "/media/" not in (args[0] if args else ""):
            sys.stderr.write("%s %s\n" % (datetime.now().strftime("%H:%M:%S"), fmt % args))

    def _skicka(self, kod: int, data: bytes, typ: str, extra: dict | None = None):
        self.send_response(kod)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            return self._skicka(200, (PANEL / "index.html").read_bytes(), "text/html; charset=utf-8")
        if p == "/favicon.ico":
            return self._skicka(204, b"", "image/x-icon")
        if p == "/api/par":
            return self._skicka(200, (PANEL / "par.json").read_bytes(), "application/json; charset=utf-8")
        mt = MEDIA_RE.match(p)
        if mt and (MEDIA / mt.group(1)).is_file():
            return self._media(MEDIA / mt.group(1), TYP[mt.group(2)])
        return self._skicka(404, b"finns inte", "text/plain")

    def _media(self, f: Path, typ: str):
        storlek = f.stat().st_size
        rng = self.headers.get("Range")
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            a = int(m.group(1)) if m and m.group(1) else 0
            b = int(m.group(2)) if m and m.group(2) else storlek - 1
            b = min(b, storlek - 1)
            if a > b:
                return self._skicka(416, b"", typ, {"Content-Range": f"bytes */{storlek}"})
            with f.open("rb") as fh:
                fh.seek(a)
                data = fh.read(b - a + 1)
            return self._skicka(206, data, typ, {"Content-Range": f"bytes {a}-{b}/{storlek}", "Accept-Ranges": "bytes"})
        return self._skicka(200, f.read_bytes(), typ, {"Accept-Ranges": "bytes"})

    def do_POST(self):
        if self.path != "/api/svar":
            return self._skicka(404, b"finns inte", "text/plain")
        n = int(self.headers.get("Content-Length") or 0)
        try:
            d = json.loads(self.rfile.read(n).decode("utf-8"))
            assert isinstance(d, dict) and re.match(r"^p_[0-9a-f]{10}$", d.get("par", ""))
        except Exception:
            return self._skicka(400, b'{"ok":false}', "application/json")
        tillatna = {"par", "nr", "session", "a", "b", "samma_scen", "kommentar", "sekunder", "ljud_hort"}
        post = {k: d[k] for k in tillatna if k in d}
        post["tid"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        antal = spara_svar(post)
        return self._skicka(200, json.dumps({"ok": True, "antal": antal}).encode(), "application/json")


if __name__ == "__main__":
    print(f"Ägarpanelen: http://127.0.0.1:{PORT}/  (svar -> {SVAR.name})")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
