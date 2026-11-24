"""Uppdatera slutdiagnostik; bevisa att renderad geometri/kamera är oförändrad."""
import hashlib
import json
import shutil
import time
from gemensamt import HIT,ladda,skriv
from kompilera import kompilera
from trohet import rapport

UT=HIT/'ut/notan'


def main():
    results=[]
    for name,clip,regi in [('golv_tom','notan',UT/'golv_tom/regi.json'),
                            ('golv_redigerad','notan',HIT/'exempel/notan/regi.json'),
                            ('golv_bar','bar',HIT/'exempel/bar/regi.json')]:
        d=UT/name;backup=UT/'fore_golv/slutmetadata'/name;backup.mkdir(parents=True,exist_ok=False)
        for f in ('plan.json','plan_trohet.json','plan_trohet.md','kvalitet.md'):
            if (d/f).exists():shutil.copy2(d/f,backup/f)
        old=ladda(d/'plan.json');start=time.perf_counter();new=kompilera(HIT/f'exempel/{clip}/kalla.json',regi)
        def geom(p):return {k:v for k,v in p.items() if k not in ('matning','kvalitet')}
        assert geom(old)==geom(new),name+' ändrade renderdata'
        digest=hashlib.sha256(json.dumps(geom(new),sort_keys=True).encode()).hexdigest()
        skriv(d/'plan.json',new);rapport(new,d/'plan.json')
        results.append(dict(mapp=name,renderdata_oforandrade=True,renderdata_sha256=digest,tid_s=time.perf_counter()-start))
    skriv(UT/'golv_metadata_verifiering.json',results);print(results,flush=True)


if __name__=='__main__':main()
