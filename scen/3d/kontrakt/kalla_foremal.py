"""0016: för över det kedjan redan vet till källans semantiska lager, så att Jev och regin kan välja det.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_foremal.py <kalla.json> <ny kalla.json> [--plan plan.json]

1. Föremål som deklarationen bygger (på möbel eller i hand) blir namngivna props i semantik.props med deklaration{former, scener, pa, i_hand}.
   Härleds ur planens plats[].deklarerat.foremal, formerna <stöd>:pa:<föremål> i plan.objekt och plan.handforemal.
2. Scengrupper: intilliggande scener med samma enda roll i bild (scenernas personer och bindningar, som kommer ur deklarationen).
Utan --plan kompileras källan med tom regi (snabb). Den nya källan skrivs bredvid den gamla så att relativa sökvägar gäller; revision ökas.
Föremål som redan finns som prop (samma id) och källor utan deklarerade föremål lämnas orörda.
"""
import argparse
import copy
import json
import tempfile
from pathlib import Path

from gemensamt import ladda, skriv

SIDA = {'v': 'vanster', 'h': 'hoger'}


def props_ur_plan(plan):
    ut = {s['id']: s['ut'] for s in (plan.get('scener') or plan['matkamera'].get('scener', []))}
    def scener_for(a, b): return [sid for sid, (sa, sb) in ut.items() if a < sb and sa < b]
    out = []
    for pl in plan.get('plats') or []:
        for fid, spec in ((pl.get('deklarerat') or {}).get('foremal') or {}).items():
            former = [o for o in plan['objekt'] + (plan.get('props') or []) if str(o.get('id', '')).endswith(':pa:' + fid)]
            hand = [h for h in plan.get('handforemal') or [] if h.get('foremal') == fid]
            scener = set()
            for o in former: scener.update(scener_for(*(o.get('synlig_ut') or [0, len(plan['kallrutor'])])))
            scener.update(h['scen'] for h in hand)
            if not former and not hand: continue
            ordn = list(ut)
            storlek = max([o['matt_m'] for o in former] + [h['matt_m'] for h in hand], key=lambda m: m[0] * m[1] * m[2], default=None)
            pa = spec.get('pa') if any(o['id'].startswith(str(spec.get('pa')) + ':pa:') for o in former) else (former[0]['id'].split(':pa:')[0] if former else None)
            forsta = hand[0] if hand else None
            out.append(dict(id=fid, typ=fid, etikett=fid, agare=forsta['person'] if forsta and len({h['person'] for h in hand})==1 else None, stod=pa,
                            faste=dict(person=forsta['person'], led=forsta['ben'], hand=SIDA.get(forsta['sida'])) if forsta else None,
                            rum_ref=None, kalla='deklaration (kalla_foremal.py)', plats_id=None,
                            deklaration=dict(foremal=fid, former=sorted({o['id'] for o in former} | {h['id'] for h in hand}),
                                             scener=sorted(scener, key=ordn.index), pa=pa,
                                             i_hand=[dict(scen=h['scen'], person=h['person'], sida=h['sida']) for h in hand],
                                             storlek_m=[round(float(v), 4) for v in storlek] if storlek else None)))
    return out


def grupper(sem):
    runs = []
    for s in sem['scener']:
        roll = s['personer'][0] if len(s['personer']) == 1 else None
        if roll and runs and runs[-1]['roll'] == roll: runs[-1]['scener'].append(s['id'])
        else: runs.append(dict(roll=roll, scener=[s['id']]))
    out, n = [], {}
    for r in runs:
        if r['roll'] is None or len(r['scener']) < 2: continue
        n[r['roll']] = n.get(r['roll'], 0) + 1
        out.append(dict(id=f'grupp_{r["roll"]}' + ('' if n[r['roll']] == 1 else f'_{n[r["roll"]]}'), etikett=None, roll=r['roll'], scener=r['scener'],
                        kalla='intilliggande scener med samma enda roll i bild (semantik.scener.personer ur deklarationen)'))
    return out


def bygg(kalla, plan=None):
    K = copy.deepcopy(ladda(kalla))
    if plan is None:
        from kompilera import kompilera
        regi = dict(schema_version='regi/1', kalla=dict(klipp_id=K['klipp']['id'], sha256=K['klipp']['sha256'], revision=K['revision']), edits=[],
                    utdata=dict(fps_taljare=K['tidsbas']['fps_taljare'], fps_namnare=K['tidsbas']['fps_namnare'], bredd=K['klipp']['video']['bredd'],
                                hojd=K['klipp']['video']['hojd'], stil_ref=None, ljudpolicy='original', render_backend='blender_mhr'),
                    ramar=dict(bevara_beats=[], bevara_klippoffset_s=None, tillat_retiming=False, max_talfaktor=1.15))
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'regi.json'; skriv(f, regi); plan = kompilera(kalla, f, snabb=True)
    sem = K['semantik']; finns = {p['id'] for p in sem['props']}
    nya = [p for p in props_ur_plan(plan) if p['id'] not in finns]
    sem['props'] += nya
    g = grupper(sem)
    if g: sem['scengrupper'] = g
    if nya or g:
        K['revision'] += 1
        K['matning']['kvalitet'].append(dict(post='semantik.props', status='antagen',
            metod=f'0016: {len(nya)} föremål ur deklarationen ({", ".join(p["id"] for p in nya)}); formerna och scenerna ur planens lyft (foremallyft, handforemal).',
            osakerhet=None, saknas_steg=None, kalla_fil=None))
        if g: K['matning']['kvalitet'].append(dict(post='semantik.scengrupper', status='antagen',
            metod=f'0016: {len(g)} grupper, intilliggande scener med samma enda roll i bild.', osakerhet=None, saknas_steg=None, kalla_fil=None))
    return K, nya, g


def main():
    a = argparse.ArgumentParser(description=__doc__); a.add_argument('kalla'); a.add_argument('ut'); a.add_argument('--plan'); x = a.parse_args()
    kalla, ut = Path(x.kalla).resolve(), Path(x.ut).resolve()
    if ut.parent != kalla.parent: raise ValueError('Den nya källan ska ligga bredvid den gamla (relativa sökvägar).')
    if ut.exists(): raise FileExistsError(ut)
    K, nya, g = bygg(kalla, ladda(x.plan) if x.plan else None)
    skriv(ut, K); print(ut, 'props +', [p['id'] for p in nya], 'grupper', [(y['id'], y['scener']) for y in g], 'revision', K['revision'])


if __name__ == '__main__': main()
