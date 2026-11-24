"""Attach source audio without truncating the last animation frame; verify exports."""
import json
import subprocess
from pathlib import Path
from glb_gate import require_current_export,file_hash

HERE=Path(__file__).resolve().parent
OUT=HERE/'ut/c-sketch-tre'
SOURCE=HERE.parents[1]/'scen/klipp/c-sketch-tre.mp4'
export_report=require_current_export(OUT)
render_manifest=json.loads((OUT/'render_manifest.json').read_text(encoding='utf-8'))
assert render_manifest['blend_sha256']==export_report['blend_sha256'], 'Stale render: rebuild from current scene'
assert render_manifest['glb_sha256']==export_report['glb_sha256'], 'Stale render: export changed'
assert render_manifest['video_sha256']==file_hash(OUT/'animatik_silent.mp4'), 'Stale render manifest'
meta=json.loads((OUT/'ingest/meta.json').read_text())
duration=meta['N']/meta['fps']
common=['-c:a','aac','-b:a','160k','-af','apad','-t',str(duration),'-movflags','+faststart']
subprocess.run(['ffmpeg','-y','-v','error','-i',str(OUT/'animatik_silent.mp4'),'-i',str(SOURCE),
                '-map','0:v:0','-map','1:a:0','-c:v','copy',*common,str(OUT/'animatik.mp4')],check=True)
subprocess.run(['ffmpeg','-y','-v','error','-i',str(SOURCE),'-i',str(OUT/'animatik_silent.mp4'),
                '-filter_complex','[0:v]scale=288:512,setsar=1,setpts=PTS-STARTPTS[a];[1:v]setsar=1,setpts=PTS-STARTPTS[b];[a][b]hstack=inputs=2[v]',
                '-map','[v]','-map','0:a:0','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',
                *common,str(OUT/'jamforelse.mp4')],check=True)
report={}
for name in ('animatik.mp4','jamforelse.mp4'):
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(OUT/name)]))
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    audio=next(s for s in info['streams'] if s['codec_type']=='audio')
    assert int(video['nb_frames'])==meta['N'],(name,video['nb_frames'])
    assert abs(float(video['duration'])-duration)<.001
    report[name]={'frames':int(video['nb_frames']),'seconds':float(video['duration']),
                  'resolution':[video['width'],video['height']],'video_codec':video['codec_name'],'audio_codec':audio['codec_name']}
(OUT/'delivery_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
