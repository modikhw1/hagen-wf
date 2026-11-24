"""0030: en tagnings parametrar för den generativa nedbrytningen. Skripten läser dem här i stället för att ha gelato S1 inskrivet.

Konfig: miljövariabeln GENNED_TAGNING pekar på en JSON (kedja/<klipp>/<tagning>.json, se kedja.py). Utan den gäller gelato S1, med
exakt de värden som skripten hade inskrivna före 0030, så gamla körningar ger samma utfall.
Fält:
  klipp, tagning, scen        ingestmappen (ingest/ut/<klipp>/<tagning>) och källans scen-id
  offs                        ingestruta = klippruta + offs (gelato S1: 7; tagningens första lästa ruta)
  kalla_rutor                 rutor i den kamerafria källan genereringen följer (gelato S1: 148)
  plan                        kedjans plan som genereringen läggs in i (kontrakt/ut/<variant>/narvaro/plan.json)
  handling                    handlingsspårets fil (relativ till gennedbrytning/)
  avbildning                  den kamerafria avbildningen per ruta (relativ till gennedbrytning/)
  ankare                      fotter (står) eller sate (sitter): vad som står still i världen vid roträttningen
  fot_rutor                   rutorna där ankarets läge mäts (planrutor)
  utzoom                      kamerafria källans utzoomning (guacamole 0,62), null = ingen
  vandpunkter                 segment-id för tidspassningens kontrollpunkter: lag (handen lägst), fram (armen längst fram); null = inga
  kamera                      r_kamera.py-flaggor (modell, hojd, lins0, ymin, vrid_vikt)
  scen                        s_scen.py-flaggor (trag_max, glas, bak_lag)
  handforemal                 id, ben, ljus (r_sked.py), null = inget föremål i handen
"""
import json, os
from pathlib import Path

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'; KON = HIT.parent / 'kontrakt'
STANDARD = dict(klipp='kand-kennysgelato-tagningar', tagning='S1', scen='s1', offs=7, kalla_rutor=148,
                plan='kontrakt/ut/kand-kennysgelato_n06-hand/narvaro/plan.json', handling='handling/S1/handling.json',
                avbildning='kamerafri/avbildning.json', ankare='fotter', fot_rutor=[7, 22], utzoom=None,
                vandpunkter=dict(lag='h3', fram='h8'),
                kamera=dict(modell='dolly_zoom', hojd='1.3', lins0=64, ymin=-0.8, vrid_vikt=1),
                scen_flaggor=dict(trag_max=.8, glas='disk_A:fram', bak_lag=True),
                handforemal=dict(id='A:hand:provsked', ben='r_wrist', ljus=228))


def konfig():
    k = dict(STANDARD); f = os.environ.get('GENNED_TAGNING')
    if f: k.update(json.loads(Path(f).read_text(encoding='utf-8')))
    return k


T = konfig()
TAG = ING / 'ut' / T['klipp'] / T['tagning']          # ingestens tagningsmapp
DAG = TAG / 'kropp/1'                                   # dagens läsning av originalet, ingestrutor
OFFS = int(T['offs'])
PLAN = HIT.parent / T['plan']                          # scen/3d/<plan>
PLAN_DIR = PLAN.parent
HANDLING = HIT / T['handling']
AVBILDNING = HIT / T['avbildning']
