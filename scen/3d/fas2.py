"""Phase 2 inputs. Run: scen/.venv/Scripts/python.exe -B scen/3d/fas2.py"""
import json, time, hashlib, struct, zipfile, io, subprocess
from pathlib import Path
import requests
import numpy as np
from scipy.signal import savgol_filter
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parent
def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path, data):
    p=ROOT/path; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def download(url, path):
    p=ROOT/path; p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():
        r=requests.get(url,timeout=180); r.raise_for_status(); p.write_bytes(r.content)
    return p

def dependencies():
    manifest=[]
    items={
      'three.module.js':'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js',
      'OrbitControls.js':'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js',
      'GLTFLoader.js':'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/loaders/GLTFLoader.js',
      'utils/BufferGeometryUtils.js':'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/utils/BufferGeometryUtils.js',
      'RoundedBoxGeometry.js':'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/geometries/RoundedBoxGeometry.js',
      'three-vrm.module.js':'https://cdn.jsdelivr.net/npm/@pixiv/three-vrm@3.3.3/lib/three-vrm.module.js',
      'kalidokit.js':'https://cdn.jsdelivr.net/npm/kalidokit@1.1.5/dist/kalidokit.es.js',
      'licenses/three.txt':'https://cdn.jsdelivr.net/npm/three@0.170.0/LICENSE',
      'licenses/three-vrm.txt':'https://cdn.jsdelivr.net/npm/@pixiv/three-vrm@3.3.3/LICENSE',
      'licenses/kalidokit.txt':'https://cdn.jsdelivr.net/npm/kalidokit@1.1.5/LICENSE.md',
    }
    for filename,url in items.items():
        p=download(url, 'vendor/'+filename)
        manifest.append(dict(path=str(p.relative_to(ROOT)),url=url,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    # GLTFLoader's upstream relative ../utils import: retained in vendor/loaders.
    (ROOT/'vendor/loaders').mkdir(exist_ok=True)
    (ROOT/'vendor/loaders/GLTFLoader.js').write_bytes((ROOT/'vendor/GLTFLoader.js').read_bytes())
    licenses=[]
    for sex in ['female','male']:
        url=f'https://opengameart.org/sites/default/files/base_{sex}.zip'
        p=download(url,f'modeller/base_{sex}.zip')
        with zipfile.ZipFile(p) as z:
            name=next(n for n in z.namelist() if n.lower().endswith('.vrm'))
            b=z.read(name); length=struct.unpack_from('<I',b,12)[0]
            gltf=json.loads(b[20:20+length]); meta=gltf['extensions']['VRM']['meta']
            allowed=meta.get('licenseName')=='CC0' and meta.get('commercialUssageName',meta.get('commercialUsage')) in ['Allow',True]
            licenses.append(dict(source=url,member=name,sha256=hashlib.sha256(b).hexdigest(),meta=meta,approved=allowed))
            if not allowed: raise RuntimeError('VRM metadata does not permit use: '+json.dumps(meta))
            (ROOT/f'modeller/base_{sex}.vrm').write_bytes(b)
    write('vendor/manifest.json',manifest);write('modeller/licenses-vrm.json',licenses)
    print('Offline dependencies and VRM licenses:',[(x['member'],x['meta']['licenseName'],x['approved']) for x in licenses])

def smooth(a):
    a=np.asarray(a,float)
    return savgol_filter(a,min(5,len(a)//2*2-1),2,axis=0,mode='interp') if len(a)>=5 else a

def fuse_hands():
    """Hand worlds are hand-centered: locate wrists using their independent image ray.
    Preserve PoseLandmarker's wrist camera-depth. Same input for both avatar methods.
    This corrects an inconsistent wrist anchor, not the camera or depth observations.
    """
    motion=read('data/motion-2.json');layout=read('data/layout.json');statistics={}
    for sid,c in layout['cameras'].items():
        fs=[f for f in motion['frames'] if f['shot']==sid]
        T=np.array(c['world_to_camera_cv'])@np.array(layout['actors'][c['actor']]['raw_pose_to_world']);inverse=np.linalg.inv(T);K=np.array(c['intrinsics_px']);moves=[]
        for f in fs:f['poseFused']=np.array(f['pose']).copy();f['handAnchorCorrections']=[]
        for side,wrist in [('Left',15),('Right',16)]:
            run=[]
            def flush():
                if not run:return
                image=smooth([h['image'][0][:2] for f,h in run])
                for (f,h),uv in zip(run,image):
                    original=np.array(f['pose'][wrist]);depth=(T@np.r_[original,1])[2]
                    ray=np.array([(uv[0]*576-K[0,2])/K[0,0],(uv[1]*1024-K[1,2])/K[1,1],1])*depth
                    anchor=(inverse@np.r_[ray,1])[:3];f['poseFused'][wrist]=anchor
                    for pose_idx,hand_idx in [(17,20),(19,8),(21,4)]:f['poseFused'][pose_idx+(wrist-15)]=anchor+np.array(h['world'][hand_idx])-np.array(h['world'][0])
                    shift=float(np.linalg.norm(anchor-original));moves.append(shift);f['handAnchorCorrections'].append(dict(side=side,meters=shift,depth_m=float(depth)))
                run.clear()
            for f in fs:
                h=next((h for h in f['hands'] if h['side']==side),None)
                if h:run.append((f,h))
                else:flush()
            flush()
        for f in fs:f['poseFused']=f['poseFused'].round(6).tolist()
        statistics[sid]=dict(count=len(moves),median_m=float(np.median(moves)) if moves else None,max_m=max(moves) if moves else None)
    motion['handAnchorMethod']='Independent smoothed HandLandmarker wrist image ray at smoothed PoseLandmarker wrist camera-depth; no depth fitting. Raw pose retained; fused input shared by procedural and VRM.'
    (ROOT/'data/motion-2.json').write_text(json.dumps(motion,ensure_ascii=False,separators=(',',':')),encoding='utf-8');write('data/hand-anchor-2.json',statistics)

def prepare():
    layout=read('data/layout.json'); tracking=read('data/sparning.json'); frames=tracking['frames']; out=[]
    for camera in layout['cameras'].values():
        fs=frames[camera['start_frame']:camera['end_frame_exclusive']]
        pose=smooth([np.array(f['pose']['world'])[:,:3] for f in fs])
        names=list(fs[0]['face']['blendshapes']); blend=np.clip(smooth([[f['face']['blendshapes'][n] for n in names] for f in fs]),0,1)
        qs=Rotation.from_matrix([f['face']['head_rotation_matrix'] for f in fs]).as_quat()
        for i in range(1,len(qs)):
            if qs[i-1]@qs[i]<0: qs[i]*=-1
        qs=smooth(qs);qs/=np.linalg.norm(qs,axis=1)[:,None]
        # Smooth hands only over contiguous detections, never across cuts or missing data.
        hand_data={}
        for side in ['Left','Right']:
            run=[]
            def flush():
                if not run:return
                a=smooth([np.array(h['world'])[:,:3] for _,h in run])
                for (i,h),w in zip(run,a):hand_data[(i,side)]=w
                run.clear()
            for i,f in enumerate(fs):
                h=next((h for h in f['hands'] if h['side']==side),None)
                if h:run.append((i,h))
                else:flush()
            flush()
        for i,f in enumerate(fs):
            hands=[]
            for h in f['hands']:
                hands.append(dict(side=h['side'],world=hand_data[(i,h['side'])].round(6).tolist(),image=np.array(h['image'],object)[:,:3].tolist()))
            out.append(dict(frame=f['frame'],t=f['t'],shot=f['shot'],actor=f['actor'],pose=pose[i].round(6).tolist(),image=f['pose']['image'],hands=hands,face=dict(quaternion=qs[i].round(7).tolist(),blendshapes=dict(zip(names,blend[i].round(6).tolist())))))
    neutral={s:np.median([f['pose'] for f in out if f['shot']==s],axis=0).round(6).tolist() for s in layout['cameras']}
    p=ROOT/'data/motion-2.json';p.write_text(json.dumps(dict(fps=30,smoothing='Savitzky-Golay 5 frames / order 2; shot bounded; hands detection-run bounded; normalized face quaternions',neutralPoses=neutral,frames=out),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    looks={
      'A':dict(height=1.65,build=1.0,skin='#e6ad8b',hair='#523323',hairStyle='long',shirt='#181a20',trousers='#24252c',head=[.105,.139,.101],torsoWidth=.39,torsoDepth=.21,sleeveRadius=.073),
      'B':dict(height=1.78,build=1.0,skin='#e7b392',hair='#4a3025',hairStyle='short',shirt='#19253b',trousers='#242a34',head=[.108,.136,.105],torsoWidth=.44,torsoDepth=.25,sleeveRadius=.070),
      'C':dict(height=1.78,build=1.0,skin='#e5b595',hair='#352a25',hairStyle='cap',shirt='#191b20',trousers='#202228',head=[.097,.133,.101],torsoWidth=.40,torsoDepth=.23,sleeveRadius=.069)}
    actors=[]
    for aid,a0 in layout['actors'].items():
        a=dict(a0,id=aid)
        actors.append(dict(id=a['id'],role={'A':'woman','B':'man','C':'waiter'}[a['id']],look=looks[a['id']],transform=dict(position=a['position_m'],yaw=a['yaw_deg']),motion=dict(ref='data/motion-2.json',actor=a['id'],intensity=1,handAnchor='imageRayAtPoseDepth'),seated=a['id']!='C'))
    objects=[]
    for o in layout['furniture']:
        objects.append(dict(id=o['id'],type=o['type'],label=o['id'].replace(':',' '),transform=dict(position=o['position_m'],yaw=o['yaw_deg']),dims=o['dims_m'],color='#202329',provenance=o['provenance']))
    bounds=layout['room']['bounds_m'];xmin,xmax=bounds['x'];zmin,zmax=bounds['z'];cx=(xmin+xmax)/2;cz=(zmin+zmax)/2;h=2.8
    def obj(id,type,pos,dims,color,yaw=0):objects.append(dict(id=id,type=type,label=id,transform=dict(position=pos,yaw=yaw),dims=dims,color=color,provenance='Phase2 room dressing; unmeasured dimension prior'))
    obj('floor','floor',[cx,-.04,cz],[xmax-xmin,.08,zmax-zmin],'#c5bcb0')
    obj('wall:B:white','wall',[cx,h/2,zmin-.05],[xmax-xmin,h,.1],'#eee9df')
    obj('wall:A:window','window_wall',[cx,h/2,zmax],[xmax-xmin,h,.10],'#33383e')
    obj('wall:side','wall',[xmin-.05,h/2,cz],[.1,h,zmax-zmin],'#d7d0c3')
    obj('ceiling','ceiling',[cx,h+.05,cz],[xmax-xmin,.1,zmax-zmin],'#e5e0d7')
    obj('counter','counter',[3.8,.5,2.9],[1.8,1.0,.65],'#41464a')
    for i,(x,z) in enumerate([(-.5,.5),(-.5,2.8),(1.7,1.4),(3.2,1.4)]):obj(f'lamp:{i}','pendant',[x,2.4,z],[.29,.35,.29],'#303438')
    props=[]
    for o in layout['props']:
        p=dict(id=o['id'],type=o['type'],label=o['id'].replace(':',' '),transform=dict(position=o['position_m'],yaw=0),dims=o['dims_m'],support=o.get('support'),color='#ddd4be')
        if 'attach' in o:p['attach']=dict(actor=o['attach']['actor'],joint=o['attach']['pose_joint'],offset=[0,0,.04])
        props.append(p)
    props.append(dict(id='B:fry',type='fry',label='fry in right hand',transform=dict(position=[0,0,0],yaw=0),dims=[.01,.08,.01],visible=False,color='#e6b848'))
    lines=[(0,2.3,'A','Men vadå, menar du att du inte ska betala notan?'),(2.3,3.7,'B','Varför skulle jag ta notan?'),(3.7,5.8,'A','För det är ju så gentlemen gör.'),(5.8,7.9,'A','Eller liksom betala halva åtminstone?'),(7.9,9.3,'B','Varför skulle jag betala halva?'),(9.3,11.1,'A','För jag trodde du var en riktig man.'),(11.1,383/30,'B','Men jag känner inte ens dig?')]
    dialogue=[dict(start=t,end=e,speaker=s,text=text) for t,e,s,text in lines]
    beats=['hook','build-up','build-up','turn','reaction','punchline','payoff'];shots=[]
    for i,c in enumerate(layout['cameras'].values()):
        shots.append(dict(id=c['id'],source=dict(inSec=c['time_in'],outSec=c['time_out']),duration=c['time_out']-c['time_in'],actors=[dict(id=c['actor'])],camera=dict(keyframes=[dict(t=0,pos=c['position_m'],target=c['target_m'],up=c['up'],fov=c['vertical_fov_deg'])]),beat=beats[i],dialogue=[d for d in dialogue if d['end']>c['time_in'] and d['start']<c['time_out']],audioRange=[c['time_in'],c['time_out']],propOverrides=({'B:fry':dict(visible=True,attach=dict(actor='B',joint=16,offset=[0,.025,.015]))} if c['id']=='S2' else {'B:burger':dict(attach=dict(actor='B',joint=15,offset=[0,0,.035]))} if c['id']=='S5' else {})))
    spec=dict(schema='scen3d/2',units=dict(distance='meters',time='seconds',angle='degrees',up='y'),source=dict(clip='../klipp/d-dialog-notan.mp4',fps=30,width=576,height=1024,duration=383/30),defaultAvatar='procedural',set=objects,actors=actors,props=props,shots=shots,dialogue=dialogue,audio='data/source-audio.m4a',editLog=[dict(phase=2,action='Built from active layout-1b with fixed measured cameras and table sizes; no Phase3 operations.')])
    # Preserve the measured A far edge. Refine only the weak seat-side extent using
    # source body/table occlusion; keep this separate from the Phase1b archive.
    table=next(o for o in spec['set'] if o['id']=='table:A');delta=table['dims'][2]-.80;yaw=np.deg2rad(table['transform']['yaw']);table['dims'][2]=.80
    table['transform']['position'][0]-=delta/2*np.sin(yaw);table['transform']['position'][2]-=delta/2*np.cos(yaw)
    table['provenance']+='; Phase2 occlusion refinement: seat-side edge shortened .264m, measured far edge unchanged'
    spec['editLog'].append(dict(phase=2,action='A table depth 1.064 -> .800 m from body/table occlusion; fixed measured far edge. Raw layout.json unchanged. S7 hides unobserved foreground food/cup; can remains.'))
    # The intervening table is a qualitative prior in layout-1b, not a measured edge.
    empty=next(o for o in spec['set'] if o['id']=='table:empty:1');empty['transform']['position']=[-.65,.375,1.65]
    empty['provenance']+='; Phase2 qualitative placement brings the empty intervening tabletop into S7'
    spec['editLog'].append(dict(phase=2,action='Unmeasured empty table center [-1.05,.375,1.75] -> [-.65,.375,1.65] to make the intervening tabletop visible in S7.'))
    spec['set'].append(dict(id='table:empty:2',type='table',label='second empty intervening table',transform=dict(position=[-.65,.375,.80],yaw=0),dims=[.7,.75,.7],color='#202329',provenance='Phase2 qualitative empty-table row prior; not a measured tabletop.'))
    spec['editLog'].append(dict(phase=2,action='Added unmeasured empty table at [-.65,.375,.80] to complete the intervening table row; separated .15m from table:empty:1.'))
    next(p for p in props if p['id']=='B:fry')['dims']=[.01,.12,.01]
    for s in spec['shots']:
        if s['id']=='S2':s['propOverrides']['B:fry']['attach']=dict(actor='B',hand='Left',joint=15,offset=[-.025,.085,.005],rotation=[0,0,25])
        if s['id']=='S5':s['propOverrides']['B:burger']['attach']=dict(actor='B',hand='Left',joint=15,offset=[-.045,.11,.02])
        if s['id']=='S7':s['propOverrides']={f'A:{p}':dict(visible=False) for p in ['cup','burger','fries','tray','sauce']}
    write('scen3d.json',spec)
    fuse_hands()
    if not (ROOT/'data/source-audio.m4a').exists():subprocess.run(['ffmpeg','-v','error','-y','-i',str(ROOT.parent/'klipp/d-dialog-notan.mp4'),'-vn','-c:a','copy',str(ROOT/'data/source-audio.m4a')],check=True)
    print('Prepared',len(out),'motion frames;',len(objects),'set objects;',len(props),'props')

if __name__=='__main__':
    start=time.perf_counter();dependencies();prepare();write('data/prepare-2.json',dict(seconds=time.perf_counter()-start))
