"""Lätt HTTP-jobbtjänst för en hyrd varm Linux-maskin (RunPod / Hetzner / Vast.ai) (INFRA.md §2).

Håller Silero VAD + YOLOv8n + O-lagret laddat i RAM (M6: noll kallstart) och exponerar ett
autentiserat HTTP-API över SSH-tunnel eller privat nätverk.

Start på varm maskin:
    HAGEN_WORKER_TOKEN=<hemlig_token> HAGEN_DATA_ROT=/workspace/hagen \
        python3 -m infra.varm_maskin.worker_server --host 127.0.0.1 --port 8765
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hmac
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROT = Path(__file__).resolve().parents[2]
if str(ROT) not in sys.path:
    sys.path.insert(0, str(ROT))

from infra.extraktorer import VarmExtraktor
from infra.olager import OLager, bygg_klipp, hamta_fran_url
from infra.steg2_snabb import kor_analys, mat_ref_c_klipp, mat_test_klipp


class VarmTjanstState:
    def __init__(self, data_rot: Path, token: str, workers: int) -> None:
        self.data_rot = data_rot
        self.kallor = data_rot / "kallor"
        self.olager_dir = data_rot / "olager"
        self.kallor.mkdir(parents=True, exist_ok=True)
        self.olager_dir.mkdir(parents=True, exist_ok=True)
        self.token = token
        self.workers = workers
        self.extr = VarmExtraktor(torch_threads=2)
        self.olager = OLager(self.olager_dir)
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
        self.startad = time.time()


STATE: VarmTjanstState | None = None


class Handler(BaseHTTPRequestHandler):
    def _auth_ok(self) -> bool:
        assert STATE is not None
        hdr = self.headers.get("Authorization", "")
        if not hdr.startswith("Bearer "):
            return False
        return hmac.compare_digest(hdr[7:].strip(), STATE.token)

    def _skicka(self, kod: int, obj: Any) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _las_body(self) -> dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}

    def do_GET(self) -> None:
        assert STATE is not None
        if not self._auth_ok():
            return self._skicka(401, {"ok": False, "fel": "kräver Bearer-token"})
        if self.path == "/health":
            return self._skicka(200, {
                "ok": True,
                "varm": True,
                "modeller_laddade": True,
                "extraktor_laddtid_sek": STATE.extr.laddtid_sek,
                "n_olager": len(STATE.olager.lista_klipp()),
                "workers": STATE.workers,
                "upptid_sek": round(time.time() - STATE.startad, 1),
            })
        if self.path == "/olager/lista":
            return self._skicka(200, {"klipp": STATE.olager.lista_klipp()})
        return self._skicka(404, {"ok": False, "fel": "okänd slutpunkt"})

    def do_POST(self) -> None:
        assert STATE is not None
        if not self._auth_ok():
            return self._skicka(401, {"ok": False, "fel": "kräver Bearer-token"})
        body = self._las_body()
        t0 = time.monotonic()

        if self.path == "/olager/ingest":
            url = body["url"]
            cid = body["clip_id"]
            ut_mp4 = STATE.kallor / f"{cid}.mp4"
            hamta_fran_url(url, ut_mp4, ytdlp_cmd=["yt-dlp"])
            r = bygg_klipp(cid, ut_mp4, STATE.olager_dir, STATE.extr, url=url, force=bool(body.get("force")))
            return self._skicka(200, {"ok": True, "vaggtid_sek": round(time.monotonic() - t0, 3), **r})

        if self.path == "/olager/forladda":
            r = STATE.olager.forladda_i_minnet(med_jpack=bool(body.get("med_jpack", False)))
            return self._skicka(200, {"ok": True, **r})

        if self.path == "/steg2/kor":
            ref_ids: list[str] = body["ref_ids"]
            test_ids: list[str] = body["test_ids"]
            fran_olager = bool(body.get("fran_olager", True))

            def _ref(cid: str) -> dict[str, Any]:
                cf = STATE.olager_dir / cid / "c_ref.json"
                if fran_olager and cf.exists():
                    return json.loads(cf.read_text(encoding="utf-8"))
                return mat_ref_c_klipp(cid, STATE.kallor / f"{cid}.mp4", STATE.extr)

            def _test(cid: str) -> dict[str, Any]:
                return mat_test_klipp(cid, STATE.kallor / f"{cid}.mp4", STATE.extr)

            ref_rows = list(STATE.pool.map(_ref, ref_ids))
            test_res = list(STATE.pool.map(_test, test_ids))
            test_rows = [r for tr in test_res for r in tr["rader"]]
            analys = kor_analys(ref_rows, test_rows, test_ids)
            return self._skicka(200, {
                "ok": True,
                "vaggtid_sek": round(time.monotonic() - t0, 2),
                "n_ref": len(ref_rows),
                "n_test_rader": len(test_rows),
                "analys": analys,
            })

        return self._skicka(404, {"ok": False, "fel": "okänd slutpunkt"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--data-rot", default=os.environ.get("HAGEN_DATA_ROT", "/workspace/hagen"))
    ap.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) // 2))
    a = ap.parse_args()
    token = os.environ.get("HAGEN_WORKER_TOKEN")
    if not token:
        raise SystemExit("Sätt miljövariabeln HAGEN_WORKER_TOKEN före start (§6: ingen oautentiserad tjänst).")
    global STATE
    STATE = VarmTjanstState(Path(a.data_rot), token=token, workers=a.workers)
    print(f"Varm worker lyssnar på http://{a.host}:{a.port} (workers={a.workers}, laddtid={STATE.extr.laddtid_sek}s)", flush=True)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
