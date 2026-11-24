import json,re,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'scratch/storage-audit-2026-11-21.json').read_text(encoding='utf-8'))
groups=collections.defaultdict(list)
for f in data['files']:
    p=Path(f['path'])
    if f['path'].startswith('scen/3d/kontrakt/ut/') and re.fullmatch(r'f?\d+\.png',p.name):
        groups[p.parent.as_posix()].append(f)
eligible={p:fs for p,fs in groups.items() if Path(p).name in {'render','komposit'} and (root/p).parent.joinpath('scen.blend').is_file()}
print('Eligible GB',sum(f['bytes'] for fs in eligible.values() for f in fs)/1e9)
selected=[]; kept=[]; scenes=[]
# Prefer historical snapshots, then the superseded pipeline's other exports.
order=sorted(eligible,key=lambda p:(not any(x.startswith(('fore','gamla')) for x in Path(p).parts),p))
for parent in order:
    fs=sorted(eligible[parent],key=lambda f:int(re.search(r'\d+',Path(f['path']).stem)[0]))
    if len(fs)<60: continue
    scene=(root/parent).parent
    plan=scene/'plan.json'
    if not plan.is_file(): continue
    pd=json.loads(plan.read_text(encoding='utf-8'))
    keyframes=set()
    for shot in pd.get('scener',[]):
        interval=shot.get('ut',[])
        if len(interval)==2:
            a,b=interval; keyframes.update([a-1,a,a+1,(a+b)//2,b-2,b-1,b])
    samples=[]; removals=[]
    for i,f in enumerate(fs):
        frame=int(re.search(r'\d+',Path(f['path']).stem)[0])
        (samples if i in {0,len(fs)//2,len(fs)-1} or frame%30==0 or frame in keyframes else removals).append(f)
    selected+=removals; kept+=samples
    scenes.append({'directory':parent,'deleted_files':len(removals),'bytes':sum(f['bytes'] for f in removals),'kept_files':len(samples),'scene':scene.relative_to(root).as_posix()+'/scen.blend','plan':plan.relative_to(root).as_posix()})
    if sum(f['bytes'] for f in selected)>=12_000_000_000: break
manifest={'root':str(root),'reason':'Superseded Blender pipeline: remove regenerable numbered PNG sequences only. Preserve .blend, plans, raw ingest, video, code, named comparisons, and first/middle/last, every 30th frame and shot-boundary samples.','files':selected,'kept_samples':kept,'groups':scenes}
(root/'scratch/render-cleanup-manifest-2026-11-21.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'GB':sum(f['bytes'] for f in selected)/1e9,'files':len(selected),'kept_samples':len(kept),'groups':len(scenes),'by_top':dict(collections.Counter())},indent=2))
c=collections.Counter()
for f in selected: c[f['path'].split('/')[5]]+=f['bytes']
print(json.dumps(c,indent=2))
