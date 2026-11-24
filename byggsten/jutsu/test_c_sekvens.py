import unittest
import numpy as np
from c_sekvens import brus_sigma, J


class SparseNoiseTests(unittest.TestCase):
    def test_dense_matches_existing_estimator(self):
        y = np.random.default_rng(8).normal(size=(90, 2))
        w = np.ones(90)
        np.testing.assert_allclose(brus_sigma(y, w), J.brus_sigma(y, w))

    def test_sparse_noise_does_not_collapse(self):
        y = np.random.default_rng(8).normal(size=(900, 2))
        w = (np.arange(900) % 3 == 0).astype(float)
        self.assertTrue(np.isnan(J.brus_sigma(y, w)).all())
        sigma = brus_sigma(y, w)
        self.assertTrue(np.all((sigma > .7) & (sigma < 1.3)))

    def test_missing_frames_do_not_affect_estimate(self):
        y = np.random.default_rng(8).normal(size=(900, 2))
        w = (np.arange(900) % 3 == 0).astype(float)
        w[451:480] = 0
        expected = brus_sigma(y, w)
        y[w == 0] = np.nan
        np.testing.assert_allclose(brus_sigma(y, w), expected)


if __name__ == '__main__':
    unittest.main()
