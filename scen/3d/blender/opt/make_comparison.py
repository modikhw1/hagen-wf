"""Frame-exact source | before | after, original audio, Windows-safe encoding."""
from common import *
import cv2, subprocess, struct

def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],text=True))
def atoms(p):
    result=[]
    with Path(p).open('rb') as f:
        while True:
            at=f.tell();h=f.read(8)
            if len(h)<8:break
            size,name=struct.unpack('>I4s',h)
            if size==1:size=struct.unpack('>Q',f.read(8))[0]
            if size==0:break
            result.append([name.decode('ascii','replace'),at]);f.seek(at+size)
    return result

def main():
    paths=[ROOT.parent/'klipp/d-dialog-notan.mp4',HERE.parent/'ut/blockout.mp4',HERE/'ut/blockout.mp4']
    caps=[cv2.VideoCapture(str(p)) for p in paths];assert all(c.isOpened() for c in caps)
    for c in caps:assert round(c.get(cv2.CAP_PROP_FRAME_COUNT))==383
    output=HERE/'jamforelse-opt.mp4'
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','1728x1060','-r','30','-i','pipe:0','-i',str(HERE.parent/'ljud-original.wav'),'-map','0:v','-map','1:a','-af','apad','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-crf','18','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-movflags','+faststart','-t',str(383/30),str(output)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    selected={36:'S1',93:'S2',142:'S3',213:'S4',268:'S5',309:'S6',360:'S7'}
    for i in range(383):
        images=[]
        for c in caps:
            ok,im=c.read();assert ok,f'Missing video frame {i}';assert im.shape[:2]==(1024,576);images.append(im)
        frame=np.zeros((1060,1728,3),np.uint8);frame[36:]=np.hstack(images)
        for j,label in enumerate(['SOURCE','BEFORE','AFTER']):cv2.putText(frame,f'{label}  |  frame {i:03d}  {i/30:.3f}s',(j*576+12,25),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),1,cv2.LINE_AA)
        process.stdin.write(frame.tobytes())
        if i in selected:cv2.imwrite(str(HERE/f'comparison-{selected[i]}.jpg'),frame,[cv2.IMWRITE_JPEG_QUALITY,92])
    process.stdin.close();assert process.wait()==0
    for c in caps:c.release()
    info=probe(output);vs=next(s for s in info['streams'] if s['codec_type']=='video');au=next(s for s in info['streams'] if s['codec_type']=='audio');top=atoms(output);locations=dict(top)
    checks=dict(video_frames=int(vs['nb_frames'])==383,fps=vs['avg_frame_rate']=='30/1',h264_main=vs['codec_name']=='h264' and vs['profile']=='Main',yuv420p=vs['pix_fmt']=='yuv420p',aac_stereo_48khz=au['codec_name']=='aac' and au['channels']==2 and au['sample_rate']=='48000',faststart=locations['moov']<locations['mdat'],duration=abs(float(info['format']['duration'])-383/30)<1/30,original_audio_copy=sha(HERE/'ljud-original.wav')==sha(HERE.parent/'ljud-original.wav'),blend_saved=(HERE/'scen-opt.blend').exists(),render_outputs=all((HERE/'ut'/f'tagning_S{i}.mp4').exists() and (HERE/'ut'/f'djup_S{i}.png').exists() for i in range(1,8)))
    report=dict(passed=all(checks.values()),checks=checks,video=info,mp4_top_level_atoms=top,source_files=[str(p) for p in paths],source_audio_sha256=sha(HERE.parent/'ljud-original.wav'),optimized_bake_sha256=sha(HERE/'bake-opt.json'),commands=['bygg_scen.py --bake opt/bake-opt.json --arbetsut opt --spara opt/scen-opt.blend','rendera.py --arbetsut opt --ut opt/ut --windows-video'],encode_command=command)
    write(HERE/'integration-check.json',report);print(json.dumps(checks,indent=2));assert report['passed']

if __name__=='__main__':main()
