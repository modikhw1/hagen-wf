"""MVP-film för granskning (produkten spelas live; detta är bara en förhandsvisning): varje bildruta i 30 fps
ur uppspelaren (X Bot, designade röster, ordvis textning) + ljudmixen i källtid -> verifiering/fas4/mvp.mp4.
Kör: scen/.venv/Scripts/python.exe -B scen/3d/mvp_render.py [--original] [--avatar procedural] [--bara-mux]
"""
import json, sys, subprocess, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parent; OUT = ROOT / 'verifiering/fas4/mvp'; OUT.mkdir(parents=True, exist_ok=True)
sys.argv, args = [sys.argv[0]], sys.argv[1:]
spec_ = importlib.util.spec_from_file_location('vf', ROOT / 'verifiera_fas4.py'); vf = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(vf)
vf.OUT = OUT
avatar = args[args.index('--avatar') + 1] if '--avatar' in args else 'xbot'; original = '--original' in args
S = json.loads((ROOT / 'scen3d.json').read_text(encoding='utf-8')); total = sum(s['duration'] for s in S['shots']); n = int(total * 30)
orig_render = vf._render
def _render(jobs):    # samma som verifieraren men med textning och valt ljudläge i adressen
    (OUT / 'jobs.json').write_text(json.dumps(jobs), encoding='utf-8')
    import threading, socket
    p = vf.port(); srv = vf.ThreadingHTTPServer(('127.0.0.1', p), vf.H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    try: r = subprocess.run(['node', str(ROOT / 'capture.mjs'), f'http://127.0.0.1:{p}/index.html#t=0&capture=1&textning=1&ljud={"original" if original else "designed"}', str(OUT), str(OUT / 'jobs.json'), str(vf.port())], capture_output=True, text=True)
    finally: srv.shutdown()
    if r.returncode: raise SystemExit('capture.mjs: ' + r.stderr[-800:])
    return json.loads((OUT / 'capture-results.json').read_text(encoding='utf-8'))
vf._render = _render
res = {'results': []} if '--bara-mux' in args else vf.render([dict(t=round(i / 30, 4), variant=avatar, file=f'f{i:04d}.png') for i in range(n)])
# ljud: varje tagnings källintervall läggs i tidslinjens ordning (tidskartor/tysta tagningar respekteras grovt: tyst = stillhet)
ljud = S['audio'] if original or not S.get('audioDesigned') else S['audioDesigned']
delar, filt = [], []
for i, sh in enumerate(S['shots']):
    a, b = sh['source']['inSec'], sh['source']['outSec']; d = sh['duration']
    if sh.get('tyst'): filt.append(f'anullsrc=r=44100:cl=mono,atrim=0:{d:.4f}[s{i}]')
    else:
        tempo = (b - a) / d
        filt.append(f'[1:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=mono' + (f',atempo={tempo:.4f}' if abs(tempo - 1) > .01 else '') + f'[s{i}]')
    delar.append(f'[s{i}]')
filt.append(''.join(delar) + f'concat=n={len(delar)}:v=0:a=1[a]')
mp4 = ROOT / f"verifiering/fas4/mvp-{avatar}{'-original' if original else ''}.mp4"
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', str(OUT / 'f%04d.png'), '-i', str(ROOT / ljud), '-filter_complex', ';'.join(filt),
                '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-c:a', 'aac', '-b:a', '128k', '-shortest', str(mp4)], check=True)
print('sidfel', sum(len(x['data'].get('errors') or []) for x in res['results']), '->', mp4)
