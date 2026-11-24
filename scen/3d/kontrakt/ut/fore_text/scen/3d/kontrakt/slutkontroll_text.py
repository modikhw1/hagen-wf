"""Manifest, radslut och lätt kontroll av slutfilmernas strömmar."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from textarbete import jsonfil,UT

HIT=Path(__file__).resolve().parent
ROT=HIT.parents[2]


def sha(p):
    digest=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def endings(p):
    data=p.read_bytes();crlf=data.count(b'\r\n');lf=data.count(b'\n')-crlf
    return dict(CRLF=crlf,LF=lf)


def main():
    changed=[]
    for old in (UT/'scen/3d').rglob('*'):
        if not old.is_file():continue
        rel=old.relative_to(UT);parts=rel.parts
        # Slutresultat har egna provarkiv; manifestet visar källkod och indata.
        if len(parts)>4 and parts[3]=='ut':continue
        if parts[:4]==('scen','3d','ingest','ut') and old.suffix!='.npz':continue
        now=ROT/rel
        if not now.is_file():continue
        a,b=sha(old),sha(now)
        if a==b:continue
        row=dict(fil=rel.as_posix(),backup=old.relative_to(ROT).as_posix(),fore_sha256=a,efter_sha256=b)
        if old.suffix in ['.py','.json','.md']:
            before,after=endings(old),endings(now)
            row['radslut_fore']=before;row['radslut_efter']=after
            assert not ((before['CRLF'] and not before['LF'] and after['LF']) or (before['LF'] and not before['CRLF'] and after['CRLF'])),rel
        changed.append(row)
    assert not any(x['fil'].startswith('scen/3d/kontrakt/exempel/bar/') for x in changed)
    assert not any('/bro/' in x['fil'] for x in changed)
    jsonfil(UT/'andrade_filer.json',changed)
    source_names={
      'kontrakt':['textarbete.py','diagnos_text.py','forbered_text.py','kor_textarbete.py','slutfor_text.py','bygg_lokalbank.py','passa_disk_igen.py','kontroll_disk.py','verifiera_text.py','regression_text.py','prova_komposit.py','rendera_text.py','avsluta_text.py','rattad_forstatext.py','textgranska.py','sammanfatta_text.py','slutkontroll_text.py','skarmtext.py','textenheter.py','textreferens.py','textmalning.py','skymning_disk.py','test_text_disk.py'],
      'ingest':['bildskydd.py','vertikaler.py','kamera_vertikal.py','diskprojektion.py','diskplats.py']}
    created=[(ROT/'scen/3d'/folder/name).relative_to(ROT).as_posix() for folder,names in source_names.items() for name in names]
    created += [p.relative_to(ROT).as_posix() for p in (HIT/'rumsmall').glob('lokal_*.json')]
    created += [f'scen/3d/kontrakt/rumsmall/{name}.json' for name in ['chark_disk','glass_disk','servering_disk','fiktiv_mandisk','lokalkoder']]
    created += [p.relative_to(ROT).as_posix() for p in (HIT/'textreferenser').glob('*.json')]
    films=[]
    for clip,folder in [('b','tom2'),('kenny','tom2'),('a','tom2'),('b','redigerad2'),('notan','text_redigerad')]:
        d=HIT/f'ut/{clip}/{folder}';p=json.loads((d/'plan.json').read_text(encoding='utf-8'))
        cmd=[shutil.which('ffprobe'),'-v','error','-show_streams','-of','json',str(d/'film.mp4')]
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',check=True)
        streams=json.loads(result.stdout)['streams'];v=next(s for s in streams if s['codec_type']=='video')
        assert int(v['nb_frames'])==len(p['kallrutor']),(clip,folder,v['nb_frames'],len(p['kallrutor']))
        assert (v['width'],v['height'])==(p['utdata']['bredd'],p['utdata']['hojd'])
        assert any(s['codec_type']=='audio' for s in streams)
        sheets=sorted(x.stem for x in (d/'blad').glob('s*.png'))
        assert set(sheets)=={s['id'] for s in p['scener']}
        films.append(dict(klipp=clip,mapp=folder,rutor=int(v['nb_frames']),fps=v['r_frame_rate'],bredd=v['width'],hojd=v['height'],blad=sheets,ljud=True))
        created += [(d/name).relative_to(ROT).as_posix() for name in ['film.mp4','plan.json','kvalitet.md','tider.json']]
    jsonfil(UT/'skapade_filer.json',sorted(set(created)))
    jsonfil(UT/'filmkontroll.json',films)
    print('ändrade källfiler',len(changed),'filmer',len(films),'blad',sum(len(x['blad']) for x in films),'radslut oförändrade',flush=True)


if __name__=='__main__':main()
