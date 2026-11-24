"""Låt jämn-omkörning läsa det verkliga gamla golvutfallet, inte bara en loggnyckel."""
from prop_filer import andra

def code(s):
    i=s.index('\ndef sakra(ut):')
    s=s[:i]+'''
def hade_golv(ut, pid):
    """En faktisk tidigare golvskala är starkare evidens än formatet i tider.json."""
    f = Path(ut) / 'fore_jamn' / f'sekvens_{pid}.npz'
    if not f.exists(): return False
    with np.load(f) as old:
        return 'golv_skala' in old and bool(np.any(old['golv_skala'] != 1.0))

'''+s[i:]
    s=s.replace("if 'utsnitt' not in gammal.get(u.stem[8:], {}):", "if 'utsnitt' not in gammal.get(u.stem[8:], {}) or hade_golv(ut, u.stem[8:]):")
    s=s.replace('Äldre ingest utan regeln om endast överkropp (före 10 nov): golv och kontakt körs som 9 nov.', 'Tidigare körning använde golv, eller saknar utsnittsbeslut. Golv och kontakt bevaras för samma 3D-registrering; ingen ny golvmätning påstås.')
    return s
andra('scen/3d/ingest/kor_jamn.py',code)
andra('scen/3d/kontrakt/test_kroppmatt.py',lambda s:s.replace("class Matcache(unittest.TestCase):",'''class GolvBakåtkompatibilitet(unittest.TestCase):
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


class Matcache(unittest.TestCase):'''))
andra('scen/3d/kontrakt/engang/prop_rendera.py',lambda s:s.replace("'--kalla','kalla_prop.json'", "'--kalla',('kalla_prop_golv.json' if clip=='notan' else 'kalla_prop.json')"))
