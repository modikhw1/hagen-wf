"""till_kalla_underlag.py: semantik.json (+ ordtider.json) -> de indata som de befintliga verktygen redan läser. Inget verktyg ändras.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/semantik/till_kalla_underlag.py <klipp>

Skriver i semantik/ut/<klipp>/underlag/:
  vem_ar_vem.json       spår (tagning, ingest-id) -> klippnivåns person, roll och skäl; spår som inte är berättelsepersoner; dubbletter. Allt med ursprung.
  scen3d_roller.json    minimal fil i scen3d.json:s form (actors, shots[].actors/beat/source) för --scen3d i plats.py och kalla_bygg.py. Rollerna
                        binds av de verktygen i ordning efter rutor i bild, så aktörslistan skrivs i just den ordningen, med okand_s<n>_<id> på de platser
                        där spåret inte är en berättelseperson (samma namn som verktygen själva ger).
  hand.json             för plats.py --hand: rumsmall och layout (modellbedömt, med motivering). Inga meterlägen: dem kan modellen inte ge.
  ordtider_underlag.json  ordtider.json-formatet för kalla_bygg.py --ordtider: bara repliker som Whisper hörde. Resten står i ofunna_repliker.json.
  patch.json            kalla-patch/1 (bro/kort_till_kalla.py) för scener, intention och beats, plus avsnittet "tillagg" för det bron inte har fält för
                        (personer, skärmtext, props, plats). Alla värden har ursprung. tillampa_tillagg() fyller en kallas null/tomma fält.

Personer får bokstavsnamn A, B, C ... i ordning efter första tagning där de syns (modellens P1, P2 ... sparas i vem_ar_vem.json). Skälet: rumsmallarna och
plats.py namnger ankare efter person-id (stol_A, stol_B); ett id som P1 ger stol_P1 som ingen mall har.
"""
import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sem_gemensamt import UT, ladda, skriv, sha256, klipp_vagar, tagningar, sparlista  # noqa: E402

FUNK_TILL_BEAT = {'krok': 'hook', 'uppbyggnad': 'build-up', 'vandning': 'turn', 'punchline': 'punchline', 'avslut': 'payoff'}   # kalla_flera.BEAT_TILL_FUNKTION åt andra hållet
KONF = {'hog': 'hog', 'medel': 'medel', 'lag': 'lag', 'osaker': None}
ROLLTIPS = {'sitter': 'sate'}


def ursprung(sem, konfidens, **extra):
    return dict(typ='modellbedomd', modell=sem['ursprung']['modell'], prompt_version=sem['ursprung']['prompt_version'], konfidens=konfidens, **extra)


def personnamn(d, shots):
    """P-id -> bokstav i ordning efter första tagning där personen har ett spår (sedan P-nummer)."""
    forsta = {}
    for p in d['personer']:
        tg = sorted(int(s['tagning'][1:]) for s in p['spar']) or [10 ** 6]
        forsta[p['id']] = (tg[0], p['id'])
    ordn = sorted(forsta, key=lambda k: forsta[k])
    return {pid: chr(ord('A') + i) for i, pid in enumerate(ordn)}


def bygg(klipp):
    v = klipp_vagar(klipp); ut = v['ut']; sem = ladda(ut / 'semantik.json'); d = sem['data']
    shots = tagningar(v['ingest']); sp = {s['id']: sparlista(s) for s in shots}
    namn = personnamn(d, shots)
    # spår -> person eller None
    spar_person = {}; skal = {}
    for p in d['personer']:
        for s in p['spar']: spar_person[(s['tagning'], s['spar_id'])] = (p['id'], s['konfidens'])
    for e in d['ej_personer']: skal[(e['tagning'], e['spar_id'])] = e
    # -- vem_ar_vem och aktörslistor
    vv = {'schema': 'vem_ar_vem/1', 'klipp': klipp, 'not': 'Alla uppgifter är modellbedömda; spåren (tagning + ingest-id) är uppmätta nycklar.',
          'ursprung': ursprung(sem, None), 'personer': [], 'tagningar': []}
    vv['personer'] = [dict(id=namn[p['id']], modellens_id=p['id'], roll=p['roll'], beskrivning=p['beskrivning'], ursprung=ursprung(sem, KONF[p['konfidens']] or 'osaker')) for p in d['personer']]
    vv['personer'].sort(key=lambda x: x['id'])
    actors_per_shot = {}; dubbletter = []
    for s in shots:
        sid = s['id']; n = sid[1:]
        rang = sorted([t for t in sp[sid] if sp[sid][t]['har_sekvens']], key=lambda t: (-sp[sid][t]['rutor_i_bild'], t))
        sett = set(); lista = []; poster = []
        for t in sorted(sp[sid], key=lambda x: (len(x), x)):
            m = spar_person.get((sid, t)); e = skal.get((sid, t))
            post = dict(spar_id=t, rutor_i_bild=sp[sid][t]['rutor_i_bild'], har_sekvens=sp[sid][t]['har_sekvens'])
            if m:
                post.update(person=namn[m[0]], ursprung=ursprung(sem, m[1]))
            elif e:
                post.update(person=None, ej_berattelseperson=dict(typ=e['typ'], skal=e['skal']), ursprung=ursprung(sem, e['konfidens']))
            else:
                post.update(person=None, ej_berattelseperson=dict(typ='saknas_i_svaret', skal='Modellen nämnde inte spåret.'), ursprung=ursprung(sem, 'osaker'))
            poster.append(post)
        for t in rang:
            m = spar_person.get((sid, t))
            if m and namn[m[0]] not in sett:
                sett.add(namn[m[0]]); lista.append(namn[m[0]])
            else:
                lista.append(f'okand_s{n}_{t}')
                if m: dubbletter.append(dict(tagning=sid, spar_id=t, person=namn[m[0]], orsak='Två spår i samma tagning pekar på samma person; spåret med flest rutor behåller personen, det andra blir okand_.'))
        for post in poster:
            if post['person'] and f'okand_s{n}_{post["spar_id"]}' in lista:
                post['dubblett_av_person'] = post.pop('person'); post['person'] = None
        actors_per_shot[sid] = lista
        vv['tagningar'].append(dict(tagning=sid, spar=poster, aktorsordning_for_verktygen=lista))
    vv['dubbletter'] = dubbletter
    # -- scen3d_roller.json
    fps = shots[0]['fps']
    fkn = {x['tagning']: x for x in d['tagningar']}
    s3 = {'schema': 'scen3d/2-minimal', 'not': 'Endast fälten som plats.py och kalla_flera.py läser. Skriven av till_kalla_underlag.py ur modellbedömda uppgifter.'}
    s3.update(source=dict(clip=str(v['video'].relative_to(v['video'].parents[2])).replace('\\', '/'), fps=fps),
              actors=[dict(id=p['id'], role=p['roll'], _ursprung=p['ursprung']) for p in vv['personer']], shots=[], dialogue=[])
    for s in shots:
        f = fkn.get(s['id'])
        beat = FUNK_TILL_BEAT.get(f['funktion']) if f else None
        s3['shots'].append(dict(id=s['id'], source=dict(inSec=s['start'] / fps, outSec=s['slut'] / fps), actors=[dict(id=a) for a in actors_per_shot[s['id']]], beat=beat,
                                _ursprung=ursprung(sem, f['konfidens'] if f else 'osaker', funktion_modell=f['funktion'] if f else None)))
    # -- hand.json (plats.py)
    pl = d['plats']; hand = dict(_ursprung=ursprung(sem, KONF[pl['konfidens']] or 'osaker'))
    if pl['rumsmall_forslag'] not in ('ingen_passar', 'osaker'):
        hand['rumsmall'] = pl['rumsmall_forslag']
    par = [p for p in d['par'] if p['over'] != 'osaker']
    over = par[0]['over'] if par else 'osaker'
    hand['layout'] = dict(val={'separata_bord': 'tva_bord', 'samma_bord': 'gemensamt_bord', 'disk_mellan': 'disk', 'sida_vid_sida': 'sida_vid_sida'}.get(over, 'okand'),
                          status='modellbedomd', orsak=f'Modellens bedömning ({sem["ursprung"]["modell"]}): plats {pl["typ"]}; {pl["motivering"]} Paret: {over}. Inga avstånd i meter anges: modellen kan inte mäta.')
    # -- ordtider_underlag.json
    ot_fil = ut / 'ordtider.json'; ot = ladda(ot_fil) if ot_fil.exists() else None; ofunna = []
    if ot:
        kept = []
        for l in ot['lines']:
            if l['stodd']:
                l = dict(l); l['i'] = len(kept)
                l['speaker'] = namn.get(l['speaker']) if l['speaker'] != 'okand' else None
                l['ursprung_text_talare'] = ursprung(sem, None, falt='text och talare'); kept.append(l)
            else:
                ofunna.append(dict(id=l['id'], text=l['text'], talare=namn.get(l['speaker'], l['speaker']), orsak=l['skal'], geminis_tid=[l['est_start'], l['est_end']], tackning=l['tackning']))
        otu = dict(ot, lines=kept); otu['match_ratio'] = round(sum(x['tackning'] for x in kept) / len(kept), 3) if kept else None
        otu['not'] = 'Repliker som Whisper inte hörde är borttagna (se ofunna_repliker.json). Text och talare är modellens; ord och tider är Whispers.'
    else:
        otu = None
    # -- patch.json (kalla-patch/1)
    sce = []
    for s in shots:
        f = fkn.get(s['id'])
        k = KONF[f['konfidens']] if f else None
        ok = f is not None and f['funktion'] not in ('osaker',)
        sce.append(dict(id=f's{s["id"][1:]}', beats=[], funktion=(None if not ok or f['funktion'] == 'ingen' else f['funktion']), bar=None, syfte=f['vad'] if f else None,
                        konfidens=k, metod='modellbedomd',
                        ursprung=ursprung(sem, f['konfidens'] if f else 'osaker')))
    def moment(fn):
        t = next((x for x in d['tagningar'] if x['funktion'] == fn), None)
        return dict(finns=True if t else None, vad=t['vad'] if t else None, scen=f's{t["tagning"][1:]}' if t else None)
    patch = dict(schema_version='kalla-patch/1', klipp=klipp,
                 beskrivning='Modellbedömd patch i bro/kort_till_kalla.py:s format. Beats saknas (modellen gav ingen kortindelning). Scenfälten följer tagningarna.',
                 semantik=dict(beats=[], scener=sce, intention=dict(karna=d['klipp']['karna'], krok=moment('krok'), vandning=moment('vandning'), payoff=moment('punchline'),
                                                                   kalla='modellbedomd'), serie=None),
                 justering=[], ursprung=ursprung(sem, KONF[d['klipp']['konfidens']] or 'osaker'))
    patch['tillagg'] = {'not': 'Det bron inte har fält för. Format: eget, tillampa_tillagg() här. Där kalla-schemat har ett ursprungsfält (roll_kalla, kalla) sätts det till modell; annars står ursprunget bara här.'}
    patch['tillagg'].update(
        personer=[dict(id=p['id'], roll=p['roll'], beskrivning=p['beskrivning'], roll_kalla='modell', ursprung=p['ursprung']) for p in vv['personer']],
        skarmtext=[dict(scen=f's{x["tagning"][1:]}', text=x['text'], kalla='modell', ursprung=ursprung(sem, KONF[x['konfidens']] or 'osaker')) for x in d['skarmtext']],
        props=[dict(id=f'm_{o["id"]}', typ=o['typ'], etikett=o['etikett'], agare=namn.get(o['hallare']), scener=[f's{t[1:]}' for t in o['tagningar']], anvands=o['anvands'], kalla='modell',
                    ursprung=ursprung(sem, KONF[o['konfidens']] or 'osaker')) for o in d['props']],
        plats=dict(typ=pl['typ'], rumsmall_forslag=pl['rumsmall_forslag'], beskrivning=pl['beskrivning'], ursprung=ursprung(sem, KONF[pl['konfidens']] or 'osaker')),
        placeringar=[dict(person=namn[x['person']], hallning=x['hallning'], ankartyp=x['ankartyp'], vid_del=x['vid_del'], beskrivning=x['beskrivning'], scener=[f's{t[1:]}' for t in x['tagningar']],
                          ursprung=ursprung(sem, KONF[x['konfidens']] or 'osaker')) for x in d['placeringar']],
        par=[dict(a=namn[x['a']], b=namn[x['b']], vander_mot_varandra=x['vander_mot_varandra'], over=x['over'], ursprung=ursprung(sem, KONF[x['konfidens']] or 'osaker')) for x in d['par']],
        kamerauppstallningar=[dict(id=k['id'], scener=[f's{t[1:]}' for t in k['tagningar']], ursprung=ursprung(sem, KONF[k['konfidens']] or 'osaker')) for k in d['kamerauppstallningar']])
    u = ut / 'underlag'; u.mkdir(parents=True, exist_ok=True)
    for namn_, data in (('vem_ar_vem.json', vv), ('scen3d_roller.json', s3), ('hand.json', hand), ('patch.json', patch)): skriv(u / namn_, data)
    if otu: skriv(u / 'ordtider_underlag.json', otu); skriv(u / 'ofunna_repliker.json', ofunna)
    skriv(u / 'ursprung.json', dict(semantik_sha256=sha256(ut / 'semantik.json'), ordtider_sha256=sha256(ot_fil) if ot else None, personnamn=namn))
    return u, namn, ofunna, dubbletter


def tillampa_tillagg(kalla, patch, min_konfidens='medel', semantik_fil=None):
    """Kopia av kalla där patch['tillagg'] fyllt i det som saknas: personers roll/beskrivning (där null), skärmtext och props (läggs till om tomma).
    Rör inte kallas mätningsdel. Värden under min_konfidens hoppas över. Ger (kopia, lista över vad som gjordes).
    Rättar också ursprunget som kalla_bygg skriver fast när modellens underlag används: roll_kalla 'scen3d' -> 'modell' för personer vars roll kommer
    från patchen, och replik.kalla 'whisper' -> 'modell' (texten och talaren är modellens, bara orden och tiderna är Whispers). Lägger en kvalitetspost."""
    r = {'hog': 3, 'medel': 2, 'lag': 1}
    k = copy.deepcopy(kalla); sem = k['semantik']; gjort = []
    ok = lambda u: r.get(u['konfidens'], 0) >= r[min_konfidens]
    T = patch['tillagg']
    per = {p['id']: p for p in sem['personer']}
    for p in T['personer']:
        q = per.get(p['id'])
        if q and q.get('roll') == p['roll'] and q.get('roll_kalla') == 'scen3d':
            q['roll_kalla'] = 'modell'; gjort.append(f'person {p["id"]}.roll_kalla scen3d -> modell')
        if q and ok(p['ursprung']):
            if q.get('roll') is None: q['roll'] = p['roll']; q['roll_kalla'] = 'modell'; gjort.append(f'person {p["id"]}.roll')
            if q.get('beskrivning') is None: q['beskrivning'] = p['beskrivning']; gjort.append(f'person {p["id"]}.beskrivning')
    scener = {s['id'] for s in sem['scener']}
    if not sem['skarmtext']:
        for i, x in enumerate(T['skarmtext']):
            if x['scen'] in scenerna(scener) and ok(x['ursprung']):
                s = next(s for s in sem['scener'] if s['id'] == x['scen'])
                sem['skarmtext'].append(dict(id=f'st{i + 1}', text=x['text'], start_s=s['start_s'], slut_s=s['slut_s'], scen=x['scen'], kalla='modell')); gjort.append(f'skarmtext st{i + 1}')
    for o in T['props']:
        if ok(o['ursprung']) and (o['agare'] is None or o['agare'] in per) and all(s in scener for s in o['scener']):
            sem['props'].append(dict(id=o['id'], typ=o['typ'], etikett=o['etikett'], agare=o['agare'], stod=None, faste=None, rum_ref=None, kalla='modell', scen=o['scener'][0] if o['scener'] else None)); gjort.append(f'prop {o["id"]}')
    for rep in sem['repliker']:
        if rep['kalla'] == 'whisper': rep['kalla'] = 'modell'
    gjort.append('repliker.kalla whisper -> modell')
    k['matning']['kvalitet'].append(dict(post='semantik.modellbedomt_underlag', status='modellbedomd',
        metod='Personer, roller, vem som är vem per tagning, replikernas text och talare, scenfunktion, plats, skärmtext och props kommer från ' + (patch['ursprung']['modell']) +
              ' (semantik.json), bundet till uppmätta spår. Ord och tider i replikerna är lokal Whisper. Där äldre kvalitetsposter säger scen3d.json avser de handkalibrerade notan, inte detta underlag.',
        osakerhet='Modellens konfidens per värde ligger i patch.json (ursprung). Ingen människa har granskat.', saknas_steg='Granska semantik.json mot kontaktbladen.', kalla_fil=semantik_fil))
    return k, gjort


def scenerna(s): return s


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); a.add_argument('klipp'); x = a.parse_args()
    u, namn, ofunna, dubb = bygg(x.klipp)
    print('skrev', u); print('personnamn', namn); print('ofunna repliker', [o['id'] for o in ofunna]); print('dubbletter', dubb)


if __name__ == '__main__':
    main()
