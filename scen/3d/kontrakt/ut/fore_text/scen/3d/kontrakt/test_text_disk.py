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
        absolute(self.k);self.r['edits']=[]
        r=self.k['semantik']['repliker'][-1]
        self.k['semantik']['skarmtext']=[dict(id='provtext',scen=r['scen'],text=r['text'],start_s=r['start_s'],slut_s=r['slut_s'],kalla='cm',typ='undertext',replik=r['id'],
            box=[40,700,480,90],stil=dict(font='arial.ttf',storlek_px=32,justering='center',farg='#ffffff',kontur_farg='#000000',kontur_px=2),ursprung=dict(typ='antagen',metod='Syntetiskt test.'),konfidens=1.)]

    def plan(self):
        skriv(self.d/'k.json',self.k);skriv(self.d/'r.json',self.r)
        return kompilera(self.d/'k.json',self.d/'r.json')

    def test_textbyte_genom_kompilering(self):
        self.r['edits']=[dict(id='textedit',op='skarmtext',ursprung=dict(typ='cm'),atgard='byt',skarmtext_id='provtext',scen='s7',text='Ny redigerad text')]
        p=self.plan();self.assertEqual(p['skarmtext'][0]['text'],'Ny redigerad text');self.assertEqual(p['tillampat'][0]['id'],'textedit')

    def test_replikbyte_byter_undertext(self):
        self.r['edits']=[dict(id='replikedit',op='byt_replik',ursprung=dict(typ='cm'),replik='r7',text='En ny rad.',sprak='sv',rost=None,tidspolicy='samma_lucka',max_talfaktor=None)]
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


if __name__=='__main__':unittest.main()
