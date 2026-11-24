"""0028 punkt 1–2: renderkameran som en jämn inåkning, inte en skakig väg. Kroppen orörd (roten ur r_rot.py).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/r_kamera.py <g_forvarld-variant_rot> <samspel_rot.json> [--modell dolly|dolly_zoom|separat] [--hojd 1.3|fri]
Problemet i 0027: kamerans centrum och lins löstes fritt per ruta (x, y och lins; höjden låst), och utjämnades först efteråt. Det ger en väg på
8,8 m för en tagning där originalets kamera gör en inåkning och en tippning. Felet sitter i att dolly och zoom nästan inte går att skilja åt
per ruta: få synliga leder, och linsen och avståndet byter av varandra (linsen hoppade mellan 43 och 140 mm).
Här låses fler frihetsgrader, och allt löses på en gång över hela tagningen:
  C(u) = A + s(u)·d,   d = (cos θ, sin θ, 0)   kameran åker längs en rak linje i golvplanet
  höjd   konstant (--hojd 1.3: låst som i 0027; fri: en enda höjd för hela tagningen, 1,1–1,8 m)
  lins   konstant (dolly), eller lins(u) = l0·(1 + k·s(u)) (dolly_zoom: zoomen följer samma förlopp som åkningen)
  s(u)   en jämn kurva genom K knutar (kubisk interpolation), s(start) = 0, med straff på andraderivatan
  rotationen per ruta behålls ur planen (originalets tippning, ur varld.npz)
Målen i bild är originalets synliga överkroppsleder (dagens 2D-läsning), som i r_rot.py. Höjden och y ≤ Y_MAX som i 0027.
Ut: g_forvarld/<variant>_kam/plan.json (planen med den nya kameran; sekvensen pekas till <variant>/sekvens_1.npz), kamera.json (mått).
--fri ger 0027:s lösning (fri per ruta, utjämnad) för jämförelse, utan att skriva plan.
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import least_squares

HIT = Path(__file__).resolve().parent
sys.path.insert(0, str(HIT))
from r_rot import mal2d, proj, OVER, Y_MAX  # noqa: E402

K = 9   # knutar för s(u)
VRID = '--vrid' in sys.argv
LINS0 = float(sys.argv[sys.argv.index('--lins0') + 1]) if '--lins0' in sys.argv else None   # linsen i början låst (ingestens antagande, som kroppen lästes med)
Y_MIN = float(sys.argv[sys.argv.index('--ymin') + 1]) if '--ymin' in sys.argv else -2.4   # rummets bakre gräns (golvet 4,87 m djupt); kunden står vid disken: -0,8
VV = float(sys.argv[sys.argv.index('--vrid-vikt') + 1]) if '--vrid-vikt' in sys.argv else 4.
VB = .6   # största rättning av vridningen, rad
def rx(a): c, s_ = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])
def ry(a): c, s_ = np.cos(a), np.sin(a); return np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])


def _arg(n, f): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else f


def main():
    v, spf = sys.argv[1], HIT / sys.argv[2]; modell = _arg('--modell', 'dolly_zoom'); hojd = _arg('--hojd', '1.3')
    G = HIT / 'g_forvarld' / v; plan = json.loads((G / 'plan.json').read_text(encoding='utf-8')); nk = plan['renderkamera']['nycklar']
    sp = json.loads(spf.read_text())['rutor']; n = len(sp)
    C_in = np.array([np.array(k['matris'])[:3, 3] for k in nk[:n]]); L_in = np.array([k['lins_mm'] for k in nk[:n]])
    Rk = [np.array(k['matris'])[:3, :3] for k in nk[:n]]
    obs = {}
    for u in range(n):
        m = mal2d(u)
        if m is None or m[1].sum() < 3: continue
        P = np.array([sp[u]['leder'][j]['huvud'] for j in OVER]); obs[u] = (P[m[1]], m[0][m[1]])
    us = np.array(sorted(obs)); knut = np.linspace(us[0], us[-1], K)
    hfri = hojd == 'fri'; h0 = 1.3 if hfri else float(hojd.split(',')[0])
    if ',' in hojd:   # 0028: höjdprofil bas,topp,a,b: kunden lyfter telefonen över montern i rutorna a–b (mjuka ramper på 15 rutor)
        hb, ht, ha, hbb = [float(t) for t in hojd.split(',')]; uu_ = np.arange(n)
        ramp = np.clip(np.minimum((uu_ - ha + 15) / 15, (hbb + 15 - uu_) / 15), 0, 1); HPROF = hb + (ht - hb) * (.5 - .5 * np.cos(np.pi * ramp))
    else: HPROF = None

    def packa(x):
        A = x[0:2]; th = x[2]; s = np.r_[0., x[3:3 + K - 1]]; i = 3 + K - 1
        h = x[i] if hfri else h0; i += hfri
        l0 = LINS0 or x[i]; kz = x[i + 1] if modell == 'dolly_zoom' else 0.
        uu = np.clip(np.arange(n), knut[0], knut[-1]); su = CubicSpline(knut, s, bc_type='natural')(uu)
        d = np.array([np.cos(th), np.sin(th)]); C = np.c_[A + su[:, None] * d, HPROF if HPROF is not None else np.full(n, h)]; L = l0 * (1 + kz * su)
        if modell == 'separat':                                            # zoomen ett eget jämnt förlopp: lins = l0·exp(z(u)), z(start) = 0
            z = np.r_[0., x[i + 1:i + K]]; L = l0 * np.exp(CubicSpline(knut, z, bc_type='natural')(uu)); s = np.r_[s, 3 * z]
        R = Rk
        if VRID:                                                           # jämn rättning av tippning och panorering (kameraramen), K knutar var
            j = len(x) - 2 * K; tp = CubicSpline(knut, x[j:j + K], bc_type='natural')(uu); pa = CubicSpline(knut, x[j + K:], bc_type='natural')(uu)
            R = [Rk[u] @ rx(tp[u]) @ ry(pa[u]) for u in range(n)]; s = np.r_[s, 20 * x[j:]]
        return C, L, s, R

    def res(x):
        C, L, s, R = packa(x); r = []
        for u in us:
            P, q = obs[u]; r.append((proj(P, R[u], C[u], L[u]) - q).ravel())
        for b in range(0, len(s), K): r.append(40 * np.diff(s[b:b + K], 2))   # jämnt: straff på andraderivatan i knutarna, per förlopp
        if VRID: r.append(VV * s[-2 * K:])                                  # och rättningen av vridningen hålls liten
        r.append(5000 * np.maximum(0, C[:, 1] - Y_MAX)); r.append(5000 * np.maximum(0, Y_MIN - C[:, 1]))                     # kameran stannar på kundens sida
        r.append(200 * np.maximum(0, 15 - L))
        return np.concatenate(r)

    # start: riktningen ur 0027:s fria lösning (start -> närmast kroppen)
    a0 = C_in[us[0], :2]; b0 = C_in[us[len(us) // 2], :2]; th0 = float(np.arctan2(*(b0 - a0)[::-1]))
    x0 = np.r_[a0, th0, np.linspace(0, np.linalg.norm(b0 - a0), K)[1:], ([h0] if hfri else []), L_in[us[0]], ([0.] if modell == 'dolly_zoom' else []), (np.zeros(K - 1) if modell == 'separat' else []), (np.zeros(2 * K) if VRID else [])]
    lo = np.r_[-3, Y_MIN, -np.pi, np.full(K - 1, -4), ([1.1] if hfri else []), 15, ([-0.5] if modell == 'dolly_zoom' else []), (np.full(K - 1, -1.5) if modell == 'separat' else []), (np.full(2 * K, -VB) if VRID else [])]
    hi = np.r_[3, Y_MAX, np.pi, np.full(K - 1, 4), ([1.8] if hfri else []), 200, ([3.] if modell == 'dolly_zoom' else []), (np.full(K - 1, 1.5) if modell == 'separat' else []), (np.full(2 * K, VB) if VRID else [])]
    x = least_squares(res, np.clip(x0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), loss='soft_l1', f_scale=20, max_nfev=4000).x
    C, L, s, R = packa(x)
    fel = {u: float(np.median(np.linalg.norm(proj(obs[u][0], R[u], C[u], L[u]) - obs[u][1], axis=1)) / 1920 * 1000) for u in us}
    fel_in = {u: float(np.median(np.linalg.norm(proj(obs[u][0], Rk[u], C_in[u], L_in[u]) - obs[u][1], axis=1)) / 1920 * 1000) for u in us}
    seg = {g['id']: g['rutor_plan'] for g in json.loads(__import__('tagning').HANDLING.read_text(encoding='utf-8'))['segment']}
    med = lambda f, a, b: (round(float(np.median([e for u, e in f.items() if a <= u <= b])), 1) if any(a <= u <= b for u in f) else None)
    vag = lambda C: round(float(np.linalg.norm(np.diff(C, axis=0), axis=1).sum()), 2)
    ryck = lambda C: round(float(np.linalg.norm(np.diff(C, 2, axis=0), axis=1).max() * 1000), 1)   # största andraderivata, mm per ruta²
    res_ = dict(variant=v, modell=modell, hojd=('fri: ' if hfri else 'låst: ') + (f'{C[0, 2]:.2f} m' if HPROF is None else f'profil {hojd} (bas, topp, rutor)'),
                kamera=dict(vag_m=vag(C), vag_0027_m=vag(C_in), ryck_mm=ryck(C), ryck_0027_mm=ryck(C_in), start=C[0].round(3).tolist(), slut=C[n - 1].round(3).tolist(),
                            lins_mm=[round(float(L.min()), 1), round(float(L.max()), 1)], lins_0027_mm=[round(float(L_in.min()), 1), round(float(L_in.max()), 1)],
                            zoom=round(float(L.max() / L.min()), 2), riktning_grader=round(float(np.degrees(x[2])), 1),
                            vridning_rattad_grader=(round(float(np.degrees(np.abs(x[-2 * K:-K]).max())), 1), round(float(np.degrees(np.abs(x[-K:]).max())), 1)) if VRID else None,
                            tippning_ned_grader={u: round(float(np.degrees(np.arcsin(-R[u][2, 2] * -1 if False else -(-R[u][:, 2])[2]))), 1) for u in (0, 20, 39, 50, 60, 78, 100, 130, 155)}),
                projektionsfel_promille={k: dict(nu=med(fel, *ab), i_0027=med(fel_in, *ab)) for k, ab in seg.items()},
                hela=dict(nu=med(fel, 0, 999), i_0027=med(fel_in, 0, 999)))
    print(json.dumps(res_, ensure_ascii=False, indent=1))
    if '--skriv' in sys.argv:
        ut = HIT / 'g_forvarld' / _arg('--skriv', v + '_kam'); ut.mkdir(exist_ok=True); plan['renderkamera']['nycklar'] = nk
        for u in range(n):   # 0028: bara tagningens egna rutor (n); senare tagningars nycklar lämnas orörda
            j = u; M = np.array(nk[u]['matris']); M[:3, 3] = C[j]; M[:3, :3] = R[j]; nk[u]['matris'] = M.tolist(); nk[u]['lins_mm'] = float(L[j])
        plan.setdefault('beslut', []).append(f'0028: renderkameran som jämn inåkning ({modell}, höjd {res_["hojd"]}), löst över hela tagningen mot originalets synliga överkropp (gennedbrytning/r_kamera.py).')
        (ut / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
        (ut / 'kamera.json').write_text(json.dumps(res_, ensure_ascii=False, indent=1), encoding='utf-8')
        np.savez(ut / 'kamera_bana.npz', C=C, L=L, R=np.array(R), C_0027=C_in, L_0027=L_in)


if __name__ == '__main__': main()
