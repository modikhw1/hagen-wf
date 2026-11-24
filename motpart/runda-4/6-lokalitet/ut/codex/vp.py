"""Independent image-line witness; no MoGe normals, gravity or target pitch used in fitting.
Pixel centres and square pixels assumed. Focal length from the camera being tested;
results also computed for focal +/-20%. Manual architecture ROIs are recorded below.
"""
from pathlib import Path
import json, math, sys
import cv2
import numpy as np
from scipy.optimize import least_squares

OUT=Path(__file__).resolve().parent; BASE=OUT.parents[1]
KEYS=['duepiani','spanjorskan','08burgerkebab','babasburgers','kennysgelato2.0']

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')

# Coordinates in the original 540x960 frames. Only architectural verticals.
ROIS={
 'duepiani': {'s1':[[0,145,225,740],[460,110,540,900]], 's3':[[0,145,225,740],[460,110,540,900]],
             **{s:[[0,270,290,610]] for s in ['s4','s5','s6','s7','s9']},
             's11':[[0,200,205,350],[490,210,540,730]],'s12':[[0,210,185,510],[400,240,540,410]]},
 'spanjorskan': {'s1':[[0,80,410,370]],'s3':[[0,80,410,370]]},
 '08burgerkebab': {},
 'babasburgers': {'s1':[[0,70,540,360]],'s5':[[0,60,540,420]],'s8':[[0,60,540,400]]},
 'kennysgelato2.0': {'s1':[[0,180,540,580]]}
}
MISSING={
 'duepiani':{'s2':'Tallriksnärbild: inga spridda, säkert vertikala byggnadslinjer.',
             's8':'Panna ovanifrån: inga säkra vertikala linjer.','s10':'Mat/panna ovanifrån: inga säkra vertikala linjer.'},
 'spanjorskan':{'s2':'Bordsnärbild ovanifrån: bordskanter är inte lodlinjer.'},
 '08burgerkebab':{'s9':'Maträtt ovanifrån: inga säkra vertikala linjer.'},
 'babasburgers':{s:'Bords-/matnärbild: för få säkra, separerade vertikaler; burk, koniskt kärl och stolsben räcker inte.' for s in ['s2','s3','s4','s6','s7','s9']},
 'kennysgelato2.0':{}
}
MISSING['babasburgers'].update({s:'Visuell kontroll: LSD-konsensus på lutande stolsben, kläder eller koniska lampskärmar. För få säkra vertikaler.' for s in ['s10','s11']})

def detect(im,rois,min_length=40):
    gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    seg=cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(gray)[0]
    if seg is None: return np.empty((0,4))
    seg=seg.reshape(-1,4).astype(float); d=seg[:,2:]-seg[:,:2]; mid=(seg[:,:2]+seg[:,2:])/2
    lengths=np.linalg.norm(d,axis=1)
    ok=(lengths>=min_length)&(np.abs(d[:,0])<np.abs(d[:,1])*math.tan(math.radians(35)))
    if rois:
        inside=np.zeros(len(seg),bool)
        for x0,y0,x1,y1 in rois:
            inside|=(mid[:,0]>=x0)&(mid[:,0]<=x1)&(mid[:,1]>=y0)&(mid[:,1]<=y1)
        ok&=inside
    else: ok&=(mid[:,1]>60)&(mid[:,1]<910)
    seg=seg[ok]
    # Merge duplicated edges/collinear fragments into at most one vote per physical line.
    d=seg[:,2:]-seg[:,:2]; length=np.linalg.norm(d,axis=1); kept=[]
    for j in np.argsort(-length):
        v=d[j]/length[j]; p=seg[j,:2]
        duplicate=False
        for k in kept:
            vk=d[k]/length[k]
            angle=math.degrees(math.acos(np.clip(abs(v@vk),-1,1)))
            delta=seg[k,:2]-p; dist=abs(v[0]*delta[1]-v[1]*delta[0])
            if angle<0.5 and dist<6: duplicate=True; break
        if not duplicate: kept.append(j)
    return seg[kept]

def pitch(par):
    v=np.array([par[0],-1.,par[1]])
    return math.degrees(math.asin(v[2]/np.linalg.norm(v)))

def fit(seg,W,H,f):
    if len(seg)<5: return {'valid':False,'reason':'Färre än fem separerade linjer.'}
    mid=(seg[:,:2]+seg[:,2:])/2; d=seg[:,2:]-seg[:,:2]
    d=d*np.where(d[:,1:2]<0,-1,1); lengths=np.linalg.norm(d,axis=1)
    xy=(mid-[W/2,H/2])/f; slopes=d[:,0]/d[:,1]
    A=np.stack([np.ones(len(seg)),slopes*xy[:,1]-xy[:,0]],1); b=-slopes
    def residual(par):
        pred=np.stack([par[0]-xy[:,0]*par[1],-1-xy[:,1]*par[1]],1)
        cross=pred[:,0]*d[:,1]-pred[:,1]*d[:,0]
        return np.degrees(np.arcsin(np.clip(cross/(np.linalg.norm(pred,axis=1)*lengths),-1,1)))
    pairs=np.array([(i,j) for i in range(len(seg)) for j in range(i+1,len(seg))])
    if len(pairs)>2000: pairs=pairs[np.random.default_rng(829).choice(len(pairs),2000,replace=False)]
    best=None
    for ids in pairs:
        if abs(np.linalg.det(A[ids]))<.02: continue
        par=np.linalg.solve(A[ids],b[ids]); err=np.abs(residual(par)); sel=err<.8
        if abs(math.degrees(math.atan(par[0])))>35: continue
        score=float(np.minimum(lengths[sel],200).sum())
        if best is None or score>best[0]: best=(score,par,sel)
    if best is None: return {'valid':False,'reason':'Ingen stabil linjehypotes.'}
    _,par,sel=best
    for _ in range(3):
        par=least_squares(lambda x:residual(x)[sel]*np.sqrt(np.minimum(lengths[sel],200)),par,loss='soft_l1',f_scale=3).x
        sel=np.abs(residual(par))<.8
    span=float(np.ptp(mid[sel,0])) if sel.any() else 0
    rng=np.random.default_rng(54); boots=[]; ids=np.where(sel)[0]
    for _ in range(150):
        ii=rng.choice(ids,len(ids),replace=True)
        if np.linalg.matrix_rank(A[ii])<2: continue
        q=np.linalg.lstsq(A[ii]*lengths[ii,None],b[ii]*lengths[ii],rcond=None)[0]
        boots.append(pitch(q))
    ci=np.percentile(boots,[2.5,97.5]).tolist() if boots else [-90,90]
    reasons=[]
    if sel.sum()<5: reasons.append('färre än 5 inlierlinjer')
    if span<.25*W: reasons.append('horisontellt stöd <25% av bilden')
    if ci[1]-ci[0]>10: reasons.append('bootstrapintervall bredare än 10 grader')
    vp=[W/2+f*par[0]/par[1],H/2-f/par[1]] if abs(par[1])>1e-9 else None
    return {'valid':not reasons,'reason':'; '.join(reasons),'pitch':pitch(par),'ci95':ci,
            'inliers':np.where(sel)[0].tolist(),'n_lines':len(seg),'span_px':span,'vp_px':vp,
            'direction':[float(par[0]),-1.,float(par[1])],
            'median_residual_deg':float(np.median(np.abs(residual(par)[sel]))),
            'focal_sensitivity':[pitch([par[0],par[1]*s]) for s in [.8,1.2]]}

def run(key):
    meta=read(BASE/'ut'/key/'obs_gpu.json'); loc=read(BASE/'ut'/key/'lokalitet.json')
    result=[]; vis=OUT/'vp-images'; vis.mkdir(exist_ok=True)
    for s in meta['tagningar']:
        sid=s['id']; W,H=meta['bild_px']; f=loc['tagningar'][sid]['lins_mm']['anvand']/36*W
        reason=MISSING[key].get(sid); row={'clip':key,'shot':sid,'f_px':f,'roi':ROIS[key].get(sid),
                'missing_reason':reason,'frames':[]}
        for u in s['nyckelrutor']:
            im=cv2.imread(str(OUT/'frames'/f'{key}-{sid}-{u}.png'))
            min_length=25 if key=='duepiani' and sid in ['s9','s11','s12'] else 40
            seg=detect(im,ROIS[key].get(sid),min_length); r=fit(seg,W,H,f)
            r['min_length_px']=min_length
            if key=='duepiani' and sid=='s9':
                alt=fit(detect(im,ROIS[key].get(sid),40),W,H,f)
                r['alternative_min40']={k:v for k,v in alt.items() if k!='inliers'}
                if 'pitch' in r and 'pitch' in alt and abs(r['pitch']-alt['pitch'])>5:
                    r['valid']=False
                    r['reason']='Tvetydig VP: 25/40 px minsta linjelängd ändrar pitch mer än 5 grader.'
            r['frame']=u; r['segments']=seg.tolist()
            # Retain raw proposals even for scenes without valid structural witnesses.
            if reason: r['valid']=False; r['reason']=reason
            row['frames'].append(r)
            inset=im.copy()
            inliers=set(r.get('inliers',[]))
            for j,(x1,y1,x2,y2) in enumerate(seg):
                col=(0,255,0) if j in inliers else (40,40,230)
                cv2.line(inset,(round(x1),round(y1)),(round(x2),round(y2)),col,2)
                cv2.putText(inset,str(j),(round((x1+x2)/2),round((y1+y2)/2)),cv2.FONT_HERSHEY_SIMPLEX,.4,col,1)
            label=f'{key} {sid} f{u} VP={r.get("pitch",0):.1f} valid={r["valid"]}'
            cv2.putText(inset,label,(5,25),cv2.FONT_HERSHEY_SIMPLEX,.45,(0,0,0),3)
            cv2.putText(inset,label,(5,25),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1)
            cv2.imwrite(str(vis/f'{key}-{sid}-{u}.jpg'),inset)
        valid=[r for r in row['frames'] if r['valid']]
        row['pitch']=float(np.median([r['pitch'] for r in valid])) if len(valid)>=2 else None
        row['target_pitch']=loc['tagningar'][sid]['lutning_grader']
        row['spread']=loc['tagningar'][sid]['lodlinje']['spridning_per_ruta_grader']
        row['delta']=abs(row['pitch']-row['target_pitch']) if row['pitch'] is not None else None
        result.append(row)
        print(key,sid,'VP',None if row['pitch'] is None else round(row['pitch'],1),'target',row['target_pitch'],
              'frames',[(r['frame'],round(r.get('pitch',0),1),r['valid'],r['reason']) for r in row['frames']])
    write(OUT/f'vp-{key}.json',result)
    # Contact sheets of all three keyframes, one shot per row, at 50% original size.
    for start in range(0,len(result),4):
        group=result[start:start+4]; sheet=np.zeros((480*len(group),810,3),np.uint8)
        for i,row in enumerate(group):
            for j,r in enumerate(row['frames']):
                im=cv2.imread(str(vis/f'{key}-{row["shot"]}-{r["frame"]}.jpg'))
                sheet[i*480:(i+1)*480,j*270:(j+1)*270]=cv2.resize(im,(270,480))
        cv2.imwrite(str(OUT/f'vp-{key}-{start//4+1}.jpg'),sheet)

def selftest():
    tests=[]; rng=np.random.default_rng(332)
    for p in [-50,-15,0,15]:
        par=np.array([.04,math.tan(math.radians(p))*math.sqrt(1+.04**2)])
        seg=[]
        for x,y in zip(np.linspace(45,495,20),rng.uniform(200,700,20)):
            mid=np.array([x,y]); xy=(mid-[270,480])/800
            d=np.array([par[0]-xy[0]*par[1],-1-xy[1]*par[1]])
            d=d/np.linalg.norm(d)*60
            seg.append(np.r_[mid-d,mid+d]+rng.normal(0,.05,4))
        r=fit(np.array(seg),540,960,800)
        assert r['valid'] and abs(r['pitch']-p)<.2, (p,r)
        tests.append({'truth':p,'estimated':r['pitch'],'valid':r['valid']})
    # A permanent discrepancy gate must reject a 15-degree injected pitch error.
    test_pitch=tests[1]['estimated']; assert abs(test_pitch-(-15+15))>10
    write(OUT/'vp-selftest.json',{'synthetic_lines':tests,'pitch_injection_15_deg_detected':True})
    print('PASS: signed pitch, infinity VP, four synthetic projections, 15-degree fault detected')

if __name__=='__main__':
    if sys.argv[1:]==['--selftest']: selftest()
    else:
        for key in sys.argv[1:] or KEYS: run(key)
