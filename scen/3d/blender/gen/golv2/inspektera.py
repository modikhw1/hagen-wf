from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[5]
P = ROOT/'scen/3d'
for file, a, b in [('ingest/mhr_rig.py',180,230), ('ingest/plats.py',0,145), ('kontrakt/golvmatning.py',200,500)]:
    print('\nFILE',file)
    print(''.join((P/file).read_text(encoding='utf-8').splitlines(True)[a:b]))
for f in [ROOT/'forvarld/varld/pipeline/kalla.json',P/'kontrakt/ut/bar/kalla.json']:
    k=json.loads(f.read_text(encoding='utf-8'))
    print('\nMANIFEST',f)
    def walk(o, path=''):
        if isinstance(o,dict):
            if 'sokvag' in o: print(path,o['sokvag'])
            for key,v in o.items(): walk(v,path+'/'+key)
        elif isinstance(o,list):
            for i,v in enumerate(o): walk(v,path+'/'+str(i))
    walk(k)
print('ARCHIVE DIRECT',list((P/'kontrakt/ut/golv2').iterdir()))
