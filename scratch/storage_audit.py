import os, json, collections, shutil, sys
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
from pathlib import Path
root = Path(__file__).resolve().parents[1]
files, errors = [], []
def err(e): errors.append(str(e))
for base, dirs, names in os.walk(root, onerror=err, followlinks=False):
    dirs[:] = [d for d in dirs if d not in {'.venv','node_modules','.git','site-packages'}]
    if len(Path(base).relative_to(root).parts) <= 2:
        print('Scanning ' + str(Path(base).relative_to(root)), flush=True)
    for name in names:
        p = Path(base, name)
        try:
            s=p.stat()
            files.append({'path':p.relative_to(root).as_posix(), 'bytes':s.st_size, 'mtime':s.st_mtime})
        except OSError as e: err(e)
out=root/'scratch/storage-audit-2026-11-21.json'
out.write_text(json.dumps({'files':files,'errors':errors,'disk':shutil.disk_usage(root)._asdict()},ensure_ascii=False),encoding='utf-8')
def groups(rows, depth):
    agg=collections.Counter()
    for f in rows: agg['/'.join(f['path'].split('/')[:depth])]+=f['bytes']
    return [(p,round(n/1e9,3)) for p,n in agg.most_common(25)]
blend=[f for f in files if '.blend' in Path(f['path']).suffix.lower()]
print(json.dumps({'total_GB':round(sum(f['bytes'] for f in files)/1e9,3),'disk':shutil.disk_usage(root)._asdict(),'errors':errors[:8],'top':groups(files,2),'blend_GB':round(sum(f['bytes'] for f in blend)/1e9,3),'blend_groups':groups(blend,4),'largest':sorted(files,key=lambda f:f['bytes'],reverse=True)[:35]},ensure_ascii=False,indent=2))
