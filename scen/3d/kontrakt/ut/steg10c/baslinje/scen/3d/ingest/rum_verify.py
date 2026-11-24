"""Measured acceptance report; never changes body, camera or room geometry."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from rum import corners, gravity, project, write_json


def segment_hits_box(camera, targets, obj, G):
    """Ray segments to body joints vs the room's convex box (including sloped top)."""
    a=obj['yaw'];B=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1.]])
    c=(camera-obj['centre'])@G.T@B;target=(targets-obj['centre'])@G.T@B;direction=target-c
    half=np.asarray(obj['size'])/2;slope=obj.get('top_slope',0.)
    normals=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,-1],[-slope,0,1.]])
    bounds=np.array([half[0],half[0],half[1],half[1],half[2],half[2]])
    lo=np.zeros(len(targets));hi=np.ones(len(targets));valid=np.ones(len(targets),bool)
    for n,b in zip(normals,bounds):
        den=direction@n;num=b-c@n;parallel=np.abs(den)<1e-9
        valid &= ~(parallel & (num<0))
        t=num/np.where(parallel,1,den)
        lo=np.maximum(lo,np.where(den < -1e-9,t,-np.inf));hi=np.minimum(hi,np.where(den > 1e-9,t,np.inf))
    return valid & (lo<=hi) & (lo<.999) & (hi>0)


def verify(ut):
    ut=Path(ut);room=json.loads((ut/'rum.json').read_text(encoding='utf-8'));V=dict(np.load(ut/'varld.npz'));G=gravity(V['upp'])
    M=json.loads((ut/'meta.json').read_text());F=np.diag([1.,-1.,-1.]);result={}
    before=json.loads((ut/'rum_fore_hash.json').read_text())
    result['unchanged_inputs']={name:hashlib.sha256((ut/name).read_bytes()).hexdigest()==digest for name,digest in before.items()}
    fore=json.loads((ut/'vakt_rum_fore.json').read_text(encoding='utf-8'));after=json.loads((ut/'vakt_rum_efter.json').read_text(encoding='utf-8'))
    result['guard_identical']=fore==after
    result['floor']=dict(rendered_difference_cm=100*(room['floor']['height']-float(V['golv_h'])),
                         normal_angle_deg=float(np.degrees(np.arccos(np.clip(np.dot(room['floor']['normal'],V['upp']),-1,1)))),
                         independent_depth_difference_cm=room['floor']['difference_cm'],independent_depth_verified=room['floor']['verified'])
    result['walls']=[dict(id=w['id'],camera_path_m=w['camera_path_m']) for w in room['walls']]
    result['objects']=[dict(id=o['id'],label=o['label'],size=o['size']) for o in room['objects']]
    counters=[o for o in room['objects'] if o['label']=='bar counter']
    if counters:
        result['counter_edge']=json.loads((ut/'rum/counter_edge_check.json').read_text())
        result['counter_lower_body_occlusion']={}
        for file in sorted(ut.glob('sekvens_*.npz')):
            S=np.load(file);pid=file.stem[8:];focal=float(S['fokal']);details=[]
            for frame in np.flatnonzero(S['inom']):
                cam=S['pose'][frame,[1,3,4,8,19,20,24],:3]/100@F+S['cam_t'][frame]
                points=cam@V['kam_R'][frame].T+V['kam_C'][frame]
                uv,z=project(points,frame,V,focal,(M['bredd'],M['hojd']))
                visible=(z>0)&(uv[:,0]>=0)&(uv[:,0]<M['bredd'])&(uv[:,1]>=0)&(uv[:,1]<M['hojd'])
                hit=np.any([segment_hits_box(V['kam_C'][frame],points,o,G) for o in counters],axis=0)
                if visible.any():details.append(dict(frame=int(frame),in_image=int(visible.sum()),occluded=int(hit[visible].sum())))
            total=sum(d['in_image'] for d in details);hit=sum(d['occluded'] for d in details)
            result['counter_lower_body_occlusion'][pid]=dict(joints_in_image=total,joints_occluded=hit,
                fraction=hit/total if total else None,frames=len(details),per_frame=details)
    tables=[o for o in room['objects'] if o['label']=='pool table']
    result['table_count']=len(tables)
    result['render_frames']=len(list((ut/'render').glob('f*.png')))
    result['comparison_exists']=(ut/'jamforelse.mp4').exists()
    result['cached_pipeline_seconds']=json.loads((ut/'tider.json').read_text()).get('senaste_korning',{}).get('sek')
    result['criteria']=dict(inputs_unchanged=all(result['unchanged_inputs'].values()),guard_no_regression=result['guard_identical'],
        rendered_floor_within_5cm=abs(result['floor']['rendered_difference_cm'])<=5,
        wall_distances_reported=bool(room['walls']),all_frames_rendered=result['render_frames']==M['N'],
        cached_under_90s=result['cached_pipeline_seconds'] is not None and result['cached_pipeline_seconds']<90)
    if counters:
        # Strict clip-wide threshold, rather than calling a good median a full pass.
        result['criteria']['counter_edge_all_measured_frames_within_25px']=result['counter_edge']['max_px']<=25
        result['criteria']['counter_edge_p95_within_25px']=result['counter_edge']['p95_px']<=25
        result['criteria']['lower_bodies_occluded']=all(p['fraction'] is not None and p['fraction']>=.95 for p in result['counter_lower_body_occlusion'].values())
    if tables:
        result['criteria']['at_least_two_tables']=len(tables)>=2
        result['criteria']['table_dimensions_plausible']=sum(2.1<=o['size'][0]<=2.9 and 1.1<=o['size'][1]<=1.65 and .65<=o['size'][2]<=.95 for o in tables)>=2
    write_json(ut/'rum_acceptance.json',result)
    print(json.dumps({k:v for k,v in result.items() if k in ('criteria','floor','objects','cached_pipeline_seconds')},indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('ut');a=p.parse_args();verify(a.ut)
