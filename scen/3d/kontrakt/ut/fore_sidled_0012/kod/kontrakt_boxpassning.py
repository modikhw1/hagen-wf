"""Gemensam robust passning av en fast 3D-låda mot bildrutor i flera tagningar."""
import math

import numpy as np
from scipy.optimize import least_squares


KANTGRANS = 10.0
AVVIKELSEGRANS_M = .75            # lyft längre än så från medianen på golvet är en avvikande box (kräver minst tre boxar)
SOKRADIE_M = 4.0                  # sökområde kring startläget i x och y
VILLKORSSTRAFF_PX_PER_M = 2000.   # straff i pixlar per meter ett kamera–möbel–person-villkor bryts
SVAG_PX_PER_M = 100.              # riktningar där kanterna rör sig mindre än så per meter räknas som obestämda och låses vid startläget
OMPROVNINGSGRANS_PX = 50.         # en box utesluts i andra varvet om dess RMS är över detta ...
OMPROVNINGSFAKTOR = 2.5           # ... och över så många gånger medianen av boxarnas RMS


def bilddata(plan, bild):
    """Validerad box, slutkameranyckel och utdataruta för bildens tagning."""
    from foremallyft import _scen

    box = bild.get('box_2d') if isinstance(bild, dict) else None
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        raise ValueError('box_2d saknas eller har inte fyra tal')
    try:
        box = np.asarray([float(v) for v in box], float)
    except (TypeError, ValueError):
        raise ValueError('box_2d innehåller annat än tal')
    if not np.all(np.isfinite(box)):
        raise ValueError('box_2d innehåller ett ogiltigt tal')
    scen = _scen(plan, bild.get('tagning'))
    if not scen:
        raise ValueError(f"tagningen {bild.get('tagning')!r} saknar scen med ut-intervall")
    if len(scen.get('ut') or []) != 2 or scen['ut'][1] <= scen['ut'][0]:
        raise ValueError('tagningens ut-intervall är tomt')
    ruta = (int(scen['ut'][0]) + int(scen['ut'][1]) - 1) // 2
    nycklar = (plan.get('renderkamera') or {}).get('nycklar') or []
    if not 0 <= ruta < len(nycklar):
        raise ValueError('renderkameran saknar en nyckel i tagningens ut-intervall')
    return box, nycklar[ruta], ruta


def _horn(objekt, xy):
    matt = objekt.get('matt_m') or []
    pos = objekt.get('pos_m') or []
    if len(matt) != 3 or min(float(v) for v in matt) <= 0:
        raise ValueError('lådmått saknas eller är inte positiva')
    if len(pos) != 3:
        raise ValueError('lådans position saknas')
    yaw = float((objekt.get('rotation_rad') or [0, 0, 0])[2])
    c, s = math.cos(yaw), math.sin(yaw)
    R = np.array([[c, -s], [s, c]])
    hx, hy, hz = np.asarray(matt, float) / 2.
    fot = np.array([[a, b] for a in (-hx, hx) for b in (-hy, hy)]) @ R.T + np.asarray(xy, float)
    return np.vstack((np.c_[fot, np.full(4, float(pos[2]) - hz)],
                      np.c_[fot, np.full(4, float(pos[2]) + hz)]))


def projicerade_kanter(plan, objekt, xy, key):
    """Axisriktade bildkanter; toppen mäts enbart från lådans övre plan."""
    w = float(plan['utdata']['bredd']); h = float(plan['utdata']['hojd'])
    sensor = float((plan.get('renderkamera') or {}).get('sensor_bredd_mm', 36.))
    lins = float(key['lins_mm'])
    if min(w, h, sensor, lins) <= 0:
        raise ValueError('kamera eller bildmått är inte positiva')
    M = np.asarray(key['matris'], float)
    if M.shape != (4, 4) or not np.all(np.isfinite(M)):
        raise ValueError('kameramatrisen är ogiltig')
    horn = _horn(objekt, xy)
    lokalt = (horn - M[:3, 3]) @ M[:3, :3]
    djup = -lokalt[:, 2]
    if np.any(djup <= 1e-6):
        raise ValueError('lådan ligger i eller bakom kameran')
    fok = lins / sensor * w
    uv = lokalt[:, :2] / djup[:, None] * np.array([fok, -fok]) + np.array([w / 2., h / 2.])
    return dict(vanster=float(np.min(uv[:, 0])), hoger=float(np.max(uv[:, 0])),
                botten=float(np.max(uv[:, 1])), topp=float(np.min(uv[4:, 1])))


def anvanda_kanter(plan, box):
    """Målvärden i utdatapixlar för boxkanter som inte är bildbeskurna."""
    y0, x0, y1, x1 = box
    w = float(plan['utdata']['bredd']); h = float(plan['utdata']['hojd'])
    kanter = {}
    if x0 > KANTGRANS: kanter['vanster'] = float(x0 / 1000. * w)
    if x1 < 1000. - KANTGRANS: kanter['hoger'] = float(x1 / 1000. * w)
    if y0 > KANTGRANS: kanter['topp'] = float(y0 / 1000. * h)
    if y1 < 990.: kanter['botten'] = float(y1 / 1000. * h)
    if not kanter:
        raise ValueError('bildrutan har inga obeskurna kanter att passa')
    return kanter


def klassa_bilder(plan, bilder):
    """Delar boxarna i användbara och hoppade (ogiltig box, saknad kamera eller inga obeskurna kanter).

    En enda dålig box får aldrig avbryta passningen; den hoppas över med en orsak.
    """
    anv, hoppade = [], []
    for idx, bild in enumerate(bilder):
        tagning = bild.get('tagning') if isinstance(bild, dict) else None
        try:
            box, key, ruta = bilddata(plan, bild)
            mal = anvanda_kanter(plan, box)
        except (ValueError, KeyError, TypeError, IndexError) as ex:
            hoppade.append(dict(idx=idx, tagning=tagning, orsak=str(ex)))
            continue
        anv.append(dict(idx=idx, tagning=tagning, bild=bild, box=box, key=key, ruta=int(ruta), mal=mal))
    return anv, hoppade


def tillforlitligast(plan, bilder):
    """Boxen med flest obeskurna kanter, därefter störst bildyta. Behållen för äldre anrop; passningen använder `startlage`."""
    anv, _ = klassa_bilder(plan, bilder)
    if not anv:
        raise ValueError('ingen box har obeskurna kanter att passa')
    kandidater = []
    for a in anv:
        y0, x0, y1, x1 = a['box']
        kandidater.append((len(a['mal']), float(max(0., y1 - y0) * max(0., x1 - x0)), -a['idx'], a['bild']))
    return max(kandidater, key=lambda x: x[:3])[3]


def startlage(plan, bilder, enbild, grans_m=AVVIKELSEGRANS_M):
    """Startläge som median av enbildslägena, samt vilka boxar som ligger för långt ifrån medianen.

    ``enbild(bild)`` ger ett XY ur en enda box och får kasta ValueError/KeyError. Avvikande boxar pekas ut först när det
    finns minst tre lyft (med två går det inte att säga vilken som är fel) och uteslutande ur startvärdet; passningen
    får därefter utesluta dem ur anpassningen.
    """
    lyft = {}; fel = []
    for idx, bild in enumerate(bilder):
        tagning = bild.get('tagning') if isinstance(bild, dict) else None
        try:
            lyft[idx] = (tagning, np.asarray(enbild(bild), float)[:2])
        except (ValueError, KeyError, TypeError, IndexError) as ex:
            fel.append(dict(tagning=tagning, orsak=str(ex)))
    if not lyft:
        raise ValueError('inget enbildslyft kunde beräknas')
    punkter = np.array([p for _, p in lyft.values()])
    median = np.median(punkter, axis=0)
    avst = {i: float(np.hypot(*(p - median))) for i, (_, p) in lyft.items()}
    avvikande = []
    if len(lyft) >= 3:
        avvikande = [dict(tagning=lyft[i][0], avstand_till_median_m=round(d, 3)) for i, d in avst.items() if d > grans_m]
    ute = {a['tagning'] for a in avvikande}
    kvar = [p for _, (t, p) in lyft.items() if t not in ute] or list(punkter)
    start = np.median(np.array(kvar), axis=0)
    return start, dict(enbildslyft={t: [round(float(v), 3) for v in p] for t, p in lyft.values()},
                       median_xy=[round(float(v), 3) for v in median], start_xy=[round(float(v), 3) for v in start],
                       avvikande_boxar=avvikande, avvikelsegrans_m=grans_m, enbildsfel=fel)


def _projektera_halvplan(xy, villkor):
    """Närmaste punkt i skärningen av a·xy <= b för ett tvådimensionellt läge. Returnerar (punkt, genomförbart)."""
    xy = np.asarray(xy, float); kandidater = [xy]
    for a, b in villkor:
        a = np.asarray(a, float)
        if float(a @ a) > 1e-12:
            kandidater.append(xy - max(0., float(a @ xy - b)) / float(a @ a) * a)
    for i, (a, b) in enumerate(villkor):
        for c, d in villkor[i + 1:]:
            A = np.asarray([a, c], float)
            if abs(float(np.linalg.det(A))) > 1e-10:
                kandidater.append(np.linalg.solve(A, np.asarray([b, d], float)))
    giltiga = [p for p in kandidater if all(float(np.asarray(a) @ p) <= b + 1e-8 for a, b in villkor)]
    return (min(giltiga, key=lambda p: float(np.sum((p - xy) ** 2))), True) if giltiga else (xy, False)


def framfor_alla_kameror(plan, objekt, bilder, xy):
    """Närmaste XY där lådans samtliga hörn ligger framför varje bildkamera. Boxar utan giltig kamera hoppas över."""
    horn0 = _horn(objekt, [0., 0.]); villkor = []
    for bild in bilder:
        try:
            _, key, _ = bilddata(plan, bild)
        except (ValueError, KeyError, TypeError, IndexError):
            continue
        M = np.asarray(key['matris'], float)
        fram = M[:3, :3] @ np.array([0., 0., -1.])
        for horn in horn0:
            # (horn + [x,y,0] - kamera)·fram >= 1 mm.
            a = -fram[:2]; b = float((horn - M[:3, 3]) @ fram - .001)
            if float(a @ a) <= 1e-12 and b < 0: return np.asarray(xy, float), False
            villkor.append((a, b))
    return _projektera_halvplan(xy, villkor)


def _matning(plan, objekt, xy, obs):
    poster = []
    for o in obs:
        try:
            proj = projicerade_kanter(plan, objekt, xy, o['key'])
            fel = {kant: float(proj[kant] - mal) for kant, mal in o['mal'].items()}
            poster.append(dict(tagning=o['tagning'], ruta=int(o['ruta']), kanter=list(o['mal']), anvand=True,
                               residualer_px=fel, rms_px=float(np.sqrt(np.mean(np.square(list(fel.values())))))))
        except ValueError as ex:
            poster.append(dict(tagning=o['tagning'], ruta=int(o['ruta']), kanter=list(o['mal']), anvand=False,
                               residualer_px={}, rms_px=None, orsak=str(ex)))
    return poster


def passa(plan, objekt, bilder, xy0, efterbehandling=None, rapport_xy0=None, uteslut=None, villkor=None,
          sokradie_m=SOKRADIE_M, omprovning=True):
    """Passa XY robust mot minst två användbara boxar och returnera läge, mätningar och lösarinfo.

    - Boxar utan obeskurna kanter eller giltig kamera hoppas över (``hoppad_orsak``), de avbryter inte passningen.
    - ``uteslut`` (tagnings-id) mäts och redovisas men ingår inte i anpassningen.
    - ``villkor`` är halvplan a·xy <= b (kamera–möbel–person-ordningen). De är straffade i själva passningen och läget
      projiceras till det genomförbara området, så att ``lyckad`` gäller läget som faktiskt används.
    """
    uteslut = set(uteslut or ()); villkor = [(np.asarray(a, float), float(b)) for a, b in (villkor or [])]
    anv, hoppade = klassa_bilder(plan, bilder)
    obs = [dict(idx=a['idx'], tagning=a['tagning'], key=a['key'], ruta=a['ruta'], mal=a['mal'],
                i_passning=a['tagning'] not in uteslut) for a in anv]
    if sum(o['i_passning'] for o in obs) < 2:
        raise ValueError('flerbildspassning kräver minst två användbara bildrutor')
    xy0 = np.asarray(xy0, float)
    straff = 2. * math.hypot(float(plan['utdata']['bredd']), float(plan['utdata']['hojd']))
    passade = [o for o in obs if o['i_passning']]

    def rest(xy):
        svar = []
        for o in passade:
            try:
                proj = projicerade_kanter(plan, objekt, xy, o['key'])
                svar.extend(proj[k] - v for k, v in o['mal'].items())
            except ValueError:
                svar.extend([straff] * len(o['mal']))
        for a, b in villkor:
            svar.append(VILLKORSSTRAFF_PX_PER_M * max(0., float(a @ np.asarray(xy, float) - b)))
        return np.asarray(svar, float)


    def kantrest(xy):
        svar = []
        for o in passade:
            try:
                proj = projicerade_kanter(plan, objekt, xy, o['key'])
                svar.extend(proj[k] - v for k, v in o['mal'].items())
            except ValueError:
                svar.extend([straff] * len(o['mal']))
        return np.asarray(svar, float)

    def las_svaga(xy):
        """Riktningar i XY som kanterna knappt känner av (singulärvärde under SVAG_PX_PER_M) låses vid startläget."""
        h = 1e-3; xy = np.asarray(xy, float)
        J = np.column_stack([(kantrest(xy + h * e) - kantrest(xy - h * e)) / (2 * h) for e in np.eye(2)])
        _, S, Vt = np.linalg.svd(J, full_matrices=True); lasta = []
        for i in range(2):
            sv = float(S[i]) if i < len(S) else 0.
            if sv < SVAG_PX_PER_M:
                v = Vt[i]; xy = xy - float((xy - xy0) @ v) * v
                lasta.append(dict(riktning=[round(float(c), 3) for c in v], kantkanslighet_px_per_m=round(sv, 1)))
        return xy, lasta

    fore = _matning(plan, objekt, xy0 if rapport_xy0 is None else np.asarray(rapport_xy0, float), obs)
    xy_start = xy0; efterfit_ute = []
    while True:
        fit = least_squares(rest, xy_start, bounds=(xy0 - sokradie_m, xy0 + sokradie_m), method='trf',
                            loss='soft_l1', f_scale=20., x_scale='jac', max_nfev=120)
        xy, lasta = las_svaga(np.asarray(fit.x, float))
        if not omprovning or len(passade) <= 2: break
        # Andra varvet: boxen som passar sämst utesluts när den är långt sämre än typvärdet (en i taget, minst två kvar).
        rms = [m['rms_px'] if m['rms_px'] is not None else straff for m in _matning(plan, objekt, xy, passade)]
        grans = max(OMPROVNINGSGRANS_PX, OMPROVNINGSFAKTOR * float(np.median(rms)))
        i = int(np.argmax(rms))
        if rms[i] <= grans: break
        o = passade.pop(i); o['i_passning'] = False
        o['orsak_ute'] = f'passade inte med övriga efter första passningen ({rms[i]:.0f} px mot gränsen {grans:.0f} px)'
        efterfit_ute.append(dict(tagning=o['tagning'], rms_px=round(rms[i], 1), grans_px=round(grans, 1)))
        xy_start = xy0                    # ny anpassning från ursprungsläget så att den uteslutna boxen inte lämnar spår i x/y
    villkor_ok = True; villkor_flytt = 0.
    if villkor:
        fore_proj = xy.copy(); xy, villkor_ok = _projektera_halvplan(xy, villkor)
        villkor_flytt = float(np.hypot(*(xy - fore_proj)))
    extra = {}; efter_flytt = 0.
    if efterbehandling is not None:
        fore_eb = xy.copy(); xy, extra = efterbehandling(xy, obs); xy = np.asarray(xy, float)
        efter_flytt = float(np.hypot(*(xy - fore_eb)))
    efter = _matning(plan, objekt, xy, obs)
    per = {}
    for o, a, b in zip(obs, fore, efter):
        post = dict(tagning=a['tagning'], ruta=a['ruta'], kanter=a['kanter'], i_passning=o['i_passning'],
                    fore_anvand=a['anvand'], efter_anvand=b['anvand'],
                    fore_residualer_px=a['residualer_px'], fore_rms_px=a['rms_px'],
                    efter_residualer_px=b['residualer_px'], efter_rms_px=b['rms_px'])
        if not a['anvand']: post['fore_orsak'] = a['orsak']
        if not b['anvand']: post['efter_orsak'] = b['orsak']
        if not o['i_passning']: post['uteslutningsorsak'] = o.get('orsak_ute') or 'avvikande box; ingår inte i anpassningen'
        per[o['idx']] = post
    for h in hoppade:
        per[h['idx']] = dict(tagning=h['tagning'], ruta=None, kanter=[], i_passning=False, fore_anvand=False, efter_anvand=False,
                             fore_residualer_px={}, fore_rms_px=None, efter_residualer_px={}, efter_rms_px=None,
                             hoppad_orsak=h['orsak'])
    per_tagning = [per[i] for i in sorted(per)]
    lyckad = bool(fit.success and villkor_ok)
    info = dict(loss='soft_l1', f_scale_px=20., sokradie_m=sokradie_m, antal_boxar=len(bilder),
                antal_boxar_i_passning=len(passade), antal_residualer=int(sum(len(o['mal']) for o in passade)),
                lyckad=lyckad, lyckad_slutlage=bool(lyckad and efter_flytt <= .02), losarstatus=str(fit.message),
                antal_villkor=len(villkor), villkor_uppfyllda=bool(villkor_ok), villkor_flyttade_m=round(villkor_flytt, 4),
                efterbehandling_flyttade_m=round(efter_flytt, 4),
                hoppade_boxar=[dict(tagning=h['tagning'], orsak=h['orsak']) for h in hoppade],
                uteslutna_boxar=sorted({str(t) for t in uteslut} | {str(e['tagning']) for e in efterfit_ute}),
                uteslutna_efter_passning=efterfit_ute, last_riktningar=lasta, per_tagning=per_tagning)
    info.update(extra or {})
    return xy, info
