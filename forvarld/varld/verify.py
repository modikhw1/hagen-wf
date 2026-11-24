"""Audit the delivered package against exported skinning and delivered evidence."""
import os
os.environ['PYTHONIOENCODING']='utf-8'
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from refine import pose
OUT=Path(__file__).resolve().parent;PK=OUT/'paket/notan';IM=OUT/'bilder'
M=json.loads((PK/'manifest.json').read_text(encoding='utf8'))
report=dict(scenes=[],frames=M['frames'],packageBytes=sum(p.stat().st_size for p in PK.iterdir() if p.is_file()))
assert len(M['scenes'])==7 and len(M['cameras']['nycklar'])==383
for s in M['scenes']:
    m=s['person'];raw=dict(np.load(OUT/'intermediat'/f"{m['stem']}-raw.npz"));data=np.fromfile(PK/f"{m['stem']}.bin",dtype='<f4');n=m['triangles']*3
    assert m['triangles']==1800 and m['bones']==126
    assert len(data)==n*13+m['frames']*m['bones']*16
    assert np.array_equal(data[:n*3].reshape(n,3),raw['pos'][raw['tri'].ravel()]),s['id']+' mesh changed'
    assert np.array_equal(data[n*3:n*7].reshape(n,4),raw['ids'][raw['tri'].ravel()])
    assert np.array_equal(data[n*7:n*11].reshape(n,4),raw['weights'][raw['tri'].ravel()])
    assert np.array_equal(data[n*13:],raw['matrices'].ravel()),s['id']+' bone palettes changed'
    assert np.allclose(raw['weights'].sum(1),1,atol=1e-6)
    assert np.array(Image.open(PK/f"{m['stem']}-observed.png")).astype(bool).sum()==m['observedTexels']
    allpoints=np.concatenate([pose(raw,i) for i in range(m['frames'])]);collisions=[]
    for j,o in enumerate(M['room']):
        a,b=o.get('synlig_ut',[0,383])
        if not a<=s['source'][0]<b or o.get('deltyp') not in ['golv','vagg','stol']:continue
        centre=np.array(next((r['position'] for r in s.get('roomAdjustments',[]) if r['objectIndex']==j),o['pos_m']))
        angle=o['rotation_rad'][2];R=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
        local=(allpoints-centre)@R;inside=(abs(local)<np.array(o['matt_m'])/2-1e-5).all(1)
        if inside.any():collisions.append(dict(objectIndex=j,id=o['id'],vertexInstances=int(inside.sum())))
    report['scenes'].append(dict(id=s['id'],meshAndSkinExact=True,assumedSurfaceFraction=m['assumedSurfaceFraction'],roomVertexIntersections=collisions))
    for kind in ['head','foreground','nearForeground']:
        if kind not in s['layers']:continue
        a=np.array(Image.open(PK/s['layers'][kind]['texture']))
        assert a.shape==(1024,576,4)
        assert (a[:,:,:3][a[:,:,3]==0]==0).all()
for j in range(1,8):
    for suffix in ['', '-source','-ps2','-room','-layered','-changed']:
        assert (IM/f's{j}{suffix}.png').is_file()
plain=np.asarray(Image.open(IM/'look-plain.png').convert('RGB')).astype(float)
ps2=np.asarray(Image.open(IM/'look-ps2.png').convert('RGB')).astype(float)
report['plainVsPS2']=dict(outputPixels=[576,1024],meanAbsoluteChannelDifference=float(abs(plain-ps2).mean()),differentPixelFraction=float((abs(plain-ps2).max(2)>0).mean()))
for j in range(1,5):assert (IM/f'rorelse-{j}.png').is_file()
if (IM/'ps2-6s.mp4').exists():
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,codec_type,width,height,nb_frames','-of','json',str(IM/'ps2-6s.mp4')],capture_output=True,text=True,check=True)
    report['video']=json.loads(r.stdout)
else:report['video']='not yet composed'
report['remainingRoomIntersections']=sum(len(s['roomVertexIntersections']) for s in report['scenes'])
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
