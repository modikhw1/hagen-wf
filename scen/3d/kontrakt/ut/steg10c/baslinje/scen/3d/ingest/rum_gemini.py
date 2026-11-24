"""Open-vocabulary boxes and visible furniture edges; credentials never logged."""
import base64
import json
from pathlib import Path
import time

import cv2
import requests

MODEL = 'gemini-3.5-flash-lite'
PROMPT = '''Locate the furniture and props in these video frames. This is geometric scene layout.
Return JSON {"frames":[{"frame":integer,"objects":[{"id":string,"label":string,
"box":[ymin,xmin,ymax,xmax],"top_polygon":[[x,y],...],"back_edge":[[x,y],[x,y]]}]}]}.
Coordinates are normalized 0..1000. Keep the SAME id for the same physical object across frames.
Use labels bar counter, pool table, table, chair, cabinet, shelf, card payment terminal.
Include the large foreground bar counter if present, even when cropped by all sides of the image.
For pool tables identify each physical table separately, especially the two nearest tables on the left and right.
The box includes the visible object, including legs. top_polygon is the visible tabletop polygon, 3-6 ordered corners,
clipped to image edges. Ignore people covering it; infer the CONTINUATION of a straight edge behind them when clear.
back_edge for a bar counter is the straight TOP edge nearest the bartenders, where their lower bodies disappear,
across its full visible width. This is the far edge of the counter, not its front lip. Use [] if not visible.
Do not use the text overlay as an object boundary. No made-up objects. Empty polygons for objects with no visible top.'''


def detect(clip, ut, step=6, batch_size=8):
    ut=Path(ut); target=ut/'rum/gemini'; target.mkdir(parents=True,exist_ok=True)
    env=Path(__file__).resolve().parents[3]/'video/.env.local'
    line=next((s for s in env.read_text(encoding='utf-8').splitlines() if s.startswith('GEMINI_API_KEY_GRATIS=')),None)
    if not line: raise RuntimeError('GEMINI_API_KEY_GRATIS unavailable')
    key=line.split('=',1)[1].strip().strip('\"\'')
    cap=cv2.VideoCapture(str(clip)); n=int(cap.get(7)); w,h=int(cap.get(3)),int(cap.get(4)); result=[]
    for start in range(0,n,step*batch_size):
        path=target/f'{start:04d}.json'
        if path.exists(): data=json.loads(path.read_text())
        else:
            parts=[dict(text=PROMPT)]
            for i in range(start,min(start+step*batch_size,n),step):
                cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,img=cap.read()
                if not ok: raise RuntimeError(f'Cannot decode frame {i}')
                img=cv2.resize(img,(round(w*768/h),768))
                parts += [dict(text=f'FRAME {i}'),dict(inline_data=dict(mime_type='image/jpeg',data=base64.b64encode(cv2.imencode('.jpg',img)[1]).decode()))]
            schema={'type':'OBJECT','properties':{'frames':{'type':'ARRAY','items':{'type':'OBJECT','properties':{
                'frame':{'type':'INTEGER'},'objects':{'type':'ARRAY','items':{'type':'OBJECT','properties':{
                    'id':{'type':'STRING'},'label':{'type':'STRING'},
                    'box':{'type':'ARRAY','items':{'type':'NUMBER'},'minItems':4,'maxItems':4}},'required':['id','label','box']}}},
                'required':['frame','objects']}}},'required':['frames']}
            parts[0]={'text':PROMPT.split('top_polygon for')[0]+'\nFor this request return ONLY frame, id, label, box as in the schema; omit polygons and back_edge.'}
            body=dict(contents=[dict(role='user',parts=parts)],generationConfig=dict(responseMimeType='application/json',responseSchema=schema,temperature=0,maxOutputTokens=12000))
            t=time.perf_counter()
            # No key in URL; deliberately suppress request exception text.
            for attempt in range(3):
                try:
                    response=requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent',
                        headers={'x-goog-api-key':key},json=body,timeout=90)
                    if response.status_code!=200: raise RuntimeError(f'Gemini HTTP {response.status_code}')
                    raw=response.json(); txt=''.join(p.get('text','') for p in raw['candidates'][0]['content']['parts'] if not p.get('thought'))
                    data=json.loads(txt)
                    if len(data['frames'])!=len(range(start,min(start+step*batch_size,n),step)): raise ValueError('Missing frames')
                    break
                except (requests.RequestException, ValueError, KeyError, RuntimeError):
                    if attempt==2: raise RuntimeError('Gemini failed after 3 attempts (HTTP/JSON/timeout); cache is resumable') from None
                    time.sleep(3)
            path.write_text(json.dumps(data,indent=2),encoding='utf-8')
            print(f'Gemini frames {start}..{min(start+step*batch_size,n)-1}: {time.perf_counter()-t:.1f}s',flush=True)
        for frame in data['frames']:
            for obj in frame['objects']:
                box=obj.get('box',[])
                if len(box)==1 and isinstance(box[0],list): box=box[0]
                if len(box)!=4 or not all(isinstance(x,(int,float)) for x in box): continue
                y0,x0,y1,x1=box
                def polygon(key):
                    p=obj.get(key,[])
                    return [[x*w/1000,y*h/1000] for x,y in p] if all(isinstance(v,list) and len(v)==2 and all(isinstance(x,(int,float)) for x in v) for v in p) else []
                result.append(dict(frame=frame['frame'],label=obj['label'],track=obj['id'],
                    box=[x0*w/1000,y0*h/1000,x1*w/1000,y1*h/1000],confidence=None,
                    top_polygon=polygon('top_polygon'),back_edge=polygon('back_edge'),model=MODEL))
    cap.release(); (ut/'rum/detections_gemini.json').write_text(json.dumps(result,indent=1),encoding='utf-8')
    return result


if __name__=='__main__':
    import sys
    detect(sys.argv[1],sys.argv[2])
