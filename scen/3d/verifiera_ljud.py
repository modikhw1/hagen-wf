"""Fas 4, del C2: ljud, munnar och textning efter de senaste ändringarna, i basen och i ett redigerat scenario.

A. Basen (designade röster): för varje ord, en bildruta mitt i ordet:
   - textningen innehåller ordet, rätt talare och rätt antal sagda ord (teleprompter)
   - talaren i bild har öppen mun (> 0,05) mitt i sina ord; i pauser (> 0,25 s) är munnen stängd (< 0,15)
   - mixen har ljud i varje replik (RMS > -35 dBFS) och tystnad i pauserna mellan repliker (< -45 dBFS)
   (pauserna mäts mellan repliker)
B. Redigerat: demo-andringar.sh + titta S4 C --mot A + replik 3 + casting A/B/C, svep var 0,1 s:
   - noll sidfel, huvudaktören i varje bildruta, källtiden växer inom varje tagning (tidskartor)
   - tysta kopior (S8): ingen textning, stängd mun; rollnamnen står i textningen; den nya repliken syns
Basen återställs efteråt (scen3d.bas.json, röster om ur cachen). Ut: data/verification-ljud.json
Kör: scen/.venv/Scripts/python.exe -B scen/3d/verifiera_ljud.py
"""
import json, sys, re, wave, shutil, subprocess, os, importlib.util
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent; PY = sys.executable
spec_ = importlib.util.spec_from_file_location('vf', ROOT / 'verifiera_fas4.py'); vf = importlib.util.module_from_spec(spec_)
argv, sys.argv = sys.argv, [sys.argv[0]]; spec_.loader.exec_module(vf); sys.argv = argv
norm = lambda s: re.sub(r'[^\wåäö]', '', s.lower())
def las(): return json.loads((ROOT / 'scen3d.json').read_text(encoding='utf-8'))
def tidslinje(S):
    t, ut = 0.0, []
    for sh in S['shots']: ut.append((sh, t)); t += sh['duration']
    return ut, t
ut = {}
# ---------------- A. basen
S = las(); ord_ = [(i, k, w, d) for i, d in enumerate(S['dialogue']) for k, w in enumerate(d['words'])]
jobs = [dict(t=round((w['start'] + w['end']) / 2, 3), variant='xbot', temporal=True, ord=[i, k]) for i, k, w, d in ord_]
rader = sorted((d['start'], d['end']) for d in S['dialogue']); pauser = []   # pauser MELLAN repliker (en designad röst har egen rytm inne i repliken)
for (s0, e0), (s1, e1) in zip(rader, rader[1:]):
    if s1 - e0 > .25: pauser.append(round((e0 + s1) / 2, 3))
jobs += [dict(t=p, variant='xbot', temporal=True, paus=True) for p in pauser]
res = vf.render(jobs)['results']
fel_text, fel_talare, fel_sagda, mun_öppen, mun_ej_i_bild, paus_mun = [], [], [], [], 0, []
for r in res:
    f = r['data']; cap = f['caption']
    if r.get('paus'):
        for aid, m in f['mouthByActor'].items(): paus_mun.append(m)
        continue
    i, k = r['ord']; d = S['dialogue'][i]; w = d['words'][k]
    if norm(w['w']) not in norm(cap['text']): fel_text.append((d['speaker'], w['w'], cap['text'][:40]))
    if cap['talare'] != d['speaker']: fel_talare.append((w['w'], cap['talare'], d['speaker']))
    väntat = sum(1 for x in d['words'] if x['start'] <= r['t'])   # teleprompter: ord som har börjat (nollånga ord från Whisper ingår)
    if cap['sagda'] != väntat: fel_sagda.append((w['w'], cap['sagda'], väntat))
    if d['speaker'] in f['mouthByActor']: mun_öppen.append(f['mouthByActor'][d['speaker']])
    else: mun_ej_i_bild += 1
with wave.open(str(ROOT / 'data/roster-mix.wav')) as wv: sr = wv.getframerate(); x = np.frombuffer(wv.readframes(wv.getnframes()), np.int16).astype(np.float32) / 32768
db = lambda a, b: 20 * np.log10(np.sqrt(np.mean(x[int(a * sr):int(b * sr)] ** 2)) + 1e-9)
rep_db = [round(float(db(d['start'], d['end'])), 1) for d in S["dialogue"]]
paus_db = [round(float(db(p - .08, p + .08)), 1) for p in pauser]
A = dict(ord=len(ord_), textning_saknar_ord=fel_text, fel_talare=fel_talare, fel_antal_sagda=fel_sagda[:5], antal_fel_sagda=len(fel_sagda),
         mun_oppen_andel=round(float(np.mean(np.array(mun_öppen) > .05)), 3), mun_median=round(float(np.median(mun_öppen)), 3), ord_utanfor_bild=mun_ej_i_bild,
         pauser=len(pauser), mun_i_paus_max=round(float(max(paus_mun or [0])), 3), replik_dbfs=rep_db, paus_dbfs=paus_db)
A['godkänt'] = (not fel_text and not fel_talare and not fel_sagda and A['mun_oppen_andel'] >= .9 and A['mun_i_paus_max'] < .15
                and min(rep_db) > -35 and (max(paus_db) if paus_db else -99) < -45)
ut['A_bas'] = A; print('A (bas):', json.dumps(A, ensure_ascii=False))
# ---------------- B. redigerat scenario
env = {**os.environ, 'PYTHONUTF8': '1'}; op = [PY, '-B', str(ROOT / 'op.py')]
try:
    subprocess.run(['C:/Program Files/Git/bin/bash.exe' if Path('C:/Program Files/Git/bin/bash.exe').exists() else 'bash', str(ROOT / 'demo-andringar.sh')], check=True, capture_output=True, env=env)   # Git Bash, inte WSL
    for a in (['titta', 'S4', 'C', '--mot', 'A', '--fran', '0.3'], ['replik', '3', '--text', 'För det är ju så en riktig karl gör.'],
              ['casting', 'A', '--roll', 'Kunden'], ['casting', 'B', '--roll', 'Främlingen'], ['casting', 'C', '--roll', 'Servitören']):
        r = subprocess.run(op + a, capture_output=True, text=True, encoding='utf-8', env=env); print('  ', r.stdout.strip()[:150])
    S2 = las(); linje, total = tidslinje(S2)
    res = vf.render([dict(t=round(t, 2), variant='xbot', temporal=True, svep=True) for t in np.arange(0, total, .1)])['results']
    sidfel = sum(len(r['data'].get('errors') or []) for r in res); utan = [r['t'] for r in res if not r['data'].get('joints')]
    mono = []; prev = {}
    for r in res:
        f = r['data']
        if f['shot'] in prev and f['sourceT'] < prev[f['shot']] - 1e-6: mono.append((f['shot'], r['t']))
        prev[f['shot']] = f['sourceT']
    tyst = [r for r in res if any(sh['id'] == r['data']['shot'] and sh.get('tyst') for sh in S2['shots'])]
    tyst_fel = [(r['t'], r['data']['caption']['text'][:20], r['data']['mouthOpen']) for r in tyst if r['data']['caption']['text'] or (r['data']['mouthOpen'] or 0) > .01]
    roller = {S2_a['casting']['role'] for S2_a in S2['actors'] if S2_a.get('casting', {}).get('role')}
    med_text = [r for r in res if r['data']['caption']['text']]
    utan_roll = [r['t'] for r in med_text if not any(r['data']['caption']['text'].startswith(x) for x in roller)]
    ny = any('riktig karl' in r['data']['caption']['text'] for r in res)
    B = dict(bildrutor=len(res), sidfel=sidfel, utan_huvudaktor=utan[:5], kalltid_bakat=mono[:5], tysta_bildrutor=len(tyst), tyst_fel=tyst_fel[:5],
             textning_utan_rollnamn=utan_roll[:5], ny_replik_syns=ny, langd=sum(sh['duration'] for sh in S2['shots']))
    B['godkänt'] = sidfel == 0 and not utan and not mono and not tyst_fel and not utan_roll and ny and len(tyst) > 0
    ut['B_redigerat'] = B; print('B (redigerat):', json.dumps(B, ensure_ascii=False))
finally:
    shutil.copy(ROOT / 'scen3d.bas.json', ROOT / 'scen3d.json'); shutil.rmtree(ROOT / 'historik', ignore_errors=True)
    subprocess.run([PY, '-B', str(ROOT / 'roster.py')], capture_output=True, env=env)
(ROOT / 'data/verification-ljud.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
print('GODKÄNT' if all(v.get('godkänt') for v in ut.values()) else 'EJ GODKÄNT', '-> data/verification-ljud.json')
