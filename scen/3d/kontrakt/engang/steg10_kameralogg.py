"""Rätta faktisk omkörningsloggning och kontrollera den utan ingest."""
from steg10_filer import andra
from steg10_koppla import ersatt


def code(s):
    s=ersatt(s,"    r['sekvens'] = IK.steg_sekvens(ut, M); (ut / 'sekvens.klar').write_text('ok')",
        "    ts = time.perf_counter()\n    r['sekvens'] = IK.steg_sekvens(ut, M); (ut / 'sekvens.klar').write_text('ok')\n    IK.logg(ut, 'sekvens', time.perf_counter()-ts, **r['sekvens'])")
    s=ersatt(s,"    r['varld'] = IK.steg_varld(ut, M)\n    r['golv'] = IK.steg_golv(ut, M); (ut / 'golv.klar').write_text('ok')",
        "    ts = time.perf_counter()\n    r['varld'] = IK.steg_varld(ut, M)\n    IK.logg(ut, 'varld', time.perf_counter()-ts, **r['varld'])\n    ts = time.perf_counter()\n    r['golv'] = IK.steg_golv(ut, M); (ut / 'golv.klar').write_text('ok')\n    IK.logg(ut, 'golv', time.perf_counter()-ts, **r['golv'])")
    s=ersatt(s,"    r['kontakt'] = steg_kontakt(ut, M); (ut / 'kontakt.klar').write_text('ok')",
        "    ts = time.perf_counter()\n    r['kontakt'] = steg_kontakt(ut, M); (ut / 'kontakt.klar').write_text('ok')\n    IK.logg(ut, 'kontakt', time.perf_counter()-ts, **r['kontakt'])")
    return s
andra('scen/3d/ingest/kor_jamn.py',code)


def tests(s):
    marker='class Matcache(unittest.TestCase):'
    return ersatt(s,marker,'''class Omkorningslogg(unittest.TestCase):
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


''' + marker)
andra('scen/3d/kontrakt/test_kroppmatt.py',tests)
