"""Extract the exact mapped source frames; no generation or image retouching."""
import json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
shots = json.loads((HERE.parent / 'tagningslista.json').read_text(encoding='utf-8'))['tagningar']
panels = []
for shot in shots:
    sid = shot['id']
    target = HERE / 'referenser' / f'kalla_{sid}.png'
    source_frame = round(shot['kalla_s'][0] * 30)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(HERE.parents[2] / 'klipp/d-dialog-notan.mp4'), '-vf', f"select=eq(n\\,{source_frame})", '-frames:v', '1', str(target)], check=True)
    pair = Image.new('RGB', (432, 408), '#202020')
    for x, p in [(0, target), (216, HERE.parent / 'ut' / f'forsta_{sid}.png')]:
        im = Image.open(p).convert('RGB').resize((216, 384))
        pair.paste(im, (x, 24))
    ImageDraw.Draw(pair).text((8, 5), f'{sid} source | blockout', fill='white')
    panels.append(pair)
sheet = Image.new('RGB', (432*4, 408*2), '#202020')
for i, panel in enumerate(panels): sheet.paste(panel, ((i%4)*432, (i//4)*408))
sheet.save(HERE / 'referenser' / 'oversikt.jpg')
