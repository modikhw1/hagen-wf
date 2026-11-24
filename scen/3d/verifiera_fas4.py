"""Fas 4, del C: verifiera figurvarianterna mot källan och välj standard.

För varje variant (procedural, xbot): 3 bildrutor per tagning (start, mitt, slut) -> ledfel mot källans bildpunkter och
silhuettöverlapp (IoU) mot YOLO-masken (samma mått och källmasker som fas 2). Dessutom:
  - ryck i renderade armar: 2:a differensen (px) av projicerade armbågar/handleder över hela S1 och S3
  - svep över hela tidslinjen (var 0,1 s) med sidfel räknade
  - kontaktark: källa | procedural | xbot, tre rutor per tagning; remsa med 10 bildrutor i följd (S1)
Kör: scen/.venv/Scripts/python.exe -B scen/3d/verifiera_fas4.py
"""
import os, json, time, threading, subprocess, socket, sys
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import numpy as np, cv2
ROOT = Path(__file__).resolve().parent; sys.path.insert(0, str(ROOT))
from fas1_geometry import points
import verifiera as V2                     # källmasker (cachade i verifiering/fas2)
OUT = ROOT / 'verifiering/fas4/verif'; OUT.mkdir(parents=True, exist_ok=True)
VARIANTER = ['procedural', 'xbot']
def read(p): return json.loads((ROOT / p).read_text(encoding='utf-8'))
def port():
    with socket.socket() as s: s.bind(('127.0.0.1', 0)); return s.getsockname()[1]
class H(SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=str(ROOT), **k)
    def log_message(s, *a): pass

def render(jobs, omgång=60, försök=2):   # ny Chrome per omgång; Chrome/SwiftShader kraschar sporadiskt (CDP 1006) -> nytt försök, sedan halvering
    if len(jobs) > omgång:
        delar = [render(jobs[i:i + omgång], omgång) for i in range(0, len(jobs), omgång)]
        return dict(results=[r for d in delar for r in d['results']], errors=[e for d in delar for e in d.get('errors', [])])
    try: return _render(jobs)
    except SystemExit as e:
        if försök > 1: print('  Chrome kraschade, nytt försök', flush=True); return render(jobs, omgång, försök - 1)
        if len(jobs) == 1: raise
        h = len(jobs) // 2; a, b = render(jobs[:h], h, 2), render(jobs[h:], h, 2)
        return dict(results=a['results'] + b['results'], errors=a.get('errors', []) + b.get('errors', []))

def _render(jobs):
    (OUT / 'jobs.json').write_text(json.dumps(jobs), encoding='utf-8')
    p = port(); srv = ThreadingHTTPServer(('127.0.0.1', p), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    try: r = subprocess.run(['node', str(ROOT / 'capture.mjs'), f'http://127.0.0.1:{p}/index.html#t=0&capture=1', str(OUT), str(OUT / 'jobs.json'), str(port())], capture_output=True, text=True)
    finally: srv.shutdown()
    if r.returncode: raise SystemExit('capture.mjs: ' + r.stderr[-2000:])
    return json.loads((OUT / 'capture-results.json').read_text(encoding='utf-8'))

if __name__ == '__main__':
    t0 = time.perf_counter()
    frames = read('data/sparning.json')['frames']; layout = read('data/layout.json'); spec = read('scen3d.json')
    idx = []
    for c in layout['cameras'].values():
        a, b = c['start_frame'], c['end_frame_exclusive']; idx += [a, (a + b - 1) // 2, b - 1]
    seg = V2.sources(idx, frames)          # skapar/återanvänder källbild + mask i verifiering/fas2
    jobs = [dict(t=n / 30, variant=v, mask=m, file=f"{frames[n]['shot']}-{n:03d}-{v}{'-mask' if m else ''}.png") for v in VARIANTER for n in idx for m in (False, True)]
    ryck = {sid: [n for n in range(len(frames)) if frames[n]['shot'] == sid] for sid in ('S1', 'S3')}
    jobs += [dict(t=n / 30, variant=v, temporal=True, ryck=sid) for v in VARIANTER for sid, ns in ryck.items() for n in ns]
    remsa = list(range(30, 40))
    jobs += [dict(t=n / 30, variant='xbot', file=f'remsa-{n:03d}.png') for n in remsa]
    total = sum(s['duration'] for s in spec['shots'])
    jobs += [dict(t=round(t, 2), variant='xbot', temporal=True, svep=True) for t in np.arange(0, total, .1)]
    cap = render(jobs); res = cap['results']
    # ---- ledfel och IoU
    rader = []
    for v in VARIANTER:
        for n in idx:
            f = frames[n]; pre = f"{f['shot']}-{n:03d}"
            r = next(x for x in res if x.get('file') == f'{pre}-{v}.png')
            mask = cv2.imread(str(OUT / f'{pre}-{v}-mask.png'), 0) > 127; truth = cv2.imread(str(V2.OUT / f'{pre}-source-mask.png'), 0) > 127
            iou = float(np.logical_and(mask, truth).sum() / np.logical_or(mask, truth).sum())
            _, uv, ids = points(f); pj = r['data']['joints']
            errs = [float(np.linalg.norm(np.array(pj[j][:2]) - xy)) for j, xy in zip(ids, uv) if pj[j] is not None]
            rader.append(dict(variant=v, shot=f['shot'], frame=n, joint_px=float(np.median(errs)), iou=iou))
    shots = []
    for v in VARIANTER:
        for sid in [f'S{i}' for i in range(1, 8)]:
            rs = [r for r in rader if r['variant'] == v and r['shot'] == sid]
            shots.append(dict(variant=v, shot=sid, joint_px=round(float(np.median([r['joint_px'] for r in rs])), 1), joint_H=round(float(np.median([r['joint_px'] for r in rs])) / 1024, 4),
                              iou_mean=round(float(np.mean([r['iou'] for r in rs])), 3), iou_min=round(min(r['iou'] for r in rs), 3),
                              pass_=bool(np.median([r['joint_px'] for r in rs]) <= 40.96 and min(r['iou'] for r in rs) >= .5) if sid != 'S7' else None))
    # ---- ryck i renderade armar (2D, px/bildruta²) per variant
    jitter = {}
    for v in VARIANTER:
        acc = []
        for sid in ryck:
            js = [np.array([x['data']['joints'][j][:2] for j in (13, 14, 15, 16)], float) for x in res if x.get('ryck') == sid and x.get('variant') == v]
            for i in range(1, len(js) - 1): acc += list(np.linalg.norm(js[i - 1] - 2 * js[i] + js[i + 1], axis=1))
        jitter[v] = dict(median=round(float(np.median(acc)), 2), p90=round(float(np.percentile(acc, 90)), 2), flap_share_over_25px=round(float(np.mean(np.array(acc) > 25)), 4))
    svep = [x for x in res if x.get('svep')]; sidfel = sum(len(x['data'].get('errors') or []) for x in res)
    utan_aktör = [x['t'] for x in svep if not x['data'].get('joints')]
    # ---- kontaktark: källa | procedural | xbot (tre rutor per tagning)
    ark = []
    for sid in [f'S{i}' for i in range(1, 8)]:
        rad = []
        for n in [n for n in idx if frames[n]['shot'] == sid]:
            pre = f'{sid}-{n:03d}'
            rad += [cv2.resize(cv2.imread(str(V2.OUT / f'{pre}-source.jpg')), (192, 341))] + [cv2.resize(cv2.imread(str(OUT / f'{pre}-{v}.png')), (192, 341)) for v in VARIANTER] + [np.full((341, 8, 3), 255, np.uint8)]
        ark.append(np.hstack(rad))
    cv2.imwrite(str(ROOT / 'verifiering/fas4/kontaktark.jpg'), np.vstack(ark), [cv2.IMWRITE_JPEG_QUALITY, 80])
    cv2.imwrite(str(ROOT / 'verifiering/fas4/remsa-S1-xbot.jpg'), np.hstack([cv2.resize(cv2.imread(str(OUT / f'remsa-{n:03d}.png'))[60:700], (180, 360)) for n in remsa]), [cv2.IMWRITE_JPEG_QUALITY, 82])
    ut = dict(shots=shots, frames=rader, render_jitter_px=jitter, sweep=dict(samples=len(svep), page_errors=sidfel, missing_main_actor_at=utan_aktör[:10]),
              stabilization=read('data/motion-3.json')['stabilization']['metrics'], seconds=round(time.perf_counter() - t0, 1))
    (ROOT / 'data/verification-4.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
    for s in shots: print(f"{s['variant']:<11}{s['shot']}  led {s['joint_px']:5.1f}px ({s['joint_H']:.3f} H)  IoU {s['iou_mean']:.3f} (min {s['iou_min']:.3f})  {'OK' if s['pass_'] else ('-' if s['pass_'] is None else 'MISS')}")
    print('ryck i renderade armar:', jitter); print('svep:', ut['sweep']); print('tid', ut['seconds'], 's')
