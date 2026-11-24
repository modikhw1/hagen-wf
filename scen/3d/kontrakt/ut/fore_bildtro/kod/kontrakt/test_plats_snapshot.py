"""Kör platssteget med historiska, säkerhetskopierade indata (fore_jamn).

Standard är dagens solver. Bara --solver-fore-golv2 väljer arkivets plats.py,
golvmatning.py och lednamn. Flaggan används av det namngivna historiska provet;
dagens determinism- och referensprov kör ingest/plats.py direkt på dagens data.
"""
import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np

H=Path(__file__).resolve().parent;sys.path[:0]=[str(H.parent/'ingest'),str(H)]
if '--solver-fore-golv2' in sys.argv:
    sys.argv.remove('--solver-fore-golv2')
    sys.path.insert(0,str(H/'testdata/solver_fore_golv2'))
import plats

def main():
    load=np.load;read=Path.read_text
    def historical(p):
        p=Path(p);backup=p.parent/'fore_jamn'/p.name
        return backup if backup.exists() else p
    def np_load(p,*args,**kwargs):return load(historical(p),*args,**kwargs)
    def text(p,*args,**kwargs):return read(historical(p),*args,**kwargs)
    with patch('numpy.load',side_effect=np_load),patch.object(Path,'read_text',text):plats.main()

if __name__=='__main__':main()
