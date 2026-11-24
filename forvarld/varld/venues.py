"""Small masked background medians from existing static shots. No service/Blender."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import json,warnings,time
import cv2,numpy as np
from scipy.ndimage import distance_transform_edt
from export import wait_heavy
O=Path('forvarld/varld'); D=O/'paket/backdrops';D.mkdir(exist_ok=True)
def read(p):
 try:return json.loads(Path(p).read_text(encoding='utf8'))
 except UnicodeDecodeError:return json.loads(Path(p).read_text(encoding='cp1252'))
bank=[];audit=[];start=time.perf_counter()
for clip,directory in [('b','b-tilltal-ravara-tagningar'),('a','a-sketch-servering-tagningar'),('kenny','kand-kennysgelato-tagningar')]:
 base=Path('scen/3d/ingest/ut')/directory; sem=read(f'scen/3d/kontrakt/semantik/ut/{clip}/semantik.json')['data']; shots=read(base/'tagningar.json')
 for s in shots['tagningar']:
  wait_heavy();sd=base/s['id'];camera=read(sd/'kamera.json') if (sd/'kamera.json').exists() else {}; desc=next((x['beskrivning'] for x in sem['kamerauppstallningar'] if s['id'] in x['tagningar']),'okänd')
  reason='moving camera' if not camera.get('statisk') else 'detail/overhead shot, no useful venue' if any(w in desc.lower() for w in ['närbild','uppifrån']) else None
  if reason:audit.append(dict(clip=clip,shot=s['id'],excluded=reason));continue
  mk=np.load(sd/'masker.npy',mmap_mode='r');cap=cv2.VideoCapture(str(base/'klipp'/f"{s['id']}.mp4"));stack=[]
  for i in np.unique(np.linspace(0,len(mk)-1,min(25,len(mk))).astype(int)):
   cap.set(cv2.CAP_PROP_POS_FRAMES,int(i));ok,im=cap.read()
   if not ok:continue
   im=cv2.resize(im,(288,512)).astype(np.float32);mask=cv2.resize(mk[i].astype(np.uint8),(288,512),interpolation=cv2.INTER_NEAREST);mask=cv2.dilate(mask,np.ones((13,13),np.uint8))>0;im[mask]=np.nan;stack.append(im)
  cap.release()
  if not stack:continue
  with warnings.catch_warnings():warnings.simplefilter('ignore');plate=np.nanmedian(np.stack(stack),axis=0)
  missing=np.isnan(plate[:,:,0]);unknown=float(missing.mean());audit.append(dict(clip=clip,shot=s['id'],unknown=unknown,samples=len(stack)))
  if missing.all() or unknown>.65:audit[-1]['excluded']='more than 65% never observed';continue
  plate[missing]=0;plate=cv2.inpaint(plate.astype(np.uint8),missing.astype(np.uint8)*255,5,cv2.INPAINT_TELEA)
  # Source overlays are not venue signage. Conservative manually assumed erase areas.
  erase=np.zeros((512,288),np.uint8)
  if clip=='b':erase[240:465,20:270]=255
  elif clip=='a':erase[300:425,20:270]=255
  else:erase[95:165,10:278]=255
  plate=cv2.inpaint(plate.astype(np.uint8),erase,5,cv2.INPAINT_TELEA)
  id=f'{clip}_{s["id"].lower()}';cv2.imwrite(str(D/(id+'.jpg')),plate,[cv2.IMWRITE_JPEG_QUALITY,91])
  label={'a':'Snabbmatsdisk','b':'Charkbutik','kenny':'Glassbar'}[clip]+' '+s['id']
  bank.append(dict(id=id,url='/paket/backdrops/'+id+'.jpg',label=label,source=clip,shot=s['id'],kind=sem['plats']['typ'],description=sem['plats']['beskrivning'],sourceFile=str(Path(shots['klipp']).relative_to(Path.cwd())) if Path(shots['klipp']).is_absolute() else shots['klipp'],semanticFile=f'scen/3d/kontrakt/semantik/ut/{clip}/semantik.json',static=True,unknownFraction=unknown,horizon=.45,floor=.80,status={'pixels':'measured','placeKind':'model-judged','holeFill':'assumed','horizonFloor':'assumed','projection':'template'},assumption='Masked median 25 frames max; never observed pixels locally inpainted, source overlays manually erased/inpainted. Flat rear card uses original scene coordinates; no room reconstruction.'))
manifest=read(O/'paket/notan/manifest.json');manifest['backdrops']=bank
manifest['provenance']['assumed'].append('Venue plates: original table and person depths retained. Rear card at 2.8x torso depth; horizon .45 in venue aligned to .45 in close shot, .40 in s7; floor .80 aligned to .84/.62. This is a 2D framing assumption, not metric reconstruction. Uploaded images assume horizon .52 and floor .8.')
(O/'paket/notan/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
(D/'bank.json').write_text(json.dumps(dict(bank=bank,audit=audit,seconds=time.perf_counter()-start),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(count=len(bank),ids=[b['id'] for b in bank],seconds=time.perf_counter()-start)))
