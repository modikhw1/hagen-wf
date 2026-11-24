"""Jämför semantik.json + ordtider.json för notan med facit: scen3d.json (roller, beats, repliker), data/ordtider.json, exempel/notan/kalla.json
och ingest/ut/notan-tagningar/plats/ (hand.json, plats_matt.json). Facit är handgjort och kan ha fel: varje avvikelse listas för bedömning.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/semantik/utvardera_notan.py
Skriver ut/notan/utvardering.json och skriver ut en sammanfattning.
"""
import json
import statistics
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sem_gemensamt import SCEN, INGEST_UT, UT, HIT, ladda, skriv, klipp_vagar, tagningar, sparlista, norm_ord  # noqa: E402

BEAT = {'hook': 'krok', 'build-up': 'uppbyggnad', 'turn': 'vandning', 'punchline': 'punchline', 'payoff': 'avslut', 'reaction': None}


def wer(ref, hyp):
    r = [norm_ord(w) for w in ref.split() if norm_ord(w)]; h = [norm_ord(w) for w in hyp.split() if norm_ord(w)]
    d = np.zeros((len(r) + 1, len(h) + 1), int); d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return int(d[-1, -1]), len(r)


def main():
    v = klipp_vagar('notan'); sem = ladda(UT / 'notan/semantik.json')['data']; ot = ladda(UT / 'notan/ordtider.json')
    s3 = ladda(SCEN / '3d/scen3d.json'); kalla = ladda(SCEN / '3d/kontrakt/exempel/notan/kalla.json')
    hand = ladda(v['ingest'] / 'plats/hand.json'); gm = ladda(v['ingest'] / 'plats/plats_matt.json')
    ut = {}; avv = []

    # --- 1. vem är vem per spår. Facit: samma regel som kalla_flera (rang efter rutor i bild, actors i ordning); S4:4 har ingen roll.
    facit = {}
    for sh in tagningar(v['ingest']):
        sp = sparlista(sh); rang = sorted(sp, key=lambda p: (-sp[p]['rutor_i_bild'], p))
        akt = [a['id'] for a in next(s for s in s3['shots'] if s['id'] == sh['id'])['actors']]
        for i, p in enumerate(rang): facit[(sh['id'], p)] = akt[i] if i < len(akt) else None
    modell = {}
    for p in sem['personer']:
        for s in p['spar']: modell[(s['tagning'], s['spar_id'])] = p['id']
    for e in sem['ej_personer']: modell[(e['tagning'], e['spar_id'])] = None
    # Modellens P-id -> facitets roll: röstning över spåren
    roller_f = {}
    for k, pid in modell.items():
        if pid and facit.get(k): roller_f.setdefault(pid, []).append(facit[k])
    pmap = {pid: max(set(r), key=r.count) for pid, r in roller_f.items()}
    ok = 0; rader = []
    for k in sorted(facit, key=lambda x: (int(x[0][1:]), x[1])):
        m = modell.get(k, 'saknas'); mr = pmap.get(m) if m not in (None, 'saknas') else m
        stam = (mr == facit[k]) if m != 'saknas' else False
        ok += stam
        rader.append(dict(spar=f'{k[0]}:{k[1]}', facit=facit[k], modell=('ej berättelseperson' if m is None else m), modellens_roll_via_rostning=('ej berättelseperson' if m is None else mr), stammer=bool(stam)))
        if not stam: avv.append(dict(post='vem är vem', spar=f'{k[0]}:{k[1]}', facit=facit[k], modell=m))
    ut['vem_ar_vem'] = dict(stammer=ok, av=len(facit), person_till_roll=pmap, rader=rader,
                            antal_personer_modell=len(sem['personer']), antal_roller_facit=len({r for r in facit.values() if r}),
                            roller_modell={p['id']: p['roll'] for p in sem['personer']}, roller_facit={a['id']: a['role'] for a in s3['actors']},
                            bifigur_S4_markerad_som_ej_berattelseperson=any(e['tagning'] == 'S4' and e['spar_id'] == '4' for e in sem['ej_personer']))

    # --- 2. repliker: parning i ordning (7 mot 7), talare, text (WER), tider
    rl = sorted(sem['repliker'], key=lambda r: (r['start_s'], r['slut_s'])); gt = s3['dialogue']
    gt_ot = ladda(SCEN / '3d/data/ordtider.json')['lines']
    n = min(len(rl), len(gt)); tal_ok = 0; fel_ord = tot_ord = 0; rt = []
    for r, g, o, mine in zip(rl, gt, gt_ot, ot['lines']):
        talare = pmap.get(r['talare'], r['talare']); tal_ok += talare == g['speaker']
        if talare != g['speaker']: avv.append(dict(post='talare', replik=r['id'], facit=g['speaker'], modell=r['talare'], modell_roll=talare))
        e, t = wer(g['text'], r['text']); fel_ord += e; tot_ord += t
        if e: avv.append(dict(post='text', replik=r['id'], facit=g['text'], modell=r['text'], ordfel=e))
        rt.append(dict(replik=r['id'], facit_text=g['text'], modell_text=r['text'], ordfel=e, ord=t, talare_facit=g['speaker'], talare_modell=talare,
                       facit_tid=[o['start'], o['end']], whisper_vår_tid=[mine['start'], mine['end']], gemini_tid=[r['start_s'], r['slut_s']]))
    ut['repliker'] = dict(antal_modell=len(rl), antal_facit=len(gt), talare_stammer=tal_ok, wer=round(fel_ord / tot_ord, 4), ordfel=fel_ord, ord_facit=tot_ord, rader=rt)
    def med_fel(par):
        d = [abs(a - b) for a, b in par]; return round(statistics.median(d), 3) if d else None, round(max(d), 3) if d else None
    s_v = [(x['whisper_vår_tid'][0], x['facit_tid'][0]) for x in rt if x['whisper_vår_tid'][0] is not None]
    e_v = [(x['whisper_vår_tid'][1], x['facit_tid'][1]) for x in rt if x['whisper_vår_tid'][1] is not None]
    s_g = [(x['gemini_tid'][0], x['facit_tid'][0]) for x in rt]; e_g = [(x['gemini_tid'][1], x['facit_tid'][1]) for x in rt]
    ut['tider'] = dict(whisper_start_median_max_s=med_fel(s_v), whisper_slut_median_max_s=med_fel(e_v), gemini_start_median_max_s=med_fel(s_g), gemini_slut_median_max_s=med_fel(e_g),
                       anm='Facit-ordtiderna kommer från samma Whisper-modell (kb-whisper-medium) men med de kända replikerna som ledtråd (initial_prompt); vår körning har ingen ledtråd.',
                       ord_med_tid_facit=sum(len(l['words']) for l in gt_ot), ord_med_tid_vår=sum(len(l['words']) for l in ot['lines']))
    # ordnivå: medianfel mot facitets ordtider
    od = []
    for g, mine in zip(gt_ot, ot['lines']):
        for a, b in zip(g['words'], mine['words']):
            if norm_ord(a['w']) == norm_ord(b['w']): od.append(abs(a['start'] - b['start']))
    ut['tider']['ordstart_median_s'] = round(statistics.median(od), 3) if od else None; ut['tider']['ord_jamforda'] = len(od)

    # --- 3. funktion per tagning
    ff = {x['id']: x['funktion'] for x in kalla['semantik']['scener']}; fm = {x['tagning']: x['funktion'] for x in sem['tagningar']}
    fr = []; fok = 0
    for sid in sorted(ff, key=lambda s: int(s[1:])):
        sm = fm.get('S' + sid[1:]); fa = ff[sid]; st = (sm == fa) or (fa is None and sm in ('ingen', 'osaker')); fok += st
        fr.append(dict(tagning='S' + sid[1:], facit=fa, modell=sm, beat_facit=next(s['beat'] for s in s3['shots'] if s['id'] == 'S' + sid[1:]), stammer=st))
        if not st: avv.append(dict(post='funktion', tagning='S' + sid[1:], facit=fa, modell=sm))
    ut['funktion'] = dict(stammer=fok, av=len(ff), rader=fr)

    # --- 4. plats, sittande, par, kamerastationer
    pl = {p['person']: p for p in sem['placeringar']}; pf = {'A': ('sitter', 'sate'), 'B': ('sitter', 'sate'), 'C': ('star', 'staplats')}
    prad = []; pok = 0
    for pid, rolle in pmap.items():
        m = pl.get(pid); want = pf[rolle]; got = (m['hallning'], m['ankartyp']) if m else None; st = got == want; pok += st
        prad.append(dict(person=pid, facit_roll=rolle, facit=want, modell=got, vid_del=m['vid_del'] if m else None, stammer=st))
        if not st: avv.append(dict(post='placering', person=pid, facit=want, modell=got))
    par = next((p for p in sem['par'] if {p['a'], p['b']} == {k for k, r in pmap.items() if r in ('A', 'B')}), None)
    stat_f = [set(s['ids']) for s in gm['d_grammatik']['stationer']]; stat_m = [set(k['tagningar']) for k in sem['kamerauppstallningar']]
    def par_av(grupper): return {frozenset((a, b)) for g in grupper for a in g for b in g if a < b}
    pf_, pm_ = par_av(stat_f), par_av(stat_m)
    ut['plats'] = dict(facit=dict(layout=hand['layout']['val'], rumsmall=hand['rumsmall'], status=hand['layout']['status']),
                       modell=dict(typ=sem['plats']['typ'], rumsmall=sem['plats']['rumsmall_forslag']),
                       rumsmall_stammer=sem['plats']['rumsmall_forslag'] == hand['rumsmall'],
                       placeringar_stammer=pok, placeringar_av=len(pmap), placeringar=prad,
                       par_A_B=dict(vander_mot_varandra=par['vander_mot_varandra'] if par else None, over=par['over'] if par else None,
                                    facit='två separata bord, vända mot varandra över rummet (hand.json layout tva_bord)'),
                       kamerastationer=dict(facit_mätt=[sorted(s) for s in stat_f], modell=[sorted(s) for s in stat_m],
                                            samma_station_par_facit=sorted(map(sorted, pf_)), samma_station_par_modell=sorted(map(sorted, pm_)),
                                            par_som_modellen_lagger_till=sorted(map(sorted, pm_ - pf_)), par_som_modellen_missar=sorted(map(sorted, pf_ - pm_))))
    ut['avvikelser'] = avv
    skriv(UT / 'notan/utvardering.json', ut)
    V = ut['vem_ar_vem']; R = ut['repliker']; T = ut['tider']; F = ut['funktion']; P = ut['plats']
    print(f'vem är vem: {V["stammer"]}/{V["av"]} spår; personer modell {V["antal_personer_modell"]}, roller facit {V["antal_roller_facit"]}; bifigur S4:4 markerad: {V["bifigur_S4_markerad_som_ej_berattelseperson"]}; {V["person_till_roll"]}')
    print(f'repliker: {R["antal_modell"]} modell / {R["antal_facit"]} facit; talare {R["talare_stammer"]}/{n}; WER {R["wer"]:.1%} ({R["ordfel"]}/{R["ord_facit"]} ord)')
    print(f'tider: whisper start median/max {T["whisper_start_median_max_s"]}, slut {T["whisper_slut_median_max_s"]}; gemini start {T["gemini_start_median_max_s"]}, slut {T["gemini_slut_median_max_s"]}; ordstart median {T["ordstart_median_s"]} ({T["ord_jamforda"]} ord)')
    print(f'funktion: {F["stammer"]}/{F["av"]}; plats rumsmall stämmer {P["rumsmall_stammer"]}; placeringar {P["placeringar_stammer"]}/{P["placeringar_av"]}; par A-B {P["par_A_B"]}')
    print('kamerastationer', P['kamerastationer'])
    print('AVVIKELSER'); [print(' ', a) for a in avv]


if __name__ == '__main__':
    main()
