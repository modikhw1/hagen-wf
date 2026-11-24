"""Kontaktblad av brons steg: blockoutbild, t, finger, premiss och bevisklipp. Skylten ritas i bilden."""
import json
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent


def font(storlek, fet=False):
    for namn in (['arialbd.ttf', 'segoeuib.ttf'] if fet else ['arial.ttf', 'segoeui.ttf']):
        try:
            return ImageFont.truetype(namn, storlek)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    # argument: [bro-fil] [bildmapp] [prefix] [utfil]
    a = sys.argv[1:]
    bro = json.loads(Path(a[0] if a else HERE / 'bro_notan_gelato.json').read_text(encoding='utf-8'))
    mapp = Path(a[1]) if len(a) > 1 else HERE / 'ut/blockout'
    prefix = a[2] if len(a) > 2 else 'steg'
    steg = bro['steg']
    W, H, T = 360, 640, 250
    # 'rader' i filen ger en rad per version (t.ex. originalet överst, kundens under)
    radlangder = bro.get('rader') or None
    per_rad = max(radlangder) if radlangder else 5
    plats = []
    if radlangder:
        for ri, n in enumerate(radlangder):
            plats += [(ci, ri) for ci in range(n)]
    else:
        plats = [(i % per_rad, i // per_rad) for i in range(len(steg))]
    rader = max(p[1] for p in plats) + 1
    blad = Image.new('RGB', (per_rad * W, rader * (H + T)), (250, 250, 248))
    d = ImageDraw.Draw(blad)
    f1, f2, f3 = font(20, True), font(15), font(13)
    for i, s in enumerate(steg):
        x, y = plats[i][0] * W, plats[i][1] * (H + T)
        bild = Image.open(mapp / f'{prefix}_{i:02d}.png').convert('RGB').resize((W, H))
        skylt = s['scen'].get('skylt')
        if skylt:
            bd = ImageDraw.Draw(bild)
            w = bd.textlength(skylt, font=f1)
            bd.rectangle([(W - w) / 2 - 8, 70, (W + w) / 2 + 8, 104], fill=(255, 255, 255))
            bd.text(((W - w) / 2, 74), skylt, font=f1, fill=(0, 0, 0))
        blad.paste(bild, (x, y))
        d.rectangle([x, y, x + W - 1, y + H - 1], outline=(200, 60, 40) if s.get('sprang') else (200, 200, 200),
                    width=4 if s.get('sprang') else 1)
        ty = y + H + 8
        d.text((x + 10, ty), (f"t = {s['t']:.2f}" if isinstance(s['t'], float) else f"takt {s['t']}") + ('   SPRÅNG' if s.get('sprang') else ''), font=f1,
               fill=(200, 60, 40) if s.get('sprang') else (0, 0, 0))
        ty += 28
        for rad in textwrap.wrap(s.get('finger') or 'start', 44)[:2]:
            d.text((x + 10, ty), rad, font=f2, fill=(30, 90, 160))
            ty += 19
        for rad in textwrap.wrap(s['premiss'], 50)[:6]:
            d.text((x + 10, ty), rad, font=f3, fill=(20, 20, 20))
            ty += 17
        ty += 4
        for rad in textwrap.wrap('Bevis: ' + s['bevis'], 50)[:3]:
            d.text((x + 10, ty), rad, font=f3, fill=(110, 110, 110))
            ty += 16
    ut = Path(a[3]) if len(a) > 3 else HERE / 'ut/bro_kontaktblad.png'
    blad.save(ut)
    print(ut, blad.size)


if __name__ == '__main__':
    sys.exit(main())
