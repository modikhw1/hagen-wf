"""COLMAP-kamera (var 3:e ruta, halv upplösning) + SAM 3D Body (person i kamerarummet, meter) -> gemensam metrisk värld.
Skalan k (COLMAP-enheter -> meter) väljs så att personens rotbana i världen blir jämnast (minst acceleration).
Gravitation: världens upp-axel = medel av personens ryggriktning (rot->nacke) över klippet.
Ut: varld.npz med kam_R (N,3,3) värld<-kamera (OpenCV), kam_C (N,3) i meter, k, upp, rot_varld (N,3)."""
import numpy as np, pycolmap, glob
rec = pycolmap.Reconstruction('colmap/sparse/1'); S = np.load('sam3db/sekvens.npz'); N = len(S['pose'])
F = np.diag([1., -1., -1.])
pos = {}
for im in rec.images.values():
    i = int(im.name[:4]); T = im.cam_from_world() if callable(im.cam_from_world) else im.cam_from_world
    Rcw = np.array(T.rotation.matrix()); t = np.array(T.translation)
    pos[i] = (Rcw.T, -Rcw.T @ t)            # värld<-kamera, kamerans centrum
idx = sorted(pos); print('COLMAP-rutor', len(idx), idx[:3], idx[-3:])
def interp(i):
    if i in pos: return pos[i]
    a = max([j for j in idx if j < i], default=idx[0]); b = min([j for j in idx if j > i], default=idx[-1])
    if a == b: return pos[a]
    t = (i - a) / (b - a); from scipy.spatial.transform import Rotation as Ro, Slerp
    sl = Slerp([0, 1], Ro.from_matrix([pos[a][0], pos[b][0]])); return sl(t).as_matrix(), (1 - t) * pos[a][1] + t * pos[b][1]
RC = [interp(i) for i in range(N)]; R = np.stack([r for r, _ in RC]); C = np.stack([c for _, c in RC])
# personens rot (led 1, höft) i kamerarummet, meter: F @ (modell_cm/100) + cam_t
rot_kam = np.stack([F @ (S['pose'][i, 1, :3] / 100) + S['cam_t'][i] for i in range(N)])
nacke_kam = np.stack([F @ (S['pose'][i, 110, :3] / 100) + S['cam_t'][i] for i in range(N)])
def bana(k): return np.stack([k * C[i] + R[i] @ rot_kam[i] for i in range(N)])
ks = np.exp(np.linspace(np.log(.05), np.log(50), 400)); rad = [np.abs(np.diff(bana(k), 2, axis=0)).mean() for k in ks]
k = float(ks[int(np.argmin(rad))]); W = bana(k)
upp = np.mean([R[i] @ ((nacke_kam[i] - rot_kam[i]) / np.linalg.norm(nacke_kam[i] - rot_kam[i])) for i in range(N)], 0); upp /= np.linalg.norm(upp)
steg = np.linalg.norm(W[-1] - W[0])
print('skala k', round(k, 3), '| jämnhet', round(min(rad) * 100, 3), 'cm/ruta² | kamerans väg', round(float(np.linalg.norm(np.diff(k * C, axis=0), axis=1).sum()), 2), 'm | personens förflyttning', round(float(steg), 2), 'm')
np.savez('varld.npz', kam_R=R, kam_C=k * C, k=k, upp=upp, rot_varld=W)
