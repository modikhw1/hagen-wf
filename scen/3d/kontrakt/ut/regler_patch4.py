import sys
from pathlib import Path
sys.path.insert(0,str(Path('scen/3d/ingest').resolve()))
from sakra_filer import sakerhetskopiera
def edit(path,old,new):
 p=Path(path);s=p.read_text(encoding='utf-8')
 if old not in s:raise ValueError(f'{p}: {old[:100]}')
 sakerhetskopiera(p);p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')

I='scen/3d/ingest/ingest_klipp.py'
edit(I,"a.add_argument('--om', default=None); x = a.parse_args()", "a.add_argument('--om', default=None); a.add_argument('--till', choices=STEG); x = a.parse_args()")
edit(I,"    M = meta(klipp, ut); fran", "    sakerhetskopiera(ut)\n    M = meta(klipp, ut); fran")
edit(I,"    for i, s in enumerate(STEG):", "    for i, s in enumerate(STEG):\n        if x.till and i > STEG.index(x.till): break")

F='scen/3d/ingest/flera/ingest_flera.py'
edit(F,"KORT = 12", "KORT = 12\nfrom sakra_filer import sakerhetskopiera\nfrom semantik_input import hitta, Semantik\nfrom regler import kamerabeslut")
edit(F,"def budget_skriv(b): (HIT / 'budget.json').write_text(json.dumps(b, indent=1))", "def budget_skriv(b):\n    sakerhetskopiera(HIT / 'budget.json')\n    (HIT / 'budget.json').write_text(json.dumps(b, indent=1, ensure_ascii=False), encoding='utf-8')")
edit(F,"a.add_argument('--endast-dela', action='store_true'); x = a.parse_args()", "a.add_argument('--endast-dela', action='store_true')\n    a.add_argument('--semantiskt', action='store_true', help='Billiga steg för alla tagningar, semantikpaus, sedan bara berättelsepersoner.')\n    a.add_argument('--semantik'); a.add_argument('--granska-budget', action='store_true')\n    a.add_argument('--regler', action='store_true', help='Pröva befintlig brännvidd och personmängd, kör ogiltiga kroppar igen.')\n    a.add_argument('--till', default='rum', choices=['rum', 'jamfor'])\n    a.add_argument('--uppdrag', default='regler-2026-11-10'); a.add_argument('--uppdragstak', type=int, default=1500)\n    x = a.parse_args()")
edit(F,"    if x.endast_dela: return", "    if x.endast_dela: return\n    sakerhetskopiera(ut / 'status.json')\n    sem = None\n    if x.semantiskt or x.regler or x.semantik:\n        # Alla kontaktblad måste kunna byggas innan någon betald kropp startas.\n        for s in plan['tagningar']:\n            forsteg_personer(ut / 'klipp' / f'{s[\"id\"]}.mp4', ut / s['id'])\n        sf = hitta(ut, x.semantik)\n        if not sf or not sf.exists():\n            config = ut / 'semantik_klipp.json'\n            if not config.exists(): config.write_text(json.dumps(dict(ingest=str(ut), video=str(klipp), ut=str(ut / 'semantik')), ensure_ascii=False), encoding='utf-8')\n            print('STOPP före betald kropp. Kör följande uttryckliga semantikanrop och lokala ordtider, granska sedan och kör detta kommando igen:', flush=True)\n            print(f'{PY} scen/3d/kontrakt/semantik/semantik_ingest.py {config}', flush=True)\n            print(f'{PY} scen/3d/kontrakt/semantik/ordtider_klipp.py {config}', flush=True)\n            return\n        sem = Semantik(sf)")
edit(F,"        if (u / 'jamforelse.mp4').exists()", "        if not sem and (u / 'jamforelse.mp4').exists()")
edit(F,"        jobb = sum(len(v) for v in P.values());", "        om = None\n        if sem:\n            original = u / 'personer_matning.json'\n            if original.exists(): P = json.loads(original.read_text())\n            fp, rm, beslut = sem.filtrera(sid, P)\n            K = json.loads((u / 'kamera.json').read_text()) if (u / 'kamera.json').exists() else {}\n            kb = kamerabeslut(K, M)\n            import numpy as np\n            focals = [float(np.load(f)['fokal']) for f in u.glob('sekvens_*.npz') if f.stem[8:] in fp]\n            fore = json.loads((u / 'personer.json').read_text())\n            invalid = fore != fp or any(abs(f-kb['fokal_px']) > .01 for f in focals)\n            om = 'kropp' if invalid else ('varld' if x.regler else None)\n            P = fp\n            print(sid, 'kropp måste köras om' if invalid else 'kropp återanvänds', 'personrutor', sum(map(len, P.values())), 'kamera', kb, flush=True)\n            if not x.granska_budget:\n                sakerhetskopiera(u)\n                if not original.exists(): original.write_text(json.dumps(fore), encoding='utf-8')\n                (u / 'personer.json').write_text(json.dumps(fp), encoding='utf-8')\n                (u / 'semantik_beslut.json').write_text(json.dumps(dict(fil=str(sem.fil), roller=rm, beslut=beslut), ensure_ascii=False), encoding='utf-8')\n                K['beslut'] = kb; K['statisk'] = K.get('statisk', True) or kb['kalla'] != 'COLMAP'\n                (u / 'kamera.json').write_text(json.dumps(K), encoding='utf-8')\n        jobb = sum(len(v) for v in P.values());")
edit(F,"        spent = (u / 'kropp/timing.json').exists(); stopp = None", "        if x.granska_budget: continue\n        spent = (u / 'kropp/timing.json').exists() and om != 'kropp'; stopp = None")
edit(F,"            if len(P) == 0: stopp = 'inga personer spårade: kropp/sekvens har inget att göra'\n            elif est", "            if est")
edit(F,"            elif B['total'] + jobb > x.total:", "            elif sum(v['personrutor'] for v in B.get('korningar', []) if v['uppdrag'] == x.uppdrag) + jobb > x.uppdragstak: stopp = f'vakt: uppdragstaket {x.uppdragstak} personrutor skulle passeras'\n            elif B['total'] + jobb > x.total:")
edit(F,"            B['tagningar'][f'{ut.name}/{sid}'] = jobb; B['total'] += jobb; budget_skriv(B)", "            B['tagningar'][f'{ut.name}/{sid}'] = B['tagningar'].get(f'{ut.name}/{sid}', 0) + jobb\n            B.setdefault('korningar', []).append(dict(uppdrag=x.uppdrag, tagning=f'{ut.name}/{sid}', personrutor=jobb, status='reserverad före anrop'))\n            B['total'] += jobb; budget_skriv(B)")
edit(F,"str(k), str(u)], stdout=lg", "str(k), str(u), '--till', x.till] + (['--om', om] if om else []), stdout=lg")
edit(F,"    skriv()\n\n\ndef main", "    skriv()\n\n\ndef main") if False else None
# Budgetgranskning ska vara läsande, även status.json.
edit(F,"    skriv()\n\n\nif __name__", "    if not x.granska_budget: skriv()\n\n\nif __name__")

S='scen/3d/kontrakt/semantik/sem_gemensamt.py'
edit(S,"    if namn not in KLIPP: raise SystemExit", "    if Path(namn).is_file():\n        k = ladda(namn)\n        return dict(namn=Path(namn).stem, ingest=Path(k['ingest']).resolve(), video=Path(k['video']).resolve(), ut=Path(k['ut']).resolve())\n    if namn not in KLIPP: raise SystemExit")
M='scen/3d/ingest/mhr_rig.py'
edit(M,"float(np.load(sekvenser[0])['fokal'])", "float(np.load(sekvenser[0])['fokal']) if sekvenser else max(meta['bredd'], meta['hojd'])")
