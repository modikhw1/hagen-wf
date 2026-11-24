"""Gemensam robust passning av en fast 3D-låda mot bildrutor i flera tagningar."""
import math

import numpy as np
from scipy.optimize import least_squares


KANTGRANS = 10.0


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


def tillforlitligast(plan, bilder):
    """Boxen med flest obeskurna kanter, därefter störst bildyta."""
    kandidater = []
    for i, bild in enumerate(bilder):
        box, _, _ = bilddata(plan, bild)
        y0, x0, y1, x1 = box
        kandidater.append((len(anvanda_kanter(plan, box)), float(max(0., y1 - y0) * max(0., x1 - x0)), -i, bild))
    return max(kandidater, key=lambda x: x[:3])[3]


def _projektera_halvplan(xy, villkor):
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
    giltiga = [p for p in kandidater if all(float(a @ p) <= b + 1e-8 for a, b in villkor)]
    return (min(giltiga, key=lambda p: float(np.sum((p - xy) ** 2))), True) if giltiga else (xy, False)


def framfor_alla_kameror(plan, objekt, bilder, xy):
    """Närmaste XY där lådans samtliga hörn ligger framför varje bildkamera."""
    horn0 = _horn(objekt, [0., 0.]); villkor = []
    for bild in bilder:
        _, key, _ = bilddata(plan, bild); M = np.asarray(key['matris'], float)
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


def passa(plan, objekt, bilder, xy0, efterbehandling=None, rapport_xy0=None):
    """Passa XY robust mot minst två boxar och returnera läge, mätningar och lösarinfo."""
    obs = []
    for bild in bilder:
        box, key, ruta = bilddata(plan, bild)
        obs.append(dict(tagning=bild.get('tagning'), key=key, ruta=ruta,
                        mal=anvanda_kanter(plan, box)))
    if len(obs) < 2:
        raise ValueError('flerbildspassning kräver minst två bildrutor')
    xy0 = np.asarray(xy0, float)

    def rest(xy):
        svar = []
        straff = 2. * math.hypot(float(plan['utdata']['bredd']), float(plan['utdata']['hojd']))
        for o in obs:
            try:
                proj = projicerade_kanter(plan, objekt, xy, o['key'])
                svar.extend(proj[k] - v for k, v in o['mal'].items())
            except ValueError:
                svar.extend([straff] * len(o['mal']))
        return np.asarray(svar, float)

    fore = _matning(plan, objekt, xy0 if rapport_xy0 is None else np.asarray(rapport_xy0, float), obs)
    fit = least_squares(rest, xy0, bounds=(xy0 - 20., xy0 + 20.), method='trf',
                        loss='soft_l1', f_scale=20., x_scale='jac', max_nfev=120)
    xy = np.asarray(fit.x, float)
    extra = {}
    if efterbehandling is not None:
        xy, extra = efterbehandling(xy, obs)
        xy = np.asarray(xy, float)
    efter = _matning(plan, objekt, xy, obs)
    per_tagning = []
    for a, b in zip(fore, efter):
        per_tagning.append(dict(tagning=a['tagning'], ruta=a['ruta'], kanter=a['kanter'],
                                fore_anvand=a['anvand'], efter_anvand=b['anvand'],
                                fore_residualer_px=a['residualer_px'], fore_rms_px=a['rms_px'],
                                efter_residualer_px=b['residualer_px'], efter_rms_px=b['rms_px'],
                                **({'fore_orsak': a['orsak']} if not a['anvand'] else {}),
                                **({'efter_orsak': b['orsak']} if not b['anvand'] else {})))
    info = dict(loss='soft_l1', f_scale_px=20., antal_boxar=len(obs), antal_residualer=int(len(rest(xy))),
                lyckad=bool(fit.success), losarstatus=str(fit.message), per_tagning=per_tagning)
    info.update(extra or {})
    return xy, info
