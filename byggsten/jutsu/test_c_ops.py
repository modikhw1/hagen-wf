import unittest
import numpy as np
from c_ops import export_frames


class VisibilityTests(unittest.TestCase):
    def test_identity_gap_remains_hidden(self):
        track = {str(f): [] for f in list(range(451))+list(range(480,819))}
        frames = export_frames({'inom': np.ones(819, bool)}, track)
        self.assertFalse(np.any((frames >= 451) & (frames < 480)))

    def test_last_frame_and_short_detection_gap(self):
        support = np.zeros(819, bool); support[21:814] = True
        track = {str(f): [] for f in list(range(21,814))+[817,818]}
        frames = export_frames({'inom': support}, track)
        self.assertTrue(all(f in frames for f in range(810,819)))
        self.assertNotIn(20, frames)

    def test_no_unbounded_extrapolation(self):
        support = np.zeros(100, bool); support[10:50] = True
        frames = export_frames({'inom': support}, {str(f): [] for f in range(100)})
        self.assertEqual((frames[0], frames[-1]), (5,54))


if __name__ == '__main__':
    unittest.main()
