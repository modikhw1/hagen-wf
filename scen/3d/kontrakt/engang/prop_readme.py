"""Registrera nya pipelinefiler i README, med säkerhetskopia."""
from prop_filer import andra

def readme(s):
    needle='| `kompilera.py` |'
    i=s.index(needle)
    rows=('| `kalla_prop.py`, `prop_referenser.json` | Lokal komplettering med props: sparad semantik, avlästa källregioner, handledsfästen och märkta yt-/djupantaganden. Se `PROPS.md`. |\n'
          '| `propbank.py`, `propplan.py` | Parametriska former med greppunkt; upplösta hand-/yt-/kamerafästen, regi och propdiagnostik. Blenderdel i `../ingest/prop_blender.py`. |\n')
    s=s[:i]+rows+s[i:]
    i=s.index('| `golvmatning.py`')
    s=s[:i]+'| `kroppmatt.py` | Oberoende silhuett mot YOLO-mask, darr och täckning. |\n'+s[i:]
    i=s.index('| `kontrollera.py` | Validerar exemplen')
    s=s[:i]+'| `kalla_omhasha.py` | Ny källkopia efter lokalt omräknade ingestfiler; originalet bevaras. |\n'+s[i:]
    s=s.replace('`test_flode.py`, `test_rumsmall.py`, `test_regler.py`, `test_text_disk.py` |','`test_flode.py`, `test_rumsmall.py`, `test_regler.py`, `test_text_disk.py`, `test_kroppmatt.py`, `test_props.py` |',1)
    s=s.replace('python -m unittest test_flode test_rumsmall test_regler test_text_disk`','python -m unittest test_flode test_rumsmall test_regler test_text_disk test_kroppmatt test_props`',1)
    return s+'\n## Lokal rekvisita\n\nKör `kalla_prop.py` efter färdig ingest och före `kor_klipp.py --kalla kalla_prop.json`. Originalkällan skrivs aldrig över. Se `PROPS.md` för kommandon, mätning, grepp, regi, kvalitetsmått och begränsningar.\n\nMetodtabellen i `ut/jamn_tabell/tabell.md` har rättats: dolda ben ska uteslutas, inte alla fingerleder. Alla metoder använder nu samma ledurval och medianidentitet som filmen. 2,52/5,17 px för b s1 gällde bara två axelleder; filmens 44 synliga ledpar ger 15,73/48,50 px.\n'
andra('scen/3d/kontrakt/README.md',readme)
andra('scen/3d/ingest/sekvens_stabil.py',lambda s:'\n'.join(' 1. Identiteten (45 formparametrar) låses till medianen. Rådata varierar; det tidigare påståendet att de var lika var fel.' if l.startswith(' 1. Identiteten') else l for l in s.split('\n')))
