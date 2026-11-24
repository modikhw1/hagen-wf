"""Små, lokala beslut med synligt ursprung. Inga nätanrop."""
import numpy as np

KAMERA_GRANSER = dict(min_registrerade=8, min_andel=.5, max_fel_px=1., fokal_kvot=[.5, 2.5])
STATISK_VAG_M = .15  # Egen tolerans: b S5 7 cm, a S1 3 cm, Kenny S1 14 cm.


def kamerabeslut(k, m):
    """COLMAP:s fåpunktslösningar kan ha lågt fel men fel brännvidd."""
    g = KAMERA_GRANSER; dim = max(m['bredd'], m['hojd']); f = k.get('fokal_px')
    skal = []
    if (k.get('registrerade') or 0) < g['min_registrerade']: skal.append('för få registrerade rutor')
    if (k.get('registrerade') or 0) / max(k.get('av') or 0, 1) < g['min_andel']: skal.append('för låg registrerad andel')
    if k.get('fel_px') is None or not np.isfinite(k['fel_px']) or k['fel_px'] > g['max_fel_px']: skal.append('saknat eller för stort reprojektionsfel')
    if f is None or not np.isfinite(f) or not g['fokal_kvot'][0] * dim <= f <= g['fokal_kvot'][1] * dim: skal.append('brännvidd utanför intervallet')
    return dict(fokal_px=float(dim if skal else f), status='antagen' if skal else 'uppmatt',
                kalla='bildens längsta sida' if skal else 'COLMAP', colmap_fokal_px=f,
                orsak='; '.join(skal) if skal else 'Alla kvalitetskrav uppfyllda.', granser=g)


def kort_kamerabana(c):
    c = np.asarray(c)
    vag = float(np.linalg.norm(np.diff(c, axis=0), axis=1).sum())
    return dict(statisk=vag < STATISK_VAG_M, vag_m=vag, grans_m=STATISK_VAG_M,
                status='antagen', orsak='Liten metrisk translation räknas som stilla; skala 1 och nolltranslation. Rotation bevaras.' if vag < STATISK_VAG_M else 'Metrisk bana över toleransen.')


def overkropp(s):
    """Saknad benobservation och mycket osäker kropp ger inget golvstöd."""
    n = max(s.get('kanda', s.get('rutor', 0)), 1)
    ben = s.get('ben_synliga_rutor', 0) / n
    osaker = s.get('otillforlitliga', 0) / n
    return dict(endast_overkropp=bool(ben < .1 and osaker >= .3), status='antagen',
                benandel=ben, otillforlitlig_andel=osaker,
                orsak='Under 10 % benobservationer och minst 30 % otillförlitliga kroppsrutor; inget golv eller kontakt från denna kropp.')


def hallningsbeslut(hojd, benandel, placering=None):
    if benandel < .2 and placering and placering.get('hallning') in ('star', 'sitter'):
        return dict(hallning=placering['hallning'], status='modellbedomd', ursprung=placering['ursprung'],
                    orsak='Benen är skymda; bäckenhöjden ensam kan inte skilja stående bakom disk från sittande.')
    return dict(hallning='star' if hojd > .82 else 'sitter', status='antagen',
                orsak='Bäckenhöjd över 0,82 m; synliga ben prioriteras (tröskelklassning, ingen mätt sittkontakt).' if benandel >= .2 else 'Bäckenhöjd; semantisk hållning saknas, osäker klassning.')
