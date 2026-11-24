import sys, glob, json
from faster_whisper import WhisperModel
sys.stdout.reconfigure(encoding='utf-8')
m = WhisperModel('small', device='cpu', compute_type='int8', download_root=sys.argv[2])
ut = {}
for f in sorted(glob.glob(sys.argv[1] + '/*.mp4')):
    import subprocess, numpy as np; a = np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout, np.int16).astype(np.float32)/32768; segs, info = m.transcribe(a, language='en', vad_filter=True)
    t = [(round(s.start, 1), s.text.strip()) for s in segs]
    ut[__import__('os').path.basename(f)] = t
    print('==', f[-27:], '|', ' / '.join(f'{a}s {b}' for a, b in t)[:500], flush=True)
json.dump(ut, open(sys.argv[1] + '/../transkript.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
