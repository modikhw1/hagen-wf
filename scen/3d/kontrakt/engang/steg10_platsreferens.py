"""Återställ en fullständig platsregression med arkivets oförändrade solver.

Den historiska filmplatsen har manuella eftersteg och är inte en automatisk
solverreferens. Referensen nedan kommer från kod i backup8, med gamla
fore_jamn-indata, före nya testassertioner. Ingen tolerans ändras.
"""
import hashlib
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch
import numpy as np
from steg10c_filer import ROT, andra
from steg10_koppla import ersatt

H=ROT/'scen/3d/kontrakt';I=H.parent/'ingest';O=H/'ut/aterupptagning/plats_arkiv'
archive=Path(r'C:\Users\PRAISE~1\AppData\Local\Temp\claude\242ae36db01b5008\e8980010-bc41-44a9-af68-eb956b7a5694\scratchpad\steg10_resume_baseline/ingest/plats.py')
assert archive.read_bytes()==(I/'plats.py').read_bytes(), 'Solvern har ändrats; utred innan en referens skapas.'
reference=H/'testdata/plats_automatisk_fore_jamn.json'
if reference.exists():raise FileExistsError(reference)
O.mkdir(exist_ok=True)
read=Path.read_text;load=np.load;used={}
def historical(p):
    p=Path(p);backup=p.parent/'fore_jamn'/p.name
    p=backup if backup.exists() else p
    if p.is_file():used[str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
    return p
def np_load(p,*a,**kw):return load(historical(p),*a,**kw)
def text(p,*a,**kw):return read(historical(p),*a,**kw)
sys.path[:0]=[str(I),str(H)]
sys.argv=[str(I/'plats.py'),str(I/'ut/notan-tagningar'),'--ut',str(O),'--hand',str(I/'ut/notan-tagningar/plats/hand.json'),'--scen3d',str(H.parent/'scen3d.json')]
module=types.ModuleType('plats_arkiv');module.__file__=str(I/'plats.py')
with patch('numpy.load',side_effect=np_load),patch.object(Path,'read_text',text):
    exec(compile(archive.read_bytes(),str(archive),'exec'),module.__dict__)
    module.main()
reference.write_bytes((O/'plats.json').read_bytes())
metadata=dict(ursprung='Automatisk referens ur backup8/plats.py och de låsta historiska indatafilerna; inte den efterbearbetade filmplatsen.',
              kod_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
              referens_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),underlag=used)
(H/'testdata/plats_automatisk_fore_jamn.underlag.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fix(s):
    a=s.index('        # Platsfilmen har en senare granskad mall/golvpassning.')
    b=s.index('\n    def test_platssteget_nya_matningar',a)
    return s[:a]+'''        # Arkivets solver och låsta historiska indata ger en fullständig
        # bytejämförelse. Filmplatsen har senare manuella eftersteg.
        self.assertEqual((self.ut/'a/plats.json').read_bytes(),(HIT/'testdata/plats_automatisk_fore_jamn.json').read_bytes())
'''+s[b:]
andra('scen/3d/kontrakt/test_flode.py',fix)
print('Fullständig automatisk platsreferens,',len(used),'hashlåsta underlag.')
