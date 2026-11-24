"""Public Apache DA3-Base plus Metric-Large. This is NOT the NC Nested model."""
import io,json,time,zipfile,os
from pathlib import Path
import modal

app=modal.App('hagen-rumsbank-da3-apache')
vol=modal.Volume.from_name('hagen-rumsbank-da3-apache',create_if_missing=True)
SHA='3d835ec1a5802d64a8b8b15f817a1ab54809bfe4'
BASE_SHA='f4a6c9b3c95e41c82048423d3493a81ec3fa810e'
METRIC_SHA='4010e39f3634a45bc60553321fb49fb760bd594e'
MAX_FRAMES=24
image=(modal.Image.debian_slim(python_version='3.11')
 .apt_install('git','libgl1','libglib2.0-0')
 .pip_install('torch==2.7.1','torchvision==0.22.1',index_url='https://download.pytorch.org/whl/cu128')
 .pip_install('xformers==0.0.31.post1','addict')
 .run_commands('git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /opt/da3',f'cd /opt/da3 && git checkout {SHA}','pip install -e /opt/da3')
 .env({'HF_HUB_DISABLE_IMPLICIT_TOKEN':'1','OMP_NUM_THREADS':'4'}))

@app.function(image=image,volumes={'/weights':vol},timeout=1200,memory=16384)
def prepare():
    from huggingface_hub import snapshot_download
    started=time.monotonic();files=[]
    for name,rev,folder in [('DA3-BASE',BASE_SHA,'base'),('DA3METRIC-LARGE',METRIC_SHA,'metric')]:
        p=snapshot_download('depth-anything/'+name,revision=rev,local_dir='/weights/'+folder,token=False)
        files.extend([folder+'/'+x.name for x in Path(p).iterdir()])
        vol.commit()
    from depth_anything_3.api import DepthAnything3
    return dict(code_sha=SHA,base_sha=BASE_SHA,metric_sha=METRIC_SHA,cpu_prepare_s=time.monotonic()-started,files=files)

@app.function(image=image,gpu='A100-80GB',volumes={'/weights':vol},timeout=int(os.environ.get('RUM_GPU_TIMEOUT','840')),memory=32768,scaledown_window=2,max_containers=1)
def evaluate(jobs):
    started=time.monotonic()
    import numpy as np,torch,cv2
    from depth_anything_3.api import DepthAnything3
    torch.set_num_threads(4);cv2.setNumThreads(2)
    base=DepthAnything3.from_pretrained('/weights/base',local_files_only=True).cuda().eval()
    metric=DepthAnything3.from_pretrained('/weights/metric',local_files_only=True).cuda().eval()
    torch.cuda.synchronize();load_s=time.monotonic()-started
    for job in jobs:
        dest=Path('/tmp/rumsbank')/job['id'];dest.mkdir(parents=True,exist_ok=True);paths=[]
        for i,data in enumerate(job['images']):
            p=dest/f'{i:05d}.jpg';p.write_bytes(data);paths.append(str(p))
        torch.cuda.reset_peak_memory_stats();t=time.monotonic()
        pred=base.inference(paths,process_res=504)
        metric_depth=[]
        for path in paths:
            mp=metric.inference([path],process_res=504)
            metric_depth.append(mp.depth[0].copy())
        metric_canonical=np.stack(metric_depth)
        # Official canonical-to-metre conversion. One common scene scale, never per-frame camera scale.
        f=(pred.intrinsics[:,0,0]+pred.intrinsics[:,1,1])/2
        metric_m=metric_canonical*f[:,None,None]/300.
        good=np.isfinite(pred.depth)&(pred.depth>.001)&np.isfinite(metric_m)&(metric_m>.05)&(metric_m<50)
        if pred.conf is not None:good &= pred.conf>np.median(pred.conf)
        ratio=metric_m[good]/pred.depth[good]
        scale=float(np.median(ratio))
        torch.cuda.synchronize();infer_s=time.monotonic()-t
        blob=io.BytesIO()
        with zipfile.ZipFile(blob,'w',zipfile.ZIP_STORED) as z:
            for i in range(len(paths)):
                E=np.eye(4);E[:3,:]=pred.extrinsics[i][:3,:];E[:3,3]*=scale
                arrays=dict(depth_z=pred.depth[i]*scale,intrinsics=pred.intrinsics[i],camera_poses=np.linalg.inv(E),base_depth=pred.depth[i],metric_canonical_depth=metric_canonical[i],metric_depth_m=metric_m[i],conf=pred.conf[i] if pred.conf is not None else np.ones_like(pred.depth[i]))
                buf=io.BytesIO();np.savez_compressed(buf,**arrays);z.writestr(f'{i:05d}.npz',buf.getvalue())
                im=pred.processed_images[i]
                z.writestr(f'{i:05d}.jpg',cv2.imencode('.jpg',cv2.cvtColor(im,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,95])[1].tobytes())
        info=dict(id=job['id'],candidate='da3',code_sha=SHA,base_sha=BASE_SHA,metric_sha=METRIC_SHA,metric=True,scale=scale,scale_method='median Metric-Large canonical*f/300 divided by Base depth, high-confidence pixels, single scale for cameras and geometry',indices=job['indices'],load_s=load_s,inference_s=infer_s,frames=len(paths),gpu_s_per_frame=infer_s/len(paths),peak_vram_gb=torch.cuda.max_memory_allocated()/1e9,gpu=torch.cuda.get_device_name(),elapsed_s=time.monotonic()-started)
        print(json.dumps(info),flush=True)
        yield dict(id=job['id'],archive=blob.getvalue(),info=info)
        del pred,mp;torch.cuda.empty_cache()
