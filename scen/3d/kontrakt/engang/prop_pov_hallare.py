"""Förgrundshanden är kamerans spår, inte slaktarens kropp."""
import json
import sys
from prop_filer import andra,ROT

andra('scen/3d/kontrakt/kalla_prop.py',lambda s:s.replace("if clip=='b' and raw['id']=='o1' and sid=='s5': mode='kamera_hand'; track='2'", "if clip=='b' and raw['id']=='o1' and sid=='s5':\n                mode='kamera_hand'; track='2'; holder=None\n                owner_status=ursprung('modellbedomd','Kamerapersonens förgrundshand, spår 2 enligt ej_personer i semantiken; ingen full personidentitet mäts.','hog',modell=sem['ursprung']['modell'])"))
sys.path.insert(0,str(ROT/'scen/3d/kontrakt'))
from kalla_prop import fyll
base=ROT/'scen/3d/kontrakt/ut/b';sf=ROT/'scen/3d/kontrakt/semantik/ut/b/semantik.json'
out=fyll(json.loads((base/'kalla_jamn.json').read_text(encoding='utf-8')),base,json.loads(sf.read_text(encoding='utf-8')),'b',sf)
andra(str((base/'kalla_prop.json').relative_to(ROT)),lambda s:json.dumps(out,ensure_ascii=False,indent=2)+'\n')
