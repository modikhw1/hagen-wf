import sys,json,hashlib
from pathlib import Path
import cv2,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.path[:0]=[str(P/'kontrakt'),str(P/'ingest'),str(HERE)]
from prova import save,log,normalize,differences,sha
from trohet import KP,LED,IX,synliga_par
from kroppmatt import jamfor_mask
plans={t:json.loads((HERE/t/'plan.json').read_text(encoding='utf-8')) for t in ('fore','efter')}
data={t:json.loads((HERE/t/'blender_matning.json').read_text(encoding='utf-8')) for t in plans}
by={t:{r['ut']:r for r in rows} for t,rows in data.items()}
def read(p):return cv2.imread(str(p),cv2.IMREAD_UNCHANGED)
def img(phase,sid,u,suffix):return read(HERE/phase/f'{sid}_{u:03d}_{suffix}.png')
def title(im,text):
    if im.shape[2]==4:im=im[:,:,:3]
    dst=np.zeros((im.shape[0]+28,im.shape[1],3),np.uint8);dst[28:]=im
    cv2.putText(dst,text,(5,19),cv2.FONT_HERSHEY_SIMPLEX,.46,(255,255,255),1,cv2.LINE_AA)
    return dst
def write(p,im):p.parent.mkdir(exist_ok=True,parents=True);cv2.imwrite(str(p),im)
cap=cv2.VideoCapture(str(ROOT/'scen/klipp/d-dialog-notan.mp4'))
rows=[];montages={};snapshot=[]
for s,sold in zip(plans['efter']['scener'],plans['fore']['scener']):
    for a,b in [(s['varld'],sold['varld'])]+[(x['rorelse'],y['rorelse']) for x,y in zip(s['personer'],sold['personer'])]:
        snapshot.append(dict(dagens=a,fore=b,byteidentisk=sha(Path(a))==sha(Path(b))))
for row in data['efter']:
    u=row['ut'];sid=row['scen'];s=next(s for s in plans['efter']['scener'] if s['id']==sid);f=row['lokal']
    cap.set(cv2.CAP_PROP_POS_FRAMES,row['kallruta']);ok,source=cap.read();assert ok
    source=cv2.resize(source,(288,512),interpolation=cv2.INTER_AREA)
    write(HERE/'kalla'/f'{sid}_{u:03d}.png',source)
    current=img('efter',sid,u,'original')[:,:,:3];before=img('fore',sid,u,'original')[:,:,:3]
    mask=img('efter',sid,u,'mask')[:,:,3]>127
    overlay=source.copy();overlay[mask]=(.55*source[mask]+.45*np.array([0,220,255])).astype(np.uint8)
    # Röd kant: Blenderhud; grön kant: oberoende personmask från källfilmen.
    folder=Path(s['varld']).parent;target=np.load(folder/'masker.npy',mmap_mode='r')[f].astype(np.uint8)
    targetbig=cv2.resize(target,(288,512),interpolation=cv2.INTER_NEAREST)
    for m,c in [(targetbig,(0,220,0)),(mask.astype(np.uint8),(0,0,255))]:
        contours,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(overlay,contours,-1,c,1)
    write(HERE/'jamforelser'/f'{sid}_{u:03d}_sida.png',np.hstack([title(source,'Kalla'),title(current,'Blender efter')]))
    write(HERE/'jamforelser'/f'{sid}_{u:03d}_overlagg.png',title(overlay,'Rod hud / gron kallmask'))
    write(HERE/'jamforelser'/f'{sid}_{u:03d}_fore_efter.png',np.hstack([title(before,'Fore GOLV2'),title(current,'Efter GOLV2')]))
    write(HERE/'jamforelser'/f'{sid}_{u:03d}_flyttad.png',np.hstack([title(img('fore',sid,u,'flyttad'),'Fore, flyttad kamera'),title(img('efter',sid,u,'flyttad'),'Efter, flyttad kamera')]))
    montages.setdefault(sid,[]).append(np.hstack([title(source,f'{sid} {u} kalla'),title(before,'Fore'),title(current,'Efter'),title(overlay,'Overlagg'),title(img('efter',sid,u,'flyttad'),'Flyttad')]))
    for pr in row['personer']:
        pm=next(p for p in s['personer'] if p['id']==pr['person']);pid=pr['ingest_id']
        raw=dict(np.load(folder/'kropp'/pid/f'{f:04d}.npz'));seq=dict(np.load(pm['rorelse']))
        pal=json.loads((folder/f'palitlig_{pid}.json').read_text(encoding='utf-8'))
        pair=synliga_par(bool(seq['ben_synliga'][f]));mw,mh=target.shape[1],target.shape[0]
        r=dict(scen=sid,ut=u,lokal=f,kallruta=row['kallruta'],person=pr['person'],palitlig=pal.get(str(f),True),fore={},efter={})
        errors={}
        for phase in ['fore','efter']:
            bp=next(p for p in by[phase][u]['personer'] if p['person']==pr['person'])
            uv=np.array(bp['leder_px']);err=np.linalg.norm(uv[LED]-raw['pred_keypoints_2d'][KP],axis=1)[pair]
            errors[phase]=err
            sil=cv2.resize((img(phase,sid,u,'mask')[:,:,3]>127).astype(np.uint8),(mw,mh),interpolation=cv2.INTER_NEAREST).astype(bool)
            box=raw['bbox']*np.array([mw/576,mh/1024,mw/576,mh/1024])
            maskmetric=jamfor_mask(sil,target.astype(bool),box,mw,mh)
            r[phase]=dict(median_px=float(np.median(err)),p90_px=float(np.percentile(err,90)),mask=maskmetric,
                sula_over_golv_m=bp['sula_over_golv_m'],backen_m=bp['backen_m'],handleder_m=bp['handleder_m'])
        r['max_synlig_ledflytt_px']=float(np.linalg.norm(np.array(by['fore'][u]['personer'][0]['leder_px'])[LED[pair]]-np.array(pr['leder_px'])[LED[pair]],axis=1).max())
        r['blender_numpy_max_m']=pr['blender_numpy_max_m'];r['blender_numpy_max_px']=pr['blender_numpy_max_px']
        rows.append(r)
for sid,ims in montages.items():write(HERE/'montage'/f'{sid}_alla.png',np.vstack(ims))
for row in data['efter']:
    sid,u=row['scen'],row['ut']
    p=HERE/'efter'/f'{sid}_{u:03d}_flyttad_vid.png'
    if p.exists():write(HERE/'montage'/f'{sid}_vid.png',np.hstack([title(img('fore',sid,u,'flyttad_vid'),'Fore, vidare utsnitt'),title(img('efter',sid,u,'flyttad_vid'),'Efter, vidare utsnitt')]))
summary=[]
for sid in montages:
    rr=[r for r in rows if r['scen']==sid]
    summary.append(dict(scen=sid,fore_iou=float(np.median([r['fore']['mask']['iou'] for r in rr])),
        efter_iou=float(np.median([r['efter']['mask']['iou'] for r in rr])),
        fore_iou_synlig=float(np.median([r['fore']['mask']['iou_synlig'] for r in rr])),
        efter_iou_synlig=float(np.median([r['efter']['mask']['iou_synlig'] for r in rr])),
        median_px=[round(r['efter']['median_px'],3) for r in rr],p90_px=[round(r['efter']['p90_px'],3) for r in rr],
        max_ledflytt_px=max(r['max_synlig_ledflytt_px'] for r in rr),
        sula_m=[round(r['efter']['sula_over_golv_m'],5) for r in rr]))
save(HERE/'bildmatning.json',rows);save(HERE/'sammanfattning.json',summary);save(HERE/'fore_indatakontroll.json',snapshot)
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('Blender numpy max px',max(r['blender_numpy_max_px'] for r in rows),'m',max(r['blender_numpy_max_m'] for r in rows))
print('Identiska föreindata',all(s['byteidentisk'] for s in snapshot))
log('Båda Blenderkörningarna färdiga: 21 rutor vardera, original/silhuett/flyttad samt sju vidare översikter. Källrutor, sida-vid-sida, överlägg, före/efter och mätvärden skapade. Mätning gäller faktiska Blenderleder och rasteriserad Blenderhud; masken är oberoende YOLO men nyckelpunkterna är estimatorns egna.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck")
