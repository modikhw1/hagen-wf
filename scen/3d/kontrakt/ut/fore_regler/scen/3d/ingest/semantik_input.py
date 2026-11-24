"""Klippets eget semantiska underlag, direkt bundet till uppmätta spår-id."""
import json
from pathlib import Path


def las(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def hitta(mapp, explicit=None):
    if explicit: return Path(explicit).resolve()
    p = Path(mapp) / 'semantik.json'
    if p.exists(): return p.resolve()
    # Ett äldre klippregister får bara välja fil via exakt ingestmapp.
    root = Path(__file__).resolve().parent.parent / 'kontrakt/semantik'
    import sys
    if str(root) not in sys.path: sys.path.insert(0, str(root))
    from sem_gemensamt import KLIPP
    for namn, v in KLIPP.items():
        p = root / 'ut' / namn / 'semantik.json'
        if Path(mapp).name == v['ingest'] and p.exists(): return p.resolve()
    return None


class Semantik:
    def __init__(self, fil):
        self.fil = Path(fil).resolve(); self.sem = las(fil); self.data = self.sem['data']
        personer = sorted(self.data['personer'], key=lambda p: (min([int(s['tagning'][1:]) for s in p['spar']] or [10**6]), p['id']))
        self.namn = {p['id']: chr(65+i) for i, p in enumerate(personer)}
        self.personer = {self.namn[p['id']]: p for p in personer}
        self.spar = {(s['tagning'], str(s['spar_id'])): (self.namn[p['id']], self.ursprung(s['konfidens'])) for p in personer for s in p['spar']}
        self.ej = {(s['tagning'], str(s['spar_id'])): s for s in self.data['ej_personer']}

    def ursprung(self, konfidens):
        return dict(typ='modellbedomd', modell=self.sem['ursprung']['modell'],
                    prompt_version=self.sem['ursprung']['prompt_version'], konfidens=konfidens)

    def filtrera(self, sid, personer):
        """Behåll okända spår för granskning; bara uttryckliga avvisningar slängs.

        Dubbletter förenas ruta för ruta. Längsta spåret vinner överlapp,
        övriga fyller luckor; inga två GPU-jobb för samma person/ruta.
        """
        grupper = {}; beslut = []; resultat = {}; roller = {}
        for pid, rutor in personer.items():
            key = (sid, str(pid)); e = self.ej.get(key); match = self.spar.get(key)
            if e:
                beslut.append(dict(spar_id=pid, beslut='utelämnad', orsak=e['skal'], ursprung=self.ursprung(e['konfidens'])))
                continue
            if not match:
                raise ValueError(f'{sid}:{pid} saknas i semantikens identiteter och ej_personer; granska före betald kropp.')
            grupper.setdefault(match[0], []).append((str(pid), rutor))
        for roll, grupp in grupper.items():
            grupp.sort(key=lambda x: (-len(x[1]), x[0])); pid = grupp[0][0]; rutor = {}
            for other, frames in reversed(grupp): rutor.update(frames)
            resultat[pid] = rutor; roller[pid] = roll
            beslut.append(dict(spar_id=pid, person=roll, sammanslagna=[x[0] for x in grupp], beslut='berättelseperson',
                               orsak='Längsta spåret vinner överlapp; övriga fyller luckor.', ursprung=self.spar[(sid, pid)][1]))
        return resultat, roller, beslut

    def placering(self, sid, roll):
        p = next((p for p in self.data['placeringar'] if self.namn[p['person']] == roll and sid in p['tagningar']), None)
        return dict(p, ursprung=self.ursprung(p['konfidens'])) if p else None

    def ordtider(self):
        p = self.fil.with_name('ordtider.json')
        if not p.exists(): return dict(lines=[], model='saknas', language=self.data['klipp'].get('sprak', 'sv'), match_ratio=None)
        ot = las(p); lines = []
        for l in ot['lines']:
            if not l.get('stodd', True): continue
            l = dict(l, i=len(lines), speaker=self.namn.get(l['speaker']),
                     ursprung=self.ursprung(next((r['konfidens'] for r in self.data['repliker'] if r['id'] == l['id']), 'osaker')))
            lines.append(l)
        return dict(ot, lines=lines)
