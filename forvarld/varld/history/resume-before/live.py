"""Export per-frame source alpha and measured joint depths, with assumed patch bounds."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import json,time
import cv2,numpy as np
from export import wait_heavy
from refine import HELD_S5,projected,pose
O=Path('forvarld/varld');PK=O/'paket/notan';read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
M=read(PK/'manifest.json');P=read(PK/'plan.json');meshes=read(PK/'meshes.json');start=time.perf_counter();audit=[]
for s,scene,mesh in zip(M['scenes'],P['scener'],meshes):
 wait_heavy();raw=np.load(O/'intermediat'/f"{s['person']['stem']}-raw.npz");masks=np.load(Path(scene['varld']).parent/'masker.npy',mmap_mode='r');sk=mesh['skeleton'];names=[b['name'] for b in sk];n=s['source'][1]-s['source'][0];rows=(n+7)//8;atlas=np.zeros((rows*256,8*144,3),np.uint8);frames=[];depths=[];heads=[];wristuv=[]
 cap=cv2.VideoCapture(str(PK/'source.mp4'));cap.set(cv2.CAP_PROP_POS_FRAMES,s['source'][0])
 colors=[]
 for i in range(n):
  ok,im=cap.read()
  if not ok:raise RuntimeError('Missing source frame')
  colors.append(cv2.resize(im,(288,512)));frames.append(cv2.cvtColor(colors[-1],cv2.COLOR_BGR2GRAY))
 cap.release()
 for i in range(n):
  mats=raw['matrices'][i].transpose(0,2,1);joints=[]
  for name in ['c_head','r_lowarm','r_wrist','r_middle3','l_lowarm','l_wrist','l_middle3']:
   j=names.index(name) if name in names else names.index(name.replace('middle3','wrist'));rest=np.array(sk[j]['restMatrixColumnMajor']).reshape(4,4).T;point=mats[j]@rest@np.array([0,0,0,1.]);joints.append(point[:3])
  uv,d=projected(np.array(joints),M['cameras']['nycklar'][s['source'][0]+i]);wristuv.append(uv[[2,5]])
  src=cv2.resize(masks[scene['lokal_start']+i].astype(np.uint8),(144,256),interpolation=cv2.INTER_NEAREST)>0
  patch=np.zeros((256,144,3),np.uint8)
  hidx=names.index('c_head');hverts=(raw['weights']*(raw['ids']==hidx)).sum(1)>.3;hu,hd=projected(pose(raw,i)[hverts],M['cameras']['nycklar'][s['source'][0]+i]);hu/=2;cx=float(np.median(hu[:,0]));top=float(hu[:,1].min());bottom=float(hu[:,1].max());hh=bottom-top;radius=max(float(np.ptp(hu[:,0]))*.72,7)
  xx,yy=np.meshgrid(np.arange(288),np.arange(512));upper=(abs(xx-cx)<radius)&(yy>top-hh*.5)&(yy<bottom+hh*.20);im=colors[i];longhair=(s['person']['person']=='A')&(abs(xx-cx)<radius*1.25)&(abs(xx-cx)>radius*.4)&(yy>=bottom-hh*.1)&(yy<bottom+hh*.95)&(im.max(2)<145);roi=upper|longhair;mk=cv2.resize(src.astype(np.uint8),(288,512),interpolation=cv2.INTER_NEAREST)>0
  central=(abs(xx-cx)<radius*.48)&(yy>top+hh*.1)&(yy<bottom+hh*.1);wall=(im.min(2)>175)&((im.max(2).astype(int)-im.min(2))<45)&~central;seeds=np.where(mk,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype(np.uint8);seeds[~cv2.dilate(roi.astype(np.uint8),np.ones((9,9),np.uint8)).astype(bool)|wall]=cv2.GC_BGD;seeds[(cv2.erode(mk.astype(np.uint8),np.ones((5,5),np.uint8))>0)&upper&((im.max(2)<130)|central)]=cv2.GC_FGD
  ys,xs=np.where(roi);x0=max(0,int(xs.min())-8);x1=min(288,int(xs.max())+9);y0=max(0,int(ys.min())-8);y1=min(512,int(ys.max())+9);crop=seeds[y0:y1,x0:x1].copy()
  try:cv2.grabCut(im[y0:y1,x0:x1].copy(),crop,None,np.zeros((1,65),np.float64),np.zeros((1,65),np.float64),2,cv2.GC_INIT_WITH_MASK);seeds[y0:y1,x0:x1]=crop
  except cv2.error:pass
  alpha=((seeds==cv2.GC_FGD)|(seeds==cv2.GC_PR_FGD))&roi&~wall;patch[:,:,0]=cv2.resize(alpha.astype(np.uint8)*255,(144,256),interpolation=cv2.INTER_NEAREST)
  hx,hy=cx/2,(top+bottom)/4
  for k,ids in enumerate([[1,2,3],[4,5,6]]):
   alpha=np.zeros((256,144),np.uint8);a,b,c=np.rint(uv[ids]/4).astype(int);cv2.line(alpha,a,b,255,20);cv2.line(alpha,b,c,255,21);cv2.circle(alpha,tuple(b),14,255,-1);patch[:,:,k+1]=alpha*src
  # Reject existing burned-in source subtitles in every dynamic layer.
  for t in M['text']:
   if t['ut'][0]<=s['source'][0]+i<t['ut'][1]:
    x,y,w,h=np.rint(np.array(t['box'])/4).astype(int);patch[max(0,y-2):y+h+2,max(0,x-2):x+w+2]=0
  atlas[(i//8)*256:(i//8+1)*256,(i%8)*144:(i%8+1)*144]=patch
  depths.append([float(hd.min())-.008,float(np.mean(d[[1,2]])),float(np.mean(d[[4,5]]))]);heads.append([float(hx/144),float(hy/256)])
 held=None
 if s['id']=='s5':
  ref=s['layers']['referenceLocalFrame'];poly=np.asarray(HELD_S5,np.float32)/2;region=np.zeros_like(frames[ref]);cv2.fillPoly(region,[poly.astype(int)],255);points=cv2.goodFeaturesToTrack(frames[ref],maxCorners=40,qualityLevel=.01,minDistance=3,mask=region);offsets={ref:np.zeros(2)};counts=[]
  for direction in [-1,1]:
   prev=points.copy();total=np.zeros(2)
   for i in range(ref+direction,n if direction>0 else -1,direction):
    nxt,status,err=cv2.calcOpticalFlowPyrLK(frames[i-direction],frames[i],prev,None,winSize=(21,21),maxLevel=2);good=status.ravel()>0
    shift=np.median((nxt-prev)[good].reshape(-1,2),axis=0) if good.any() else np.zeros(2);total+=shift;offsets[i]=total.copy();counts.append(int(good.sum()));prev=nxt
  center=poly.mean(0)*2;owner=int(np.argmin(np.linalg.norm(wristuv[ref]-center,axis=1)));motion=[]
  for i in range(n):
   x=(i%8)*144;y=(i//8)*256;mask=np.zeros((256,144),np.uint8);cv2.fillPoly(mask,[np.rint((poly+offsets[i])/2).astype(int)],255);atlas[y:y+256,x:x+144,owner+1]|=mask
   motion.append(float(np.linalg.norm((wristuv[i][owner]-wristuv[ref][owner])-offsets[i]*2)))
  held=dict(owner='r_wrist' if owner==0 else 'l_wrist',method='Measured sparse LK flow of midpoint burger patch, assumed rigid translation and ownership by nearest measured wrist. Union into that hand alpha, including outside person mask.',medianJointFlowResidualPx=float(np.median(motion)),worstResidualPx=max(motion),minTrackedPoints=min(counts))
  # Remove the frozen held burger from its old card, to prevent two burgers.
  fg=cv2.imread(str(PK/s['layers']['foreground']['texture']),cv2.IMREAD_UNCHANGED);mask=np.zeros(fg.shape[:2],np.uint8);cv2.fillPoly(mask,[np.array(HELD_S5,np.int32)],255);fg[mask>0]=0;cv2.imwrite(str(PK/'s5-foreground-live.png'),fg)
 cv2.imwrite(str(PK/f"{s['id']}-live.png"),cv2.cvtColor(atlas,cv2.COLOR_RGB2BGR))
 s['live']=dict(atlas=f"{s['id']}-live.png",depths=depths,headCenters=heads,channels=['head','right forearm/hand','left forearm/hand'],rows=rows,held=held,status={'jointDepths':'measured','sourceRGB':'measured','personMask':'measured','patchBounds':'assumed','heldOwnership':'assumed'})
 audit.append(dict(scene=s['id'],held=held))
 print(s['id'],'live masks',flush=True)
M['provenance']['measured'].append('Live source RGB projected through original per-frame camera onto posed body; source-view depth test, mask and image bounds gate sampling. Original camera matrices are never edited.')
M['provenance']['assumed']+=['Live head and forearm/hand silhouette repair uses three flat per-frame source-camera cards at measured head/arm mean depths; patch boundaries are assumed joint capsules intersected with coarse person segmentation. No new finger geometry.','s5 held burger follows locally measured sparse optical flow and is unioned into nearest wrist card mask, even outside person mask. Translation and ownership assumed; background leakage possible.','Changed dialogue intervals mute original mixed audio, freeze original lower face through original card texture/atlas; no synthesized speech or lip sync.']
M['liveStatus']='Original-order source intervals only; trim/move/duplicate preserve local order and can reuse source video. Seek mismatch disables live until decoded source frame catches up. No retiming supported.'
(PK/'manifest.json').write_text(json.dumps(M,ensure_ascii=False,indent=2),encoding='utf8');(O/'live-export.json').write_text(json.dumps(dict(seconds=time.perf_counter()-start,audit=audit),ensure_ascii=False,indent=2),encoding='utf8')
