"""0026 punkt 5: kamerafri källa med originalets pixlar kvar (som k2, e2_k2.py) för valfri tagning. Allmän version av e_kamerafri + e2_k2.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/e4_kamerafri.py <ingestklipp> <tagning> <ut-mapp> [--video <mp4>] [--offset 0] [--spar 1]
- Avbildning per ruta (likformig: skala och förskjutning) som lägger personens överkropp (huvud, hals, axlar ur ingestens kropp/<spar>) där
  den är i ruta 0; utjämnad (Savitzky–Golay 15). Sparas med invers i <ut>/avbildning.json.
- Hela originalrutan följer med. Maskdelar ur ingestens personmask som rör bildkanten och inte är den största (främmande händer) målas grå.
- H.264 (Dreamina nekar MPEG-4 Part 2) i originalets fps. Ut: <ut>/1_kalla_kamerafri.mp4, avbildning.json, oversikt.jpg.
<video>: förval ingest/ut/<klipp>/klipp/<tagning>.mp4. <offset>: ingestens rutnummer för videons ruta 0 (förval tagningens start i kropp/).
"""
import argparse, json, subprocess, tempfile
from pathlib import Path
import cv2, numpy as np
from scipy.signal import savgol_filter

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; N = json.loads((ING / 'mhr_ledernamn.json').read_text()); GRA = 200
LED = ['c_head', 'c_neck', 'l_uparm', 'r_uparm']


def main():
    a = argparse.ArgumentParser(); a.add_argument('klipp'); a.add_argument('tagning'); a.add_argument('ut'); a.add_argument('--video'); a.add_argument('--offset', type=int, default=0)
    a.add_argument('--spar', default='1'); x = a.parse_args()
    T = ING / 'ut' / x.klipp / x.tagning; ut = Path(x.ut); ut.mkdir(parents=True, exist_ok=True)
    vid = x.video or str(ING / 'ut' / x.klipp / 'klipp' / f'{x.tagning}.mp4'); cap = cv2.VideoCapture(vid); fps = cap.get(5); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(f)
    H, W = F[0].shape[:2]; n = len(F)
    def punkter(i):
        f = T / f'kropp/{x.spar}/{i + x.offset:04d}.npz'
        if not f.exists(): return None
        z = np.load(f); k = (z['pred_joint_coords'] + z['pred_cam_t']).astype(float); fl = float(z['focal_length'])
        return np.array([[fl * k[N.index(m), 0] / k[N.index(m), 2] + W / 2, fl * k[N.index(m), 1] / k[N.index(m), 2] + H / 2] for m in LED])
    P0 = next(p for p in (punkter(i) for i in range(n)) if p is not None); S, Tt = np.full(n, np.nan), np.full((n, 2), np.nan)
    for i in range(n):
        P = punkter(i)
        if P is None: continue
        pm, qm = P.mean(0), P0.mean(0); s = float(((P - pm) * (P0 - qm)).sum() / ((P - pm) ** 2).sum()); S[i], Tt[i] = s, qm - s * pm
    ok = ~np.isnan(S); xx = np.arange(n); S = np.interp(xx, xx[ok], S[ok]); Tt = np.stack([np.interp(xx, xx[ok], Tt[ok, j]) for j in range(2)], 1)
    fl = min(15, n - (1 - n % 2)); S = np.exp(savgol_filter(np.log(S), fl, 2)); Tt = np.stack([savgol_filter(Tt[:, j], fl, 2) for j in range(2)], 1)
    M = np.load(T / 'masker.npy'); avb = []; hand = []
    with tempfile.TemporaryDirectory() as d:
        for i, f in enumerate(F):
            lo = M[min(i, len(M) - 1)].astype(np.uint8); nk, lab, st, _ = cv2.connectedComponentsWithStats(lo); b = f.copy()
            if nk > 2:
                stor = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); hm, wm = lo.shape; g = np.zeros_like(lo)
                for c in range(1, nk):
                    x0, y0, ww, hh = st[c, :4]
                    if c != stor and (x0 == 0 or y0 == 0 or x0 + ww >= wm or y0 + hh >= hm): g[lab == c] = 1
                if g.any():
                    hand.append(i); g = cv2.dilate(cv2.resize(g, (W, H), interpolation=cv2.INTER_NEAREST), np.ones((31, 31), np.uint8)); b[g > 0] = GRA
            A = np.array([[S[i], 0, Tt[i, 0]], [0, S[i], Tt[i, 1]]]); avb.append(dict(ruta=i, skala=round(float(S[i]), 5), forskjutning=Tt[i].round(2).tolist(), A=A.round(6).tolist(), invers=cv2.invertAffineTransform(A).round(6).tolist()))
            cv2.imwrite(str(Path(d) / f'{i:04d}.png'), cv2.warpAffine(b, A, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(GRA, GRA, GRA)))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', str(Path(d) / '%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', str(ut / '1_kalla_kamerafri.mp4')], check=True)
        K = [cv2.imread(str(Path(d) / f'{i:04d}.png')) for i in np.linspace(0, n - 1, 6).astype(int)]
    cv2.imwrite(str(ut / 'oversikt.jpg'), np.hstack([np.vstack([cv2.resize(F[i], (160, 284)), cv2.resize(k, (160, 284))]) for i, k in zip(np.linspace(0, n - 1, 6).astype(int), K)]))
    (ut / 'avbildning.json').write_text(json.dumps(dict(klipp=x.klipp, tagning=x.tagning, video=vid, fps=fps, rutor=n, storlek=[W, H], skala_omfang=[round(float(S.min()), 3), round(float(S.max()), 3)],
                                                      framande_hand_gra_rutor=hand, rutor_avbildning=avb), ensure_ascii=False, indent=1), encoding='utf-8')
    print('klar', n, 'rutor', W, H, 'skala', round(float(S.min()), 3), round(float(S.max()), 3), 'främmande hand i', len(hand), 'rutor')


if __name__ == '__main__': main()
