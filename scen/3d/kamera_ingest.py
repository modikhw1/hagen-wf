"""Kamera-ingest per tagning, i ord och tal som går att återanvända för nästa scen.

Ur scen3d.json (källkameran per tagning, löst med PnP), data/huvudpunkter.json (huvudets läge), data/kamera-3.json
(rörelse inom tagningen) och replikernas ordtider:
  utsnitt     ECU/CU/MCU/MS/WS ur huvudets höjd i bilden (andel av bildhöjden)
  vinkel      kamerans höjd mot ögonen (m) och lutning (grader; negativ = ser ner), rollvinkel
  avstånd     kamera -> huvud (m); objektiv som 35 mm-ekvivalent (68° över långsidan)
  rörelse     statisk/handhållen ur kamera-3 (topp-till-topp i grader)
  klipp mot tal: tal i tagningen (s, andel), första ord efter in, tystnad före ut,
              J-klipp (nästa talare börjar före klippet), L-klipp (repliken fortsätter över klippet)
Ut: data/kamera-ingest.json; med --skriv även shots[].ingest i scen3d.json och scen3d.bas.json.
"""
import json, math, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent
S = json.loads((ROOT / 'scen3d.bas.json').read_text(encoding='utf-8'))
HP = json.loads((ROOT / 'data/huvudpunkter.json').read_text(encoding='utf-8'))
K3 = json.loads((ROOT / 'data/kamera-3.json').read_text(encoding='utf-8'))['shots']
SK = {'A': 1.65, 'B': 1.78, 'C': 1.78}; H = 1024; HUVUD = .23
def huvud(aid, sid):
    a = next(x for x in S['actors'] if x['id'] == aid); s = a['look']['height'] / SK[aid]; x, y, z = HP[aid][sid]
    l = np.array([x, -y, -z]) * s; yaw = math.radians(a['transform'].get('yaw', 0)); c, sn = math.cos(yaw), math.sin(yaw)
    return np.array([c * l[0] + sn * l[2], l[1], -sn * l[0] + c * l[2]]) + np.array(a['transform']['position'])
def utsnitt(andel):
    return 'ECU' if andel > .32 else 'CU' if andel > .2 else 'MCU' if andel > .12 else 'MS' if andel > .065 else 'WS'
ord_ = sorted((w['start'], w['end'], d['speaker']) for d in S['dialogue'] for w in d.get('words', []))
def klipp(b, aid, nästa):
    """klippet ut ur tagningen mot talet: J = nästa bilds talare hörs före klippet (bilden följer rösten), L = den här bildens talare
    hörs efter klippet, rent = tystnad över klippet. offset = klipptid - nästa talares första ord i repliken (s)."""
    if not nästa: return dict(typ='slut')
    nb = nästa['actors'][0]['id']
    for d in S['dialogue']:
        if d.get('words') and d['speaker'] == nb and d['start'] < b + .05 and d['end'] > b - .4:
            return dict(typ='J', talare=nb, offset_s=round(b - d['start'], 2), text='nästa talare började %.2f s före klippet' % (b - d['start']))
    for d in S['dialogue']:
        if d.get('words') and d['speaker'] == aid and d['start'] < b < d['end']:
            return dict(typ='L', talare=aid, offset_s=round(d['end'] - b, 2), text='repliken fortsätter %.2f s efter klippet' % (d['end'] - b))
    sista = max((e for s0, e, _ in ord_ if e <= b), default=None); nästa_ord = min((s0 for s0, e, _ in ord_ if s0 >= b), default=None)
    return dict(typ='rent', tystnad_fore_s=round(b - sista, 2) if sista else None, tystnad_efter_s=round(nästa_ord - b, 2) if nästa_ord else None)
ut = {}
for i, sh in enumerate(S['shots']):
    sid = sh['id']; k = sh['source']['camera']; aid = sh['actors'][0]['id']
    pos, mål = np.array(k['pos']), np.array(k['target']); up = np.array(k.get('up', [0, 1, 0]))
    hp = huvud(aid, sid); d = hp - pos; avst = float(np.linalg.norm(d))
    f = (mål - pos) / np.linalg.norm(mål - pos); lut = math.degrees(math.asin(f[1]))
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); roll = math.degrees(math.atan2(np.dot(up, r), np.dot(up, np.cross(r, f))))
    fpx = (H / 2) / math.tan(math.radians(k['fov']) / 2); andel = fpx * HUVUD / avst / H
    mm = 18 / math.tan(math.radians(k['fov']) / 2)
    a, b = sh['source']['inSec'], sh['source']['outSec']; w = [x for x in ord_ if x[1] > a and x[0] < b]
    tal = sum(min(e, b) - max(s, a) for s, e, _ in w)
    nästa = S['shots'][i + 1] if i + 1 < len(S['shots']) else None
    j_klipp = [x for x in ord_ if x[0] < b < x[1] or (b - .4 < x[0] < b)] if nästa else []
    rörelse = K3.get(sid, {}).get('range', {})
    ut[sid] = dict(
        subjekt=aid, utsnitt=utsnitt(andel), huvud_andel_av_bild=round(andel, 3), avstand_m=round(avst, 2),
        kamerahojd_mot_ogon_m=round(float(pos[1] - hp[1]), 2), lutning_grader=round(lut, 1), roll_grader=round(roll, 1),
        objektiv_mm_ekv=round(mm, 1), fov_grader=k['fov'],
        rorelse=('statisk' if max(rörelse.values() or [0]) < 1.0 else 'handhållen') if rörelse else 'okänd',
        rorelse_topp_grader={kk: v for kk, v in rörelse.items() if kk != 'fov'},
        langd_s=round(b - a, 2), tal_s=round(tal, 2), tal_andel=round(tal / (b - a), 2),
        forsta_ord_efter_in_s=round(w[0][0] - a, 2) if w else None, tystnad_fore_ut_s=round(b - max(e for _, e, _ in w), 2) if w and max(e for _, e, _ in w) < b else 0.0,
        talare_i_bild=sorted({sp for *_, sp in w if sp == aid}), talare_utanfor_bild=sorted({sp for *_, sp in w if sp != aid}),
        klipp_ut=klipp(b, aid, nästa),
        beat=sh.get('beat'))
    x = ut[sid]
    print(f"{sid} {aid} {x['utsnitt']:<3} {x['avstand_m']:.2f} m  höjd {x['kamerahojd_mot_ogon_m']:+.2f} m  lutning {x['lutning_grader']:+.1f}°  roll {x['roll_grader']:+.1f}°  {x['objektiv_mm_ekv']} mm  {x['rorelse']}  "
          f"tal {x['tal_s']}/{x['langd_s']} s  första ord {x['forsta_ord_efter_in_s']:+.2f} s  ut: {x['klipp_ut'].get('typ')} {x['klipp_ut'].get('text', '')}  utanför bild: {x['talare_utanfor_bild']}")
(ROOT / 'data/kamera-ingest.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
if '--skriv' in sys.argv:
    for fn in ('scen3d.json', 'scen3d.bas.json'):
        X = json.loads((ROOT / fn).read_text(encoding='utf-8'))
        for sh in X['shots']:
            sid = sh['source'].get('shotId', sh['id'])
            if sid in ut: sh['ingest'] = ut[sid]
        (ROOT / fn).write_text(json.dumps(X, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ingest inskriven i scen3d.json och scen3d.bas.json')
