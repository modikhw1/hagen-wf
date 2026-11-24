"""Vår parametriska tolkning av harnessens lokalkoder, inga kundmått."""
import json
import math
from pathlib import Path
from textarbete import jsonfil

HIT=Path(__file__).resolve().parent


def del_(id,typ,pos,matt,farg='#a5aaa8',ankare=None):
    return dict(id=id,typ=typ,pos_m=pos,matt_m=matt,yaw_rad=0.,material=dict(farg=farg,ben_farg='#343e43'),ankare=ankare or [])


def ank(id,typ,pos,direction):
    return dict(id=id,typ=typ,pos_m=pos,riktning_rad=direction,fotled_over_golv_m=.065)


def mall(id,kind='disk',farg='#b4c8cc',fiktiv=False):
    parts=[del_('golv','golv',[0,0,-.04],[10,10,.04],'#655d52')]
    if kind in ('disk','glass','chark','bar','kok'):
        anchors=[ank('sta_bakom','sta_bakom',[0,-.8,0],math.pi/2),ank('kundsida','staplats',[0,.8,0],-math.pi/2),ank('kamera_kund','annat',[0,1.5,1.45],-math.pi/2),ank('kamera_personal','annat',[0,-1.5,1.45],math.pi/2)]
        parts += [del_('disk','bardisk',[0,0,0],[3.6,.65,1.0],farg,anchors),del_('bakre_hylla','hylla',[0,-2,0],[3.2,.35,1.8],'#899e9d')]
        if kind in ('glass','chark'):
            parts += [del_('monter','hylla',[0,.32,.65],[3.4,.6,.42],'#c6dfe2')]
        if kind=='kok':parts += [del_('arbetsbord','bord',[2.5,-1,0],[1.4,.7,.9],'#b8bfc1')]
    elif kind in ('matsal','uteservering'):
        parts += [del_('bord','bord',[0,0,0],[1.2,.8,.74],'#ab825a')]
        for i,y in enumerate([-1.,1.]):
            a=ank(f'stol_{i+1}','sate',[0,0,0],math.pi/2 if y<0 else -math.pi/2);a.update(sate_hojd_m=.46,backen_over_sate_m=.11)
            parts += [del_(f'stol_{i+1}','stol',[0,y,0],[.45,.45,.46],'#445a52',[a])]
    else:
        parts += [del_('entre_vagg','vagg',[-2,0,0],[.15,4,2.5],'#d5c9b5'),del_('fonster','fonster',[-1.9,0,.8],[.06,1.4,1.3],'#b3c9cb', [ank('staplats','staplats',[1,0,-.8],0)])]
    if kind in ('glass','chark') or id=='servering_disk':
        for piece in parts:
            if piece['typ'] in ('bardisk','hylla') and piece['id']!='bakre_hylla':piece['oppen_mitt']=True
    if fiktiv:
        for piece in parts:
            piece['material']['farg']='#442255' if piece['typ']=='golv' else '#c836ee'
            piece['material']['ben_farg']='#efdb26'
    return dict(schema_version='rumsmall/1',id=id,beskrivning=('Helt påhittad måndisk på planeten Ärtan. ' if fiktiv else '')+f'Parametrisk {kind}; vår egen mall, ingen uppmätt kundlokal.',fiktiv=fiktiv,status='mall',antaganden=['Alla mått, färger, konstruktioner och avstånd är mallvärden. Anpassad diskhöjd redovisas separat med rest mot källans handledscues.'],delar=parts)


def bygg():
    mapping={code:'lokal_'+code for code in ['disk_kassa','kok','matsal','entre','bar','uteservering']}
    types=dict(disk_kassa='disk',kok='kok',matsal='matsal',entre='entre',bar='bar',uteservering='uteservering')
    for code,id in mapping.items():jsonfil(HIT/'rumsmall'/f'{id}.json',mall(id,types[code]))
    for id,kind,col in [('chark_disk','chark','#c3d1d2'),('glass_disk','glass','#d8d6b7'),('servering_disk','disk','#5d7f70'),('fiktiv_mandisk','chark','#703faa')]:
        jsonfil(HIT/'rumsmall'/f'{id}.json',mall(id,kind,col,id.startswith('fiktiv')))
    jsonfil(HIT/'rumsmall/lokalkoder.json',dict(status='antagen',ursprung='Vår egen mapping av harnessens lokal[] till parametriska mallar. Ingen kunddata eller uppmätt rumskoppling.',koder=mapping))


if __name__=='__main__':bygg()
