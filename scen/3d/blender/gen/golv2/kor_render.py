import sys,subprocess,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
phase=sys.argv[1]
assert phase in ('fore','efter')
cmd=[r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','-b','--factory-startup','-t','8','--python-exit-code','1','--python',str(HERE/'render_blender.py'),'--',phase]
with (HERE/phase/'blender.log').open('wb') as f:
    r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
print(phase,'exit',r.returncode,flush=True)
if r.returncode:print((HERE/phase/'blender.log').read_text(encoding='utf-8',errors='replace')[-6500:])
raise SystemExit(r.returncode)
