"""Ägarpanelen som stående tjänst (INFRA.md §4, §6, M5).

Bygger vidare på motpart/runda-4/A-domare/panel/:
  - Blind, slumpade id:n (p_<hex>, m_<hex>), kontrollpar.
  - nyckel.json serveras ALDRIG publikt (404).
  - Svaren läggs till atomärt i svar.json och svar.logg.jsonl och skrivs aldrig över.
  - Ägarens kommentarer sparas ordagrant.
  - Original, varianter och svar kopplas till O-lagrets id i nyckel.json.
  - Autentisering krävs med token (cookie eller Bearer) när tjänsten exponeras (§6).
  - API för att publicera nytt bedömningspass på < 1 min (M5) och synka svar tillbaka till repot.

Start lokalt:
    .\\scen\\.venv\\Scripts\\python.exe infra\\panel\\tjanst.py --port 5191
"""
from __future__ import annotations

import argparse
import base64
import hmac
import json
import os
import re
import secrets
import sys
import threading
import urllib.parse
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
INDEX_HTML = HERE / "index.html"

PASS_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
MEDIA_FIL_RE = re.compile(r"^m_[0-9a-f]{16}\.(mp4|png|jpg|webp)$")
PAR_ID_RE = re.compile(r"^p_[0-9a-f]{10}$")

MIME = {
    "mp4": "video/mp4",
    "png": "image/png",
    "jpg": "image/jpeg",
    "webp": "image/webp",
}

TILLATNA_SVARSFALT = {
    "par", "nr", "session", "kommentar", "sekunder", "ljud_hort",
    # K2-fält
    "a", "b", "samma_scen",
    # Steg 2 (invarians A2)-fält
    "samma_handling", "samma_tempo", "samma_energi", "snabbare", "gain_komp_db",
    # Steg 3 (par_ingrepp B5)-fält
    "riktning_a_tempo", "riktning_b_tempo", "riktning_a_energi", "riktning_b_energi",
    "omsesidig_tempo", "omsesidig_energi", "avsikt_a", "avsikt_b", "skilja_ab",
    "sammanhang_a", "sammanhang_b", "godkann_forsta", "rattelser_bedomd", "felkategori",
}


def _iso_nu() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _atomisk_json(fil: Path, data: Any) -> None:
    fil.parent.mkdir(parents=True, exist_ok=True)
    tmp = fil.with_suffix(fil.suffix + f".tmp.{os.getpid()}.{secrets.token_hex(3)}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, fil)


class PanelLagring:
    """Trådsäker lagring av flera bedömningspass med append-only svar och strikt nyckelseparation."""

    def __init__(self, rot: Path, on_write: Any = None) -> None:
        self.rot = Path(rot)
        self.pass_dir = self.rot / "pass"
        self.pass_dir.mkdir(parents=True, exist_ok=True)
        self._las = threading.Lock()
        self._on_write = on_write  # t.ex. vol.commit() på Modal

    def _commit(self) -> None:
        if self._on_write is not None:
            self._on_write()

    def _pass_mapp(self, pass_id: str) -> Path:
        if not PASS_ID_RE.match(pass_id):
            raise ValueError(f"Ogiltigt pass_id: {pass_id}")
        return self.pass_dir / pass_id

    def lista_pass(self) -> list[dict[str, Any]]:
        ut: list[dict[str, Any]] = []
        if not self.pass_dir.exists():
            return ut
        for d in sorted(self.pass_dir.iterdir(), reverse=True):
            mf = d / "meta.json"
            if not (d.is_dir() and mf.exists()):
                continue
            meta = json.loads(mf.read_text(encoding="utf-8"))
            sf = d / "svar.json"
            svar = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else []
            besvarade = len({s.get("par") for s in svar if s.get("par")})
            ut.append({
                "pass_id": d.name,
                "titel": meta.get("titel", d.name),
                "lage": meta.get("lage", "k2"),
                "beskrivning": meta.get("beskrivning", ""),
                "skapad": meta.get("skapad"),
                "status": meta.get("status", "aktiv"),
                "antal_par": meta.get("antal_par", 0),
                "besvarade_par": besvarade,
                "antal_svar": len(svar),
            })
        ut.sort(key=lambda x: (x.get("skapad") or ""), reverse=True)
        return ut

    def las_par(self, pass_id: str) -> dict[str, Any] | None:
        d = self._pass_mapp(pass_id)
        pf = d / "par.json"
        if not pf.exists():
            return None
        data = json.loads(pf.read_text(encoding="utf-8"))
        mf = d / "meta.json"
        meta = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
        sf = d / "svar.json"
        svar = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else []
        senast: dict[str, dict] = {}
        for s in svar:
            if s.get("par"):
                senast[s["par"]] = s
        return {
            "pass_id": pass_id,
            "meta": meta,
            "par": data.get("par", []),
            "sparade_svar": senast,
        }

    def media_fil(self, pass_id: str, namn: str) -> Path | None:
        if not MEDIA_FIL_RE.match(namn):
            return None
        f = self._pass_mapp(pass_id) / "media" / namn
        return f if f.is_file() else None

    def spara_svar(self, pass_id: str, in_data: dict[str, Any]) -> int:
        if not isinstance(in_data, dict) or not PAR_ID_RE.match(str(in_data.get("par", ""))):
            raise ValueError("Ogiltigt par-id")
        d = self._pass_mapp(pass_id)
        if not (d / "par.json").exists():
            raise FileNotFoundError(f"Pass saknas: {pass_id}")
        post = {k: in_data[k] for k in TILLATNA_SVARSFALT if k in in_data}
        # Säkerställ ordagrant bevarande av kommentar (ingen trimning eller omskrivning)
        if "kommentar" in in_data and in_data["kommentar"] is not None:
            post["kommentar"] = str(in_data["kommentar"])
        post["pass_id"] = pass_id
        post["tid"] = _iso_nu()

        with self._las:
            sf = d / "svar.json"
            lf = d / "svar.logg.jsonl"
            lista = json.loads(sf.read_text(encoding="utf-8") or "[]") if sf.exists() else []
            lista.append(post)
            _atomisk_json(sf, lista)
            with lf.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(post, ensure_ascii=False) + "\n")
            self._commit()
            return len(lista)

    def spara_media(self, pass_id: str, namn: str, data: bytes, commit: bool = True) -> dict[str, Any]:
        if not MEDIA_FIL_RE.match(namn):
            raise ValueError(f"Ogiltigt medianamn (måste vara blind m_<16hex>.<ext>): {namn}")
        d = self._pass_mapp(pass_id) / "media"
        d.mkdir(parents=True, exist_ok=True)
        fil = d / namn
        tmp = fil.with_suffix(fil.suffix + f".tmp.{secrets.token_hex(3)}")
        tmp.write_bytes(data)
        os.replace(tmp, fil)
        if commit:
            self._commit()
        return {"ok": True, "pass_id": pass_id, "fil": namn, "bytes": len(data)}

    def publicera_pass(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Publicerar ett nytt blint bedömningspass atomärt (< 1 s för metadata + ev. inline-media)."""
        pass_id = str(payload["pass_id"])
        d = self._pass_mapp(pass_id)
        if (d / "svar.json").exists() and not payload.get("tillat_ny_version"):
            raise ValueError(f"Pass {pass_id} har redan svar och får inte skrivas över.")

        par_lista = payload["par"]
        nyckel = payload["nyckel"]
        # Säkerställ att alla par har blinda p_<hex>-id:n
        for p in par_lista:
            if not PAR_ID_RE.match(str(p.get("id", ""))):
                raise ValueError(f"Par saknar giltigt blint id (p_<10hex>): {p.get('id')}")

        with self._las:
            (d / "media").mkdir(parents=True, exist_ok=True)
            for namn, b64 in (payload.get("media_b64") or {}).items():
                if not MEDIA_FIL_RE.match(namn):
                    raise ValueError(f"Ogiltigt medianamn: {namn}")
                (d / "media" / namn).write_bytes(base64.b64decode(b64))

            meta = {
                "pass_id": pass_id,
                "titel": payload.get("titel", pass_id),
                "lage": payload.get("lage", "k2"),
                "beskrivning": payload.get("beskrivning", ""),
                "skapad": _iso_nu(),
                "status": "aktiv",
                "antal_par": len(par_lista),
            }
            _atomisk_json(d / "meta.json", meta)
            _atomisk_json(d / "par.json", {"par": par_lista})
            _atomisk_json(d / "nyckel.json", nyckel)
            self._commit()
        return {"ok": True, "pass_id": pass_id, "antal_par": len(par_lista), "url_sokvag": f"/pass/{pass_id}"}

    def exportera_pass(self, pass_id: str) -> dict[str, Any]:
        d = self._pass_mapp(pass_id)
        if not (d / "meta.json").exists():
            raise FileNotFoundError(f"Pass saknas: {pass_id}")
        sf = d / "svar.json"
        lf = d / "svar.logg.jsonl"
        nf = d / "nyckel.json"
        return {
            "pass_id": pass_id,
            "meta": json.loads((d / "meta.json").read_text(encoding="utf-8")),
            "svar": json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else [],
            "logg_jsonl": lf.read_text(encoding="utf-8") if lf.exists() else "",
            "nyckel": json.loads(nf.read_text(encoding="utf-8")) if nf.exists() else None,
        }


def _kontrollera_auth(
    headers: dict[str, str],
    query: dict[str, list[str]],
    token: str | None,
) -> tuple[bool, bool]:
    """Returnerar (godkand, satt_cookie). Om token är None (ren localhost) är allt godkänt."""
    if not token:
        return True, False
    # 1. Bearer header (API)
    auth = headers.get("authorization", "")
    if auth.startswith("Bearer ") and hmac.compare_digest(auth[7:].strip(), token):
        return True, False
    # 2. Cookie (webbläsare)
    raw_cookie = headers.get("cookie", "")
    if raw_cookie:
        c = SimpleCookie()
        c.load(raw_cookie)
        m = c.get("hagen_panel_auth")
        if m and hmac.compare_digest(m.value, token):
            return True, False
    # 3. Query ?token=... -> godkänn och sätt HttpOnly-cookie
    qtok = (query.get("token") or [""])[0]
    if qtok and hmac.compare_digest(qtok, token):
        return True, True
    return False, False


def hantera_request(
    method: str,
    raw_path: str,
    headers_in: dict[str, str],
    body: bytes,
    lagring: PanelLagring,
    token: str | None,
) -> tuple[int, dict[str, str], bytes]:
    """Protokollagnostisk router (används av både lokal stdlib-server och Modal ASGI-app)."""
    headers = {k.lower(): v for k, v in headers_in.items()}
    parsed = urllib.parse.urlsplit(raw_path)
    path = parsed.path
    query = urllib.parse.parse_qs(parsed.query)

    if path == "/health":
        return 200, {"Content-Type": "application/json"}, json.dumps({"ok": True, "antal_pass": len(lagring.lista_pass())}).encode()

    # Skydda nyckel.json OAVSETT sökväg eller autentisering (utom admin-export API)
    if "nyckel.json" in path:
        return 404, {"Content-Type": "text/plain; charset=utf-8"}, b"finns inte"

    ok, satt_cookie = _kontrollera_auth(headers, query, token)
    if not ok:
        if path.startswith("/api/"):
            return 401, {"Content-Type": "application/json"}, b'{"ok":false,"fel":"kraver autentisering"}'
        login_html = (
            "<!doctype html><html lang='sv'><head><meta charset='utf-8'><title>Ägarpanelen</title>"
            "<style>body{background:#16181c;color:#eceef1;font:16px system-ui;display:grid;place-items:center;min-height:100vh;margin:0}"
            "form{background:#22252b;padding:24px 28px;border-radius:10px;display:grid;gap:12px;width:min(380px,92vw)}"
            "input,button{font:inherit;padding:9px 12px;border-radius:6px;border:1px solid #3a3f47;background:#16181c;color:#eceef1}"
            "button{background:#5aa2ff;color:#08111f;border:none;font-weight:600;cursor:pointer}</style></head>"
            "<body><form method='get' action='/'><strong>Ägarpanelen</strong>"
            "<input type='password' name='token' placeholder='Åtkomstnyckel' required autofocus>"
            "<button type='submit'>Öppna</button></form></body></html>"
        ).encode("utf-8")
        return 401, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}, login_html

    if satt_cookie and method == "GET" and not path.startswith("/api/"):
        ren_url = path or "/"
        cookie_val = f"hagen_panel_auth={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=2592000"
        return 302, {"Location": ren_url, "Set-Cookie": cookie_val, "Cache-Control": "no-store"}, b""

    if method in ("GET", "HEAD"):
        if path in ("/", "/index.html") or re.match(r"^/pass/[a-z0-9][a-z0-9_-]{1,63}/?$", path):
            html = INDEX_HTML.read_bytes()
            return 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}, (b"" if method == "HEAD" else html)
        if path == "/favicon.ico":
            return 204, {"Content-Type": "image/x-icon"}, b""
        if path == "/api/pass":
            raw = json.dumps({"pass": lagring.lista_pass()}, ensure_ascii=False).encode("utf-8")
            return 200, {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}, raw

        m_par = re.match(r"^/api/pass/([a-z0-9][a-z0-9_-]{1,63})/par$", path)
        if m_par:
            data = lagring.las_par(m_par.group(1))
            if data is None:
                return 404, {"Content-Type": "application/json"}, b'{"ok":false,"fel":"pass saknas"}'
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            return 200, {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}, raw

        m_exp = re.match(r"^/api/export/([a-z0-9][a-z0-9_-]{1,63})$", path)
        if m_exp:
            # Export med nyckel kräver uttrycklig Bearer-header (inte vanlig webbläsarcookie)
            auth = headers.get("authorization", "")
            if token and not (auth.startswith("Bearer ") and hmac.compare_digest(auth[7:].strip(), token)):
                return 403, {"Content-Type": "application/json"}, b'{"ok":false,"fel":"kraver Bearer-token"}'
            try:
                raw = json.dumps(lagring.exportera_pass(m_exp.group(1)), ensure_ascii=False).encode("utf-8")
                return 200, {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}, raw
            except FileNotFoundError:
                return 404, {"Content-Type": "application/json"}, b'{"ok":false,"fel":"pass saknas"}'

        m_med = re.match(r"^/pass/([a-z0-9][a-z0-9_-]{1,63})/media/(m_[0-9a-f]{16}\.(mp4|png|jpg|webp))$", path)
        if m_med:
            f = lagring.media_fil(m_med.group(1), m_med.group(2))
            if f is None:
                return 404, {"Content-Type": "text/plain"}, b"finns inte"
            typ = MIME[m_med.group(3)]
            storlek = f.stat().st_size
            rng = headers.get("range")
            if rng:
                mr = re.match(r"bytes=(\d*)-(\d*)", rng)
                a = int(mr.group(1)) if mr and mr.group(1) else 0
                b = int(mr.group(2)) if mr and mr.group(2) else storlek - 1
                b = min(b, storlek - 1)
                if a > b:
                    return 416, {"Content-Type": typ, "Content-Range": f"bytes */{storlek}"}, b""
                with f.open("rb") as fh:
                    fh.seek(a)
                    chunk = fh.read(b - a + 1)
                hdrs = {"Content-Type": typ, "Content-Range": f"bytes {a}-{b}/{storlek}", "Accept-Ranges": "bytes", "Cache-Control": "no-store"}
                return 206, hdrs, (b"" if method == "HEAD" else chunk)
            data = b"" if method == "HEAD" else f.read_bytes()
            return 200, {"Content-Type": typ, "Accept-Ranges": "bytes", "Content-Length": str(storlek), "Cache-Control": "no-store"}, data

        return 404, {"Content-Type": "text/plain"}, b"finns inte"

    if method == "POST":
        m_sv = re.match(r"^/api/pass/([a-z0-9][a-z0-9_-]{1,63})/svar$", path)
        if m_sv:
            try:
                d = json.loads(body.decode("utf-8"))
                antal = lagring.spara_svar(m_sv.group(1), d)
                return 200, {"Content-Type": "application/json"}, json.dumps({"ok": True, "antal": antal}).encode()
            except Exception as exc:
                return 400, {"Content-Type": "application/json"}, json.dumps({"ok": False, "fel": str(exc)}).encode()

        # Publicerings-API kräver Bearer-token om token är satt
        auth = headers.get("authorization", "")
        if token and not (auth.startswith("Bearer ") and hmac.compare_digest(auth[7:].strip(), token)):
            return 403, {"Content-Type": "application/json"}, b'{"ok":false,"fel":"kraver Bearer-token"}'

        if path == "/api/publicera":
            try:
                d = json.loads(body.decode("utf-8"))
                res = lagring.publicera_pass(d)
                return 200, {"Content-Type": "application/json"}, json.dumps(res, ensure_ascii=False).encode("utf-8")
            except Exception as exc:
                return 400, {"Content-Type": "application/json"}, json.dumps({"ok": False, "fel": str(exc)}).encode()

        m_up = re.match(r"^/api/publicera/([a-z0-9][a-z0-9_-]{1,63})/media/(m_[0-9a-f]{16}\.(mp4|png|jpg|webp))$", path)
        if m_up:
            try:
                do_commit = (query.get("commit") or ["1"])[0] != "0"
                res = lagring.spara_media(m_up.group(1), m_up.group(2), body, commit=do_commit)
                return 200, {"Content-Type": "application/json"}, json.dumps(res).encode("utf-8")
            except Exception as exc:
                return 400, {"Content-Type": "application/json"}, json.dumps({"ok": False, "fel": str(exc)}).encode()

        return 404, {"Content-Type": "text/plain"}, b"finns inte"

    return 405, {"Content-Type": "text/plain"}, b"metod ej tillaten"


def skapa_http_server(host: str, port: int, rot: Path, token: str | None) -> ThreadingHTTPServer:
    lagring = PanelLagring(rot)

    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            msg = fmt % args if args else fmt
            msg = re.sub(r"token=[^&\s\"']+", "token=***", msg)
            if "/media/" not in msg:
                sys.stderr.write(f"{datetime.now().strftime('%H:%M:%S')} {msg}\n")

        def _kor(self) -> None:
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n > 0 else b""
            hdrs = {k: v for k, v in self.headers.items()}
            kod, out_hdrs, data = hantera_request(self.command, self.path, hdrs, body, lagring, token)
            self.send_response(kod)
            if "Content-Length" not in out_hdrs:
                self.send_header("Content-Length", str(len(data)))
            for k, v in out_hdrs.items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD" and data:
                self.wfile.write(data)

        do_GET = _kor
        do_HEAD = _kor
        do_POST = _kor

    return ThreadingHTTPServer((host, port), H)


def skapa_asgi_app(lagring: PanelLagring, token: str | None):
    """Minimal ASGI-app för driftsättning som alltid-uppe Modal web endpoint utan FastAPI-krav."""
    async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "lifespan":
            while True:
                msg = await receive()
                if msg["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif msg["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
            return
        if scope["type"] != "http":
            return
        method = scope["method"]
        raw_path = scope["path"]
        qs = scope.get("query_string", b"").decode("latin-1")
        if qs:
            raw_path = f"{raw_path}?{qs}"
        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers", [])}
        chunks = []
        while True:
            ev = await receive()
            chunks.append(ev.get("body", b""))
            if not ev.get("more_body", False):
                break
        body = b"".join(chunks)
        kod, out_hdrs, data = hantera_request(method, raw_path, headers, body, lagring, token)
        if "Content-Length" not in out_hdrs:
            out_hdrs["Content-Length"] = str(len(data))
        await send({
            "type": "http.response.start",
            "status": kod,
            "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in out_hdrs.items()],
        })
        await send({"type": "http.response.body", "body": b"" if method == "HEAD" else data})

    return app


def main() -> int:
    ap = argparse.ArgumentParser(description="Ägarpanelen som stående tjänst")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PANEL_PORT", "5191")))
    ap.add_argument("--data-rot", default=os.environ.get("PANEL_DATA_ROT", str(HERE.parent.parent / "data" / "panel")))
    ap.add_argument("--token", default=os.environ.get("PANEL_TOKEN"))
    a = ap.parse_args()

    if a.host not in ("127.0.0.1", "localhost") and not a.token:
        raise SystemExit("Säkerhetskrav (§6): sätt --token eller PANEL_TOKEN när panelen binder utanför localhost.")

    srv = skapa_http_server(a.host, a.port, Path(a.data_rot), a.token)
    print(f"Ägarpanelen (stående tjänst): http://{a.host}:{a.port}/  (data -> {a.data_rot})", flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
