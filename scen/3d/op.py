"""op.py: semantiska operationer på scen3d.json (Scen3D, fas 3).

Varje operation är liten, loggas i scen3d.json:editLog (med tid i ms), sparar föregående version i historik/ och kan ångras.
Uppspelaren (index.html) läser om scen3d.json inom 1 s.

VÄLJARE (överlever ombyggen, eftersom de bygger på roller och etiketter):
  A, B, C            aktör (roll)
  A:cup, B:burger    föremål via ägare:etikett  (även exakt id)
  S1:burger          föremål med etiketten 'burger' som syns i tagning S1 (tagningens aktör föredras)
  table:A, seat:B    möbler/rum via exakt id i 'set'
  A:huvud            punkt: aktörens huvud (för kamera/vändning)

KOMMANDON (exempel):
  list                                        alla adresserbara saker per tagning
  show S1:burger                              visa ett föremål / en aktör / en tagning
  flytta A:cup --mot A --m 0.12 [--tagning S1]   flytta mot en annan sak (meter i golvplanet)
  flytta A:cup --dx 0.1 --dz -0.05 [--tagning S1]
  rotera A:cup --yaw 30
  byt A:burger --typ pizza_slice              byt föremålstyp (förpackningen är eget föremål och behålls)
  dolj S1:can [--tagning S1]  /  visa ...
  dolly S6 --mot A:huvud --faktor 0.6         kameran åker mot målet under tagningen (0.6 = slutar på 60 % av avståndet)
  zoom S6 --fov 50                            gradvis zoom under tagningen
  orbit S8 --runt B --grader 90 [--radie 1.6] kameran kretsar runt en punkt under tagningen
  kamera S2 --pos x,y,z --mal x,y,z [--fov 68]
  langd S4 --s 1.6 [--lage replik|trim|stretch] [--tal-max 1.15]
                                              replik (standard) = pauser krymper/växer, talet max x1.15, ord klipps aldrig;
                                              trim = klipp slutet (varnar om ord klipps); stretch = hela tagningen sakta/snabba
  duplicera S7 --som S8 [--med-ljud]          ny tagning efter originalet; tyst som standard (repliken upprepas inte)
  ta-bort S3  /  flytta-tagning S6 --fore S5 | --sist
  lagg-till-aktor S6 C --bakom A --avstand 1.1 --sida 0.45 --vand-mot A [--fran-tagning S4]
  vand S4 C --mot A                           aktören vänder kroppen mot målet (endast i tagningen)
  titta S4 C --mot A [--mangd 0.85] [--fran 0.2] [--ramp 0.35]   bara huvudet vrids mot målet (högst 80°)
  spegla S2 B
  intensitet S1 A --varde 1.6                 (tagning 'alla' = aktörens grundvärde)
  humor S6 A --namn stressed --mangd 0.8      (stressed|happy|angry|sad|neutral)
  utseende A --nyckel shirt --varde #3a3f58
  replik 3 --text "För det är ju så riktiga män gör."   ny text i samma lucka: designad röst (~1 s), teleprompter; rälsen varnar om farten
  casting A --roll Ägaren [--rost alma|lisa|nst] [--farg #a05a3c]   rollnamn i textningen, röst och tröjfärg
  angra                                       återställ föregående version
  normalisera                                 (körs automatiskt) frys källkameror per tagning
"""
import json, sys, time, math, shutil, copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIL = ROOT / 'scen3d.json'; HIST = ROOT / 'historik'

def las(): return json.load(open(FIL, encoding='utf-8'))
def spara(S): FIL.write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding='utf-8')
def fel(msg): print('FEL:', msg); sys.exit(2)
def arg(namn, std=None):
    a = sys.argv
    return a[a.index('--' + namn) + 1] if '--' + namn in a else std
def vec(s): return [float(x) for x in s.split(',')]

# ---------- uppslag
def tagning(S, sid):
    for s in S['shots']:
        if s['id'] == sid: return s
    fel(f'ingen tagning {sid}; finns: {[s["id"] for s in S["shots"]]}')
def aktor(S, ref):
    for a in S['actors']:
        if a['id'] == ref or a.get('semantic', {}).get('role') == ref: return a
    return None
def etikett(o): return (o.get('semantic', {}).get('label') or o['id'].split(':')[-1]).lower()
def agare(o): return o.get('semantic', {}).get('owner') or (o['id'].split(':')[0] if ':' in o['id'] else None)
def synlig_i(S, o, sid):
    sh = tagning(S, sid); ov = sh.get('propOverrides', {}).get(o['id'], {})
    return ov.get('visible', o.get('visible', True)) is not False
def foremal(S, sel):
    alla = S['props'] + S['set']
    for o in alla:
        if o['id'] == sel: return o
    if ':' in sel:
        a, b = sel.split(':', 1); b = b.lower()
        if a.startswith('S') and a[1:].isdigit():          # tagningsväljare S1:burger
            sh = tagning(S, a); ägare = [e['id'] for e in sh['actors']]
            kand = [o for o in S['props'] if (b == etikett(o) or b in etikett(o)) and synlig_i(S, o, a)]
            kand.sort(key=lambda o: (agare(o) not in ägare, etikett(o) != b))
            if kand: return kand[0]
        else:                                               # ägare:etikett
            kand = [o for o in alla if agare(o) == a and (etikett(o) == b or b in etikett(o))]
            kand.sort(key=lambda o: etikett(o) != b)
            if kand: return kand[0]
    fel(f'hittar inget föremål för "{sel}" (kör: op.py list)')
_RÖRELSE = None
def huvudpunkt(S, a, sid):
    """aktörens näsa i världen enligt den uppmätta posen (median över aktörens bildrutor i tagningens källa),
    placerad som i spelaren (Character.update): pos + Ry(yaw)·(x,-y,-z)·skala"""
    global _RÖRELSE
    cache = ROOT / 'data/huvudpunkter.json'   # näsa (lokal pose) per aktör och källtagning; byggs en gång ur motion-2.json
    if _RÖRELSE is None:
        if cache.exists(): _RÖRELSE = json.load(open(cache, encoding='utf-8'))
        else:
            fr_all = json.load(open(ROOT / 'data/motion-2.json', encoding='utf-8'))['frames']; _RÖRELSE = {}
            for f in sorted(fr_all, key=lambda f: f['t']): _RÖRELSE.setdefault(f['actor'], {}).setdefault(f['shot'], []).append(f['pose'][0])
            _RÖRELSE = {a_: {sh: v[len(v) // 2] for sh, v in d.items()} for a_, d in _RÖRELSE.items()}
            cache.write_text(json.dumps(_RÖRELSE), encoding='utf-8')
    src = tagning(S, sid)['source'].get('shotId', sid) if sid else None
    per = _RÖRELSE.get(a['id'], {})
    nose = per.get(src) or next(iter(per.values()))
    e = next((e for e in tagning(S, sid)['actors'] if e['id'] == a['id']), {}) if sid else {}
    tr = {**a['transform'], **e.get('transform', {})}; yaw = math.radians(tr.get('yaw', 0))
    skala = a['look']['height'] / {'A': 1.65, 'B': 1.78, 'C': 1.78}.get(a['id'], 1.78)
    x, y, z = nose[0] * skala, -nose[1] * skala, -nose[2] * skala
    return [tr['position'][0] + math.cos(yaw) * x + math.sin(yaw) * z, tr['position'][1] + y, tr['position'][2] - math.sin(yaw) * x + math.cos(yaw) * z]

def punkt(S, sel, sid=None):
    """världspunkt för ett mål: aktör / A:huvud (näsa enligt posen), föremål (mitt)"""
    if sel.endswith(':huvud'): sel = sel[:-6]
    a = aktor(S, sel)
    if a: return [round(v, 4) for v in huvudpunkt(S, a, sid)]
    o = foremal(S, sel); return list(o['transform']['position'])
def kamera0(sh): return sh['camera']['keyframes'][0]
def logg(S, op, args, vad):
    S.setdefault('editLog', []).append({'phase': 3, 'op': op, 'args': args, 'vad': vad, 'by': 'op.py'})

def normalisera(S):
    """frys varje tagnings källkamera (rörelsen mättes med den) så att bildkameran kan redigeras fritt"""
    n = 0
    for s in S['shots']:
        src = s.setdefault('source', {})
        if 'shotId' not in src: src['shotId'] = s['id']; n += 1
        if 'camera' not in src: src['camera'] = copy.deepcopy(kamera0(s)); n += 1
        s.setdefault('propOverrides', {})
    return n

# ---------- operationer
def op_list(S):
    for s in S['shots']:
        print(f"{s['id']}  {s['duration']:.2f}s  {s.get('beat', '')}  aktörer: {', '.join(e['id'] for e in s['actors'])}  källa: {s['source'].get('shotId', s['id'])}")
        vis = [f"{o['id']}({o['type']})" for o in S['props'] if synlig_i(S, o, s['id']) and not (o.get('attach') and o['attach'].get('actor') not in [e['id'] for e in s['actors']])]
        print('    föremål:', ', '.join(vis))
    print('möbler/rum:', ', '.join(o['id'] for o in S['set']))
    print('aktörer:', ', '.join(f"{a['id']} ({a.get('role', '')})" for a in S['actors']))
    return None

def op_show(S, sel):
    if aktor(S, sel): print(json.dumps(aktor(S, sel), ensure_ascii=False, indent=1)[:1500]); return None
    if sel.startswith('S') and sel[1:].isdigit(): print(json.dumps({k: v for k, v in tagning(S, sel).items() if k != 'dialogue'}, ensure_ascii=False, indent=1)[:2500]); return None
    print(json.dumps(foremal(S, sel), ensure_ascii=False, indent=1)); return None

def op_flytta(S, sel):
    o = foremal(S, sel); sid = arg('tagning'); pos = list(o['transform']['position'])
    if sid:
        ov = tagning(S, sid)['propOverrides'].setdefault(o['id'], {})
        pos = list(ov.get('transform', o['transform'])['position'])
    if arg('mot'):
        m = punkt(S, arg('mot'), sid); d = [m[0] - pos[0], m[2] - pos[2]]; L = math.hypot(*d) or 1; s = float(arg('m', .1))
        pos[0] += d[0] / L * s; pos[2] += d[1] / L * s
    elif arg('till'): pos = vec(arg('till'))
    else: pos = [pos[0] + float(arg('dx', 0)), pos[1] + float(arg('dy', 0)), pos[2] + float(arg('dz', 0))]
    pos = [round(v, 4) for v in pos]
    if sid:
        ov['transform'] = {**o['transform'], 'position': pos}; return f"{o['id']} flyttad till {pos} i {sid}"
    o['transform']['position'] = pos; return f"{o['id']} flyttad till {pos}"

def op_rotera(S, sel):
    o = foremal(S, sel); o['transform']['yaw'] = float(arg('yaw')); return f"{o['id']} yaw {o['transform']['yaw']}"

STD_DIMS = {'pizza_slice': (1.0, .22, 1.1), 'burger': (1.0, .55, 1.0), 'paper_cup': (1.0, 2.2, 1.0), 'drink_can': (1.0, 2.5, 1.0), 'fries_box': (1.0, 1.0, .8), 'sauce_cup': (1.0, .55, 1.0)}
def op_byt(S, sel):
    o = foremal(S, sel); ny = arg('typ'); gammal = o['type']
    if arg('dims'): o['dims'] = vec(arg('dims'))
    elif ny in STD_DIMS:   # behåll fotavtrycket (bredden), anpassa höjd/djup till typens form
        fw, fh, fd = STD_DIMS[ny]; w = o['dims'][0]; o['dims'] = [round(w * fw, 4), round(w * fh, 4), round(w * fd, 4)]
    botten = o['transform']['position'][1] - (o.get('_h0') or 0)
    o['transform']['position'][1] = round(o['transform']['position'][1] - o['dims'][1] * 0 , 4)
    o['type'] = ny; o.setdefault('semantic', {})['label'] = {'pizza_slice': 'pizza', 'burger': 'burger'}.get(ny, ny)
    return f"{o['id']}: {gammal} -> {ny} (dims {o['dims']})"

def op_dolj(S, sel, synlig):
    o = foremal(S, sel); sid = arg('tagning')
    if sid: tagning(S, sid)['propOverrides'].setdefault(o['id'], {})['visible'] = synlig; return f"{o['id']} {'visas' if synlig else 'döljs'} i {sid}"
    o['visible'] = synlig; return f"{o['id']} {'visas' if synlig else 'döljs'} överallt"

def op_dolly(S, sid):
    sh = tagning(S, sid); k = kamera0(sh); m = punkt(S, arg('mot'), sid); f = float(arg('faktor', .6))
    slut = [k['pos'][i] + (m[i] - k['pos'][i]) * (1 - f) for i in range(3)]
    sh['camera']['keyframes'] = [k, {**k, 't': round(sh['duration'], 4), 'pos': [round(v, 4) for v in slut], 'target': [round(v, 4) for v in m]}]
    sh['camera'].pop('orbit', None)
    return f"{sid}: kameran åker mot {arg('mot')} till {int(f * 100)} % av avståndet ({math.dist(k['pos'], m):.2f} m -> {math.dist(slut, m):.2f} m)"

def op_zoom(S, sid):
    sh = tagning(S, sid); k = kamera0(sh); fov = float(arg('fov'))
    sh['camera']['keyframes'] = [k, {**k, 't': round(sh['duration'], 4), 'fov': fov}]; return f"{sid}: zoom {k['fov']}° -> {fov}°"

def op_orbit(S, sid):
    sh = tagning(S, sid); k = kamera0(sh); p = punkt(S, arg('runt'), sid); g = float(arg('grader', 90)); start = list(k['pos'])
    if arg('radie'):   # flytta startpunkten längs samma riktning till given radie (samma höjd)
        d = [start[0] - p[0], start[2] - p[2]]; L = math.hypot(*d) or 1; r = float(arg('radie')); start = [p[0] + d[0] / L * r, start[1], p[2] + d[1] / L * r]
    sh['camera']['orbit'] = {'start': float(arg('start', 0)), 'end': float(arg('slut', sh['duration'])), 'pivot': p, 'degrees': g, 'startPos': [round(v, 4) for v in start]}
    sh['camera']['keyframes'] = [{**k, 'target': p}]
    return f"{sid}: kameran kretsar {g}° runt {arg('runt')} {p}"

def op_kamera(S, sid):
    sh = tagning(S, sid); k = kamera0(sh)
    nk = {**k, 'pos': vec(arg('pos')) if arg('pos') else k['pos'], 'target': vec(arg('mal')) if arg('mal') else k['target'], 'fov': float(arg('fov', k['fov'])), 'up': [0, 1, 0]}
    sh['camera']['keyframes'] = [nk]; sh['camera'].pop('orbit', None); return f"{sid}: kamera satt {nk['pos']} -> {nk['target']}"

TAL_PAD, MIN_PAUS = .05, .12          # s: marginal runt ord, kortaste paus mellan tal

def tal_intervall(S, a, b):
    """talade intervall (källtid) inom [a, b] ur replikernas ordtider; ord närmare än MIN_PAUS slås ihop"""
    ws = sorted((w['start'], w['end']) for d in S['dialogue'] for w in d.get('words', []) if w['end'] > a and w['start'] < b)
    iv = []
    for s0, e0 in ws:
        s0, e0 = max(a, s0 - TAL_PAD), min(b, e0 + TAL_PAD)
        if iv and s0 - iv[-1][1] < MIN_PAUS: iv[-1][1] = max(iv[-1][1], e0)
        else: iv.append([s0, e0])
    return iv

def tidskarta(a, b, iv, D, vmax):
    """replik-säker tidskarta: knots [(lokal tid, källtid)]. Kortning: pauser (före, mellan, efter) krymper först,
    sedan får talet gå upp till vmax (webbläsaren behåller tonhöjden). Förlängning: inre pauser växer.
    Ord klipps aldrig. Returnerar (knots, faktisk längd, info)."""
    orig = b - a; head = iv[0][0] - a; tail = b - iv[-1][1]
    gaps = [iv[i + 1][0] - iv[i][1] for i in range(len(iv) - 1)]; tal = sum(e - s for s, e in iv); v = 1.0
    head2, tail2, gaps2 = head, tail, list(gaps)
    if D < orig:
        excess = [head, tail] + [max(0, g - MIN_PAUS) for g in gaps]; tot = sum(excess); R = orig - D
        f = min(1.0, R / tot) if tot > 1e-9 else 0.0
        head2, tail2 = head * (1 - f), tail * (1 - f); gaps2 = [g - max(0, g - MIN_PAUS) * f for g in gaps]
        R2 = R - tot * f
        if R2 > 1e-6: v = min(vmax, tal / max(1e-6, tal - R2))
    elif D > orig:
        X = D - orig
        if sum(gaps) > 1e-6: gaps2 = [g + X * g / sum(gaps) for g in gaps]
        else: tail2 = tail + X
    seg = [(min(head, head2), head2)]          # (källängd, lokal längd)
    for i, (s0, e0) in enumerate(iv):
        seg.append((e0 - s0, (e0 - s0) / v))
        if i < len(gaps): seg.append((gaps[i], gaps2[i]))
    seg.append((min(tail, tail2), tail2))
    src0 = iv[0][0] - min(head, head2); knots = [(0.0, src0)]; L, T = 0.0, src0
    for sl, ll in seg:
        if ll <= 1e-6 and sl <= 1e-6: continue
        L += ll; T += sl; knots.append((round(L, 4), round(T, 4)))
    knots[0] = (0.0, round(src0, 4))
    return knots, L, dict(pauser_s=round(sum(gaps), 2), pauser_efter_s=round(sum(gaps2), 2), tal_s=round(tal, 2), talfart=round(v, 3),
                          trimmat_fore_s=round(head - min(head, head2), 2), trimmat_efter_s=round(tail - min(tail, tail2), 2))

def op_langd(S, sid):
    sh = tagning(S, sid); D = float(arg('s')); src = sh['source']
    a, b = src.get('full') or (src['inSec'], src['outSec']); src['full'] = [a, b]; orig = b - a
    iv = tal_intervall(S, a, b); läge = arg('lage', 'replik' if iv else 'trim'); vmax = float(arg('tal-max', 1.15)); info = ''
    src.pop('knots', None)
    if läge == 'replik' and iv:
        D_min = sum(min(g, MIN_PAUS) for g in [iv[i + 1][0] - iv[i][1] for i in range(len(iv) - 1)]) + sum(e - s for s, e in iv) / vmax
        mål = D
        if D < D_min - 1e-6: D = D_min
        knots, D, info_ = tidskarta(a, b, iv, D, vmax)
        src['knots'] = knots; src['inSec'], src['outSec'] = knots[0][1], knots[-1][1]
        info = f" (replik: pauser {info_['pauser_s']}->{info_['pauser_efter_s']} s, talfart x{info_['talfart']}, trimmat {info_['trimmat_fore_s']}/{info_['trimmat_efter_s']} s före/efter)"
        if mål < D - 1e-3: info += f" OBS: {mål:.2f} s går inte utan att klippa ord; kortaste {D:.2f} s. --lage trim klipper repliken, --tal-max höjer talfarten."
    elif läge == 'trim' and D <= orig + 1e-6:
        src['inSec'], src['outSec'] = a, round(a + D, 4)
        klippta = [w['w'] for d in S['dialogue'] for w in d.get('words', []) if w['start'] < b and w['end'] > a + D + .02]
        if klippta: info = f" OBS: klipper {len(klippta)} ord: {' '.join(klippta)}"
    else:
        src['inSec'], src['outSec'] = a, b
    sh['audioRange'] = [src['inSec'], src['outSec']]
    sh['duration'] = round(D, 4)
    for k in sh['camera']['keyframes'][1:]: k['t'] = round(D, 4)
    if sh['camera'].get('orbit'): sh['camera']['orbit']['end'] = round(D, 4)
    return f"{sid}: {orig:.2f}s -> {D:.2f}s ({läge}){info}"

def op_duplicera(S, sid):
    sh = tagning(S, sid); ny = copy.deepcopy(sh); ny['id'] = arg('som'); ny['source'].setdefault('shotId', sid)
    ny['tyst'] = '--med-ljud' not in sys.argv; ny['dialogue'] = [] if ny['tyst'] else ny.get('dialogue', [])   # kopian upprepar inte repliken (tyst bild, stängd mun)
    i = S['shots'].index(tagning(S, arg('efter', sid))); S['shots'].insert(i + 1, ny); return f"{sid} duplicerad som {ny['id']}"

def op_ta_bort(S, sid):
    sh = tagning(S, sid)
    if not any(s['source'].get('shotId') == sh['source'].get('shotId', sid) for s in S['shots'] if s is not sh): pass  # källkameran ligger i tagningen själv; övriga använder egna kopior
    S['shots'].remove(sh); return f"{sid} borttagen"

def op_flytta_tagning(S, sid):
    sh = tagning(S, sid); S['shots'].remove(sh)
    if arg('sist') is not None or '--sist' in sys.argv: S['shots'].append(sh)
    elif arg('fore'): S['shots'].insert(S['shots'].index(tagning(S, arg('fore'))), sh)
    elif arg('efter'): S['shots'].insert(S['shots'].index(tagning(S, arg('efter'))) + 1, sh)
    return 'ordning: ' + ' '.join(s['id'] for s in S['shots'])

def yaw_mot(fran, till): return round(math.degrees(math.atan2(till[0] - fran[0], till[2] - fran[2])), 2)

def op_lagg_till_aktor(S, sid, aid):
    sh = tagning(S, sid); a = aktor(S, aid) or fel(f'ingen aktör {aid}')
    if any(e['id'] == a['id'] for e in sh['actors']): fel(f'{aid} finns redan i {sid}')
    if arg('vid'): x, z = vec(arg('vid'))
    else:   # bakom en annan aktör sett från tagningens kamera, något åt sidan så att hen syns
        ref = punkt(S, arg('bakom'), sid); cam = kamera0(sh)['pos']; d = [ref[0] - cam[0], ref[2] - cam[2]]; L = math.hypot(*d); d = [d[0] / L, d[1] / L]
        sida = [-d[1], d[0]]; avst = float(arg('avstand', 1.0)); s = float(arg('sida', 0.4))
        x, z = ref[0] + d[0] * avst + sida[0] * s, ref[2] + d[1] * avst + sida[1] * s
    # håll aktören inne i rummet (väggarna i 'set'), 0,25 m marginal
    väggar = {o['id']: o for o in S['set'] if o['type'] in ('wall', 'window_wall')}
    zs = sorted(o['transform']['position'][2] for o in väggar.values() if o['dims'][0] > o['dims'][2])
    xs = sorted(o['transform']['position'][0] for o in väggar.values() if o['dims'][2] > o['dims'][0])
    varning = ''
    if len(zs) >= 2 and not (zs[0] + .25 <= z <= zs[-1] - .25): z0 = z; z = min(max(z, zs[0] + .25), zs[-1] - .25); varning += f' (z {z0:.2f} utanför väggarna, flyttad till {z:.2f})'
    if xs and x < xs[0] + .25: x0 = x; x = xs[0] + .25; varning += f' (x {x0:.2f} utanför sidoväggen, flyttad till {x:.2f})'
    pos = [round(x, 4), a['transform']['position'][1], round(z, 4)]
    yaw = float(arg('yaw')) if arg('yaw') else (yaw_mot(pos, punkt(S, arg('vand-mot'), sid)) if arg('vand-mot') else a['transform'].get('yaw', 0))
    e = {'id': a['id'], 'transform': {'position': pos, 'yaw': yaw}, 'motion': {'fromShot': arg('fran-tagning') or next((s['id'] for s in S['shots'] if any(x['id'] == a['id'] for x in s['actors'])), None)}}
    sh['actors'].append(e); return f"{aid} tillagd i {sid} vid {pos}, yaw {yaw}, rörelse från {e['motion']['fromShot']}{varning}"

def entry(S, sid, aid):
    sh = tagning(S, sid); a = aktor(S, aid) or fel(f'ingen aktör {aid}')
    e = next((e for e in sh['actors'] if e['id'] == a['id']), None) or fel(f'{aid} finns inte i {sid}')
    return sh, a, e

def op_vand(S, sid, aid):
    sh, a, e = entry(S, sid, aid); p = e.get('transform', {}).get('position', a['transform']['position'])
    yaw = yaw_mot(p, punkt(S, arg('mot'), sid)); e.setdefault('transform', {})['yaw'] = yaw
    return f"{aid} i {sid} vänd mot {arg('mot')} (yaw {a['transform'].get('yaw', 0)} -> {yaw})"

def op_titta(S, sid, aid):
    """bara huvudet vrids mot målet (kroppen gör det den gjorde); mjuk ingång över --ramp s från --fran s"""
    sh, a, e = entry(S, sid, aid); mål = punkt(S, arg('mot'), sid); huvud = punkt(S, aid, sid)
    t0 = float(arg('fran', 0)); r = float(arg('ramp', .35)); m = float(arg('mangd', .85))
    e.setdefault('motion', {})['lookAt'] = dict(target=mål, amount=m, ramp=[t0, t0 + r], mot=arg('mot'))
    cam = (sh['source'].get('camera') or kamera0(sh))['pos']
    def vinkel(u, v): return abs((math.degrees(math.atan2(u[0], u[2]) - math.atan2(v[0], v[2])) + 180) % 360 - 180)
    dy = math.radians(e.get('transform', {}).get('yaw', a['transform'].get('yaw', 0)) - a['transform'].get('yaw', 0))   # vand i tagningen vrider blicken med kroppen
    bx, bz = cam[0] - huvud[0], cam[2] - huvud[2]; blick = [bx * math.cos(dy) + bz * math.sin(dy), 0, -bx * math.sin(dy) + bz * math.cos(dy)]
    v = vinkel(blick, [mål[0] - huvud[0], 0, mål[2] - huvud[2]])
    not_ = f' OBS: {v:.0f}° från blicken mot kameran; huvudet vrids högst 80°, använd vand för resten' if v > 80 else ''
    return f"{aid} i {sid} tittar mot {arg('mot')} ({v:.0f}° vridning, mängd {m}, från {t0} s){not_}"

def ordskatt(text, a, b):
    """ordtider för en ny replik: luckan delas efter ordens längd (rösten passas in i samma lucka)"""
    ws = text.split(); L = sum(len(w) + 1 for w in ws); t = a; ut = []
    for w in ws: d = (b - a) * (len(w) + 1) / L; ut.append(dict(w=w, start=round(t, 3), end=round(t + d * .92, 3))); t += d
    return ut

def röst_om(S):
    """designade röster och munkurvor om (cache per replik, ~1 s) mot den osparade scenen; ljudet får ny version"""
    import subprocess, os, urllib.request
    try:   # varm server (rostserver.py) först: ~0,3 s i stället för ~6 s
        req = urllib.request.Request('http://127.0.0.1:5193/bygg', data=json.dumps(S, ensure_ascii=False).encode('utf-8'), headers={'Content-Type': 'application/json'})
        svar = json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8'))
        if not svar.get('ok'): fel('rostserver: ' + svar.get('fel', ''))
        rader = svar['rader']; S['_röstväg'] = 'server'
    except OSError:
        tmp = ROOT / 'cache/op-spec.json'; tmp.parent.mkdir(exist_ok=True); tmp.write_text(json.dumps(S, ensure_ascii=False), encoding='utf-8')
        r = subprocess.run([sys.executable, '-B', str(ROOT / 'roster.py'), '--spec', str(tmp)], capture_output=True, text=True, encoding='utf-8', env={**os.environ, 'PYTHONUTF8': '1'})
        if r.returncode: fel('roster.py: ' + r.stderr[-400:])
        rader = r.stdout.splitlines(); S['_röstväg'] = 'underprocess'
    S['audioVersion'] = int(time.time() * 1000)
    brott = [l.strip() for l in rader if 'RÄLSBROTT' in l]
    return (' | ' + ' | '.join(brott)) if brott else ''

def op_replik(S, nr):
    """byt en repliks text (eget tal): designad röst i samma lucka, uppskattade ordtider, teleprompter; rälsen varnar om fart"""
    i = int(nr) - 1
    if not 0 <= i < len(S['dialogue']): fel(f"replik 1-{len(S['dialogue'])}")
    d = S['dialogue'][i]; ny = arg('text') or fel('--text saknas')
    d.setdefault('originalText', d['text']); d.setdefault('originalWords', d.get('words'))
    d['text'] = ny; d['words'] = d['originalWords'] if ny == d['originalText'] else ordskatt(ny, d['start'], d['end'])
    d['timing'] = 'ordtider (källjud)' if ny == d['originalText'] else 'uppskattade i luckan (designad röst)'
    for sh in S['shots']:
        if not sh.get('tyst'):
            a, b = sh['source']['inSec'], sh['source']['outSec']; sh['dialogue'] = [x for x in S['dialogue'] if x['start'] < b and x['end'] > a]
    t = time.perf_counter(); brott = röst_om(S)
    return f"replik {nr} ({d['speaker']}): \"{d['originalText']}\" -> \"{ny}\" (röst {1000 * (time.perf_counter() - t):.0f} ms, {S.pop('_röstväg', '')}){brott}"

def op_casting(S, aid):
    """roll -> namn, röst, färg: casting märker replikerna (A -> Ägaren); ingen likhet med källpersonen"""
    a = aktor(S, aid) or fel(f'ingen aktör {aid}'); c = a.setdefault('casting', {}); delar = []
    if arg('roll'): c['role'] = arg('roll'); delar.append(f"roll {c['role']}")
    if arg('farg'): a['look']['roleColor'] = arg('farg'); delar.append(f"färg {arg('farg')}")
    extra = ''
    if arg('rost'):
        if not (ROOT / f"modeller/piper/sv_SE-{arg('rost')}-medium.onnx").exists(): fel('röster: alma, lisa, nst')
        c['voice'] = arg('rost'); a.setdefault('voice', {})['voice'] = arg('rost'); delar.append(f"röst {arg('rost')}")
        t = time.perf_counter(); extra = röst_om(S) + f" (röst {1000 * (time.perf_counter() - t):.0f} ms, {S.pop('_röstväg', '')})"
    return f'{aid}: ' + ', '.join(delar) + extra

def op_spegla(S, sid, aid):
    sh, a, e = entry(S, sid, aid); m = e.setdefault('motion', {}); m['mirror'] = not m.get('mirror', False); return f"{aid} i {sid} speglad={m['mirror']}"

def op_intensitet(S, sid, aid):
    v = float(arg('varde'))
    if sid == 'alla': (aktor(S, aid) or fel(aid))['motion']['intensity'] = v; return f"{aid}: grundintensitet {v}"
    sh, a, e = entry(S, sid, aid); e.setdefault('motion', {})['intensity'] = v; return f"{aid} i {sid}: intensitet {v}"

def op_humor(S, sid, aid):
    md = {'name': arg('namn', 'neutral'), 'amount': float(arg('mangd', 1))}
    if sid == 'alla': (aktor(S, aid) or fel(aid))['motion']['mood'] = md; return f"{aid}: humör {md}"
    sh, a, e = entry(S, sid, aid); e.setdefault('motion', {})['mood'] = md; return f"{aid} i {sid}: humör {md}"

def op_utseende(S, aid):
    a = aktor(S, aid) or fel(aid); a['look'][arg('nyckel')] = arg('varde'); return f"{aid}: {arg('nyckel')} = {arg('varde')}"

# ---------- huvud
def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'hjälp'): print(__doc__); return
    op = sys.argv[1]; t0 = time.perf_counter()
    if op == 'angra':
        v = sorted(HIST.glob('v*.json'))
        if not v: fel('ingen historik')
        shutil.copy(v[-1], FIL); v[-1].unlink(); print('ångrade till', v[-1].name); return
    S = las(); n = normalisera(S)
    if op in ('list', 'show'):
        (op_list(S) if op == 'list' else op_show(S, sys.argv[2]))
        if n: spara(S)
        return
    pos = [a for a in sys.argv[2:] if not a.startswith('--')]
    pos = [a for i, a in enumerate(sys.argv[2:]) if not a.startswith('--') and not (i > 0 and sys.argv[2:][i - 1].startswith('--') and sys.argv[2:][i - 1] not in ('--sist',))]
    tabell = {'flytta': lambda: op_flytta(S, pos[0]), 'rotera': lambda: op_rotera(S, pos[0]), 'byt': lambda: op_byt(S, pos[0]),
              'dolj': lambda: op_dolj(S, pos[0], False), 'visa': lambda: op_dolj(S, pos[0], True), 'dolly': lambda: op_dolly(S, pos[0]),
              'zoom': lambda: op_zoom(S, pos[0]), 'orbit': lambda: op_orbit(S, pos[0]), 'kamera': lambda: op_kamera(S, pos[0]),
              'langd': lambda: op_langd(S, pos[0]), 'duplicera': lambda: op_duplicera(S, pos[0]), 'ta-bort': lambda: op_ta_bort(S, pos[0]),
              'flytta-tagning': lambda: op_flytta_tagning(S, pos[0]), 'lagg-till-aktor': lambda: op_lagg_till_aktor(S, pos[0], pos[1]),
              'vand': lambda: op_vand(S, pos[0], pos[1]), 'titta': lambda: op_titta(S, pos[0], pos[1]), 'spegla': lambda: op_spegla(S, pos[0], pos[1]),
              'intensitet': lambda: op_intensitet(S, pos[0], pos[1]), 'humor': lambda: op_humor(S, pos[0], pos[1]),
              'utseende': lambda: op_utseende(S, pos[0]), 'replik': lambda: op_replik(S, pos[0]), 'casting': lambda: op_casting(S, pos[0]), 'normalisera': lambda: f'normaliserade {n} fält'}
    if op not in tabell: fel(f'okänt kommando {op} (op.py --help)')
    HIST.mkdir(exist_ok=True); shutil.copy(FIL, HIST / f'v{len(list(HIST.glob("v*.json"))):03d}.json')
    vad = tabell[op](); ms = (time.perf_counter() - t0) * 1000
    logg(S, op, sys.argv[2:], vad); S['editLog'][-1]['ms'] = round(ms, 1); spara(S)
    print(f'{vad}  ({ms:.1f} ms)')

if __name__ == '__main__': main()
