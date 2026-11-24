"""0013: gelato genom klipp_kor.prepare/render. Videon heter inte som ingesten (kand-kennysgelato2.0-....mp4), så sökvägarna sätts här."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import klipp_kor as k
I = k.ING / 'ut/kand-kennysgelato-tagningar'; O = k.KON / 'ut/kand-kennysgelato_n06-hand'
VIDEO = k.ROOT / 'scen/klipp/kand-kennysgelato2.0-7596403003901381910.mp4'; D = Path(__file__).resolve().parent / 'deklaration_gelato_hand.json'
PLATS = I / 'plats_n06-hand'
assert VIDEO.exists() and I.exists() and D.exists()
if sys.argv[1] == 'prepare': k.prepare('kand-kennysgelato', I, O, VIDEO, D, 'tom', PLATS)
else: k.render(I, VIDEO, O / 'narvaro')
