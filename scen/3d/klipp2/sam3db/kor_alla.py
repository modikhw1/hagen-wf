"""SAM 3D Body över klippet (CPU), var STEG:e bildruta, kan återupptas. Personruta från YOLO-maskerna, fast fokal ur COLMAP (2154 px)."""
import sys, time, os, json, numpy as np, cv2, torch
sys.path.insert(0, 'sam3db/kod')
from sam_3d_body import load_sam_3d_body, SAM3DBodyEstimator
STEG = int(sys.argv[1]) if len(sys.argv) > 1 else 3
model, cfg = load_sam_3d_body('sam3db/ckpt-vith/model.ckpt', device=torch.device('cpu'), mhr_path='sam3db/ckpt-vith/assets/mhr_model.pt')
est = SAM3DBodyEstimator(sam_3d_body_model=model, model_cfg=cfg)
M = np.load('masker.npy'); s = 1080 / 270
K = np.array([[2154.07, 0, 540], [0, 2154.07, 960], [0, 0, 1]], np.float32)
cap = cv2.VideoCapture('C:/Users/praiseworthy/Desktop/hagen-wf/scen/klipp/kand-interpooluppsala-7599643065644551446.mp4')
ramar = []; i = 0
while True:
    ok, f = cap.read()
    if not ok: break
    if i % STEG == 0: ramar.append((i, f))
    i += 1
# ordning: grovt först (var 9:e), sedan resten, så att en tidig avbrytning ändå täcker hela klippet
ramar.sort(key=lambda x: (x[0] % 9 != 0, x[0]))
for i, f in ramar:
    ut = f'sam3db/ramar/{i:04d}.npz'
    if os.path.exists(ut): continue
    ys, xs = np.nonzero(M[i])
    if len(xs) < 50: continue
    box = np.array([[xs.min()*s, ys.min()*s, xs.max()*s, ys.max()*s]], np.float32)
    t = time.time()
    out = est.process_one_image(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), bboxes=box, cam_int=torch.tensor(K)[None])
    if out:
        np.savez(ut, **{k: np.asarray(v) for k, v in out[0].items() if hasattr(v, 'shape')})
    print(i, round(time.time() - t, 1), 's', flush=True)
