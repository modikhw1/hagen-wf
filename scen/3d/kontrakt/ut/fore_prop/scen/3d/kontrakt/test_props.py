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

    def test_banken_har_grepp_och_ursprung(self):
        for typ in BANK:
            b=hamta(typ);self.assertEqual(b['status'],'mall');self.assertEqual(len(b['grepp']),3);self.assertIsNone(b['modell_ref'])
            self.assertTrue(all(v>0 for v in b['matt']));self.assertTrue(b['delar'])

class Regi(unittest.TestCase):
    """Verklig kompilator, billigt kvalitetssteg ersatt för edit-provet."""
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
        # Kroppsmått prövas i den ordinarie femminuterssviten. Här prövas edits.
        with tempfile.TemporaryDirectory(prefix='prop_',dir=HIT/'ut') as td,patch('kvalitet.komplettera'):
            d=Path(td);skriv(d/'kalla.json',k);r['edits']=edits;skriv(d/'regi.json',r)
            p=kompilera(d/'kalla.json',d/'regi.json')
            self.assertEqual(p['ej_tillampat'],[]);self.assertEqual(p['props'][0]['prop_typ'],'fiktiv_molnfrukt')
            self.assertTrue(p['props'][0]['byggd']);self.assertEqual(len(p['props'][0]['nycklar']),len(p['kallrutor']))
            r['edits'].append(dict(id='bort',op='ta_bort_prop',ursprung=origin,prop='mat',scen='s1'));skriv(d/'regi.json',r)
            p=kompilera(d/'kalla.json',d/'regi.json');self.assertFalse(p.get('props'));self.assertFalse(p['ej_tillampat'])

if __name__=='__main__':unittest.main()
