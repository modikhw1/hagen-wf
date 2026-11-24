"""Lager 1, observationer per tagning: MoGe-2 (punkter, normaler, fokal) + ADE20K-etiketter (SegFormer).

Allmänt: samma kod för alla klipp. Tagningar tas ur ingest_v2-paketet om det finns, annars ur en
enkel klippdetektor (histogramavstånd). Tre nyckelrutor per tagning (början/mitt/slut).
Cache: ut/<klipp>/obs/<ruta>.npz, nyckel = källans sha256 + modellnamn. Inga nätverksanrop utöver
första nedladdning av öppna vikter.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import cv2, numpy as np, torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KLIPP = ROOT / 'data/format/kontroll/klipp'
MOGE = 'Ruicheng/moge-2-vits-normal'
SEG = 'nvidia/segformer-b2-finetuned-ade-512-512'
OBSV = 'obs/2:fp32,niva3,argmax-nearest'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def las_rutor(video):
    cap = cv2.VideoCapture(str(video)); fps = cap.get(cv2.CAP_PROP_FPS); out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(f)
    return out, fps


def klippdetektor(frames, trosk=0.45, min_len=8):
    """Hårda klipp ur HSV-histogram (Bhattacharyya). Returnerar halvöppna intervall."""
    hs = []
    for f in frames:
        h = cv2.calcHist([cv2.cvtColor(cv2.resize(f, (135, 240)), cv2.COLOR_BGR2HSV)], [0, 1], None, [32, 32], [0, 180, 0, 256])
        hs.append(cv2.normalize(h, h).flatten())
    cuts = [0]
    for i in range(1, len(hs)):
        if cv2.compareHist(hs[i - 1], hs[i], cv2.HISTCMP_BHATTACHARYYA) > trosk and i - cuts[-1] >= min_len:
            cuts.append(i)
    cuts.append(len(frames))
    return [[a, b] for a, b in zip(cuts, cuts[1:])]


def a_paket(nyckel):
    """Kroppspaket (ingest_v2): delade arbetsbord/data eller detta provs egen körning (ut/<nyckel>/ingest_v2)."""
    for pk in (ROOT / 'arbetsbord/data/ingest_v2' / nyckel / 'paket.json', HERE / 'ut' / nyckel / 'ingest_v2' / 'paket.json'):
        if pk.is_file():
            return pk
    return None


def tagningar_for(nyckel, frames):
    pk = a_paket(nyckel)
    if pk is not None:
        p = json.loads(pk.read_text(encoding='utf-8'))
        return [{'id': t['id'], 'ut': t['ut']} for t in p['tagningar']], 'ingest_v2-paket'
    return [{'id': f's{i + 1}', 'ut': u} for i, u in enumerate(klippdetektor(frames))], 'klippdetektor/hsv'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('klipp'); ap.add_argument('--nyckel'); a = ap.parse_args()
    video = KLIPP / (a.klipp + '.mp4'); nyckel = a.nyckel or a.klipp.split('-')[0]
    out = HERE / 'ut' / nyckel; (out / 'obs').mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter(); frames, fps = las_rutor(video); H, W = frames[0].shape[:2]
    shots, kalla = tagningar_for(nyckel, frames)
    src = sha(video)
    from moge.model.v2 import MoGeModel
    from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor
    torch.set_num_threads(max(1, torch.get_num_threads()))
    moge = MoGeModel.from_pretrained(MOGE).eval()
    proc = SegformerImageProcessor.from_pretrained(SEG); seg = SegformerForSemanticSegmentation.from_pretrained(SEG).eval()
    labels = seg.config.id2label
    tider = []
    for s in shots:
        a0, b0 = s['ut']; n = b0 - a0
        # Tre rutor bara där kroppar finns (skala/lodlinje ur flera lägen); annars mittrutan, som är den lokaliteten använder.
        s['nyckelrutor'] = sorted({a0 + min(2, n - 1), a0 + n // 2, b0 - 1 - min(2, n - 1)}) if kalla == 'ingest_v2-paket' else [a0 + n // 2]
        for u in s['nyckelrutor']:
            fil = out / 'obs' / f'{u:04d}.npz'
            try:
                if fil.is_file() and str(np.load(fil)['nyckel']) == src + MOGE + SEG + OBSV:
                    continue
            except Exception:
                pass  # halvskriven/trasig cache räknas som saknad
            t1 = time.perf_counter()
            rgb = cv2.cvtColor(frames[u], cv2.COLOR_BGR2RGB)
            with torch.inference_mode():
                mo = moge.infer(torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0, resolution_level=3, use_fp16=False)
                inp = proc(images=rgb, return_tensors='pt')
                lg = seg(**inp).logits
                lab = torch.nn.functional.interpolate(lg.argmax(1, keepdim=True).float(), size=(H, W), mode='nearest')[0, 0].long()
            tmp = fil.with_suffix('.tmp.npz')
            np.savez_compressed(tmp, nyckel=src + MOGE + SEG + OBSV, points=mo['points'].numpy().astype(np.float16),
                                normal=mo['normal'].numpy().astype(np.float16), mask=mo['mask'].numpy(),
                                intrinsics=mo['intrinsics'].numpy(), labels=lab.numpy().astype(np.uint8))
            tmp.replace(fil)  # atomisk publicering
            tider.append(round(time.perf_counter() - t1, 2))
    meta = {'klipp': a.klipp, 'nyckel': nyckel, 'kalla_sha256': src, 'fps': fps, 'bild_px': [W, H], 'antal_rutor': len(frames),
            'tagningar': shots, 'tagningskalla': kalla, 'modeller': {'djup': MOGE, 'etiketter': SEG},
            'etiketter': {int(k): v for k, v in labels.items()}, 'sek_per_ruta': tider, 'sek_totalt': round(time.perf_counter() - t0, 1)}
    (out / 'obs.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: meta[k] for k in ('nyckel', 'tagningskalla', 'sek_totalt')} | {'tagningar': len(shots), 'nya_rutor': len(tider)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
