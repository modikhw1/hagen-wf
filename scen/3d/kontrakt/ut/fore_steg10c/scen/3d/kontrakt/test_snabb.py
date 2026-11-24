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


def byggdata(plan):
    p=copy.deepcopy(plan);p.pop('kvalitet',None)
    p['varningar']=[v for v in p['varningar'] if not v.startswith('Bildtrohet överskrider egna diagnostiska trösklar.')]
    return p


class Snabb(unittest.TestCase):
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


if __name__=='__main__':unittest.main()
