"""Lokala regressioner. Varje test skapar ut/bar/test_* och tar bort just den mappen när testet är klart."""
import ast
import copy
import hashlib
import json
import shutil
import tempfile
import sys
import unittest
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
from gemensamt import HIT, ladda, skriv
from kalla_bygg import bygg
from kompilera import kompilera

UT=HIT/'ut/bar'; INGEST=HIT.parent/'ingest'; KALLA=HIT/'exempel/bar/kalla.json'; REGI=HIT/'exempel/bar/regi.json'


class Flode(unittest.TestCase):
    def setUp(self):
        self.ut=Path(tempfile.mkdtemp(prefix='test_',dir=UT)); self.addCleanup(shutil.rmtree,self.ut,ignore_errors=True)
        self.k=ladda(KALLA); self.r=ladda(REGI)
        # Flytta källfilen: även videon och alla mätpekare måste rebasa.
        def absref(o):
            if isinstance(o,dict):
                for k,v in o.items():
                    if k=='sokvag': o[k]=str((KALLA.parent/v).resolve())
                    else: absref(v)
            elif isinstance(o,list):
                for v in o: absref(v)
        absref(self.k)

    def plan(self, edits=None):
        if edits is not None: self.r['edits']=edits
        skriv(self.ut/'kalla.json',self.k); skriv(self.ut/'regi.json',self.r)
        return kompilera(self.ut/'kalla.json',self.ut/'regi.json')

    def edit(self,op,**kw): return dict(id='e'+str(len(kw))+op,op=op,ursprung=dict(typ='cm'),**kw)

    def test_bar_och_determinism(self):
        p=self.plan(); skriv(self.ut/'a.json',p); skriv(self.ut/'b.json',self.plan())
        self.assertEqual((self.ut/'a.json').read_bytes(),(self.ut/'b.json').read_bytes())
        self.assertEqual(p['kallrutor'],list(range(156)))
        self.assertEqual([e['id'] for e in p['tillampat']],['e2','e3','e4','e5'])
        self.assertEqual([e['id'] for e in p['ej_tillampat']],['e1'])
        self.assertEqual(p['personer'][0]['farg'],'#2f4f6f')
        prop=next(o for o in p['objekt'] if o['id']=='prop_1')
        self.assertEqual(prop['matt_m'],ladda(INGEST/'ut/bar/rum.json')['objects'][1]['size'])
        self.assertTrue(all(n==p['renderkamera']['nycklar'][0] for n in p['renderkamera']['nycklar']))
        from kompilera import gravitation, F
        s=np.load(p['personer'][0]['rorelse']); v=np.load(p['matning']['kameror'][0]['spar_metrisk']['sokvag']); g=gravitation(v)
        key=p['renderkamera']['nycklar'][0]; inv=np.linalg.inv(key['matris'])
        for f in p['kallrutor']:
            head=g @ (v['kam_C'][f]+v['kam_R'][f] @ (F @ (s['pose'][f,113,:3]/100)+s['cam_t'][f]))
            point=inv @ [*head,1]; self.assertLess(point[2],0)
            self.assertLess(abs(point[0]/-point[2]*key['lins_mm']/18),1)

    def test_ordning_trim_flytt_bort(self):
        original=self.k['semantik']['scener'][0]
        self.k['semantik']['scener']=[dict(original,id='s1',slut_s=2),dict(original,id='s2',start_s=2,slut_s=4),dict(original,id='s3',start_s=4)]
        p=self.plan([self.edit('trimma_scen',scen='s2',start_s=2.5,lage='klipp_slut'),
                     self.edit('flytta_scen',scen='s3',efter=None),self.edit('ta_bort_scen',scen='s1')])
        self.assertEqual(p['kallrutor'],list(range(120,202))+list(range(75,120)))
        self.assertEqual(p['tidskarta'],[dict(ut=[0,82],kalla=[120,202],ljud=True),dict(ut=[82,127],kalla=[75,120],ljud=True)])

    def test_prop_tillagg_flytt_bort_och_axlar(self):
        edits=[self.edit('lagg_till_prop',ny_id='ny',typ='skylt',scen='s1',matt_m=[.3,.5,.1],stod='bar_counter_1'),
               self.edit('flytta_prop',prop='ny',scen='s1',till=dict(relativt='bar_counter_1',forskjutning_m=[.2,0,.8])),
               self.edit('ta_bort_prop',prop='prop_1',scen='s1')]
        p=self.plan(edits); self.assertFalse(p['ej_tillampat'])
        ny=next(o for o in p['objekt'] if o['id']=='ny'); bar=next(o for o in p['objekt'] if o['id']=='bar_counter_1')
        self.assertEqual(ny['matt_m'],[.3,.1,.5]); self.assertNotIn('prop_1',[o['id'] for o in p['objekt']])
        yaw=bar['rotation_rad'][2]; np.testing.assert_allclose(ny['pos_m'],np.array(bar['pos_m'])+[.2*np.cos(yaw),.2*np.sin(yaw),.8])
        skriv(UT/'plan_props_test.json',p)

    def test_scenbunden_prop_och_duplicering(self):
        p=self.plan([self.edit('duplicera_scen',scen='s1',ny_id='s2',efter=None,med_ljud=False),self.edit('ta_bort_prop',prop='prop_1',scen='s1')])
        self.assertEqual(len(p['kallrutor']),404)
        self.assertEqual([o['synlig_ut'] for o in p['objekt'] if o['id']=='prop_1'],[[202,404]])
        self.assertFalse(p['tidskarta'][1]['ljud'])

    def test_fel_edit_ar_atomisk(self):
        p=self.plan([self.edit('duplicera_scen',scen='s1',ny_id='s2',efter=None,med_ljud=True),
                     self.edit('ta_bort_prop',prop='prop_1',scen='s2'),
                     self.edit('byt_prop',prop='prop_1',ny_typ='ny')])
        self.assertEqual(p['ej_tillampat'][0]['op'],'byt_prop')
        self.assertEqual(next(o for o in p['objekt'] if o['id']=='prop_1')['namn'],'rum:card payment terminal:prop_1')

    def test_revision_och_hash_stoppar(self):
        self.r['kalla']['revision']=2
        with self.assertRaisesRegex(ValueError,'revision'): self.plan()
        self.r['kalla']['revision']=1; self.k['matning']['personer'][0]['rorelse']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'sha256'): self.plan()

    def test_senare_trim_kan_inte_aterinföra_rutor(self):
        e=self.edit('trimma_scen',scen='s1',slut_s=3,lage='klipp_slut'); e2=dict(e,id='andra',slut_s=4)
        p=self.plan([e,e2]); self.assertEqual(len(p['kallrutor']),90); self.assertEqual(len(p['ej_tillampat']),1)

    def test_ord_skydd_och_tom_tidslinje(self):
        self.k['semantik']['repliker']=[dict(id='r1',talare='1',sprak='sv',text='Hej',start_s=1,slut_s=2,i_bild=True,scen='s1',ord=[],kalla='cm')]
        p=self.plan([self.edit('trimma_scen',scen='s1',slut_s=1.5,lage='replik_sakert')]); self.assertEqual(len(p['ej_tillampat']),1)
        with self.assertRaisesRegex(ValueError,'Alla scener'): self.plan([self.edit('ta_bort_scen',scen='s1')])

    def test_kalla_utan_tillforlitlighet(self):
        import shutil
        for namn in ('meta.json','sekvens_1.npz','varld.npz'):
            shutil.copy2(INGEST/'ut/bar'/namn,self.ut/namn)
        video=KALLA.parent/ladda(KALLA)['klipp']['video']['sokvag']
        k=bygg(self.ut,self.ut/'ny.json',video)
        self.assertIsNone(k['matning']['personer'][0]['rutor_otillforlitliga'])
        self.assertIsNone(k['matning']['personer'][0]['palitlighet'])
        self.assertTrue(any(p['status']=='saknas' for p in k['matning']['kvalitet']))

    def meta_ns(self):
        # Kör den verkliga funktionen isolerad; inga ingest-steg eller GPU-importer.
        import cv2
        tree=ast.parse((INGEST/'ingest_klipp.py').read_text(encoding='utf-8'))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='meta')
        ns=dict(cv2=cv2,json=json,hashlib=hashlib); exec(compile(ast.Module(body=[fn],type_ignores=[]),'meta','exec'),ns)
        return tree,ns

    def test_meta_framtid_och_legacy_cache(self):
        tree,ns=self.meta_ns()
        video=(KALLA.parent/ladda(KALLA)['klipp']['video']['sokvag']).resolve()
        m=ns['meta'](video,self.ut); self.assertEqual(m['kallvideo'],str(video))
        self.assertEqual(m['kallvideo_sha256'],hashlib.sha256(video.read_bytes()).hexdigest())
        legacy=(INGEST/'ut/bar/meta.json').read_bytes(); (self.ut/'meta.json').write_bytes(legacy)
        ns['meta'](video,self.ut); self.assertEqual((self.ut/'meta.json').read_bytes(),legacy)
        # Det enda övriga ändrade moduluttrycket är hashlib-importen. main() jämförs inte: static-kamera-fixen
        # (kamera-steget giltigt vid 0 registrerade rutor) och plan-argumentet ändrar den medvetet.
        original=ast.parse((UT/'original/ingest_klipp.py').read_text(encoding='utf-8'))
        def utan_meta(t): return ast.dump(ast.Module(body=[n for n in t.body if not isinstance(n,ast.Import) and not (isinstance(n,ast.FunctionDef) and n.name in ('meta','main'))],type_ignores=[]))
        self.assertEqual(utan_meta(tree),utan_meta(original))

    def test_meta_tom_trasig_och_saknad_video(self):
        _,ns=self.meta_ns(); video=(KALLA.parent/ladda(KALLA)['klipp']['video']['sokvag']).resolve()
        for trasig in (b'', b'{"fps": 3', b'[1]'):
            (self.ut/'meta.json').write_bytes(trasig)
            m=ns['meta'](video,self.ut); self.assertIn('kallvideo_sha256',m)
            self.assertEqual(json.loads((self.ut/'meta.json').read_text()),m)
        self.assertEqual([p.name for p in self.ut.iterdir()],['meta.json'])   # ingen kvarglömd temporärfil (atomisk skrivning)
        (self.ut/'meta.json').unlink()
        m=ns['meta'](self.ut/'finns_inte.mp4',self.ut)   # som före ändringen: ingen krasch, ingen proveniens
        self.assertNotIn('kallvideo',m); self.assertEqual(json.loads((self.ut/'meta.json').read_text()),m)

    def test_rum_cache_ignorerar_mhr_rig(self):
        sys.path.insert(0,str(INGEST))
        try: import rum
        finally: sys.path.remove(str(INGEST))
        bar=INGEST/'ut/bar'; clip=KALLA.parent/ladda(KALLA)['klipp']['video']['sokvag']
        for namn in ('varld.npz','masker.npy','kamera.json','meta.json','sekvens_1.npz','sekvens_2.npz'): shutil.copy2(bar/namn,self.ut/namn)
        (self.ut/'rum').mkdir()
        for namn in ('rum.json','rum.md','rum/cloud.npz','rum/overlay.jpg'): (self.ut/namn).write_bytes(b'x')
        sig=rum.input_signature(clip,self.ut); self.assertNotIn('mhr_rig.py',sig['hashes'])
        gammal=copy.deepcopy(sig); gammal['hashes']['mhr_rig.py']='0'*64   # så såg en äldre cache ut
        skriv(self.ut/'rum/cache.json',gammal); self.assertTrue(rum.cache_valid(clip,self.ut))
        skriv(self.ut/'rum/cache.json',sig); self.assertTrue(rum.cache_valid(clip,self.ut))
        sig['hashes']['rum.py']='0'*64; skriv(self.ut/'rum/cache.json',sig); self.assertFalse(rum.cache_valid(clip,self.ut))
        (self.ut/'rum/cache.json').write_bytes(b''); self.assertFalse(rum.cache_valid(clip,self.ut))

    def test_stadar_efter_sig(self):
        t=Flode('test_bar_och_determinism'); t.setUp(); d=t.ut; self.assertTrue(d.is_dir()); t.doCleanups(); self.assertFalse(d.exists())

    def test_avrundade_tider_ger_narmaste_ruta(self):
        original=self.k['semantik']['scener'][0]
        self.k['semantik']['scener']=[dict(original,id='s1',slut_s=0.667),dict(original,id='s2',start_s=0.667,slut_s=2.0667),dict(original,id='s3',start_s=2.0667)]
        p=self.plan([])
        self.assertEqual([t['kalla'] for t in p['tidskarta']],[[0,20],[20,62],[62,202]])   # ceil gav 21 och 63
        self.assertEqual(p['kallrutor'],list(range(202)))

    def test_prop_utan_plats_uppfinns_inte(self):
        p=self.plan([dict(self.edit('lagg_till_prop',ny_id='ny',typ='skylt',scen='s1',matt_m=[.3,.5,.1]),id='utan_plats')])
        self.assertEqual([e['id'] for e in p['ej_tillampat']],['utan_plats']); self.assertIn('Placering saknas',p['ej_tillampat'][0]['orsak'])
        self.assertFalse(p['tillampat']); self.assertNotIn('ny',[o['id'] for o in p['objekt']])

    def test_standardvarden_markeras_och_tomma_edits_nekas(self):
        kam=lambda i,**kw: dict(id=i,op='renderkamera',ursprung=dict(typ='cm'),scen='s1',kamera_id='rk_1',lage='stativ',**kw)
        cast=lambda i,namn,farg: dict(id=i,op='casta',ursprung=dict(typ='cm'),person='1',kundroll=dict(id='r',namn=namn),utseende=dict(troja_farg=farg,harstil=None),rost=None)
        trim=lambda i,**kw: dict(id=i,op='trimma_scen',ursprung=dict(typ='cm'),scen='s1',lage='klipp_slut',**kw)
        p=self.plan([kam('fov_null',inramning='halv',mal=dict(typ='person',id='1',punkt=None),fov_grader=None),
                     kam('fov_satt',inramning='halv',mal=dict(typ='person',id='1',punkt='kropp'),fov_grader=50),
                     cast('cast_rollnamn','Bartender',None), cast('cast_inget','Bartender',None), cast('cast_roll','Kund',None), cast('cast_farg','Kund','#2f4f6f'),
                     trim('trim_samma',slut_s=6.7333)])
        ok={e['id']:e for e in p['tillampat']}; nej={e['id']:e['orsak'] for e in p['ej_tillampat']}
        self.assertEqual([(d['falt'],d['varde']) for d in ok['fov_null']['andring']['standardvarden']],[('fov_grader',40),('mal.punkt','kropp (c_spine2)')])
        self.assertNotIn('standardvarden',ok['fov_satt']['andring'])
        # Källans roll är null: första castingen ändrar rollnamnet (tillämpas), den identiska andra ändrar ingenting.
        self.assertEqual(sorted(nej),['cast_inget','trim_samma'])
        self.assertEqual(sorted(ok),['cast_farg','cast_roll','cast_rollnamn','fov_null','fov_satt'])

    def test_kamera_pa_malet_avbryter_inte_kompileringen(self):
        bas=self.plan([]); pos=np.array(bas['renderkamera']['nycklar'][0]['matris'])[:3,3]
        bar=next(o for o in bas['objekt'] if o['id']=='bar_counter_1'); y=bar['rotation_rad'][2]
        Rz=np.array([[np.cos(y),-np.sin(y),0],[np.sin(y),np.cos(y),0],[0,0,1]]); off=(Rz.T@(pos-np.array(bar['pos_m']))).tolist()
        p=self.plan([self.edit('flytta_prop',prop='prop_1',scen='s1',till=dict(relativt='bar_counter_1',forskjutning_m=off)),
                     dict(id='kam_pa_mal',op='renderkamera',ursprung=dict(typ='cm'),scen='s1',kamera_id='rk_1',lage='stativ',inramning='halv',mal=dict(typ='prop',id='prop_1',punkt=None),fov_grader=40)])
        nej={e['id']:e['orsak'] for e in p['ej_tillampat']}
        self.assertEqual(len(p['tillampat']),1)   # flytten
        self.assertIn('sammanfaller',nej['kam_pa_mal'])


if __name__=='__main__': unittest.main(verbosity=2)
