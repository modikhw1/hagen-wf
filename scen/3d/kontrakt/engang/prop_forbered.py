"""Regifiler och billigt propförprov. Inga filmer, inga ingestreferenser ändras."""
import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H))
from kompilera import kompilera

for clip,old in [('b','tom3'),('kenny','tom3'),('a','tom3'),('notan','jamn_tom')]:
    k=json.loads((H/'ut'/clip/'kalla_prop.json').read_text(encoding='utf-8'))
    r=json.loads((H/'ut'/clip/old/'regi.json').read_text(encoding='utf-8'));r['kalla']['revision']=k['revision'];r['edits']=[]
    p=H/'ut'/clip/'regi_prop_tom.json'
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with patch('kvalitet.komplettera'):
        plan=kompilera(H/'ut'/clip/'kalla_prop.json',p)
    (H/f'ut/prop_granskning/provplan_{clip}.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(clip,[(o['scen'],o['id'],o['byggd'],o['antaganden']) for o in plan['props']],flush=True)
    if clip=='b':
        products=dict(kund='FIKTIV_TESTKUND',status='antagen',orsak='Uttryckligen påhittad produktlista för ett lokalt regi-prov.',produkter=[dict(id='fiktiv_molnfrukt',namn='Lila molnfrukt med turkosa prickar',prop_typ='fiktiv_molnfrukt',fiktiv=True)])
        (H/'ut/b/produkter_fiktiva.json').write_text(json.dumps(products,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        r=copy.deepcopy(r);r['edits']=[dict(id='produktbyte_fiktivt',op='byt_prop',ursprung=dict(typ='cm'),prop='prop_o1',ny_typ='fiktiv_molnfrukt',kommentar='PÅHITTAD produkt från produkter_fiktiva.json, FIKTIV_TESTKUND; ingen riktig kundprodukt.')]
        (H/'ut/b/regi_prop_byte.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
