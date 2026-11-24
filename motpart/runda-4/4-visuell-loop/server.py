"""Isolated visual baseline experiment. No ingestion, cloud requests or edits to source packages."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, mimetypes, re, threading, time, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / 'ut'
SPECS = {
    'duepiani': ('Due Piani', 'duepiani-7650849186912406806', 'Kända risker: personidentiteter mellan tagningar, bordshöjd och matens placering.'),
    'spanjorskan': ('Spanjorskan', 'spanjorskansthlm-7474263274415082774', 'Kända risker: personförväxling och stora djupsprång. Detta är ett avsiktligt svårt kontrollfall.'),
}
LOCK = threading.Lock()
CACHE = {}
START = time.monotonic()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def lens_variant(package, factor):
    if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not math.isfinite(factor) or not .8 <= factor <= 1.2:
        raise ValueError('Linsfaktorn måste vara mellan 0.8 och 1.2.')
    variant = copy.deepcopy(package)
    for shot in variant['tagningar']:
        for key in shot['kamera']['nycklar']:
            key[8] *= factor
    return variant

def load_clip(key):
    if key not in SPECS:
        raise KeyError(key)
    if key in CACHE:
        return CACHE[key]
    started = time.perf_counter()
    name, source_id, risk = SPECS[key]
    folder = ROOT / 'arbetsbord/data/ingest_v2' / key
    package_file = folder / 'paket.json'
    video = ROOT / 'data/format/kontroll/klipp' / (source_id + '.mp4')
    package = json.loads(package_file.read_text(encoding='utf-8'))
    timeline = json.loads((folder / 'tidslinje.json').read_text(encoding='utf-8'))
    shots = package['tagningar']
    n = package['tidsbas']['antal_rutor']
    assert shots[0]['ut'][0] == 0 and shots[-1]['ut'][1] == n
    assert all(a['ut'][1] == b['ut'][0] for a,b in zip(shots,shots[1:]))
    assert all(s['kamera']['nycklar'] for s in shots)
    data = {'id': key, 'name': name, 'source_id': source_id, 'risk': risk,
        'package': package, 'duration': timeline['kalla']['langd'], 'video': '/media/' + key,
        'provenance': {'source_sha256': sha(video), 'package_sha256': sha(package_file),
            'renderer_sha256': sha(ROOT / 'arbetsbord/web/scen3d.js'),
            'operator': 'lens_factor/1', 'operator_sha256': sha(Path(__file__)),
            'baseline': 'befintlig ingest_v2, ej ny eller godkänd rekonstruktion',
            'units': package.get('koordinater'), 'source_path': video.relative_to(ROOT).as_posix()},
        'inventory': {'shots': len(shots), 'camera_keys': sum(len(s['kamera']['nycklar']) for s in shots),
            'people': len(package['personer']), 'motion_frames': sum(len(t['rutor']) for tracks in package['rorelse'].values() for t in tracks)},
        'load_ms': round((time.perf_counter()-started)*1000,3)}
    CACHE[key] = data
    return data

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def json_response(self, value, status=200):
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def send_file(self, path):
        if not path.is_file():
            self.send_error(404); return
        size = path.stat().st_size
        start, end, partial = 0, size-1, False
        requested = self.headers.get('Range')
        if requested:
            match = re.fullmatch(r'bytes=(\d+)-(\d*)', requested)
            if not match:
                self.send_error(416); return
            start = int(match[1]); end = min(int(match[2]), size-1) if match[2] else size-1
            if start > end or start >= size:
                self.send_error(416); return
            partial = True
        self.send_response(206 if partial else 200)
        mime = {'js':'text/javascript', 'html':'text/html; charset=utf-8', 'css':'text/css; charset=utf-8'}.get(path.suffix[1:]) or mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(end-start+1))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-cache')
        if partial: self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            with path.open('rb') as stream:
                stream.seek(start); remaining = end-start+1
                while remaining:
                    block = stream.read(min(remaining, 65536))
                    if not block: break
                    self.wfile.write(block); remaining -= len(block)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_GET(self):
        path = urlparse(self.path).path
        files = {'/': HERE/'index.html', '/app.js': HERE/'app.js', '/style.css': HERE/'style.css',
            '/renderer.js': ROOT/'arbetsbord/web/scen3d.js',
            '/three/three.module.js': ROOT/'scen/3d/vendor/three.module.js',
            '/three/OrbitControls.js': ROOT/'scen/3d/vendor/OrbitControls.js'}
        if path in files: return self.send_file(files[path])
        if path == '/api/clips':
            return self.json_response([{'id':k, 'name':v[0]} for k,v in SPECS.items()])
        if path.startswith('/api/clip/'):
            try: return self.json_response(load_clip(path.rsplit('/',1)[-1]))
            except KeyError: return self.send_error(404)
        if path.startswith('/media/'):
            key = path.rsplit('/',1)[-1]
            if key in SPECS:
                return self.send_file(ROOT/'data/format/kontroll/klipp'/(SPECS[key][1]+'.mp4'))
        self.send_error(404)

    def do_POST(self):
        if self.path != '/api/feedback': return self.send_error(404)
        if self.headers.get('Origin') not in (None, f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'):
            return self.send_error(403)
        try:
            length = int(self.headers.get('Content-Length',0))
            if not 0 < length <= 16000: raise ValueError('Ogiltig längd')
            body = json.loads(self.rfile.read(length))
            clip = load_clip(body['clip'])
            factor = body['factor']; lens_variant(clip['package'],factor)
            if body.get('verdict') not in ('baslinje_faller','baslinje_lasbar','andring_anvandbar','andring_faller','osaker'):
                raise ValueError('Ogiltig bedömning')
            position = float(body['time'])
            if not math.isfinite(position) or not 0 <= position <= clip['duration'] + .1: raise ValueError('Ogiltig tid')
            comment = body.get('comment','')
            if not isinstance(comment,str) or len(comment)>4000: raise ValueError('Ogiltig kommentar')
            row = {'id':uuid.uuid4().hex, 'at':datetime.now(timezone.utc).isoformat(), 'experiment':'visuell-loop/1',
                'clip':body['clip'], 'factor':factor, 'time':position, 'verdict':body['verdict'], 'comment':comment,
                'provenance':clip['provenance'], 'method_blind':False}
            OUT.mkdir(exist_ok=True)
            with LOCK, (OUT/'svar.jsonl').open('a',encoding='utf-8') as f:
                f.write(json.dumps(row,ensure_ascii=False)+'\n')
            return self.json_response({'saved':True,'id':row['id']})
        except (ValueError,KeyError,TypeError) as exc:
            return self.json_response({'error':str(exc)},400)

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--port',type=int,default=5204); args=ap.parse_args()
    inventory=[{k:v for k,v in load_clip(key).items() if k!='package'} for key in SPECS]
    OUT.mkdir(exist_ok=True)
    (OUT/'inventering.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'FRAMSTEG.json').write_text(json.dumps({'experiment':'visuell-loop/1','stage':'panel_ready','clips':len(inventory),'cloud_cost_usd':0,'modal':'timeout_20s','visual_verification':'pending','startup_s':round(time.monotonic()-START,3)},indent=2),encoding='utf-8')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'VISUELL_LOOP http://127.0.0.1:{args.port} startup={time.monotonic()-START:.3f}s',flush=True)
    server.serve_forever()
