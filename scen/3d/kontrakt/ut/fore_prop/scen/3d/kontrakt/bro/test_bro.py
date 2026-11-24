"""Tester för bron. Kör från projektroten:
  scen/.venv/Scripts/python.exe -B -m unittest scen/3d/kontrakt/bro/test_bro.py
eller
  scen/.venv/Scripts/python.exe -B scen/3d/kontrakt/bro/test_bro.py

Kort, scenplaner och kundlinjer i testerna är konstruerade testunderlag (märkta TEST). De är inte
harnessens utdata och ska aldrig läsas som analys av notan-klippet. Kalla är den riktiga notan-kallan, läst oförändrad.
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HIT = Path(__file__).resolve().parent
KONTRAKT = HIT.parent
sys.path.insert(0, str(HIT))
sys.path.insert(0, str(KONTRAKT))

import kort_till_kalla as K   # noqa: E402
import scenplan_till_regi as S   # noqa: E402
from gemensamt import kontrollmodul   # noqa: E402

NOTAN = json.loads((KONTRAKT / 'exempel/notan/kalla.json').read_text(encoding='utf-8'))
SCHEMA_K = json.loads((KONTRAKT / 'kalla.schema.json').read_text(encoding='utf-8'))
SCHEMA_R = json.loads((KONTRAKT / 'regi.schema.json').read_text(encoding='utf-8'))
LINJE = dict(konto='testkund', produkter='Kebab, shawarma och bowls.', lokal=['disk_kassa', 'matsal'], max_personer=1,
             frontfigurer=[dict(etikett='Huvudtjejen', roll='anstalld', funktion='fokus', styrka='TEST'),
                           dict(etikett='Kepstjejen', roll='anstalld', funktion='roll', styrka='TEST')])


def beat(i, atgard, funktion='uppbyggnad', bar='karna', vad='TEST', skal='TEST-skäl'):
    return dict(nr=i, funktion=funktion, bar=bar, vad=vad, atgard=atgard, skal=skal, omrendera=atgard != 'behall')


def patch_1till1(plan_beats, scener=None, konf='medel'):
    """Patch där beat i ligger på scen i (för att styra tester av åtgärdsmappningen)."""
    ids = scener or [s['id'] for s in NOTAN['semantik']['scener']]
    return dict(justering=[dict(beat_nr=b['nr'], scener=[ids[b['nr'] - 1]], metod='ordning_1till1', konfidens=konf, belagg='TEST')
                           for b in plan_beats])


def forslag_for(plan_beats, linje=LINJE, patch=None, platsbank=None, rumsmall=None, kalla=NOTAN):
    plan = dict(beats=plan_beats)
    return S.bygg_forslag(plan, kalla, patch or patch_1till1(plan_beats), linje, plan_fil='TEST/plan.json', platsbank=platsbank, rumsmall=rumsmall)


def validera_regi(regi, kalla=NOTAN):
    mod = kontrollmodul()
    fel = mod.validera(regi, SCHEMA_R, 'regi', SCHEMA_R)
    if not fel:
        mod.referenser(kalla, regi)
        fel = list(mod.fel_lista)
    return fel


class Atgarder(unittest.TestCase):
    def op(self, atgard, **kw):
        bb = [beat(1, atgard, **kw)]
        f = forslag_for(bb)
        return f, S.till_regi(f)

    def test_behall_ger_ingenting(self):
        f, r = self.op('behall')
        self.assertEqual(f['edits'], [])
        self.assertEqual(f['behalls_beats'], [1])
        self.assertEqual(validera_regi(r), [])

    def test_eget_tal_utan_text(self):
        f, r = self.op('eget_tal')
        e = f['edits'][0]
        self.assertEqual((e['op'], e['replik']), ('byt_replik', 'r1'))
        self.assertIsNone(e['text'])
        self.assertTrue(e['forslag']['behover_text'])
        self.assertEqual(e['ursprung']['harness']['atgard'], 'eget_tal')
        self.assertEqual(e['ursprung']['harness']['skal'], 'TEST-skäl')
        self.assertIsNone(e['ursprung']['godkand_av_cm'])
        # schemat kräver text: i regi.json blir det en flagga, inte en byt_replik med uppdiktad text
        self.assertEqual(r['edits'][0]['op'], 'flagga')
        self.assertEqual(r['edits'][0]['allvar'], 'fraga')
        self.assertEqual(r['edits'][0]['scen'], 's1')
        self.assertEqual(validera_regi(r), [])

    def test_eget_tal_med_text_i_planen(self):
        bb = [beat(4, 'eget_tal')]
        bb[0]['replik'] = ['TEST ny text A']   # s4 har r4 och r5: en text räcker inte
        f = forslag_for(bb, patch=dict(justering=[dict(beat_nr=4, scener=['s4'], metod='x', konfidens='medel', belagg='')]))
        self.assertEqual([e['replik'] for e in f['edits']], ['r4', 'r5'])
        self.assertTrue(all(e['text'] is None for e in f['edits']))
        bb[0]['replik'] = ['TEST ny text A', 'TEST ny text B']
        f = forslag_for(bb, patch=dict(justering=[dict(beat_nr=4, scener=['s4'], metod='x', konfidens='medel', belagg='')]))
        self.assertEqual([e['text'] for e in f['edits']], ['TEST ny text A', 'TEST ny text B'])
        r = S.till_regi(f)
        self.assertEqual([e['op'] for e in r['edits']], ['byt_replik', 'byt_replik'])
        self.assertEqual(validera_regi(r), [])

    def test_eget_tal_utan_repliker_i_scenen(self):
        k = copy.deepcopy(NOTAN)
        k['semantik']['repliker'] = []
        f = forslag_for([beat(1, 'eget_tal')], kalla=k)
        self.assertEqual(f['edits'][0]['op'], 'flagga')
        self.assertTrue(f['edits'][0]['forslag']['behover_text'])

    def test_frontfigur_blir_casta(self):
        f, r = self.op('frontfigur', skal='Kepstjejen tar rollen: TEST')
        e = f['edits'][0]
        self.assertEqual((e['op'], e['person']), ('casta', 'A'))   # s1 har bara A
        self.assertEqual(e['kundroll']['namn'], 'Kepstjejen')   # skälet pekar ut figuren
        self.assertTrue(e['kundroll']['id'].startswith('PLATSHALLARE:testkund:'))
        self.assertEqual(validera_regi(r), [])

    def test_frontfigur_standard_ar_fokus_och_person_valjs_inte_gissat(self):
        bb = [beat(1, 'frontfigur', skal='TEST')]
        f = forslag_for(bb, patch=dict(justering=[dict(beat_nr=1, scener=['s1', 's2'], metod='x', konfidens='lag', belagg='')]))
        e = f['edits'][0]
        self.assertEqual(e['kundroll']['namn'], 'Huvudtjejen')
        self.assertTrue(e['person'].startswith('PLATSHALLARE:'))   # A och B talar en replik var: ingen gissning
        self.assertEqual(sorted(e['forslag']['kandidater']), ['A', 'B'])
        self.assertEqual(e['forslag']['konfidens'], 'lag')
        self.assertTrue(e['kommentar'])

    def test_frontfigur_saknas_ger_risk_flagga(self):
        l2 = dict(LINJE, frontfigurer=[])
        f = forslag_for([beat(1, 'frontfigur')], linje=l2)
        self.assertEqual((f['edits'][0]['op'], f['edits'][0]['allvar']), ('flagga', 'risk'))

    def test_byt_produkt_blir_byt_prop(self):
        f, r = self.op('byt_produkt')
        e = f['edits'][0]
        self.assertEqual(e['op'], 'byt_prop')
        self.assertEqual(e['ny_typ'], 'Kebab')
        self.assertEqual(e['forslag']['alternativ'], ['Kebab', 'shawarma', 'bowls'])
        self.assertTrue(e['forslag']['mal_saknas'])   # inget notanprop har ägare i s1
        self.assertTrue(e['prop'].startswith('PLATSHALLARE:'))
        self.assertEqual(validera_regi(r), [])

    def test_byt_produkt_pa_prop_som_scenen_agar(self):
        k = copy.deepcopy(NOTAN)
        k['semantik']['props'][0]['agare'] = 'A'   # TEST: gör första propen till A:s
        f = forslag_for([beat(1, 'byt_produkt')], kalla=k)
        self.assertEqual([(e['prop'], e['forslag']['mal_saknas']) for e in f['edits']], [(k['semantik']['props'][0]['id'], False)])
        self.assertEqual(validera_regi(S.till_regi(f), k), [])

    def test_byt_lokal_utan_plats_ar_namngiven_platshallare(self):
        f, r = self.op('byt_lokal')
        e = f['edits'][0]
        self.assertEqual(e['op'], 'byt_miljo')
        self.assertEqual((e['scen'], e['rum']['kalla'], e['rum']['tillgang_id']), ('s1', 'ord', None))
        self.assertEqual(e['rum']['ord'], ['disk_kassa', 'matsal'])
        self.assertTrue(e['forslag']['plats_saknas'])
        self.assertEqual(e['forslag']['mallkandidater'], ['bar_disk', 'restaurang_tva'])   # tips ur lokaldelarna, inget val
        self.assertEqual(validera_regi(r), [])

    def test_byt_lokal_med_plats_i_banken(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'testkund.json').write_text(json.dumps(dict(id='testkund')), encoding='utf-8')
            f = forslag_for([beat(1, 'byt_lokal')], platsbank=t)
        e = f['edits'][0]
        self.assertEqual((e['rum']['kalla'], e['rum']['tillgang_id']), ('bank', 'testkund'))
        self.assertFalse(e['forslag']['plats_saknas'])

    def test_byt_lokal_med_mall_i_rumsmall(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'testkund_matsal.json').write_text(json.dumps(dict(id='testkund_matsal')), encoding='utf-8')
            f = forslag_for([beat(1, 'byt_lokal')], rumsmall=t)
        e = f['edits'][0]
        self.assertEqual((e['rum']['kalla'], e['rum']['rumsmall_id'], e['rum']['tillgang_id']), ('bank', 'testkund_matsal', None))
        self.assertEqual(validera_regi(S.till_regi(f)), [])

    def test_forenkla(self):
        f, r = self.op('forenkla', funktion='vandning')
        e = f['edits'][0]
        self.assertEqual((e['op'], e['scen'], e['regler']), ('forenkla', 's1', ['inga_effekter']))
        f = forslag_for([beat(1, 'forenkla')], linje=dict(LINJE, max_personer=0))
        self.assertEqual(f['edits'][0]['regler'], ['inga_effekter', 'farre_personer'])
        self.assertEqual(validera_regi(r), [])

    def test_fritt_ar_valfritt_och_inte_standard(self):
        f, r = self.op('fritt', bar='fri')
        e = f['edits'][0]
        self.assertEqual((e['op'], e['lage']), ('fri_scen', 'stryk'))
        self.assertTrue(e['forslag']['valfri'])
        self.assertFalse(e['forslag']['tillampas_som_standard'])
        self.assertEqual(r['edits'][0]['op'], 'flagga')   # i regi.json ingen strykning
        self.assertNotIn('fri_scen', [x['op'] for x in r['edits']])
        self.assertEqual(validera_regi(r), [])

    def test_fritt_varnar_om_scenen_delas(self):
        bb = [beat(1, 'fritt', bar='fri'), beat(2, 'behall')]
        p = dict(justering=[dict(beat_nr=1, scener=['s1'], metod='x', konfidens='lag', belagg=''),
                            dict(beat_nr=2, scener=['s1'], metod='x', konfidens='lag', belagg='')])
        f = forslag_for(bb, patch=p)
        self.assertIn('delas med beat 2', f['edits'][0]['forslag']['varning'])

    def test_risk_ar_varning_utan_andring(self):
        f, r = self.op('risk')
        self.assertEqual(f['edits'][0]['op'], 'flagga')
        self.assertEqual(f['edits'][0]['allvar'], 'risk')
        self.assertEqual(f['varningar'][0]['text'], 'TEST-skäl')
        self.assertEqual(validera_regi(r), [])

    def test_alla_atgarder_tacks_och_ids_ar_unika(self):
        bb = [beat(i + 1, a) for i, a in enumerate(['behall', 'fritt', 'byt_produkt', 'byt_lokal', 'frontfigur', 'risk', 'eget_tal'])]
        f = forslag_for(bb)
        r = S.till_regi(f)
        ids = [e['id'] for e in f['edits']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(validera_regi(r), [])
        self.assertTrue(all(e['ursprung']['typ'] == 'harness-forslag' and e['ursprung']['godkand_av_cm'] is None for e in r['edits']))
        self.assertEqual(set(f['sammanfattning']['per_atgard']), {'behall', 'fritt', 'byt_produkt', 'byt_lokal', 'frontfigur', 'risk', 'eget_tal'})

    def test_okand_atgard_avvisas(self):
        with self.assertRaises(ValueError):
            forslag_for([beat(1, 'hittepa')])


def kort(n, extra=None):
    funk = ['krok', 'uppbyggnad', 'vandning', 'punchline', 'visning', 'tilltal', 'avslut']
    return dict(id='TEST-kort', konto='TEST', modell='TEST', karna='TEST kärna',
                grundvarde=dict(krok='stark', vandning=True),
                beats=[dict(vad=f'TEST beat {i + 1}', funktion=funk[i % 7], bar='karna' if i % 2 == 0 else 'stod',
                            bunden='ingen') for i in range(n)])


class Justering(unittest.TestCase):
    def kor(self, k):
        return K.bygg_patch(k, NOTAN)

    def test_lika_manga_beats_som_scener(self):
        p = self.kor(kort(7))
        self.assertEqual([j['scener'] for j in p['justering']], [[f's{i}'] for i in range(1, 8)])
        self.assertEqual({j['metod'] for j in p['justering']}, {'ordning_1till1'})
        self.assertEqual({j['konfidens'] for j in p['justering']}, {'medel'})

    def test_farre_beats_an_scener(self):
        p = self.kor(kort(3))
        sc = [j['scener'] for j in p['justering']]
        self.assertEqual(sum(sc, []), [f's{i}' for i in range(1, 8)])   # alla scener, i ordning, utan dubbletter
        self.assertTrue(all(len(x) >= 2 for x in sc))
        self.assertEqual({j['konfidens'] for j in p['justering']}, {'lag'})
        # ett beat på flera scener kan inte bindas till en: scen = null
        self.assertTrue(all(b['scen'] is None for b in p['semantik']['beats']))

    def test_fler_beats_an_scener(self):
        k = kort(6)
        s6 = copy.deepcopy(NOTAN)
        s6['semantik']['scener'] = s6['semantik']['scener'][:3]
        p = K.bygg_patch(k, s6)
        sc = [j['scener'] for j in p['justering']]
        self.assertTrue(all(len(x) == 1 for x in sc))
        self.assertEqual([x[0] for x in sc], ['s1', 's1', 's2', 's2', 's3', 's3'])
        self.assertEqual({j['konfidens'] for j in p['justering']}, {'lag'})
        # s1 har funktion krok och uppbyggnad: oenig, så scenens funktion lämnas null
        s1 = p['semantik']['scener'][0]
        self.assertIsNone(s1['funktion'])
        self.assertIsNone(s1['syfte'])

    def test_en_scen_ar_hog_konfidens(self):
        s1 = copy.deepcopy(NOTAN)
        s1['semantik']['scener'] = s1['semantik']['scener'][:1]
        p = K.bygg_patch(kort(4), s1)
        self.assertEqual({(j['metod'], j['konfidens']) for j in p['justering']}, {('enda_scen', 'hog')})

    def test_textankare(self):
        k = kort(7)
        k['beats'][1]['vad'] = "TEST: B säger 'Varför skulle jag ta notan?'"
        k['beats'][3]['vad'] = "TEST: A frågar 'Eller liksom betala halva åtminstone?'"
        p = self.kor(k)
        j = {x['beat_nr']: x for x in p['justering']}
        self.assertEqual((j[2]['scener'], j[2]['metod']), (['s2'], 'text'))
        self.assertEqual((j[4]['scener'], j[4]['metod']), (['s4'], 'text'))
        self.assertIn(j[2]['konfidens'], ('hog', 'medel'))
        self.assertEqual(j[1]['scener'], ['s1'])   # före första ankaret
        self.assertEqual(j[3]['scener'], ['s3'])   # mellan ankarna
        self.assertEqual(j[5]['metod'], 'ordning')
        self.assertTrue(all(x['scener'] for x in p['justering']))

    def test_textankare_som_bryter_ordningen_forkastas(self):
        k = kort(7)
        k['beats'][1]['vad'] = "TEST: 'Men jag känner inte ens dig'"        # r7 = s7
        k['beats'][2]['vad'] = "TEST: 'Varför skulle jag ta notan'"          # r2 = s2, före s7: förkastas
        p = self.kor(k)
        j = {x['beat_nr']: x for x in p['justering']}
        self.assertEqual(j[2]['scener'], ['s7'])
        self.assertNotEqual(j[3]['metod'], 'text')

    def test_tidsbaserad_bara_om_kortet_har_tider(self):
        k = kort(2)
        sc = NOTAN['semantik']['scener']
        k['beats'][0].update(start_s=sc[0]['start_s'], slut_s=sc[0]['slut_s'])
        k['beats'][1].update(start_s=sc[1]['start_s'], slut_s=sc[1]['slut_s'])
        p = self.kor(k)
        self.assertEqual({j['metod'] for j in p['justering']}, {'tid'})
        self.assertEqual(p['justering'][0]['scener'], ['s1'])
        self.assertEqual(p['justering'][1]['scener'], ['s2'])   # halvöppna intervall: s1 slutar där s2 börjar
        # beatens tider kopieras aldrig till patchen
        self.assertNotIn('start_s', json.dumps(p['semantik']['beats']))

    def test_konflikt_med_handkalibrerad_kalla_och_tillampning(self):
        p = self.kor(kort(7))   # s1 är krok i kalla, kortet säger krok: ingen konflikt
        self.assertNotIn('konflikt_med_kalla', p['semantik']['scener'][0])
        k = kort(7)
        k['beats'][0]['funktion'] = 'tilltal'
        p = self.kor(k)
        self.assertEqual(p['semantik']['scener'][0]['konflikt_med_kalla']['funktion'], dict(kalla='krok', kort='tilltal'))
        ny = K.tillampa_patch(NOTAN, p)
        self.assertEqual(ny['semantik']['scener'][0]['funktion'], 'krok')   # kalla vinner: patchen fyller bara null
        # s5 har funktion null i kalla: patchen fyller den (kort: beat 5 = visning)
        self.assertIsNone(NOTAN['semantik']['scener'][4]['funktion'])
        self.assertEqual(ny['semantik']['scener'][4]['funktion'], 'visning')
        mod = kontrollmodul()
        self.assertEqual(mod.validera(ny, SCHEMA_K, 'kalla', SCHEMA_K), [])
        self.assertEqual(NOTAN['semantik']['beats'], [])   # indata orörd

    def test_lag_konfidens_tillampas_inte_som_standard(self):
        p = self.kor(kort(3))
        ny = K.tillampa_patch(NOTAN, p)
        self.assertIsNone(ny['semantik']['scener'][4]['funktion'])
        self.assertTrue(all(b['scen'] is None for b in ny['semantik']['beats']))
        alla = K.tillampa_patch(NOTAN, p, min_konfidens='lag')
        self.assertIsNotNone(alla['semantik']['scener'][4]['funktion'])
        mod = kontrollmodul()
        self.assertEqual(mod.validera(alla, SCHEMA_K, 'kalla', SCHEMA_K), [])

    def test_intention(self):
        p = self.kor(kort(7))
        i = p['semantik']['intention']
        self.assertEqual(i['karna'], 'TEST kärna')
        self.assertEqual((i['krok']['finns'], i['krok']['scen']), (True, 's1'))
        self.assertEqual(i['vandning']['finns'], True)
        self.assertEqual(i['payoff']['scen'], 's4')
        self.assertEqual(i['payoff']['vad'], 'TEST beat 4')
        self.assertIsNone(p['semantik']['serie'])
        k = kort(2)   # ingen punchline-beat: payoff okänt, inte "finns inte"
        self.assertEqual(self.kor(k)['semantik']['intention']['payoff'], dict(finns=None, vad=None, scen=None))

    def test_bunden_ingen_blir_null(self):
        p = self.kor(kort(2))
        self.assertTrue(all(b['bunden'] is None for b in p['semantik']['beats']))
        k = kort(2)
        k['beats'][0]['bunden'] = 'lokal'
        self.assertEqual(self.kor(k)['semantik']['beats'][0]['bunden'], 'lokal')


class Inget_uppdiktat(unittest.TestCase):
    def alla_strangar(self, o, ut=None):
        ut = set() if ut is None else ut
        if isinstance(o, dict):
            for v in o.values():
                self.alla_strangar(v, ut)
        elif isinstance(o, list):
            for v in o:
                self.alla_strangar(v, ut)
        elif isinstance(o, str):
            ut.add(o)
        return ut

    def test_patch_har_inga_tider_och_bara_kanda_id(self):
        k = kort(7)
        p = K.bygg_patch(k, NOTAN)
        txt = json.dumps(p)
        for nyckel in ('start_s', 'slut_s', 'tid_s', 'tider'):
            self.assertNotIn(f'"{nyckel}"', txt)
        scen_ids = {s['id'] for s in NOTAN['semantik']['scener']}
        for j in p['justering']:
            self.assertLessEqual(set(j['scener']), scen_ids)
        # fria texter i patchen är kortets egna beats-texter, kärnan eller bunden text från bron
        indata = {b['vad'] for b in k['beats']} | {k['karna']}
        for b in p['semantik']['beats']:
            self.assertIn(b['vad'], indata)
        for s in p['semantik']['scener']:
            self.assertTrue(s['syfte'] is None or s['syfte'] in indata)

    def test_forslag_har_inga_nya_texter_eller_tider(self):
        bb = [beat(1, 'eget_tal'), beat(2, 'frontfigur'), beat(3, 'byt_produkt'), beat(4, 'byt_lokal'), beat(5, 'forenkla'),
              beat(6, 'fritt'), beat(7, 'risk')]
        f = forslag_for(bb)
        for e in f['edits']:
            if e['op'] == 'byt_replik':
                self.assertIsNone(e['text'])
        r = S.till_regi(f)
        for e in r['edits']:
            self.assertNotIn('start_s', e)
            self.assertNotIn('slut_s', e)
            self.assertNotIn(e['op'], ('lagg_till_replik', 'lagg_till_scen', 'trimma_scen'))
        # numeriska värden i regin kommer från kallan (fps, mått) eller är schemats standard
        self.assertEqual((r['utdata']['fps_taljare'], r['utdata']['bredd'], r['utdata']['hojd']), (30, 576, 1024))
        # sträng ur kundlinjen, planen eller kallan
        ok = self.alla_strangar([LINJE, bb, NOTAN['semantik']['repliker'], NOTAN['semantik']['scener'], NOTAN['semantik']['personer'],
                                 NOTAN['klipp']])
        for e in f['edits']:
            if e['op'] == 'byt_prop':
                self.assertIn(e['ny_typ'], ['Kebab', 'shawarma', 'bowls'])
            if e['op'] == 'casta':
                self.assertIn(e['kundroll']['namn'], {x['etikett'] for x in LINJE['frontfigurer']})
            if e['op'] == 'byt_miljo':
                self.assertLessEqual(set(e['rum']['ord']), set(LINJE['lokal']))
            if e['op'] in ('byt_replik',):
                self.assertIn(e['sprak'], ok)

    def test_deterministisk(self):
        k = kort(5)
        a = json.dumps(K.bygg_patch(k, NOTAN), ensure_ascii=False, sort_keys=False)
        b = json.dumps(K.bygg_patch(copy.deepcopy(k), copy.deepcopy(NOTAN)), ensure_ascii=False, sort_keys=False)
        self.assertEqual(a, b)
        bb = [beat(i + 1, a_) for i, a_ in enumerate(['eget_tal', 'frontfigur', 'byt_produkt', 'byt_lokal', 'forenkla', 'fritt', 'risk'])]
        x = json.dumps(forslag_for(bb), ensure_ascii=False)
        y = json.dumps(forslag_for(copy.deepcopy(bb)), ensure_ascii=False)
        self.assertEqual(x, y)
        self.assertEqual(json.dumps(S.till_regi(forslag_for(bb))), json.dumps(S.till_regi(forslag_for(bb))))

    def test_indata_andras_inte(self):
        k = copy.deepcopy(NOTAN)
        bb = [beat(1, 'eget_tal')]
        antingen = copy.deepcopy(bb)
        forslag_for(bb, kalla=k)
        K.bygg_patch(kort(3), k)
        self.assertEqual(k, NOTAN)
        self.assertEqual(bb, antingen)


class Kompilering(unittest.TestCase):
    """Kompilatorn tillämpar inte harnessförslag som CM inte godkänt. Kräver notans mätfiler (ingest/ut)."""

    def test_ogodkanda_forslag_tillampas_inte(self):
        import kompilera
        bb = [beat(1, 'frontfigur'), beat(2, 'forenkla'), beat(3, 'risk'), beat(4, 'byt_lokal')]
        f = forslag_for(bb)
        r = S.till_regi(f)
        r['kalla']['revision'] = NOTAN['revision']
        with tempfile.TemporaryDirectory() as t:
            rf = Path(t) / 'regi.json'
            rf.write_text(json.dumps(r), encoding='utf-8')
            try:
                plan = kompilera.kompilera(KONTRAKT / 'exempel/notan/kalla.json', rf)
            except (ValueError, OSError) as e:
                self.skipTest(f'notans mätfiler saknas eller kontraktet ändrades: {e}')
        self.assertEqual(plan['tillampat'], [])
        self.assertEqual(len(plan['ej_tillampat']), len(r['edits']))
        self.assertTrue(all('inte godkänt' in e['orsak'] for e in plan['ej_tillampat']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
