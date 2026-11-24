"""Streaming NumPy/OpenCV measurements, no torch, model loading, or inference.

Reuse kroppmatt exactly. All outputs confined to this script's directory.
"""
import json
import sys
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
CONTRACT = ROOT.parent / 'kontrakt'
sys.path.insert(0, str(CONTRACT))
import kroppmatt as KM

cv2.setNumThreads(1)
RIG = json.loads((CONTRACT / 'tro_rigg.json').read_text(encoding='utf-8'))
NAMES = RIG['namn']
IX = {n: i for i, n in enumerate(NAMES)}
BODY_NAMES = ['root', 'l_upleg', 'r_upleg', 'l_lowleg', 'r_lowleg', 'l_foot', 'r_foot',
              'c_neck', 'c_head', 'l_uparm', 'r_uparm', 'l_lowarm', 'r_lowarm', 'l_wrist', 'r_wrist']
BODY = [IX[n] for n in BODY_NAMES]
LEGS = [IX[n] for n in BODY_NAMES[1:7]]
HANDS = [i for i, n in enumerate(NAMES) if any(k in n for k in
         ['thumb', 'index', 'middle', 'ring', 'pinky']) or n in ['l_wrist', 'r_wrist', 'l_wrist_twist', 'r_wrist_twist']]
FINGERS = [i for i in HANDS if 'wrist' not in NAMES[i]]
F = np.diag([1., -1., -1.])


def read_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def clean(x):
    if isinstance(x, dict): return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, np.ndarray): return clean(x.tolist())
    if isinstance(x, (float, np.floating)): return float(x) if np.isfinite(x) else None
    if isinstance(x, np.integer): return int(x)
    return x


def save_json(p, value):
    Path(p).write_text(json.dumps(clean(value), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def range_metrics(x, hidden):
    a = x.copy()
    a[~hidden] = np.nan
    rel = a - a[:, IX['root']:IX['root'] + 1]
    if not np.isfinite(rel).any(): return {'frames': 0}
    r = np.nanmax(rel[:, LEGS], axis=0) - np.nanmin(rel[:, LEGS], axis=0)
    return {'frames': int(hidden.sum()), 'jitter_cm_frame2': KM.jitter(a[:, LEGS]),
            'root_relative_jitter_cm_frame2': KM.jitter(rel[:, LEGS]),
            'root_relative_range_xyz_cm': r, 'max_joint_range_diagonal_cm': np.linalg.norm(r, axis=1).max(),
            'max_depth_range_cm': r[:, 2].max(),
            'note': 'Temporal stability only; hidden-joint ground truth is unavailable.'}


def sequence_metrics(x, hidden):
    fingers = x[:, FINGERS].copy()
    for j, i in enumerate(FINGERS):
        fingers[:, j] -= x[:, IX[NAMES[i][0] + '_wrist']]
    return {'jitter_body15_cm_frame2': KM.jitter(x[:, BODY]),
            'jitter_all127_cm_frame2': KM.jitter(x),
            'jitter_root_relative_body15_cm_frame2': KM.jitter(x[:, BODY] - x[:, IX['root']:IX['root'] + 1]),
            'hands': {'available': True, 'joints': len(HANDS),
                      'jitter_cm_frame2': KM.jitter(x[:, HANDS]),
                      'wrist_jitter_cm_frame2': KM.jitter(x[:, [IX['l_wrist'], IX['r_wrist']]]),
                      'finger_relative_to_wrist_jitter_cm_frame2': KM.jitter(fingers)},
            'hidden_legs': range_metrics(x, hidden),
            'frames_3d': int(np.isfinite(x).all(axis=(1, 2)).sum())}


def raw_frame(p, w, h, mw, mh):
    with np.load(p) as z:
        x = (z['pred_joint_coords'].astype(float) + z['pred_cam_t'].astype(float)) * 100
        sil = KM.estimator_silhuett(z, w, h, mw, mh)
        focal = float(z['focal_length'])
    return x, sil, focal


def seq_frame(z, f, w, h, mw, mh, before=False):
    if before:
        pose = z.get('pose_fore_kontakt', z['pose'])[f].copy()
        pose[:, :3] /= z.get('golv_skala', np.ones(len(z['pose'])))[f]
        translation = z.get('cam_t_fore_golv', z['cam_t'])[f]
    else:
        pose, translation = z['pose'][f], z['cam_t'][f]
    x = pose[:, :3] @ F + 100 * translation
    vertices = KM.hudhorn(pose) / 100 @ F + translation
    if (vertices[:, 2] < .05).mean() > .02:
        return x, None, float(z['fokal'])
    uv = vertices[:, :2] / vertices[:, 2:3] * float(z['fokal']) + [w/2, h/2]
    sil = KM.fyll(uv * [mw/w, mh/h], KM.hud()['faces'], mw, mh)
    return x, sil, float(z['fokal'])


def overlay(source, frame_data, label, f, w, h):
    tile = cv2.resize(source, (288, 512), interpolation=cv2.INTER_AREA)
    for pid, (x, sil, focal) in frame_data.items():
        col = (20, 240, 250) if pid == '1' else (250, 240, 40)
        if sil is not None:
            big = cv2.resize(sil.astype(np.uint8), (288, 512), interpolation=cv2.INTER_NEAREST)
            contours, _ = cv2.findContours(big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(tile, contours, -1, col, 1)
        uv = x[:, :2] / x[:, 2:3] * focal + [w/2, h/2]
        uv *= [288/w, 512/h]
        # Use rig hierarchy; procedural twist and facial bones are omitted.
        draw = set(BODY + HANDS + [IX[n] for n in ['c_spine0','c_spine1','c_spine2','c_spine3','l_clavicle','r_clavicle']])
        for j in draw:
            parent = RIG.get('parents', [])[j] if 'parents' in RIG else -1
            if parent < 0:
                # tro_rigg uses 'foralder' in some revisions; use the fixed read-only skeleton.
                parent = PARENTS[j]
            if parent not in draw: continue
            a, b = uv[[j, parent]]
            if np.isfinite([a,b]).all() and np.abs([a,b]).max() < 20000:
                cv2.line(tile, tuple(np.round(a).astype(int)), tuple(np.round(b).astype(int)), col, 1, cv2.LINE_AA)
        for j in BODY:
            if np.isfinite(uv[j]).all() and (uv[j] >= 0).all() and (uv[j] < [288,512]).all():
                cv2.circle(tile, tuple(np.round(uv[j]).astype(int)), 2, col, -1)
    cv2.rectangle(tile, (0,0), (288,36), (15,15,15), -1)
    cv2.putText(tile, f'{label} f{f}', (7,23), cv2.FONT_HERSHEY_SIMPLEX, .48, (255,255,255), 1, cv2.LINE_AA)
    return tile


PARENTS = read_json(ROOT.parent / 'klipp2/sam3db/mhr_skelett.json')['parents']


def evaluate_shot(entry, method):
    folder = Path(entry['folder'])
    out = ROOT / 'ut' / method / entry['id']
    out.mkdir(parents=True, exist_ok=True)
    n, w, h = (entry['meta'][k] for k in ['N','bredd','hojd'])
    mask = np.load(folder / 'masker.npy', mmap_mode='r')
    mh, mw = mask.shape[1:]
    boxes = read_json(folder / 'personer.json')
    seq = {pid: dict(np.load(folder / f'sekvens_{pid}.npz')) for pid in entry['pids']}
    xs = {pid: np.full((n,127,3), np.nan) for pid in entry['pids']}
    samples = {pid: [] for pid in entry['pids']}
    rows = []
    selected = set(np.linspace(0, n-1, 8).round().astype(int))
    cap = cv2.VideoCapture(entry['video'])
    tiles = []
    for f in range(n):
        frame_data = {}
        for pid in entry['pids']:
            if method in ('slutsekvens', 'fore-golv-kontakt'):
                if not seq[pid]['inom'][f]: continue
                value = seq_frame(seq[pid], f, w,h,mw,mh, before=method=='fore-golv-kontakt')
            else:
                p = (folder/'kropp' if method=='sam-raw' else ROOT/'ut'/method/entry['id']) / pid / f'{f:04d}.npz'
                if not p.exists(): continue
                value = raw_frame(p,w,h,mw,mh)
            xs[pid][f] = value[0]
            frame_data[pid] = value
        for pid, (_, sil, _) in frame_data.items():
            if sil is None or str(f) not in boxes.get(pid, {}): continue
            others = [v[1] for p,v in frame_data.items() if p != pid and v[1] is not None]
            other = np.logical_or.reduce(others) if others else None
            box = np.asarray(boxes[pid][str(f)]) * [mw/w,mh/h,mw/w,mh/h]
            metric = KM.jamfor_mask(sil, mask[f].astype(bool), box,mw,mh, andra=other)
            if metric: samples[pid].append({'frame':f, **metric})
        if f in selected:
            cap.set(cv2.CAP_PROP_POS_FRAMES, f)
            ok, source = cap.read()
            if ok: tiles.append(overlay(source, frame_data, method, f,w,h))
    cap.release()
    if tiles: cv2.imwrite(str(out/'overlay.jpg'), np.concatenate(tiles,axis=1), [cv2.IMWRITE_JPEG_QUALITY,90])
    for pid in entry['pids']:
        hidden = seq[pid]['inom'].astype(bool) & ~seq[pid]['ben_synliga'].astype(bool)
        metrics = sequence_metrics(xs[pid], hidden)
        reliable = read_json(folder/f'palitlig_{pid}.json') if (folder/f'palitlig_{pid}.json').exists() else {}
        fair = xs[pid].copy()
        for f in range(n):
            if not reliable.get(str(f),True): fair[f] = np.nan
        metrics['jitter_all127_reliable_cm_frame2'] = KM.jitter(fair)
        metrics['silhouette'] = KM.sammanfatta(samples[pid])
        metrics['silhouette']['mask_boxes_available'] = len(boxes.get(pid, {}))
        metrics['silhouette']['all_mask_frames_attempted'] = True
        row = {'method':method,'shot':entry['id'],'person':pid, **metrics}
        np.savez_compressed(out/f'joints_{pid}.npz', camera_cm=xs[pid], hidden_legs=hidden)
        save_json(out/f'metrics_{pid}.json', row)
        save_json(out/f'silhouette_frames_{pid}.json', samples[pid])
        rows.append(row)
    return rows


def main():
    manifest = read_json(ROOT/'manifest.json')
    rows=[]
    for method in ['sam-raw','slutsekvens','fore-golv-kontakt','fast-vith']:
        for entry in manifest['shots']:
            if method=='fast-vith' and not (ROOT/'ut'/method/entry['id']/'timing.json').exists(): continue
            result = evaluate_shot(entry, method)
            rows.extend(result)
            for r in result:
                print(method,entry['id'],r['person'], 'j15',round(r['jitter_body15_cm_frame2'],3),
                      'j127',round(r['jitter_all127_cm_frame2'],3), 'iou',round(r['silhouette'].get('iou_median',float('nan')),3),flush=True)
    save_json(ROOT/'matningar.json', {'rows':rows,
              'joint_mapping':{'body15':{n:IX[n] for n in BODY_NAMES},
                               'hands':{NAMES[i]:i for i in HANDS},
                               'hidden_legs':{NAMES[i]:i for i in LEGS}},
              'coordinate_system':'Camera coordinates in cm, y down, z forward; final MHR cm multiplied by diag(1,-1,-1), plus camera translation.',
              'independent_2d_pose':None,
              'independent_2d_pose_reason':'No independent detector used by the cached ViT-H/supplied-box Fast variant; no new model inference locally.',
              'baseline_final_scope':'Persisted sekvens_*.npz including saved floor/contact corrections; later render-plan support is not replayed.',
              'mask_limitation':'masker.npy is a union of YOLO person masks, evaluated in each tracked box excluding other predicted silhouettes. Occluding tables and clothing are not body geometry.'})


if __name__=='__main__': main()
