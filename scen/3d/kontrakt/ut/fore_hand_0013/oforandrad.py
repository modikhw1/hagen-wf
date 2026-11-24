"""0013: notans och guacamoles befintliga planer genom handforemal.los. Ska ge None och lämna planen byteidentisk. Från scen/3d/kontrakt."""
import glob, hashlib, json, sys
from pathlib import Path
sys.path[:0] = ['.', '../ingest']
import handforemal
ut = {}
for f in sorted(glob.glob('ut/notan*/**/plan.json', recursive=True) + glob.glob('ut/e-dialog-guacamole*/**/plan.json', recursive=True)):
    plan = json.loads(Path(f).read_text(encoding='utf-8')); fore = json.dumps(plan, sort_keys=True)
    r = handforemal.los(plan); efter = json.dumps(plan, sort_keys=True)
    ut[f] = dict(ingen_post=r is None, oforandrad=fore == efter, sha=hashlib.sha256(efter.encode()).hexdigest()[:16])
print(json.dumps(dict(antal=len(ut), alla_oforandrade=all(v['oforandrad'] and v['ingen_post'] for v in ut.values())), ensure_ascii=False))
json.dump(ut, open('ut/fore_hand_0013/oforandrad.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
