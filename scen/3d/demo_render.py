"""Fas 3: rendera före/efter för de semantiska ändringarna (demo-andringar.sh).

  python -B scen/3d/demo_render.py fore    -> renderar scen3d.bas.json-läget (måste vara aktivt i scen3d.json)
  python -B scen/3d/demo_render.py efter   -> renderar nuvarande scen3d.json
  python -B scen/3d/demo_render.py ark     -> sätter ihop kontaktark i verifiering/fas3/demo/
Tidpunkter räknas per version ur tagningarnas längder (de ändras av ändringarna).
"""
import json, sys, threading, subprocess, socket, os
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import numpy as np, cv2

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'verifiering/fas3/demo'; OUT.mkdir(parents=True, exist_ok=True)

def port():
    with socket.socket() as s: s.bind(('127.0.0.1', 0)); return s.getsockname()[1]
class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(ROOT), **k)
    def log_message(self, *a): pass

def tider(spec):
    t = 0; ut = {}
    for s in spec['shots']: ut[s['id']] = (t, s['duration']); t += s['duration']
    return ut

def jobs_for(spec, etikett):
    T = tider(spec); j = []
    def lagg(sid, frac, namn):
        if sid in T: a, d = T[sid]; j.append({'t': round(a + d * frac, 4), 'file': f'{etikett}-{namn}.png'})
    lagg('S1', .45, 'S1'); lagg('S2', .5, 'S2'); lagg('S4', .5, 'S4'); lagg('S6', .03, 'S6-start'); lagg('S6', .97, 'S6-slut'); lagg('S7', .5, 'S7')
    if 'S8' in T:
        for i, f in enumerate([.0, .25, .5, .75, .99]): lagg('S8', f, f'S8-orbit-{i}')
    return j

def render(etikett):
    spec = json.loads((ROOT / 'scen3d.json').read_text(encoding='utf-8')); jobs = jobs_for(spec, etikett)
    (OUT / 'jobs.json').write_text(json.dumps(jobs), encoding='utf-8')
    p = port(); srv = ThreadingHTTPServer(('127.0.0.1', p), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    try: subprocess.run(['node', str(ROOT / 'capture.mjs'), f'http://127.0.0.1:{p}/index.html#t=0&capture=1', str(OUT), str(OUT / 'jobs.json'), str(port())], check=True)
    finally: srv.shutdown()
    res = json.loads((OUT / 'capture-results.json').read_text(encoding='utf-8'))
    fel = [r for r in res['results'] if r.get('data', {}).get('errors')] if isinstance(res, dict) and 'results' in res else []
    print(etikett, 'renderade', len(jobs), 'bilder', '| fel i sidan:', len(fel))

def ark():
    def bild(n):
        im = cv2.imread(str(OUT / n)); return None if im is None else cv2.resize(im, (288, 512))
    def text(im, t):
        cv2.rectangle(im, (0, 0), (288, 26), (0, 0, 0), -1); cv2.putText(im, t, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 1); return im
    rader = []
    for namn, rubrik in [('S1', 'S1: burger->pizza, burk bort, mugg narmare, stress'), ('S4', 'S4: servitoren vand mot A, 1.6 s'),
                         ('S6-start', 'S6 start'), ('S6-slut', 'S6 slut: dolly in + servitor bakom A')]:
        a, b = bild(f'fore-{namn}.png'), bild(f'efter-{namn}.png')
        if a is None or b is None: continue
        rader.append(np.hstack([text(a, 'FORE ' + namn), text(b, rubrik[:44])]))
    if rader:
        W = max(r.shape[1] for r in rader)
        cv2.imwrite(str(OUT / 'fore-efter.jpg'), np.hstack(rader), [cv2.IMWRITE_JPEG_QUALITY, 85])
    orb = [bild(f'efter-S8-orbit-{i}.png') for i in range(5)]
    if all(o is not None for o in orb):
        cv2.imwrite(str(OUT / 'S8-orbit.jpg'), np.hstack([text(o, f'S8 orbit {i * 22.5:.0f} grader') for i, o in enumerate(orb)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print('ark ->', OUT)

def svep():
    spec = json.loads((ROOT / 'scen3d.json').read_text(encoding='utf-8')); L = sum(s['duration'] for s in spec['shots'])
    jobs = [{'t': round(i * 0.2, 3)} for i in range(int(L / 0.2) + 1)]
    (OUT / 'jobs.json').write_text(json.dumps(jobs), encoding='utf-8')
    p = port(); srv = ThreadingHTTPServer(('127.0.0.1', p), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    try: subprocess.run(['node', str(ROOT / 'capture.mjs'), f'http://127.0.0.1:{p}/index.html#t=0&capture=1', str(OUT), str(OUT / 'jobs.json'), str(port())], check=True, capture_output=True)
    finally: srv.shutdown()
    res = json.loads((OUT / 'capture-results.json').read_text(encoding='utf-8')); res = res.get('results', res)
    fel = [r for r in res if r['data'].get('errors')]; utan = [r for r in res if not r['data'].get('joints')]
    print(f'svep: {len(res)} bildrutor över {L:.2f} s | sidfel {len(fel)} | bildrutor utan aktiv huvudaktör {len(utan)}', [ (r['t'], r['data']['shot']) for r in utan][:8])

if __name__ == '__main__':
    {'fore': lambda: render('fore'), 'efter': lambda: render('efter'), 'ark': ark, 'svep': svep}[sys.argv[1]]()
