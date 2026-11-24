"""Installera propstödet med säkerhetskopior och oförändrade radslut."""
import json
from prop_filer import andra

def byt(s,a,b):
    if a not in s:raise ValueError('Saknar ändringsställe: '+a[:100])
    return s.replace(a,b,1)

def kompilator(s):
    s=byt(s,"        spar = [dict(matris=", "        from propplan import fran_kalla\n        for p in K['semantik']['props']:\n            obj=fran_kalla(p,sk['id'])\n            if obj is not None: objekt[obj['id']]=obj\n        spar = [dict(matris=")
    s=byt(s,"                if e.get('tillgang_id') or e.get('faste'): raise EjTillampad('Endast statiska lådor stöds; tillgång eller handfäste är inte implementerat.')",
          "                if e.get('tillgang_id'): raise EjTillampad('Extern proptillgång är reserverad; använd en typ i propbanken.')")
    s=byt(s,"                        o=dict(id=e['ny_id'],namn='rum:'+e['typ']+':'+e['ny_id'],typ='lada',matt_m=storlek(e.get('matt_m')),\n                               rotation_rad=[0,0,0],farg='#e2ac46',top_slope=0)\n                        placera(s,o,e.get('plats'),e.get('stod')); s['objekt'][o['id']]=o",
          "                        from propbank import BANK\n                        if e['typ'] in BANK:\n                            from propplan import ny\n                            o=ny(e)\n                            if not e.get('faste'): placera(s,o,e.get('plats'),e.get('stod'))\n                        else:\n                            if e.get('faste'): raise EjTillampad('Handfäste kräver en typ i propbanken.')\n                            o=dict(id=e['ny_id'],namn='rum:'+e['typ']+':'+e['ny_id'],typ='lada',matt_m=storlek(e.get('matt_m')),rotation_rad=[0,0,0],farg='#e2ac46',top_slope=0)\n                            placera(s,o,e.get('plats'),e.get('stod'))\n                        s['objekt'][o['id']]=o")
    s=byt(s,"                            placera(s,o,e['till'])", "                            placera(s,o,e['till'])\n                            if o['typ']=='rekvisita': o['propdata']['lage']='explicit'")
    s=byt(s,"                            o.update(namn='rum:'+e['ny_typ']+':'+e['prop'],farg='#e2ac46')\n                            if e.get('matt_m') is not None: o['matt_m']=storlek(e['matt_m'])",
          "                            if o['typ']=='rekvisita':\n                                from propplan import byt\n                                try: byt(o,e['ny_typ'],e.get('matt_m'))\n                                except ValueError as exc: raise EjTillampad(str(exc))\n                            else:\n                                o.update(namn='rum:'+e['ny_typ']+':'+e['prop'],farg='#e2ac46')\n                                if e.get('matt_m') is not None: o['matt_m']=storlek(e['matt_m'])")
    s=byt(s,"                kallbild_bredd=K['klipp']['video']['bredd'],tillampat=", "                kallbild_bredd=K['klipp']['video']['bredd'],tillampat=")
    s=byt(s,"    resolved_text=lostext", "    reks=[o for o in plan['objekt'] if o['typ']=='rekvisita']\n    if reks:\n        plan['props']=reks\n        plan['objekt']=[o for o in plan['objekt'] if o['typ']!='rekvisita']\n    resolved_text=lostext")
    # Även oförändrad rekvisita måste få en scen: hand/ytposition är per tagning.
    s=byt(s,"            if len(fk)==len(scener) and all(o==fk[0][1] for _,o in fk):", "            if fk[0][1]['typ']!='rekvisita' and len(fk)==len(scener) and all(o==fk[0][1] for _,o in fk):")
    s=byt(s,"    komplettera(plan, PL)", "    komplettera(plan, PL)\n    if plan.get('props'):\n        from propplan import los as los_props\n        los_props(plan)")
    return s

andra('scen/3d/kontrakt/kompilera.py',kompilator)
andra('scen/3d/ingest/mhr_rig.py',lambda s:byt(s,"    bygg_planrum(plan)\n", "    bygg_planrum(plan)\n    from prop_blender import bygg as bygg_props\n    bygg_props(plan)\n"))
andra('scen/3d/kontrakt/kvalitet.py',lambda s:byt(s,"    Path(fil).with_name('kvalitet.md').write_text", "    if plan.get('props'):\n        from propplan import rapportrader\n        rows += rapportrader(plan)\n    Path(fil).with_name('kvalitet.md').write_text"))

def schema(s):
    d=json.loads(s)
    d['$defs']['prop']['properties']['rekonstruktion']={
        'description':'Lokalt mätt bildregion, hand/surface och dokumenterade antaganden per scen. Värdenas ursprung och konfidens redovisas separat.',
        'type':'object','required':['schema_version','anvands','semantik_id','ursprung','bank','scener'],
        'properties':{
            'schema_version':{'description':'Propkontraktets version.','const':'prop/1'},
            'anvands':{'description':'Användning enligt semantiken.','type':'string'},
            'semantik_id':{'description':'Id i semantikfilen eller lokal observation.','type':'string'},
            'semantik_fil':{'description':'Lokal semantikfil som avlästs, inga nätanrop.','type':['string','null']},
            'ursprung':{'description':'Typ, modell och konfidens för identitet/användning.','type':'object'},
            'bank':{'description':'Parametrisk form i XYZ meter, greppunkt och delarnas relativa mått. Status mall; ingen verklig tillgång.','type':'object'},
            'scener':{'description':'Per scen: hållare, hand/led eller mallens yta; avlästa bildregioner, RGB och ursprung/konfidens för varje härledning.','type':'array','items':{'type':'object','required':['scen','lage','hallare','hand','led','yta','spar_id','bildregioner','ursprung'],
                 'properties':{'scen':{'type':'string'},'lage':{'enum':['hand','yta','kamera_hand']},'hallare':{'type':['string','null']},'hand':{'enum':['vanster','hoger',None]},'led':{'type':['string','null']},'yta':{'type':['string','null']},'spar_id':{'type':['string','null']},'bildregioner':{'type':'array'},'ursprung':{'type':'object'}},'additionalProperties':False}}
        },'additionalProperties':False}
    return json.dumps(d,ensure_ascii=False,indent=2)+'\n'
andra('scen/3d/kontrakt/kalla.schema.json',schema)
print('Propstöd installerat. Alla befintliga filer kopierade till fore_prop.')
