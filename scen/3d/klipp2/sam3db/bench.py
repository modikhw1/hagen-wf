import sys, time, json, numpy as np, cv2, torch
sys.path.insert(0, 'sam3db/kod')
from sam_3d_body import load_sam_3d_body, SAM3DBodyEstimator
torch.set_num_threads(8)
model, cfg = load_sam_3d_body('sam3db/ckpt-vith/model.ckpt', device=torch.device('cpu'), mhr_path='sam3db/ckpt-vith/assets/mhr_model.pt')
est = SAM3DBodyEstimator(sam_3d_body_model=model, model_cfg=cfg)
cap = cv2.VideoCapture('C:/Users/praiseworthy/Desktop/hagen-wf/scen/klipp/kand-interpooluppsala-7599643065644551446.mp4'); cap.set(cv2.CAP_PROP_POS_FRAMES, 150); ok, f = cap.read()
m = np.load('masker.npy')[150]; ys, xs = np.nonzero(m); s = 1080/270
box = np.array([[xs.min()*s, ys.min()*s, xs.max()*s, ys.max()*s]], np.float32)
K = torch.tensor(np.array([[2154.07,0,540],[0,2154.07,960],[0,0,1]], np.float32))[None]
ref = np.load('sam3db/test_150.npz')
img = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
for typ in sys.argv[1:]:
    t = time.time()
    with torch.inference_mode():
        o = est.process_one_image(img, bboxes=box, cam_int=K, inference_type=typ)[0]
    dt = time.time() - t
    k = np.asarray(o['pred_keypoints_2d']); d = np.linalg.norm(k - ref['pred_keypoints_2d'], axis=1)
    print(f'{typ}: {dt:.1f} s | 2D-avvikelse mot full: kropp(0-20) median {np.median(d[:21]):.1f} px, händer(21-62) median {np.median(d[21:63]):.1f} px max {d[21:63].max():.1f}', flush=True)
    np.savez(f'sam3db/bench_{typ}.npz', **{kk: np.asarray(v) for kk, v in o.items() if hasattr(v, 'shape')})
