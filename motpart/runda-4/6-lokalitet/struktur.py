"""struktur/1: rummet som primitiver i stället för pixelskärvor (jämförelsevariant 'Ls' bredvid 'Lt').

Facit 21 nov (Gemini 38 + Codex hold-out 16): rum och objekt faller sönder i skärvor så fort kameran vrids. Här byggs
samma observationer (lokalitet.py -> ut/<k>/struktur_in/<sid>.npz) om till hela former:
- golv: planet z=0 (L4), rektangel längs rummets huvudriktning över allt rum som syns
- väggar: vertikala plan inom observerad höjd, med anslutning till känt golv/tak när observationerna når dit
- tak: horisontellt plan om taket syns
- möbler (bänk, bord, spis, skåp): lådor längs huvudriktningen med observerad topp och botten.
  Syns bara framsidan sträcks lådan 0,6 m bort från kameran (antaget, märkt)
- kärl och mat: observerade SAM- eller Lt-nät med separat kontaktgeometri. Enstaka mätningar kan bilda pixelrutor.
Textur: pixeltäckning och kameradjup prövas i mittrutan. Visaren projicerar den per fragment.
Bakom personen används rumshjärnans hypotes om grind 1b släppt den.
Resten får ytans egen medelfärg och märks antagen.
Inga klippkonstanter. usage: python struktur.py <nyckel>
"""
from __future__ import annotations
import json, math, os, sys
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
CELL = 0.08  # m, rutnät på plana ytor
RUNDA = ('plate', 'bowl', 'cup', 'glass', 'bottle', 'pot', 'pan', 'food', 'mug', 'vase', 'jar', 'can')
FORMAL = RUNDA + ('tray', 'box', 'basket', 'bag')
MOBEL = {'table': 'bord', 'counter': 'bank', 'chair': 'stol', 'stool': 'stol', 'bench': 'stol'}
MOBELGRUPPER = ('bank', 'bord', 'spis', 'skap', 'stol')
RUMSGRUPPER = ('golv', 'vagg', 'tak', *MOBELGRUPPER)


def B(v):
    v = np.asarray(v, float); return np.stack([v[..., 0], -v[..., 1], -v[..., 2]], axis=-1)


class Kamera:
    def __init__(self, C, R, f, w0, h0):
        self.C, self.R, self.fx, self.fy, self.w0, self.h0 = C, R, f[0], f[1], w0, h0

    def proj(self, X):
        p = B((X - self.C) @ self.R)  # R^T (X - C) per rad, sedan till cv
        z = p[..., 2]; zz = np.where(z > 1e-3, z, np.nan)
        xn = 0.5 + self.fx * p[..., 0] / zz; yn = 0.5 + self.fy * p[..., 1] / zz
        return xn, yn, z


def manhattan_yaw(N, mask):
    n = N[mask]; h = n[:, :2]; l = np.linalg.norm(h, axis=1); h = h[(l > 0.8) & (np.abs(n[:, 2]) < 0.4)]
    if len(h) < 50:
        return 0.0
    a = np.mod(np.arctan2(h[:, 1], h[:, 0]), np.pi / 2); hist, kant = np.histogram(a, 90, (0, np.pi / 2))
    hist = np.convolve(np.r_[hist[-3:], hist, hist[:3]], np.ones(5) / 5, 'same')[3:-3]
    return float(kant[np.argmax(hist)] + (kant[1] - kant[0]) / 2)


def rot(yaw):
    c, s = math.cos(yaw), math.sin(yaw); return np.array([[c, -s], [s, c]])


def grid(o, a, b, na, nb):
    i, j = np.meshgrid(np.linspace(0, 1, na + 1), np.linspace(0, 1, nb + 1), indexing='ij')
    V = o + i[..., None] * a + j[..., None] * b; V = V.reshape(-1, 3)
    idx = np.arange((na + 1) * (nb + 1)).reshape(na + 1, nb + 1)
    t = np.concatenate([np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:]], -1).reshape(-1, 3),
                        np.stack([idx[:-1, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 3)])
    return V, t


def plan(o, a, b):
    na = max(1, int(np.linalg.norm(a) / CELL)); nb = max(1, int(np.linalg.norm(b) / CELL)); return grid(o, a, b, na, nb)


def lada(c2, ex, ey, yaw, z0, z1, botten=False, oppen=None):
    """Låda: centrum (x,y), halvbredder längs huvudriktningen, z0..z1. Ytor: topp + fyra sidor (+ botten)."""
    Rm = rot(yaw); ux = np.r_[Rm[:, 0], 0]; uy = np.r_[Rm[:, 1], 0]; uz = np.array([0, 0, 1.0]); c = np.r_[c2, 0]
    h = z1 - z0; delar = []
    p = lambda sx, sy, z: c + sx * ex * ux + sy * ey * uy + z * uz
    delar.append(plan(p(-1, -1, z1), 2 * ex * ux, 2 * ey * uy))
    if h == 0:
        return delar[0]
    for tecken in (-1, 1):
        if oppen != (0, tecken):
            delar.append(plan(p(tecken, -1, z0), 2 * ey * uy, h * uz))
        if oppen != (1, tecken):
            delar.append(plan(p(-1, tecken, z0), 2 * ex * ux, h * uz))
    if botten:
        delar.append(plan(p(-1, -1, z0), 2 * ex * ux, 2 * ey * uy))
    return slå_ihop(delar)


def mobeldelar(c2, ex, ey, yaw, z0, top, grupp, cam_xy):
    """Dela precis vid det observerade djupet. Ingen innervägg i skarven."""
    rm = rot(yaw)
    mitt = c2 @ rm
    radie = np.array([ex, ey])
    bort = (c2 - cam_xy) @ rm
    ax = int(np.argmax(np.abs(bort)))
    tecken = int(np.sign(bort[ax]))
    kant = None
    delar = {'skattad_ur_bild': [], 'antagen_djup': []}
    # Den robusta botten måste ligga inom 5 cm från golvplanet för att snäppas till det.
    bas = 0.0 if abs(z0) <= 0.05 and top >= 0 else z0
    skiva = max(bas, top - 0.04) if grupp == 'bord' else bas
    botten = grupp == 'bord' or bas != 0
    if tecken and 2 * radie[ax] < 0.3:
        kant = (ax, tecken)
        ny_radie = radie.copy()
        ny_radie[ax] = 0.3 - radie[ax]
        ny_mitt = mitt.copy()
        ny_mitt[ax] += tecken * (radie[ax] + ny_radie[ax])
        delar['antagen_djup'].append(lada(rm @ ny_mitt, *ny_radie, yaw, skiva, top, botten, (ax, -tecken)))
    delar['skattad_ur_bild'].append(lada(c2, ex, ey, yaw, skiva, top, botten, kant))
    lo, hi = mitt - radie, mitt + radie
    if kant:
        (hi if tecken > 0 else lo)[ax] += tecken * (0.6 - 2 * radie[ax])
    if grupp == 'bord' and skiva > bas:
        for sx in (-1, 1):
            for sy in (-1, 1):
                sida = np.array([sx, sy])
                ben = (lo + hi) / 2 + sida * np.maximum(0, (hi - lo) / 2 - 0.04)
                til = 'antagen_djup' if kant and sida[ax] == tecken else 'skattad_ur_bild'
                if kant and til == 'skattad_ur_bild':
                    ben[ax] = np.clip(ben[ax], mitt[ax] - radie[ax] + 0.025, mitt[ax] + radie[ax] - 0.025)
                delar[til].append(lada(rm @ ben, 0.025, 0.025, yaw, bas, skiva))
    return [(*slå_ihop(ytor), til) for til, ytor in delar.items() if ytor], ((lo, hi), top)


def cylinder(c2, r, z0, z1, n=28):
    th = np.linspace(0, 2 * np.pi, n + 1); rader = max(1, int((z1 - z0) / CELL) + 1); zs = np.linspace(z0, z1, rader + 1)
    V = np.array([[c2[0] + r * math.cos(t), c2[1] + r * math.sin(t), z] for z in zs for t in th])
    idx = np.arange(len(V)).reshape(len(zs), n + 1)
    t = np.concatenate([np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:]], -1).reshape(-1, 3),
                        np.stack([idx[:-1, :-1], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 3)])
    ringar = max(1, int(r / CELL)); Vt = [[c2[0], c2[1], z1]]; tt = []
    for k in range(1, ringar + 1):
        rr = r * k / ringar; Vt += [[c2[0] + rr * math.cos(a), c2[1] + rr * math.sin(a), z1] for a in th]
    Vt = np.array(Vt); bas = len(V)
    for k in range(ringar):
        for m in range(n):
            if k == 0:
                tt.append([bas, bas + 1 + m, bas + 1 + m + 1])
            else:
                a0 = bas + 1 + (k - 1) * (n + 1) + m; b0 = bas + 1 + k * (n + 1) + m
                tt += [[a0, b0, b0 + 1], [a0, b0 + 1, a0 + 1]]
    return np.vstack([V, Vt]), np.vstack([t, np.array(tt)])


def slå_ihop(delar):
    V, T, off = [], [], 0
    for v, t in delar:
        V.append(v); T.append(t + off); off += len(v)
    return np.vstack(V), np.vstack(T)


def kantkanter(T):
    e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    u_, n_ = np.unique(e, axis=0, return_counts=True)
    return u_[n_ == 1]


def skarva(Xw, Zc, mask, F=2, hopp=0.06):
    """Pröva alla pixelcentrum inom varje rastertriangel mot mask och kameradjup."""
    h, w = mask.shape
    y, x = np.meshgrid(np.arange(0, h-F, F), np.arange(0, w-F, F), indexing='ij')
    giltig = mask & np.isfinite(Xw).all(-1) & np.isfinite(Zc) & (Zc > 0)
    tackning = np.zeros_like(mask)
    trianglar = []
    for nedre in (True, False):
        offset = [(i, j) for i in range(F + 1) for j in range(F + 1) if (j <= i if nedre else i <= j)]
        ok = np.ones(y.shape, bool)
        dmin = np.full(y.shape, np.inf)
        dmax = np.zeros(y.shape)
        for i, j in offset:
            d = Zc[y+i, x+j]
            ok &= giltig[y+i, x+j]
            dmin = np.minimum(dmin, d)
            dmax = np.maximum(dmax, d)
        ok &= dmax < dmin * (1 + hopp)
        yy, xx = y[ok], x[ok]
        for i, j in offset:
            tackning[yy+i, xx+j] = True
        a = yy * w + xx
        c = a + F * (w + 1)
        horn = (a, a + F*w, c) if nedre else (a, c, a + F)
        trianglar.append(np.stack(horn, axis=-1))
    anv, index = np.unique(np.concatenate(trianglar).ravel(), return_inverse=True)
    yy, xx = np.divmod(anv, w)
    uv = np.stack([(xx + 0.5) / w, 1 - (yy + 0.5) / h], axis=-1)
    return Xw[yy, xx], index.reshape(-1, 3), uv, tackning


def pixelrutor(kam, Xw, Zc, mask):
    """En texturerad pixel på sitt observerade djup, även för isolerade mätningar."""
    y, x = np.nonzero(mask)
    h, w = mask.shape
    horn = np.array([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]])
    delta = np.column_stack([horn[:, 0] / (w * kam.fx), horn[:, 1] / (h * kam.fy), np.zeros(4)])
    V = Xw[y, x, None] + Zc[y, x, None, None] * (B(delta) @ kam.R.T)
    uv = (np.stack([x, y], axis=-1)[:, None] + 0.5 + horn) / [w, h]
    uv[..., 1] = 1 - uv[..., 1]
    T = 4 * np.arange(len(y))[:, None, None] + np.array([[0, 1, 2], [0, 2, 3]])
    return V.reshape(-1, 3), T.reshape(-1, 3), uv.reshape(-1, 2)


def robust(P, lo=3, hi=97):
    return np.percentile(P, lo, axis=0), np.percentile(P, hi, axis=0)


def bildtrianglar(kam, V, T):
    """Klipp mot närplanet före perspektivdivision. Behåll ursprungligt triangel-ID."""
    horn = B((V - kam.C) @ kam.R)[T]
    inne = horn[..., 2] >= 0.05
    hela = np.flatnonzero(inne.all(1))
    delar, index = [], []
    for i in np.flatnonzero(inne.any(1) & ~inne.all(1)):
        polygon = []
        for j, b in enumerate(horn[i]):
            a = horn[i, j-1]
            if inne[i, j-1] != inne[i, j]:
                polygon.append(a + (b - a) * ((0.05 - a[2]) / (b[2] - a[2])))
            if inne[i, j]:
                polygon.append(b)
        for j in range(1, len(polygon) - 1):
            delar.append([polygon[0], polygon[j], polygon[j+1]])
            index.append(i)
    klippta = np.concatenate([horn[hela], np.asarray(delar).reshape(-1, 3, 3)])
    z = klippta[..., 2]
    xy = (0.5 + klippta[..., :2] / z[..., None] * [kam.fx, kam.fy]) * [kam.w0, kam.h0]
    return np.r_[hela, np.asarray(index, int)], xy, z


def rasterprov(kam, V, T):
    """Besök överlappande pixelrutor i begränsade block. 1/z är linjärt i bildplanet."""
    index, xy, z = bildtrianglar(kam, V, T)
    a, b, c = xy.transpose(1, 0, 2)
    ab, ac = b - a, c - a
    det = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    storlek = np.array([kam.w0, kam.h0])
    lo = np.clip(np.floor(xy.min(1)), 0, storlek).astype(int)
    hi = np.clip(np.ceil(xy.max(1)), 0, storlek).astype(int)
    bredd, hojd = (hi - lo).T
    antal = np.where(np.abs(det) > 1e-12, bredd * hojd, 0)
    slut = antal.cumsum(dtype=np.int64)
    start = slut - antal
    det = np.where(antal, det, 1)
    # Gradienter för de tre barycentriska vikterna. En pixel har halvbredderna (0.5, 0.5).
    gb = np.column_stack([ac[:, 1], -ac[:, 0]]) / det[:, None]
    gc = np.column_stack([-ab[:, 1], ab[:, 0]]) / det[:, None]
    grad = np.stack([-gb-gc, gb, gc], axis=1)
    marginal = 0.5 * np.abs(grad).sum(2)
    # Exportens float32-positioner kan flytta en gemensam pixelkant några miljondels pixlar.
    kantfel = 2e-5 * np.abs(grad).sum(2) + 1e-12
    invz = 1 / z
    dz = 0.5 * np.abs((grad * invz[..., None]).sum(1)).sum(1)
    for k in range(0, int(antal.sum()), 65536):
        nr = np.arange(k, min(k + 65536, slut[-1]))
        i = np.searchsorted(slut, nr, side='right')
        y, x = np.divmod(nr - start[i], bredd[i])
        x += lo[i, 0]; y += lo[i, 1]
        diff = np.column_stack([x + 0.5, y + 0.5]) - a[i]
        wb = (diff * gb[i]).sum(1); wc = (diff * gc[i]).sum(1)
        vikt = np.column_stack([1 - wb - wc, wb, wc])
        # Separataxeltest: bildaxlarna täcks av omslutande rektangel, övriga av triangelns kanter.
        traff = (vikt >= -marginal[i] - kantfel[i]).all(1)
        i, vikt = i[traff], vikt[traff]
        iz = (vikt * invz[i]).sum(1)
        # Begränsa djupintervallet till både pixelrutan och triangeln, även för delvis täckta pixlar.
        nara = 1 / np.minimum(invz[i].max(1), iz + dz[i])
        fjarr = 1 / np.maximum(invz[i].min(1), iz - dz[i])
        mitt = (vikt >= -kantfel[i]).all(1)
        yield index[i], y[traff] * kam.w0 + x[traff], mitt, nara, fjarr, iz


def prova_yta(kam, V, T, Zref, ogiltig, sparrad, bak=1.12, bak_m=0.03):
    """Avgör klippning, textur och faktisk observerad täckning med samma rasterprov."""
    xn, yn, z = kam.proj(V)
    inne = (xn >= 0) & (xn <= 1) & (yn >= 0) & (yn <= 1) & (z >= 0.05)
    syn = inne[T].all(1)
    hall = np.ones(len(T), bool)
    traffad = np.zeros(len(T), bool)
    bedomd = np.zeros(Zref.size, bool)
    skymd = np.zeros_like(bedomd)
    centrum = []
    for i, p, mitt, nara, fjarr, iz in rasterprov(kam, V, T):
        zr = Zref.flat[p]
        giltig = ~ogiltig.flat[p] & np.isfinite(zr) & (zr > 0)
        grans = zr * 0.85 - 0.05
        framfor = giltig & (nara < grans)
        hall[i[framfor]] = False
        syn[i[~giltig | sparrad.flat[p] | (fjarr > zr * bak + bak_m)]] = False
        traffad[i] = True
        bed = mitt & giltig
        bedomd[p[bed]] = True
        skymd[p[bed & (iz * grans > 1)]] = True
        centrum.append((i[bed], p[bed]))
    syn &= hall & traffad
    tackning = np.zeros(Zref.size, bool)
    for i, p in centrum:
        tackning[p[syn[i]]] = True
    n = int(bedomd.sum())
    return hall, syn, tackning.reshape(Zref.shape), skymd.sum() / max(1, n), n


def samma_instans(a, b):
    return (a & b).sum() > 0.7 * (a | b).sum()


def las_sam(fil, sid, ruta, bild_px, rutnat, aldre_mittruta):
    """Nya filer identifierar källbilden. Äldre export skrev exakt halva formatet och metadatas mittruta."""
    h, w = rutnat
    with np.load(fil, allow_pickle=False) as z:
        n, mh, mw = map(int, z['form'])
        W, H = bild_px
        if {'tagning', 'ruta', 'bild_px'}.intersection(z.files):
            if (str(z['tagning']) != sid or int(z['ruta']) != ruta or tuple(z['bild_px']) != (W, H)):
                raise ValueError('annan tagning, ruta eller källupplösning')
        elif ruta != aldre_mittruta or (mw, mh) != (W // 2, H // 2):
            raise ValueError('äldre SAM-fil stämmer inte med tagningens mittruta och halvupplösning')
        if min(mh, mw) <= 0 or any(abs(x*H - y*W) >= max(W, H) for x, y in [(mw, mh), (w, h)]):
            raise ValueError('maskens eller rutnätets bildformat avviker från källan')
        packat, etik, poang = z['masker'], json.loads(str(z['etiketter'])), z['poang']
        if (packat.shape != (n, mh, (mw+7)//8) or packat.dtype != np.uint8 or
                len(etik) != n or poang.shape != (n,) or not np.isfinite(poang).all()):
            raise ValueError('inkonsekvent maskform, etiketter eller poäng')
        masker = np.unpackbits(packat, count=mw, axis=-1)
    beh = []
    for i in np.argsort(-poang, kind='stable'):
        mask = masker[i]
        if (mh, mw) != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST_EXACT)
        mask = mask.astype(bool)
        grupp = MOBEL.get(etik[i], etik[i])
        if mask.any() and not any(MOBEL.get(e, e) == grupp and samma_instans(mask, m) for e, m, _ in beh):
            beh.append((etik[i], mask, float(poang[i])))
    return beh


def main(nyckel):
    out = HERE / 'ut' / nyckel; ind = out / 'struktur_in'; ut = out / 'struktur'; ut.mkdir(exist_ok=True)
    nat = json.loads((out / 'nat.json').read_text(encoding='utf-8'))['tagningar']
    meta = json.loads((out / 'obs_gpu.json').read_text(encoding='utf-8')); W0, H0 = meta['bild_px']
    mittrutor = {t['id']: t['nyckelrutor'][len(t['nyckelrutor']) // 2] for t in meta['tagningar']}
    video = ROOT / 'data/format/kontroll/klipp' / (meta['klipp'] + '.mp4')
    manifest = {}; rapport = {}
    for fil in sorted(ind.glob('s*.npz'), key=lambda p: int(p.stem[1:])):
        sid = fil.stem; z = np.load(fil, allow_pickle=False)
        Xw, Zc, M, I, person, ovl = z['Xw'], z['Zc'], z['M'], z['I'], z['person'], z['overlagg']
        segs = {int(k): v for k, v in json.loads(str(z['segs'])).items()}; namn = {int(k): v for k, v in json.loads(str(z['namn'])).items()}
        gk = {int(k): v for k, v in json.loads(str(z['gk'])).items()}; u = int(z['u'])
        h, w = Zc.shape; kam = Kamera(z['C'], z['R'], z['f'], w, h)
        cap = cv2.VideoCapture(str(video)); cap.set(cv2.CAP_PROP_POS_FRAMES, u); ok, bild = cap.read(); cap.release()
        if not ok or bild.shape[:2] != (H0, W0):
            raise ValueError(f'{sid}: kunde inte läsa ruta {u} i angiven källupplösning')
        bild = cv2.resize(bild, (w * 2, h * 2), interpolation=cv2.INTER_AREA)
        # texturbild: original; bakom personen rumshjärnans hypotes om den släppts, annars ogiltigt
        ogiltig = cv2.dilate((person | ovl[:h, :w]).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
        Zref = np.where(M & (Zc > 0), Zc, np.nan); gen = 'gen_Z' in z.files
        gpng = HERE / 'ut' / 'rumshjarna' / nyckel / 'fyllnad' / f'{sid}_v2.png'
        if gen and gpng.is_file():
            g = cv2.resize(cv2.imread(str(gpng)), (w * 2, h * 2), interpolation=cv2.INTER_AREA)
            gm = cv2.resize((ogiltig & z['gen_M'][:h, :w]).astype(np.uint8), (w * 2, h * 2), interpolation=cv2.INTER_NEAREST).astype(bool)
            bild[gm] = g[gm]; Zref = np.where(ogiltig & z['gen_M'][:h, :w], z['gen_Z'][:h, :w], Zref); ogiltig = ogiltig & ~z['gen_M'][:h, :w]
        cv2.imwrite(str(ut / f'{sid}.png'), bild, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        Gm = np.full(I.shape, '', dtype=object)
        for i_, l_ in segs.items():
            Gm[I == i_] = gk.get(l_, '')
        ok_ = M & np.isfinite(Xw).all(-1) & np.isfinite(Zc) & (Zc > 0) & ~person
        observerad = ok_ & ~ovl[:h, :w]
        # normaler ur världspunkterna (för huvudriktningen)
        dx = np.gradient(Xw, axis=1); dy = np.gradient(Xw, axis=0); N = np.cross(dx, dy); N /= np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-9)
        yaw = manhattan_yaw(N, ok_ & np.isin(Gm, ['vagg', 'skap', 'bank', 'spis']))
        Rm = rot(yaw)
        former = []  # (namn, grupp, V, T, tilltro, farg-källa-mask)

        def farg_av(mask):
            if mask.sum() < 5:
                return '#8a8f94'
            mm = cv2.resize(mask.astype(np.uint8), (w * 2, h * 2), interpolation=cv2.INTER_NEAREST).astype(bool)
            c = np.median(bild[mm], axis=0).astype(int); return '#%02x%02x%02x' % (c[2], c[1], c[0])

        rum_p = Xw[ok_ & (Gm != '')]
        tak_z = None
        tm = ok_ & (Gm == 'tak')
        if tm.sum() > 200:
            tak_z = float(np.median(Xw[tm][:, 2]))
        ytor = []  # stödytor: (polygon i huvudriktningens ram, z)
        # golv
        if len(rum_p) >= 100:
            lo, hi = robust((rum_p[:, :2] @ Rm), 1, 99); lo -= 0.3; hi += 0.3
            o = np.r_[Rm @ lo, 0.0]; a = np.r_[Rm @ np.array([hi[0] - lo[0], 0]), 0]; b = np.r_[Rm @ np.array([0, hi[1] - lo[1]]), 0]
            former.append(('golv', 'golv', *plan(o, a, b), 'skattad_ur_bild', ok_ & (Gm == 'golv'))); ytor.append(((lo, hi), 0.0))
            if tak_z is not None:
                former.append(('tak', 'tak', *plan(np.r_[Rm @ lo, tak_z], a, b), 'skattad_ur_bild', tm))
        # väggar: RANSAC på vertikala plan
        vm = ok_ & (Gm == 'vagg'); P = Xw[vm]; rest = np.ones(len(P), bool); rng = np.random.default_rng(0); vaggar = 0
        while rest.sum() > max(300, 0.04 * len(P)) and vaggar < 5:
            Q = P[rest]; bast = None
            for _ in range(300):
                i0, i1 = rng.integers(0, len(Q), 2); d = Q[i1, :2] - Q[i0, :2]
                if np.linalg.norm(d) < 0.2:
                    continue
                n2 = np.array([-d[1], d[0]]) / np.linalg.norm(d)
                for ax in (Rm[:, 0], Rm[:, 1]):  # lås till huvudriktningen om nära
                    if abs(n2 @ ax) > math.cos(math.radians(12)):
                        n2 = ax * np.sign(n2 @ ax)
                dist = np.abs((Q[:, :2] - Q[i0, :2]) @ n2); inl = dist < 0.04
                if bast is None or inl.sum() > bast[0]:
                    bast = (int(inl.sum()), n2, float(Q[i0, :2] @ n2))
            if bast is None or bast[0] < max(300, 0.04 * len(P)):
                break
            _, n2, dd = bast; idx = np.where(rest)[0]; inl = np.abs(P[idx, :2] @ n2 - dd) < 0.06
            Pi = P[idx[inl]]; t2 = np.array([-n2[1], n2[0]]); tt = Pi[:, :2] @ t2; t0, t1 = np.percentile(tt, [2, 98])
            # höjd: bara till golv/tak när observationerna når dit (annars är det en skiva, t.ex. glasdörr eller skärm)
            zl, zh = np.percentile(Pi[:, 2], [2, 98]); zbot = 0.0 if zl < 0.5 else float(zl)
            ztop = tak_z if tak_z is not None and abs(zh - tak_z) < 0.5 and zh > 1.6 else float(zh)
            o = np.r_[dd * n2 + t0 * t2, zbot]
            former.append((f'vägg {vaggar + 1}', 'vagg', *plan(o, np.r_[(t1 - t0) * t2, 0], np.array([0, 0, ztop - zbot])), 'skattad_ur_bild', vm))
            rest[idx[inl]] = False; vaggar += 1
        # SAM 3 (föremål/2): öppen vokabulär för möbler och föremål, om körd
        sfil = out / 'foremal_sam3' / f'{sid}.npz'; sam = []; sam_fel = None
        if sfil.is_file():
            try:
                sam = las_sam(sfil, sid, u, (W0, H0), (h, w), mittrutor.get(sid))
            except (ValueError, KeyError) as e:
                sam_fel = str(e)
        sam_mobel = [(e, MOBEL[e], m) for e, m, _ in sam if e in MOBEL]
        sam_obj = [(e, m) for e, m, _ in sam if e not in MOBEL]
        lt_bitar = nat.get(sid, {}).get('bitar', []) if not sam else []
        lt_id = {b['instans'] for b in lt_bitar if b.get('grupp') not in (*RUMSGRUPPER, 'bakom_person') and b['instans'] >= 0}
        obj_id = [i for i, l in segs.items() if i in lt_id or gk.get(l) in ('mat', 'karl', 'foremal') or
                  set(namn.get(l, '').lower().replace(',', ' ').split()).intersection(FORMAL)]
        objpix = np.isin(I, obj_id)
        for _, m in sam_obj:
            objpix |= m
        # rumstextur: föremålens pixlar ifyllda ur omgivningen (prov 12: "golv och bord tar slut under föremålen").
        # Rumsytor under föremål blir hela och ser ut som sin omgivning; föremålen själva behåller originalets pixlar.
        om_u = cv2.resize(cv2.dilate(objpix.astype(np.uint8), np.ones((5, 5), np.uint8)), (bild.shape[1], bild.shape[0]), interpolation=cv2.INTER_NEAREST)
        rumbild = cv2.inpaint(bild, om_u * 255, 7, cv2.INPAINT_TELEA) if om_u.any() else bild
        cv2.imwrite(str(ut / f'{sid}_rum.png'), rumbild, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        # möbler och föremål per instans (OneFormer, plus SAM 3-möbler som egna instanser)
        cam_xy = kam.C[:2]
        poster = [(i_, gk.get(l_, ''), namn.get(l_, '?').split(',')[0], ok_ & (I == i_)) for i_, l_ in segs.items()]
        if sam_mobel:
            poster = [p for p in poster if not any(p[1] == g and samma_instans(p[3], ok_ & m) for _, g, m in sam_mobel)]
            poster += [(f'sam{k_}', g_, e_, ok_ & m_) for k_, (e_, g_, m_) in enumerate(sam_mobel)]
        for i_, g, nm, mi in poster:
            if g in ('bank', 'bord', 'spis', 'skap', 'stol'):
                mi = mi & ~objpix  # möbler mäts bara på pixlar som inget föremål gör anspråk på (prov 6: bordsskiva över tallriken)
            if mi.sum() < 40:
                continue
            Pi = Xw[mi]; q = Pi[:, :2] @ Rm; (q0, q1) = robust(q); (z0_, z1_) = np.percentile(Pi[:, 2], [3, 97])
            if g in ('bank', 'bord'):  # skivans höjd ur ytor som pekar uppåt, om de finns
                upp = mi & (np.abs(N[..., 2]) > 0.8)  # vågrät yta (normalens tecken beror på bildaxlarna)
                if upp.sum() > 30:
                    z1_ = float(np.percentile(Xw[upp][:, 2], 60))
            c2 = Rm @ ((q0 + q1) / 2); ex, ey = max(0.03, (q1 - q0)[0] / 2), max(0.03, (q1 - q0)[1] / 2)
            yaw_i = yaw
            if g in MOBELGRUPPER and len(Pi) >= 40:
                # egen orientering (minsta omslutande rektangel) när den är klart tätare än huvudriktningens låda.
                # Prov 14: en snett stående möbel blev en för stor låda vars framskjutande delar skars till remsor.
                xy = Pi[:, :2]; l_, h_ = np.percentile(xy, [3, 97], axis=0); sel = np.all((xy >= l_) & (xy <= h_), 1)
                if sel.sum() >= 20:
                    (cx_, cy_), (rw_, rh_), ang_ = cv2.minAreaRect(xy[sel].astype(np.float32))
                    if rw_ * rh_ < 0.8 * (2 * ex) * (2 * ey) and min(rw_, rh_) > 0.02:
                        yaw_i = math.radians(ang_); c2 = np.array([cx_, cy_]); ex, ey = max(0.03, rw_ / 2), max(0.03, rh_ / 2)
            if g in MOBELGRUPPER:
                delar, stod = mobeldelar(c2, ex, ey, yaw_i, float(z0_), float(z1_), g, cam_xy)
                if yaw_i != yaw:  # stödytan i huvudriktningens ram (stödgrafen jämför där)
                    (lo_, hi_), top_ = stod; rmi = rot(yaw_i)
                    hr = np.array([[x_, y_] for x_ in (lo_[0], hi_[0]) for y_ in (lo_[1], hi_[1])]) @ rmi.T @ Rm
                    stod = ((hr.min(0), hr.max(0)), top_)
                former.extend((nm, g, V, T, til, mi) for V, T, til in delar)
                ytor.append(stod)
            elif os.environ.get('STRUKTUR_FOREMAL') == '1' and (g in ('karl', 'mat') or any(k_ in nm for k_ in FORMAL)):
                former.append(('_obj', (nm, g, c2, ex, ey, float(z0_), float(z1_)), None, None, None, mi))
        # föremål på stödytor (stödgraf: högsta yta under föremålet som täcker dess mitt)
        slut = []
        for f_ in former:
            if f_[0] != '_obj':
                slut.append(f_); continue
            nm, g, c2, ex, ey, z0_, z1_ = f_[1]; mi = f_[5]; qc = c2 @ Rm
            stod = [zz for (a_, b_), zz in ytor if np.all(qc >= a_ - 0.05) and np.all(qc <= b_ + 0.05) and zz <= z0_ + 0.12]
            bas = max(stod) if stod else z0_
            r = max(0.03, min(0.35, max(ex, ey)))
            hgt = max(0.015, min(0.4, z1_ - z0_)) if not any(k_ in nm for k_ in ('plate', 'tray')) else 0.02
            V, T = cylinder(c2, r, bas, bas + hgt) if any(k_ in nm for k_ in RUNDA) else lada(c2, ex, ey, yaw, bas, bas + hgt)
            slut.append((nm, g or 'foremal', V, T, 'skattad_ur_bild' if stod else 'utan_stod', mi))
        bitar = []; blob = bytearray(); tex = 0; tot = 0
        forkastade = []; accepterade = []; forklarad = np.zeros((h, w), bool)

        def lagg(nm, g, V, T, UV, textur, tilltro, farg):
            if not len(T):
                return
            bit = {'etikett': nm, 'grupp': g, 'instans': len(bitar), 'tilltro': tilltro, 'textur': textur,
                   'farg': farg, 'nv': len(V), 'ni': int(T.size)}
            for nyck, arr in (('pos', V.astype(np.float32)), ('uv', UV.astype(np.float32)), ('ind', T.astype(np.uint32))):
                bit[nyck] = [len(blob), arr.nbytes]
                blob.extend(arr.tobytes())
            bitar.append(bit)

        for nm, g, V, T, til, mi in slut:
            sparrad = np.zeros_like(objpix) if g in RUMSGRUPPER else ~mi  # rumsytor texturerar genom föremål ur rumstexturen
            # möbellådor är grova approximationer: generösare texturkrav bakåt (prov 7: spisen nästan helt otexturerad)
            tol = (1.25, 0.08) if g in ('bank', 'bord', 'spis', 'skap', 'stol') else (1.12, 0.03)
            hall, syn, tackning, fr, n = prova_yta(kam, V, T, Zref, ogiltig, sparrad, *tol)
            if g in ('vagg', 'tak') and n > 20 and fr > 0.10:
                forkastade.append((nm, round(fr, 2)))
                continue
            if not hall.any():
                continue
            accepterade.append((nm, g, til))
            if til == 'antagen_djup':
                syn[:] = False
            else:
                forklarad |= tackning
            tot += int(hall.sum()); tex += int(syn.sum())
            xn, yn, _ = kam.proj(V)
            uv = np.column_stack([np.nan_to_num(xn), 1 - np.nan_to_num(yn)])
            farg = farg_av(mi)
            styp = 'struktur_rum' if g in RUMSGRUPPER else 'struktur'
            genom = np.zeros(len(T), bool)
            if g in RUMSGRUPPER and objpix.any():
                # rumsyta som bara syns genom ett föremål: ifylld textur är en hypotes -> antagen (dold i originalkameran;
                # prov 13: annars lade sig bänkskivan över föremålen framifrån, originalkameran Lt 40 / Ls 6)
                po = np.clip((np.nan_to_num(yn) * h).astype(int), 0, h - 1) * w + np.clip((np.nan_to_num(xn) * w).astype(int), 0, w - 1)
                genom = objpix.ravel()[po][T].any(1)
            for val, typ, tro in ((syn & ~genom, styp, til), (syn & genom, styp, 'antagen'),
                                  (hall & ~syn, 'farg', til if til == 'antagen_djup' else 'antagen')):
                if val.any():
                    anv, ix = np.unique(T[val].ravel(), return_inverse=True)
                    etik = f'{nm} ({"syns" if typ == "struktur" else "ej sedd"})'
                    lagg(etik, g, V[anv], ix.reshape(-1, 3), uv[anv], typ, tro, farg)

        def kjol(nm, V, T, farg, utan_stod=False):
            cq = np.median(V[:, :2], axis=0) @ Rm; zb = float(np.percentile(V[:, 2], 5))
            kand = [zz for (a, b), zz in ytor if np.all(cq >= a - 0.03) and np.all(cq <= b + 0.03)
                    and zb - 0.15 <= zz <= zb + 0.25]
            if not kand and not utan_stod:
                return
            bas = max(kand) if kand else V[:, 2].min()
            kant = kantkanter(T)
            over = V[kant]
            # En separat kontaktyta kan gå både upp och ned till ett observerat stöd.
            kant = kant[np.any(np.abs(over[..., 2] - bas) > 0.005, axis=1)]
            if len(kant):
                a, b = V[kant[:, 0]], V[kant[:, 1]]
                c, d = b.copy(), a.copy()
                c[:, 2] = d[:, 2] = bas
                Vk = np.stack([a, b, c, d], axis=1).reshape(-1, 3)
                Tk = 4 * np.arange(len(kant))[:, None, None] + np.array([[0, 1, 2], [0, 2, 3]])
                lagg(f'{nm} (kjol)', 'foremal', Vk, Tk.reshape(-1, 3), np.zeros((len(Vk), 2)), 'farg', 'antagen', farg)

        lt_n = 0; n_obj = 0
        agd = np.zeros((h, w), bool)
        for e, m in sorted(sam_obj, key=lambda post: post[1].sum()):
            mm = m & observerad & ~agd
            if mm.sum() < 20:
                continue
            V, T, uv, tackning = skarva(Xw, Zc, mm, hopp=0.12)  # inom en SAM 3-mask: generösare djupsprång (prov 14: revor i tallrikskanter)
            if len(T):
                farg = farg_av(tackning)
                lagg(f'{e} (SAM 3)', 'foremal', V, T, uv, 'struktur', 'skattad_ur_bild', farg)
                agd |= tackning
                n_obj += 1
                kjol(e, V, T, farg, utan_stod=True)

        # Behåll Lt-bitens ursprungliga positioner, index och bildregistrering.
        lt_fil = out / 'nat' / f'{sid}.bin'
        if lt_bitar and lt_fil.is_file():
            nb = lt_fil.read_bytes()
            for b0 in lt_bitar:
                if b0.get('grupp') in (*RUMSGRUPPER, 'bakom_person') or b0.get('tilltro') in ('antagen', 'genererad'):
                    continue
                bit = dict(b0, instans=len(bitar), kalla='Lt')
                for nyck in ('pos', 'uv', 'ind'):
                    off, antal = b0[nyck]
                    bit[nyck] = [len(blob), antal]
                    blob.extend(nb[off:off+antal])
                bitar.append(bit); lt_n += 1
                off, antal = b0['pos']
                V = np.frombuffer(nb, np.float32, count=antal//4, offset=off).reshape(-1, 3)
                off, antal = b0['ind']
                T = np.frombuffer(nb, np.uint32, count=antal//4, offset=off).reshape(-1, 3)
                for _, p, mitt, _, _, iz in rasterprov(kam, V, T):
                    # Endast Lt-trianglarnas inre på observationens djup förklarar originalpixlar.
                    zr = Zc.flat[p]
                    stammer = mitt & (iz * (zr * 0.85 - 0.05) <= 1) & (iz * (zr * 1.12 + 0.03) >= 1)
                    forklarad.flat[p[stammer]] = True
                if len(T) and np.ptp(V[:, :2], axis=0).max() < 0.8:
                    kjol(b0['etikett'], V, T, bit.get('farg', '#8a8f94'))

        restmask = observerad & ~forklarad & ~agd
        V, T, uv, tackning = skarva(Xw, Zc, restmask)
        # prov 7 (Neon): "punktmolnsdamm". Små lösa komponenter och enstaka pixlar fyller bara originalkamerans bild;
        # de visas bara där (bara_0), inte i fri kamera. Komponenter på minst 40 trianglar är rum/föremål och visas alltid.
        if len(T):
            from scipy.sparse import coo_matrix
            from scipy.sparse.csgraph import connected_components
            e_ = np.concatenate([T[:, [0, 1]], T[:, [1, 2]]]); G_ = coo_matrix((np.ones(len(e_)), (e_[:, 0], e_[:, 1])), shape=(len(V), len(V)))
            _, lab = connected_components(G_, directed=False); tl = lab[T[:, 0]]; storlek = np.bincount(tl, minlength=lab.max() + 1)
            stor = storlek[tl] >= 40
            lagg('rest (observerad)', 'rest', V, T[stor], uv, 'struktur', 'skattad_ur_bild', '#8a8f94')
            lagg('rest (små delar, bara originalkameran)', 'rest', V, T[~stor], uv, 'struktur', 'bara_0', '#8a8f94')
        V, T, uv = pixelrutor(kam, Xw, Zc, restmask & ~tackning)
        lagg('rest (enstaka pixlar, bara originalkameran)', 'rest', V, T, uv, 'struktur', 'bara_0', '#8a8f94')
        # fokus för fri kamera: motivet (föremål och personer), annars kamerans mittaxel på medianddjup i bildens mitt.
        # Orbit kring alla bitars mittpunkt svängde ut närliggande bord ur bild (prov 9: "bordet med mat försvinner").
        ok_f = M & np.isfinite(Xw).all(-1)
        mot = ok_f & (objpix | person[:h, :w])
        if mot.sum() > 200:
            fokus = np.median(Xw[mot], axis=0)
        else:
            mitt = np.zeros_like(ok_f); mitt[h // 4: 3 * h // 4, w // 4: 3 * w // 4] = True
            zc_ = Zc[ok_f & mitt]; zm = float(np.median(zc_)) if len(zc_) else 2.0
            fokus = kam.C + kam.R @ B(np.array([0.0, 0.0, zm]))
        fokus = [round(float(v), 4) for v in fokus]
        (ut / f'{sid}.bin').write_bytes(blob)
        n_ = nat.get(sid, {})
        manifest[sid] = {'fil': f'{sid}.bin', 'ruta': u, 'bitar': bitar, 'transform': n_.get('transform'), 'rum': n_.get('rum', f'egen_{sid}'), 'rorlig': n_.get('rorlig'),
                         'kamera': {'C': kam.C.tolist(), 'R': kam.R.tolist(), 'f': [float(kam.fx), float(kam.fy)]},
                         'textur_bild': f'{sid}.png', 'fokus': fokus}
        rapport[sid] = {'former': len(accepterade), 'vaggar': sum(g == 'vagg' for _, g, _ in accepterade), 'tak': tak_z is not None, 'yaw_grader': round(math.degrees(yaw), 1),
                        'texturerade_trianglar': round(tex / max(1, tot), 3), 'utan_stod': sum(til == 'utan_stod' for _, _, til in accepterade), 'forkastade': forkastade, 'lt_bitar': lt_n, 'sam3_foremal': n_obj, 'sam3_mobler': len(sam_mobel), 'sam3_avvisad': sam_fel}
    (out / 'struktur.json').write_text(json.dumps({'schema': 'lokalitet-struktur/1', 'koordinater': 'samma världsram som nat.json', 'tagningar': manifest},
                                                  ensure_ascii=False), encoding='utf-8')
    (out / 'struktur_rapport.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')
    print(nyckel, json.dumps(rapport, ensure_ascii=False)[:600])


if __name__ == '__main__':
    for k in sys.argv[1:]:
        main(k)
