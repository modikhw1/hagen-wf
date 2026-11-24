"""Steg 11: skymning per källruta, källkontroll i långlivad process, tal utan syntes i snabbvägen, unika text-id,
enskilt avvisade schemafel och uttryck för kortbyte/lokalbyte. Kör från projektroten:
  scen/.venv/Scripts/python.exe -m unittest test_steg11   (i mappen scen/3d/kontrakt)
"""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.dont_write_bytecode = True
from gemensamt import HIT, ladda, skriv, kontrollmodul
from kompilera import kompilera
import datacache
import skymning
import tal

KALLA_N = HIT/'exempel/notan/kalla_jamn.json'; REGI_N = HIT/'exempel/notan/regi.json'
KALLA_B = HIT/'exempel/bar/kalla.json'; REGI_B = HIT/'exempel/bar/regi.json'
_TMP = {}


def setUpModule():
    UT = HIT/'ut'; UT.mkdir(exist_ok=True)
    _TMP['d'] = Path(tempfile.mkdtemp(prefix='steg11_', dir=UT))
    _TMP['cache'] = patch.object(datacache, 'CACHE', _TMP['d']/'cache'); _TMP['cache'].start()
    _TMP['tal'] = patch.object(tal, 'CACHE', _TMP['d']/'tal'); _TMP['tal'].start()


def tearDownModule():
    _TMP['cache'].stop(); _TMP['tal'].stop(); shutil.rmtree(_TMP['d'], ignore_errors=True)


def cm(id, op, **kw): return dict(id=id, op=op, ursprung=dict(typ='cm'), **kw)


class Bas(unittest.TestCase):
    kalla = KALLA_N; regi = REGI_N

    def setUp(self):
        self.ut = Path(tempfile.mkdtemp(prefix='t_', dir=_TMP['d'])); self.addCleanup(shutil.rmtree, self.ut, ignore_errors=True)
        self.r = ladda(self.regi)

    def plan(self, edits, kalla=None, snabb=True):
        self.r['edits'] = edits; skriv(self.ut/'regi.json', self.r)
        return kompilera(kalla or self.kalla, self.ut/'regi.json', snabb=snabb)


class Skymning(Bas):
    def test_flera_lador_ger_exakt_samma_djup_som_en_i_taget(self):
        rng = np.random.default_rng(3)
        origin = rng.normal(size=3); rays = rng.normal(size=(500, 3)); rays /= np.linalg.norm(rays, axis=1)[:, None]
        objs = [dict(pos_m=list(rng.normal(size=3)*2), matt_m=list(rng.uniform(.1, 2, 3)), rotation_rad=[0, 0, float(rng.uniform(-3, 3))]) for _ in range(40)]
        objs.append(dict(pos_m=[0, 0, 0], matt_m=[1, 1, 1]))   # utan rotation_rad
        rader = skymning.boxdjup_flera(origin, rays, objs)
        for o, rad in zip(objs, rader): np.testing.assert_array_equal(skymning.boxdjup(origin, rays, o), rad)

    def test_konflikt_minns_per_lada_och_raknar_bara_nya(self):
        key = dict(matris=np.eye(4).tolist(), lins_mm=50.)
        uv = np.array([[288., 512.], [290., 514.], [100., 100.]]); depth = np.array([5., 5., 5.])
        a = dict(id='a', pos_m=[0, 0, -2], matt_m=[1, 1, 1], rotation_rad=[0, 0, 0]); b = dict(id='b', pos_m=[.2, 0, -3], matt_m=[1, 1, 1], rotation_rad=[0, 0, .3])
        ref = skymning.konflikt(uv, depth, key, 576, 1024, [a, b])
        skymning._TRAFF.clear(); ett = skymning.konflikt(uv, depth, key, 576, 1024, [a], ('prov', 'f'))
        with patch.object(skymning, 'boxdjup_flera', wraps=skymning.boxdjup_flera) as ber:
            tva = skymning.konflikt(uv, depth, key, 576, 1024, [a, b], ('prov', 'f'))
            self.assertEqual([len(c.args[2]) for c in ber.call_args_list], [1])   # bara den nya lådan b räknades
            skymning._TRAFF.clear()   # ny process: läs från disk
            ber.reset_mock(); tre = skymning.konflikt(uv, depth, key, 576, 1024, [b, a], ('prov', 'f'))
            ber.assert_not_called()
        for k in ('a', 'b'): np.testing.assert_array_equal(ref[k], tva[k]); np.testing.assert_array_equal(ref[k], tre[k])
        np.testing.assert_array_equal(ref['a'], ett['a'])
        self.assertTrue(ref['a'].any() or ref['b'].any(), 'provet ska ha minst en träff')

    def test_nytt_tidsurval_efter_forvarm_raknar_inga_lador_och_ger_samma_beslut(self):
        p0 = self.plan([])
        with patch.object(skymning, 'boxdjup_flera', wraps=skymning.boxdjup_flera) as ber:
            n = skymning.forvarm(p0); self.assertGreater(n, 300); self.assertGreater(ber.call_count, 0)
        trim = [cm('t1', 'trimma_scen', scen='s3', slut_s=5.45, lage='klipp_slut'), cm('t2', 'trimma_scen', scen='s2', start_s=2.6, lage='klipp_slut')]
        for edits in (trim, [cm('d1', 'ta_bort_scen', scen='s4')], [cm('f1', 'flytta_scen', scen='s5', efter='s6')]):
            with patch.object(skymning, 'boxdjup_flera', side_effect=AssertionError('lådor räknades om för redan färdiga rutor')):
                warm = self.plan(edits)
            # Samma plan med tomt minne: ingen cache alls, alla rutor räknas på nytt. Beslut och objekt ska vara identiska.
            with patch.object(datacache, 'CACHE', _TMP['d']/('kall_'+edits[0]['id'])):
                skymning._RUTOR.clear(); skymning._TRAFF.clear(); kall = self.plan(edits)
            self.assertEqual(warm['kvalitet']['skymning'], kall['kvalitet']['skymning'])
            self.assertEqual(warm['objekt'], kall['objekt'])
            self.assertEqual(json.dumps(warm['kvalitet']['skymning']['fore'], sort_keys=True), json.dumps(kall['kvalitet']['skymning']['fore'], sort_keys=True))
        self.assertTrue(p0['kvalitet']['skymning']['atgarder'], 'notan har ett skymningsbeslut som provet ska täcka')


def absoluta(o, mapp):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'sokvag': o[k] = str((mapp/v).resolve())
            else: absoluta(v, mapp)
    elif isinstance(o, list):
        for v in o: absoluta(v, mapp)


class Kallkontroll(Bas):
    kalla = KALLA_B; regi = REGI_B

    def kalla_kopia(self, andra=None):
        k = ladda(KALLA_B); absoluta(k, KALLA_B.parent)
        if andra: andra(k)
        skriv(self.ut/'kalla.json', k); return self.ut/'kalla.json'

    def test_hash_minns_per_filstampel_och_raknar_om_vid_andring(self):
        kontroll = kontrollmodul(); fil = _TMP['d']/'hashprov.bin'; fil.write_bytes(b'abc')
        h1 = kontroll.sha_fil(fil)
        with patch.object(kontroll, 'hashlib') as hl:
            self.assertEqual(kontroll.sha_fil(fil), h1); hl.sha256.assert_not_called()   # oförändrad stämpel: ingen ny hash
        fil.write_bytes(b'abcd'); h2 = kontroll.sha_fil(fil)
        self.assertNotEqual(h1, h2)

    def test_fel_hash_stoppar_aven_efter_en_lyckad_kompilering_i_samma_process(self):
        self.plan([], kalla=self.kalla_kopia())
        fel = self.kalla_kopia(lambda k: k['matning']['personer'][0]['rorelse'].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'sha256'): self.plan([], kalla=fel)

    def test_andra_anropet_hashar_inga_filer_om(self):
        kalla = self.kalla_kopia(); self.plan([], kalla=kalla); kontroll = kontrollmodul()
        with patch.object(kontroll, 'hashlib') as hl: self.plan([], kalla=kalla); hl.sha256.assert_not_called()

    def test_ny_process_hashar_allt_forst(self):
        import subprocess
        kod = ("import sys;sys.path.insert(0,sys.argv[1]);import gemensamt;m=gemensamt.kontrollmodul();"
               "from pathlib import Path;f=Path(sys.argv[2]);m._HASHMINNE.clear();import hashlib;from unittest.mock import patch\n"
               "with patch.object(m.hashlib,'sha256',wraps=hashlib.sha256) as h:\n  m.sha_fil(f);assert h.call_count==1;m.sha_fil(f);assert h.call_count==1\n")
        fil = _TMP['d']/'ny_process.bin'; fil.write_bytes(b'x')
        r = subprocess.run([sys.executable, '-c', kod, str(HIT), str(fil)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TalUtanSyntes(Bas):
    def repl(self, id, replik, text, **kw):
        return cm(id, 'byt_replik', replik=replik, text=text, sprak='sv', rost=dict(motor='piper', rost_id=None, stil=None), tidspolicy='samma_lucka', max_talfaktor=kw.get('max'))

    def test_langder_utan_syntes_ar_markta(self):
        with patch.object(tal, 'CACHE', _TMP['d']/'tal_tom'):
            (o, n), kalla = tal.langder_utan_syntes('nst', 'Hej du', 'Hej du kära', 2.0)
            self.assertEqual((kalla, o, n), ('uppskattad', 2.0, round(2.0*11/6, 4)))
            tal.CACHE.mkdir(parents=True)
            np.save(tal.CACHE/f'mat_{tal._nyckel("nst", "Hej du")}.npy', np.float64(1.5)); np.save(tal.CACHE/f'mat_{tal._nyckel("nst", "Hej du kära")}.npy', np.float64(2.5))
            self.assertEqual(tal.langder_utan_syntes('nst', 'Hej du', 'Hej du kära', 2.0), ((1.5, 2.5), 'matt'))

    def test_snabbvagen_syntetiserar_inget_men_utvarderar_regeln(self):
        with patch.object(tal, 'CACHE', _TMP['d']/'tal_tom2'), patch.object(tal, 'mat_langd', side_effect=AssertionError('syntes')), patch.object(tal, 'passa', side_effect=AssertionError('syntes')):
            p = self.plan([self.repl('kort', 'r7', 'Men jag känner dig ju inte?'), self.repl('lang', 'r1', 'Men vänta nu, menar du verkligen att du inte tänker betala notan i kväll?')])
        self.assertEqual([e['id'] for e in p['tillampat']], ['kort', 'lang']); t = {x['edit']: x for x in p['tal']}
        for post in t.values():
            self.assertEqual((post['ljud'], post['langd_kalla']), ('vantar', 'uppskattad'))
            self.assertIsNone(post['syntetiserad_langd_s']); self.assertIsNone(post['length_scale']); self.assertIsNone(post['extra_tempo'])
            self.assertTrue(post['text'] and post['slot_langd_s'] > 0 and post['ut_slot_s'])
        self.assertEqual(t['kort']['regel'], 'inom_gransen'); self.assertEqual(t['lang']['regel'], 'over_gransen_uppskattad')
        self.assertGreater(t['lang']['taktfaktor_mot_original'], 1.15)
        self.assertTrue(any('uppskattad taktfaktor' in v and 'lang' in v for v in p['varningar']))
        self.assertFalse(any('kort' in v for v in p['varningar'] if 'taktfaktor' in v))
        self.assertEqual(next(e for e in p['tillampat'] if e['id'] == 'lang')['andring']['langd_kalla'], 'uppskattad')

    def test_undertexten_byts_och_kopior_far_unika_id(self):
        with patch.object(tal, 'CACHE', _TMP['d']/'tal_tom3'):
            p = self.plan([self.repl('r', 'r1', 'Hej igen.'), cm('u', 'duplicera_scen', scen='s1', ny_id='s1_copy', efter='s1', med_ljud=False)])
        ids = [x['id'] for x in p['skarmtext']]; self.assertEqual(len(ids), len(set(ids)), ids)
        self.assertIn('st1', ids); self.assertIn('st1@s1_copy', ids)
        self.assertEqual({x['scen']: x['text'] for x in p['skarmtext'] if x['id'].split('@')[0] == 'st1'}['s1'], 'Hej igen.')

    @unittest.skipUnless(__import__('test_flode')._piper(), 'Piper eller röstfiler saknas')
    def test_syntessteget_fyller_i_och_utvarderar_regeln_pa_riktigt(self):
        p = self.plan([self.repl('kort', 'r7', 'Men jag känner dig ju inte?'), self.repl('lang', 'r1', 'Men vänta nu, menar du verkligen att du inte tänker betala notan i kväll?')])
        self.assertTrue(all(x['ljud'] == 'vantar' for x in p['tal']))
        tal.syntetisera_plan(p); t = {x['edit']: x for x in p['tal']}
        self.assertTrue(all(x['ljud'] == 'klart' and x['langd_kalla'] == 'matt' and x['syntetiserad_langd_s'] > 0 for x in p['tal']))
        self.assertEqual(t['kort']['regel'], 'inom_gransen'); self.assertEqual(t['lang']['regel'], 'over_gransen')
        self.assertFalse(any('uppskattad taktfaktor' in v for v in p['varningar']))
        self.assertTrue(any('efter syntes' in v and 'lang' in v for v in p['varningar']))


class SchemafelEnskilt(Bas):
    def test_schemafelaktig_edit_avvisas_ensam_och_resten_galler(self):
        trasig = cm('trasig', 'byt_replik', replik='r1', text='Hej igen.', sprak='sv', tidspolicy='samma_lucka', max_talfaktor=None)   # rost saknas
        okand = dict(id='okand', op='finns_inte', ursprung=dict(typ='cm'))
        p = self.plan([cm('bort', 'ta_bort_scen', scen='s2'), trasig, okand, cm('flytt', 'flytta_scen', scen='s7', efter=None)])
        self.assertEqual([e['id'] for e in p['tillampat']], ['bort', 'flytt'])
        nej = {e['id']: e for e in p['ej_tillampat']}; self.assertEqual([e['id'] for e in p['ej_tillampat']], ['trasig', 'okand'])
        self.assertIn('regi-schemat', nej['trasig']['orsak']); self.assertIn('rost', nej['trasig']['orsak']); self.assertEqual(nej['trasig']['op'], 'byt_replik')
        self.assertIn('finns_inte', nej['okand']['orsak'])
        self.assertEqual([t['kalla'] for t in p['tidskarta']][0], [337, 383])   # flytten gällde
        self.assertEqual(len(p['scener']), 6)

    def test_sakra_edit_utan_id_far_syntetiskt_id_och_ordning_bevaras(self):
        p = self.plan([cm('a', 'ta_bort_scen', scen='s2'), dict(op='ta_bort_scen', scen='s3'), cm('c', 'ta_bort_scen', scen='s4')])
        self.assertEqual([e['id'] for e in p['ej_tillampat']], ['edit[1]']); self.assertEqual([e['id'] for e in p['tillampat']], ['a', 'c'])

    def test_fel_i_regins_huvud_och_i_kalla_avvisar_fortfarande_hela_regin(self):
        self.r['utdata'].pop('bredd')
        with self.assertRaisesRegex(ValueError, 'bredd'): self.plan([cm('a', 'ta_bort_scen', scen='s2')])
        self.r = ladda(self.regi); self.r['kalla']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'sha256'): self.plan([cm('a', 'ta_bort_scen', scen='s2')])
        self.r = ladda(self.regi)
        # 0016: ett referensfel i en enskild edit avvisar bara den editen, med skäl (förut hela regin).
        p = self.plan([cm('a', 'ta_bort_scen', scen='s99'), cm('b', 'ta_bort_scen', scen='s2')])
        self.assertEqual([e['id'] for e in p['ej_tillampat']], ['a']); self.assertIn('finns inte i kalla', p['ej_tillampat'][0]['orsak'])
        self.assertEqual([e['id'] for e in p['tillampat']], ['b'])


class Tillgangar(Bas):
    def test_kort_med_tillgang_far_post_och_markt_geometri(self):
        p = self.plan([cm('k', 'byt_prop', prop='bord_A', ny_typ='foreground', tillgang_id='s3:foreground', tillgang_kalla='kort', scen='alla')])
        self.assertEqual([e['id'] for e in p['tillampat']], ['k'])
        poster = [o for o in p['objekt'] if o['id'] == 'bord_A']; self.assertTrue(poster)
        for o in poster: self.assertEqual((o['tillgang']['id'], o['tillgang']['kalla'], o['tillgang']['geometri']), ('s3:foreground', 'kort', 'ej_byggd'))
        t0 = self.plan([]); self.assertFalse(any('tillgang' in o for o in t0['objekt']))

    def test_lagg_till_kort_och_propbank_tillgang(self):
        p = self.plan([cm('l', 'lagg_till_prop', ny_id='kort_ny', typ='foreground', tillgang_id='s3:foreground', tillgang_kalla='kort', scen='s1', matt_m=[.3, .3, .1], stod='bord_A')])
        self.assertEqual([e['id'] for e in p['tillampat']], ['l']); self.assertEqual(next(o for o in p['objekt'] if o['id'] == 'kort_ny')['tillgang']['geometri'], 'ej_byggd')
        from propbank import BANK
        typ = sorted(BANK)[0]
        p = self.plan([cm('b', 'byt_prop', prop='bord_A', ny_typ=typ, tillgang_id=typ, tillgang_kalla='propbank', scen='s1')])
        self.assertEqual(next(o for o in p['objekt'] + p.get('props', []) if o['id'] == 'bord_A')['tillgang'], dict(id=typ, kalla='propbank', geometri='byggd'))

    def test_tillgang_utan_kalla_eller_okand_propbank_nekas(self):
        p = self.plan([cm('a', 'byt_prop', prop='bord_A', ny_typ='foreground', tillgang_id='s3:foreground', scen='s1'),
                       cm('b', 'byt_prop', prop='bord_A', ny_typ='x', tillgang_id='finns_inte', tillgang_kalla='propbank', scen='s1')])
        self.assertEqual(p['tillampat'], []); orsaker = {e['id']: e['orsak'] for e in p['ej_tillampat']}
        self.assertIn('tillgang_kalla', orsaker['a']); self.assertIn('propbanken', orsaker['b'])
        self.assertFalse(any('tillgang' in o for o in p['objekt']))   # nekad edit lämnar inget spår

    def test_lokalbyte_med_platta_bars_av_planen_och_markt_ej_byggt(self):
        rum = dict(kalla='platta', tillgang_id='b_s2', ord=[], beskrivning='Plåt ur klippet')
        p = self.plan([cm('m', 'byt_miljo', scen='s1', rum=rum)])
        self.assertEqual([e['id'] for e in p['tillampat']], ['m'])
        lb = p['lokalbyte']; self.assertEqual(len(lb), 1); self.assertEqual((lb[0]['scen'], lb[0]['tillgang_id'], lb[0]['kalla'], lb[0]['geometri']), ('s1', 'b_s2', 'platta', 'ej_byggd'))
        self.assertEqual(lb[0]['ersatter'], 'plats_1' if p['scener'][0].get('plats_id') == 'plats_1' else lb[0]['ersatter'])
        self.assertEqual(p['scener'][0]['lokal']['geometri'], 'ej_byggd'); self.assertNotIn('lokal', p['scener'][1])
        self.assertEqual(self.plan([])['plats'][0]['id'], p['plats'][0]['id'])   # det uppmätta rummet står kvar som platshållare
        up = self.plan([cm('u', 'byt_miljo', scen='alla', rum=dict(rum, kalla='upload'))])
        self.assertEqual(len(up['lokalbyte']), 7)

    def test_okand_bankplats_nekas_som_forut(self):
        p = self.plan([cm('m', 'byt_miljo', scen='s1', rum=dict(kalla='bank', tillgang_id='b_s2', ord=[], beskrivning=None))])
        self.assertEqual(p['tillampat'], []); self.assertIn('platsbanken', p['ej_tillampat'][0]['orsak']); self.assertNotIn('lokalbyte', p)


if __name__ == '__main__': unittest.main()
