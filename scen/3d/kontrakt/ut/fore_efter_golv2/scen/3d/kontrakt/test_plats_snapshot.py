"""Återskapa platsreferensen med dess historiska, säkerhetskopierade indata.

Anropas av determinismprovet. Filnamn i utdata är fortfarande de ursprungliga;
bara läsning av de filer som jämn-passet skrev om styrs till fore_jamn.

GOLV2 (10 nov) ändrade platssteget och golvbeslutet med avsikt. Referensen är
framställd av arkivets solver, så den körs här med de oförändrade modulerna
från före GOLV2 i testdata/solver_fore_golv2/ (plats.py, golvmatning.py,
mhr_ledernamn.json). Övriga moduler är dagens.
"""
import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np

H=Path(__file__).resolve().parent;sys.path[:0]=[str(H/'testdata/solver_fore_golv2'),str(H.parent/'ingest'),str(H)]
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
