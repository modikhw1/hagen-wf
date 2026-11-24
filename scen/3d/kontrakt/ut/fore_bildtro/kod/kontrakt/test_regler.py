"""Tester för reglerna efter klipptestet b/a/kenny (steg 8). SYNTETISKA indata där inget annat anges; de skrivs bara till temporära mappar.

    scen/.venv/Scripts/python.exe -B scen/3d/kontrakt/test_regler.py
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HIT = Path(__file__).resolve().parent
sys.path.insert(0, str(HIT)); sys.path.insert(0, str(HIT.parent / 'ingest'))
from regler import kamerabeslut, kort_kamerabana, overkropp, hallningsbeslut  # noqa: E402
from semantik_input import Semantik  # noqa: E402

M = dict(bredd=576, hojd=1024)


class Kamera(unittest.TestCase):
    def test_absurd_brannvidd_fran_fa_rutor_avvisas(self):  # b S1: 2 av 17 rutor, 1618 px
        b = kamerabeslut(dict(registrerade=2, av=17, fel_px=.19, fokal_px=1617.98), M)
        self.assertEqual((b['status'], b['kalla'], b['fokal_px']), ('antagen', 'bildens längsta sida', 1024.0))
        self.assertIn('för få registrerade rutor', b['orsak'])

    def test_brannvidd_utanfor_intervall_avvisas_trots_manga_rutor(self):
        b = kamerabeslut(dict(registrerade=20, av=20, fel_px=.3, fokal_px=8671.), M)
        self.assertEqual(b['status'], 'antagen'); self.assertIn('brännvidd utanför intervallet', b['orsak'])

    def test_bra_losning_godtas_och_sager_vilken(self):
        b = kamerabeslut(dict(registrerade=20, av=24, fel_px=.5, fokal_px=900.), M)
        self.assertEqual((b['status'], b['kalla'], b['fokal_px']), ('uppmatt', 'COLMAP', 900.))

    def test_saknat_fel_avvisas(self):
        self.assertEqual(kamerabeslut(dict(registrerade=0, av=17, fel_px=None, fokal_px=None), M)['status'], 'antagen')


class Bana(unittest.TestCase):
    def test_kort_bana_ar_statisk(self):  # b S5: 7 cm
        c = np.zeros((10, 3)); c[:, 0] = np.linspace(0, .07, 10)
        self.assertTrue(kort_kamerabana(c)['statisk'])

    def test_lang_bana_ar_inte_statisk(self):
        c = np.zeros((10, 3)); c[:, 0] = np.linspace(0, 1.5, 10)
        self.assertFalse(kort_kamerabana(c)['statisk'])


class Kropp(unittest.TestCase):
    def test_endast_overkropp(self):  # b S8–S10, a S4
        self.assertTrue(overkropp(dict(kanda=50, ben_synliga_rutor=0, otillforlitliga=30))['endast_overkropp'])

    def test_ben_synliga_ger_inte_overkropp(self):
        self.assertFalse(overkropp(dict(kanda=50, ben_synliga_rutor=40, otillforlitliga=30))['endast_overkropp'])


class Hallning(unittest.TestCase):
    ur = dict(typ='modellbedomd', modell='MOCK', konfidens='hog')

    def test_skymda_ben_anvander_semantiken(self):  # b: stående bakom disk mättes som sittande
        h = hallningsbeslut(.7, 0., dict(hallning='star', ursprung=self.ur))
        self.assertEqual((h['hallning'], h['status']), ('star', 'modellbedomd'))

    def test_synliga_ben_vinner_over_semantiken(self):
        h = hallningsbeslut(.7, .9, dict(hallning='star', ursprung=self.ur))
        self.assertEqual((h['hallning'], h['status']), ('sitter', 'antagen'))


def _sem(tmp, **over):
    ku = 'hog'
    d = dict(klipp=dict(sprak='sv'), personer=[
        dict(id='P1', beskrivning='MOCK', roll='butcher', konfidens=ku, spar=[dict(tagning='S1', spar_id='1', konfidens=ku), dict(tagning='S1', spar_id='3', konfidens=ku)])],
        ej_personer=[dict(tagning='S1', spar_id='2', typ='forgrundsarm', skal='MOCK: arm som filmar', konfidens=ku)],
        placeringar=[dict(person='P1', hallning='star', tagningar=['S1'], konfidens=ku)], repliker=[], par=[], kamerauppstallningar=[],
        plats=dict(typ='butik_eller_disk', konfidens=ku), tagningar=[])
    d.update(over)
    p = Path(tmp) / 'semantik.json'
    p.write_text(json.dumps(dict(ursprung=dict(modell='MOCK', prompt_version='0'), data=d)), encoding='utf-8')
    return Semantik(p)


class Personer(unittest.TestCase):
    def test_arm_utelamnas_dubbletter_slas_ihop_med_ursprung(self):
        with tempfile.TemporaryDirectory() as t:
            sem = _sem(t)
            P = {'1': {'0': [0, 0, 1, 1], '1': [0, 0, 1, 1]}, '2': {'0': [5, 5, 6, 6]}, '3': {'1': [0, 0, 2, 2], '2': [0, 0, 2, 2]}}
            fp, roller, beslut = sem.filtrera('S1', P)
            self.assertEqual(list(fp), ['1'])
            self.assertEqual(set(fp['1']), {'0', '1', '2'})   # luckor fylls av dubbletten
            self.assertEqual(roller, {'1': 'A'})
            b = {x['spar_id']: x for x in beslut}
            self.assertEqual(b['2']['beslut'], 'utelämnad'); self.assertEqual(b['2']['ursprung']['typ'], 'modellbedomd')
            self.assertEqual(b['1']['sammanslagna'], ['1', '3'])

    def test_okant_spar_stoppar_innan_betald_kropp(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError): _sem(t).filtrera('S1', {'9': {'0': [0, 0, 1, 1]}})


class Standardvarden(unittest.TestCase):
    def test_inga_klippspecifika_standardfiler(self):
        for fil, flaggor in (('kalla_bygg.py', ('--scen3d', '--ordtider')), ('plats.py', ('--scen3d',))):
            p = HIT / fil if fil.startswith('kalla') else HIT.parent / 'ingest' / fil
            for rad in p.read_text(encoding='utf-8').splitlines():
                for f in flaggor:
                    if f"add_argument('{f}'" in rad: self.assertNotIn('default=', rad.split(f"add_argument('{f}'")[1].split('add_argument')[0], (fil, f))


class Ursprung(unittest.TestCase):
    def test_kalla_flera_hardkodar_inte_roll_och_replikkalla(self):
        k = (HIT / 'kalla_flera.py').read_text(encoding='utf-8')
        self.assertIn("'modellbedomd' if sm else 'scen3d'", k); self.assertIn("'modellbedomd' if sm else 'whisper'", k)


class TomtRum(unittest.TestCase):
    def test_tomt_rumssteg_blir_saknas(self):
        r = (HIT.parent / 'ingest/rum.py').read_text(encoding='utf-8')
        self.assertIn("status='modellbedomd' if walls or objects else 'saknas'", r)


class Semantikfil(unittest.TestCase):
    def test_okant_klipp_saknar_semantik_och_handvag_ignorerar_registret(self):
        from semantik_input import hitta
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(hitta(t))
        notan = HIT.parent / 'ingest/ut/notan-tagningar'   # verkliga data: notan har både handfiler och semantik
        self.assertIsNone(hitta(notan, None, True)); self.assertIsNotNone(hitta(notan))

    def test_flera_tagningar_utan_roller_stoppar(self):
        import argparse
        import plats, semantik_input
        orig = semantik_input.hitta; semantik_input.hitta = lambda *a, **k: None   # SYNTETISKT: klipp utan semantikfil
        try:
            a = argparse.Namespace(ingest=str(HIT.parent / 'ingest/ut/notan-tagningar'), ut=tempfile.mkdtemp(), scen3d=None, semantik=None, hand=None, video=None)
            with self.assertRaises(SystemExit): plats.bygg_plats(a)
        finally: semantik_input.hitta = orig


class PersonfriScen(unittest.TestCase):
    def test_scen_utan_person_i_a_ar_giltig(self):  # a S6; läser byggda utdata om de finns
        k = HIT / 'ut/a/kalla.json'
        if not k.exists(): self.skipTest('a är inte byggt')
        K = json.loads(k.read_text(encoding='utf-8'))
        s6 = next(x for x in K['semantik']['scener'] if x['id'] == 's6')
        self.assertFalse(s6.get('bindningar'))
        self.assertFalse([m for m in K['matning']['personer'] if m.get('scen') == 's6'])


if __name__ == '__main__':
    unittest.main()
