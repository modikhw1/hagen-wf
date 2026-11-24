"""0017 del G / 0021 punkt 5: den nya kroppsläsningen in i gelatos förvärld, i en kopia av planen. Kedjans kod är oförändrad.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/g_forvarld.py <variant>
1. Läsningen ur d_video/<variant>/las/1/<i>.npz läggs som ingestrutor <i+7> (klippets ruta 0 = ingestens 7), omskalad till ingestens
   ram: focal_length och pred_keypoints_2d gånger 1080/videobredd (cam_t och 3D oförändrade, de beror bara på kvoten fokal/bild).
2. Synlighet per ruta: underkroppen syns om båda knäna (pred_keypoints_2d[11:13], som i ingest_klipp) ligger i bild. Pålitlighet: alla rutor.
3. ingest/sekvens_stabil.py (oförändrad, sam3db-venv) gör sekvensen, N och fps som ingestens S1.
4. Planen kopieras (kontrakt/ut/kand-kennysgelato_n06-hand/narvaro/plan.json); bara S1:s rorelse byts. Plats, golv, kamera, stöd och
   handfäste kommer ur dagens plan. Blender bygger scenen (mhr_rig.py, oförändrad) och renderar S1:s rutor.
5. Film: original | dagens förvärld | förvärld med ny kropp, S1:s 156 rutor.
"""
import json, shutil, subprocess, sys
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; ROT = HIT.parents[2]; ING = HIT.parent / 'ingest'
S1 = ING / 'ut/kand-kennysgelato-tagningar/S1'; DAG = HIT.parent / 'kontrakt/ut/kand-kennysgelato_n06-hand/narvaro'
PY_SAM = HIT.parent / 'klipp2/sam3db/.venv/Scripts/python.exe'
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'


def main():
    v = sys.argv[1]; d = HIT / 'g_forvarld' / v; kropp = d / 'kropp'; kropp.mkdir(parents=True, exist_ok=True)
    meta = json.loads((S1 / 'meta.json').read_text()); N, fps = meta['N'], meta['fps']
    src = HIT / 'd_video' / v / 'las' / '1'; vb = cv2.VideoCapture(str(HIT / 'd_video' / v / 'isolerad.mp4')).get(3); s = 1080 / vb
    syn, pal = {}, {}
    kf = '--kamerafri' in sys.argv
    avb = json.loads((HIT / 'kamerafri/avbildning.json').read_text(encoding='utf-8'))['rutor'] if kf else None
    for f in sorted(src.glob('*.npz')):
        z = dict(np.load(f)); i = int(f.stem) + 7
        z['focal_length'] = np.asarray(z['focal_length'] * s); z['pred_keypoints_2d'] = z['pred_keypoints_2d'] * s
        if kf:
            # Läsningen är gjord i den kamerafria ramen (u_k = s*u + t). Tillbaka till originalets kamera: roten flyttas så att
            # projektionen blir u = (u_k - t)/s. Med Z' = s*Z och X' = X + Z*(c - t - s*c)/f per axel; kroppens form ändras inte.
            a = avb[int(f.stem)]; sk = a['skala']; t = np.array(a['forskjutning']); fl = float(z['focal_length']); c = np.array([540., 960.])
            X, Y, Zc = z['pred_cam_t'].astype(float)
            z['pred_cam_t'] = np.array([X + Zc * (c[0] - t[0] - sk * c[0]) / fl, Y + Zc * (c[1] - t[1] - sk * c[1]) / fl, sk * Zc], z['pred_cam_t'].dtype)
            z['pred_keypoints_2d'] = (z['pred_keypoints_2d'] - t) / sk
        np.savez(kropp / f'{i:04d}.npz', **z)
        kn = z['pred_keypoints_2d'][11:13]; syn[str(i)] = bool(all(0 <= x < 1080 and 0 <= y < 1920 for x, y in kn)); pal[str(i)] = True
    for i in range(N): syn.setdefault(str(i), False)
    (d / 'synlighet.json').write_text(json.dumps(syn)); (d / 'palitlig.json').write_text(json.dumps(pal))
    sek = d / 'sekvens_1.npz'
    if not sek.exists():
        r = subprocess.run([str(PY_SAM), str(ING / 'sekvens_stabil.py'), str(kropp), str(d / 'synlighet.json'), str(sek), str(N), str(fps), str(d / 'palitlig.json')],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        (d / 'sekvens.log').write_text(r.stdout + r.stderr, encoding='utf-8')
        if r.returncode: raise SystemExit('sekvens: ' + r.stderr[-1500:])
    plan = json.loads((DAG / 'plan.json').read_text(encoding='utf-8'))
    sc = next(x for x in plan['scener'] if x['id'] == 's1')
    for pm in sc['personer']: pm['rorelse'] = str(sek)
    plan.setdefault('beslut', []).append(f'0017 G/0021: S1:s rörelse ur den isolerade videon {v} (gennedbrytning), läst med samma läsare; plats, golv, kamera och stöd ur dagens plan.')
    pf = d / 'plan.json'; pf.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
    a, b = sc['ut']
    if not (d / 'scen.blend').exists():
        with open(d / 'blender.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', '--factory-startup', '-t', '8', '--python-exit-code', '1', '--python', str(ING / 'mhr_rig.py'), '--',
                            str(S1), plan['kallvideo'], '--plan', str(pf), '--ut', str(d), '--tillat-flaggad'], cwd=ROT, stdout=f, stderr=subprocess.STDOUT, check=True)
    if len(list((d / 'render').glob('f*.png'))) < b - a:
        (d / 'render').mkdir(exist_ok=True)
        with open(d / 'render.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', str(d / 'scen.blend'), '-o', str(d / 'render' / 'f####'), '-F', 'PNG', '-s', str(a), '-e', str(b - 1), '-a'],
                           cwd=ROT, stdout=f, stderr=subprocess.STDOUT, check=True)
    # film: original | dagens förvärld | ny kropp
    cap = cv2.VideoCapture(plan['kallvideo']); O = []
    for u in range(a, b):
        cap.set(cv2.CAP_PROP_POS_FRAMES, plan['kallrutor'][u]); ok, f = cap.read(); O.append(f)
    def last(p):
        im = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
        if im is None: return np.full((1920, 1080, 3), 128, np.uint8)
        if im.shape[2] == 4:
            al = im[..., 3:4] / 255.; im = (im[..., :3] * al + np.array([128, 128, 128]) * (1 - al)).astype(np.uint8)
        return im
    w, h = 360, 640; vw = cv2.VideoWriter(str(d / 'tre_bredvid.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), fps, (3 * w, h))
    for k, u in enumerate(range(a, b)):
        rad = [cv2.resize(O[k], (w, h)), cv2.resize(last(DAG / 'render' / f'f{u:04d}.png'), (w, h)), cv2.resize(last(d / 'render' / f'f{u:04d}.png'), (w, h))]
        for j, t in enumerate(('original', 'dagens forvarld', f'ny kropp ({v})')): cv2.putText(rad[j], t, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 0, 0), 2)
        cv2.putText(rad[0], str(u), (8, 48), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 2)
        vw.write(np.hstack(rad))
    vw.release()
    rutor = [10, 40, 70, 100, 130, 150]
    cv2.imwrite(str(d / 'tre_bredvid_rutor.jpg'), np.vstack([np.hstack([cv2.resize(O[u - a], (240, 427)), cv2.resize(last(DAG / 'render' / f'f{u:04d}.png'), (240, 427)),
                                                                     cv2.resize(last(d / 'render' / f'f{u:04d}.png'), (240, 427))]) for u in rutor[:3]] ) if False else
                np.hstack([np.vstack([cv2.resize(O[u - a], (180, 320)), cv2.resize(last(DAG / 'render' / f'f{u:04d}.png'), (180, 320)), cv2.resize(last(d / 'render' / f'f{u:04d}.png'), (180, 320))]) for u in rutor]))
    print(d / 'tre_bredvid.mp4')


if __name__ == '__main__': main()
