"""0040: Kimodo-SOMA-RP-v1.1 (vikter NVIDIA Open Model License; kod Apache-2.0) på Modal. Ingen textkodare (gated Llama-3) i avbildningen.

Från projektroten, PYTHONIOENCODING=utf-8:
  scen/.venv/Scripts/python.exe -m modal run forvarld/kropp/kimodo/modal_kimodo.py --inn <ref.npz> --inst <inst.json> --ut <ut.npz>
Avbildningen (Python 3.11, torch 2.5.1 cu121, kimodo-repot på commit e1c219c, MotionCorrection, vikterna) byggs en gång och cachas.
"""
from pathlib import Path
import modal

HIT = Path(__file__).resolve().parent if modal.is_local() else Path('/opt/k')
app = modal.App('hagen-kimodo')
image = (
    modal.Image.debian_slim(python_version='3.11')
    .apt_install('git', 'cmake', 'build-essential', 'curl')
    .pip_install('torch==2.5.1', index_url='https://download.pytorch.org/whl/cu121')
    .add_local_dir(str(HIT / 'repo'), '/opt/kimodo', copy=True, ignore=['.git', 'docs', 'benchmark', 'assets/demo'])
    .run_commands('cd /opt/kimodo && pip install ./MotionCorrection && SKIP_MOTION_CORRECTION_IN_SETUP=1 pip install -e .',
                  "python -c \"from huggingface_hub import snapshot_download; print(snapshot_download('nvidia/Kimodo-SOMA-RP-v1.1'))\"")
    .env({'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1', 'TEXT_ENCODER_MODE': 'local', 'LOCAL_CACHE': 'True'})
    .add_local_file(str(HIT / 'kor_kimodo.py'), '/opt/k/kor_kimodo.py')
)


@app.function(image=image, gpu='L4', timeout=1800, memory=16384)
def kor(inn: bytes, inst: str) -> bytes:
    import subprocess, time
    Path('/tmp/in.npz').write_bytes(inn); Path('/tmp/inst.json').write_text(inst); t0 = time.time()
    r = subprocess.run(['python', '/opt/k/kor_kimodo.py', '/tmp/in.npz', '/tmp/ut.npz', '/tmp/inst.json'], cwd='/opt/kimodo', capture_output=True, text=True)
    print(r.stdout[-6000:]); print(r.stderr[-8000:]); print('CONTAINER_S', round(time.time() - t0, 1))
    if r.returncode: raise RuntimeError('kor_kimodo misslyckades')
    return Path('/tmp/ut.npz').read_bytes()


@app.local_entrypoint()
def main(inn: str, inst: str, ut: str):
    import time
    t0 = time.time(); b = kor.remote(Path(inn).read_bytes(), Path(inst).read_text(encoding='utf-8')); Path(ut).write_bytes(b)
    print('LOKALT_S', round(time.time() - t0, 1), '->', ut)
