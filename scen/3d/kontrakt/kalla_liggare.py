"""0031: för in en referens till liggaren i källan (semantik.liggare). Befintliga utdata skrivs aldrig över.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_liggare.py <kalla.json> <ny kalla.json> <liggare.json>
Kör liggare_kontroll.py först (kontrollens fil <liggare>.kontroll.json pekas ut om den finns). Revision +1.
"""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
from gemensamt import ladda, skriv
from kalla_generering import filref

kin, kut, lf = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
if kut.exists(): raise SystemExit(f'{kut} finns redan.')
K = ladda(kin); L = ladda(lf); kf = lf.with_suffix('.kontroll.json')
K['semantik']['liggare'] = dict(fil=filref(lf, kut.parent, 'Liggaren: entiteter, händelser med förvillkor och effekt, förlopp, mening och frihetsgrader.'),
                                kontroll=filref(kf, kut.parent, 'Kontrollens utfall.') if kf.exists() else None, skriven_av=L['skriven_av']['modell'])
K['revision'] += 1; skriv(kut, K); print('KALLA', kut, 'revision', K['revision'])
