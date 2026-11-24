"""Offline motprov. All new files stay under ut/codex; no Modal imports/jobs.
Run from 6-lokalitet: .venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py COMMAND
"""
from pathlib import Path
import argparse, ast, hashlib, json, re, shutil, subprocess, sys, time
import cv2
import numpy as np

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[1]
ROOT = BASE.parents[2]
KEYS = ['duepiani', 'spanjorskan', '08burgerkebab', 'babasburgers', 'kennysgelato2.0']
MROOT = OUT / 'isolated'
MBASE = MROOT / 'motpart/runda-4/6-lokalitet'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2), encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def manifest():
    paths = [BASE / f for f in ('lokalitet.py', 'observera.py', 'modal_obs.py', 'geom.py', 'RAPPORT.md', 'README.md')]
    paths += [p for p in (BASE/'ut').rglob('*') if p.is_file() and not p.is_relative_to(OUT)]
    return {str(p.relative_to(BASE)): sha(p) for p in paths}

def prepare():
    if (OUT/'baseline.json').exists(): raise RuntimeError('Baseline already exists; do not overwrite evidence')
    write(OUT/'baseline.json', manifest())
    MBASE.mkdir(parents=True, exist_ok=True)
    for f in ('lokalitet.py', 'geom.py'):
        shutil.copy2(BASE/f, MBASE/f)
    orig = BASE/'ut/babasburgers'
    target = MBASE/'ut/babasburgers'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(orig/'paket_L.json', OUT/'paket_L.original.json')
    for f in ('obs_gpu.json', 'pose2d.json'):
        shutil.copy2(orig/f, target/f)
    shutil.copytree(orig/'obs_gpu', target/'obs_gpu', dirs_exist_ok=True)
    if (orig/'ingest_v2').exists():
        (target/'ingest_v2').mkdir(exist_ok=True)
        shutil.copy2(orig/'ingest_v2/paket.json', target/'ingest_v2/paket.json')
    shared = ROOT/'arbetsbord/data/ingest_v2/babasburgers/paket.json'
    if shared.exists():
        dest = MROOT/'arbetsbord/data/ingest_v2/babasburgers/paket.json'
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(shared, dest)
    video = ROOT/'data/format/kontroll/klipp'/(read(orig/'obs_gpu.json')['klipp']+'.mp4')
    dest = MROOT/'data/format/kontroll/klipp'/video.name
    dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(video, dest)
    assert sha(MBASE/'lokalitet.py') == sha(BASE/'lokalitet.py')
    print('Prepared byte-identical source and inputs in', MBASE)

def determinism(n):
    cmd = [str(BASE/'.venv/Scripts/python.exe'), '-I', '-X', 'utf8', '-W', 'ignore', 'lokalitet.py', 'babasburgers', '--obs', 'gpu']
    t = time.perf_counter()
    with (OUT/f'determinism-{n}.log').open('w', encoding='utf-8') as log:
        p = subprocess.run(cmd, cwd=MBASE, stdout=log, stderr=subprocess.STDOUT, timeout=155)
    r = {'command': cmd, 'cwd': str(MBASE), 'exit': p.returncode, 'seconds': time.perf_counter()-t,
         'source_sha256': sha(MBASE/'lokalitet.py')}
    if p.returncode == 0:
        for f in ('paket_L.json', 'lokalitet.json'):
            shutil.copy2(MBASE/'ut/babasburgers'/f, OUT/f'{n}-{f}')
        r['sha256'] = sha(OUT/f'{n}-paket_L.json')
    write(OUT/f'determinism-{n}.json', r)
    # Explicitly restore the requested original (the isolated process never changed it).
    shutil.copy2(OUT/'paket_L.original.json', BASE/'ut/babasburgers/paket_L.json')
    r['original_restored_sha256'] = sha(BASE/'ut/babasburgers/paket_L.json')
    write(OUT/f'determinism-{n}.json', r)
    print(json.dumps(r, ensure_ascii=False)); assert p.returncode == 0

def basic():
    hits, constants = [], []
    pat = re.compile(r'duepiani|spanjorskan|08burgerkebab|babasburgers|kennysgelato|notan|guacamole|\b[Ss]\d+\b|\d{15,}', re.I)
    for fn in ('lokalitet.py', 'observera.py', 'modal_obs.py'):
        src = (BASE/fn).read_text(encoding='utf-8'); lines = src.splitlines()
        hits.extend({'file':fn, 'line':i, 'text':s} for i,s in enumerate(lines,1) if pat.search(s))
        # Complete executable literal inventory, including generic algorithm parameters.
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Constant) and isinstance(node.value,(int,float)) and not isinstance(node.value,bool):
                constants.append({'file':fn,'line':node.lineno,'value':node.value,'text':lines[node.lineno-1].strip()})
    write(OUT/'code-scan.json', {'name_and_id_hits':hits,'numeric_literals':constants})
    feet, summary = [], []
    for key in KEYS:
        meta=read(BASE/'ut'/key/'obs_gpu.json'); loc=read(BASE/'ut'/key/'lokalitet.json')
        for s in meta['tagningar']:
            i=loc['tagningar'][s['id']]
            summary.append({'clip':key,'shot':s['id'],'frames':s['nyckelrutor'],'pitch':i['lutning_grader'],
                            'spread':i['lodlinje']['spridning_per_ruta_grader'],'lens':i['lins_mm']})
            if key=='duepiani':
                h=i['kamerahojd']; sc=i['skala']; f=i.get('fot_over_golv_m',{})
                feet.append({'shot':s['id'],'height':h,'feet':f,'scale':sc,
                             'height_minus_feet':round(h['m']-h['fotter_m'],6) if 'fotter_m' in h else None,
                             'height_with_surface_scale':h['m']*sc['personyta_skulle_ge']/sc['varde'] if 'personyta_skulle_ge' in sc else None})
    write(OUT/'feet.json',feet); write(OUT/'shots.json',summary)
    print('name hits',hits)
    for s in summary: print(s['clip'],s['shot'],'pitch',s['pitch'],'spread',s['spread'])
    print('FEET',json.dumps(feet,ensure_ascii=False))

def frames():
    dest=OUT/'frames'; dest.mkdir(exist_ok=True)
    for key in KEYS:
        meta=read(BASE/'ut'/key/'obs_gpu.json')
        video=ROOT/'data/format/kontroll/klipp'/(meta['klipp']+'.mp4')
        assert sha(video)==meta['kalla_sha256']
        cap=cv2.VideoCapture(str(video)); tiles=[]
        for s in meta['tagningar']:
            for u in s['nyckelrutor']:
                cap.set(cv2.CAP_PROP_POS_FRAMES,u); ok,bgr=cap.read(); assert ok
                cv2.imwrite(str(dest/f'{key}-{s["id"]}-{u}.png'),bgr)
                if u==s['nyckelrutor'][len(s['nyckelrutor'])//2]:
                    tile=cv2.resize(bgr,(270,480)); tile=cv2.copyMakeBorder(tile,26,0,0,0,cv2.BORDER_CONSTANT)
                    cv2.putText(tile,f'{key} {s["id"]} f{u}',(5,18),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1)
                    tiles.append(tile)
        cap.release()
        cols=min(4,len(tiles)); sheet=np.zeros(((len(tiles)+cols-1)//cols*506,cols*270,3),np.uint8)
        for j,tile in enumerate(tiles): sheet[(j//cols)*506:(j//cols+1)*506,(j%cols)*270:(j%cols+1)*270]=tile
        cv2.imwrite(str(OUT/f'{key}-contact.jpg'),sheet)
        print(key,len(meta['tagningar']),'shots extracted')

def integrity():
    before=read(OUT/'baseline.json'); after=manifest()
    diffs={k:[before.get(k),after.get(k)] for k in set(before)|set(after) if before.get(k)!=after.get(k)}
    # The external task runner appends the command transcript to this log while we work.
    transcript='ut\\codex_kontroll.log'
    substantive={k:v for k,v in diffs.items() if k!=transcript}
    write(OUT/'integrity.json', {'files_checked':len(before),'differences':diffs,
          'source_and_data_differences':substantive,'external_live_transcript':transcript})
    print('Files checked',len(before),'source/data differences',substantive,'external transcript changed',transcript in diffs)
    assert not substantive

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('command',choices=['prepare','det1','det2','basic','frames','integrity']); a=ap.parse_args()
    if a.command.startswith('det'): determinism(a.command[-1])
    else: globals()[a.command]()
