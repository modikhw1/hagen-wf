"""Granskningsbord för lokalitet/1: flera klipp, original | A | (B) | L. Läser paket, skriver bara ägarsvar (append-only)."""
from __future__ import annotations
import argparse, hashlib, json, math, mimetypes, re, threading, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / 'ut'
LOCK = threading.Lock()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def klipp():
    out = {}
    for d in (sorted(OUT.iterdir()) if OUT.is_dir() else []):
        mf = d / 'obs_gpu.json' if (d / 'obs_gpu.json').is_file() else d / 'obs.json'
        if ((d / 'paket_L.json').is_file() or (d / 'paket_L_cpu.json').is_file()) and mf.is_file():
            meta = json.loads(mf.read_text(encoding='utf-8'))
            v = {}
            a = next((p_ for p_ in (ROOT / 'arbetsbord/data/ingest_v2' / d.name / 'paket.json', d / 'ingest_v2' / 'paket.json') if p_.is_file()), None)
            if a: v['A'] = ('A · ingest_v2', a, None)
            if d.name == 'duepiani': v['B'] = ('B · bildstöd + handkartläggning', ROOT / 'motpart/runda-4/5-rum-due-piani/ut/paket_B.json', ROOT / 'motpart/runda-4/5-rum-due-piani/ut/recept_B.json')
            if (d / 'paket_L.json').is_file(): v['L'] = ('L · lådlager (redigerbart)', d / 'paket_L.json', d / 'lokalitet.json')
            if (d / 'nat.json').is_file(): v['Lt'] = ('L · texturerade instanser', d / 'paket_L.json', d / 'lokalitet.json')
            if (d / 'struktur.json').is_file(): v['Ls'] = ('Ls · struktur (plan, lådor, kärl)', d / 'paket_Ls.json' if (d / 'paket_Ls.json').is_file() else d / 'paket_L.json', d / 'lokalitet.json')
            out[d.name] = {'video': ROOT / 'data/format/kontroll/klipp' / (meta['klipp'] + '.mp4'), 'varianter': v}
    return out


def variant(k, key):
    kl = klipp()[k]; name, fil, recept = kl['varianter'][key]
    return {'id': key, 'name': name, 'package': json.loads(fil.read_text(encoding='utf-8')),
            'recept': json.loads(recept.read_text(encoding='utf-8')) if recept and recept.is_file() else None,
            'provenance': {'paket': fil.relative_to(ROOT).as_posix(), 'paket_sha256': sha(fil),
                           'renderer_sha256': sha(ROOT / 'arbetsbord/web/scen3d.js'), 'kalla_sha256': sha(kl['video'])}}


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
                 '/extra.css': ROOT / 'motpart/runda-4/5-rum-due-piani/extra.css', '/renderer.js': ROOT / 'arbetsbord/web/scen3d.js',
                 '/three/three.module.js': ROOT / 'scen/3d/vendor/three.module.js', '/three/OrbitControls.js': ROOT / 'scen/3d/vendor/OrbitControls.js'}
        if p in files:
            return self.send_file(files[p])
        if p.startswith('/media/') and not p.startswith(('/media/ruta/', '/media/fyllnad/', '/media/struktur/')):  # ruta-routen hanteras nedan (fryst textur)
            k = p.rsplit('/', 1)[-1]; kl = klipp()
            return self.send_file(kl[k]['video']) if k in kl else self.send_error(404)
        if p.startswith('/api/struktur/'):
            _, _, _, k, f = p.split('/')
            if k not in klipp() or not re.fullmatch(r'(manifest|s[0-9]+\.bin)', f):
                return self.send_error(404)
            return self.send_file(OUT / k / 'struktur.json' if f == 'manifest' else OUT / k / 'struktur' / f)
        if p.startswith('/media/struktur/'):
            _, _, _, k, sid = p.split('/')
            if k not in klipp() or not re.fullmatch(r's[0-9]+(_rum)?', sid):
                return self.send_error(404)
            return self.send_file(OUT / k / 'struktur' / f'{sid}.png')
        if p.startswith('/api/nat/'):
            _, _, _, k, f = p.split('/')
            d = OUT / k
            if k not in klipp() or not re.fullmatch(r'(manifest|s\d+\.bin)', f):
                return self.send_error(404)
            return self.send_file(d / 'nat.json' if f == 'manifest' else d / 'nat' / f)
        if p.startswith('/media/fyllnad/'):
            _, _, _, k, sid = p.split('/')
            if k not in klipp() or not re.fullmatch(r's[0-9]+', sid):
                return self.send_error(404)
            return self.send_file(OUT / 'rumshjarna' / k / 'fyllnad' / f'{sid}_v2.png')
        if p.startswith('/media/ruta/'):
            _, _, _, k, n = p.split('/')
            kl = klipp()
            if k not in kl or not n.isdigit():
                return self.send_error(404)
            import cv2
            cap = cv2.VideoCapture(str(kl[k]['video'])); cap.set(cv2.CAP_PROP_POS_FRAMES, int(n)); ok, fr = cap.read()
            if not ok:
                return self.send_error(404)
            raw = cv2.imencode('.jpg', fr, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tobytes()
            self.send_response(200); self.send_header('Content-Type', 'image/jpeg'); self.send_header('Content-Length', str(len(raw))); self.end_headers()
            return self.wfile.write(raw)
        if p == '/api/klipp':
            return self.js([{'id': k, 'varianter': [{'id': i, 'name': v[0]} for i, v in d['varianter'].items()]} for k, d in klipp().items()])
        if p.startswith('/api/variant/'):
            try:
                _, _, _, k, key = p.split('/')
                return self.js(variant(k, key))
            except (KeyError, ValueError):
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
            v = variant(b['klipp'], b['variant'])
            t = float(b['time'])
            if not math.isfinite(t) or t < 0 or t > 600:
                raise ValueError('Ogiltig tid')
            if b.get('dom') not in ('narmare_original', 'samma', 'samre', 'osaker'):
                raise ValueError('Ogiltig bedömning')
            c = b.get('comment', '')
            if not isinstance(c, str) or len(c) > 4000:
                raise ValueError('Ogiltig kommentar')
            row = {'id': uuid.uuid4().hex, 'at': datetime.now(timezone.utc).isoformat(), 'experiment': 'lokalitet/1', 'klipp': b['klipp'],
                   'variant': b['variant'], 'tagning': str(b.get('shot', ''))[:8], 'time': t, 'dom': b['dom'], 'comment': c,
                   'provenance': v['provenance'], 'method_blind': False}
            OUT.mkdir(exist_ok=True)
            with LOCK, (OUT / 'svar.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
            return self.js({'saved': True, 'id': row['id']})
        except (ValueError, KeyError, TypeError) as e:
            return self.js({'error': str(e)}, 400)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=5206); a = ap.parse_args()
    s = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    print(f'LOKALITET http://127.0.0.1:{a.port}', flush=True)
    s.serve_forever()
