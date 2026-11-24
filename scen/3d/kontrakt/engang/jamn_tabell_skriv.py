"""Rätta den befintliga metodtabellen från den fulla lokala ommätningen."""
import json
from prop_filer import andra,ROT

rows=json.loads((ROT/'scen/3d/kontrakt/ut/prop_granskning/metoder_korrigerade.json').read_text(encoding='utf-8'))
lines=['# Utjämningsmetoder: sju scener, rättat ledurval','',
       'Rättat 10 november: den tidigare tabellen räknade bara två axelleder när benen var dolda. Filmens kvalitetssida räknade också alla 42 fingerleder. Nu räknar båda samma 44 par (48 med synliga ben), på samma pålitliga rutor. B s1 blir 15,73/48,50 px, exakt filmens värden. Formparametrar låses till samma median som sekvens_stabil.py; det tidigare påståendet att råformen var konstant var fel.','',
       'Alla tabellmetoder mäts före golv/kontakt/stöd i tagningens kamera. Filmens sida gäller kroppen efter dessa steg. Px är avvikelse från estimatorns egna 2D-punkter, inte oberoende kvalitet. IoU är hudnät mot YOLO-mask på alla mätbara maskrutor; synlig klipper vid maskens underkant. Darr: 127 leder, cm/ruta² i kamerarum. Täckning är px / mask. Parametrarna och diagnostiska gränserna har inte ändrats för att få godkända resultat.','']
for name,record in rows.items():
    lines+=['','## '+name,'','| Metod | median px | p90 px | IoU | IoU synlig | Darr | Täckning px/mask |','|---|---:|---:|---:|---:|---:|---:|']
    for r in record['rader']:
        name=r['metod']+(' (vald)' if r['metod']=='ror fc4 k2 d2 T-ny' else '')
        lines.append(f"| {name} | {r['px_median']:.2f} | {r['px_p90']:.2f} | {r['iou']:.3f} | {r['iou_synlig']:.3f} | {r['darr']:.2f} | {r['tackning_px']:.2f}/{r['tackning_iou']:.2f} |")
lines+=['','Valet behålls för jämn rörelse utan bildskyddets ruta-för-ruta-blandning. Det ger inte samtidigt bra fingerpassning i alla scener. Kenny s1 och a s1 har fortfarande för mycket darr enligt de oförändrade gränserna. Att byta parameteruppsättning utan en ny oberoende granskning skulle inte lösa det.']
andra('scen/3d/kontrakt/ut/jamn_tabell/tabell.md',lambda s:'\n'.join(lines)+'\n')
