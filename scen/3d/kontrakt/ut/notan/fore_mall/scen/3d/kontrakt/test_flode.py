"""Lokala regressioner. Varje test skapar ut/bar/test_* och tar bort just den mappen när testet är klart."""
import ast
import copy
import hashlib
import json
import math
import shutil
import tempfile
import sys
import unittest
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
from gemensamt import HIT, ladda, skriv
from kalla_bygg import bygg, sha
from kalla_flera import bygg_flera
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


def _piper():
    try: import tal; tal.mat_langd('nst','Hej.'); return True
    except Exception: return False


class BarOforandrad(unittest.TestCase):
    def test_barplanen_ar_byteidentisk_med_referensen(self):
        # Referens efter bar-omkörningen (tider.json fick ny hash); plan.json är den äldre och rörs inte.
        ut=Path(tempfile.mkdtemp(prefix='test_',dir=UT)); self.addCleanup(shutil.rmtree,ut,ignore_errors=True)
        skriv(ut/'plan.json',kompilera(KALLA,REGI))
        self.assertEqual((ut/'plan.json').read_bytes(),(UT/'plan_efter_baromkorning.json').read_bytes())


KALLA_N=HIT/'exempel/notan/kalla.json'; REGI_N=HIT/'exempel/notan/regi.json'; UT_N=HIT/'ut/notan'


class Notan(unittest.TestCase):
    def setUp(self):
        UT_N.mkdir(parents=True,exist_ok=True)
        self.ut=Path(tempfile.mkdtemp(prefix='test_',dir=UT_N)); self.addCleanup(shutil.rmtree,self.ut,ignore_errors=True)
        self.r=ladda(REGI_N)

    def plan(self, edits):
        self.r['edits']=edits; skriv(self.ut/'regi.json',self.r)
        return kompilera(KALLA_N,self.ut/'regi.json')

    def cm(self,id,op,**kw): return dict(id=id,op=op,ursprung=dict(typ='cm'),**kw)

    def repl(self,id,replik,text): return self.cm(id,'byt_replik',replik=replik,text=text,sprak='sv',rost=dict(motor='piper',rost_id=None,stil=None),tidspolicy='samma_lucka',max_talfaktor=None)

    def test_flerklippskalla_ider_rutor_och_roller(self):
        k=bygg_flera(INGEST/'ut/notan-tagningar',self.ut/'kalla.json',HIT.parents[1]/'klipp/d-dialog-notan.mp4',HIT.parent/'scen3d.json',HIT.parent/'data/ordtider.json',sha)
        sc=k['semantik']['scener']; fps=30
        self.assertEqual([s['id'] for s in sc],['s%d'%i for i in range(1,8)])
        rutor=[(round(s['start_s']*fps),round(s['slut_s']*fps)) for s in sc]
        self.assertEqual(rutor,[(0,73),(73,114),(114,171),(171,256),(256,281),(281,337),(337,383)])   # sammanhängande och täcker 0-383
        self.assertTrue(all(x[1]==y[0] for x,y in zip(rutor,rutor[1:]))); self.assertEqual(k['tidsbas']['antal_rutor'],383)
        # roll per tagning ur scen3d.json: A,B,A,C,B,A,B; S4:s extra person (ingest-id 4) får ingen roll
        self.assertEqual([s['personer'][0] for s in sc],['A','B','A','C','B','A','B'])
        self.assertEqual(sc[3]['personer'],['C','okand_s4_4'])
        roller={p['id']:p for p in k['semantik']['personer']}
        self.assertEqual((roller['C']['roll'],roller['C']['roll_kalla']),('waiter','scen3d')); self.assertIsNone(roller['okand_s4_4']['roll'])
        mp={(m['scen'],m['ingest_id']):m['person'] for m in k['matning']['personer']}
        self.assertEqual(mp[('s4','1')],'C'); self.assertEqual(mp[('s4','4')],'okand_s4_4'); self.assertEqual(mp[('s7','1')],'B')
        # varje scen pekar på egna mätfiler
        self.assertEqual([c['kalla_ruta0'] for c in k['matning']['kameror']],[a for a,_ in rutor])
        self.assertEqual(len({m['rorelse']['sokvag'] for m in k['matning']['personer']}),len(k['matning']['personer']))
        # funktion ur beat; reaction har ingen motsvarighet
        self.assertEqual([s['funktion'] for s in sc],['krok','uppbyggnad','uppbyggnad','vandning',None,'punchline','avslut'])
        kv={p['post']:p for p in k['matning']['kvalitet']}
        self.assertEqual(kv['semantik.scener.funktion']['status'],'antagen'); self.assertEqual(kv['semantik.scener.s5.funktion']['status'],'saknas')
        self.assertEqual(kv['semantik.personer.roll']['status'],'antagen')
        self.assertEqual(len(k['semantik']['repliker']),7); self.assertEqual(k['semantik']['repliker'][0]['ord'][0]['ord'],'Men')
        self.assertIsNone(k['matning']['korlogg'])   # körloggen hashlåses inte

    def test_tom_regi_ger_alla_rutor_i_ordning(self):
        p=self.plan([]); self.assertEqual(p['kallrutor'],list(range(383)))
        self.assertEqual([t['kalla'] for t in p['tidskarta']],[[0,73],[73,114],[114,171],[171,256],[256,281],[281,337],[337,383]])
        self.assertEqual([d['lokal_start'] for d in p['scener']],[0]*7); self.assertEqual(p['tal'],[])
        self.assertEqual(len({d['varld'] for d in p['scener']}),7)

    @unittest.skipUnless(_piper(),'Piper eller röstfiler saknas')
    def test_replikbyte_passar_stracks_nekas(self):
        p=self.plan([self.repl('kort','r7','Men jag känner dig ju inte?'),self.repl('lite_langre','r4','Eller liksom bara betala halva åtminstone?'),
                     self.repl('lang','r1','Men vänta nu, menar du verkligen att du inte tänker betala notan i kväll?')])
        ok={e['id']:e['andring'] for e in p['tillampat']}; nej={e['id']:e['orsak'] for e in p['ej_tillampat']}
        self.assertEqual(ok['kort']['utfall'],'passar'); self.assertEqual(ok['kort']['stracka_procent'],0.0)
        self.assertEqual(ok['lite_langre']['utfall'],'stracks'); self.assertTrue(0<ok['lite_langre']['stracka_procent']<=15)
        self.assertIn('Nekad',nej['lang']); self.assertEqual([t['replik'] for t in p['tal']],['r4','r7'] if p['tal'][0]['replik']=='r4' else ['r7','r4'])
        t7=next(t for t in p['tal'] if t['replik']=='r7')
        self.assertEqual(t7['slot_langd_s'],1.02); self.assertEqual(t7['ut_slot_s'],[11.16,12.18])   # inget bortklippt: utdatatid = källtid
        # nekad replik ändrar ingenting: originalet finns kvar och planen är i övrigt oförändrad
        self.assertEqual(p['kallrutor'],list(range(383)))

    @unittest.skipUnless(_piper(),'Piper eller röstfiler saknas')
    def test_borttagen_scen_flyttar_senare_repliker(self):
        p=self.plan([self.cm('bort','ta_bort_scen',scen='s1'),self.repl('r3kort','r3','Så gör en gentleman.'),self.repl('r2','r2','Varför ska jag ta notan?'),
                     self.repl('r1_bort','r1','Men vadå, ska inte du betala?')])
        self.assertEqual(p['kallrutor'],list(range(73,383))); self.assertEqual(p['tidskarta'][0]['ut'],[0,41])
        ok={e['id']:e['andring'] for e in p['tillampat']}; nej={e['id']:e['orsak'] for e in p['ej_tillampat']}
        self.assertEqual(p['tal'][0]['ut_slot_s'],[round(3.82-73/30,4),round(3.82-73/30+1.86,4)])   # tidigare än källans 3,82-5,68
        self.assertIn('inte hel i utdata',nej['r1_bort'])   # r1 ligger helt i den borttagna scenen
        # r2 (2,38-3,56) börjar 0,05 s före s2 men s1 är borta: luckan klipps av scengränsen och byts inte
        self.assertIn('inte hel i utdata',nej['r2']); self.assertNotIn('r2',ok)

    @unittest.skipUnless(_piper(),'Piper eller röstfiler saknas')
    def test_regins_exempel(self):
        p=self.plan(ladda(REGI_N)['edits'])
        self.assertEqual([e['id'] for e in p['tillampat']],['e1','e3','e4','e5','e6']); self.assertEqual([e['id'] for e in p['ej_tillampat']],['e2'])
        self.assertEqual(p['kallrutor'],list(range(0,114))+list(range(171,383)))
        self.assertEqual(len([o for o in p['objekt'] if o.get('scen')=='s3']),0)   # platsens objekt har ingen scen
        farg={x['id']:x['farg'] for x in p['personer']}; self.assertEqual(farg['B'],'#d1495b'); self.assertNotEqual(farg['A'],'#d1495b')
        # senare repliker flyttas 1,9 s (s3 = 57 rutor) i utdatatiden
        self.assertEqual(next(t for t in p['tal'] if t['replik']=='r7')['ut_slot_s'][0],round(11.16-57/30,4))
        # renderkameran i s1 är ändrad medan s2 behåller uppmätt kamera
        t0=self.plan([]); self.assertNotEqual(p['renderkamera']['nycklar'][0],t0['renderkamera']['nycklar'][0]); self.assertEqual(p['renderkamera']['nycklar'][73],t0['renderkamera']['nycklar'][73])

    @unittest.skipUnless(_piper(),'Piper eller röstfiler saknas')
    def test_kompilering_ar_deterministisk(self):
        e=ladda(REGI_N)['edits']; a=self.plan(e); skriv(self.ut/'a.json',a); skriv(self.ut/'b.json',self.plan(e))
        self.assertEqual((self.ut/'a.json').read_bytes(),(self.ut/'b.json').read_bytes())


# ---------------------------------------------------------------- plats (ingest/plats.py, kalla.platser, plan.plats)
INGEST_N=INGEST/'ut/notan-tagningar'; PLATS_N=INGEST_N/'plats/plats.json'; REGI_BYT=HIT/'exempel/notan/regi_byt_lokal.json'


def _plats_modul():
    sys.path.insert(0,str(INGEST))
    import plats; return plats


class Plats(unittest.TestCase):
    def setUp(self):
        UT_N.mkdir(parents=True,exist_ok=True)
        self.ut=Path(tempfile.mkdtemp(prefix='test_',dir=UT_N)); self.addCleanup(shutil.rmtree,self.ut,ignore_errors=True)

    def test_transformer_ger_samma_punkt_i_platsen(self):
        # Punkter som bildmatchningen sett i två tagningar (S3, S6 mot S1) ska hamna på samma ställe i platsen, inom 0,25 m (median).
        # Uppmätt: 0,13 respektive 0,23 m; resten är vertikal skillnad mellan matchningen och golvantagandet plus några graders tyngdkraftsfel.
        import argparse
        pl=_plats_modul(); P=ladda(PLATS_N); reg={t['id']:np.array(t['till_plats']['matris']) for t in P['tagningar']}
        tl,_=pl.hitta_tagningar(INGEST_N); T=[pl.ladda_tagning(i,d) for i,d in tl]
        _,acc=pl.matcha_par(T,argparse.Namespace(video=None)); self.assertGreaterEqual(len(acc),2)
        for (j,i),a in acc.items():
            fran=a['Xfran']@reg[j][:3,:3].T+reg[j][:3,3]; till=a['Xtill']@reg[i][:3,:3].T+reg[i][:3,3]
            med=float(np.median(np.linalg.norm(fran-till,axis=1))); self.assertLess(med,0.25,(j,i,med))
        self.assertEqual([t['kvalitet']['metod'] for t in P['tagningar']],['landmark','landmark','matchning','antagande','landmark','matchning','landmark'])
        # transformen är en ren rotation kring Z med skala 1
        for m in reg.values():
            self.assertTrue(np.allclose(m[:3,:3]@m[:3,:3].T,np.eye(3))); self.assertTrue(np.allclose(m[2,:3],[0,0,1])); self.assertTrue(np.allclose(m[3],[0,0,0,1]))

    def test_bar_identitet_ger_samma_plan(self):
        import argparse
        pl=_plats_modul()
        a=argparse.Namespace(ingest=str(INGEST/'ut/bar'),ut=str(self.ut/'p'),scen3d=None,hand=None,video=None)
        P,matt,ut,tl,reg=pl.bygg_plats(a); self.assertEqual(len(P['tagningar']),1)
        self.assertTrue(np.array_equal(np.array(P['tagningar'][0]['till_plats']['matris']),np.eye(4))); self.assertEqual(P['tagningar'][0]['kvalitet']['metod'],'identitet')
        rum=ladda(INGEST/'ut/bar/rum.json'); self.assertEqual(P['golv']['hojd_m'],rum['floor']['height'])
        skriv(ut/'plats.json',P)
        k=bygg(INGEST/'ut/bar',self.ut/'kalla.json',None,ut/'plats.json'); skriv(self.ut/'kalla.json',k)
        self.assertEqual(k['semantik']['scener'][0]['plats_id'],'plats_1')
        plan=kompilera(self.ut/'kalla.json',REGI); ref=kompilera(KALLA,REGI)
        for nyckel in ('objekt','renderkamera','personer','kallrutor','tidskarta','tillampat','ej_tillampat','utdata','kallbild_bredd'): self.assertEqual(plan[nyckel],ref[nyckel],nyckel)
        self.assertEqual(plan['plats'][0]['id'],'plats_1'); self.assertNotIn('scener',plan)

    def test_ankare_och_bindningar(self):
        P=ladda(PLATS_N); ids={a['id'] for a in P['ankare']}
        self.assertEqual(ids,{'stol_A','stol_B','bordskant_A','bordskant_B','staplats_C'})
        for b in P['bindningar']: self.assertIn(b['ankare'],ids); self.assertLess(b['avstand_till_ankare_m'],0.15)
        self.assertEqual({(b['tagning'],b['roll']) for b in P['bindningar']},{('S1','A'),('S2','B'),('S3','A'),('S4','C'),('S5','B'),('S6','A'),('S7','B')})
        K=ladda(KALLA_N); sc={s['id']:s for s in K['semantik']['scener']}
        self.assertEqual([(b['person'],b['ankare']) for b in sc['s4']['bindningar']],[('C','staplats_C')])   # okand_s4_4 är obunden
        self.assertEqual({a['id'] for a in K['semantik']['platser'][0]['ankare']},ids)
        a={x['id']:x for x in P['ankare']}; self.assertEqual(a['stol_A']['pos_m'][2],0.0); self.assertGreater(a['stol_B']['pos_m'][1]-a['stol_A']['pos_m'][1],1.5)
        self.assertAlmostEqual(abs(((a['stol_A']['riktning_rad']-a['stol_B']['riktning_rad'])+math.pi)%(2*math.pi)-math.pi),math.pi,delta=0.05)   # vända mot varandra

    def test_platssteget_ar_deterministiskt(self):
        import subprocess
        for n in 'ab':
            subprocess.run([sys.executable,'-I',str(INGEST/'plats.py'),str(INGEST_N),'--ut',str(self.ut/n),'--hand',str(INGEST_N/'plats/hand.json')],check=True,capture_output=True)
        for f in ('plats.json','plats_matt.json'): self.assertEqual((self.ut/'a'/f).read_bytes(),(self.ut/'b'/f).read_bytes(),f)
        self.assertEqual((self.ut/'a/plats.json').read_bytes(),PLATS_N.read_bytes())

    def test_planen_har_ett_rum_och_ar_deterministisk(self):
        r=ladda(REGI_N); r['edits']=[]; skriv(self.ut/'regi.json',r)
        a=kompilera(KALLA_N,self.ut/'regi.json'); skriv(self.ut/'a.json',a); skriv(self.ut/'b.json',kompilera(KALLA_N,self.ut/'regi.json'))
        self.assertEqual((self.ut/'a.json').read_bytes(),(self.ut/'b.json').read_bytes())
        self.assertEqual(len({o['id'] for o in a['objekt']}),len(a['objekt']))   # varje objekt en gång
        self.assertTrue(all(o['synlig_ut']==[0,383] for o in a['objekt'])); self.assertTrue(all('till_plats' in d for d in a['scener']))
        self.assertEqual(next(o for o in a['objekt'] if o['id']=='golv')['pos_m'][2],0.0)
        # S1:s kamera står i platsen på ungefär 1 m från stol_A (uppmätt 0,99 m) och ser mot den
        m=np.array(a['renderkamera']['nycklar'][0]['matris']); stol=np.array(next(x for x in a['plats'][0]['ankare'] if x['id']=='stol_A')['pos_m'])
        self.assertLess(abs(np.hypot(*(m[:2,3]-stol[:2]))-1.0),0.2)
        blick=-m[:3,2]; mot=stol-m[:3,3]; mot[2]=0; mot/=np.linalg.norm(mot); b=blick.copy(); b[2]=0; b/=np.linalg.norm(b); self.assertGreater(float(b@mot),0.95)

    def test_byt_lokal_flyttar_personerna_med_ankarna(self):
        self.r=ladda(REGI_BYT); skriv(self.ut/'regi.json',self.r)
        a=kompilera(KALLA_N,self.ut/'regi.json'); self.assertEqual([e['id'] for e in a['tillampat']],['e1']); self.assertEqual(a['ej_tillampat'],[])
        r0=ladda(REGI_N); r0['edits']=[]; skriv(self.ut/'tom.json',r0); b=kompilera(KALLA_N,self.ut/'tom.json')
        ga={x['id']:x for x in ladda(PLATS_N)['ankare']}; na={x['id']:x for x in ladda(HIT/'plats_bank/fiktiv_lokal.json')['ankare']}
        bind={s['id']:s for s in ladda(KALLA_N)['semantik']['scener']}
        for d0,d1 in zip(b['scener'],a['scener']):
            ref=sorted(bind[d0['id']]['bindningar'],key=lambda x:x['person'])[0]['ankare']
            # det gamla ankaret, uttryckt i tagningens värld, ska hamna på det nya ankarets läge och riktning
            M0=np.array(d0['till_plats']); M1=np.array(d1['till_plats']); q=M1@(np.linalg.inv(M0)@np.array([*ga[ref]['pos_m'],1.0]))
            self.assertTrue(np.allclose(q[:3],na[ref]['pos_m'],atol=1e-6),(d0['id'],q[:3],na[ref]['pos_m']))
            yaw=math.atan2(M1[1,0],M1[0,0])-math.atan2(M0[1,0],M0[0,0]); self.assertAlmostEqual(((yaw-(na[ref]['riktning_rad']-ga[ref]['riktning_rad']))+math.pi)%(2*math.pi)-math.pi,0,places=6)
        self.assertEqual({o['id'] for o in a['objekt']},{'golv','bakvagg','disk','bord_fiktivt'}); self.assertEqual(a['plats'][0]['id'],'fiktiv_lokal')

    def test_byt_lokal_nekas_med_orsak(self):
        r=ladda(REGI_BYT); r['edits'][0]['rum']['tillgang_id']='finns_inte'; skriv(self.ut/'regi.json',r)
        a=kompilera(KALLA_N,self.ut/'regi.json'); self.assertEqual(a['tillampat'],[]); self.assertIn('platsbanken',a['ej_tillampat'][0]['orsak'])
        bank=self.ut/'bank'; bank.mkdir(); ny=ladda(HIT/'plats_bank/fiktiv_lokal.json'); ny['ankare']=[x for x in ny['ankare'] if x['id']!='stol_A']; skriv(bank/'fiktiv_lokal.json',ny)
        r['edits'][0]['rum']['tillgang_id']='fiktiv_lokal'; skriv(self.ut/'regi.json',r)
        a=kompilera(KALLA_N,self.ut/'regi.json',bank); self.assertEqual(a['tillampat'],[]); self.assertIn('ingen bunden person',a['ej_tillampat'][0]['orsak'])   # atomisk: s1 saknar stol_A


if __name__=='__main__': unittest.main(verbosity=2)
