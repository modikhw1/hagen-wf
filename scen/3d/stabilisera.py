"""Fas 4 del A: stabiliserad rörelse (motion-3.json) — armarna ska inte flaxa.

Varför de flaxar: armarnas leder kommer från MediaPipes metriska världspunkter, vars djup brusar.
Här förankras armbågar och handleder i BILDEN (källkamerans stråle genom ledens 2D-punkt), på det djup som ger
konstanta benlängder (per aktör, median), med kontinuitet över tid. Bål och huvud behålls (stabila). Skymda leder
(låg synlighet) hålls och glider mot tagningens viloläge. Sist One-Euro-filter.

Koordinater (som Character.update i meshes.js): lokal = (x, -y, -z) av MediaPipe-världspunkten; värld = pos + Ry(yaw)·lokal·skala.
Mått (före/efter, armbågar och handleder, inom tagningar):
  flaxindex  = andel bildrutor där en armbåge flyttas > 8 cm mellan två bildrutor
  jitter     = |andra differensen| (m/bildruta², px/bildruta²), median och p90
  återprojektion = median px mot MediaPipes bildpunkter (synliga leder)
Användning: scen/.venv/Scripts/python.exe -B scen/3d/stabilisera.py
"""
import json, math, copy
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
W, H = 576, 1024
spec = json.loads((ROOT / 'scen3d.bas.json').read_text(encoding='utf-8'))
M = json.loads((ROOT / 'data/motion-2.json').read_text(encoding='utf-8'))
frames = M['frames']
SKALA = {'A': 1.65, 'B': 1.78, 'C': 1.78}
aktorer = {a['id']: a for a in spec['actors']}
källkamera = {}
for s in spec['shots']:
    k = s['source']['camera']; källkamera[s['source'].get('shotId', s['id'])] = k

def kamera(k):
    pos, tgt, up = map(np.array, (k['pos'], k['target'], k.get('up', [0, 1, 0])))
    f = tgt - pos; f /= np.linalg.norm(f); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    return pos, r, u, f, (H / 2) / math.tan(math.radians(k['fov']) / 2)
KAM = {sid: kamera(k) for sid, k in källkamera.items()}

def till_värld(a, P):     # P: (n,3) MediaPipe-världspunkter
    tr = a['transform']; yaw = math.radians(tr.get('yaw', 0)); s = a['look']['height'] / SKALA.get(a['id'], 1.78)
    L = np.stack([P[:, 0], -P[:, 1], -P[:, 2]], -1) * s
    c, sn = math.cos(yaw), math.sin(yaw)
    x = c * L[:, 0] + sn * L[:, 2]; z = -sn * L[:, 0] + c * L[:, 2]
    return np.stack([x, L[:, 1], z], -1) + np.array(tr['position'])

def från_värld(a, X):
    tr = a['transform']; yaw = math.radians(tr.get('yaw', 0)); s = a['look']['height'] / SKALA.get(a['id'], 1.78)
    D = X - np.array(tr['position']); c, sn = math.cos(yaw), math.sin(yaw)
    lx = c * D[:, 0] - sn * D[:, 2]; lz = sn * D[:, 0] + c * D[:, 2]; ly = D[:, 1]
    L = np.stack([lx, ly, lz], -1) / s
    return np.stack([L[:, 0], -L[:, 1], -L[:, 2]], -1)

def projicera(cam, X):
    pos, r, u, f, fpx = cam; d = X - pos
    return np.stack([W / 2 + (d @ r) / (d @ f) * fpx, H / 2 - (d @ u) / (d @ f) * fpx], -1)

def stråle(cam, uv):
    pos, r, u, f, fpx = cam
    d = r * (uv[0] * W - W / 2) / fpx + u * (-(uv[1] * H - H / 2)) / fpx + f
    return pos, d / np.linalg.norm(d)

def på_sfär(C, d, S, L, t_pref):
    """punkt på strålen C + t d med |p - S| = L; välj t närmast t_pref; annars närmaste punkt på strålen"""
    oc = C - S; b = d @ oc; c = oc @ oc - L * L; disk = b * b - c
    if disk < 0:   # strålen når inte sfären: punkten på sfären närmast strålen (längden hålls)
        närmast = C + (-b) * d; v = närmast - S; return S + v / (np.linalg.norm(v) + 1e-9) * L, False
    t1, t2 = -b - math.sqrt(disk), -b + math.sqrt(disk)
    t = t1 if abs(t1 - t_pref) < abs(t2 - t_pref) else t2
    return C + t * d, True

class OneEuro:
    def __init__(s, fc=1.2, beta=0.25, dfc=1.0, fps=30.0): s.fc, s.beta, s.dfc, s.dt = fc, beta, dfc, 1.0 / fps; s.x = s.dx = None
    def a(s, fc): r = 2 * math.pi * fc * s.dt; return r / (r + 1)
    def __call__(s, x):
        if s.x is None: s.x = x.copy(); s.dx = np.zeros_like(x); return x
        dx = (x - s.x) / s.dt; s.dx = s.dx + s.a(s.dfc) * (dx - s.dx)
        fc = s.fc + s.beta * np.linalg.norm(s.dx); s.x = s.x + s.a(fc) * (x - s.x); return s.x.copy()

ARM = [(11, 13, 15), (12, 14, 16)]        # axel, armbåge, handled
VIS = 0.6
# benlängder per aktör (median, symmetriska) ur världspunkterna
längd = {}
for aid in aktorer:
    fr = [f for f in frames if f['actor'] == aid]
    ö, u_ = [], []
    for f in fr:
        P = np.array(f['pose']); I = np.array(f['image'])
        for s_, e_, w_ in ARM:
            if min(I[s_, 3], I[e_, 3]) > .8: ö.append(np.linalg.norm(P[s_] - P[e_]))
            if min(I[e_, 3], I[w_, 3]) > .8: u_.append(np.linalg.norm(P[e_] - P[w_]))
    s = aktorer[aid]['look']['height'] / SKALA.get(aid, 1.78)
    längd[aid] = (float(np.median(ö)) * s if ö else .28, float(np.median(u_)) * s if u_ else .25)

ut = copy.deepcopy(M); ut['stabilization'] = {'method': 'armar förankrade i bildstrålar med fasta benlängder (median per aktör), skymda leder hålls/glider mot vila, One-Euro (fc 1.2 Hz, beta 0.25)', 'bone_lengths_m': längd}
nya = []
filter_ = {}; förra = {}
for i, f in enumerate(frames):
    aid = f['actor']; a = aktorer[aid]; sid = f['shot']; cam = KAM[sid]
    P = np.array(f.get('poseFused') or f['pose']); I = np.array(f['image'])
    X = till_värld(a, P)                       # MediaPipe placerat (som spelaren)
    Xn = X.copy()
    neutral = till_värld(a, np.array(M['neutralPoses'][sid])) if sid in M['neutralPoses'] else X
    ny_tagning = i == 0 or frames[i - 1]['shot'] != sid or frames[i - 1]['actor'] != aid
    if ny_tagning: filter_[aid] = {j: OneEuro() for j in range(33)}; förra[aid] = {}
    Lö, Lu = längd[aid]
    # axlar: på sina bildstrålar, på MediaPipes djup (förankrar armkedjans start i bilden)
    for j in (11, 12):
        if I[j, 3] >= VIS:
            C, d = stråle(cam, (I[j, 0], I[j, 1])); Xn[j] = C + ((X[j] - C) @ d) * d
    for s_, e_, w_ in ARM:
        S = Xn[s_]
        # handleden: helst handdetektorns bildpunkt (stabilare), annars posens
        hand = next((h for h in f['hands'] if h['side'] == ('Left' if s_ == 11 else 'Right')), None)
        for j, parent, Ln, uv in ((e_, s_, Lö, I[e_]), (w_, e_, Lu, (hand['image'][0] if hand else I[w_]))):
            synlig = (I[j, 3] >= VIS) or (j == w_ and hand is not None)
            if synlig:
                C, d = stråle(cam, (uv[0], uv[1]))
                t_pref = (X[j] - C) @ d
                if j in förra[aid]: t_pref = 0.5 * t_pref + 0.5 * ((förra[aid][j] - C) @ d)
                p, ok = på_sfär(C, d, Xn[parent], Ln, t_pref)
                Xn[j] = p
            else:   # skymd: håll senaste, glid mot vila (tidskonstant ~0,5 s), behåll benlängd
                base = förra[aid].get(j, neutral[j]); mål = neutral[j]
                p = base + (mål - base) * (1 / 15)
                v = p - Xn[parent]; Xn[j] = Xn[parent] + v / (np.linalg.norm(v) + 1e-9) * Ln
            förra[aid][j] = Xn[j].copy()
        # händernas fingrar följer handleden (flytta hela handskelettet med samma förskjutning)
    # One-Euro på alla leder (i världen), sedan tillbaka till lokala posekoordinater
    Xs = np.stack([filter_[aid][j](Xn[j]) for j in range(33)])
    nya.append(Xs)
    lok = från_värld(a, Xs)
    ut['frames'][i]['poseRaw'] = f['pose']; ut['frames'][i]['pose'] = lok.round(5).tolist(); ut['frames'][i]['poseFused'] = lok.round(5).tolist()

# ---------- mått före/efter
def mått(Xs_lista, etikett):
    J = [13, 14, 15, 16]; acc3, acc2, flap, rep = [], [], [], []
    for i in range(1, len(frames) - 1):
        f0, f1, f2 = frames[i - 1], frames[i], frames[i + 1]
        if not (f0['shot'] == f1['shot'] == f2['shot'] and f0['actor'] == f1['actor'] == f2['actor']): continue
        cam = KAM[f1['shot']]; a2 = Xs_lista[i - 1][J] - 2 * Xs_lista[i][J] + Xs_lista[i + 1][J]
        acc3 += list(np.linalg.norm(a2, axis=1))
        p0, p1, p2 = (projicera(cam, Xs_lista[k][J]) for k in (i - 1, i, i + 1)); acc2 += list(np.linalg.norm(p0 - 2 * p1 + p2, axis=1))
        flap.append(bool(np.any(np.linalg.norm(Xs_lista[i][[13, 14]] - Xs_lista[i - 1][[13, 14]], axis=1) > .08)))
        I = np.array(f1['image']); vis = [j for j in [11, 12, 13, 14, 15, 16] if I[j, 3] > .8]
        if vis: rep += list(np.linalg.norm(projicera(cam, Xs_lista[i][vis]) - I[vis, :2] * [W, H], axis=1))
    r = {'flaxindex': round(float(np.mean(flap)), 4), 'jitter3d_m_median': round(float(np.median(acc3)), 4), 'jitter3d_m_p90': round(float(np.percentile(acc3, 90)), 4),
         'jitter2d_px_median': round(float(np.median(acc2)), 2), 'jitter2d_px_p90': round(float(np.percentile(acc2, 90)), 2), 'reproj_px_median': round(float(np.median(rep)), 2)}
    print(f'{etikett:<8}', r); return r
gamla = [till_värld(aktorer[f['actor']], np.array(f.get('poseFused') or f['pose'])) for f in frames]
r0 = mått(gamla, 'före'); r1 = mått(nya, 'efter')
ut['stabilization']['metrics'] = {'before': r0, 'after': r1}
(ROOT / 'data/motion-3.json').write_text(json.dumps(ut, separators=(',', ':')), encoding='utf-8')
print('benlängder (överarm, underarm) m:', {k: tuple(round(x, 3) for x in v) for k, v in längd.items()})
print('-> data/motion-3.json')
