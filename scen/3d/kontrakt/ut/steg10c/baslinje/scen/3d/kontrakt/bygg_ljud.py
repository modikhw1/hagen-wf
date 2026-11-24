"""plan.json -> ljudspår (WAV, 44,1 kHz stereo) och ljudrapport. Lokalt: ffmpeg och Piper (via tal.py), inget nätanrop.

python bygg_ljud.py <plan.json> <ut.wav> [<rapport.json>]

Originalljudet följer planens tidskarta (samma bitar som bilden). För varje ersatt replik (plan.tal):
  1. originalet i luckan, plus 40 ms på var sida, tas bort helt. Tal och ljudbädd (rumsljud, eventuell musik) går inte att skilja,
     så hela luckan ersätts. Det syns som ett kort hål i rumsljudet; se rapporten.
  2. den syntetiserade repliken (tal.passa, samma cache som kompilatorn) läggs vid luckans start i utdatatiden.
     Nivån sätts efter originalets RMS i luckan, med toppgräns 0,85 så att inget klipper.
Vid scengränser som inte är sammanhängande i källan görs 10 ms ton ut/in så att det inte knäpper.
"""
import json
import subprocess
import sys
import wave
from fractions import Fraction
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tal

SR = 44100


def avkoda(video):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2)


def upp(x):
    """22,05 kHz -> 44,1 kHz, linjär interpolation (tal), mono -> stereo."""
    y = np.interp(np.arange(0, len(x), tal.SR / SR), np.arange(len(x)), x).astype(np.float32)
    return np.stack([y, y], 1)


def rms(x): return float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0


def bygg(plan, ut_wav, rapport=None):
    fps = Fraction(plan['utdata']['fps_taljare'], plan['utdata']['fps_namnare']); f = float(fps)
    src = avkoda(plan['kallvideo']); tidskarta = plan['tidskarta']
    total = int(round(tidskarta[-1]['ut'][1] / f * SR)); ut = np.zeros((total, 2), np.float32)
    fade = int(.010 * SR)
    for i, iv in enumerate(tidskarta):
        if not iv['ljud']: continue
        k0, k1 = (int(round(v / f * SR)) for v in iv['kalla']); u0 = int(round(iv['ut'][0] / f * SR))
        seg = np.zeros((k1 - k0, 2), np.float32); have = src[k0:k1]; seg[:len(have)] = have   # källljudet är något kortare än bilden
        fore = tidskarta[i - 1] if i else None; efter = tidskarta[i + 1] if i + 1 < len(tidskarta) else None
        if fore is not None and not (fore['ljud'] and fore['kalla'][1] == iv['kalla'][0]): seg[:fade] *= np.linspace(0, 1, fade)[:, None]
        if efter is not None and not (efter['ljud'] and efter['kalla'][0] == iv['kalla'][1]): seg[-fade:] *= np.linspace(1, 0, fade)[:, None]
        ut[u0:u0 + len(seg)] = seg[:max(0, total - u0)]
    orig = ut.copy(); rader = []
    for t in plan.get('tal', []):
        s0, s1 = t['ut_slot_s']; pad = .04
        a, b = max(0, int(round((s0 - pad) * SR))), min(total, int(round((s1 + pad) * SR)))
        rms_o = rms(orig[int(round(s0 * SR)):int(round(s1 * SR))])
        x, ls, tempo = tal.passa(t['rost']['rost_id'], t['text'], t['slot_langd_s']); ny = upp(x)
        gain = float(np.clip(rms_o / max(rms(ny), 1e-6), .05, 4.0)); ny = ny * gain
        topp = float(np.abs(ny).max());
        if topp > .85: ny = ny * (.85 / topp); gain *= .85 / topp
        ff = int(.015 * SR)   # 15 ms ton ut och in runt hålet; i mitten är originalet helt borttaget
        hal = np.zeros(b - a, np.float32); hal[:ff] = np.linspace(1, 0, ff); hal[-ff:] = np.maximum(hal[-ff:], np.linspace(0, 1, ff)); hal[ff:-ff] = 0
        ut[a:b] *= hal[:, None]
        i0 = int(round(s0 * SR)); n = min(len(ny), total - i0); ut[i0:i0 + n] += ny[:n]
        rader.append(dict(edit=t['edit'], replik=t['replik'], text=t['text'], ut_slot_s=t['ut_slot_s'], rost=t['rost']['rost_id'],
                          original_rms=round(rms_o, 5), ny_rms_efter_niva=round(rms(ny[:n]), 5), niva_gain=round(gain, 3),
                          rms_ut_i_luckan=round(rms(ut[int(round(s0 * SR)):int(round(s1 * SR))]), 5),
                          syntetiserad_s=round(len(ny) / SR, 3), length_scale=round(ls, 3), extra_tempo=round(max(1.0, tempo), 3),
                          samplingar_skilda_mot_original=int(np.sum(np.abs(ut[a:b] - orig[a:b]) > 1e-4)), samplingar_i_luckan=int(b - a)))
    topp = float(np.abs(ut).max()); klippta = int(np.sum(np.abs(ut) >= .999))
    if topp > .98: ut *= .98 / topp
    with wave.open(str(ut_wav), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(ut, -1, 1) * 32767).astype(np.int16).tobytes())
    r = dict(langd_s=round(total / SR, 4), forvantad_langd_s=round(tidskarta[-1]['ut'][1] / f, 4), topp=round(topp, 4), klippta_samplingar=klippta,
             ersatta=rader, kalla='originalljud ur ' + Path(plan['kallvideo']).name, anmarkning='Tal och bakgrundsljud är inte separerade: hela luckan (plus 40 ms) ersätts, även rumsljudet i den.')
    if rapport: Path(rapport).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
    return r


if __name__ == '__main__':
    plan = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    r = bygg(plan, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    print(json.dumps({k: v for k, v in r.items() if k != 'ersatta'}, ensure_ascii=False)); [print(x) for x in r['ersatta']]
