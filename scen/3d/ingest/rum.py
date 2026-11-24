"""Room geometry only: masked metric depth, COLMAP scale check, planes and furniture.

World coordinates match varld.npz (metres). gravity_rotation maps world to a Z-up
frame; object yaw is about that frame's Z, size = local X/Y/Z. Distances are
horizontal root-to-solid-footprint clearances (zero inside), never centre distances.
All inferred dimensions are estimates, with observed support and priors recorded.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import time

import cv2
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
VERSION = 1
STEP = 6


from metrisk import las as las_sekvens

def write_json(path, obj):
    path = Path(path); tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    tmp.replace(path)


def gravity(u):
    u = np.asarray(u) / np.linalg.norm(u); z = np.array([0., 0., 1.])
    v = np.cross(u, z); c = u @ z
    if c < -1 + 1e-8: return np.diag([1., -1., -1.])
    skew = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + skew + skew @ skew / (1 + c)


def stats(values):
    a = np.asarray(values); a = a[np.isfinite(a)]
    return {key: round(float(fn(a)), 4) if len(a) else None
            for key, fn in [('min', np.min), ('median', np.median), ('max', np.max)]}


def input_signature(clip, ut):
    clip = Path(clip); s = clip.stat()
    files = [ut / 'varld.npz', ut / 'masker.npy', ut / 'kamera.json', ut / 'meta.json',
             *sorted(ut.glob('sekvens_*.npz')), HERE / 'rum.py', HERE / 'rum_detect.py', HERE / 'modal_rum.py',
             HERE / 'rum_gemini.py', HERE / 'rum_objects.py']   # mhr_rig.py (Blender) importeras aldrig av rumssteget
    return dict(version=VERSION, source=str(clip.resolve()), source_bytes=s.st_size, source_mtime=s.st_mtime_ns,
                hashes={str(p.relative_to(ut)) if p.is_relative_to(ut) else p.name:
                        hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() or p.name != 'kamera.json' else None for p in files})


def cache_valid(clip, ut):
    p = ut / 'rum/cache.json'
    required = ['rum.json', 'rum.md', 'rum/cloud.npz', 'rum/overlay.jpg']
    if not p.exists() or not all((ut / f).exists() for f in required): return False
    try:
        fore = json.loads(p.read_text()); fore.get('hashes', {}).pop('mhr_rig.py', None)   # äldre cache hashade även mhr_rig.py
        return fore == input_signature(clip, ut)
    except (ValueError, OSError, AttributeError): return False


def sparse_points(ut, k):
    import pycolmap
    candidates = list((ut / 'colmap/sparse').glob('*/points3D.bin'))
    if not candidates: return np.empty((0, 3))
    recs = [pycolmap.Reconstruction(str(p.parent)) for p in candidates]
    rec = max(recs, key=lambda r: r.num_reg_images())
    return np.array([p.xyz for p in rec.points3D.values() if p.error < 2.0 and p.track.length() >= 3]).reshape(-1, 3) * k


def utan_parallax(V):
    return np.allclose(V['kam_C'], V['kam_C'][0], rtol=0, atol=1e-8)


def project(points, frame, V, focal, wh):
    cam = (np.asarray(points).reshape(-1, 3) - V['kam_C'][frame]) @ V['kam_R'][frame]
    denominator = np.where(np.abs(cam[:, 2:3]) < 1e-8, 1e-8, cam[:, 2:3])
    uv = cam[:, :2] / denominator * focal + np.array(wh) / 2
    return uv, cam[:, 2]


def fuse(ut, M, V, focal):
    # Den statiska reservkameran har inte COLMAP-punkternas koordinatsystem/skala.
    G = gravity(V['upp']); statisk = utan_parallax(V)
    sparse = np.empty((0, 3)) if statisk else sparse_points(ut, float(V['k']))
    scale_frames = []; frame_data = []
    for file in sorted((ut / 'rum/depth').glob('*.npz')):
        i = int(file.stem); d = np.load(file); depth = d['depth']; h, w = depth.shape
        # COLMAP point depths are ALREADY in metres, after exactly the same k as the camera.
        uv, z = project(sparse, i, V, focal * w / M['bredd'], (w, h))
        inside = (z > .1) & (uv[:, 0] >= 0) & (uv[:, 0] < w-1) & (uv[:, 1] >= 0) & (uv[:, 1] < h-1)
        pix = uv[inside].astype(int); observed = depth[pix[:, 1], pix[:, 0]]
        ratio = z[inside] / observed; ratio = ratio[np.isfinite(ratio) & (ratio > .05) & (ratio < 20)]
        if len(ratio) >= 10:
            scale_frames.append(dict(frame=i, n=len(ratio), ratio=float(np.median(ratio)),
                                     ratio_p10_p90=np.percentile(ratio, [10, 90]).tolist()))
        frame_data.append((i, depth, d['normal'].astype(np.float32)))
    if not frame_data: raise RuntimeError('No dense depth frames')
    sparse_factor = float(np.median([x['ratio'] for x in scale_frames])) if scale_frames else 1.
    # MoGe already returns metres. k belongs to the COLMAP translations / sparse points,
    # NOT to metric depth a second time. Do not shrink the room to an inconsistent sparse
    # scale (near-pure rotation can make that scale weakly constrained).
    factor = 1.
    scale_report = dict(colmap_k=float(V['k']), depth_to_pipeline_scale=factor,
                        sparse_matching_multiplier=sparse_factor,
                        disagreement_percent=100*(1/sparse_factor-1), frames=scale_frames,
                        method='median sparse metric z / MoGe metric z, equal weight per frame',
                        fusion='C_metric=k*C_colmap; X_world=C_metric+R*depth_metric*ray; depth is already metres',
                        verified=bool(scale_frames))
    if not scale_frames:
        scale_report.update(sparse_matching_multiplier=None, disagreement_percent=None,
                            reason='Ingen kameraparallax' if statisk else 'För få användbara COLMAP-punkter',
                            method='Monokulärt MoGe-djup; metrisk skala antagen, inte verifierad mot COLMAP',
                            fusion='X_world=kam_C+kam_R*depth_metric*ray, kamera från varld.npz',
                            antaganden=['MoGe-modellens meterskala behålls (djupfaktor 1)'])
    xyz, normals, pixels, frames = [], [], [], []
    for i, depth, normal in frame_data:
        h, w = depth.shape; yy, xx = np.mgrid[0:h:3, 0:w:3]
        z = depth[yy, xx] * factor
        valid = np.isfinite(z); xx, yy, z = xx[valid], yy[valid], z[valid]
        f = focal*w/M['bredd']
        pc = np.c_[(xx+.5-w/2)/f*z, (yy+.5-h/2)/f*z, z]
        world = pc @ V['kam_R'][i].T + V['kam_C'][i]
        xyz.append(world); normals.append(normal[yy, xx] @ V['kam_R'][i].T @ G.T)
        pixels.append(np.c_[(xx+.5)*M['bredd']/w, (yy+.5)*M['hojd']/h])
        frames.append(np.full(len(xx), i, np.int32))
    world = np.concatenate(xyz); aligned = world @ G.T
    source = dict(world=world.astype(np.float32), xyz=aligned.astype(np.float32),
                  normals=np.concatenate(normals).astype(np.float32), uv=np.concatenate(pixels).astype(np.float32),
                  frames=np.concatenate(frames))
    # Voxel fusion keeps geometry bounded without bias towards a frequently observed frame.
    vox = np.floor(aligned/.025).astype(np.int32)
    _, inv, counts = np.unique(vox, axis=0, return_inverse=True, return_counts=True)
    fused = np.column_stack([np.bincount(inv, weights=aligned[:, j])/counts for j in range(3)])
    nrm = np.column_stack([np.bincount(inv, weights=source['normals'][:, j])/counts for j in range(3)])
    np.savez_compressed(ut/'rum/cloud.npz', points=(fused@G).astype(np.float32), normals=(nrm@G).astype(np.float32), observations=counts)
    return source, fused, nrm, scale_report


def plane_ransac(points, kind, reference=None, threshold=.045, iterations=450):
    """Constrained RANSAC followed by TLS; return measured plane and its inliers."""
    if len(points) < 60: return None
    rng = np.random.default_rng(42); sample = points[rng.choice(len(points), min(len(points), 14000), replace=False)]
    best = None; best_n = 0
    for _ in range(iterations):
        a, b, c = sample[rng.choice(len(sample), 3, replace=False)]
        n = np.cross(b-a, c-a); length = np.linalg.norm(n)
        if length < 1e-6: continue
        n /= length
        if kind == 'horizontal' and abs(n[2]) < np.cos(np.deg2rad(10)): continue
        if kind == 'vertical' and abs(n[2]) > np.sin(np.deg2rad(10)): continue
        if kind == 'vertical': n[2] = 0; n /= np.linalg.norm(n)
        elif n[2] < 0: n = -n
        d = float(n @ a)
        if reference is not None and abs(d/n[2]-reference) > .45: continue
        inliers = np.abs(sample@n-d) < threshold
        if inliers.sum() > best_n: best_n = int(inliers.sum()); best = (n.copy(), d)
    if best is None or best_n < 60: return None
    n, d = best
    for _ in range(3):
        inside = np.abs(points@n-d) < threshold; p = points[inside]
        if kind == 'vertical':
            _, _, vt = np.linalg.svd(p[:, :2]-p[:, :2].mean(0), full_matrices=False)
            n = np.r_[vt[-1], 0.]
        else:
            _, _, vt = np.linalg.svd(p-p.mean(0), full_matrices=False); n = vt[-1]
            if n[2] < 0: n = -n
            if n[2] < np.cos(np.deg2rad(10)): return None
        d = float(n@p.mean(0))
    return n, d, np.abs(points@n-d)<threshold


def room_planes(points, normals, V, anchors=None):
    G = gravity(V['upp']); floor_h = float(V['golv_h'])
    floor_candidates = points[(np.abs(points[:, 2]-floor_h)<.45) & (np.abs(normals[:, 2])>.75)]
    fitted = plane_ransac(floor_candidates, 'horizontal', reference=floor_h)
    floor = dict(height=floor_h, normal=V['upp'].tolist(), source='golv_h constraint', measured_height=None,
                 difference_cm=None, normal_angle_deg=None, support=0, verified=False,
                 rendered_difference_cm=0., rendered_normal_angle_deg=0., rendered_agrees=True)
    if fitted and fitted[2].sum() >= 600 and abs(fitted[1]/fitted[0][2]-floor_h)<.45:
        n, d, inside = fitted; measured = float(d/n[2])
        floor.update(measured_height=measured, difference_cm=100*(measured-floor_h),
                     measured_normal=(n@G).tolist(), normal_angle_deg=float(np.degrees(np.arccos(n[2]))),
                     support=int(inside.sum()), verified=abs(measured-floor_h)<=.05)
    # Vertical surfaces require height coverage: small cabinet fronts are not room walls.
    remaining = points[(points[:, 2] > floor_h+.8) & (np.abs(normals[:, 2]) < .3)]
    walls = []; cam = V['kam_C']@G.T
    for _ in range(24):
        fit = plane_ransac(remaining, 'vertical', threshold=.07)
        if not fit: break
        n, d, inside = fit; p = remaining[inside]; remaining = remaining[~inside]
        tangent = np.array([-n[1], n[0], 0.]); ts = p@tangent
        lo, hi = np.percentile(ts, [2, 98]); zs = np.percentile(p[:, 2], [2, 98])
        if hi-lo < .8 or zs[1]-zs[0] < .9 or len(p)<180: continue
        if cam.mean(0)@n < d: n=-n; d=-d; tangent=-tangent; lo, hi=-hi, -lo
        if np.min(cam@n-d)<.25: continue
        if anchors is not None and np.percentile(anchors@n-d,1)<.25: continue
        if any(abs(np.dot(n, w['_n']))>.97 and abs(abs(d)-abs(w['distance']))<.8 for w in walls): continue
        centre = n*d + tangent*(lo+hi)/2; centre[2]=(zs[0]+zs[1])/2
        walls.append(dict(id=f'wall_{len(walls)+1}', normal=(n@G).tolist(), distance=d,
                          centre=(centre@G).tolist(), tangent=(tangent@G).tolist(),
                          width=float(hi-lo), height=float(zs[1]-zs[0]), support=len(p),
                          camera_path_m=stats(np.abs(cam@n-d)), _n=n))
        if len(walls)==4: break
    for w in walls: w.pop('_n')
    return floor, walls


def oriented_rectangle(points):
    xy = np.asarray(points)[:, :2].astype(np.float32)
    # Quantile envelope after PCA is more robust than an untrimmed min-area rectangle.
    _, _, vt = np.linalg.svd(xy-np.median(xy, 0), full_matrices=False)
    axis = vt[0]; yaw = np.arctan2(axis[1], axis[0])
    B = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])
    local = xy@B; low, high = np.percentile(local, [2, 98], axis=0)
    return (low+high)/2@B.T, high-low, float(yaw)


def object_distance(roots, obj, G):
    centre = np.array(obj['centre'])@G.T; yaw=obj['yaw']
    B = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])
    delta=(roots[:, :2]-centre[:2])@B
    return np.linalg.norm(np.maximum(np.abs(delta)-np.array(obj['size'][:2])/2, 0), axis=1)


def distances(ut, V, objects, walls):
    G=gravity(V['upp']); result={}; F=np.diag([1., -1., -1.])
    for file in sorted(ut.glob('sekvens_*.npz')):
        pid=file.stem[8:]; S=las_sekvens(file); frames=np.flatnonzero(S['inom'])
        rootcam=S['pose'][:, 1, :3]/100@F + S['cam_t']
        root=V['kam_C']+np.einsum('nij,nj->ni', V['kam_R'], rootcam)
        wd={w['id']: np.abs(root@w['normal']-w['distance']) for w in walls}
        od={o['id']:object_distance(root@G.T,o,G) for o in objects}
        nearest=np.min(list(wd.values()),axis=0) if wd else np.full(len(root),np.nan)
        result[pid]=dict(reference='MHR root projected to floor; horizontal clearance to object footprint',
                        frames=[dict(frame=int(i), nearest_wall_m=float(nearest[i]) if wd else None,
                                     walls_m={k:float(v[i]) for k,v in wd.items()}, objects_m={k:float(v[i]) for k,v in od.items()}) for i in frames],
                        ranges=dict(nearest_wall_m=stats(nearest[frames]),walls_m={k:stats(v[frames]) for k,v in wd.items()},
                                    objects_m={k:stats(v[frames]) for k,v in od.items()}))
    return result


def corners(obj, G):
    size=np.asarray(obj['size']); yaw=obj['yaw']; B=np.array([[np.cos(yaw),-np.sin(yaw),0],[np.sin(yaw),np.cos(yaw),0],[0,0,1.]])
    signs=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])
    local=signs*size/2
    if obj.get('top_slope'): local[4:,2]+=local[4:,0]*obj['top_slope']
    return local@B.T@G+obj['centre']


def overlay(clip, ut, M, V, focal, objects):
    G=gravity(V['upp']); cap=cv2.VideoCapture(str(clip)); images=[]
    for frame in np.linspace(6,M['N']-7,6).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES,int(frame)); ok,img=cap.read()
        if not ok: continue
        for o in objects:
            uv,z=project(corners(o,G),frame,V,focal,(M['bredd'],M['hojd']))
            for a,b in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:
                if min(z[a],z[b])>.05:
                    cv2.line(img,tuple(np.clip(uv[a],-10000,10000).astype(int)),tuple(np.clip(uv[b],-10000,10000).astype(int)),(0,220,255),3)
        cv2.putText(img,str(frame),(20,45),0,1.2,(0,255,255),3)
        images.append(cv2.resize(img,(270,480)))
    cap.release(); cv2.imwrite(str(ut/'rum/overlay.jpg'),np.hstack(images))


def markdown(room):
    f=room['floor']; text=['# Room estimates (metres)','',
        'Distances: horizontal person-root clearance to object footprint; walls: perpendicular to fitted plane.', '',
        f"Floor used: {f['height']:.3f} m; rendered difference from golv_h: 0.00 cm. Independent depth difference: {f['difference_cm']} cm; verified: {f['verified']}.",
        f"MoGe / COLMAP metric disagreement: {room['scale']['disagreement_percent']:.1f}%; depth multiplier: {room['scale']['depth_to_pipeline_scale']:.4f}." if room['scale']['disagreement_percent'] is not None else room['scale']['reason'] + ': ' + room['scale']['method'], '',
        '| Object | Size X × Y × Z (m) | Support frames |','|---|---:|---:|']
    text += [f"| {o['id']} ({o['label']}) | {' × '.join(f'{v:.2f}' for v in o['size'])} | {len(o['frames'])} |" for o in room['objects']]
    text += ['', '| Wall | Camera path min / median / max (m) |','|---|---:|']
    text += [f"| {w['id']} | {' / '.join(str(x) for x in w['camera_path_m'].values())} |" for w in room['walls']]
    text += ['', '| Person | Target | Min / median / max (m) |','|---|---|---:|']
    for pid,p in room['people'].items():
        for target, r in {**p['ranges']['walls_m'], **p['ranges']['objects_m']}.items():
            text.append(f"| {pid} | {target} | {' / '.join(str(v) for v in r.values())} |")
    text += ['', 'Model licences: ../../RUM-LICENSES.md. Scale, incomplete surfaces and object support are retained in rum.json.', '']
    if room.get('antaganden'): text += ['Antaganden: ' + '; '.join(room['antaganden']), room.get('reason', '')]
    return '\n'.join(text)


def steg_rum(clip, ut, M):
    from rum_gemini import detect
    from rum_objects import fit_objects
    ut=Path(ut); (ut/'rum').mkdir(exist_ok=True)
    V=dict(np.load(ut/'varld.npz')); seqfile=next(ut.glob('sekvens_*.npz'), None)
    focal=float(np.load(seqfile)['fokal']) if seqfile else max(M['bredd'], M['hojd'])
    # Source/mask/intrinsic changes invalidate expensive inference independently of geometry.
    sig=input_signature(clip,ut)
    raw_signature=dict(source=sig['source'],source_bytes=sig['source_bytes'],source_mtime=sig['source_mtime'],
                       masks=sig['hashes']['masker.npy'],focal=focal,step=STEP,width=M['bredd'],height=M['hojd'])
    manifest=ut/'rum/inference_cache.json'
    if manifest.exists() and json.loads(manifest.read_text())!=raw_signature:
        root=(ut/'rum').resolve()
        old = json.loads(manifest.read_text())
        source_changed = any(old.get(k) != raw_signature.get(k) for k in ('source', 'source_bytes', 'source_mtime'))
        for name in (['depth','gemini','detections_gemini.json','detections.json'] if source_changed else ['depth']):
            p=(root/name).resolve()
            if not p.is_relative_to(root): raise RuntimeError('Unsafe inference cache path')
            from sakra_filer import arkivera
            arkivera(p)
    write_json(manifest,raw_signature)
    expected=[ut/f'rum/depth/{i:04d}.npz' for i in range(0,M['N'],STEP)]
    if not all(p.exists() for p in expected):
        cmd=[str(HERE.parents[1]/'.venv/Scripts/modal.exe'),'run',str(HERE/'modal_rum.py'),'--klipp',str(clip),
             '--ut',str(ut/'rum/depth'),'--fokal',str(focal)]
        with (ut/'rum/modal.log').open('w',encoding='utf-8') as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    # Geometriförändring kräver nytt djup men inte nya bilddetektioner.
    # Nätanrop för Gemini är uttryckligt avstängbara, även inne i rumsteget.
    if os.environ.get('HAGEN_NO_GEMINI', '1') == '1' and not (ut / 'rum/detections_gemini.json').exists():
        det=[]
    elif os.environ.get('HAGEN_NO_GEMINI', '1') == '1':
        det=json.loads((ut / 'rum/detections_gemini.json').read_text())
    else: det=detect(clip,ut)
    source,points,normals,scale=fuse(ut,M,V,focal)
    roots=[];G=gravity(V['upp'])
    for file in ut.glob('sekvens_*.npz'):
        S=las_sekvens(file);cam=S['pose'][:,1,:3]/100@np.diag([1.,-1.,-1.])+S['cam_t']
        roots.append((V['kam_C']+np.einsum('nij,nj->ni',V['kam_R'],cam))[S['inom']]@G.T)
    floor,walls=room_planes(points,normals,V,np.concatenate(roots) if roots else None)
    objects=fit_objects(clip,ut,M,V,source,det)
    room=dict(version=VERSION,coordinates='COLMAP world, metres; yaw in gravity_rotation frame, radians',
              gravity_rotation=gravity(V['upp']).tolist(),floor=floor,walls=walls,objects=objects,scale=scale,
              people=distances(ut,V,objects,walls),depth_frames=len(expected),cloud_points=len(points),
              licences='../../RUM-LICENSES.md')
    if utan_parallax(V):
        T=json.loads((ut/'tider.json').read_text()) if (ut/'tider.json').exists() else {}
        room.update(coordinates='varld.npz, statisk reservkamera; yaw i gravity_rotation, radianer',
                    method='Monokulärt djup, flera bildrutor från samma vy; ingen triangulering',
                    antaganden=['Metrisk rumsskala och ytor från MoGe, inte uppmätta med parallax',
                                'Kameraposen från varld.npz; världsskala k=1 är en konvention',
                                'Uppåtriktning från kropparnas ryggar',
                                'Fokal från sekvens; COLMAP-skattning med få rutor eller antagen max(bredd, höjd)'])
        floor['source']=T.get('golv',{}).get('kalla','golv_h från varld.npz')
        room['antaganden'].append('Golv: ' + floor['source'])
        for item in walls + objects:
            item['antagen']=True
            item['reason']='Enkelvyskattning från modelldjup; mått och avstånd saknar parallaxverifiering'
            if 'source' in item: item['source']=item['source'].replace('multiview', 'single-view').replace('multi-view', 'single-view')
        if not walls and not objects:
            room['reason']='Ingen stödd rumsgeometri i monokulärt djup/detekteringar; kameraparallax saknas'
    room['kunskap'] = dict(status='modellbedomd' if walls or objects else 'saknas', orsak='Ytor ur modelldjup och befintliga detektioner.' if walls or objects else 'Inga stödda ytor. Tom utdata betyder okänt rum, inte tom lokal.')
    overlay(clip,ut,M,V,focal,objects)
    write_json(ut/'rum.json',room); (ut/'rum.md').write_text(markdown(room),encoding='utf-8')
    write_json(ut/'rum/cache.json',input_signature(clip,ut))
    return dict(depth_frames=len(expected),cloud_points=len(points),walls=len(walls),objects=len(objects),
                floor_difference_cm=floor['difference_cm'],depth_scale_disagreement_percent=scale['disagreement_percent'],
                **({k:room[k] for k in ('method','antaganden','reason') if k in room} if utan_parallax(V) else {}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('clip'); parser.add_argument('ut'); a=parser.parse_args()
    ut=Path(a.ut); t=time.perf_counter()
    print(steg_rum(Path(a.clip),ut,json.loads((ut/'meta.json').read_text())))
    print(f'{time.perf_counter()-t:.1f} s')
