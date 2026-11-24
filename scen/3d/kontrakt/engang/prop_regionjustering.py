"""Justera avläsning efter att ha öppnat regionernas källbildsbevis."""
import json
from prop_filer import andra

def refs(s):
    d=json.loads(s)
    d['b']['o1']['s3'][1]=[0,.53,.64,.68]
    d['b']['o1']['s5']=[[0,.48,.97,.81],[0,.48,.97,.82]]
    d['b']['o1']['s9']=[None,None]
    d['kenny']['o1']['s1']=[[.32,.63,.53,.79],[.15,.27,.46,.37]]
    d['kenny']['o2']['s2']=[[.34,.48,.64,.70],[.34,.00,.65,.58]]
    d['a']['o2']['s3'][1]=[.66,.74,1,.97]
    d['a']['o3']['s7']=[[.16,.68,1,.84],[.49,.68,1,.86]]
    d['notan']['o1']['s7']=[[.45,.43,.62,.50],[.45,.43,.62,.50]]
    return json.dumps(d,ensure_ascii=False,indent=2)+'\n'
andra('scen/3d/kontrakt/prop_referenser.json',refs)
andra('scen/3d/kontrakt/kalla_prop.py',lambda s:s.replace("                box = np.array(box)*[w,h,w,h];", "                if box is None: continue  # Produkten ligger utanför bilden; ingen region uppfinns.\n                box = np.array(box)*[w,h,w,h];")
    .replace("sid in ('s8','s9','s10','s11')", "sid in ('s8','s9','s10')")
    .replace("if clip=='a' and sid in ('s3','s6'): mode='yta'", "if clip=='a' and sid=='s6': mode='yta'")
    .replace("if mode=='hand' and holder:", "if mode=='hand' and holder and records:"))
