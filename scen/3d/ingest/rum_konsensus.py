"""Konsensus över flera modellförslag till deklaration (rum_video.py --variant deklaration): topologin ur majoritet, talen som intervall över körningarna.

    python rum_konsensus.py <ingestmapp> <dekl_k1.json> <dekl_k2.json> ... [--ut <fil>] [--tröskel 0.5]
    -> konsensus.json (deklaration 0.8, allt antaget) och konsensus_rapport.md bredvid

Ett enskilt förslag behöver inte vara giltigt; bara dess topologi läses:
  - per tagning: huvudroll, person_plats och kamera_vid (etiketterna är körningens egna och jämförs bara inom körningen);
  - par av tagningar som delar person, plats respektive kamera, i andel av de körningar som uttalar sig;
  - kluster = tagningar som parvis delar med andel över tröskeln (genomsnittlig koppling, så att en enstaka länk inte kedjar ihop allt).
Geometrin byggs sedan allmänt: platserna längs x i en gemensam ram, kamerorna rakt framför sin plats på läst avstånd, så att tagningar på samma plats
landar på samma punkt (lösaren rättar resten). Avstånd mellan platser, kamerahöjder och möbelmått blir [min, max] över körningarna.
"""
import argparse, itertools, json, math, statistics
from pathlib import Path

from rum_video import las_json


def topologi(D, skott):
    kam = {t: c for t, c in (D.get('kameror') or {}).items() if t in skott and isinstance(c, dict)}
    return {n: {t: c.get(n) for t, c in kam.items() if c.get(n)} for n in ('huvudroll', 'person_plats', 'kamera_vid')}


def samforekomst(etiketter, skott):
    """Andel körningar där två tagningar har samma etikett, bland körningar som har etikett för båda."""
    ut = {}
    for a, b in itertools.combinations(skott, 2):
        roster = [e[a] == e[b] for e in etiketter if a in e and b in e]
        ut[(a, b)] = (sum(roster) / len(roster), len(roster)) if roster else (None, 0)
    return ut


def kluster(par, skott, troskel):
    grupper = [[s] for s in skott]
    def koppling(g, h):
        v = [par[tuple(sorted((a, b), key=skott.index))][0] for a in g for b in h]
        v = [x for x in v if x is not None]
        return sum(v) / len(v) if v else 0.
    while True:
        basta = max(((koppling(g, h), i, j) for (i, g), (j, h) in itertools.combinations(enumerate(grupper), 2)), default=(0, 0, 0))
        if basta[0] <= troskel: return grupper
        _, i, j = basta; grupper[i] += grupper.pop(j)


def platspos(D, pid, last):
    """Körningens läge för en plats: pos_m, annars kamerans läge plus läst avstånd längs kamerans blick."""
    P = D.get('platser') or {}; pl = P.get(pid) or {}
    if isinstance(pl.get('pos_m'), list) and len(pl['pos_m']) >= 2: return [float(v if not isinstance(v, list) else sum(v) / 2) for v in pl['pos_m'][:2]]
    las = pl.get('las') or {}; k = P.get(las.get('kamera_vid')) or {}
    if isinstance(k.get('pos_m'), list) and las.get('tagning') in last:
        b = math.radians(k.get('blick_grader', 90)); d = last[las['tagning']]
        return [k['pos_m'][0] + d * math.cos(b), k['pos_m'][1] + d * math.sin(b)]


def intervall(v, standard):
    v = [float(x) for x in v if isinstance(x, (int, float))]
    return [round(min(v), 2), round(max(v), 2)] if len(v) >= 2 and max(v) > min(v) else ([round(v[0] * .9, 2), round(v[0] * 1.1, 2)] if v else standard)


def tal(v):
    if isinstance(v, list): return [x for x in v if isinstance(x, (int, float))]
    return [v] if isinstance(v, (int, float)) else []


def main():
    a = argparse.ArgumentParser(description=__doc__); a.add_argument('ingest'); a.add_argument('forslag', nargs='+'); a.add_argument('--ut'); a.add_argument('--troskel', type=float, default=.5); a.add_argument('--fokus'); a.add_argument('--grupper', help='grupper.json ur rum_grupper.py: mätta kameragrupper som givna fakta för frågan samma kamera')
    a = a.parse_args(); I = Path(a.ingest); T = las_json(I / 'tagningar.json'); skott = [t['id'] for t in T['tagningar']]
    L = las_json(I / 'brief' / 'lasning.json') or {}
    last = {}
    for t, v in (L.get('tagningar') or {}).items():
        for p in v.get('personspar', []):
            d = (p.get('kropp') or {}).get('kamera_till_hoft_m')
            if d and t not in last: last[t] = d
    F = [las_json(f) for f in a.forslag]; F = [D.get('svar', D) for D in F]; topo = [topologi(D, skott) for D in F]
    rapport = [f'# Konsensus över {len(F)} förslag ({I.name})', '', f'Tröskel för samma kluster: andel > {a.troskel}.', '']
    K, PAR = {}, {}
    fokus = json.loads(Path(a.fokus).read_text(encoding='utf-8')) if a.fokus else {}
    matta = []                                                   # par vars `kamera_vid` är mätt (rum_grupper.py), inte röstat
    if a.grupper:
        matta = [tuple(sorted(p, key=skott.index)) for g in json.loads(Path(a.grupper).read_text(encoding='utf-8'))['delar_plats'] for p in itertools.combinations(g, 2)]
    for n in ('huvudroll', 'person_plats', 'kamera_vid'):
        par = samforekomst([t[n] for t in topo], skott)
        # Fokusfrågor (rum_fokus.py) ersätter den breda röstningen för de par de gäller.
        for nyckel, v in (fokus.get(n) or {}).items():
            x, y = nyckel.split('|')
            if v.get('andel') is not None: par[tuple(sorted((x, y), key=skott.index))] = (v['andel'], v['antal'])
        if n == 'kamera_vid':                                   # mätt går före röstat; Geminis röster används bara för par som mätningen inte säger något om
            for pr in matta: par[pr] = (1.0, 99)
        K[n] = kluster(par, skott, a.troskel); PAR[n] = {f'{x}|{y}': v for (x, y), v in par.items() if v[0] is not None}
        rapport += [f'## {n}', '', ' | '.join('{' + ', '.join(g) + '}' for g in K[n]), '']
        if n == 'kamera_vid' and matta: rapport += ['Mätta par (rum_grupper.py, ger andel 1,0): ' + '; '.join(f'{x}–{y}' for x, y in matta) + '. Övriga par är röstade.', '']
        osakra = [f'{x}–{y}: {v:.2f} av {m}' for (x, y), (v, m) in par.items() if v is not None and .25 <= v <= .75 and m >= 2]
        if osakra: rapport += ['Osäkra par (andel 0,25–0,75): ' + '; '.join(osakra[:20]), '']
    # Roller A, B, C … i den ordning personklustren först syns. Namn ur majoriteten av körningarnas roller.
    personer = sorted(K['huvudroll'], key=lambda g: skott.index(g[0])); roll_av = {}
    for i, g in enumerate(personer):
        for s in g: roll_av[s] = chr(65 + i)
    namn = {}
    for D, t in zip(F, topo):
        for s, r in t['huvudroll'].items():
            # Ett namn räknas bara om körningens roll inte spänner över flera personkluster.
            n = ((D.get('roller') or {}).get(r) or {}).get('namn')
            if n and len({roll_av[x] for x, rr in t['huvudroll'].items() if rr == r}) == 1: namn.setdefault(roll_av[s], []).append(n)
    platser = sorted(K['person_plats'], key=lambda g: skott.index(g[0]))
    # Härledning ur mätningarna: delar två platskluster kamerakluster, och personerna står på nästan samma avstånd (< 0,5 m) och nästan samma
    # läge i bild (rutans mitt < 15 % av bildbredden), står de på samma ställe. Modellen ger topologin; ingestens mätningar avgör geometrin.
    import numpy as np
    def bildmitt(s):
        pers = las_json(I / s / 'personer.json') or {}; meta = las_json(I / s / 'meta.json') or {}
        if not pers or not meta: return None
        b = np.median(np.array(list(next(iter(pers.values())).values())), axis=0); return float((b[0] + b[2]) / 2 / meta['bredd'])
    kam_av = {s: i for i, g in enumerate(K['kamera_vid']) for s in g}; harledda = []
    andrat = True
    while andrat:
        andrat = False
        for g, h in itertools.combinations(platser, 2):
            if not {kam_av[s] for s in g} & {kam_av[s] for s in h}: continue
            dg, dh = [statistics.median([last[s] for s in x if s in last] or [0]) for x in (g, h)]
            mg, mh = [statistics.median([m for m in map(bildmitt, x) if m is not None] or [.5]) for x in (g, h)]
            if abs(dg - dh) < .5 and abs(mg - mh) < .15:
                harledda.append(f"{'+'.join(g)} och {'+'.join(h)}: samma kamerakluster, avstånd {dg:.2f}/{dh:.2f} m, bildmitt {mg:.2f}/{mh:.2f}")
                platser.remove(h); g.extend(h); andrat = True; break
    if harledda: rapport += ['## Härledda sammanslagningar (mätning)', ''] + [f'- {x}' for x in harledda] + ['']
    K['person_plats'] = platser
    # Avstånd i x mellan platsklustren, per körning ur dess egna lägen; intervall över körningarna.
    avst = {i: [] for i in range(1, len(platser))}
    for D, t in zip(F, topo):
        lage = [platspos(D, t['person_plats'].get(g[0]), last) if t['person_plats'].get(g[0]) else None for g in platser]
        for i in avst:
            if lage[i] and lage[0]: avst[i].append(math.dist(lage[0], lage[i]))
    hojd = [x for D in F for c in (D.get('kameror') or {}).values() if isinstance(c, dict) for x in tal(c.get('hojd_m'))]
    hojd += [p['pos_m'][2] for D in F for p in (D.get('platser') or {}).values() if isinstance(p, dict) and isinstance(p.get('pos_m'), list) and len(p['pos_m']) > 2 and str(p.get('roll', '')).startswith('kamera') or False]
    H = intervall([h for h in hojd if .5 < h < 2.5], [1.1, 1.6])
    sitter = {}
    for D, t in zip(F, topo):
        for s, pp in t['person_plats'].items():
            pl = (D.get('platser') or {}).get(pp) or {}; rr = ((D.get('roller') or {}).get(t['huvudroll'].get(s)) or {})
            typ = pl.get('typ') or ('sits' if str(rr.get('lage', '')).startswith('sit') else 'staplats')
            sitter.setdefault(roll_av[s], []).append(typ == 'sits')
    sitt = {r: sum(v) > len(v) / 2 for r, v in sitter.items()}
    namnplats = lambda r: f"{'stol' if sitt.get(r) else 'staplats'}_{r}"
    sitthojd = intervall([x for D in F for p in (D.get('platser') or {}).values() if isinstance(p, dict) and p.get('typ') == 'sits' for x in tal(p.get('sitthojd_m'))], [0.42, 0.5])
    P, kameror, setup_av = {}, {}, {}
    for j, g in enumerate(K['kamera_vid']):
        for s in g: setup_av[s] = f'kamera_{j + 1}'
    x = 0.
    for i, g in enumerate(platser):
        if i: x += statistics.median(avst[i]) if avst[i] else 3.0
        roller = sorted({roll_av[s] for s in g}, key=lambda r: r)
        # Platsens djup: median av klustrets lästa avstånd, så att en enstaka felläsning (b-tilltal S5: 3,7 m) inte flyttar platsen.
        hem = roller[0]; d0 = statistics.median([last[s] for s in g if s in last] or [1.3]); punkt = [round(x, 3), round(d0, 3)]
        P[namnplats(hem)] = dict(typ='sits' if sitt.get(hem) else 'staplats', **({'sitthojd_m': sitthojd} if sitt.get(hem) else {}),
                                 pos_m=[punkt[0], punkt[1], 0.0], roll=hem, roller=roller, blick_grader=270, status='antagen',
                                   kalla=f'konsensus: tagningarna {", ".join(g)} delar plats; läge i x ur {len(avst.get(i, []))} körningar' + (f' ({intervall(avst[i], None)} m)' if i and avst[i] else ''))
        for r in roller[1:]: P[namnplats(r)] = dict(P[namnplats(hem)], typ='sits' if sitt.get(r) else 'staplats', roll=r, roller=[r])
        for s in g:
            kid = setup_av[s]
            if kid not in P:
                d = last.get(s, 1.3); P[kid] = dict(typ='staplats', pos_m=[punkt[0], round(punkt[1] - d, 3), round(sum(H) / 2, 2)], blick_grader=90, roll=None, roller=[],
                                                   status='antagen', kalla=f'konsensus: kameran rakt framför platsen på läst avstånd {d} m (tagning {s})')
            kameror[s] = dict(huvudroll=roll_av[s], spar_id=1, person_plats=namnplats(roll_av[s]), kamera_vid=kid, hojd_m=H, hojd_status='antagen', status='antagen')
    # Möbler: finns massiva bord/diskar i minst hälften av körningarna står en disk framför varje plats (lösaren justerar inom intervallen).
    # Måtten är medianen av körningarnas undre respektive övre gränser. Små icke-massiva föremål listas med vad de står på; formatet bygger dem inte.
    massiva = [[p for p in (D.get('platser') or {}).values() if isinstance(p, dict) and p.get('typ') == 'bord' and p.get('massiv')] for D in F]
    def median_intervall(nyckel, standard):
        lo = [min(tal(p['storlek_m'][nyckel])) for r in massiva for p in r if tal((p.get('storlek_m') or {}).get(nyckel))]
        hi = [max(tal(p['storlek_m'][nyckel])) for r in massiva for p in r if tal((p.get('storlek_m') or {}).get(nyckel))]
        return [round(statistics.median(lo), 2), round(statistics.median(hi), 2)] if lo else standard
    if sum(bool(r) for r in massiva) >= len(F) / 2:
        storlek = dict(langs_x=median_intervall('langs_x', [1.2, 2.4]), langs_y=median_intervall('langs_y', [0.6, 0.9]), hojd=median_intervall('hojd', [0.85, 1.0]))
        for g in platser:
            hem = roll_av[g[0]]
            P[f'disk_{hem}'] = dict(typ='bord', framfor=namnplats(hem), roller=sorted({roll_av[s] for s in g}), massiv=True, storlek_m=storlek, status='antagen',
                                    kalla=f'konsensus: massiva bord i {sum(bool(r) for r in massiva)} av {len(F)} körningar; mått = median av intervallens gränser')
    foremal = {}
    for D in F:
        for pid, p in (D.get('platser') or {}).items():
            if isinstance(p, dict) and p.get('typ') == 'bord' and not p.get('massiv'):
                foremal.setdefault(pid, dict(antal=0, pa=[]))['antal'] += 1; foremal[pid]['pa'].append(p.get('framfor'))
    rollmap = {chr(65 + i): dict(namn=statistics.mode(namn[chr(65 + i)]) if namn.get(chr(65 + i)) else None, tagningar=sorted(g, key=skott.index), lage='sitter' if sitt.get(chr(65 + i)) else 'står', status='antagen')
               for i, g in enumerate(personer)}
    rollmap['kameraman'] = dict(beskrivning='Den som filmar.', tagningar=[], lage='står')
    # Relevans: poster som minst hälften av körningarna nämner.
    rel = {}
    for niva in ('bar_scenen', 'satter_rummet', 'stryks'):
        rakna = {}
        for D in F:
            for s in set(((D.get('relevans') or {}).get(niva) or {}).get('saker', [])): rakna[s] = rakna.get(s, 0) + 1
        rel[niva] = dict(saker=sorted(s for s, n in rakna.items() if n >= len(F) / 2), alla=dict(sorted(rakna.items(), key=lambda kv: -kv[1])))
    osakert = sorted({o for D in F for o in (D.get('osakert') or []) if isinstance(o, str)})
    K_ = dict(schema_version='deklaration/0.8', klipp=f'{I.name}_' + (Path(a.ut).stem if a.ut else 'konsensus'),  # eget namn: rumsmallen dekl_<klipp> får inte skriva över ägarens
              datum='konsensus', version='konsensus',
              golv=dict(hojd_m=[0.0, 0.0], status='antagen', kalla='konsensus'),
              berattat_rum=dict(status='antagen', beskrivning=statistics.mode([(D.get('berattat_rum') or {}).get('beskrivning') or '' for D in F]) or ''),
              kameror=kameror, roller=rollmap, platser=P, narvaro={s: [roll_av[s]] for s in skott}, relevans={k: dict(saker=v['saker']) for k, v in rel.items()},
              osakert=osakert)
    meta = dict(antal=len(F), forslag=[str(f) for f in a.forslag], kluster=K, par=PAR, fokus=bool(fokus), kamera_vid_matta_par=[f'{x}|{y}' for x, y in matta], avstand_mellan_platser={str(i): [round(v, 2) for v in avst[i]] for i in avst},
                relevans_rakning={k: v['alla'] for k, v in rel.items()}, foremal_i_korningarna=foremal)
    ut = Path(a.ut) if a.ut else Path(a.forslag[0]).parent / 'konsensus.json'
    ut.write_text(json.dumps(K_, ensure_ascii=False, indent=2), encoding='utf-8')
    ut.with_name(ut.stem + '_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    rapport += ['## Roller', ''] + [f'- {r}: {v["namn"]}, {", ".join(v["tagningar"])}' for r, v in rollmap.items() if v.get('tagningar')]
    rapport += ['', f'Kamerahöjd: {H} m. Avstånd från första platsen: ' + '; '.join(f'plats {i + 1}: {[round(v, 2) for v in avst[i]]}' for i in avst), '']
    ut.with_name(ut.stem + '_rapport.md').write_text('\n'.join(rapport), encoding='utf-8'); print('\n'.join(rapport)); print('->', ut)


if __name__ == '__main__': main()
