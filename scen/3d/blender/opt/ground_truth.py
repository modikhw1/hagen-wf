"""CPU source measurements; raw detector outputs are immutable evaluation data."""
import os, sys, json, time, hashlib, urllib.request, zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(HERE/'deps'))
os.environ['YOLO_CONFIG_DIR']=str(HERE/'cache/ultralytics')
os.environ['CUDA_VISIBLE_DEVICES']=''
import cv2
import numpy as np

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v): Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    import torch
    torch.set_num_threads(4)
    cv2.setNumThreads(4)
    from ultralytics import YOLO, SAM
    from rtmlib import RTMPose
    gt=HERE/'gt';gt.mkdir(exist_ok=True)
    for d in ['source','masks','sheets']: (gt/d).mkdir(exist_ok=True)
    modeldir=HERE/'models';modeldir.mkdir(exist_ok=True)
    modelname='rtmw-dw-x-l_simcc-cocktail14_270e-384x288_20231122.zip'
    url='https://huggingface.co/Tau-J/RTMPose/resolve/main/rtmw/onnx_sdk/'+modelname
    archive=modeldir/modelname
    if not archive.exists():
        print('Downloading RTMW whole-body model',flush=True)
        urllib.request.urlretrieve(url,archive)
    if not list(modeldir.rglob('*.onnx')):
        with zipfile.ZipFile(archive) as z: z.extractall(modeldir)
    onnx=next(modeldir.rglob('*.onnx'))
    import onnxruntime as ort
    ort.set_default_logger_severity(3)
    pose=RTMPose(str(onnx),model_input_size=(288,384),backend='onnxruntime',device='cpu')
    options=ort.SessionOptions();options.intra_op_num_threads=4;options.inter_op_num_threads=1
    pose.session=ort.InferenceSession(str(onnx),sess_options=options,providers=['CPUExecutionProvider'])
    detector=YOLO(str(ROOT.parent/'py/modeller/yolo11n-seg.pt'))
    mp=read(ROOT/'data/sparning.json')
    cap=cv2.VideoCapture(str(ROOT.parent/'klipp/d-dialog-notan.mp4'))
    rows=[];start=time.perf_counter();sam=None;segmentation='YOLO11n-seg fallback' if '--yolo' in sys.argv else None;probe=None
    for f in mp['frames']:
        i=f['frame'];ok,im=cap.read();assert ok
        cv2.imwrite(str(gt/'source'/f'{i:04d}.jpg'),im,[cv2.IMWRITE_JPEG_QUALITY,95])
        cache=gt/f'raw-{i:04d}.json'
        cached=read(cache) if cache.exists() else None
        if cached and cached['segmentation']==segmentation:rows.append(cached);continue
        y=detector.predict(im,imgsz=1024,conf=.15,classes=[0],retina_masks=True,verbose=False,device='cpu')[0]
        nose=np.array(f['pose']['image'][0][:2])*[576,1024]
        boxes=y.boxes.xyxy.numpy()
        assert len(boxes),'Main person not detected'
        rank=[(10000 if b[0]<=nose[0]<=b[2] and b[1]<=nose[1]<=b[3] else 0)-np.linalg.norm((b[:2]+b[2:])/2-nose) for b in boxes]
        k=int(np.argmax(rank));box=boxes[k]
        if cached: points,scores=np.array([cached['rtmw']['xy']]),np.array([cached['rtmw']['confidence']])
        else: points,scores=pose(im,bboxes=[box.tolist()])
        ym=(y.masks.data[k].numpy()>.5).astype(np.uint8)*255
        if segmentation is None:
            pstart=time.perf_counter()
            try:
                sam=SAM(str(ROOT.parent/'py/modeller/sam2.1_t.pt'))
                sm=sam.predict(im,bboxes=[box.tolist()],device='cpu',verbose=False)[0]
                smask=(sm.masks.data[0].numpy()>.5).astype(np.uint8)*255
                cv2.imwrite(str(gt/'sam-probe.png'),smask)
                seconds=time.perf_counter()-pstart
                segmentation='SAM 2.1 tiny' if seconds<5 else 'YOLO11n-seg fallback'
                probe=dict(seconds=seconds,chosen=segmentation,reason='Use SAM if first CPU frame including load takes <5 s; otherwise bounded-cost YOLO fallback.')
            except Exception as e:
                segmentation='YOLO11n-seg fallback';probe=dict(error=type(e).__name__+': '+str(e),chosen=segmentation)
            write(gt/'segmentation-probe.json',probe)
        if segmentation=='SAM 2.1 tiny':
            if i==0: mask=smask
            else:
                r=sam.predict(im,bboxes=[box.tolist()],device='cpu',verbose=False)[0]
                mask=(r.masks.data[0].numpy()>.5).astype(np.uint8)*255
        else: mask=ym
        if mask.shape!=im.shape[:2]:mask=cv2.resize(mask,(576,1024),interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(str(gt/'masks'/f'{i:04d}.png'),mask)
        row=dict(i=i,shot=f['shot'],actor=f['actor'],box=box.tolist(),box_confidence=float(y.boxes.conf[k]),rtmw=dict(xy=points[0].tolist(),confidence=scores[0].tolist()),mediapipe=f,segmentation=segmentation)
        write(cache,row);rows.append(row)
        if i%30==0: print(f'GT {i+1}/383, {time.perf_counter()-start:.1f} s',flush=True)
    cap.release()
    # Timestamped source-only contact sheets, also suitable for manual blind labels.
    for sid in [f'S{i}' for i in range(1,8)]:
        ids=[r['i'] for r in rows if r['shot']==sid]
        sample=np.linspace(ids[0],ids[-1],8).round().astype(int)
        panels=[]
        for i in sample:
            im=cv2.imread(str(gt/'source'/f'{i:04d}.jpg'))
            im=cv2.resize(im,(288,512));cv2.rectangle(im,(0,0),(288,28),(0,0,0),-1)
            cv2.putText(im,f'{sid} frame {i} / {i/30:.3f}s',(5,19),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
            panels.append(im)
        cv2.imwrite(str(gt/'sheets'/f'{sid}.jpg'),np.vstack([np.hstack(panels[:4]),np.hstack(panels[4:])]))
    write(gt/'raw.json',dict(schema='source-observations/1',width=576,height=1024,fps=30,source_sha256=sha(ROOT.parent/'klipp/d-dialog-notan.mp4'),mediapipe_sha256=sha(ROOT/'data/sparning.json'),rtmw_url=url,rtmw_sha256=sha(onnx),runtime_s=time.perf_counter()-start,frames=rows))
    print('Ground truth complete',flush=True)

if __name__=='__main__':main()
