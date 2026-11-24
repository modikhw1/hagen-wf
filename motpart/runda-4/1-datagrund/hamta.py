"""Runda 4 steg 1: sekventiell, återupptagbar hämtning av urval.json till ~/Downloads/letrend-r4/.

Kör: scen/.venv/Scripts/python.exe -I -X utf8 motpart/runda-4/1-datagrund/hamta.py
- yt-dlp 2026.10.26 via uvx (samma som video/bank/hamta.mjs), format bv*[height<=720]+ba/b[height<=720]/b, mp4,
  ingen omkodning, ingen bildtaktsändring.
- Paus 2-4 s mellan klipp. Hoppar över befintliga mp4. Avbryter om ledigt utrymme < 6 GB eller total > 2 GB.
- Ett misslyckat klipp ersätts av nästa i samma cell (urval.json:reserv, kontotak 6) och loggas med orsak.
- Skriver manifest_hamtning.jsonl (en rad per försök) och hamta.logg.txt. Raderar ingenting.
"""
import json, random, shutil, subprocess, sys, time, re, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
UT = Path.home() / 'Downloads' / 'letrend-r4'
UT.mkdir(parents=True, exist_ok=True)
GB = 1024 ** 3
MIN_LEDIGT = 6 * GB
MAX_TOTAL = 2 * GB
YT = ['uvx', '--from', 'yt-dlp[default,curl-cffi]==2026.10.26', 'yt-dlp']
FORMAT = 'bv*[height<=720]+ba/b[height<=720]/b'

u = json.loads((HERE / 'urval.json').read_text(encoding='utf-8'))
man_fil = HERE / 'manifest_hamtning.jsonl'
logg_fil = HERE / 'hamta.logg.txt'
rng = random.Random(u['frö'] + 1)

def logg(s):
    t = time.strftime('%H:%M:%S') + ' ' + s
    print(t, flush=True)
    with open(logg_fil, 'a', encoding='utf-8') as f:
        f.write(t + '\n')

def man(rec):
    with open(man_fil, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def total():
    return sum(p.stat().st_size for p in UT.glob('*.mp4'))

def ledigt():
    return shutil.disk_usage(UT).free

# tidigare försök (återupptagning)
hist = []
if man_fil.exists():
    hist = [json.loads(x) for x in open(man_fil, encoding='utf-8') if x.strip()]
klara = {h['id'] for h in hist if h['status'] in ('ok', 'fanns')}
fallda = {h['id'] for h in hist if h['status'] == 'misslyckad'}
used = set(klara) | fallda
konto_n = collections.Counter()

valda = {v['id']: v for v in u['valda']}
kö = [v['id'] for v in u['valda']]
meta = dict(valda)
# ersättare som redan valts i tidigare körning
for h in hist:
    if h.get('ersatter') and h['id'] not in meta:
        meta[h['id']] = dict(id=h['id'], konto=h['konto'], stratum=h['stratum'])
        if h['id'] not in kö: kö.append(h['id'])
reserv = {k: [i for i in lst if i not in used and i not in meta] for k, lst in u['reserv'].items()}
res_konto = {}
for lst in u['reserv'].values():
    pass

def video_id(i): return i.rsplit('-', 1)[1]
def url(m): return f"https://www.tiktok.com/@{m['konto']}/video/{video_id(m['id'])}"

def ersatt(m):
    """Nästa i samma cell med kontotak; None om slut."""
    cell = m['stratum']
    lst = reserv.get(cell, [])
    for j, i in enumerate(lst):
        konto = i.rsplit('-', 1)[0]
        n = sum(1 for x in meta.values() if x['id'] not in fallda_nu and x['konto'] == konto)
        if n < u['per_konto_max']:
            lst.pop(j)
            return i
    return None

fallda_nu = set(fallda)
TRANSIENT = re.compile(r'timed out|timeout|HTTP Error 5\d\d|429|Connection|reset|temporar', re.I)

def hamta(m):
    fil = UT / f"{m['id']}.mp4"
    for forsok in (1, 2, 3):
        p = subprocess.run(YT + ['-f', FORMAT, '--merge-output-format', 'mp4', '--no-progress', '--no-write-comments',
                                 '--socket-timeout', '30', '-o', str(UT / f"{m['id']}.%(ext)s"), url(m)],
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
        if p.returncode == 0 and fil.exists() and fil.stat().st_size > 0:
            return True, ''
        err = ' '.join(l for l in (p.stderr or '').splitlines() if 'ERROR' in l)[:300] or (p.stderr or p.stdout)[-300:]
        if forsok < 3 and TRANSIENT.search(err):
            logg(f"  försök {forsok} fick tillfälligt fel: {err[:120]}; väntar 15 s")
            time.sleep(15)
            continue
        return False, err
    return False, err

i_kö = 0
nr = 0
while i_kö < len(kö):
    cid = kö[i_kö]; i_kö += 1
    m = meta[cid]
    if cid in klara: continue
    if cid in fallda: 
        continue
    fil = UT / f"{cid}.mp4"
    if fil.exists() and fil.stat().st_size > 0:
        man(dict(id=cid, konto=m['konto'], stratum=m['stratum'], status='fanns', ts=time.time())); klara.add(cid); continue
    if ledigt() < MIN_LEDIGT:
        logg(f'AVBRYT: ledigt {ledigt()/GB:.2f} GB < 6 GB'); sys.exit(2)
    if total() > MAX_TOTAL:
        logg(f'AVBRYT: total {total()/GB:.2f} GB > 2 GB'); sys.exit(3)
    nr += 1
    ok, err = hamta(m)
    if ok:
        man(dict(id=cid, konto=m['konto'], stratum=m['stratum'], status='ok', bytes=fil.stat().st_size, ts=time.time(),
                 **({'ersatter': m['ersatter']} if m.get('ersatter') else {})))
        klara.add(cid)
        logg(f"ok {cid} {fil.stat().st_size/1e6:.1f} MB (summa {total()/1e6:.0f} MB, ledigt {ledigt()/GB:.2f} GB)")
    else:
        # städa halvfärdiga delar (bara för detta id)
        for q in UT.glob(f'{cid}.*'):
            try: q.unlink()
            except OSError: pass
        man(dict(id=cid, konto=m['konto'], stratum=m['stratum'], status='misslyckad', orsak=err, ts=time.time()))
        fallda_nu.add(cid)
        logg(f"MISSLYCKAD {cid}: {err[:200]}")
        ny = ersatt(m)
        if ny:
            konto = ny.rsplit('-', 1)[0]
            meta[ny] = dict(id=ny, konto=konto, stratum=m['stratum'], ersatter=cid)
            kö.append(ny)
            man(dict(id=ny, konto=konto, stratum=m['stratum'], status='vald_som_ersattare', ersatter=cid, ts=time.time()))
            logg(f"  ersätts av {ny} (nästa i {m['stratum']})")
        else:
            logg(f"  ingen reserv kvar i {m['stratum']}")
    time.sleep(rng.uniform(2, 4))

logg(f'KLAR: {len(klara)} klara, {len(fallda_nu)} misslyckade, total {total()/1e6:.0f} MB, ledigt {ledigt()/GB:.2f} GB')
