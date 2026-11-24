"""Runda 4, steg 1: fröordnat, stratifierat urval (~200 klipp) ur de klipp som redan har lokala mått.

Kör: scen/.venv/Scripts/python.exe -I -X utf8 motpart/runda-4/1-datagrund/urval.py
Skriver urval.json (valda + reserver per stratum). Läser bara; hämtar ingenting. Frö: 20261120.

Population (alla villkor):
  - id finns i data/format/e28/tek.jsonl (lokala mått) OCH data/format/e15/klipp.jsonl (typ, konto, visningar)
  - lokal kopia finns i ~/Downloads/letrend-e13/<id>.mp4
  - längd 5-60 s (lokal längd i tek) för att hålla diskbudgeten
  - inte runda 3:s hold-out (motpart/runda-3-opus/A-domare/holdout_lista.txt) och inte klipp ur
    data/format/kontroll/klipp/ vars id står i den listan
Strata: typ (5, ur e15) x utfall (3) x längd (3).
  utfall = log(visningar / kontots median i e15, konton med >= 10 klipp); förlorare < -0,5 (under 0,61 x),
  vinnare > +0,5 (över 1,65 x), annars mitten.
  längd: kort < 15 s, mellan 15-30 s, lång > 30 s.
Kvot per typ: 40 (200 / 5). Inom typ: vinnare 14, förlorare 14, mitten 12. Inom utfall fördelas längd
jämnt (varvning). Högst 6 klipp per konto totalt. Inom varje cell är kandidaterna slumpordnade med
fröet; varvningen väljer bland kandidater från konton med minst antal valda hittills (slumpad
oavgjort). Reserver per cell = resten av cellens slumpordning, i ordning.
"""
import json, os, random, statistics, collections
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
D = ROT / 'data' / 'format'
E13 = Path.home() / 'Downloads' / 'letrend-e13'
FRO = 20261120
PER_KONTO = 6
KVOT = {'vinnare': 14, 'forlorare': 14, 'mitten': 12}

def jl(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(x) for x in f if x.strip()]

e15 = {r['id']: r for r in jl(D / 'e15/klipp.jsonl')}
tek = {r['id']: r for r in jl(D / 'e28/tek.jsonl')}
holdout = {x.strip() for x in open(ROT / 'motpart/runda-3-opus/A-domare/holdout_lista.txt', encoding='utf-8') if x.strip()}
kontroll_klipp = {p.stem for p in (D / 'kontroll/klipp').glob('*.mp4')}
holdout_kontroll = kontroll_klipp & holdout  # hold-out i kontrollmappen = listans id

# kontots median (alla klipp med visningar i e15)
perkonto = collections.defaultdict(list)
for r in e15.values():
    if r.get('visningar'):
        perkonto[r['konto']].append(r['visningar'])
med = {k: statistics.median(v) for k, v in perkonto.items() if len(v) >= 10}

import math
pop, uteslutna = [], collections.Counter()
for i, t in tek.items():
    r = e15.get(i)
    if r is None: uteslutna['saknas_i_e15'] += 1; continue
    if i in holdout or i in holdout_kontroll: uteslutna['holdout'] += 1; continue
    if not (E13 / f'{i}.mp4').exists(): uteslutna['ingen_lokal_kopia'] += 1; continue
    if not r.get('visningar') or r['konto'] not in med: uteslutna['saknar_utfall'] += 1; continue
    if not (5 <= t['langd'] <= 60): uteslutna['langd_utanfor_5_60'] += 1; continue
    z = math.log(r['visningar'] / med[r['konto']])
    utf = 'vinnare' if z > 0.5 else 'forlorare' if z < -0.5 else 'mitten'
    l = t['langd']
    lk = 'kort' if l < 15 else 'mellan' if l <= 30 else 'lang'
    pop.append(dict(id=i, konto=r['konto'], typ=r['typ'], visningar=r['visningar'], konto_median=med[r['konto']],
                    z=round(z, 3), utfall=utf, langd_lokal=l, langdklass=lk))

rng = random.Random(FRO)
cells = collections.defaultdict(list)
for p in sorted(pop, key=lambda p: p['id']):
    cells[(p['typ'], p['utfall'], p['langdklass'])].append(p)
for k in sorted(cells):
    rng.shuffle(cells[k])

typer = sorted({p['typ'] for p in pop})
konto_n = collections.Counter()
valda = []
for typ in typer:
    for utf, n in KVOT.items():
        order = ['kort', 'mellan', 'lang']
        ptr = {lk: 0 for lk in order}
        got = 0
        stuck = 0
        li = 0
        while got < n and stuck < 3:
            lk = order[li % 3]; li += 1
            lst = cells.get((typ, utf, lk), [])
            # kandidater från kontot med minst antal valda hittills, bland de som återstår
            cand = [p for p in lst if p['id'] not in {v['id'] for v in valda} and konto_n[p['konto']] < PER_KONTO]
            if not cand: stuck += 1; continue
            stuck = 0
            mn = min(konto_n[p['konto']] for p in cand[:60])
            first = next(p for p in cand if konto_n[p['konto']] == mn) if any(konto_n[p['konto']] == mn for p in cand) else cand[0]
            first = dict(first, stratum=f'{typ}|{utf}|{lk}')
            valda.append(first); konto_n[first['konto']] += 1; got += 1

valda_id = {v['id'] for v in valda}
reserv = {}
for k, lst in sorted(cells.items()):
    reserv['|'.join(k)] = [p['id'] for p in lst if p['id'] not in valda_id]

res = dict(frö=FRO, skript='motpart/runda-4/1-datagrund/urval.py', per_konto_max=PER_KONTO, kvot_per_typ=KVOT,
           populations_storlek=len(pop), uteslutna=dict(uteslutna), holdout_ids=sorted(holdout),
           antal_valda=len(valda), valda=valda, reserv=reserv,
           utvecklingsklipp='ingen identifierad (se URVAL.md)')
(ROT / 'motpart/runda-4/1-datagrund/urval.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')

print('pop', len(pop), dict(uteslutna))
print('valda', len(valda), 'konton', len(konto_n), 'max/konto', max(konto_n.values()))
for name in ('typ', 'utfall', 'langdklass'):
    print(name, dict(collections.Counter(v[name] for v in valda)))
print('tot lokal längd s', sum(v['langd_lokal'] for v in valda))
