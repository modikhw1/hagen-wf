"""Varm röstserver: Piper-rösterna laddas en gång (onnxruntime-sessionen tar ~5 s per röst), sedan görs en ändrad
replik om på ~0,3–0,5 s. op.py (replik, casting) anropar POST http://127.0.0.1:5193/bygg med scenen som JSON;
utan server kör op.py roster.py som underprocess (~6 s).
Kör: scen/.venv/Scripts/python.exe -B scen/3d/rostserver.py
"""
import json, sys, time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
ROOT = Path(__file__).resolve().parent; sys.path.insert(0, str(ROOT))
import roster
t = time.perf_counter()
for namn in ('alma', 'lisa', 'nst'): roster.röst(namn)
print(f'röster laddade på {time.perf_counter() - t:.1f} s; lyssnar på 127.0.0.1:5193', flush=True)

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
    def do_POST(self):
        if self.path != '/bygg': self.send_response(404); self.end_headers(); return
        S = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        try: out, cast, rader = roster.bygg(S); svar = dict(ok=True, rader=rader, cast=cast)
        except Exception as e: svar = dict(ok=False, fel=repr(e))
        b = json.dumps(svar, ensure_ascii=False).encode('utf-8')
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

HTTPServer(('127.0.0.1', 5193), H).serve_forever()   # en tråd: onnx-sessionerna används inte samtidigt
