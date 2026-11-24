"""Placera deklarerade möbler från originalets bildruta mot slutkameran.

Bildrutan ligger i ``plats[].deklarerat.mobler`` och berör därför inte den strikt
validerade rumsmallen. Modulen körs efter bildkamera. För bildbekräftade möbler
körs den före möbelintervall/skymning, så att intervallet prövas på rätt plats;
vägganpassning och föremålslyft ser sedan den färdiga geometrin.
"""
import math
import numpy as np

from foremallyft import _flytta, _traff
from boxpassning import framfor_alla_kameror, passa, tillforlitligast


METOD = ('Stråle genom box_2d:s valda kant mot golv eller vald möbelhöjd med planens '
         'slutliga renderkamera; möbeln flyttas endast i XY och behåller mått, höjd och yaw. '
         'Med framfor hålls djupordningen kamera–möbel–person.')
FLER_METOD = ('Robust soft-L1-passning av fast möbellådas synliga bildkanter mot alla bilder med '
              'varje tagnings slutliga renderkamera; XY är fritt medan mått, höjd och yaw är fasta. '
              'Djupordningen kamera–möbel–person kläms samtidigt för alla tagningar.')


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


def _projektera_halvplan(xy, villkor):
    """Närmaste punkt i skärningen av a·xy <= b för ett tvådimensionellt läge."""
    xy = np.asarray(xy, float)
    kandidater = [xy]
    for a, b in villkor:
        a = np.asarray(a, float); kandidater.append(xy - max(0., float(a @ xy - b)) / float(a @ a) * a)
    for i, (a, b) in enumerate(villkor):
        for c, d in villkor[i + 1:]:
            A = np.asarray([a, c], float)
            if abs(float(np.linalg.det(A))) > 1e-10:
                kandidater.append(np.linalg.solve(A, np.asarray([b, d], float)))
    giltiga = [p for p in kandidater if all(float(a @ p) <= b + 1e-8 for a, b in villkor)]
    if not giltiga:
        return xy, False
    return min(giltiga, key=lambda p: float(np.sum((p - xy) ** 2))), True


def _klam_flera(plan, pl, spec, mobel, xy, obs):
    """Kläm samma XY mot varje bildkameras deklarerade kamera–möbel–person-ordning."""
    ankare_id = spec.get('framfor')
    if not ankare_id:
        return xy, dict(klamd=False, klamningsgrans=None, granskonflikt=False, klamningar=[])
    person_xy, ankarkalla = _framfor_ankare(pl, ankare_id)
    villkor = []; data = []; konflikt = False
    for o in obs:
        kamera_xy, fram = _kamera(plan, o['ruta']); halva = _djuphalva(mobel, fram)
        persondjup = float((person_xy - kamera_xy) @ fram)
        undre, ovre = .30 + halva, persondjup - .10 - halva
        lokal_konflikt = undre > ovre
        konflikt = konflikt or lokal_konflikt
        # Samma prioritering som enbildsvägen: vid omöjligt intervall skyddas personmarginalen.
        if not lokal_konflikt:
            villkor.append((-fram, -(undre + float(kamera_xy @ fram))))
        villkor.append((fram, ovre + float(kamera_xy @ fram)))
        data.append(dict(tagning=o['tagning'], ruta=int(o['ruta']), kamera_xy=kamera_xy,
                         fram=fram, halva=halva, persondjup=persondjup, undre=undre, ovre=ovre,
                         granskonflikt=lokal_konflikt))
    nytt, genomforbart = _projektera_halvplan(xy, villkor)
    konflikt = konflikt or not genomforbart
    if not genomforbart:
        # Skydda i första hand samtliga personmarginaler om alla intervall tillsammans saknar skärning.
        personvillkor = [(d['fram'], d['ovre'] + float(d['kamera_xy'] @ d['fram'])) for d in data]
        nytt, _ = _projektera_halvplan(xy, personvillkor)
    poster = []
    for d in data:
        fore = float((xy - d['kamera_xy']) @ d['fram']); efter = float((nytt - d['kamera_xy']) @ d['fram'])
        poster.append(dict(tagning=d['tagning'], ruta=d['ruta'], centrumdjup_fore_m=fore,
                           centrumdjup_efter_m=efter, centrumdjup_granser_m=[d['undre'], d['ovre']],
                           uppnadd_kameramarginal_m=efter - d['halva'],
                           uppnadd_personmarginal_m=d['persondjup'] - (efter + d['halva']),
                           granskonflikt=d['granskonflikt']))
    flyttad = not np.allclose(nytt, xy, atol=1e-9, rtol=0.)
    return nytt, dict(klamd=flyttad, klamningsgrans='flera_tagningar' if flyttad else None,
                      framfor=ankare_id, framfor_ankare_kalla=ankarkalla,
                      granskonflikt=konflikt, klamningar=poster,
                      regel='framkant minst 0,30 m efter varje kamera; bakkant minst 0,10 m före framfor-platsen')


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
            if len(bilder) > 1:
                fore = np.asarray(mobel['pos_m'], float).copy()
                bast = tillforlitligast(plan, bilder); startorsak = None
                try: start = _enbildslage(plan, pl, spec, mobel, bast)
                except (KeyError, TypeError, ValueError, IndexError) as ex:
                    start = fore[:2].copy(); startorsak = str(ex)
                start, framfor_alla = framfor_alla_kameror(plan, mobel, bilder, start)
                efter_xy, info = passa(plan, mobel, bilder, start,
                                       lambda xy, obs: _klam_flera(plan, pl, spec, mobel, xy, obs),
                                       rapport_xy0=fore[:2])
                efter = fore.copy(); efter[:2] = efter_xy
                _flytta(plan, did, efter - fore)
                post.update(status='flyttad', metod=FLER_METOD, fore_pos_m=fore.tolist(),
                            efter_pos_m=efter.tolist(), slutlig_pos_m=efter.tolist(),
                            start_tagning=bast.get('tagning'), start_pos_m=[float(start[0]), float(start[1]), float(fore[2])],
                            start_framfor_alla_kameror=framfor_alla,
                            **({'start_orsak': startorsak} if startorsak else {}), **info)
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
