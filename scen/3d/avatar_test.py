"""Fas 4: rendera samma bildrutor med xbot och procedural + källa sida vid sida. python -B scen/3d/avatar_test.py [rutor...]"""
import json, sys, threading, subprocess, socket
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import numpy as np, cv2
ROOT = Path(__file__).resolve().parent; OUT = ROOT / 'verifiering/fas4'; OUT.mkdir(parents=True, exist_ok=True)
def port():
    with socket.socket() as s: s.bind(('127.0.0.1', 0)); return s.getsockname()[1]
class H(SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=str(ROOT), **k)
    def log_message(s, *a): pass
rutor = [int(x) for x in sys.argv[1:]] or [36, 93, 142, 213, 268, 308, 359]
jobs = [{'t': n / 30, 'variant': v, 'file': f'{v}-{n:03d}.png'} for n in rutor for v in ('xbot', 'procedural')]
(OUT / 'jobs.json').write_text(json.dumps(jobs), encoding='utf-8')
p = port(); srv = ThreadingHTTPServer(('127.0.0.1', p), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
try: r = subprocess.run(['node', str(ROOT / 'capture.mjs'), f'http://127.0.0.1:{p}/index.html#t=0&capture=1', str(OUT), str(OUT / 'jobs.json'), str(port())], capture_output=True, text=True)
finally: srv.shutdown()
if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
res = json.loads((OUT / 'capture-results.json').read_text(encoding='utf-8')); res = res.get('results', res)
print('sidfel:', sum(len(x['data'].get('errors') or []) for x in res), [x['data'].get('errors') for x in res if x['data'].get('errors')][:2])
cap = cv2.VideoCapture(str(ROOT.parent / 'klipp/d-dialog-notan.mp4')); rader = []
for n in rutor:
    cap.set(cv2.CAP_PROP_POS_FRAMES, n); ok, src = cap.read()
    ims = [cv2.resize(src, (288, 512))] + [cv2.resize(cv2.imread(str(OUT / f'{v}-{n:03d}.png')), (288, 512)) for v in ('xbot', 'procedural')]
    rader.append(np.hstack(ims))
cv2.imwrite(str(OUT / 'xbot-jamforelse.jpg'), np.hstack(rader) if len(rader) <= 3 else np.vstack([np.hstack(rader[i:i + 3]) if len(rader[i:i + 3]) == 3 else np.hstack(rader[i:i + 3] + [np.zeros_like(rader[0])] * (3 - len(rader[i:i + 3]))) for i in range(0, len(rader), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 82])
print('->', OUT / 'xbot-jamforelse.jpg')
