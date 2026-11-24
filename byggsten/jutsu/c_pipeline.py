"""Canonical C delivery: build -> GLB gate -> round trip -> render -> validated mux."""
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
BLENDER=Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
SCENE=HERE/'ut/c-sketch-tre/preview/scene.blend'


def run(*command):
    subprocess.run([str(value) for value in command],check=True)


if __name__=='__main__':
    run(sys.executable,HERE/'c_ingest.py',*(['--rebuild-sequences'] if '--rebuild-sequences' in sys.argv else []))
    run(sys.executable,HERE/'c_ops.py')
    run(BLENDER,'-b','--factory-startup','--python-exit-code','1','--python',HERE/'c_preview.py')
    run(BLENDER,'-b',SCENE,'--python-exit-code','1','--python',HERE/'c_export_verify.py')
    run(BLENDER,'-b',SCENE,'--python-exit-code','1','--python',HERE/'c_render.py')
    run(sys.executable,HERE/'c_mux.py')
