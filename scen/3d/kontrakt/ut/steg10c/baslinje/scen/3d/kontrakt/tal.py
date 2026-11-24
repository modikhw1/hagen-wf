"""Talsyntes för kontraktet: samma lokala Piper-väg som ../roster.py, men med egen cache under kontrakt/ut/notan/tal_cache.

roster.py importeras bara för synt(), atempo(), röst() och SR; dess cache (scen/3d/cache/roster) rörs inte.
Piper brusar (noise_scale .75, noise_w_scale .9), så samma text ger olika längd varje gång. Därför:
  - mat_langd() mäter längden med brus 0 (deterministisk) och används för tidspolicyn,
  - passa() syntetiserar som roster.passa (length_scale 0,75-1,3, sedan atempo) och cachar resultatet per (röst, text, lucka).
Samma cache läses av kompilatorn (planens siffror) och av bygg_ljud.py (ljudet), så de stämmer överens.
"""
import hashlib
import os
import sys
from pathlib import Path
import numpy as np
from gemensamt import HIT

CACHE = Path(os.environ.get('TAL_CACHE') or HIT / 'ut/notan/tal_cache')
SR = 22050
_rost = None


def _roster():
    global _rost
    if _rost is None:
        sys.path.insert(0, str(HIT.parent))
        sys.dont_write_bytecode = True
        try: import roster
        finally: sys.path.remove(str(HIT.parent))
        _rost = roster
    return _rost


def standardrost(roll):
    """Samma tilldelning som roster.py: kvinna = alma, annars nst."""
    return 'alma' if roll in ('woman', 'kvinna') else 'nst'


def _nyckel(*delar): return hashlib.sha1('|'.join(str(d) for d in delar).encode('utf-8')).hexdigest()[:16]


def mat_langd(rost, text):
    """Längd i sekunder i normaltempo, deterministiskt (brus 0), tystnad i ändarna trimmad som i roster.synt."""
    CACHE.mkdir(parents=True, exist_ok=True)
    fil = CACHE / f'mat_{_nyckel(rost, text)}.npy'
    if fil.exists(): return float(np.load(fil))
    from piper import SynthesisConfig
    r = _roster()
    ch = list(r.röst(rost).synthesize(text, syn_config=SynthesisConfig(length_scale=1.0, noise_scale=0.0, noise_w_scale=0.0)))
    x = np.concatenate([c.audio_float_array for c in ch]).astype(np.float32)
    on = np.where(np.abs(x) > .02)[0]
    x = x[max(0, on[0] - 220):on[-1] + 660] if len(on) else x
    v = round(len(x) / SR, 4); np.save(fil, np.float64(v)); return v


def passa(rost, text, lucka):
    """Repliken i sin lucka, som roster.passa. Returnerar (ljud float32 SR Hz, length_scale, extra_tempo)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    k = _nyckel(rost, text, f'{lucka:.4f}'); fil = CACHE / f'pass_{k}.npz'
    if fil.exists():
        z = np.load(fil); return z['x'], float(z['ls']), float(z['tempo'])
    r = _roster()
    x = r.synt(rost, text); naturlig = len(x) / SR; ls = float(np.clip(lucka / naturlig, .75, 1.3))
    if abs(ls - 1) > .03: x = r.synt(rost, text, ls)
    tempo = (len(x) / SR) / lucka
    if tempo > 1.04: x = r.atempo(x, tempo)
    x = x.astype(np.float32)
    np.savez(fil, x=x, ls=np.float64(ls), tempo=np.float64(tempo)); return x, ls, float(tempo)
