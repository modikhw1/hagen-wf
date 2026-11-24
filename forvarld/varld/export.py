"""Local once-per-clip export. Never writes outside this directory."""
import os
os.environ['PYTHONIOENCODING']='utf-8'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,time,json,subprocess,shutil,warnings,hashlib
from pathlib import Path
import numpy as np,cv2,psutil
from scipy.ndimage import distance_transform_edt
from body_source import BODY_PLAN, BODY_BLEND, load_body_source, read_body_raw, body_dependencies, body_rig_names
ROOT=Path.cwd(); OUT=ROOT/'forvarld/varld'; PK=OUT/'paket/notan';PK.mkdir(parents=True,exist_ok=True)
PLAN=BODY_PLAN
WAIT_SECONDS=0.
def wait_heavy():
    global WAIT_SECONDS
    start=time.perf_counter()
    while True:
        busy=[]
        for p in psutil.process_iter(['name']):
            if p.info['name']=='blender.exe':
                try:
                    if '-b' in p.cmdline() or '--background' in p.cmdline():busy.append(p.pid)
                except psutil.AccessDenied:busy.append(p.pid)
        if not busy:
            WAIT_SECONDS+=time.perf_counter()-start
            return
        print('Waiting for headless/unknown Blender:',busy,flush=True);time.sleep(30)
def writejson(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def frame(cap,i):
    cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,im=cap.read()
    if not ok:raise RuntimeError(f'Frame {i} missing')
    return cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
def saveim(p,im):cv2.imwrite(str(p),cv2.cvtColor(im,cv2.COLOR_RGB2BGR))
def main():
    start=time.perf_counter();P=load_body_source(reuse_raw='--reuse-raw' in sys.argv);writejson(PK/'plan.json',P)
    writejson(OUT/'body-dependencies.json',dict(entryPoint='body_source.py:load_body_source / read_body_raw',files=body_dependencies(P),reuseRaw='--reuse-raw' in sys.argv))
    wait_heavy()
    if '--reuse-raw' not in sys.argv:
        with (OUT/'export-blender.log').open('w',encoding='utf8') as log:
            subprocess.run([r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','-b','--factory-startup',str(BODY_BLEND),'--threads','2','--python',str(OUT/'export_blender.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
    meshes=json.loads((PK/'meshes.json').read_text());cap=cv2.VideoCapture(P['kallvideo']);scenes=[]
    for s,m in zip(P['scener'],meshes):
        wait_heavy();a,b=s['ut'];directory=Path(s['varld']).parent; mask=np.load(directory/'masker.npy',mmap_mode='r')
        # Exact masked median at 288x512, never a full-resolution frame stack.
        stack=[]
        for i in range(b-a):
            im=cv2.resize(frame(cap,s['kalla'][0]+i),(288,512)).astype(np.float32)
            mk=cv2.resize(mask[s['lokal_start']+i].astype(np.uint8),(288,512),interpolation=cv2.INTER_NEAREST)>0
            mk=cv2.dilate(mk.astype(np.uint8),np.ones((5,5),np.uint8))>0
            im[mk]=np.nan;stack.append(im)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');plate=np.nanmedian(np.stack(stack),axis=0)
        del stack
        missing=np.isnan(plate[:,:,0]); inds=distance_transform_edt(missing,return_distances=False,return_indices=True);plate[missing]=plate[tuple(inds[:,missing])]
        saveim(PK/f"{s['id']}-plate.jpg",plate.astype(np.uint8))
        maskrows=int(np.ceil((b-a)/8));maskatlas=np.zeros((maskrows*256,8*144),np.uint8)
        for i in range(b-a):
            mm=cv2.resize(mask[s['lokal_start']+i].astype(np.uint8)*255,(144,256),interpolation=cv2.INTER_NEAREST)
            maskatlas[(i//8)*256:(i//8+1)*256,(i%8)*144:(i%8+1)*144]=mm
        cv2.imwrite(str(PK/f"{s['id']}-visibility.png"),maskatlas)
        # Select maximum target-person box-intersected visible segmentation area.
        boxes=json.loads((directory/'personer.json').read_text(encoding='utf8'))[s['personer'][0]['ingest_id']]
        scores=[]
        for i in range(b-a):
            box=boxes.get(str(s['lokal_start']+i))
            if box is None:scores.append(0);continue
            x0,y0,x1,y1=np.array(box)*np.array([mask.shape[2]/576,mask.shape[1]/1024]*2)
            scores.append(int(mask[i,max(0,int(y0)):int(y1),max(0,int(x0)):int(x1)].sum()))
        ref=int(np.argmax(scores));source=frame(cap,s['kalla'][0]+ref)
        for t in P.get('skarmtext',[]):
            if t['ut'][0]<=a+ref<t['ut'][1]:
                x,y,w,h=map(int,t['box']);erase=np.zeros(source.shape[:2],np.uint8);erase[max(0,y-5):y+h+5,max(0,x-5):x+w+5]=255
                source=cv2.inpaint(source,erase,5,cv2.INPAINT_TELEA)
        rawpath=PK/f"{m['stem']}-raw.npz"
        if not rawpath.exists():rawpath=OUT/'intermediat'/rawpath.name
        raw=read_body_raw(m['stem']);pos=raw['pos'];ids=raw['ids'];weights=raw['weights'];tris=raw['tri'];mats=raw['matrices'];visibility=raw['visible'].tolist();n=len(tris)
        M=mats[ref].transpose(0,2,1);hp=np.c_[pos,np.ones(len(pos))]
        posed=sum(np.einsum('nij,nj->ni',M[ids[:,k]],hp)*weights[:,k,None] for k in range(4))[:,:3]
        cam=P['renderkamera'];key=cam['nycklar'][a+ref];C=np.linalg.inv(np.array(key['matris']));q=(C@np.c_[posed,np.ones(len(pos))].T).T[:,:3]
        focal=key['lins_mm']/cam['sensor_bredd_mm']*576;uv=np.c_[288+focal*q[:,0]/-q[:,2],512-focal*q[:,1]/-q[:,2]]
        # Generic MHR scalp omits hair/cap volume. Fit only its crown to the measured
        # top silhouette at this one reference. Bones/palettes are not changed.
        names=body_rig_names()
        head=(weights*(ids>=names.index('c_head'))).sum(1)>.5
        top=float(uv[head,1].min());bottom=float(uv[head,1].max());hx=uv[head,0]
        x0=max(0,int(hx.min()/4));x1=min(144,int(hx.max()/4))
        ys=np.where(mask[ref,:,x0:x1].any(1))[0]
        crownPixels=float(np.clip(top-(ys[0]*4 if len(ys) else top),0,(bottom-top)*.35))
        blend=sum(M[ids[:,k]]*weights[:,k,None,None] for k in range(4))
        strength=np.clip((top+(bottom-top)*.45-uv[:,1])/((bottom-top)*.45),0,1)*head
        delta=np.array(key['matris'])[:3,1][None,:]*(crownPixels*(-q[:,2])/focal*strength)[:,None]
        pos=pos+np.linalg.solve(blend[:,:3,:3],delta[:,:,None])[:,:,0]
        hp=np.c_[pos,np.ones(len(pos))];posed=np.einsum('nij,nj->ni',blend,hp)[:,:3]
        q=(C@np.c_[posed,np.ones(len(pos))].T).T[:,:3];uv=np.c_[288+focal*q[:,0]/-q[:,2],512-focal*q[:,1]/-q[:,2]]
        # CPU z buffer identifies source-facing visible surface, including self occlusion.
        zbuf=np.full((1024,576),np.inf,np.float32)
        def pixels(p,width,height):
            lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),[width-1,height-1])
            if np.any(hi<lo):return None
            xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));A=np.c_[p,np.ones(3)].T
            if abs(np.linalg.det(A))<1e-6:return None
            bary=np.linalg.inv(A)@np.stack([xx.ravel()+.5,yy.ravel()+.5,np.ones(xx.size)])
            good=(bary>=-.001).all(0);return xx.ravel()[good],yy.ravel()[good],bary[:,good].T
        for tr in tris:
            r=pixels(uv[tr],576,1024)
            if r is None:continue
            x,y,bc=r;dep=1/(bc@(1/-q[tr,2]));zbuf[y,x]=np.minimum(zbuf[y,x],dep)
        grid=int(np.ceil(np.sqrt(n)));cell=512//grid;tex=np.zeros((512,512,3),np.uint8);known=np.zeros((512,512),bool);atlasuv=[]
        targetmask=cv2.resize(mask[ref].astype(np.uint8),(576,1024),interpolation=cv2.INTER_NEAREST)>0
        for j,tr in enumerate(tris):
            x=(j%grid)*cell;y=(j//grid)*cell
            au=np.array([[x+1,y+1],[x+cell-1,y+1],[x+1,y+cell-1]],float);atlasuv.extend(au/512)
            r=pixels(au,512,512)
            if r is None:continue
            ax,ay,bc=r;world=bc@posed[tr];cq=(C@np.c_[world,np.ones(len(world))].T).T
            sx=np.rint(288+focal*cq[:,0]/-cq[:,2]).astype(int);sy=np.rint(512-focal*cq[:,1]/-cq[:,2]).astype(int)
            inside=(sx>=0)&(sx<576)&(sy>=0)&(sy<1024)&(cq[:,2]<0);sx=np.clip(sx,0,575);sy=np.clip(sy,0,1023)
            normal=np.cross(posed[tr[1]]-posed[tr[0]],posed[tr[2]]-posed[tr[0]])
            front=np.dot(normal,np.array(key['matris'])[:3,3]-world.mean(0))>0
            good=inside & targetmask[sy,sx] & (np.abs(zbuf[sy,sx]+cq[:,2])<.025) & front
            tex[ay[good],ax[good]]=source[sy[good],sx[good]];known[ay[good],ax[good]]=True
        # Unseen texels use nearest seen surface in rest-space, not nearest atlas tile.
        from scipy.spatial import cKDTree
        flat=tris.ravel(); expanded=pos[flat]; au=np.array(atlasuv);centres=au.reshape(-1,3,2).mean(1)*512
        cols=[];seen=[]
        for j,(cx,cy) in enumerate(centres):
            x=(j%grid)*cell;y=(j//grid)*cell;k=known[y:y+cell,x:x+cell]
            cols.append(np.median(tex[y:y+cell,x:x+cell][k],axis=0) if k.any() else [100,80,70]);seen.append(k.any())
        seen=np.array(seen);tc=pos[tris].mean(1)
        if seen.any():
            tree=cKDTree(tc[seen]);nearest=np.flatnonzero(seen)[tree.query(tc)[1]]
            for j in range(n):
                x=(j%grid)*cell;y=(j//grid)*cell;region=tex[y:y+cell,x:x+cell];k=known[y:y+cell,x:x+cell]
                if k.any():
                    ii=distance_transform_edt(~k,return_distances=False,return_indices=True);region[~k]=region[tuple(ii[:,~k])]
                else:region[:]=cols[nearest[j]]
        saveim(PK/f"{m['stem']}-texture.png",tex)
        # Binary layout: expanded positions, skin indices (float), weights, UV, palettes.
        au[:,1]=1-au[:,1]
        arrays=[expanded.astype('<f4'),ids[flat].astype('<f4'),weights[flat].astype('<f4'),au.astype('<f4'),mats.astype('<f4')]
        with (PK/f"{m['stem']}.bin").open('wb') as f:
            for ar in arrays:f.write(ar.tobytes())
        # raw intermediates retained outside served package.
        rawdir=OUT/'intermediat';rawdir.mkdir(exist_ok=True)
        if rawpath.parent==PK:rawpath.replace(rawdir/rawpath.name)
        m.update(referenceLocalFrame=ref,referenceSourceFrame=s['kalla'][0]+ref,texture='512x512 triangle atlas',seenTriangles=int(seen.sum()),visible=visibility,crownFitPixels=crownPixels,crownFitStatus='assumed mesh-only hair/cap volume from measured top silhouette; skeleton unchanged')
        scenes.append(dict(id=s['id'],ut=s['ut'],source=s['kalla'],person=m,plate=f"{s['id']}-plate.jpg",visibilityAtlas=f"{s['id']}-visibility.png",visibilityRows=maskrows,plateUnknownFraction=float(missing.mean())))
        print(s['id'],m['triangles'],'triangles',int(seen.sum()),'seen',flush=True)
    cap.release()
    subprocess.run(['ffmpeg','-y','-v','error','-i',P['kallvideo'],'-vn','-c:a','aac','-b:a','96k',str(PK/'audio.m4a')],check=True)
    shutil.copyfile(P['kallvideo'],PK/'source.mp4')
    manifest=dict(schema='forvarld/1',fps=30,frames=len(P['kallrutor']),width=576,height=1024,scenes=scenes,cameras=P['renderkamera'],room=P['objekt'],text=P['skarmtext'],timeMap=P['tidskarta'],
        provenance=dict(measured=['Plan camera keys, MHR body animation, visibility, source audio, source RGB, segmentation masks, text boxes/timing','Per-frame source segmentation visibility matte at 144x256: clips 3D only in tracked plate view; explicitly a hybrid, disabled for template/new camera'],assumed=['Existing plan skeleton/body fit and support corrections preserved; body shape is MHR generic, not scanned identity','Crown of head mesh fitted once to reference mask top to approximate missing hair/cap volume; bone matrices unchanged','Top four skin weights normalized','Largest mask intersected with tracked box approximates least occluded reference','Source subtitles in reference texture removed by local inpainting','Unseen body triangles filled from nearest seen triangle in rest-space; no invented face detail','Never observed background pixels filled from nearest observed pixel'],template=['Furnished restaurant from plan','Tripod camera derived from tracked setup','PS2 raster treatment']),exportSeconds=round(time.perf_counter()-start-WAIT_SECONDS,3),exportWallSeconds=round(time.perf_counter()-start,3),waitForOtherBlenderSeconds=round(WAIT_SECONDS,3))
    # plan is an offline audit input; the viewer only requests manifest + binary/images/audio.
    # Semantic data is an explicit data file, never rebuilt by the old UI migration.
    metadata=json.loads((OUT/'world-metadata.json').read_text(encoding='utf8'))
    for key in ('lines','cardBindings','backdrops'):manifest[key]=metadata[key]
    writejson(PK/'manifest.json',manifest);writejson(OUT/'export-result.json',dict(seconds=manifest['exportSeconds'],wallSeconds=manifest['exportWallSeconds'],waitSeconds=manifest['waitForOtherBlenderSeconds'],packageBytes=sum(x.stat().st_size for x in PK.iterdir() if x.is_file()),plan=str(PLAN),meshes=meshes))
if __name__=='__main__':main()
