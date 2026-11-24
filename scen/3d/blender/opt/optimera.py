"""blender -b --factory-startup --python .../opt/optimera.py [-- --reuse-fit]

CPU torch/scipy worker uses the provided Python 3.12 environment. Blender's own
Python is a different ABI; never load those native wheels into Blender.
"""
import sys, subprocess, os, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    if '--reuse-fit' not in sys.argv:
        subprocess.run([str(HERE.parents[2]/'.venv/Scripts/python.exe'),'-u',str(HERE/'fit_cpu.py')],check=True)
        subprocess.run([str(HERE.parents[2]/'.venv/Scripts/python.exe'),'-u',str(HERE/'preserve_timing.py')],check=True)
        subprocess.run([str(HERE.parents[2]/'.venv/Scripts/python.exe'),'-u',str(HERE/'refine_ik.py')],check=True)
    sys.path.insert(0,str(HERE.parent))
    from bygg_scen import bygg
    bygg(bake_path=HERE/'bake-opt.json',arbetsut=HERE,spara=HERE/'scen-opt.blend')
if __name__=='__main__':
    try:main()
    except Exception:traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
