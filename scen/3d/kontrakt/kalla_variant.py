"""0033: en arm i scenbygget får en variant för den andra handen (kroppsdel), så att en frihetsgrad i liggaren har en regi.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_variant.py <kalla.json> <ny kalla.json> --arm <objekt-id> --kropp <objekt-id> [--namn vanster]
Allmänt för en platshållarperson byggd av lådor (s_scen.py): armen går från en axel till en handpunkt. Varianten låter armen gå från den
andra axeln (axeln speglad över kroppens mittplan, kroppslådans egen sidoaxel) till samma handpunkt, så att kontakten med föremålet
står kvar. Varianten läggs som objekt['varianter']['kroppsdel'][namn] och märks antagen. Befintliga utdata skrivs aldrig över.
"""
import argparse, copy, math, sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
from gemensamt import ladda, skriv

a = argparse.ArgumentParser(); a.add_argument('kalla'); a.add_argument('ny'); a.add_argument('--arm'); a.add_argument('--kropp'); a.add_argument('--namn', default='vanster'); x = a.parse_args()
kin, kut = Path(x.kalla).resolve(), Path(x.ny).resolve()
if kut.exists(): raise SystemExit(f'{kut} finns redan.')
K = ladda(kin); n = 0
for b in K['matning'].get('scenbygge', []):
    ob = {o['id']: o for o in b['objekt']}
    if x.arm not in ob or x.kropp not in ob: continue
    arm, kr = ob[x.arm], ob[x.kropp]; c = np.array(arm['pos_m']); L = arm['matt_m'][0]; p, y = arm['rotation_rad'][1], arm['rotation_rad'][2]
    d = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), -math.sin(p)]); hand, axel = c + L / 2 * d, c - L / 2 * d
    ky = kr['rotation_rad'][2]; sida = np.array([math.cos(ky), math.sin(ky), 0.]); bas = np.array(kr['pos_m'])
    ny_axel = axel - 2 * ((axel - bas) @ sida) * sida; v = hand - ny_axel; Ln = float(np.linalg.norm(v))
    var = dict(pos_m=((ny_axel + hand) / 2).tolist(), matt_m=[Ln, arm['matt_m'][1], arm['matt_m'][2]],
               rotation_rad=[0., -math.asin(v[2] / Ln), math.atan2(v[1], v[0])], status=f'antagen: {x.namn} hand (axeln speglad över kroppens mittplan, samma handpunkt), 0033')
    arm.setdefault('varianter', {}).setdefault('kroppsdel', {})[x.namn] = var; n += 1
if not n: raise SystemExit('Armen eller kroppen finns inte i något scenbygge.')
K['revision'] += 1; skriv(kut, K); print('KALLA', kut, 'revision', K['revision'], 'varianter', n)
