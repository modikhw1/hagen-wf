"""Avläs använd Kenny-bana; bevara den historiska loggen och uppdatera manifest."""
import json
import sys
from pathlib import Path
import numpy as np
from steg10_filer import ROT, andra

H=ROT/'scen/3d/kontrakt';I=H.parent/'ingest'
sys.path[:0]=[str(H),str(I)]
from kalla_omhasha import uppdatera
from regler import kort_kamerabana

folder=I/'ut/kand-kennysgelato-tagningar/S2'
with np.load(folder/'varld.npz') as v:
    C=v['kam_C'].copy();scale=float(v['k'])
    decision=json.loads(str(v['metriskt_skalbeslut']))
distance=float(np.linalg.norm(np.diff(C,axis=0),axis=1).sum())
def sync(s):
    d=json.loads(s)
    assert 'varld_fore_loggsynk' not in d
    old=d['varld'];d['varld_fore_loggsynk']=old
    d['varld']=dict(old,skala=scale,kamerans_vag_m=round(distance,6),banbeslut=kort_kamerabana(C),skalbeslut=decision,
        ojamnhet_cm=None,loggsynk=dict(status='uppmatt',
        metod='Aktuell kam_C, k och skalbeslut avlästa ur varld.npz. Ingen ny ingest. Tidigare varld-post bevarad; ojämnhetsmåttet är inte ommätt.',
        fil=str(folder/'varld.npz')))
    return json.dumps(d,ensure_ascii=False,indent=1)+'\n'
andra(str((folder/'tider.json').relative_to(ROT)),sync)
changes=[]
for name in ['kalla_jamn.json','kalla_prop.json']:
    path=H/'ut/kenny'/name
    changed,missing=uppdatera(path)
    assert not missing
    changes.append(dict(fil=str(path),andrade=changed))
out=H/'ut/aterupptagning/kenny_kamera.json'
rows=[]
for file in folder.glob('sekvens_*.npz'):
    with np.load(file) as seq:
        valid=np.flatnonzero(seq['inom'])
        rows.append(dict(fil=file.name,inom=[int(valid[0]),int(valid[-1])]))
out.write_text(json.dumps(dict(anvand_bana_m=distance,skalbeslut=decision,personrutor=rows,manifest=changes),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Aktuell använd kamerabana',distance,'m; tidigare logg bevarad.')
