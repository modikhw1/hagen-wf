"""Möbler (bord, disk) som deklarerat intervall som skymningskontrollen får justera inom.

Platsens `deklarerat.mobler` (skrivet av ingest/deklaration_till_hand.py ur plats/deklaration.json) anger per bord/disk höjd,
mått och mittpunkt som ett tal (hårt: lösaren rör det aldrig) eller [min, max] (lösaren får välja inom intervallet):

    mobler: {del_id: {hojd_m, langs_x_m, langs_y_m, mitt_x_m, mitt_y_m}}     (varje värde tal eller [min, max])

Lösaren väljer EN uppsättning värden per möbel för hela klippet (inte per tagning): den som ger minst skymningskonflikt över alla
tagningar gemensamt, mätt med skymningskontrollens egna regler (skymning.py: 2 % av maskproven, 10 % av en kroppsdel, 5 cm djupmarginal;
de gränserna rörs inte). Är möbeln inte flaggad i någon scen vid det deklarerade utgångsläget rörs den inte alls. Hittar lösaren
inget värde som klarar alla scener väljs det med minst konflikt, och skymningskontrollen (`skymning.los`) utelämnar möbeln i de
scener som ändå är flaggade, som förut. Valt värde, konflikt före/efter och om intervallets gräns nåddes redovisas i
plan.kvalitet.mobelintervall.

Mittpunkten i intervall ges i deklarationens ram; platsens passning (yaw) vrider förskjutningen in i platsens ram.
Inga modeller, inget nät: bara kropps- och maskcacharna som skymningskontrollen redan använder."""
import copy
import itertools
import math
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent
PARAMETRAR = ('hojd_m', 'langs_x_m', 'langs_y_m', 'mitt_x_m', 'mitt_y_m')
PUNKTER = {1: 7, 2: 5, 3: 5, 4: 4, 5: 3}     # antal värden per fritt intervall, efter hur många parametrar som är fria (begränsar antalet kombinationer till högst 125)
LIKA = 1e-9


def _spann(v):
    return (float(v[0]), float(v[1])) if isinstance(v, (list, tuple)) else (float(v), float(v))


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


def fria_parametrar(spec):
    """{parameter: (min, max)} för de värden i en möbels deklaration som är intervall med bredd. Tal och smala intervall är hårda."""
    ut = {}
    for k, v in (spec or {}).items():
        if k in PARAMETRAR and isinstance(v, (list, tuple)):
            lo, hi = _spann(v)
            if lo > hi: raise ValueError(f'Deklarerat intervall {k} {v} har min över max.')
            if hi - lo > LIKA: ut[k] = (lo, hi)
    return ut


def _tillampa(d, varden, mitt, yaw):
    """Kopia av mallens del med valda värden. Förskjutning av mittpunkten (jämfört med intervallets mitt) vrids in i platsens ram."""
    d = copy.deepcopy(d)
    for k, v in varden.items():
        if k == 'hojd_m': d['matt_m'][2] = float(v)
        elif k == 'langs_x_m': d['matt_m'][0] = float(v)
        elif k == 'langs_y_m': d['matt_m'][1] = float(v)
    dx, dy = varden.get('mitt_x_m', mitt['mitt_x_m']) - mitt['mitt_x_m'], varden.get('mitt_y_m', mitt['mitt_y_m']) - mitt['mitt_y_m']
    if abs(dx) > 0 or abs(dy) > 0:
        d['pos_m'][:2] = (np.asarray(d['pos_m'][:2], float) + _rz(yaw) @ np.array([dx, dy])).tolist()
    return d


def _lador(d):
    from rumsmall import byggobjekt
    return {o['id']: o for o in byggobjekt(dict(delar=[d]))}


def _kandidater(fria, bas, mitt):
    """Rutnät över de fria intervallen. Utgångsvärdet (mallens eget) tas alltid med."""
    n = PUNKTER[min(len(fria), 5)]
    lister = []
    for k, (lo, hi) in fria.items():
        v = list(np.linspace(lo, hi, n))
        b = bas.get(k, mitt.get(k))
        if b is not None and lo - LIKA <= b <= hi + LIKA: v.append(float(b))
        v = sorted({round(float(x), 9) for x in v})
        lister.append(v)
    return [dict(zip(fria, c)) for c in itertools.product(*lister)]


def _forbered(plan):
    """Allt som inte beror på möbelns geometri: maskprov och kamera per provruta (samma urval som skymning.mat)."""
    import datacache
    import skymning as S
    w = plan['kallbild_bredd']; h = plan['kallbild_hojd']; sigs = {}; scener = []
    S._KODNU[0] = None; S._KODNU[0] = datacache.kodnyckel([S.__file__]); S._LADNYCKEL.clear()
    for scene in plan.get('scener') or plan['matkamera']['scener']:
        a, b = scene['ut']; ruta = []
        for u in sorted(set(range(a, b, 3)) | {b - 1}):
            key = plan['matkamera']['nycklar'][u]
            f = scene['lokal_start'] + u - a if plan.get('scener') else plan['kallrutor'][u]
            prov = []
            for pm in scene['personer']:
                folder = Path(pm['rorelse']).parent; pid = pm.get('ingest_id') or Path(pm['rorelse']).stem[8:]
                raw = folder / 'kropp' / str(pid) / f'{f:04d}.npz'; maskfile = folder / 'masker.npy'
                if not raw.exists() or not maskfile.exists(): continue
                if folder not in sigs: sigs[folder] = datacache.signatur([maskfile])
                P, rk = S._rutdel(raw, maskfile, f, w, h, sigs[folder])
                if len(P['uv']): prov.append(P)
            ruta.append((u, key, prov))
        scener.append(dict(id=scene['id'], rutor=ruta))
    return w, h, scener


def _mat(forb, objekt, antal_rutor):
    """Skymning per scen för EN möbelgrupp (samma räkning och flaggregel som skymning.mat). Scener där möbeln inte syns hoppas över."""
    import skymning as S
    w, h, scener = forb; ut = []
    for sc in scener:
        n = den = 0; pc = np.zeros((len(S.DELAR), 2), int); sett = False
        for u, key, prov in sc['rutor']:
            objs = [o for o in objekt if o.get('synlig_ut', [0, antal_rutor])[0] <= u < o.get('synlig_ut', [0, antal_rutor])[1]]
            if not objs: continue
            sett = True
            for P in prov:
                hits = S.konflikt(P['uv'], P['dep'], key, w, h, objs, None)
                kombinerad = np.logical_or.reduce([hits[o['id']] for o in objs]); n += int(kombinerad.sum()); den += len(P['uv'])
                for j in range(len(S.DELAR)):
                    sel = P['delar'] == j; pc[j, 0] += int((kombinerad & sel).sum()); pc[j, 1] += int(sel.sum())
        if not sett: continue
        delar = [dict(del_=S.DELAR[j], skymda=int(pc[j, 0]), prov=int(pc[j, 1]), andel=float(pc[j, 0] / max(pc[j, 1], 1)))
                 for j in range(len(S.DELAR)) if pc[j, 0] >= S.DEL_MIN and pc[j, 0] / max(pc[j, 1], 1) > S.DEL_GRANS]
        andel = n / max(den, 1)
        ut.append(dict(scen=sc['id'], ockluderade_prov=n, synliga_maskprov=den, andel=float(andel),
                       flaggad=bool((andel > S.GRANS and n >= 10) or delar), flaggade_kroppsdelar=delar))
    return ut


def _poang(rader, avstand):
    """Lägre är bättre: antal flaggade scener, summa skymningsandel, avstånd från utgångsvärdet (så att inget flyttas utan skäl)."""
    return (sum(r['flaggad'] for r in rader), round(sum(r['andel'] for r in rader), 12), avstand)


def losa(plan, platser):
    """Väljer värde inom deklarerade intervall för varje möbel och skriver det i plan['objekt']. Returnerar lista av poster (tom om inget är deklarerat som intervall)."""
    jobb = []
    for plid, pl in (platser or {}).items():
        rm = pl.get('rumsmall'); mob = (pl.get('deklarerat') or {}).get('mobler')
        if not rm or not mob: continue
        for did, spec in mob.items():
            d = next((x for x in rm['delar'] if x['id'] == did), None)
            fria = fria_parametrar(spec)
            if d is not None and fria: jobb.append((plid, rm, d, spec, fria))
    if not jobb: return []
    forb = _forbered(plan); N = len(plan['kallrutor']); poster = []
    for plid, rm, d, spec, fria in jobb:
        yaw = float(((rm.get('passning') or {}).get('yaw_rad')) or 0.)
        mitt = {k: float(np.mean(_spann(spec[k]))) for k in ('mitt_x_m', 'mitt_y_m') if k in spec}
        mitt.setdefault('mitt_x_m', 0.); mitt.setdefault('mitt_y_m', 0.)
        bas = {'hojd_m': d['matt_m'][2], 'langs_x_m': d['matt_m'][0], 'langs_y_m': d['matt_m'][1], 'mitt_x_m': mitt['mitt_x_m'], 'mitt_y_m': mitt['mitt_y_m']}
        grundlador = _lador(d); did = d['id']
        grupp = [o for o in plan['objekt'] if o['id'] == did or o['id'].startswith(did + ':')]
        if not grupp: continue

        ordning = {i: k for k, i in enumerate(grundlador)}; gl = list(grundlador.values())

        def med(varden):
            # Lådorna matchas på plats i mallens ordning, inte på id: benens id bär deras förskjutning (x:y) och ändras när måtten ändras.
            nyl = list(_lador(_tillampa(d, varden, mitt, yaw)).values()); ut = []
            for o in grupp:
                n = copy.deepcopy(o); k = ordning.get(o['id'])
                if k is not None and k < len(nyl):
                    n['pos_m'] = (np.asarray(o['pos_m'], float) + np.asarray(nyl[k]['pos_m'], float) - np.asarray(gl[k]['pos_m'], float)).tolist()
                    n['matt_m'] = list(nyl[k]['matt_m']); n['fas_m'] = nyl[k]['fas_m']
                ut.append(n)
            return ut

        skala = {k: max(hi - lo, LIKA) for k, (lo, hi) in fria.items()}
        avst = lambda v: float(math.sqrt(sum(((v[k] - bas[k]) / skala[k]) ** 2 for k in fria)))
        fore_v = {k: bas[k] for k in fria}; fore = _mat(forb, med(fore_v), N)
        kandidater = _kandidater(fria, bas, mitt)
        valt_v, valt = fore_v, fore
        if any(r['flaggad'] for r in fore):     # rör bara möbeln när kontrollen annars skulle utelämna den
            basp = _poang(fore, 0.); bast = (basp, fore_v, fore)
            for v in kandidater:
                if all(abs(v[k] - fore_v[k]) < LIKA for k in fria): continue
                r = _mat(forb, med(v), N); p = _poang(r, avst(v))
                if p < bast[0]: bast = (p, v, r)
            valt_v, valt = bast[1], bast[2]
        nya = med(valt_v)
        # Scenspecifika kopior av samma delar (olika synlig_ut) byts var och en mot sin egen nya geometri.
        ersatt = {}
        for o, n in zip(grupp, nya): ersatt[id(o)] = n
        plan['objekt'] = [ersatt.get(id(o), o) for o in plan['objekt']]
        param = {}
        for k, (lo, hi) in fria.items():
            v = valt_v[k]
            param[k] = dict(deklarerat=[lo, hi], utgangsvarde=float(fore_v[k]), valt=float(v),
                            grans_nadd='min' if abs(v - lo) < 1e-6 else 'max' if abs(v - hi) < 1e-6 else None)
        fasta = {k: _spann(v)[0] for k, v in spec.items() if k in PARAMETRAR and k not in fria}
        poster.append(dict(plats=plid, del_id=did, parametrar=param, hardvarden=fasta, kandidater=len(kandidater), granser_nadda=[k for k, p in param.items() if p['grans_nadd']],
                           fore=dict(varden=fore_v, per_scen=fore, flaggade_scener=[r['scen'] for r in fore if r['flaggad']]),
                           efter=dict(varden=valt_v, per_scen=valt, flaggade_scener=[r['scen'] for r in valt if r['flaggad']]),
                           atgard='oförändrad' if valt_v == fore_v else 'justerad', status='antagen',
                           regel='Ett värde per möbel för hela klippet. Möbeln rörs bara om minst en scen är flaggad vid utgångsvärdet; då väljs det värde i rutnätet över intervallen '
                                 'med minst (antal flaggade scener, summa skymningsandel), vid lika det närmast utgångsvärdet. Skymningskontrollens gränser (2 %, 10 % per kroppsdel, 5 cm) är orörda; '
                                 'scener som ändå är flaggade utelämnar möbeln som förut.'))
    return poster


def skriv_i_plats(plan):
    """Lägger de valda måtten i planens kopia av rumsmallen (plan['plats'][].rumsmall.delar) så att planen är samstämmig."""
    for p in plan['kvalitet'].get('mobelintervall') or []:
        for pl in plan.get('plats', []):
            if pl['id'] != p['plats'] or not pl.get('rumsmall'): continue
            for d in pl['rumsmall']['delar']:
                if d['id'] != p['del_id']: continue
                yaw = float(((pl['rumsmall'].get('passning') or {}).get('yaw_rad')) or 0.)
                v = p['efter']['varden']; u = p['fore']['varden']
                if 'hojd_m' in v: d['matt_m'][2] = v['hojd_m']
                if 'langs_x_m' in v: d['matt_m'][0] = v['langs_x_m']
                if 'langs_y_m' in v: d['matt_m'][1] = v['langs_y_m']
                dx, dy = v.get('mitt_x_m', 0.) - u.get('mitt_x_m', 0.), v.get('mitt_y_m', 0.) - u.get('mitt_y_m', 0.)
                if dx or dy: d['pos_m'][:2] = (np.asarray(d['pos_m'][:2], float) + _rz(yaw) @ np.array([dx, dy])).tolist()
