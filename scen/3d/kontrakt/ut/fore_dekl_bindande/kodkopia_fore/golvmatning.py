"""Golvbeslut av befintliga mätningar. Inga ingeststeg eller nätanrop.

Intervall för möbler och knävinkel är uttryckliga priorer. Ett modellgolv
är en djupskattning, inte en oberoende inmätning av meterskalan.
"""
import numpy as np
from pathlib import Path
import json

TOLERANS_M = .10  # Egen diagnostisk tolerans mellan cues, inte ett mätkrav.
PRIORER = dict(bord_m=[.72, .76], sits_m=[.43, .48],
               backen_over_sits_m=[.02, .15], kamera_m=[1.20, 1.70],
               kna_sankning_m=[0., .12])


def cue(namn, varde, spridning, familj, direkt=False, **extra):
    return dict(cue=namn, varde_m=float(varde), spridning_m=float(spridning),
                intervall_m=[float(varde-spridning), float(varde+spridning)],
                familj=familj, direkt=bool(direkt), **extra)


def kombinera(cues, tolerans=TOLERANS_M):
    """Välj starkaste cue-familjen. Behåll alla rester, även avvisade cues."""
    cues = [dict(c) for c in cues]
    ordning = {'fotter':0, 'sits':1, 'djup':2, 'bord':3, 'kropp':4, 'kamera':5}
    bra = [c for c in cues if c.get('anvandbar',True)]
    if not bra:
        return dict(status='antagen',orsak='Ingen användbar cue.',varde_m=None,
                    spridning_m=None,spann_m=None,konflikt=True,cues=cues)
    rank = min(ordning.get(c['familj'],4) for c in bra)
    selected = [c for c in bra if ordning.get(c['familj'],4)==rank]
    # En person i en tagning får en röst oavsett antal kontaktbilder.
    groups = {}
    for c in selected:
        groups.setdefault((c.get('tagning'),c.get('ingest_id',c['cue'])),[]).append(c['varde_m'])
    value = float(np.median([np.median(v) for v in groups.values()]))
    spread = float(max(abs(c['varde_m']-value)+c['spridning_m'] for c in selected))
    nonprior = [c for c in bra if c['familj']!='kamera'] or bra
    span = float(np.ptp([c['varde_m'] for c in nonprior]))
    for c in cues:
        c['anvand'] = c in selected
        c['rest_m'] = float(c['varde_m']-value)
        c['beslut'] = ('använd: starkaste cue-familjen' if c['anvand'] else
                       c.get('orsak','avvisad: svagare cue-familj; avvikare redovisas'))
    status = ('uppmatt' if all(c['direkt'] and c.get('status')!='modellbedomd' for c in selected)
              else 'modellbedomd' if rank in (0,2) else 'antagen')
    return dict(varde_m=value,spridning_m=spread,spann_m=span,konflikt=span>tolerans,
                tolerans_m=tolerans,status=status,
                orsak=('Endast kamerahöjdens prior finns.' if rank==5 else
                       'Starkaste tillgängliga cue-familj: '+selected[0]['familj']+'. Svagare cues ändrar inte golvet.'),cues=cues)


def fotkontroll(d, pid, meta):
    """MHR70: knä 11/12, vrist 13/14, tå/häl 15–20. Masken är en UNION.

    Därför krävs även personens egen ruta. Synlighet på en annan persons
    mask räcker inte. Bara sparade tillförlitliga rutor räknas.
    """
    d=Path(d); masks=np.load(d/'masker.npy', mmap_mode='r') if (d/'masker.npy').exists() else None
    palfile=d/f'palitlig_{pid}.json';pal=json.loads(palfile.read_text(encoding='utf-8')) if palfile.exists() else {}
    rows=[];accepted=[];points=[]
    for f in sorted((d/'kropp'/str(pid)).glob('*.npz')):
        i=int(f.stem)
        with np.load(f) as b:
            kp=b['pred_keypoints_2d'];bb=b['bbox'];sides=[];knees=[]
            for ids in ([11,13,15,16,17],[12,14,18,19,20]):
                q=kp[ids];inside=(q[:,0]>=max(0,bb[0]))&(q[:,0]<min(meta['bredd'],bb[2]))&(q[:,1]>=max(0,bb[1]))&(q[:,1]<min(meta['hojd'],bb[3]))
                hit=np.zeros(len(ids),bool)
                if masks is not None:
                    xx=np.clip((q[:,0]*masks.shape[2]/meta['bredd']).astype(int),0,masks.shape[2]-1)
                    yy=np.clip((q[:,1]*masks.shape[1]/meta['hojd']).astype(int),0,masks.shape[1]-1)
                    hit=masks[i,yy,xx].astype(bool)&inside
                # Knä och vrist samt två av tå/hälpunkterna måste stödjas.
                sides.append(bool(hit[0] and hit[1] and hit[2:].sum()>=2))
                knees.append(bool(hit[0] and pal.get(str(i),True)))
            ok=any(sides) and pal.get(str(i),True)
            rows.append(dict(ruta=i,anvandbar=bool(ok),sidor=sides,synliga_knan=knees,
                             fotpunkter_i_bbox=int(((kp[13:21,1]>=bb[1])&(kp[13:21,1]<bb[3])&(kp[13:21,0]>=bb[0])&(kp[13:21,0]<bb[2])).sum())))
            if ok: accepted.append(i)
    return dict(ingest_id=str(pid),rutor=len(rows),anvandbara_rutor=accepted,per_ruta=rows,
                orsak='Mask + egen bbox + knä/vrist/tå eller häl + tillförlitlighet krävs. Ingests 13–14 är vrist, inte knä. Fötter utanför dessa stöd används inte som mätning.')


def undersok(tagningar, reg, roller):
    """Alla värden i samma redan registrerade platsram, före golvbeslutet."""
    from trohet import IX, F, las_sekvens
    from trostod import begransa, matt
    shots=[];role_obs={};visibility=[]
    for t in tagningar:
        M=reg[t['id']]['M'];floor=t['golv']['hojd_m'];old=float(floor+M[2,3]);cues=[]
        r=t['rum']['floor'];height=r.get('measured_height')
        if height is not None:
            # RANSAC använder 5 cm planavstånd; spridningen sparades inte.
            # 5 cm + lutningsosäkerhet är ett antaget felintervall, inte SEM.
            spread=.05+min(.10,abs(np.tan(np.radians(r.get('normal_angle_deg') or 0)))*.5)
            cues.append(cue('djupgolv',height+M[2,3],spread,'djup',False,
                            stodpunkter=r.get('support'),osakerhet='Antaget felintervall: 5 cm RANSAC + lutning över 0,5 m. Monokulärt modelldjup.'))
        camera_z=float(np.median((t['V']['kam_C']@t['G'].T)[:,2]))
        cues.append(cue('kamerahöjd 1,45 m',camera_z-1.45+M[2,3],.25,'kamera',False,prior=True,prior_intervall_m=PRIORER['kamera_m']))
        for pid,pp in t['personer'].items():
            S=las_sekvens(t['mapp']/f'sekvens_{pid}.npz');frames=np.flatnonzero(S['inom']);V=t['V'];G=M[:3,:3]@t['G']
            Q=np.einsum('ij,njk,kl->nil',G,V['kam_R'][frames],F)
            T=(V['kam_C'][frames]+np.einsum('nij,nj->ni',V['kam_R'][frames],S['cam_t'][frames]))@G.T+M[:3,3]
            X=np.einsum('nij,ntj->nti',Q,S['pose'][frames,:,:3]/100)+T[:,None]
            vis=fotkontroll(t['mapp'],pid,t['meta']);visibility.append(dict(tagning=t['id'],**vis))
            # Per sida: synlig och tillförlitlig i rutan, och låg vertikal fart för
            # just den sidans tå. En dold fot får varken avvisa eller ge ett värde.
            side_by_frame={v['ruta']:(v['sidor'] if v['anvandbar'] else [False,False]) for v in vis['per_ruta']}
            feet=[]
            for side,s in enumerate('lr'):
                z=X[:,IX[s+'_ball'],2];speed=np.r_[np.inf,np.abs(np.diff(z))]
                for j,f in enumerate(frames):
                    if side_by_frame.get(int(f),[False,False])[side] and speed[j]<=.01 and j>0 and frames[j]==frames[j-1]+1:
                        feet.append((int(f),z[j]-.025))
            if feet:
                # Tåleden + antagen 2,5 cm sula; per ruta lägsta synliga sida.
                per={}
                for f,z in feet:per[f]=min(z,per.get(f,np.inf))
                feet=np.array(list(per.values()))
                cues.append(cue('synliga fötter '+pid,np.median(feet),max(.03,float(np.ptp(np.percentile(feet,[10,90]))/2)),
                                'fotter',False,status='modellbedomd',ingest_id=pid,rutor=len(feet),sula_prior_m=.025))
            hip=float(np.median(X[:,IX['root'],2]));role=roller[(t['id'],pid)]
            # GOLV2 punkt 2: sittande kräver stöd i semantikens hållning OCH en
            # identifierad sitstyp. Låg modellhöft, dolda ben eller ett bord är
            # inte bevis för en stol. Sitsprioren gäller bara vanlig stol.
            placering=pp.get('semantisk_placering') or {}
            seated=placering.get('hallning')=='sitter'
            sitstyp=placering.get('sitstyp')
            if seated and not role.startswith('okand_'):
                # Lägsta fasta horisontella lårpose ger ett intervall, inte krav på sträckta ben.
                lengths=matt(S['pose'][frames])
                body=float(np.median(X[:,[IX['l_upleg'],IX['r_upleg']],2]))-float(np.mean([lengths[IX[s+'_foot']] for s in 'lr']))-.08-.06
                cues.append(cue('sittande ben '+role,body,.09,'kropp',False,prior=True,anvandbar=False,orsak='Kroppsräckvidd är en kontroll, aldrig en golvmätning.',
                                orsak_intervall='Fast vadlängd; fotled/sula prior 8 cm, knäsänkning 0–12 cm och 3 cm posemarginal. Hela benets räckvidd är större.'))
                if sitstyp=='stol':
                    cues.append(cue('sitshöjd '+role,hip-.085-.455,.09,'sits',False,prior=True,sitstyp=sitstyp,
                                    priorer=['sits_m','backen_over_sits_m']))
                else:
                    cues.append(cue('sitshöjd '+role,hip-.085-.455,.09,'sits',False,prior=True,anvandbar=False,sitstyp=sitstyp,
                                    orsak='Sitstypen är inte identifierad som vanlig stol; stolsprioren gäller inte.'))
                wrists=X[:,[IX['l_wrist'],IX['r_wrist']]];stable=[]
                for side in range(2):
                    for a in range(len(frames)-11):
                        seg=wrists[a:a+12,side]
                        if np.ptp(seg[:,2])<=.03 and np.linalg.norm(np.ptp(seg[:,:2],axis=0))<=.08:
                            stable.append(dict(hojd_m=float(np.median(seg[:,2])),tagning=t['id'],sida='lr'[side],ruta=int(frames[a])))
                role_obs.setdefault(role,[]).append(dict(tagning=t['id'],hip_m=hip,stabila=stable))
            elif not seated:
                # Stående utan synlig fot ger bara räckvidd, aldrig en golvmätning.
                lengths=pp['knoglangder_cm'];reach=(lengths['lar']+lengths['underben'])/100
                cues.append(cue('stående räckvidd '+role,hip-reach-.05,.12,'kropp',False,prior=True,anvandbar=False,orsak='Kroppsräckvidd är en kontroll, aldrig en golvmätning.',
                                orsak_intervall='Fast benlängd; knäböjning och höft/sula är osäkra. Inte en synlig fot.'))
        shots.append(dict(tagning=t['id'],gammalt_golv_m=old,cues=cues))
    scale=[]
    for role,obs in role_obs.items():
        stable=[c for o in obs for c in o['stabila']]
        if not stable:continue
        best=min(stable,key=lambda c:c['hojd_m'])
        for o in obs:
            shot=next(s for s in shots if s['tagning']==o['tagning'])
            local=min(o['stabila'],key=lambda c:c['hojd_m']) if o['stabila'] else None
            shot.setdefault('lokal_handledsevidens',[]).append(dict(roll=role,
                varde_m=local['hojd_m']-.74 if local else None,spridning_m=.05 if local else None,
                evidens=local,anvand_separat=False,
                orsak='Lokalt stilla läge loggas separat. Rollens lägsta stabila läge över tagningarna används som svag kontaktcue; högre lägen kan vara gester och är inte oberoende golvmätningar.'))
        hip=float(np.median([o['hip_m'] for o in obs]));difference=best['hojd_m']-hip
        scale_range=[.09/difference,.31/difference] if difference>0 else None
        scale.append(dict(roll=role,handled_minus_backen_m=difference,skala_intervall_fran_prior=scale_range,
                          skala_1_inom=bool(scale_range and scale_range[0]<=1<=scale_range[1]),
                          orsak='Bord minus sits minus bäckenöverhöjd: prior 0,09–0,31 m. MHR root är en riggled, inte en uppmätt sittyta. Stilla handled kan vara gest; detta verifierar inte en ny skala.'))
        for shot in shots:
            if any(o['tagning']==shot['tagning'] for o in obs):
                shot['cues'].append(cue('stilla handled/bord '+role,best['hojd_m']-.74,.05,'bord',False,prior=True,
                                         evidens=best,prior_intervall_m=PRIORER['bord_m'],kontakt='antagen; 3 cm handled/kontaktyta + 2 cm bordprior'))
    allc=[]
    for shot in shots:
        shot['beslut']=kombinera(shot['cues'])
        shot['har_synlig_kontakt']=any(c['familj']=='fotter' for c in shot['cues'])
        shot['begransning']=None if shot['har_synlig_kontakt'] else 'Tagningen kan inte placeras tillförlitligt i höjd: inget i bilden mäter golvkontakt.'
        allc.extend(dict(c,tagning=shot['tagning']) for c in shot['cues'])
    pooled=kombinera(allc)
    depth_checks=[dict(tagning=t['id'],djupfaktor=t['rum'].get('scale',{}).get('depth_to_pipeline_scale'),
                       sparse_matching_multiplier=t['rum'].get('scale',{}).get('sparse_matching_multiplier'),
                       skillnad_procent=t['rum'].get('scale',{}).get('disagreement_percent'),
                       verifierad=t['rum'].get('scale',{}).get('verified',False)) for t in tagningar]
    depth_conflict=any(c['skillnad_procent'] is not None and c['skillnad_procent']>10 for c in depth_checks)
    return dict(priorer=PRIORER,per_tagning=shots,pool=pooled,fotsynlighet=visibility,
                skala=dict(varde=1.,status='antagen',behalls=True,kontroller=scale,
                           djupkontroller=depth_checks,djupkonflikt=depth_conflict,djuptolerans_procent=10.,
                           overens=False if depth_conflict else all(c['skala_1_inom'] for c in scale) if scale else None,
                           orsak='Kroppsmodellens meter behålls. Möbelpriorer prövar bara förenlighet; djupet saknar oberoende metrisk verifiering. Ingen längdskalning av kroppar.'))


def platsbeslut(prov, reg, tagningar=None):
    """Ett golv per plats, en registrering per kamera; aldrig per person.

    reg ska vara basregistreringen före varje golvbeslut. Äldre registreringars
    Z kom från golvantaganden även vid bildmatchning. En accepterad matchning
    återför den bildbaserade höjden; i en kedja A<-B<-C ackumuleras resterna
    längs grafen. Stationer utan sådan koppling får ett lokalt
    arbetsantagande. En ensam tagning med identitetsregistrering behåller sin
    ram; golvhöjden anges då i ramen i stället (prov['golv_hojd_m']).
    Varje stations totala Z-flytt sparas som 'z_flytt_m' så att en ny
    behandling kan börja från basregistreringen.
    """
    tags = {t['id']:t for t in (tagningar or [])}
    shots = {s['tagning']:s for s in prov['per_tagning']}
    parents = {s:s for s in shots}
    def root(s):
        while parents[s]!=s:s=parents[s]
        return s
    link = {}
    for sid,t in tags.items():
        q=t.get('kvalitet',{})
        target=q.get('mot')
        if not (sid in shots and target in shots and q.get('metod')=='matchning'):continue
        # Bara accepterad bildregistrering kopplar höjden mellan stationer.
        # Matchningens Z accepteras med plats.py:s egna gränser (TROSKEL):
        # kvarvarande lutning <= 2 grader och fri rigid rest <= 0,15 m. Med
        # större lutning beror höjdresten på var punkterna ligger, inte på
        # kamerans höjd; den redovisas då men flyttar ingenting.
        dz=q.get('hojdskillnad_mot_golvantagandet_m')
        tilt=q.get('lutning_kvar_grader');rest=q.get('rest_fri_rigid_m')
        ok=(q.get('status')=='uppmatt' and dz is not None and tilt is not None and tilt<=2. and rest is not None and rest<=.15)
        shots[sid]['registrering_hojd']=dict(mot=target,hojdrest_m=dz,lutning_kvar_grader=tilt,rest_fri_rigid_m=rest,
            status='accepterad' if ok else 'ej_accepterad',
            orsak='Höjd överförd från bildmatchning.' if ok else 'Matchningens höjd ej accepterad (lutning > 2 grader, rest > 0,15 m eller saknad); stationens golv väljs lokalt och är antaget.')
        if ok:link[sid]=(target,float(dz))
    # Resten mättes mot målstationens basram; målets egen korrigering följer med.
    offset={}
    def off(s,seen=()):
        if s in offset:return offset[s]
        if s not in link or s in seen:offset[s]=0.;return 0.
        target,dz=link[s];offset[s]=dz+off(target,seen+(s,));return offset[s]
    for sid in shots:
        o=off(sid)
        if sid in link:
            reg[sid]['M'][2,3]-=o
            for c in shots[sid]['cues']:
                c['varde_m']-=o;c['intervall_m']=[x-o for x in c['intervall_m']]
            shots[sid]['registrering_hojdrest_m']=o
            parents[root(sid)]=root(link[sid][0])
    ensam_identitet=(len(shots)==1 and all(t.get('kvalitet',{}).get('metod')=='identitet' for t in tags.values()))
    for group in {root(s) for s in shots}:
        members=[s for s in shots if root(s)==group]
        candidates=[dict(c,tagning=s) for s in members for c in shots[s]['cues']]
        decision=kombinera(candidates)
        for sid in members:
            shot=shots[sid];shot['lokalt_beslut']=shot['beslut'];shot['beslut']=dict(decision)
            shot['registreringsgrupp']=members
            shot['hojdkoppling_status']='modellbedomd' if len(members)>1 else 'antagen'
            value=decision['varde_m'];shot['z_flytt_m']=float(offset.get(sid,0.))
            if value is not None:
                shot['valt_golv_i_tagningen_m']=float(value-reg[sid]['M'][2,3])
                if ensam_identitet:prov['golv_hojd_m']=float(value)
                else:
                    reg[sid]['M'][2,3]-=value;shot['z_flytt_m']+=float(value)
            shot['gemensamt_golv_m']=0.
    prov['tillampad']=True
    prov['version']=2
    return prov


def mappsignatur(folder):
    """Samma uppgifter som datacache.signatur (sökväg, storlek, ändrings- och
    skapandetid i ns) för tagningsmappens mätfiler och kropp/*/*.npz, men via
    os.scandir: på Windows följer stat-uppgifterna med kataloglistningen, så
    tusentals kroppsfiler kostar inga egna systemanrop."""
    import os
    out=[]
    def scan(d,filter_):
        try:
            with os.scandir(d) as it:
                for e in it:
                    if e.is_file() and filter_(e.name):
                        st=e.stat();out.append([os.path.abspath(e.path),st.st_size,st.st_mtime_ns,st.st_ctime_ns])
                    elif e.is_dir() and d==str(folder)+os.sep+'kropp':scan(e.path,lambda n:n.endswith('.npz'))
        except FileNotFoundError:pass
    folder=Path(folder)
    scan(str(folder),lambda n:n.endswith(('.json','.npz','.npy')))
    scan(str(folder)+os.sep+'kropp',lambda n:False)
    return sorted(out)


def lokalt_golv(folder):
    """GOLV2-beslut för en tagning utan platsreferens, i tagningens egen ram (G). Beständig cache.

    Utan semantik finns ingen identifierad sits; synliga fötter, djupgolv och
    sist antagen kamerahöjd avgör. Returnerar hela undersökningen med beslut."""
    import plats
    from datacache import nyckel,kodnyckel,signatur,hamta,spara
    h=Path(__file__).resolve().parent;folder=Path(folder)
    key=nyckel(dict(kod=kodnyckel([Path(__file__),h/'dolda_fotter.py',h/'trohet.py',h/'trostod.py',h/'trosula.py',h/'tro_rigg.json',
                                   h.parent/'ingest/metrisk.py',h.parent/'ingest/plats.py',h.parent/'ingest/mhr_ledernamn.json']),
                    filer=mappsignatur(folder)))
    prov=hamta('golv2_lokal',key)
    if prov is None:
        t=plats.ladda_tagning(folder.name,folder)
        prov=undersok([t],{t['id']:dict(M=np.eye(4))},{(t['id'],pid):pid for pid in t['personer']})
        prov['tillampad']=True;prov['version']=2
        prov['golv_hojd_m']=prov['per_tagning'][0]['beslut']['varde_m']
        spara('golv2_lokal',key,prov)
    return prov


def sitstyp(pl, ankare_id):
    """Identifierad sitstyp för ett bundet ankare: mallens deltyp ('stol', ...) eller None."""
    rm=pl.get('rumsmall') or {}
    a=next((a for a in rm.get('ankare',[]) if a['id']==ankare_id),None)
    if a is None or a.get('typ')!='sate':return None
    d=next((d for d in rm.get('delar',[]) if d['id']==a.get('del')),None)
    return d.get('typ') if d else None


_MINNE={}  # processminne för senaste golv2-beslutet (nyckeln är densamma som den beständiga)


def for_plan(k, matning, platser):
    """Lös även frysta äldre platser med nya kroppsläsaren, med beständig cache."""
    import copy
    import plats
    from datacache import nyckel,kodnyckel,signatur,hamta,spara
    h=Path(__file__).resolve().parent
    files=[mappsignatur(Path(cam['spar_metrisk']['sokvag']).parent) for cam in matning['kameror']]
    key=nyckel(dict(kod=kodnyckel([Path(__file__),h/'dolda_fotter.py',h/'trohet.py',h/'trostod.py',h/'trosula.py',h/'tro_rigg.json',
                                   h.parent/'ingest/metrisk.py',h.parent/'ingest/plats.py',h.parent/'ingest/mhr_ledernamn.json']),
                    filer=files,scener=k['semantik']['scener'],matning=matning,platser=platser))
    cached=_MINNE.get(key)
    if cached is None:
        cached=hamta('golv2',key)
        if cached is not None:_MINNE.clear();_MINNE[key]=cached
    if cached is not None:return copy.deepcopy(cached)
    matning=copy.deepcopy(matning);platser=copy.deepcopy(platser)
    for plid,pl in platser.items():
        mp=next(p for p in matning['platser'] if p['id']==plid)
        ts=[];reg={};roles={}
        for registration in mp['registreringar']:
            sc=next(s for s in k['semantik']['scener'] if s['id']==registration['scen'])
            cam=next(c for c in matning['kameror'] if c['id']==sc['kamera'])
            tid=registration['tagning'];folder=Path(cam['spar_metrisk']['sokvag']).parent
            t=plats.ladda_tagning(tid,folder);ts.append(t)
            reg[tid]=dict(M=np.array(registration['till_plats']['matris'],float))
            for pid,pp in t['personer'].items():
                person=next((p['person'] for p in matning['personer'] if p.get('scen') in (None,sc['id']) and str(p.get('ingest_id',p['person']))==pid),None)
                roles[tid,pid]=person or 'okand_'+pid
                binding=next((b for b in sc.get('bindningar',[]) if b['person']==person),None)
                if binding:pp['semantisk_placering']=dict(hallning=binding['hallning'],status=binding.get('status','antagen'),sitstyp=sitstyp(pl,binding.get('ankare')))
        # Börja alltid från basregistreringen. Äldre plats.py drog varje
        # tagnings eget golvvärde från Z efter bildmatchningen; GOLV2 sparar
        # sin totala flytt som z_flytt_m. Båda återställs här, så att
        # matchningens höjdrest gäller samma ram som när den mättes och en
        # andra behandling inte dubblar korrigeringen.
        old=pl['golv'].get('matning') or {}
        if old.get('tillampad'):
            for s in old.get('per_tagning',[]):
                value=s.get('z_flytt_m') if old.get('version')==2 else s.get('beslut',{}).get('varde_m')
                if value is not None and s['tagning'] in reg:reg[s['tagning']]['M'][2,3]+=float(value)
        prov=platsbeslut(undersok(ts,reg,roles),reg,pl.get('tagningar'))
        pl['golv'].update(hojd_m=float(prov.get('golv_hojd_m',0.)),matning=prov,status=prov['pool']['status'],kalla='GOLV2: starkaste cue per registrerad kameragrupp; ett platsgolv.')
        from dolda_fotter import besluta
        besluta(ts,reg,roles,prov,matning,k['semantik']['scener'],pl['golv']['hojd_m'])
        for registration in mp['registreringar']:
            m=reg[registration['tagning']]['M'];registration['till_plats']['matris']=m.tolist()
            registration['till_plats']['translation_m']=m[:3,3].tolist()
        mp['golv']=copy.deepcopy(pl['golv'])
    result=[matning,platser];spara('golv2',key,result);_MINNE.clear();_MINNE[key]=copy.deepcopy(result)
    return result


STOD_STEG=3  # Fotrest efter stöd mäts var tredje ruta (stödet är det dyra steget).


def rapport_3d(plan):
    """Rester för alla skattade personer, även spår som planen utelämnar. Beständig cache."""
    from datacache import nyckel,kodnyckel,signatur,hamta,spara
    h=Path(__file__).resolve().parent
    scener=plan.get('scener') or plan['matkamera']['scener']
    files=[mappsignatur(f) for f in sorted({str(Path(sc['varld']).parent) for sc in scener})]
    key=nyckel(dict(kod=kodnyckel([Path(__file__),h/'trohet.py',h/'trostod.py',h/'tro_rigg.json',h.parent/'ingest/metrisk.py',h.parent/'ingest/kroppsstod.py']),
                    filer=files,scener=scener,plats=plan.get('plats'),nycklar=plan['matkamera']['nycklar'],steg=STOD_STEG))
    rows=hamta('golv2_3d',key)
    if rows is None:
        rows=_rapport_3d(plan,scener);spara('golv2_3d',key,rows)
    return rows


def _rapport_3d(plan,scener):
    from trohet import gravitation, F, las_sekvens, ruta
    rows=[]
    for sc in scener:
        folder=Path(sc['varld']).parent
        with np.load(sc['varld']) as src:v=dict(src)
        m=np.asarray(sc.get('till_plats',np.eye(4)));g=m[:3,:3]@gravitation(v)
        floor=next((float(p.get('golv_hojd_m',p.get('golv',{}).get('hojd_m',0.))) for p in plan.get('plats',[]) if p['id']==sc.get('plats_id')),0.)
        if not plan.get('plats'):floor=float(next(o['pos_m'][2] for o in plan['objekt'] if o['id']=='golv'))
        meta=json.loads((folder/'meta.json').read_text(encoding='utf-8'))
        for file in sorted(folder.glob('sekvens_*.npz')):
            s=las_sekvens(file);pid=file.stem[8:]
            indices=np.arange(sc['lokal_start'],sc['lokal_start']+sc['ut'][1]-sc['ut'][0]);indices=indices[s['inom'][indices]]
            if not len(indices):continue
            q=np.einsum('ij,njk,kl->nil',g,v['kam_R'][indices],F)
            trans=(v['kam_C'][indices]+np.einsum('nij,nj->ni',v['kam_R'][indices],s['cam_t'][indices]))@g.T+m[:3,3]
            x=np.einsum('nij,ntj->nti',q,s['pose'][indices,:,:3]/100)+trans[:,None]
            vis=fotkontroll(folder,pid,meta)
            sides={r['ruta']:(r['sidor'] if r['anvandbar'] else [False,False]) for r in vis['per_ruta']}
            feet=x[:,[4,8,20,24],2].min(1)-floor
            # Synlig fotrest: bara synliga, tillförlitliga sidor (vrist och tå på samma sida).
            seen=np.full(len(indices),np.inf)
            for side,(a,b) in enumerate(([4,8],[20,24])):
                on=np.array([sides.get(int(i),[False,False])[side] for i in indices],bool)
                seen[on]=np.minimum(seen[on],x[on][:,[a,b],2].min(1)-floor)
            ok=np.isfinite(seen)
            cam=v['kam_C'][indices]@g.T+m[:3,3]
            keys=plan['matkamera']['nycklar'];gap=[];heights=[]
            for j,f in enumerate(indices):
                u=sc['ut'][0]+int(f)-sc['lokal_start'];c=np.asarray(keys[u]['matris'])[:3,3]
                gap.append(float(np.linalg.norm(c-cam[j])));heights.append(float(c[2]-floor))
            pm=next((p for p in sc['personer'] if str(p.get('ingest_id',Path(p['rorelse']).stem[8:]))==pid),None)
            built=[]
            if pm:
                for f in indices[::STOD_STEG]:built.append(float(ruta(sc,pm,int(f),data=(s,v))[[4,8,20,24],2].min()-floor))
            rows.append(dict(scen=sc['id'],ingest_id=pid,person=pm['id'] if pm else None,i_plan=pm is not None,
                kamerahojd_m=float(np.median(heights)),kamera_rum_avstand_m=float(np.median(gap)),
                modellfotrest_m=float(np.median(feet)),modellfotrest_p90_abs_m=float(np.percentile(np.abs(feet),90)),
                synliga_fotrutor=int(ok.sum()),synlig_fotrest_m=float(np.median(seen[ok])) if ok.any() else None,
                fotrest_efter_stod_m=float(np.median(built)) if built else None,
                kontakt_status='modellbedomd' if ok.any() else 'saknas',
                begransning=None if ok.any() else 'Dolda fötter: kontakt okänd; modellresten styr inte golvet.'))
    return rows
