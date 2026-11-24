"""Komplettera en källkopia med lokal propmätning. Ingen modelltjänst.

python kalla_prop.py <kalla.json> <semantik.json> <klipp> <ny kalla.json>
Utfilen måste ligga bredvid källan och får inte finnas. Källregioner är
manuellt avlästa, handleder kommer från sparad kropp, ytor från rumsmall.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from propbank import hamta
from trohet import IX

HIT = Path(__file__).resolve().parent

def ursprung(typ, metod, konfidens='medel', **extra):
    return dict(typ=typ, metod=metod, konfidens=konfidens, **extra)

def fyll(k, bas, sem, clip, semfil=None):
    k = copy.deepcopy(k); data = sem['data']; w = k['klipp']['video']['bredd']; h = k['klipp']['video']['hojd']
    refs = json.loads((HIT/'prop_referenser.json').read_text(encoding='utf-8'))
    spec = refs[clip]; video = (bas/k['klipp']['video']['sokvag']).resolve()
    cap = cv2.VideoCapture(str(video))
    props = list(data['props'])
    if clip == 'notan':
        props.append(dict(id='burk_kallbild', typ='can', etikett='Gul burk i källbilden', hallare='ingen',
                          tagningar=['S1', 'S3', 'S6'], anvands='Står på bordet', konfidens='medel'))
    for raw in props:
        bank = hamta(raw['typ']); scenes = []
        for sid, boxes in spec.get(raw['id'], {}).items():
            sc = next(s for s in k['semantik']['scener'] if s['id']==sid)
            kam = next(c for c in k['matning']['kameror'] if c['id']==sc['kamera'])
            folder = (bas/kam['spar_metrisk']['sokvag']).resolve().parent
            n = len(np.load(folder/'varld.npz')['kam_C']); off = kam.get('kalla_ruta0', 0)
            records = []
            for f, box in zip([n//3, 2*n//3], boxes):
                if box is None: continue  # Produkten ligger utanför bilden; ingen region uppfinns.
                box = np.array(box)*[w,h,w,h]; cap.set(1,off+f); ok, image = cap.read(); color = None
                if ok:
                    x0,y0,x1,y1 = np.round(box).astype(int); crop = image[max(0,y0):min(h,y1),max(0,x0):min(w,x1)]
                    if crop.size:
                        hsv = cv2.cvtColor(crop,cv2.COLOR_BGR2HSV); pixels = crop[hsv[:,:,1]>60]
                        if len(pixels)<10: pixels=crop.reshape(-1,3)
                        color=np.round(np.median(pixels[:,::-1],0)).astype(int).tolist()
                records.append(dict(lokal_ruta=f,kallruta=off+f,box_px=box.tolist(),rgb=color))
            measured = [m for m in k['matning']['personer'] if m.get('scen')==sid]
            semantic_person = next((p for p in data['personer'] if p['id']==raw['hallare']),None)
            tracks = [x['spar_id'] for x in semantic_person['spar'] if x['tagning'].lower()==sid] if semantic_person else []
            holder = next((m for m in measured if m.get('ingest_id') in tracks),None)
            owner_status = ursprung('modellbedomd','Hållare ur sparad semantik.',raw['konfidens'],modell=sem['ursprung']['modell'])
            # Semantiken anger P3 för alla slaktare och P2 också där kunden har tallriken.
            if holder is None and measured and raw['hallare']!='ingen':
                holder=measured[0]; owner_status=ursprung('antagen','Semantikens hållare saknas i scenen; synlig person med produkten i det granskade källbladet. Semantiken är motsägande.','lag')
            mode='hand'; surface=None; track=None
            if clip=='notan': mode='hand' if sid=='s5' and raw['id']=='o1' else 'yta'
            if clip=='b' and (raw['id']=='o2' or sid in ('s8','s9','s10')): mode='yta'
            if clip=='a' and sid=='s6': mode='yta'
            if clip=='b' and raw['id']=='o1' and sid=='s5':
                mode='kamera_hand'; track='2'; holder=None
                owner_status=ursprung('modellbedomd','Kamerapersonens förgrundshand, spår 2 enligt ej_personer i semantiken; ingen full personidentitet mäts.','hog',modell=sem['ursprung']['modell'])
            if mode=='yta':
                surface='bord' if clip=='notan' else 'disk'
                if clip=='b' and raw['id']=='o1' and sid in ('s8','s9','s10'): surface='prop_o2'
            hand=None
            if mode=='hand' and holder and records:
                files=sorted((folder/'kropp'/str(holder['ingest_id'])).glob('*.npz'))
                if files:
                    # Källprovet kan ligga i en kort lucka. Byt då inte till en
                    # hand från en helt annan del av scenen.
                    records.sort(key=lambda r:min(abs(int(x.stem)-r['lokal_ruta']) for x in files))
                    f=records[0]['lokal_ruta'];rp=min(files,key=lambda x:abs(int(x.stem)-f))
                else: rp=folder/'ingen_handled.npz'
                if rp.exists() and abs(int(rp.stem)-f)<=5:
                    with np.load(rp) as b:
                        center=np.mean(np.array(records[0]['box_px']).reshape(2,2),axis=0)
                        # MHR70:s sista punkt i varje hand är handledens twist-led.
                        hand='hoger' if np.linalg.norm(b['pred_keypoints_2d'][41]-center)<np.linalg.norm(b['pred_keypoints_2d'][62]-center) else 'vanster'
            placement_status=ursprung('antagen','Grepphand väljs närmast avläst produktregion vid en provruta med kroppsskattning inom fem rutor (antagen tolerans). Greppets djup följer handleden; utsträckning och dolda sidor är bankvärden. Saknad hand betyder ingen byggbar mätning.','lag')
            if mode=='yta': placement_status=ursprung('antagen','Regionens siktlinje skär mallens bord/diskskiva. Ythöjd och djup är mallantaganden; ingen uppmätt objektposition i 3D.','lag')
            if mode=='kamera_hand': placement_status=ursprung('antagen','Förgrundsspår 2 är kamerahand enligt semantiken. Boxens övre del styr hand, djup 0,65 m är antaget; ingen full kropp skapas.','lag')
            scenes.append(dict(scen=sid,lage=mode,hallare=holder['person'] if holder else None,hand=hand,
                               led=('r' if hand=='hoger' else 'l')+'_wrist_twist' if hand else None,
                               yta=surface,spar_id=track,bildregioner=records,
                               ursprung=dict(hallare=owner_status,placering=placement_status,
                                   bildregion=ursprung('uppmatt',refs['beskrivning'],'lag'),
                                   farg=ursprung('uppmatt','Median RGB av mättade pixlar i regionen; bakgrund och skärmtext kan ingå.','lag'),
                                   matt=ursprung('antagen','Bredd ur regionens pixelbredd och handdjup eller mallplan; andra dimensioners proportioner från propbanken.','lag'))))
        typ_origin=ursprung('modellbedomd','Typ och användning ur sparad semantik.',raw['konfidens'],modell=sem['ursprung']['modell'])
        if raw['id']=='burk_kallbild': typ_origin=ursprung('antagen','Burkform och närvaro avläst i källbladen; burken saknas i semantikfilen.','medel')
        k['semantik']['props'].append(dict(id='prop_'+raw['id'],typ=raw['typ'],etikett=raw['etikett'],agare=None,stod=None,faste=None,rum_ref=None,kalla='lokal propmätning',
             rekonstruktion=dict(schema_version='prop/1',anvands=raw['anvands'],semantik_id=raw['id'],
                 semantik_fil=str(semfil) if semfil else None,ursprung=typ_origin,bank=bank,scener=scenes)))
    cap.release(); k['revision']+=1
    return k

def main():
    src, semfil, clip, dst = sys.argv[1:]; src=Path(src).resolve();dst=Path(dst).resolve();semfil=Path(semfil).resolve()
    if dst.exists(): raise FileExistsError(dst)
    if src.parent!=dst.parent: raise ValueError('Källkopian måste ligga bredvid originalet.')
    k=fyll(json.loads(src.read_text(encoding='utf-8')),src.parent,json.loads(semfil.read_text(encoding='utf-8')),clip,semfil)
    dst.write_text(json.dumps(k,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(dst, 'props', len(k['semantik']['props']))

if __name__=='__main__': main()
