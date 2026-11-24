"""struktur/1: rummet som primitiver i stället för pixelskärvor (jämförelsevariant 'Ls' bredvid 'Lt').

Facit 21 nov (Gemini 38 + Codex hold-out 16): rum och objekt faller sönder i skärvor så fort kameran vrids. Här byggs
samma observationer (lokalitet.py -> ut/<k>/struktur_in/<sid>.npz) om till hela former:
- golv: planet z=0 (L4), rektangel längs rummets huvudriktning över allt rum som syns
- väggar: vertikala plan ur vägg-/dörr-/fönsterpixlar (RANSAC, riktning låst till huvudriktningen inom 12°), från golv till tak
- tak: horisontellt plan om taket syns
- möbler (bänk, bord, spis, skåp): lådor längs huvudriktningen; ovansida = robust topp, botten = golvet.
  Syns bara framsidan sträcks lådan 0,6 m bort från kameran (antaget, märkt)
- kärl och mat: cylindrar (tallrik låg, skål/kopp högre) som ställs på högsta stödyta under sig (stödgraf)
Textur: originalets mittruta projiceras på varje hörn som syns: inne i bilden, inte person/överlagrad text och
djupet stämmer med observationen (±8 %). Bakom personen används rumshjärnans hypotes om grind 1b släppt den.
Resten får ytans egen medelfärg och märks antagen.
Inga klippkonstanter. usage: python struktur.py <nyckel>
"""
from __future__ import annotations
import json, math, os, sys
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
CELL = 0.08  # m, rutnät på plana ytor (perspektivriktig textur per hörn)
RUNDA = ('plate', 'bowl', 'cup', 'glass', 'bottle', 'pot', 'pan', 'food', 'mug', 'vase', 'jar', 'can')
FORMAL = RUNDA + ('tray', 'box', 'basket', 'bag')


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


def lada(c2, ex, ey, yaw, z0, z1, botten=False):
    """Låda: centrum (x,y), halvbredder längs huvudriktningen, z0..z1. Ytor: topp + fyra sidor (+ botten)."""
    Rm = rot(yaw); ux = np.r_[Rm[:, 0], 0]; uy = np.r_[Rm[:, 1], 0]; uz = np.array([0, 0, 1.0]); c = np.r_[c2, 0]
    h = z1 - z0; delar = []
    p = lambda sx, sy, z: c + sx * ex * ux + sy * ey * uy + z * uz
    delar.append(plan(p(-1, -1, z1), 2 * ex * ux, 2 * ey * uy))
    delar.append(plan(p(-1, -1, z0), 2 * ex * ux, h * uz)); delar.append(plan(p(-1, 1, z0), 2 * ex * ux, h * uz))
    delar.append(plan(p(-1, -1, z0), 2 * ey * uy, h * uz)); delar.append(plan(p(1, -1, z0), 2 * ey * uy, h * uz))
    if botten:
        delar.append(plan(p(-1, -1, z0), 2 * ex * ux, 2 * ey * uy))
    return slå_ihop(delar)


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


def skarva(Xw, mask, F=2, hopp=0.06):
    """Observerad yta som nät (originalets djup och pixlar). Returnerar V, T, UV och kantkanter (för kjol)."""
    h, w = mask.shape; ii, jj = np.meshgrid(np.arange(0, h, F), np.arange(0, w, F), indexing='ij')
    V = Xw[::F, ::F]; ok = mask[::F, ::F] & np.isfinite(V).all(-1); hh, ww = ok.shape
    idx = -np.ones((hh, ww), int); idx[ok] = np.arange(ok.sum())
    d = np.linalg.norm(V, axis=-1)
    T = []
    for (a0, a1), (b0, b1), (c0, c1) in (((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 1), (0, 1))):
        A = idx[a0:hh - 1 + a0, a1:ww - 1 + a1]; B_ = idx[b0:hh - 1 + b0, b1:ww - 1 + b1]; C_ = idx[c0:hh - 1 + c0, c1:ww - 1 + c1]
        dA = d[a0:hh - 1 + a0, a1:ww - 1 + a1]; dB = d[b0:hh - 1 + b0, b1:ww - 1 + b1]; dC = d[c0:hh - 1 + c0, c1:ww - 1 + c1]
        dmax = np.maximum(np.maximum(dA, dB), dC); dmin = np.minimum(np.minimum(dA, dB), dC)
        okt = (A >= 0) & (B_ >= 0) & (C_ >= 0) & (dmax < dmin * (1 + hopp))
        T.append(np.stack([A[okt], B_[okt], C_[okt]], -1))
    T = np.concatenate(T) if T else np.zeros((0, 3), int)
    Vp = V[ok]; UV = np.stack([(jj[ok] + 0.5) / w, 1 - (ii[ok] + 0.5) / h], -1).astype(np.float32)
    if not len(T):
        return Vp, T, UV, np.zeros((0, 2), int)
    e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    u_, n_ = np.unique(e, axis=0, return_counts=True)
    return Vp, T, UV, u_[n_ == 1]


def robust(P, lo=3, hi=97):
    return np.percentile(P, lo, axis=0), np.percentile(P, hi, axis=0)


def main(nyckel):
    out = HERE / 'ut' / nyckel; ind = out / 'struktur_in'; ut = out / 'struktur'; ut.mkdir(exist_ok=True)
    nat = json.loads((out / 'nat.json').read_text(encoding='utf-8'))['tagningar']
    meta = json.loads((out / 'obs_gpu.json').read_text(encoding='utf-8')); W0, H0 = meta['bild_px']
    video = ROOT / 'data/format/kontroll/klipp' / (meta['klipp'] + '.mp4')
    manifest = {}; rapport = {}
    for fil in sorted(ind.glob('s*.npz'), key=lambda p: int(p.stem[1:])):
        sid = fil.stem; z = np.load(fil, allow_pickle=False)
        Xw, Zc, M, I, person, ovl = z['Xw'], z['Zc'], z['M'], z['I'], z['person'], z['overlagg']
        segs = {int(k): v for k, v in json.loads(str(z['segs'])).items()}; namn = {int(k): v for k, v in json.loads(str(z['namn'])).items()}
        gk = {int(k): v for k, v in json.loads(str(z['gk'])).items()}; u = int(z['u'])
        h, w = Zc.shape; kam = Kamera(z['C'], z['R'], z['f'], w, h)
        cap = cv2.VideoCapture(str(video)); cap.set(cv2.CAP_PROP_POS_FRAMES, u); ok, bild = cap.read(); cap.release()
        bild = cv2.resize(bild, (w * 2, h * 2), interpolation=cv2.INTER_AREA)
        # texturbild: original; bakom personen rumshjärnans hypotes om den släppts, annars ogiltigt
        ogiltig = cv2.dilate((person | ovl[:h, :w]).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
        Zref = Zc.copy(); gen = 'gen_Z' in z.files
        gpng = HERE / 'ut' / 'rumshjarna' / nyckel / 'fyllnad' / f'{sid}_v2.png'
        if gen and gpng.is_file():
            g = cv2.resize(cv2.imread(str(gpng)), (w * 2, h * 2), interpolation=cv2.INTER_AREA)
            gm = cv2.resize((ogiltig & z['gen_M'][:h, :w]).astype(np.uint8), (w * 2, h * 2), interpolation=cv2.INTER_NEAREST).astype(bool)
            bild[gm] = g[gm]; Zref = np.where(ogiltig & z['gen_M'][:h, :w], z['gen_Z'][:h, :w], Zref); ogiltig = ogiltig & ~z['gen_M'][:h, :w]
        cv2.imwrite(str(ut / f'{sid}.png'), bild, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        Gm = np.full(I.shape, '', dtype=object)
        for i_, l_ in segs.items():
            Gm[I == i_] = gk.get(l_, '')
        ok_ = M & np.isfinite(Xw).all(-1) & ~person
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
        if len(rum_p) < 100:
            continue
        lo, hi = robust((rum_p[:, :2] @ Rm), 1, 99); lo -= 0.3; hi += 0.3
        tak_z = None
        tm = ok_ & (Gm == 'tak')
        if tm.sum() > 200:
            tak_z = float(np.median(Xw[tm][:, 2]))
        ytor = []  # stödytor: (polygon i huvudriktningens ram, z)
        # golv
        o = np.r_[Rm @ lo, 0.0]; a = np.r_[Rm @ np.array([hi[0] - lo[0], 0]), 0]; b = np.r_[Rm @ np.array([0, hi[1] - lo[1]]), 0]
        former.append(('golv', 'golv', *plan(o, a, b), 'skattad_ur_bild', ok_ & (Gm == 'golv'))); ytor.append(((lo, hi), 0.0))
        if tak_z:
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
            ztop = (tak_z if tak_z else max(2.4, float(zh))) if (tak_z is None or zh > tak_z - 0.5) and zh > 1.6 else float(zh)
            o = np.r_[dd * n2 + t0 * t2, zbot]
            former.append((f'vägg {vaggar + 1}', 'vagg', *plan(o, np.r_[(t1 - t0) * t2, 0], np.array([0, 0, ztop - zbot])), 'skattad_ur_bild', vm))
            rest[idx[inl]] = False; vaggar += 1
        # SAM 3 (föremål/2): öppen vokabulär för möbler och föremål, om körd
        sfil = out / 'foremal_sam3' / f'{sid}.npz'; sam = []
        if sfil.is_file():
            zs = np.load(sfil); fo = tuple(int(x) for x in zs['form'])
            if fo[0]:
                MM = np.unpackbits(zs['masker'], axis=-1)[..., :fo[2]].astype(bool)[:, :h, :w]; ET = json.loads(str(zs['etiketter'])); PO = zs['poang']
                ordn = np.argsort(-PO); beh_ = []
                for i in ordn:  # samma begrepp, nästan samma mask: behåll den säkraste
                    if any(ET[j] == ET[i] and (MM[i] & MM[j]).sum() > 0.7 * min(MM[i].sum(), MM[j].sum()) for j in beh_):
                        continue
                    beh_.append(i)
                sam = [(ET[i], MM[i], float(PO[i])) for i in beh_]
        MOBEL = {'table': 'bord', 'counter': 'bank', 'chair': 'stol', 'stool': 'stol', 'bench': 'stol'}
        sam_mobel = [(e, MOBEL[e], m) for e, m, _ in sam if e in MOBEL]
        sam_obj = [(e, m) for e, m, _ in sam if e not in MOBEL]
        tackt = np.zeros((h, w), bool)
        for _, _, m in sam_mobel:
            tackt |= m
        objpix = np.zeros((h, w), bool)  # föremålens pixlar: får aldrig bli textur på rumsytor (blint prov 4: dubbla kärl i 0°)
        for _, m in sam_obj:
            objpix |= m
        # möbler och föremål per instans (OneFormer, plus SAM 3-möbler som egna instanser)
        cam_xy = kam.C[:2]
        poster = [(i_, gk.get(l_, ''), namn.get(l_, '?').split(',')[0], ok_ & (I == i_)) for i_, l_ in segs.items()]
        if sam_mobel:  # OneFormer-möbel som till största delen täcks av en SAM 3-möbel ersätts av den
            poster = [p_ for p_ in poster if not (p_[1] in ('bank', 'bord') and (p_[3] & tackt).sum() > 0.5 * max(1, p_[3].sum()))]
            poster += [(f'sam{k_}', g_, e_, ok_ & m_) for k_, (e_, g_, m_) in enumerate(sam_mobel)]
        for i_, g, nm, mi in poster:
            if mi.sum() < 40:
                continue
            Pi = Xw[mi]; q = Pi[:, :2] @ Rm; (q0, q1) = robust(q); (z0_, z1_) = np.percentile(Pi[:, 2], [3, 97])
            c2 = Rm @ ((q0 + q1) / 2); ex, ey = max(0.03, (q1 - q0)[0] / 2), max(0.03, (q1 - q0)[1] / 2)
            if g in ('bank', 'bord', 'spis', 'skap', 'stol'):
                til = 'skattad_ur_bild'
                bort = (c2 - cam_xy) @ Rm  # sträck bort från kameran om bara framsidan syns
                if 2 * ex < 0.3 and abs(bort[0]) > abs(bort[1]):
                    c2 = c2 + Rm[:, 0] * np.sign(bort[0]) * (0.3 - ex); ex = 0.3; til = 'antagen_djup'
                if 2 * ey < 0.3 and abs(bort[1]) >= abs(bort[0]):
                    c2 = c2 + Rm[:, 1] * np.sign(bort[1]) * (0.3 - ey); ey = 0.3; til = 'antagen_djup'
                top = float(z1_)
                golv_ = float(z0_) < 0.35 or g == 'stol'  # står på golvet; annars hänger/står den högre (huv, hylla, väggskåp)
                if g == 'bord':
                    V, T = slå_ihop([lada(c2, ex, ey, yaw, top - 0.04, top, botten=True)] +
                                    [lada(c2 + Rm @ np.array([sx * (ex - 0.04), sy * (ey - 0.04)]), 0.025, 0.025, yaw, 0.0, top - 0.04)
                                     for sx in (-1, 1) for sy in (-1, 1)])
                else:
                    V, T = lada(c2, ex, ey, yaw, 0.0 if golv_ else float(z0_), top, botten=not golv_)
                former.append((nm, g, V, T, til, mi)); ytor.append(((((c2 @ Rm) - [ex, ey]), ((c2 @ Rm) + [ex, ey])), top))
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
        # grundregel: en struktur får inte dölja det kameran såg. Hörn klart framför observerat djup (inne i bilden,
        # utanför person/text) räknas; plana rumsytor som döljer mer än 10 % av sina synliga hörn förkastas.
        def doljer(V):
            xn, yn, zc = kam.proj(V); inne = (xn >= 0) & (xn < 1) & (yn >= 0) & (yn < 1) & (zc > 0.05)
            px = np.clip((np.nan_to_num(xn) * w).astype(int), 0, w - 1); py = np.clip((np.nan_to_num(yn) * h).astype(int), 0, h - 1)
            bed = inne & ~ogiltig[py, px] & np.isfinite(Zref[py, px])
            return float(((zc < Zref[py, px] * 0.85 - 0.05) & bed).sum() / max(1, bed.sum())), int(bed.sum())
        forkastade = []; beh = []
        for f_ in slut:
            fr, n_ = doljer(f_[2])
            if f_[1] in ('vagg', 'tak') and n_ > 20 and fr > 0.10:
                forkastade.append((f_[0], round(fr, 2))); continue
            beh.append(f_)
        slut = beh
        # textur per hörn: syns i bilden, inte ogiltigt, inget framför
        bitar = []; blob = b''; off = 0; tex = 0; tot = 0
        for nm, g, V, T, til, mi in slut:
            xn, yn, zc = kam.proj(V)
            px = np.clip((xn * w).astype(int), 0, w - 1); py = np.clip((yn * h).astype(int), 0, h - 1)
            inne = (xn >= 0) & (xn < 1) & (yn >= 0) & (yn < 1) & (zc > 0.05)
            # syns = inne i bilden, inte person/text, och inget ligger klart framför (primitiven får vara något större än ytan)
            zr = Zref[py, px]; syn = inne & ~ogiltig[py, px] & (zc <= zr * 1.12 + 0.03) & ~objpix[py, px]
            if g in ('karl', 'mat', 'foremal') or (g not in ('golv', 'vagg', 'tak', 'bank', 'bord', 'spis', 'skap')):
                syn = inne & ~ogiltig[py, px]  # små föremål: originalets projektion även på självskymda sidor (0° ska likna originalet)
            # grundregeln per triangel: en triangel som ligger klart framför det kameran såg (inne i bilden, ej person/text)
            # skärs bort, oavsett primitiv (blint prov 2: lådor och bordsskivor täckte mat och skyltar i 0°)
            bed = inne & ~ogiltig[py, px] & np.isfinite(zr)
            framfor = bed & (zc < zr * 0.85 - 0.05)
            hall = ~framfor[T].any(1)
            T = T[hall]
            if not len(T):
                continue
            tsyn = syn[T].all(1); tot += len(T); tex += int(tsyn.sum())
            uv = np.stack([np.nan_to_num(xn), 1 - np.nan_to_num(yn)], -1).astype(np.float32)
            for sel, textur, tilltro in ((tsyn, 'struktur', til), (~tsyn, 'farg', 'antagen')):
                if not sel.any():
                    continue
                Ts = T[sel]; anv = np.unique(Ts); karta = -np.ones(len(V), int); karta[anv] = np.arange(len(anv))
                pos = V[anv].astype(np.float32); uvs = uv[anv]; ix = karta[Ts].astype(np.uint32).ravel()
                b_ = {'etikett': f'{nm} ({"syns" if textur == "struktur" else "ej sedd"})', 'grupp': g, 'instans': len(bitar), 'tilltro': tilltro, 'textur': textur,
                      'farg': farg_av(mi), 'nv': len(pos), 'ni': len(ix)}
                for nyck, arr in (('pos', pos), ('uv', uvs), ('ind', ix)):
                    raw = arr.tobytes(); b_[nyck] = [off, len(raw)]; blob += raw; off += len(raw)
                bitar.append(b_)
        # SAM 3-föremål: observerad yta (skärva ur originalets djup, exakt 0°) + kontakt med stödytan + kjol ned till den
        # (volym och kontakt vid vridning). Pixlar delas exklusivt: den minsta masken vinner (mat före tallrik före bricka).
        def lagg(nm, g, V, T, UV, textur, tilltro, farg):
            nonlocal blob, off
            if not len(T):
                return
            b_ = {'etikett': nm, 'grupp': g, 'instans': len(bitar), 'tilltro': tilltro, 'textur': textur, 'farg': farg, 'nv': len(V), 'ni': int(T.size)}
            for nyck, arr in (('pos', V.astype(np.float32)), ('uv', UV.astype(np.float32)), ('ind', T.astype(np.uint32).ravel())):
                raw = arr.tobytes(); b_[nyck] = [off, len(raw)]; blob += raw; off += len(raw)
            bitar.append(b_)
        lt_n = 0; n_obj = 0
        if sam:
            ordn = sorted(range(len(sam_obj)), key=lambda k_: sam_obj[k_][1].sum()); agd = np.zeros((h, w), bool)
            for k_ in ordn:
                e_, m_ = sam_obj[k_]; mm = m_ & ok_ & ~agd; agd |= mm
                if mm.sum() < 20:
                    continue
                V, T, UV, kant = skarva(Xw, mm)
                if not len(T):
                    continue
                cq = np.median(V[:, :2], axis=0) @ Rm; zb = float(np.percentile(V[:, 2], 5))
                kand = [zz for (a_, b2), zz in ytor if np.all(cq >= a_ - 0.03) and np.all(cq <= b2 + 0.03) and zb - 0.15 <= zz <= zb + 0.25]
                bas = max(kand) if kand else None  # föremålet flyttas inte (0° ska stämma); kjolen sluter mot stödytan
                lagg(f'{e_} (SAM 3)', 'foremal', V, T, UV, 'struktur', 'skattad_ur_bild', farg_av(mm)); n_obj += 1
                if len(kant):  # kjol: kantkanter ned till stödytan (eller föremålets lägsta punkt)
                    zl = bas if bas is not None else float(V[:, 2].min())
                    nedre = V[kant].copy(); nedre[..., 2] = np.minimum(nedre[..., 2], zl)
                    Vk = np.concatenate([V[kant[:, 0]], V[kant[:, 1]], nedre[:, 1], nedre[:, 0]]); n4 = len(kant); ar = np.arange(n4)
                    Tk = np.concatenate([np.stack([ar, ar + n4, ar + 2 * n4], -1), np.stack([ar, ar + 2 * n4, ar + 3 * n4], -1)])
                    lagg(f'{e_} (kjol)', 'foremal', Vk, Tk, np.zeros((len(Vk), 2)), 'farg', 'antagen', farg_av(mm))
            # resten: allt som syns, inte är person, inte förklaras av en rumsyta och inte är ett föremål
            forklarad = np.isin(Gm, ['golv', 'tak', 'bank', 'bord', 'spis', 'skap']) | ((Gm == 'vagg') & (vaggar > 0)) | tackt | agd
            V, T, UV, _ = skarva(Xw, ok_ & ~forklarad)
            lagg('rest (observerad)', 'rest', V, T, UV, 'struktur', 'skattad_ur_bild', '#8a8f94')
        # hybrid utan SAM 3 (blint prov 21 nov: Ls vinner rum 44/54 men förlorar 0° 53/54): allt som inte är rum behåller Lt:s nät
        RUM_G = ('golv', 'vagg', 'tak', 'bank', 'bord', 'spis', 'skap', 'bakom_person')
        if not sam and sid in nat and (out / 'nat' / f'{sid}.bin').is_file():
            nb = (out / 'nat' / f'{sid}.bin').read_bytes(); lt_n = 0
            for b0 in nat[sid]['bitar']:
                if b0.get('grupp') in RUM_G or b0.get('tilltro') in ('antagen', 'genererad'):
                    continue
                b_ = dict(b0); b_['instans'] = len(bitar); b_['kalla'] = 'Lt'
                o0, n0 = b0['pos']; pos0 = np.frombuffer(nb[o0:o0 + n0], np.float32).reshape(-1, 3).copy()
                # kontakt (blint prov 3: plan skär genom föremål): ett litet föremål ställs på sin stödyta, högsta yta under
                # dess mitt inom rimligt avstånd; lyfts om det sjunkit in, sänks om det svävar lite. Större bitar rörs inte.
                if len(pos0) and np.ptp(pos0[:, :2], axis=0).max() < 0.8:
                    cq = np.median(pos0[:, :2], axis=0) @ Rm; zb = float(np.percentile(pos0[:, 2], 5))
                    kand = [zz for (a_, b2), zz in ytor if np.all(cq >= a_ - 0.03) and np.all(cq <= b2 + 0.03) and zb - 0.15 <= zz <= zb + 0.25]
                    if kand:
                        dz = max(kand) - zb
                        if abs(dz) > 0.005:
                            pos0[:, 2] += dz; b_['kontakt_dz'] = round(dz, 3)
                for nyck in ('pos', 'uv', 'ind'):
                    o0, n0 = b0[nyck]; raw = pos0.tobytes() if nyck == 'pos' else nb[o0:o0 + n0]
                    blob += raw; b_[nyck] = [off, len(raw)]; off += len(raw)
                bitar.append(b_); lt_n += 1
        (ut / f'{sid}.bin').write_bytes(blob)
        n_ = nat.get(sid, {})
        manifest[sid] = {'fil': f'{sid}.bin', 'ruta': u, 'bitar': bitar, 'transform': n_.get('transform'), 'rum': n_.get('rum', f'egen_{sid}'), 'rorlig': n_.get('rorlig'),
                         'textur_bild': f'{sid}.png'}
        rapport[sid] = {'former': len(slut), 'vaggar': vaggar, 'tak': tak_z is not None, 'yaw_grader': round(math.degrees(yaw), 1),
                        'texturerade_trianglar': round(tex / max(1, tot), 3), 'utan_stod': sum(1 for f_ in slut if f_[4] == 'utan_stod'), 'forkastade': forkastade, 'lt_bitar': lt_n, 'sam3_foremal': n_obj, 'sam3_mobler': len(sam_mobel)}
    (out / 'struktur.json').write_text(json.dumps({'schema': 'lokalitet-struktur/1', 'koordinater': 'samma världsram som nat.json', 'tagningar': manifest},
                                                  ensure_ascii=False), encoding='utf-8')
    (out / 'struktur_rapport.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')
    print(nyckel, json.dumps(rapport, ensure_ascii=False)[:600])


if __name__ == '__main__':
    for k in sys.argv[1:]:
        main(k)
