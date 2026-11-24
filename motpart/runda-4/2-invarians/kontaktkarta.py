"""Kontaktkarta: original och varje ingrepp för ett klipp. Läser W/kontakt[_dry]/<id>/ (skrivs av test_kor.py) och bygg_logg.
  python kontaktkarta.py --lage test|dry --id <id>
Skriver kontaktkarta_<kort id>_<del>.png i denna mapp.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mat_adapter as M

HER = Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("--lage", required=True)
ap.add_argument("--id", required=True)
a = ap.parse_args()
pre = "" if a.lage == "test" else "dry_"
KONT = M.W / ("kontakt" if a.lage == "test" else "kontakt_dry") / a.id
logg = {}
for l in (HER / f"{pre}bygg_logg.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(l)
    if r["id"] == a.id and "sha256" in r:
        logg[r["variant"]] = r
RADER = ["O", "C", "N0", "N1", "N2", "N3", "N4", "N5", "N6", "P"]
H = 170
BW = 300
cdur = None
meta = {n: json.load(open(KONT / f"{n}_meta.json")) for n in RADER if (KONT / f"{n}_meta.json").exists()}
lj = {n: np.load(KONT / f"{n}_ljud.npy").astype(np.float32) for n in RADER if (KONT / f"{n}_ljud.npy").exists()}
nC = len(lj["C"])


def foto(p, h=H):
    im = Image.open(p).convert("RGB")
    return im.resize((max(1, round(im.width * h / im.height)), h))


def rad(n):
    bilder = [foto(KONT / f"{n}_f{k}.png") for k in range(3)]
    sek = [KONT / f"{n}_s{k}.png" for k in range(1, 7) if (KONT / f"{n}_s{k}.png").exists()]
    sb = [foto(p) for p in sek]
    ww = sum(b.width for b in bilder) + 20 + sum(b.width for b in sb) + 10
    return bilder, sb, ww


rb = {n: rad(n) for n in RADER if (KONT / f"{n}_f0.png").exists()}
wmax = max(v[2] for v in rb.values())
for del_, namn in enumerate((RADER[:5], RADER[5:])):
    bredd = 230 + wmax + BW + 20
    sheet = Image.new("RGB", (bredd, (H + 30) * len(namn)), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for r, n in enumerate(namn):
        if n not in rb:
            continue
        y = r * (H + 30)
        L = logg.get(n, {})
        ff = L.get("ffprobe", {}).get("video", {})
        s = L.get("slutider", {})
        vol = L.get("volym", {})
        txt = [f"{n}", f"{ff.get('width')}x{ff.get('height')} {ff.get('codec_name')}", f"fps {ff.get('avg_frame_rate')}  pkt {s.get('v', {}).get('paket')}",
               f"slut v {s.get('v', {}).get('slut'):.3f}" if s.get("v", {}).get("slut") else "", f"slut a {s.get('a', {}).get('slut'):.3f}" if s.get("a", {}).get("slut") else "",
               f"mean {vol.get('mean')} dB  max {vol.get('max')} dB"]
        for k, t in enumerate(txt):
            d.text((6, y + 4 + k * 14), t, fill=(255, 255, 255) if k == 0 else (200, 200, 200))
        x = 230
        bilder, sb, _ = rb[n]
        for b in bilder:
            sheet.paste(b, (x, y)); x += b.width
        x += 20
        pts = meta[n]["pts"]
        for k, b in enumerate(sb):
            sheet.paste(b, (x, y))
            if k < len(pts):
                d.text((x + 2, y + H), f"{pts[k]:.3f}", fill=(255, 220, 120))
            x += b.width
        # ljudkuvert, gemensam skala (±1) och gemensam tid per pixel
        wx0 = 230 + wmax + 10
        d.rectangle([wx0, y, wx0 + BW, y + H], outline=(70, 70, 70))
        mid = y + H // 2
        x_ = lj.get(n)
        if x_ is not None and len(x_):
            spp = nC / BW
            ncol = min(BW, int(len(x_) / spp))
            for c in range(ncol):
                seg = x_[int(c * spp):int((c + 1) * spp)]
                if len(seg):
                    d.line([wx0 + c, mid - int(seg.max() * H / 2), wx0 + c, mid - int(seg.min() * H / 2)], fill=(120, 200, 255))
    sheet.save(HER / f"kontaktkarta_{a.id.split('-')[0]}_{del_ + 1}.png")
print("klart")
