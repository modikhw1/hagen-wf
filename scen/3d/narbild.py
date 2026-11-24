"""Närbilder av ansikten (fri kamera) för granskning: python -B scen/3d/narbild.py [variant]"""
import json, sys, threading, subprocess, socket
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import numpy as np, cv2
ROOT = Path(__file__).resolve().parent; OUT = ROOT / 'verifiering/fas4/narbild'; OUT.mkdir(parents=True, exist_ok=True)
def port():
    with socket.socket() as s: s.bind(('127.0.0.1', 0)); return s.getsockname()[1]
class H(SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=str(ROOT), **k)
    def log_message(s, *a): pass
variant = sys.argv[1] if len(sys.argv) > 1 else 'xbot'
spec = json.loads((ROOT / 'scen3d.json').read_text(encoding='utf-8')); hp = json.loads((ROOT / 'data/huvudpunkter.json').read_text(encoding='utf-8'))
SK = {'A': 1.65, 'B': 1.78, 'C': 1.78}
def huvud(aid, sid):
    a = next(x for x in spec['actors'] if x['id'] == aid); s = a['look']['height'] / SK[aid]; x, y, z = hp[aid][sid]
    l = np.array([x, -y, -z]) * s; yaw = np.radians(a['transform'].get('yaw', 0)); c, sn = np.cos(yaw), np.sin(yaw)
    return np.array([c * l[0] + sn * l[2], l[1], -sn * l[0] + c * l[2]]) + np.array(a['transform']['position']), yaw
jobs = []
for n, aid, sid in [(36, 'A', 'S1'), (142, 'A', 'S3'), (268, 'B', 'S5'), (213, 'C', 'S4')]:
    h, yaw = huvud(aid, sid); fram = np.array([np.sin(yaw), 0, np.cos(yaw)])
    jobs.append({'t': n / 30, 'variant': variant, 'file': f'{variant}-{aid}-{n:03d}.png', 'orbit': {'pos': (h + fram * .42 + [0, .02, 0]).tolist(), 'target': h.tolist()}})
(OUT / 'jobs.json').write_text(json.dumps(jobs), encoding='utf-8')
p = port(); srv = ThreadingHTTPServer(('127.0.0.1', p), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
try: r = subprocess.run(['node', str(ROOT / 'capture.mjs'), f'http://127.0.0.1:{p}/index.html#t=0&capture=1', str(OUT), str(OUT / 'jobs.json'), str(port())], capture_output=True, text=True)
finally: srv.shutdown()
if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
ims = [cv2.imread(str(OUT / j['file']))[200:712, 32:544] for j in jobs]
cv2.imwrite(str(OUT / f'{variant}-ansikten.jpg'), np.hstack([cv2.resize(i, (320, 320)) for i in ims]), [cv2.IMWRITE_JPEG_QUALITY, 85]); print('->', OUT / f'{variant}-ansikten.jpg')
