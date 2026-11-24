"""Mäter Wan-utfallen i genererat_klipp/ mot originalens SAM-läsning.
  python mat_klipp.py forbered   -> mat_klipp/alla.mp4 + jobb.json (alla klipp i en video, en Modal-körning)
  modal run ../ingest/modal_sam3db.py --klipp mat_klipp/alla.mp4 --jobb mat_klipp/jobb.json --ut mat_klipp/kropp --fokal 650
  python mat_klipp.py analys     -> mat_klipp/resultat.json + panel per klipp
Fokal 650 = originalets 1024 px gånger placeringsskalan 650/1024 (samma kamera, mindre bild på duken)."""
import json, sys, glob
from pathlib import Path
import cv2, numpy as np

HIT = Path(__file__).resolve().parent; UT = HIT / 'mat_klipp'; UT.mkdir(exist_ok=True)
ING = HIT.parent / 'ingest' / 'ut'
KLIPP = {'notanS1': 'notan-tagningar/S1', 'ravaraS5': 'b-tilltal-ravara-tagningar/S5', 'kennyS2': 'kand-kennysgelato-tagningar/S2',
         'serveringS2': 'a-sketch-servering-tagningar/S2'}

def last(k):
    T = ING / KLIPP[k]; M = json.loads((T / 'meta.json').read_text(encoding='utf-8'))
    tim = json.loads((HIT / 'in_klipp' / k / 'timing.json').read_text(encoding='utf-8'))
    return T, M, tim, json.loads((T / 'personer.json').read_text(encoding='utf-8'))

if sys.argv[1] == 'forbered':
    vw, jobb, index, g = None, [], {}, 0
    for k in KLIPP:
        raw = glob.glob(str(HIT / 'genererat_klipp' / k / '*_raw_16fps.mp4'))
        if not raw: print('saknas', k); continue
        T, M, tim, P = last(k); tr = tim['transform']; s_sp = 576 / M['bredd']
        cap = cv2.VideoCapture(raw[0]); gen = []
        while True:
            ok, f = cap.read()
            if not ok: break
            gen.append(f)
        n, fps = tim['source_frames'], tim['source_fps']
        if vw is None: vw = cv2.VideoWriter(str(UT / 'alla.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 30, (gen[0].shape[1], gen[0].shape[0]))
        index[k] = dict(start=g, n=n)
        for i in range(n):
            vw.write(gen[min(round(i * 16 / fps), len(gen) - 1)])
            for pid, d in P.items():
                b = d.get(str(i))
                if b is None: continue
                x0, y0, x1, y1 = [v * s_sp * tr['scale'] for v in b]
                x0 += tr['x0']; x1 += tr['x0']; y0 += tr['y0']; y1 += tr['y0']
                if y1 > tr['placed_height'] - 8: y1 = tr['canvas_height'] - 1   # rutan nådde bildkanten: låt den gå ned i den breddade ytan
                jobb.append([g + i, f'{k}__{pid}', [x0, y0, x1, y1]])
        g += n
    vw.release(); json.dump(jobb, open(UT / 'jobb.json', 'w')); json.dump(index, open(UT / 'index.json', 'w'))
    print('rutor', g, 'jobb', len(jobb))
else:
    index = json.load(open(UT / 'index.json')); res = {}
    for k, ix in index.items():
        T, M, tim, P = last(k); tr = tim['transform']; s_sp = 576 / M['bredd']
        for pid in P:
            drift, ben_g, ben_o, hojd, rot_g, rot_o = [], 0, 0, [], [], []
            for i in range(ix['n']):
                fg = HIT / 'mat_klipp' / 'kropp' / f'{k}__{pid}' / f'{ix["start"] + i:04d}.npz'; fo = T / 'kropp' / pid / f'{i:04d}.npz'
                if not (fg.exists() and fo.exists()): continue
                G, O = np.load(fg), np.load(fo)
                kg = (G['pred_keypoints_2d'][:21] - [tr['x0'], tr['y0']]) / tr['scale']; ko = O['pred_keypoints_2d'][:21] * s_sp
                drift.append(float(np.median(np.linalg.norm(kg[:9] - ko[:9], axis=1))))     # huvud + axlar/armbågar/händer
                kn = G['pred_keypoints_2d'][13:17]; ben_g += all(0 <= x < tr['canvas_width'] and 0 <= y < tr['canvas_height'] for x, y in kn)
                kn = O['pred_keypoints_2d'][13:17] / s_sp * s_sp; ben_o += all(0 <= x < M['bredd'] and 0 <= y < M['hojd'] for x, y in O['pred_keypoints_2d'][13:17])
                hojd.append(float(np.ptp(G['pred_vertices'][:, 1]))); rot_g.append(G['pred_cam_t']); rot_o.append(O['pred_cam_t'])
            if not drift: continue
            skak = lambda R: float(np.median(np.linalg.norm(np.diff(np.array(R), 2, axis=0), axis=1)) * 100) if len(R) > 2 else None
            res[f'{k}/{pid}'] = dict(rutor=len(drift), drift_px_median=round(float(np.median(drift)), 1), drift_px_p90=round(float(np.percentile(drift, 90)), 1),
                                    ben_synliga_genererat=f'{ben_g}/{len(drift)}', ben_synliga_original=f'{ben_o}/{len(drift)}',
                                    langd_m_median=round(float(np.median(hojd)), 3), skak_rot_cm_genererat=round(skak(rot_g), 2), skak_rot_cm_original=round(skak(rot_o), 2))
        # panel: mittruta, original | genererat med leder
        i = ix['n'] // 2; cap = cv2.VideoCapture(str(UT / 'alla.mp4')); cap.set(cv2.CAP_PROP_POS_FRAMES, ix['start'] + i); ok, gf = cap.read()
        src = cv2.VideoCapture(tim['source']); src.set(cv2.CAP_PROP_POS_FRAMES, i); ok2, of = src.read()
        for pid in P:
            fg = HIT / 'mat_klipp' / 'kropp' / f'{k}__{pid}' / f'{ix["start"] + i:04d}.npz'
            if fg.exists():
                for x, y in np.load(fg)['pred_keypoints_2d'][:21]: cv2.circle(gf, (int(x), int(y)), 4, (0, 0, 255), -1)
        if ok and ok2:
            of = cv2.resize(of, (int(of.shape[1] * gf.shape[0] / of.shape[0]), gf.shape[0]))
            cv2.imwrite(str(UT / f'panel_{k}.jpg'), np.hstack([of, gf]), [cv2.IMWRITE_JPEG_QUALITY, 82])
    json.dump(res, open(UT / 'resultat.json', 'w'), indent=1, ensure_ascii=False)
    for k, v in res.items(): print(k, v)
