import numpy as np, json
b='ingest/ut/notan-tagningar/'; F=np.diag([1.,-1.,-1.])
p=json.load(open('kontrakt/ut/notan/jamn_tom_rattad/plan.json',encoding='utf-8'))
for s in p['scener']:
    print(s['id'],[(q['id'],q['ingest_id'],q.get('rorelse','')[-30:]) for q in s['personer']])
def proj(X,f): return f*X[:,:2]/X[:,2:3]
for sc in ['S1','S4']:
    S1=np.load(f'{b}{sc}/sekvens_1.npz'); ii=np.nonzero(S1['inom'])[0]
    d1=(S1['cam_t']-S1['cam_t_fore_golv'])
    for pid in (['1'] if sc=='S1' else ['1','4']):
        S=np.load(f'{b}{sc}/sekvens_{pid}.npz'); ii=np.nonzero(S['inom'])[0]; f=float(S['fokal'])
        Xo=np.array([F@(S['pose'][i,1,:3]/100)+S['cam_t_fore_golv'][i] for i in ii])   # original (före golv), kamerarum
        Xs=np.array([F@(S['pose'][i,1,:3]/100)+S['cam_t'][i] for i in ii])               # sparad, utan kompensation
        Xk=Xs-d1[ii]                                                                      # med planens kamerakomp (huvudperson 1)
        for nm,X in [('sparad utan komp',Xs),('med planens komp',Xk)]:
            e=np.linalg.norm(proj(X,f)-proj(Xo,f),axis=1)
            print(sc,'person',pid,nm,'rotpunkt 2D-fel px median %.1f p90 %.1f; djupändring %.3f m'%(np.median(e),np.percentile(e,90),np.median(X[:,2]-Xo[:,2])))
