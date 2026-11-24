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

    def test_bord_som_intervall_ger_mobler_och_mallens_mitt(self):
        P = dict(stol_A=dict(typ='sits', roll='A', pos_m=[0, 0, 0], blick_grader=90, sitthojd_m=.75),
                 disk=dict(typ='bord', mitt_m=[0, [0.5, 0.8], 0], framfor='stol_A', storlek_m=dict(langs_x=2.8, langs_y=[0.5, 0.8], hojd=[0.95, 1.15]), massiv=True,
                           bild=dict(tagning='S1', box_2d=[550, 0, 1000, 1000])),
                 bord=dict(typ='bord', mitt_m=[1, 1, 0], framfor='stol_A', storlek_m=dict(langs_x=.6, langs_y=1.2, hojd=.74)))
        D = dict(schema_version='deklaration/0.7', datum='2026-11-11', klipp='prov', platser=P,
                 roller=dict(A=dict(tagningar=['S1'], lage='sitter')), kameror=dict(S1=dict(huvudroll='A', person_plats='stol_A', hojd_m=1.4)),
                 berattat_rum=dict(status='antagen'), narvaro=dict(bryter_rummet=[]))
        K = np.zeros((3, 70, 3)); K[:, :, 2] = 2
        with tempfile.TemporaryDirectory() as tmp:
            I = Path(tmp); (I / 'S1/kropp/1').mkdir(parents=True)
            with patch.object(d, 'kropp', return_value=K), patch.object(d, 'handsyn', return_value=np.ones((3, 2), bool)):
                hand, _ = d.oversatt(I, D)
        m = hand['deklarerat']['mobler']
        self.assertEqual(m['disk'], dict(hojd_m=[0.95, 1.15], langs_x_m=2.8, langs_y_m=[0.5, 0.8], mitt_x_m=0, mitt_y_m=[0.5, 0.8], massiv=True,
                                         bild=dict(tagning='S1', box_2d=[550, 0, 1000, 1000]), framfor='stol_A'))   # intervall, form, bildruta och ordningsrelation förs vidare orörda
        self.assertEqual(m['bord']['hojd_m'], .74)                                                                                       # ett tal är hårt
        self.assertNotIn('framfor', m['bord'])                                                                                           # utan bildruta: ingen ny metadata eller ändrat flöde
        mall = {x['id']: x for x in d.rumsmall(D)['delar']}
        self.assertEqual(mall['disk']['matt_m'], [2.8, .65, 1.05]); self.assertEqual(mall['disk']['pos_m'], [0, .65, 0])                 # mallen får intervallens mitt
        self.assertEqual(mall['bord']['matt_m'], [.6, 1.2, .74])
        import rumsmall
        lador=rumsmall.byggobjekt(dict(delar=[mall['disk']]))
        self.assertEqual(len(lador),1);self.assertEqual(lador[0]['matt_m'],[2.8,.65,1.05]);self.assertEqual(lador[0]['pos_m'][2],.525)

    def test_deklarerad_vagg_ar_hard_och_foljer_deklarationen_annars_mallens_marginal(self):
        P = dict(stol_A=dict(typ='sits', roll='A', pos_m=[0, 0, 0], blick_grader=90, sitthojd_m=.75), staplats_B=dict(typ='staplats', roll='B', pos_m=[0, 1.7, 0], blick_grader=-90))
        D = dict(schema_version='deklaration/0.7', datum='2026-11-12', klipp='prov', platser=P, roller=dict(A=dict(tagningar=['S1'], lage='sitter')),
                 kameror=dict(S1=dict(huvudroll='A', person_plats='stol_A', hojd_m=1.4)), berattat_rum=dict(status='antagen'), narvaro=dict(bryter_rummet=[]))
        K = np.zeros((3, 70, 3)); K[:, :, 2] = 2
        def kor(D):
            with tempfile.TemporaryDirectory() as tmp:
                I = Path(tmp); (I / 'S1/kropp/1').mkdir(parents=True)
                with patch.object(d, 'kropp', return_value=K), patch.object(d, 'handsyn', return_value=np.ones((3, 2), bool)):
                    hand, _ = d.oversatt(I, D)
            return hand, {x['id']: x for x in d.rumsmall(D)['delar']}
        hand, mall = kor(D)
        self.assertNotIn('vaggar', hand.get('deklarerat', {}))                            # utan deklaration: ingen hård vägg, mallens marginal
        self.assertAlmostEqual(mall['vagg_bak']['pos_m'][1], 1.7 + 1.2); self.assertAlmostEqual(mall['vagg_sida']['pos_m'][0], 0 + 1.2)
        D['vaggar'] = dict(bak=dict(y_m=2.2, status='uppmatt'))
        hand, mall = kor(D)
        self.assertEqual(hand['deklarerat']['vaggar'], dict(vagg_bak=dict(y_m=2.2, status='uppmatt')))
        self.assertAlmostEqual(mall['vagg_bak']['pos_m'][1], 2.2); self.assertAlmostEqual(mall['vagg_sida']['pos_m'][0], 1.2)

    def test_vilande_handled_sanker_bara_intervallets_tak(self):
        P = dict(stol_A=dict(typ='sits', roll='A', pos_m=[0, 0, 0], blick_grader=90, sitthojd_m=.45),
                 bord=dict(typ='bord', mitt_m=[0, .8, 0], storlek_m=dict(langs_x=.6, langs_y=1.2, hojd=[.66, .74]), hojd_regel='vilande_handled', roller=['A']))
        D = dict(schema_version='deklaration/0.7', datum='2026-11-11', klipp='prov', platser=P, roller=dict(A=dict(tagningar=['S1'], lage='sitter')),
                 kameror=dict(S1=dict(huvudroll='A', person_plats='stol_A', hojd_m=1.2)), berattat_rum=dict(status='antagen'), narvaro=dict(bryter_rummet=[]))
        K = np.zeros((3, 70, 3)); K[:, :, 2] = 2; K[:, 41, 1] = -.77            # lägsta vilande handled
        with tempfile.TemporaryDirectory() as tmp:
            I = Path(tmp); (I / 'S1/kropp/1').mkdir(parents=True)
            with patch.object(d, 'kropp', return_value=K), patch.object(d, 'handsyn', return_value=np.ones((3, 2), bool)):
                hand, logg = d.oversatt(I, D)
        h = hand['deklarerat']['mobler']['bord']['hojd_m']
        self.assertIsInstance(h, list); self.assertLessEqual(h[1], .74); self.assertLessEqual(h[0], h[1])

    def test_foremalmetadata_foljer_deklareratvagen_och_byggs_i_stodkedja(self):
        P = dict(staplats_A=dict(typ='staplats',roll='A',pos_m=[0,1,0],blick_grader=-90),
                 disk=dict(typ='bord',mitt_m=[0,0,0],storlek_m=dict(langs_x=2.,langs_y=1.,hojd=.9),massiv=True,bilder=[]))
        D = dict(schema_version='deklaration/0.8',datum='2026-11-12',klipp='prov',platser=P,
                 roller=dict(A=dict(tagningar=['S1'],lage='står')),kameror=dict(S1=dict(huvudroll='A',person_plats='staplats_A',hojd_m=1.4)),
                 berattat_rum=dict(status='antagen'),narvaro=dict(bryter_rummet=[]),
                 foremal=dict(vag=dict(pa='disk',storlek_m=[.4,.3,.5],bild=dict(tagning='S1',box_2d=[100,200,300,400]),
                                        bilder=[dict(tagning='S1',box_2d=[100,200,300,400]),dict(tagning='S2',box_2d=[110,210,310,410])]),
                              kott=dict(pa='vag',storlek_m=[.2,.2,.1])))
        K=np.zeros((3,70,3));K[:,:,2]=2
        with tempfile.TemporaryDirectory() as tmp:
            I=Path(tmp);(I/'S1/kropp/1').mkdir(parents=True)
            with patch.object(d,'kropp',return_value=K),patch.object(d,'handsyn',return_value=np.ones((3,2),bool)):
                hand,_=d.oversatt(I,D)
        self.assertEqual(hand['deklarerat']['foremal']['vag']['objekt_id'],'disk:pa:vag')
        self.assertEqual(hand['deklarerat']['foremal']['kott']['objekt_id'],'disk:pa:vag:pa:kott')
        self.assertEqual(len(hand['deklarerat']['foremal']['vag']['bilder']),2)
        self.assertEqual(hand['deklarerat']['mobler']['disk']['bilder'],[])
        delar={x['id']:x for x in d.rumsmall(D)['delar']}
        self.assertEqual(delar['disk:pa:vag']['pos_m'][2],.9)
        self.assertEqual(delar['disk:pa:vag:pa:kott']['pos_m'][2],1.4)

    def _ersattnings_D(self, bord_tagn):
        P = dict(staplats_A=dict(typ='staplats', roll='A', pos_m=[0, 1, 0], blick_grader=-90),
                 disk_A=dict(typ='bord', mitt_m=[0, 0, 0], storlek_m=dict(langs_x=2., langs_y=1., hojd=.9), massiv=True, tagningar_i_bild=bord_tagn[0]),
                 disk_C=dict(typ='bord', mitt_m=[3, 0, 0], storlek_m=dict(langs_x=2., langs_y=1., hojd=1.), massiv=True, tagningar_i_bild=bord_tagn[1]))
        return dict(schema_version='deklaration/0.8', datum='2026-11-12', klipp='prov', platser=P,
                    roller=dict(A=dict(tagningar=['S1'], lage='står')), kameror=dict(S1=dict(huvudroll='A', person_plats='staplats_A', hojd_m=1.4)),
                    berattat_rum=dict(status='antagen'), narvaro=dict(bryter_rummet=[]),
                    foremal=dict(kott=dict(pa='inslagspapper', storlek_m=[.2, .2, .1], tagningar_i_bild=['S1', 'S2', 'S3'])))

    def test_foremal_vars_stod_inte_byggs_far_ersattningsstod(self):
        D = self._ersattnings_D((['S1'], ['S2', 'S3']))
        self.assertEqual(d.ersatt_stod(D, 'kott'), 'disk_C')               # bordet som täcker flest av föremålets tagningar
        self.assertEqual(d.foremal_id(D, 'kott'), 'disk_C:pa:kott')
        K = np.zeros((3, 70, 3)); K[:, :, 2] = 2
        with tempfile.TemporaryDirectory() as tmp:
            I = Path(tmp); (I / 'S1/kropp/1').mkdir(parents=True)
            with patch.object(d, 'kropp', return_value=K), patch.object(d, 'handsyn', return_value=np.ones((3, 2), bool)):
                hand, _ = d.oversatt(I, D)
        meta = hand['deklarerat']['foremal']['kott']
        self.assertEqual(meta['objekt_id'], 'disk_C:pa:kott'); self.assertEqual(meta['stod_ersatt']['fran'], 'inslagspapper')
        delar = {x['id']: x for x in d.rumsmall(D)['delar']}
        self.assertEqual(delar['disk_C:pa:kott']['pos_m'][2], 1.0)           # står på diskens ovansida
        # utan bord som delar tagning med föremålet finns inget ersättningsstöd, och kedjan förblir bruten som förut
        D2 = self._ersattnings_D(([], ['S9']))
        self.assertIsNone(d.ersatt_stod(D2, 'kott')); self.assertIsNone(d.foremal_id(D2, 'kott'))
        self.assertNotIn('disk_C:pa:kott', {x['id'] for x in d.rumsmall(D2)['delar']})

    def test_fokal_per_klipp_provas_mot_klippets_spridning(self):
        import fokal_klipp as fk
        vp = [950, 980, 1000, 1020, 1050, 1100]
        tag = dict(S1=dict(colmap=1618., colmap_godkand=False, vp=vp[:3]), S2=dict(colmap=1040., colmap_godkand=True, vp=vp[3:]),
                   S5=dict(colmap=2335., colmap_godkand=True, vp=[]), S6=dict(colmap=None, colmap_godkand=False, vp=[]))
        klipp, per = fk.bestam(tag, 1024)
        self.assertAlmostEqual(klipp['fokal_px'], 1010., delta=1.)
        self.assertEqual(per['S2']['fokal_status'], 'matt'); self.assertEqual(per['S2']['fokal_px'], 1040.)   # inom spridningen
        self.assertEqual(per['S5']['fokal_status'], 'skattad'); self.assertAlmostEqual(per['S5']['fokal_px'], 1010., delta=1.)   # 2,3 gånger klippet: avvisas
        self.assertEqual(per['S5']['avvikelse']['utfall'][:7], 'klippet'); self.assertGreater(per['S5']['avvikelse']['kvot'], 2.)
        self.assertEqual(per['S1']['fokal_status'], 'skattad')               # underkänd COLMAP-fokal ersätts av klippvärdet
        # saknas allt gäller längsta sidan, märkt antagen
        k0, p0 = fk.bestam(dict(S1=dict(colmap=None, colmap_godkand=False, vp=[])), 1024)
        self.assertNotIn('fokal_px', k0); self.assertEqual(p0['S1'], dict(fokal_px=1024., fokal_status='antagen', fokal_kalla='bildens längsta sida', colmap_px=None))
        # rörlig zoom: tagningens egna försvinningspunkter och COLMAP stämmer med varandra men inte med klippet, så tagningen behåller sitt värde
        tag['Z'] = dict(colmap=1650., colmap_godkand=True, vp=[1600, 1640, 1700])
        klipp2, per2 = fk.bestam(tag, 1024)
        self.assertEqual(per2['Z']['fokal_px'], 1650.); self.assertEqual(per2['Z']['fokal_status'], 'matt')
        self.assertIn('rörlig zoom', per2['Z']['avvikelse']['utfall'])

    def test_kamerabeslut_med_klippfokal_behaller_gamla_statusord(self):
        import regler
        m = dict(bredd=576, hojd=1024); k = dict(registrerade=11, av=16, fel_px=.08, fokal_px=2334.7)
        fore = regler.kamerabeslut(k, m)
        self.assertEqual((fore['fokal_px'], fore['status'], fore['kalla']), (2334.7, 'uppmatt', 'COLMAP'))
        efter = regler.kamerabeslut(k, m, dict(fokal_px=1010., fokal_status='skattad', fokal_kalla='klippets median', avvikelse=dict(kvot=2.3)))
        self.assertEqual((efter['fokal_px'], efter['status'], efter['fokal_status']), (1010., 'antagen', 'skattad'))
        self.assertEqual(efter['colmap_fokal_px'], 2334.7)
        self.assertEqual(regler.kamerabeslut(k, m, None), fore)              # utan klippfokal är allt som förut

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
