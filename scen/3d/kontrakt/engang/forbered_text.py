"""Reproducerbart lokalt arbetsflöde för text- och diskförbättringen."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from textarbete import backup, byt, jsonfil, UT

HIT=Path(__file__).resolve().parent
sys.path[:0]=[str(HIT.parent/'ingest'),str(HIT/'semantik')]


def sekvenser():
    from bildskydd import skydda
    for clip in ('b','kenny','a'):
        plan=json.loads((HIT/f'ut/{clip}/tom/plan.json').read_text(encoding='utf-8'))
        for sc in plan['scener']:
            for pm in sc['personer']:
                f=Path(pm['rorelse']);backup(f)
                source=UT/f.relative_to(HIT.parents[2])
                s=dict(np.load(source));pid=pm.get('ingest_id') or '1'
                report=skydda(s,f.parent,pid);np.savez(f,**s)
                jsonfil(f.with_name(f'bildskydd_{pid}.json'),report)
                print(clip,sc['id'],'bildskydd',sum(x['stabil_andel']<1 for x in report['rutor']),flush=True)


def schema():
    kf=HIT/'kalla.schema.json';rf=HIT/'regi.schema.json'
    k=json.loads(kf.read_text());r=json.loads(rf.read_text())
    box=dict(type='array',description='X, Y, bredd, höjd i källpixlar; bildens övre vänstra hörn är origo.',items=dict(type='number'),minItems=4,maxItems=4)
    style=dict(type='object',description='Upplöst 2D-stil.',properties={
        'font':dict(type='string'), 'storlek_px':dict(type='number',minimum=1),
        'justering':dict(type='string',enum=['vanster','center','hoger']),
        'farg':dict(type='string',pattern='^#[0-9a-fA-F]{6}$'),
        'kontur_farg':dict(type='string',pattern='^#[0-9a-fA-F]{6}$'),
        'kontur_px':dict(type='number',minimum=0)},additionalProperties=False)
    p=k['$defs']['skarmtext']['properties'];p.update(box=box,stil=style,typ=dict(type='string',enum=['overlay','undertext']),replik=dict(type=['string','null']),
        ursprung=dict(type='object',description='Textens och lokaliseringens ursprung, metod och antaganden.',additionalProperties=True),konfidens=dict(type='number',minimum=0,maximum=1))
    k['$defs']['scen']['properties']['kamera_bindning']=dict(type='object',description='Kameran följer ankaret med uppmätt lokal rörelse; en POV-kamera har kundsidans ankare.',properties={
        'ankare':dict(type='string'),'status':dict(type='string',enum=['uppmatt','antagen','modellbedomd']),'metod':dict(type='string')},required=['ankare','status','metod'],additionalProperties=False)
    r['$defs']['skarmtext']['properties']['box']=box
    r['$defs']['skarmtext']['properties']['stil']=dict(oneOf=[style,dict(type=['string','null'])],description='Stilobjekt; äldre fria strängar avvisas tydligt vid kompilering.')
    jsonfil(kf,k);jsonfil(rf,r)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('steg',choices=['sekvenser','schema']);a=p.parse_args()
    globals()[a.steg]()
