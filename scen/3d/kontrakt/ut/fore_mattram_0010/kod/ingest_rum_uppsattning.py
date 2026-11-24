"""Konsensus över uppsättningsbedömningar (rum_video.py --variant uppsattning) och urval på nivåreglaget 0–1.

    python rum_uppsattning.py <u1.json> <u2.json> ... [--ut uppsattning.json] [--niva 0.6] [--deklaration konsensus.json --ut-deklaration niva.json]

Element matchas mellan körningarna på normaliserade ord i id (å/ä/ö vikta, ordsplit på _), inom samma kategorifamilj.
Ett element behålls om minst hälften av körningarna har det. Tröskeln är medianen; pa, ankare och bar_handlingen tas med majoritet.
Med --niva skrivs också vad som byggs vid den nivån (tröskel <= nivå) och vad formatet ännu inte kan bygga.
Med --deklaration skrivs en deklaration för nivån: bord/diskar med tröskel över nivån stryks, och föremål och utrustning upp till nivån
läggs i fältet `foremal` (pa = möbel eller roll som håller, storlek som antaget intervall ±25 %).
"""
import argparse, json, statistics, unicodedata
from collections import Counter
from pathlib import Path

FAMILJ = {'figur': 'figur', 'rumsskal': 'rum', 'mobel': 'sak', 'foremal': 'sak', 'utrustning': 'sak', 'dekor': 'sak', 'text': 'text'}
BYGGBAR = {'figur': 'byggs (kroppar)', 'rumsskal': 'byggs som mallens golv och väggar', 'mobel': 'byggs som bord/disk (lada) om den finns i deklarationen'}
STOPP = {'i', 'pa', 'med', 'the', 'of', 'en', 'ett', 'och'}


def ord_(s):
    s = unicodedata.normalize('NFKD', s.replace('�', 'a')).encode('ascii', 'ignore').decode().lower()
    return {w for w in s.replace('-', '_').split('_') if w and w not in STOPP}


def lika(a, b):
    if a['id'] == b['id']: return True
    A, B = ord_(a['id']), ord_(b['id'])
    if not A or not B: return False
    # Rollbokstäver (a, b, c) skiljer t.ex. forklade_A från forklade_B och måste stämma om båda har en.
    ra, rb = {w for w in A if len(w) == 1}, {w for w in B if len(w) == 1}
    if ra and rb and ra != rb: return False
    A, B = A - ra, B - rb
    return bool(A and B) and (len(A & B) / len(A | B) >= .5 or A <= B or B <= A)


def bildkonsensus(E):
    """Vanligaste tagningen bland körningarnas bildrutor och medianrutan i den."""
    b = [e['bild'] for e in E if isinstance(e.get('bild'), dict) and len(e['bild'].get('box_2d') or []) == 4]
    if not b: return None
    t = Counter(x['tagning'] for x in b).most_common(1)[0][0]; rutor = [x['box_2d'] for x in b if x['tagning'] == t]
    return dict(tagning=t, box_2d=[round(statistics.median(v)) for v in zip(*rutor)], antal=len(rutor))


def bilderkonsensus(E):
    """Per tagning: medianrutan bland körningarna som angav elementet i den tagningen (minst två körningar, annars den enda)."""
    per = {}
    for e in E:
        for b in (e.get('bilder') or []) + ([e['bild']] if isinstance(e.get('bild'), dict) else []):
            if isinstance(b, dict) and len(b.get('box_2d') or []) == 4: per.setdefault(b.get('tagning'), {}).setdefault(id(e), b['box_2d'])
    ut = []
    for t, d in sorted(per.items(), key=lambda kv: str(kv[0])):
        rutor = list(d.values())
        if len(rutor) >= min(2, len(E)): ut.append(dict(tagning=t, box_2d=[round(statistics.median(v)) for v in zip(*rutor)], antal=len(rutor)))
    return ut


def main():
    a = argparse.ArgumentParser(description=__doc__); a.add_argument('filer', nargs='+'); a.add_argument('--ut'); a.add_argument('--niva', type=float)
    a.add_argument('--deklaration'); a.add_argument('--ut-deklaration')
    a = a.parse_args(); R = [json.loads(Path(f).read_text(encoding='utf-8'))['svar'] for f in a.filer]; N = len(R)
    kluster = []
    for r, S in enumerate(R):
        for e in S['element']:
            k = next((k for k in kluster if FAMILJ.get(k['kategori'][0]) == FAMILJ.get(e['kategori']) and r not in k['korningar'] and any(lika(e, x) for x in k['element'])), None)
            if not k: k = dict(kategori=[], korningar=[], element=[]); kluster.append(k)
            k['kategori'].append(e['kategori']); k['korningar'].append(r); k['element'].append(e)
    ut = []
    for k in kluster:
        if len(k['korningar']) < N / 2: continue
        E = k['element']; maj = lambda f: Counter(str(e.get(f, '')) for e in E).most_common(1)[0][0]
        storlek = [statistics.median(v) for v in zip(*[e['storlek_m'] for e in E if len(e.get('storlek_m') or []) == 3])] if any(len(e.get('storlek_m') or []) == 3 for e in E) else None
        ut.append(dict(id=Counter(e['id'] for e in E).most_common(1)[0][0], varianter=sorted({e['id'] for e in E}), kategori=Counter(k['kategori']).most_common(1)[0][0],
                       troskel=statistics.median(e['troskel'] for e in E), troskel_spann=[min(e['troskel'] for e in E), max(e['troskel'] for e in E)],
                       antal=f"{len(E)}/{N}", bar_handlingen=sum(e['bar_handlingen'] for e in E) > len(E) / 2, pa=maj('pa'), ankare=maj('ankare'),
                       storlek_m=[round(v, 2) for v in storlek] if storlek else None, beskrivning=next((e.get('beskrivning') for e in E if e.get('beskrivning')), ''),
                       bild=bildkonsensus(E), bilder=bilderkonsensus(E),
                       tagningar=sorted({t for e in E for t in e.get('tagningar', [])}, key=lambda t: (len(t), t)) and
                                 sorted([t for t in {t for e in E for t in e.get('tagningar', [])} if sum(t in e.get('tagningar', []) for e in E) >= len(E) / 2], key=lambda t: (len(t), t))))
    ut.sort(key=lambda e: (e['troskel'], e['id']))
    res = dict(antal_korningar=N, rekommenderad_niva=statistics.median(S['rekommenderad_niva'] for S in R),
               rekommenderad_niva_spann=[min(S['rekommenderad_niva'] for S in R), max(S['rekommenderad_niva'] for S in R)],
               sammanfattningar=[S['sammanfattning'] for S in R], element=ut)
    if a.niva is not None:
        med = [e for e in ut if e['troskel'] <= a.niva]
        res['urval'] = dict(niva=a.niva, byggs=[e['id'] for e in med if e['kategori'] in BYGGBAR],
                            kan_inte_byggas_an=[f"{e['id']} ({e['kategori']}, på {e['pa']})" for e in med if e['kategori'] not in BYGGBAR])
    if a.deklaration and a.niva is not None:
        D = json.loads(Path(a.deklaration).read_text(encoding='utf-8')); trosk = {v: e['troskel'] for e in ut for v in e['varianter']}
        strukna = [p for p, v in D['platser'].items() if v.get('typ') == 'bord' and trosk.get(p, 0) > a.niva]
        for p in strukna: del D['platser'][p]
        roller = set(D['roller'])
        D['foremal'] = {e['id']: dict(kategori=e['kategori'], beskrivning=e['beskrivning'], troskel=e['troskel'], bar_handlingen=e['bar_handlingen'],
                                      **({'halls_av': e['pa']} if e['pa'] in roller else {'pa': e['pa']}),
                                      storlek_m=[[round(v * .75, 2), round(v * 1.25, 2)] for v in e['storlek_m']] if e['storlek_m'] else None, status='antagen',
                                      **({'bild': {k: e['bild'][k] for k in ('tagning', 'box_2d')}} if e.get('bild') else {}),
                                      **({'bilder': [{k: b[k] for k in ('tagning', 'box_2d')} for b in e['bilder']]} if e.get('bilder') else {}),
                                      tagningar_i_bild=e['tagningar'], kalla=f"uppsättningskonsensus {e['antal']} körningar, tröskel {e['troskel']}")
                        for e in ut if e['kategori'] in ('foremal', 'utrustning') and e['troskel'] <= a.niva}
        # Möbler som finns kvar får sin bildruta (originalets 2D-läge), så att kompilatorn kan placera dem mot den lösta kameran.
        for e in ut:
            for v in e['varianter']:
                if v in D['platser'] and D['platser'][v].get('typ') == 'bord':
                    D['platser'][v].setdefault('beskrivning', e['beskrivning']); D['platser'][v]['tagningar_i_bild'] = e['tagningar']
                if v in D['platser'] and D['platser'][v].get('typ') == 'bord' and e.get('bild'):
                    D['platser'][v]['bild'] = {k: e['bild'][k] for k in ('tagning', 'box_2d')}
                    if e.get('bilder'): D['platser'][v]['bilder'] = [{k: b[k] for k in ('tagning', 'box_2d')} for b in e['bilder']]
        D['niva'] = dict(varde=a.niva, rekommenderad=res['rekommenderad_niva'], strukna_mobler=strukna, status='antagen')
        D['klipp'] = D['klipp'] + f'_n{int(a.niva * 10)}'
        Path(a.ut_deklaration).write_text(json.dumps(D, ensure_ascii=False, indent=2), encoding='utf-8'); print('deklaration för nivå', a.niva, '->', a.ut_deklaration)
    ut_fil = Path(a.ut) if a.ut else Path(a.filer[0]).parent / 'uppsattning.json'
    ut_fil.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"rekommenderad nivå {res['rekommenderad_niva']} (spann {res['rekommenderad_niva_spann']}), {len(ut)} element i minst hälften av {N} körningar")
    for e in ut: print(f"  {e['troskel']:.1f} [{e['troskel_spann'][0]}–{e['troskel_spann'][1]}] {e['antal']} {e['kategori']:<10} {e['id']:<26} på {e['pa']:<14} {'BÄR' if e['bar_handlingen'] else ''}")
    if 'urval' in res: print('nivå', a.niva, 'byggs:', res['urval']['byggs'], '| kan inte byggas än:', res['urval']['kan_inte_byggas_an'])
    print('->', ut_fil)


if __name__ == '__main__': main()
