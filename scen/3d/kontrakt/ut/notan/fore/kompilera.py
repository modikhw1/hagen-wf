"""kalla.json + regi.json -> deterministisk, upplöst plan/1. Bara stdlib och numpy."""
import argparse
import copy
import math
import re
import sys
from fractions import Fraction
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
from gemensamt import HIT, ladda, skriv, kontrollera

F = np.diag([1., -1., -1.])
FARGER = ['#c9b7a5', '#8fa3b8', '#b89a8f', '#9fb48f', '#b0a0c0']


class EjTillampad(ValueError): pass


def gravitation(v):
    u = v['upp'] / np.linalg.norm(v['upp']); z = np.array([0., 0., 1.]); c = float(u @ z)
    if c < -1 + 1e-10: return np.diag([1., -1., -1.])
    x, y, z = np.cross(u, z); vx = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def transform(pos, rot):
    m = np.eye(4); m[:3, :3] = rot; m[:3, 3] = pos
    return m.tolist()


def sikta(pos, mal):
    bak = np.array(pos) - mal; norm = np.linalg.norm(bak)
    if not np.all(np.isfinite(bak)): raise EjTillampad('Kamerans position eller mål är inte ändliga tal.')
    if norm < 1e-8: raise EjTillampad('Kamerans position och mål sammanfaller.')
    bak /= norm; hoger = np.cross([0., 0., 1.], bak)
    if np.linalg.norm(hoger) < 1e-8: hoger = np.cross([0., 1., 0.], bak)
    hoger /= np.linalg.norm(hoger)
    return transform(pos, np.column_stack([hoger, np.cross(bak, hoger), bak]))


def storlek(matt):
    if matt is None or min(matt) <= 0: raise EjTillampad('Lådan kräver tre positiva mått i matt_m.')
    return [matt[0], matt[2], matt[1]]  # kontrakt: bredd, höjd, djup -> lokalt XYZ


def rumobjekt(rum, G):
    objekt = [dict(id='golv', namn='golv', typ='plan', pos_m=[0, 0, rum['floor']['height']],
                   rotation_rad=[0, 0, 0], matt_m=[40, 40, 0], farg='#5a554e', top_slope=0)]
    for w in rum['walls']:
        t = G @ w['tangent']
        objekt.append(dict(id=w['id'], namn='rum:'+w['id'], typ='lada', pos_m=(G @ w['centre']).tolist(),
                            rotation_rad=[0, 0, math.atan2(t[1], t[0])], matt_m=[w['width'], .01, w['height']], farg='#77716a', top_slope=0))
    for o in rum['objects']:
        farg = '#347e77' if o['label'] == 'pool table' else '#a58b68' if o['label'] == 'bar counter' else '#777e87'
        objekt.append(dict(id=o['id'], namn='rum:'+o['label']+':'+o['id'], typ='lada', pos_m=(G @ o['centre']).tolist(),
                            rotation_rad=[0, 0, o['yaw']], matt_m=o['size'], farg=farg, top_slope=o.get('top_slope', 0)))
    return {o['id']: o for o in objekt}


def kompilera(kallfil, regifil):
    kallfil, regifil = Path(kallfil).resolve(), Path(regifil).resolve()
    K, R = ladda(kallfil), ladda(regifil)
    varningar = kontrollera(K, R, kallfil.parent)
    def absolut(o):
        if isinstance(o, dict): return {k: str((kallfil.parent/v).resolve()) if k == 'sokvag' else absolut(v) for k,v in o.items()}
        if isinstance(o, list): return [absolut(v) for v in o]
        return o
    matning = absolut(K['matning'])
    # Saknade filer får vara varningar i kontraktet, men aldrig i en byggbar plan.
    def filer(o):
        if isinstance(o, dict):
            if 'sokvag' in o and not Path(o['sokvag']).is_file(): raise ValueError('Mätfil saknas: ' + o['sokvag'])
            for v in o.values(): filer(v)
        elif isinstance(o, list):
            for v in o: filer(v)
    filer(matning)
    if len(matning['kameror']) != 1 or len(matning['rum']) != 1: raise ValueError('Byggaren kräver en uppmätt kamera och ett rum.')
    kamera = matning['kameror'][0]
    V = np.load(kamera['spar_metrisk']['sokvag']); G = gravitation(V); N = K['tidsbas']['antal_rutor']
    if len(V['kam_R']) != N: raise ValueError('Kamerans bildantal avviker från tidsbasen.')
    fps = Fraction(K['tidsbas']['fps_taljare'], K['tidsbas']['fps_namnare'])
    ofps = Fraction(R['utdata']['fps_taljare'], R['utdata']['fps_namnare'])
    if fps != ofps: raise ValueError('Ändrad bildfrekvens stöds inte ännu; ange källans fps.')
    if R['utdata']['render_backend'] != 'blender_mhr': raise ValueError('Planen kräver blender_mhr.')
    if R['utdata']['stil_ref']: raise ValueError('stil_ref kan inte lösas till MHR-material.')
    if R['utdata']['ljudpolicy']=='designade_rostar': raise ValueError('designade_rostar kräver ett röstbygge som inte ingår.')
    if not (kallfil.parent/K['klipp']['video']['sokvag']).is_file(): raise ValueError('Källvideon saknas.')
    if R['ramar']['bevara_klippoffset_s'] is not None: raise ValueError('bevara_klippoffset_s stöds inte ännu.')
    # Tider i kalla är avrundade (3-4 decimaler): närmaste ruta, inte uppåt. 0,667 s vid 30 fps är ruta 20.
    def ruta(t): return min(N, math.floor(Fraction(str(t)) * fps + Fraction(1, 2)))
    seq = {p['person']: dict(np.load(p['rorelse']['sokvag'])) for p in matning['personer']}
    for pid, s in seq.items():
        if len(s['pose']) != N or len(s['inom']) != N: raise ValueError('Fel bildantal för person ' + pid)
    pers = {p['id']: dict(id=p['id'], roll=p['roll'], farg=FARGER[i % len(FARGER)],
                         rorelse=next(m['rorelse']['sokvag'] for m in matning['personer'] if m['person']==p['id']))
            for i,p in enumerate(sorted(K['semantik']['personer'], key=lambda p:p['id']))}
    rum = ladda(matning['rum'][0]['fil']['sokvag']); objekt = rumobjekt(rum, G)
    # Semantiska prop-id kan skilja från mätningens objekt-id.
    for p in K['semantik']['props']:
        if p['rum_ref'] in objekt and p['id'] != p['rum_ref']:
            o=objekt.pop(p['rum_ref']); o['id']=p['id']; objekt[p['id']]=o
    spar = [dict(matris=transform(G @ V['kam_C'][i], G @ V['kam_R'][i] @ F),
                 lins_mm=float(next(iter(seq.values()))['fokal']) * 36 / K['klipp']['video']['bredd']) for i in range(N)]
    scener = [dict(id=s['id'], a=ruta(s['start_s']), b=ruta(s['slut_s']), ursprung=s['id'],
                   objekt=copy.deepcopy(objekt), kamera=copy.deepcopy(spar), ljud=True) for s in K['semantik']['scener']]
    if not scener: raise ValueError('Källan saknar tidsatta scener.')
    skyddade = {b['scen'] for b in K['semantik']['beats'] if b['id'] in R['ramar']['bevara_beats']}
    if None in skyddade: raise ValueError('Ett bevarat beat saknar scenbindning.')
    tillampat, ej = [], []; standard = []   # standardvärden som planen själv valt, inte CM; skrivs i andring
    lednamn = ladda(HIT.parent/'ingest/mhr_ledernamn.json')
    def scen(sid):
        s=next((s for s in scener if s['id']==sid), None)
        if s is None: raise EjTillampad('Scenen finns inte i den aktuella tidslinjen: '+sid)
        return s
    def valda(e): return scener if e.get('scen', 'alla')=='alla' else [scen(e['scen'])]
    def hitta(s, pid):
        if pid not in s['objekt']: raise EjTillampad('Objektet finns inte i scenen: '+pid)
        return s['objekt'][pid]
    def placera(s, o, plats, stod=None):
        if plats:
            ref=hitta(s, plats['relativt']); yaw=ref['rotation_rad'][2]; c, z=math.cos(yaw), math.sin(yaw)
            o['pos_m']=(np.array(ref['pos_m']) + np.array([[c,-z,0],[z,c,0],[0,0,1]]) @ plats['forskjutning_m']).tolist()
        elif stod:
            ref=hitta(s, stod); o['pos_m']=[*ref['pos_m'][:2], ref['pos_m'][2]+ref['matt_m'][2]/2+o['matt_m'][2]/2]
        else: raise EjTillampad('Placering saknas: ange plats eller stod; ingen position uppfinns.')
    def kameranycklar(e, s):
        lage=e['lage']; a,b=s['a'],s['b']; resultat=copy.deepcopy(spar)
        if lage=='folj_uppmatt':
            if e.get('mal') or e.get('inramning') or e.get('fov_grader'): raise EjTillampad('folj_uppmatt med ändrat utsnitt stöds inte.')
            return resultat
        if lage not in ('stativ', 'nyckelbilder'): raise EjTillampad('Kameraläget stöds inte: '+lage)
        fov=e.get('fov_grader')
        if fov is None and lage=='stativ': fov=40; standard.append(dict(falt='fov_grader',varde=40,orsak='CM angav ingen synvinkel'))
        if fov is not None and not 0<fov<180: raise EjTillampad('fov_grader måste vara mellan 0 och 180.')
        def nyckel(pos, mal, fov):
            # Vertikal FOV, men Blender har horisontell sensor 36 mm.
            lins=36 * R['utdata']['hojd'] / R['utdata']['bredd'] / (2*math.tan(math.radians(fov)/2))
            return dict(matris=sikta(pos, mal), lins_mm=lins)
        if lage=='nyckelbilder':
            keys=e.get('nyckelbilder', [])
            if not keys or any(y['t_s']<=x['t_s'] for x,y in zip(keys,keys[1:])): raise EjTillampad('Kameranycklar måste finnas och ha stigande tider.')
            for f in range(a,b):
                t=(f-a)/float(fps); left=max((k for k in keys if k['t_s']<=t),key=lambda k:k['t_s'],default=keys[0]); right=next((k for k in keys if k['t_s']>=t),keys[-1])
                w=0 if left is right else (t-left['t_s'])/(right['t_s']-left['t_s'])
                pos=G @ ((1-w)*np.array(left['pos_m'])+w*np.array(right['pos_m'])); mal=G @ ((1-w)*np.array(left['mal_m'])+w*np.array(right['mal_m']))
                resultat[f]=nyckel(pos,mal,(1-w)*left['fov_grader']+w*right['fov_grader'])
        else:
            mal=e.get('mal'); pos=G @ V['kam_C'][a]; punkter=[]
            if mal and mal['typ']=='person':
                if mal['id'] not in seq: raise EjTillampad('Personmålet saknar rörelse.')
                punkt=mal.get('punkt')
                if punkt is None: punkt='kropp'; standard.append(dict(falt='mal.punkt',varde='kropp (c_spine2)',orsak='CM angav ingen målpunkt'))
                namn={'huvud':'c_head', 'kropp':'c_spine2'}.get(punkt)
                if namn is None: raise EjTillampad('Okänd målpunkt på person.')
                S=seq[mal['id']]; i=lednamn.index(namn)
                punkter=[G @ (V['kam_C'][f]+V['kam_R'][f] @ (F @ (S['pose'][f,i,:3]/100)+S['cam_t'][f]))
                         for f in range(a,b) if S['inom'][f]]
                if not punkter: raise EjTillampad('Personmålet är inte synligt i scenen.')
                target=np.median(punkter,axis=0)
            elif mal and mal['typ']=='prop': target=np.array(hitta(s,mal['id'])['pos_m'])
            elif mal: raise EjTillampad('Punktmål saknar numeriska koordinater; använd nyckelbilder.')
            else:
                target=pos + G @ V['kam_R'][a] @ [0.,0.,1.]
                standard.append(dict(falt='mal',varde='uppmätta kamerans blickriktning',orsak='CM angav inget mål'))
            if e.get('inramning'):
                hojd={'hel':2.1,'halv':1.25,'nara':.55}[e['inramning']]
                # För huvudmål placeras huvudet i bildens övre del, med luft ovanför.
                if mal and mal['typ']=='person' and mal.get('punkt')=='huvud': target=target-np.array([0,0,hojd*.28])
                riktning=pos-target; nr=np.linalg.norm(riktning)
                if nr<1e-8: raise EjTillampad('Kamerans position och mål sammanfaller.')
                riktning/=nr
                avstand=hojd/(2*math.tan(math.radians(fov)/2))
                # Ett stativ kan inte följa en person. Öka avståndet vid behov så
                # huvudets uppmätta bana och scenens rekvisita ryms i samma bild.
                rot=np.array(sikta(target+riktning,target))[:3,:3]
                tv=math.tan(math.radians(fov)/2); th=tv*R['utdata']['bredd']/R['utdata']['hojd']
                for prop in K['semantik']['props']:
                    if prop['id'] in s['objekt']:
                        o=s['objekt'][prop['id']]; punkter.append(np.array(o['pos_m']))
                for punkt in punkter:
                    x,y,z=rot.T @ (punkt-target)
                    avstand=max(avstand,z+(abs(x)+.25)/th,z+(abs(y)+.2)/tv)
                pos=target+riktning*avstand
            key=nyckel(pos,target,fov)
            for f in range(a,b): resultat[f]=copy.deepcopy(key)
        return resultat
    for e in R['edits']:
        # En edit är atomisk: även ett fel i den sista scenen rullar tillbaka hela editen.
        fore=copy.deepcopy((scener,pers)); op=e['op']; andring={}; standard.clear()
        try:
            if e['ursprung']['typ']=='harness-forslag' and e['ursprung'].get('godkand_av_cm') is not True:
                raise EjTillampad('Harnessförslaget är inte godkänt av CM.')
            if op in ('byt_replik','lagg_till_replik'): raise EjTillampad('Talersättning ingår inte; barkällan saknar kända repliker.' if not K['semantik']['repliker'] else 'Talersättning ingår inte.')
            if op=='casta':
                if e['person'] not in pers: raise EjTillampad('Personen saknas.')
                if any(v is not None for k,v in e['utseende'].items() if k!='troja_farg') or e.get('rost'): raise EjTillampad('MHR-förhandsvisningen stöder endast helkroppsfärg och rollnamn.')
                p=pers[e['person']]; farg=e['utseende'].get('troja_farg') or p['farg']
                if not re.fullmatch('#[0-9a-fA-F]{6}', farg): raise EjTillampad('Färg måste vara #RRGGBB.')
                roll=e['kundroll']['namn']
                if farg.lower()==p['farg'].lower() and roll==p['roll']: raise EjTillampad('Castingen ändrar ingenting: ingen ny färg (troja_farg) och samma rollnamn.')
                p.update(farg=farg.lower(), roll=roll); andring=copy.deepcopy(p)
            elif op in ('trimma_scen','ta_bort_scen','flytta_scen','duplicera_scen'):
                s=scen(e['scen'])
                if s['ursprung'] in skyddade: raise EjTillampad('Scenen innehåller ett beat som ska bevaras.')
                if op=='trimma_scen':
                    if e['lage']=='stracka': raise EjTillampad('Tidssträckning stöds inte.')
                    if e.get('start_s') is None and e.get('slut_s') is None: raise EjTillampad('Trimningen saknar start_s och slut_s och ändrar ingenting.')
                    a=s['a'] if e.get('start_s') is None else ruta(e['start_s']); b=s['b'] if e.get('slut_s') is None else ruta(e['slut_s'])
                    if not s['a']<=a<b<=s['b']: raise EjTillampad('Trimningen är tom eller utanför nuvarande intervall.')
                    if (a,b)==(s['a'],s['b']): raise EjTillampad('Trimningen ändrar inte scenens intervall.')
                    if e['lage']=='replik_sakert':
                        for r in K['semantik']['repliker']:
                            for word in r['ord'] or [r]:
                                if any(word['start_s'] < t < word['slut_s'] for t in (a/float(fps),b/float(fps))): raise EjTillampad('Trimningen skulle klippa ett ord eller en replik.')
                    andring=dict(fore=[s['a'],s['b']],efter=[a,b]); s.update(a=a,b=b)
                    if s.get('kamera_edit'): s['kamera']=kameranycklar(s['kamera_edit'],s)
                elif op=='ta_bort_scen': scener.remove(s); andring=dict(borttaget=[s['a'],s['b']])
                else:
                    if e.get('efter')==s['id'] and op=='flytta_scen': raise EjTillampad('En scen kan inte flyttas efter sig själv.')
                    efter=scen(e['efter']) if e.get('efter') else (s if op=='duplicera_scen' else None)
                    if op=='duplicera_scen':
                        if any(x['id']==e['ny_id'] for x in scener): raise EjTillampad('Scen-id finns redan.')
                        s=copy.deepcopy(s); s['id']=e['ny_id']; s['ljud']=e['med_ljud']
                    else: scener.remove(s)
                    scener.insert(scener.index(efter)+1 if efter else 0,s); andring=dict(ordning=[s['id'] for s in scener])
            elif op in ('byt_prop','lagg_till_prop','flytta_prop','ta_bort_prop'):
                if e.get('tillgang_id') or e.get('faste'): raise EjTillampad('Endast statiska lådor stöds; tillgång eller handfäste är inte implementerat.')
                for s in valda(e):
                    if op=='lagg_till_prop':
                        if e['ny_id'] in s['objekt']: raise EjTillampad('Objekt-id finns redan.')
                        o=dict(id=e['ny_id'],namn='rum:'+e['typ']+':'+e['ny_id'],typ='lada',matt_m=storlek(e.get('matt_m')),
                               rotation_rad=[0,0,0],farg='#e2ac46',top_slope=0)
                        placera(s,o,e.get('plats'),e.get('stod')); s['objekt'][o['id']]=o
                    else:
                        o=hitta(s,e['prop'])
                        if op=='ta_bort_prop': del s['objekt'][e['prop']]
                        elif op=='flytta_prop':
                            if not e['till']: raise EjTillampad('Flytt kräver en explicit placering.')
                            placera(s,o,e['till'])
                        else:
                            o.update(namn='rum:'+e['ny_typ']+':'+e['prop'],farg='#e2ac46')
                            if e.get('matt_m') is not None: o['matt_m']=storlek(e['matt_m'])
                    andring[s['id']]=copy.deepcopy(o) if op!='ta_bort_prop' else dict(borttaget=e['prop'])
            elif op=='renderkamera':
                s=scen(e['scen']); s['kamera']=kameranycklar(e,s); s['kamera_edit']=e
                andring=dict(kallintervall=[s['a'],s['b']],lage=e['lage'],forsta_nyckel=s['kamera'][s['a']])
                if standard: andring['standardvarden']=copy.deepcopy(standard)
            else: raise EjTillampad('Operationen stöds inte av denna byggare.')
            tillampat.append(dict(id=e['id'],op=op,andring=andring))
        except (EjTillampad, ArithmeticError, KeyError, IndexError, TypeError, np.linalg.LinAlgError) as ex:
            # En trasig edit får aldrig avbryta hela kompileringen.
            scener,pers=fore; ej.append(dict(id=e['id'],op=op,orsak=str(ex) if isinstance(ex,EjTillampad) else f'Editen kunde inte tolkas ({type(ex).__name__}: {ex}).'))
    if not scener: raise ValueError('Alla scener togs bort; det finns inga rutor att rendera.')
    rutor, intervall, renderkamera, byggobjekt = [], [], [], []
    for s in scener:
        start=len(rutor); rutor.extend(range(s['a'],s['b'])); slut=len(rutor)
        intervall.append(dict(ut=[start,slut],kalla=[s['a'],s['b']],ljud=s['ljud']))
        renderkamera.extend(s['kamera'][s['a']:s['b']])
        for o in s['objekt'].values():
            o=copy.deepcopy(o); o['synlig_ut']=[start,slut]; byggobjekt.append(o)
    utdata=copy.deepcopy(R['utdata']); utdata.update(antal_rutor=len(rutor),render_motor='BLENDER_WORKBENCH',upplosning_procent=100,
                                                   bildformat='PNG',farglage='RGBA',transparent=True)
    return dict(schema_version='plan/1',koordinater='Blender: Z upp, meter, radianer; kameramatris world_from_camera, lokal -Z blick, Y upp.',
                tidskarta=intervall,kallrutor=rutor,personer=list(pers.values()),objekt=byggobjekt,
                renderkamera=dict(lage='upplosta_nycklar',sensor_bredd_mm=36,nycklar=renderkamera),
                utdata=utdata,matning=matning,kallvideo=str((kallfil.parent/K['klipp']['video']['sokvag']).resolve()),
                kallbild_bredd=K['klipp']['video']['bredd'],tillampat=tillampat,ej_tillampat=ej,varningar=varningar,
                beslut=['Halvbild = minst 1,25 m vertikalt utsnitt; huvudmål ligger 28 % över bildcentrum. Stativ vidgas för huvudets bana och rekvisita, med 25 cm sidomarginal.',
                        'Propbyte och tillägg visas som ockragula lådor; mått behålls om matt_m är null.',
                        'Ingen talersättning: blandat_duckad använder bara tidsmappat originalljud.'])


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('kalla'); p.add_argument('regi'); p.add_argument('ut'); a=p.parse_args()
    plan=kompilera(a.kalla,a.regi); skriv(a.ut,plan)
    for namn in ('tillampat','ej_tillampat'):
        print(namn)
        for e in plan[namn]: print(e['id'],e['op'],e.get('orsak',e.get('andring')))


if __name__=='__main__': main()
