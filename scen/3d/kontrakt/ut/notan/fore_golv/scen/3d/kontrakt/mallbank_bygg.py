"""Skriv den lilla, lokala mallbanken. Kör bara när bankfiler saknas.

Alla siffror här är mallvärden, valda för enkel procedurgeometri. De är
inte uppmätta lokaldata. Notans två bord är ett handbedömt topologival.
"""
import copy
import math
from pathlib import Path
from gemensamt import skriv

BANK = Path(__file__).parent/'rumsmall'


def eg(t, text, **kw): return dict(type=t, description=text, **kw)
def obj(text, props, required): return eg('object',text,properties=props,required=required,additionalProperties=False)
def vec(text): return eg('array',text,items=eg('number','Meter.'),minItems=3,maxItems=3)


def schema():
    ank = obj('Ankare som delen tillhandahåller, i delens lokala ram.', dict(
        id=eg('string','Stabilt namn.',minLength=1), typ=eg('string','Stödets funktion.',enum=['sate','bordskant','staplats','sta_bakom','annat']),
        pos_m=vec('Golvpunkten under sitt/ståplats; bordskant ligger på skivan.'), riktning_rad=eg('number','Framåt från +X, radianer.'),
        sate_hojd_m=eg('number','Sitsens ovansida över golv, mallvärde.',minimum=.1),
        backen_over_sate_m=eg('number','Ledcentrum över sitsens yta, mallvärde för mjukdelar.',minimum=0),
        fotled_over_golv_m=eg('number','Fotledens ledcentrum över sulan, mallvärde.',minimum=0)), ['id','typ','pos_m','riktning_rad'])
    delp = obj('En typad parametrisk del. Lokalt XY på golvet; mått X,Y,Z. Alla tal är mallvärden.',dict(
        id=eg('string','Unikt delnamn.',minLength=1), typ=eg('string','Procedurbyggare.',enum=['golv','vagg','bord','stol','bardisk','hylla','fonster','lampa']),
        pos_m=vec('Delens lokala origo på golvet, alternativt nederkanten för vägg/fönster/lampa.'), matt_m=eg('array','Bredd, djup, totalhöjd till sits/skiva. Meter.',items=eg('number','Positivt mallmått.',minimum=.001),minItems=3,maxItems=3),
        yaw_rad=eg('number','Rotation kring +Z.'), material=obj('Enkelt material.',dict(farg=eg('string','Färg.',pattern='^#[0-9a-fA-F]{6}$'),ben_farg=eg('string','Ben/kantfärg.',pattern='^#[0-9a-fA-F]{6}$')),['farg']),
        ankare=eg('array','Delens stödankare.',items=ank), folj_ankare=eg('string','Valfritt mätt ankare som delen snäpps till efter rigid passning.'),
        modell_ref=eg(['string','null'],'Valfri framtida lokal modellreferens. Laddas inte nu.'),
        texturprojektion=eg(['object','null'],'Reserverat för framtida projektion från källbilder. Används inte nu.',additionalProperties=True)),['id','typ','pos_m','matt_m','yaw_rad','material','ankare'])
    return dict({'$schema':'https://json-schema.org/draft/2020-12/schema'}, **obj('rumsmall/1. Malltal, ingen påstådd rumsrekonstruktion.',dict(
        schema_version=eg('string','Format.',const='rumsmall/1'), id=eg('string','Mall-id.',minLength=1),
        beskrivning=eg('string','Vad mallen föreställer.'),fiktiv=eg('boolean','Sant för helt påhittad kundlokal.'),
        status=eg('string','Alla numeriska värden i delar och ankare kommer från mallen.',const='mall'),
        antaganden=eg('array','Skäl och gränser.',items=eg('string','Ett skäl.')),
        delar=eg('array','Parametriska byggdelar.',minItems=1,items=delp)),['schema_version','id','beskrivning','fiktiv','status','antaganden','delar']))


def anchor(id, typ, pos, yaw, **kw): return dict(id=id,typ=typ,pos_m=pos,riktning_rad=yaw,**kw)
def part(id, typ, p, size, yaw=0, col='#d5ccb6', anchors=None, **kw):
    return dict(id=id,typ=typ,pos_m=p,matt_m=size,yaw_rad=yaw,material=dict(farg=col,ben_farg='#303537'),ankare=anchors or [],modell_ref=None,texturprojektion=None,**kw)
def chair(role, y, yaw=0):
    return part('stol_'+role,'stol',[0,y,0],[.48,.48,.52],yaw,'#6d6252',
                [anchor('stol_'+role,'sate',[0,0,0],math.pi/2,sate_hojd_m=.52,backen_over_sate_m=.11,fotled_over_golv_m=.065)])


def main():
    bank={}; shell=[part('golv','golv',[-.5,1,-.08],[6,6,.08],col='#a8a299'),
                   part('vagg_bak','vagg',[0,3.3,0],[5,.12,2.7],col='#e5ddc7'),
                   part('vagg_sida','vagg',[1.7,1,0],[.12,4.6,2.7],col='#d8d0ba'),
                   part('fonster','fonster',[1.62,.5,.9],[.04,1.7,1.5],col='#a7cad4'),
                   part('lampa','lampa',[0,1,2.25],[.36,.36,.22],col='#d9bb72')]
    chairs=[chair('A',0),chair('B',2.5,math.pi)]
    tables=[part('bord_A','bord',[0,.64,0],[.90,.68,.88],col='#333638',anchors=[anchor('bordskant_A','bordskant',[0,-.34,.88],-math.pi/2)],folj_ankare='stol_A'),
            part('bord_B','bord',[0,1.79,0],[.90,.72,.94],col='#333638',anchors=[anchor('bordskant_B','bordskant',[0,.36,.94],math.pi/2)],folj_ankare='stol_B')]
    shell[0]['ankare']=[anchor('staplats_C','staplats',[-.45,-.45,.08],0,fotled_over_golv_m=.065)]
    def mall(id,desc,delar,fiktiv=False):
        return dict(schema_version='rumsmall/1',id=id,beskrivning=desc,fiktiv=fiktiv,status='mall',
                    antaganden=['Alla mått, färger, sitsdetaljer och väggutsträckningar är mallvärden, inte uppmätta.',
                                'Bordshöjderna är valda nära det befintliga kroppslägets händer. Källans metriska skala är osäker. Inga yttexturer har återskapats.'],delar=copy.deepcopy(delar))
    bank['notan_tva_bord']=mall('notan_tva_bord','Källrummets topologi: två separata svarta bord med varsin stol. S7 visar mellanrummet. Måtten är mallvärden.',shell+chairs+tables)
    pairchairs=[chair('A',0),chair('B',1.25,math.pi)]
    pairtable=part('bord_gemensamt','bord',[0,.625,0],[.9,.72,.78],col='#694f37',anchors=[anchor('bordskant_A','bordskant',[0,-.36,.78],-math.pi/2),anchor('bordskant_B','bordskant',[0,.36,.78],math.pi/2)])
    bank['restaurang_tva']=mall('restaurang_tva','Restaurangbord för två: ett gemensamt bord, två stolar, golv, väggar, fönster och lampa.',shell+pairchairs+[pairtable])
    bar=part('disk','bardisk',[0,.5,0],[3,.7,1.05],col='#95724c',anchors=[anchor('staplats_1','staplats',[-.5,-.65,0],math.pi/2,fotled_over_golv_m=.065),anchor('staplats_2','staplats',[.5,-.65,0],math.pi/2,fotled_over_golv_m=.065),anchor('bakom_disk','sta_bakom',[0,-.65,0],math.pi/2),anchor('disk_kant','bordskant',[0,.35,1.05],math.pi/2)])
    bank['bar_disk']=mall('bar_disk','Bar med disk, ståplatser bakom disken, hylla och väggar.',shell+[bar,part('hylla','hylla',[0,2.8,0],[2,.3,2])])
    customer=copy.deepcopy(shell+chairs+tables)
    for d in customer:
        if d['typ']=='golv':d['material']['farg']='#4f8d91'
        if d['typ']=='vagg':d['material']['farg']='#e7a5a4'
        if d['typ']=='stol':d['material']['farg']='#184864'
        if d['typ']=='bord':d['material']['farg']='#e5c078'
        p=d['pos_m'];d['pos_m']=[4-p[1],3+p[0],p[2]];d['yaw_rad']+=math.pi/2
    customer += [part('disk_kund','bardisk',[4.8,4.15,0],[2.0,.6,1.1],col='#174a60'),part('hylla_kund','hylla',[4.8,4.5,0],[2.0,.3,1.8],col='#edbb76')]
    bank['fiktiv_lokal']=mall('fiktiv_lokal','FIKTIV kundlokal: rosa väggar, turkost golv, blå stolar och guldfärgade bord. Ingen verklig kund.',customer,True)
    for name,data in [('rumsmall.schema',schema()),*bank.items()]:
        p=BANK/(name+'.json')
        if p.exists(): raise FileExistsError(p)
        skriv(p,data)


if __name__=='__main__': main()
