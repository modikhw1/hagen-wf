"""Numpy-skinning av fothud uppmätt ur den lokala FBX-riggen.

Samma linjära benvikter och globala benmatriser som MHR-byggaren använder.
Detta är riggens hud, inte en antagen avståndsschablon från tåleden.
"""
from functools import lru_cache
from pathlib import Path
import numpy as np


def rotation(q):
    q=np.asarray(q,float);q=q/np.linalg.norm(q,axis=-1,keepdims=True)
    x,y,z,w=np.moveaxis(q,-1,0)
    return np.stack([1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),
                     2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),
                     2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)],axis=-1).reshape(q.shape[:-1]+(3,3))


def data():
    file=Path(__file__).parent/'tro_fothud.npz';st=file.stat()
    return _data((st.st_size,st.st_mtime_ns,st.st_ctime_ns))


@lru_cache(maxsize=1)
def _data(stamp):
    d=dict(np.load(Path(__file__).parent/'tro_fothud.npz'))
    j=d['joints'];vi=d['vertex_index'];restrot=rotation(d['rest'][:,3:7])
    offsets=d['vertices'][vi]-d['rest_heads'][j-1]
    d['offsets']=np.einsum('nij,nj->ni',np.transpose(restrot[j],(0,2,1)),offsets@d['rigg_rotation'])
    return d


def hud(pose,Q,T):
    d=data();j=d['joints'];vi=d['vertex_index']
    offsets=np.einsum('nij,nj->ni',rotation(pose[j,3:7]),d['offsets'])
    points=(offsets+pose[j,:3]/100)@Q.T+T
    verts=np.zeros_like(d['vertices']);np.add.at(verts,vi,points*d['weights'][:,None])
    return verts


def lagsta(pose,Q,T):
    return float(hud(pose,Q,T)[:,2].min())


def per_fot(pose,Q,T):
    verts=hud(pose,Q,T);x=data()['vertices'][:,0]
    return dict(l=float(verts[x>0,2].min()),r=float(verts[x<0,2].min()))
