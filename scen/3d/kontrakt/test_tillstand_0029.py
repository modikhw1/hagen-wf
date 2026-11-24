"""0029: mening i källan (handlingsspår, relevans), regi på handlingar, renderbana och scenbygge ur en generering.

    scen/.venv/Scripts/python.exe -m unittest test_tillstand_0029      (från scen/3d/kontrakt)
Integrationsproven kompilerar gelatos källa (ut/kand-kennysgelato_n06-hand/kalla_0029.json) med snabbvägen och egen tom cache.
"""
import copy, json, shutil, sys, tempfile, unittest
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
HIT = Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))
import datacache
from gemensamt import ladda

KALLA = HIT / 'ut/kand-kennysgelato_n06-hand/kalla_0029.json'
BAS = HIT / 'ut/kand-kennysgelato_n06-hand/tom/regi.json'


class Gelato(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix='t0029_')); cls._cache = datacache.CACHE; datacache.CACHE = cls.tmp / 'cache'
        from kompilera import kompilera
        cls.kompilera = staticmethod(kompilera); cls.K = ladda(KALLA)
        cls.bas = cls.plan([])

    @classmethod
    def tearDownClass(cls):
        datacache.CACHE = cls._cache; shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def plan(cls, edits, namn=None):
        r = ladda(BAS); r['kalla']['revision'] = cls.K['revision'] if hasattr(cls, 'K') else ladda(KALLA)['revision']
        r['edits'] = [dict(id=f'e{i}', ursprung={'typ': 'cm'}, **e) for i, e in enumerate(edits)]
        f = cls.tmp / f'{namn or len(list(cls.tmp.glob("r*.json")))}_r.json'; f.write_text(json.dumps(r, ensure_ascii=False), encoding='utf-8')
        return cls.kompilera(KALLA, f, snabb=True)

    def seg(self, sid): return next(g for g in self.K['semantik']['handling'][0]['segment'] if g['id'] == sid)

    def test_kallan_bar_mening_och_ursprung(self):
        sem, mat = self.K['semantik'], self.K['matning']
        self.assertEqual([g['id'] for g in sem['handling'][0]['segment']], [f'h{i}' for i in range(1, 10)])
        self.assertEqual(self.seg('h9')['handling']['varde'], 'luta_sig'); self.assertIn('rattad', self.seg('h9')['handling'])
        self.assertTrue(any(p['id'] == 'kund_hand' and p['roll'] == 'bar' for p in sem['relevans']['poster']))
        mp = next(m for m in mat['personer'] if m.get('scen') in (None, 's1') and m['person'] == 'A' and m.get('ursprung'))
        self.assertEqual(mp['ursprung']['typ'], 'generering'); self.assertTrue(any('tidsavbildning' in f['roll'] for f in mp['ursprung']['filer']))

    def test_renderbana_och_kropp_ur_genereringen(self):
        rb = np.load(KALLA.parent / next(k for k in self.K['matning']['kameror'] if k['id'] == 'kam_s1')['renderbana']['fil']['sokvag'])
        nk = self.bas['renderkamera']['nycklar']
        self.assertTrue(np.allclose(np.array(nk[0]['matris']), rb['matris'][0])); self.assertAlmostEqual(nk[155]['lins_mm'], float(rb['lins_mm'][155]))
        self.assertIn('dreamina_t_rot', self.bas['scener'][0]['personer'][0]['rorelse'])

    def test_scenbygge_ersatter_disken_bara_i_s1(self):
        ob = [(o['id'], tuple(o['synlig_ut'])) for o in self.bas['objekt']]
        self.assertIn(('disk_A', (156, 252)), ob); self.assertIn(('disk_A:trag', (0, 156)), ob)
        self.assertTrue(any(i == 'kund:arm' and a >= 116 for i, (a, b) in ob))
        h = next(x for x in self.bas['handforemal'] if x['scen'] == 's1'); self.assertEqual(h['offset_status'], 'matt ur genereringen, mot den byggda kroppen')

    def test_ta_bort_handling_med_overgang_och_varning(self):
        p = self.plan([dict(op='ta_bort_handling', scen='s1', segment='h3')])
        a, b = self.seg('h3')['rutor']; n = b - a
        self.assertEqual(len(p['kallrutor']), len(self.bas['kallrutor']) - n + 6)
        d = p['scener'][0]; self.assertEqual([x['marke'] for x in d['handlingsrutor']], ['last', 'overgang', 'last'])
        self.assertTrue(any(v.startswith('Meningen bärs av') for v in p['varningar'])); self.assertTrue(p['mening']['varningar'])
        tk = [x for x in p['tidskarta'] if x.get('handling') == 'overgang']; self.assertTrue(tk and not tk[0]['ljud'])
        self.assertTrue(any(h['scen'] == 's1' and h['synlig_ut'] == d['ut'] for h in p['handforemal']))

    def test_tempo_och_upprepa(self):
        a, b = self.seg('h3')['rutor']; n = b - a
        p = self.plan([dict(op='tempo_handling', scen='s1', segment='h3', faktor=2.0)])
        self.assertEqual(len(p['kallrutor']), len(self.bas['kallrutor']) + n)
        a3, b8 = self.seg('h3')['rutor'][0], self.seg('h8')['rutor'][1]
        q = self.plan([dict(op='upprepa_handling', scen='s1', fran='h3', till='h8', antal=2)])
        self.assertEqual(len(q['kallrutor']), len(self.bas['kallrutor']) + (b8 - a3) + 6)
        self.assertIn('upprepning', [x['marke'] for x in q['scener'][0]['handlingsrutor']])

    def test_okant_segment_avvisas_ensamt(self):
        p = self.plan([dict(op='ta_bort_handling', scen='s1', segment='h99'), dict(op='trimma_scen', scen='s2', slut_s=9.4084, lage='hall_sista')])
        self.assertEqual([x['id'] for x in p['ej_tillampat']], ['e0']); self.assertEqual([x['id'] for x in p['tillampat']], ['e1'])

    def test_borttagen_disk_kommer_inte_tillbaka_ur_bygget(self):
        p = self.plan([dict(op='ta_bort_prop', scen='alla', prop='disk_A')])
        self.assertFalse(any(o['id'] == 'disk_A' or o['id'].startswith('disk_A:') for o in p['objekt']))
        self.assertTrue(any(' ramar meningen: ' in v for v in p['varningar']))


class Omsampling(unittest.TestCase):
    def test_kvaternion_och_rotation_interpoleras(self):
        from kompilera import omsampla
        from scipy.spatial.transform import Rotation as Ro
        d = Path(tempfile.mkdtemp(prefix='t0029o_'))
        try:
            pose = np.zeros((3, 2, 8), np.float32); q0 = Ro.from_euler('z', 0).as_quat(); q1 = Ro.from_euler('z', 90, degrees=True).as_quat()
            pose[0, :, 3:7] = q0; pose[1, :, 3:7] = q1; pose[2, :, 3:7] = q1; pose[1, :, 0] = 10
            R = np.stack([Ro.from_euler('x', a, degrees=True).as_matrix() for a in (0, 60, 60)])
            np.savez(d / 's.npz', pose=pose, kam_R=R, inom=np.array([True, False, False]), rest=np.ones((2, 8)), fokal=np.array(770.))
            ut = np.load(omsampla(d / 's.npz', [(0, 0, 0.0, None), (0, 1, .5, 'overgang'), (1, 1, 0.0, None)], 0, 3, d / 'ut'))
            self.assertEqual(ut['pose'].shape, (3, 2, 8)); self.assertAlmostEqual(float(ut['pose'][1, 0, 0]), 5.0, places=4)
            self.assertAlmostEqual(Ro.from_quat(ut['pose'][1, 0, 3:7]).as_euler('zyx', degrees=True)[0], 45, places=3)
            self.assertAlmostEqual(Ro.from_matrix(ut['kam_R'][1]).as_euler('xyz', degrees=True)[0], 30, places=4)
            self.assertEqual(ut['inom'].tolist(), [True, False, False]); self.assertEqual(ut['rest'].shape, (2, 8))
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
