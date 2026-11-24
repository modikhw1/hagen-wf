"""0026 punkt 1: lägg en generering av godtycklig längd på källans rutor. Monoton dynamisk tidspassning (DTW) ur mätning.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/t_tid.py <variant> [--kalla-rutor 148]
Läser d_video/<variant>/las/1/*.npz (läsningen ur genereringen, alla rutor) och dagens läsning ur originalet (ingest kropp/1, ruta+7).
Drag per ruta, valda för att inte bero på kamerans skala och läge (genereringens kamera är en annan än originalets):
  - bålens lutning framåt (roten->halsen mot kamerans lodaxel, grader / 30)
  - höger handled relativt halsen, i bållängder (3D, kamerans ram)
  - höger armbågsvinkel (grader / 60)
  - vänster handled relativt halsen, i bållängder (halv vikt)
Dragen jämnas (Savitzky–Golay 9) och standardiseras per drag. DTW med lutningsgräns: varje steg flyttar källan 1 och genereringen 0–3 rutor,
så avbildningen är monoton. minsteg 1 (förval): genereringen går alltid framåt, så kroppen fryser inte (0026: minsteg 0 gav platåer på 30 rutor). Jämförs med linjär omskalning (generering ruta = i * (G-1)/(K-1)).
Kontroll: handlingsspårets vändpunkter (handen lägst i h3, armen längst fram i h8) på källans rutor efter passningen.
Ut: d_video/<variant>/tid.json (avbildning källruta -> genereringsruta, kostnad per ruta för båda, vändpunkter), tid.jpg (dragen före/efter),
och d_video/<variant>_t/ med isolerad.mp4 (148 rutor) och las/1/<källruta>.npz, som kedjan tar emot som vanligt.
"""
import json, shutil, sys
from pathlib import Path
import cv2, numpy as np
from scipy.signal import savgol_filter

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; from tagning import DAG, OFFS, HANDLING, T as KONF   # 0030
N = json.loads((ING / 'mhr_ledernamn.json').read_text())


def drag(f):
    if not f.exists(): return None
    z = np.load(f); k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); g = lambda n: k[N.index(n)]
    bal = g('c_neck') - g('root'); L = np.linalg.norm(bal)
    lut = np.degrees(np.arctan2(-bal[2], -bal[1])) / 30
    hr = (g('r_wrist') - g('c_neck')) / L; hl = (g('l_wrist') - g('c_neck')) / L * .5
    a, b = g('r_uparm') - g('r_lowarm'), g('r_wrist') - g('r_lowarm')
    arm = np.degrees(np.arccos(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1))) / 60
    return np.r_[lut, hr, arm, hl]


def serie(filer):
    D = [drag(f) for f in filer]; ok = np.array([d is not None for d in D]); X = np.zeros((len(D), 8))
    X[ok] = np.array([d for d in D if d is not None]); x = np.arange(len(D))
    for j in range(8): X[:, j] = savgol_filter(np.interp(x, x[ok], X[ok, j]), 9, 2)
    return X


def dtw(A, B, maxsteg=3, minsteg=1):
    """A: källa (K), B: generering (G). Väg w(i) monoton, w(i+1)-w(i) in minsteg..maxsteg, w(0)=0, w(K-1) fritt (genereringens slut kapas)."""
    K, G = len(A), len(B); C = np.linalg.norm(A[:, None] - B[None], axis=2); D = np.full((K, G), np.inf); P = np.zeros((K, G), int)
    D[0, 0] = C[0, 0]
    for i in range(1, K):
        for j in range(G):
            lo = max(0, j - maxsteg); hi = j - minsteg + 1
            if hi <= lo: continue
            prev = D[i - 1, lo:hi]
            if not np.isfinite(prev).any(): continue
            k = int(np.argmin(prev)); D[i, j] = C[i, j] + prev[k]; P[i, j] = lo + k
    w = [int(np.argmin(D[K - 1]))]   # fritt slut: genereringens överskott efter sista källrutan kapas (0026)
    for i in range(K - 1, 0, -1): w.append(P[i, w[-1]])
    return np.array(w[::-1]), C


def main():
    v = sys.argv[1]; K = int(sys.argv[sys.argv.index('--kalla-rutor') + 1]) if '--kalla-rutor' in sys.argv else int(KONF['kalla_rutor'])
    d = HIT / 'd_video' / v; las = sorted((d / 'las/1').glob('*.npz')); G = len(las)
    A = serie([DAG / f'{i + OFFS:04d}.npz' for i in range(K)]); B = serie([d / 'las/1' / f'{j:04d}.npz' for j in range(G)])
    mu, sd = A.mean(0), A.std(0) + 1e-6; An, Bn = (A - mu) / sd, (B - mu) / sd   # samma skala för båda: källans
    ms = int(sys.argv[sys.argv.index('--minsteg') + 1]) if '--minsteg' in sys.argv else 1
    w, C = dtw(An, Bn, minsteg=ms); lin = np.round(np.arange(K) * (G - 1) / (K - 1)).astype(int)
    kd, kl = C[np.arange(K), w], C[np.arange(K), lin]
    hand = A[:, 1:4]; hb = B[:, 1:4]
    # vändpunkter: handen lägst (y störst, kamerans y nedåt) inom h3, armen längst fram (z minst) inom h8
    H = json.loads(HANDLING.read_text(encoding='utf-8'))['segment']; seg = {s['id']: s['rutor_klipp'] for s in H}
    def vand(X, a, b, kol, f): r = range(a, b + 1); return a + int(f(X[a:b + 1, kol]))
    src_lag = vand(A, *seg['h3'], 2, np.argmax); src_fram = vand(A, *seg['h8'], 3, np.argmin)
    gen_lag = int(np.argmax(B[:, 2][: G * 2 // 3])); gen_fram = int(np.argmin(B[:, 3]))
    def till_kalla(j, m): return int(np.argmin(np.abs(m - j)))
    res = dict(variant=v, kalla_rutor=K, generering_rutor=G, metod=__doc__.split('\n')[1].strip(), maxsteg=3,
               avbildning=w.tolist(), linjar=lin.tolist(),
               kostnad=dict(dtw_median=round(float(np.median(kd)), 3), dtw_p90=round(float(np.percentile(kd, 90)), 3),
                            linjar_median=round(float(np.median(kl)), 3), linjar_p90=round(float(np.percentile(kl, 90)), 3)),
               lutning_korrelation=dict(dtw=round(float(np.corrcoef(A[:, 0], B[w, 0])[0, 1]), 3), linjar=round(float(np.corrcoef(A[:, 0], B[lin, 0])[0, 1]), 3)),
               vandpunkter=dict(handen_lagst=dict(kalla=src_lag, generering=gen_lag, dtw_ger_kalla=till_kalla(gen_lag, w), linjar_ger_kalla=till_kalla(gen_lag, lin)),
                                armen_langst_fram=dict(kalla=src_fram, generering=gen_fram, dtw_ger_kalla=till_kalla(gen_fram, w), linjar_ger_kalla=till_kalla(gen_fram, lin))),
               tempo=dict(genereringsrutor_per_kallruta_per_segment={s['id']: round(float((w[s['rutor_klipp'][1]] - w[s['rutor_klipp'][0]] + 1) / (s['rutor_klipp'][1] - s['rutor_klipp'][0] + 1)), 2) for s in H}))
    (d / 'tid.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    # bild: lutning och handens höjd, källa mot generering linjärt och med DTW
    h, W_ = 300, 900; img = np.full((2 * h, W_, 3), 255, np.uint8)
    for r, kol in enumerate([0, 2]):
        def kurva(y, farg):
            y = (y - A[:, kol].min()) / (np.ptp(A[:, kol]) + 1e-6); pts = np.stack([np.linspace(10, W_ - 10, K), r * h + h - 20 - y * (h - 40)], 1).astype(np.int32)
            cv2.polylines(img, [pts], False, farg, 2)
        kurva(A[:, kol], (0, 0, 0)); kurva(B[lin, kol], (0, 140, 255)); kurva(B[w, kol], (200, 80, 0))
        cv2.putText(img, ['lutning', 'handens hojd (y)'][r] + ': kalla svart, linjar orange, dtw bla', (12, r * h + 22), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 0, 0), 1)
    cv2.imwrite(str(d / 'tid.jpg'), img)
    # läsning och video på källans rutor
    ut = HIT / 'd_video' / f'{v}_t'; (ut / 'las/1').mkdir(parents=True, exist_ok=True)
    c = cv2.VideoCapture(str(d / 'isolerad.mp4')); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    vw = cv2.VideoWriter(str(ut / 'isolerad.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 29.97, F[0].shape[1::-1])
    for i, j in enumerate(w):
        shutil.copy(d / 'las/1' / f'{j:04d}.npz', ut / 'las/1' / f'{i:04d}.npz'); vw.write(F[min(j, len(F) - 1)])
    vw.release(); (ut / 'kalla.json').write_text(json.dumps(dict(fran=v, avbildning='../' + v + '/tid.json'), ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: res[k] for k in ('kostnad', 'lutning_korrelation', 'vandpunkter', 'tempo')}, ensure_ascii=False, indent=1))


if __name__ == '__main__': main()
