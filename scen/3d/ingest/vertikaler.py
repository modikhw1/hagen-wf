"""Lokal kontroll av upp-riktning mot långa bakgrundskanter i källbilden."""
import cv2
import numpy as np


def mat(img,personmask,fokal):
    h,w=img.shape[:2];grey=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    detected=cv2.createLineSegmentDetector().detect(grey)[0]
    if detected is None:return None
    mask=cv2.resize(personmask.astype('uint8'),(w,h),interpolation=cv2.INTER_NEAREST)
    K=np.array([[fokal,0,w/2],[0,fokal,h/2],[0,0,1.]])
    lines=[];planes=[];lengths=[]
    for segment in detected.reshape(-1,4):
        a,b=segment.reshape(2,2);d=b-a;length=np.linalg.norm(d)
        if length<max(30,h*.04) or abs(d[0])>abs(d[1])*.7:continue
        sample=np.array([a+(b-a)*t for t in np.linspace(0,1,9)]).astype(int);sample[:,0]=sample[:,0].clip(0,w-1);sample[:,1]=sample[:,1].clip(0,h-1)
        if mask[sample[:,1],sample[:,0]].any():continue
        line=np.cross(np.r_[a,1.],np.r_[b,1.]);n=K.T@line;n/=np.linalg.norm(n)
        planes.append(n);lengths.append(length);lines.append(segment.tolist())
    if len(planes)<6:return None
    normals=np.array(planes);weights=np.array(lengths);best=None
    for i in range(len(normals)):
        for j in range(i):
            u=np.cross(normals[i],normals[j]);norm=np.linalg.norm(u)
            if norm<1e-4:continue
            u/=norm
            if u[1]>0:u=-u
            if abs(u[1])<.25:continue
            err=np.degrees(np.arcsin(np.clip(abs(normals@u),0,1)));inlier=err<.6
            score=weights[inlier].sum()
            if best is None or score>best[0]:best=(score,u,inlier)
    if best is None or best[2].sum()<6:return None
    inside=best[2]
    _,vectors=np.linalg.eigh((normals[inside]*weights[inside,None]).T@normals[inside]);u=vectors[:,0]
    if u[1]>0:u=-u
    err=np.degrees(np.arcsin(np.clip(abs(normals@u),0,1)))
    return dict(status='uppmatt',metod='LSD-bakgrundskanter utanför personmask. RANSAC på vertikala flyktpunktens kamerariktning; bildvertikaler antas vara lodräta i världen.',upp_cam=u.tolist(),
                roll_grader=float(np.degrees(np.arctan2(u[0],-u[1]))),pitch_ner_grader=float(np.degrees(np.arctan2(-u[2],np.linalg.norm(u[:2])))),
                inliers=int(inside.sum()),linjer=len(lines),median_rest_grader=float(np.median(err[inside])),linjer_px=[line for line,ok in zip(lines,inside) if ok],
                antagande='Kanter nära bildens vertikal är lodräta byggnadsdelar, inte lutande föremål. Brännvidd från den sparade kroppsmodellen.')
