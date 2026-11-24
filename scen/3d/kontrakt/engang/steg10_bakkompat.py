"""Behåll tidigare planformat för propedits som saknar tidsankare."""
from steg10_filer import andra
from steg10_koppla import ersatt

def fix(s):
    marker = "                    changed=andra_prop(s,e.get('ny_id') if op=='lagg_till_prop' else e['prop'],span,redigera)\n                    if changed is not None: andring[s['id']]=changed"
    return ersatt(s, marker, """                    pid=e.get('ny_id') if op=='lagg_till_prop' else e['prop']
                    versions=bool(s['objekt'].get(pid,{}).get('_propversioner'))
                    changed=andra_prop(s,pid,span,redigera)
                    if changed is not None:
                        if tidsbeslut_edit or versions: andring[s['id']]=changed
                        else: andring[s['id']]=copy.deepcopy(s['objekt'][pid]) if op!='ta_bort_prop' else dict(borttaget=pid)""")
andra('scen/3d/kontrakt/kompilera.py',fix)
