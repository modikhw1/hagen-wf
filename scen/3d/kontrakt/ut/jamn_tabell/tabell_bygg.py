import re
names={'raw':'raw (estimatorn)','gammal':'gammal stabilisering (Hampel + 6 Hz)','bildskydd':'bildskydd (som tom2)','sg9/3':'Savitzky-Golay 9/3','oneeuro':'One-Euro (dubbelriktad)',
 'whitt fc4 k2 d2 T-gammal':'Whittaker 4 Hz, utan rör','ror fc4 k2 d2 T-gammal':'rör 4 Hz k2, gammal cam_t','ror fc4 k2 d2 T-ny':'**rör 4 Hz k2 + ny cam_t (vald)**',
 'ror fc4 k1 d2 T-gammal':'rör k1','ror fc4 k3 d2 T-gammal':'rör k3','ror fc3 k2 d3 T-gammal':'rör 3 Hz, jerk-straff (d3)','ror fc6 k2 d2 T-gammal':'rör 6 Hz k2'}
out=['# Utjämningsmetoder, sju scener (jamn_utvardera.py, rå-estimat ur kropp/, tagningens egen kamera före golv/kontakt)','',
'px = avvikelse mot estimatorns 2D-punkter (EJ oberoende; 42 av 48 punkter är fingerleder). IoU = hudnätets silhuett mot YOLO-masken, alla rutor med mask (oberoende modell; `syn` = klippt vid maskens nedre rad). Darr = medel andra differens, 127 leder, cm/ruta², kamerarum. Täckning px / IoU = bedömda rutor / rutor i tagningen.','']
for fn in ('b_s1.log','tabell1.log'):
    cur=None
    for l in open(fn,encoding='utf-8',errors='replace'):
        l=l.rstrip()
        m=re.match(r'.*ingest/ut/(\S+) person (\d+)',l)
        if m:
            cur=m.group(1); out+=['',f'### {cur} person {m.group(2)}','','| metod | px median | px p90 | IoU | IoU syn | darr | täckn px | täckn IoU |','|---|---|---|---|---|---|---|---|']; continue
        for k,v in names.items():
            if l.startswith(k+' ') and cur:
                f=l[len(k):].split(); out.append(f'| {v} | '+' | '.join(f[:2]+[f[2],f[3]]+[f[5],f[6],f[7]])+' |'); break
open('tabell.md','w',encoding='utf-8').write('\n'.join(out)+'\n')
