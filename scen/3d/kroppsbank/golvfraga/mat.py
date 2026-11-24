import numpy as np, json, sys
b='ingest/ut/notan-tagningar/'
F=np.diag([1.,-1.,-1.])
for sc,pid in [('S1','1'),('S4','1'),('S4','4')]:
    S=np.load(f'{b}{sc}/sekvens_{pid}.npz'); V=np.load(f'{b}{sc}/varld.npz')
    print(sc,pid,S.files)
    inom=S['inom']; gs=S['golv_skala'] if 'golv_skala' in S.files else None
    print(' inom',inom.sum(),'ben_synliga',S['ben_synliga'].sum(),'gs median',None if gs is None else np.median(gs[inom]), 'min/max',None if gs is None else (gs[inom].min(),gs[inom].max()))
    ct=S['cam_t']; cf=S['cam_t_fore_golv'] if 'cam_t_fore_golv' in S.files else None
    ck=S['cam_t_fore_kontakt'] if 'cam_t_fore_kontakt' in S.files else None
    if cf is not None:
        d=ct-cf; print(' delta golv+kontakt median |m|',np.median(np.linalg.norm(d[inom],axis=1)),'cam_t norm median',np.median(np.linalg.norm(ct[inom],axis=1)))
    if ck is not None and cf is not None:
        print(' kontakt delta median',np.median(np.linalg.norm((ct-ck)[inom],axis=1)),' golv delta median',np.median(np.linalg.norm((ck-cf)[inom],axis=1)))
    p=S['pose'][inom][:,:,:3]/100@F
    h=p[:,:,1]; 
    # kroppslängd: huvud (113) till lägsta fot (4,20) rotrelativ; modellrum y-upp? använd kamerarum F
    print(' pose joints',S['pose'].shape,'golv_h' ,V['golv_h'] if 'golv_h' in V.files else None,'kam höjd',float(np.median(V['kam_C']@V['upp'])))
    # lodrät utsträckning i världsupp (u) av hela kroppen (alla leder), median
    R,C,u=V['kam_R'],V['kam_C'],V['upp']
    ex=[];ex2=[]
    for i in np.nonzero(inom)[0]:
        X=np.array([R[i]@(F@(S['pose'][i,j,:3]/100)) for j in range(S['pose'].shape[1])])@u
        ex.append(X.max()-X.min())
    print(' kroppshöjd (lodrät utsträckning alla leder) median m',np.median(ex),'p10-90',np.percentile(ex,[10,90]))
    if gs is not None: print(' x skala S1/S4 ->',np.median(ex)*np.median(gs[inom]),' /',np.median(ex)/np.median(gs[inom]))
