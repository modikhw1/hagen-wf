"""Placera deklarerade möbler från originalets bildruta mot slutkameran.

Bildrutan ligger i ``plats[].deklarerat.mobler`` och berör därför inte den strikt
validerade rumsmallen. Modulen körs efter bildkamera. För bildbekräftade möbler
körs den före möbelintervall/skymning, så att intervallet prövas på rätt plats;
vägganpassning och föremålslyft ser sedan den färdiga geometrin.
"""
import math
import numpy as np

from foremallyft import _flytta, _traff
from boxpassning import (_projektera_halvplan, bilddata, framfor_alla_kameror, klassa_bilder, passa,
                         passa_grupp, startlage)


METOD = ('Stråle genom box_2d:s valda kant mot golv eller vald möbelhöjd med planens '
         'slutliga renderkamera; möbeln flyttas endast i XY och behåller mått, höjd och yaw. '
         'Med framfor hålls djupordningen kamera–möbel–person.')
FLER_METOD = ('Robust soft-L1-passning av fast möbellådas synliga bildkanter mot alla användbara bilder med '
              'varje tagnings slutliga renderkamera; XY är fritt medan mått, höjd och yaw är fasta. '
              'Startläget är medianen av enbildslägena (avvikande boxar utesluts ur anpassningen). Djupordningen '
              'kamera–möbel–person är villkor i passningen för alla tagningar; kamerans gräns lättas aldrig under 0.')


def _box(bild):
    box = bild.get('box_2d') if isinstance(bild, dict) else None
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        raise ValueError('box_2d saknas eller har inte fyra tal')
    try: varden = [float(v) for v in box]
    except (TypeError, ValueError): raise ValueError('box_2d innehåller annat än tal')
    if not np.all(np.isfinite(varden)): raise ValueError('box_2d innehåller ett ogiltigt tal')
    return varden


def _kamera(plan, ruta):
    """Slutkamerans XY och horisontella blickriktning i världens XY."""
    key = (plan.get('renderkamera') or {}).get('nycklar', [])[ruta]
    M = np.asarray(key['matris'], float)
    if M.shape != (4, 4) or not np.all(np.isfinite(M)): raise ValueError('kameramatrisen är ogiltig')
    fram = (M[:3, :3] @ np.array([0., 0., -1.]))[:2]
    norm = float(np.linalg.norm(fram))
    if norm < 1e-9: raise ValueError('kamerans blickriktning saknar horisontell komponent')
    return M[:2, 3].copy(), fram / norm


def _kantradie(mobel, fram):
    """Avstånd från lådans mitt till kanten längs kamerans horisontella blickriktning."""
    matt = mobel.get('matt_m') or []
    if len(matt) != 3 or min(float(v) for v in matt) <= 0: raise ValueError('möbelns lådmått saknas eller är inte positiva')
    yaw = float((mobel.get('rotation_rad') or [0, 0, 0])[2]); c, s = math.cos(yaw), math.sin(yaw)
    lokal = np.array([[c, s], [-s, c]]) @ np.asarray(fram, float)
    namnare = abs(lokal[0]) / (float(matt[0]) / 2.) + abs(lokal[1]) / (float(matt[1]) / 2.)
    if namnare <= 0: raise ValueError('möbelns framkant kan inte bestämmas')
    return 1. / namnare


def _djuphalva(mobel, fram):
    """Möbelns halva djupomfång projicerat på kamerans horisontella blickriktning."""
    matt = mobel.get('matt_m') or []
    if len(matt) != 3 or min(float(v) for v in matt) <= 0: raise ValueError('möbelns lådmått saknas eller är inte positiva')
    yaw = float((mobel.get('rotation_rad') or [0, 0, 0])[2]); c, s = math.cos(yaw), math.sin(yaw)
    lokal = np.array([[c, s], [-s, c]]) @ np.asarray(fram, float)
    return float(abs(lokal[0]) * float(matt[0]) / 2. + abs(lokal[1]) * float(matt[1]) / 2.)


def _framfor_ankare(pl, ankare_id):
    kallor = (('uppmatta_ankare', pl.get('uppmatta_ankare') or []), ('ankare', pl.get('ankare') or []))
    kalla, ankare = next(((k, a) for k, poster in kallor for a in poster if a.get('id') == ankare_id), (None, None))
    if ankare is None: raise ValueError(f'framfor-platsen {ankare_id!r} saknas bland planens ankare')
    pos = ankare.get('pos_m') or []
    if len(pos) < 2 or not np.all(np.isfinite(np.asarray(pos[:2], float))): raise ValueError(f'framfor-platsen {ankare_id!r} saknar giltig position')
    return np.asarray(pos[:2], float), kalla


def _klam_djup(pl, spec, mobel, efter, kamera_xy, fram):
    """Kläm centrumdjupet så möbeln ligger minst 0,30 m efter kameran och 0,10 m före personen."""
    ankare_id = spec.get('framfor')
    if not ankare_id: return efter, dict(klamd=False, klamningsgrans=None)
    (person_xy, ankarkalla), halva = _framfor_ankare(pl, ankare_id), _djuphalva(mobel, fram)
    persondjup = float((person_xy - kamera_xy) @ fram)
    min_centrum = .30 + halva
    max_centrum = persondjup - .10 - halva
    konflikt = min_centrum > max_centrum
    fore = float((efter[:2] - kamera_xy) @ fram)
    # Om båda marginalerna inte ryms prioriteras den deklarerade ordningen mot personen;
    # möbeln hamnar då så långt efter kameran som personens 0,10-metersmarginal medger.
    nytt = max_centrum if konflikt else float(np.clip(fore, min_centrum, max_centrum))
    grans = 'personplats' if konflikt else 'kamera' if nytt > fore + 1e-9 else 'personplats' if nytt < fore - 1e-9 else None
    efter = efter.copy(); efter[:2] += (nytt - fore) * fram
    return efter, dict(klamd=grans is not None, klamningsgrans=grans, framfor=ankare_id,
                       framfor_ankare_kalla=ankarkalla, granskonflikt=konflikt,
                       centrumdjup_fore_m=fore, centrumdjup_efter_m=nytt,
                       centrumdjup_granser_m=[min_centrum, max_centrum],
                       uppnadd_kameramarginal_m=nytt - halva,
                       uppnadd_personmarginal_m=persondjup - (nytt + halva),
                       regel='framkant minst 0,30 m efter kameran; bakkant minst 0,10 m före framfor-platsen')


def _enbildslage(plan, pl, spec, mobel, bild):
    """Gamla enbildslyftet utan att skriva planen; används som robust startvärde."""
    y0, _, y1, _ = _box(bild)
    topp = float(mobel['pos_m'][2]) + float(mobel['matt_m'][2]) / 2.
    if y1 < 990.:
        if pl.get('golv_hojd_m') is None: raise ValueError('platsens golvhöjd saknas')
        y, z, tecken = y1, float(pl['golv_hojd_m']), 1.
    else:
        y, z, tecken = y0, topp, -1.
    traff, ruta = _traff(plan, bild, z, y_per_mille=y)
    kamera_xy, fram = _kamera(plan, ruta); radie = _kantradie(mobel, fram)
    efter = np.asarray(mobel['pos_m'], float).copy()
    efter[:2] = np.asarray(traff, float) + tecken * radie * fram
    efter, _ = _klam_djup(pl, spec, mobel, efter, kamera_xy, fram)
    return efter[:2]


# (kameramarginal, personmarginal) i meter, strängast först. Kamerans nedre gräns tas aldrig bort: den lättas bara
# stegvis och aldrig under 0, och ryms ingen nivå behålls möbelns tidigare läge.
ORDNINGSNIVAER = ((.30, .10), (.30, 0.), (.05, 0.), (0., 0.))


def _ordningsdata(plan, pl, spec, mobel, bilder):
    """Per tagning: kamerans XY och blick, möbelns halva djup och personens djup. None utan ``framfor``."""
    ankare_id = spec.get('framfor')
    if not ankare_id: return None
    person_xy, ankarkalla = _framfor_ankare(pl, ankare_id)
    data = []; sedda = set()
    for bild in bilder:
        try: _, _, ruta = bilddata(plan, bild)
        except (ValueError, KeyError, TypeError, IndexError): continue
        if ruta in sedda: continue
        sedda.add(ruta)
        kamera_xy, fram = _kamera(plan, ruta); halva = _djuphalva(mobel, fram)
        data.append(dict(tagning=bild.get('tagning'), ruta=int(ruta), kamera_xy=kamera_xy, fram=fram, halva=halva,
                         persondjup=float((person_xy - kamera_xy) @ fram)))
    return dict(ankare_id=ankare_id, ankarkalla=ankarkalla, data=data)


def _ordningsvillkor(data, kam_m, pers_m):
    """Halvplan a·xy <= b: framkant minst kam_m efter varje kamera, bakkant minst pers_m före personen."""
    villkor = []
    for d in data:
        undre = kam_m + d['halva']; ovre = d['persondjup'] - pers_m - d['halva']; k = float(d['kamera_xy'] @ d['fram'])
        villkor.append((-d['fram'], -(undre + k)))
        villkor.append((d['fram'], ovre + k))
    return villkor


def _valj_ordningsniva(ordning, xy):
    """Första nivån (strängast först) där ordningen ryms i alla tagningar samtidigt. (None, []) om ingen gör det."""
    for niva, (kam_m, pers_m) in enumerate(ORDNINGSNIVAER):
        villkor = _ordningsvillkor(ordning['data'], kam_m, pers_m)
        if _projektera_halvplan(xy, villkor)[1]: return niva, villkor
    return None, []


def _ordningsrapport(ordning, niva, xy_fore, xy_efter, klamd):
    """Per tagning före/efter och uppnådda marginaler samt vilken lättnad som behövdes."""
    xy_fore = np.asarray(xy_fore, float); xy_efter = np.asarray(xy_efter, float); poster = []
    for d in ordning['data']:
        fore = float((xy_fore - d['kamera_xy']) @ d['fram']); efter = float((xy_efter - d['kamera_xy']) @ d['fram'])
        kam = efter - d['halva']; pers = d['persondjup'] - (efter + d['halva'])
        poster.append(dict(tagning=d['tagning'], ruta=d['ruta'], centrumdjup_fore_m=fore, centrumdjup_efter_m=efter,
                           centrumdjup_granser_m=[ORDNINGSNIVAER[0][0] + d['halva'], d['persondjup'] - ORDNINGSNIVAER[0][1] - d['halva']],
                           uppnadd_kameramarginal_m=kam, uppnadd_personmarginal_m=pers,
                           granskonflikt=bool(kam < ORDNINGSNIVAER[0][0] - 1e-9 or pers < ORDNINGSNIVAER[0][1] - 1e-9)))
    rapport = dict(klamd=bool(klamd), klamningsgrans='flera_tagningar' if klamd else None, framfor=ordning['ankare_id'],
                   framfor_ankare_kalla=ordning['ankarkalla'], granskonflikt=bool(niva != 0), ordningsniva=niva, klamningar=poster,
                   regel='framkant minst 0,30 m efter varje kamera och bakkant minst 0,10 m före framfor-platsen; lättas stegvis '
                         '(kameran aldrig under 0 m), annars behålls möbelns tidigare läge')
    if niva is None:
        rapport['orsak_granskonflikt'] = 'ordningen ryms inte i alla tagningar ens med kameramarginal 0 m och personmarginal 0 m'
    elif niva > 0:
        konflikt = [d['tagning'] for d in ordning['data'] if d['persondjup'] - ORDNINGSNIVAER[0][1] - d['halva'] < ORDNINGSNIVAER[0][0] + d['halva']]
        rapport['orsak_granskonflikt'] = (f'kraven {ORDNINGSNIVAER[0][0]:.2f} m kamera och {ORDNINGSNIVAER[0][1]:.2f} m person ryms inte tillsammans; '
                                          f'lättat till {ORDNINGSNIVAER[niva][0]:.2f} m kamera och {ORDNINGSNIVAER[niva][1]:.2f} m person'
                                          + (f' (omöjligt i sig för {", ".join(map(str, konflikt))})' if konflikt else ''))
    return rapport


def los(plan):
    """Flytta möbler med deklarerad bildruta. Returnerar rapport eller None utan sådan metadata."""
    poster = []
    for pl in plan.get('plats', []):
        for did, spec in ((pl.get('deklarerat') or {}).get('mobler') or {}).items():
            if isinstance(spec, dict) and ('bilder' in spec or spec.get('bild')):
                poster.append((pl, did, spec))
    if not poster: return None
    rapport = []
    for pl, did, spec in poster:
        post = dict(plats=pl.get('id'), mobel=did, status='bevarad', metod=METOD)
        try:
            if 'bilder' in spec:
                if not isinstance(spec['bilder'], list): raise ValueError('bilder är inte en lista')
                bilder = spec['bilder']
            else:
                bilder = [spec['bild']]
            if not bilder:
                post['orsak'] = 'inga bildrutor finns för möbeln'
                rapport.append(post)
                continue
            mobel = next((o for o in plan.get('objekt', []) if o.get('id') == did), None)
            if mobel is None: raise ValueError('möbeln saknas i planens byggobjekt')
            if len(mobel.get('pos_m') or []) != 3: raise ValueError('möbelns position saknas')
            if any(isinstance(b, dict) and b.get('grupp') for b in bilder):
                post.update(los_grupper(plan, pl, did, spec, mobel, bilder))      # 0012: ett läge per mätt kameragrupp
                rapport.append(post)
                continue
            if len(bilder) > 1:
                anv, hoppade = klassa_bilder(plan, bilder)
                if hoppade: post['hoppade_boxar'] = [dict(tagning=h['tagning'], orsak=h['orsak']) for h in hoppade]
                if not anv:
                    post['orsak'] = 'ingen box har obeskurna kanter eller giltig kamera: ' + '; '.join(f"{h['tagning']}: {h['orsak']}" for h in hoppade)
                    rapport.append(post)
                    continue
                if len(anv) == 1:
                    bilder = [anv[0]['bild']]          # bara en användbar box: det gamla enbildslyftet
                else:
                    fore = np.asarray(mobel['pos_m'], float).copy()
                    anvanda = [a['bild'] for a in anv]
                    ordning = _ordningsdata(plan, pl, spec, mobel, bilder)
                    niva, villkor = (0, []) if ordning is None else _valj_ordningsniva(ordning, fore[:2])
                    if ordning is not None and niva is None:
                        post.update(orsak='kamera–möbel–person-ordningen ryms inte i alla tagningar; möbelns tidigare läge behålls',
                                    fore_pos_m=fore.tolist(), efter_pos_m=fore.tolist(), slutlig_pos_m=fore.tolist(),
                                    **_ordningsrapport(ordning, None, fore[:2], fore[:2], False))
                        rapport.append(post)
                        continue
                    try: start, startinfo = startlage(plan, anvanda, lambda b: _enbildslage(plan, pl, {}, mobel, b))
                    except ValueError as ex: start, startinfo = fore[:2].copy(), dict(start_orsak=str(ex), avvikande_boxar=[])
                    start, framfor_alla = framfor_alla_kameror(plan, mobel, anvanda, start)
                    uteslut = {a['tagning'] for a in startinfo.get('avvikande_boxar', [])}
                    if len(anvanda) - len(uteslut) < 2: uteslut = set()      # kan inte passa mot färre än två
                    efter_xy, info = passa(plan, mobel, bilder, start, uteslut=uteslut, villkor=villkor, rapport_xy0=fore[:2])
                    efter = fore.copy(); efter[:2] = efter_xy
                    _flytta(plan, did, efter - fore)
                    post.update(status='flyttad', metod=FLER_METOD, fore_pos_m=fore.tolist(),
                                efter_pos_m=efter.tolist(), slutlig_pos_m=efter.tolist(),
                                start_pos_m=[float(start[0]), float(start[1]), float(fore[2])],
                                start_framfor_alla_kameror=framfor_alla, startlage=startinfo, **info)
                    if ordning is not None:
                        post.update(_ordningsrapport(ordning, niva, fore[:2], efter_xy, info['villkor_flyttade_m'] > 1e-6 or niva > 0))
                    else:
                        post.update(klamd=False, klamningsgrans=None, granskonflikt=False)
                    rapport.append(post)
                    continue
            bild = bilder[0]
            y0, _, y1, _ = _box(bild)
            topp = float(mobel['pos_m'][2]) + float(mobel['matt_m'][2]) / 2.
            if y1 < 990.:
                if pl.get('golv_hojd_m') is None: raise ValueError('platsens golvhöjd saknas')
                kant, kantorsak, y, z, tecken = ('bottenkant', 'boxens botten ligger innanför bilden (ymax < 990)',
                                                 y1, float(pl['golv_hojd_m']), 1.)
            else:
                kant, kantorsak, y, z, tecken = ('ovansidans_bakkant', 'boxens botten är beskuren (ymax >= 990)',
                                                 y0, topp, -1.)
            post.update(kant=kant, kantorsak=kantorsak)
            traff, ruta = _traff(plan, bild, z, y_per_mille=y)
            kamera_xy, fram = _kamera(plan, ruta); radie = _kantradie(mobel, fram)
            fore = np.asarray(mobel['pos_m'], float).copy(); efter = fore.copy()
            efter[:2] = np.asarray(traff, float) + tecken * radie * fram
            efter, klamning = _klam_djup(pl, spec, mobel, efter, kamera_xy, fram)
            _flytta(plan, did, efter - fore)
            post.update(status='flyttad', ruta=int(ruta), fore_pos_m=fore.tolist(), efter_pos_m=efter.tolist(), **klamning)
        except (KeyError, TypeError, ValueError, IndexError) as ex:
            post['orsak'] = str(ex)
        rapport.append(post)
    plan['kvalitet']['mobel_lyft'] = rapport
    return rapport


# --- Uppdrag 0012: ett läge per mätt kameragrupp, beskurna kanter som olikheter och ett uttalat förval ---
GRUPP_METOD = ('Per mätt kameragrupp (ingest/rum_grupper.py; tagning utan grupp = egen grupp): fast möbellåda passad mot gruppens bildrutor, '
               'obeskurna kanter som likheter och beskurna som olikheter. En koordinat som färre än två kanter bestämmer hålls vid förvalet '
               '(deklarationens läge relativt framfor-platsen) och märks antagen. Väggar, deklarerat intervall och kamera–möbel–person är villkor. '
               'Varje grupp får en egen kopia av möbeln (och det som står på den) för sina scener; övriga scener följer gruppen med flest bilder.')
BAKKANT_FORE_PERSON_M = .15   # förval: möbelns bakkant så här långt framför framfor-platsen, mot gruppens kameror (antaget)


def _spann_eller_tal(v):
    if isinstance(v, (list, tuple)) and len(v) == 2: return float(v[0]), float(v[1])
    return (float(v), float(v)) if v is not None else None


def _vaggvillkor(plan, mobel, inre_xy):
    """Halvplan som håller möbelns fotavtryck MOBEL_MARGINAL_M innanför de genererade väggarna (som de står före vaggar.py)."""
    from vaggar import GENERERADE, MOBEL_MARGINAL_M
    yaw_m = float((mobel.get('rotation_rad') or [0, 0, 0])[2]); c, s = math.cos(yaw_m), math.sin(yaw_m)
    ax = np.array([c, s]); ay = np.array([-s, c]); hx, hy = float(mobel['matt_m'][0]) / 2., float(mobel['matt_m'][1]) / 2.
    villkor = []; poster = []
    for v in plan.get('objekt', []):
        if v.get('id') not in GENERERADE: continue
        m = np.asarray(v['matt_m'], float); p = np.asarray(v['pos_m'][:2], float); yaw = float((v.get('rotation_rad') or [0, 0, 0])[2])
        tunn = 0 if m[0] <= m[1] else 1
        n = np.array([math.cos(yaw), math.sin(yaw)]) if tunn == 0 else np.array([-math.sin(yaw), math.cos(yaw)])
        if float(n @ (np.asarray(inre_xy, float) - p)) < 0: n = -n
        inre = p + n * m[tunn] / 2.
        ext = abs(float(n @ ax)) * hx + abs(float(n @ ay)) * hy
        # n·xy >= n·inre + ext + marginal  <=>  -n·xy <= -(n·inre + ext + marginal)
        villkor.append((-n, -(float(n @ inre) + ext + MOBEL_MARGINAL_M)))
        poster.append(dict(vagg=v['id'], normal=[round(float(x), 3) for x in n], inre_yta=[round(float(x), 3) for x in inre], marginal_m=MOBEL_MARGINAL_M))
    return villkor, poster


def _harledd_mitt(spec, k):
    """Ett ensamt tal i mitt_* bredvid `framfor` är härlett av ingest/deklaration_till_hand.py:120 (rakt framför platsen), inte deklarerat."""
    return bool(spec.get('framfor')) and not isinstance(spec.get(k), (list, tuple))


def _intervallvillkor(spec):
    villkor = []; poster = {}
    for i, k in enumerate(('mitt_x_m', 'mitt_y_m')):
        sp = _spann_eller_tal(spec.get(k))
        if sp is None or _harledd_mitt(spec, k): continue      # härlett läge är förval (se _forval), inte villkor
        e = np.zeros(2); e[i] = 1.
        villkor += [(e, sp[1]), (-e, -sp[0])]; poster[k] = list(sp)
    return villkor, poster


def _forval(plan, pl, spec, mobel, bilder, fore_xy):
    """Förvalet: centrerat framför framfor-platsen mot gruppens kameror (bakkant BAKKANT_FORE_PERSON_M före platsen); deklarerad mitt går före."""
    kalla = 'möbelns tidigare läge (ingen framfor-plats)'; xy = np.asarray(fore_xy, float).copy()
    if spec.get('framfor'):
        person, _ = _framfor_ankare(pl, spec['framfor']); riktn = []
        for b in bilder:
            try:
                _, _, ruta = bilddata(plan, b); kxy, _ = _kamera(plan, ruta)
            except (ValueError, KeyError, TypeError, IndexError): continue
            d = kxy - person
            if np.linalg.norm(d) > 1e-6: riktn.append(d / np.linalg.norm(d))
        if riktn:
            r = np.mean(riktn, axis=0); r = r / max(np.linalg.norm(r), 1e-9)
            xy = person + r * (BAKKANT_FORE_PERSON_M + _djuphalva(mobel, r))
            kalla = f"framför {spec['framfor']} mot gruppens kameror, bakkant {BAKKANT_FORE_PERSON_M:.2f} m före platsen, centrerad"
    for i, k in enumerate(('mitt_x_m', 'mitt_y_m')):
        sp = _spann_eller_tal(spec.get(k))
        if sp is not None:
            xy[i] = (sp[0] + sp[1]) / 2.
            kalla += f'; {k} härlett framför platsen (deklaration_till_hand)' if _harledd_mitt(spec, k) else f'; {k} ur deklarationen'
    return xy, kalla


def _intervall(plan, tagningar):
    """Sammanhängande ut-intervall för tagningarnas scener."""
    from foremallyft import _scen
    iv = sorted(tuple(s['ut']) for s in (_scen(plan, t) for t in tagningar) if s and len(s.get('ut') or []) == 2)
    ut = []
    for a, b in iv:
        if ut and ut[-1][1] >= a: ut[-1][1] = max(ut[-1][1], b)
        else: ut.append([a, b])
    return ut


def _minus(helt, delar):
    ut = [list(helt)]
    for a, b in delar:
        ny = []
        for c, d in ut:
            if b <= c or a >= d: ny.append([c, d]); continue
            if c < a: ny.append([c, a])
            if b < d: ny.append([b, d])
        ut = ny
    return [x for x in ut if x[1] > x[0]]


def _kameror_i_mobel(plan, mobel, xy, intervall):
    """Utdatarutor i intervallen där renderkameran står inne i möbelns fotavtryck (under dess ovansida)."""
    nyck = (plan.get('renderkamera') or {}).get('nycklar') or []
    yaw = float((mobel.get('rotation_rad') or [0, 0, 0])[2]); c, s = math.cos(yaw), math.sin(yaw); R = np.array([[c, -s], [s, c]])
    hx, hy = float(mobel['matt_m'][0]) / 2., float(mobel['matt_m'][1]) / 2.; topp = float(mobel['pos_m'][2]) + float(mobel['matt_m'][2]) / 2.
    traff = []
    for a, b in intervall:
        for u in range(a, min(b, len(nyck))):
            C = np.asarray(nyck[u]['matris'], float)[:3, 3]; lok = R.T @ (C[:2] - np.asarray(xy, float))
            if abs(lok[0]) <= hx and abs(lok[1]) <= hy and C[2] <= topp: traff.append(u)
    return traff


def los_grupper(plan, pl, did, spec, mobel, bilder):
    """0012: en passning per kameragrupp. Returnerar rapportfält. Skriver kopior av möbeln och dess delar per synlighetsintervall."""
    from foremallyft import _scen
    fore = np.asarray(mobel['pos_m'], float).copy()
    N = len(plan.get('kallrutor') or (plan.get('renderkamera') or {}).get('nycklar') or [])
    grupper = {}
    for b in bilder:
        if not isinstance(b, dict) or not _scen(plan, b.get('tagning')): continue
        grupper.setdefault(str(b.get('grupp') or b.get('tagning')), []).append(b)
    if not grupper: raise ValueError('inga bildrutor med scen för någon kameragrupp')
    inre = _framfor_ankare(pl, spec['framfor'])[0] if spec.get('framfor') else fore[:2]
    vagg_v, vagg_p = _vaggvillkor(plan, mobel, inre)
    int_v, int_p = _intervallvillkor(spec)
    resultat = []
    for namn, gb in grupper.items():
        forval, forval_kalla = _forval(plan, pl, spec, mobel, gb, fore[:2])
        ordning = _ordningsdata(plan, pl, spec, mobel, gb)
        # Trohet per tagning först: passa utan ordningen, välj sedan den strängaste ordningsnivån som det läget redan uppfyller.
        # Uppfyller det ingen nivå används den lösaste (kameran aldrig i möbeln, marginal 0 m).
        niva, ord_v = 0, []
        if ordning is not None:
            fri_v = vagg_v + int_v if _projektera_halvplan(forval, vagg_v + int_v)[1] else int_v
            xy_fri, _ = passa_grupp(plan, mobel, gb, forval, fri_v)
            niva = next((i for i, (k_m, p_m) in enumerate(ORDNINGSNIVAER)
                         if all(float(a @ xy_fri) <= b + 1e-6 for a, b in _ordningsvillkor(ordning['data'], k_m, p_m))), len(ORDNINGSNIVAER) - 1)
            ord_v = _ordningsvillkor(ordning['data'], *ORDNINGSNIVAER[niva])
        villkor = vagg_v + int_v + ord_v; konflikt = None
        if not _projektera_halvplan(forval, villkor)[1]:
            villkor = vagg_v + int_v; konflikt = 'ordningen ryms inte tillsammans med väggar och intervall; ordningen släpps för gruppen'
            if not _projektera_halvplan(forval, villkor)[1]:
                villkor = int_v; konflikt = 'väggarna ryms inte heller; bara deklarerat intervall gäller'
        xy, info = passa_grupp(plan, mobel, gb, forval, villkor)
        medlemmar = sorted(set(namn.split('+')) | {b['tagning'] for b in gb}, key=lambda t: int(str(t)[1:]) if str(t)[1:].isdigit() else 0)
        r = dict(grupp=namn, tagningar=medlemmar, bilder=[b['tagning'] for b in gb], forval_kalla=forval_kalla, xy=xy, info=info,
                 intervall=_intervall(plan, medlemmar), konflikt=konflikt)
        if ordning is not None:
            r['ordning'] = _ordningsrapport(ordning, niva, forval, xy, niva not in (0, None))
            r['ordning']['val'] = 'strängaste nivån som passningen utan ordning redan uppfyller (0012: trohet per tagning först); annars den lösaste'
        resultat.append(r)
    huvud = max(resultat, key=lambda r: (len(r['bilder']), sum(len(p.get('likheter', {})) for p in r['info']['per_tagning'])))
    rest = _minus([0, N], [iv for r in resultat for iv in r['intervall']])
    huvud['intervall'] = sorted(huvud['intervall'] + rest)
    # Kopior: möbeln och allt som hör till den (ben, föremål på den) får en post per intervall med gruppens förskjutning.
    hor = lambda o: o.get('id') == did or str(o.get('id', '')).startswith(did + ':')
    nya = []
    for o in plan['objekt']:
        if not hor(o): nya.append(o); continue
        s0, s1 = o.get('synlig_ut', [0, N])
        for r in resultat:
            d = np.r_[r['xy'] - fore[:2], 0.]
            for a, b in r['intervall']:
                lo, hi = max(a, s0), min(b, s1)
                if lo >= hi: continue
                k = dict(o); k['pos_m'] = (np.asarray(o['pos_m'], float) + d).tolist(); k['synlig_ut'] = [lo, hi]; k['kameragrupp'] = r['grupp']
                nya.append(k)
    plan['objekt'] = nya
    dh = np.r_[huvud['xy'] - fore[:2], 0.]
    for p in plan.get('plats', []):
        for dl in (p.get('rumsmall') or {}).get('delar', []):
            if hor(dl): dl['pos_m'] = (np.asarray(dl['pos_m'], float) + dh).tolist()
    grupposter = []
    for r in resultat:
        pos = [float(r['xy'][0]), float(r['xy'][1]), float(fore[2])]
        g = dict(grupp=r['grupp'], tagningar=r['tagningar'], bilder=r['bilder'], synlig_ut=r['intervall'], pos_m=pos,
                 forval_kalla=r['forval_kalla'], kameror_i_mobel=_kameror_i_mobel(plan, mobel, r['xy'], r['intervall']), **r['info'])
        if r.get('ordning'): g['ordning'] = r['ordning']
        if r['konflikt']: g['konflikt'] = r['konflikt']
        grupposter.append(g)
    kval = {k: ('antagen' if any(g['kvalitet'][k] == 'antagen' for g in grupposter) else 'matt') for k in ('x', 'y')}
    slut = [float(huvud['xy'][0]), float(huvud['xy'][1]), float(fore[2])]
    return dict(status='flyttad', metod=GRUPP_METOD, fore_pos_m=fore.tolist(), efter_pos_m=slut, slutlig_pos_m=slut,
                huvudgrupp=huvud['grupp'], grupper=grupposter, kvalitet=kval, vaggar=vagg_p, deklarerat_intervall=int_p,
                klamd=False, klamningsgrans=None,
                granskonflikt=bool(any((g.get('ordning') or {}).get('granskonflikt') or g.get('konflikt') for g in grupposter)),
                kameror_i_mobel=sorted({u for g in grupposter for u in g['kameror_i_mobel']}),
                regel='lägena ligger inom deklarationens intervall för möbeln; mått och höjd är ett värde per klipp (mobelintervall.py)')
