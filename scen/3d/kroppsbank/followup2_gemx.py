"""Uppföljning del 2 (efter avbrott 17:21). Endast sparad geometri, ingen inferens.
Kör från projektroten:  scen/.venv/Scripts/python.exe scen/3d/kroppsbank/followup2_gemx.py <läge>
Lägen: configs, curves, videos.
"""
import argparse
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np
import followup_gemx as F

E = F.E
B = F.B
OUT = F.OUT


def candidates(s):
    c = ['gemx-raw', 'gemx-contact_ik']
    c += sorted(p.name for p in (B / 'ut/gemx_followup').glob(s['id'] + '__*') if p.is_dir())
    if s['id'].startswith('notan'):
        c += sorted(p.name for p in (B / 'ut/gemx_followup').glob('notan-whole__*') if (p / '1/raw_joints.npz').exists())
    return c


def pids_for(s, method):
    return s['pids'] if method.startswith('gemx-') or 'adapter' in method else ['1']


def box_iou(a, b):
    inter = np.maximum(0, np.minimum(a[2:], b[2:]) - np.maximum(a[:2], b[:2])).prod()
    return inter / ((a[2:] - a[:2]).prod() + (b[2:] - b[:2]).prod() - inter)


def box_stats(s, pid, method):
    """Modellens beskärningsrutor mot personer.json, och rutornas egen darr (px)."""
    p = B / 'ut/gemx_followup' / method / pid if '__' in method else B / 'ut/gemx' / s['id'] / pid
    c = np.load(p / 'conditions.npz')
    boxes = E.read_json(Path(s['folder']) / 'personer.json')[pid]
    start = F.offsets()[s['id']]['offset'] if method.startswith('notan-whole') else 0
    cb = c['boxes'][start:start + s['meta']['N']]
    ious = [box_iou(np.asarray(boxes[str(f)]), cb[f]) for f in range(len(cb)) if str(f) in boxes]
    centre = (cb[:, :2] + cb[:, 2:]) / 2
    size = (cb[:, 2:] - cb[:, :2]).mean(-1, keepdims=True)
    return dict(box_iou_median=float(np.median(ious)), box_centre_jitter_px=F.jitter(centre[:, None]),
                box_size_jitter_px=F.jitter(size[:, None]))


def configs(only=None):
    rows = [] if only is None else [r for r in E.read_json(OUT / 'configurations.json') if not r['method'].startswith(only)]
    for s in F.SHOTS:
        pb = E.read_json(Path(s['folder']) / 'personer.json')
        for pid in (s['pids'] if only is None else []):
            # personer.json-rutornas egen darr, samma mått (referens för adaptern).
            ids = sorted(int(f) for f in pb[pid])
            b = np.asarray([pb[pid][str(f)] for f in ids], float)
            rows.append(dict(shot=s['id'], person=pid, method='personer.json-rutor',
                             box_centre_jitter_px=F.jitter(((b[:, :2] + b[:, 2:]) / 2)[:, None]),
                             box_size_jitter_px=F.jitter((b[:, 2:] - b[:, :2]).mean(-1)[:, None, None])))
        for method in candidates(s):
            if only and not method.startswith(only): continue
            people = {pid: F.load(s, pid, method, mesh=True) for pid in pids_for(s, method)}
            sm, _ = F.silhouette_frames(s, people)
            for pid, d in people.items():
                r = dict(shot=s['id'], person=pid, method=method, **F.decompose(d['x'], d['K'], d['world']),
                         **F.kp_measure(s, pid, d), silhouette=sm[pid], **box_stats(s, pid, method))
                rows.append(r)
                print(s['id'], pid, method.ljust(28), 'J %.3f px %.2f djup %.3f pose %.3f rot %.3f IoU %.3f kp %.1f boxIoU %.3f boxjit %.2f' % (
                    r['camera_cm'], r['image_px'], r['depth_cm'], r['pose_cm'], r['root_cm'],
                    sm[pid]['iou_median'], r['kp_px'], r['box_iou_median'], r['box_centre_jitter_px']), flush=True)
            del people
        E.save_json(OUT / 'configurations.json', rows)
    choose(rows)


def choose(rows):
    """Bästa GEM-X per spår: högst silhuett-IoU bland konfigurationer vars kameradarr
    är högst 1,25 x den lägsta; därefter lägst kameradarr. Regeln är bedömd, inte ägarens krav."""
    best = {}
    for s in F.SHOTS:
        best[s['id']] = {}
        for pid in s['pids']:
            c = [r for r in rows if r['shot'] == s['id'] and r['person'] == pid and 'silhouette' in r]
            low = min(r['camera_cm'] for r in c)
            ok = [r for r in c if r['camera_cm'] <= 1.25 * low] or c
            pick = max(ok, key=lambda r: r['silhouette']['iou_median'])
            best[s['id']][pid] = pick['method']
    E.save_json(OUT / 'best.json', best)
    print('best', best)


def curves():
    best = E.read_json(OUT / 'best.json')
    rows = [r for r in E.read_json(OUT / 'curves_baseline.json') if r['method'] != 'best-gemx']
    for s in F.SHOTS:
        data = {pid: F.load(s, pid, best[s['id']][pid], mesh=True) for pid in s['pids']}
        for sigma in [0, .5, 1, 2, 3]:
            people = {pid: F.filter_data(d, sigma) for pid, d in data.items()}
            sm, sils = F.silhouette_frames(s, people)
            for pid, d in people.items():
                r = dict(shot=s['id'], person=pid, method='best-gemx', config=best[s['id']][pid], sigma_frames=sigma,
                         **F.decompose(d['x'], d['K']), **F.kp_measure(s, pid, d), silhouette=sm[pid],
                         bone_length_delta_p95_pct=d.get('bone_length_delta_p95_pct', 0))
                rows.append(r)
                print('curve', s['id'], pid, best[s['id']][pid], sigma, round(r['camera_cm'], 3),
                      round(sm[pid]['iou_median'], 3), round(r['kp_px'], 1), flush=True)
            if sigma in [0, 1, 2]:
                p = OUT / 'cache' / s['id']
                for pid, d in people.items():
                    np.savez_compressed(p / f'{pid}_best-gemx_{sigma}_display.npz', x=d['x'], K=d['K'],
                                        sil=np.array(sils[pid]), valid=d['valid'])
        E.save_json(OUT / 'curves.json', rows)


def videos(sam_sigma=1, gem_sigma=0):
    """Tre paneler: slutkedjan, rå SAM + Gauss sigma=1, bästa GEM-X. H.264 via ffmpeg."""
    best = E.read_json(OUT / 'best.json')
    for s in F.SHOTS[:3]:
        n = s['meta']['N']; w, h = s['meta']['bredd'], s['meta']['hojd']; fps = s['meta']['fps']
        PW, PH = 360, 640
        panels = [('slutsekvens', 0, 'DAGENS SLUTKEDJA'), ('sam-raw', sam_sigma, f'RÅ SAM + Gauss s={sam_sigma}'),
                  ('best-gemx', gem_sigma, 'GEM-X ' + best[s['id']]['1'].split('__')[-1] + (f' s={gem_sigma}' if gem_sigma else ''))]
        data = {m: {pid: dict(np.load(OUT / 'cache' / s['id'] / f'{pid}_{m}_{sig}_display.npz')) for pid in s['pids']}
                for m, sig, _ in panels}
        path = OUT / f'{s["id"]}_sida-vid-sida.mp4'
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                               '-s', f'{3 * PW}x{PH}', '-r', f'{fps:g}', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                               '-crf', '18', '-r', f'{fps:g}', str(path)], stdin=subprocess.PIPE)
        cap = cv2.VideoCapture(s['video'])
        stills = OUT / 'rutor' / s['id']; stills.mkdir(parents=True, exist_ok=True)
        pick = set(np.linspace(0, n - 1, 5).round().astype(int).tolist())
        for f in range(n):
            ok, src = cap.read(); assert ok
            source = cv2.resize(src, (PW, PH))
            tiles = []
            for m, sig, label in panels:
                tile = source.copy()
                for pid, d in data[m].items():
                    if not d['valid'][f]: continue
                    col = (20, 240, 250) if pid == '1' else (250, 210, 40)
                    mask = cv2.resize(d['sil'][f].astype(np.uint8), (PW, PH), interpolation=cv2.INTER_NEAREST)
                    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cv2.drawContours(tile, cs, -1, (60, 60, 255), 1, cv2.LINE_AA)
                    uv = F.project(d['x'][f:f + 1], d['K'][f:f + 1])[0] * [PW / w, PH / h]
                    for a, b in F.EDGE:
                        pts = uv[[a, b]]
                        if np.isfinite(pts).all() and np.abs(pts).max() < 20000:
                            cv2.line(tile, tuple(pts[0].round().astype(int)), tuple(pts[1].round().astype(int)), col, 2, cv2.LINE_AA)
                    if np.isfinite(uv[0]).all():
                        cv2.circle(tile, tuple(uv[0].round().astype(int)), 4, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.rectangle(tile, (0, 0), (PW, 28), (15, 15, 15), -1)
                txt = label.replace('Å', 'A')  # Hershey saknar å/ä/ö
                cv2.putText(tile, f'{txt}  f{f}', (6, 19), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1, cv2.LINE_AA)
                tiles.append(tile)
            frame = np.concatenate(tiles, axis=1)
            ff.stdin.write(frame.tobytes())
            if f in pick: cv2.imwrite(str(stills / f'f{f:03d}.png'), frame)
        cap.release(); ff.stdin.close(); assert ff.wait() == 0
        probe = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames',
                                         '-show_entries', 'stream=codec_name,r_frame_rate,nb_read_frames', '-of', 'json', str(path)])
        print('video', path, json.loads(probe)['streams'][0], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=['configs', 'whole', 'curves', 'videos']); a = p.parse_args()
    {'configs': configs, 'whole': lambda: configs('notan-whole'), 'curves': curves, 'videos': videos}[a.mode]()
