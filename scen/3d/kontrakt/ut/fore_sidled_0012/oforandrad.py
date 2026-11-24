"""0012: notans och guacamoles befintliga planer genom mobellyft.los och foremallyft.los, baslinje mot ny kod. Skriver sha256 per plan."""
import copy, glob, hashlib, json, sys
from pathlib import Path
HIT = Path(__file__).resolve().parent; KON = HIT.parents[1]
sys.path[:0] = [str(HIT / 'baslinje_import') if sys.argv[1] == 'bas' else str(KON), str(KON), str(KON.parent / 'ingest')]
import mobellyft, foremallyft
print('modul', mobellyft.__file__, file=sys.stderr)
ut = {}
for f in sorted(glob.glob(str(KON / 'ut/notan*/**/plan.json'), recursive=True) + glob.glob(str(KON / 'ut/e-dialog-guacamole/**/plan.json'), recursive=True)):
    plan = json.loads(Path(f).read_text(encoding='utf-8')); fore = json.dumps(plan, sort_keys=True)
    p = copy.deepcopy(plan); r1 = mobellyft.los(p); r2 = foremallyft.los(p)
    efter = json.dumps(p, sort_keys=True)
    ut[str(Path(f).relative_to(KON))] = dict(mobel=r1 is None, foremal=r2 is None, oforandrad=fore == efter, sha=hashlib.sha256(efter.encode()).hexdigest()[:16])
print(json.dumps(ut, ensure_ascii=False, indent=1))
