"""Granskningsbord A/B(/C) för Due Piani. Läser paket, skriver bara ägarsvar (append-only). Inga externa anrop."""
from __future__ import annotations
import argparse, hashlib, json, math, mimetypes, re, threading, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / 'ut'
VIDEO = ROOT / 'data/format/kontroll/klipp/duepiani-7650849186912406806.mp4'
VARIANTER = {
    'A': ('A · fryst baslinje', ROOT / 'arbetsbord/data/ingest_v2/duepiani/paket.json', None),
    'B': ('B · bildstöd, utan image-gen', OUT / 'paket_B.json', OUT / 'recept_B.json'),
    'C': ('C · B + image-gen-karta', OUT / 'paket_C.json', OUT / 'recept_C.json'),
}
LOCK = threading.Lock()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def variant(key):
    name, fil, recept = VARIANTER[key]
    if not fil.is_file():
        raise KeyError(key)
    return {'id': key, 'name': name, 'package': json.loads(fil.read_text(encoding='utf-8')),
            'recept': json.loads(recept.read_text(encoding='utf-8')) if recept and recept.is_file() else None,
            'provenance': {'paket': fil.relative_to(ROOT).as_posix(), 'paket_sha256': sha(fil),
                           'renderer_sha256': sha(ROOT / 'arbetsbord/web/scen3d.js'), 'kalla_sha256': sha(VIDEO)}}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def js(self, value, status=200):
        raw = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw))); self.send_header('Cache-Control', 'no-store'); self.end_headers()
        self.wfile.write(raw)

    def send_file(self, path):
        if not path.is_file():
            return self.send_error(404)
        size = path.stat().st_size; start, end, partial = 0, size - 1, False
        rq = self.headers.get('Range')
        if rq:
            m = re.fullmatch(r'bytes=(\d+)-(\d*)', rq)
            if not m:
                return self.send_error(416)
            start = int(m[1]); end = min(int(m[2]), size - 1) if m[2] else size - 1
            if start > end:
                return self.send_error(416)
            partial = True
        self.send_response(206 if partial else 200)
        mime = {'.js': 'text/javascript', '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8'}.get(path.suffix) or mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        self.send_header('Content-Type', mime); self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Accept-Ranges', 'bytes'); self.send_header('Cache-Control', 'no-cache')
        if partial:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            with path.open('rb') as s:
                s.seek(start); left = end - start + 1
                while left:
                    b = s.read(min(left, 65536))
                    if not b:
                        break
                    self.wfile.write(b); left -= len(b)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_GET(self):
        p = urlparse(self.path).path
        files = {'/': HERE / 'index.html', '/app.js': HERE / 'app.js', '/style.css': ROOT / 'motpart/runda-4/4-visuell-loop/style.css',
                 '/extra.css': HERE / 'extra.css', '/renderer.js': ROOT / 'arbetsbord/web/scen3d.js',
                 '/three/three.module.js': ROOT / 'scen/3d/vendor/three.module.js', '/three/OrbitControls.js': ROOT / 'scen/3d/vendor/OrbitControls.js',
                 '/media/original': VIDEO}
        if p in files:
            return self.send_file(files[p])
        if p == '/api/varianter':
            return self.js([{'id': k, 'name': v[0]} for k, v in VARIANTER.items() if v[1].is_file()])
        if p.startswith('/api/variant/'):
            try:
                return self.js(variant(p.rsplit('/', 1)[-1]))
            except KeyError:
                return self.send_error(404)
        self.send_error(404)

    def do_POST(self):
        if self.path != '/api/svar':
            return self.send_error(404)
        if self.headers.get('Origin') not in (None, f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'):
            return self.send_error(403)
        try:
            n = int(self.headers.get('Content-Length', 0))
            if not 0 < n <= 16000:
                raise ValueError('Ogiltig längd')
            b = json.loads(self.rfile.read(n))
            v = variant(b['variant'])
            t = float(b['time'])
            if not math.isfinite(t) or t < 0 or t > 20:
                raise ValueError('Ogiltig tid')
            if b.get('dom') not in ('narmare_original', 'samma', 'samre', 'osaker'):
                raise ValueError('Ogiltig bedömning')
            c = b.get('comment', '')
            if not isinstance(c, str) or len(c) > 4000:
                raise ValueError('Ogiltig kommentar')
            row = {'id': uuid.uuid4().hex, 'at': datetime.now(timezone.utc).isoformat(), 'experiment': 'rum-due-piani/1',
                   'variant': b['variant'], 'tagning': str(b.get('shot', ''))[:8], 'time': t, 'dom': b['dom'], 'comment': c,
                   'provenance': v['provenance'], 'method_blind': False}
            OUT.mkdir(exist_ok=True)
            with LOCK, (OUT / 'svar.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
            return self.js({'saved': True, 'id': row['id']})
        except (ValueError, KeyError, TypeError) as e:
            return self.js({'error': str(e)}, 400)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=5205); a = ap.parse_args()
    s = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    print(f'RUM_DUE_PIANI http://127.0.0.1:{a.port}', flush=True)
    s.serve_forever()
