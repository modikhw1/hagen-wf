"""För in granskade textreferenser i befintliga källkontrakt, med backup."""
import json
from pathlib import Path
from textarbete import jsonfil, UT
from skarmtext import items

HIT=Path(__file__).resolve().parent


def kor():
    for clip in ('kenny','a','notan'):
        f=HIT/'exempel/notan/kalla.json' if clip=='notan' else HIT/f'ut/{clip}/kalla.json'
        k=json.loads(f.read_text(encoding='utf-8'));sem=json.loads((HIT/f'semantik/ut/{clip}/semantik.json').read_text(encoding='utf-8'))
        video=(f.parent/k['klipp']['video']['sokvag']).resolve()
        k['semantik']['skarmtext'],log=items(k,sem,video);jsonfil(f,k);jsonfil(HIT/f'ut/{clip}/textmatning_granskad.json',log)
        print(clip,[(t['scen'],round(t['start_s'],3),round(t['slut_s'],3),t['text']) for t in k['semantik']['skarmtext']],flush=True)
        if clip=='notan':
            # Samma relativa djup: exempel/notan och ut/notan har identiska referensbaser.
            jsonfil(HIT/'ut/notan/kalla.json',k)


if __name__=='__main__':kor()
