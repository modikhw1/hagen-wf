"""Kontroll att deklarerade värden överlevde kompilatorn: golv, sitthöjd och kamerahöjd. Inga mätningar läses, bara den färdiga planen.

Platsens `deklarerat` (skrivet av ingest/plats.py ur plats/deklaration.json) anger varje värde som ett tal (hårt) eller [min, max]
(kompilatorn får röra sig inom intervallet). Varje post jämför det deklarerade med det planen faktiskt har; allt som ligger utanför
flaggas som avvikelse (och blir en varning i planen), aldrig tyst. Plats utan `deklarerat` ger ingen post: gamla vägen är orörd.
"""
import numpy as np

REGISTRERING_VARNING_M = .15   # Restfel per roll mellan kroppens lästa bäcken och dess deklarerade plats efter flerrollsregistreringen. 15 cm = en tredjedel av en stolsbredd (0,48 m)
#                              och strax över läsbruset: bäckenet spretar 2–12 cm inom en tagning (plats_matt.json spridning_m) och golvcuernas spann är 7–17 cm. Mindre fel kan en stel kamera
#                              inte skilja från läsbrus; större betyder att läsningen och deklarationen säger olika om rollernas inbördes läge.
TOLERANS_M = .01   # Avrundning och kameraregistrering; större skillnad än 1 cm mot ett deklarerat värde är en avvikelse.


def _spann(v):
    return (float(v[0]), float(v[1])) if isinstance(v, (list, tuple)) else (float(v), float(v))


def _post(typ, id_, dekl, faktiskt, **extra):
    lo, hi = _spann(dekl)
    avvik = 0. if lo - TOLERANS_M <= faktiskt <= hi + TOLERANS_M else float(faktiskt - (lo if faktiskt < lo else hi))
    return dict(typ=typ, id=id_, deklarerat=dekl, planens_m=float(faktiskt), avvikelse_m=avvik, status='bunden' if avvik == 0. else 'avviker', **extra)


def kontrollera(plan):
    """Returnerar None när ingen plats har deklarerade värden, annars dict(status, poster, avvikelser)."""
    platser = [p for p in plan.get('plats', []) if p.get('deklarerat')]
    if not platser: return None
    poster = []
    tagning_scen = {r['tagning']: r['scen'] for p in plan['matning'].get('platser', []) for r in p['registreringar']}
    scen_plats = {s['id']: s.get('plats_id') for s in plan.get('scener', [])}
    ut = {s['id']: s['ut'] for s in (plan.get('scener') or plan['matkamera'].get('scener', []))}
    for p in platser:
        d = p['deklarerat']; golv = float(p['golv_hojd_m'])
        # Golvet: planens golv är platsens eget golv i dess ram; kamerorna och kropparna är registrerade mot det.
        if d.get('golv_hojd_m') is not None:
            poster.append(_post('golv', p['id'], d['golv_hojd_m'], golv, orsak='Platsens golv i planen; deklarationens golv är platsramens z=0 (plats.py).'))
        rm = p.get('rumsmall') or {}
        for pid, v in (d.get('sitthojd_m') or {}).items():
            a = next((a for a in rm.get('ankare', []) if a['id'] == pid and a['typ'] == 'sate'), None)
            if a is None: poster.append(dict(typ='sitthojd', id=pid, deklarerat=v, planens_m=None, avvikelse_m=None, status='avviker', orsak='Platsen har inget sittankare med detta id i planens rumsmall.')); continue
            fit = next((h for h in plan['kvalitet'].get('hojdpassning', []) if h.get('typ') == 'sate' and h.get('ankare') == pid and h.get('plats') == p['id']), {})
            poster.append(_post('sitthojd', pid, v, float(a['sate_hojd_m']), kroppslasning_onskad_m=fit.get('onskad_m'), lasrest_m=fit.get('lasrest_m'),
                                orsak='Sitsens höjd i planens rumsmall; stolsprioren 43–48 cm gäller inte när sitthöjd är deklarerad.'))
        for tagning, v in (d.get('kamerahojd_m') or {}).items():
            scen = tagning_scen.get(tagning)
            if scen is None or scen not in ut or scen_plats.get(scen) not in (None, p['id']): continue
            a, b = ut[scen]; z = [plan['matkamera']['nycklar'][i]['matris'][2][3] for i in range(a, b)]
            poster.append(_post('kamerahojd', f'{tagning}/{scen}', v, float(np.median(z)) - golv, spridning_m=float(np.ptp(z)),
                                orsak='Uppmätt kamera (matkamera) över platsens golv, median över scenens rutor.'))
    avvikelser = [x for x in poster if x['status'] == 'avviker']
    # Flerrollsregistrering: kameran passad mot alla synliga rollers deklarerade platser (plats.py). Restfelet per roll redovisas och varnas över tröskeln;
    # kropparna är inte flyttade individuellt. Tagningar med en synlig roll har inget sådant fält och ger inga poster.
    registrering = []
    for mp in plan['matning'].get('platser', []):
        for r in mp['registreringar']:
            rr = r.get('roller_registrering')
            if not rr: continue
            for x in rr['roller']:
                registrering.append(dict(plats=mp['id'], tagning=r['tagning'], scen=r['scen'], roll=x['roll'], deklarerad_plats=x.get('plats'), deklarerad_pos_m=x['deklarerad_pos_m'], last_pos_m=x['last_pos_m'],
                                         restfel_m=x['restfel_m'], blick_rest_grader=x.get('blick_rest_grader'), troskel_m=REGISTRERING_VARNING_M,
                                         status='over_troskel' if x['restfel_m'] > REGISTRERING_VARNING_M else 'inom', avstandsfel_mellan_roller_m=rr.get('avstandsfel_m'),
                                         laspar_avstand_m=rr.get('laspar_avstand_m'), deklarerat_avstand_m=rr.get('deklarerat_avstand_m'), metod=rr['metod']))
    # Mätkonflikter: där GOLV2:s fria cue-beslut hade valt ett annat golv än det deklarerade. Deklarationen vinner; detta är ingen avvikelse
    # i planen utan en redovisning av läsfelet (hur långt kroppens/kamerans cues ligger från deklarationen).
    konflikter = []
    for p in platser:
        golv = next((m['golv'] for m in plan['matning'].get('platser', []) if m['id'] == p['id']), {})
        for s in (golv.get('matning') or {}).get('per_tagning', []):
            b = s.get('beslut') or {}
            if b.get('status') == 'deklarerad' and b.get('konflikt_med_deklaration'):
                fam = sorted({c['familj'] for c in b.get('cues', []) if c.get('anvand')})
                konflikter.append(dict(plats=p['id'], tagning=s['tagning'], fri_varde_m=b['fri_varde_m'], avvikelse_fri_mot_deklarerad_m=b['avvikelse_fri_mot_deklarerad_m'], cuefamiljer=fam,
                                       beslut='deklarationen vinner'))
    ut = dict(status='avviker' if avvikelser else 'bunden', tolerans_m=TOLERANS_M, poster=poster, avvikelser=avvikelser, matkonflikter=konflikter)
    if registrering: ut['registrering'] = dict(troskel_m=REGISTRERING_VARNING_M, roller=registrering, over_troskel=[x for x in registrering if x['status'] == 'over_troskel'])
    return ut
