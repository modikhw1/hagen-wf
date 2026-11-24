"""Lokalt mallprov: passning, kompilering, ljud och tre bakgrundsfilmer.

Kör från projektroten med scen/.venv/Scripts/python.exe. Läser BLENDER
ur ingest_klipp.py utan att importera eller köra dess ingeststeg.
"""
import ast
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from gemensamt import HIT,ladda,skriv
from kompilera import kompilera
from mall_migrera import uppdatera_exempel

ROT=HIT.parents[2];INGEST=HIT.parent/'ingest';UT=HIT/'ut/notan'


def blender():
    tree=ast.parse((INGEST/'ingest_klipp.py').read_text(encoding='utf-8'))
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='BLENDER' for x in n.targets):return ast.literal_eval(n.value)
    raise ValueError('BLENDER saknas i ingest_klipp.py')


def main():
    os.environ['PYTHONIOENCODING']='utf-8';tider={};exe=blender()
    def run(n,args,log):
        t=time.perf_counter()
        with open(log,'w',encoding='utf-8') as f:
            subprocess.run(args,cwd=ROT,env=os.environ,stdout=f,stderr=subprocess.STDOUT,check=True)
        tider[n]=time.perf_counter()-t;print(n,round(tider[n],3),'s',flush=True);skriv(UT/'tider_mall.json',tider)
    for name in ('mall_tom','mall_redigerad','mall_byt_lokal'):
        if (UT/name/'film.mp4').exists():raise FileExistsError(UT/name/'film.mp4')
        (UT/name).mkdir(exist_ok=True)
    run('passning_notan',[sys.executable,str(INGEST/'plats.py'),str(INGEST/'ut/notan-tagningar'),'--hand',str(INGEST/'ut/notan-tagningar/plats/hand.json')],UT/'passning_mall.log')
    uppdatera_exempel()
    for name,regi in [('mall_tom',None),('mall_redigerad','regi.json'),('mall_byt_lokal','regi_byt_lokal.json')]:
        d=UT/name;t=time.perf_counter()
        rf=HIT/'exempel/notan'/regi if regi else d/'regi.json'
        if not regi:
            r=ladda(HIT/'exempel/notan/regi.json');r['edits']=[];skriv(rf,r)
        p=kompilera(HIT/'exempel/notan/kalla.json',rf);skriv(d/'plan.json',p)
        tider[name+'_kompilering']=time.perf_counter()-t
        run(name+'_ljud',[sys.executable,str(HIT/'bygg_ljud.py'),str(d/'plan.json'),str(d/'ljud.wav'),str(d/'ljud_rapport.json')],d/'ljud.log')
        run(name+'_bygg_render',[exe,'-b','--factory-startup','-t','8','--python-exit-code','1','--python',str(INGEST/'mhr_rig.py'),'--',str(INGEST/'ut/notan-tagningar/S1'),str(ROT/'scen/klipp/d-dialog-notan.mp4'),'--plan',str(d/'plan.json'),'--ut',str(d),'--ljud',str(d/'ljud.wav'),'--render'],d/'blender.log')
        if name!='mall_redigerad':
            run(name+'_oversikt',[exe,'-b','--factory-startup','-t','8','--python-exit-code','1','--python',str(INGEST/'plats_oversikt.py'),'--',str(d),str(d/'plan.json'),str(d/'oversikt')],d/'oversikt.log')
    skriv(UT/'tider_mall.json',tider)


if __name__=='__main__':main()
