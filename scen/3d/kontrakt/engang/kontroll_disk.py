"""Kompilera de tre nya diskplatserna utan Blender och skriv diagnos."""
import json
import sys
from pathlib import Path
from gemensamt import HIT
from kompilera import kompilera
from trohet import rapport
from textarbete import jsonfil


if __name__=='__main__':
    for clip in ['b','kenny','a']:
        k=json.loads((HIT/f'ut/{clip}/kalla.json').read_text(encoding='utf-8'));r=json.loads((HIT/f'ut/{clip}/tom/regi.json').read_text(encoding='utf-8'));r['kalla']['revision']=k['revision'];r['edits']=[]
        d=HIT/f'ut/{clip}'/(sys.argv[1] if len(sys.argv)>1 else 'kontroll_disk');d.mkdir(exist_ok=False);jsonfil(d/'regi.json',r);p=kompilera(HIT/f'ut/{clip}/kalla.json',d/'regi.json');jsonfil(d/'plan.json',p);rapport(p,d/'plan.json')
        print(clip,[(x['scen'],round(x.get('p90_px',0),2),x['flaggad']) for x in p['kvalitet']['bildtrohet']['personer']],p['kvalitet']['skymning']['atgarder'],flush=True)
