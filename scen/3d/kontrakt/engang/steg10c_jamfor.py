"""Exakt jämförelse av upplösta planer och samlad mätredovisning för steg 10c."""
import hashlib
import json
from pathlib import Path
from steg10c_filer import ROT, andra
H=ROT/'scen/3d/kontrakt';O=H/'ut/steg10c'
WARNING='Bildtrohet överskrider egna diagnostiska trösklar. Se kvalitet.bildtrohet; render kräver uttryckligt granskningsläge.'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')).hexdigest()
def built(p):
 d={k:v for k,v in p.items() if k!='kvalitet'}
 d['varningar']=[v for v in d['varningar'] if v!=WARNING]
 return d
proof=[]
for kind in ('trim','text','prop'):
 before=load(O/('fore_'+kind+'_plan.json'));base=digest(built(before))
 for phase in ('snabb_kall','snabb_varm1','snabb_varm2','full_kall','full_varm'):
  p=load(O/(phase+'_'+kind+'_plan.json'))
  decisions={k:digest(before['kvalitet'].get(k))==digest(p['kvalitet'].get(k)) for k in ('hojdpassning','kamerakalibrering','golv_skala','skymning','props')}
  result=dict(edit=kind,fas=phase,bygg_sha256=digest(built(p)),baslinje_sha256=base,identisk=base==digest(built(p)),beslut=decisions)
  proof.append(result)
  assert result['identisk'] and all(decisions.values()),result
# Full diagnostik läser samma kroppsmått i nya processer.
for kind in ('trim','text','prop'):
 a=load(O/('full_kall_'+kind+'_plan.json'));b=load(O/('full_varm_'+kind+'_plan.json'))
 assert digest(a['kvalitet']['kropp'])==digest(b['kvalitet']['kropp']),kind
proofpath=O/'planlikhet.json'
if proofpath.exists():andra(str(proofpath.relative_to(ROT)),lambda s:json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
else:proofpath.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(len(proof),'exakta planjämförelser OK; kroppsmått identiska över processgräns')
