"""Designade röster (wiki: "designade röster, inte läppsynk"; ingen syntetisk likhet med källans skapare).

Lokalt och gratis: Piper (svenska röster: alma CC BY 4.0, lisa, nst CC0). Ingen röstkloning.
1. Casting: roll -> röst (actors[].voice.voice; standard A=alma/lisa enligt test, B=nst).
2. Varje replik syntetiseras och passas in i sin tidslucka ur ordtiderna (length_scale 0,75–1,3; därefter atempo om det behövs).
3. Spår per talare i källtid + mix (data/roster-mix.m4a).
4. Munkurvor (jawOpen 30 fps, källtid) ur varje talares spår: RMS-hölje, snabb attack, långsammare släpp -> data/mun-<id>.json.
5. --testa: alla repliker med lisa och alma, transkriberas tillbaka med kb-whisper-small -> ordfel (WER) per röst.
Kör: scen/.venv/Scripts/python.exe -B scen/3d/roster.py [--testa] [--skriv]
"""
import json, sys, wave, subprocess, re, time
from pathlib import Path
import numpy as np
from piper import PiperVoice, SynthesisConfig
ROOT = Path(__file__).resolve().parent; MOD = ROOT / 'modeller/piper'; SR = 22050
röster = {}
def röst(namn):
    if namn not in röster: röster[namn] = PiperVoice.load(str(MOD / f'sv_SE-{namn}-medium.onnx'))
    return röster[namn]
def synt(namn, text, ls=1.0, noise=.75):
    ch = list(röst(namn).synthesize(text, syn_config=SynthesisConfig(length_scale=ls, noise_scale=noise, noise_w_scale=.9)))
    x = np.concatenate([c.audio_float_array for c in ch]).astype(np.float32)
    on = np.where(np.abs(x) > .02)[0]                      # trimma tystnad i ändarna
    return x[max(0, on[0] - 220):on[-1] + 660] if len(on) else x
def atempo(x, f):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-filter:a', f'atempo={f:.4f}', '-f', 'f32le', '-'], input=x.tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32)
CACHE = ROOT / 'cache/roster'; CACHE.mkdir(parents=True, exist_ok=True)
def passa(namn, text, lucka):
    """repliken i sin lucka: length_scale 0,75–1,3, sedan atempo. Cache per (röst, text, lucka) så att en ändrad replik görs om på ~1 s."""
    import hashlib
    nyckel = hashlib.sha1(f'{namn}|{text}|{lucka:.3f}'.encode()).hexdigest()[:16]; fil = CACHE / f'{nyckel}.npy'
    if fil.exists(): x = np.load(fil); return x, float(np.load(CACHE / f'{nyckel}.ls.npy')), float(np.load(CACHE / f'{nyckel}.tempo.npy'))
    x = synt(namn, text); naturlig = len(x) / SR; ls = float(np.clip(lucka / naturlig, .75, 1.3))
    if abs(ls - 1) > .03: x = synt(namn, text, ls)
    tempo = (len(x) / SR) / lucka
    if tempo > 1.04: x = atempo(x, tempo)
    np.save(fil, x); np.save(CACHE / f'{nyckel}.ls.npy', ls); np.save(CACHE / f'{nyckel}.tempo.npy', tempo)
    return x, ls, tempo
norm = lambda s: re.sub(r'[^\wåäö ]', '', s.lower()).split()
def wer(ref, hyp):
    r, h = norm(ref), norm(hyp); d = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        prev, d[0] = d.copy(), i
        for j in range(1, len(h) + 1): d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(1, len(r))

def bygg(S):
    """spår, mix, munkurvor och rapport för scenen S (kan anropas varmt från rostserver.py)"""
    t0 = time.perf_counter()
    cast = {a['id']: (a.get('casting') or {}).get('voice') or (a.get('voice') or {}).get('voice') for a in S['actors']}
    test = json.loads((ROOT / 'data/roster-test.json').read_text(encoding='utf-8')) if (ROOT / 'data/roster-test.json').exists() else {}
    kvinna = min(('alma', 'lisa'), key=lambda n: test.get(n, 1))
    cast = {aid: (v or {'A': kvinna, 'B': 'nst'}.get(aid, 'nst')) for aid, v in cast.items()}
    total = max(sh['source']['outSec'] for sh in S['shots']) + .5
    spår = {aid: np.zeros(int(total * SR), np.float32) for aid in cast}; rapport = []
    for d in S['dialogue']:
        lucka = d['end'] - d['start']; x, ls, tempo = passa(cast[d['speaker']], d['text'], lucka)
        i0 = int(d['start'] * SR); n = min(len(x), len(spår[d['speaker']]) - i0); spår[d['speaker']][i0:i0 + n] += x[:n]
        fart = max(1.0, tempo) / ls; brott = False                  # fart mot rösten i normaltempo
        if d.get('originalText') and d['text'] != d['originalText']:   # rälsen: en ny replik får inte kräva mer än 15 % högre fart än originalet i samma lucka
            _, ls0, t0_ = passa(cast[d['speaker']], d['originalText'], lucka); brott = fart > max(1.0, t0_) / ls0 * 1.15
        rapport.append(dict(speaker=d['speaker'], text=d['text'], lucka_s=round(lucka, 2), langd_s=round(len(x) / SR, 2), length_scale=round(ls, 2),
                            extra_tempo=round(max(1.0, tempo), 2), fart=round(fart, 2), ralsbrott=bool(brott)))
    mix = sum(spår.values()); mix = mix / max(1e-6, np.abs(mix).max()) * .89
    def skriv_wav(p, x):
        with wave.open(str(p), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    skriv_wav(ROOT / 'data/roster-mix.wav', mix)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(ROOT / 'data/roster-mix.wav'), '-c:a', 'aac', '-b:a', '96k', str(ROOT / 'data/roster-mix.m4a')], check=True)
    # munkurvor: RMS per 1/30 s (fönster 40 ms), attack 1 bildruta, släpp ~3 bildrutor, normaliserat mot talarens p95
    for aid, x in spår.items():
        hop = SR // 30; n = len(x) // hop; rms = np.array([np.sqrt(np.mean(x[max(0, i * hop - hop // 4):i * hop + hop] ** 2)) for i in range(n)])
        ref = np.percentile(rms[rms > 1e-4], 95) if np.any(rms > 1e-4) else 1
        v = np.clip((rms / ref - .08) / .92, 0, 1) ** .8 * .75; ut = np.zeros_like(v)
        for i in range(n): ut[i] = v[i] if v[i] > (ut[i - 1] if i else 0) else (ut[i - 1] if i else 0) * .62 + v[i] * .38
        (ROOT / f'data/mun-{aid}.json').write_text(json.dumps(dict(fps=30, time='source', source=f'roster.py ({cast[aid]})', values=ut.round(3).tolist())), encoding='utf-8')
    out = dict(cast={k: f'piper sv_SE-{v}-medium' for k, v in cast.items()}, lines=rapport, seconds=round(time.perf_counter() - t0, 2), mix='data/roster-mix.m4a')
    (ROOT / 'data/roster.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    rader = [f"{r['speaker']} {cast[r['speaker']]:<5} lucka {r['lucka_s']:.2f} s  röst {r['langd_s']:.2f} s  (length_scale {r['length_scale']}, extra tempo x{r['extra_tempo']}){'  RÄLSBROTT: texten kräver mer än +15 % fart mot originalet i luckan' if r['ralsbrott'] else ''}  {r['text']}" for r in rapport]
    rader.append(f"tid {out['seconds']} s -> {out['mix']}")
    return out, cast, rader

if __name__ == '__main__':
    SPEC = Path(sys.argv[sys.argv.index('--spec') + 1]) if '--spec' in sys.argv else ROOT / 'scen3d.json'   # op.py skickar sin osparade scen
    S = json.loads(SPEC.read_text(encoding='utf-8'))
    if '--testa' in sys.argv:
        from faster_whisper import WhisperModel
        asr = WhisperModel('KBLab/kb-whisper-small', device='cpu', compute_type='int8', download_root=str(ROOT / 'cache/whisper'))
        res = {}
        for namn in ('alma', 'lisa', 'nst'):
            fel = []
            for d in S['dialogue']:
                x, _, _ = passa(namn, d['text'], d['end'] - d['start'])
                y = np.interp(np.arange(0, len(x), SR / 16000), np.arange(len(x)), x).astype(np.float32)
                segs, _ = asr.transcribe(y, language='sv', beam_size=1); hyp = ' '.join(s.text for s in segs)
                fel.append(wer(d['text'], hyp))
            res[namn] = round(float(np.mean(fel)), 3); print(namn, 'WER', res[namn], [round(f, 2) for f in fel])
        (ROOT / 'data/roster-test.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
        sys.exit()

    out, cast, rader = bygg(S)
    print(chr(10).join(rader))
    if '--skriv' in sys.argv:
        for fn in ('scen3d.json', 'scen3d.bas.json'):
            X = json.loads((ROOT / fn).read_text(encoding='utf-8'))
            for a in X['actors']:
                if a['id'] in cast and a['id'] in {d['speaker'] for d in X['dialogue']}:
                    a['voice'] = dict(voice=cast[a['id']], engine='piper (lokal)', mouthTrack=f"data/mun-{a['id']}.json", designed=True)
            X['audioDesigned'] = 'data/roster-mix.m4a'; X.setdefault('audioMode', 'designed')
            (ROOT / fn).write_text(json.dumps(X, ensure_ascii=False, indent=1), encoding='utf-8')
        print('röster inskrivna (actors[].voice, audioDesigned)')
