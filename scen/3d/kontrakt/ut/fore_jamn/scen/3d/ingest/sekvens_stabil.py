"""SAM 3D Body-utdata per ruta -> stabil MHR-sekvens (körs i sam3db-venv: torch + MHR).

Skillnad mot klipp2/sam3db/skelett_sekvens.py: tidslogik och skymningslogik i MHR:s parameterrum, INNAN skelettet räknas fram.
 1. Identiteten (45 formparametrar) låses till medianen.
 2. Luckor fylls linjärt i parameterrummet.
 3. Skymda ben (underkroppens ledpunkter utanför bild eller utanför personmasken): benparametrarna hålls från närmaste
    ruta där benen syns. Syns benen aldrig blir de en neutral stående pose (0), och modellen får inte hitta på ben.
 4. Butterworth-lågpass utan tidsförskjutning (filtfilt) på alla rörelseparametrar: fc = 6 Hz för kroppen och
    8 Hz för händerna (gester bevaras, ingen tidsförskjutning). Samma princip som Blenders Butterworth-utjämning i grafeditorn.
Kör: python sekvens_stabil.py <ramar-mapp> <synlighet.json> <ut.npz> <N> <fps> [palitlig.json]
"""
import sys, os, glob, json, numpy as np, torch
from scipy.signal import butter, filtfilt
mapp, synfil, ut, N, fps = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), float(sys.argv[5])
HIT = os.path.dirname(os.path.abspath(__file__)); SAM = os.path.join(HIT, '..', 'klipp2', 'sam3db')
NAMN = json.load(open(os.path.join(SAM, 'mhr_parametrar.json')))
BEN = np.array([i for i, n in enumerate(NAMN) if any(k in n for k in ('upleg', 'knee', 'lowleg', 'foot')) and not n.startswith('scale')])
HAND = np.array([i for i, n in enumerate(NAMN) if any(k in n for k in ('thumb', 'index', 'middle', 'ring', 'pinky', 'wrist'))])
D = {int(os.path.basename(f)[:4]): np.load(f) for f in sorted(glob.glob(os.path.join(mapp, '*.npz')))}
syn = json.load(open(synfil))                      # {ruta: true/false}: syns underkroppen?
idx = sorted(D); kand = np.zeros(N, bool); kand[idx] = True
P = np.full((N, 204), np.nan); E = np.full((N, 72), np.nan); T = np.full((N, 3), np.nan)
inom = np.zeros(N, bool); inom[idx[0]:idx[-1] + 1] = True
# 1b. tillförlitlighet: en anpassning där kroppen mest ligger utanför bild eller utanför personmasken (personen går ut ur bild,
#     skyms helt) är modellens gissning. Sådana rutor räknas som okända och fylls från grannarna (inne i klippet) eller hålls (i kanten).
pal = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else {}
otillf = [i for i in idx if not pal.get(str(i), True)]
if len(otillf) < len(idx) - 2: idx = [i for i in idx if pal.get(str(i), True)]
for i in idx: P[i] = D[i]['mhr_model_params']; E[i] = D[i]['expr_params']; T[i] = D[i]['pred_cam_t']


def fyll(X):
    X = X.copy(); r = np.arange(N); ok = ~np.isnan(X[:, 0])
    for j in range(X.shape[1]): X[:, j] = np.interp(r, r[ok], X[ok, j])
    return X


from scipy.spatial.transform import Rotation as Rot
ROT = [NAMN.index(n) for n in ('root_rx', 'root_ry', 'root_rz')]
# 2b. roten som kvaternion. MHR:s rot är extrinsisk 'xyz'-Euler (verifierat mot modellen, 0,0°). Nära ±π byter anpassningen mellan
#     likvärdiga Euler-tripplar ([3,07 −0,91 −3,11] ~ [−3,11 −1,08 3,04]); linjär fyllning/utjämning av Euler drar då genom 0 och
#     vrider kroppen 100–180° (barklippet ruta 116 och 126–127). np.unwrap per komponent löser inte det. Kvaternion med
#     kontinuerligt tecken är entydig: fyllning, Hampel och lågpass görs på den, och tillbaka till Euler sist.
Q = np.full((N, 4), np.nan); Q[idx] = Rot.from_euler('xyz', P[idx][:, ROT]).as_quat()
for a_, b_ in zip(idx[:-1], idx[1:]):
    if Q[b_] @ Q[a_] < 0: Q[b_] = -Q[b_]
P, E, T, Q = fyll(P), fyll(E), fyll(T), fyll(Q)
P[:, ROT] = 0.0; QK = np.arange(204, 208)          # kvaternionens kolumner i den utökade matrisen
P = np.concatenate([P, Q], 1)
# 2c. Hampel-filter: en ruta som avviker mer än 3·MAD från medianen över ±4 rutor (t.ex. person sedd bakifrån, felskattad
#     och vänd upp och ner) ersätts med medianen. Standardmetod för robust utjämning; den tar bort spikar men inte gester.
def hampel(X, k=4, n=3.0):
    X = X.copy(); ut_ = np.zeros(len(X), bool)
    for i in range(len(X)):
        a, b = max(0, i - k), min(len(X), i + k + 1); med = np.median(X[a:b], 0); mad = 1.4826 * np.median(np.abs(X[a:b] - med), 0) + 1e-6
        dev = (np.abs(X[i] - med) / mad)[BEDOM]
        if (dev > n).mean() > .15 or (np.abs(X[i, QK] - med[QK]) / mad[QK]).max() > n * 2:      # många parametrar eller roten avviker samtidigt -> trasig ruta
            X[i] = med; ut_[i] = True
    return X, ut_
BEDOM = np.setdiff1d(np.arange(208), np.concatenate([BEN, HAND, ROT]))   # benen och händerna hanteras separat och ska inte fälla rutor
P, utbytta = hampel(P)
# 2d. vrid-spikar per parameter: underarmens/handledens vrid är tvetydigt i en enda bild (känt HMR-fel, "candy wrapper") och
#     hoppar 1–2,5 rad på en ruta. Komponentvis Hampel (±3 rutor, 3·MAD, minst 0,35 rad avvikelse) byter bara ut den enskilda parametern.
VRID = np.array([i for i, n in enumerate(NAMN) if ('twist' in n or 'wrist' in n or 'lowarm' in n) and not n.startswith('scale')])
def hampel_komp(X, cols, k=3, n=3.0, golv=.35):
    X = X.copy(); antal = 0
    for i in range(len(X)):
        a, b = max(0, i - k), min(len(X), i + k + 1); med = np.median(X[a:b, cols], 0); mad = 1.4826 * np.median(np.abs(X[a:b, cols] - med), 0)
        avv = np.abs(X[i, cols] - med); byt = (avv > np.maximum(n * mad, golv)); X[i, cols[byt]] = med[byt]; antal += int(byt.sum())
    return X, antal
P, vridbyten = hampel_komp(P, VRID)
# 2e. fartgräns på vrid/handled: tvetydigheten ger också stegbyten som består i flera rutor (biljard r_wrist_ry 0,66 rad på en
#     ruta, 38°). Max 0,3 rad/ruta (~500°/s, över naturliga gester). Fram- och baklänges begränsning medelvärdesbildas -> ett steg
#     blir en kort centrerad ramp utan tidsförskjutning.
def fartgrans(X, cols, m=.3):
    F_ = X[:, cols].copy(); B_ = X[:, cols].copy()
    for i in range(1, len(X)): F_[i] = np.clip(F_[i], F_[i - 1] - m, F_[i - 1] + m)
    for i in range(len(X) - 2, -1, -1): B_[i] = np.clip(B_[i], B_[i + 1] - m, B_[i + 1] + m)
    X = X.copy(); X[:, cols] = (F_ + B_) / 2; return X
P = fartgrans(P, VRID)
benvis = np.array([bool(syn.get(str(i), False)) for i in range(N)]) & kand
skymda = int((inom & ~benvis).sum())
if benvis.any():
    synliga = np.nonzero(benvis)[0]
    for i in np.nonzero(inom & ~benvis)[0]:
        j = synliga[np.argmin(np.abs(synliga - i))]; P[i, BEN] = P[j, BEN]
else:
    P[:, BEN] = 0.0


def lp(X, fc):
    b, a = butter(2, fc / (fps / 2)); Y = X.copy()
    a0, a1 = idx[0], idx[-1] + 1
    if a1 - a0 > 12: Y[a0:a1] = filtfilt(b, a, X[a0:a1], axis=0)
    return Y


ovr = np.setdiff1d(np.arange(208), HAND)
P[:, ovr] = lp(P[:, ovr], 6.0); P[:, HAND] = lp(P[:, HAND], 8.0); E = lp(E, 8.0)
Qf = P[:, QK] / np.linalg.norm(P[:, QK], axis=1, keepdims=True); P = P[:, :204].copy(); P[:, ROT] = Rot.from_quat(Qf).as_euler('xyz')
m = torch.jit.load(os.path.join(SAM, 'ckpt-vith', 'assets', 'mhr_model.pt'), map_location='cpu')
shape = torch.tensor(np.median(np.stack([D[i]['shape_params'] for i in idx]), 0))[None].float()
with torch.no_grad():
    _, rest = m(shape, torch.zeros(1, 204), torch.zeros(1, 72))
    pose = np.concatenate([m(shape.expand(len(b), -1), torch.tensor(P[b]).float(), torch.tensor(E[b]).float())[1].numpy() for b in np.array_split(np.arange(N), max(1, N // 64))])
fok = float(np.median([float(D[i]['focal_length']) for i in idx]))
np.savez(ut, rest=rest[0].numpy(), pose=pose, cam_t=T, cam_t_ra=T.copy(), fokal=fok, expr=E, kand=kand, inom=inom, ben_synliga=benvis, params=P)
print(json.dumps(dict(rutor=N, otillforlitliga=len(otillf), utbytta_rutor=int(utbytta.sum()), vridbyten=vridbyten, kanda=int(kand.sum()), ben_skymda_rutor=skymda, ben_synliga_rutor=int(benvis.sum()))))
