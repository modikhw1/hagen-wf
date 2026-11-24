"""Tester för silhuettmåttet, darret, utjämningsmetoden och kamerabanans rimlighetsgräns.
    scen/.venv/Scripts/python.exe -m unittest test_kroppmatt   (i scen/3d/kontrakt)
"""
import sys
import unittest
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent
sys.path[:0] = [str(HIT), str(HIT.parent / 'ingest')]
import kroppmatt as K
import sekvens_jamn as J
from regler import kamerabana_rimlig, skala_bestamd


def kamera(w=576, h=1024, lins=50.):
    # blick längs -Z i Blender-konvention: matris world_from_camera; kameran står på (0,-3,1) och ser mot +Y
    M = np.eye(4); M[:3, :3] = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0.]]); M[:3, 3] = [0, -3, 1]
    return dict(matris=M.tolist(), lins_mm=lins), w, h


class Siluett(unittest.TestCase):
    def kropp(self, dx=0.):
        # en stående standardkropp: vilopose, modellrum (cm, y upp) -> värld (m, z upp)
        pose = K.hud()['s0'].copy(); v = K.hudhorn(pose) / 100
        return np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1) + [dx, 0, 0]

    def test_egen_mask_ger_iou_nara_ett(self):
        key, w, h = kamera(); mw, mh = 144, 256; x = self.kropp()
        sil = K.siluett(x, key, w, h, mw, mh); self.assertIsNotNone(sil); self.assertGreater(sil.sum(), 300)
        ys, xs = np.nonzero(sil); box = [xs.min(), ys.min(), xs.max(), ys.max()]
        r = K.jamfor_mask(sil, sil.copy(), box, mw, mh)
        self.assertGreater(r['iou'], .99); self.assertLess(r['tyngdpunkt_bildhojdandel'], .001)

    def test_forskjuten_kropp_flaggas(self):
        key, w, h = kamera(); mw, mh = 144, 256
        a = K.siluett(self.kropp(), key, w, h, mw, mh); b = K.siluett(self.kropp(.25), key, w, h, mw, mh)
        ys, xs = np.nonzero(a); box = [xs.min() - 20, ys.min(), xs.max() + 20, ys.max()]
        r = K.jamfor_mask(b, a, box, mw, mh)
        self.assertLess(r['iou'], .75); self.assertGreater(r['tyngdpunkt_bildhojdandel'], .02)

    def test_skinning_stammer_med_modellen(self):
        import torch
        m = torch.jit.load(str(HIT.parent / 'klipp2/sam3db/ckpt-vith/assets/mhr_model.pt'), map_location='cpu')
        p = torch.zeros(1, 204); p[0, 10:30] = .3
        with torch.no_grad(): v, s = m(torch.zeros(1, 45), p, torch.zeros(1, 72))
        medel, mx = K.kontrollera_hud(s[0].numpy().astype(float), v[0].numpy().astype(float))
        self.assertLess(medel, .2)   # cm


class Darr(unittest.TestCase):
    def test_rak_rorelse_har_inget_darr_brus_har(self):
        t = np.arange(30)[:, None, None] * np.ones((1, 3, 3)); self.assertAlmostEqual(K.jitter(t), 0., places=9)
        rng = np.random.default_rng(1); self.assertGreater(K.jitter(t + rng.normal(0, .5, t.shape)), .5)

    def test_luckor_ger_inga_trippler(self):
        t = np.arange(10, dtype=float)[:, None, None] * np.ones((1, 2, 3)); t[5] = np.nan
        self.assertAlmostEqual(K.jitter(t), 0.)


class Utjamning(unittest.TestCase):
    def test_brus_minskar_avvikelsen_ar_begransad(self):
        rng = np.random.default_rng(2); N = 120; t = np.arange(N) / 30.
        sann = np.stack([np.sin(2 * np.pi * .8 * t), np.cos(2 * np.pi * .5 * t) * .5], 1); y = sann + rng.normal(0, .05, sann.shape)
        X, sig, eps = J.utjamna(y, np.ones(N), 30., fc=4., k=2.)
        d2 = lambda a: np.abs(a[:-2] - 2 * a[1:-1] + a[2:]).mean()
        self.assertLess(d2(X), .4 * d2(y))
        self.assertLessEqual(np.abs(X - y).max(0)[0], eps[0] * 1.25)          # röret
        self.assertLess(np.abs(X - sann).mean(), np.abs(y - sann).mean())     # närmare sanningen än brusiga indata

    def test_snabb_rorelse_foljs_inte_slatas_bort(self):
        N = 90; y = np.zeros((N, 1)); y[40:50, 0] = 1.0; y += np.random.default_rng(3).normal(0, .01, y.shape)
        X, _, _ = J.utjamna(y, np.ones(N), 30., fc=4., k=2.)
        self.assertGreater(X[44, 0], .85)

    def test_luckor_fylls_mjukt(self):
        N = 60; y = np.linspace(0, 1, N)[:, None]; w = np.ones(N); w[20:30] = 0; y2 = y.copy(); y2[20:30] = 99
        X, _, _ = J.utjamna(y2, w, 30.)
        self.assertLess(np.abs(X[:, 0] - y[:, 0]).max(), .03)

    def test_trasig_ruta_hittas(self):
        rng = np.random.default_rng(4); N = 80; Y = np.cumsum(rng.normal(0, .01, (N, 40)), 0) * .2; Y[37] += 3.0
        fel = J.hitta_trasiga(Y, np.ones(N), 30., np.arange(40)); self.assertTrue(fel[37]); self.assertEqual(int(fel.sum()), 1)

    def test_benlangder_bevaras(self):
        # kroppen byggs ur parametrar med låst form: utjämning av parametrar rör aldrig benens längd.
        import torch
        m = torch.jit.load(str(HIT.parent / 'klipp2/sam3db/ckpt-vith/assets/mhr_model.pt'), map_location='cpu')
        rng = np.random.default_rng(5); N = 24; P = np.zeros((N, 204)); P[:, 10:60] = rng.normal(0, .3, (N, 50))
        X, _, _ = J.utjamna(P, np.ones(N), 30.)
        with torch.no_grad():
            _, s = m(torch.zeros(N, 45), torch.tensor(X).float(), torch.zeros(N, 72))
        s = s.numpy(); par = [(2, 1), (3, 2), (4, 3)]
        for a, b in par:
            l = np.linalg.norm(s[:, a, :3] - s[:, b, :3], axis=1); self.assertLess(l.std(), 1e-3 + .02 * l.mean())


class Kamerabana(unittest.TestCase):
    def test_orimlig_bana_flaggas(self):
        c = np.linspace(0, 11693., 96)[:, None] * [1, 0, 0]; r = kamerabana_rimlig(c, 30.)
        self.assertFalse(r['rimlig']); self.assertTrue(r['skal'])

    def test_handhallen_bana_ar_rimlig(self):
        c = np.linspace(0, 2., 96)[:, None] * [1, 0, 0]; self.assertTrue(kamerabana_rimlig(c, 30.)['rimlig'])

    def test_platt_skalkurva_ar_oidentifierbar(self):
        self.assertFalse(skala_bestamd(np.full(50, .0017) + np.random.default_rng(0).normal(0, 1e-12, 50)))
        self.assertTrue(skala_bestamd(np.linspace(.01, .05, 50)))


class Ledurval(unittest.TestCase):
    def test_fingerleder_raknas_aven_nar_benen_ar_dolda(self):
        from trohet import synliga_par, KP
        from jamn_utvardera import matt
        # Felet finns bara i fingrarna. Det gamla tabellfelet rapporterade 0.
        pose=np.zeros((3,127,8));pose[:,:,2]=-100
        target=np.tile([288.,512.],(3,70,1));target[:,KP[6:],0]+=10
        R=dict(idx=[0,1,2],FOC=np.full(3,576.),KP=target)
        result=matt(pose,np.zeros((3,3)),R,dict(bredd=576,hojd=1024),np.zeros((3,10,10)),{}, {'0':True,'1':True,'2':True},{},np.ones(3,bool),3,{},med_iou=False)
        self.assertEqual(int(synliga_par(False).sum()),44)
        self.assertAlmostEqual(result['px_median'],10.)
        self.assertAlmostEqual(result['px_p90'],10.)


class GolvBakåtkompatibilitet(unittest.TestCase):
    def test_tidigare_tillampad_skala_bevaras_aven_med_ny_logg(self):
        import tempfile
        from kor_jamn import hade_golv
        with tempfile.TemporaryDirectory(prefix='golvregel_',dir=HIT/'ut') as td:
            d=Path(td);(d/'fore_jamn').mkdir()
            self.assertFalse(hade_golv(d,'1'))
            np.savez(d/'fore_jamn/sekvens_1.npz',golv_skala=np.array([.85,.85]))
            self.assertTrue(hade_golv(d,'1'))
            np.savez(d/'fore_jamn/sekvens_1.npz',golv_skala=np.ones(2))
            self.assertFalse(hade_golv(d,'1'))


class Omkorningslogg(unittest.TestCase):
    def test_verkliga_stegresultat_loggas_inte_bara_en_summering(self):
        import json, tempfile
        from unittest.mock import patch
        import kor_jamn as kor
        with tempfile.TemporaryDirectory(prefix='steglogg_',dir=HIT/'ut') as td:
            d=Path(td);(d/'meta.json').write_text('{}',encoding='utf-8')
            (d/'tider.json').write_text(json.dumps(dict(sekvens={})),encoding='utf-8')
            with patch.object(kor.IK,'steg_sekvens',return_value={}), patch.object(kor.IK,'steg_varld',return_value=dict(kamerans_vag_m=0)), patch.object(kor.IK,'steg_golv',return_value={}), patch('kontakt.steg_kontakt',return_value={}), patch.object(kor.IK,'logg') as log:
                kor.kor_tagning(d)
            self.assertEqual([c.args[1] for c in log.call_args_list],['sekvens','varld','golv','kontakt','jamn_omkorning'])
            self.assertEqual(log.call_args_list[1].kwargs['kamerans_vag_m'],0)


    def test_slutligt_utsnittsbeslut_loggas_efter_historisk_golvregel(self):
        import json, tempfile
        from unittest.mock import patch
        import kor_jamn as kor
        with tempfile.TemporaryDirectory(prefix='utsnittslogg_',dir=HIT/'ut') as td:
            d=Path(td);(d/'meta.json').write_text('{}',encoding='utf-8')
            (d/'tider.json').write_text(json.dumps(dict(sekvens={})),encoding='utf-8')
            def sequence(*args):
                (d/'utsnitt_1.json').write_text(json.dumps(dict(endast_overkropp=True,orsak='Prov')),encoding='utf-8')
                return {'1':dict(utsnitt=dict(endast_overkropp=True))}
            with patch.object(kor.IK,'steg_sekvens',side_effect=sequence),patch.object(kor.IK,'steg_varld',return_value={}),patch.object(kor.IK,'steg_golv',return_value={}),patch('kontakt.steg_kontakt',return_value={}),patch.object(kor.IK,'logg') as log:
                kor.kor_tagning(d)
            final=json.loads((d/'utsnitt_1.json').read_text(encoding='utf-8'))
            self.assertFalse(final['endast_overkropp'])
            self.assertEqual(log.call_args_list[0].kwargs['1']['utsnitt'],final)


class Matcache(unittest.TestCase):
    def test_cache_ogiltig_vid_fil_kamera_och_stod(self):
        import copy
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='matcache_',dir=HIT/'ut') as td:
            folder=Path(td);file=folder/'sekvens_1.npz';file.write_bytes(b'initial')
            sc=dict(id='s1',ut=[0,1],lokal_start=0,varld=str(folder/'varld.npz'),personer=[dict(id='A',ingest_id='1',rorelse=str(file))])
            p=dict(scener=[sc],kallrutor=[0],kallbild_bredd=576,utdata=dict(bredd=576,hojd=1024),matkamera=dict(nycklar=[dict(lins_mm=36,matris=np.eye(4).tolist())]))
            K._MATT_CACHE.clear()
            with patch.object(K,'_matt_plan_utan_cache',return_value=[dict(matt=1)]) as measure:
                first=K.matt_plan(p);first[0]['matt']=999
                self.assertEqual(K.matt_plan(p),[dict(matt=1)]);self.assertEqual(measure.call_count,1)
                file.write_bytes(b'changed file size');K.matt_plan(p);self.assertEqual(measure.call_count,2)
                p['matkamera']['nycklar'][0]['lins_mm']=40;K.matt_plan(p);self.assertEqual(measure.call_count,3)
                p['scener'][0]['personer'][0]['stod']=dict(hojd_m=.75);K.matt_plan(p);self.assertEqual(measure.call_count,4)
                K.matt_plan(p,False);self.assertEqual(measure.call_count,5)
            K._MATT_CACHE.clear()


if __name__ == '__main__':
    unittest.main()
