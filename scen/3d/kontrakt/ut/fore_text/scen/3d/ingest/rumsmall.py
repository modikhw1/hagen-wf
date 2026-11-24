"""Rumsmallar: deklarativa möbler, rigid ankarpassning och procedurdelar.

Inga modeller eller nätanrop. Mått och material i banken är mallvärden.
Djupfragmenten stannar i platsens evidens och används aldrig som möbler.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np

BANK = Path(__file__).resolve().parent.parent / 'kontrakt/rumsmall'


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])


def las(mall):
    p = Path(mall)
    if not p.is_file(): p = BANK / (str(mall) + '.json')
    m = json.loads(p.read_text(encoding='utf-8'))
    # Samma paketfria schemavaliderare som kontraktet använder.
    import sys
    sys.path.insert(0, str(BANK.parent))
    from gemensamt import kontrollmodul
    schema = json.loads((BANK / 'rumsmall.schema.json').read_text(encoding='utf-8'))
    fel = kontrollmodul().validera(m, schema, str(p), schema)
    if fel: raise ValueError('\n'.join(fel))
    ids = [a['id'] for a in ankare(m)]
    if len(ids) != len(set(ids)): fel.append('Mallens ankarnamn är inte unika.')
    delar=[d['id'] for d in m['delar']]
    if len(delar)!=len(set(delar)):fel.append('Mallens delnamn är inte unika.')
    for d in m['delar']:
        for a in d['ankare']:
            if a['typ']=='sate' and ('sate_hojd_m' not in a or 'backen_over_sate_m' not in a):fel.append('Sittankare kräver sitsens höjd och bäckenets mjukdelsmått.')
    if fel: raise ValueError('\n'.join(fel))
    return m, hashlib.sha256(p.read_bytes()).hexdigest()


def ankare(m):
    res = []
    for d in m['delar']:
        for a in d['ankare']:
            a = copy.deepcopy(a)
            a['pos_m'] = (rz(d['yaw_rad']) @ a['pos_m'] + d['pos_m']).tolist()
            a['riktning_rad'] += d['yaw_rad']; a['del'] = d['id']
            a['etikett'] = a['id']; a['status'] = 'antagen'; a['metod'] = 'Mall: ' + m['id']
            a['hojd_m'] = a.get('sate_hojd_m', a['pos_m'][2]); a['osakerhet_m'] = None
            res.append(a)
    return res


def passa(m, uppmatt, golv_hojd=None):
    """Minsta kvadrat i XY + riktningar. Skala 1; golvhöjd från platsen.

    Namn OCH typ måste stämma. Bordskanter är svaga fragment (vikt 0,1),
    sitt/ståplats vikt 1. Riktning motsvarar en hävarm på 0,5 mallmeter.
    Dessa vikter är antagna algoritmval, inte mätvärden.
    """
    src = {a['id']: a for a in ankare(m)}; par = []
    for b in uppmatt:
        a = src.get(b['id'])
        if a and a['typ'] == b['typ']: par.append((a, b, .1 if a['typ'] == 'bordskant' else 1.))
    if not par: raise ValueError('Ingen mallankare matchar namn och typ.')
    X = np.array([a['pos_m'][:2] for a, b, w in par]); Y = np.array([b['pos_m'][:2] for a, b, w in par]); W = np.array([w for a, b, w in par])
    cx = np.average(X, axis=0, weights=W); cy = np.average(Y, axis=0, weights=W)
    A, B = X - cx, Y - cy
    co = sum(W * (A * B).sum(1)); si = sum(W * (A[:, 0]*B[:, 1] - A[:, 1]*B[:, 0]))
    for a, b, w in par:
        da = b['riktning_rad'] - a['riktning_rad']; co += w*.5**2*math.cos(da); si += w*.5**2*math.sin(da)
    yaw = math.atan2(si, co); R = rz(yaw); t = np.r_[cy - R[:2, :2] @ cx, np.median([b['pos_m'][2]-a['pos_m'][2] for a, b, w in par if a['typ'] != 'bordskant'] or [0.])]
    if golv_hojd is not None: t[2] = golv_hojd
    residual = [dict(ankare=a['id'], typ=a['typ'], avstand_m=float(np.linalg.norm(R @ a['pos_m'] + t - b['pos_m'])),
                     vinkel_rad=float((a['riktning_rad']+yaw-b['riktning_rad']+math.pi)%(2*math.pi)-math.pi), vikt=w) for a, b, w in par]
    return dict(yaw_rad=yaw, translation_m=t.tolist(), skala=1., residualer=residual,
                rms_m=float(np.sqrt(np.average([r['avstand_m']**2 for r in residual], weights=W))),
                status='antagen', metod='Rigid XY-passning, namn + typ + riktning; ingen skala. Vikter: sitt/stå 1, bordskant 0,1, riktning 0,5 m hävarm.')


def moblera(plats, val=None):
    """Fäst stöd till mätta ankare efter rigid passning; redovisa varje ändring.

    En stol snäpps till sitt ankare. Bord med följankare snäpps till stolen
    med mallens avstånd. Därmed blir passningens rest aldrig ett glapp till stolen.
    """
    val = val or ('restaurang_tva' if sum(a['typ']=='sate' for a in plats['ankare']) >= 2 else 'bar_disk')
    m, sha = las(val); fitank=copy.deepcopy(plats['ankare']); evidens=[]
    if not any(a['id']==b['id'] and a['typ']==b['typ'] for a in ankare(m) for b in fitank):
        # Barklippets personer går; inga stationära personankare finns.
        # Diskens redan uppmätta främre kant räcker för yaw/XY. Golvet låser Z.
        disk=next((o for o in plats['objekt'] if o['etikett']=='bar counter'),None)
        if disk:
            p=np.array(disk['centrum_m'])+rz(disk['yaw_rad'])@np.array([0.,disk['matt_m'][1]/2,disk['matt_m'][2]/2])
            a=dict(id='disk_kant',typ='bordskant',pos_m=p.tolist(),riktning_rad=disk['yaw_rad']+math.pi/2,status='antagen',metod='Främre kant ur befintligt djupfragment. Svag skaluppgift; golvet låser Z.')
            fitank.append(a);evidens.append(a)
    fit = passa(m, fitank, plats['golv']['hojd_m']); R = rz(fit['yaw_rad']); t = np.array(fit['translation_m'])
    delar = copy.deepcopy(m['delar']); gamla = {a['id']:a for a in ankare(m)}; matta = {a['id']:a for a in plats['ankare']}
    justeringar = []
    for d in delar:
        p0 = R @ d['pos_m'] + t; yaw0 = d['yaw_rad'] + fit['yaw_rad']; d['pos_m'] = p0.tolist(); d['yaw_rad'] = yaw0
        ref = d.get('folj_ankare') or next((a['id'] for a in d['ankare'] if a['typ']=='sate'), None)
        if ref in gamla and ref in matta and gamla[ref]['typ'] == matta[ref]['typ']:
            a, b = gamla[ref], matta[ref]; dy = b['riktning_rad']-a['riktning_rad']; rr = rz(dy)
            # Delens lokala läge före den rigida passningen.
            original = next(x for x in m['delar'] if x['id']==d['id'])
            pn = np.array(b['pos_m']) + rr @ (np.array(original['pos_m'])-a['pos_m'])
            d['pos_m'] = pn.tolist(); d['yaw_rad'] = original['yaw_rad']+dy
            justeringar.append(dict(del_id=d['id'], ankare=ref, forskjutning_m=(pn-p0).tolist(), status='antagen', orsak='Stödet följer uppmätt ankare; mått och avstånd inom möbeln är mallvärden.'))
    inst = dict(m, delar=delar); fitted = ankare(inst)
    plats['rumsmall'] = dict(id=m['id'], sha256=sha, status='mall', fiktiv=m['fiktiv'], passning=fit, justeringar=justeringar, passningsevidens=evidens, delar=delar,
                            ankare=fitted, antaganden=m['antaganden'], texturprojektion=None)
    plats['utelamnade'] = []
    return plats['rumsmall']


def som_plats(m):
    """Kundmall i egen värld; ingen påstådd mätpassning."""
    return dict(id=m['id'], golv=dict(hojd_m=0.), ankare=ankare(m), objekt=[], vaggar=[],
                rumsmall=dict(m, status='mall', passning=None, justeringar=[], ankare=ankare(m)))


def byggobjekt(rum):
    """Utvidga typade möbler till lådor/cylindrar med material och fasning.

    Alla konstruktionsdetaljer nedan (bentjocklek, skivtjocklek, fasning)
    är mallvärden. modell_ref och texturprojektion reserveras, laddas inte.
    """
    res = []
    for d in rum['delar']:
        w, dep, h = d['matt_m']; R = rz(d['yaw_rad']); p = np.array(d['pos_m']); typ = d['typ']
        def bit(n, xyz, size, col=None, form='lada'):
            res.append(dict(id=d['id']+n, namn='mall:'+d['id']+n, typ=form, pos_m=(p+R@xyz).tolist(), rotation_rad=[0,0,d['yaw_rad']],
                            matt_m=list(size), farg=col or d['material']['farg'], top_slope=0, fas_m=min(.015,min(size)/5), status='mall', deltyp=typ,
                            modell_ref=d.get('modell_ref'), texturprojektion=d.get('texturprojektion')))
        if typ in ('bord','stol'):
            thick=.045 if typ=='bord' else .055
            bit('',[0,0,h-thick/2],[w,dep,thick])
            for x in (-w/2+.055,w/2-.055):
                for y in (-dep/2+.055,dep/2-.055): bit(f':ben:{x}:{y}',[x,y,(h-thick)/2],[.045,.045,h-thick],d['material'].get('ben_farg','#292c2e'))
            if typ=='stol':
                bit(':rygg',[0,-dep/2+.025,h+.23],[w,.055,.43])
                for x in (-w/2+.04,w/2-.04): bit(f':ryggstod:{x}',[x,-dep/2+.025,h+.1],[.035,.035,.35])
        elif typ=='bardisk':
            bit('',[0,0,(h-.06)/2],[w,dep*.85,h-.06]);bit(':skiva',[0,0,h-.03],[w+.08,dep,.06],d['material'].get('ben_farg','#292c2e'))
        elif typ=='lampa':
            bit('',[0,0,h/2],[w,dep,h],form='cylinder')
        elif typ=='hylla':
            for z in (.06,h/2,h): bit(f':plan:{z}',[0,0,z],[w,dep,.04])
        elif typ=='fonster':
            bit('',[0,0,h/2],[w,dep,h]);
            for x in (-w/2,w/2): bit(f':karm:{x}',[x,0,h/2],[.06,dep+.02,h],'#ddd8c8')
        else: bit('' if typ!='golv' else '',[0,0,h/2],[w,dep,h])
    return res
