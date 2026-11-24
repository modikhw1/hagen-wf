"""Modultider och tre verkliga notan-edits, en process i taget."""
import importlib.abc, importlib.util, json, os, subprocess, sys, time, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];H=ROOT/'scen/3d/kontrakt';O=H/'ut/steg10c';os.chdir(ROOT)
sys.path[:0]=[str(H),str(H.parent/'ingest')]
mode=sys.argv[1]
if mode=='child':
 phase,kind=sys.argv[2:4]
 if phase=='fore':
  files=json.loads((O/'baslinje.json').read_text(encoding='utf-8'))
  class Snapshot(importlib.abc.MetaPathFinder,importlib.abc.Loader):
   def find_spec(self,fullname,path=None,target=None):
    from importlib.machinery import PathFinder
    spec=PathFinder.find_spec(fullname,path)
    if spec and spec.origin in files:
     return importlib.util.spec_from_file_location(fullname,spec.origin,loader=self)
   def create_module(self,spec):return None
   def exec_module(self,module):exec(compile(Path(files[module.__file__]).read_bytes(),module.__file__,'exec'),module.__dict__)
  sys.meta_path.insert(0,Snapshot())
 if phase.startswith('snabb_'):
  import datacache
  datacache.CACHE=O/('cache_snabb_'+kind)
 if kind in ('trim','text','prop'):
  from kompilera import kompilera
  from gemensamt import skriv
  t=time.perf_counter();p=kompilera(H/'ut/notan/kalla_handelser.json',O/(kind+'_regi.json'),**({'snabb':True} if phase.startswith('snabb') else {}));elapsed=time.perf_counter()-t
  assert not p['ej_tillampat'],p['ej_tillampat']
  skriv(O/(phase+'_'+kind+'_plan.json'),p)
  result=dict(fas=phase,slag=kind,sek=elapsed)
 else:
  class LiveResult(unittest.TextTestResult):
   def addError(self,test,err):
    super().addError(test,err);self.stream.writeln(self.errors[-1][1]);self.stream.flush()
   def addFailure(self,test,err):
    super().addFailure(test,err);self.stream.writeln(self.failures[-1][1]);self.stream.flush()
  t=time.perf_counter();suite=unittest.defaultTestLoader.loadTestsFromName(kind);r=unittest.TextTestRunner(verbosity=1,resultclass=LiveResult).run(suite)
  result=dict(fas=phase,modul=kind,antal=r.testsRun,fel=len(r.failures),error=len(r.errors),hoppade=len(r.skipped),sek=time.perf_counter()-t)
 (O/(phase+'_'+kind.replace('.','_')+'_tid.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result,flush=True)
 if 'fel' in result:sys.exit(bool(result['fel']+result['error']))
else:
 phase=mode
 kinds=sys.argv[2:] or ['trim','text','prop','test_flode','test_rumsmall','test_regler','test_text_disk','test_kroppmatt','test_props','test_handelser','test_snabb','semantik.test_semantik','bro.test_bro','test_rum']
 for kind in kinds:
  log=O/(phase+'_'+kind.replace('.','_')+'.log')
  print('START',phase,kind,flush=True)
  with log.open('w',encoding='utf-8') as f:r=subprocess.run([sys.executable,__file__,'child',phase,kind],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
  print('KLAR',kind,r.returncode,flush=True)
