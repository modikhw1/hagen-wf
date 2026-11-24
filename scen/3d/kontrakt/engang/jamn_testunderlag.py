"""Frys stödprovens gamla pose; använd nya hashlåsta kopior efter omkörningen."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from prop_filer import andra,ROT

H=ROT/'scen/3d/kontrakt';sys.path.insert(0,str(H))
from kalla_omhasha import main as omhasha
from trohet import gravitation,F

target=H/'exempel/notan/kalla_jamn.json'
if not target.exists():print('Nya fixture-hashar:',omhasha(H/'exempel/notan/kalla.json',target))
for rel in ['test_flode.py','test_rumsmall.py','test_text_disk.py','bro/test_bro.py']:
    andra('scen/3d/kontrakt/'+rel,lambda s:s.replace('exempel/notan/kalla.json','exempel/notan/kalla_jamn.json'))
andra('scen/3d/kontrakt/test_text_disk.py',lambda s:s.replace('ut/b/kalla.json','ut/b/kalla_jamn.json'))

folder=ROT/'scen/3d/ingest/ut/notan-tagningar/S1'
S=np.load(folder/'fore_jamn/sekvens_1.npz');V=np.load(folder/'fore_jamn/varld.npz')
pl=json.loads((folder.parent/'plats/plats.json').read_text(encoding='utf-8'));M=np.array(pl['tagningar'][0]['till_plats']['matris']);G=gravitation(V)
Q=M[:3,:3]@G@V['kam_R'][30]@F;T=M[:3,:3]@G@(V['kam_C'][30]+V['kam_R'][30]@S['cam_t'][30])+M[:3,3]
anchor=next(x for x in pl['rumsmall']['ankare'] if x['id']=='stol_A')
data=H/'testdata';data.mkdir(exist_ok=True);file=data/'stod_s1_fore_jamn.npz'
if not file.exists():np.savez_compressed(file,pose=S['pose'][30],Q=Q,T=T)
meta=dict(ankare=anchor,ursprung=dict(typ='uppmatt',metod='Fryst befintlig provpose, notan S1 ruta 30 före jämn-passet. De syntetiska korta benen ska hänga och knäna ligga över golvet. Nuvarande ingest har annan golv/rotplacering och är inte samma provfall.',filer=[str(folder/'fore_jamn/sekvens_1.npz'),str(folder/'fore_jamn/varld.npz')],sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
mf=data/'stod_s1_fore_jamn.json'
if not mf.exists():mf.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fixture(s):
    a=s.index('        s=np.load(',s.index('    def kropp(self):'));b=s.index('\n    def test_sittstod',a)
    return s[:a]+'''        # Stabilt provfall från före ingest-omkörningen, inte en rörlig indatafil.
        s=np.load(HIT/'testdata/stod_s1_fore_jamn.npz')
        a=ladda(HIT/'testdata/stod_s1_fore_jamn.json')['ankare']
        return s['pose'].copy(),s['Q'].copy(),s['T'].copy(),a
'''+s[b:]
andra('scen/3d/kontrakt/test_rumsmall.py',fixture)
def plats(s):
    # Behåll bytejämförelsen mot den historiska platsen och pröva dessutom
    # determinism med dagens indata, utan att byta den frysta filmens plats.
    a=s.index('    def test_platssteget_ar_deterministiskt(self):');b=s.index('    def test_planen_har_ett_rum',a)
    block=s[a:b].replace("str(INGEST/'plats.py')","str(HIT/'test_plats_snapshot.py')")
    block+='''    def test_platssteget_nya_matningar_ar_deterministiskt(self):
        import subprocess
        before=PLATS_N.read_bytes()
        for n in 'ab':
            subprocess.run([sys.executable,'-I',str(INGEST/'plats.py'),str(INGEST_N),'--ut',str(self.ut/n),'--hand',str(INGEST_N/'plats/hand.json'),'--scen3d',str(HIT.parent/'scen3d.json')],check=True,capture_output=True)
        for f in ('plats.json','plats_matt.json'): self.assertEqual((self.ut/'a'/f).read_bytes(),(self.ut/'b'/f).read_bytes(),f)
        self.assertEqual(PLATS_N.read_bytes(),before)

'''
    return s[:a]+block+s[b:]
andra('scen/3d/kontrakt/test_flode.py',plats)
print('Historiska provfall frysta; ursprungliga kalla.json och plats.json är oförändrade.')
