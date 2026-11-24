"""Nya lokala golvfilmer. Vägrar skriva över tidigare renderingsmappar."""
import os
import subprocess
import sys
import time
from gemensamt import HIT,skriv,ladda
from kompilera import kompilera
from trohet import rapport
from verifiera_mall import blender

ROT=HIT.parents[2];UT=HIT/'ut/notan';INGEST=HIT.parent/'ingest'


def main():
    os.environ['PYTHONIOENCODING']='utf-8';times={};exe=blender()
    for name in ('golv_tom','golv_redigerad'):
        if (UT/name).exists():raise FileExistsError(UT/name)
    def run(name,args,folder):
        start=time.perf_counter()
        with (folder/(name+'.log')).open('w',encoding='utf-8') as f:
            r=subprocess.run(args,cwd=ROT,env=os.environ,stdout=f,stderr=subprocess.STDOUT)
        times[folder.name+'_'+name]=dict(tid_s=time.perf_counter()-start,exitkod=r.returncode)
        skriv(UT/'tider_golv.json',times);print(folder.name,name,times[folder.name+'_'+name],flush=True)
        if r.returncode:raise RuntimeError('Se '+str(folder/(name+'.log')))
    for name,edited in [('golv_tom',False),('golv_redigerad',True)]:
        d=UT/name;d.mkdir();rf=HIT/'exempel/notan/regi.json'
        if not edited:
            r=ladda(rf);r['edits']=[];rf=d/'regi.json';skriv(rf,r)
        start=time.perf_counter();p=kompilera(HIT/'exempel/notan/kalla.json',rf);skriv(d/'plan.json',p);rapport(p,d/'plan.json')
        times[name+'_kompilering']=dict(tid_s=time.perf_counter()-start)
        run('ljud',[sys.executable,str(HIT/'bygg_ljud.py'),str(d/'plan.json'),str(d/'ljud.wav'),str(d/'ljud_rapport.json')],d)
        run('bygg_render',[exe,'-b','--factory-startup','-t','8','--python-exit-code','1','--python',str(INGEST/'mhr_rig.py'),'--',str(INGEST/'ut/notan-tagningar/S1'),str(ROT/'scen/klipp/d-dialog-notan.mp4'),
                          '--plan',str(d/'plan.json'),'--ut',str(d),'--ljud',str(d/'ljud.wav'),'--tillat-flaggad','--render'],d)
        assert len(list((d/'render').glob('f*.png')))==len(p['kallrutor'])
        run('blenderkontroll',[exe,'-b','--factory-startup','-t','4','--python-exit-code','1','--python',str(HIT/'tro_granska_blender.py'),'--',str(d)],d)
        run('oversikt',[exe,'-b','--factory-startup','-t','4','--python-exit-code','1','--python',str(INGEST/'plats_oversikt.py'),'--',str(d),str(d/'plan.json'),str(d/'oversikt')],d)
    p=kompilera(HIT/'exempel/bar/kalla.json',HIT/'exempel/bar/regi.json');skriv(UT/'golv_bar/plan.json',p);rapport(p,UT/'golv_bar/plan.json')
    print('Klart',flush=True)


if __name__=='__main__':main()
