import json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.path.insert(0,str(HERE));from prova import save
plans={t:json.loads((HERE/t/'plan.json').read_text(encoding='utf-8')) for t in ['fore','efter']}
contacts=[]
for phase,plan in plans.items():
    measures=json.loads((HERE/phase/'blender_matning.json').read_text(encoding='utf-8'))
    for row in measures:
        sid,u=row['scen'],row['ut'];sc=next(s for s in plan['scener'] if s['id']==sid)
        for pr in row['personer']:
            pm=next(p for p in sc['personer'] if p['id']==pr['person']);a=pm['stod'];hip=np.array(pr['backen_m'])
            chair=next((o for o in plan['objekt'] if o['id']==a['id'] and o['synlig_ut'][0]<=u<o['synlig_ut'][1]),None)
            if chair and a['typ']=='sate':
                top=chair['pos_m'][2]+chair['matt_m'][2]/2
                contacts.append(dict(fas=phase,scen=sid,ut=u,sits=chair['id'],sits_topp_m=top,backen_over_sits_m=float(hip[2]-top),backen_xy_m=float(np.linalg.norm(hip[:2]-np.array(chair['pos_m'])[:2]))))
save(HERE/'sitskontakter.json',contacts)
print('SITS efter',[(sid,[(round(r['backen_over_sits_m'],4),round(r['backen_xy_m'],4)) for r in contacts if r['fas']=='efter' and r['scen']==sid]) for sid in [f's{i}' for i in range(1,8)]])
print('PROP ORSAK')
for phase,p in plans.items():
    for r in p['kvalitet'].get('props',[]):
        if r['scen'] in ['s2','s3','s7']:print(phase,r['scen'],r['prop'],r['antaganden'])
print('SCENHEIGHT')
for s in plans['efter']['scener']:
    row=next(r for r in json.loads((HERE/'efter/blender_matning.json').read_text(encoding='utf-8')) if r['scen']==s['id'])
    x=np.array(row['personer'][0]['leder_m']);print(s['id'],'huvud',x[110,2],'root',row['personer'][0]['backen_m'])
