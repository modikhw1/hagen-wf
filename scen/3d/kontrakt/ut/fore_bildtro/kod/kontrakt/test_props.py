"""Propregressioner: rörelse, redigeringar och okända lägen."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from propbank import hamta, BANK
from propplan import fast_i_hand, byt, ny, los

class Props(unittest.TestCase):
    def test_scenlokal_mobelrest_foljer_bunden_person(self):
        from tropassning import scenpassa_ankare,scenpassa_objekt
        decision=dict(scen='s7',person='B',ankare='stol_B',del_ids=['stol_B','bord_B'],
                      flytt_xy_m=[.4,-.2],status='antagen',metod='prov')
        room=dict(scenpassning=[decision])
        objects={i:dict(id=i,pos_m=[x,y,z]) for i,x,y,z in
                 [('stol_B',1.,2.,.4),('stol_B:ben',1.1,2.1,.2),('bord_B',0.,2.,.7),('bord_A',0.,0.,.7)]}
        scenpassa_objekt(objects,room,'s7')
        np.testing.assert_allclose(objects['stol_B']['pos_m'],[1.4,1.8,.4])
        np.testing.assert_allclose(objects['stol_B:ben']['pos_m'],[1.5,1.9,.2])
        np.testing.assert_allclose(objects['bord_B']['pos_m'],[.4,1.8,.7])
        np.testing.assert_allclose(objects['bord_A']['pos_m'],[0.,0.,.7])
        anchor=scenpassa_ankare(dict(id='stol_B',pos_m=[1.,2.,.43]),room,'s7')
        np.testing.assert_allclose(anchor['pos_m'],[1.4,1.8,.43])
        untouched=scenpassa_ankare(dict(id='stol_B',pos_m=[1.,2.,.43]),room,'s2')
        np.testing.assert_allclose(untouched['pos_m'],[1.,2.,.43])

    def test_grepp_foljer_roterad_hand(self):
        grip=np.array([.05,-.02,.01]);offset=np.array([.01,.03,0])
        for angle in [0,.4,1.7]:
            c,s=np.cos(angle),np.sin(angle);r=np.array([[c,-s,0],[s,c,0],[0,0,1]])
            h=np.array([angle,2.,1.]);root=fast_i_hand(h,r,offset,grip)
            np.testing.assert_allclose(root+r@grip,h+r@offset,atol=1e-14)

    def test_byte_bevarar_faste_och_uppmatta_regioner(self):
        o=ny(dict(ny_id='mat',typ='meat_cut',faste=dict(person='A',led='l_wrist_twist',hand='vanster')))
        o['propdata']['bildregioner']=[dict(box_px=[10,20,100,80])];before=copy.deepcopy(o['propdata'])
        byt(o,'fiktiv_molnfrukt')
        self.assertEqual(o['propdata'],before);self.assertEqual(o['bank']['typ'],'fiktiv_molnfrukt');self.assertTrue(o['edit']['fiktiv'])
        with self.assertRaisesRegex(ValueError,'Ingen form'):byt(o,'okand_produkt')

    def test_okand_position_utelamnas_med_skal(self):
        o=ny(dict(ny_id='okand',typ='plate'));o.update(scen='s1',synlig_ut=[0,2])
        plan=dict(kallbild_bredd=576,utdata=dict(bredd=576,hojd=1024),scener=[dict(id='s1',ut=[0,2],lokal_start=0,personer=[])],renderkamera=dict(nycklar=[dict(matris=np.eye(4).tolist(),lins_mm=36)]*2),props=[o],objekt=[],kvalitet={})
        los(plan);self.assertFalse(o['byggd']);self.assertEqual(o['nycklar'],[]);self.assertIn('Ingen mätbar position',o['antaganden'][0])

    def test_upplost_prop_foljer_hand_och_bankgrepp(self):
        from gemensamt import HIT
        from trohet import IX
        with tempfile.TemporaryDirectory(prefix='prop_hand_',dir=HIT/'ut') as td:
            path=Path(td);np.savez(path/'s.npz',inom=np.ones(3,bool));np.savez(path/'v.npz',kam_C=np.zeros((3,3)))
            o=ny(dict(ny_id='mat',typ='meat_cut',faste=dict(person='A',led='l_wrist_twist',hand='vanster')));o.update(scen='s1',synlig_ut=[0,3])
            pm=dict(id='A',rorelse=str(path/'s.npz'));sc=dict(id='s1',ut=[0,3],lokal_start=0,varld=str(path/'v.npz'),personer=[pm])
            keys=[dict(matris=np.eye(4).tolist(),lins_mm=36)]*3
            plan=dict(kallbild_bredd=576,utdata=dict(bredd=576,hojd=1024),scener=[sc],renderkamera=dict(nycklar=keys),props=[o],objekt=[],kvalitet={})
            def pose(sc,pm,f,stod,data):
                p=np.zeros((127,8));p[:,6]=1;p[IX['l_wrist_twist'],:3]=[10*f,0,100]
                return p,np.eye(3),np.zeros(3)
            with patch('propplan.ruta_pose',side_effect=pose):los(plan)
            for f,key in enumerate(o['nycklar']):
                m=np.array(key['matris']);np.testing.assert_allclose(m[:3,3]+m[:3,:3]@o['bank']['grepp'],[f*.1,0,1.])

    def test_banken_har_grepp_och_ursprung(self):
        for typ in BANK:
            b=hamta(typ);self.assertEqual(b['status'],'mall');self.assertEqual(len(b['grepp']),3);self.assertIsNone(b['modell_ref'])
            self.assertTrue(all(v>0 for v in b['matt']));self.assertTrue(b['delar'])

class Regi(unittest.TestCase):
    """Verklig kompilator med snabbväg; byggbesluten körs även i edit-provet."""
    def test_tillagg_byte_bort_genom_kompilatorn(self):
        from gemensamt import HIT,ladda,skriv
        from kompilera import kompilera
        src=HIT/'exempel/bar/kalla.json';k=ladda(src);r=ladda(HIT/'exempel/bar/regi.json')
        def absolute(x):
            if isinstance(x,dict):
                for key,v in x.items():
                    if key=='sokvag':x[key]=str((src.parent/v).resolve())
                    else:absolute(v)
            elif isinstance(x,list):
                for v in x:absolute(v)
        absolute(k)
        origin=dict(typ='cm')
        edits=[dict(id='ny',op='lagg_till_prop',ursprung=origin,ny_id='mat',typ='meat_cut',scen='s1',faste=dict(person='1',led='l_wrist_twist',hand='vanster')),
               dict(id='byt',op='byt_prop',ursprung=origin,prop='mat',ny_typ='fiktiv_molnfrukt')]
        # Kroppsmått prövas i test_kroppmatt. Här prövas edits med alla byggbeslut.
        with tempfile.TemporaryDirectory(prefix='prop_',dir=HIT/'ut') as td:
            d=Path(td);skriv(d/'kalla.json',k);r['edits']=edits;skriv(d/'regi.json',r)
            p=kompilera(d/'kalla.json',d/'regi.json', snabb=True)
            self.assertEqual(p['ej_tillampat'],[]);self.assertEqual(p['props'][0]['prop_typ'],'fiktiv_molnfrukt')
            self.assertTrue(p['props'][0]['byggd']);self.assertEqual(len(p['props'][0]['nycklar']),len(p['kallrutor']))
            r['edits'].append(dict(id='bort',op='ta_bort_prop',ursprung=origin,prop='mat',scen='s1'));skriv(d/'regi.json',r)
            p=kompilera(d/'kalla.json',d/'regi.json', snabb=True);self.assertFalse(p.get('props'));self.assertFalse(p['ej_tillampat'])

if __name__=='__main__':unittest.main()
