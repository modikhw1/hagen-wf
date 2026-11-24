import sys,json
sys.path[:0]=['scen/3d/kontrakt']
from pathlib import Path
from gemensamt import ladda,skriv
from kompilera import kompilera
import kvalitet,shutil
H=Path('scen/3d/kontrakt');ut=H/'ut/jamn_tabell'
old=ladda(H/'ut/bar/plan_efter_baromkorning.json')
p=kompilera(H/'exempel/bar/kalla.json',H/'exempel/bar/regi.json')
skriv(ut/'bar_plan_efter.json',p)
kvalitet.skriv(p,ut/'bar_plan_efter.json')
shutil.move(str(ut/'kvalitet.md'),str(ut/'bar_kvalitet_efter.md'))
def sam(pl):
    q=pl['kvalitet'];b=q['bildtrohet']
    return dict(objekt=len(pl['objekt']),bildtrohet=[(r['scen'],r['person'],round(r.get('median_px',0),2),round(r.get('p90_px',0),2),r['flaggad']) for r in b['personer']],
        skymning_efter=[(r['scen'],r['del_id'],round(r['andel'],3),r['flaggad']) for r in q.get('skymning',{}).get('efter',{}).get('per_del',[])],
        atgarder=[(a['scen'],a['del_id']) for a in q.get('skymning',{}).get('atgarder',[])])
print('FORE objekt',len(old['objekt']),sorted({o['id'].split(':')[0] for o in old['objekt']}),'har kvalitet' if 'kvalitet' in old else 'saknar kvalitet');print('EFTER',json.dumps(sam(p),ensure_ascii=False))
print(json.dumps(p['kvalitet'].get('kropp',{}).get('rader'),ensure_ascii=False)[:1500])
