"""Jämför rekvisitakorrigerad baslinje mot dold-fot-planen."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
KONTRAKT=HERE.parent
sys.path[:0]=[str(KONTRAKT),str(KONTRAKT.parent/'ingest')]
from metrisk import las,registrera_dolda_fotter
import trohet
import kroppmatt

OUT=KONTRAKT/'ut/dolda_fotter'
BEFORE=OUT/'rekvisita_passad2'
AFTER=OUT/'dolda_efter'


def load(path):return json.loads(path.read_text(encoding='utf-8'))


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def diffs(a,b,path=''):
    if type(a)!=type(b):return [dict(path=path,fore=a,efter=b)]
    if isinstance(a,dict):
        return [r for k in sorted(a.keys()|b.keys()) for r in diffs(a.get(k),b.get(k),path+'/'+k)]
    if isinstance(a,list):
        if len(a)!=len(b):return [dict(path=path+'/length',fore=len(a),efter=len(b))]
        return [r for i,(x,y) in enumerate(zip(a,b)) for r in diffs(x,y,path+'/'+str(i))]
    return [] if a==b else [dict(path=path,fore=a,efter=b)]


def strip_s4(scene):
    scene=copy.deepcopy(scene)
    for pm in scene.get('personer',[]):
        pm.pop('dolda_fotter',None);pm.pop('benlangder_m',None)
    return scene


def plan_kontroll(before,after):
    bsc={s['id']:s for s in before['scener']};asc={s['id']:s for s in after['scener']}
    checks={
        'tidskarta':before['tidskarta']==after['tidskarta'],
        'kallrutor':before['kallrutor']==after['kallrutor'],
        'renderkamera':before['renderkamera']==after['renderkamera'],
        'matkamera':before['matkamera']==after['matkamera'],
        'objekt':before['objekt']==after['objekt'],
        'props':before.get('props')==after.get('props'),
        'globala_personer':before['personer']==after['personer'],
        'andra_scener':all(bsc[s]==asc[s] for s in bsc if s!='s4'),
        's4_bara_c_och_skala':strip_s4(bsc['s4'])==strip_s4(asc['s4']),
    }
    return dict(kontroller=checks,alla=all(checks.values()),fulla_diffar=diffs(before,after))


def rootfel(plan):
    registrera_dolda_fotter(plan['matning'])
    sc=next(s for s in plan['scener'] if s['id']=='s4');pm=next(p for p in sc['personer'] if p['id']=='C')
    s=las(pm['rorelse']);raw=las(pm['rorelse'],beslut={});v=dict(np.load(sc['varld']))
    errors=[]
    for u in range(*sc['ut']):
        f=sc['lokal_start']+u-sc['ut'][0]
        if not s['inom'][f]:continue
        pose,q,t=trohet.ruta_pose(sc,pm,f,stod=False,data=(s,v));x=pose[1,:3]/100@q.T+t
        o=raw['pose'][f,1,:3]/100@trohet.F+raw['cam_t'][f]
        target=o[:2]/o[2]*float(raw['fokal'])+[plan['kallbild_bredd']/2,plan['kallbild_hojd']/2]
        uv=trohet.projicera(x[None],plan['matkamera']['nycklar'][u],plan['kallbild_bredd'],plan['kallbild_hojd'])[0]
        errors.append(float(np.linalg.norm(uv-target)))
    return dict(median_px=float(np.median(errors)),p90_px=float(np.percentile(errors,90)),max_px=max(errors))


def projection(plan):
    registrera_dolda_fotter(plan['matning'])
    image=next(r for r in trohet.mat(plan,stod=False)['personer'] if r['scen']=='s4' and r['person']=='C')
    skin=next(r for r in kroppmatt.matt_plan(plan,stod=False) if r['scen']=='s4' and r['person']=='C')
    return dict(root=rootfel(plan),bild=dict(median_px=image['median_px'],p90_px=image['p90_px'],bbox_iou=image['bbox_iou']),
                silhuett=dict(iou_median=skin['mask'].get('iou_median'),iou_synlig_median=skin['mask'].get('iou_synlig_median'),
                               tyngdpunkt_median=skin['mask'].get('tyngdpunkt_median')))


def main():
    before=load(BEFORE/'notan/plan.json');after=load(AFTER/'notan/plan.json')
    bar_before=load(BEFORE/'bar/plan.json');bar_after=load(AFTER/'bar/plan.json')
    result=dict(notan=plan_kontroll(before,after),bar=plan_kontroll(bar_before,bar_after) if bar_before.get('scener') else dict(
                    renderdata_lika=all(bar_before.get(k)==bar_after.get(k) for k in ('tidskarta','kallrutor','renderkamera','matkamera','objekt','props','personer'))),
                projektion=dict(fore=projection(before),efter=projection(after)))
    result['projektion']['differens']=diffs(result['projektion']['fore'],result['projektion']['efter'])
    save(OUT/'jamforelse.json',result)
    print('notan renderdata',result['notan']['kontroller'])
    print('bar',result['bar'])
    print('projektion',json.dumps(result['projektion'],ensure_ascii=False,indent=2))
    if not result['notan']['alla'] or not all(result['bar'].values()):raise SystemExit(1)


if __name__=='__main__':main()
