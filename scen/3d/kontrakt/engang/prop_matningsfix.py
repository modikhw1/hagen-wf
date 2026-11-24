"""Hitta närmaste faktiskt mätta handled och mallens bordsskivor."""
import json
import sys
from prop_filer import andra, ROT

def mata(s):
    a="                f=records[0]['lokal_ruta']; rp=folder/'kropp'/str(holder['ingest_id'])/f'{f:04d}.npz'\n                if rp.exists():"
    b="""                files=sorted((folder/'kropp'/str(holder['ingest_id'])).glob('*.npz'))
                if files:
                    # Källprovet kan ligga i en kort lucka. Byt då inte till en
                    # hand från en helt annan del av scenen.
                    records.sort(key=lambda r:min(abs(int(x.stem)-r['lokal_ruta']) for x in files))
                    f=records[0]['lokal_ruta'];rp=min(files,key=lambda x:abs(int(x.stem)-f))
                else: rp=folder/'ingen_handled.npz'
                if rp.exists() and abs(int(rp.stem)-f)<=5:"""
    if a not in s:raise ValueError('Saknar handledsval')
    return s.replace(a,b).replace("'Grepphand väljs närmast avläst produktregion vid första provrutan. Greppets djup följer handleden, utsträckning och dolda sidor är bankvärden.'", "'Grepphand väljs närmast avläst produktregion vid en provruta med kroppsskattning inom fem rutor (antagen tolerans). Greppets djup följer handleden; utsträckning och dolda sidor är bankvärden. Saknad hand betyder ingen byggbar mätning.'")
andra('scen/3d/kontrakt/kalla_prop.py',mata)
andra('scen/3d/kontrakt/propplan.py',lambda s:s.replace("if ('skiva' in x['id']) and", "if ('skiva' in x['id'] or (x['id'].startswith('bord') and ':' not in x['id'] and x['matt_m'][2]<.1)) and"))
sys.path.insert(0,str(ROT/'scen/3d/kontrakt'))
from kalla_prop import fyll
for c in ['b','kenny','a','notan']:
    base=ROT/'scen/3d/kontrakt/ut'/c
    k=json.loads((base/'kalla_jamn.json').read_text(encoding='utf-8'));semfil=ROT/'scen/3d/kontrakt/semantik/ut'/c/'semantik.json'
    out=fyll(k,base,json.loads(semfil.read_text(encoding='utf-8')),c,semfil)
    andra(str((base/'kalla_prop.json').relative_to(ROT)),lambda s:json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(c,'källkopia uppdaterad med säkerhetskopia',flush=True)
