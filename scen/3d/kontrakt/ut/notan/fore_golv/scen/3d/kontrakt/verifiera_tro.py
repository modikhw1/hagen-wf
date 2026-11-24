"""Lokala trohetsfilmer i nya mappar; inga ingeststeg eller GUI-anrop."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import shutil
from gemensamt import HIT,skriv
from kompilera import kompilera
from trohet import rapport,mat
from verifiera_mall import blender

ROT=HIT.parents[2];UT=HIT/'ut/notan';INGEST=HIT.parent/'ingest'


def main():
    os.environ['PYTHONIOENCODING']='utf-8';tider={};exe=blender()
    def run(name,args,log):
        t=time.perf_counter()
        with log.open('w',encoding='utf-8') as f:
            r=subprocess.run(args,cwd=ROT,env=os.environ,stdout=f,stderr=subprocess.STDOUT)
        tider[name]=dict(tid_s=time.perf_counter()-t,exitkod=r.returncode)
        skriv(UT/'tider_tro.json',tider);print(name,tider[name],flush=True)
        if r.returncode:
            text=log.read_text(encoding='utf-8',errors='replace')
            if 'ig9icd64.dll' not in text:raise RuntimeError(name+' misslyckades: '+text[-1500:])
    for name,rf in [('tro_tom',UT/'tro_tom/regi.json'),('tro_redigerad',HIT/'exempel/notan/regi.json')]:
        d=UT/name;d.mkdir(exist_ok=True)
        if (d/'film.mp4').exists():
            if '--ersatt-eget-prov' not in sys.argv:raise FileExistsError(d/'film.mp4')
            # Bara denna körnings egna första prov. Tidigare mall/plats-mappar rörs aldrig.
            backup=UT/'fore_tro/eget_forsta_prov'/name
            if backup.exists():raise FileExistsError(backup)
            shutil.copytree(d,backup)
        t=time.perf_counter();p=kompilera(HIT/'exempel/notan/kalla.json',rf);skriv(d/'plan.json',p);rapport(p,d/'plan.json')
        tider[name+'_kompilering']=dict(tid_s=time.perf_counter()-t)
        run(name+'_ljud',[sys.executable,str(HIT/'bygg_ljud.py'),str(d/'plan.json'),str(d/'ljud.wav'),str(d/'ljud_rapport.json')],d/'ljud.log')
        # Flaggningen är läst och denna körning är uttryckligen en granskning.
        run(name+'_bygg_render',[exe,'-b','--factory-startup','-t','8','--python-exit-code','1','--python',str(INGEST/'mhr_rig.py'),'--',str(INGEST/'ut/notan-tagningar/S1'),str(ROT/'scen/klipp/d-dialog-notan.mp4'),
                                 '--plan',str(d/'plan.json'),'--ut',str(d),'--ljud',str(d/'ljud.wav'),'--tillat-flaggad','--render'],d/'blender.log')
        count=len(list((d/'render').glob('f*.png')))
        assert count==len(p['kallrutor']),(name,count)
        assert (d/'film.mp4').exists()
        run(name+'_blenderkontroll',[exe,'-b','--factory-startup','-t','4','--python-exit-code','1','--python',str(HIT/'tro_granska_blender.py'),'--',str(d)],d/'kontroll.log')
        if name=='tro_tom':
            run(name+'_oversikt',[exe,'-b','--factory-startup','-t','4','--python-exit-code','1','--python',str(INGEST/'plats_oversikt.py'),'--',str(d),str(d/'plan.json'),str(d/'oversikt')],d/'oversikt.log')
    for name in ('notan','bar'):
        old=json.loads((UT/f'tro_fore_{name}.json').read_text(encoding='utf-8'))
        skriv(UT/f'tro_fore_{name}_matning.json',mat(old,stod=False))
    p=kompilera(HIT/'exempel/bar/kalla.json',HIT/'exempel/bar/regi.json');skriv(UT/'tro_barplan.json',p);rapport(p,UT/'tro_barplan.json')
    print('Klart',flush=True)


if __name__=='__main__':main()
