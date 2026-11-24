import sys, time, json, numpy as np, cv2, torch
sys.path.insert(0, 'sam3db/kod')
from sam_3d_body import load_sam_3d_body, SAM3DBodyEstimator
torch.set_num_threads(max(1, torch.get_num_threads()))
t0 = time.time()
model, cfg = load_sam_3d_body('sam3db/ckpt-vith/model.ckpt', device=torch.device('cpu'), mhr_path='sam3db/ckpt-vith/assets/mhr_model.pt')
est = SAM3DBodyEstimator(sam_3d_body_model=model, model_cfg=cfg)
print('laddning', round(time.time()-t0,1), 's', flush=True)
K = 'C:/Users/praiseworthy/Desktop/hagen-wf/scen/klipp/kand-interpooluppsala-7599643065644551446.mp4'
cap = cv2.VideoCapture(K); cap.set(cv2.CAP_PROP_POS_FRAMES, 150); ok, f = cap.read()
m = np.load('masker.npy')[150]; ys, xs = np.nonzero(m); s = 1080/270
box = np.array([[xs.min()*s, ys.min()*s, xs.max()*s, ys.max()*s]], np.float32)
I = json.load(open('colmap/intrinsik.json')); fpx = I['params'][0] * 2  # COLMAP på halv upplösning
Kint = np.array([[fpx,0,540],[0,fpx,960],[0,0,1]], np.float32)
t1 = time.time()
out = est.process_one_image(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), bboxes=box, cam_int=torch.tensor(Kint)[None])
print('inferens', round(time.time()-t1,1), 's', flush=True)
o = out[0]; print({k: (tuple(v.shape) if hasattr(v,'shape') else type(v).__name__) for k, v in o.items()})
np.savez('sam3db/test_150.npz', **{k: np.asarray(v) for k, v in o.items() if hasattr(v, 'shape')})
