"""Regressioner för mallformat, passning och skyddad kroppsmätning."""
import copy
import math
import sys
import unittest
from pathlib import Path
import numpy as np
from gemensamt import HIT,ladda,kontrollmodul
sys.path.insert(0,str(HIT.parent/'ingest'))
import rumsmall as rm
import kroppsstod as ks


class Rumsmall(unittest.TestCase):
    def test_bankens_schema_och_felaktiga_delar(self):
        schema=ladda(rm.BANK/'rumsmall.schema.json');kontroll=kontrollmodul();kontroll.lint(schema,'rumsmall')
        self.assertFalse(kontroll.fel_lista)
        for id in ('restaurang_tva','notan_tva_bord','bar_disk','fiktiv_lokal'):
            m,_=rm.las(id);self.assertFalse(kontroll.validera(m,schema,id,schema))
        m=copy.deepcopy(m);m['delar'][0]['typ']='soffa_som_inte_finns'
        self.assertTrue(kontroll.validera(m,schema,'trasig',schema))
        m['delar'][0]['typ']='golv';m['delar'][0]['matt_m'][0]=-1
        self.assertTrue(kontroll.validera(m,schema,'trasig',schema))

    def test_kand_transform_aterfas_utan_skala(self):
        m,_=rm.las('notan_tva_bord');a=rm.ankare(m);yaw=.73;t=np.array([4.,-2.,.3]);R=rm.rz(yaw)
        for b in a:b['pos_m']=(R@b['pos_m']+t).tolist();b['riktning_rad']+=yaw
        p=rm.passa(m,a)
        self.assertAlmostEqual(p['yaw_rad'],yaw,places=10)
        np.testing.assert_allclose(p['translation_m'],t,atol=1e-10)
        self.assertLess(p['rms_m'],1e-10);self.assertEqual(p['skala'],1)

    def test_fel_ankartyp_anvands_inte(self):
        m,_=rm.las('restaurang_tva');a=rm.ankare(m)
        for b in a:b['typ']='annat'
        with self.assertRaises(ValueError):rm.passa(m,a)

    def kropp(self):
        s=np.load(HIT.parent/'ingest/ut/notan-tagningar/S1/sekvens_1.npz')
        p=ladda(HIT.parent/'ingest/ut/notan-tagningar/plats/plats.json')
        V=np.load(HIT.parent/'ingest/ut/notan-tagningar/S1/varld.npz')
        import plats
        M=np.array(p['tagningar'][0]['till_plats']['matris']);G=plats.gravitation(V['upp']);Q=M[:3,:3]@G@V['kam_R'][30]@plats.F
        T=M[:3,:3]@G@(V['kam_C'][30]+V['kam_R'][30]@s['cam_t'][30])+M[:3,3]
        a=next(x for x in p['rumsmall']['ankare'] if x['id']=='stol_A')
        return s['pose'][30].copy(),Q,T,a

    def test_sittstod_hoft_lar_fotter_och_exakt_overkropp(self):
        p,Q,T,a=self.kropp();ny,r=ks.begransa(p,Q,T,a,False);X=ny[:,:3]/100@Q.T+T
        self.assertAlmostEqual(X[ks.IX['root'],2],a['pos_m'][2]+a['sate_hojd_m']+a['backen_over_sate_m'],places=6)
        for side in 'lr':
            self.assertAlmostEqual(X[ks.IX[side+'_foot'],2],a['pos_m'][2]+a['fotled_over_golv_m'],places=6)
            self.assertAlmostEqual(X[ks.IX[side+'_upleg'],2],X[ks.IX[side+'_lowleg'],2],places=6)
        np.testing.assert_array_equal(ny[34:],p[34:])
        np.testing.assert_array_equal(ny[0],p[0]);self.assertIn('root',r['leder'])
        self.assertTrue(set(r['leder']) <= {ks.NAMN[i] for i in ks.BEN+[ks.IX['root']]})

    def test_synliga_ben_och_saknad_flagga_skyddas_helt(self):
        p,Q,T,a=self.kropp()
        for flag in (True,None):
            ny,r=ks.begransa(p,Q,T,a,flag);np.testing.assert_array_equal(ny,p);self.assertEqual(r['leder'],[])

    def test_stastaende_bevarar_backen_och_overkropp(self):
        p,Q,T,a=self.kropp();a=dict(a,typ='staplats')
        ny,r=ks.begransa(p,Q,T,a,False);X=ny[:,:3]/100@Q.T+T
        np.testing.assert_array_equal(ny[1],p[1]);np.testing.assert_array_equal(ny[34:],p[34:])
        self.assertAlmostEqual(X[ks.IX['l_foot'],2],a['pos_m'][2]+a['fotled_over_golv_m'],places=6)

    def test_okand_saknar_stod_och_renderas_inte(self):
        p=ladda(HIT.parent/'ingest/ut/notan-tagningar/plats/plats.json')
        self.assertEqual([u['person'] for u in p['utelamnade']],['okand_s4_4'])
        self.assertGreater(p['utelamnade'][0]['avstand_m'],p['utelamnade'][0]['tolerans_m'])


if __name__=='__main__':unittest.main()
