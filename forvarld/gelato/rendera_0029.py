"""0029: bilder och korta filmer för meningarna som gick hela vägen (ut = med mening i tillståndet, ut_utan = utan). Kör: scen/.venv/Scripts/python.exe forvarld/gelato/rendera_0029.py"""
import sys, time
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bild
D = Path(__file__).resolve().parent; U, V = D / 'ut', D / 'ut_utan'; t0 = time.time()
def logg(x): print(f'{time.time() - t0:6.0f} s  {x}', flush=True)
bild.ark(U, 'm1', [(40, 31, 'h3 före; efter: mitt i övergången h2 -> h4'), (100, 68, 'h6, samma källruta')], 'Hoppa över när hon skopar (ta_bort_handling h3)'); logg('m1')
bild.ark(U, 'm5', [(50, 50, 'h3'), (125, 125, 'h8')], 'Ta bort disken (ta_bort_prop disk_A; varning: disken ramar meningen)'); logg('m5')
bild.ark(U, 'm9', [(130, 119, 'h8 före; efter: övergång h7 -> h9')], 'Låt kunden ta emot med andra handen (Jev: ta_bort_handling h8, fel tolkning)'); logg('m9')
bild.ark(V, 'm4', [(100, 100, 'h6'), (130, 130, 'h8')], 'Byt glassen mot en kaka (byt_prop provsked -> kaka, platshållare)'); logg('m4')
bild.film(U, 'm2', 20, 110, 'Gör skopandet långsammare (tempo_handling h3, faktor 2)'); logg('m2')
bild.film(U, 'm3', 110, 200, 'Låt henne räcka fram två smakprov (upprepa_handling h8, 2 gånger)'); logg('m3')
bild.film(U, 'm6', 156, 252, 'Stabilisera kameran (renderkamera stativ i s2)'); logg('m6')
bild.film(U, 'm7', 222, 282, 'Gör klippet en sekund längre i slutet (hall_sista s2 +1,0 s)'); logg('m7')
