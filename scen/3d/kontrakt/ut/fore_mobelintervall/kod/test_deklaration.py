"""Nya klipp får explicit huvudroll/spår utan att deklarationen blir ägarbeslut."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import deklaration_till_hand as d


class Deklaration(unittest.TestCase):
    def test_explicit_roll_och_spar_i_tvapersonstagning(self):
        # A kommer först och skulle annars skrivas över av B i roll_i.
        D = dict(schema_version='deklaration/0.6', datum='2026-11-11', klipp='prov',
                 platser=dict(stol_A=dict(typ='sits', roll='A', pos_m=[0, 0, 0], blick_grader=90, sitthojd_m=.75),
                              staplats_B=dict(typ='staplats', roll='B', pos_m=[0, 1.3, 0], blick_grader=-90)),
                 roller=dict(A=dict(tagningar=['S1'], lage='sitter'), B=dict(tagningar=['S1'], lage='står')),
                 kameror=dict(S1=dict(huvudroll='A', spar_id='2', person_plats='stol_A', hojd_m=1.4)),
                 berattat_rum=dict(status='antagen'))
        K = np.zeros((3, 70, 3)); K[:, :, 2] = 2
        with tempfile.TemporaryDirectory() as tmp:
            I = Path(tmp); (I / 'S1/kropp/2').mkdir(parents=True)
            with patch.object(d, 'kropp', return_value=K) as body, patch.object(d, 'handsyn', return_value=np.ones((3, 2), bool)) as hands:
                hand, logg = d.oversatt(I, D)
            body.assert_called_once_with(I / 'S1', '2')
            hands.assert_called_once_with(I / 'S1', 3, '2')
            self.assertEqual(logg['S1']['roll'], 'A')
            self.assertEqual(hand['S1']['huvudroll'], 'A')
            self.assertEqual(logg['S1']['hofthojd_m'], .835)
            self.assertEqual(hand['S1']['person_pos_m'], [0., 0., 0.])

    def test_flera_roller_skrivs_bara_nar_tva_roller_har_deklarerad_plats(self):
        P = dict(stol_A=dict(typ='sits', roll='A', pos_m=[0, 0, 0], blick_grader=90, sitthojd_m=.75),
                 staplats_B=dict(typ='staplats', roll='B', pos_m=[0, 1.3, 0], blick_grader=-90))
        D = dict(schema_version='deklaration/0.6', datum='2026-11-11', klipp='prov', platser=P,
                 roller=dict(A=dict(tagningar=['S1', 'S2'], lage='sitter'), B=dict(tagningar=['S2'], lage='står')),
                 kameror=dict(S1=dict(huvudroll='A', person_plats='stol_A', hojd_m=1.4), S2=dict(huvudroll='B', person_plats='staplats_B', hojd_m=1.4)),
                 berattat_rum=dict(status='antagen'), narvaro=dict(bryter_rummet=[]))
        K = np.zeros((3, 70, 3)); K[:, :, 2] = 2
        with tempfile.TemporaryDirectory() as tmp:
            I = Path(tmp); (I / 'S1/kropp/1').mkdir(parents=True); (I / 'S2/kropp/1').mkdir(parents=True)
            with patch.object(d, 'kropp', return_value=K), patch.object(d, 'handsyn', return_value=np.ones((3, 2), bool)):
                hand, _ = d.oversatt(I, D)
                D['narvaro']['bryter_rummet'] = ['S2']; bryt, _ = d.oversatt(I, D)
        self.assertNotIn('flera_roller', hand['S1'])                                   # en deklarerad roll: som förut
        self.assertEqual(hand['S2']['flera_roller']['A']['pos_m'], [0., 0., 0.]); self.assertEqual(hand['S2']['flera_roller']['B']['blick_grader'], -90)
        self.assertNotIn('flera_roller', bryt['S2'])                                   # en tagning som bryter rummet registreras inte mot platserna

    def test_passa_roller_loser_yaw_och_translation_i_minsta_kvadrat(self):
        import math, plats
        mal = np.array([[0., 0.], [0., 1.3]]); a = 0.7; R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        last = (mal - [0.3, 0.2]) @ R.T                                                # samma par roterat och flyttat: exakt lösning
        yaw, t = plats.passa_roller(last, mal)
        self.assertLess(np.abs((last @ plats.rz(yaw)[:2, :2].T + t) - mal).max(), 1e-9)
        last2 = (np.array([[0., 0.], [0., 1.7]]) - [0.3, 0.2]) @ R.T                  # för långt avstånd: felet delas lika
        yaw, t = plats.passa_roller(last2, mal); res = np.linalg.norm((last2 @ plats.rz(yaw)[:2, :2].T + t) - mal, axis=1)
        self.assertAlmostEqual(res[0], .2, 6); self.assertAlmostEqual(res[1], .2, 6)
        self.assertIsNone(plats.passa_roller([[1., 1.], [1., 1.]], mal))               # utan riktning: ingen lösning, plats.py faller tillbaka


if __name__ == '__main__':
    unittest.main()
