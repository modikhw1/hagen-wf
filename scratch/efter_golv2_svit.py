"""Kör sviten seriellt från kontrakt/, med loggar och gräns mot stora diffar."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / 'scen/3d/kontrakt'
UT = K / 'ut/efter_golv2/svit'
UT.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
moduler = ['test_flode', 'test_rumsmall', 'test_regler', 'test_text_disk',
           'test_kroppmatt', 'test_props', 'test_handelser', 'test_snabb',
           'test_steg11', 'bro.test_bro']
jobb = [(m, ['-m', 'unittest', '-v', m]) for m in moduler]
jobb += [('ingest.test_rum', ['-m', 'unittest', 'discover', '-v', '-s', '../ingest', '-p', 'test_rum.py']),
         ('semantik', ['semantik/test_semantik.py'])]
resultat = []
for namn, args in jobb:
    print('START', namn, flush=True)
    start = time.perf_counter()
    try:
        r = subprocess.run([sys.executable, '-B', *args], cwd=K, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           encoding='utf-8', timeout=240)
        text = r.stdout
        kod = r.returncode
    except subprocess.TimeoutExpired as e:
        text = (e.stdout or b'').decode('utf-8', errors='replace') if isinstance(e.stdout, bytes) else (e.stdout or '')
        text += '\nAVBRUTET efter 240 s; jämför eventuella stora planer separat.\n'
        kod = -1
    (UT / (namn + '.log')).write_text(text, encoding='utf-8', newline='\n')
    antal = re.search(r'Ran (\d+) tests?', text)
    rad = dict(modul=namn, antal=int(antal[1]) if antal else None,
               exit=kod, sekunder=round(time.perf_counter()-start, 2))
    resultat.append(rad)
    print(json.dumps(rad), flush=True)
    (UT / 'resultat.json').write_text(json.dumps(resultat, indent=2)+'\n', encoding='utf-8', newline='\n')
    if kod:
        print(text[-6000:], flush=True)
        sys.exit(1)
print('KLART', sum(x['antal'] or 0 for x in resultat), 'unittest-prov; semantik exit 0', flush=True)
