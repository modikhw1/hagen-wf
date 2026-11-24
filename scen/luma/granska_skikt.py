import json, cv2, numpy as np, sys
S=json.load(open("scen25d.json",encoding="utf-8")); W,H=S["storlek"]
def ruta(sk):
    can=np.full((H,W,3),200,np.uint8); can[(np.indices((H,W)).sum(0)//24)%2==0]=170
    im=cv2.imread(sk["bild"],cv2.IMREAD_UNCHANGED); x0,y0,x1,y1=[int(round(v*s)) for v,s in zip(sk["ruta"],[W,H,W,H])]
    im=cv2.resize(im,(max(1,x1-x0),max(1,y1-y0))); a=im[...,3:4]/255.0 if im.shape[2]==4 else 1
    can[y0:y1,x0:x1]=(im[...,:3]*a+can[y0:y1,x0:x1]*(1-a)).astype(np.uint8); return can, (x0,y0,x1,y1)
rader=[]
for sc in S["scener"]:
    by={s["typ"]:s for s in sc["skikt"]}
    bg,_=ruta(by["bakgrund"]); per=ruta(by["person"])[0] if "person" in by else np.zeros((H,W,3),np.uint8)
    fg=ruta(by["forgrund"])[0] if "forgrund" in by else np.zeros((H,W,3),np.uint8)
    fo=bg.copy()//3+120
    for s in sc["skikt"]:
        if s["typ"]=="foremal":
            f,(x0,y0,x1,y1)=ruta(s); fo[y0:y1,x0:x1]=f[y0:y1,x0:x1]; cv2.rectangle(fo,(x0,y0),(x1,y1),(0,0,255),2)
            cv2.putText(fo,s["klass"].replace("å","a"),(x0,max(20,y0-4)),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2)
    rad=np.hstack([bg,per,fg,fo]); cv2.putText(rad,sc["id"],(10,40),cv2.FONT_HERSHEY_SIMPLEX,1.4,(0,0,255),3)
    rader.append(cv2.resize(rad,None,fx=0.25,fy=0.25))
cv2.imwrite(sys.argv[1] if len(sys.argv)>1 else "skikt-granskning.jpg",np.vstack(rader),[cv2.IMWRITE_JPEG_QUALITY,80]); print("ok")
