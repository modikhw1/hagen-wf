"""Snabb kompilering, oförändrade byggbeslut och cache över processgränsen."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from gemensamt import HIT, ladda, skriv
from kompilera import kompilera
import datacache
import kroppmatt
import kvalitet
import mobelintervall
import mobellyft
import foremallyft
import boxpassning
import skymning


def byggdata(plan):
    p=copy.deepcopy(plan);p.pop('kvalitet',None)
    p['varningar']=[v for v in p['varningar'] if not v.startswith('Bildtrohet överskrider egna diagnostiska trösklar.')]
    return p


class Snabb(unittest.TestCase):
    def test_skymning_anvander_3d_segment_till_kroppspunkt(self):
        from bildkamera import _projicera
        from kompilera import sikta
        key=dict(matris=sikta([0.,-3.,1.2],[0.,0.,1.]),lins_mm=36.)
        M=np.asarray(key['matris'],float)
        # Samma disk: handen ligger över ovansidan och dess kamerasegment missar
        # lådan; höften ligger bakom fronten och segmentet går genom lådan.
        varld=np.array([[0.,0.,1.2],[0.,.5,.8]])
        lokal=(varld-M[:3,3])@M[:3,:3]
        mhr=lokal*np.array([1.,-1.,-1.])
        uv=_projicera(varld,key,np.zeros(6),1000,1000)
        disk=dict(id='disk',pos_m=[0.,0.,.5],matt_m=[2.,.5,1.],rotation_rad=[0,0,0])
        traff=skymning.konflikt(uv,mhr,key,1000,1000,[disk])['disk']
        np.testing.assert_array_equal(traff,[False,True])

    def test_bildbekraftad_mobel_bevaras_vid_granskonflikt(self):
        plan=dict(objekt=[dict(id='disk',status='mall',deltyp='bord',synlig_ut=[0,1])],kallrutor=[0],
                  scener=[dict(id='s1',ut=[0,1])],matkamera=dict(scener=[]),
                  kvalitet=dict(mobel_lyft=[dict(mobel='disk',status='flyttad')]))
        matt=dict(per_del=[dict(scen='s1',del_id='disk',flaggad=True)],omvand=[])
        with patch.object(skymning,'mat',return_value=matt): rapport=skymning.los(plan)
        self.assertEqual([o['id'] for o in plan['objekt']],['disk'])
        self.assertTrue(rapport['atgarder'][0]['granskonflikt'])
        self.assertEqual(rapport['atgarder'][0]['atgard'],'bevarad trots skymningskonflikt')

    def test_foremal_foljer_mobelns_valda_hojd_och_mitt(self):
        del_ = dict(id='disk',typ='bord',massiv=True,pos_m=[10.,20.,0.],matt_m=[2.,1.,1.],yaw_rad=np.pi/2,
                    material=dict(farg='#333638',ben_farg='#303537'),ankare=[],modell_ref=None,texturprojektion=None)
        bord=next(iter(mobelintervall._lador(del_).values()))
        foremal=dict(id='disk:pa:vag',namn='mall:disk:pa:vag',typ='lada',pos_m=[10.2,20.1,1.1],rotation_rad=[0,0,0],
                     matt_m=[.2,.3,.2],farg='#fff',top_slope=0,fas_m=.01,status='mall',deltyp='bord',modell_ref=None,texturprojektion=None)
        plan=dict(objekt=[bord,foremal],kallrutor=[0],kvalitet={})
        plats={'p':dict(rumsmall=dict(passning=dict(yaw_rad=np.pi/2),delar=[del_]),
                        deklarerat=dict(mobler={'disk':dict(hojd_m=[.8,1.],mitt_x_m=[1.,2.],mitt_y_m=0.)}))}
        def matt(_, objekt, __):
            b=next(o for o in objekt if o['id']=='disk')
            fel=abs(b['matt_m'][2]-.8)+abs(b['pos_m'][1]-20.5)
            return [dict(scen='s',andel=fel,flaggad=fel>1e-8)]
        with patch.object(mobelintervall,'_forbered',return_value=None),patch.object(mobelintervall,'_mat',side_effect=matt):
            rapport=mobelintervall.losa(plan,plats)
        vag=next(o for o in plan['objekt'] if o['id']=='disk:pa:vag')
        np.testing.assert_allclose(vag['pos_m'],[10.2,20.6,.9],atol=1e-9)
        self.assertEqual(vag['matt_m'],[.2,.3,.2])
        self.assertEqual(rapport[0]['efter']['varden']['hojd_m'],.8)
        self.assertEqual(rapport[0]['efter']['varden']['mitt_x_m'],2.)

    def test_foremal_lyfts_mot_slutkamera_och_klams_till_stodet(self):
        from bildkamera import _projicera
        from kompilera import sikta
        key=dict(matris=sikta([0.,-3.,3.],[0.,0.,1.]),lins_mm=36.)
        mal=np.array([[.5,0.,1.]])
        uv=_projicera(mal,key,np.zeros(6),1000,1000)[0]
        box=[float(uv[1]-80),float(uv[0]-40),float(uv[1]),float(uv[0]+40)]
        stod=dict(id='disk',pos_m=[0.,0.,.5],matt_m=[.6,2.,1.],rotation_rad=[0,0,0])
        vag=dict(id='disk:pa:vag',pos_m=[0.,0.,1.1],matt_m=[.2,.2,.2],rotation_rad=[0,0,0])
        plan=dict(objekt=[stod,vag],renderkamera=dict(sensor_bredd_mm=36,nycklar=[key]),utdata=dict(bredd=1000,hojd=1000),
                  scener=[dict(id='s1',ut=[0,1])],kvalitet={},plats=[dict(id='p',deklarerat=dict(foremal={
                      'vag':dict(pa='disk',objekt_id='disk:pa:vag',bild=dict(tagning='S1',box_2d=box))}))])
        rapport=foremallyft.los(plan)
        np.testing.assert_allclose(vag['pos_m'],[.2,0.,1.1],atol=1e-9)
        self.assertEqual(rapport[0]['status'],'flyttad')
        self.assertEqual(rapport[0]['ruta'],0)
        self.assertIn('bottenmitt',rapport[0]['metod'])

    def _mobelplan(self, punkt, toppkant=False, barn=False):
        from bildkamera import _projicera
        from kompilera import sikta
        key = dict(matris=sikta([0., -4., 3.], [0., 0., .8]), lins_mm=36.)
        uv = _projicera(np.asarray([punkt], float), key, np.zeros(6), 1000, 1000)[0]
        box = [float(uv[1] if toppkant else uv[1] - 100), float(uv[0] - 80),
               1000. if toppkant else float(uv[1]), float(uv[0] + 80)]
        disk = dict(id='disk', pos_m=[2., 2., .5], matt_m=[.6, 1., 1.], rotation_rad=[0, 0, 0])
        objekt = [disk]
        if barn: objekt.append(dict(id='disk:pa:vag', pos_m=[2.1, 2.2, 1.1], matt_m=[.2, .2, .2], rotation_rad=[0, 0, 0]))
        plan = dict(objekt=objekt, renderkamera=dict(sensor_bredd_mm=36, nycklar=[key]), utdata=dict(bredd=1000, hojd=1000),
                    scener=[dict(id='S1', ut=[0, 1])], kvalitet={}, plats=[dict(id='p', golv_hojd_m=0., deklarerat=dict(mobler={
                        'disk': dict(bild=dict(tagning='S1', box_2d=box))}))])
        return plan

    def test_mobel_lyfts_fran_synlig_bottenkant_mot_golvet(self):
        plan = self._mobelplan([.4, 0., 0.])
        rapport = mobellyft.los(plan)
        np.testing.assert_allclose(plan['objekt'][0]['pos_m'], [.4, .5, .5], atol=1e-9)
        self.assertEqual(plan['objekt'][0]['matt_m'], [.6, 1., 1.])
        self.assertEqual(plan['objekt'][0]['rotation_rad'], [0, 0, 0])
        self.assertEqual(rapport[0]['kant'], 'bottenkant')
        self.assertIn('ymax < 990', rapport[0]['kantorsak'])

    def test_mobel_lyfts_fran_beskuren_topps_bakkant(self):
        plan = self._mobelplan([-.3, 1., 1.], toppkant=True)
        rapport = mobellyft.los(plan)
        np.testing.assert_allclose(plan['objekt'][0]['pos_m'], [-.3, .5, .5], atol=1e-9)
        self.assertEqual(rapport[0]['kant'], 'ovansidans_bakkant')
        self.assertIn('ymax >= 990', rapport[0]['kantorsak'])

    def test_mobel_lyft_flyttar_pa_barn_med_samma_delta(self):
        plan = self._mobelplan([.4, 0., 0.], barn=True)
        fore_mobel = np.asarray(plan['objekt'][0]['pos_m'], float).copy()
        fore_barn = np.asarray(plan['objekt'][1]['pos_m'], float).copy()
        mobellyft.los(plan)
        np.testing.assert_allclose(np.asarray(plan['objekt'][1]['pos_m']) - fore_barn,
                                   np.asarray(plan['objekt'][0]['pos_m']) - fore_mobel, atol=1e-9)

    def test_mobel_lyft_klams_fore_framfor_personen(self):
        plan = self._mobelplan([0., 1.5, 0.])
        plan['plats'][0]['deklarerat']['mobler']['disk']['framfor'] = 'person'
        plan['plats'][0]['ankare'] = [dict(id='person', pos_m=[0., 1.5, 0.])]
        rapport = mobellyft.los(plan)
        np.testing.assert_allclose(plan['objekt'][0]['pos_m'], [0., .9, .5], atol=1e-9)
        self.assertTrue(rapport[0]['klamd'])
        self.assertEqual(rapport[0]['klamningsgrans'], 'personplats')
        self.assertEqual(rapport[0]['framfor'], 'person')
        self.assertFalse(rapport[0]['granskonflikt'])
        self.assertAlmostEqual(rapport[0]['uppnadd_personmarginal_m'], .1)

        trang = self._mobelplan([0., 1., 0.])
        trang['plats'][0]['deklarerat']['mobler']['disk']['framfor'] = 'person'
        trang['plats'][0]['ankare'] = [dict(id='person', pos_m=[0., -3.25, 0.])]
        rapport = mobellyft.los(trang)
        self.assertTrue(rapport[0]['granskonflikt'])
        self.assertEqual(rapport[0]['klamningsgrans'], 'personplats')
        self.assertAlmostEqual(rapport[0]['uppnadd_personmarginal_m'], .1)
        self.assertLess(rapport[0]['uppnadd_kameramarginal_m'], .3)

    def _flerbildsplan(self, kameror, start=(1., 1.)):
        disk = dict(id='disk', pos_m=[float(start[0]), float(start[1]), .5], matt_m=[.8, .6, 1.], rotation_rad=[0, 0, .2])
        plan = dict(objekt=[disk], renderkamera=dict(sensor_bredd_mm=36, nycklar=kameror),
                    utdata=dict(bredd=1000, hojd=1000),
                    scener=[dict(id=f'S{i + 1}', ut=[i, i + 1]) for i in range(len(kameror))],
                    kvalitet={}, plats=[dict(id='p', golv_hojd_m=0., deklarerat=dict(mobler={}))])
        bilder = []
        for i, key in enumerate(kameror):
            kant = boxpassning.projicerade_kanter(plan, disk, [0., 0.], key)
            bilder.append(dict(tagning=f'S{i + 1}', box_2d=[kant['topp'], kant['vanster'], kant['botten'], kant['hoger']]))
        return plan, bilder

    def test_mobel_flerbildspassning_forenar_tva_oeniga_enbildslyft(self):
        from kompilera import sikta
        kameror = [dict(matris=sikta([-1., -4., 2.5], [0., 0., .5]), lins_mm=36.),
                   dict(matris=sikta([1.2, -3., 2.2], [0., 0., .5]), lins_mm=42.)]
        plan, bilder = self._flerbildsplan(kameror)
        enbild = []
        for bild in bilder:
            p = copy.deepcopy(plan); p['plats'][0]['deklarerat']['mobler']['disk'] = dict(bild=bild)
            mobellyft.los(p); enbild.append(np.asarray(p['objekt'][0]['pos_m'][:2]))
        self.assertGreater(np.linalg.norm(enbild[0] - enbild[1]), .05)
        plan['plats'][0]['deklarerat']['mobler']['disk'] = dict(bilder=bilder)
        rapport = mobellyft.los(plan)[0]
        np.testing.assert_allclose(plan['objekt'][0]['pos_m'][:2], [0., 0.], atol=1e-7)
        self.assertEqual([p['tagning'] for p in rapport['per_tagning']], ['S1', 'S2'])
        self.assertTrue(all(p['efter_rms_px'] < 1e-6 for p in rapport['per_tagning']))

    def test_mobel_flerbildspassning_minskar_vikten_for_en_uteliggare(self):
        from kompilera import sikta
        kameror = [dict(matris=sikta([-1., -4., 2.5], [0., 0., .5]), lins_mm=36.),
                   dict(matris=sikta([1.2, -3., 2.2], [0., 0., .5]), lins_mm=42.),
                   dict(matris=sikta([-.3, -3.5, 2.8], [0., 0., .5]), lins_mm=38.),
                   dict(matris=sikta([.7, -4.2, 2.4], [0., 0., .5]), lins_mm=40.)]
        plan, bilder = self._flerbildsplan(kameror, start=(.8, .8))
        bilder[-1]['box_2d'][1] += 300.; bilder[-1]['box_2d'][3] += 300.
        plan['plats'][0]['deklarerat']['mobler']['disk'] = dict(bilder=bilder)
        rapport = mobellyft.los(plan)[0]
        self.assertLess(np.linalg.norm(plan['objekt'][0]['pos_m'][:2]), .04)
        bra = [p['efter_rms_px'] for p in rapport['per_tagning'][:-1]]
        self.assertLess(max(bra), 7.)
        self.assertGreater(rapport['per_tagning'][-1]['efter_rms_px'], 150.)

    def test_foremal_flerbildspassas_och_klams_till_stodets_topp(self):
        from kompilera import sikta
        kameror = [dict(matris=sikta([-1., -4., 2.8], [0., 0., 1.1]), lins_mm=36.),
                   dict(matris=sikta([1., -3., 2.4], [0., 0., 1.1]), lins_mm=42.)]
        stod = dict(id='disk', pos_m=[0., 0., .5], matt_m=[1., 1., 1.], rotation_rad=[0, 0, 0])
        vag = dict(id='disk:pa:vag', pos_m=[0., 0., 1.1], matt_m=[.2, .2, .2], rotation_rad=[0, 0, 0])
        plan = dict(objekt=[stod, vag], renderkamera=dict(sensor_bredd_mm=36, nycklar=kameror),
                    utdata=dict(bredd=1000, hojd=1000), scener=[dict(id='S1', ut=[0, 1]), dict(id='S2', ut=[1, 2])],
                    kvalitet={}, plats=[dict(id='p', deklarerat=dict(foremal={}))])
        bilder = []
        for i, key in enumerate(kameror):
            kant = boxpassning.projicerade_kanter(plan, vag, [.8, 0.], key)
            bilder.append(dict(tagning=f'S{i + 1}', box_2d=[kant['topp'], kant['vanster'], kant['botten'], kant['hoger']]))
        plan['plats'][0]['deklarerat']['foremal']['vag'] = dict(pa='disk', objekt_id='disk:pa:vag', bilder=bilder)
        rapport = foremallyft.los(plan)[0]
        np.testing.assert_allclose(vag['pos_m'], [.4, 0., 1.1], atol=1e-7)
        self.assertEqual(rapport['antal_boxar'], 2)
        self.assertGreater(min(p['efter_rms_px'] for p in rapport['per_tagning']), 1.)

    def test_full_ar_standard_och_snabb_bevarar_samtliga_byggfalt(self):
        # Verklig bildtrohet och alla byggbeslut. Kroppsmåttets algoritm har egna prov.
        with patch('kroppmatt.matt_plan',return_value=[]) as matt:
            full=kompilera(HIT/'exempel/bar/kalla.json',HIT/'exempel/bar/regi.json')
            self.assertEqual(matt.call_count,1)
        with patch('trohet.mat',side_effect=AssertionError('diagnostik i snabbvägen')),patch('kvalitet.komplettera',side_effect=AssertionError('diagnostik i snabbvägen')):
            fast=kompilera(HIT/'exempel/bar/kalla.json',HIT/'exempel/bar/regi.json',snabb=True)
        self.assertEqual(byggdata(fast),byggdata(full))
        self.assertEqual(fast['kvalitet']['diagnostik'],'ej_kord')
        self.assertTrue(fast['kvalitet']['bildtrohet']['flaggad'])
        self.assertEqual(fast['kvalitet']['skymning'],full['kvalitet']['skymning'])

    def test_separat_diagnostik_bevarar_byggfalt_och_avvisar_andrat_underlag(self):
        from diagnostik import diagnostik
        fast=kompilera(HIT/'exempel/bar/kalla.json',HIT/'exempel/bar/regi.json',snabb=True)
        before=byggdata(fast)
        with patch('kroppmatt.matt_plan',return_value=[]):checked=diagnostik(copy.deepcopy(fast))
        self.assertEqual(byggdata(checked),before)
        self.assertNotIn('diagnostik',checked['kvalitet'])
        fast['kvalitet']['byggunderlag']=[]
        with self.assertRaisesRegex(ValueError,'mätunderlag har ändrats'):diagnostik(fast)

    def test_handledens_matris_ar_exakt_samma_med_och_utan_benstod(self):
        from test_rumsmall import Rumsmall
        from propplan import handmatris
        from trohet import ruta_pose, IX, F
        pose,Q,T,anchor=Rumsmall().kropp()
        # ruta_pose bygger Q ur G, kam_R och F; välj motsvarande världskamera.
        seq=dict(pose=pose[None],cam_t=np.zeros((1,3)),ben_synliga=np.zeros(1,bool))
        world=dict(upp=np.array([0.,0.,1.]),kam_R=(Q@F)[None],kam_C=T[None])
        scene=dict(varld='oanvand');pm=dict(stod=anchor)
        full,q,t=ruta_pose(scene,pm,0,True,(seq,world))
        hand,qh,th=handmatris(scene,pm,0,(seq,world),led='l_wrist_twist')
        np.testing.assert_array_equal(full[IX['l_wrist_twist']],hand[IX['l_wrist_twist']])
        j=IX['l_wrist_twist']
        np.testing.assert_array_equal(full[j,:3]/100@q.T+t,hand[j,:3]/100@qh.T+th)
        np.testing.assert_array_equal(q,qh);np.testing.assert_array_equal(t,th)
        leg,ql,tl=handmatris(scene,pm,0,(seq,world),led='l_foot')
        np.testing.assert_array_equal(full,leg)


class Cache(unittest.TestCase):
    def test_kroppsmatt_ateranvands_i_en_ny_pythonprocess(self):
        with tempfile.TemporaryDirectory(dir=HIT/'ut',prefix='persist_') as td:
            code="""
import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import datacache,kroppmatt
import numpy as np
datacache.CACHE=Path(sys.argv[2])
p=dict(kallrutor=[0],kallbild_bredd=576,utdata=dict(bredd=576,hojd=1024),matkamera=dict(nycklar=[]))
def measure(*args):
    if sys.argv[3]=='las':raise AssertionError('Cachen försvann med processen')
    return [dict(mask=dict(rutor=7),darr=float('nan'))]
kroppmatt._matt_plan_utan_cache=measure
r=kroppmatt.matt_plan(p)
assert r[0]['mask']['rutor']==7
"""
            for mode in ('skriv','las'):
                r=subprocess.run([sys.executable,'-c',code,str(HIT),td,mode],capture_output=True,text=True,encoding='utf-8')
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_kroppsmatt_ogiltigt_vid_mask_raw_palitlighet_och_kod(self):
        with tempfile.TemporaryDirectory(dir=HIT/'ut',prefix='kroppcache_') as td,patch.object(datacache,'CACHE',Path(td)/'cache'):
            folder=Path(td);seq=folder/'sekvens_1.npz';seq.write_bytes(b'pose')
            p=dict(scener=[dict(id='s1',ut=[0,1],lokal_start=0,varld=str(folder/'varld.npz'),personer=[dict(id='A',ingest_id='1',rorelse=str(seq))])],kallrutor=[0],kallbild_bredd=576,utdata=dict(bredd=576,hojd=1024),matkamera=dict(nycklar=[]))
            kroppmatt._MATT_CACHE.clear()
            with patch.object(kroppmatt,'_matt_plan_utan_cache',return_value=[dict(matt=1)]) as run:
                kroppmatt.matt_plan(p);self.assertEqual(run.call_count,1)
                kroppmatt._MATT_CACHE.clear();kroppmatt.matt_plan(p);self.assertEqual(run.call_count,1)
                for i,name in enumerate(('masker.npy','palitlig_1.json','kropp/1/0000.npz'),2):
                    file=folder/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'nytt underlag')
                    kroppmatt.matt_plan(p);self.assertEqual(run.call_count,i)
                with patch.object(datacache,'kodnyckel',return_value='annan kod eller rigg'):
                    kroppmatt.matt_plan(p);self.assertEqual(run.call_count,5)
            kroppmatt._MATT_CACHE.clear()

    def test_trasig_cache_ger_omrakning(self):
        with tempfile.TemporaryDirectory(dir=HIT/'ut',prefix='cache_') as td,patch.object(datacache,'CACHE',Path(td)):
            key=datacache.nyckel(dict(indata=1));datacache.spara('prov',key,dict(varde=3))
            self.assertEqual(datacache.hamta('prov',key),dict(varde=3))
            file=Path(td)/'prov'/(key+'.json');d=ladda(file);d['data']['varde']=999;skriv(file,d)
            self.assertIsNone(datacache.hamta('prov',key))
            file.write_text('{avbrutet',encoding='utf-8');self.assertIsNone(datacache.hamta('prov',key))

    def test_planbeslut_cache_ogiltig_vid_geometri_och_matfil(self):
        with tempfile.TemporaryDirectory(dir=HIT/'ut',prefix='beslut_') as td,patch.object(datacache,'CACHE',Path(td)/'cache'):
            raw=Path(td)/'varld.npz';raw.write_bytes(b'fore')
            p=dict(scener=[dict(id='s1',ut=[0,1],varld=str(raw),personer=[])],personer=[],objekt=[],matkamera=dict(nycklar=[]),kallrutor=[0],kallbild_bredd=576,kallbild_hojd=1024,kvalitet={})
            def decide(plan,places):
                plan['objekt']=[dict(id='bevarat_bord')]
                plan['kvalitet'].update(golv_skala={},skymning=dict(atgarder=['provbeslut']))
            with patch.object(kvalitet,'_planbeslut_utan_cache',side_effect=decide) as run:
                a=copy.deepcopy(p);kvalitet.planbeslut(a,{})
                b=copy.deepcopy(p);kvalitet.planbeslut(b,{})
                self.assertEqual(a,b);self.assertEqual(run.call_count,1)
                raw.write_bytes(b'efter nytt underlag');kvalitet.planbeslut(copy.deepcopy(p),{});self.assertEqual(run.call_count,2)
                p['objekt']=[dict(id='nytt_bord')];kvalitet.planbeslut(copy.deepcopy(p),{});self.assertEqual(run.call_count,3)

    def test_kodnyckel_foljer_transitiva_importer(self):
        # Planbeslutets nyckel ska ändras när en modul ändras som bara importeras indirekt (inne i en funktion).
        with tempfile.TemporaryDirectory(dir=HIT/'ut',prefix='moduler_') as td:
            d=Path(td);(d/'a.py').write_text('def f():\n    import b\n',encoding='utf-8')
            (d/'b.py').write_text('from c import g\n',encoding='utf-8');(d/'c.py').write_text('def g(): return 1\n',encoding='utf-8')
            (d/'fri.py').write_text('x=1\n',encoding='utf-8')
            mods=datacache.lokala_moduler([d/'a.py'],[d])
            self.assertEqual([m.name for m in mods],['a.py','b.py','c.py'])
            fore=datacache.kodnyckel(mods);(d/'c.py').write_text('def g(): return 2\n',encoding='utf-8')
            self.assertNotEqual(fore,datacache.kodnyckel(datacache.lokala_moduler([d/'a.py'],[d])))
        verklig={m.name for m in datacache.lokala_moduler([HIT/'kvalitet.py'],[HIT,HIT.parent/'ingest'])}
        self.assertTrue({'skymning.py','dolda_fotter.py','rumsmall.py','mobelintervall.py'}<=verklig)


if __name__=='__main__':unittest.main()
