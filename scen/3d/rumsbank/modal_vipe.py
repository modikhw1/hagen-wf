"""ViPE camera + MoGe2 priors; reuses ingest person masks, no NC priors.

Dense files are independent MoGe2 at recovered K, NOT ViPE adaptive fusion.
The official adaptive processor constructs PriorDA with DAV2-Base NC weights;
that complete dense pipeline is commercially blocked and not downloaded here.
"""
import io,json,time,zipfile,os
from pathlib import Path
import modal

app=modal.App('hagen-rumsbank-vipe-moge2')
vol=modal.Volume.from_name('hagen-rumsbank-vipe-public',create_if_missing=True)
SHA='ead2e008bc055310121736a49ff306bba50d10dc'
USE_EXISTING_MASKS=True
image=(modal.Image.from_registry('nvidia/cuda:12.8.1-devel-ubuntu22.04',add_python='3.11')
 .apt_install('git','build-essential','libeigen3-dev','libgl1','libglib2.0-0','zlib1g-dev')
 .pip_install('torch==2.7.1','torchvision==0.22.1',index_url='https://download.pytorch.org/whl/cu128')
 .pip_install('setuptools>=77','wheel','ninja')
 .env({'TORCH_CUDA_ARCH_LIST':'8.0','MAX_JOBS':'4','HF_HUB_DISABLE_IMPLICIT_TOKEN':'1','TORCH_HOME':'/weights/torch','OMP_NUM_THREADS':'4'})
 .apt_install('clang')
 .run_commands('git clone https://github.com/nv-tlabs/vipe.git /opt/vipe',f'cd /opt/vipe && git checkout {SHA}',
    "python -c \"from pathlib import Path;p=Path('/opt/vipe/pyproject.toml');p.write_text(p.read_text().replace('gtsam-develop==4.3a2.dev202609030306','gtsam-develop==4.3.2.dev202611100512'))\"",
    "pip install --no-build-isolation /opt/vipe"))

@app.function(image=image,volumes={'/weights':vol},timeout=1200,memory=16384)
def prepare():
    import urllib.request,hashlib,gdown
    from huggingface_hub import hf_hub_download
    from vipe.priors.geocalib import GeoCalib
    import vipe_ext
    started=time.monotonic();files=[]
    # Public releases only, never consult a token or submit a licence form.
    jobs=[('https://github.com/cvg/GeoCalib/releases/download/v1.0/geocalib-pinhole.tar','/weights/torch/hub/geocalib/pinhole.tar')]
    for url,name in jobs:
        p=Path(name);p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():urllib.request.urlretrieve(url,p)
        files.append(dict(path=name,source=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    p=Path('/weights/torch/hub/droid_slam/droid.pth');p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():gdown.download(id='1PpqVt1H4maBa_GbPJp4NwxRsd9jk-elh',output=str(p))
    files.append(dict(path=str(p),source='DROID-SLAM release linked by ViPE',sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    from huggingface_hub import HfApi
    info=HfApi(token=False).model_info('Ruicheng/moge-2-vitl',revision='39c4d5e957afe587e04eec59dc2bcc3be5ecd968')
    p=hf_hub_download('Ruicheng/moge-2-vitl','model.pt',revision=info.sha,local_dir='/weights/moge2',token=False)
    files.append(dict(path=p,source='Ruicheng/moge-2-vitl',revision=info.sha))
    vol.commit()
    return dict(code_sha=SHA,cpu_prepare_s=time.monotonic()-started,files=files)

@app.function(image=image,gpu='A100-80GB',volumes={'/weights':vol},timeout=int(os.environ.get('RUM_GPU_TIMEOUT','840')),memory=32768,scaledown_window=2,max_containers=1)
def evaluate(jobs):
    started=time.monotonic()
    import os,traceback
    os.environ['VIPE_MOGE2_CHECKPOINT']='/weights/moge2/model.pt'
    import cv2,numpy as np,torch
    from omegaconf import OmegaConf
    from vipe.streams.frame_dir_stream import FrameDirStream
    from vipe.streams.base import StreamProcessor,ProcessedVideoStream,FrameAttribute
    from vipe.pipeline.processors import GeoCalibIntrinsicsProcessor
    from vipe.slam.system import SLAMSystem
    from vipe.utils.cameras import CameraType
    from vipe.utils.model_cache import ModelCache
    from vipe.priors.depth import DepthEstimationInput
    from vipe.priors.depth.moge import MogeModel
    cv2.setNumThreads(2);torch.set_num_threads(4)
    cache=ModelCache()
    class Masks(StreamProcessor):
        def __init__(self,masks):super().__init__();self.masks=masks
        def update_attributes(self,attrs):return attrs|{FrameAttribute.INSTANCE,FrameAttribute.MASK}
        def __call__(self,i,frame):
            mk=cv2.imdecode(np.frombuffer(self.masks[i],np.uint8),0);h,w=frame.size();mk=cv2.resize(mk,(w,h),interpolation=cv2.INTER_NEAREST)>0
            mk=cv2.dilate(mk.astype(np.uint8),np.ones((7,7),np.uint8))>0
            frame.instance=torch.as_tensor(mk.astype(np.uint8),device='cuda');frame.instance_phrases={1:'person'};frame.mask=~frame.instance.bool();return frame
    for job in jobs:
        t=time.monotonic();torch.cuda.reset_peak_memory_stats();blob=io.BytesIO()
        info=dict(id=job['id'],candidate='vipe',code_sha=SHA,metric=True,indices=job['indices'],frames=len(job['images']),masks_available=job['masks_available'],geometry_method='Independent MoGe2 depth at recovered ViPE K; not official adaptive PriorDA/VDA dense fusion (NC dependencies)')
        try:
            dest=Path('/tmp/rumsbank')/job['id'];dest.mkdir(parents=True,exist_ok=True)
            for i,data in enumerate(job['images']):(dest/f'{i:05d}.jpg').write_bytes(data)
            stream=FrameDirStream(dest,seek_range=range(0,-1,1));stream._fps=job['fps']
            calibration=GeoCalibIntrinsicsProcessor(stream,camera_type=CameraType.PINHOLE,model_cache=cache)
            processed=ProcessedVideoStream(stream,[calibration,Masks(job['masks'])]).cache('inputs',online=True,async_prefetch=False)
            cfg=OmegaConf.load('/opt/vipe/configs/slam/default.yaml');cfg.keyframe_depth='moge2-l';cfg.optimize_intrinsics=True
            slam=SLAMSystem(torch.device('cuda'),cfg,model_cache=cache)
            output=slam.run([processed],camera_type=CameraType.PINHOLE)
            poses=output.get_view_trajectory(0).matrix().detach().cpu().numpy();intr=output.intrinsics[0].detach().cpu().numpy();K=np.array([[intr[0],0,intr[2]],[0,intr[1],intr[3]],[0,0,1]],np.float32)
            model=cache.get('depth/moge2-l',lambda:MogeModel(version=2,variant='l'))
            with zipfile.ZipFile(blob,'w',zipfile.ZIP_STORED) as z:
                for i,data in enumerate(job['images']):
                    rgb=cv2.cvtColor(cv2.imdecode(np.frombuffer(data,np.uint8),1),cv2.COLOR_BGR2RGB)
                    from vipe.streams.base import VideoFrame
                    f=VideoFrame(raw_frame_idx=i,rgb=torch.from_numpy(rgb.copy()).cuda().float()/255,intrinsics=torch.from_numpy(intr).cuda(),camera_type=CameraType.PINHOLE)
                    d=model.estimate(DepthEstimationInput(rgb=f.rgb,intrinsics=f.intrinsics,camera_type=f.camera_type)).metric_depth.detach().float().cpu().numpy()
                    buf=io.BytesIO();np.savez_compressed(buf,depth_z=d,intrinsics=K,camera_poses=poses[i],conf=np.ones_like(d));z.writestr(f'{i:05d}.npz',buf.getvalue());z.writestr(f'{i:05d}.jpg',data)
            info.update(status='ran',ba_residual=float(output.ba_residual))
        except Exception:
            error=traceback.format_exc();print(error,flush=True);info.update(status='did_not_run',error=error)
            blob=io.BytesIO()
            with zipfile.ZipFile(blob,'w') as z:z.writestr('error.txt',error)
        torch.cuda.synchronize();elapsed=time.monotonic()-t
        info.update(inference_s=elapsed,gpu_s_per_frame=elapsed/len(job['images']),peak_vram_gb=torch.cuda.max_memory_allocated()/1e9,gpu=torch.cuda.get_device_name(),elapsed_s=time.monotonic()-started)
        print(json.dumps(info),flush=True);yield dict(id=job['id'],archive=blob.getvalue(),info=info)
        torch.cuda.empty_cache()
