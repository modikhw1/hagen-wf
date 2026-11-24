"""Local visibility-aware texture fusion and paper-theatre assets; no Blender needed.

Run from repo root, after export.py. All outputs stay beside this script.
Manual image boundaries below are explicitly assumptions, never measurements.
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import sys, json, time
from pathlib import Path
import numpy as np
import cv2
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from body_source import load_body_source, read_body_raw

OUT = Path(__file__).resolve().parent
PK = OUT/'paket/notan'
W,H = 576,1024
# Reviewed table/object contours in source pixels. The hands are NOT foreground
# objects: the per-frame person mask removes them from these object cards.
CONTOURS = {
 's1': [[0,755],[48,755],[45,680],[72,660],[112,665],[118,755],[139,754],[138,665],[162,652],[239,654],[256,679],[251,750],[323,718],[351,655],[433,633],[471,654],[470,737],[550,768],[576,765],[576,1024],[0,1024]],
 's2': [[0,802],[16,802],[24,701],[52,672],[141,666],[176,691],[174,792],[184,792],[198,723],[254,707],[273,670],[305,695],[310,716],[328,767],[348,747],[430,727],[478,749],[498,795],[576,802],[576,1024],[0,1024]],
 's3': [[0,736],[47,737],[49,651],[77,634],[114,647],[122,731],[137,731],[138,627],[170,610],[231,622],[247,644],[248,726],[326,706],[349,613],[424,601],[460,626],[470,714],[576,758],[576,1024],[0,1024]],
 's5': [[0,836],[63,835],[65,657],[85,632],[163,628],[192,647],[190,751],[222,715],[290,696],[330,721],[350,721],[414,704],[485,718],[504,789],[576,812],[576,1024],[0,1024]],
 's6': [[0,745],[44,744],[45,665],[70,644],[111,654],[119,747],[139,743],[138,645],[168,623],[232,633],[247,657],[246,732],[325,718],[348,624],[422,616],[463,644],[469,735],[576,763],[576,1024],[0,1024]],
 's7': [[153,550],[244,482],[260,480],[263,437],[286,434],[296,441],[296,465],[311,450],[348,468],[408,468],[434,483],[495,550],[495,566],[154,568]],
}
NEAR_S7=[[0,699],[417,709],[422,669],[457,649],[513,652],[550,681],[569,747],[576,784],[576,1024],[0,1024]]
HELD_S5=[[329,579],[360,553],[373,532],[420,529],[456,552],[488,559],[515,591],[509,628],[482,643],[441,645],[408,658],[373,640],[344,637]]

def writejson(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def readjson(p): return json.loads(p.read_text(encoding='utf8'))
def save(p,rgb):
    if rgb.shape[2]==4:
        rgb=rgb.copy();rgb[rgb[:,:,3]==0,:3]=0
    cv2.imwrite(str(p),cv2.cvtColor(rgb, cv2.COLOR_RGBA2BGRA if rgb.shape[2]==4 else cv2.COLOR_RGB2BGR))
def frame(cap,i):
    cap.set(cv2.CAP_PROP_POS_FRAMES,int(i)); ok,im=cap.read()
    if not ok: raise RuntimeError(f'Cannot read frame {i}')
    return cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
def polygon(points):
    a=np.zeros((H,W),np.uint8)
    if points:cv2.fillPoly(a,[np.asarray(points,np.int32)],255)
    return a>0
def projected(pos,key):
    C=np.array(key['matris']); q=(pos-C[:3,3])@C[:3,:3]
    focal=key['lins_mm']/36*W
    return np.c_[W/2+focal*q[:,0]/-q[:,2],H/2-focal*q[:,1]/-q[:,2]],-q[:,2]
def pose(raw,i):
    mats=raw['matrices'][i].transpose(0,2,1)
    blend=np.sum(mats[raw['ids']]*raw['weights'][:,:,None,None],axis=1)
    return np.einsum('nij,nj->ni',blend,np.c_[raw['pos'],np.ones(len(raw['pos']))])[:,:3]
def raster(p,w,h):
    lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),[w-1,h-1])
    if np.any(hi<lo): return None
    x,y=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));xx=x.ravel()+.5;yy=y.ravel()+.5
    a,b,c=p;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(den)<1e-8:return None
    u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
    v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
    bc=np.c_[u,v,1-u-v];good=(bc>=-.001).all(1)
    return x.ravel()[good],y.ravel()[good],bc[good]
def zbuffer(uv,depth,tris):
    z=np.full((H,W),np.inf,np.float32)
    for tr in tris:
        if depth[tr].min()<=0: continue
        r=raster(uv[tr],W,H)
        if r is None:continue
        x,y,bc=r;dep=1/(bc@(1/depth[tr]));z[y,x]=np.minimum(z[y,x],dep)
    return z
def source_mask(mask,i,box=None):
    mk=cv2.resize(mask[i].astype(np.uint8),(W,H),interpolation=cv2.INTER_NEAREST)
    if box is not None:
        x0,y0,x1,y1=np.rint(box).astype(int);clip=np.zeros_like(mk);clip[max(0,y0):min(H,y1),max(0,x0):min(W,x1)]=1;mk*=clip
    return mk>0
def clean_text(im,P,sf):
    erase=np.zeros((H,W),np.uint8)
    for t in P.get('skarmtext',[]):
        if t['ut'][0]<=sf<t['ut'][1]:
            x,y,w,h=map(int,t['box']);erase[max(0,y-5):min(H,y+h+5),max(0,x-5):min(W,x+w+5)]=255
    return cv2.inpaint(im,erase,4,cv2.INPAINT_TELEA),erase>0
def region_ids(raw,names):
    dominant=raw['ids'][np.arange(len(raw['pos'])),raw['weights'].argmax(1)]
    reg=[]
    for i in dominant:
        n=names[i]
        if n.startswith('c_head') or n in ['c_jaw','c_teeth'] or i>=113: reg.append(4)
        elif i>=109:reg.append(3)
        elif 'leg' in n or 'foot' in n or 'tarsal' in n or 'ball' in n or n=='root':reg.append(1)
        elif (41<=i<=63) or (77<=i<=99):reg.append(3)
        elif 'lowarm' in n or 'wrist_twist' in n:reg.append(2)
        else:reg.append(0)
    return np.asarray(reg)

def bake(s,scene,P,cap):
    m=s['person'];stem=m['stem'];raw=read_body_raw(stem)
    tri=raw['tri'];n=len(tri);grid=int(np.ceil(np.sqrt(n)));cell=512//grid
    names=[b['name'] for b in readjson(PK/'meshes.json')[int(s['id'][1:])-1]['skeleton']]
    vreg=region_ids(raw,names);treg=np.array([np.bincount(vreg[t],minlength=5).argmax() for t in tri])
    # A fixed triangle atlas; each texel stores a surface coordinate, not a screen UV.
    atlasuv=[];ax=[];ay=[];bcs=[];ti=[]
    for j in range(n):
        x=(j%grid)*cell;y=(j//grid)*cell
        au=np.array([[x+1,y+1],[x+cell-1,y+1],[x+1,y+cell-1]],float);atlasuv.extend(au/512)
        r=raster(au,512,512)
        if r:
            xx,yy,bc=r;ax.extend(xx);ay.extend(yy);bcs.extend(bc);ti.extend([j]*len(xx))
    ax=np.asarray(ax);ay=np.asarray(ay);bc=np.asarray(bcs);ti=np.asarray(ti);reg=treg[ti]
    tex=np.zeros((512,512,3),np.uint8);known=np.zeros((512,512),bool)
    quality=np.full(len(ax),-np.inf);colour=np.zeros((len(ax),3),np.uint8);chosen=np.full(len(ax),-1,np.int16)
    directory=Path(scene['varld']).parent;mask=np.load(directory/'masker.npy',mmap_mode='r')
    boxes=readjson(directory/'personer.json')[scene['personer'][0]['ingest_id']]
    # Choose a stable reference for identity; remaining frames reveal hidden surfaces.
    ref=m['referenceLocalFrame'];refs=sorted(set([ref,(m['frames']//2)]+np.linspace(0,m['frames']-1,9).astype(int).tolist()))
    foreground=polygon(CONTOURS.get(s['id'],[]));rejected=dict(mask=0,depth=0,foreground=0,clothing=0)
    for i in refs:
        sf=s['source'][0]+i;key=P['renderkamera']['nycklar'][sf]
        posed=pose(raw,i);uv,dep=projected(posed,key);z=zbuffer(uv,dep,tri)
        points=np.einsum('ni,nij->nj',bc,posed[tri[ti]]);xy,d=projected(points,key)
        inside=(xy[:,0]>=0)&(xy[:,0]<W)&(xy[:,1]>=0)&(xy[:,1]<H)&(d>0)
        x=np.clip(xy[:,0].astype(int),0,W-1);y=np.clip(xy[:,1].astype(int),0,H-1)
        mk=source_mask(mask,scene['lokal_start']+i,boxes.get(str(scene['lokal_start']+i)))
        # Erode low-resolution segmentation boundaries to avoid a wall/food halo.
        mk=cv2.erode(mk.astype(np.uint8),np.ones((5,5),np.uint8))>0
        im,textmask=clean_text(frame(cap,sf),P,sf);col=im[y,x]
        normals=np.cross(posed[tri[:,1]]-posed[tri[:,0]],posed[tri[:,2]]-posed[tri[:,0]])
        normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-10)
        direction=np.array(key['matris'])[:3,3]-points;direction/=np.linalg.norm(direction,axis=1,keepdims=True)
        facing=np.einsum('ij,ij->i',normals[ti],direction)
        own=(np.abs(z[y,x]-d)<.014)&(facing>.05)
        # Source segmentation can include a held burger. Explicit reviewed regions
        # and dark-clothing checks reject those pixels, also when labelled person.
        fg=foreground[y,x]&~mk[y,x]
        cloth=(reg==0)|((reg==2)&(m['person']!='C'))
        dark=(col.max(1)<155)&(col[:,0].astype(float)<col[:,2]*1.35+14)&(col[:,0].astype(float)<col[:,1]*1.16+8)
        skin=(col[:,2].astype(float)>col[:,0]*.43)&(col[:,1].astype(float)>col[:,0]*.5)&(col[:,0].astype(float)>col[:,1]*1.08)&(col[:,0].astype(float)>col[:,2]*1.14)
        good=inside&mk[y,x]&own&~fg&~textmask[y,x]&(~cloth|dark)&((reg!=3)|skin)&((reg!=1)|dark)
        # Table polygons exclude clothing too, except genuinely dark visible sleeves.
        good &= ~(foreground[y,x]&((reg==0)|(reg==1)|(reg==2)))
        if s['id']=='s5':good &= ~((x>310)&(x<555)&(y>490)&(y<665))
        score=facing + (.4 if i==ref else 0) - abs(i-ref)/max(1,m['frames'])*.08
        # Prefer the reference on the face; use others only where not observed.
        score += (reg==4)*(.8 if i==ref else 0)
        take=good&(score>quality);quality[take]=score[take];colour[take]=col[take];chosen[take]=i
        rejected['mask']+=int((inside&~mk[y,x]).sum());rejected['depth']+=int((inside&~own).sum());rejected['foreground']+=int(fg.sum());rejected['clothing']+=int((cloth&~dark).sum())
    tex[ay,ax]=colour;known[ay,ax]=chosen>=0
    # Save the truth before filling: white observed, black assumed/padding.
    cv2.imwrite(str(PK/f'{stem}-observed.png'),known.astype(np.uint8)*255)
    # Fill only from the SAME semantic body region, using rest-space proximity.
    # Legs never seen in seated shots borrow plain dark cloth, not skin/food.
    centres=raw['pos'][tri].mean(1);cols=np.zeros((n,3));seen=np.zeros(n,bool)
    for j in range(n):
        x=(j%grid)*cell;y=(j//grid)*cell;k=known[y:y+cell,x:x+cell];seen[j]=k.any()
        if seen[j]:cols[j]=np.median(tex[y:y+cell,x:x+cell][k],axis=0)
    darkcloth=colour[(chosen>=0)&(reg==0)]
    fallback=np.median(darkcloth,axis=0) if len(darkcloth) else np.array([35,37,40])
    defaults={0:fallback,1:fallback*.8,2:fallback if m['person']!='C' else [160,115,100],3:[160,115,100],4:[125,90,75]}
    for j in range(n):
        x=(j%grid)*cell;y=(j//grid)*cell;k=known[y:y+cell,x:x+cell];tile=tex[y:y+cell,x:x+cell]
        if k.any():
            ii=distance_transform_edt(~k,return_distances=False,return_indices=True);tile[~k]=tile[tuple(ii[:,~k])]
        else:
            candidates=np.flatnonzero(seen&(treg==treg[j]))
            tile[:]=cols[candidates[np.argmin(np.linalg.norm(centres[candidates]-centres[j],axis=1))]] if len(candidates) else defaults[treg[j]]
    save(PK/f'{stem}-texture.png',tex)
    flat=tri.ravel();au=np.asarray(atlasuv);au[:,1]=1-au[:,1]
    with (PK/f'{stem}.bin').open('wb') as f:
        for ar in [raw['pos'][flat],raw['ids'][flat],raw['weights'][flat],au,raw['matrices']]:f.write(np.asarray(ar,dtype='<f4').tobytes())
    m.update(fusionFrames=refs,seenTriangles=int(seen.sum()),observedTexels=int(known.sum()),surfaceTexels=len(ax),assumedSurfaceFraction=float(1-known.sum()/len(ax)),observedMap=f'{stem}-observed.png',fillMethod='Same semantic body region, nearest observed rest-space triangle; never-seen seated legs plain median dark clothing * .8 (assumed).',fusionRejections=rejected,crownFitPixels=0,crownFitStatus='Original exported mesh restored; silhouette supplied by separate head-attached card.')
    # Shared data used by layer creation, not retained in served package.
    print(s['id'],len(refs),'frames fused;',int(known.sum()),'observed /',len(ax),'surface texels',flush=True)
    return raw

def make_layers(s,scene,P,cap,raw):
    m=s['person'];ref=m['frames']//2;sf=s['source'][0]+ref;key=P['renderkamera']['nycklar'][sf]
    im,tm=clean_text(frame(cap,sf),P,sf);directory=Path(scene['varld']).parent
    mask=np.load(directory/'masker.npy',mmap_mode='r');boxes=readjson(directory/'personer.json')[scene['personer'][0]['ingest_id']]
    mk=source_mask(mask,scene['lokal_start']+ref,boxes.get(str(scene['lokal_start']+ref)))
    posed=pose(raw,ref);uv,dep=projected(posed,key)
    names=[b['name'] for b in readjson(PK/'meshes.json')[int(s['id'][1:])-1]['skeleton']]
    headix=names.index('c_head');head=(raw['weights']*(raw['ids']==headix)).sum(1)>.3
    hu=uv[head];cx=float(np.median(hu[:,0]));top=float(hu[:,1].min());bottom=float(hu[:,1].max());hh=bottom-top
    # A full source head restores the genuine silhouette; below the jaw only dark
    # side hair is retained. Card is rigid to c_head, with source-pose expression.
    xx,yy=np.meshgrid(np.arange(W),np.arange(H));radius=max(float(np.ptp(hu[:,0]))*.72,14)
    upper=(abs(xx-cx)<radius)&(yy>top-hh*.5)&(yy<bottom+hh*.20)
    longhair=(m['person']=='A')&(abs(xx-cx)<radius*1.25)&(abs(xx-cx)>radius*.4)&(yy>=bottom-hh*.10)&(yy<bottom+hh*.95)&(im.max(2)<145)
    # Local GrabCut uses only source RGB and the existing segmentation as seeds.
    # It removes the 4-pixel coarse-mask wall halo, without inventing hair pixels.
    roi=upper|longhair
    dilated=cv2.dilate(mk.astype(np.uint8),np.ones((9,9),np.uint8))>0
    seeds=np.where(mk,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype(np.uint8)
    seeds[~dilated|~cv2.dilate(roi.astype(np.uint8),np.ones((15,15),np.uint8)).astype(bool)]=cv2.GC_BGD
    central=(abs(xx-cx)<radius*.48)&(yy>top+hh*.1)&(yy<bottom+hh*.1)
    definite=(cv2.erode(mk.astype(np.uint8),np.ones((13,13),np.uint8))>0)&upper&((im.max(2)<130)|central)
    wall=(im.min(2)>175)&((im.max(2).astype(int)-im.min(2))<45)&~central
    seeds[wall]=cv2.GC_BGD
    seeds[definite]=cv2.GC_FGD
    cv2.grabCut(im,seeds,None,np.zeros((1,65),np.float64),np.zeros((1,65),np.float64),3,cv2.GC_INIT_WITH_MASK)
    precise=(seeds==cv2.GC_FGD)|(seeds==cv2.GC_PR_FGD)
    alpha=(precise&roi&~tm&~wall).astype(np.uint8)*255
    # Keep only components connected to upper head (remove isolated raised hands).
    count,labels,stats,_=cv2.connectedComponentsWithStats(alpha)
    for k in range(1,count):
        if not ((labels==k)&(yy<bottom-hh*.2)).any():alpha[labels==k]=0
    headrgba=np.dstack([im,alpha]);save(PK/f"{s['id']}-head.png",headrgba)
    headdepth=float(dep[head].min())-.008
    # Reconstruct c_head's actual world transform from the skin palette and rest.
    skeleton=readjson(PK/'meshes.json')[int(s['id'][1:])-1]['skeleton']
    rest=np.array(skeleton[headix]['restMatrixColumnMajor']).reshape(4,4).T
    headworld=raw['matrices'][ref,headix].T@rest
    layers=dict(referenceLocalFrame=ref,referenceSourceFrame=sf,head=dict(texture=f"{s['id']}-head.png",depth=headdepth,bone=headix,restMatrix=rest.tolist(),referenceBoneWorld=headworld.tolist(),status='assumed 2.5D source-head cutout, rigid attachment to measured c_head; expression frozen, hair not simulated'),camera=key)
    contour=polygon(CONTOURS.get(s['id'],[]))
    if contour.any():
        # The missing-mask portion at the table is the source foreground; retain
        # explicitly reviewed bright cups/bags even if the coarse mask includes them.
        foreground=contour&~cv2.erode(mk.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
        if s['id']=='s5':foreground|=polygon(HELD_S5)
        # A person-mask hole is not proof of an object elsewhere in the room.
        rgba=np.dstack([im,foreground.astype(np.uint8)*255]);save(PK/f"{s['id']}-foreground.png",rgba)
        torso=(raw['weights']*((raw['ids']>=33)&(raw['ids']<=36))).sum(1)>.35
        depth=float(np.median(dep[torso]))-.22
        layers['foreground']=dict(texture=f"{s['id']}-foreground.png",depth=max(.2,depth),status='assumed table-depth camera-facing card; source contour manually reviewed, alpha from inverse person mask; fixed midpoint objects, hand holes are not reconstructed')
        if s['id']=='s7':
            near=polygon(NEAR_S7);save(PK/'s7-near-foreground.png',np.dstack([im,near.astype(np.uint8)*255]))
            layers['nearForeground']=dict(texture='s7-near-foreground.png',depth=max(.4,depth*.28),status='assumed nearer A-table card, separate from distant B-table; no recovered side surfaces')
    s['layers']=layers
    # Small audit sheet makes head/foreground selection reviewable.
    audit=np.zeros((H,W*3,3),np.uint8)+64;audit[:,:W]=im
    for j,a in [(1,alpha),(2,foreground.astype(np.uint8)*255 if contour.any() else np.zeros((H,W),np.uint8))]:
        a=a[:,:,None]/255;audit[:,j*W:(j+1)*W]=(im*a+audit[:,j*W:(j+1)*W]*(1-a)).astype(np.uint8)
    save(OUT/'bilder'/f"{s['id']}-layer-audit.png",cv2.resize(audit,(864,512),interpolation=cv2.INTER_NEAREST))

def adjust_room(s,M,raw):
    """Conservative vertex clearance against simple template boxes, not a room fit."""
    points=np.concatenate([pose(raw,int(i)) for i in np.linspace(0,len(raw['matrices'])-1,7)])
    edits=[]
    for j,o in enumerate(M['room']):
        a,b=o.get('synlig_ut',[0,M['frames']])
        if not a<=s['source'][0]<b or o.get('deltyp') not in ['golv','vagg','stol']:continue
        centre=np.array(o['pos_m'],float);size=np.array(o['matt_m'],float);angle=o['rotation_rad'][2]
        R=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1.]])
        if o.get('deltyp')=='golv':centre[2]=min(centre[2],float(points[:,2].min())-size[2]/2-.025)
        else:
            local=(points-centre)@R;half=size/2+.035
            if not (abs(local)<half).all(1).any():continue
            # Move along the narrowest horizontal box axis away from the person.
            axis=int(np.argmin(size[:2]));lo=local[:,axis].min();hi=local[:,axis].max()
            shift=hi+half[axis] if abs(hi+half[axis])<abs(lo-half[axis]) else lo-half[axis]
            centre+=R[:,axis]*shift
        if not np.allclose(centre,o['pos_m']):edits.append(dict(objectIndex=j,id=o['id'],position=centre.tolist(),original=o['pos_m'],status='template',reason='Viewer-only conservative clearance from body vertices sampled at 7 poses, 3.5 cm margin; floor below all sampled soles.'))
    s['roomAdjustments']=edits

def main():
    start=time.perf_counter();M=readjson(PK/'manifest.json');P=load_body_source();cap=cv2.VideoCapture(P['kallvideo'])
    for s,scene in zip(M['scenes'],P['scener']):
        raw=read_body_raw(s['person']['stem']) if '--layers-only' in sys.argv else bake(s,scene,P,cap)
        make_layers(s,scene,P,cap,raw);adjust_room(s,M,raw)
    cap.release()
    M['schema']='forvarld/2'
    elapsed=round(time.perf_counter()-start,3)
    if '--layers-only' in sys.argv:M['lastLayerOnlySeconds']=elapsed
    else:M['refineSeconds']=elapsed
    M['provenance']['measured']+=['Multi-frame body RGB samples accepted only inside target-person segmentation and own frontmost mesh depth (14 mm tolerance), with source text rejected; observed texture maps preserve evidence','Original exported skin matrices, weights and mesh coordinates preserved byte-for-byte in v2; seven people instances only, s4 bystander stays on plate']
    M['provenance']['assumed']+=['Reviewed table polygons and dark-clothing filter reject food/box contamination not resolved by coarse person segmentation','Unobserved texture fill is plain same-region clothing colour, with per-texel observed/assumed maps; no inferred detail','Rigid head/hair source cards at measured head depth; fixed source expression and hair pose','Foreground inverse-person-mask cards at assumed table depth 22 cm in front of torso; midpoint frame, no reconstructed hands or object backs','Moderate tripod moves 12 cm sideways and 8 cm closer, same orientation/lens; large orbit unsupported','Room collision adjustments are viewer-only template placement assumptions, logged separately']
    M['provenance']['assumed']+=['Layered mode replaces template table surfaces and legs with the source foreground cards, preventing duplicate table geometry clipping the cards','Source-head alpha refined locally by GrabCut seeded from the measured mask and central face/dark-hair pixels; pale neutral wall pixels outside face excluded','s5 held burger source contour manually traced at midpoint; s7 near table uses a second card at 28 percent of far-table camera depth (assumed)']
    M['provenance']['assumed']=[x for x in M['provenance']['assumed'] if not x.startswith('Crown of head') and not x.startswith('Unseen body triangles')]
    M['renderModes']=dict(ps2=dict(internalResolution=[192,342],outputResolution=[576,1024],nearestUpscale=True,vertexSnap=True,affineUV=True,rgbBits=[5,5,5],bayerDither='4x4',lighting='flat derivative normals',antialias=False),plain=dict(internalResolution=[576,1024],vertexSnap=False,affineUV=False,colourReduction=False,antialias=False))
    for key in M['provenance']:M['provenance'][key]=list(dict.fromkeys(M['provenance'][key]))
    writejson(PK/'manifest.json',M)
    writejson(OUT/'refine-result.json',dict(seconds=M['refineSeconds'],packageBytes=sum(p.stat().st_size for p in PK.iterdir() if p.is_file()),scenes=[dict(id=s['id'],observed=s['person']['observedTexels'],surface=s['person']['surfaceTexels'],assumedFraction=s['person']['assumedSurfaceFraction']) for s in M['scenes']]))
    print('Refined in',elapsed,'seconds',flush=True)
if __name__=='__main__':main()
