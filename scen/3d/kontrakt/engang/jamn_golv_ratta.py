"""Återställ avsiktligt tidigare golvbeslut för notan efter jämn-passet.

Poseparametrar och kroppsskattningar ändras inte. Bara golv och kontakt körs.
Alla befintliga ändrade filer kopieras först till fore_prop med relativ väg.
"""
import json
import shutil
import sys
import time
from pathlib import Path
import numpy as np
from prop_filer import andra,ROT,BACKUP

I=ROT/'scen/3d/ingest';H=I.parent/'kontrakt';sys.path[:0]=[str(I),str(H)]
import ingest_klipp as IK
from kontakt import steg_kontakt

def skydda(p):
    if not p.exists():return
    target=BACKUP/p.relative_to(ROT)
    if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)

def kor():
    root=I/'ut/notan-tagningar';rows=[]
    for folder in sorted(root.glob('S*'),key=lambda p:int(p.name[1:])):
        for cut in folder.glob('utsnitt_*.json'):
            pid=cut.stem[8:];previous=folder/'fore_jamn'/f'sekvens_{pid}.npz'
            if not previous.exists():continue
            with np.load(previous) as old:
                applied='golv_skala' in old and bool(np.any(old['golv_skala']!=1))
                scale=float(np.median(old['golv_skala'])) if applied else 1.
            decision=json.loads(cut.read_text(encoding='utf-8'))
            if not applied or not decision.get('endast_overkropp'):continue
            for pattern in ['sekvens_*.npz','varld.npz','kontakt_*.json','utsnitt_*.json','tider.json','golv.klar','kontakt.klar']:
                for p in folder.glob(pattern):skydda(p)
            decision.update(endast_overkropp=False,status='antagen',orsak_jamn='Tidigare sekvens har faktiskt tillämpad golvskala. Den tidigare 3D-registreringen/mallen bygger på det beslutet. Överkroppsflaggan får inte ensidigt ta bort golvsteget vid omkörning. Ingen ny golvmätning påstås.',tidigare_golv_skala=scale)
            cut.write_text(json.dumps(decision,ensure_ascii=False)+'\n',encoding='utf-8')
            start=time.perf_counter();meta=json.loads((folder/'meta.json').read_text());floor=IK.steg_golv(folder,meta);contact=steg_kontakt(folder,meta)
            IK.logg(folder,'jamn_golv_aterstallning',time.perf_counter()-start,orsak='Bevara faktiskt tidigare golvbeslut, inte ett felaktigt antagande om tider.json.',tidigare_skala=scale)
            rows.append(dict(tagning=folder.name,tidigare_skala=scale,golv=floor,kontakt=contact));print(folder.name,floor,flush=True)
    out=H/'ut/prop_granskning/golv_rattning.json'
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from kalla_omhasha import main
    main(H/'ut/notan/kalla_jamn.json',H/'ut/notan/kalla_jamn_golv.json')
    # Testkällan är en ny kopia, inte det frysta originalet.
    target=H/'exempel/notan/kalla_jamn.json';skydda(target)
    from kalla_omhasha import omhasha
    k=json.loads((H/'exempel/notan/kalla.json').read_text(encoding='utf-8'));changed=[];missing=[];omhasha(k,target.parent,changed,missing)
    target.write_text(json.dumps(k,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':kor()
