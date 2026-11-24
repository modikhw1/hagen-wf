"""Lokala kontraktsprov; syntetiska texter, verkliga oförändrade notan-mätfiler."""
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

from gemensamt import HIT, ladda, skriv
from kompilera import kompilera, ankarpose
from skarmtext import edit
from rumsmall import las, ankare


class TextDisk(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=HIT/'ut/fore_text');self.addCleanup(self.temp.cleanup);self.d=Path(self.temp.name)
        source=HIT/'exempel/notan/kalla.json';self.k=ladda(source);self.r=ladda(HIT/'ut/notan/golv_tom/regi.json')
        def absolute(o):
            if isinstance(o,dict):
                for key,v in o.items():
                    if key=='sokvag':o[key]=str((source.parent/v).resolve())
                    else:absolute(v)
            elif isinstance(o,list):
                for v in o:absolute(v)
        absolute(self.k);self.r['edits']=[];self.r['kalla']['revision']=self.k['revision']
        r=copy.deepcopy(self.k['semantik']['repliker'][-1])
        sc=next(s for s in self.k['semantik']['scener'] if s['id']==r['scen']);r['start_s']=max(r['start_s'],sc['start_s']);r['slut_s']=min(r['slut_s'],sc['slut_s'])
        self.k['semantik']['skarmtext']=[dict(id='provtext',scen=r['scen'],text=r['text'],start_s=r['start_s'],slut_s=r['slut_s'],kalla='cm',typ='undertext',replik=r['id'],
            box=[40,700,480,90],stil=dict(font='arial.ttf',storlek_px=32,justering='center',farg='#ffffff',kontur_farg='#000000',kontur_px=2),ursprung=dict(typ='antagen',metod='Syntetiskt test.'),konfidens=1.)]

    def plan(self):
        skriv(self.d/'k.json',self.k);skriv(self.d/'r.json',self.r)
        return kompilera(self.d/'k.json',self.d/'r.json')

    def test_textbyte_genom_kompilering(self):
        self.r['edits']=[dict(id='textedit',op='skarmtext',ursprung=dict(typ='cm'),atgard='byt',skarmtext_id='provtext',scen='s7',text='Ny redigerad text')]
        p=self.plan();self.assertEqual(p['skarmtext'][0]['text'],'Ny redigerad text');self.assertEqual(p['tillampat'][0]['id'],'textedit')

    def test_replikbyte_byter_undertext(self):
        self.r['edits']=[dict(id='replikedit',op='byt_replik',ursprung=dict(typ='cm'),replik='r7',text='En ny rad.',sprak='sv',rost=dict(motor='piper',rost_id=None,stil=None),tidspolicy='samma_lucka',max_talfaktor=None)]
        import tal
        with patch.object(tal,'mat_langd',return_value=1.),patch.object(tal,'passa',return_value=(np.zeros(tal.SR),1.,1.)):
            p=self.plan()
        self.assertEqual(p['skarmtext'][0]['text'],'En ny rad.');self.assertEqual(p['skarmtext'][0]['ersatt_replik'],'replikedit')

    def test_borttagen_scen_flyttar_texttid(self):
        first=self.plan()['skarmtext'][0]['ut'];sc=self.k['semantik']['scener'][0]
        self.r['edits']=[dict(id='klipp',op='ta_bort_scen',ursprung=dict(typ='cm'),scen=sc['id'])]
        after=self.plan()['skarmtext'][0]['ut'];n=round((sc['slut_s']-sc['start_s'])*30)
        self.assertEqual(after,[f-n for f in first])

    def test_text_lagg_till_och_ta_bort(self):
        t=copy.deepcopy(self.k['semantik']['skarmtext']);sc=self.k['semantik']['scener']
        edit(t,dict(id='ny',atgard='lagg_till',skarmtext_id='nytext',scen='s1',text='Hej',box=[12,14,120,30]),sc)
        self.assertEqual(t[-1]['box'],[12,14,120,30])
        edit(t,dict(id='bort',atgard='ta_bort',skarmtext_id='nytext',scen='s1'),sc);self.assertEqual(len(t),1)

    def test_mapping_tacker_kundernas_koder(self):
        root=HIT.parents[2];codes=set()
        for p in (root/'data/format/harness/linje').glob('*.json'):codes.update(ladda(p).get('lokal',[]))
        m=ladda(HIT/'rumsmall/lokalkoder.json');self.assertEqual(set(m['koder']),codes)
        for id in m['koder'].values():las(id)

    def test_diskankare_vander_mot_varandra(self):
        for id in ['chark_disk','glass_disk','servering_disk','fiktiv_mandisk','lokal_bar','lokal_disk_kassa']:
            a={x['id']:x for x in ankare(las(id)[0])};staff=a['sta_bakom'];customer=a['kundsida']
            direction=np.array(customer['pos_m'])-staff['pos_m']
            for anchor,vec in [(staff,direction),(customer,-direction)]:
                look=np.array([math.cos(anchor['riktning_rad']),math.sin(anchor['riktning_rad']),0])
                self.assertGreater(float(look@vec),0)

    def test_kamera_till_ankare_bevarar_matning(self):
        # Exakt samma källkamera ska fås när lokalt kameraoffset löses igen.
        p=self.plan();sc=self.k['semantik']['scener'][0];pl=next(x for x in self.k['semantik']['platser'] if x['id']==sc['plats_id'])
        sc['kamera_bindning']=dict(ankare=pl['ankare'][0]['id'],status='antagen',metod='Syntetisk bindning med uppmätt lokalt offset.')
        after=self.plan()
        np.testing.assert_allclose([x['matris'] for x in p['renderkamera']['nycklar']],[x['matris'] for x in after['renderkamera']['nycklar']],atol=1e-10)
        self.assertEqual(after['scener'][0]['kamera_bindning']['ankare'],pl['ankare'][0]['id'])

    def test_miljobyte_flyttar_kamerans_eget_ankare(self):
        baseline=self.plan()
        self.k['semantik']['scener'][0]['kamera_bindning']=dict(ankare='stol_B',status='antagen',metod='Syntetiskt POV-prov: kamerans ankare skiljer från personens stol_A.')
        e=copy.deepcopy(ladda(HIT/'exempel/notan/regi_byt_lokal.json')['edits'][0]);e['scen']='s1';self.r['edits']=[e]
        after=self.plan();self.assertEqual(after['ej_tillampat'],[])
        source=next(a for a in baseline['plats'][0]['uppmatta_ankare'] if a['id']=='stol_B')
        target=next(a for p in after['plats'] if p['id']!=baseline['plats'][0]['id'] for a in p['ankare'] if a['id']=='stol_B')
        expected=ankarpose(target)@np.linalg.inv(ankarpose(source))@np.array(baseline['renderkamera']['nycklar'][0]['matris'])
        np.testing.assert_allclose(after['renderkamera']['nycklar'][0]['matris'],expected,atol=1e-8)

    def test_diskbindning_for_overkropp_gissar_inte_fotkontakt(self):
        k=ladda(HIT/'ut/b/kalla.json');r=ladda(HIT/'ut/b/tom/regi.json');r['kalla']['revision']=k['revision'];r['edits']=[]
        skriv(self.d/'b_regi.json',r);p=kompilera(HIT/'ut/b/kalla.json',self.d/'b_regi.json')
        upper=[pm for s in p['scener'] for pm in s['personer'] if pm.get('stod_utelamnat')]
        self.assertTrue(upper)
        for pm in upper:
            self.assertIn(pm['ankare'],['sta_bakom','kundsida']);self.assertNotIn('stod',pm)

    def test_kort_translation_bevarar_kamerarotation(self):
        from ingest_klipp import steg_varld
        folder=self.d/'kamera';folder.mkdir();N=12;poses={}
        for i in range(N):
            angle=.4*i/(N-1);c,s=math.cos(angle),math.sin(angle)
            poses[str(i)]=[[[c,0,s],[0,1,0],[-s,0,c]],[0,0,0]]
        skriv(folder/'kamera.json',dict(registrerade=N,av=N,fel_px=.1,fokal_px=1024,statisk=False,pose=poses))
        steg_varld(folder,dict(N=N,fps=30,bredd=576,hojd=1024))
        with np.load(folder/'varld.npz') as v:
            np.testing.assert_allclose(v['kam_C'],0);self.assertFalse(np.allclose(v['kam_R'][-1],np.eye(3)))

    def test_osaker_monterdel_tar_inte_bort_hela_disken(self):
        from skymning_disk import valj
        bad=np.zeros(1000,bool);bad[:40]=True;safe=np.zeros(1000,bool)
        removed,handled,actions=valj([dict(scen='s1',grupp='disk',hits={'disk:kant':bad,'disk:sockel':safe})],{('s1','disk')},.02)
        self.assertEqual(removed,{('s1','disk:kant')});self.assertEqual(handled,{('s1','disk')})
        self.assertLessEqual(actions[-1]['grupp_efter_andel'],.02)


class AvlastaTextkopplingar(unittest.TestCase):
    def test_avlasta_undertexter_pekar_pa_ratt_replik(self):
        b=ladda(HIT/'ut/b/kalla.json')
        first=next(t for t in b['semantik']['skarmtext'] if t['scen']=='s1')
        self.assertEqual((first['typ'],first['replik']),('undertext','r1'))
        a=ladda(HIT/'ut/a/kalla.json')
        texts=[t for t in a['semantik']['skarmtext'] if t['scen']=='s4']
        self.assertEqual(len(texts),5)
        self.assertTrue(all((t['typ'],t['replik'])==('undertext','r4') for t in texts))
        refs=ladda(HIT/'textreferenser/a-sketch-servering.json')
        self.assertTrue(all(t.get('replik')=='r4' for t in refs['texter'] if t['scen']=='s4'))


if __name__=='__main__':unittest.main()
