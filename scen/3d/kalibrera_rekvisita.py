"""Fas 3, fix 1–2: kalibrera rekvisitans storlek och plats mot källans rutor, och lägg till förpackningar.

Källrutor: data/props-source-S{1..6}-3.json (Gemini 3.5 Flash-Lite på källbildrutor, mätta av Codex i fas 3).
För varje statiskt föremål löses (x, z på bordet, bredd, höjd) med minsta kvadrat över ALLA tagningar där det syns
(S1/S3/S6 för A:s bord, S2/S5 för B:s), med varje tagnings egen kamera. Föremål i handen (B:burger i S5, C:terminal)
kalibreras inte här.

Acceptans (granskning-fas2.md): projicerad ruta inom ±25 % i bredd och höjd och mittpunkt inom 30 px.
Skriver: scen3d.json (kalibrerad), data/kalibrering-3.json (före/efter per föremål och tagning), verifiering/fas3/kalibrering.jpg
Användning: scen/.venv/Scripts/python.exe -B scen/3d/kalibrera_rekvisita.py
"""
import json, math, shutil, copy
from pathlib import Path
import numpy as np, cv2
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
W, H = 576, 1024
SAMPLES = {'S1': 36, 'S2': 93, 'S3': 141, 'S5': 267, 'S6': 309}   # S4 har bara terminalen (i handen)
BAS = ROOT / 'scen3d.fas2.json'
spec = json.load(open(BAS, encoding='utf-8'))

def kamera(shot):
    k = shot['camera']['keyframes'][0]
    pos, tgt, up = map(np.array, (k['pos'], k['target'], k.get('up', [0, 1, 0])))
    f = tgt - pos; f /= np.linalg.norm(f); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    fpx = (H / 2) / math.tan(math.radians(k['fov']) / 2)
    return pos, r, u, f, fpx

def projicera(P, cam):
    pos, r, u, f, fpx = cam; d = P - pos
    x, y, z = d @ r, d @ u, d @ f
    return np.stack([W / 2 + x / z * fpx, H / 2 - y / z * fpx], -1), z

def hörn(pos, dims, yaw):
    w, h, d = dims; c = math.cos(math.radians(yaw)); s = math.sin(math.radians(yaw))
    pts = []
    for sx in (-.5, .5):
        for sy in (-.5, .5):
            for sz in (-.5, .5):
                x, z = sx * w, sz * d
                pts.append([pos[0] + c * x + s * z, pos[1] + sy * h, pos[2] - s * x + c * z])
    return np.array(pts)

def ruta2d(pos, dims, yaw, cam):
    p, z = projicera(hörn(pos, dims, yaw), cam)
    return np.array([p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max()])

def källruta(b):  # box_2d [ymin,xmin,ymax,xmax] 0-1000 -> px [x0,y0,x1,y1]
    return np.array([b[1] / 1000 * W, b[0] / 1000 * H, b[3] / 1000 * W, b[2] / 1000 * H])

källor = {sid: {s['etikett']: källruta(s['box_2d']) for s in json.load(open(ROOT / f'data/props-source-{sid}-3.json', encoding='utf-8'))['saker']}
          for sid in SAMPLES}
shots = {s['id']: s for s in spec['shots']}
kameror = {sid: kamera(shots[sid]) for sid in SAMPLES}

# --- nya förpackningsföremål (separata från maten, så att 'byt mat' behåller förpackningen)
def ny_prop(pid, typ, label, ref, dims):
    base = next(p for p in spec['props'] if p['id'] == ref)
    return {'id': pid, 'type': typ, 'label': label, 'transform': {'position': list(base['transform']['position']), 'yaw': base['transform'].get('yaw', 0)},
            'dims': dims, 'support': base.get('support'), 'semantic': {'owner': pid.split(':')[0], 'label': pid.split(':')[1], 'kind': 'packaging'},
            'provenance': 'fas 3: förpackning separerad från maten, kalibrerad mot källrutor'}
ids = {p['id'] for p in spec['props']}
if 'A:burger_wrap' not in ids: spec['props'].append(ny_prop('A:burger_wrap', 'food_box', 'A burger box', 'A:burger', [.24, .09, .20]))
if 'B:burger_wrap' not in ids: spec['props'].append(ny_prop('B:burger_wrap', 'food_box', 'B burger box', 'B:burger', [.22, .08, .18]))
if 'A:rear_wrap' not in ids: spec['props'].append(ny_prop('A:rear_wrap', 'paper_wrap', 'A rear wrapped item', 'A:fries', [.16, .10, .14]))
for p in spec['props']:
    p.setdefault('semantic', {'owner': p['id'].split(':')[0], 'label': p['id'].split(':')[1], 'kind': 'food' if p['type'] in ('burger', 'pizza_slice', 'fries_box', 'fry') else 'object'})

# --- vilka föremål kalibreras i vilka tagningar
STATISKA = {'A:can': ['S1', 'S3', 'S6'], 'A:cup': ['S1', 'S3', 'S6'], 'A:burger': ['S1', 'S3', 'S6'], 'A:burger_wrap': ['S1', 'S3', 'S6'],
            'A:fries': ['S1', 'S3', 'S6'], 'A:sauce': ['S1', 'S3'], 'A:tray': ['S1', 'S3', 'S6'], 'A:rear_wrap': ['S1', 'S3', 'S6'],
            'B:cup': ['S2', 'S5'], 'B:sauce': ['S2', 'S5'], 'B:fries': ['S2'],          # S5:s pommesruta täcker bara innehållet (annan etikettering)
            'B:burger': ['S2'], 'B:burger_wrap': ['S2']}                                 # i S5 hålls hamburgaren i handen (fästs, ej kalibrerad)
# rimliga gränser (meter): [bredd, höjd]
GRÄNS = {'drink_can': ([.05, .08], [.10, .20]), 'paper_cup': ([.07, .13], [.10, .24]), 'burger': ([.08, .16], [.05, .12]),
         'food_box': ([.12, .30], [.03, .14]), 'fries_box': ([.07, .18], [.06, .18]), 'sauce_cup': ([.04, .09], [.02, .06]),
         'tray': ([.30, .60], [.015, .04]), 'paper_wrap': ([.08, .22], [.04, .14])}
props = {p['id']: p for p in spec['props']}

def mät(pid, p):
    out = {}
    for sid in STATISKA[pid]:
        if pid not in källor[sid]: continue
        b = ruta2d(p['transform']['position'], p['dims'], p['transform'].get('yaw', 0), kameror[sid]); s = källor[sid][pid]
        out[sid] = {'bredd_kvot': round((b[2] - b[0]) / (s[2] - s[0]), 3), 'höjd_kvot': round((b[3] - b[1]) / (s[3] - s[1]), 3),
                    'mitt_px': round(float(np.hypot((b[0] + b[2] - s[0] - s[2]) / 2, (b[1] + b[3] - s[1] - s[3]) / 2)), 1), 'modell': b.round(1).tolist(), 'källa': s.round(1).tolist()}
    return out

rapport = {}
for pid, tagn in STATISKA.items():
    p = props[pid]; före = mät(pid, p); tagn = [t for t in tagn if pid in källor[t]]
    if not tagn: rapport[pid] = {'status': 'ingen källruta'}; continue
    ytan = p['transform']['position'][1] - p['dims'][1] / 2   # underkant = bordsytan/brickan
    (wl, wh), (hl, hh) = GRÄNS[p['type']]
    djupkvot = p['dims'][2] / p['dims'][0]
    def res(x):
        X, Z, w, h = x; dims = [w, h, w * djupkvot]; pos = [X, ytan + h / 2, Z]; r = []
        for sid in tagn:
            b = ruta2d(pos, dims, p['transform'].get('yaw', 0), kameror[sid]); s = källor[sid][pid]
            r += list((b - s) / 10.0)          # px/10
        return np.array(r)
    x0 = [p['transform']['position'][0], p['transform']['position'][2], float(np.clip(p['dims'][0], wl, wh)), float(np.clip(p['dims'][1], hl, hh))]
    lo = [x0[0] - .5, x0[1] - .5, wl, hl]; hi = [x0[0] + .5, x0[1] + .5, wh, hh]
    sol = least_squares(res, x0, bounds=(lo, hi))
    X, Z, w, h = sol.x
    p['dims'] = [round(w, 4), round(h, 4), round(w * djupkvot, 4)]
    p['transform']['position'] = [round(X, 4), round(ytan + h / 2, 4), round(Z, 4)]
    p['provenance'] = (p.get('provenance', '') + ' | fas 3: x,z,bredd,höjd minsta-kvadrat mot källrutor i ' + ','.join(tagn)).strip(' |')
    efter = mät(pid, p)
    rapport[pid] = {'tagningar': tagn, 'före': före, 'efter': efter,
                    'klarar': all(abs(v['bredd_kvot'] - 1) <= .25 and abs(v['höjd_kvot'] - 1) <= .25 and v['mitt_px'] <= 30 for v in efter.values())}

# brickan bär maten: lyft det som står på brickan till brickans överkant
tray = props['A:tray']; tray_top = tray['transform']['position'][1] + tray['dims'][1] / 2
tx, tz = tray['transform']['position'][0], tray['transform']['position'][2]
for pid in ('A:burger_wrap', 'A:burger', 'A:fries', 'A:sauce', 'A:rear_wrap', 'A:cup', 'A:can'):
    p = props[pid]; x, _, z = p['transform']['position']
    on = abs(x - tx) < tray['dims'][0] / 2 and abs(z - tz) < tray['dims'][2] / 2
    if on:
        bottom = tray_top + (0.0 if pid != 'A:burger' else 0.012)
        p['transform']['position'][1] = round(bottom + p['dims'][1] / 2, 4); p['support'] = 'A:tray'
# hamburgaren ligger i lådan: centrera i lådan
bw, bb = props['A:burger_wrap'], props['A:burger']
bb['transform']['position'][0] = bw['transform']['position'][0]; bb['transform']['position'][2] = bw['transform']['position'][2]

# B: hamburgaren ligger i sin låda på bordet i S2; i S5 hålls båda i vänster hand
bw, bb = props['B:burger_wrap'], props['B:burger']
bb['transform']['position'][0] = bw['transform']['position'][0]; bb['transform']['position'][2] = bw['transform']['position'][2]
bb['transform']['position'][1] = round(bw['transform']['position'][1] - bw['dims'][1] / 2 + 0.012 + bb['dims'][1] / 2, 4)
for s_ in spec['shots']:
    if s_['id'] == 'S5' and 'B:burger' in s_['propOverrides']:
        a = s_['propOverrides']['B:burger'].get('attach')
        if a: s_['propOverrides']['B:burger_wrap'] = {'attach': {**a, 'offset': [a['offset'][0], a['offset'][1] - 0.03, a['offset'][2]]}}
    if s_['id'] == 'S7': s_['propOverrides'].setdefault('B:burger_wrap', {})
# S7: A:s mat syns inte (dold i fas 2) -> dölj även de nya förpackningarna där
for s in spec['shots']:
    if s['id'] == 'S7':
        for pid in ('A:burger_wrap', 'A:rear_wrap'): s['propOverrides'][pid] = {'visible': False}

spec['editLog'].append({'phase': 3, 'action': 'Rekvisita kalibrerad mot källrutor (minsta kvadrat, alla tagningar samtidigt); förpackningar A:burger_wrap (food_box) och A:rear_wrap (paper_wrap) tillagda som egna föremål.'})
json.dump(spec, open(ROOT / 'scen3d.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(rapport, open(ROOT / 'data/kalibrering-3.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print(f"{'föremål':<15}{'tagn':<10}{'före b/h/mitt':<26}{'efter b/h/mitt':<26}klarar")
for pid, r in rapport.items():
    if 'efter' not in r: print(pid, r['status']); continue
    for sid in r['tagningar']:
        f, e = r['före'][sid], r['efter'][sid]
        print(f"{pid:<15}{sid:<10}{f['bredd_kvot']:.2f}/{f['höjd_kvot']:.2f}/{f['mitt_px']:>5.0f}px      {e['bredd_kvot']:.2f}/{e['höjd_kvot']:.2f}/{e['mitt_px']:>5.0f}px      {'ja' if r['klarar'] else 'NEJ'}")
print('dims efter:', {k: props[k]['dims'] for k in STATISKA})

# kontaktark: källa med källrutor (cyan) och modellrutor (orange) efter kalibrering
cap = cv2.VideoCapture(str(REPO / 'scen/klipp/d-dialog-notan.mp4')); bilder = []
for sid, n in SAMPLES.items():
    cap.set(cv2.CAP_PROP_POS_FRAMES, n); ok, im = cap.read()
    for pid, tagn in STATISTA.items() if False else STATISKA.items():
        if sid not in tagn or pid not in källor[sid]: continue
        p = props[pid]; s = källor[sid][pid].astype(int); b = ruta2d(p['transform']['position'], p['dims'], p['transform'].get('yaw', 0), kameror[sid]).astype(int)
        cv2.rectangle(im, tuple(s[:2]), tuple(s[2:]), (255, 255, 0), 2); cv2.rectangle(im, tuple(b[:2]), tuple(b[2:]), (0, 140, 255), 2)
        cv2.putText(im, pid, (int(s[0]), int(s[1]) - 4), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 0), 1)
    cv2.putText(im, f'{sid}  cyan=kalla  orange=modell', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, .7, (255, 255, 255), 2)
    bilder.append(cv2.resize(im, (288, 512)))
(ROOT / 'verifiering/fas3').mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(ROOT / 'verifiering/fas3/kalibrering.jpg'), np.hstack(bilder), [cv2.IMWRITE_JPEG_QUALITY, 85])
