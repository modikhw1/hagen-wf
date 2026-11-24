"""Färska standardplaner mot de begärda sparade planerna."""
import copy
import json
import time
from pathlib import Path
from gemensamt import HIT,ladda,skriv
from kompilera import kompilera
from textarbete import jsonfil


def skillnader(a,b,path=''):
    if type(a)!=type(b):return [path]
    if isinstance(a,dict):
        return [path+'/'+key for key in a.keys()^b.keys()]+[p for key in a.keys()&b.keys() for p in skillnader(a[key],b[key],path+'/'+key)]
    if isinstance(a,list):
        if len(a)!=len(b):return [path+'/antal']
        return [p for i,(x,y) in enumerate(zip(a,b)) for p in skillnader(x,y,path+'/'+str(i))]
    return [] if a==b else [path]


if __name__=='__main__':
    ut=HIT/'ut/fore_text';results=[]
    for name,kalla,regi,stored in [
        ('notan',HIT/'exempel/notan/kalla.json',HIT/'ut/notan/golv_tom/regi.json',HIT/'ut/notan/golv_tom/plan.json'),
        ('bar',HIT/'exempel/bar/kalla.json',HIT/'exempel/bar/regi.json',HIT/'ut/bar/plan_efter_baromkorning.json')]:
        start=time.perf_counter();r=ladda(regi);k=ladda(kalla);r['kalla']['revision']=k['revision']
        if name=='notan':r['edits']=[]
        temp=ut/f'regression_{name}_regi.json';jsonfil(temp,r)
        p=kompilera(kalla,temp);jsonfil(ut/f'regression_{name}_plan.json',p);old=ladda(stored)
        keys=['personer','renderkamera','matkamera','scener','tidskarta','kallrutor']
        protected={key:skillnader(old.get(key),p.get(key),key) for key in keys}
        changes=skillnader(old,p)
        result=dict(klipp=name,sekunder=round(time.perf_counter()-start,2),skyddade=protected,alla_andrade_sokvagar=changes)
        results.append(result);print(name,result['sekunder'],{key:len(v) for key,v in protected.items()},'alla',len(changes),flush=True)
    jsonfil(ut/'regression.json',results)
