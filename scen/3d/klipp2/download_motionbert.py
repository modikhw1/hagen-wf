"""Download only the Apache-2.0 pose lifter, never SMPL or mesh modules."""
from pathlib import Path
import requests,hashlib,json,time
HERE=Path(__file__).resolve().parent
BASE='https://huggingface.co/walterzhu/MotionBERT/resolve/main/'
FILES=['LICENSE','lib/model/DSTformer.py','lib/model/drop.py','configs/pose3d/MB_ft_h36m.yaml','checkpoint/pose3d/FT_MB_release_MB_ft_h36m/best_epoch.bin']
start=time.perf_counter();manifest=[]
for name in FILES:
    p=HERE/'deps/MotionBERT'/name;p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():
        with requests.get(BASE+name,stream=True,timeout=180) as r:
            r.raise_for_status()
            with p.open('wb') as f:
                for chunk in r.iter_content(1024*1024):f.write(chunk)
    manifest.append(dict(path=str(p.relative_to(HERE)),url=BASE+name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
    print(name,p.stat().st_size,flush=True)
(HERE/'motionbert-download.json').write_text(json.dumps(dict(files=manifest,seconds=time.perf_counter()-start),indent=2))
