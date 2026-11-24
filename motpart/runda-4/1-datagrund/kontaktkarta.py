"""Kontaktkartor: (1) 40 slumpade klipp (frö 20261121), en ruta ur mitten; (2) 3 klipp x 8 tätt samplade rutor (4 bilder/s ur 2 s).
Kör: scen/.venv/Scripts/python.exe -I -X utf8 motpart/runda-4/1-datagrund/kontaktkarta.py"""
import json, random, subprocess, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
UT = Path.home() / 'Downloads' / 'letrend-r4'
man = [json.loads(x) for x in open(HERE / 'manifest.jsonl', encoding='utf-8')]
rng = random.Random(20261121)
sl = rng.sample(sorted(man, key=lambda r: r['id']), 40)
tmp = Path(tempfile.mkdtemp(prefix='kk_'))
for n, r in enumerate(sl):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(r['langd_s'] / 2), '-i', str(UT / f"{r['id']}.mp4"), '-frames:v', '1',
                    '-vf', 'scale=180:320:force_original_aspect_ratio=decrease,pad=180:320:(ow-iw)/2:(oh-ih)/2:color=black', str(tmp / f'{n:02d}.jpg')], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '1', '-i', str(tmp / '%02d.jpg'), '-vf', 'tile=10x4:padding=4:color=white', '-frames:v', '1', str(HERE / 'kontaktkarta_40.jpg')], check=True)
(HERE / 'kontaktkarta_40.txt').write_text('\n'.join(f"{n//10+1},{n%10+1}: {r['id']} {r['typ']} {r['utfall']} {r['fps']}fps {r['bredd']}x{r['hojd']}" for n, r in enumerate(sl)), encoding='utf-8')
# tät: 3 klipp med 25-30 fps och längd >= 8 s, slumpade
kand = [r for r in man if r['langd_s'] >= 8 and r['fps'] >= 24]
tre = rng.sample(sorted(kand, key=lambda r: r['id']), 3)
rows = []
for k, r in enumerate(tre):
    d = tmp / f't{k}'; d.mkdir()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '3', '-t', '2', '-i', str(UT / f"{r['id']}.mp4"), '-vf', 'fps=4,scale=-2:300', str(d / '%02d.jpg')], check=True)
    row = HERE / f'_rad{k}.jpg'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '1', '-i', str(d / '%02d.jpg'), '-vf', 'tile=8x1:padding=3:color=white', '-frames:v', '1', str(row)], check=True)
    rows.append(row)
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + sum([['-i', str(p)] for p in rows], []) + ['-filter_complex', 'vstack=inputs=3', '-frames:v', '1', str(HERE / 'kontaktkarta_tat.jpg')], check=True)
for p in rows: p.unlink()
(HERE / 'kontaktkarta_tat.txt').write_text('\n'.join(f"rad {k+1}: {r['id']} {r['fps']}fps, 0,25 s mellan rutorna, sekund 3-5" for k, r in enumerate(tre)), encoding='utf-8')
print('ok', [r['id'] for r in tre])
