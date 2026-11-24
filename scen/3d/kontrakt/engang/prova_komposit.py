"""En ruta: verifiera samma alpha-overlay som den färdiga filmen använder."""
import copy
import json
import shutil
import wave
from pathlib import Path
from skarmtext import kompositera

HIT=Path(__file__).resolve().parent


if __name__=='__main__':
    d=HIT/'ut/fore_text/kompositprov';d.mkdir(exist_ok=False);(d/'render').mkdir()
    p=json.loads((HIT/'ut/b/tom/plan.json').read_text(encoding='utf-8'));k=json.loads((HIT/'ut/b/kalla.json').read_text(encoding='utf-8'))
    p['kallrutor']=[231];p['utdata']['antal_rutor']=1;p['skarmtext']=[]
    for t in k['semantik']['skarmtext']:
        if t['start_s']<=231/30<t['slut_s']:p['skarmtext'].append(dict(copy.deepcopy(t),ut=[0,1]))
    shutil.copyfile(HIT/'ut/b/tom/render/f0231.png',d/'render/f0000.png')
    with wave.open(str(d/'ljud.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(22050);f.writeframes(b'\0\0'*2205)
    kompositera(p,d);print(d,flush=True)
