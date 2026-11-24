"""0022 punkt 1: sammansatt kropp, i kroppsmodellens parametrar. Körs i sam3db-venv (torch + MHR), som ingest/sekvens_stabil.py.

  scen/3d/klipp2/sam3db/.venv/Scripts/python.exe scen/3d/gennedbrytning/komponera.py
Källor (samma tidsbas, ingestens 156 rutor för S1):
  dagens:  ingest/ut/kand-kennysgelato-tagningar/S1/sekvens_1.npz   (originalets läsning)
  k:       g_forvarld/k/sekvens_1.npz                                (läsningen ur den kamerafria genereringen, förd tillbaka genom inversen)
Regel, led för led:
  - överkropp (rygg, nacke, huvud, nyckelben, armar), ansikte och bäckenets vridning (root_r*): ur dagens, där ruta och led har bildstöd
    (palitlig_1.json per ruta; handled och fingrar per sida ur handsyn_1.json). Saknas bildstöd: ur k, och rutan märks.
  - ben (upleg, knä, underben, fot, tå), rotens läge (root_t*, cam_t) och kroppens mått (parametrar 130–203): ur k.
  - skarven: bäckenet vrids som i originalet, så höftleden (och knä, fot) löses om per ruta så att knän, fotleder och tår står där k har dem.
    Lutningen tas alltså i ryggraden (dagens) och höftleden (omlöst); fötterna står kvar. Lösningen görs för alla rutor samtidigt
    (Adam, 300 steg) med en liten dragning mot k:s vinklar, och benvinklarna jämnas sedan över tiden (Savitzky–Golay, 9 rutor).
  - byte mellan källor i en led jämnas över 5 rutor.
Ut: g_forvarld/sammansatt/sekvens_1.npz (samma nycklar som sekvens_stabil) och komponera.json (källa per ruta och led, skarvens rest).
"""
import json, os
import numpy as np, torch
from scipy.signal import savgol_filter

HIT = os.path.dirname(os.path.abspath(__file__)); D3 = os.path.dirname(HIT)
S1 = os.path.join(D3, 'ingest/ut/kand-kennysgelato-tagningar/S1'); SAM = os.path.join(D3, 'klipp2', 'sam3db')
NP = json.load(open(os.path.join(SAM, 'mhr_parametrar.json'))); NJ = json.load(open(os.path.join(D3, 'ingest/mhr_ledernamn.json')))
UT = os.path.join(HIT, 'g_forvarld', 'sammansatt'); os.makedirs(UT, exist_ok=True)

dag = dict(np.load(os.path.join(S1, 'sekvens_1.npz'))); k = dict(np.load(os.path.join(HIT, 'g_forvarld/k/sekvens_1.npz')))
pal = json.load(open(os.path.join(S1, 'palitlig_1.json'))); hs = json.load(open(os.path.join(S1, 'handsyn_1.json')))
n = len(dag['params'])
BEN = [i for i, x in enumerate(NP) if any(t in x for t in ('upleg', 'knee', 'lowleg', 'foot', 'ball', 'toe')) and i < 130]
ROT_T = [0, 1, 2]; ROT_R = [3, 4, 5]; MATT = list(range(130, 204))
HAND = {s: [i for i, x in enumerate(NP) if i < 130 and x.startswith(s + '_') and any(t in x for t in ('wrist', 'thumb', 'index', 'middle', 'ring', 'pinky'))] for s in ('r', 'l')}
OVER = [i for i in range(6, 130) if i not in BEN and i not in HAND['r'] and i not in HAND['l']]

# vikt per ruta och grupp: 1 = dagens, 0 = k. Utan k-ruta (k inte inom): dagens rakt av.
kin = k['inom'].astype(bool); w_over = np.array([1.0 if pal.get(str(i), True) else 0.0 for i in range(n)])
w_hand = {'r': np.array(hs['h']['synlig'], float)[:n], 'l': np.array(hs['v']['synlig'], float)[:n]}
def mjuka(w): return np.clip(np.convolve(np.pad(w, 2, mode='edge'), np.ones(5) / 5, 'valid'), 0, 1)
w_over, w_hand = mjuka(w_over), {s: mjuka(v) for s, v in w_hand.items()}
P = k['params'].copy()
for i in range(n):
    if not kin[i]: P[i] = dag['params'][i]; continue
    P[i, OVER] = w_over[i] * dag['params'][i, OVER] + (1 - w_over[i]) * k['params'][i, OVER]
    for s in ('r', 'l'): P[i, HAND[s]] = w_hand[s][i] * dag['params'][i, HAND[s]] + (1 - w_hand[s][i]) * k['params'][i, HAND[s]]
    P[i, ROT_R] = w_over[i] * dag['params'][i, ROT_R] + (1 - w_over[i]) * k['params'][i, ROT_R]
m = torch.jit.load(os.path.join(SAM, 'ckpt-vith', 'assets', 'mhr_model.pt'), map_location='cpu')
# formen (45 identitetsparametrar) är inte sparad i sekvensen: medianen ur k:s rutor, som i sekvens_stabil
import glob
shape = torch.tensor(np.median(np.stack([np.load(f)['shape_params'] for f in sorted(glob.glob(os.path.join(HIT, 'g_forvarld/k/kropp/*.npz')))]), 0))[None].float()
E = torch.tensor(dag['expr']).float()
def fk(Pt, idx=None):
    b = len(Pt); return m(shape.expand(b, -1), Pt, E[idx] if idx is not None else E[:b])[1]
mal_led = [NJ.index(x) for x in ('l_lowleg', 'r_lowleg', 'l_foot', 'r_foot', 'l_ball', 'r_ball')]
idx = np.flatnonzero(kin); Kt = torch.tensor(k['params'][idx]).float()
with torch.no_grad(): mal = fk(Kt, torch.tensor(idx))[:, mal_led, :3]
Pt = torch.tensor(P[idx]).float(); var = Pt[:, BEN].clone().requires_grad_(True); fast = Pt.clone()
opt = torch.optim.Adam([var], lr=0.02)
for steg in range(300):
    X = fast.clone(); X[:, BEN] = var
    Y = fk(X, torch.tensor(idx))[:, mal_led, :3]
    loss = ((Y - mal) ** 2).sum(-1).mean() + 1e-3 * ((var - Kt[:, BEN]) ** 2).mean()
    opt.zero_grad(); loss.backward(); opt.step()
with torch.no_grad():
    X = fast.clone(); X[:, BEN] = var; rest_cm = ((fk(X, torch.tensor(idx))[:, mal_led, :3] - mal) ** 2).sum(-1).sqrt()
ben = var.detach().numpy(); ben = savgol_filter(ben, 9, 2, axis=0) if len(ben) >= 9 else ben
P[idx[:, None], np.array(BEN)[None]] = ben
Pt = torch.tensor(P).float()
with torch.no_grad():
    pose = np.concatenate([m(shape.expand(len(b), -1), Pt[b], E[b])[1].numpy() for b in np.array_split(np.arange(n), max(1, n // 64))])
    rest = m(shape, torch.zeros(1, 204), torch.zeros(1, 72))[1][0].numpy()
cam_t = np.where(kin[:, None], k['cam_t'], dag['cam_t'])
np.savez(os.path.join(UT, 'sekvens_1.npz'), rest=rest, pose=pose, cam_t=cam_t, cam_t_ra=cam_t.copy(), fokal=k['fokal'], expr=dag['expr'], kand=k['kand'] | dag['kand'],
         inom=k['inom'] | dag['inom'], ben_synliga=np.where(kin, k['ben_synliga'], dag['ben_synliga']), params=P)
rap = dict(rutor=n, k_rutor=int(kin.sum()), overkropp_ur_k_rutor=[int(i) for i in np.flatnonzero(kin & (w_over < 1))],
           hand_ur_k_rutor={s: int((kin & (w_hand[s] < 0.5)).sum()) for s in ('r', 'l')},
           skarv_rest_cm=dict(median=round(float(rest_cm.median()), 2), max=round(float(rest_cm.max()), 2)),
           grupper=dict(ben=len(BEN), overkropp=len(OVER), hand_r=len(HAND['r']), hand_l=len(HAND['l'])))
json.dump(rap, open(os.path.join(UT, 'komponera.json'), 'w'), indent=1); print(json.dumps(rap))
