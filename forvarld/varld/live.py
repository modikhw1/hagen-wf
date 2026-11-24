"""Live masks from source RGB, measured joints and a frozen body snapshot. No Blender."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import json,time
import cv2,numpy as np
from body_source import load_body_source,read_body_raw
from refine import projected,pose
cv2.setNumThreads(1)
O=Path('forvarld/varld');PK=O/'paket/notan'
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))

def reject_text(mask,texts,sf,scale=4):
 for t in texts:
  if t['ut'][0]<=sf<t['ut'][1]:
   x,y,w,h=np.asarray(t['box'])/scale;pad=12/scale
   mask[max(0,int(y-pad)):int(np.ceil(y+h+pad)),max(0,int(x-pad)):int(np.ceil(x+w+pad))]=0

def follow_patch(frames,ref,region):
 points=cv2.goodFeaturesToTrack(frames[ref],40,.01,3,mask=region)
 if points is None or len(points)<6:return None
 offsets={ref:np.zeros(2)};counts=[]
 for direction in [-1,1]:
  prev=points.copy();total=np.zeros(2)
  for i in range(ref+direction,len(frames) if direction>0 else -1,direction):
   nxt,status,_=cv2.calcOpticalFlowPyrLK(frames[i-direction],frames[i],prev,None,winSize=(21,21),maxLevel=2)
   good=status.ravel()>0
   if good.sum()<6:return None
   total+=np.median((nxt-prev)[good].reshape(-1,2),axis=0);offsets[i]=total.copy();counts.append(int(good.sum()));prev=nxt[good].reshape(-1,1,2)
 return offsets,min(counts,default=len(points))

def main():
 M=read(PK/'manifest.json');P=load_body_source();meshes=read(PK/'meshes.json');start=time.perf_counter();audit=[]
 for s,scene,mesh in zip(M['scenes'],P['scener'],meshes):
  if s['id']!=scene['id'] or s['person']['stem']!=mesh['stem']:raise ValueError('Body snapshot differs; full export required.')
  raw=read_body_raw(s['person']['stem']);masks=np.load(Path(scene['varld']).parent/'masker.npy',mmap_mode='r');sk=mesh['skeleton'];names=[b['name'] for b in sk];n=s['source'][1]-s['source'][0];rows=(n+7)//8
  if len(raw['matrices'])!=n:raise ValueError('Body frame count differs; full export required.')
  atlas=np.zeros((rows*256,8*144,3),np.uint8);depths=[];heads=[];jointuv=[]
  cap=cv2.VideoCapture(str(PK/'source.mp4'));cap.set(cv2.CAP_PROP_POS_FRAMES,s['source'][0]);colors=[];frames=[]
  for i in range(n):
   ok,im=cap.read()
   if not ok:raise RuntimeError('Missing source frame')
   colors.append(cv2.resize(im,(288,512)));frames.append(cv2.cvtColor(colors[-1],cv2.COLOR_BGR2GRAY))
  cap.release()
  ref=s['layers']['referenceLocalFrame'];spec=s['layers']['head'];hidx=names.index('c_head')
  refalpha=cv2.resize(cv2.imread(str(PK/spec['texture']),cv2.IMREAD_UNCHANGED)[:,:,3],(288,512),interpolation=cv2.INTER_NEAREST)
  refworld=np.asarray(spec['referenceBoneWorld']);rest=np.asarray(spec['restMatrix']);refcam=np.asarray(s['layers']['camera']['matris']);focal=s['layers']['camera']['lins_mm']/36*576
  corners=np.array([[0,0],[576,0],[576,1024],[0,1024]],np.float32)
  xyz=np.c_[(corners[:,0]-288)/focal*spec['depth'],(512-corners[:,1])/focal*spec['depth'],np.full(4,-spec['depth']),np.ones(4)];reference=(refcam@xyz.T).T
  for i in range(n):
   mats=raw['matrices'][i].transpose(0,2,1);joints=[]
   for name in ['c_head','r_lowarm','r_wrist','r_middle3','l_lowarm','l_wrist','l_middle3']:
    j=names.index(name) if name in names else names.index(name.replace('middle3','wrist'));r=np.array(sk[j]['restMatrixColumnMajor']).reshape(4,4).T;joints.append((mats[j]@r@np.array([0,0,0,1.]))[:3])
   key=M['cameras']['nycklar'][s['source'][0]+i];uv,d=projected(np.array(joints),key);jointuv.append(uv)
   src=cv2.resize(masks[scene['lokal_start']+i].astype(np.uint8),(144,256),interpolation=cv2.INTER_NEAREST)>0;patch=np.zeros((256,144,3),np.uint8)
   # A skin-only head has no hair: warp the complete reference head bounds.
   current=mats[hidx]@rest;world=(current@np.linalg.inv(refworld)@reference.T).T[:,:3];dst,_=projected(world,key);hom=cv2.getPerspectiveTransform(corners/2,(dst/2).astype(np.float32));warped=cv2.warpPerspective(refalpha,hom,(288,512),flags=cv2.INTER_NEAREST)>0
   roi=cv2.dilate(warped.astype(np.uint8),np.ones((9,9),np.uint8))>0;mk=cv2.resize(src.astype(np.uint8),(288,512),interpolation=cv2.INTER_NEAREST)>0
   seeds=np.where(mk,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype(np.uint8);seeds[~roi]=cv2.GC_BGD;seeds[(cv2.erode(warped.astype(np.uint8),np.ones((7,7),np.uint8))>0)&mk]=cv2.GC_FGD
   ys,xs=np.where(roi)
   if len(xs):
    x0=max(0,int(xs.min())-1);x1=min(288,int(xs.max())+2);y0=max(0,int(ys.min())-1);y1=min(512,int(ys.max())+2);crop=seeds[y0:y1,x0:x1].copy()
    try:cv2.grabCut(colors[i][y0:y1,x0:x1].copy(),crop,None,np.zeros((1,65),np.float64),np.zeros((1,65),np.float64),2,cv2.GC_INIT_WITH_MASK);seeds[y0:y1,x0:x1]=crop
    except cv2.error:pass
   alpha=((seeds==cv2.GC_FGD)|(seeds==cv2.GC_PR_FGD))&roi;patch[:,:,0]=cv2.resize(alpha.astype(np.uint8)*255,(144,256),interpolation=cv2.INTER_NEAREST)
   for k,ids in enumerate([[1,2,3],[4,5,6]]):
    hand=np.zeros((256,144),np.uint8);a,b,c=np.rint(uv[ids]/4).astype(int);radius=int(np.clip(np.linalg.norm(a-b)*.55,6,16));cv2.line(hand,a,b,255,radius*2);cv2.line(hand,b,c,255,radius*2);cv2.circle(hand,tuple(b),radius,255,-1);patch[:,:,k+1]=hand*src
   reject_text(patch,M['text'],s['source'][0]+i);atlas[(i//8)*256:(i//8+1)*256,(i%8)*144:(i%8+1)*144]=patch
   hverts=(raw['weights']*(raw['ids']==hidx)).sum(1)>.3;_,hd=projected(pose(raw,i)[hverts],key);depths.append([float(hd.min())-.008,float(np.mean(d[[1,2]])),float(np.mean(d[[4,5]]))]);heads.append([float(uv[0,0]/576),float(uv[0,1]/1024)])
  # Candidate held pixels: foreground near either hand, validated by wrist/flow
  # agreement over the shot. No scene IDs, food polygons or object labels.
  held=[];fgspec=s['layers'].get('foreground');foreground=None
  if fgspec:
   fg=cv2.imread(str(PK/fgspec['texture']),cv2.IMREAD_UNCHANGED);fgsmall=cv2.resize(fg[:,:,3],(288,512),interpolation=cv2.INTER_NEAREST);removed=np.zeros((512,288),np.uint8);uvs=np.array(jointuv)
   for owner,(wrist,tip) in enumerate([(2,3),(5,6)]):
    w=uvs[ref,wrist]/2;t=uvs[ref,tip]/2;center=t+(t-w)*.35;radius=int(np.clip(np.linalg.norm(t-w)*1.3,24,52));near=np.zeros_like(removed);cv2.circle(near,tuple(np.rint(center).astype(int)),radius,255,-1);region=cv2.bitwise_and(fgsmall,near);reject_text(region,M['text'],s['source'][0]+ref,2)
    if np.count_nonzero(region)<60:continue
    track=follow_patch(frames,ref,region)
    if track is None:continue
    offsets,count=track;residual=[float(np.linalg.norm((uvs[i,wrist]-uvs[ref,wrist])-offsets[i]*2)) for i in range(n)];excursion=float(np.max(np.linalg.norm(uvs[:,wrist]-uvs[ref,wrist],axis=1)));accepted=float(np.median(residual))<6 and float(np.percentile(residual,90))<12 and excursion>4
    held.append(dict(owner=['r_wrist','l_wrist'][owner],accepted=bool(accepted),medianJointFlowResidualPx=float(np.median(residual)),worstResidualPx=max(residual),minTrackedPoints=count,excursionPx=excursion))
    if not accepted:continue
    removed|=region
    for i in range(n):
     moved=cv2.warpAffine(region,np.array([[1,0,offsets[i][0]],[0,1,offsets[i][1]]],np.float32),(288,512),flags=cv2.INTER_NEAREST);moved=cv2.resize(moved,(144,256),interpolation=cv2.INTER_NEAREST);x=(i%8)*144;y=(i//8)*256;atlas[y:y+256,x:x+144,owner+1]|=moved
   if removed.any():
    erase=cv2.resize(removed,fg.shape[1::-1],interpolation=cv2.INTER_NEAREST)>0;fg[erase]=0;foreground=f"{s['id']}-foreground-live.png";cv2.imwrite(str(PK/foreground),fg)
  # Reject text after the held-object union too.
  for i in range(n):
   x=(i%8)*144;y=(i//8)*256;reject_text(atlas[y:y+256,x:x+144],M['text'],s['source'][0]+i)
  cv2.imwrite(str(PK/f"{s['id']}-live.png"),cv2.cvtColor(atlas,cv2.COLOR_RGB2BGR));s['live']=dict(atlas=f"{s['id']}-live.png",depths=depths,headCenters=heads,channels=['head','right forearm/hand','left forearm/hand'],rows=rows,held=held,foreground=foreground,status={'jointDepths':'measured','sourceRGB':'measured','personMask':'measured','patchBounds':'assumed','heldOwnership':'assumed'});audit.append(dict(scene=s['id'],held=held));print(s['id'],'live masks',held,flush=True)
 M['provenance']['measured']=list(dict.fromkeys(M['provenance']['measured']+['Live source RGB projected through original per-frame camera; body source-view depth, segmentation and source-text rejection gate sampling.']))
 M['provenance']['assumed']=[a for a in M['provenance']['assumed'] if not a.startswith(('Live head and forearm/hand','s5 held burger','Changed dialogue intervals','Possible held foreground'))]
 M['provenance']['assumed']+=['Live head and forearm/hand repair uses three source-camera planes at measured head/arm depths. Head bounds follow the existing reference cutout; hand bounds are joint capsules intersected with measured coarse segmentation. No finger geometry.', 'Possible held foreground is detected near either hand, tracked with sparse LK flow, admitted only when wrist/flow residual is small. Ownership and rigid translation are assumptions; nearby background can leak. No clip-specific live regions.', 'Changed dialogue intervals mute original mixed audio and freeze lower-face source sampling. No synthesized speech or lip sync. Source-text boxes plus 12 pixels reject burned-in text; hidden RGB is unavailable and falls back to fused texture or a card gap.']
 M['liveStatus']='Original-order intervals only. Trim/move/duplicate reuse the source time map. Decode/seek mismatch disables live. No retiming.'
 (PK/'manifest.json').write_text(json.dumps(M,ensure_ascii=False,indent=2),encoding='utf8');(O/'live-export.json').write_text(json.dumps(dict(seconds=time.perf_counter()-start,audit=audit),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
