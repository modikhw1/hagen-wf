"""Placera deklarerade föremål mot den färdiglösta renderkameran.

Bildrutan färdas via ``plats[].deklarerat.foremal`` och läggs aldrig i den strikt
validerade rumsmallen. Modulen körs efter bildkamera, möbelintervall och väggar.
"""
import math
import numpy as np


METOD = ('Stråle genom box_2d:s bottenmitt mot stödets valda ovansida, med planens '
         'slutliga renderkamera; träffen kläms till stödytan med föremålets fotavtryck.')
FLER_METOD = ('Robust soft-L1-passning av föremålets fasta 3D-låda mot synliga bildkanter i alla '
              'tagningar med slutliga renderkameror; XY kläms därefter till stödets ovansida.')


def _scen(plan, tagning):
    if not isinstance(tagning, str): return None
    scener = plan.get('scener') or (plan.get('matkamera') or {}).get('scener') or []
    return next((s for s in scener if str(s.get('id', '')).casefold() == tagning.casefold()), None)


def _traff(plan, bild, z_m, y_per_mille=None):
    """Världens XY där bildrutans horisontella mitt vid y träffar planet z_m, samt använd utdataruta.

    Utelämnat y behåller föremålslyftets tidigare beteende: ``box_2d``:s bottenkant.
    """
    scen = _scen(plan, bild.get('tagning'))
    if not scen: raise ValueError(f"tagningen {bild.get('tagning')!r} saknar scen med ut-intervall")
    if len(scen.get('ut') or []) != 2 or scen['ut'][1] <= scen['ut'][0]: raise ValueError('tagningens ut-intervall är tomt')
    u_ruta = (int(scen['ut'][0]) + int(scen['ut'][1]) - 1) // 2
    nycklar = (plan.get('renderkamera') or {}).get('nycklar') or []
    if not 0 <= u_ruta < len(nycklar): raise ValueError('renderkameran saknar en nyckel i tagningens ut-intervall')
    key = nycklar[u_ruta]; box = bild.get('box_2d')
    if not isinstance(box, (list, tuple)) or len(box) != 4: raise ValueError('box_2d saknas eller har inte fyra tal')
    try: y0, x0, y1, x1 = [float(v) for v in box]
    except (TypeError, ValueError): raise ValueError('box_2d innehåller annat än tal')
    w = float(plan['utdata']['bredd']); h = float(plan['utdata']['hojd'])
    sensor = float(plan['renderkamera'].get('sensor_bredd_mm', 36.)); lins = float(key['lins_mm'])
    if min(w, h, sensor, lins) <= 0: raise ValueError('kamera eller bildmått är inte positiva')
    py_per_mille = y1 if y_per_mille is None else float(y_per_mille)
    px, py = (x0 + x1) / 2000. * w, py_per_mille / 1000. * h
    fok = lins / sensor * w
    lokal = np.array([(px - w / 2.) / fok, -(py - h / 2.) / fok, -1.])
    M = np.asarray(key['matris'], float)
    if M.shape != (4, 4) or not np.all(np.isfinite(M)): raise ValueError('kameramatrisen är ogiltig')
    C = M[:3, 3]; riktning = M[:3, :3] @ lokal
    if abs(riktning[2]) < 1e-9: raise ValueError('bildstrålen är parallell med stödytan')
    t = (float(z_m) - C[2]) / riktning[2]
    if t <= 0: raise ValueError('bildstrålen når inte stödytan framför kameran')
    return (C + t * riktning)[:2], u_ruta


def _klam(stod, foremal, xy):
    """Kläm föremålets centrum så att dess roterade fotavtryck ryms på stödets ovansida."""
    syaw = float((stod.get('rotation_rad') or [0, 0, 0])[2]); fyaw = float((foremal.get('rotation_rad') or [0, 0, 0])[2])
    c, s = math.cos(syaw), math.sin(syaw); R = np.array([[c, -s], [s, c]])
    lokal = R.T @ (np.asarray(xy, float) - np.asarray(stod['pos_m'][:2], float))
    d = fyaw - syaw; cd, sd = abs(math.cos(d)), abs(math.sin(d))
    ex = (cd * foremal['matt_m'][0] + sd * foremal['matt_m'][1]) / 2.
    ey = (sd * foremal['matt_m'][0] + cd * foremal['matt_m'][1]) / 2.
    hx, hy = float(stod['matt_m'][0]) / 2., float(stod['matt_m'][1]) / 2.
    lx = 0. if ex >= hx else float(np.clip(lokal[0], -hx + ex, hx - ex))
    ly = 0. if ey >= hy else float(np.clip(lokal[1], -hy + ey, hy - ey))
    return np.asarray(stod['pos_m'][:2], float) + R @ np.array([lx, ly])


def _flytta(plan, objekt_id, delta):
    """Flytta föremålet och alla föremål som står på det, både i bygglistan och mallkopian."""
    prefix = objekt_id + ':pa:'
    for o in plan['objekt']:
        if o.get('id') == objekt_id or str(o.get('id', '')).startswith(prefix):
            o['pos_m'] = (np.asarray(o['pos_m'], float) + delta).tolist()
    for pl in plan.get('plats', []):
        for d in (pl.get('rumsmall') or {}).get('delar', []):
            if d.get('id') == objekt_id or str(d.get('id', '')).startswith(prefix):
                d['pos_m'] = (np.asarray(d['pos_m'], float) + delta).tolist()


def _ersattningsstod(plan, metadata, plats_id, f, oid, saknat_id):
    """Närmaste byggda stöd när det angivna stödet inte byggs.

    Kedjan uppåt ur objekt-id:t (``a:pa:b:pa:c`` -> ``a:pa:b`` -> ``a``), därefter förälderns stöd i metadatan och sist
    föremålets ankare om det är ett byggt objekt. Ersättningen redovisas i rapporten (``stod_ersatt``).
    """
    byggda = {o.get('id'): o for o in plan['objekt']}
    kandidater = []
    delar = str(oid).split(':pa:')
    kandidater += [(':pa:'.join(delar[:i]), 'stödkedjan i föremålets objekt-id') for i in range(len(delar) - 1, 0, -1)]
    nasta = f.get('pa'); sedda = set()
    while nasta and nasta not in sedda:
        sedda.add(nasta); m = metadata.get((plats_id, nasta))
        if not m: break
        if m.get('objekt_id'): kandidater.append((m['objekt_id'], 'förälderns objekt-id'))
        nasta = m.get('pa')
    if f.get('ankare'): kandidater.append((f['ankare'], 'föremålets ankare'))
    for kid, kalla in kandidater:
        if kid in byggda and kid != oid:
            return byggda[kid], dict(fran=saknat_id, till=kid, kalla=kalla,
                                     orsak='det angivna stödet byggs inte; närmast byggda stöd i kedjan används')
    raise ValueError(f'stödet {saknat_id!r} saknas i planens byggobjekt och inget ersättningsstöd finns i kedjan')


def los(plan):
    """Flytta alla deklarerade föremål med bildruta. Returnerar rapport eller None utan föremålsmetadata."""
    poster = []; metadata = {}
    for pl in plan.get('plats', []):
        for fid, f in ((pl.get('deklarerat') or {}).get('foremal') or {}).items():
            if isinstance(f, dict):
                metadata[(pl.get('id'), fid)] = f
            if isinstance(f, dict) and ('bilder' in f or f.get('bild')):
                poster.append((pl.get('id'), fid, f))
    if not poster: return None
    # Ett stöd flyttas före föremålen ovanpå det.
    poster.sort(key=lambda x: str(x[2].get('objekt_id', '')).count(':pa:'))
    rapport = []
    for plats_id, fid, f in poster:
        oid = f.get('objekt_id'); pa = f.get('pa')
        post = dict(plats=plats_id, foremal=fid, objekt_id=oid, stod=pa, status='bevarad', metod=METOD)
        try:
            if 'bilder' in f:
                if not isinstance(f['bilder'], list): raise ValueError('bilder är inte en lista')
                bilder = f['bilder']
            else:
                bilder = [f['bild']]
            if not bilder:
                post['orsak'] = 'inga bildrutor finns för föremålet'
                rapport.append(post)
                continue
            if not oid: raise ValueError('föremålet saknar byggbart objekt-id (handhållet eller trasig stöd-kedja)')
            objekt = next((o for o in plan['objekt'] if o.get('id') == oid), None)
            if objekt is None: raise ValueError('föremålet saknas i planens byggobjekt')
            foralder = metadata.get((plats_id, pa))
            stod_id = foralder['objekt_id'] if foralder and foralder.get('objekt_id') else pa
            stod = next((o for o in plan['objekt'] if o.get('id') == stod_id), None)
            if stod is None:
                stod, post['stod_ersatt'] = _ersattningsstod(plan, metadata, plats_id, f, oid, stod_id)
                post['stod'] = stod['id']
            if len(stod.get('matt_m') or []) != 3 or len(objekt.get('matt_m') or []) != 3: raise ValueError('stödets eller föremålets lådmått saknas')
            # 0012: kopior per kameragrupp (mobellyft) eller maskdata i rutorna ger placering per kopia ur maskens tyngdpunkt.
            if (sum(o.get('id') == oid for o in plan['objekt']) > 1
                    or any(isinstance(b, dict) and b.get('tyngdpunkt_2d') for b in bilder)):
                post.update(los_kopior(plan, f, oid, stod, bilder))
                rapport.append(post)
                continue
            topp = float(stod['pos_m'][2]) + float(stod['matt_m'][2]) / 2.
            fore = np.asarray(objekt['pos_m'], float)
            if len(bilder) > 1:
                from boxpassning import klassa_bilder
                anv, hoppade = klassa_bilder(plan, bilder)
                if hoppade: post['hoppade_boxar'] = [dict(tagning=h['tagning'], orsak=h['orsak']) for h in hoppade]
                if not anv:
                    post['orsak'] = 'ingen box har obeskurna kanter eller giltig kamera: ' + '; '.join(f"{h['tagning']}: {h['orsak']}" for h in hoppade)
                    rapport.append(post)
                    continue
                if len(anv) == 1: bilder = [anv[0]['bild']]          # bara en användbar box: det gamla enbildslyftet
            if len(bilder) > 1:
                from boxpassning import passa, startlage
                anvanda = [a['bild'] for a in anv]
                centrum_z = topp + float(objekt['matt_m'][2]) / 2.
                passningsobjekt = dict(objekt); passningsobjekt['pos_m'] = [float(fore[0]), float(fore[1]), centrum_z]
                try: start, startinfo = startlage(plan, anvanda, lambda b: _traff(plan, b, topp)[0])
                except ValueError as ex: start, startinfo = fore[:2].copy(), dict(start_orsak=str(ex), avvikande_boxar=[])
                start = _klam(stod, objekt, start)
                uteslut = {a['tagning'] for a in startinfo.get('avvikande_boxar', [])}
                if len(anvanda) - len(uteslut) < 2: uteslut = set()      # kan inte passa mot färre än två
                xy, info = passa(plan, passningsobjekt, bilder, start,
                                 lambda kandidat, _: (_klam(stod, objekt, kandidat), {}), uteslut=uteslut, rapport_xy0=fore[:2])
                post['startlage'] = startinfo
                efter = np.array([xy[0], xy[1], centrum_z])
                _flytta(plan, oid, efter - fore)
                post.update(status='flyttad', metod=FLER_METOD, fore_pos_m=fore.tolist(),
                            efter_pos_m=efter.tolist(), slutlig_pos_m=efter.tolist(), **info)
                rapport.append(post)
                continue
            xy, ruta = _traff(plan, bilder[0], topp); xy = _klam(stod, objekt, xy)         # en (användbar) box: enbildsvägen
            efter = np.array([xy[0], xy[1], topp + float(objekt['matt_m'][2]) / 2.])
            _flytta(plan, oid, efter - fore)
            post.update(status='flyttad', ruta=int(ruta), fore_pos_m=fore.tolist(), efter_pos_m=efter.tolist())
        except (KeyError, TypeError, ValueError, IndexError) as ex:
            post['orsak'] = str(ex)
        rapport.append(post)
    plan['kvalitet']['foremal_lyft'] = rapport
    return rapport


# --- Uppdrag 0012: föremål på möbel ur maskens tyngdpunkt, bredd ur masken, ett läge per kopia (kameragrupp) ---
MASK_METOD = ('Stråle genom maskens tyngdpunkt (segmenteraren) mot planet på föremålets halva höjd över stödets ovansida i samma tagning, '
              'med planens slutliga renderkamera; median över kopians tagningar, klämd till stödytan. Bredden i sidled ur maskens bredd på '
              'tyngdpunktens rad vid det djupet (bara rutor som inte är beskurna i sidled), median över klippet, inom deklarerat intervall.')


def _straale(plan, bild, x_pm, y_pm):
    """Kamerans läge, strålens riktning, nyckel och utdataruta genom bildpunkten (promille) i tagningens mittruta."""
    scen = _scen(plan, bild.get('tagning'))
    if not scen or len(scen.get('ut') or []) != 2 or scen['ut'][1] <= scen['ut'][0]: raise ValueError('tagningen saknar scen med ut-intervall')
    u = (int(scen['ut'][0]) + int(scen['ut'][1]) - 1) // 2
    nyck = (plan.get('renderkamera') or {}).get('nycklar') or []
    if not 0 <= u < len(nyck): raise ValueError('renderkameran saknar en nyckel i tagningens ut-intervall')
    key = nyck[u]; w = float(plan['utdata']['bredd']); h = float(plan['utdata']['hojd'])
    fok = float(key['lins_mm']) / float(plan['renderkamera'].get('sensor_bredd_mm', 36.)) * w
    M = np.asarray(key['matris'], float)
    lokal = np.array([(x_pm / 1000. * w - w / 2.) / fok, -(y_pm / 1000. * h - h / 2.) / fok, -1.])
    return M[:3, 3], M[:3, :3] @ lokal, M, fok, u


def _maskpunkt(plan, bild, z_m):
    """XY där strålen genom maskens tyngdpunkt når höjden z_m, djupet längs kamerans axel och utdataruta."""
    ty, tx = bild['tyngdpunkt_2d']
    C, d, M, fok, u = _straale(plan, bild, float(tx), float(ty))
    if abs(d[2]) < 1e-9: raise ValueError('strålen genom tyngdpunkten är parallell med planet')
    t = (float(z_m) - C[2]) / d[2]
    if t <= 0: raise ValueError('strålen genom tyngdpunkten når inte planet framför kameran')
    P = C + t * d; djup = float((P - C) @ (M[:3, :3] @ np.array([0., 0., -1.])))
    return P[:2], djup, fok, M, u


def _bredd_ur_mask(plan, objekt, bilder, z_c, intervall):
    """Föremålets mått i sidled ur maskens bredd: (axel 0/1, värde, poster). Bara rutor som inte är beskurna i sidled."""
    w = float(plan['utdata']['bredd']); prov = []; axlar = []
    for b in bilder:
        if not b.get('tyngdpunkt_2d') or b.get('bredd_2d') is None: continue
        box = b.get('box_2d') or []
        if len(box) != 4 or box[1] <= 10. or box[3] >= 990.: continue
        try: _, djup, fok, M, _ = _maskpunkt(plan, b, z_c)
        except (ValueError, KeyError, TypeError, IndexError): continue
        sid = (M[:3, :3] @ np.array([1., 0., 0.]))[:2]; sid = sid / max(np.linalg.norm(sid), 1e-9)
        axlar.append(0 if abs(sid[0]) >= abs(sid[1]) else 1)
        prov.append(dict(tagning=b.get('tagning'), bredd_m=round(float(b['bredd_2d']) / 1000. * w * djup / fok, 3), djup_m=round(djup, 3)))
    if not prov: return None, None, []
    axel = int(round(float(np.median(axlar))))
    varde = float(np.median([p['bredd_m'] for p in prov]))
    if intervall is not None:
        lo, hi = (float(intervall[axel][0]), float(intervall[axel][1])) if isinstance(intervall[axel], (list, tuple)) else (float(intervall[axel]),) * 2
        varde = float(np.clip(varde, lo, hi))
    return axel, varde, prov


def _scenmitt(plan, tagning):
    s = _scen(plan, tagning)
    return None if not s else (int(s['ut'][0]) + int(s['ut'][1]) - 1) // 2


def los_kopior(plan, f, oid, stod, bilder):
    """0012: föremålet placeras per kopia (synlighetsintervall) på stödets kopia i samma intervall, ur maskens tyngdpunkt. Returnerar rapportfält."""
    N = len(plan.get('kallrutor') or (plan.get('renderkamera') or {}).get('nycklar') or [])
    kopior = [o for o in plan['objekt'] if o.get('id') == oid]
    stodkopior = [o for o in plan['objekt'] if o.get('id') == stod['id']] or [stod]
    if not kopior: raise ValueError('föremålet saknas i planens byggobjekt')
    iv = lambda o: o.get('synlig_ut') or [0, N]

    def stod_for(k):
        a, b = iv(k)
        return max(stodkopior, key=lambda s: (s.get('kameragrupp') == k.get('kameragrupp'), min(b, iv(s)[1]) - max(a, iv(s)[0])))
    hojd = float(kopior[0]['matt_m'][2])
    s0 = stod_for(kopior[0]); z_c = float(s0['pos_m'][2]) + float(s0['matt_m'][2]) / 2. + hojd / 2.
    axel, bredd, bredd_prov = _bredd_ur_mask(plan, kopior[0], bilder, z_c, (f.get('bild') or {}).get('storlek_m_dekl'))
    fore_matt = list(kopior[0]['matt_m'])
    if bredd is not None:
        for o in plan['objekt']:
            if o.get('id') == oid: o['matt_m'] = list(o['matt_m']); o['matt_m'][axel] = bredd
        for pl in plan.get('plats', []):
            for d in (pl.get('rumsmall') or {}).get('delar', []):
                if d.get('id') == oid: d['matt_m'] = list(d['matt_m']); d['matt_m'][axel] = bredd
    poster = []; prefix = oid + ':pa:'; dolda = []
    med_ruta = [x for x in bilder if isinstance(x, dict) and _scenmitt(plan, x.get('tagning')) is not None]
    for k in kopior:
        a, b = iv(k); s = stod_for(k); topp = float(s['pos_m'][2]) + float(s['matt_m'][2]) / 2.
        egna = [x for x in bilder if isinstance(x, dict) and (lambda m: m is not None and a <= m < b)(_scenmitt(plan, x.get('tagning')))]
        if med_ruta and not egna:
            # Trohet per tagning (0012): föremålet har rutor i andra tagningar men ingen i kopians. Där syns det inte i originalet,
            # och kopians läge är bara stödets; den visas därför inte (en vågkopia mitt framför personen i S6 utan stöd i bild).
            dolda.append(dict(synlig_ut=[a, b], kameragrupp=k.get('kameragrupp'), status='dold',
                              orsak='föremålet har bildrutor i andra tagningar men ingen i kopians intervall; syns inte i originalet där'))
            continue
        punkter = []; kallor = []
        for x in egna:
            try:
                if x.get('tyngdpunkt_2d'):
                    p, _, _, _, _ = _maskpunkt(plan, x, topp + hojd / 2.); kallor.append('tyngdpunkt')
                else:
                    p, _ = _traff(plan, x, topp); kallor.append('bottenmitt')
                punkter.append(np.asarray(p, float))
            except (ValueError, KeyError, TypeError, IndexError): continue
        fore = np.asarray(k['pos_m'], float)
        if punkter:
            xy = _klam(s, k, np.median(np.array(punkter), axis=0)); efter = np.array([xy[0], xy[1], topp + hojd / 2.])
            status = 'flyttad'
        else:
            efter = np.array([fore[0], fore[1], topp + hojd / 2.]); status = 'följer stödet'
        delta = efter - fore
        for o in plan['objekt']:
            if (o is k) or (str(o.get('id', '')).startswith(prefix) and iv(o) == [a, b]):
                o['pos_m'] = (np.asarray(o['pos_m'], float) + delta).tolist()
        poster.append(dict(synlig_ut=[a, b], kameragrupp=k.get('kameragrupp'), stod_synlig_ut=iv(s), bilder=[x.get('tagning') for x in egna],
                           kallor=kallor, status=status, fore_pos_m=fore.tolist(), efter_pos_m=efter.tolist()))
    if dolda:
        bort = {tuple(d['synlig_ut']) for d in dolda}
        plan['objekt'] = [o for o in plan['objekt'] if not ((o.get('id') == oid or str(o.get('id', '')).startswith(prefix)) and tuple(iv(o)) in bort)]
    if not poster:
        return dict(status='dold', metod=MASK_METOD, kopior=[], dolda_kopior=dolda, orsak='ingen kopia har en egen bildruta')
    huvud = max(poster, key=lambda p: (len(p['bilder']), p['synlig_ut'][1] - p['synlig_ut'][0]))
    return dict(status='flyttad' if any(p['status'] == 'flyttad' for p in poster) else 'bevarad', metod=MASK_METOD,
                fore_pos_m=huvud['fore_pos_m'], efter_pos_m=huvud['efter_pos_m'], slutlig_pos_m=huvud['efter_pos_m'], kopior=poster, dolda_kopior=dolda,
                bredd=dict(axel=axel, fore_m=fore_matt[axel] if axel is not None else None, valt_m=bredd, prov=bredd_prov,
                           deklarerat=(f.get('bild') or {}).get('storlek_m_dekl'),
                           orsak=None if bredd is not None else 'ingen maskbredd i en ruta som inte är beskuren i sidled; måttet oförändrat'),
                avvikelse='strålen skärs med planet på föremålets halva höjd över stödets ovansida (tyngdpunkten ligger där), inte med själva ovansidan')
