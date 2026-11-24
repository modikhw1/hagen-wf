"""Gemensam geometri: Blender-kamera (tittar längs -Z lokalt, upp +Y), scenpaket/2-led."""
from __future__ import annotations
import math
import numpy as np

def q2R(q):
    w, x, y, z = q
    n = math.sqrt(w*w + x*x + y*y + z*z); w, x, y, z = w/n, x/n, y/n, z/n
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def R2q(R):
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; q = [0.25*s, (R[2,1]-R[1,2])/s, (R[0,2]-R[2,0])/s, (R[1,0]-R[0,1])/s]
    elif R[0,0] > R[1,1] and R[0,0] > R[2,2]:
        s = math.sqrt(1 + R[0,0] - R[1,1] - R[2,2]) * 2; q = [(R[2,1]-R[1,2])/s, 0.25*s, (R[0,1]+R[1,0])/s, (R[0,2]+R[2,0])/s]
    elif R[1,1] > R[2,2]:
        s = math.sqrt(1 + R[1,1] - R[0,0] - R[2,2]) * 2; q = [(R[0,2]-R[2,0])/s, (R[0,1]+R[1,0])/s, 0.25*s, (R[1,2]+R[2,1])/s]
    else:
        s = math.sqrt(1 + R[2,2] - R[0,0] - R[1,1]) * 2; q = [(R[1,0]-R[0,1])/s, (R[0,2]+R[2,0])/s, (R[1,2]+R[2,1])/s, 0.25*s]
    q = np.array(q); q /= np.linalg.norm(q)
    if q[0] < 0: q = -q
    return [round(float(c), 6) for c in q]

def f_px(lins_mm, bredd_px, sensor_mm=36.0):
    return lins_mm / sensor_mm * bredd_px

def world_to_cv(P, C, R):
    """Världspunkter -> OpenCV-kamerakoordinater (x höger, y ned, z framåt)."""
    Pc = (np.asarray(P) - C) @ R  # Blender-kamera lokalt: x höger, y upp, z bakåt
    return np.stack([Pc[..., 0], -Pc[..., 1], -Pc[..., 2]], axis=-1)

def cv_to_world_dir(v, R):
    v = np.asarray(v, float); b = np.array([v[0], -v[1], -v[2]])
    return R @ b

def project(P, C, R, f, W, H):
    c = world_to_cv(P, C, R)
    z = np.maximum(c[..., 2], 1e-6)
    return np.stack([f*c[..., 0]/z + W/2, f*c[..., 1]/z + H/2], axis=-1), c[..., 2]

def nyckel_pose(k):
    return np.array(k[1:4], float), q2R(k[4:8]), float(k[8])

def led_rutor(paket, pid, tagning):
    for tr in paket['rorelse'].get(pid, []):
        if tr['tagning'] == tagning:
            arr = np.array(tr['rutor'], float)
            return arr[:, 0].astype(int), arr[:, 1:].reshape(len(arr), -1, 3) / 1000.0
    return None, None
