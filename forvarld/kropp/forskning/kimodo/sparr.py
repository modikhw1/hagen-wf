"""FORSKNING: spärr mot onaturliga rörelsekandidater, mätt mot originalet. Ingen språkmodell.

  matt(pos)                          kroppsmått per ruta och median. pos: MHR-leder i världen (T,127,3), meter, z upp (M.till_varld)
  sparr(kand, orig, vridning=False)  dict(godkand, skal, matt, grans): gränserna är relativa originalet, inte absoluta
  las_original() / las_kandidat(n)   b-tilltal S3 B och mm/ut/mening_<n>/sekvens.npz som positioner

Gränserna (GRANS) är diagnosgränser satta 17 nov så att 'uttrakad_vrid' (apan som inte står upprätt) stoppas
och originalet passerar. De är inte ägarens krav, och de ska flyttas när fler kandidater är bedömda av människa.
"""
import sys
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent; ROOT = HIT.parents[3]; MM = HIT.parent / 'mm'
sys.path.insert(0, str(MM)); import mhr_smpl as M  # noqa: E402

ix = M.ix
FOT = {'V': ('l_foot', 'l_ball', 'l_subtalar'), 'H': ('r_foot', 'r_ball', 'r_subtalar')}
KONTAKT_M = 0.05        # foten räknas som i golvkontakt när den är högst så här över golvet
UNDER_TOL_M = 0.03      # en led får ligga så här under originalets golv innan det räknas som genom golvet

# Diagnosgränser (relativa originalets median). Skäl i rapporten och i sparr().
GRANS = dict(
    kna_extra_bojning_grad=20,    # original 177°, apan 137-142° (35-40° mer): stående med lätt svikt ryms, sittande/hukande inte
    bal_extra_lutning_grad=10,    # original 5°, apan 19° (+14): att luta sig fram mot bordet ryms, framåtfallen bål inte
    huvud_extra_lutning_grad=15,  # original 26°, apan 55° (+29): en nick ryms; huvud som hänger gör det inte
    huvud_extra_vridning_grad=25, # samma men när meningen uttryckligen begär vridning/blick bort
    backen_sankning_cm=10,        # bäckenet närmare fötterna än så: knäna viker sig eller kroppen sjunker
    fotglidning_extra_cm=5,       # glidning med foten i golvet utöver originalets egen (läsningens darr)
    ryck_faktor=2.5,              # ryckets 95-percentil får vara högst så många gånger originalets
    axlar_extra_cm=8,             # höjdskillnad mellan axlarna utöver originalets
)


def _vinkel(a, b):
    c = np.sum(a * b, -1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1) + 1e-9)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def _fran_lodratt(v): return _vinkel(v, np.array([0., 0., 1.]))


def _yaw(v): return np.arctan2(v[..., 1], v[..., 0])


def golv(pos):
    """Golvets höjd: lägsta foten per ruta, 5-percentil över tagningen."""
    f = np.min([pos[:, ix(n), 2] for s in FOT.values() for n in s], axis=0)
    return float(np.percentile(f, 5))


def matt(pos, fps=30.0, golvniva=None):
    """Mått per ruta (nyckel 'ruta') och median (nyckel 'median'). golvniva: originalets golv (annars eget)."""
    p = np.asarray(pos, float); T = len(p); g = golv(p) if golvniva is None else golvniva; r = {}
    for s, pre in (('V', 'l_'), ('H', 'r_')):
        r[f'kna_{s}'] = _vinkel(p[:, ix(pre + 'upleg')] - p[:, ix(pre + 'lowleg')], p[:, ix(pre + 'foot')] - p[:, ix(pre + 'lowleg')])
    r['bal'] = _fran_lodratt(p[:, ix('c_neck')] - p[:, ix('root')])
    r['huvud'] = _fran_lodratt(p[:, ix('c_head')] - p[:, ix('c_neck')])
    fotz = np.min([p[:, ix(n), 2] for s in FOT.values() for n in s], axis=0)
    r['backen_cm'] = (p[:, ix('root'), 2] - fotz) * 100
    r['axlar_cm'] = np.abs(p[:, ix('l_uparm'), 2] - p[:, ix('r_uparm'), 2]) * 100
    anat = [i for i, n in enumerate(M.N) if not n.startswith('__')]
    r['under_golv_cm'] = (g - p[:, anat, 2].min(1)) * 100
    # huvudets vridning i sidled relativt bålen: ögonlinjen mot axellinjen, i vågplanet
    oga = p[:, ix('l_eye_null')] - p[:, ix('r_eye_null')]; axl = p[:, ix('l_uparm')] - p[:, ix('r_uparm')]
    r['huvud_yaw'] = np.degrees(np.unwrap(_yaw(oga) - _yaw(axl)))
    r['hand_V_cm'] = (p[:, ix('l_wrist'), 2] - p[:, ix('root'), 2]) * 100
    r['hand_H_cm'] = (p[:, ix('r_wrist'), 2] - p[:, ix('root'), 2]) * 100
    # fotglidning: vågrät väg medan foten ligger i golvet i båda rutorna
    glid = {}
    for s, namn in FOT.items():
        h = np.min([p[:, ix(n), 2] for n in namn], axis=0) - g; xy = p[:, ix(namn[0]), :2]
        k = (h[1:] < KONTAKT_M) & (h[:-1] < KONTAKT_M); d = np.linalg.norm(np.diff(xy, axis=0), axis=1)
        glid[s] = float(np.sum(d[k]) * 100); r[f'glid_{s}_cm'] = np.r_[0., np.cumsum(d * k) * 100]
    ryck = {}
    for n in ('root', 'l_wrist', 'r_wrist', 'c_head'):
        j = np.diff(p[:, ix(n)], 3, axis=0) * fps ** 3 if T > 3 else np.zeros((1, 3))
        ryck[n] = np.linalg.norm(j, axis=1)
    med = {k: round(float(np.median(v)), 2) for k, v in r.items() if not k.startswith('glid_')}
    med.update(golv_m=round(g, 3), under_golv_max_cm=round(float(r['under_golv_cm'].max()), 1),
               fotglidning_cm=round(max(glid.values()), 1), **{f'glid_{s}_cm': round(v, 1) for s, v in glid.items()},
               **{f'ryck95_{n}': round(float(np.percentile(v, 95)), 1) for n, v in ryck.items()},
               kna_min_p10=round(float(min(np.percentile(r['kna_V'], 10), np.percentile(r['kna_H'], 10))), 1))
    med['ryck95_max'] = max(med[f'ryck95_{n}'] for n in ryck)
    return dict(ruta=r, ryck=ryck, median=med)


def sparr(kand, orig, vridning=False, fps=30.0, grans=None):
    """Godkänd eller inte, med skäl. kand, orig: (T,127,3). vridning: meningen begär uttryckligen huvudvridning/blick bort."""
    G = dict(GRANS, **(grans or {})); g = golv(orig)
    mo, mk = matt(orig, fps)['median'], matt(kand, fps, golvniva=g)['median']; skal = []
    for s in ('V', 'H'):
        if mk[f'kna_{s}'] < mo[f'kna_{s}'] - G['kna_extra_bojning_grad']:
            skal.append(f"knä {s} {mk[f'kna_{s}']:.0f}° mot originalets {mo[f'kna_{s}']:.0f}° (högst {G['kna_extra_bojning_grad']}° mer böjt)")
    if mk['bal'] > mo['bal'] + G['bal_extra_lutning_grad']:
        skal.append(f"bålen lutar {mk['bal']:.0f}° mot {mo['bal']:.0f}° (högst +{G['bal_extra_lutning_grad']}°)")
    hg = G['huvud_extra_vridning_grad' if vridning else 'huvud_extra_lutning_grad']
    if mk['huvud'] > mo['huvud'] + hg:
        skal.append(f"huvudet lutar {mk['huvud']:.0f}° mot {mo['huvud']:.0f}° (högst +{hg}°)")
    if mk['backen_cm'] < mo['backen_cm'] - G['backen_sankning_cm']:
        skal.append(f"bäckenet {mk['backen_cm']:.0f} cm över fötterna mot {mo['backen_cm']:.0f} (högst {G['backen_sankning_cm']} cm lägre)")
    if mk['fotglidning_cm'] > mo['fotglidning_cm'] + G['fotglidning_extra_cm']:
        skal.append(f"foten glider {mk['fotglidning_cm']:.0f} cm i golvet mot {mo['fotglidning_cm']:.0f} (högst +{G['fotglidning_extra_cm']})")
    for n in ('root', 'l_wrist', 'r_wrist', 'c_head'):
        if mk[f'ryck95_{n}'] > mo[f'ryck95_{n}'] * G['ryck_faktor']:
            skal.append(f"ryck i {n} {mk[f'ryck95_{n}']:.0f} m/s³ mot {mo[f'ryck95_{n}']:.0f} (högst ×{G['ryck_faktor']})")
    if mk['axlar_cm'] > mo['axlar_cm'] + G['axlar_extra_cm']:
        skal.append(f"axlarna skiljer {mk['axlar_cm']:.0f} cm i höjd mot {mo['axlar_cm']:.0f} (högst +{G['axlar_extra_cm']})")
    if mk['under_golv_max_cm'] > max(mo['under_golv_max_cm'], 0) + UNDER_TOL_M * 100:
        skal.append(f"en led går {mk['under_golv_max_cm']:.0f} cm under golvet")
    return dict(godkand=not skal, skal=skal, matt=mk, original=mo, grans=dict(G, vridning=vridning))


def las_original():
    import tagning as TG
    t = TG.las('b-tilltal-ravara_n06-hand/kalla_0032.json', 'b-tilltal-ravara_n06-hand/liggare_0032.json', 's3', 'B')
    return t, M.till_varld(t['z'], t['V'])[0]


def las_kandidat(namn, t):
    """namn: 'trofe2' -> mm/ut/mening_trofe2/sekvens.npz, eller en sökväg till en .npz."""
    f = Path(namn) if namn.endswith('.npz') else MM / 'ut' / f'mening_{namn}' / 'sekvens.npz'
    z = dict(np.load(f)); n, m = len(t['V']['kam_R']), len(np.load(f)['pose'])
    if m > n: z = {k: (v[:n] if getattr(v, 'ndim', 0) and len(v) == m else v) for k, v in z.items()}   # längre än tagningen: kapas
    return M.till_varld(z, t['V'])[0]
