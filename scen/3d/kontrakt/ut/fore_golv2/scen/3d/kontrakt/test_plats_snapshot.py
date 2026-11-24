"""Återskapa platsreferensen med dess historiska, säkerhetskopierade indata.

Anropas av determinismprovet. Filnamn i utdata är fortfarande de ursprungliga;
bara läsning av de filer som jämn-passet skrev om styrs till fore_jamn.
"""
import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np

H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'ingest'))
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
