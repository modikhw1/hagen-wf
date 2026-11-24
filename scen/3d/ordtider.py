"""Ordtider ur källjudet (faster-whisper + KBLab kb-whisper, svenska) och koppling till replikerna i scen3d.json.

Varför: replikernas tider i scen3d.json är uppskattade per tagning. Ordens verkliga tider behövs för
  - textning/teleprompter som följer orden,
  - att en kortad tagning inte klipper mitt i en replik (op.py langd tar bort pauser, inte ord),
  - designade röster: varje replik får sin tidslucka.
Ut: data/ordtider.json  {model, words:[{w,start,end,p}], lines:[{i,speaker,text,start,end,words:[...]}]}
Kör: scen/.venv/Scripts/python.exe -B scen/3d/ordtider.py [small|medium|large]
"""
import json, re, sys, time, difflib
from pathlib import Path
ROOT = Path(__file__).resolve().parent
storlek = next((a for a in sys.argv[1:] if not a.startswith('--')), 'medium')

def manusord(text, hw):
    """manusets ord (det som visas) med tider ur Whispers ord: lika -> samma tid, ersatta -> Whisper-ordens spann delat
    efter teckenlängd, saknade -> mellan grannarna"""
    import difflib, re
    n = lambda s: re.sub(r'[^\wåäö]', '', s.lower()); mw = text.split(); ut = [None] * len(mw)
    sm = difflib.SequenceMatcher(a=[n(w) for w in mw], b=[n(w['w']) for w in hw], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1): ut[i1 + k] = (hw[j1 + k]['start'], hw[j1 + k]['end'])
        elif op == 'replace':
            a, b = hw[j1]['start'], hw[j2 - 1]['end']; L = sum(len(w) for w in mw[i1:i2]); t = a
            for k in range(i1, i2): d = (b - a) * len(mw[k]) / L; ut[k] = (t, t + d); t += d
    for k in range(len(mw)):   # saknade: mellan grannarna
        if ut[k] is None:
            fö = next((ut[j][1] for j in range(k - 1, -1, -1) if ut[j]), hw[0]['start'] if hw else 0)
            ef = next((ut[j][0] for j in range(k + 1, len(mw)) if ut[j]), fö + .25); ut[k] = (fö, max(fö, ef))
    return [dict(w=w, start=round(s, 3), end=round(e, 3)) for w, (s, e) in zip(mw, ut)]

def skriv_in(ut):
    """Replikerna i scen3d.json (och .bas) får ordtider: start/slut ur orden, words[] i källtid. Tagningarnas dialogue[] = repliker som överlappar."""
    for fn in ('scen3d.json', 'scen3d.bas.json'):
        S = json.loads((ROOT / fn).read_text(encoding='utf-8'))
        for d, r in zip(S['dialogue'], ut['lines']):
            if r['start'] is None: continue
            d.update(start=r['start'], end=r['end'], words=manusord(d['text'], r['words']), timing='ordtider (data/ordtider.json): manusets ord, Whispers tider')
        for sh in S['shots']:
            a, b = sh['source']['inSec'], sh['source']['outSec']
            sh['dialogue'] = [d for d in S['dialogue'] if d['start'] < b and d['end'] > a]
        (ROOT / fn).write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ordtider inskrivna i scen3d.json och scen3d.bas.json')

if '--bara-skriv' in sys.argv:
    skriv_in(json.loads((ROOT / 'data/ordtider.json').read_text(encoding='utf-8'))); sys.exit()
from faster_whisper import WhisperModel
t0 = time.perf_counter()
spec = json.loads((ROOT / 'scen3d.json').read_text(encoding='utf-8'))
ljud = ROOT / spec['audio']['src'] if isinstance(spec.get('audio'), dict) and spec['audio'].get('src') else ROOT / 'data/source-audio.m4a'
modell = WhisperModel(f'KBLab/kb-whisper-{storlek}', device='cpu', compute_type='int8', download_root=str(ROOT / 'cache/whisper'))
import subprocess, numpy as np    # avkoda med ffmpeg (PyAV i venv saknar faster-whispers argument)
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(ljud), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
ljudvåg = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
segs, info = modell.transcribe(ljudvåg, language='sv', word_timestamps=True, beam_size=5, vad_filter=False, condition_on_previous_text=False,
                               initial_prompt=' '.join(d['text'] for d in spec['dialogue']))   # kända repliker som ledtråd (stavning)
ord_ = [dict(w=w.word.strip(), start=round(w.start, 3), end=round(w.end, 3), p=round(w.probability, 3)) for s in segs for w in s.words]
norm = lambda s: re.sub(r'[^\wåäö]', '', s.lower())
# koppla orden till replikerna: sekvensjämförelse på normaliserade ord
rep_ord = [(i, norm(w)) for i, d in enumerate(spec['dialogue']) for w in d['text'].split()]
sm = difflib.SequenceMatcher(a=[w for _, w in rep_ord], b=[norm(o['w']) for o in ord_], autojunk=False)
tillhör = {}
for a, b, n in sm.get_matching_blocks():
    for k in range(n): tillhör[b + k] = rep_ord[a + k][0]
# omatchade ord: ärv replik från närmaste matchade granne i tid
for k in range(len(ord_)):
    if k not in tillhör:
        nära = sorted(tillhör, key=lambda j: abs(j - k)); tillhör[k] = tillhör[nära[0]] if nära else 0
rader = []
for i, d in enumerate(spec['dialogue']):
    w = [ord_[k] for k in sorted(tillhör) if tillhör[k] == i]
    rader.append(dict(i=i, speaker=d['speaker'], text=d['text'], est_start=d['start'], est_end=d['end'],
                      start=w[0]['start'] if w else None, end=w[-1]['end'] if w else None, words=w))
ut = dict(model=f'KBLab/kb-whisper-{storlek} (faster-whisper, int8, CPU)', language=info.language, audio=str(ljud.relative_to(ROOT)).replace('\\', '/'),
          seconds=round(time.perf_counter() - t0, 1), match_ratio=round(sm.ratio(), 3), words=ord_, lines=rader)
(ROOT / 'data/ordtider.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
print(f"{ut['model']}  {ut['seconds']} s  matchning {ut['match_ratio']}")
for r in rader: print(f"{r['speaker']} {r['start']}–{r['end']} (uppsk. {r['est_start']}–{r['est_end']:.2f})  {' '.join(w['w'] for w in r['words'])}")
if '--skriv' in sys.argv: skriv_in(ut)
