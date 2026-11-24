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
