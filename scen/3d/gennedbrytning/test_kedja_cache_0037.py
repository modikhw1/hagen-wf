"""0037: cachen per steg. En ändrad konfig ogiltigförklarar bara stegen som läser det ändrade fältet."""
import json, sys, unittest
from pathlib import Path
HIT = Path(__file__).resolve().parent; sys.path.insert(0, str(HIT))
import kedja


class CachePerSteg(unittest.TestCase):
    def setUp(self): self.K = json.loads((HIT / 'kedja/kand-kennysgelato-tagningar/S1.json').read_text(encoding='utf-8')) if (HIT / 'kedja/kand-kennysgelato-tagningar/S1.json').exists() else dict(namn='x')

    def andrade(self, **ny):
        K2 = {**self.K, **ny}; return {s for s in kedja.STEG if kedja.falt_sha(self.K, s) != kedja.falt_sha(K2, s)}

    def test_kamera(self): self.assertEqual(self.andrade(kamera=dict(modell='stativ')), {'kamera'})
    def test_om(self): self.assertEqual(self.andrade(om='ny text'), set())
    def test_scen_flaggor(self): self.assertEqual(self.andrade(scen_flaggor=dict(trag_max=.5)), {'scen1', 'scen2'})
    def test_ankare(self): self.assertEqual(self.andrade(ankare='sate'), {'samspel', 'rot'})
    def test_alla_steg_har_falt(self): self.assertEqual(set(kedja.FALT), set(kedja.STEG))


if __name__ == '__main__': unittest.main()
