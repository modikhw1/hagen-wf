"""Diagnos köttbit: jämför bas mot ändrade (ur kropp_*.json, fasten_*.json): ledernas världsförskjutning relativt roten (cm), medel över rutorna 105–143,
köttbit–handled-avstånd och handledens vinkelskillnad mot bas."""
import json, glob, numpy as np
from scipy.spatial.transform import Rotation as Ro
K = {p[6:-5]: json.load(open(p, encoding='utf-8')) for p in glob.glob('kropp_*.json')}; b = K.pop('bas_b-tilltal-ravara_n06-hand')
F = [str(f) for f in range(105, 144)]
def rel(R, f, n): return np.array(R[f][n]['varld']) - np.array(R[f]['root']['varld'])
for m, R in K.items():
    print('==', m)
    for n in ('c_spine3', 'c_head', 'r_lowarm', 'r_wrist', 'l_wrist'):
        d = np.array([rel(R, f, n) - rel(b, f, n) for f in F]) * 100; print(f'  {n:9s} Δ rel. rot (x,y,z cm) medel {d.mean(0).round(1)}  max|Δ| {np.linalg.norm(d,axis=1).max():.1f}')
    ux = np.array([R[f]['r_wrist']['bild'][0] for f in F]); print(f'  r_wrist bild-x: min {ux.min():.2f} max {ux.max():.2f}  (bas {min(b[f]["r_wrist"]["bild"][0] for f in F):.2f}..{max(b[f]["r_wrist"]["bild"][0] for f in F):.2f}); rutor med x<0: {int((ux<0).sum())}/{len(F)}')
for p in sorted(glob.glob('fasten_*.json')):
    R = json.load(open(p, encoding='utf-8')); B = json.load(open('fasten_bas_b-tilltal-ravara_n06-hand.json', encoding='utf-8'))
    for f, r in R['rutor'].items():
        k = np.array(r['B:hand:kottbit:s3']['varld']); w = np.array(r['person:B/r_wrist']['varld'])
        q = Ro.from_quat(np.roll(r['person:B/r_wrist']['quat'], -1)); q0 = Ro.from_quat(np.roll(B['rutor'][f]['person:B/r_wrist']['quat'], -1))
        print(f'{p[7:-5]:32s} ruta {f}: köttbit–r_wrist {np.linalg.norm(k-w)*100:.1f} cm, köttbit bild-x {r["B:hand:kottbit:s3"]["bild"][0]:+.2f}, r_wrist vinkel mot bas {np.degrees((q*q0.inv()).magnitude()):.0f}°')
