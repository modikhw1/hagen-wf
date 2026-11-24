"""All-frame source metrics from evaluated Blender geometry, no fitted values."""
from common import *
import cv2,sys,subprocess

def contact_rows(data,spec,events):
    rows=[];props={p['id']:p for p in spec['props']};objects={p['id']:p for p in spec['set']}
    for event in events:
        if event['type'] not in ['seated','standing','hold']:continue
        frames=[f for f in data['frames'] if f['shot']==event['shot'] and event['startSec']-1e-6<=f['i']/30<event['endSec']-1e-6]
        distances=[];inside=[]
        for f in frames:
            if event['type']=='hold':
                side=event['side'];grip=np.mean([f['xyz'][FEATURES.index(side+'Hand'+n+'1')] for n in ['Index','Middle','Ring']],axis=0)
                prop=f['props'][event['object']];m=mat(prop['matrix']);p=props[event['object']]
                local=(np.linalg.inv(m)@np.r_[grip,1])[:3];nearest=np.clip(local,-np.array(p['dims'])/2,np.array(p['dims'])/2)
                distance=np.linalg.norm(grip-(m@np.r_[nearest,1])[:3]);valid=prop['visible'] and distance<.03
            elif event['type']=='seated':
                seat=objects['seat:'+event['actor']];centre=np.array(seat['transform']['position']);hips=np.array(f['hips'])
                # Builder's chair seat top: centre y + h/2 + .055/2.
                target=centre[1]+seat['dims'][1]/2+.0275+.12
                distance=abs(hips[1]-target)
                horizontal=np.abs((Rotation.from_euler('y',-seat['transform'].get('yaw',0),degrees=True).apply(hips-centre))[[0,2]])
                valid=distance<.03 and np.all(horizontal<np.array(seat['dims'])[[0,2]]/2+.03)
            else:
                distance=max(abs(np.array(f['toes'])[:,1]-.03));valid=distance<.03
            distances.append(float(distance));inside.append(bool(valid))
        rows.append(dict(shot=event['shot'],type=event['type'],object=event.get('object'),side=event.get('side'),window=[event['startSec'],event['endSec']],frames=len(frames),satisfied=sum(inside),percent=100*np.mean(inside) if inside else 0,distance_max_m=max(distances,default=0),distance_median_m=float(np.median(distances)) if distances else None,visibility=event.get('support_visibility')))
    return rows

def stats(values):
    if len(values)==0:return dict(n=0,median=None,p90=None)
    return dict(n=len(values),median=float(np.median(values)),p90=float(np.percentile(values,90)))

def main():
    b=read(HERE/'evaluated-before.json');a=read(HERE/'evaluated-after.json');targets=read(HERE/'gt/targets.json');spec=read(ROOT/'scen3d.json')
    before=read(HERE.parent/'bake.json');after=read(HERE/'bake-opt.json');assets=read(HERE.parent/'bake-assets.json')
    assert b['bake_sha256']==sha(HERE.parent/'bake.json') and a['bake_sha256']==sha(HERE/'bake-opt.json'),'Stale native evaluations'
    assert len(b['frames'])==len(a['frames'])==len(targets['frames'])==383
    events=read(HERE/'gt/events-checked.json')['events'];contacts=[contact_rows(x,spec,events) for x in [b,a]]
    reports=[];rows=[];fk_error=0
    for fa,fb,t in zip(a['frames'],b['frames'],targets['frames']):
        assert fa['i']==fb['i']==t['i']
        masks=[cv2.imread(str(HERE/x['mask']),0)>127 for x in [fb,fa]];source=cv2.imread(str(HERE/'gt/masks'/f'{fa["i"]:04d}.png'),0)>127
        iou=[float(np.logical_and(m,source).sum()/max(1,np.logical_or(m,source).sum())) for m in masks]
        w=np.array(t['confidence'])>0
        err=[np.linalg.norm(np.array(x['uv'])-t['xy'],axis=-1) for x in [fb,fa]]
        rows.append(dict(i=fa['i'],shot=fa['shot'],iou_before=iou[0],iou_after=iou[1],valid=w.tolist(),error_before=err[0].tolist(),error_after=err[1].tolist()))
        f=after['frames'][fa['i']];expected=features(f['actors'][f['mainActor']],assets['actors'][f['mainActor']])
        fk_error=max(fk_error,float(np.linalg.norm(expected-np.array(fa['xyz']),axis=-1).max()))
    for s in spec['shots']:
        sid=s['id'];r=[r for r in rows if r['shot']==sid];ids=[r['i'] for r in r];valid=np.array([r['valid'] for r in r])
        es=[np.array([r['error_'+v] for r in r]) for v in ['before','after']]
        uv=[np.array([x['frames'][i]['uv'] for i in ids]) for x in [b,a]]
        jit=[motion_metrics(x) for x in uv];jall=[float(np.linalg.norm(np.diff(x,n=2,axis=0),axis=-1).mean()) for x in uv];shift,peaks=peak_shift(*uv)
        all_extrema_shift=0
        # Also audit unfiltered strict local extrema, including tiny tracking noise.
        for j in [0,5,6]:
            speeds=[np.linalg.norm(np.diff(x[:,j],axis=0),axis=-1) for x in uv]
            for sign in [1,-1]:
                aa,bb=[find_peaks(sign*x)[0] for x in speeds]
                ds=[min(abs(int(i)-bb),default=len(ids)) for i in aa]+[min(abs(int(i)-aa),default=len(ids)) for i in bb]
                all_extrema_shift=max(all_extrema_shift,max(ds,default=0))
        cr=[[c for c in cs if c['shot']==sid] for cs in contacts]
        cp=[100*sum(c['satisfied'] for c in cs)/sum(c['frames'] for c in cs) for cs in cr]
        mask=[float(np.mean([x['iou_'+v] for x in r])) for v in ['before','after']]
        rp=dict(shot=sid,frames=len(ids),keypoints_before=stats(es[0][valid]),keypoints_after=stats(es[1][valid]),body_before=stats(es[0][:,:7][valid[:,:7]]),body_after=stats(es[1][:,:7][valid[:,:7]]),hands_before=stats(es[0][:,7:][valid[:,7:]]),hands_after=stats(es[1][:,7:][valid[:,7:]]),iou_before=mask[0],iou_after=mask[1],jitter_before=jit[0],jitter_after=jit[1],peak_shift_frames=shift,all_extrema_shift_frames=int(all_extrema_shift),peak_details=peaks,contacts_before_pct=cp[0],contacts_after_pct=cp[1],contact_windows_before=cr[0],contact_windows_after=cr[1])
        rp['jitter_all_before'],rp['jitter_all_after']=jall
        rp['criteria']=dict(median_clearly_drops=rp['keypoints_after']['median']<=rp['keypoints_before']['median']*.9,target_10px=rp['keypoints_after']['median']<=10,jitter_not_increased=jit[1]<=jit[0]+1e-5,all_joint_jitter_not_increased=jall[1]<=jall[0]+1e-5,peaks_within_1_frame=shift<=1 and all_extrema_shift<=1,contacts_each_window_90pct=all(c['percent']>=90 for c in cr[1]),iou_not_decreased=mask[1]>=mask[0]-1e-6)
        reports.append(rp)
    timeline_keys=['i','t','shot','sourceT','sourceIndex','audioTime','audioMode','mainActor','camera']
    timeline_unchanged=all(all(f[k]==g[k] for k in timeline_keys) for f,g in zip(before['frames'],after['frames']))
    face_unchanged=all(f['actors'][aid].get('face')==g['actors'][aid].get('face') and f['actors'][aid].get('mouthOpen')==g['actors'][aid].get('mouthOpen') for f,g in zip(before['frames'],after['frames']) for aid in f['actors'])
    video=HERE/'jamforelse-opt.mp4';vinfo=None
    if video.exists():
        vinfo=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],text=True))
    integration=read(HERE/'integration-check.json') if (HERE/'integration-check.json').exists() else dict(pass_=False)
    report=dict(schema='scen3d-opt-verification/1',shots=reports,frames=rows,contacts_definition='Palm (mean index/middle/ring MCP) to visible oriented prop box <3 cm; pelvis centre 12 cm above chair surface within 3 cm and chair footprint; standing toe base 3 cm above floor within 3 cm. Occluded seat/feet are scene priors, not observed 3D ground truth.',keypoints_definition='Identical source-selected per-joint confidence gate before/after; seven core body points plus 40 finger joints; median/p90 pooled across every valid point/frame. Separate body/hand summaries prevent hiding finger error. Pixels at 576x1024.',jitter_definition='Mean Euclidean norm of second frame differences of seven core projected joints, px/frame^2; no cut-crossing derivatives.',peaks_definition='Head/nose and both wrist screen-speed maxima/minima; bidirectional nearest-frame shift. Prominent extrema (max(.25px/frame,10% speed range), distance3) AND all strict local extrema are required within one frame.',timeline_unchanged=timeline_unchanged,face_local_channels_unchanged=face_unchanged,native_fk_max_error_m=fk_error,video=vinfo,integration=integration,before_sha256=sha(HERE.parent/'bake.json'),after_sha256=sha(HERE/'bake-opt.json'))
    report['passed']=bool(timeline_unchanged and face_unchanged and fk_error<.00001 and integration.get('passed',False) and all(all(v for k,v in s['criteria'].items() if k!='target_10px') for s in reports))
    write(HERE/'verification-report.json',report)
    for s in reports:print(s['shot'],f"median {s['keypoints_before']['median']:.2f}->{s['keypoints_after']['median']:.2f}, P90 {s['keypoints_before']['p90']:.2f}->{s['keypoints_after']['p90']:.2f}, IoU {s['iou_before']:.4f}->{s['iou_after']:.4f}, jitter {s['jitter_before']:.4f}->{s['jitter_after']:.4f}, peaks {s['peak_shift_frames']}/{s['all_extrema_shift_frames']}, contact {s['contacts_before_pct']:.1f}->{s['contacts_after_pct']:.1f}",s['criteria'])
    print('ACCEPTANCE',report['passed'])
    if not report['passed']:sys.exit(1)

if __name__=='__main__':main()
