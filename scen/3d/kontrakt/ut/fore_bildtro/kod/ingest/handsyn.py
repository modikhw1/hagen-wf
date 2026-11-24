"""Handsyn: syns handen i källbilden, ruta för ruta?

    python handsyn.py <ingestmapp> [--kalla <kalla.json>]     (en tagningsmapp med meta.json, eller en mapp med S1, S2, ...)
    -> <tagning>/handsyn_<person>.json

Kroppsestimatorn ger alltid två händer, också när de är skymda av mat, bord eller inbränd text. De händerna är gissningar
och rör sig ryckigt. Det här steget säger vilka händer som har bildstöd, så att senare steg kan låta bli att lita på resten.

En hand räknas som synlig i en ruta när minst hälften av dess 21 ledpunkter
  - ligger i bild,
  - ligger i personens segmentmask (masker.npy, en annan modell än kroppsestimatorn), och
  - inte ligger i en inbränd textruta (om --kalla ges; rutorna kommer ur semantik.skarmtext).
Flimmer tas bort med majoritet över fem rutor. Gränserna är egna val, inte mätta."""
import argparse, json
from pathlib import Path
import numpy as np

HAND = dict(h=slice(21, 42), v=slice(42, 63))      # MHR70: höger hand 21–41, vänster 42–62
ANDEL = 0.5; FONSTER = 5


def tagningar(mapp):
    if (mapp / 'meta.json').exists(): return [mapp]
    return sorted([p for p in mapp.iterdir() if p.is_dir() and (p / 'meta.json').exists()], key=lambda p: int(p.name[1:]) if p.name[1:].isdigit() else 0)


def textrutor(kalla):
    """{tagning: [(lokal start, lokal slut, x0, y0, x1, y1)]} ur kalla.semantik.skarmtext, i tagningens egna rutor."""
    if not kalla: return {}
    K = json.loads(Path(kalla).read_text(encoding='utf-8')); fps = K['tidsbas']['fps_taljare'] / K['tidsbas']['fps_namnare'] if 'fps_taljare' in K['tidsbas'] else K['tidsbas'].get('fps', 30)
    start = {s['id']: s['start_s'] for s in K['semantik']['scener']}; ut = {}
    for t in K['semantik'].get('skarmtext', []):
        if not t.get('box') or t.get('scen') not in start: continue
        x, y, w, h = t['box']; a = round((t['start_s'] - start[t['scen']]) * fps); b = round((t['slut_s'] - start[t['scen']]) * fps)
        ut.setdefault(t['scen'].upper(), []).append((a, b, x, y, x + w, y + h))
    return ut


def majoritet(v, n=FONSTER):
    v = np.asarray(v, float); k = n // 2; p = np.pad(v, k, mode='edge')
    return np.array([p[i:i + n].mean() >= 0.5 for i in range(len(v))])


def spann(dold):
    ut, i = [], 0
    while i < len(dold):
        if dold[i]:
            j = i
            while j < len(dold) and dold[j]: j += 1
            ut.append([i, j]); i = j
        else: i += 1
    return ut


def mat(T, text=()):
    meta = json.loads((T / 'meta.json').read_text(encoding='utf-8')); W, H, N = meta['bredd'], meta['hojd'], meta['N']
    M = np.load(T / 'masker.npy', mmap_mode='r'); mh, mw = M.shape[1:]; res = {}
    for pdir in sorted((T / 'kropp').iterdir()):
        if not pdir.is_dir(): continue
        post = {}
        for namn, ix in HAND.items():
            andel, itext, finns = np.zeros(N), np.zeros(N), np.zeros(N, bool)
            for f in range(N):
                fil = pdir / f'{f:04d}.npz'
                if not fil.exists(): continue
                p = np.load(fil)['pred_keypoints_2d'][ix]; finns[f] = True
                ib = (p[:, 0] >= 0) & (p[:, 0] < W) & (p[:, 1] >= 0) & (p[:, 1] < H)
                q = np.clip((p / [W, H] * [mw, mh]).astype(int), 0, [mw - 1, mh - 1]); im = ib & M[f][q[:, 1], q[:, 0]].astype(bool)
                it = np.zeros(len(p), bool)
                for a, b, x0, y0, x1, y1 in text:
                    if a <= f < b: it |= (p[:, 0] >= x0) & (p[:, 0] <= x1) & (p[:, 1] >= y0) & (p[:, 1] <= y1)
                andel[f] = float((im & ~it).mean()); itext[f] = float((im & it).mean())
            synlig = majoritet(andel >= ANDEL) & finns; stord = majoritet(itext >= 0.25) & synlig
            post[namn] = dict(synlig=[bool(x) for x in synlig], stord=[bool(x) for x in stord], andel=[round(float(x), 2) for x in andel], dolda_spann=spann(~synlig),
                              synlig_andel_rutor=round(float(synlig.mean()), 3), i_text_andel_rutor=round(float((itext >= 0.25).mean()), 3))
        post.update(N=N, regel=f'synlig = minst {ANDEL:.0%} av handens ledpunkter i bild, i personmasken och utanför textrutor; majoritet över {FONSTER} rutor',
                    textrutor=len(text), status='modellbedomd')
        (T / f'handsyn_{pdir.name}.json').write_text(json.dumps(post, ensure_ascii=False), encoding='utf-8'); res[pdir.name] = post
    return res


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); a.add_argument('ingest'); a.add_argument('--kalla'); x = a.parse_args()
    text = textrutor(x.kalla)
    for T in tagningar(Path(x.ingest).resolve()):
        for pid, post in mat(T, text.get(T.name, ())).items():
            print(T.name, pid, {n: (post[n]['synlig_andel_rutor'], 'text', post[n]['i_text_andel_rutor'], 'dolda', post[n]['dolda_spann'][:4]) for n in ('h', 'v')})
