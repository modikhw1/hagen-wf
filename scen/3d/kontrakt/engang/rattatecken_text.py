"""Återställ schemasvenska från säkerhetskopian utan att ändra valideringen."""
import copy
import json
import shutil
from pathlib import Path
from textarbete import jsonfil,UT

HIT=Path(__file__).resolve().parent
BAD='\u00c3\u00c2\ufffd'


def without_descriptions(v):
    if isinstance(v,dict):return {k:without_descriptions(x) for k,x in v.items() if k!='description'}
    if isinstance(v,list):return [without_descriptions(x) for x in v]
    return v


def main():
    logs=[]
    for name in ['kalla.schema.json','regi.schema.json']:
        f=HIT/name;old=json.loads((UT/'scen/3d/kontrakt'/name).read_text(encoding='utf-8'))
        now=json.loads(f.read_text(encoding='utf-8'));before=copy.deepcopy(now);paths=[]
        def fix(v,source,path=''):
            if isinstance(v,dict):
                for key,value in v.items():
                    src=source.get(key) if isinstance(source,dict) else None
                    if key=='description' and isinstance(value,str) and any(c in value for c in BAD):
                        corrected=src if isinstance(src,str) else value
                        for _ in range(4):
                            if not any(c in corrected for c in BAD):break
                            candidates=[]
                            for encoding in ['cp1252','latin1']:
                                try:candidates.append(corrected.encode(encoding).decode('utf-8'))
                                except UnicodeError:pass
                            if not candidates:break
                            corrected=min(candidates,key=lambda s:sum(s.count(c) for c in BAD))
                        assert not any(c in corrected for c in BAD),(path,key,corrected)
                        v[key]=corrected;paths.append(path+'/'+key)
                    else:fix(value,src,path+'/'+key)
            elif isinstance(v,list):
                for i,value in enumerate(v):fix(value,source[i] if isinstance(source,list) and i<len(source) else None,path+'/'+str(i))
        fix(now,old)
        assert without_descriptions(before)==without_descriptions(now)
        archive=UT/'teckenkod_fore_rattning'/name;archive.parent.mkdir(exist_ok=True)
        if not archive.exists():shutil.copy2(f,archive)
        jsonfil(f,now);logs.append(dict(fil=name,antal=len(paths),bara_beskrivningar=True,sokvagar=paths))
    jsonfil(UT/'teckenkod_rattad.json',logs)
    print([(r['fil'],r['antal']) for r in logs])


if __name__=='__main__':main()
