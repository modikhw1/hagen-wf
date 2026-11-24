"""Tidsutjämning av kroppsestimatorns parameterspår: slät och nära uppskattningen samtidigt.

Ersätter Hampel-radbyte + Butterworth-lågpass (6 Hz) + bildskyddets ruta-för-ruta-blandning. Mätningar (jamn_utvardera.py, README) visade
att det gamla sättet drev från estimaten på två ställen: Hampel byter hela rutor mot medianen i ett fönster (falska träffar vid snabba
rörelser) och lågpass på rotens orientering flyttar hela kroppen (6° rotfel ger ~30 px vid handleden på 2 m avstånd).

Metod ("rör"-utjämning, tube smoothing): per spår (en parameter eller en kvaternionskomponent) lösa
    min  sum_t w_t (x_t - y_t)^2 + lambda * sum_t (D^d x)_t^2        (Whittaker-utjämnare, d = 2 eller 3, symmetrisk, ingen fasförskjutning)
under villkoret |x_t - y_t| <= eps, där eps = k * sigma och sigma är spårets egen mätbrus (robust skattat ur tredje differensen).
Följden: brus (som estimatorn har ruta för ruta) jämnas ut, men en verklig rörelse som skulle ligga längre från estimaten än brusnivån
får aldrig ersättas av en kompromiss: avvikelsen är begränsad till k brusenheter. Villkoret löses med viktad omräkning (vikten ökar där
röret överskrids). Luckor (opålitliga rutor, dolda ben) har vikt 0 och fylls av utjämnaren (ingen slerp, ingen konstant hållning).
Trasiga rutor (en enstaka ruta där många spår hoppar samtidigt, t.ex. en person sedd bakifrån och uppochner) hittas mot den utjämnade
kurvan och får vikt 0; de byts alltså inte mot en medianruta.

Alla parametrar (fc, k, d, trasig-gränserna) är våra egna val; värdena står i STANDARD och motiveras i ingest/README.md.
Bara numpy och scipy.
"""
import numpy as np
from scipy.linalg import cho_factor, cho_solve

STANDARD = dict(fc=4.0, k=2.0, d=2, trasig_sigma=6.0, trasig_andel=.25, iter=10, min_sigma=1e-4)


def diffmatris(n, d):
    D = np.eye(n)
    for _ in range(d): D = np.diff(D, axis=0)
    return D


def lambda_fran_fc(fc, fps, d=2):
    """Whittaker-utjämnarens halveffektgräns: 1 / (1 + lambda (2 sin(w/2))^(2d)) = 1/2."""
    w = np.pi * min(fc / fps, .49)
    return 1.0 / (2 * np.sin(w)) ** (2 * d)


def brus_sigma(Y, w, d=3):
    """Robust brusskattning per spår ur d:e differensen (vitt brus: Var(D^d) = C(2d,d) sigma^2), bara över giltiga d+1-grupper. Y: (N, k)."""
    Y = np.asarray(Y, float); N = len(Y); D = diffmatris(N, d)
    ok = np.array([w[i:i + d + 1].min() > 0 for i in range(N - d)])
    if ok.sum() < 3: return np.full(Y.shape[1], np.nan)
    R = D[ok] @ Y; from math import comb
    return 1.4826 * np.median(np.abs(R - np.median(R, 0)), 0) / np.sqrt(comb(2 * d, d))


def whittaker(y, w, lam, d=2, eps=None, iter=10):
    """Ett spår (N,). w: vikt per ruta (0 = lucka). eps: rörets halvbredd (skalär eller None). Returnerar x (N,)."""
    N = len(y); D = diffmatris(N, d); P = lam * (D.T @ D); w0 = np.asarray(w, float).copy(); ww = w0.copy()
    y = np.asarray(y, float)
    for it in range(iter if eps is not None else 1):
        A = P + np.diag(ww + 1e-9); x = cho_solve(cho_factor(A), ww * y + 1e-9 * 0)
        if eps is None: break
        r = np.abs(x - y); viol = (r > eps * 1.05) & (w0 > 0)
        if not viol.any(): break
        ww[viol] *= 4.0
    return x


def utjamna(Y, w, fps, fc=4.0, k=2.0, d=2, sigma=None, min_sigma=1e-4, iter=10, rorbredd=True):
    """Rör-utjämna alla spår. Y: (N, J) (luckor får innehålla vad som helst), w: (N,) eller (N, J) vikter (0 = lucka).
    sigma: brusnivå per spår (J,) eller None (skattas ur Y). Returnerar (X, sigma, eps)."""
    Y = np.asarray(Y, float); N, J = Y.shape; w = np.asarray(w, float)
    W = np.repeat(w[:, None], J, 1) if w.ndim == 1 else w
    lam = lambda_fran_fc(fc, fps, d)
    if sigma is None:
        sigma = np.array([brus_sigma(Y[:, [j]], W[:, j], d=3)[0] for j in range(J)])
        sigma = np.where(np.isfinite(sigma), sigma, min_sigma)
    sigma = np.maximum(sigma, min_sigma); X = np.empty_like(Y); eps = k * sigma
    for j in range(J):
        if W[:, j].sum() < d + 2: X[:, j] = np.interp(np.arange(N), np.nonzero(W[:, j] > 0)[0], Y[W[:, j] > 0, j]) if (W[:, j] > 0).any() else 0.; continue
        X[:, j] = whittaker(Y[:, j], W[:, j], lam, d, eps[j] if rorbredd else None, iter)
    return X, sigma, eps


def hitta_trasiga(Y, w, fps, kolumner, fc=4.0, d=2, sigma=None, trasig_sigma=6.0, trasig_andel=.25, min_sigma=1e-4):
    """Rutor där minst `trasig_andel` av `kolumner` ligger mer än `trasig_sigma` brusenheter från en kraftigt utjämnad kurva (rör av).
    Kurvan skattas två gånger, andra gången utan de rutor som flaggats första gången, så att en trasig ruta inte drar kurvan åt sig.
    Returnerar bool (N,)."""
    Y = np.asarray(Y, float); N = len(Y); w = np.asarray(w, float).copy(); fel = np.zeros(N, bool); lam = lambda_fran_fc(fc, fps, d)
    sig = sigma if sigma is not None else np.array([brus_sigma(Y[:, [j]], w, d=3)[0] for j in range(Y.shape[1])])
    sig = np.maximum(np.where(np.isfinite(sig), sig, min_sigma), min_sigma)
    for _ in range(2):
        X = np.stack([whittaker(Y[:, j], np.where(fel, 0., w), lam, d) for j in kolumner], 1)
        z = np.abs(Y[:, kolumner] - X) / sig[kolumner]
        ny = (z > trasig_sigma).mean(1) >= trasig_andel
        ny &= w > 0
        if (ny == fel).all(): break
        fel = ny
    return fel


def kvaternion_kontinuerlig(Q, giltig):
    """Teckenkontinuerlig kvaternionföljd (N,4) över giltiga rutor."""
    Q = Q.copy(); ix = np.nonzero(giltig)[0]
    for a, b in zip(ix[:-1], ix[1:]):
        if Q[b] @ Q[a] < 0: Q[b] = -Q[b]
    return Q


def utjamna_t(T, w, fps, fc=2.0, k=2.0, d=2):
    """Rotens kamerarumsposition cam_t (N,3): siktlinjen (enhetsvektor) och log-avståndet utjämnas som egna spår.
    Avståndet är svagt bestämt ur en kamera och får därför längre rör (k * sigma med samma brusskattning)."""
    T = np.asarray(T, float); dist = np.linalg.norm(T, axis=1); r = T / dist[:, None]
    Y = np.concatenate([r, np.log(dist)[:, None]], 1)
    X, sig, eps = utjamna(Y, w, fps, fc=fc, k=k, d=d)
    r2 = X[:, :3] / np.linalg.norm(X[:, :3], axis=1, keepdims=True)
    return r2 * np.exp(X[:, 3])[:, None]


def stabilisera(P, E, giltig, benvis, fps, namn, fc=None, k=None, d=None, ut=None, trasiga=True, fc_hand=None, k_hand=None):
    """Hela sekvensutjämningen för en person, utan torch. P: (N,204) råa modellparametrar (NaN/valfritt i luckor), E: (N,72) uttryck,
    giltig: bool (N,) pålitliga rutor, benvis: bool (N,) benen syns. namn: parameternamnen (mhr_parametrar.json).
    Returnerar (P (N,204) med rotens Euler, E). Formparametrarna (identiteten) hanteras av anroparen: medianen låses som förr.
    Steg: rotens orientering som teckenkontinuerlig kvaternion; vrid/handled med samma fartgräns som förr; benparametrar får vikt 0 där benen
    inte syns (mjuk överbryggning i stället för att hålla värdet från närmaste ruta); trasiga rutor hittas och får vikt 0; rör-utjämning.
    Utanför första och sista giltiga rutan hålls värdet från närmaste giltiga ruta."""
    from scipy.spatial.transform import Rotation as Rot
    fc = fc or STANDARD['fc']; k = k or STANDARD['k']; d = d or STANDARD['d']
    N = len(P); giltig = np.asarray(giltig, bool); benvis = np.asarray(benvis, bool) & giltig
    ROT = [namn.index(n) for n in ('root_rx', 'root_ry', 'root_rz')]
    BEN = np.array([i for i, n in enumerate(namn) if any(t in n for t in ('upleg', 'knee', 'lowleg', 'foot')) and not n.startswith('scale')])
    HAND = np.array([i for i, n in enumerate(namn) if any(t in n for t in ('thumb', 'index', 'middle', 'ring', 'pinky', 'wrist'))])
    VRID = np.array([i for i, n in enumerate(namn) if ('twist' in n or 'wrist' in n or 'lowarm' in n) and not n.startswith('scale')])
    BEDOM = np.setdiff1d(np.arange(208), np.concatenate([BEN, HAND, ROT])); ix = np.nonzero(giltig)[0]
    Q = np.full((N, 4), np.nan); Q[ix] = Rot.from_euler('xyz', P[ix][:, ROT]).as_quat(); Q = kvaternion_kontinuerlig(Q, giltig)
    Y = np.concatenate([np.nan_to_num(P), np.nan_to_num(Q)], 1); Y[:, ROT] = 0.0
    w = np.repeat(giltig[:, None].astype(float), 208, 1)
    # vrid/handled: tvetydiga vrid hoppar flera rutor i följd; fartgräns 0,3 rad/ruta fram och bak (medel), utan medianbyte
    Yf = Y.copy()
    for j in VRID: Yf[:, j] = np.interp(np.arange(N), ix, Y[ix, j])
    Fw = Yf[:, VRID].copy(); Bw = Yf[:, VRID].copy(); m = .3
    for i in range(1, N): Fw[i] = np.clip(Fw[i], Fw[i - 1] - m, Fw[i - 1] + m)
    for i in range(N - 2, -1, -1): Bw[i] = np.clip(Bw[i], Bw[i + 1] - m, Bw[i + 1] + m)
    Y[:, VRID] = (Fw + Bw) / 2
    if benvis.any(): w[:, BEN] *= benvis[:, None]
    else: Y[:, BEN] = 0.0; w[:, BEN] = 1.0
    fel = hitta_trasiga(Y, giltig.astype(float), fps, BEDOM, fc=fc, d=d) if trasiga else np.zeros(N, bool)
    w[fel, :] = 0.0
    X, sigma, eps = utjamna(Y, w, fps, fc=fc, k=k, d=d)
    if fc_hand or k_hand:   # händerna har mer brus och mindre verklig rörelse per ruta: egen gräns och eget rör
        Xh, _, _ = utjamna(Y[:, HAND], w[:, HAND], fps, fc=fc_hand or fc, k=k_hand or k, d=d); X[:, HAND] = Xh
    ok = giltig & ~fel; ixk = np.nonzero(ok)[0]; X[:ixk[0]] = X[ixk[0]]; X[ixk[-1] + 1:] = X[ixk[-1]]
    we = np.repeat(ok[:, None].astype(float), 72, 1); Xe, _, _ = utjamna(np.nan_to_num(E), we, fps, fc=8.0, k=k, d=d)
    Xe[:ixk[0]] = Xe[ixk[0]]; Xe[ixk[-1] + 1:] = Xe[ixk[-1]]
    Qf = X[:, 204:208] / np.linalg.norm(X[:, 204:208], axis=1, keepdims=True); Pn = X[:, :204].copy(); Pn[:, ROT] = Rot.from_quat(Qf).as_euler('xyz')
    if ut is not None: ut.update(trasiga_rutor=int(fel.sum()), fc=fc, k=k, d=d)
    return Pn, Xe
