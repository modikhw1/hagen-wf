"""Pinned public Apache MapAnything. Run only via run_bank.py (budget lock)."""
import io,json,time,zipfile,os
from pathlib import Path
import modal

app=modal.App('hagen-rumsbank-mapanything')
vol=modal.Volume.from_name('hagen-rumsbank-mapanything-apache',create_if_missing=True)
SHA='3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9'
WEIGHTS_SHA='00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a'
image=(modal.Image.debian_slim(python_version='3.12')
 .apt_install('git','libgl1','libglib2.0-0')
 .pip_install('torch==2.7.1','torchvision==0.22.1',index_url='https://download.pytorch.org/whl/cu128')
 .run_commands('git clone https://github.com/facebookresearch/map-anything.git /opt/mapanything',f'cd /opt/mapanything && git checkout {SHA}',"pip install -e /opt/mapanything")
 .env({'HF_HUB_DISABLE_IMPLICIT_TOKEN':'1','TORCH_HOME':'/weights/torch','OMP_NUM_THREADS':'4'}))

@app.function(image=image,volumes={'/weights':vol},timeout=1200,memory=16384)
def prepare():
    from huggingface_hub import snapshot_download
    t=time.monotonic()
    p=snapshot_download('facebook/map-anything-apache',revision=WEIGHTS_SHA,local_dir='/weights/model',token=False)
    from mapanything.models import MapAnything
    from mapanything.utils.image import load_images
    # Torch hub code is needed for the architecture even when checkpoint contains all parameters.
    import torch
    torch.hub.help('facebookresearch/dinov2','dinov2_vitg14',trust_repo=True)
    vol.commit()
    return dict(code_sha=SHA,weights_sha=WEIGHTS_SHA,cpu_prepare_s=time.monotonic()-t,files=[x.name for x in Path(p).iterdir()])

@app.function(image=image,gpu='A100-80GB',volumes={'/weights':vol},timeout=int(os.environ.get('RUM_GPU_TIMEOUT','840')),memory=32768,scaledown_window=2,max_containers=1)
def evaluate(jobs):
    started=time.monotonic()
    import numpy as np,torch,cv2
    from mapanything.models import MapAnything
    from mapanything.utils.image import load_images,rgb
    cv2.setNumThreads(2);torch.set_num_threads(4)
    model=MapAnything.from_pretrained('/weights/model',local_files_only=True).cuda().eval()
    torch.cuda.synchronize();load_s=time.monotonic()-started
    for job in jobs:
        dest=Path('/tmp/rumsbank')/job['id'];dest.mkdir(parents=True,exist_ok=True)
        paths=[]
        for i,data in enumerate(job['images']):
            p=dest/f'{i:05d}.jpg';p.write_bytes(data);paths.append(str(p))
        views=load_images(paths)
        torch.cuda.reset_peak_memory_stats();t=time.monotonic()
        with torch.inference_mode():
            preds=model.infer(views,memory_efficient_inference=True,minibatch_size=1,use_amp=True,amp_dtype='bf16',apply_mask=False,mask_edges=False,apply_confidence_mask=False)
        torch.cuda.synchronize();infer_s=time.monotonic()-t
        blob=io.BytesIO()
        with zipfile.ZipFile(blob,'w',zipfile.ZIP_STORED) as z:
            for i,(pred,view) in enumerate(zip(preds,views)):
                arrays={k:pred[k].detach().float().cpu().numpy() for k in ['depth_z','intrinsics','camera_poses','conf','mask'] if k in pred}
                buf=io.BytesIO();np.savez_compressed(buf,**arrays);z.writestr(f'{i:05d}.npz',buf.getvalue())
                im=(rgb(view['img'],'dinov2')[0]*255).astype(np.uint8)
                z.writestr(f'{i:05d}.jpg',cv2.imencode('.jpg',cv2.cvtColor(im,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,95])[1].tobytes())
        info=dict(id=job['id'],candidate='mapanything',code_sha=SHA,weights_sha=WEIGHTS_SHA,metric=True,load_s=load_s,inference_s=infer_s,frames=len(paths),gpu_s_per_frame=infer_s/len(paths),peak_vram_gb=torch.cuda.max_memory_allocated()/1e9,gpu=torch.cuda.get_device_name(),elapsed_s=time.monotonic()-started,output='OpenCV camera-to-world; raw depth in metres; masks disabled')
        print(json.dumps(info),flush=True)
        yield dict(id=job['id'],archive=blob.getvalue(),info=info)
        del preds,views;torch.cuda.empty_cache()
