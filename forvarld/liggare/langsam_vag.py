"""0031: den långsamma vägen. När Jev väljer ingen_passar, eller en ändring utan regi, får en stark modell liggaren och meningen och svarar
med regi (bara befintliga operationer) eller ett tydligt nej med skäl. Tiden mäts.

  scen/.venv/Scripts/python.exe forvarld/liggare/langsam_vag.py <liggare.json> <ut.json> "<mening>" [...] [--modell google/gemini-2.5-flash]
"""
import json, os, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from kor_liggare import OPS, GATEWAY

a = sys.argv[1:]; modell = a[a.index('--modell') + 1] if '--modell' in a else 'google/gemini-2.5-flash'; a = [x for x in a if x not in ('--modell', modell)]
L = json.loads(Path(a[0]).read_text(encoding='utf-8')); ut = Path(a[1]); k = os.environ.get('AI_GATEWAY_API_KEY') or Path(os.environ['AI_GATEWAY_NYCKELFIL']).read_text(encoding='utf-8').splitlines()[0].strip()
res = []
for m in a[2:]:
    text = f"""You are the slow path of an editing system for a 3D pre-world of a video clip. The fast selector found no legal edit for the CM's sentence.
LEDGER (what the actions mean and what may change):
{json.dumps(L, ensure_ascii=False)}
OPERATIONS available (nothing else exists):
{OPS}
CM: "{m}"
Answer JSON only: {{"beslut": "regi" or "nej", "edits": [ ... edits using only the operations above, empty if nej ... ], "skal": "one or two sentences: why, and for nej what is missing (which level: 3d, redigering or generering)"}}"""
    body = dict(model=modell, max_tokens=4000, messages=[dict(role='user', content=text)], response_format=dict(type='json_object'))
    t = time.time(); d = json.load(urllib.request.urlopen(urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json'}), timeout=300))
    s = round(time.time() - t, 2); svar = json.loads(d['choices'][0]['message']['content'].strip().removeprefix('```json').removesuffix('```'))
    res.append(dict(mening=m, modell=modell, sekunder=s, kostnad=(d.get('usage') or {}).get('cost'), **svar)); print(m, '|', s, 's |', svar.get('beslut'), '|', svar.get('skal'))
ut.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
