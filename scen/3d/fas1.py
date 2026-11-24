"""Phase 1 only. Run with scen/.venv/Scripts/python.exe scen/3d/fas1.py STAGE.

Stages: extract, depth, solve, verify. All writes are inside this directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HOME'] = str(ROOT / 'modeller' / 'huggingface')
os.environ['TORCH_HOME'] = str(ROOT / 'modeller' / 'torch')
os.environ['MPLCONFIGDIR'] = str(ROOT / 'cache' / 'matplotlib')
os.environ['YOLO_CONFIG_DIR'] = str(ROOT / 'cache' / 'ultralytics')
sys.stdout.reconfigure(encoding='utf-8')
import cv2
import numpy as np

VIDEO = REPO / 'scen/klipp/d-dialog-notan.mp4'
CUTS = [0, 73, 114, 171, 256, 281, 337, 383]
ACTORS = ['A', 'B', 'A', 'C', 'B', 'A', 'B']
SHOTS = [dict(id=f'S{i+1}', actor=ACTORS[i], start_frame=CUTS[i], end_frame_exclusive=CUTS[i+1]) for i in range(7)]
W, H = 576, 1024


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def log(text):
    with (ROOT / 'LOGG.md').open('a', encoding='utf-8') as f:
        f.write('\n' + text + '\n')


def get_frame(frame):
    cap = cv2.VideoCapture(str(VIDEO))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
    ok, image = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f'Cannot decode frame {frame}')
    return image


def download_model(name):
    path = ROOT / 'modeller' / f'{name}_landmarker.task'
    path.parent.mkdir(exist_ok=True, parents=True)
    if not path.exists():
        url = f'https://storage.googleapis.com/mediapipe-models/{name}_landmarker/{name}_landmarker/float16/1/{name}_landmarker.task'
        urllib.request.urlretrieve(url, path)
    return path


def landmark_array(landmarks):
    return [[p.x, p.y, p.z, p.visibility, p.presence] for p in landmarks]


def extract():
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python import vision
    start = time.perf_counter()
    models = {'pose': REPO / 'scen/py/modeller/pose_landmarker_full.task',
              'hand': download_model('hand'), 'face': download_model('face')}
    frames = []
    cap = cv2.VideoCapture(str(VIDEO))
    for shot in SHOTS:
        # Reset temporal state at every cut, and never propagate identity across cuts.
        pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(models['pose'])),
            running_mode=vision.RunningMode.VIDEO, num_poses=3,
            min_pose_detection_confidence=.35, min_pose_presence_confidence=.35))
        hand = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(models['hand'])),
            running_mode=vision.RunningMode.IMAGE, num_hands=4,
            min_hand_detection_confidence=.35, min_hand_presence_confidence=.35))
        face = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(models['face'])),
            running_mode=vision.RunningMode.IMAGE, num_faces=4,
            min_face_detection_confidence=.35, min_face_presence_confidence=.35,
            output_face_blendshapes=True, output_facial_transformation_matrixes=True))
        for n in range(shot['start_frame'], shot['end_frame_exclusive']):
            ok, bgr = cap.read()
            if not ok: raise RuntimeError(f'Missing frame {n}')
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            pr = pose.detect_for_video(image, round(n * 1000 / 30))
            candidates = []
            for j, lm in enumerate(pr.pose_landmarks):
                a = np.array([[p.x, p.y] for p in lm])
                torso = a[[0, 11, 12, 23, 24]]
                area = np.prod(np.maximum(np.ptp(torso, axis=0), .01))
                center = torso.mean(axis=0)
                score = area / (1 + 3 * abs(center[0] - .5))
                candidates.append((score, j))
            record = dict(frame=n, t=n/30, shot=shot['id'], actor=shot['actor'],
                          pose=None, hands=[], face=None, detected_people=len(candidates))
            if candidates:
                chosen = max(candidates)[1]
                lm = pr.pose_landmarks[chosen]
                world = pr.pose_world_landmarks[chosen]
                record['pose'] = dict(image=landmark_array(lm), world=landmark_array(world),
                                      source='MediaPipe PoseLandmarker full VIDEO', candidate=chosen)
                # Full source frame avoids changing face camera geometry through cropping.
                fr = face.detect(image)
                nose = np.array([lm[0].x, lm[0].y])
                if fr.face_landmarks:
                    distances = [np.linalg.norm(np.array([f[1].x, f[1].y])-nose) for f in fr.face_landmarks]
                    fi = int(np.argmin(distances))
                    if distances[fi] < .12:
                        matrix = np.asarray(fr.facial_transformation_matrixes[fi])
                        u, _, vt = np.linalg.svd(matrix[:3, :3])
                        record['face'] = dict(
                            blendshapes={c.category_name: c.score for c in fr.face_blendshapes[fi]},
                            transformation_matrix=matrix.tolist(), head_rotation_matrix=(u@vt).tolist(),
                            nose_image=[fr.face_landmarks[fi][1].x, fr.face_landmarks[fi][1].y],
                            source='MediaPipe FaceLandmarker, original full frame')
                if record['face'] is None:
                    # Small/profile faces need an enlarged head ROI. Preserve its camera
                    # provenance: crop-relative face pose is not a calibrated room pose.
                    sw=np.linalg.norm(np.array([lm[11].x-lm[12].x,lm[11].y-lm[12].y])*[W,H])
                    size=max(96,int(sw*.95));cx=int(lm[0].x*W);cy=int((lm[0].y+lm[2].y)*H/2)
                    x0=max(0,cx-size//2);x1=min(W,cx+size//2)
                    y0=max(0,cy-size//2);y1=min(H,cy+size//2)
                    roi=cv2.resize(rgb[y0:y1,x0:x1],(512,512))
                    fallback=face.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=roi))
                    if fallback.face_landmarks:
                        fi=int(np.argmin([np.linalg.norm(np.array([f[1].x,f[1].y])-.5) for f in fallback.face_landmarks]))
                        matrix=np.asarray(fallback.facial_transformation_matrixes[fi]);u,_,vt=np.linalg.svd(matrix[:3,:3])
                        record['face']=dict(blendshapes={c.category_name:c.score for c in fallback.face_blendshapes[fi]},
                            transformation_matrix=matrix.tolist(),head_rotation_matrix=(u@vt).tolist(),
                            crop_xyxy_pixels=[x0,y0,x1,y1],
                            nose_image=[(x0+fallback.face_landmarks[fi][1].x*(x1-x0))/W,(y0+fallback.face_landmarks[fi][1].y*(y1-y0))/H],
                            source='MediaPipe FaceLandmarker enlarged head ROI; matrix is ROI camera-relative')
                hr = hand.detect(image)
                wrists = np.array([[lm[i].x, lm[i].y] for i in [15, 16]])
                shoulder_width = np.linalg.norm(np.array([lm[11].x-lm[12].x, lm[11].y-lm[12].y]))
                for j, hl in enumerate(hr.hand_landmarks):
                    distance = np.linalg.norm(wrists-np.array([hl[0].x, hl[0].y]), axis=1)
                    wi = int(np.argmin(distance))
                    if distance[wi] < max(.06, shoulder_width*.45):
                        record['hands'].append(dict(
                            side=['Left','Right'][wi], handedness_model=hr.handedness[j][0].category_name,
                            score=hr.handedness[j][0].score, wrist_distance_normalized=float(distance[wi]),
                            image=landmark_array(hl), world=landmark_array(hr.hand_world_landmarks[j]),
                            world_origin='hand geometric center; not hip; meters', pose_wrist_index=[15,16][wi]))
            frames.append(record)
        pose.close(); hand.close(); face.close()
        sf = [f for f in frames if f['shot']==shot['id']]
        print(shot['id'], 'frames',len(sf),'pose',sum(f['pose'] is not None for f in sf),
              'face',sum(f['face'] is not None for f in sf),'hands',sum(bool(f['hands']) for f in sf), flush=True)
    cap.release()
    elapsed = time.perf_counter()-start
    coverage = {s['id']: dict(frames=sum(f['shot']==s['id'] for f in frames),
        pose=sum(f['shot']==s['id'] and f['pose'] is not None for f in frames),
        face=sum(f['shot']==s['id'] and f['face'] is not None for f in frames),
        hands=sum(f['shot']==s['id'] and bool(f['hands']) for f in frames)) for s in SHOTS}
    write_json(ROOT/'data/sparning.json',dict(schema='scen3d.motion.phase1.v1',fps=30,width=W,height=H,
        source=str(VIDEO.relative_to(REPO)),shots=SHOTS,frames=frames,coverage=coverage,runtime_s=elapsed,
        coordinates=dict(pose_world='MediaPipe metric hip-centered x right, y down, z away; raw retained',
                         image='x,y normalized; z model relative; visibility,presence',
                         face='canonical-to-observed MediaPipe face matrix; rotation orthonormalized; NOT room transform'),
        models={k:dict(file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for k,p in models.items()}))
    log(f'## Extraction — 30 fps\nRuntime: {elapsed:.1f} s. All 383 decoded source frames; exact cut frame indices {CUTS}. '
        'Temporal pose state reset at cuts. Largest central torso selected; hands matched to its wrists; face matched to its nose. '
        'Missing detections are null, never fabricated or interpolated.\n\nCoverage (frames / pose / face / frames with >=1 hand):\n\n' +
        '\n'.join(f"- {k}: {v['frames']} / {v['pose']} / {v['face']} / {v['hands']}" for k,v in coverage.items()))
    print('Extraction seconds',round(elapsed,2),flush=True)


def depth():
    import torch
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation
    from PIL import Image
    start = time.perf_counter()
    torch.set_num_threads(min(8, os.cpu_count() or 4))
    cached = Path.home()/'.cache/huggingface/hub/models--depth-anything--Depth-Anything-V2-Small-hf/snapshots'
    snapshots = sorted(cached.iterdir()) if cached.exists() else []
    source = str(snapshots[-1]) if snapshots else 'depth-anything/Depth-Anything-V2-Small-hf'
    processor = AutoImageProcessor.from_pretrained(source, local_files_only=bool(snapshots))
    model = AutoModelForDepthEstimation.from_pretrained(source, local_files_only=bool(snapshots)).eval()
    summary=[]
    for shot in SHOTS:
        n = (shot['start_frame']+shot['end_frame_exclusive']-1)//2
        bgr = get_frame(n)
        inputs=processor(images=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)),return_tensors='pt')
        with torch.inference_mode():
            prediction=model(**inputs).predicted_depth
            d=torch.nn.functional.interpolate(prediction.unsqueeze(1),size=(H,W),mode='bicubic',align_corners=False)[0,0].numpy()
        np.save(ROOT/'data'/f'{shot["id"]}-relative-depth.npy',d)
        lo,hi=np.percentile(d,[2,98]);color=cv2.applyColorMap(np.uint8(np.clip((d-lo)/(hi-lo),0,1)*255),cv2.COLORMAP_TURBO)
        cv2.imwrite(str(ROOT/'verifiering'/f'{shot["id"]}-depth.jpg'),np.hstack([bgr,color]))
        summary.append(dict(shot=shot['id'],frame=n,range=[float(d.min()),float(d.max())]))
        print('Depth',shot['id'],flush=True)
    elapsed=time.perf_counter()-start
    write_json(ROOT/'data/depth-metadata.json',dict(model='depth-anything/Depth-Anything-V2-Small-hf',
        model_snapshot=source,units='relative inverse depth; larger is nearer, no metric calibration',shots=summary,runtime_s=elapsed))
    log(f'## Depth inference\nSeven source keyframes, CPU, {elapsed:.1f} s. Reused cached Depth Anything V2 Small weights read-only. '
        'Relative inverse-depth maps retained as .npy; scale and shift are not metric observations. '
        'Official sources: https://github.com/DepthAnything/Depth-Anything-V2 and '
        'https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python .')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['extract','depth','solve','layout','verify'])
    parser.add_argument('--reuse',action='store_true',help='layout only: reassemble saved camera comparison without refitting')
    args=parser.parse_args()
    for folder in ['data','verifiering','modeller','cache']:
        (ROOT/folder).mkdir(exist_ok=True)
    if args.stage in ['extract','depth']:
        globals()[args.stage]()
    else:
        from fas1_geometry import solve, layout, verify, build_layout
        if args.stage=='layout' and args.reuse:
            build_layout(read_json(ROOT/'data/sparning.json'),read_json(ROOT/'data/layout-comparison.json')['shots'])
        else:
            {'solve':solve,'layout':layout,'verify':verify}[args.stage]()
