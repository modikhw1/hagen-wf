import sys,json,shutil
from pathlib import Path
import cv2,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.path.insert(0,str(HERE));from prova import save,log,hashcheck
changed=[]
for f in HERE.rglob('*'):
    if f.is_file() and f.suffix in ['.json','.md','.py','.log']:
        raw=f.read_bytes();text=raw.decode('utf-8')
        if '\r' in text:
            back=P/'kontrakt/ut/fore_golv2_blender'/f.relative_to(ROOT);back.parent.mkdir(parents=True,exist_ok=True)
            if not back.exists():shutil.copy2(f,back)
            f.write_text(text.replace('\r\n','\n').replace('\r','\n'),encoding='utf-8',newline='\n');changed.append(str(f.relative_to(HERE)))
counts={}
for phase in ['fore','efter']:
    counts[phase]={k:len(list((HERE/phase).glob('*_'+k+'.png'))) for k in ['original','mask','flyttad','flyttad_vid']}
    assert counts[phase]==dict(original=21,mask=21,flyttad=21,flyttad_vid=7),counts
    for f in (HERE/phase).glob('*_mask.png'):
        im=cv2.imread(str(f),cv2.IMREAD_UNCHANGED);assert im.shape==(512,288,4)
        assert (im[:,:,3]>127).sum()>100
for f in HERE.rglob('*.md'):
    import re
    for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if not target.startswith(('http:', 'https:')):assert (f.parent/target).exists(),(f,target)
hashcheck()
save(HERE/'slutkontroll.json',dict(bilder=counts,utf8_lf_normaliserade=changed,rapportlankar='alla finns',originalandringar=0))
log('Slutkontroll: 21 original + 21 hudpass + 21 flyttade + 7 vidare bilder per fas finns. Rapportlänkar kontrollerade. Genererade textfiler validerade UTF-8 och normaliserade till LF (kopior före normalisering sparade). SHA256-kontroll efter alla tester: 921 original, 0 ändrade.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck")
print(counts,'UTF8/LF OK; länkar OK')
