"""Build comparisons, six triptychs and machine-readable acceptance results."""
import json,time,subprocess,hashlib
from pathlib import Path
import cv2,numpy as np
from prepare_motion import EDGES,project
HERE=Path(__file__).resolve().parent
FRAMES=[38,120,160,228,288,330]
def read(p):return json.loads((HERE/p).read_text(encoding='utf-8'))
def write(p,v):(HERE/p).write_text(json.dumps(v,indent=2,allow_nan=False),encoding='utf-8')
def ff(args):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y']+args,check=True)
def title(im,text):
    out=cv2.copyMakeBorder(im,38,0,0,0,cv2.BORDER_CONSTANT,value=(25,25,25));cv2.putText(out,text,(12,25),cv2.FONT_HERSHEY_SIMPLEX,.55,(245,245,245),1,cv2.LINE_AA);return out
def main():
    start=time.perf_counter();d=np.load(HERE/'motion.npz');m=read('metrics.json');a=read('animation.json');out=HERE/'verifiering';out.mkdir(exist_ok=True)
    for f in FRAMES:
        src=cv2.imread(str(HERE/'source'/f'{f:04d}.jpg'));base=cv2.imread(str(HERE/'baseline'/f'{f:04d}.png'));final=cv2.imread(str(HERE/'render'/f'{f:04d}.png'));assert src is not None and base is not None and final is not None
        sheet=np.hstack([title(src,f'Source | frame {f}'),title(base,'A: MediaPipe | same rig'),title(final,'Chosen | Blender')]);cv2.imwrite(str(out/f'triptyk-{f:04d}.jpg'),sheet,[cv2.IMWRITE_JPEG_QUALITY,95])
    # Source | actual Blender, each panel 540x960, no retiming. Preserve initial black frames.
    source=str(HERE.parent.parent/'klipp/kand-interpooluppsala-7599643065644551446.mp4')
    ff(['-framerate','30','-start_number','0','-i',str(HERE/'render/%04d.png'),'-i',source,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-crf','18','-preset','fast','-c:a','aac','-ac','2','-ar','48000','-af','apad','-t','12.3','-movflags','+faststart',str(HERE/'blender.mp4')])
    ff(['-i',source,'-i',str(HERE/'blender.mp4'),'-filter_complex','[0:v]scale=540:960,setsar=1[l];[1:v]setsar=1[r];[l][r]hstack=inputs=2[v]','-map','[v]','-map','0:a:0','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-crf','18','-preset','fast','-c:a','aac','-ac','2','-ar','48000','-af','apad','-t','12.3','-movflags','+faststart',str(HERE/'jamforelse.mp4')])
    # Candidate comparison uses precisely the measured 3D reprojections, never detector 2D as model 3D.
    R=d['camera'][:,:3,:3]@np.diag([1.,-1.,-1.]);orig=d['camera'][:,:3,3];uvs=[]
    for key in ['a_world','c_world','chosen_world']:
        local=np.einsum('tji,tkj->tki',R,d[key]-orig[:,None]);uvs.append(project(local,d['K']))
    temp=HERE/'candidate-preview.avi';v=cv2.VideoWriter(str(temp),cv2.VideoWriter_fourcc(*'MJPG'),30,(1080,510))
    for i in range(369):
        src=cv2.imread(str(HERE/'source'/f'{i:04d}.jpg'));panels=[cv2.resize(src,(270,480))]
        for uv in uvs:
            im=cv2.resize(src,(270,480));q=uv[i]/2
            for aa,bb in EDGES:
                p1=tuple(np.rint(q[aa]).astype(int));p2=tuple(np.rint(q[bb]).astype(int));cv2.line(im,p1,p2,(40,230,255),2,cv2.LINE_AA)
            for pp in q:cv2.circle(im,tuple(np.rint(pp).astype(int)),3,(50,60,255),-1)
            panels.append(im)
        row=np.hstack(panels);row=cv2.copyMakeBorder(row,30,0,0,0,cv2.BORDER_CONSTANT,value=(25,25,25))
        for j,label in enumerate(['Source','A: MediaPipe 3D','C: MotionBERT','Chosen fit']):cv2.putText(row,label,(j*270+8,21),0,.55,(240,240,240),1,cv2.LINE_AA)
        v.write(row)
    v.release();ff(['-i',str(temp),'-i',source,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-crf','20','-c:a','aac','-ac','2','-ar','48000','-af','apad','-t','12.3','-movflags','+faststart',str(HERE/'bakeoff.mp4')])
    # Actual evaluated Blender common-joint audit (face points are not equivalent to head bone origin).
    indices=[0,1,2,3,4,5,6,11,12,13,14,15,16];rigmetrics={}
    for label in ['baseline','render']:
        data=read(label+'-rig-measurements.json');uv=np.array([[r['uv'][str(j)] for j in indices] for r in data]);world=np.array([[r['world'][str(j)] for j in indices] for r in data]);valid=d['conf'][:,indices]>.5;err=np.linalg.norm(uv-d['uv'][:,indices],axis=-1);edges=[(indices.index(x),indices.index(y)) for x,y in EDGES if x in indices and y in indices];lens=np.stack([np.linalg.norm(world[:,x]-world[:,y],axis=-1) for x,y in edges],axis=1)
        rigmetrics[label]=dict(mean_reprojection_px=float(err[valid].mean()),median_reprojection_px=float(np.median(err[valid])),jitter_m_s2=float(np.linalg.norm(np.diff(world,n=2,axis=0),axis=-1).mean()*900),bone_length_cv_percent=float(np.mean(np.std(lens,axis=0)/np.mean(lens,axis=0))*100))
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(HERE/'jamforelse.mp4')],text=True));video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio');mp4=(HERE/'jamforelse.mp4').read_bytes();faststart=mp4.find(b'moov')<mp4.find(b'mdat')
    media_checks=dict(frame_count=int(video['nb_frames'])==369,fps=video['r_frame_rate']=='30/1',resolution=(video['width'],video['height'])==(1080,960),h264_main=video['codec_name']=='h264' and video['profile']=='Main',yuv420p=video['pix_fmt']=='yuv420p',aac_stereo_48k=audio['codec_name']=='aac' and audio['channels']==2 and audio['sample_rate']=='48000',faststart=faststart,six_triptychs=len(list(out.glob('triptyk-*.jpg')))==6,all_render_frames=all((HERE/'render'/f'{i:04d}.png').exists() for i in range(369)))
    assert all(media_checks.values()),media_checks
    report=dict(overall='FAIL / incomplete acceptance',media=media_checks,actual_rig=rigmetrics,source_fit=m['candidates'],acceptance=dict(three_candidate_bakeoff='FAIL: RTMW weight commercial-use conflict; no RTMW numerical results',same_performance_visual='REQUIRES visual review; numerical detector agreement does not establish this',peak_timing='PASS' if m['max_peak_shift_frames']<=1 else f"FAIL: max shift {m['max_peak_shift_frames']} frames",foot_sliding='UNMEASURABLE: no confident visible contact intervals',camera='PARTIAL: own tracked fallback, uncalibrated scale/floor and 73 interpolated frames',face='51 MediaPipe non-neutral channels drive matching shape keys; tongueOut is not supplied by MediaPipe and stays zero',rig='PASS: native COPY_ROTATION constraints and NLA, no position IK',room='PARTIAL: 3 pool tables and room; placements estimated, not verified tracked anchors'),audio=dict(source_duration_s=12.281905,output_duration_s=12.3,silence_padding_s=.018095,retiming=False),packaging_seconds=time.perf_counter()-start)
    write('acceptance.json',report);write('ffprobe.json',probe);print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
