"""En läsgräns för MHR-sekvenser: meter före historiskt golv/kontakt.

Äldre npz ändras inte. Dict-gränssnitt, files och context manager gör att
även Blender läser exakt samma data som kompilatorns numpy-väg.
"""
import numpy as np

class Sekvens(dict):
    @property
    def files(self): return list(self)
    def close(self): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass

def normalisera(data):
    s = Sekvens(data)
    if 'pose' not in s or 'cam_t' not in s: return s
    if int(s.get('golv_version', 0)) < 2:
        s['cam_t'] = s.get('cam_t_fore_golv', s.get('cam_t_fore_kontakt', s['cam_t']))
        s['pose'] = s.get('pose_fore_kontakt', s['pose'])
    s['golv_skala'] = np.ones(len(s['cam_t']))
    s['golv_version'] = np.array(2)
    return s

def las(path):
    with np.load(path) as source: return normalisera(dict(source))

def skala_bakgrund(kamera, punkter, faktor, origo=None):
    """Samma likformighet för C och bakgrund; aldrig för kroppens cam_t.

Anrop kräver en separat belagd meterskala. Ingen sådan ny skala väljs av
GOLV2 från dessa klipp; funktionen anger den enda tillåtna skaloperationen.
"""
    if not np.isfinite(faktor) or faktor <= 0: raise ValueError('Ogiltig bakgrundsskala')
    o = np.zeros(3) if origo is None else np.asarray(origo, float)
    return o + (np.asarray(kamera)-o)*faktor, o + (np.asarray(punkter)-o)*faktor
