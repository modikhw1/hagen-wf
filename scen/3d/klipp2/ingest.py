"""CPU-only, frame-exact source observations. Cached, separate from edit path."""
from pathlib import Path
import os, json, time, argparse, hashlib
os.environ['CUDA_VISIBLE_DEVICES']=''
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT.parent/'klipp/kand-interpooluppsala-7599643065644551446.mp4'
def write(name, data):
    (HERE/name).write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
def image(a): return mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)))
def lm(a): return [[v.x,v.y,v.z] for v in a]

def main():
    cv2.setNumThreads(3)
    start=time.perf_counter(); out=HERE/'observations';out.mkdir(exist_ok=True)
    (HERE/'source').mkdir(exist_ok=True)
    base=lambda p:python.BaseOptions(model_asset_path=str(p),delegate=python.BaseOptions.Delegate.CPU)
    pose=vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=base(ROOT.parent/'py/modeller/pose_landmarker_full.task'),running_mode=vision.RunningMode.VIDEO,num_poses=1,min_pose_detection_confidence=.35,min_tracking_confidence=.35))
    hands=vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(base_options=base(ROOT/'modeller/hand_landmarker.task'),num_hands=1,min_hand_detection_confidence=.25,min_hand_presence_confidence=.25))
    face=vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=base(ROOT/'modeller/face_landmarker.task'),num_faces=1,min_face_detection_confidence=.3,min_face_presence_confidence=.3,output_face_blendshapes=True,output_facial_transformation_matrixes=True))
    masks=np.load(HERE/'masker.npy',mmap_mode='r');cap=cv2.VideoCapture(str(SOURCE));rows=[];timings=dict(pose=0.,hands=0.,face=0.)
    for i in range(369):
        ok,im=cap.read(); assert ok
        im=cv2.resize(im,(540,960));cv2.imwrite(str(HERE/'source'/f'{i:04d}.jpg'),im,[cv2.IMWRITE_JPEG_QUALITY,96])
        cache=out/f'{i:04d}.json'
        if cache.exists(): rows.append(json.loads(cache.read_text()));continue
        t=time.perf_counter();p=pose.detect_for_video(image(im),round(i*1000/30));timings['pose']+=time.perf_counter()-t
        row=dict(frame=i,pose=[],world=[],visibility=[],hands=[],face={},face_matrix=None)
        if p.pose_landmarks:
            row.update(pose=lm(p.pose_landmarks[0]),world=lm(p.pose_world_landmarks[0]),visibility=[v.visibility for v in p.pose_landmarks[0]])
            points=np.array(row['pose'])[:,:2]*[540,960]
            for side,wi,ei in [('Left',15,13),('Right',16,14)]:
                # Wrist-centred independent crops avoid background people and improve small fingers.
                wrist=points[wi];d=np.linalg.norm(wrist-points[ei]);radius=int(np.clip(d*.85,40,150));center=wrist+(wrist-points[ei])*.22
                x,y=np.maximum(0,center-radius).astype(int);xx,yy=np.minimum([540,960],center+radius).astype(int)
                if xx-x<20 or yy-y<20: continue
                t=time.perf_counter();h=hands.detect(image(im[y:yy,x:xx]));timings['hands']+=time.perf_counter()-t
                if h.hand_landmarks:
                    uv=np.array(lm(h.hand_landmarks[0]));uv[:,:2]=(uv[:,:2]*[xx-x,yy-y]+[x,y])/[540,960]
                    if np.linalg.norm(uv[0,:2]*[540,960]-wrist)<radius:
                        row['hands'].append(dict(side=side,image=uv.tolist(),world=lm(h.hand_world_landmarks[0]),score=h.handedness[0][0].score))
            nose=points[0];radius=int(np.clip(np.linalg.norm(points[7]-points[8])*1.3,45,130));x,y=np.maximum(0,nose-radius).astype(int);xx,yy=np.minimum([540,960],nose+radius).astype(int)
            t=time.perf_counter();f=face.detect(image(im[y:yy,x:xx]));timings['face']+=time.perf_counter()-t
            if f.face_blendshapes:
                row['face']={v.category_name:float(v.score) for v in f.face_blendshapes[0]}
                row['face_matrix']=f.facial_transformation_matrixes[0].tolist()
                uv=np.array(lm(f.face_landmarks[0]));uv[:,:2]=(uv[:,:2]*[xx-x,yy-y]+[x,y])/[540,960];row['face_landmarks']=uv.tolist()
        cache.write_text(json.dumps(row,separators=(',',':')),encoding='utf-8');rows.append(row)
        if i%30==0:print('MediaPipe',i,round(time.perf_counter()-start,1),flush=True)
    cap.release();pose.close();hands.close();face.close()
    write('mediapipe.json',dict(width=540,height=960,fps=30,frames=rows))
    write('ingest-timing.json',dict(total_s=time.perf_counter()-start,inference_s=timings,pose_frames=sum(bool(r['pose']) for r in rows),face_frames=sum(bool(r['face']) for r in rows),left_hand_frames=sum(any(h['side']=='Left' for h in r['hands']) for r in rows),right_hand_frames=sum(any(h['side']=='Right' for h in r['hands']) for r in rows)))
    print('DONE',time.perf_counter()-start,flush=True)

if __name__=='__main__': main()
