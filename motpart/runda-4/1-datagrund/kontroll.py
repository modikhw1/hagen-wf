"""ffprobe + sha256 per hämtad fil -> manifest.jsonl. Jämför längd mot byggsten/hand/ut/klipp.jsonl (l1.langd, heltal s)
och mot lokal längd i e28/tek.jsonl. Läser bara.
Kör: scen/.venv/Scripts/python.exe -I -X utf8 motpart/runda-4/1-datagrund/kontroll.py"""
import json, hashlib, subprocess, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROT = HERE.parents[2]
UT = Path.home() / 'Downloads' / 'letrend-r4'
u = json.loads((HERE / 'urval.json').read_text(encoding='utf-8'))
tek = {}
for x in open(ROT / 'data/format/e28/tek.jsonl', encoding='utf-8'):
    r = json.loads(x); tek[r['id']] = r['langd']
bank = {}
for x in open(ROT / 'byggsten/hand/ut/klipp.jsonl', encoding='utf-8'):
    r = json.loads(x); bank[r['id']] = r
urv = {v['id']: v for v in u['valda']}
hist = [json.loads(x) for x in open(HERE / 'manifest_hamtning.jsonl', encoding='utf-8') if x.strip()]
ersatter = {h['id']: h['ersatter'] for h in hist if h.get('ersatter')}
meta_res = {h['id']: h for h in hist if h['status'] == 'vald_som_ersattare'}
reserv_meta = {}
# stratum/typ för ersättare ur urval.json (celler); typ/utfall/längd hämtas ur cellnamnet
def fr(frac):
    a, b = frac.split('/'); return int(a) / int(b) if int(b) else 0
out = []
for p in sorted(UT.glob('*.mp4')):
    i = p.stem
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', str(p)],
                                   capture_output=True, text=True).stdout)
    v = next((s for s in pr['streams'] if s['codec_type'] == 'video'), {})
    a = [s for s in pr['streams'] if s['codec_type'] == 'audio']
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    dur = float(pr['format'].get('duration', 0))
    st = urv[i]['stratum'] if i in urv else meta_res.get(i, {}).get('stratum')
    typ, utf, lk = (st.split('|') + [None] * 3)[:3] if st else (None, None, None)
    b = bank.get(i, {}).get('l1', {})
    out.append(dict(id=i, konto=i.rsplit('-', 1)[0], typ=typ, utfall=utf, langdklass=lk,
                    urval='ersattare' if i in ersatter else 'ordinarie', ersatter=ersatter.get(i),
                    bredd=v.get('width'), hojd=v.get('height'), codec=v.get('codec_name'),
                    fps=round(fr(v.get('avg_frame_rate', '0/1')), 3), langd_s=round(dur, 2),
                    ljud=bool(a), storlek=p.stat().st_size, sha256=h,
                    langd_klipp_jsonl=b.get('langd'), langd_tek=tek.get(i),
                    langd_avvikelse_s=(round(dur - b['langd'], 2) if b.get('langd') is not None else None)))
with open(HERE / 'manifest.jsonl', 'w', encoding='utf-8') as f:
    for r in out: f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(len(out), 'filer')
print('fps', dict(sorted(collections.Counter(round(r['fps']) for r in out).items())))
print('upplösning', dict(collections.Counter(f"{r['bredd']}x{r['hojd']}" for r in out).most_common(10)))
print('codec', dict(collections.Counter(r['codec'] for r in out)))
print('ljud', dict(collections.Counter(r['ljud'] for r in out)))
print('storlek MB', round(sum(r['storlek'] for r in out) / 1e6, 1))
av = [abs(r['langd_avvikelse_s']) for r in out if r['langd_avvikelse_s'] is not None]
print('längdavvikelse mot klipp.jsonl: n', len(av), 'max', max(av), 'median', sorted(av)[len(av)//2], '>2s:', sum(1 for x in av if x > 2))
