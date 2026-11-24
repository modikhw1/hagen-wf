import json,sys,collections,shutil
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
root=Path(__file__).resolve().parents[1]
inv=json.loads((root/'scratch/storage-audit-2026-11-21.json').read_text(encoding='utf-8'))
manifest=json.loads((root/'scratch/render-cleanup-manifest-2026-11-21.json').read_text(encoding='utf-8'))
result=json.loads((root/'scratch/render-cleanup-result-2026-11-21.json').read_text(encoding='utf-8-sig'))
removed={f['path'] for f in manifest['files']}
assert result['deleted_files']==len(removed)
assert all(not (root/p).exists() for p in removed)
issues=[]; checked=0
for f in inv['files']:
    rel=f['path']
    if rel in removed: continue
    if rel.startswith(('forvarld_karna/','scen/3d/ingest/','scen/3d/kontrakt/ut/')) or '.blend' in Path(rel).suffix:
        try:
            s=(root/rel).stat()
            if s.st_size!=f['bytes'] or abs(s.st_mtime-f['mtime'])>0.01: issues.append(rel)
        except OSError: issues.append(rel)
        checked+=1
assert not issues, issues[:20]
assert all((root/f['path']).is_file() for f in manifest['kept_samples'])
by_group=collections.Counter()
for f in manifest['files']: by_group[f['path'].split('/')[4]]+=f['bytes']
lines=[
'LAGRINGSRENSNING 2026-11-21',
f"Raderat: {result['deleted_files']} numrerade PNG-filer, {result['deleted_bytes']/1e9:.3f} GB ({result['deleted_bytes']/2**30:.2f} GiB).",
f"Ledigt före/efter: {result['free_before']/1e9:.2f} / {result['free_after']/1e9:.2f} GB.",
f"Urval kvar: {len(manifest['kept_samples'])} rutor över {len(manifest['groups'])} sekvenskataloger.",
f"Verifierat: {checked} bevarade filer oförändrade i storlek och ändringstid; alla urvalsrutor finns kvar; alla planerade raderingar genomförda.",
'',
'Avgränsning: endast render/komposit under scen/3d/kontrakt/ut, en äldre kedja som enligt CLAUDE.md och LAGE.md ersatts av forvarld_karna.',
'Varje berörd sekvens har kvar sin scen.blend och plan.json. Inga .blend, originalfilmer, NPZ/NPY-rörelser/djup, modeller, kod eller miljöer har raderats.',
'Bevarat första/mellersta/sista bilden, varje 30:e ruta och närliggande klippgränser/mittpunkter ur scenplanen. Namngivna jämförelser och MP4-filer har lämnats kvar.',
'Äldre bildspel som kräver kompletta PNG-sekvenser behöver omrendering. Den aktiva kedjans filer och rå-ingest har bevarats.',
'',
'Återskapa render: öppna berörd scen.blend i Blender och rendera animationen till den ursprungliga render-katalogen.',
'Exempel från projektroten: blender -b "scen/3d/kontrakt/ut/<variant>/scen.blend" -o "//render/f" -F PNG -a',
'Kompositbilder skapas av scen/3d/kontrakt/skarmtext.py:kompositera(plan, d), anropad av kor_klipp.py. Den förutsätter en ny komposit-katalog.',
'',
'Före inventering (exkl. .venv/node_modules/.git/site-packages): 68.277 GB; scen/3d 53.471 GB; Blender-filer 3.016 GB; PNG i gamla kontrakt/ut 19.214 GB.',
f"Inventeringen fick åtkomstfel i {len(inv['errors'])} kataloger; dessa har lämnats orörda. Ingen rensning utanför projektet.",
'',
'Raderat per äldre experiment:']
lines.extend(f'{name}: {size/1e9:.3f} GB' for name,size in by_group.most_common())
lines+=['','Exakta filvägar och ursprungsstorlekar: scratch/render-cleanup-manifest-2026-11-21.json',
'Genomförandelogg: scratch/render-cleanup-deleted-2026-11-21.jsonl']
report='\n'.join(lines)+'\n'
(root/'scratch/lagringsrensning-2026-11-21.txt').write_text(report,encoding='utf-8')
(root/'scen/3d/kontrakt/ut/RENDER-RENSNING-2026-11-21.txt').write_text(report,encoding='utf-8')
print(report)
