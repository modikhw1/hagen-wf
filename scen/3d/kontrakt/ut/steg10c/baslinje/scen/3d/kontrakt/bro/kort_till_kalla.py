"""v5-kort + kalla.json -> semantisk patch för kalla (separat JSON-fil, kalla.json rörs aldrig).

Kör från projektroten:
  scen/.venv/Scripts/python.exe scen/3d/kontrakt/bro/kort_till_kalla.py <kort.json> <kalla.json> <patch_ut.json>

Patchen innehåller beats (funktion, bar, bunden, vad), en justering beat -> scen med metod och
konfidens per beat, scenfält (funktion, bar, syfte) där justeringen räcker, och intentionsfält.
Allt som kortet inte stöder lämnas null. Inga tider och inga texter hittas på: tider kommer bara
från kalla (scenerna) eller från kortet om kortets beats har start_s och slut_s (v5-kort har inte det).
Bara standardbiblioteket.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

KONF = {'hog': 3, 'medel': 2, 'lag': 1}
STOPP = {'och', 'att', 'som', 'det', 'den', 'ett', 'med', 'för', 'på', 'av', 'till', 'en', 'är', 'inte', 'ska',
         'har', 'om', 'men', 'så', 'vi', 'du', 'jag', 'de', 'där', 'här', 'från', 'eller', 'vad', 'när'}
TEXT_TROSKEL = 0.6


def ladda(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def skriv(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def ord_(t):
    return [w for w in re.findall(r'[a-zåäöé0-9]+', (t or '').lower()) if len(w) >= 3 and w not in STOPP]


def citat(vad):
    """Textstycken i citattecken i beatets vad. Bara det kortet själv citerar."""
    return [q.strip() for q in re.findall(r"['\"“”‘’]([^'\"“”‘’]{3,}?)['\"“”‘’]", vad or '')]


def _lika(q, text):
    a, b = set(ord_(q)), set(ord_(text))
    if len(a) < 2:
        return 0.0
    return len(a & b) / len(a)


def _fordela(beats, scener):
    """Ordningsbaserad fördelning av scener på beats, jämnt efter antal. Returnerar {beat: [scen]}."""
    nb, ns = len(beats), len(scener)
    if nb == 0 or ns == 0:
        return {}
    ut = {b: [] for b in beats}
    if nb <= ns:
        for k, s in enumerate(scener):
            ut[beats[k * nb // ns]].append(s)
    else:
        for j, b in enumerate(beats):
            ut[b].append(scener[j * ns // nb])
    return ut


def justera(beats, scener, repliker, skarmtext):
    """Beat -> scen. En post per beat: {scener: [index], metod, konfidens, belagg}.
    Metoder: tid, enda_scen, text, ordning_1till1, ordning."""
    nb, ns = len(beats), len(scener)
    if ns == 0:
        raise ValueError('kalla har inga scener')
    # 1. tidsbaserad: bara om kortets beats själva har tider
    if all(isinstance(b.get('start_s'), (int, float)) and isinstance(b.get('slut_s'), (int, float)) for b in beats):
        res = []
        for b in beats:
            med = [k for k, s in enumerate(scener)
                   if min(b['slut_s'], s['slut_s']) - max(b['start_s'], s['start_s']) > 1e-9]
            res.append(dict(scener=med, metod='tid', konfidens='hog',
                            belagg=f"beatets tider [{b['start_s']}, {b['slut_s']}) mot scenernas intervall"))
        if all(r['scener'] for r in res):
            return res
    # 2. en enda scen: beatet ligger nödvändigtvis i den
    if ns == 1:
        return [dict(scener=[0], metod='enda_scen', konfidens='hog',
                     belagg='kalla har en enda scen; beatets plats inom scenen är okänd (inga tider)') for _ in beats]
    # 3. textankare: citat i beatets vad mot repliker och skärmtext
    scen_index = {s['id']: k for k, s in enumerate(scener)}
    kallor = [(r['text'], scen_index.get(r.get('scen')), f"replik {r['id']}") for r in repliker if r.get('text')]
    kallor += [(t['text'], scen_index.get(t.get('scen')), f"skarmtext {t['id']}") for t in skarmtext if t.get('text')]
    res = [None] * nb
    ankare = {}
    sista = -1
    for i, b in enumerate(beats):
        traffar = []
        for q in citat(b['vad']):
            poang = [(k, _lika(q, text), namn) for text, k, namn in kallor if k is not None]
            bast_q = max((p for _, p, _ in poang), default=0.0)
            # bara de bästa träffarna för citatet: allmänna ord ger annars falska träffar i andra repliker
            traffar += [t for t in poang if t[1] >= TEXT_TROSKEL and t[1] >= bast_q - 0.05]
        if not traffar:
            continue
        ks = sorted({t[0] for t in traffar})
        if ks[0] < sista:
            continue  # bryter ordningen mot ett tidigare ankare: förkastas
        bast = max(t[1] for t in traffar)
        res[i] = ankare[i] = dict(
            scener=ks, metod='text', konfidens='hog' if bast >= 0.9 and len(ks) == 1 else 'medel',
            belagg='citat matchar ' + ', '.join(sorted({f'{t[2]} ({t[1]:.2f})' for t in traffar})))
        sista = ks[-1]
    # 4. ordning: fyll mellanrummen mellan ankare
    lik = (nb == ns and not ankare)
    i = 0
    while i < nb:
        if res[i] is not None:
            i += 1
            continue
        j = i
        while j < nb and res[j] is None:
            j += 1
        fore = max((a for a in ankare if a < i), default=None)
        nasta = min((a for a in ankare if a >= j), default=None)
        lo = (max(ankare[fore]['scener']) + 1) if fore is not None else 0
        hi = (min(ankare[nasta]['scener']) - 1) if nasta is not None else ns - 1
        tillg = list(range(lo, hi + 1))
        grupp = list(range(i, j))
        if tillg:
            for b, sc in _fordela(grupp, tillg).items():
                res[b] = dict(scener=sc, metod='ordning_1till1' if lik else 'ordning',
                              konfidens='medel' if lik else 'lag',
                              belagg=(f'lika många beats som scener ({nb}); fördelade i ordning' if lik else
                                      f'{nb} beats på {ns} scener, fördelade jämnt i ordning (kortet saknar tider)'
                                      + ('; mellan textankare' if ankare else '')))
        else:
            delad = ankare[fore]['scener'][-1] if fore is not None else ankare[nasta]['scener'][0]
            for b in grupp:
                res[b] = dict(scener=[delad], metod='ordning', konfidens='lag',
                              belagg='ingen ledig scen mellan ankarna; beatet delar scen med ett ankare')
        i = j
    return res


def _min_konf(lista):
    return min(lista, key=lambda k: KONF[k]) if lista else None


def bygg_patch(kort, kalla, kort_fil=None):
    sem = kalla['semantik']
    scener = sem['scener']
    beats = kort['beats']
    for b in beats:
        for f in ('vad', 'funktion', 'bar', 'bunden'):
            if f not in b:
                raise ValueError(f'kortets beat saknar {f}')
    just = justera(beats, scener, sem.get('repliker', []), sem.get('skarmtext', []))
    patch_beats, just_ut = [], []
    for i, (b, j) in enumerate(zip(beats, just), start=1):
        sc_ids = [scener[k]['id'] for k in j['scener']]
        patch_beats.append(dict(id=f'b{i}', nr=i, scen=sc_ids[0] if len(sc_ids) == 1 else None,
                                funktion=b['funktion'], bar=b['bar'], vad=b['vad'],
                                bunden=None if b['bunden'] == 'ingen' else b['bunden']))
        just_ut.append(dict(beat_nr=i, scener=sc_ids, metod=j['metod'], konfidens=j['konfidens'], belagg=j['belagg']))
    # scenfält
    scen_ut = []
    for k, s in enumerate(scener):
        hit = [i for i, j in enumerate(just) if k in j['scener']]
        post = dict(id=s['id'], beats=[i + 1 for i in hit], funktion=None, bar=None, syfte=None, konfidens=None, metod=None)
        if hit:
            konf = _min_konf([just[i]['konfidens'] for i in hit])
            post['konfidens'] = konf
            post['metod'] = sorted({just[i]['metod'] for i in hit})
            fk = {beats[i]['funktion'] for i in hit}
            br = {beats[i]['bar'] for i in hit}
            if len(fk) == 1:
                post['funktion'] = next(iter(fk))
            if len(br) == 1:
                post['bar'] = next(iter(br))
            if len(hit) == 1 and len(just[hit[0]]['scener']) == 1 and KONF[konf] >= KONF['medel']:
                post['syfte'] = beats[hit[0]]['vad']   # kortets "vad", ordagrant: det som sker, inget fristående "varför"
            kon = {}
            for falt in ('funktion', 'bar', 'syfte'):
                if post[falt] is not None and s.get(falt) is not None and s[falt] != post[falt]:
                    kon[falt] = dict(kalla=s[falt], kort=post[falt])
            if kon:
                post['konflikt_med_kalla'] = kon
        scen_ut.append(post)
    # intention
    gv = kort.get('grundvarde') or {}

    def moment(finns, fn):
        i = next((n for n, b in enumerate(beats) if b['funktion'] == fn), None)
        if i is None:
            return dict(finns=finns, vad=None, scen=None)
        sc = just_ut[i]['scener']
        return dict(finns=True if finns is None else finns, vad=beats[i]['vad'], scen=sc[0] if len(sc) == 1 else None)

    krok_finns = None if gv.get('krok') is None else gv['krok'] != 'ingen'
    vandning_finns = gv['vandning'] if isinstance(gv.get('vandning'), bool) else None
    intention = dict(karna=kort.get('karna'), krok=moment(krok_finns, 'krok'),
                     vandning=moment(vandning_finns, 'vandning'),
                     payoff=moment(None, 'punchline'), kalla='harness v5-kort')
    saknas = [
        'semantik.serie: v5-kortet har ingen serieposition, lämnas null.',
        'beats[].start_s/slut_s: v5-kortets beats har inga tider, så beats har inga tider i patchen.',
    ]
    if any(p['funktion'] is None and p['beats'] for p in scen_ut):
        saknas.append('scener[].funktion: null där flera beats med olika funktion delar scen.')
    tomma = [p['id'] for p in scen_ut if not p['beats']]
    if tomma:
        saknas.append('scener utan beat: ' + ', '.join(tomma) + ' (inga beats föll på dem).')
    return dict(
        schema_version='kalla-patch/1',
        kalla=dict(klipp_id=kalla['klipp']['id'], sha256=kalla['klipp']['sha256'], revision=kalla['revision']),
        kort=dict(id=kort.get('id'), konto=kort.get('konto'), modell=kort.get('modell'), fil=kort_fil),
        metod=dict(
            beskrivning='Beat -> scen: tid om kortets beats har tider (v5 har det inte), enda_scen om kalla har en scen, '
                        'text om ett citat i beatets vad matchar en replik eller skärmtext (ordöverlapp >= '
                        f'{TEXT_TROSKEL}), annars ordning (jämn fördelning, konfidens lag; medel bara när beats = scener).',
            konfidens='hog, medel, lag. Scenfält får lägsta konfidensen bland sina beats. '
                      'tillampa_patch släpper bara igenom medel eller bättre som standard.'),
        semantik=dict(beats=patch_beats, scener=scen_ut, intention=intention, serie=None),
        justering=just_ut,
        saknas=saknas,
    )


def tillampa_patch(kalla, patch, min_konfidens='medel'):
    """Kopia av kalla med patchen ifylld. Fyller bara fält som är null eller tomma i kalla.
    Revisionen ändras inte här: den som skriver filen ökar revision. Scenfält under min_konfidens utelämnas;
    beat.scen sätts bara om beatets justering når min_konfidens."""
    k = copy.deepcopy(kalla)
    sem = k['semantik']
    gräns = KONF[min_konfidens]
    just = {j['beat_nr']: j for j in patch['justering']}
    if not sem['beats']:
        ny = []
        for b in patch['semantik']['beats']:
            b = dict(b)
            if KONF[just[b['nr']]['konfidens']] < gräns:
                b['scen'] = None
            ny.append(b)
        sem['beats'] = ny
    per = {p['id']: p for p in patch['semantik']['scener']}
    for s in sem['scener']:
        p = per.get(s['id'])
        if not p or p['konfidens'] is None or KONF[p['konfidens']] < gräns:
            continue
        for f in ('funktion', 'bar', 'syfte'):
            if s.get(f) is None and p[f] is not None:
                s[f] = p[f]
    ik, ip = sem['intention'], patch['semantik']['intention']
    if ik.get('karna') is None:
        ik['karna'] = ip['karna']
    for m in ('krok', 'vandning', 'payoff'):
        for f in ('finns', 'vad', 'scen'):
            if ik[m].get(f) is None:
                ik[m][f] = ip[m][f]
    if ik.get('kalla') in (None, 'saknas'):
        ik['kalla'] = ip['kalla']
    return k


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('kort')
    a.add_argument('kalla')
    a.add_argument('ut')
    x = a.parse_args()
    if Path(x.ut).exists():
        a.error('Utfilen finns redan; välj en ny sökväg.')
    p = bygg_patch(ladda(x.kort), ladda(x.kalla), kort_fil=Path(x.kort).as_posix())
    skriv(x.ut, p)
    print(f"{len(p['semantik']['beats'])} beats, {len(p['semantik']['scener'])} scener: "
          + ' '.join(f"b{j['beat_nr']}->{'+'.join(j['scener'])}({j['metod']},{j['konfidens']})" for j in p['justering']))


if __name__ == '__main__':
    main()
