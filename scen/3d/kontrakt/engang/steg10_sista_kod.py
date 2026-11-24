"""Sista små inkopplingar före den fulla regressionskörningen."""
from steg10_filer import andra
from steg10_koppla import ersatt

andra('scen/3d/kontrakt/kalla_handelser.py', lambda s: ersatt(s,
    "        trackfile = folder / 'personer_matning.json'\n        tracks =",
    "        trackfile = folder / 'personer_matning.json'\n        if not trackfile.exists(): trackfile = folder / 'personer.json'\n        tracks ="))
andra('scen/3d/kontrakt/kalla_handelser.py', lambda s: s.replace('detektion i personer_matning.json.', 'detektion i personer_matning.json eller äldre personer.json.'))

def ingest(s):
    marker = "    d[steg] = dict(sek=round(sek, 1), **x); p.write_text(json.dumps(d, indent=1)); print(f'[{steg}] {sek:.1f} s', x, flush=True)"
    return ersatt(s, marker, marker + "\n    if steg in ('sekvens', 'varld', 'golv', 'kontakt', 'jamn_omkorning'):\n        from kallstatus import varna\n        varna(ut)")
andra('scen/3d/ingest/ingest_klipp.py', ingest)

# Bara nuvarande kodens semantiska kommentarer rättas; inga toleranser ändras.
andra('scen/3d/kontrakt/test_flode.py', lambda s: s.replace('platsl?sning','platslösning').replace('Beh?ll','Behåll').replace('g?rs','görs'))

def prova_varning(s):
    marker = '    def test_eventunderlag_far_inte_hashas_om_tyst(self):'
    return ersatt(s, marker, '''    def test_ingest_varnar_med_refreshkommando(self):
        import contextlib, io, sys
        sys.path.insert(0,str(HIT.parent/'ingest'))
        from kallstatus import varna
        raw=self.d/'matning.json'; raw.write_bytes(b'fore')
        self.k['matning']['handelsekallor']=[dict(sokvag=str(raw),sha256=hashlib.sha256(b'fore').hexdigest(),format='json',roll='Prov')]
        skriv(self.d/'kalla.json',self.k);raw.write_bytes(b'efter')
        output=io.StringIO()
        with contextlib.redirect_stderr(output): result=varna(self.d,[self.d/'kalla.json'])
        self.assertEqual(result,[str(self.d/'kalla.json')])
        self.assertIn('kalla_omhasha.py',output.getvalue());self.assertIn('kalla_handelser.py',output.getvalue())

''' + marker)
andra('scen/3d/kontrakt/test_handelser.py', prova_varning)
