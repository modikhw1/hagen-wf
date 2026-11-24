"""Synka bara avläsbara slutvärden från sparade filer; kör inga ingeststeg."""
import json
from pathlib import Path
import numpy as np
from steg10c_filer import ROT, andra, logg
I=ROT/'scen/3d/ingest/ut'
changed=[]
for p in sorted(I.glob('*-tagningar/S*/tider.json')):
    vfile=p.with_name('varld.npz')
    if not vfile.exists():continue
    d=json.loads(p.read_text(encoding='utf-8'))
    with np.load(vfile) as v:
        if 'metriskt_skalbeslut' not in v:continue
        row=d.setdefault('varld',{})
        old={k:row.get(k) for k in ('skala','kamerans_vag_m','skalbeslut')}
        row.update(skala=round(float(v['k']),4),kamerans_vag_m=round(float(np.linalg.norm(np.diff(v['kam_C'],axis=0),axis=1).sum()),2),skalbeslut=json.loads(str(v['metriskt_skalbeslut'])))
        row['loggsynk']=dict(kalla='varld.npz',metod='Slutlig skala och bana avlästa utan omkörning. skalbeslut.vag_m avser kandidaten före eventuell avvisning.',tid='2026-11-10',tidigare=old)
    for u in sorted(p.parent.glob('utsnitt_*.json')):
        pid=u.stem[8:]
        if pid in d.get('sekvens',{}):d['sekvens'][pid]['utsnitt']=json.loads(u.read_text(encoding='utf-8'))
    andra(str(p.relative_to(ROT)),lambda s:json.dumps(d,ensure_ascii=False,indent=1)+'\n')
    changed.append(str(p.relative_to(ROT)))
logg('## Avbrutna korrigeringar klara\n- Platsreferens: arkivets oförändrade solver + 507 hashlåsta historiska indata; hela plats.json jämförs byte för byte.\n- AST-felet kom från sidoeffekten varna i logg(). Loggfunktionen återställd; varningen ligger nu vid stegkörningen och i kor_jamn. Inget provundantag tillagt.\n- Kenny: accepterad bana är 0 m, avvisad kandidat i aktuell varld.npz är 14 307,266 m; gamla tider.json sade 11 693,57 m. Fälten skiljs åt.\n- '+str(len(changed))+' tider.json synkade från befintliga varld/utsnitt; ingen mätfil omkörd.\nKommando: `scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg10c_synka.py`.')
print(len(changed),'loggar synkade')
