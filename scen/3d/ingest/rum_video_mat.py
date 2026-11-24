"""Mäter en scen3d-hypotes från rum_video.py mot originalet: projicerar varje persons kropp genom modellens kamera och jämför med ingestens personruta och lästa avstånd.

    python rum_video_mat.py <ingestmapp> <rum_video_scen3d_*.json> [...]

Per tagning: x-fel för kroppens mitt (px), fel för huvudets topp och fötterna när de syns i bild (px), avståndskvot modell/läst.
Antagna kroppsmått: höft 0,53 och hjässa 1,00 av personens längd. Kamerans inre parametrar tas ur ingesten (fokal, bildmitt).
"""
import json, math, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rum_video import las_json


def kamera(k):
    """Världspunkt -> (bildpunkt, djup). x höger, y djup i bild nedåt (bildkonvention)."""
    yaw, pitch = math.radians(k['yaw_grader']), math.radians(k['pitch_grader'])
    fram = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)])
    hoger = np.array([math.sin(yaw), -math.cos(yaw), 0.]); upp = np.cross(hoger, fram)
    C = np.array(k['pos_m'], float)
    return lambda X: (np.array([(np.asarray(X) - C) @ hoger, -((np.asarray(X) - C) @ upp)]), float((np.asarray(X) - C) @ fram))


def mat(I, fil):
    D = json.loads(Path(fil).read_text(encoding='utf-8'))['svar']; L = las_json(I / 'brief' / 'lasning.json') or {}
    langd = {p['id']: p.get('langd_m') or 1.7 for p in D.get('personer', [])}
    pose = {t['id']: t['kamera'] for t in D['tagningar']}
    rader = []
    for t in D['tagningar']:
        S = I / t['id']; meta = json.loads((S / 'meta.json').read_text(encoding='utf-8'))
        f = float(np.load(next(S.glob('sekvens_*.npz')), allow_pickle=True)['fokal']); cx, cy = meta['bredd'] / 2, meta['hojd'] / 2
        k = pose[t['id']]
        if k.get('samma_som') and k['samma_som'] in pose and not k.get('pos_m'): k = pose[k['samma_som']]
        P = kamera(k); pers = las_json(S / 'personer.json') or {}
        for p in t['personer']:
            # Modellen skriver spåret som "1", "track_1" eller personens namn; en tagning med ett enda spår tolkas som det spåret.
            sid = ''.join(c for c in str(p.get('spar')) if c.isdigit())
            if sid not in pers and len(pers) == 1 and str(p.get('spar')) != 'otrackad' and not any(q.get('id') == p['person'] and q.get('endast_hand') for q in D.get('personer', [])):
                sid = next(iter(pers))
            if sid not in pers: rader.append(dict(tagning=t['id'], spar=sid, person=p['person'], not_='ingen sådan trackad person')); continue
            box = np.median(np.array(list(pers[sid].values())), axis=0); Lm = langd.get(p['person'], 1.7); x, y = p['fot_m'][:2]
            pix = {}
            for namn, z in (('fot', 0.), ('hoft', .53 * Lm), ('topp', Lm)):
                (u, v), djup = P([x, y, z]); pix[namn] = (cx + f * u / djup, cy + f * v / djup) if djup > .05 else (math.nan, math.nan)
            _, djup_hoft = P([x, y, .53 * Lm]); last = None
            for q in (L.get('tagningar', {}).get(t['id'], {}) or {}).get('personspar', []):
                if str(q.get('spar_id')) == sid: last = (q.get('kropp') or {}).get('kamera_till_hoft_m')
            r = dict(tagning=t['id'], spar=sid, person=p['person'], x_fel_px=round(pix['hoft'][0] - (box[0] + box[2]) / 2, 1),
                     modell_avstand_m=round(math.dist(k['pos_m'], [x, y, .53 * Lm]), 2), last_avstand_m=last)
            if box[1] > 5: r['topp_fel_px'] = round(pix['topp'][1] - box[1], 1)
            if box[3] < meta['hojd'] - 5: r['fot_fel_px'] = round(pix['fot'][1] - box[3], 1)
            if last: r['avstandskvot'] = round(r['modell_avstand_m'] / last, 2)
            rader.append(r)
    ok = [r for r in rader if 'x_fel_px' in r]
    med = lambda n: round(float(np.median([abs(r[n]) for r in ok if n in r and r[n] == r[n]])), 1) if any(n in r for r in ok) else None
    sammandrag = dict(fil=str(fil), tagningar=len(D['tagningar']), personrader=len(rader), utan_track=len(rader) - len(ok),
                      median_abs_x_fel_px=med('x_fel_px'), median_abs_topp_fel_px=med('topp_fel_px'), median_abs_fot_fel_px=med('fot_fel_px'),
                      median_avstandskvot=round(float(np.median([r['avstandskvot'] for r in ok if 'avstandskvot' in r])), 2) if ok else None)
    return sammandrag, rader


if __name__ == '__main__':
    I = Path(sys.argv[1])
    for fil in sys.argv[2:]:
        s, rader = mat(I, fil); print(json.dumps(s, ensure_ascii=False))
        for r in rader: print('  ', json.dumps(r, ensure_ascii=False))
