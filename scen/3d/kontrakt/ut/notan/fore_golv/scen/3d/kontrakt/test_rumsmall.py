"""Regressioner för mallformat, passning och skyddad kroppsmätning."""
import copy
import math
import sys
import unittest
import tempfile
from pathlib import Path
import numpy as np
from gemensamt import HIT,ladda,kontrollmodul
sys.path.insert(0,str(HIT.parent/'ingest'))
import rumsmall as rm
import trostod as ks
import trohet as tr


class Bildtrohet(unittest.TestCase):
    def syntetisk(self,folder):
        rng=np.random.default_rng(7);pose=np.zeros((1,127,8));pose[0,:,:3]=rng.normal(size=(127,3))*15
        pose[0,:,6]=1;cam=np.array([[0.,0.,3.]])
        rorelse=folder/'sekvens_1.npz';varld=folder/'varld.npz'
        np.savez(rorelse,pose=pose,cam_t=cam,inom=[True],ben_synliga=[True])
        np.savez(varld,kam_R=np.eye(3)[None],kam_C=np.zeros((1,3)),upp=[0.,0.,1.])
        key=dict(matris=np.diag([1.,-1.,-1.,1.]).tolist(),lins_mm=900*36/576)
        p=dict(kallbild_bredd=576,kallbild_hojd=1024,kallrutor=[0],utdata=dict(bredd=576,hojd=1024),
               renderkamera=dict(nycklar=[key]),scener=[dict(id='kand',ut=[0,1],lokal_start=0,varld=str(varld),
                                                           personer=[dict(id='1',rorelse=str(rorelse))])])
        uv=tr.projicera(pose[0,:,:3]/100@tr.F+cam[0],key,576,1024)
        target=np.zeros((70,2));target[tr.KP]=uv[tr.LED]
        d=folder/'kropp/1';d.mkdir(parents=True)
        np.savez(d/'0000.npz',pred_keypoints_2d=target,bbox=[0,100,576,900])
        return p

    def test_kand_kamera_ger_nollfel_och_fel_fokal_flaggas(self):
        with tempfile.TemporaryDirectory(dir=HIT/'ut/notan') as name:
            p=self.syntetisk(Path(name));r=tr.mat(p)['personer'][0]
            self.assertLess(r['p90_px'],1e-10);self.assertAlmostEqual(r['bbox_iou'],1.);self.assertFalse(r['flaggad'])
            p['renderkamera']['nycklar'][0]['lins_mm']*=2
            r=tr.mat(p)['personer'][0];self.assertGreater(r['median_px'],20);self.assertTrue(r['flaggad'])


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
        np.testing.assert_array_equal(ny[1],p[1])
        for side in 'lr':
            self.assertGreaterEqual(X[ks.IX[side+'_foot'],2],a['pos_m'][2]+ks.SULA_M-1e-7)
            self.assertAlmostEqual(X[ks.IX[side+'_upleg'],2],X[ks.IX[side+'_lowleg'],2],places=6)
        np.testing.assert_array_equal(ny[34:],p[34:])
        np.testing.assert_array_equal(ny[0],p[0]);self.assertNotIn('root',r['leder'])
        self.assertTrue(set(r['leder']) <= {ks.NAMN[i] for i in ks.BEN})

    def test_synliga_ben_och_saknad_flagga_skyddas_helt(self):
        p,Q,T,a=self.kropp()
        for flag in (True,None):
            ny,r=ks.begransa(p,Q,T,a,flag);np.testing.assert_array_equal(ny,p);self.assertEqual(r['leder'],[])

    def test_stastaende_bevarar_backen_och_overkropp(self):
        p,Q,T,a=self.kropp();a=dict(a,typ='staplats')
        ny,r=ks.begransa(p,Q,T,a,False);X=ny[:,:3]/100@Q.T+T
        np.testing.assert_array_equal(ny[1],p[1]);np.testing.assert_array_equal(ny[34:],p[34:])
        self.assertGreaterEqual(r['sula_lagst_z_m'],a['pos_m'][2])
        self.assertLess(r['sula_lagst_z_m']-a['pos_m'][2],.001)

    def test_fasta_personmatt_i_alla_dolda_ben_utan_strackning(self):
        p,Q,T,a=self.kropp();lengths=ks.matt(p[None])
        for typ in ('sate','staplats'):
            ny,r=ks.begransa(p,Q,T,dict(a,typ=typ),False,lengths)
            x=ny[:,:3]/100
            for j in ks.BEN:
                self.assertAlmostEqual(np.linalg.norm(x[j]-x[ks.FORALDER[j]]),lengths[j],delta=1e-7)
            self.assertLess(r['benlangd_maxfel_m'],1e-7)
            np.testing.assert_array_equal(ny[34:],p[34:])

    def test_kort_vad_hanger_och_sulans_enkla_golvgrans(self):
        p,Q,T,a=self.kropp();lengths=ks.matt(p[None])
        lengths[ks.IX['l_foot']]=.10;lengths[ks.IX['r_foot']]=.10
        ny,r=ks.begransa(p,Q,T,a,False,lengths)
        self.assertTrue(all(b['val']=='foten hänger' for b in r['ben']))
        self.assertTrue(all(z-ks.SULA_M>=a['pos_m'][2]-1e-7 for z in r['fotled_z_m']))

    def test_sitshojd_anpassas_inom_tillatet_intervall(self):
        for hip in (.1,.65,1.8):
            fit=ks.sitt_hojd(hip)
            self.assertGreaterEqual(fit['hojd_m'],ks.SATE_INTERVALL_M[0])
            self.assertLessEqual(fit['hojd_m'],ks.SATE_INTERVALL_M[1])
        self.assertAlmostEqual(ks.sitt_hojd(.65)['hojd_m'],.54)

    def test_alla_notans_rutor_har_fasta_ben_skyddad_overkropp_och_sula_over_golv(self):
        from kompilera import kompilera
        p=kompilera(HIT/'exempel/notan/kalla.json',HIT/'ut/notan/tro_tom/regi.json')
        for d in p['scener']:
            for pm in d['personer']:
                s=np.load(pm['rorelse']);v=np.load(d['varld']);m=np.array(d['till_plats']);g=m[:3,:3]@tr.gravitation(v)
                lengths=pm['benlangder_m']
                for f in range(d['lokal_start'],d['lokal_start']+d['ut'][1]-d['ut'][0]):
                    q=g@v['kam_R'][f]@tr.F;t=g@(v['kam_C'][f]+v['kam_R'][f]@s['cam_t'][f])+m[:3,3]
                    ny,r=ks.begransa(s['pose'][f],q,t,pm['stod'],s['ben_synliga'][f],lengths)
                    np.testing.assert_array_equal(ny[34:],s['pose'][f,34:])
                    self.assertLess(r['benlangd_maxfel_m'],1e-7)
                    self.assertGreaterEqual(r['sula_lagst_z_m'],pm['stod']['pos_m'][2]-1e-7)
                    if pm['stod']['typ']=='staplats':self.assertLess(r['sula_lagst_z_m'],.001)

    def test_okand_saknar_stod_och_renderas_inte(self):
        p=ladda(HIT.parent/'ingest/ut/notan-tagningar/plats/plats.json')
        self.assertEqual([u['person'] for u in p['utelamnade']],['okand_s4_4'])
        self.assertGreater(p['utelamnade'][0]['avstand_m'],p['utelamnade'][0]['tolerans_m'])


if __name__=='__main__':unittest.main()
