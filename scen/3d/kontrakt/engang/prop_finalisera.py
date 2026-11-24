"""Små kompletteringar efter första lokala kontraktskontrollen."""
import json
from prop_filer import andra

def schema(s):
    d=json.loads(s);p=d['$defs']['prop']['properties']['rekonstruktion']['properties']['scener']['items']['properties']
    descriptions=dict(scen='Scen-id.',lage='Handfäste, mallens yta eller kamerafäst förgrundshand.',hallare='Hållarens klipp-id eller null när föremålet inte bärs.',hand='Vald grepphand eller null.',led='MHR-lednamn eller null när handled saknas.',yta='Mallfamilj bord eller disk; null vid handfäste.',spar_id='Förgrundsspår ur personer_matning.json eller null.',bildregioner='Källruta, lokal ruta, avläst XYXY-region och median RGB per prov.',ursprung='Typ, metod och konfidens separat för hållare, placering, bildregion, färg och mått.')
    for key,desc in descriptions.items():p[key]['description']=desc
    return json.dumps(d,ensure_ascii=False,indent=2)+'\n'
andra('scen/3d/kontrakt/kalla.schema.json',schema)
andra('scen/3d/kontrakt/kompilera.py',lambda s:s.replace("if flerklipp: o['scen']=s['id']", "if flerklipp or o['typ']=='rekvisita': o['scen']=s['id']"))
andra('scen/3d/kontrakt/propplan.py',lambda s:s.replace("next(s for s in plan['scener'] if s['id']==o['scen'])", "next(s for s in (plan.get('scener') or plan['matkamera']['scener']) if s['id']==o['scen'])"))
