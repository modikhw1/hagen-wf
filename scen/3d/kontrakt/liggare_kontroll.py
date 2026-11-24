"""0031: kontrollera en liggare mekaniskt, och gör Jev-ytan ur den.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/liggare_kontroll.py <liggare.json> [--yta <ut.json>] [--spridning <frihetsgrad>=<värde>]
1. Schemat (liggare.schema.json, samma validator som källan och regin).
2. Fakta: varje argument är en entitet eller en konstant (hoger, vanster).
3. STRIPS-simulering: starttillståndet, sedan händelserna i tidsordning. Varje förvillkor ska vara sant före händelsen; varje faktum
   som effekten tar bort ska vara sant före. Ett brott är en lucka i liggaren (till exempel skeden i handen utan att någon tog den).
4. Täckning: varje segment i källans handlingsspår täcks av en händelse; förloppens och frihetsgradernas händelser finns; regi-mallarna
   använder operationer som regi-schemat har.
5. Jev-ytan: en rad per laglig ändring (frihetsgrad x värde skilt från nuvärdet; intervall som 0,5 och 2), plus ingen_passar. Varje rad
   bär sin regi (mallen med värdet insatt, eller null när nivån saknas) och sin spridning.
Utfall: <liggare>.kontroll.json bredvid liggaren (och utskrift). Kod 1 om schemat bryts; luckor är diagnos (kod 0, redovisas).
"""
import argparse, copy, json, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
from gemensamt import HIT, ladda, kontrollmodul

KONST = {'hoger', 'vanster', 'kamera'}
FAKTUM = re.compile(r'^([a-z_]+)\(([^()]*)\)$')


def args(f):
    m = FAKTUM.match(f); return (m.group(1), [a.strip() for a in m.group(2).split(',') if a.strip()]) if m else (None, [])


def los_varde(v, x):
    if isinstance(v, str) and '{varde}' in v:
        s = v.replace('{varde}', str(x))
        if re.fullmatch(r'[0-9.+\-* ]+', s): return round(eval(s), 4)   # 8.4084+1 -> 9.4084 (bara aritmetik)
        try: return json.loads(s)
        except ValueError: return s
    if isinstance(v, dict): return {k: los_varde(w, x) for k, w in v.items()}
    if isinstance(v, list): return [los_varde(w, x) for w in v]
    return v


def yta(L):
    rader = []
    for g in L['frihetsgrader']:
        d = g['doman']; varden = d['varden'] if d['typ'] == 'mangd' else [v for v in (d['min'], 2.0 if d['max'] >= 2 else d['max']) if v != g.get('varde_nu')]
        if d['typ'] == 'intervall' and d['max'] >= 2 and d['min'] <= .5: varden = [.5, 2.0] if g.get('varde_nu') not in (.5, 2.0) else varden
        if g['parameter'] == 'hall_s': varden = [1.0, 2.0]
        for v in varden:
            if v == g.get('varde_nu'): continue
            rader.append(dict(id=f'{g["id"]}={v}', text=g['text'].replace('{varde}', str(v)), frihetsgrad=g['id'], varde=v, niva=g['niva'],
                              bar_meningen=g.get('bar_meningen', False), spridning=g['spridning'], regi=los_varde(g['regi'], v) if g['regi'] is not None else None))
    rader.append(dict(id='ingen_passar', text='Ingen av ändringarna ovan är det meningen ber om', frihetsgrad=None, varde=None, niva=None, regi=None))
    return rader


def main():
    a = argparse.ArgumentParser(); a.add_argument('liggare'); a.add_argument('--yta'); a.add_argument('--spridning'); x = a.parse_args()
    lf = Path(x.liggare).resolve(); L = ladda(lf); mod = kontrollmodul(); ut = dict(liggare=lf.name, schemafel=[], faktafel=[], luckor=[], tackning=[], varningar=[])
    S = ladda(HIT / 'liggare.schema.json'); mod.lint(S, 'liggare'); ut['schemafel'] += list(mod.fel_lista); mod.fel_lista.clear()
    ut['schemafel'] += mod.validera(L, S, 'liggare', S)
    if ut['schemafel']:
        print('\n'.join(ut['schemafel'][:20])); (lf.with_suffix('.kontroll.json')).write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8'); sys.exit(1)
    ent = {e['id'] for e in L['entiteter']}
    alla = list(L['starttillstand']) + [f for h in L['handelser'] for f in h['forvillkor'] + h['effekt']['lagg_till'] + h['effekt']['ta_bort']]
    for f in alla:
        p, ar = args(f)
        for q in ar:
            if q not in ent and q not in KONST: ut['faktafel'].append(f'{f}: {q} är ingen entitet')
    for h in L['handelser']:
        for r, e in h['roller'].items():
            if e not in ent and e not in KONST: ut['faktafel'].append(f'{h["id"]}.{r}={e} är ingen entitet')
    st = set(L['starttillstand']); spar = []
    for h in sorted(L['handelser'], key=lambda h: h['rutor'][0]):
        for f in h['forvillkor']:
            if f not in st: ut['luckor'].append(f'{h["id"]} ({h["ram"]}): förvillkoret {f} är inte sant före')
        for f in h['effekt']['ta_bort']:
            if f not in st: ut['luckor'].append(f'{h["id"]} ({h["ram"]}): effekten tar bort {f}, som inte är sant')
        st -= set(h['effekt']['ta_bort']); st |= set(h['effekt']['lagg_till']); spar.append(dict(efter=h['id'], tillstand=sorted(st)))
    ut['sluttillstand'] = sorted(st); ut['tillstand_per_handelse'] = spar
    K = ladda(lf.parent / L['kalla']['fil']); hid = {h['id'] for h in L['handelser']}
    if K['revision'] != L['kalla']['revision']: ut['varningar'].append(f'källans revision {K["revision"]} != liggarens {L["kalla"]["revision"]}')
    tackta = {s for h in L['handelser'] for s in h['segment']}
    for sp in K['semantik'].get('handling', []):
        for g in sp['segment']:
            if g['id'] not in tackta: ut['tackning'].append(f'segmentet {g["id"]} ({sp["scen"]}) täcks inte av någon händelse')
    for f in L['forlopp']:
        for h in f['handelser']:
            if h not in hid: ut['tackning'].append(f'förloppet {f["id"]}: {h} finns inte')
    R = ladda(HIT / 'regi.schema.json'); ops = set(R['$defs']) | {'satt_frihetsgrad'}
    for g in L['frihetsgrader']:
        for h in g['spridning']['handelser']:
            if h not in hid: ut['tackning'].append(f'{g["id"]}.spridning: {h} finns inte')
        for e in g['regi'] or []:
            if e.get('op') not in ops: ut['tackning'].append(f'{g["id"]}.regi: operationen {e.get("op")} finns inte i regi-schemat')
    Y = yta(L); ut['yta_rader'] = len(Y)
    if x.yta: Path(x.yta).write_text(json.dumps(dict(liggare=str(lf), rader=Y), ensure_ascii=False, indent=1), encoding='utf-8')
    if x.spridning:
        fid, v = x.spridning.split('='); r = next(y for y in Y if y['frihetsgrad'] == fid and str(y['varde']) == v)
        ut['spridning'] = dict(andring=r['id'], text=r['text'], niva=r['niva'], **r['spridning'], regi=r['regi'])
    (lf.with_suffix('.kontroll.json')).write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{lf.name}: schema ok; faktafel {len(ut["faktafel"])}, luckor {len(ut["luckor"])}, täckning {len(ut["tackning"])}, varningar {len(ut["varningar"])}; Jev-ytan {len(Y)} rader')
    for k in ('faktafel', 'luckor', 'tackning', 'varningar'):
        for f in ut[k]: print(' ', k, '|', f)
    if ut.get('spridning'): print(json.dumps(ut['spridning'], ensure_ascii=False, indent=1))


if __name__ == '__main__': main()
