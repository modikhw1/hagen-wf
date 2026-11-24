import sys,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
if '--blender' not in sys.argv:
    cmd=[r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','-b','--factory-startup','-t','8','--python-exit-code','1','--python',str(Path(__file__).resolve()),'--','--blender']
    with (HERE/'extra_blender.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    print('extra Blender exit',r.returncode)
    if r.returncode:print((HERE/'extra_blender.log').read_text(encoding='utf-8',errors='replace')[-4000:])
    raise SystemExit(r.returncode)
import bpy,numpy as np,importlib.util
sys.dont_write_bytecode=True
sys.path[:0]=[str(P/'ingest'),str(P/'kontrakt'),str(HERE)]
from prova import save,log
from metrisk import las
spec=importlib.util.spec_from_file_location('mhr_blender_prov',P/'blender/mhr_blender.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
seq=P/'ingest/ut/notan-tagningar/S1/sekvens_1.npz'
mod.importera(str(P/'klipp2/sam3db/mhr/assets/lod3.fbx'),str(seq),namn='direkt_lasarprov',bredd=576,hojd=1024)
state=bpy.app.driver_namespace['mhr'];expected=las(seq);raw=dict(np.load(seq))
result={k:dict(exakt_metrisk=bool(np.array_equal(state['S'][k],expected[k])),max_mot_ra=float(np.abs(state['S'][k]-raw[k]).max())) for k in ['cam_t','pose']}
mod.varld(str(seq.parent/'varld.npz'))
for f in [2,36,70]:mod.nyckla_varld(f,f+1)
save(HERE/'mhr_blender_lasarprov.json',result)
# Separat läsning av den sparade ordinarie scenen: objektgeometri och faktisk kamera.
bpy.ops.wm.open_mainfile(filepath=str(HERE/'efter/scen.blend'));sc=bpy.context.scene
plan=json.loads((HERE/'efter/plan.json').read_text(encoding='utf-8'))
objects=[]
for item in plan['objekt']:
    o=bpy.data.objects.get(item['namn'])
    if o:
        objects.append(dict(id=item['id'],namn=o.name,pos_m=list(o.location),matt_m=list(o.dimensions),deltyp=item.get('deltyp'),synlig_ut=item.get('synlig_ut')))
save(HERE/'blender_objekt.json',objects)
log('Separat Blenderprov av just blender/mhr_blender.py: importera() läser notan S1 genom metrisk, cam_t/pose exakt lika, tre världsposer nycklade. Ordinarie planväg använder ingest/mhr_rig.py (inte denna äldre direktimportör). Faktisk möbelgeometri exporterad ur sparad scen.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/analysera.py")
print(result)
