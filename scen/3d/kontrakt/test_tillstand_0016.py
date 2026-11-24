"""0016: föremål ur deklarationen i källan, ta bort/byt i alla former, scengrupper, håll sista rutan, och att en ogiltig edit bara kastar sig själv.

    scen/.venv/Scripts/python.exe -m unittest test_tillstand_0016      (från scen/3d/kontrakt)
De syntetiska proven är snabba. Integrationsprovet kompilerar b-tilltal (n06-hand, kalla_0016.json) med snabbvägen, cirka 90 s kall.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from gemensamt import HIT, ladda, skriv, kontrollera
from kalla_foremal import props_ur_plan, grupper
from kompilera import foremal_i_plan, halla_i_plan, kompilera

BT = HIT / 'ut/b-tilltal-ravara_n06-hand'


def plan_syntetisk():
    return dict(kallrutor=list(range(30)), scener=[dict(id='s1', ut=[0, 10]), dict(id='s2', ut=[10, 20]), dict(id='s3', ut=[20, 30])],
                plats=[dict(deklarerat=dict(foremal=dict(vag=dict(pa='disk'), kottbit=dict(pa='papper'))))],
                objekt=[dict(id='disk', synlig_ut=[0, 30], matt_m=[1, 1, 1]), dict(id='disk:pa:vag', synlig_ut=[10, 20], matt_m=[.3, .4, .5], farg='#fff'),
                        dict(id='disk:pa:vag', synlig_ut=[20, 30], matt_m=[.3, .4, .5], farg='#fff'), dict(id='disk:pa:kottbit', synlig_ut=[20, 30], matt_m=[.25, .2, .15])],
                handforemal=[dict(id='A:hand:kottbit', foremal='kottbit', scen='s1', person='A', sida='h', ben='r_wrist', synlig_ut=[0, 10], matt_m=[.25, .25, .19], farg='#b5654a'),
                             dict(id='B:hand:kottbit', foremal='kottbit', scen='s2', person='B', sida='v', ben='l_wrist', synlig_ut=[10, 20], matt_m=[.2, .2, .1], farg='#b5654a')],
                skarmtext=[dict(id='t1', scen='s3', ut=[22, 30]), dict(id='t2', scen='s3', ut=[20, 25])],
                tillampat=[], ej_tillampat=[])


class ForemalTillKallan(unittest.TestCase):
    def test_deklarerade_foremal_blir_namngivna_props(self):
        p = {x['id']: x for x in props_ur_plan(plan_syntetisk())}
        self.assertEqual(set(p), {'vag', 'kottbit'})
        self.assertEqual(p['vag']['deklaration']['former'], ['disk:pa:vag']); self.assertEqual(p['vag']['deklaration']['scener'], ['s2', 's3'])
        self.assertEqual(p['vag']['stod'], 'disk'); self.assertIsNone(p['vag']['faste'])
        k = p['kottbit']['deklaration']
        self.assertEqual(k['former'], ['A:hand:kottbit', 'B:hand:kottbit', 'disk:pa:kottbit']); self.assertEqual(k['scener'], ['s1', 's2', 's3'])
        self.assertEqual(p['kottbit']['faste'], dict(person='A', led='r_wrist', hand='hoger'))
        self.assertIsNone(p['kottbit']['agare'], 'köttbiten byter händer; ingen ägare')
        self.assertEqual(p['kottbit']['stod'], 'disk', 'stödet tas ur formens id när deklarationens pa inte är en form')

    def test_ta_bort_tar_alla_former(self):
        plan = plan_syntetisk(); plan['tillampat'] = [dict(id='e', op='ta_bort_prop', andring={})]
        foremal_i_plan(plan, [dict(id='e', op='ta_bort_prop', prop='kottbit', scen='alla')], {})
        self.assertFalse([o for o in plan['objekt'] if 'kottbit' in o['id']]); self.assertFalse(plan['handforemal'])
        self.assertEqual(len(plan['tillampat'][0]['andring']['traffade']), 3)
        self.assertEqual(len(plan['objekt']), 3, 'vågen och disken står kvar')

    def test_ta_bort_i_en_scen(self):
        plan = plan_syntetisk(); plan['tillampat'] = [dict(id='e', op='ta_bort_prop', andring={})]
        foremal_i_plan(plan, [dict(id='e', op='ta_bort_prop', prop='vag', scen='s3')], {})
        self.assertEqual([o['synlig_ut'] for o in plan['objekt'] if o['id'] == 'disk:pa:vag'], [[10, 20]])

    def test_byt_till_okand_typ_ar_platshallare_med_samma_plats(self):
        plan = plan_syntetisk(); fore = copy.deepcopy(plan); plan['tillampat'] = [dict(id='e', op='byt_prop', andring={})]
        foremal_i_plan(plan, [dict(id='e', op='byt_prop', prop='kottbit', ny_typ='ost', scen='alla')], {})
        for h, h0 in zip(plan['handforemal'], fore['handforemal']):
            self.assertEqual((h['etikett'], h['form_status']), ('ost', 'platshallare'))
            self.assertEqual((h['ben'], h['offset_m'] if 'offset_m' in h else None, h['matt_m']), (h0['ben'], h0.get('offset_m'), h0['matt_m']))
        o = next(o for o in plan['objekt'] if o['id'] == 'disk:pa:kottbit')
        self.assertEqual((o['namn'], o['form_status'], o['synlig_ut']), ('platshallare:ost:kottbit', 'platshallare', [20, 30]))

    def test_inget_traffat_avvisas_med_skal(self):
        plan = plan_syntetisk(); plan['tillampat'] = [dict(id='e', op='ta_bort_prop', andring={})]
        foremal_i_plan(plan, [dict(id='e', op='ta_bort_prop', prop='vag', scen='s1')], {})
        self.assertFalse(plan['tillampat']); self.assertIn('ingen form', plan['ej_tillampat'][0]['orsak'])


class Scengrupper(unittest.TestCase):
    def test_intilliggande_med_samma_roll(self):
        sem = dict(scener=[dict(id=f's{i}', personer=p) for i, p in enumerate([['A'], ['A'], ['B'], ['C'], ['C'], ['A', 'B'], ['A'], ['A']], 1)])
        self.assertEqual([(g['id'], g['scener']) for g in grupper(sem)], [('grupp_A', ['s1', 's2']), ('grupp_C', ['s4', 's5']), ('grupp_A_2', ['s7', 's8'])])


class HallSistaRutan(unittest.TestCase):
    def test_text_foremal_och_kropp_star_kvar(self):
        plan = plan_syntetisk()
        plan['scener'][2].update(lokal_start=0, varld='v.npz', personer=[dict(id='C', rorelse='s.npz')])
        d = copy.deepcopy(plan['scener'][2])
        halla_i_plan(plan, [dict(scen='s3', ut=[30, 36], kallruta=29, lokal=9, delplan=d)])
        self.assertEqual(plan['hallna_rutor'][0]['ut'], [30, 36])
        self.assertEqual(next(t for t in plan['skarmtext'] if t['id'] == 't1')['ut'], [22, 36], 'text som syns vid slutet står kvar')
        self.assertEqual(next(t for t in plan['skarmtext'] if t['id'] == 't2')['ut'], [20, 25], 'text som slutat före slutet förlängs inte')
        self.assertEqual([o['synlig_ut'] for o in plan['objekt'] if o['id'] == 'disk:pa:vag'], [[10, 20], [20, 36]])
        h = plan['scener'][3]
        self.assertEqual((h['id'], h['ut'], h['lokal_start']), ('s3#hall', [30, 36], 4))
        self.assertEqual(h['personer'][0]['rutor'], [9] * 6); self.assertTrue(h['personer'][0]['narvaro']['hall'])


class EnEditKastarSigSjalv(unittest.TestCase):
    def test_referensfel_avvisar_bara_editen(self):
        K = ladda(BT / 'kalla_0016.json')
        R = dict(schema_version='regi/1', kalla=dict(klipp_id=K['klipp']['id'], sha256=K['klipp']['sha256'], revision=K['revision']),
                 utdata=dict(fps_taljare=30, fps_namnare=1, bredd=576, hojd=1024, stil_ref=None, ljudpolicy='original', render_backend='blender_mhr'),
                 ramar=dict(bevara_beats=[], bevara_klippoffset_s=None, tillat_retiming=False, max_talfaktor=1.15),
                 edits=[dict(id='dalig', ursprung=dict(typ='cm'), op='trimma_scen', scen='s11', start_s=14.1333, slut_s=16.6667, lage='klipp_slut'),
                        dict(id='okand', ursprung=dict(typ='cm'), op='ta_bort_scen', scen='s99'),
                        dict(id='bra', ursprung=dict(typ='cm'), op='ta_bort_scen', scen='grupp_A')])
        av = []; kontrollera(K, R, BT, BT / 'kalla_0016.json', avvisade=av)
        self.assertEqual([e['id'] for e in R['edits']], ['bra'])
        self.assertEqual([a['id'] for a in av], ['dalig', 'okand']); self.assertIn('utanför scenens källintervall', av[0]['orsak'])
        with self.assertRaises(ValueError):   # utan avvisade gäller den gamla regeln: hela regin avvisas
            kontrollera(K, dict(R, edits=[dict(id='okand', ursprung=dict(typ='cm'), op='ta_bort_scen', scen='s99')]), BT, BT / 'kalla_0016.json')


class Integration(unittest.TestCase):
    def test_b_tilltal_grupp_foremal_och_hallning(self):
        K = ladda(BT / 'kalla_0016.json')
        R = dict(schema_version='regi/1', kalla=dict(klipp_id=K['klipp']['id'], sha256=K['klipp']['sha256'], revision=K['revision']),
                 utdata=dict(fps_taljare=30, fps_namnare=1, bredd=576, hojd=1024, stil_ref=None, ljudpolicy='original', render_backend='blender_mhr'),
                 ramar=dict(bevara_beats=[], bevara_klippoffset_s=None, tillat_retiming=False, max_talfaktor=1.15),
                 edits=[dict(id='g', ursprung=dict(typ='cm'), op='flytta_scen', scen='grupp_B', efter=None),
                        dict(id='v', ursprung=dict(typ='cm'), op='ta_bort_prop', scen='alla', prop='vag'),
                        dict(id='k', ursprung=dict(typ='cm'), op='byt_prop', scen='alla', prop='kottbit', ny_typ='ost'),
                        dict(id='h', ursprung=dict(typ='cm'), op='trimma_scen', scen='s11', slut_s=16.6667, lage='hall_sista')])
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'regi.json'; skriv(f, R); plan = kompilera(BT / 'kalla_0016.json', f, snabb=True)
        self.assertEqual([x['id'] for x in plan['tillampat']], ['g', 'v', 'k', 'h'], plan['ej_tillampat'])
        self.assertEqual([s['id'] for s in plan['scener']][:4], ['s3', 's4', 's1', 's2'])
        self.assertEqual(plan['scener'][-1]['id'], 's11#hall'); self.assertEqual(len(plan['kallrutor']), 500)
        kr = plan['hallna_rutor'][0]['kallruta']; self.assertEqual(plan['kallrutor'][-30:], [kr] * 30); self.assertLess(kr, 470)   # sista lästa rutan (S11:s tre sista är olästa); self.assertEqual(len(plan['renderkamera']['nycklar']), 500)
        self.assertFalse([o for o in plan['objekt'] if ':pa:vag' in o['id']])
        self.assertFalse([o for o in plan['objekt'] if o.get('synlig_ut') and o['synlig_ut'][0] >= 470], 'inga former bara i hållningen')
        self.assertTrue(plan['handforemal']); self.assertTrue(all(h['etikett'] == 'ost' for h in plan['handforemal']))
        self.assertIn('r3', plan['tillampat'][0]['andring']['repliker_over_gransen'])


if __name__ == '__main__':
    unittest.main()
