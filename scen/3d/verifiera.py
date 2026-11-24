"""Phase 2 actual WebGL render + YOLO person-mask verification, CPU/offline.
Run: scen/.venv/Scripts/python.exe -B scen/3d/verifiera.py [--quick]
"""
import os,json,time,threading,subprocess,socket,argparse
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from fas1_geometry import points
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'verifiering/fas2';OUT.mkdir(parents=True,exist_ok=True)
os.environ['YOLO_CONFIG_DIR']=str(ROOT/'cache/ultralytics')
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,j):(ROOT/p).write_text(json.dumps(j,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
    def log_message(self,*a):pass
def render(jobs,smoke=False):
    p=port();server=ThreadingHTTPServer(('127.0.0.1',p),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    write('verifiering/fas2/jobs.json',jobs)
    try:subprocess.run(['node',str(ROOT/'capture.mjs'),f'http://127.0.0.1:{p}/index.html#t=0&capture=1',str(OUT),str(OUT/'jobs.json'),str(port())],check=True,env={**os.environ,'SCEN_SMOKE':'1' if smoke else '0'})
    finally:server.shutdown()
    return read('verifiering/fas2/capture-results.json')

def sources(indices,frames):
    from ultralytics import YOLO
    model=None;cap=cv2.VideoCapture(str(ROOT.parent/'klipp/d-dialog-notan.mp4'));info={}
    for n in indices:
        prefix=f"{frames[n]['shot']}-{n:03d}";sp=OUT/f'{prefix}-source.jpg';mp=OUT/f'{prefix}-source-mask.png';jp=OUT/f'{prefix}-seg.json'
        if sp.exists() and mp.exists() and jp.exists():info[n]=json.loads(jp.read_text());continue
        cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,im=cap.read();assert ok;cv2.imwrite(str(sp),im)
        if model is None:model=YOLO(str(ROOT.parent/'py/modeller/yolo11n-seg.pt'))
        result=model.predict(im,imgsz=1024,conf=.15,classes=[0],retina_masks=True,verbose=False,device='cpu')[0]
        nose=np.array(frames[n]['pose']['image'][0][:2])*[576,1024];boxes=result.boxes.xyxy.cpu().numpy()
        scores=[]
        for b in boxes:
            inside=b[0]<=nose[0]<=b[2] and b[1]<=nose[1]<=b[3]
            scores.append((1000 if inside else 0)-np.linalg.norm((b[:2]+b[2:])/2-nose))
        k=int(np.argmax(scores));mask=(result.masks.data[k].cpu().numpy()>.5).astype(np.uint8)*255;cv2.imwrite(str(mp),mask)
        info[n]=dict(box=boxes[k].tolist(),confidence=float(result.boxes.conf[k]),person_count=len(boxes),nose_inside=bool(scores[k]>0),selection='Contains tracked nose, nearest box center; no mask tuning')
        jp.write_text(json.dumps(info[n],indent=2))
    cap.release();return info

def annotate(im,text):
    im=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)) if isinstance(im,np.ndarray) else im
    im=im.copy();d=ImageDraw.Draw(im);d.rectangle([0,0,im.width,34],fill='#17212b');d.text((9,8),text,fill='white');return im

def score(capture,frames,seg):
    by={};metrics=[]
    for r in capture['results']:
        if r.get('file') and not r.get('mask') and not r.get('orbit') and not r.get('catalog') and not r.get('mouth') and not r.get('ui'):by[(r['data']['index'],r.get('variant','procedural'))]=r
    for (n,variant),r in by.items():
        f=frames[n];prefix=f"{f['shot']}-{n:03d}";normal=OUT/r['file'];maskpath=OUT/f'{prefix}-{variant}-mask.png'
        if not maskpath.exists():continue
        source=cv2.imread(str(OUT/f'{prefix}-source.jpg'));rendered=cv2.imread(str(normal));mask=cv2.imread(str(maskpath),0)>127;truth=cv2.imread(str(OUT/f'{prefix}-source-mask.png'),0)>127
        intersection=np.logical_and(mask,truth).sum();union=np.logical_or(mask,truth).sum();iou=float(intersection/union)
        _,uv,ids=points(f);projected=r['data']['joints'];errs=[];perjoint=[]
        for j,xy in zip(ids,uv):
            if projected[j] is not None:
                e=float(np.linalg.norm(np.array(projected[j][:2])-xy));errs.append(e);perjoint.append(dict(joint=int(j),error_px=e,source=xy.tolist(),rendered=projected[j][:2]))
        metric=dict(shot=f['shot'],frame=n,t=n/30,variant=variant,joint_median_px=float(np.median(errs)),joint_median_H=float(np.median(errs)/1024),iou=iou,source_mask_pixels=int(truth.sum()),render_mask_pixels=int(mask.sum()),intersection=int(intersection),union=int(union),joints=perjoint,segmentation=seg[n],triangles=r['data']['triangles'],render_seconds=r['seconds'],mouthOpen=r['data']['mouthOpen'])
        metrics.append(metric)
        overlay=(source*.48+rendered*.52).astype(np.uint8)
        contours,_=cv2.findContours(truth.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(overlay,contours,-1,(50,220,70),2)
        contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(overlay,contours,-1,(220,70,220),2)
        for j in perjoint:
            a=tuple(np.rint(j['source']).astype(int));b=tuple(np.rint(j['rendered']).astype(int));cv2.line(overlay,a,b,(0,210,255),1);cv2.circle(overlay,b,3,(255,0,255),-1)
        sheet=Image.new('RGB',(576*3,1024));
        for i,(im,label) in enumerate([(source,f'{prefix} SOURCE'),(rendered,variant.upper()),(overlay,f"IoU {iou:.3f} | joints {np.median(errs):.1f}px / {np.median(errs)/1024:.4f}H")]):sheet.paste(annotate(im,label),(576*i,0))
        sheet.save(OUT/f'{prefix}-{variant}-comparison.jpg',quality=90)
    shots=[]
    for variant in ['procedural','vrm']:
        for sid in [f'S{i}' for i in range(1,8)]:
            rows=[m for m in metrics if m['shot']==sid and m['variant']==variant]
            if not rows:continue
            errors=[j['error_px'] for r in rows for j in r['joints']]
            shots.append(dict(shot=sid,variant=variant,joint_median_px=float(np.median(errors)),joint_median_H=float(np.median(errors)/1024),iou_mean=float(np.mean([m['iou'] for m in rows])),iou_min=min(m['iou'] for m in rows),iou_per_frame=[m['iou'] for m in rows],frames=[m['frame'] for m in rows],joints_pass=bool(np.median(errors)<=51.2),silhouette_pass_all_frames=all(m['iou']>=.5 for m in rows)))
            sheet=Image.new('RGB',(864,512*len(rows)))
            for i,m in enumerate(rows):
                p=OUT/f"{sid}-{m['frame']:03d}-{variant}-comparison.jpg";sheet.paste(Image.open(p).resize((864,512)),(0,i*512))
            sheet.save(OUT/f'{sid}-{variant}.jpg',quality=92)
    write('data/verification-2.json',dict(shots=shots,frames=metrics,smoke=capture['smoke'],browser_errors=capture['errors'],external_requests=capture['externalRequests']))
    for s in shots:print(s['variant'],s['shot'],round(s['joint_median_px'],2),round(s['iou_mean'],3),[round(v,3) for v in s['iou_per_frame']])
    # Overview: source / render / overlay, one row per shot.
    for variant in ['procedural','vrm']:
        rows=[m for m in metrics if m['variant']==variant];sheet=Image.new('RGB',(864,512*len(set(m['shot'] for m in rows))))
        for i,sid in enumerate(dict.fromkeys(m['shot'] for m in rows)):
            ms=[m for m in rows if m['shot']==sid];m=ms[len(ms)//2];sheet.paste(Image.open(OUT/f"{sid}-{m['frame']:03d}-{variant}-comparison.jpg").resize((864,512)),(0,i*512))
        if rows:sheet.save(OUT/f'fas2-{variant}.jpg',quality=92)
    return shots

def extra_checks(capture,frames):
    rows=[r for r in capture['results'] if r.get('temporal')];metrics={}
    for sid in [f'S{i}' for i in range(1,8)]:
        rs=[r for r in rows if r['data']['shot']==sid];errors=[];apertures=[];jaw=[]
        for r in rs:
            f=frames[r['data']['index']];jaw.append(r['data']['mouthOpen']);apertures.append(r['data']['mouthAperture_m'])
            for h in f['hands']:
                j=15 if h['side']=='Left' else 16;uv=np.array(h['image'][0][:2])*[576,1024];errors.append(float(np.linalg.norm(uv-np.array(r['data']['joints'][j][:2]))))
        if rs:metrics[sid]=dict(rendered_frames=len(rs),measured_hands=len(errors),hand_wrist_median_px=float(np.median(errors)) if errors else None,jaw_range=[min(jaw),max(jaw)],mouth_aperture_m=[min(apertures),max(apertures)])
    write('data/temporal-verification-2.json',metrics)
    mouthjobs=[r for r in capture['results'] if r.get('mouth')]
    if mouthjobs:
        sheet=Image.new('RGB',(640,240*6),'#17212b');row=0
        for sid in ['S1','S2','S3','S5','S6','S7']:
            rs=[r for r in mouthjobs if r['data']['shot']==sid]
            for col,r in enumerate(rs):
                im=Image.open(OUT/r['file']);xy=r['data']['joints'][0];half=110 if sid!='S7' else 55;im=im.crop((int(xy[0]-half),int(xy[1]-half*1.25),int(xy[0]+half),int(xy[1]+half*.75))).resize((240,240))
                sheet.paste(im,(col*320,row*240));ImageDraw.Draw(sheet).text((col*320+4,row*240+8),f"{sid} {r['mouth']} jaw {r['data']['mouthOpen']:.3f}",fill='white')
            row+=1
        sheet.save(OUT/'mouths.jpg',quality=92)
    cat=next((r for r in capture['results'] if r.get('catalog')),None)
    if cat:
        im=Image.open(OUT/cat['file']);d=ImageDraw.Draw(im)
        for label in cat['data']['labels']:d.text(tuple(label['uv']),label['type'],fill='#202630',anchor='mm')
        im.save(OUT/cat['file'])

def report():
    import hashlib
    v=read('data/verification-2.json');temporal=read('data/temporal-verification-2.json');runtime=read('data/runtime-2.json');prepare=read('data/prepare-2.json');anchors=read('data/hand-anchor-2.json');spec=read('scen3d.json')
    proc=[s for s in v['shots'] if s['variant']=='procedural'];rig=[s for s in v['shots'] if s['variant']=='vrm']
    numerical=all(s['joints_pass'] and s['silhouette_pass_all_frames'] for s in proc if s['shot']!='S7')
    status=dict(phase=2,numeric_S1_S6_pass=numerical,all_18_silhouettes_pass=all(s['silhouette_pass_all_frames'] for s in proc[:6]),gestures_S1_S3='measured and rendered; source/overlay sheets and temporal wrist audit',gestures_S6='unverifiable: zero detected hands, relaxed fallback',mouths='measured jawOpen drives geometry; S7 amplitude very small',S7='distant B, two empty table meshes and foreground can; seated legs are inferred',phase3_started=False,layout_equals_phase1b=(ROOT/'data/layout.json').read_bytes()==(ROOT/'data/layout-1b.json').read_bytes())
    write('data/phase2-status.json',status)
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['data/layout.json','data/sparning.json','scen3d.json','data/motion-2.json','index.html','player.js','meshes.js','rigged.js','fas2.py','verifiera.py','capture.mjs']};write('data/provenance-2.json',dict(hashes=hashes,source_clip='../klipp/d-dialog-notan.mp4',dependencies='vendor/manifest.json',model_licenses='modeller/licenses-vrm.json'))
    lines=['# Phase 2 — rendered reconstruction and verification','',
      f'Built the real 3D set, three rounded procedural actors, editable scene JSON and offline player. **S1–S6 numeric acceptance: {"PASS" if numerical else "FAIL"}.** S6 hand-gesture fidelity cannot be verified because the input contains no detected hands. S7 mouth movement is weak. Phase 3 has not been started.','',
      '## Measured results','',
      '576 × 1024 captures, actual Three.js WebGL rendering in headless Chrome/SwiftShader. Three frames per shot: start, middle, last frame before the cut. Joint error is the pooled median of visible anatomical joint centers on the rendered body versus the source MediaPipe landmarks, divided by 1024. Nose/ears are head mesh anchors; fingertips are rendered finger joints. The visibility mask is the Phase 1b mask (confidence ≥ .65; seated wrist/tips require independent detected hands). No image-space silhouette warp is used.','',
      'YOLO11n-seg, 1024 input, person class, CPU, retina masks. The main person is selected by containing the tracked nose and nearest box center; detection confidence and masks are saved per frame. IoU uses the visible main-actor render, including set/prop occlusion, against this automatic source mask. This is detector agreement, not manually labeled ground truth. We apply the 0.5 limit to **every** sampled S1–S6 frame, stricter than a shot mean.','',
      '| Shot | Frames | Median joint px | Error / H | IoU start / middle / end | Mean IoU |','|---|---|---:|---:|---|---:|']
    for s in proc:lines.append(f"| {s['shot']} | {', '.join(map(str,s['frames']))} | {s['joint_median_px']:.2f} | {s['joint_median_H']:.5f} | {' / '.join(f'{x:.3f}' for x in s['iou_per_frame'])} | {s['iou_mean']:.3f} |")
    bad=[f"{m['shot']} f{m['frame']} ({m['joint_median_px']:.1f}px)" for m in v['frames'] if m['variant']=='procedural' and m['shot']!='S7' and m['joint_median_px']>51.2]
    lines+=['',f"The criterion is a per-shot median, not a bound on each frame or joint. Sample frame medians over 51.2px: {', '.join(bad) or 'none'}. Individual elbows/fingers can deviate more. S7 is reported but is outside the numeric S1–S6 criterion; its inferred legs reduce whole-person IoU.",'',
      '## Alternatives and decisions','',
      '- **Procedural versus VRM:** both run locally, use the same smoothed motion, cameras and hand-wrist fusion, and are captured at identical times. VRM uses pinned `@pixiv/three-vrm@3.3.3` and `kalidokit@1.1.5`; Three.js is pinned to `0.170.0`. The default is procedural: measured positions remain controllable, A’s forward lean and gestures read better, and costume/hair match the roles. The CC0 sample VRMs have different proportions, blue hair and school clothing, which also affect IoU. This is a comparison of these implementations/assets, not a claim that VRM cannot fit the clip.','',
      '- **Rig coordinate alternatives:** tested unchanged Kalidokit, unmirrored left/right plus reflected Y/Z rotations, X/Z basis inversion, and both. The unmirrored mapping gives the lowest mean midpoint joint error across seven shots and is retained. The camera-to-head basis was separately corrected so the model faces the camera. Candidate numbers are in `data/vrm-retarget-candidates-2.json`. The remaining solver does not reconstruct A’s measured forward lean reliably; fixed rig lengths and clamped rotations produce misplaced arms.','',
      '| Shot | Procedural px / IoU mean | VRM px / IoU mean |','|---|---:|---:|']
    for a,b in zip(proc,rig):lines.append(f"| {a['shot']} | {a['joint_median_px']:.2f} / {a['iou_mean']:.3f} | {b['joint_median_px']:.2f} / {b['iou_mean']:.3f} |")
    lines+=['',
      '- **Body shape:** compared the initial rounded-box torso with an ellipsoid torso, anatomically higher ears/cranium, continuous long hair and narrower B sleeves. The latter is the default. Initial midpoint data/image are preserved in `data/verification-2-baseline.json` and `verifiering/fas2/baseline-procedural.jpg`. This is a stylized volume model, not a recovered body surface.','',
      '- **A table occlusion:** the Phase 1b seat-side edge clipped the lower torso/arms too early. Shortened the weak depth prior from 1.064 to 0.800 m while retaining the measured S7 far edge and yaw exactly. A pilot raised S1-start IoU 0.487→0.556 and S3-start 0.462→0.594. This refinement exists only in `scen3d.json`; `data/layout.json` remains byte-identical to `layout-1b.json`. All seven measured 68° cameras and B’s 0.593 × 1.174 m table are unchanged. The orchestrator’s former wide-table guess is superseded by the measured narrow/deep table.','',
      '- **S7 dressing:** moved the unmeasured empty table by [.40,0,-.10] m and added a second empty table to make the intervening row visible; these are declared layout priors, not new measurements. S7 hides A’s cup/food/tray that are absent from the source crop; the registered foreground can remains.','',
      '- **Hand anchoring:** first compared raw pose-wrist attachment (hands too low or under the tabletop) with independent HandLandmarker wrist-image rays at the original pose-wrist camera-depth. Selected the latter for detected hands, for both avatar routes. The 21-point hand geometry remains metric. Five-frame/order-two Savitzky–Golay filtering is bounded by shot and contiguous detection runs. Missing hands receive relaxed fingers; no hand motion is invented for S6. Raw motion is preserved alongside `poseFused`. Hand depth and metric size remain inferred.','',
      '| Shot | Detected hand samples | Median anchor shift cm | Maximum shift cm | Rendered wrist/image median px | jawOpen min–max |','|---|---:|---:|---:|---:|---|']
    for sid,t in temporal.items():
        a=anchors[sid];fmt=lambda x:'n/a' if x is None else f'{x:.2f}'
        lines.append(f"| {sid} | {t['measured_hands']} | {fmt(a['median_m']*100 if a['median_m'] is not None else None)} | {fmt(a['max_m']*100 if a['max_m'] is not None else None)} | {fmt(t['hand_wrist_median_px'])} | {t['jaw_range'][0]:.4f}–{t['jaw_range'][1]:.4f} |")
    lines+=['',
      'The wrist/image comparison is a fit diagnostic because those observations drive the anchors. Maximum corrections (up to 22.5 cm) expose inconsistent monocular pose/hand estimates, not measured physical hand travel. The procedural limbs can stretch with noisy measurements. Face rotation uses the measured camera-relative matrix/quaternion; jaw, brows, smile and blinks drive mesh parameters. All 383 frames were rendered for the temporal audit. S7 jaw amplitude produces only about a pixel of visible movement at that distance, so distant lip readability remains uncertain.','',
      '## Player and reproducibility','',
      f"Set: {len(spec['set'])} semantic objects; props: {len(spec['props'])}; actors: A/B/C plus one neutral untracked background guest in S4. Real floor/walls/window/ceiling, pendants, counter, tables/chairs; nine mesh factories including the pizza slice. JSON uses meters, seconds and degrees, includes actor looks and motion intensity/references, per-shot placements/yaw, camera keyframes, dialogue/audio ranges and an edit log. Burger/fry/terminal attachments follow hands. Seated legs use stable inferred geometry.",'',
      'The player provides sequential playback, captions (including off-screen speakers), optional local source audio, orbit inspection and an avatar comparison selector. It polls JSON every second, validates a replacement before rebuilding, and keeps playback time. Camera keyframes interpolate position/target/up/FOV. `#t=1.2&mode=mask&cam=S1` freezes the frame; `&capture=1` hides the UI for 576×1024 screenshots. Mask mode renders the tracked main actor white with depth-correct black occluders.','',
      f"Browser checks: {len(v['browser_errors'])} uncaught errors; {len(v['external_requests'])} external page requests. Frozen hash screenshot byte-identical: {v['smoke'].get('hashFrozen')}. Play advanced time: {v['smoke'].get('playAdvanced')}. JSON hot reload changed revision and the rendered can position, then restored the original file: `{v['smoke'].get('hotReload')}`. Local audio duration: {v['smoke'].get('audio',{}).get('duration','unknown')} s (video 12.7667 s). All runtime modules/models/audio are local. Model metadata in `modeller/licenses-vrm.json` says `licenseName: CC0`, `commercialUssageName: Allow` for both models; archive/member hashes and licenses are retained.",'',
      '```powershell','scen/.venv/Scripts/python.exe -B scen/3d/fas2.py','scen/.venv/Scripts/python.exe -B scen/3d/verifiera.py','scen/.venv/Scripts/python.exe -m http.server 8000 --directory scen/3d','```','',
      'Open `http://localhost:8000/`. The preparation stage rebuilds generated motion and scene JSON from Phase 1b inputs; retain any deliberate scene edits separately before rerunning it. No build step. First preparation downloads pinned public dependencies/models; subsequent preparation and all playback/verification run from local files. Verification requires the stated Windows Chrome path, Node and the existing Python venv.','',
      f"Measured repeat runtimes: preparation {prepare['seconds']:.2f} s with downloads cached; verification {runtime['verification_seconds']:.2f} s with source segmentations cached, including both avatar routes, screenshots, all 383 temporal frames and browser checks. The first download/segmentation pass and exploratory iterations are not included. Model files and source/verification image dimensions are retained for reruns.",'',
      '## Verification images and limits','',
      '- [Seven-shot source/render/overlay overview](verifiering/fas2/fas2-procedural.jpg). Full three-frame sheets: [S1](verifiering/fas2/S1-procedural.jpg), [S2](verifiering/fas2/S2-procedural.jpg), [S3](verifiering/fas2/S3-procedural.jpg), [S4](verifiering/fas2/S4-procedural.jpg), [S5](verifiering/fas2/S5-procedural.jpg), [S6](verifiering/fas2/S6-procedural.jpg), [S7](verifiering/fas2/S7-procedural.jpg). Green contours = source mask; magenta = render.','- [VRM comparison](verifiering/fas2/fas2-vrm.jpg).','- [Mouth extremes](verifiering/fas2/mouths.jpg), [prop factories](verifiering/fas2/props-catalog.png), [player](verifiering/fas2/player.png).','- Free-camera renders: [room/B](verifiering/fas2/orbit.png), [A](verifiering/fas2/orbit-A.png), [C](verifiering/fas2/orbit-C.png). Individual source, normal render and binary-mask PNG/JPG files are alongside the sheets.','',
      'Remaining limits: S6 hand fidelity is unverified; S7 whole-person IoU is below 0.5 and the far mouth is barely readable; legs/hidden anatomy, room bounds, the waiter’s global placement and added furniture are priors. Forearm/finger alignment, face likeness, grasp contacts and occasional clothing/table intersections are approximate. A’s table depth refinement is an occlusion fit, not a new physical size measurement. Automatic source masks and monocular metric scale remain uncertain. The numerical close-shot pass does not establish complete reconstruction accuracy or guarantee every frame meets every threshold.','']
    if v['smoke'].get('audioSync'):
        sync=v['smoke']['audioSync'];drift=abs(sync['audio']['time']-sync['sceneTime'])*1000
        lines+=['## Final browser/visual review','',f"Audio was actually played in muted headless Chrome (readyState {sync['audio']['ready']}, paused={sync['audio']['paused']}, rate={sync['audio']['rate']}); measured audio/scene difference {drift:.1f} ms, within the player's 120 ms correction threshold. The final player screenshot uses the corrected responsive viewport and readable status text. This UI-only follow-up is recorded in `data/player-check-2.json`; the full render-run metadata is in `data/capture-2-full.json`. Its additional runtime is excluded from the full-render runtime above.",'']
    (ROOT/'rapport.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--quick',action='store_true');parser.add_argument('--score-only',action='store_true');args=parser.parse_args();start=time.perf_counter()
    frames=read('data/sparning.json')['frames'];layout=read('data/layout.json');indices=[]
    for c in layout['cameras'].values():
        a,b=c['start_frame'],c['end_frame_exclusive'];indices.extend([(a+b-1)//2] if args.quick else [a,(a+b-1)//2,b-1])
    seg=sources(indices,frames);jobs=[]
    for variant in (['procedural'] if args.quick else ['procedural','vrm']):
        for n in indices:
            for mask in [False,True]:jobs.append(dict(t=n/30,variant=variant,mask=mask,file=f"{frames[n]['shot']}-{n:03d}-{variant}{'-mask' if mask else ''}.png"))
    jobs.append(dict(t=12,variant='procedural',orbit=dict(pos=[3.6,2.3,3.1],target=[0,.8,1.4]),file='orbit.png'))
    if not args.quick:
        jobs.extend([dict(t=1.2,orbit=dict(pos=[1.6,1.6,2.3],target=[-.07,.95,3.2]),file='orbit-A.png'),dict(t=7.1,orbit=dict(pos=[3.0,1.5,2.1],target=[2.8,1.0,.4]),file='orbit-C.png'),dict(t=0,catalog=True,file='props-catalog.png')])
        motion=read('data/motion-2.json')['frames'];dialogue=read('scen3d.json')['dialogue']
        for sid in ['S1','S2','S3','S5','S6','S7']:
            fs=[f for f in motion if f['shot']==sid and any(d['start']<=f['t']<d['end'] and d['speaker']==f['actor'] for d in dialogue)]
            for name,select in [('min',min),('max',max)]:
                f=select(fs,key=lambda f:f['face']['blendshapes']['jawOpen']);jobs.append(dict(t=f['frame']/30,mouth=name,file=f'{sid}-mouth-{name}.png'))
        jobs.extend(dict(t=n/30,temporal=True) for n in range(383));jobs.append(dict(t=1.2,ui=True,file='player.png'))
    capture=read('verifiering/fas2/capture-results.json') if args.score_only else render(jobs,not args.quick)
    score(capture,frames,seg);extra_checks(capture,frames);write('data/runtime-2.json',dict(verification_seconds=time.perf_counter()-start,quick=args.quick))
    if not args.quick:report()
