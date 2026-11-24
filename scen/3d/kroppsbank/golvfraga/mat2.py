import numpy as np
b='ingest/ut/notan-tagningar/'
F=np.diag([1.,-1.,-1.]); FOT=[4,8,20,24]
for sc,pid in [('S1','1'),('S4','1'),('S4','4')]:
    S=np.load(f'{b}{sc}/sekvens_{pid}.npz'); V=np.load(f'{b}{sc}/varld.npz'); R,C,u=V['kam_R'],V['kam_C'],V['upp']
    ii=np.nonzero(S['inom'])[0]; gh=float(V['golv_h'])
    def fh(ct):
        return np.array([min((C[i]+R[i]@(F@(S['pose'][i,j,:3]/100)+ct[i]))@u for j in FOT) for i in ii])
    for nm in ['cam_t_fore_golv','cam_t']:
        h=fh(S[nm]); print(sc,pid,nm,'lägsta fot u-höjd median %.3f m (golv_h %.3f) => kamerahöjd över fot %.2f m; cam_t-avstånd %.2f m'%(np.median(h),gh,np.median(C[ii]@u-h),np.median(np.linalg.norm(S[nm][ii],axis=1))))
    # huvud (113) höjd över lägsta fot, före golv
    hd=np.array([((C[i]+R[i]@(F@(S['pose'][i,113,:3]/100)+S['cam_t_fore_golv'][i]))@u) for i in ii]); h0=fh(S['cam_t_fore_golv'])
    print('   huvud-led över lägsta fot median %.2f m (före golv); x skala %.3f = %.2f'%(np.median(hd-h0),np.median(S['golv_skala'][ii]),np.median(hd-h0)*np.median(S['golv_skala'][ii])))
