"""SAM 3D Body-utdata per bildruta -> MHR-skelettets ställning per bildruta (CPU, snabbt: bara MHR framåt).

Kör: sam3db/.venv/Scripts/python.exe sam3db/skelett_sekvens.py <ramar-mapp> <ut.npz> [antal_bildrutor]
Formparametrarna (identiteten) låses till medianen över klippet, så att kroppen inte byter form mellan rutor.
Saknade rutor fylls genom interpolation (position linjärt, rotation slerp) mellan närmaste kända.
Ut: rest (127,8), pose (N,127,8) i modellrummet (cm, Y upp), cam_t (N,3) i meter (OpenCV-kamera), fokal, expr (N,72), kand (N,) bool.
"""
import sys, glob, os, numpy as np, torch
mapp, ut = sys.argv[1], sys.argv[2]
filer = sorted(glob.glob(os.path.join(mapp, '*.npz')))
N = int(sys.argv[3]) if len(sys.argv) > 3 else int(os.path.basename(filer[-1])[:4]) + 1
D = {int(os.path.basename(f)[:4]): np.load(f) for f in filer}
m = torch.jit.load(os.path.join(os.path.dirname(__file__), 'ckpt-vith/assets/mhr_model.pt'), map_location='cpu')
shape = torch.tensor(np.median(np.stack([d['shape_params'] for d in D.values()]), 0))[None].float()
idx = sorted(D)
with torch.no_grad():
    _, rest = m(shape, torch.zeros(1, 204), torch.zeros(1, 72))
    mp = torch.tensor(np.stack([D[i]['mhr_model_params'] for i in idx])).float()
    ex = torch.tensor(np.stack([D[i]['expr_params'] for i in idx])).float()
    _, s = m(shape.expand(len(idx), -1), mp, ex)
s = s.numpy(); cam = np.stack([D[i]['pred_cam_t'] for i in idx]); fok = float(np.median([float(D[i]['focal_length']) for i in idx]))


def slerp(q0, q1, t):
    d = np.dot(q0, q1)
    if d < 0: q1, d = -q1, -d
    if d > .9995: q = q0 + t * (q1 - q0); return q / np.linalg.norm(q)
    th = np.arccos(d); return (np.sin((1 - t) * th) * q0 + np.sin(t * th) * q1) / np.sin(th)


pose = np.zeros((N, 127, 8), np.float32); camt = np.zeros((N, 3)); expr = np.zeros((N, 72)); kand = np.zeros(N, bool)
for k, i in enumerate(idx): pose[i] = s[k]; camt[i] = cam[k]; expr[i] = ex[k].numpy(); kand[i] = True
for i in range(N):
    if kand[i]: continue
    fore = max([j for j in idx if j < i], default=None); efter = min([j for j in idx if j > i], default=None)
    if fore is None or efter is None:
        j = efter if fore is None else fore; pose[i] = pose[j]; camt[i] = camt[j]; expr[i] = expr[j]; continue
    t = (i - fore) / (efter - fore)
    pose[i, :, :3] = (1 - t) * pose[fore, :, :3] + t * pose[efter, :, :3]; pose[i, :, 7] = 1
    for j in range(127): pose[i, j, 3:7] = slerp(pose[fore, j, 3:7], pose[efter, j, 3:7], t)
    camt[i] = (1 - t) * camt[fore] + t * camt[efter]; expr[i] = (1 - t) * expr[fore] + t * expr[efter]
np.savez(ut, rest=rest[0].numpy(), pose=pose, cam_t=camt, fokal=fok, expr=expr, kand=kand)
print('bildrutor', N, 'kända', int(kand.sum()), 'fokal', round(fok, 1))
