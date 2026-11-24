"""Jämför byggbevis och paketera de färdiga PNG-sekvenserna med originalljud."""
import difflib
import hashlib
import json
import subprocess
import time
from pathlib import Path
import numpy as np
import cv2

HIT=Path(__file__).resolve().parent; UT=HIT/'ut/bar'; INGEST=HIT.parent/'ingest'
def las(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


if __name__=='__main__':
    a,b,c=[las(UT/n/'rapport.json') for n in ('original','utan_plan','plan_slutlig')]
    assert a['antal_rutor']==b['antal_rutor']==a['png_antal']==b['png_antal']==202
    assert a['objekt']==b['objekt']
    lika=sum(np.array_equal(cv2.imread(str(p),-1),cv2.imread(str(UT/'utan_plan/render'/p.name),-1))
             for p in (UT/'original/render').glob('*.png'))
    assert lika==202
    assert np.array_equal(np.load(UT/'original/poser.npy'),np.load(UT/'utan_plan/poser.npy'))
    assert np.array_equal(np.load(UT/'utan_plan/poser.npy')[:156],np.load(UT/'plan_slutlig/poser.npy'))
    assert c['antal_rutor']==c['png_antal']==156 and c['aktiv_kamera']=='renderkamera'
    assert c['renderkamera_flytt_max_kroppsskillnad']==0
    assert (UT/'plan.json').read_bytes()==(UT/'plan_andra.json').read_bytes()==(UT/'plan_v3.json').read_bytes()
    fore=las(UT/'ingest_fore.json')
    efter={str(p.relative_to(INGEST/'ut/bar')):[p.stat().st_size,p.stat().st_mtime_ns] for p in (INGEST/'ut/bar').rglob('*') if p.is_file()}
    assert fore==efter
    byggd=las(UT/'plan_fran_byggd_kalla.json'); plan=las(UT/'plan.json')
    for f in ('tidskarta','kallrutor','personer','objekt','renderkamera','utdata'):
        assert byggd[f]==plan[f], 'Byggd kalla ger annan plan: '+f
    rapport=dict(utan_plan_pixelidentiska_png=lika,png_metadata='Datum och blend-sökväg skiljer; pixelvärdena är identiska.',samma_objekt_utan_plan=True,samma_poser_alla_rutor=True,
                 plan_identiska_byte=True,plan_sha256=sha(UT/'plan.json'),byggd_kalla_samma_byggdata=True,
                 ingest_oforandrad=True,renderkamera_kroppsskillnad=0,korningar=[],andringar={})
    for p in [INGEST/'mhr_rig.py',INGEST/'ingest_klipp.py',HIT/'README.md',HIT/'kalla.schema.json']:
        before=(UT/'original'/p.name).read_text(encoding='utf-8').splitlines(); after=p.read_text(encoding='utf-8').splitlines()
        delta=list(difflib.ndiff(before,after))
        rapport['andringar'][str(p.relative_to(HIT.parents[2]))]=dict(tillagda=sum(x.startswith('+ ') for x in delta),borttagna=sum(x.startswith('- ') for x in delta))
    rapport['nya_filer']={p.name:len(p.read_text(encoding='utf-8').splitlines()) for p in sorted(HIT.glob('*')) if p.name in
                          ('kalla_bygg.py','kompilera.py','gemensamt.py','ordlista.json','test_flode.py','verifiera_blender.py','verifiera_korning.py','rapportera.py')}
    for lage in ('utan_plan','plan_slutlig'):
        dest=UT/lage/'bar.mp4'
        cmd=['ffmpeg','-v','error','-n','-framerate','30','-start_number','0','-i',str(UT/lage/'render/f%04d.png'),'-i',plan['kallvideo'],
             '-map','0:v:0','-map','1:a?','-t',str((202 if lage=='utan_plan' else 156)/30),'-c:v','libx264','-pix_fmt','yuv420p','-crf','20',
             '-c:a','aac','-movflags','+faststart',str(dest)]
        t=time.perf_counter(); r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        rapport['korningar'].append(dict(kommando=subprocess.list2cmdline(cmd),exit=r.returncode,wall_s=time.perf_counter()-t,stderr=r.stderr))
        assert r.returncode==0,r.stderr
        probe=subprocess.run(['ffprobe','-v','error','-show_streams','-of','json',str(dest)],capture_output=True,check=True)
        rapport[lage+'_video']=json.loads(probe.stdout)['streams']
    (UT/'verifiering.json').write_text(json.dumps(rapport,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in rapport.items() if not k.endswith('_video')},ensure_ascii=False,indent=2))
