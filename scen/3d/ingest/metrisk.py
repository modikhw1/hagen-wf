"""En läsgräns för MHR-sekvenser: meter före historiskt golv/kontakt.

Äldre npz ändras inte. Dict-gränssnitt, files och context manager gör att
även Blender läser exakt samma data som kompilatorns numpy-väg.
"""
import numpy as np
from pathlib import Path

_DOLDA_FOTTER = {}

class Sekvens(dict):
    @property
    def files(self): return list(self)
    def close(self): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass

def registrera_dolda_fotter(matning=None):
    """Byt processens explicita planbeslut; tomt anrop förhindrar läckage mellan planer."""
    _DOLDA_FOTTER.clear()
    for pm in (matning or {}).get('personer',[]):
        decision=pm.get('dolda_fotter')
        if decision and decision.get('tillampad'):
            _DOLDA_FOTTER[str(Path(pm['rorelse']['sokvag']).resolve())]=decision

def normalisera(data, beslut=None):
    s = Sekvens(data)
    if 'pose' not in s or 'cam_t' not in s: return s
    if int(s.get('golv_version', 0)) < 2:
        s['cam_t'] = s.get('cam_t_fore_golv', s.get('cam_t_fore_kontakt', s['cam_t']))
        s['pose'] = s.get('pose_fore_kontakt', s['pose'])
    s['golv_skala'] = np.ones(len(s['cam_t']))
    s['golv_version'] = np.array(2)
    if beslut and beslut.get('tillampad') and 'dold_fot_skala' not in s:
        faktor=float(beslut['faktor'])
        if not .92-1e-12<=faktor<=1.08+1e-12:raise ValueError('Dold-fot-faktor utanför kontraktets gräns')
        pose=np.array(s['pose'],dtype=float,copy=True);pose[...,:3]*=faktor
        s['pose']=pose;s['cam_t']=np.array(s['cam_t'],dtype=float,copy=True)*faktor
        s['dold_fot_skala']=np.array(faktor)
        s['dold_fot_status']=np.array('antagen')
    return s

def las(path, beslut=None):
    if beslut is None:beslut=_DOLDA_FOTTER.get(str(Path(path).resolve()))
    with np.load(path) as source:return normalisera(dict(source),beslut)

def skala_bakgrund(kamera, punkter, faktor, origo=None):
    """Samma likformighet för C och bakgrund; aldrig för kroppens cam_t.

Anrop kräver en separat belagd meterskala. Ingen sådan ny skala väljs av
GOLV2 från dessa klipp; funktionen anger den enda tillåtna skaloperationen.
"""
    if not np.isfinite(faktor) or faktor <= 0: raise ValueError('Ogiltig bakgrundsskala')
    o = np.zeros(3) if origo is None else np.asarray(origo, float)
    return o + (np.asarray(kamera)-o)*faktor, o + (np.asarray(punkter)-o)*faktor
