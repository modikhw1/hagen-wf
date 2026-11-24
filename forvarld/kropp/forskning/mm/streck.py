"""FORSKNING: streckfilm för att titta på kroppen direkt ur simulatorns kroppar, utan vägen tillbaka till MHR och Blender.

  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/streck.py <ut.mp4> <ref.npz> <etikett>=<raw.npz> [<etikett>=<raw.npz> ...]
Första kolumnen är referensen. Övre raden: framifrån (personens egen riktning). Nedre raden: från sidan.
Skriver också <ut>_blad.png med sex rutor.
"""
import sys, subprocess
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent)); import mhr_smpl as M

ix = M.SN.index
BEN = [(i, M.SP[i]) for i in range(1, len(M.SN))]
FARG = lambda n: '#c0392b' if n.startswith('R_') else ('#2471a3' if n.startswith('L_') else '#222222')


def ladda(ref, raws):
    r = dict(np.load(ref, allow_pickle=True)); S = M.fk_smpl(r['G'].astype(float), r['rot'].astype(float)); k = len(S) - 1; ut = []
    for etikett, f in raws:
        d = dict(np.load(f, allow_pickle=True)); P = d['pos'].astype(float) - d['skift'][None, None]; k = min(k, len(P)); P = P - np.r_[(P[0, 0] - S[1, 0])[:2], 0.]; ut.append((etikett, P))
    R = S[1:1 + k]; v = np.median(R[:, ix('L_Hip')] - R[:, ix('R_Hip')], axis=0); v[2] = 0; v /= np.linalg.norm(v); fram = np.cross(v, [0, 0, 1.])
    return [('referens', R)] + [(e, P[:k]) for e, P in ut], fram, v, R[0, 0].copy(), k


def rita(ax, P, a, b, o):
    """a, b: vågrät axel och (0,0,1). Ritar kroppen projicerad."""
    x = (P - o) @ a; z = P[:, 2]
    for i, p in BEN: ax.plot([x[i], x[p]], [z[i], z[p]], color=FARG(M.SN[i]), lw=2.2, solid_capstyle='round')
    ax.plot(x[ix('Head')], z[ix('Head')] + 0.09, 'o', color='#222222', ms=9)
    ax.axhline(0, color='#999999', lw=1); ax.set_xlim(-1.0, 1.0); ax.set_ylim(-0.05, 1.85); ax.set_aspect('equal'); ax.axis('off')


def bild(serier, fram, v, o, f, fil, rubrik=''):
    n = len(serier); fig, axs = plt.subplots(2, n, figsize=(2.6 * n, 6.4), dpi=80, squeeze=False)
    for c, (e, P) in enumerate(serier):
        rita(axs[0][c], P[f], v, None, o); rita(axs[1][c], P[f], -fram, None, o); axs[0][c].set_title(e, fontsize=10)
    axs[0][0].text(-0.98, 1.75, 'framifrån', fontsize=8, color='#666666'); axs[1][0].text(-0.98, 1.75, 'från sidan (framåt åt höger)', fontsize=8, color='#666666')
    fig.suptitle(f'{rubrik}  ruta {f}', fontsize=9, y=0.995); fig.subplots_adjust(left=0.01, right=0.99, top=0.94, bottom=0.01, wspace=0.02, hspace=0.02); fig.savefig(fil); plt.close(fig)


def blad(serier, fram, o, k, fil):
    rutor = sorted({int(round(x)) for x in np.linspace(0, k - 1, 6)}); n = len(serier)
    fig, axs = plt.subplots(n, len(rutor), figsize=(2.2 * len(rutor), 2.9 * n), dpi=110, squeeze=False)
    for r, (e, P) in enumerate(serier):
        for c, f in enumerate(rutor):
            rita(axs[r][c], P[f], -fram, None, o); axs[r][c].set_title(f'{e}, ruta {f}' if c == 0 else f'ruta {f}', fontsize=8)
    fig.suptitle('Från sidan, framåt åt höger. Röd = höger sida, blå = vänster.', fontsize=9); fig.tight_layout(); fig.savefig(fil); plt.close(fig)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; ut = Path(a[0]); serier, fram, v, o, k = ladda(a[1], [x.split('=', 1) for x in a[2:]])
    blad(serier, fram, o, k, ut.with_name(ut.stem + '_blad.png'))          # bladet först: det går på någon sekund
    if '--bara-blad' in sys.argv: print('STRECK blad', ut.with_name(ut.stem + '_blad.png')); return
    steg = 2; tmp = ut.parent / (ut.stem + '_rutor'); tmp.mkdir(parents=True, exist_ok=True)   # varannan ruta, 15 bilder per sekund
    for i, f in enumerate(range(0, k, steg)): bild(serier, fram, v, o, f, tmp / f'{i:04d}.png')
    delfil = ut.with_name(ut.stem + '_del.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(30 / steg), '-i', str(tmp / '%04d.png'), '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-pix_fmt', 'yuv420p', str(delfil)], check=True)
    delfil.replace(ut)
    for p in tmp.glob('*.png'): p.unlink()
    tmp.rmdir(); print('STRECK', ut, k, 'rutor')


if __name__ == '__main__': main()
