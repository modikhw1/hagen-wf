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
            self.assertGreater(X[ks.IX[side+'_foot'],2],a['pos_m'][2])
            self.assertLessEqual(X[ks.IX[side+'_lowleg'],2],X[ks.IX[side+'_upleg'],2]+1e-6)
        np.testing.assert_array_equal(ny[34:],p[34:])
        self.assertGreaterEqual(r['sula_lagst_z_m'],a['pos_m'][2]-1e-7)
        self.assertLess(r['sula_lagst_z_m']-a['pos_m'][2],.001)
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
        lengths[ks.IX['l_lowleg']]=.10;lengths[ks.IX['r_lowleg']]=.10
        ny,r=ks.begransa(p,Q,T,a,False,lengths)
        self.assertTrue(all(b['val']=='foten hänger' for b in r['ben']))
        self.assertTrue(all(z-ks.SULA_M>=a['pos_m'][2]-1e-7 for z in r['fotled_z_m']))

    def test_sitshojd_anpassas_inom_tillatet_intervall(self):
        for hip in (.1,.65,1.8):
            fit=ks.sitt_hojd(hip)
            self.assertGreaterEqual(fit['hojd_m'],ks.SATE_INTERVALL_M[0])
            self.assertLessEqual(fit['hojd_m'],ks.SATE_INTERVALL_M[1])
        self.assertAlmostEqual(ks.sitt_hojd(.65)['hojd_m'],.48)

    def test_deklarerad_sitthojd_ar_bindande_och_ersatter_stolsprioren(self):
        fit=ks.sitt_hojd(.85,.085,deklarerat=.75)        # barstol: 0,75 m ligger utanför stolsprioren 43–48 cm
        self.assertEqual(fit['hojd_m'],.75);self.assertTrue(fit['bunden_av_deklaration']);self.assertAlmostEqual(fit['lasrest_m'],.015)
        iv=ks.sitt_hojd(.85,.085,deklarerat=[.70,.80])    # intervall: läsningen (0,765) ryms och används
        self.assertAlmostEqual(iv['hojd_m'],.765);self.assertTrue(iv['inom_intervall'])
        self.assertEqual(ks.sitt_hojd(1.5,.085,deklarerat=[.70,.80])['hojd_m'],.80)   # utanför intervallet: klipps mot kanten
        with self.assertRaises(ValueError):ks.sitt_hojd(.85,deklarerat=[.8,.7])
        self.assertEqual(ks.sitt_hojd(.85,.085)['hojd_m'],.48)                      # utan deklaration: prioren som förut
        self.assertNotIn('bunden_av_deklaration',ks.sitt_hojd(.85,.085))

    def test_deklarationskontroll_flaggar_avvikelse_och_tiger_utan_deklaration(self):
        import deklarationskontroll as dk
        plan=dict(plats=[dict(id='p',golv_hojd_m=.05,deklarerat=dict(golv_hojd_m=0.,sitthojd_m=dict(stol=.75),kamerahojd_m=dict(S1=[1.3,1.5])),
                              rumsmall=dict(ankare=[dict(id='stol',typ='sate',sate_hojd_m=.455)]))],
                  kvalitet=dict(hojdpassning=[]),matning=dict(platser=[dict(id='p',registreringar=[dict(tagning='S1',scen='s1')],golv={})]),
                  scener=[dict(id='s1',ut=[0,2],plats_id='p')],matkamera=dict(nycklar=[dict(matris=[[0]*3+[0],[0]*3+[0],[0]*3+[1.0],[0,0,0,1]])]*2))
        r=dk.kontrollera(plan);av={x['typ']:x for x in r['avvikelser']}
        self.assertEqual(r['status'],'avviker');self.assertEqual(set(av),{'golv','sitthojd','kamerahojd'})
        self.assertAlmostEqual(av['sitthojd']['avvikelse_m'],-.295);self.assertAlmostEqual(av['kamerahojd']['avvikelse_m'],-.35)   # 1,0-0,05 = 0,95 mot 1,3
        self.assertIsNone(dk.kontrollera(dict(plats=[dict(id='p',golv_hojd_m=0.)])))

    def test_flerrollsregistrering_redovisas_per_roll_och_varnar_over_troskeln(self):
        import deklarationskontroll as dk
        def plan(rest):
            rr=dict(metod='m',laspar_avstand_m=1.5,deklarerat_avstand_m=1.3,avstandsfel_m=.2,
                    roller=[dict(roll=r,plats='pl_'+r,deklarerad_pos_m=[0,0],last_pos_m=[0,rest],restfel_m=rest,blick_rest_grader=3.) for r in 'AB'])
            return dict(plats=[dict(id='p',golv_hojd_m=0.,deklarerat=dict(golv_hojd_m=0.))],kvalitet=dict(hojdpassning=[]),
                        matning=dict(platser=[dict(id='p',registreringar=[dict(tagning='S4',scen='s4',roller_registrering=rr),dict(tagning='S1',scen='s1')],golv={})]),scener=[],matkamera=dict(scener=[]))
        r=dk.kontrollera(plan(.2))['registrering']
        self.assertEqual([x['roll'] for x in r['roller']],['A','B']);self.assertEqual(len(r['over_troskel']),2);self.assertEqual(r['troskel_m'],dk.REGISTRERING_VARNING_M)
        self.assertEqual(dk.kontrollera(plan(.1))['registrering']['over_troskel'],[])
        self.assertNotIn('registrering',dk.kontrollera(dict(plan(.1),matning=dict(platser=[dict(id='p',registreringar=[dict(tagning='S1',scen='s1')],golv={})])))) # en roll: inget fält

    def test_alla_notans_rutor_har_fasta_ben_skyddad_overkropp_och_sula_over_golv(self):
        from kompilera import kompilera
        with tempfile.TemporaryDirectory(dir=HIT/'ut/notan') as name:
            from gemensamt import skriv
            r=ladda(HIT/'exempel/notan/regi.json');r['edits']=[];rf=Path(name)/'regi.json';skriv(rf,r)
            p=kompilera(HIT/'exempel/notan/kalla_jamn.json',rf, snabb=True)
        for d in p['scener']:
            for pm in d['personer']:
                s=np.load(pm['rorelse']);v=np.load(d['varld']);m=np.array(d['till_plats']);g=m[:3,:3]@tr.gravitation(v)
                lengths=pm['benlangder_m']
                for f in range(d['lokal_start'],d['lokal_start']+d['ut'][1]-d['ut'][0]):
                    q=g@v['kam_R'][f]@tr.F;t=g@(v['kam_C'][f]+v['kam_R'][f]@s['cam_t'][f])+m[:3,3]
                    ny,r=ks.begransa(s['pose'][f],q,t,pm['stod'],s['ben_synliga'][f],lengths,skyddade_knan=pm.get('skyddade_knan',{}).get(str(f)))
                    np.testing.assert_array_equal(ny[34:],s['pose'][f,34:])
                    self.assertLess(r['benlangd_maxfel_m'],1e-7)
                    self.assertGreaterEqual(r['sula_lagst_z_m'],pm['stod']['pos_m'][2]-1e-7)
                    if pm['stod']['typ']=='staplats':self.assertLess(r['sula_lagst_z_m'],.001)

    def test_okand_saknar_stod_och_renderas_inte(self):
        p=ladda(HIT.parent/'ingest/ut/notan-tagningar/plats/plats.json')
        self.assertEqual([u['person'] for u in p['utelamnade']],['okand_s4_4'])
        self.assertGreater(p['utelamnade'][0]['avstand_m'],p['utelamnade'][0]['tolerans_m'])


class GolvOchSkymning(unittest.TestCase):
    def test_dold_fot_regeln_slar_till_bara_for_notan_s4_c(self):
        from kompilera import kompilera
        from gemensamt import skriv
        with tempfile.TemporaryDirectory(dir=HIT/'ut/notan') as name:
            r=ladda(HIT/'exempel/notan/regi.json');r['edits']=[];rf=Path(name)/'regi.json';skriv(rf,r)
            plan=kompilera(HIT/'exempel/notan/kalla_jamn.json',rf,snabb=True)
        decisions=[p['dolda_fotter'] for p in plan['matning']['personer'] if p.get('dolda_fotter')]
        self.assertEqual([(d['scen'],d['person']) for d in decisions],[('s4','C')])
        self.assertEqual(decisions[0]['status'],'antagen');self.assertTrue(decisions[0]['tillampad'])
        self.assertLess(abs(decisions[0]['sula_efter_m']),.001)

    def test_dold_fot_regeln_slar_inte_till_nar_en_fot_syns(self):
        from dolda_fotter import berattigad
        source=[dict(cue='annan fot')]
        self.assertFalse(berattigad(True,source));self.assertTrue(berattigad(False,source))
        self.assertFalse(berattigad(False,[]))

    def test_dold_fot_faktorn_begransas_till_atta_procent(self):
        from dolda_fotter import begransa_faktor,GRANS
        self.assertEqual(GRANS,(.92,1.08))
        self.assertAlmostEqual(begransa_faktor(1.2),1.08)
        self.assertAlmostEqual(begransa_faktor(.5),.92)

    def test_likformig_skala_kring_kameran_bevarar_projektionen(self):
        from metrisk import normalisera
        rng=np.random.default_rng(19);pose=np.zeros((3,127,8));pose[...,:3]=rng.normal(size=(3,127,3))*20
        pose[...,6]=1.;cam=np.array([[.2,-.1,3.],[.1,.05,2.7],[-.1,.2,3.2]])
        raw=dict(pose=pose,cam_t=cam,inom=np.ones(3,bool))
        scaled=normalisera(raw,dict(tillampad=True,faktor=1.08))
        before=pose[...,:3]/100+cam[:,None,:];after=scaled['pose'][...,:3]/100+scaled['cam_t'][:,None,:]
        np.testing.assert_allclose(before[...,:2]/before[...,2:],after[...,:2]/after[...,2:],atol=2e-15)

    def test_overensstammande_cues_ar_uppmatta(self):
        from golvmatning import cue,kombinera
        r=kombinera([cue('fot',.20,.02,'fotter',True),cue('djup',.22,.03,'djup',True)])
        # GOLV2 punkt 3: starkaste familjen (fötter) väljer; förr median mellan familjer (0,21).
        self.assertEqual(r['status'],'uppmatt');self.assertAlmostEqual(r['varde_m'],.20)
        self.assertFalse(r['konflikt'])

    def test_planterad_avvikare_avvisas_och_redovisas(self):
        from golvmatning import cue,kombinera
        r=kombinera([cue('fot',.20,.02,'fotter',True),cue('djup',.22,.03,'djup',True),cue('fel',1.5,.01,'bord')])
        # GOLV2 punkt 3: starkaste familjen (fötter) väljer; förr median mellan familjer (0,21).
        self.assertEqual(r['status'],'uppmatt');self.assertAlmostEqual(r['varde_m'],.20)
        self.assertTrue(r['konflikt']);self.assertFalse(r['cues'][2]['anvand'])
        self.assertIn('avvikare',r['cues'][2]['beslut'])

    def test_enbart_kameraprior_ar_antagen(self):
        from golvmatning import cue,kombinera
        r=kombinera([cue('kamera',-1.45,.25,'kamera',False,prior=True)])
        self.assertEqual(r['status'],'antagen');self.assertIn('Endast kamerahöjd',r['orsak'])

    def test_kameraprior_utgar_fran_kameran_inte_tidigare_golv(self):
        from golvmatning import undersok
        t=dict(id='ensam',golv=dict(hojd_m=-1.9),personer={},rum=dict(floor={}),
               V=dict(kam_C=np.array([[0.,0.,.2]])),G=np.eye(3))
        M=np.eye(4);M[2,3]=1.7
        r=undersok([t],{'ensam':dict(M=M)},{})
        self.assertAlmostEqual(r['pool']['varde_m'],.45)
        self.assertEqual(r['pool']['status'],'antagen')

    def test_fotter_nar_golv_med_fasta_ben_och_skyddad_overkropp(self):
        p,Q,T,a=Rumsmall().kropp();lengths=ks.matt(p[None]);floor=a['pos_m'][2]
        ny,r=ks.begransa(p,Q,T,a,False,lengths)
        self.assertLess(abs(r['sula_lagst_z_m']-floor),.001)
        for j in ks.BEN:self.assertAlmostEqual(np.linalg.norm(ny[j,:3]-ny[ks.FORALDER[j],:3])/100,lengths[j],delta=1e-7)
        np.testing.assert_array_equal(ny[[i for i in range(127) if i not in ks.BEN]],p[[i for i in range(127) if i not in ks.BEN]])

    def test_syntetisk_lada_skymmer_bara_fore_kroppen(self):
        from skymning import konflikt
        key=dict(matris=np.eye(4).tolist(),lins_mm=36.)
        uv=np.array([[288.,512.],[575.,0.]])
        obj=dict(id='bord',pos_m=[0,0,-2],rotation_rad=[0,0,.2],matt_m=[1,1,.1])
        hit=konflikt(uv,[3,3],key,576,1024,[obj])['bord']
        np.testing.assert_array_equal(hit,[True,False])
        obj['pos_m'][2]=-4
        self.assertFalse(konflikt(uv,[3,3],key,576,1024,[obj])['bord'].any())

    def test_synliga_knan_och_lar_skyddas_med_dolda_fotter(self):
        p,Q,T,a=Rumsmall().kropp();lengths=ks.matt(p[None])
        ny,r=ks.begransa(p,Q,T,a,False,lengths,skyddade_knan=[True,True])
        for side in 'lr':
            for name in ('upleg','lowleg'):
                np.testing.assert_allclose(ny[ks.IX[side+'_'+name],:3],p[ks.IX[side+'_'+name],:3],atol=1e-10)
            np.testing.assert_array_equal(ny[ks.IX[side+'_upleg']],p[ks.IX[side+'_upleg']])
        self.assertLess(r['benlangd_maxfel_m'],1e-7)


class Mobelintervall(unittest.TestCase):
    """Bord och diskar som deklarerat intervall: lösaren väljer ett värde för hela klippet; tal är hårda; deklarerad bordshöjd går före bordsprioren."""

    @staticmethod
    def _varld(hoppa_scen=()):
        """Kamera 5 m framför en person på (0,0), 1 m över golvet. Personens bäcken (kroppsdel 2) är 60 maskprov på höjden 0,3 m. Returnerar (forb, nyckel)."""
        w,h=1000,800;lins=36*1.2/36*36/1.2   # lins_mm=36 -> brännvidd = w px
        M=np.eye(4);M[:3,:3]=np.array([[1,0,0],[0,0,-1],[0,1,0.]]);M[:3,3]=[0,-5,1]
        key=dict(matris=M.tolist(),lins_mm=36.)
        f=36/36*w;rng=np.random.RandomState(0)
        X=np.c_[rng.uniform(-.1,.1,60),np.zeros(60),rng.uniform(.25,.35,60)]
        loc=(X-M[:3,3])@M[:3,:3]                       # kameralokalt: x höger, y upp, z bakåt
        uv=np.c_[w/2+f*loc[:,0]/-loc[:,2],h/2-f*loc[:,1]/-loc[:,2]]
        P=dict(uv=uv,dep=np.full(60,5.),delar=np.full(60,2),qh=np.zeros((0,2)),qd=np.zeros(0))
        scener=[dict(id=s,rutor=[(u,key,[P]) for u in (0,3,6)]) for s in ('s1','s2')]
        return (w,h,scener)

    def _del(self,hojd,djup=.6):
        return dict(id='disk',typ='bord',pos_m=[0.,-2.,0.],matt_m=[2.,djup,hojd],yaw_rad=0.,material=dict(farg='#333',ben_farg='#222'),ankare=[])

    def _plan(self,d):
        import mobelintervall as mi
        return dict(objekt=list(mi._lador(d).values()),kallrutor=list(range(9)))

    def test_losaren_sanker_disken_tills_scenerna_klarar_sig_och_redovisar(self):
        import mobelintervall as mi
        from unittest.mock import patch
        d=self._del(.6);plan=self._plan(d)       # skivan (4,5 cm tjock, 0,6 m djup) 3 m framför kameran på 1,0 m: siktlinjen mot bäckenet (0,3 m) går på 0,54–0,62 m genom skivdjupet, alltså träffar skivor med överkant 0,54–0,67 m
        pl=dict(p=dict(rumsmall=dict(delar=[d],passning=None),deklarerat=dict(mobler=dict(disk=dict(hojd_m=[.3,1.1],langs_x_m=2.0)))))
        with patch.object(mi,'_forbered',return_value=self._varld()):
            post,=mi.losa(plan,pl)
        self.assertEqual(post['fore']['flaggade_scener'],['s1','s2']);self.assertEqual(post['efter']['flaggade_scener'],[])
        v=post['parametrar']['hojd_m'];self.assertFalse(.538<v['valt']<.667);self.assertGreaterEqual(v['valt'],.3);self.assertEqual(v['deklarerat'],[.3,1.1])
        self.assertEqual(post['atgard'],'justerad');self.assertEqual(post['hardvarden'],{'langs_x_m':2.0})
        topp=max(o['pos_m'][2]+o['matt_m'][2]/2 for o in plan['objekt']);self.assertAlmostEqual(topp,v['valt'],places=6)   # planens lådor har det valda måttet
        for o in plan['objekt']:self.assertEqual(o['id'].split(':')[0],'disk')

    def test_gransen_nadd_och_oloslig_konflikt_redovisas(self):
        import mobelintervall as mi
        from unittest.mock import patch
        d=self._del(.6);plan=self._plan(d)
        pl=dict(p=dict(rumsmall=dict(delar=[d],passning=None),deklarerat=dict(mobler=dict(disk=dict(hojd_m=[.55,.62])))))   # hela intervallet ligger i träffbandet
        with patch.object(mi,'_forbered',return_value=self._varld()):
            post,=mi.losa(plan,pl)
        self.assertEqual(post['efter']['flaggade_scener'],['s1','s2']);self.assertIn(post['parametrar']['hojd_m']['grans_nadd'],('min','max'))
        self.assertEqual(post['granser_nadda'],['hojd_m'])

    def test_hart_varde_och_oflaggad_mobel_rors_inte(self):
        import mobelintervall as mi
        from unittest.mock import patch
        d=self._del(.6);plan=self._plan(d);fore=copy.deepcopy(plan['objekt'])
        hart=dict(p=dict(rumsmall=dict(delar=[d],passning=None),deklarerat=dict(mobler=dict(disk=dict(hojd_m=.6,langs_y_m=[.6,.6])))))   # flaggad men tal och smalt intervall: hårt, inget att välja
        with patch.object(mi,'_forbered',return_value=self._varld()):
            self.assertEqual(mi.losa(plan,hart),[])
        self.assertEqual(plan['objekt'],fore)
        d2=self._del(.4);plan2=self._plan(d2);fore2=copy.deepcopy(plan2['objekt'])   # 0,4 m: utanför träffbandet, ingen konflikt, alltså ingen ändring trots intervall
        fri=dict(p=dict(rumsmall=dict(delar=[d2],passning=None),deklarerat=dict(mobler=dict(disk=dict(hojd_m=[.3,.9])))))
        with patch.object(mi,'_forbered',return_value=self._varld()):
            post,=mi.losa(plan2,fri)
        self.assertEqual(post['atgard'],'oförändrad');self.assertEqual(plan2['objekt'],fore2);self.assertEqual(post['efter']['flaggade_scener'],[])

    def test_mittpunktens_forskjutning_vrids_in_i_platsens_ram(self):
        import mobelintervall as mi
        d=self._del(.9);mitt=dict(mitt_x_m=0.,mitt_y_m=.65)
        y=mi._tillampa(d,dict(mitt_y_m=.85),mitt,math.pi/2)      # 0,2 m framåt i deklarationens +Y; platsramen är vriden 90 grader: blir −0,2 i X
        self.assertAlmostEqual(y['pos_m'][0],-.2);self.assertAlmostEqual(y['pos_m'][1],-2.)
        self.assertEqual(mi._tillampa(d,dict(hojd_m=.7,langs_y_m=.8),mitt,0.)['matt_m'],[2.,.8,.7])
        self.assertEqual(d['matt_m'],[2.,.6,.9])                 # originalet orört
        self.assertEqual(sorted(mi.fria_parametrar(dict(hojd_m=[.9,1.1],langs_x_m=2.,langs_y_m=[.5,.5],mitt_y_m=[.5,.8]))),['hojd_m','mitt_y_m'])
        with self.assertRaises(ValueError):mi.fria_parametrar(dict(hojd_m=[1.1,.9]))

    def test_benen_foljer_nya_matt_aven_nar_deras_id_andras(self):
        import mobelintervall as mi
        from unittest.mock import patch
        d=self._del(.6);plan=self._plan(d)
        pl=dict(p=dict(rumsmall=dict(delar=[d],passning=None),deklarerat=dict(mobler=dict(disk=dict(langs_y_m=[.6,1.0])))))
        fejk=lambda forb,objekt,n:[dict(scen='s1',andel=0. if objekt[0]['matt_m'][1]>=.9 else .5,flaggad=objekt[0]['matt_m'][1]<.9,flaggade_kroppsdelar=[],ockluderade_prov=0,synliga_maskprov=1)]
        with patch.object(mi,'_forbered',return_value=None),patch.object(mi,'_mat',side_effect=fejk):
            post,=mi.losa(plan,pl)
        dj=post['parametrar']['langs_y_m']['valt'];self.assertGreaterEqual(dj,.9)
        skiva=next(o for o in plan['objekt'] if o['id']=='disk');self.assertAlmostEqual(skiva['matt_m'][1],dj)
        for o in plan['objekt']:
            if ':ben:' in o['id']:self.assertAlmostEqual(abs(o['pos_m'][1]-skiva['pos_m'][1]),dj/2-.055,places=6)

    def test_deklarerad_bordshojd_gar_fore_bordsprioren(self):
        import tropassning as tp
        self.assertEqual(tp.bord_hojd(.70)[0],tp.BORD_INTERVALL_M[0]);self.assertEqual(tp.bord_hojd(.70)[2],'prior')     # utan deklaration: prioren som förut
        self.assertEqual(tp.bord_hojd(.70,[.66,.74]),(.70,[.66,.74],'deklarerad'))                                       # intervallet släpper igenom 0,70 trots att prioren hade klämt det till 0,72
        self.assertEqual(tp.bord_hojd(.70,.66)[0],.66)                                                                   # tal: hårt värde
        self.assertEqual(tp.bord_hojd(.9,[.66,.74])[0],.74)


class Vaggar(unittest.TestCase):
    """kontrakt/vaggar.py: generade väggar vidgas till kamerorna, hårda väggar flyttas inte, kontrollen mäter slutplanens geometri."""
    def _plan(self,kamera_xy,hard=None,deklarerat=True):
        import deklaration_till_hand as dh
        P=dict(stol_A=dict(typ='sits',roll='A',pos_m=[0,0,0],blick_grader=90,sitthojd_m=.75),
               staplats_B=dict(typ='staplats',roll='B',pos_m=[0,1.7,0],blick_grader=-90),
               disk=dict(typ='bord',mitt_m=[0,.7,0],storlek_m=dict(langs_x=1.0,langs_y=.65,hojd=1.0)))
        D=dict(schema_version='deklaration/0.7',datum='2026-11-12',klipp='prov',platser=P,vaggar=hard or {})
        mall=dh.rumsmall(D);objekt=rm.byggobjekt(mall)
        for o in objekt:o['synlig_ut']=[0,3]
        plats=dict(id='p',golv_hojd_m=0.,ankare=rm.ankare(mall),objekt=[o['id'] for o in objekt],scener=['s1'],rumsmall=dict(delar=copy.deepcopy(mall['delar']),passning=dict(yaw_rad=0.),ankare=rm.ankare(mall)))
        if deklarerat:
            plats['deklarerat']=dict(golv_hojd_m=0.)
            if hard:plats['deklarerat']['vaggar']={('vagg_bak' if k=='bak' else 'vagg_sida'):v for k,v in hard.items()}
        M=np.eye(4);M[:3,3]=[kamera_xy[0],kamera_xy[1],1.4];M[:3,:3]=np.array([[0,0,-1],[-1,0,0],[0,1,0]],float)   # blickar mot -X
        return dict(objekt=objekt,plats=[plats],kallrutor=[0,1,2],renderkamera=dict(nycklar=[dict(matris=M.tolist())]*3),varningar=[],kvalitet={},
                    scener=[dict(id='s1',ut=[0,3],plats_id='p',personer=[dict(id='A',ankare='stol_A',stod=dict(pos_m=[0.,0.,0.])),dict(id='B',ankare='staplats_B')])])
    def _vagg(self,plan,i):return next(o for o in plan['objekt'] if o['id']==i)
    def test_kamera_bakom_sidovaggen_flyttar_vaggen_utanfor_kameran_och_kontrollen_blir_ren(self):
        import vaggar
        plan=self._plan([2.4,.5]);fore_sida=self._vagg(plan,'vagg_sida')['pos_m'][0]
        ut,_=vaggar.kontrollera(plan);self.assertTrue(ut[0]['flaggad']);self.assertEqual(ut[0]['blockerande_vaggar'],['vagg_sida'])   # före: kameran utanför, vägg i sikten
        r=vaggar.kor(plan);efter=self._vagg(plan,'vagg_sida')['pos_m'][0]
        self.assertGreaterEqual(efter,2.4+vaggar.KAMERA_MARGINAL_M);self.assertGreater(efter,fore_sida)
        self.assertFalse(r['kontroll'][0]['flaggad']);self.assertEqual(r['flaggade_scener'],[]);self.assertEqual(plan['varningar'],[])
        golv=self._vagg(plan,'golv');self.assertGreaterEqual(golv['pos_m'][0]+golv['matt_m'][0]/2,2.4)                        # golvet följer med
        dg=next(d for d in plan['plats'][0]['rumsmall']['delar'] if d['id']=='golv');self.assertEqual(dg['pos_m'][:2],golv['pos_m'][:2])   # planens mallkopia samstämmig
        self.assertEqual([v['status'] for v in r['platser'][0]['vaggar']],['antagen','antagen'])                              # generade väggar märks antagna
    def test_kamera_inne_i_rummet_andrar_ingenting(self):
        import vaggar
        plan=self._plan([-1.0,.5]);fore=copy.deepcopy(plan['objekt'])
        r=vaggar.kor(plan);self.assertEqual(plan['objekt'],fore);self.assertFalse(r['platser'][0]['andrad']);self.assertEqual(r['flaggade_scener'],[])
    def test_hard_deklarerad_vagg_flyttas_inte_utan_konflikt_och_varning(self):
        import vaggar
        plan=self._plan([2.4,.5],hard={'sida':dict(x_m=1.0,status='uppmatt')});sida=self._vagg(plan,'vagg_sida')['pos_m'][:2]
        r=vaggar.kor(plan);self.assertEqual(self._vagg(plan,'vagg_sida')['pos_m'][:2],sida)
        k=r['platser'][0]['konflikter'];self.assertEqual([x['vagg'] for x in k],['vagg_sida']);self.assertTrue(k[0]['deklarerad_hard']);self.assertGreater(k[0]['saknas_m'],1.0)
        self.assertEqual(r['platser'][0]['vaggar'][1]['status'],'deklarerad');self.assertEqual(r['flaggade_scener'],['s1']);self.assertTrue(any('deklarerade väggen vagg_sida' in w for w in plan['varningar']))
    def test_plats_utan_deklaration_far_ingen_andring_och_inget_falt(self):
        import vaggar
        plan=self._plan([2.4,.5],deklarerat=False);fore=copy.deepcopy(plan)
        self.assertIsNone(vaggar.kor(plan));self.assertEqual(plan,fore)
    def test_sikt_genom_vagg_och_kamera_i_vagg_upptacks(self):
        import vaggar
        self.assertTrue(vaggar.segment_skar_lada([-2,0,1],[2,0,1],np.zeros(3),np.array([.5,.5,1.5]),0.))
        self.assertFalse(vaggar.segment_skar_lada([-2,2,1],[2,2,1],np.zeros(3),np.array([.5,.5,1.5]),0.))
        self.assertTrue(vaggar.segment_skar_lada([0,0,1],[0,0,1],np.zeros(3),np.array([.5,.5,1.5]),0.))                      # kamera inuti lådan
        self.assertTrue(vaggar.segment_skar_lada([-2,-2,1],[2,2,1],np.zeros(3),np.array([.5,.1,1.5]),math.pi/4))             # roterad låda


if __name__=='__main__':unittest.main()
