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


# Fysiskt rimlig bana för en handhållen mobil inomhus. Egna gränser (inga mätningar): en snabb handhållen svepning når några m/s;
# över 5 m/s (p90) eller över 5 m/s * klippets längd i total sträcka är omöjligt. Skalan på COLMAP-banan är fri, så en orimlig
# bana betyder nästan alltid att skalan inte är bestämd, inte att kameran rörde sig så.
KAMERA_FYSIK = dict(p90_fart_m_s=5., max_fart_m_s=15., vag_per_s_m=5.)


def kamerabana_rimlig(c, fps):
    """Kontrollera en metrisk kamerabana (N,3 i meter). Returnerar dict med rimlig, de uppmätta värdena, gränserna och skälen."""
    c = np.asarray(c, float); g = KAMERA_FYSIK
    steg = np.linalg.norm(np.diff(c, axis=0), axis=1) * fps if len(c) > 1 else np.zeros(1)
    vag = float(steg.sum() / fps); langd = max(len(c) / fps, 1e-9); skal = []
    p90 = float(np.percentile(steg, 90)); mx = float(steg.max())
    if p90 > g['p90_fart_m_s']: skal.append(f'p90-fart {p90:.3g} m/s över {g["p90_fart_m_s"]} m/s')
    if mx > g['max_fart_m_s']: skal.append(f'maxfart {mx:.3g} m/s över {g["max_fart_m_s"]} m/s')
    if vag > g['vag_per_s_m'] * langd: skal.append(f'sträcka {vag:.3g} m över {g["vag_per_s_m"]} m/s * {langd:.2f} s')
    return dict(rimlig=not skal, vag_m=vag, p90_fart_m_s=p90, max_fart_m_s=mx, granser=dict(g), skal=skal)


def skala_bestamd(ojamnhet, relativ_spridning=.02):
    """Skalsökningen (steg_varld) minimerar rotbanans ojämnhet över k. Är kurvan platt (spridning < 2 % av medel) hänger roten inte på
    kamerans translation under de rutor där personen syns, och k är oidentifierbar (kenny S2: kameran stod still när personen syntes)."""
    o = np.asarray(ojamnhet, float); return bool((o.max() - o.min()) / (o.mean() + 1e-12) >= relativ_spridning)
