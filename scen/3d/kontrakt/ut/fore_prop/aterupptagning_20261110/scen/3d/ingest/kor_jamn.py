"""Kör om sekvens, varld, golv och kontakt för färdiga tagningar med den nya utjämningen (10 nov, jämn-passet). Lokalt: ingen Modal, GPU eller nätanrop,
`kropp` körs aldrig om. Går direkt på stegfunktionerna i ingest_klipp.py (inte på kommandoraden), så att inget annat steg (rum, blender) ogiltigförklaras
och inget flyttas till arkivet.

    scen/.venv/Scripts/python.exe scen/3d/ingest/kor_jamn.py <ingestmapp> [S1 S2 ...]      # tagningsmappar under <ingestmapp>
    scen/.venv/Scripts/python.exe scen/3d/ingest/kor_jamn.py --vertikaler <klipp>          # b, kenny eller a: lägg tillbaka vertikalerna efteråt

Före skrivning kopieras filerna som överskrivs (sekvens_*.npz, varld.npz, kontakt_*.json, utsnitt/palitlig/synlighet/bildskydd, tider.json, vertikaler.json)
till <tagning>/fore_jamn/ om en kopia inte redan finns. Ordning per tagning: sekvens, varld, golv, kontakt. Vertikalerna (kamera_vertikal.py) lades förr på
efteråt och körs därför som ett eget steg per klipp. Rummet (rum.json) körs inte om; det styr inga objekt i b, kenny och a (platsen har 0 uppmätta objekt).
Ett tungt steg i taget: kör inte flera tagningar parallellt.
"""
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

HIT = Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))
import ingest_klipp as IK

SKYDDA = ['sekvens_*.npz', 'varld.npz', 'kontakt_*.json', 'utsnitt_*.json', 'palitlig_*.json', 'synlighet_*.json', 'bildskydd_*.json', 'tider.json',
          'vertikaler.json', 'sekvens.klar', 'golv.klar', 'kontakt.klar']


def hade_golv(ut, pid):
    """En faktisk tidigare golvskala är starkare evidens än formatet i tider.json."""
    f = Path(ut) / 'fore_jamn' / f'sekvens_{pid}.npz'
    if not f.exists(): return False
    with np.load(f) as old:
        return 'golv_skala' in old and bool(np.any(old['golv_skala'] != 1.0))


def sakra(ut):
    m = ut / 'fore_jamn'; m.mkdir(exist_ok=True)
    for pat in SKYDDA:
        for p in ut.glob(pat):
            if not (m / p.name).exists(): shutil.copy2(p, m / p.name)


def kor_tagning(ut):
    ut = Path(ut).resolve(); sakra(ut); M = json.loads((ut / 'meta.json').read_text()); t = time.time(); r = {}   # meta.json rörs inte (rummets cache hashar den)
    for p in list(ut.glob('bildskydd_*.json')): p.rename(p.with_name(p.name + '.gammal'))   # kopia finns i fore_jamn/; nya körningar skriver ingen bildskyddslogg
    r['sekvens'] = IK.steg_sekvens(ut, M); (ut / 'sekvens.klar').write_text('ok')
    # Notans ingest gjordes 9 nov, före regeln om endast överkropp (utsnitt_*.json fanns inte). Körs golv och kontakt med dagens regel hoppas de över
    # för personer utan knän i bild, och kamerans cam_t-skala ändras (notan S1: golvskala 0,85 -> 1,0, kroppen hamnar längre bort och för liten).
    # För tagningar vars gamla sekvenslogg saknar utsnittsbeslut skrivs därför `endast_overkropp: false` med orsaken, så att golv och kontakt går som förr.
    gammal = json.loads((ut / 'fore_jamn' / 'tider.json').read_text()).get('sekvens', {})
    for u in ut.glob('utsnitt_*.json'):
        if 'utsnitt' not in gammal.get(u.stem[8:], {}) or hade_golv(ut, u.stem[8:]):   # den gamla sekvenskörningen loggade inget utsnittsbeslut: ingest före regeln
            d = json.loads(u.read_text()); d.update(endast_overkropp=False, status='antagen', orsak_jamn='Tidigare körning använde golv, eller saknar utsnittsbeslut. Golv och kontakt bevaras för samma 3D-registrering; ingen ny golvmätning påstås. Ursprungligt beslut: ' + json.dumps({k: d.get(k) for k in ('endast_overkropp', 'knan_i_egen_ruta_andel', 'orsak')}, ensure_ascii=False))
            u.write_text(json.dumps(d))
    r['varld'] = IK.steg_varld(ut, M)
    r['golv'] = IK.steg_golv(ut, M); (ut / 'golv.klar').write_text('ok')
    from kontakt import steg_kontakt
    r['kontakt'] = steg_kontakt(ut, M); (ut / 'kontakt.klar').write_text('ok')
    IK.logg(ut, 'jamn_omkorning', time.time() - t, stegen='sekvens, varld, golv, kontakt')
    return r


def vertikaler(klipp):
    sys.path[:0] = [str(HIT.parent / 'kontrakt'), str(HIT.parent / 'kontrakt' / 'semantik')]
    from sem_gemensamt import KLIPP
    from kamera_vertikal import kor
    from textarbete import backup, jsonfil
    info = KLIPP[klipp]; ingest = HIT / 'ut' / info['ingest']
    sem = HIT.parent / 'kontrakt' / 'semantik' / 'ut' / klipp / 'semantik.json'
    return kor(ingest, sem, backup, jsonfil)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--vertikaler':
        vertikaler(a[1]); print('vertikaler klara', a[1]); sys.exit(0)
    rot = Path(a[0]).resolve(); namn = a[1:] or sorted(p.name for p in rot.glob('S*') if (p / 'meta.json').exists())
    for n in sorted(namn, key=lambda s: int(s[1:])):
        t = time.time(); r = kor_tagning(rot / n)
        v = r['varld']; print(n, f'{time.time() - t:.0f} s', 'sekvens', {k: x for k, x in r['sekvens'].items() if not isinstance(x, dict) or k == 'utsnitt'}, 'varld skala', v.get('skala'),
                              'vag_m', v.get('kamerans_vag_m'), v.get('skalbeslut', {}).get('status'), flush=True)
