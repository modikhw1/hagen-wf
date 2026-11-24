"""Lokala händelser, käll-/utdatatid, tidsatta props och hashstopp."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from gemensamt import HIT, ladda, skriv, kontrollmodul
from handelser import los_edit, till_plan
from kalla_handelser import handmoten, spargranser, fyll


def event(eid, t, end=None):
    return dict(id=eid, typ='prop_synlig', vad='Lokalt prov', vem=None, till_vem=None,
                prop=None, scen='s1', start_s=t, slut_s=t if end is None else end,
                ursprung=dict(typ='uppmatt', metod='Syntetiskt mätfall.', konfidens='hog', modell=None))


class Detektion(unittest.TestCase):
    def test_sparlucka_ar_inte_en_uppfunnen_entre(self):
        self.assertEqual(spargranser([0, 1, 8, 9], 10), [('person_synlig', 0), ('person_forsvinner', 10)])
        self.assertEqual(spargranser([], 10), [])

    def test_handmote_kraver_tva_giltiga_intilliggande_rutor(self):
        a = {f: np.array([[100., 100.], [300, 300]]) for f in range(6)}
        b = {f: np.array([[110., 100.], [500, 500]]) for f in [0, 2, 3, 5]}
        self.assertEqual(handmoten(a, b, 576, 1024), [[2, 4]])
        b[3] = np.array([[np.nan, 100], [2000, 2000]])
        self.assertEqual(handmoten(a, b, 576, 1024), [])

    def test_semantisk_handling_bevarar_modell_och_spann(self):
        k = ladda(HIT/'exempel/bar/kalla.json')
        sem = dict(ursprung=dict(modell='sparad-testmodell'), data=dict(tagningar=[dict(tagning='S1',vad='Tar emot mat',konfidens='lag')]))
        result = fyll(k, HIT/'exempel/bar', sem)
        action = next(e for e in result['semantik']['handelser'] if e['typ']=='scen_handling')
        self.assertEqual(action['ursprung']['typ'], 'modellbedomd')
        self.assertEqual(action['ursprung']['modell'], 'sparad-testmodell')
        self.assertGreater(action['slut_s'], action['start_s'])
        self.assertNotIn('bevis', action)
        self.assertTrue(result['matning']['handelsebevis'])
        self.assertNotIn('handelser', k['semantik'])


class Tid(unittest.TestCase):
    def test_fran_till_och_offset(self):
        e, result = los_edit(dict(op='trimma_scen',tid=dict(fran=dict(handelse='a'),till=dict(handelse='b',kant='slut',offset_s=.1))),
                            [event('a',1),event('b',2,3)], 5)
        self.assertEqual((e['start_s'], e['slut_s']), (1, 3.1))
        self.assertEqual(result['kalla_s'], dict(start_s=1,slut_s=3.1))

    def test_spann_och_dubbla_tider_avvisas(self):
        with self.assertRaisesRegex(ValueError,'ange kant'):
            los_edit(dict(op='trimma_scen',tid=dict(fran=dict(handelse='a'))),[event('a',1,2)],5)
        with self.assertRaisesRegex(ValueError,'inte båda'):
            los_edit(dict(op='skarmtext',start_s=1,tid=dict(fran=dict(handelse='a'))),[event('a',1)],5)

    def test_handelser_foljer_trim_kopia_och_omordning(self):
        scenes = [dict(id='kopia',ursprung='s1'),dict(id='s1',ursprung='s1')]
        timeline = [dict(kalla=[20,40],ut=[0,20]),dict(kalla=[0,40],ut=[20,60])]
        result = till_plan([event('e',1),event('bort',.2)],scenes,timeline,30,lambda t:round(t*30))
        self.assertEqual([x['ut'] for x in result[0]['forekomster']],[[10,10],[50,50]])
        self.assertEqual([x['ut'] for x in result[1]['forekomster']],[[26,26]])


class Kompilator(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='handelser_',dir=HIT/'ut')
        self.addCleanup(self.temp.cleanup)
        self.d = Path(self.temp.name)
        src = HIT/'exempel/bar/kalla.json'
        self.k = ladda(src); self.r = ladda(HIT/'exempel/bar/regi.json')
        def absolute(x):
            if isinstance(x,dict):
                for key,v in x.items():
                    if key=='sokvag': x[key]=str((src.parent/v).resolve())
                    else: absolute(v)
            elif isinstance(x,list):
                for v in x: absolute(v)
        absolute(self.k)
        self.k['semantik']['handelser']=[event('start',1),event('slut',2),event('spann',.4,.8)]
        self.r['edits']=[]
        self.r['ramar']['bevara_beats']=[]

    def plan(self):
        from kompilera import kompilera
        skriv(self.d/'kalla.json',self.k);skriv(self.d/'regi.json',self.r)
        with patch('kvalitet.komplettera'):
            return kompilera(self.d/'kalla.json',self.d/'regi.json')

    def test_trimma_scen_med_handelser_upploses_i_plan(self):
        self.r['edits']=[dict(id='trim',op='trimma_scen',ursprung=dict(typ='cm'),scen='s1',lage='klipp_slut',
                             tid=dict(fran=dict(handelse='start'),till=dict(handelse='slut')))]
        p=self.plan()
        self.assertEqual(p['kallrutor'],list(range(30,60)))
        self.assertEqual(p['tillampat'][0]['andring']['tid']['kalla_s'],dict(start_s=1,slut_s=2))
        self.assertEqual(p['handelser'][0]['forekomster'][0]['ut'],[0,0])

    def test_tidsatt_tillagg_byte_och_borttagning_fungerar_i_ordning(self):
        origin=dict(typ='cm')
        self.r['edits']=[
            dict(id='ny',op='lagg_till_prop',ursprung=origin,ny_id='mat',typ='meat_cut',scen='s1',faste=dict(person='1',led='l_wrist_twist',hand='vanster')),
            dict(id='byt',op='byt_prop',ursprung=origin,prop='mat',ny_typ='fiktiv_molnfrukt',tid=dict(fran=dict(handelse='start'),till=dict(handelse='slut'))),
            dict(id='bort',op='ta_bort_prop',ursprung=origin,prop='mat',scen='s1',tid=dict(fran=dict(handelse='slut')))]
        p=self.plan()
        self.assertEqual(p['ej_tillampat'],[])
        props=p['props']
        self.assertEqual([(o['prop_typ'],o['synlig_ut']) for o in props],[('meat_cut',[0,30]),('fiktiv_molnfrukt',[30,60])])
        self.assertEqual([[k['ut'] for k in o['nycklar']] for o in props],[list(range(30)),list(range(30,60))])
        self.assertEqual(len(p['kvalitet']['props']),2)
        self.assertEqual(p['tillampat'][1]['andring']['tid']['forekomster'][0]['ut'],[30,60])

    def test_tidsatt_tillagg_finns_bara_i_sitt_intervall(self):
        self.r['edits']=[dict(id='ny',op='lagg_till_prop',ursprung=dict(typ='cm'),ny_id='mat',typ='plate',scen='s1',
            faste=dict(person='1',led='l_wrist_twist',hand='vanster'),tid=dict(fran=dict(handelse='start'),till=dict(handelse='slut')))]
        p=self.plan()
        self.assertEqual(p['props'][0]['synlig_ut'],[30,60])
        self.assertEqual(len(p['props'][0]['nycklar']),30)

    def test_okand_handelse_och_omvant_spann_stoppar_fore_bygge(self):
        self.r['edits']=[dict(id='trim',op='trimma_scen',ursprung=dict(typ='cm'),scen='s1',lage='klipp_slut',tid=dict(fran=dict(handelse='okand')))]
        with self.assertRaisesRegex(ValueError,'Okänd händelse'):self.plan()
        self.r['edits'][0]['tid']=dict(fran=dict(handelse='slut'),till=dict(handelse='start'))
        with self.assertRaisesRegex(ValueError,'omvänt'):self.plan()

    def test_dubblerat_event_och_fel_person_avvisas(self):
        self.k['semantik']['handelser'].append(copy.deepcopy(self.k['semantik']['handelser'][0]))
        with self.assertRaisesRegex(ValueError,'dubblerade händelse'):self.plan()
        self.k['semantik']['handelser'].pop();self.k['semantik']['handelser'][0]['vem']='saknas'
        with self.assertRaisesRegex(ValueError,'vem'):self.plan()

    def test_omskriven_ingestfil_ger_fel_med_refreshkommando(self):
        raw=self.d/'sekvens.npz';raw.write_bytes(b'fore')
        self.k['matning']['personer'][0]['rorelse'].update(sokvag=str(raw),sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
        raw.write_bytes(b'efter')
        with self.assertRaisesRegex(ValueError,'kalla_omhasha.py.*--uppdatera'):self.plan()

    def test_ingest_varnar_med_refreshkommando(self):
        import contextlib, io, sys
        sys.path.insert(0,str(HIT.parent/'ingest'))
        from kallstatus import varna
        raw=self.d/'matning.json'; raw.write_bytes(b'fore')
        self.k['matning']['handelsekallor']=[dict(sokvag=str(raw),sha256=hashlib.sha256(b'fore').hexdigest(),format='json',roll='Prov')]
        skriv(self.d/'kalla.json',self.k);raw.write_bytes(b'efter')
        output=io.StringIO()
        with contextlib.redirect_stderr(output): result=varna(self.d,[self.d/'kalla.json'])
        self.assertEqual(result,[str(self.d/'kalla.json')])
        self.assertIn('kalla_omhasha.py',output.getvalue());self.assertIn('kalla_handelser.py',output.getvalue())

    def test_byte_utan_scen_traf_finns_bara_i_en_scen(self):
        self.k['semantik']['handelser']=[]
        scene=self.k['semantik']['scener'][0]
        split=self.k['tidsbas']['langd_s']/2
        other=copy.deepcopy(scene);other.update(id='s2',start_s=split)
        scene['slut_s']=split;self.k['semantik']['scener'].append(other)
        origin=dict(typ='cm')
        self.r['edits']=[dict(id='ny',op='lagg_till_prop',ursprung=origin,ny_id='mat',typ='meat_cut',scen='s1',faste=dict(person='1',led='l_wrist_twist',hand='vanster')),
                        dict(id='byt',op='byt_prop',ursprung=origin,prop='mat',ny_typ='fiktiv_molnfrukt')]
        p=self.plan()
        self.assertFalse(p['ej_tillampat']);self.assertEqual(len(p['props']),1)
        self.assertEqual(p['props'][0]['prop_typ'],'fiktiv_molnfrukt')
        self.r['edits'][1]['scen']='s2'
        p=self.plan()
        self.assertEqual([e['id'] for e in p['ej_tillampat']],['byt'])
        self.assertEqual(p['props'][0]['prop_typ'],'meat_cut')

    def test_ingest_skannar_inte_omhashningsloggar_som_kallor(self):
        import sys
        sys.path.insert(0,str(HIT.parent/'ingest'))
        from kallstatus import inaktuella
        log=self.d/'kalla.json.omhashning.json';skriv(log,[dict(backup='bevarad')])
        self.assertEqual(inaktuella(log,self.d),[])

    def test_eventunderlag_far_inte_hashas_om_tyst(self):
        from kalla_omhasha import main
        raw=self.d/'spar.json';raw.write_text('{}',encoding='utf-8')
        self.k['matning']['handelsekallor']=[dict(sokvag=str(raw),sha256=hashlib.sha256(b'{}').hexdigest(),format='json',roll='Prov')]
        raw.write_text('{"andrad":true}',encoding='utf-8')
        skriv(self.d/'kalla.json',self.k)
        with self.assertRaisesRegex(ValueError,'kalla_handelser.py'):self.plan()
        with self.assertRaisesRegex(ValueError,'Händelseunderlaget'):main(self.d/'kalla.json',self.d/'ny.json')
        self.assertFalse((self.d/'ny.json').exists())


if __name__=='__main__':
    unittest.main()
