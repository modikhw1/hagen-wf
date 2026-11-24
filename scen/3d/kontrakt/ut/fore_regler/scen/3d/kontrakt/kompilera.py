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
sys.path.insert(0, str(HIT.parent/'ingest'))
from rumsmall import byggobjekt as mallobjekt, las as las_mall, som_plats

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


def platsobjekt(pl):
    """Platsens golv, väggar och fasta objekt som byggobjekt. Platsen är redan i sitt eget koordinatsystem (Z upp), ingen gravitation behövs.
    Samma fält och ordning som rumobjekt, så identitetsfallet ger samma objekt som rum.json direkt."""
    if pl.get('rumsmall'): return {o['id']:o for o in mallobjekt(pl['rumsmall'])}
    objekt = [dict(id='golv', namn='golv', typ='plan', pos_m=[0, 0, pl['golv']['hojd_m']], rotation_rad=[0, 0, 0], matt_m=[40, 40, 0], farg='#5a554e', top_slope=0)]
    for w in pl['vaggar']:
        objekt.append(dict(id=w['id'], namn='rum:'+w['id'], typ='lada', pos_m=w['centrum_m'], rotation_rad=[0, 0, w['yaw_rad']],
                            matt_m=[w['bredd_m'], .01, w['hojd_m']], farg='#77716a', top_slope=0))
    for o in pl['objekt']:
        farg = '#347e77' if o['etikett'] == 'pool table' else '#a58b68' if o['etikett'] == 'bar counter' else '#777e87'
        objekt.append(dict(id=o['id'], namn='rum:'+o['etikett']+':'+o['id'], typ='lada', pos_m=o['centrum_m'], rotation_rad=[0, 0, o['yaw_rad']],
                            matt_m=o['matt_m'], farg=farg, top_slope=o.get('top_slope', 0)))
    return {o['id']: o for o in objekt}


def ankarpose(a):
    c, z = math.cos(a['riktning_rad']), math.sin(a['riktning_rad'])
    return np.array(transform(a['pos_m'], np.array([[c, -z, 0.], [z, c, 0.], [0., 0., 1.]])))


def kompilera(kallfil, regifil, platsbank=None):
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
    kameror = {k['id']: k for k in matning['kameror']}; rumfiler = {r['id']: r for r in matning['rum']}
    if not kameror or not rumfiler or any(s['kamera'] not in kameror or s['miljo'] not in rumfiler for s in K['semantik']['scener']):
        raise ValueError('Byggaren kräver en uppmätt kamera och ett rum för varje scen.')
    platsm = {p['id']: p for p in matning.get('platser', [])}; PL = {i: ladda(p['fil']['sokvag']) for i, p in platsm.items()}
    from tropassning import anpassa
    PL, benlangder, hojdpassning = anpassa(K, matning, PL)
    platsbank = Path(platsbank) if platsbank else HIT/'rumsmall'
    flerklipp = any(m.get('scen') for m in matning['personer'])   # mätningar per scen (kalla_flera.py); annars ett sammanhängande klipp
    N = K['tidsbas']['antal_rutor']
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
    pers = {p['id']: dict(id=p['id'], roll=p['roll'], farg=FARGER[i % len(FARGER)],
                         **({} if flerklipp else dict(rorelse=next(m['rorelse']['sokvag'] for m in matning['personer'] if m['person']==p['id']))))
            for i,p in enumerate(sorted(K['semantik']['personer'], key=lambda p:p['id']))}
    # Mätningen läses en gång per scen: kamera (varld.npz), personer och rum. kx pekar ut den i ktx så att scenerna kan kopieras billigt.
    ktx = {}; filcache = {}
    def laddad(fil):
        if fil not in filcache: filcache[fil] = dict(np.load(fil))
        return filcache[fil]
    def kontext(sk, Mover=None, platsover=None):
        kam = kameror[sk['kamera']]; V = laddad(kam['spar_metrisk']['sokvag']); G = gravitation(V); offs = kam.get('kalla_ruta0', 0)
        # Plats: transformen M tar tagningens Blender-värld (G @ mätvärld) in i platsen. G_eff = Rz G och T = translation; utan plats T = None.
        reg = next((r for r in platsm.get(sk.get('plats_id'), {}).get('registreringar', []) if r['scen'] == sk['id']), None) if sk.get('plats_id') else None
        M = Mover if Mover is not None else (np.array(reg['till_plats']['matris']) if reg else None); T = None; plats = platsover or (PL[sk['plats_id']] if reg else None)
        if reg and abs(reg['till_plats']['skala'] - 1.0) > 1e-9: raise ValueError('Platsens transform har skala utom 1,0; byggaren stöder bara 1,0.')
        if M is not None and not flerklipp and not np.allclose(M, np.eye(4)): raise ValueError('En plats-transform som inte är identitet kräver flera tagningar (scener i planen).')
        if M is not None: G = M[:3, :3] @ G; T = M[:3, 3]
        pt = (lambda x: G @ x) if T is None else (lambda x: G @ x + T)
        ms = [m for m in matning['personer'] if m.get('scen') in (None, sk['id'])]
        seq = {m['person']: laddad(m['rorelse']['sokvag']) for m in ms}
        # Ett sammanhängande klipp mäts över hela tidsbasen; i flerklippsfallet över scenens egna rutor.
        antal = N if 'kalla_ruta0' not in kam else ruta(sk['slut_s']) - ruta(sk['start_s'])
        if 'kalla_ruta0' in kam and offs != ruta(sk['start_s']): raise ValueError(f'kalla_ruta0 för {kam["id"]} stämmer inte med scenens start.')
        if len(V['kam_R']) != antal: raise ValueError('Kamerans bildantal avviker från tidsbasen.')
        for pid, s in seq.items():
            if len(s['pose']) != antal or len(s['inom']) != antal: raise ValueError('Fel bildantal för person ' + pid)
        objekt = platsobjekt(plats) if plats is not None else rumobjekt(ladda(rumfiler[sk['miljo']]['fil']['sokvag']), G)
        # Semantiska prop-id kan skilja från mätningens objekt-id.
        for p in K['semantik']['props']:
            if p.get('scen') in (None, sk['id']) and p['rum_ref'] in objekt and p['id'] != p['rum_ref']:
                o=objekt.pop(p['rum_ref']); o['id']=p['id']; objekt[p['id']]=o
        spar = [dict(matris=transform(pt(V['kam_C'][i]), G @ V['kam_R'][i] @ F),
                     lins_mm=float(next(iter(seq.values()))['fokal']) * 36 / K['klipp']['video']['bredd']) for i in range(antal)]
        kalibrering = None
        if flerklipp and seq:
            # Golvsteget skalade bara cam_t, inte kroppen. Återställ projektionen
            # med motsvarande kameraförskjutning; uppmätta personer och rum står kvar.
            huvud = next((pid for pid in seq if pers[pid]['roll'] is not None), next(iter(seq)))
            S = seq[huvud]
            if 'cam_t_fore_golv' in S and 'ben_synliga' in S and not np.any(S['ben_synliga']):
                delta = S['cam_t'] - S['cam_t_fore_golv']
                for i in range(antal):
                    corr = G @ V['kam_R'][i] @ delta[i]
                    key = np.array(spar[i]['matris']); key[:3,3] += corr; spar[i]['matris'] = key.tolist()
                kalibrering = dict(status='uppmatt',person=huvud,metod='Kamerans translation kompenserar golvstegets cam_t-skala. Brännvidd och rotation oförändrade; personposer och platsläge orörda.',
                                   forskjutning_median_m=float(np.median(np.linalg.norm(delta,axis=1))),fokal_px=float(S['fokal']))
        return dict(V=V, G=G, T=T, M=M, tagning=reg['tagning'] if reg else None, plats=plats, plats_id=plats['id'] if plats is not None else None, offs=offs, ms=ms, seq=seq, objekt=objekt, spar=spar,kalibrering=kalibrering)
    scener = []
    for s in K['semantik']['scener']:
        ktx[s['id']] = c = kontext(s)
        scener.append(dict(id=s['id'], a=ruta(s['start_s']), b=ruta(s['slut_s']), ursprung=s['id'], kx=s['id'],
                           objekt=copy.deepcopy(c['objekt']), kamera=copy.deepcopy(c['spar']), ljud=True))
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
        lage=e['lage']; a,b=s['a'],s['b']; c=ktx[s['kx']]; V,G,seq,spar,offs=c['V'],c['G'],c['seq'],c['spar'],c['offs']; resultat=copy.deepcopy(spar)
        T=c['T']; pt=(lambda x: G @ x) if T is None else (lambda x: G @ x + T); ny=(lambda x: G @ x) if T is None else (lambda x: x)   # nyckelbilder: platsens koordinater direkt
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
            for f in range(a-offs,b-offs):
                t=(f-(a-offs))/float(fps); left=max((k for k in keys if k['t_s']<=t),key=lambda k:k['t_s'],default=keys[0]); right=next((k for k in keys if k['t_s']>=t),keys[-1])
                w=0 if left is right else (t-left['t_s'])/(right['t_s']-left['t_s'])
                pos=ny((1-w)*np.array(left['pos_m'])+w*np.array(right['pos_m'])); mal=ny((1-w)*np.array(left['mal_m'])+w*np.array(right['mal_m']))
                resultat[f]=nyckel(pos,mal,(1-w)*left['fov_grader']+w*right['fov_grader'])
        else:
            mal=e.get('mal'); pos=pt(V['kam_C'][a-offs]); punkter=[]
            if mal and mal['typ']=='person':
                if mal['id'] not in seq: raise EjTillampad('Personmålet saknar rörelse.')
                punkt=mal.get('punkt')
                if punkt is None: punkt='kropp'; standard.append(dict(falt='mal.punkt',varde='kropp (c_spine2)',orsak='CM angav ingen målpunkt'))
                namn={'huvud':'c_head', 'kropp':'c_spine2'}.get(punkt)
                if namn is None: raise EjTillampad('Okänd målpunkt på person.')
                S=seq[mal['id']]; i=lednamn.index(namn)
                punkter=[pt(V['kam_C'][f]+V['kam_R'][f] @ (F @ (S['pose'][f,i,:3]/100)+S['cam_t'][f]))
                         for f in range(a-offs,b-offs) if S['inom'][f]]
                if not punkter: raise EjTillampad('Personmålet är inte synligt i scenen.')
                target=np.median(punkter,axis=0)
            elif mal and mal['typ']=='prop': target=np.array(hitta(s,mal['id'])['pos_m'])
            elif mal: raise EjTillampad('Punktmål saknar numeriska koordinater; använd nyckelbilder.')
            else:
                target=pos + G @ V['kam_R'][a-offs] @ [0.,0.,1.]
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
                    # I en plats ryms bara de objekt som tagningen själv har sett (annars backar kameran för bord vid andra änden av rummet).
                    sedd=c['plats'] is None or c['tagning'] is None or any(o['id']==prop['id'] and any(x['tagning']==c['tagning'] for x in o.get('observationer',[])) for o in c['plats']['objekt'])
                    if prop['id'] in s['objekt'] and sedd:
                        o=s['objekt'][prop['id']]; punkter.append(np.array(o['pos_m']))
                for punkt in punkter:
                    x,y,z=rot.T @ (punkt-target)
                    avstand=max(avstand,z+(abs(x)+.25)/th,z+(abs(y)+.2)/tv)
                pos=target+riktning*avstand
            key=nyckel(pos,target,fov)
            for f in range(a-offs,b-offs): resultat[f]=copy.deepcopy(key)
        return resultat
    tal_vantar = {}   # edit-id -> post; platsen i utdata avgörs först när alla scenedits är gjorda
    def talbyte(e):
        if not K['semantik']['repliker']: raise EjTillampad('Talersättning ingår inte; barkällan saknar kända repliker.')
        r = next((x for x in K['semantik']['repliker'] if x['id'] == e['replik']), None)
        if r is None: raise EjTillampad('Repliken finns inte i kalla' + (' (platshållare-id).' if e['replik'].startswith('PLATSHALLARE:') else ': ' + e['replik'] + '.'))
        if e['sprak'] != 'sv': raise EjTillampad(f'Piper-rösterna är svenska; språket {e["sprak"]!r} stöds inte.')
        if (e['rost'] or {}).get('motor') not in (None, 'piper'): raise EjTillampad('Bara röstmotorn piper stöds.')
        if e['tidspolicy'] != 'samma_lucka': raise EjTillampad('forlang_scen stöds inte: scenen förlängs inte för en ny text. Använd samma_lucka.')
        if not e['text'].strip() or e['text'] == r['text']: raise EjTillampad('Den nya texten är tom eller densamma som originalets.')
        roll = next((p['roll'] for p in K['semantik']['personer'] if p['id'] == r['talare']), None)
        try:
            import tal
            rost = (e['rost'] or {}).get('rost_id') or tal.standardrost(roll)
            lucka = round(r['slut_s'] - r['start_s'], 4)
            nat_o, nat_n = tal.mat_langd(rost, r['text']), tal.mat_langd(rost, e['text'])
        except Exception as ex:   # Piper eller röstfil saknas: editen avslås, kompileringen fortsätter
            raise EjTillampad(f'Talsyntesen kan inte köras här ({type(ex).__name__}: {ex}).')
        grans = e['max_talfaktor'] or R['ramar']['max_talfaktor'] or 1.15
        rel = nat_n / nat_o; procent = round((rel - 1) * 100, 1)
        if rel > grans: raise EjTillampad(f'Nekad: den nya texten ({nat_n:.2f} s i normaltempo mot originalets {nat_o:.2f} s) kräver {procent} % högre taltakt än originalet i samma lucka ({lucka:.2f} s); gränsen är {round((grans-1)*100,1)} %.')
        utfall = 'passar' if rel <= 1.03 else 'stracks'
        x, ls, tempo = tal.passa(rost, e['text'], lucka)
        langd = round(len(x) / tal.SR, 4)
        tecken = [max(1, len(w)) for w in e['text'].split()]; summa = sum(tecken); t0 = 0.0; ord_ny = []
        for w, n in zip(e['text'].split(), tecken):
            ord_ny.append(dict(ord=w, start_rel_s=round(t0, 4), slut_rel_s=round(t0 + lucka * n / summa, 4))); t0 += lucka * n / summa
        post = dict(edit=e['id'], replik=r['id'], talare=r['talare'], rost=dict(motor='piper', rost_id=rost), text=e['text'], text_original=r['text'],
                    kalla_slot_s=[r['start_s'], r['slut_s']], slot_langd_s=lucka, naturlig_original_s=nat_o, naturlig_ny_s=nat_n,
                    taktfaktor_mot_original=round(rel, 4), utfall=utfall, stracka_procent=max(0.0, procent), length_scale=round(ls, 4), extra_tempo=round(max(1.0, tempo), 4),
                    syntetiserad_langd_s=langd, ord_ny=ord_ny, ord_ny_kalla='uppskattade efter teckenlängd (som op.py), inte mätta')
        tal_vantar[e['id']] = post
        return dict(replik=r['id'], utfall=utfall, stracka_procent=post['stracka_procent'], slot_langd_s=lucka, naturlig_ny_s=nat_n, naturlig_original_s=nat_o)
    for e in R['edits']:
        # En edit är atomisk: även ett fel i den sista scenen rullar tillbaka hela editen.
        fore=copy.deepcopy((scener,pers)); op=e['op']; andring={}; standard.clear()
        try:
            if e['ursprung']['typ']=='harness-forslag' and e['ursprung'].get('godkand_av_cm') is not True:
                raise EjTillampad('Harnessförslaget är inte godkänt av CM.')
            if op=='lagg_till_replik': raise EjTillampad('Att lägga till repliker ingår inte; barkällan saknar kända repliker.' if not K['semantik']['repliker'] else 'Att lägga till repliker ingår inte.')
            if op=='byt_replik': andring=talbyte(e)
            elif op=='casta':
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
            elif op=='byt_miljo':
                # Platsbyte: ersätt platsens geometri, behåll ankarnas namn. Personerna följer sina ankare: scenens transform räknas om så att
                # det bundna ankaret i källplatsen hamnar på samma namn i den nya platsen. Banken är en mapp med plats-JSON (plats/1).
                mallid=e['rum'].get('rumsmall_id') or e['rum'].get('tillgang_id')
                if e['rum']['kalla']!='bank' or not mallid: raise EjTillampad('Bara kalla=bank med tillgang_id eller rumsmall_id stöds; övriga källor kräver en färdig mall.')
                bf=platsbank/(mallid+'.json')
                if not bf.is_file(): raise EjTillampad(f'Platsen {mallid!r} finns inte i platsbanken ({platsbank}).')
                raw=ladda(bf)
                if 'rumsmall_ref' in raw: bf=(bf.parent/raw['rumsmall_ref']).resolve(); raw=ladda(bf)
                try:
                    if raw.get('schema_version')=='rumsmall/1':
                        mall,hash_mall=las_mall(bf);ny=som_plats(mall);ny['rumsmall']['sha256']=hash_mall
                    else: ny=raw
                except ValueError as fel: raise EjTillampad('Ogiltig rumsmall: '+str(fel)) from fel
                karta={a['fran']:a['till'] for a in e.get('ankare',[])}; nyank={a['id']:a for a in ny['ankare']}
                for s in valda(e):
                    c=ktx[s['kx']]
                    if c['plats'] is None: raise EjTillampad(f'Scenen {s["id"]} har ingen plats; byt_miljo gäller platser med ankare.')
                    ksc=next(x for x in K['semantik']['scener'] if x['id']==s['ursprung']); gamla={a['id']:a for a in c['plats']['ankare']}
                    for bind in ksc.get('bindningar',[]):
                        aid=karta.get(bind['ankare'],bind['ankare'])
                        if aid not in nyank: raise EjTillampad(f'Scenen {s["id"]}: ingen bunden person kan följa med utan ankaret {aid}.')
                        if nyank[aid]['typ']!=gamla[bind['ankare']]['typ']: raise EjTillampad(f'Ankaret {aid} har fel typ i kundmallen.')
                    val=next(((b,karta.get(b['ankare'],b['ankare'])) for b in sorted(ksc.get('bindningar',[]),key=lambda b:b['person']) if b['ankare'] in gamla and karta.get(b['ankare'],b['ankare']) in nyank),None)
                    if val is None: raise EjTillampad(f'Scenen {s["id"]}: ingen bunden person har ett ankare med motsvarande namn i {ny["id"]}; personerna kan inte följa med.')
                    b,till=val; Mn=ankarpose(nyank[till])@np.linalg.inv(ankarpose(gamla[b['ankare']]))@c['M']
                    nyckel=f'{s["id"]}#{e["id"]}'; ktx[nyckel]=nc=kontext(ksc,Mover=Mn,platsover=ny)
                    nc['ankarkarta']=karta
                    nc['person_transformer']={bind['person']:(ankarpose(nyank[karta.get(bind['ankare'],bind['ankare'])])@np.linalg.inv(ankarpose(gamla[bind['ankare']]))@c.get('person_transformer',{}).get(bind['person'],c['M'])).tolist() for bind in ksc.get('bindningar',[])}
                    s['kx']=nyckel; s['objekt']=copy.deepcopy(nc['objekt']); s['kamera']=copy.deepcopy(nc['spar'])
                    if s.get('kamera_edit'): s['kamera']=kameranycklar(s['kamera_edit'],s)
                    andring[s['id']]=dict(plats_fran=c['plats']['id'],plats_till=ny['id'],ref_person=b['person'],ankare_fran=b['ankare'],ankare_till=till,
                                          ankare_utan_motsvarighet=[i for i in gamla if karta.get(i,i) not in nyank])
            elif op=='renderkamera':
                s=scen(e['scen']); s['kamera']=kameranycklar(e,s); s['kamera_edit']=e
                andring=dict(kallintervall=[s['a'],s['b']],lage=e['lage'],forsta_nyckel=s['kamera'][s['a']-ktx[s['kx']]['offs']])
                if standard: andring['standardvarden']=copy.deepcopy(standard)
            else: raise EjTillampad('Operationen stöds inte av denna byggare.')
            tillampat.append(dict(id=e['id'],op=op,andring=andring))
        except (EjTillampad, ArithmeticError, KeyError, IndexError, TypeError, np.linalg.LinAlgError) as ex:
            # En trasig edit får aldrig avbryta hela kompileringen.
            scener,pers=fore; ej.append(dict(id=e['id'],op=op,orsak=str(ex) if isinstance(ex,EjTillampad) else f'Editen kunde inte tolkas ({type(ex).__name__}: {ex}).'))
    if not scener: raise ValueError('Alla scener togs bort; det finns inga rutor att rendera.')
    rutor, intervall, renderkamera, byggobjekt, delplan = [], [], [], [], []
    iv_ut={}; platsmodus=all(ktx[s['kx']]['plats'] is not None for s in scener)
    for s in scener:
        start=len(rutor); rutor.extend(range(s['a'],s['b'])); slut=len(rutor)
        intervall.append(dict(ut=[start,slut],kalla=[s['a'],s['b']],ljud=s['ljud']))
        if flerklipp:
            c=ktx[s['kx']]
            delplan.append(dict(id=s['id'],ut=[start,slut],kalla=[s['a'],s['b']],lokal_start=s['a']-c['offs'],
                                varld=kameror[next(x['kamera'] for x in K['semantik']['scener'] if x['id']==s['ursprung'])]['spar_metrisk']['sokvag'],
                                personer=[dict(id=m['person'],ingest_id=m.get('ingest_id'),rorelse=m['rorelse']['sokvag']) for m in c['ms']]))
            if c['M'] is not None: delplan[-1].update(plats_id=c['plats_id'],till_plats=c['M'].tolist())
            if c['plats'] and c['plats'].get('rumsmall'):
                sk=next(x for x in K['semantik']['scener'] if x['id']==s['ursprung'])
                bind={x['person']:x for x in sk.get('bindningar',[])}
                an={a['id']:a for a in c['plats']['rumsmall']['ankare']}
                behall=[]; uteslut=[]
                for pm in delplan[-1]['personer']:
                    b=bind.get(pm['id']); aid=c.get('ankarkarta',{}).get(b['ankare'],b['ankare']) if b else None
                    if b and aid in an:
                        pm['stod']=copy.deepcopy(an[aid]);pm['ankare']=aid
                        if pm['id'] in benlangder: pm['benlangder_m']=benlangder[pm['id']]
                        syn=next((v for v in c['plats']['golv'].get('matning',{}).get('fotsynlighet',[])
                                  if v['tagning']==c['tagning'] and v['ingest_id']==pm.get('ingest_id')),None)
                        if syn:
                            skydd={str(v['ruta']):v['synliga_knan'] for v in syn['per_ruta'] if any(v.get('synliga_knan',[]))}
                            if skydd:pm['skyddade_knan']=skydd
                        if pm['id'] in c.get('person_transformer',{}) and not np.allclose(c['person_transformer'][pm['id']],c['M'],atol=1e-10):pm['till_plats']=c['person_transformer'][pm['id']]
                        behall.append(pm)
                    elif pers[pm['id']]['roll'] is None:
                        uteslut.append(dict(person=pm['id'],orsak='Ingen roll eller bunden mallsits inom platsstegets tolerans. Renderas inte utan stöd.'))
                    else: behall.append(pm)
                delplan[-1]['personer']=behall;delplan[-1]['utelamnade']=uteslut
        renderkamera.extend(s['kamera'][s['a']-ktx[s['kx']]['offs']:s['b']-ktx[s['kx']]['offs']])
        iv_ut[s['id']]=[start,slut]
        if not platsmodus:
            for o in s['objekt'].values():
                o=copy.deepcopy(o); o['synlig_ut']=[start,slut]
                if flerklipp: o['scen']=s['id']
                byggobjekt.append(o)
    if platsmodus:
        # Platsens rum byggs en gång: ett objekt som finns oförändrat i alla scener syns hela tiden; annars läggs det scen för scen.
        for i in dict.fromkeys(i for s in scener for i in s['objekt']):
            fk=[(s,s['objekt'][i]) for s in scener if i in s['objekt']]
            if len(fk)==len(scener) and all(o==fk[0][1] for _,o in fk):
                o=copy.deepcopy(fk[0][1]); o['synlig_ut']=[0,len(rutor)]; byggobjekt.append(o)
            else:
                for s,o in fk:
                    o=copy.deepcopy(o); o['synlig_ut']=list(iv_ut[s['id']])
                    if flerklipp: o['scen']=s['id']
                    byggobjekt.append(o)
    # Ersättningsreplikernas plats i utdata. En replik får bara bytas om luckan ligger hel inom en sammanhängande, ljudsatt bit av utdata.
    korn = []
    for iv in intervall:
        if korn and korn[-1]['ljud'] == iv['ljud'] and korn[-1]['kalla'][1] == iv['kalla'][0] and korn[-1]['ut'][1] == iv['ut'][0]:
            korn[-1]['kalla'][1] = iv['kalla'][1]; korn[-1]['ut'][1] = iv['ut'][1]
        else: korn.append(dict(ut=list(iv['ut']), kalla=list(iv['kalla']), ljud=iv['ljud']))
    tal_plan = []; ordning = {e['id']: i for i, e in enumerate(R['edits'])}; senaste = {}
    for eid, post in tal_vantar.items(): senaste[post['replik']] = eid
    for eid, post in tal_vantar.items():
        ap = next(x for x in tillampat if x['id'] == eid); orsak = None; platser = []
        if senaste[post['replik']] != eid: orsak = f'Ersatt av den senare editen {senaste[post["replik"]]} på samma replik.'
        else:
            s0, s1 = post['kalla_slot_s']
            for kb in korn:
                if kb['ljud'] and kb['kalla'][0] / float(fps) <= s0 + 1e-6 and s1 <= kb['kalla'][1] / float(fps) + 1e-6:
                    platser.append(round(kb['ut'][0] / float(fps) + (s0 - kb['kalla'][0] / float(fps)), 4))
            if not platser: orsak = 'Luckan ligger inte hel i utdata: scenen är bortklippt eller trimmad, ligger i en tyst scen, eller klipps mitt i luckan av en scengräns som inte längre är sammanhängande.'
        if orsak:
            tillampat.remove(ap); ej.append(dict(id=eid, op='byt_replik', orsak=orsak))
        else:
            for u0 in platser: tal_plan.append(dict(post, ut_slot_s=[u0, round(u0 + post['slot_langd_s'], 4)]))
            ap['andring']['ut_slot_s'] = [[u0, round(u0 + post['slot_langd_s'], 4)] for u0 in platser]
    tillampat.sort(key=lambda x: ordning[x['id']]); ej.sort(key=lambda x: ordning[x['id']])
    utdata=copy.deepcopy(R['utdata']); utdata.update(antal_rutor=len(rutor),render_motor='BLENDER_WORKBENCH',upplosning_procent=100,
                                                   bildformat='PNG',farglage='RGBA',transparent=True)
    plan=dict(schema_version='plan/1',koordinater='Blender: Z upp, meter, radianer; kameramatris world_from_camera, lokal -Z blick, Y upp.',
                tidskarta=intervall,kallrutor=rutor,personer=list(pers.values()),objekt=byggobjekt,
                renderkamera=dict(lage='upplosta_nycklar',sensor_bredd_mm=36,nycklar=renderkamera),
                utdata=utdata,matning=matning,kallvideo=str((kallfil.parent/K['klipp']['video']['sokvag']).resolve()),
                kallbild_bredd=K['klipp']['video']['bredd'],tillampat=tillampat,ej_tillampat=ej,varningar=varningar,
                beslut=['Halvbild = minst 1,25 m vertikalt utsnitt; huvudmål ligger 28 % över bildcentrum. Stativ vidgas för huvudets bana och rekvisita, med 25 cm sidomarginal.',
                        'Propbyte och tillägg visas som ockragula lådor; mått behålls om matt_m är null.',
                        'Ingen talersättning: blandat_duckad använder bara tidsmappat originalljud.'])
    if platsmodus:
        anv={ktx[s['kx']]['plats']['id']:ktx[s['kx']]['plats'] for s in scener}
        plan['plats']=[dict(id=i,golv_hojd_m=pl['golv']['hojd_m'],ankare=pl['ankare'],objekt=[o['id'] for o in pl['objekt']],scener=[s['id'] for s in scener if ktx[s['kx']]['plats']['id']==i])
                        for i,pl in anv.items()]
        for p in plan['plats']:
            pl=anv[p['id']]
            if pl.get('rumsmall'):
                p['rumsmall']=copy.deepcopy(pl['rumsmall']);p['ankare']=copy.deepcopy(pl['rumsmall']['ankare'])
                p['uppmatta_ankare']=copy.deepcopy(pl['ankare']);p['utelamnade']=copy.deepcopy(pl.get('utelamnade',[]))
        if any(pl.get('rumsmall') for pl in anv.values()):
            plan['beslut'].append('Rumsmall: djupfragment är enbart evidens. Mallens delar byggs en gång. Stöd begränsar bara osynliga ben; uppmätt överkropp och synliga ben lämnas exakt oförändrade.')
            if not flerklipp:
                pl=next(iter(anv.values()));an={a['id']:a for a in pl['rumsmall']['ankare']}
                bind={b['person']:b for s in K['semantik']['scener'] for b in s.get('bindningar',[])}
                for pm in plan['personer']:
                    if pm['id'] in bind and bind[pm['id']]['ankare'] in an:
                        pm['stod']=copy.deepcopy(an[bind[pm['id']]['ankare']])
                        if pm['id'] in benlangder: pm['benlangder_m']=benlangder[pm['id']]
        plan['beslut'].append('Platsen: rummet byggs en gång i platsens koordinater; varje scens personer och kamera flyttas in med scenens transform (yaw + translation, skala 1,0). Transformernas ursprung och säkerhet står i kalla.matning.platser[].registreringar.')
    if flerklipp:
        # Flerklippsplan: varje scen har egna mätfiler (scener) och talersättningarna ligger i tal. Bar (ett klipp) får inga av dessa nycklar.
        plan['scener']=delplan; plan['tal']=tal_plan
        plan['beslut'][2]=('Talersättning: ersatta repliker syntetiseras med Piper (bygg_ljud.py) och läggs i sina luckor i utdatatiden; originaltalet i luckan tas bort helt (tal och ljudbädd går inte att skilja). Övrigt originalljud är tidsmappat.' if tal_plan
                           else 'Ingen talersättning: blandat_duckad använder bara tidsmappat originalljud.')
        if not platsmodus: plan['beslut'].append('Varje scen har egen uppmätt kamera och eget rum i eget världssystem; tagningarna är inte registrerade mot varandra.')
        plan['beslut'].append('Munnen följer inte ny text (uttryck/expr används inte av MHR-renderaren).')
    # Kontrollera alltid mätkameran före CM-edits, även för klippta/kopierade scener.
    plan['kallbild_hojd']=K['klipp']['video']['hojd']
    matnycklar=[]
    for s in scener:
        c=ktx[s['kx']];matnycklar.extend(c['spar'][s['a']-c['offs']:s['b']-c['offs']])
    plan['matkamera']=dict(sensor_bredd_mm=36,nycklar=matnycklar)
    if not flerklipp:
        plan['matkamera']['scener']=[dict(id=s['id'],ut=iv_ut[s['id']],lokal_start=s['a'],
                                        varld=kameror[next(sk['kamera'] for sk in K['semantik']['scener'] if sk['id']==s['ursprung'])]['spar_metrisk']['sokvag'],personer=plan['personer']) for s in scener]
    from trohet import mat
    plan['kvalitet']=dict(bildtrohet=mat(plan),hojdpassning=hojdpassning,
                         kamerakalibrering=[dict(scen=s['id'],**ktx[s['kx']]['kalibrering']) for s in scener if ktx[s['kx']]['kalibrering']])
    from kvalitet import komplettera
    komplettera(plan, PL)
    if plan['kvalitet']['bildtrohet']['flaggad']:
        plan['varningar'].append('Bildtrohet överskrider egna diagnostiska trösklar. Se kvalitet.bildtrohet; render kräver uttryckligt granskningsläge.')
    return plan


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('kalla'); p.add_argument('regi'); p.add_argument('ut'); p.add_argument('--platsbank',help='mapp med plats-JSON för byt_miljo (standard: plats_bank/)'); a=p.parse_args()
    plan=kompilera(a.kalla,a.regi,a.platsbank); skriv(a.ut,plan)
    from trohet import rapport
    rapport(plan,a.ut)
    for namn in ('tillampat','ej_tillampat'):
        print(namn)
        for e in plan[namn]: print(e['id'],e['op'],e.get('orsak',e.get('andring')))


if __name__=='__main__': main()
