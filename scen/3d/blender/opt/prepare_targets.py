"""Compare blind visual checks; confidence-select detector per joint, never per fit."""
from common import *
from collections import defaultdict

def observations(row,n):
    mp=row['mediapipe'];rt=row['rtmw'];out={}
    if n in BODY:
        p=mp['pose']['image'][BODY[n]];out['mediapipe']=(np.array(p[:2])*[576,1024],float(p[3] or 0))
        k=COCO[n]
    else:
        side,lm=HAND_LM[n];k=(91 if side=='Left' else 112)+lm
        hands=[h for h in mp['hands'] if h['side']==side]
        if hands:
            h=max(hands,key=lambda h:h['score']);out['mediapipe']=(np.array(h['image'][lm][:2])*[576,1024],h['score'])
    out['rtmw']=(np.array(rt['xy'][k]),float(rt['confidence'][k]))
    return out

def main():
    raw=read(HERE/'gt/raw.json');rows=raw['frames'];labels=read(HERE/'gt/manual-checks.json')
    errors=defaultdict(list);per=[]
    for c in labels['checks']:
        for n,xy in c['points'].items():
            group='hands' if n in HAND_LM else ('wrists' if n.endswith('Hand') else 'body')
            for model,(point,conf) in observations(rows[c['i']],n).items():
                error=float(np.linalg.norm(point-xy));errors[(group,model)].append(error)
                per.append(dict(i=c['i'],joint=n,model=model,xy=point.tolist(),confidence=conf,error_px=error))
    summary={g:{m:dict(n=len(errors[(g,m)]),median_px=float(np.median(errors[(g,m)]))) for m in ['mediapipe','rtmw'] if errors[(g,m)]} for g in ['body','wrists','hands']}
    # Calibrate relative confidence with validation accuracy. Handedness confidence
    # is NOT localization confidence: MP hand score is capped and explained below.
    factors={g:{m:1/max(v['median_px'],6) for m,v in summary[g].items()} for g in summary}
    for g in factors:
        top=max(factors[g].values());factors[g]={m:v/top for m,v in factors[g].items()}
    targets=[]
    for row in rows:
        xy=[];weights=[];selected=[]
        for n in FEATURES:
            group='hands' if n in HAND_LM else ('wrists' if n.endswith('Hand') else 'body')
            options=observations(row,n);valid=[]
            for m,(p,conf) in options.items():
                if not(0<=p[0]<576 and 0<=p[1]<1024):continue
                if conf < (.65 if m=='mediapipe' and n in BODY else .35):continue
                confidence=min(conf,.75) if m=='mediapipe' and n in HAND_LM else min(conf,1)
                valid.append((confidence*factors[group].get(m,1),m,p))
            # Hands/elbows are wholly hidden in S6. Do not score hallucinated joints.
            if row['shot']=='S6' and n not in ['nose','LeftArm','RightArm']:valid=[]
            if valid:
                score,m,p=max(valid,key=lambda x:x[0]);xy.append(p.tolist());weights.append(score);selected.append(m)
            else:xy.append([0,0]);weights.append(0);selected.append(None)
        targets.append(dict(i=row['i'],shot=row['shot'],xy=xy,confidence=weights,selected=selected))
    write(HERE/'gt/detector-comparison.json',dict(method=labels['method'],summary=summary,confidence_factors=factors,points=per,decision='Per joint: larger calibrated confidence, using only source observations. MP hand handedness score capped at .75, not treated as localization probability. Missing/hidden joints never interpolated. All detector joints retained raw.',limitation='23 approximate visual checks, not expert human ground truth; detector confidence scales are heuristic.'))
    write(HERE/'gt/targets.json',dict(features=FEATURES,frames=targets,source_sha256=raw['source_sha256'],raw_sha256=sha(HERE/'gt/raw.json')))
    spec=read(ROOT/'scen3d.json');events=read(HERE/'gt/events-sheets.json')['events'];accepted=[];audit=[]
    for e in events:
        mid=(e['startSec']+e['endSec'])/2
        s=next(s for s in spec['shots'] if s['source']['inSec']<=mid<s['source']['outSec'])
        v=dict(e);v['shot']=s['id'];v['startSec']=max(e['startSec'],s['source']['inSec']);v['endSec']=min(e['endSec'],s['source']['outSec'])
        if e['type']=='touch_table':
            audit.append(dict(event=e,status='rejected',reason='Source S1 sheets: hands clasped in air at chest level, elbows supported. Wrist tracks above table. Table-touch claim confuses elbows and hands.'))
            continue
        if e['type']=='hold':
            v['side']='Left';audit.append(dict(event=e,status='corrected side' if str(e['side']).lower()!='left' else 'confirmed',reason='Source sheets and anatomical wrist identity: fry S2, terminal S4 and burger S5 are in image-right/anatomical Left hand. S5 right hand is at opposite frame edge, not on burger. Continuous whole-shot hold, no observed onset/offset inside the shot.'))
        if e['type'] in ['seated','standing','hold']:
            v['startSec']=s['source']['inSec'];v['endSec']=s['source']['outSec']
            v['support_visibility']='inferred from torso/table and existing scene; seat/feet occluded' if e['type']!='hold' else 'visible'
        accepted.append(v)
    audit.append(dict(status='rejected initial video pass',reason='Initial video Gemini mislabeled S5 as A and omitted burger; S2 fry side wrong; claimed whole-shot S1/S3 hand-table contact. Timestamped per-shot sheets used for correction. S1 gesture window 1.367-1.700 is coarse: frame36 (1.200 s) already has separated hands; semantics never used to retime gestures. End times snapped to exact shot boundaries only for visually continuous contacts; uncertainty of internal transitions is at least sheet sampling interval.'))
    write(HERE/'gt/events-checked.json',dict(events=accepted,audit=audit,validation='Manual source-sheet spot checks + measured wrist tracks. Gemini used only for semantic categories/windows. No Gemini coordinates. Raw outputs retained.'))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
