"""Bar före propstödet och notans jämn-film: människor, kamera och tid."""
import json
import sys
import time
from pathlib import Path

H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H))
from kompilera import kompilera
from gemensamt import ladda,skriv
from kvalitet import skriv as kvalitet

out=H/'ut/prop_granskning';results=[]
start=time.perf_counter();bar=kompilera(H/'exempel/bar/kalla.json',H/'exempel/bar/regi.json')
skriv(out/'bar_plan_prop.json',bar);kvalitet(bar,out/'bar_plan_prop.json')
# Kvalitetssidan ovan hör till bar, spara under ett eget nytt namn.
(out/'kvalitet.md').rename(out/'bar_kvalitet_prop.md')
for name,old,new in [('bar',ladda(H/'ut/bar/plan_efter_baromkorning.json'),bar),('notan',ladda(H/'ut/notan/jamn_tom/plan.json'),ladda(H/'ut/notan/prop_tom/plan.json'))]:
    checks={k:old.get(k)==new.get(k) for k in ['personer','renderkamera','kallrutor','tidskarta','scener']}
    results.append(dict(klipp=name,kontroller=checks,gron=all(checks.values())))
    print(results[-1],flush=True)
(out/'regression.json').write_text(json.dumps(dict(sek=round(time.perf_counter()-start,2),resultat=results),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if not all(x['gron'] for x in results):sys.exit(1)
