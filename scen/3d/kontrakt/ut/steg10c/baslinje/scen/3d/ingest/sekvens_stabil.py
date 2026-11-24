"""SAM 3D Body-utdata per ruta -> utjämnad MHR-sekvens (körs i sam3db-venv: torch + MHR).

Ändrat 10 nov (jämn-passet). Före: Hampel-radbyte, komponent-Hampel för handled/underarm, lågpass, cam_t-filter och bildskydd.
Stegvis ablation visar att komponent-Hampel, cam_t-filter och lågpass gav avvikelse. Roten ensam förklarar inte felet.
Nu: rör-utjämning (sekvens_jamn.py), utan komponent-Hampel och ruta-för-ruta-blandning. Metoden ger mindre darr än bildskyddet,
men fortfarande fingerfel och darr i vissa scener; se ingest/README.md. Identiteten är låst som förr.
 1. Identiteten (45 formparametrar) låses till medianen. Rådata varierar; det tidigare påståendet att de var lika var fel.
 2. Rotens orientering som kvaternion med kontinuerligt tecken; luckor och opålitliga rutor har vikt 0 och överbryggas mjukt av utjämnaren.
 3. Skymda ben (benen syns inte): benparametrarna har vikt 0 i de rutorna. Syns benen aldrig blir de en neutral stående pose (0).
 4. Trasiga rutor (många spår hoppar samtidigt mot den utjämnade kurvan) får vikt 0 i stället för att bytas mot en medianruta.
 5. Rör-utjämning per parameterspår: Whittaker (andra differensen, 4 Hz halveffekt) med avvikelsen från estimatet begränsad till 2 brusenheter.
 6. cam_t: siktlinje och log-avstånd utjämnas som egna spår med samma metod (2 Hz).
Kör: python sekvens_stabil.py <ramar-mapp> <synlighet.json> <ut.npz> <N> <fps> [palitlig.json]
"""
import sys, os, glob, json, numpy as np, torch
mapp, synfil, ut, N, fps = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), float(sys.argv[5])
HIT = os.path.dirname(os.path.abspath(__file__)); SAM = os.path.join(HIT, '..', 'klipp2', 'sam3db')
sys.path.insert(0, HIT)
import sekvens_jamn as J
NAMN = json.load(open(os.path.join(SAM, 'mhr_parametrar.json')))
D = {int(os.path.basename(f)[:4]): np.load(f) for f in sorted(glob.glob(os.path.join(mapp, '*.npz')))}
syn = json.load(open(synfil))                      # {ruta: true/false}: syns underkroppen?
idx = sorted(D); kand = np.zeros(N, bool); kand[idx] = True
P = np.full((N, 204), np.nan); E = np.full((N, 72), np.nan); T = np.full((N, 3), np.nan)
inom = np.zeros(N, bool); inom[idx[0]:idx[-1] + 1] = True
# tillförlitlighet: en anpassning där kroppen mest ligger utanför bild eller utanför personmasken är modellens gissning. Sådana rutor räknas som
# okända (vikt 0) och överbryggas inne i klippet, och hålls i kanten.
pal = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else {}
otillf = [i for i in idx if not pal.get(str(i), True)]
if len(otillf) < len(idx) - 2: idx = [i for i in idx if pal.get(str(i), True)]
for i in idx: P[i] = D[i]['mhr_model_params']; E[i] = D[i]['expr_params']; T[i] = D[i]['pred_cam_t']
giltig = ~np.isnan(P[:, 0])
benvis = np.array([bool(syn.get(str(i), False)) for i in range(N)]) & kand
skymda = int((inom & ~benvis).sum())
info = {}
Pn, En = J.stabilisera(P, E, giltig, benvis, fps, NAMN, ut=info)
# cam_t: rå (ifylld) sparas som cam_t_ra; utjämnad som cam_t. Siktlinje och log-avstånd utjämnas, utanför giltiga rutor hålls närmaste värde.
r_ = np.arange(N); Tf = np.stack([np.interp(r_, r_[giltig], T[giltig, j]) for j in range(3)], 1)
Tn = J.utjamna_t(Tf, giltig.astype(float), fps); ixg = np.nonzero(giltig)[0]; Tn[:ixg[0]] = Tn[ixg[0]]; Tn[ixg[-1] + 1:] = Tn[ixg[-1]]
m = torch.jit.load(os.path.join(SAM, 'ckpt-vith', 'assets', 'mhr_model.pt'), map_location='cpu')
shape = torch.tensor(np.median(np.stack([D[i]['shape_params'] for i in idx]), 0))[None].float()
with torch.no_grad():
    _, rest = m(shape, torch.zeros(1, 204), torch.zeros(1, 72))
    pose = np.concatenate([m(shape.expand(len(b), -1), torch.tensor(Pn[b]).float(), torch.tensor(En[b]).float())[1].numpy() for b in np.array_split(np.arange(N), max(1, N // 64))])
fok = float(np.median([float(D[i]['focal_length']) for i in idx]))
np.savez(ut, rest=rest[0].numpy(), pose=pose, cam_t=Tn, cam_t_ra=Tf.copy(), fokal=fok, expr=En, kand=kand, inom=inom, ben_synliga=benvis, params=Pn)
print(json.dumps(dict(rutor=N, otillforlitliga=len(otillf), utbytta_rutor=info['trasiga_rutor'], vridbyten=0, kanda=int(kand.sum()), ben_skymda_rutor=skymda, ben_synliga_rutor=int(benvis.sum()),
                      metod='ror-utjamning', fc=info['fc'], k=info['k'], d=info['d'])))
