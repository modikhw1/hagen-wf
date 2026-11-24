"""YOLO person union vs visible Blender actor union, without alignment or dilation."""
import os
from pathlib import Path
HERE = Path(__file__).resolve().parent
os.environ['YOLO_CONFIG_DIR'] = str(HERE / 'yolo_config')
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from ultralytics import YOLO
MODEL = HERE.parents[2] / 'py/modeller/yolo11n-seg.pt'
model = YOLO(str(MODEL))
rows = []
for image_path in sorted(HERE.glob('forsta_S*.png')):
    sid = image_path.stem.split('_')[1]
    im = Image.open(image_path).convert('RGB')
    result = model.predict(str(image_path), classes=[0], conf=.25, imgsz=1024, retina_masks=True, device='cpu', verbose=False)[0]
    pred = np.zeros((im.height, im.width), dtype=bool)
    if result.masks is not None:
        for mask in result.masks.data.cpu().numpy():
            pred |= np.array(Image.fromarray((mask > .5).astype('uint8')*255).resize(im.size, Image.Resampling.NEAREST)) > 127
    ref_im = Image.open(HERE / 'masker' / f'blockout_{sid}.png').convert('L')
    if ref_im.size != im.size: raise RuntimeError(f'Dimension mismatch: {sid}')
    ref = np.asarray(ref_im) > 127
    inter, union = int((ref & pred).sum()), int((ref | pred).sum())
    iou = inter / union if union else 0.
    Image.fromarray(pred.astype('uint8')*255).save(HERE/'masker'/f'ps2_{sid}.png')
    overlay = np.zeros((*pred.shape, 3), dtype='uint8')
    overlay[ref & pred] = [230,230,230]
    overlay[ref & ~pred] = [255,150,30]
    overlay[pred & ~ref] = [30,150,255]
    Image.fromarray(overlay).save(HERE/'masker'/f'overlap_{sid}.png')
    triptych = Image.new('RGB', (im.width*3, im.height+36), '#202020')
    for i, (p, label) in enumerate([(HERE/'referenser'/f'kalla_{sid}.png','SOURCE'), (HERE.parent/'ut'/f'forsta_{sid}.png','BLOCKOUT'),(image_path,f'PS2  IoU {iou:.4f}')]):
        triptych.paste(Image.open(p).convert('RGB').resize(im.size), (i*im.width,36))
        ImageDraw.Draw(triptych).text((i*im.width+10,10), f'{sid} {label}', fill='white')
    triptych.save(HERE/f'kontroll_{sid}.jpg', quality=94)
    row = dict(shot=sid,iou=iou,pass_iou=iou>=.7,intersection_px=inter,union_px=union,blockout_px=int(ref.sum()),ps2_px=int(pred.sum()),detected_people=len(result.boxes),confidences=result.boxes.conf.cpu().tolist(),boxes_xyxy=result.boxes.xyxy.cpu().tolist(),image_sha256=hashlib.sha256(image_path.read_bytes()).hexdigest(),blockout_mask_sha256=hashlib.sha256((HERE/'masker'/f'blockout_{sid}.png').read_bytes()).hexdigest(),ps2_mask_sha256=hashlib.sha256((HERE/'masker'/f'ps2_{sid}.png').read_bytes()).hexdigest())
    rows.append(row)
    print(f'{sid}: IoU={iou:.6f} people={len(result.boxes)} ref={ref.sum()} pred={pred.sum()}', flush=True)
data = dict(method='Union of YOLO class 0 masks vs Blender visible actor collection, retaining set/prop occlusion. No translation, warping, dilation or optimization of masks.',model=str(MODEL.relative_to(HERE.parents[3])),model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),confidence=.25,imgsz=1024,retina_masks=True,threshold=.7,shots=rows)
(HERE/'mask_metrics.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
