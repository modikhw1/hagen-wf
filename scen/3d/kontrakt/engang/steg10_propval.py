"""Låt ett ospecificerat propbyte träffa just de scener där propens id finns."""
import json
from steg10_filer import andra
from steg10_koppla import ersatt


def compiler(s):
    marker="                for s in valda(e):\n                    def redigera(o):"
    return ersatt(s,marker,"                for s in valda(e):\n                    if op!='lagg_till_prop' and e.get('scen','alla')=='alla' and e['prop'] not in s['objekt']: continue\n                    def redigera(o):")
andra('scen/3d/kontrakt/kompilera.py',compiler)


def schema(s):
    d=json.loads(s)
    d['$defs']['byt_prop']['properties']['scen']=dict(description='Valfri scen. Utan scen ändras de scener där föremålet finns.',type='string',minLength=1)
    return json.dumps(d,ensure_ascii=False,indent=2)+'\n'
andra('scen/3d/kontrakt/regi.schema.json',schema)


def scan(s):
    return ersatt(s,"    changed = []\n", "    if not isinstance(k, dict) or k.get('schema_version') != 'kalla/1': return []\n    changed = []\n")
andra('scen/3d/ingest/kallstatus.py',scan)


def tests(s):
    marker='    def test_eventunderlag_far_inte_hashas_om_tyst(self):'
    return ersatt(s,marker,'''    def test_byte_utan_scen_traf_finns_bara_i_en_scen(self):
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

''' + marker)
andra('scen/3d/kontrakt/test_handelser.py',tests)
