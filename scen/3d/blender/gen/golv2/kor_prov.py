import sys,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.path.insert(0,str(HERE));from prova import save,log
results=[]
modules=['test_flode','test_rumsmall','test_kroppmatt']
for i,module in enumerate(modules):
    start=time.perf_counter()
    r=subprocess.run([sys.executable,'-m','unittest',module],cwd=P/'kontrakt',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    text=r.stdout.decode('utf-8',errors='replace').replace('\r\n','\n')
    (HERE/f'{module}.log').write_text(text,encoding='utf-8',newline='\n')
    results.append(dict(modul=module,exit=r.returncode,sekunder=round(time.perf_counter()-start,3)));save(HERE/'testresultat.json',results)
    print(module,results[-1],text[-130:],flush=True)
    nxt=f"& 'C:\\Users\\praiseworthy\\Desktop\\hagen-wf\\scen\\.venv\\Scripts\\python.exe' -m unittest {modules[i+1]}" if i+1<len(modules) else 'scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/slutrapport.py'
    log(f'Seriell provkörning från kontrakt/: {module}, exit {r.returncode}. UTF-8/LF-logg: blender/gen/golv2/{module}.log. Inga produktionsändringar har behövts; dessa är regressionskontroller för läsning/golv/kropp.',nxt+(' # kör från scen/3d/kontrakt' if i+1<len(modules) else ''))
    if r.returncode:raise SystemExit(r.returncode)
