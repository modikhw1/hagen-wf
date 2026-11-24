"""Audit the delivered GLB, not just Blender renders. Standard-library CLI."""
import itertools
import hashlib
import json
import math
import struct
import sys
from pathlib import Path


def read_glb(path):
    data=Path(path).read_bytes()
    magic,version,length=struct.unpack_from('<4sII',data)
    if magic!=b'glTF' or version!=2 or length!=len(data):
        raise ValueError('Invalid GLB header')
    length,kind=struct.unpack_from('<II',data,12)
    if kind!=0x4e4f534a:
        raise ValueError('Missing GLB JSON chunk')
    return json.loads(data[20:20+length])


IDENTITY=[[float(i==j) for j in range(4)] for i in range(4)]


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def require_current_export(out):
    out=Path(out)
    report=json.loads((out/'glb_local_audit.json').read_text(encoding='utf-8'))
    if not report.get('passed'):
        raise RuntimeError('Delivery blocked: GLB audit failed')
    for key,path in [('blend_sha256',out/'preview/scene.blend'),('glb_sha256',out/'preview/delivery.glb')]:
        if report.get(key)!=file_hash(path):
            raise RuntimeError('Delivery blocked: missing/stale GLB audit for '+str(path))
    if not report.get('roundtrip_passed'):
        raise RuntimeError('Delivery blocked: exported animation has not passed round-trip verification')
    return report


def multiply(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def transform(node):
    if 'matrix' in node:
        return [[node['matrix'][j*4+i] for j in range(4)] for i in range(4)]
    x,y,z,w=node.get('rotation',[0,0,0,1])
    scale=node.get('scale',[1,1,1]); pos=node.get('translation',[0,0,0])
    r=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
       [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
       [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
    return [[r[i][j]*scale[j] for j in range(3)]+[pos[i]] for i in range(3)]+[[0,0,0,1]]


def audit_gltf(doc):
    errors=[]; heads=[]; meshes=0; seen=set(); visibility=0
    animation_errors=[]
    if len(doc.get('animations',[]))>1:
        animation_errors.append('Scene motion split into '+str(len(doc['animations']))+' clips; expected one shared timeline')
    animated_scale={c['target']['node'] for a in doc.get('animations',[]) for c in a['channels'] if c['target'].get('path')=='scale'}
    def visit(index,parent):
        nonlocal meshes,visibility
        if index in seen:
            errors.append('Duplicate/cyclic node '+str(index)); return
        seen.add(index); node=doc['nodes'][index]; name=node.get('name','node_'+str(index))
        world=multiply(parent,transform(node))
        if not all(math.isfinite(v) for row in world for v in row):
            errors.append(name+': nonfinite transform')
        if '_beat_' in name:
            errors.append(name+': forbidden alternative rig')
        if 'mesh' in node:
            meshes+=1; points=[]
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                bounds=doc['accessors'][primitive['attributes']['POSITION']]
                if 'min' not in bounds or 'max' not in bounds:
                    errors.append(name+': missing POSITION bounds'); continue
                for corner in itertools.product(*zip(bounds['min'],bounds['max'])):
                    points.append([sum(world[i][j]*corner[j] for j in range(3))+world[i][3] for i in range(3)])
            if points:
                dimensions=[max(p[k] for p in points)-min(p[k] for p in points) for k in range(3)]
                if not all(math.isfinite(v) for v in dimensions):
                    errors.append(name+': nonfinite geometry')
                if name.startswith('RIG_') and name.endswith('_huvud'):
                    heads.append({'name':name,'dimensions_m':dimensions})
                    if max(dimensions)>.4:
                        errors.append(name+': head exceeds 0.4 m: '+str(dimensions))
            if node.get('extras',{}).get('pipe_visibility'):
                visibility+=1
                if node['extras'].get('pipe_visibility_animated',True) and index not in animated_scale:
                    errors.append(name+': visibility scale animation lost')
        for child in node.get('children',[]):
            visit(child,world)
    for index in doc['scenes'][doc.get('scene',0)]['nodes']:
        visit(index,IDENTITY)
    if not heads:
        errors.append('No delivery heads found')
    return {'passed':not errors and not animation_errors,'geometry_passed':not errors,'animation_passed':not animation_errors,'errors':errors+animation_errors,'active_nodes':len(seen),'mesh_nodes':meshes,'heads':heads,'portable_visibility_meshes':visibility,'animation_clips':len(doc.get('animations',[]))}


if __name__=='__main__':
    report=audit_gltf(read_glb(sys.argv[1]))
    if len(sys.argv)>2:
        Path(sys.argv[2]).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
    raise SystemExit(0 if report['passed'] else 1)
