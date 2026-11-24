"""FORSKNING (0039): ProtoMotions v3.0 + MaskedMimic SMPL (AMASS-tränad, icke-kommersiell) + IsaacGym Preview 4 på Modal.

Avbildningen byggs en gång och cachas av Modal (CUDA 12.1, Python 3.8, IsaacGym, ProtoMotions v3.0 med kontrollpunkten).
Kör från projektroten, PYTHONIOENCODING=utf-8:
  scen/.venv/Scripts/python.exe -m modal run forvarld/kropp/forskning/mm/modal_mm.py --inn <ref.npz> --villkor <villkor.json> --ut <ut.npz>
En container per jobb. Inget går in i kedjan utan flaggan licens: forskning.
"""
from pathlib import Path
import modal

HIT = Path(__file__).resolve().parent if modal.is_local() else Path('/opt/mm')
PM = HIT.parent / 'ProtoMotions' if modal.is_local() else Path('/opt/protomotions')
app = modal.App('hagen-maskedmimic-forskning')
image = (
    modal.Image.from_registry('nvidia/cuda:12.1.0-devel-ubuntu20.04', add_python='3.11')   # 3.11 för Modal, 3.8 för IsaacGym
    .env({'DEBIAN_FRONTEND': 'noninteractive'})
    .apt_install('git', 'wget', 'libglu1-mesa-dev', 'libgl1-mesa-dev', 'libosmesa6-dev', 'patchelf', 'python3.8', 'python3.8-dev', 'python3-pip',
                 'build-essential', 'libvulkan1')
    .run_commands('python3.8 -m pip install --upgrade "pip<25" setuptools wheel',
                  'cd /opt && wget -q https://developer.nvidia.com/isaac-gym-preview-4 -O ig.tgz && tar -xzf ig.tgz && rm ig.tgz',
                  'cd /opt/isaacgym/python && python3.8 -m pip install -e .',
                  'python3.8 -m pip install "torch==2.4.1" --index-url https://download.pytorch.org/whl/cu121')
    .add_local_file(str(PM / 'requirements_isaacgym.txt'), '/tmp/req.txt', copy=True)
    .run_commands("sed -i '/^torch/d' /tmp/req.txt", 'python3.8 -m pip uninstall -y onnx || true', 'python3.8 -m pip install --no-cache-dir -r /tmp/req.txt')
    .add_local_dir(str(PM), '/opt/protomotions', copy=True, ignore=['.git', '**/*.gif', '**/*.mp4', 'docs', 'examples/data'])
    .run_commands('cd /opt/protomotions && python3.8 -m pip install -e .')
    .env({'IG_LD': '/usr/lib/x86_64-linux-gnu:/usr/local/lib/python3.8/dist-packages/torch/lib', 'PYTHONPATH': '/opt/protomotions'})
    .add_local_file(str(HIT / 'kor_mm.py'), '/opt/mm/kor_mm.py')
)


@app.function(image=image, gpu='L4', timeout=1800, memory=16384)
def kor(inn: bytes, villkor: str) -> bytes:
    import subprocess, time, os
    Path('/tmp/in.npz').write_bytes(inn); Path('/tmp/v.json').write_text(villkor); t0 = time.time()
    env = {k: v for k, v in os.environ.items() if not k.startswith('PYTHON')}
    env.update(PYTHONPATH='/opt/protomotions:/opt/isaacgym/python', LD_LIBRARY_PATH=os.environ['IG_LD'] + ':' + os.environ.get('LD_LIBRARY_PATH', ''))
    d = subprocess.run(['python3.8', '-c', 'import sys; print(sys.version, sys.path[:6]); import isaacgym; print("isaacgym ok")'], capture_output=True, text=True, env=env)
    print('DIAG', d.stdout[-800:], d.stderr[-1500:])
    r = subprocess.run(['/usr/bin/python3.8', '/opt/mm/kor_mm.py', '/tmp/in.npz', '/tmp/ut.npz', '/tmp/v.json'], cwd='/opt/protomotions', capture_output=True, text=True, env=env)
    print(r.stdout[-6000:]); print(r.stderr[-8000:]); print('CONTAINER_S', round(time.time() - t0, 1))
    if r.returncode: raise RuntimeError('kor_mm misslyckades')
    return Path('/tmp/ut.npz').read_bytes()


@app.local_entrypoint()
def main(inn: str, villkor: str, ut: str):
    import time
    t0 = time.time(); b = kor.remote(Path(inn).read_bytes(), Path(villkor).read_text(encoding='utf-8')); Path(ut).write_bytes(b)
    print('LOKALT_S', round(time.time() - t0, 1), '->', ut)
