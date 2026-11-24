"""Uppdatera endast notans platsreferens efter säkerhetskopiering i fore_golv."""
import os
import hashlib
from pathlib import Path
from gemensamt import HIT,ladda,skriv
from kalla_plats import plats_delar


def main():
    f=HIT/'exempel/notan/kalla.json';k=ladda(f);p=HIT.parent/'ingest/ut/notan-tagningar/plats/plats.json'
    def pek(path,roll):return dict(sokvag=Path(os.path.relpath(path,f.parent)).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),format='json',roll=roll)
    sem,mat,sc,props=plats_delar(p,[(s['id'],s['kamera'],'S'+s['id'][1:]) for s in k['semantik']['scener']],pek,{s['id']:s['personer'] for s in k['semantik']['scener']})
    k['revision']=4;k['semantik']['platser']=[sem];k['matning']['platser']=[mat];k['semantik']['props']=props
    for s in k['semantik']['scener']:s['plats_id'],s['bindningar']=sc[s['id']]
    for post in k['matning']['kvalitet']:
        if post['post'] in ('semantik.platser','matning.skala'):
            post['metod']='Golv: cue-beslut per tagning till ett gemensamt plan, se plats.json golv.matning. Skala 1,0 behålls från kroppsmodellen; möbelpriorer och monokulärt djup verifierar den inte.'
            post['osakerhet']='Golv/skalakonflikter loggas uttryckligen. Kamerahöjd 1,45 m är endast reservprior.'
    skriv(f,k)
    for f in (HIT/'exempel/notan').glob('regi*.json'):
        r=ladda(f);r['kalla']['revision']=4;skriv(f,r)


if __name__=='__main__':main()
