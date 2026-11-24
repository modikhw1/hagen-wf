"""Lokalt före/efter-prov, bara sparade data och numpy-skinning. Ingen inferens."""
import sys, json, time, copy
from pathlib import Path
import numpy as np
import cv2
ROOT = Path(__file__).resolve().parents[4]
H = ROOT/'scen/3d/kontrakt'
sys.path[:0] = [str(H),str(H.parent/'ingest')]
sys.dont_write_bytecode = True
import kompilera, trohet, kroppmatt
if sys.argv[1]=='fore':
    import importlib
    for name in ('trohet','kroppmatt','tropassning','golvmatning','plats','kompilera'):
        mod=importlib.import_module(name)
        old=H/'ut/fore_golv2'/Path(mod.__file__).resolve().relative_to(ROOT)
        if old.exists(): exec(compile(old.read_text(encoding='utf-8'),mod.__file__,'exec'),mod.__dict__)
from golvmatning import fotkontroll
from golv2_tools import write
phase = sys.argv[1]
out = H/'ut/golv2'/phase
out.mkdir(parents=True,exist_ok=True)
def save(path, obj): write(path,json.dumps(obj,ensure_ascii=False,indent=1)+'\n')
def draw(plan,sc):
    u=(sc['ut'][0]+sc['ut'][1])//2; f=sc['lokal_start']+u-sc['ut'][0]
    key=copy.deepcopy(plan['matkamera']['nycklar'][u]); m=np.array(key['matris'])
    target=m[:3,3]-m[:3,2]*3
    if sc['personer']:
        pm=sc['personer'][0]; target=trohet.ruta(sc,pm,f)[1]
    pos=m[:3,3]+.5*m[:3,0]+[0,0,.3]
    key['matris']=kompilera.sikta(pos,target)
    w,h=576,1024; img=np.full((h,w,3),235,np.uint8)
    def project(x): return trohet.projicera(np.array(x),key,w,h)
    def line(x,c,th=1):
        uv=project(x)
        if np.isfinite(uv).all() and np.abs(uv).max()<30000:cv2.polylines(img,[uv.astype(np.int32)],False,c,th,cv2.LINE_AA)
    floor=next((o['pos_m'][2] for o in plan['objekt'] if o['typ']=='plan' or 'golv' in o['id']),0.)
    # Grid around target, only points in front of camera.
    for a in np.arange(-3,3.01,.5):
        for axis in (0,1):
            pts=np.array([[target[0]-3,target[1]+a,floor],[target[0]+3,target[1]+a,floor]])
            if axis:pts=np.array([[target[0]+a,target[1]-3,floor],[target[0]+a,target[1]+3,floor]])
            cam=(pts-pos)@np.array(key['matris'])[:3,:3]
            if (cam[:,2]<-.05).all():line(pts,(190,190,190))
    for o in plan['objekt']:
        if o['typ']=='plan' or o.get('synlig_ut') and not (o['synlig_ut'][0]<=u<o['synlig_ut'][1]):continue
        sz=np.array(o['matt_m'])/2;poso=np.array(o['pos_m']);yaw=o['rotation_rad'][2]
        R=np.array([[np.cos(yaw),-np.sin(yaw),0],[np.sin(yaw),np.cos(yaw),0],[0,0,1]])
        pts=np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)])*sz@R.T+poso
        for i in range(8):
            for bit in (1,2,4):
                j=i^bit
                if i<j and (((pts[[i,j]]-pos)@np.array(key['matris'])[:3,:3])[:,2]<-.05).all():line(pts[[i,j]],(110,130,150),2)
    for n,pm in enumerate(sc['personer']):
        pose,q,t=trohet.ruta_pose(sc,pm,f);x=kroppmatt.hudhorn(pose)/100@q.T+t
        sil=kroppmatt.siluett(x,key,w,h,w,h)
        if sil is not None:img[sil]=(95,150,190) if n==0 else (130,180,100)
        joints=pose[:,:3]/100@q.T+t
        for names in [('root','c_spine2','c_head'),('l_upleg','l_lowleg','l_foot','l_ball'),('r_upleg','r_lowleg','r_foot','r_ball')]:
            line(joints[[trohet.IX[n] for n in names]],(30,50,60),2)
    cv2.putText(img,f'{phase} {sc["id"]} +0.5m / +0.3m',(15,30),cv2.FONT_HERSHEY_SIMPLEX,.65,(10,10,10),2)
    cv2.imwrite(str(out/f'notan_{sc["id"]}_flyttad.png'),img)
    save(out/f'notan_{sc["id"]}_flyttad_kamera.json',dict(key=key,mal=target.tolist(),golv_m=floor))

allrows={}
for clip,source in [('notan',ROOT/'forvarld/varld/pipeline/kalla.json'),('b',H/'ut/b/kalla_prop.json')]:
    k=json.loads(source.read_text(encoding='utf-8'))
    base=json.loads((ROOT/'forvarld/varld/pipeline/base-regi.json').read_text(encoding='utf-8'))
    base['edits']=[];base['kalla']=dict(klipp_id=k['klipp']['id'],sha256=k['klipp']['sha256'],revision=k['revision']);base['ramar']['bevara_beats']=[]
    rf=out/f'{clip}_regi.json';save(rf,base)
    start=time.perf_counter();p=kompilera.kompilera(source,rf,snabb=True)
    p['kvalitet']['bildtrohet']=trohet.mat(p)
    p['kvalitet']['kropp']=dict(rader=kroppmatt.matt_plan(p))
    if phase!='fore':
        from golvmatning import rapport_3d
        p['kvalitet']['golv2_3d']=rapport_3d(p)
    save(out/f'{clip}_plan.json',p)
    rows=[]
    for sc in p['scener']:
        V=dict(np.load(sc['varld']));M=np.array(sc.get('till_plats',np.eye(4)));g=M[:3,:3]@trohet.gravitation(V)
        floor=next((o['pos_m'][2] for o in p['objekt'] if o['typ']=='plan' or 'golv' in o['id']),0.)
        for pm in sc['personer']:
            s=dict(np.load(pm['rorelse']));pid=pm.get('ingest_id') or Path(pm['rorelse']).stem[8:];folder=Path(pm['rorelse']).parent
            meta=json.loads((folder/'meta.json').read_text());vis=fotkontroll(folder,pid,meta)
            feet=[];visible=[];roots=[];cameras=[];heights=[]
            for u in range(*sc['ut']):
                f=sc['lokal_start']+u-sc['ut'][0]
                if not s['inom'][f]:continue
                x=trohet.ruta(sc,pm,f);key=p['matkamera']['nycklar'][u];c=np.array(key['matris'])[:3,3]
                foot=float(x[[4,8,20,24],2].min()-floor);feet.append(foot)
                if f in vis['anvandbara_rutor']:visible.append(foot)
                original=(s['pose'][f,1,:3]/100@trohet.F+s.get('cam_t_fore_golv',s['cam_t'])[f])
                uv=original[:2]/original[2]*float(s['fokal'])+[meta['bredd']/2,meta['hojd']/2]
                roots.append(float(np.linalg.norm(trohet.projicera(x[1:2],key,meta['bredd'],meta['hojd'])[0]-uv)))
                cameras.append(float(np.linalg.norm(c-(g@V['kam_C'][f]+M[:3,3]))));heights.append(float(c[2]-floor))
            fit=next(r for r in p['kvalitet']['bildtrohet']['personer'] if r['scen']==sc['id'] and r['person']==pm['id'])
            mask=next(r['mask'] for r in p['kvalitet']['kropp']['rader'] if r['scen']==sc['id'] and r['person']==pm['id'])
            rows.append(dict(scen=sc['id'],person=pm['id'],ingest_id=pid,rot_px=float(np.median(roots)),median_px=fit.get('median_px'),p90_px=fit.get('p90_px'),iou=mask.get('iou_median'),kamerahojd_m=float(np.median(heights)),kamera_rum_avstand_m=float(np.median(cameras)),fotrest_m=float(np.median(feet)),synlig_fotrest_m=float(np.median(visible)) if visible else None,synliga_fotrutor=len(visible)))
        if clip=='notan':draw(p,sc)
    allrows[clip]=rows;save(out/'matning.json',allrows)
    print(clip,round(time.perf_counter()-start,1),'s',json.dumps(rows),flush=True)
