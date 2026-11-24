"""Läsbar diagnos bredvid varje upplöst plan. Trösklarna är våra egna."""
from pathlib import Path
import numpy as np


# Egna diagnostiska val (inga ägarkrav, inte avstämda så att scener ska passera). Referens: estimatorns egna hörn mot samma mask ger IoU ~0,76 (b S1),
# eftersom masken har kläder/hår/föremål men nätet är en naken standardkropp; därför ligger gränserna under det.
GRANSER_KROPP=dict(iou_synlig_bra=.65,iou_synlig_dalig=.50,tyngdpunkt_p90_granska=.03,tyngdpunkt_p90_dalig=.06,darr_granska=1.5,darr_dalig=3.0,
                   tackning_granska=.6,mask_tackning_granska=.6)


def kroppsskal(r,g=GRANSER_KROPP):
    """(allvarlighet, skäl) per scen/person: 0 = ok, 1 = granska, 2 = dålig."""
    sk=[];lv=0;m=r['mask']
    if not m.get('rutor'):sk.append('inget oberoende mått (ingen mask i rutan)');lv=max(lv,1)
    else:
        if m['iou_synlig_median']<g['iou_synlig_dalig']:sk.append(f"silhuett-IoU {m['iou_synlig_median']:.2f} < {g['iou_synlig_dalig']}");lv=2
        elif m['iou_synlig_median']<g['iou_synlig_bra']:sk.append(f"silhuett-IoU {m['iou_synlig_median']:.2f} < {g['iou_synlig_bra']}");lv=max(lv,1)
        if m['tyngdpunkt_p90']>g['tyngdpunkt_p90_dalig']:sk.append(f"tyngdpunkt p90 {m['tyngdpunkt_p90']*100:.1f} % av bildhöjden");lv=2
        elif m['tyngdpunkt_p90']>g['tyngdpunkt_p90_granska']:sk.append(f"tyngdpunkt p90 {m['tyngdpunkt_p90']*100:.1f} % av bildhöjden");lv=max(lv,1)
    d=r['darr_cm_per_ruta2']['byggd']
    if d is not None and d==d:
        if d>g['darr_dalig']:sk.append(f'darr {d:.2f} cm/ruta²');lv=2
        elif d>g['darr_granska']:sk.append(f'darr {d:.2f} cm/ruta²');lv=max(lv,1)
    if r['tackning']<g['tackning_granska']:sk.append(f"passningen bedömd på {r['passning_bedomda']} av {r['ruta_antal']} rutor");lv=max(lv,1)
    return lv,sk


def s_personer(plan,sid):
    sc=next((x for x in (plan.get('scener') or []) if x['id']==sid),None)
    return sc['personer'] if sc else []


def kamerabana(plan):
    import json as _j,sys as _s
    _s.path.insert(0,str(Path(__file__).resolve().parent.parent/'ingest'))
    from regler import kamerabana_rimlig
    fps=plan['utdata']['fps_taljare']/plan['utdata']['fps_namnare'];cam=[]
    for sc in (plan.get('scener') or plan['matkamera']['scener']):
        v=np.load(sc['varld'],allow_pickle=True);r=kamerabana_rimlig(v['kam_C'],fps)
        beslut=_j.loads(str(v['metriskt_skalbeslut'])) if 'metriskt_skalbeslut' in v.files else {}
        cam.append(dict(scen=sc['id'],avvisad=bool(v['metrisk_translation_avvisad']) if 'metrisk_translation_avvisad' in v.files else False,
                        skalbeslut_status=beslut.get('status'),skalbeslut_orsak=beslut.get('orsak'),skalbeslut_p90_fart_m_s=beslut.get('p90_fart_m_s'),skalbeslut_vag_m=beslut.get('vag_m'),**r))
    return cam


def omskriv(planfil):
    """Skriv om kvalitet.md bredvid en befintlig plan.json (t.ex. efter att kvalitetssidan fått nya avsnitt). Räknar inte om kroppsmått som redan finns."""
    import json
    f=Path(planfil);plan=json.loads(f.read_text(encoding='utf-8'))
    if 'kamerabana' not in plan['kvalitet']:plan['kvalitet']['kamerabana']=kamerabana(plan)
    skriv(plan,f)
    f.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')


def _planbeslut_utan_cache(plan, platser):
    from skymning import los
    from golvmatning import undersok
    import plats
    floors={i:pl['golv']['matning'] for i,pl in platser.items() if 'matning' in pl['golv']}
    if not floors:
        # Källor utan platsreferens: samma lokala GOLV2-beslut som kompilatorn tillämpade.
        from golvmatning import lokalt_golv
        folder=Path(plan['matning']['kameror'][0]['spar_metrisk']['sokvag']).parent
        floors['ensam']=lokalt_golv(folder)
    plan['kvalitet']['golv_skala']=floors
    plan['kvalitet']['dolda_fotter']=[dict(p['dolda_fotter']) for p in plan['matning'].get('personer',[]) if p.get('dolda_fotter')]
    for s in plan.get('scener') or plan['matkamera']['scener']:
        for pm in s['personer']:
            if not pm.get('stod') or pm.get('skyddade_knan'):continue
            pid=pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]
            vis=next((v for f in floors.values() for v in f['fotsynlighet']
                      if v['ingest_id']==pid and (v['tagning'].lower()==s['id'].lower() or len(floors)==1 and len(f['per_tagning'])==1)),None)
            if vis:
                protected={str(v['ruta']):v['synliga_knan'] for v in vis['per_ruta'] if any(v.get('synliga_knan',[]))}
                if protected:pm['skyddade_knan']=protected
    # Möbler med deklarerat intervall (platsens deklarerat.mobler) justeras inom intervallet före skymningskontrollen, så att den inte behöver stryka dem.
    from mobelintervall import losa
    mobler=losa(plan,platser)
    if mobler:plan['kvalitet']['mobelintervall']=mobler
    plan['kvalitet']['skymning']=los(plan)


def planbeslut(plan, platser):
    """Knäskydd och skymning är byggbeslut och körs även utan diagnostik."""
    from datacache import kodnyckel, nyckel, signatur, matfiler, hamta, spara, lokala_moduler
    import copy
    h=Path(__file__).resolve().parent
    # All lokal kod som planbeslutet importerar, transitivt, plus de datafiler koden läser.
    kod=lokala_moduler([h/'kvalitet.py',h/'datacache.py',h.parent/'ingest/plats.py',h.parent/'ingest/metrisk.py'],[h,h.parent/'ingest'])+[h/'tro_rigg.json',h/'tro_fothud.npz']
    key=nyckel(dict(kod=kodnyckel(kod),filer=signatur(matfiler(plan,alla=True)),platser=platser,
                    scener=plan.get('scener'),personer=plan['personer'],objekt=plan['objekt'],
                    kamera=plan['matkamera'],kallrutor=plan['kallrutor'],bredd=plan['kallbild_bredd'],hojd=plan['kallbild_hojd']))
    cached=hamta('planbeslut',key)
    if cached is None:
        _planbeslut_utan_cache(plan,platser)
        scenes=plan.get('scener') or plan['matkamera']['scener']
        cached=dict(objekt=plan['objekt'],skydd=[[pm.get('skyddade_knan') for pm in sc['personer']] for sc in scenes],
                    kvalitet={k:plan['kvalitet'][k] for k in ('golv_skala','dolda_fotter','skymning','mobelintervall') if k in plan['kvalitet']})
        spara('planbeslut',key,cached)
    else:
        plan['objekt']=copy.deepcopy(cached['objekt'])
        scenes=plan.get('scener') or plan['matkamera']['scener']
        for sc,skydd in zip(scenes,cached['skydd']):
            for pm,knan in zip(sc['personer'],skydd):
                if knan is not None:pm['skyddade_knan']=copy.deepcopy(knan)
        plan['kvalitet'].update(copy.deepcopy(cached['kvalitet']))


def komplettera(plan, platser, *, med_planbeslut=True):
    """Full diagnostik. Redan lösta byggbeslut kan behållas vid separat kontroll."""
    if med_planbeslut:planbeslut(plan,platser)
    from trostod import NAMN,BEN
    overrides=[]
    for s in plan.get('scener') or plan['matkamera']['scener']:
        for pm in s['personer']:
            if not pm.get('stod'):continue
            with np.load(pm['rorelse']) as seq:
                a=s['lokal_start'];b=a+s['ut'][1]-s['ut'][0]
                n=int((~seq['ben_synliga'][a:b]&seq['inom'][a:b]).sum()) if 'ben_synliga' in seq else 0
            names=[NAMN[i] for i in BEN] if n else []
            protected=pm.get('skyddade_knan',{})
            for side_index,side in enumerate('lr'):
                if protected and all(protected.get(str(i),[False,False])[side_index] for i in range(a,b)):
                    names=[name for name in names if not name.startswith(side+'_upleg')]
            overrides.append(dict(scen=s['id'],person=pm['id'],rutor=n,leder=names,
                                  skyddade_knalagen_rutor=sum(sum(v) for v in protected.values()),
                                  antagande='Dold benpose och hudens sula; fasta mått i ändrade segment. Synligt lår/knäläge behåller uppmätt längdvariation. Bäcken och överkropp skyddas.'))
    plan['kvalitet']['ledersattningar']=overrides
    plan['kvalitet']['kamerabana']=kamerabana(plan)
    from golvmatning import rapport_3d
    plan['kvalitet']['golv2_3d']=rapport_3d(plan)
    from kroppmatt import matt_plan
    plan['kvalitet']['kropp']=dict(grans=GRANSER_KROPP,rader=matt_plan(plan))


def skriv(plan, fil):
    q=plan['kvalitet'];occ=q.get('skymning',{});floors=q.get('golv_skala',{})
    slutkamera=any('medel_offset_px' in r for r in q['bildtrohet']['personer'])
    if slutkamera:
        rows=['# Kvalitet', '',
              'Detta är egna diagnostiska trösklar, valda i förväg och inte justerade så att scener ska passera: slutkamerans medeloffset 3 % av bildhöjden, skalfaktor 0,85–1,15 och led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal; kroppsmåtten nedan. Slutbildsmåttet projicerar samma leder genom kameran som Blender renderar med. Det är inte oberoende av kroppsestimatorn, men till skillnad från ingestkameramåttet ser det ändrad inramning. Den oberoende kontrollen är silhuett-IoU mot YOLO-masken.', '',
              '| Scen | Slutkamera: medel px / % höjd / skala / IoU | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |','|---|---|---|---|---|---|']
    else:
        rows=['# Kvalitet', '',
              'Detta är egna diagnostiska trösklar, valda i förväg och inte justerade så att scener ska passera: avvikelse från estimatorns 2D median 20 px/4 % av personhöjd, p90 40 px/8 %, led-IoU 0,65; golvcues 10 cm; skymning 2 % med 5 cm djupmarginal; kroppsmåtten nedan. Bra betyder att alla kontroller passerar. Granska betyder osäkra antaganden, konflikt, darr, låg täckning eller svag oberoende matchning. Dålig betyder att en oberoende gräns (silhuett, tyngdpunkt, darr) är tydligt passerad; avvikelsen från estimatorns 2D ger bara granska, eftersom den inte är oberoende och domineras av fingerleder (42 av de 48 mätta punkterna). **En scen kan aldrig bli bättre än granska på avvikelsen från estimatorns 2D ensam.** Den siffran är inte oberoende: estimatorn passas mot samma 2D-punkter som mäts, och om bildskyddet (äldre ingest) har blandat tillbaka råposen ligger p90 vid gränsen 6 px av konstruktion. Den oberoende kontrollen är silhuett-IoU mot YOLO-masken.', '',
              '| Scen | Avvikelse från estimatorns 2D median/p90 px (ej oberoende) | Golv, skala och spridning | Ersatta leder | Skymning före → efter | Omdöme och skäl |','|---|---|---|---|---|---|']
    for sid in dict.fromkeys(r['scen'] for r in q['bildtrohet']['personer']):
        people=[r for r in q['bildtrohet']['personer'] if r['scen']==sid]
        if slutkamera:
            worst=max(people,key=lambda p:p.get('medel_offset_bildhojdandel',0))
            err=f"{worst.get('medel_offset_px',0):.2f} / {100*worst.get('medel_offset_bildhojdandel',0):.2f} % / {worst.get('skalfaktor',0):.3f} / {worst.get('bbox_iou',0):.3f}"
        else:err='/'.join(f'{max(p.get(k,0) for p in people):.2f}' for k in ('median_px','p90_px'))
        f=next(iter(floors.values()),None);shot=None
        if f:shot=next((s for s in f['per_tagning'] if s['tagning'].lower()==sid.lower()),f['per_tagning'][0])
        decision=shot['beslut'] if shot else {};spread=decision.get('spridning_m');span=decision.get('spann_m')
        fs=decision.get('status','saknas');conflict=decision.get('konflikt',True);scale=f.get('skala',{}) if f else {}
        applied=f.get('tillampad',False) if f else False
        floorlabel=f'{fs}, ±{spread*100:.1f} cm; spann {span*100:.1f} cm' if spread is not None else 'saknas'
        floorlabel+=f'; skala 1,0 {scale.get("status","saknas")}'
        if not applied:floorlabel+='; golv endast granskat'
        bef=[r for r in occ.get('fore',{}).get('per_del',[]) if r['scen']==sid];aft=[r for r in occ.get('efter',{}).get('per_del',[]) if r['scen']==sid]
        oc=f'{max([r["andel"] for r in bef] or [0])*100:.1f} → {max([r["andel"] for r in aft] or [0])*100:.1f} %'
        overrides=[r for r in q.get('ledersattningar',[]) if r['scen']==sid]
        joints='; '.join(f'{r["person"]}: {len(r["leder"])} i {r["rutor"]} rutor' for r in overrides) or '0'
        bad=any(r['flaggad'] for r in people);reasons=[]
        if bad:reasons.append('slutkamerans inramning avviker från originalets 2D-läsning' if slutkamera else 'avvikelse från estimatorns 2D över gränsen (ej oberoende; mest fingerleder; räknas som granska)')
        import json as _j
        for r in s_personer(plan,sid):
            u=Path(r['rorelse']).with_name('utsnitt_'+Path(r['rorelse']).stem[8:]+'.json')
            if u.exists() and _j.loads(u.read_text(encoding='utf-8')).get('endast_overkropp'):reasons.append(f'endast överkropp ({r["id"]}): inget golv eller kontakt')
        cb=next((c for c in q.get('kamerabana',[]) if c['scen']==sid),None)
        if cb and not cb['rimlig']:reasons.append('kamerabana orimlig: '+'; '.join(cb['skal']))
        if cb and cb['avvisad']:reasons.append('kamerans translation okänd (avvisad skala)')
        if fs!='uppmatt':reasons.append('golv '+fs)
        if shot and shot.get('begransning'):reasons.append(shot['begransning'])
        hidden=[r for r in q.get('dolda_fotter',[]) if r.get('scen')==sid]
        for r in hidden:
            reasons.append(f"dolda fötter {r['person']}: antagen skala {r['faktor']:.6f}"+(f", kvarstående konflikt {r['sula_efter_m']:.3f} m" if r.get('kvarstaende_konflikt') else ''))
        if conflict:reasons.append('golvcues oense')
        if scale.get('overens') is False:reasons.append('skalprior oense')
        actions=[r for r in occ.get('atgarder',[]) if r['scen']==sid]
        if actions:reasons.append('mall utelämnad: '+', '.join(r['del_id'] for r in actions))
        if any(r['flaggad'] for r in aft):reasons.append('skymningsrest')
        kr=[r for r in q.get('kropp',{}).get('rader',[]) if r['scen']==sid];lv=0
        for r in kr:
            l_,sk_=kroppsskal(r);lv=max(lv,l_);reasons+=[f"{r['person']}: {t}" for t in sk_]
        if not kr:reasons.append('kroppsmått saknas')
        status='dålig' if lv==2 else 'granska' if reasons else 'bra'
        rows.append(f'| {sid} | {err} | {floorlabel} | {joints} | {oc} | {status}: {", ".join(reasons) or "diagnostiken passerar"} |')
    for sc in (plan.get('scener') or []):
        if not sc['personer']: rows.append(f'| {sc["id"]} | – | – | – | – | ej bedömd: scen utan person (bara kamera och rum, inga kroppar att mäta) |')
    rows += ['', '## GOLV2: kropp och rum', '',
             'Kroppens kameraposition bevaras. Synlig fot är modellbedömd kontakt, inte fysisk inmätning. Dolda fötter styr inte golvet.', '',
             '| Scen/person | Kamera över golv m | Kamera till rumskamera m | Modellfotrest m | Synlig fotrest m | Kontakt |',
             '|---|---:|---:|---:|---:|---|']
    for r in q.get('golv2_3d',[]):
        foot='saknas' if r['synlig_fotrest_m'] is None else f"{r['synlig_fotrest_m']:.3f}"
        rows.append(f"| {r['scen']}/{r['ingest_id']} | {r['kamerahojd_m']:.3f} | {r['kamera_rum_avstand_m']:.6f} | {r['modellfotrest_m']:.3f} | {foot} | {r['kontakt_status']}; {r.get('begransning') or ''} |")
    hidden=q.get('dolda_fotter',[])
    if hidden:
        rows += ['', '### Antagen skala för helt dolda fötter', '',
                 'Detta är aldrig en mätning. Kropp och kameraavstånd skalas tillsammans kring varje bildrutas kameracentrum med en konstant faktor per person/tagning.', '',
                 '| Scen/person | Faktor | Längd före → efter m | Sula före → efter m | Golvet satt av | Gräns/konflikt |',
                 '|---|---:|---:|---:|---|---|']
        for r in hidden:
            sources=', '.join(x['cue'] for x in r.get('golv_satt_av',[])) or '–'
            conflict=(f"gräns {r['faktor_grans']}; kvar {r['sula_efter_m']:.3f} m" if r.get('kvarstaende_konflikt') else 'ingen kvarstående konflikt')
            rows.append(f"| {r.get('scen')}/{r['person']} | {r['faktor']:.6f} (antagen) | {r['langd_fore_m']:.3f} → {r['langd_efter_m']:.3f} | {r['sula_fore_m']:.3f} → {r['sula_efter_m']:.3f} | {sources} | {conflict} |")
    k=q.get('kropp')
    if k:
        g=k['grans']
        rows+=['','## Kropp: oberoende mått, darr och täckning','',
               f"Silhuett: kroppsmodellens hudnät skinnat med de byggda lederna, projicerat i den spårade kameran, mot YOLO11-seg-masken (en annan modell än kroppsestimatorn), inom personens egen spårruta, på ALLA rutor där masken finns (även opålitliga). IoU `synlig` klipper nätet vid maskens nedersta rad (skymmande disk/bord). Tyngdpunktsfel i andel av bildhöjden. **Skevhet:** masken har kläder, hår och hållna föremål som kroppen saknar och kan sakna fingrar; estimatorns egna hörn mot samma mask ger referens-IoU (kolumn ref); IoU under ref är alltså inte automatiskt fel. Hudnätet är lod1 (renderingen använder lod3, samma kropp) utan korrigerande blendshapes (< 2 cm lokalt).",
               f"Darr: medel andra differens av ledpositionerna (127 leder, planens värld, cm/ruta²) för byggd pose, stabiliserad pose före golv/kontakt/stöd, och estimatorns råa pose med råa cam_t. Råa är skakigare än filmen får vara; byggd över {g['darr_granska']} = granska, över {g['darr_dalig']} = dålig (våra val). Andel = hur stor del av den stabiliserade posen som överlevde äldre bildskydd (– = inget bildskydd, ny metod).",
               f"Täckning: rutor där avvikelsen från estimatorns 2D kunde bedömas / rutor i scenen. Orsaker till uteblivna rutor: ej i bild (personen ej spårad), opålitlig (under 35 % av kroppspunkterna i bild eller 15 % i masken: estimatorn gissar), rådata saknas. Under {g['tackning_granska']:.0%} = granska.",
               f"Gränser (våra, inga ägarkrav): IoU synlig bra ≥ {g['iou_synlig_bra']}, dålig < {g['iou_synlig_dalig']}; tyngdpunkt p90 > {g['tyngdpunkt_p90_granska']*100:.0f} % granska, > {g['tyngdpunkt_p90_dalig']*100:.0f} % dålig.",'',
               '| Scen | Person | IoU / IoU synlig / ref (median) | Tyngdpunkt median/p90 (% bildhöjd) | Mask-rutor | Darr byggd / stabil / rå | Andel | Täckning (bedömda/rutor) | Utelämnade: ej i bild / opålitliga / rådata saknas |','|---|---|---|---|---|---|---|---|---|']
        for r in k['rader']:
            m=r['mask'];ref=r['referens_estimator'];dd=r['darr_cm_per_ruta2'];f_=lambda x:'–' if x is None or x!=x else f'{x:.2f}'
            iou=f"{m['iou_median']:.2f} / {m['iou_synlig_median']:.2f} / {ref['iou_median']:.2f}" if m.get('rutor') and ref.get('rutor') else (f"{m['iou_median']:.2f} / {m['iou_synlig_median']:.2f} / –" if m.get('rutor') else 'saknas')
            tp=f"{m['tyngdpunkt_median']*100:.1f} / {m['tyngdpunkt_p90']*100:.1f}" if m.get('rutor') else '–'
            rows.append(f"| {r['scen']} | {r['person']} | {iou} | {tp} | {m.get('rutor',0)} av {r['mask_rutor_av']} | {f_(dd['byggd'])} / {f_(dd['stabil'])} / {f_(dd['ra'])} | {'–' if r['bildskydd_stabil_andel'] is None else format(r['bildskydd_stabil_andel'],'.2f')} | {r['passning_bedomda']} av {r['ruta_antal']} | {r['ej_i_bild']} / {r['opalitliga']} / {r['ravdata_saknas']} |")
    kb=q.get('kamerabana')
    if kb:
        g=kb[0]['granser']
        rows+=['','## Kamerabana','',f"Den metriska kamerabanan som bärs in i bygget (`varld.npz`) kontrolleras mot vad en handhållen mobil kan göra inomhus: p90-fart ≤ {g['p90_fart_m_s']} m/s, maxfart ≤ {g['max_fart_m_s']} m/s, sträcka ≤ {g['vag_per_s_m']} m/s × scenens längd (våra gränser). En orimlig bana betyder nästan alltid att COLMAP-skalan inte är bestämd (kenny S2 hade 11,7 km). Avvisad skala = translationen är nollad och bara rotationen används.",'',
              '| Scen | Bana (m) | p90 / max fart (m/s) | Rimlig | Skalbeslut vid ingest |','|---|---|---|---|---|']
        for c in kb:rows.append(f"| {c['scen']} | {c['vag_m']:.2f} | {c['p90_fart_m_s']:.2f} / {c['max_fart_m_s']:.2f} | {'ja' if c['rimlig'] else 'NEJ: '+'; '.join(c['skal'])} | {c['skalbeslut_status'] or '–'}{(': '+c['skalbeslut_orsak']) if c['skalbeslut_orsak'] and c['skalbeslut_status']!='uppmatt' else ''}{' (translation avvisad; p90 före avvisning '+format(c['skalbeslut_p90_fart_m_s'],'.3g')+' m/s, '+format(c['skalbeslut_vag_m'],'.4g')+' m)' if c['avvisad'] and c['skalbeslut_p90_fart_m_s'] is not None else ''} |")
    rows+=['', 'Antaget: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm; kamerahöjd 1,45 m (reservprior 1,20–1,70 m). Dessa möbelpriorer används bara vid vanligt bord, inte bardisk. En stilla handled behöver inte vila på bordet. Passningens rest mot handled och bäcken loggas, även när en höjd begränsas av priorn. Ingen kropp skalas för att passa en prior.', '',
           'Skymning är provandel av källmask inom personrutan: segmentet från mätkameran till närmaste synliga MHR70-punkts riktiga 3D-position provas mot möbellådorna; ingen exakt hudarea. Var tredje och sista rutan kontrolleras (före 10 nov var sjätte). Varje kroppsdel har egen gräns, 10 % av delens maskprov (minst 8), så att tunna skenor över höften syns även när de är << 2 % av alla prov före regins kameraedits. Saknad mask bakom möbler rapporteras bara; ingen möbel skapas därifrån. Fötter utanför mask/personruta är inte verifierade mätningar. Alla cuevärden, avvisningar, lednamn och omvända konflikter finns i plan.json under kvalitet.']
    rows += ['', '## Skärmtext', '', f"{len(plan.get('skarmtext',[]))} tidsatta 2D-lager i källpixlar. Textinnehåll från sparad semantik; teckenmallar mäter plats och synlighet utan OCR. Fontval är närmaste installerade font. Konfidens avser teckenmatchning, inte sannolikheten att modellens text är rätt."]
    for t in plan.get('skarmtext',[]):
        if t.get('ursprung',{}).get('typ')=='antagen':rows.append(f"- {t['id']} ({t['scen']}): antagen placering/tid; {t['ursprung']['metod']}")
    rows += ['', '## Diskpassning', '']
    for p in plan.get('plats',[]):
        room=p.get('rumsmall',{})
        for fit in room.get('hojdpassning',[]):
            if 'evidens_rest_m' in fit:rows.append(f"- {room['id']}: höjd {fit['hojd_m']:.3f} m ({fit['status']}), rest {fit['evidens_rest_m']} m. {fit['metod']}")
    if plan.get('props'):
        from propplan import rapportrader
        rows += rapportrader(plan)
    Path(fil).with_name('kvalitet.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
