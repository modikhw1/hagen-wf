import json,sys,copy
from pathlib import Path
import numpy as np,cv2
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.path[:0]=[str(HERE),str(P/'kontrakt')]
from prova import save,log,normalize,differences
plans={t:json.loads((HERE/t/'plan.json').read_text(encoding='utf-8')) for t in ('fore','efter')}
rows=[]
for row in json.loads((HERE/'efter/blender_matning.json').read_text(encoding='utf-8')):
    sid,u=row['scen'],row['ut'];sc=next(s for s in plans['efter']['scener'] if s['id']==sid)
    objects=[o for o in plans['efter']['objekt'] if o['synlig_ut'][0]<=u<o['synlig_ut'][1]]
    for pr in row['personer']:
        pm=next(p for p in sc['personer'] if p['id']==pr['person']);hip=np.array(pr['backen_m']);wrists=np.array(pr['handleder_m'])
        seat=[o for o in objects if 'sits' in o['id']]
        tables=[o for o in objects if 'skiva' in o['id'] and o['id'].startswith('bord')]
        nearest=lambda os: min(os,key=lambda o:np.linalg.norm(np.array(o['pos_m'])[:2]-hip[:2])) if os else None
        chair=nearest(seat);table=nearest(tables)
        r=dict(scen=sid,ut=u,person=pr['person'],sula_m=pr['sula_over_golv_m'],stod=pm.get('stod'))
        if chair:
            pos=np.array(chair['pos_m']);size=np.array(chair['matt_m']);r['sits']=dict(id=chair['id'],hojd_m=float(pos[2]+size[2]/2),backen_over_sits_m=float(hip[2]-pos[2]-size[2]/2),backen_xy_avstand_m=float(np.linalg.norm(hip[:2]-pos[:2])),matt_m=size.tolist())
        if table:
            pos=np.array(table['pos_m']);size=np.array(table['matt_m']);yaw=table['rotation_rad'][2];c,s=np.cos(yaw),np.sin(yaw);R=np.array([[c,-s],[s,c]])
            xy=(wrists[:,:2]-pos[:2])@R
            r['bord']=dict(id=table['id'],topp_m=float(pos[2]+size[2]/2),handled_over_topp_m=(wrists[:,2]-pos[2]-size[2]/2).tolist(),handled_xy_utanfor_skiva_m=np.linalg.norm(np.maximum(np.abs(xy)-size[:2]/2,0),axis=1).tolist(),matt_m=size.tolist())
        rows.append(r)
    source=cv2.imread(str(HERE/'kalla'/f'{sid}_{u:03d}.png'));render=cv2.imread(str(HERE/'efter'/f'{sid}_{u:03d}_original.png'))
    cv2.imwrite(str(HERE/'jamforelser'/f'{sid}_{u:03d}_rgb_overlagg.png'),cv2.addWeighted(source,.5,render,.5,0))
save(HERE/'kontakter.json',rows)
# Separera full plans proveniens från exakt byggd geometri, utan tolerans.
exact={}
for name in ['notan','bar']:
    a=normalize(json.loads((HERE/f'{name}_dagens_plan.json').read_text(encoding='utf-8')))
    b=normalize(json.loads((HERE/f'{name}_ny_plan.json').read_text(encoding='utf-8')))
    for x in [a,b]:
        for group in x['matning'].values():
            pass
        def strip(o):
            if isinstance(o,dict):
                if 'sokvag' in o:o.pop('sha256',None)
                for v in o.values():strip(v)
            elif isinstance(o,list):
                for v in o:strip(v)
        strip(x['matning']);x['kvalitet'].pop('byggunderlag',None)
    diff=differences(a,b);exact[name]=dict(antal_scen_skillnader=len(diff),skillnader=diff)
save(HERE/'exakt_scenjamforelse.json',exact)
props=[]
for phase,plan in plans.items():
    for r in plan['kvalitet'].get('props',[]):
        props.append(dict(fas=phase,**r))
save(HERE/'prop_jamforelse.json',props)
print('EXAKT',exact)
print('CONTACTS MID')
for sid in [f's{i}' for i in range(1,8)]:
    rr=[r for r in rows if r['scen']==sid];print(rr[1])
print('PROPS')
for r in props:
    print(r['fas'],r['scen'],r['prop'],r['matt_m'],[(v['centrumfel_px'],v['breddkvot']) for v in r['jamforelse']])
log('Slutliga mask- och kamerabilder ersatta efter provskriptsrättning. Normaliserad full plan är exakt lika efter att enbart filproveniens (sha256 och byggunderlag) tagits bort; samtliga övriga fält jämförda utan tolerans. Kontakter mot sits/bord samt faktiska RGB-överlägg skapade.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck")
