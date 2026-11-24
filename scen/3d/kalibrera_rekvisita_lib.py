"""Gemensam projektion för kalibrering/förfining (samma kameramodell som spelaren: three.js PerspectiveCamera, vertikal fov)."""
import math
import numpy as np

W, H = 576, 1024

def kamera_fran(k):
    pos, tgt, up = map(np.array, (k['pos'], k['target'], k.get('up', [0, 1, 0])))
    f = tgt - pos; f = f / np.linalg.norm(f); r = np.cross(f, up); r = r / np.linalg.norm(r); u = np.cross(r, f)
    return pos, r, u, f, (H / 2) / math.tan(math.radians(k['fov']) / 2)

def projicera(P, cam):
    pos, r, u, f, fpx = cam; d = P - pos
    x, y, z = d @ r, d @ u, d @ f
    return np.stack([W / 2 + x / z * fpx, H / 2 - y / z * fpx], -1)

def hörn(pos, dims, yaw):
    w, h, d = dims; c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)); pts = []
    for sx in (-.5, .5):
        for sy in (-.5, .5):
            for sz in (-.5, .5):
                x, z = sx * w, sz * d; pts.append([pos[0] + c * x + s * z, pos[1] + sy * h, pos[2] - s * x + c * z])
    return np.array(pts)

def ruta2d(pos, dims, yaw, cam):
    p = projicera(hörn(pos, dims, yaw), cam)
    return np.array([p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max()])

def källruta(b):
    return np.array([b[1] / 1000 * W, b[0] / 1000 * H, b[3] / 1000 * W, b[2] / 1000 * H])
