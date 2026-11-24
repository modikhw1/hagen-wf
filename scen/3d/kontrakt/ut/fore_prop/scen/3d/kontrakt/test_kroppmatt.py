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


if __name__ == '__main__':
    unittest.main()
