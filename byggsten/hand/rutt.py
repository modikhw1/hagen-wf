"""Rutten 0..1 mellan två klipp, v0. Lagd över riktiga klipp i banken.

Regler:
  - Varje hållpunkt är ett klipp som finns, och de två läsarna får inte säga emot varandra om det.
  - Handflatan bevaras: det ändpunkterna har gemensamt får inte röra sig.
  - Styrande fingrar går mot målet, aldrig bort, och högst MAX_PER_HOPP ändras per hopp.
  - Relation och insats (ur läsningen) är styrande fingrar när båda ändpunkterna har en läsning.
    Då syns det när bron byter berättelse.
  - Bland lagliga rutter med samma antal hopp väljs den där hållpunkterna ligger närmast varandra i tema.

Kör: python rutt.py [start-id] [mål-id]      (utan argument: notan -> gelato)
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
NOTAN, GELATO = 'd-dialog-notan', 'kennysgelato2.0-7596403003901381910'

TAL = ['ensemble', 'ord', 'produkt', 'poang_i_ord', 'poang_i_sak']   # styrande, 0..1
KAT = ['plats', 'relation', 'insats']                                  # styrande, kategorier
BEVARADE_TAL = ['vandning']
BEVARADE_KAT = ['strategi', 'tilltal', 'offer']
MAX_PER_HOPP = 2
MAX_SPRANG = 4   # ett språng är ett hopp som ändrar fler än MAX_PER_HOPP fingrar. Tillåts, men kostar och redovisas.
SPRANGKOSTNAD = 3.0
SKILLNAD = 0.3   # minsta avstånd mellan ändpunkterna för att ett finger ska vara en rutt
HOPP = 0.25      # minsta framsteg för att ett finger ska räknas som ändrat
SLACK = 0.2      # hur långt utanför ändpunkternas spann ett värde får ligga
# Meningsfingrar som bara en läsare har läst får inte hålla handflatan hårt.
BEVARA_SLACK = {'poang_i_ord': 0.5, 'poang_i_sak': 0.5, 'vandning': 0.35}
PARTER = {'personal_mot_gast': 'pg', 'gast_mot_personal': 'pg', 'personal_sinsemellan': 'p',
          'chef_och_personal': 'cp', 'gaster_sinsemellan': 'g', 'personal_ensam': 'p', 'annan': ''}


def kat(r, k):
    if k == 'plats':
        return tuple(r['plats'])
    if k in ('strategi', 'tilltal'):
        return r[k]
    return (r.get('lasning') or {}).get(k)


def katframsteg(k, v, s, m):
    """0 = startens värde, 1 = målets, 0.5 = ett mellanläge. None = utanför."""
    if k == 'plats':
        a, b = s[0] in v, m[0] in v
        return 0.5 if a and b else (0.0 if a else (1.0 if b else None))
    if v == s:
        return 0.0
    if v == m:
        return 1.0
    if k == 'relation' and v is not None:
        p = set(PARTER[v])
        if p & set(PARTER[s]) and p & set(PARTER[m]) and p <= set(PARTER[s]) | set(PARTER[m]):
            return 0.5
    return None


def main():
    R = {}
    for line in open(UT / 'rum.jsonl', encoding='utf-8'):
        r = json.loads(line)
        R[r['id']] = r
    sid = sys.argv[1] if len(sys.argv) > 1 else NOTAN
    mid = sys.argv[2] if len(sys.argv) > 2 else GELATO
    S, M = R[sid], R[mid]
    t = np.load(UT / 'tema.npz')
    tix = {str(x): i for i, x in enumerate(t['ids'])}
    V = t['V']
    alla = np.sort((V @ V.T)[np.triu_indices(len(V), 1)])

    def temanarhet(a, b):
        """Andel av alla kortpar som ligger längre ifrån varandra i tema än a och b."""
        return float(np.searchsorted(alla, float(V[tix[a]] @ V[tix[b]])) / len(alla))

    las_bada = bool(S.get('lasning') and M.get('lasning'))
    kats = [k for k in KAT if k == 'plats' or las_bada]
    bev_kat = [k for k in BEVARADE_KAT if k in ('strategi', 'tilltal') or las_bada]

    skiljer = [k for k in TAL if abs(M['f'][k] - S['f'][k]) >= SKILLNAD] + [k for k in kats if kat(S, k) != kat(M, k)]
    haller_tal = [k for k in TAL + BEVARADE_TAL if k not in skiljer]
    haller_kat = [k for k in kats + bev_kat if k not in skiljer and kat(S, k) == kat(M, k)]

    def framsteg(r):
        p = {}
        for k in skiljer:
            if k in TAL:
                v = r['f'][k]
                lo, hi = sorted((S['f'][k], M['f'][k]))
                if v is None or not (lo - SLACK <= v <= hi + SLACK):
                    return None
                p[k] = min(1.0, max(0.0, (v - S['f'][k]) / (M['f'][k] - S['f'][k])))
            else:
                p[k] = katframsteg(k, kat(r, k), kat(S, k), kat(M, k))
                if p[k] is None:
                    return None
        return p

    noder, bort = {}, {'oeniga_lasare': 0, 'bryter_handflatan': 0, 'utanfor': 0, 'saknar_lasning': 0}
    for i, r in R.items():
        if i in (sid, mid) or r.get('handkodad'):
            continue
        if any(k in r['oenig'] for k in TAL):
            bort['oeniga_lasare'] += 1
            continue
        if las_bada and not r.get('lasning'):
            bort['saknar_lasning'] += 1
            continue
        if any(kat(r, k) != kat(S, k) for k in haller_kat):
            bort['bryter_handflatan'] += 1
            continue
        if any(r['f'][k] is None or not (min(S['f'][k], M['f'][k]) - BEVARA_SLACK.get(k, SLACK) <= r['f'][k]
                                         <= max(S['f'][k], M['f'][k]) + BEVARA_SLACK.get(k, SLACK)) for k in haller_tal):
            bort['bryter_handflatan'] += 1
            continue
        p = framsteg(r)
        if p is None:
            bort['utanfor'] += 1
            continue
        noder[i] = {'p': p, 't': sum(p.values()) / len(p), 'kv': r['kvalitet']}
    noder[sid] = {'p': {k: 0.0 for k in skiljer}, 't': 0.0, 'kv': 0}
    noder[mid] = {'p': {k: 1.0 for k in skiljer}, 't': 1.0, 'kv': 0}

    def steg(a, b):
        pa, pb = noder[a]['p'], noder[b]['p']
        if any(pb[k] < pa[k] - 0.05 for k in skiljer):
            return None
        d = [k for k in skiljer if pb[k] - pa[k] >= HOPP]
        return d if 0 < len(d) <= MAX_SPRANG else None

    ordning = sorted(noder, key=lambda i: (noder[i]['t'], i == mid, i != sid))
    kvmax = max(n['kv'] for n in noder.values()) or 1
    kanter = {b: [a for a in ordning[:j] if steg(a, b)] for j, b in enumerate(ordning)}
    nar = {}

    def kostnad(a, b):
        if (a, b) not in nar:
            nar[a, b] = temanarhet(a, b)
        extra = SPRANGKOSTNAD * max(0, len(steg(a, b)) - MAX_PER_HOPP)
        return (1 - nar[a, b]) + 0.25 * (1 - noder[b]['kv'] / kvmax) * (b != mid) + extra

    # bästa rutt per antal hopp: minsta summa av temaavstånd (plus lite för hållpunktens kvalitet)
    MAXH = 12
    bast = {sid: {0: (0.0, None)}}
    for b in ordning:
        if b == sid:
            continue
        d = {}
        for a in kanter[b]:
            for h, (c, _) in bast.get(a, {}).items():
                if h + 1 <= MAXH:
                    k = c + kostnad(a, b)
                    if h + 1 not in d or k < d[h + 1][0]:
                        d[h + 1] = (k, a)
        if d:
            bast[b] = d

    def spar(h):
        v, x = [], mid
        while x is not None:
            v.append(x)
            x, h = bast[x][h][1], h - 1
        return v[::-1]

    ut = {'version': 'rutt/0', 'start': sid, 'mal': mid,
          'skiljer': {k: {'start': S['f'][k] if k in TAL else kat(S, k), 'mal': M['f'][k] if k in TAL else kat(M, k)}
                      for k in skiljer},
          'handflatan': {**{k: [S['f'][k], M['f'][k]] for k in haller_tal}, **{k: kat(S, k) for k in haller_kat}},
          'tema_start_mal': round(temanarhet(sid, mid), 3),
          'noder_mellan': len(noder) - 2, 'bortfall': bort, 'rutter': []}

    def varde(i, k):
        r = R[i]
        return round(r['f'][k], 2) if k in TAL else ('/'.join(kat(r, k)) if k == 'plats' else kat(r, k))

    for h in sorted(bast.get(mid, {})):
        v = spar(h)
        hall = []
        for a, b in zip(v, v[1:]):
            r = R[b]
            hall.append({'t': round(noder[b]['t'], 2), 'id': b, 'sprang': len(steg(a, b)) > MAX_PER_HOPP, 'andrat': {k: [varde(a, k), varde(b, k)] for k in steg(a, b)},
                         'tema_mot_forra': round(nar[a, b], 2), 'url': r['url'], 'karna': r['karna'], 'handling': r['handling'],
                         'mall': r['mall'], 'plats': r['plats'], 'lasning': r.get('lasning'), 'hylla': r['hylla'],
                         'rekonbar': r['rekonbar'], 'kalla': r['kalla'], 'roller': r['roller'], 'beats': r['beats']})
        ut['rutter'].append({'hopp': h, 'sprang': sum(x['sprang'] for x in hall), 'tema_medel': round(float(np.mean([x['tema_mot_forra'] for x in hall])), 3),
                             'tema_samst': min(x['tema_mot_forra'] for x in hall), 'hallpunkter': hall})

    (UT / f'rutt_{sid}__{mid}.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding='utf-8')
    print('klipp mellan ändpunkterna', ut['noder_mellan'], bort)
    print('skiljer', ut['skiljer'])
    print('handflatan', ut['handflatan'], '| tema start-mål', ut['tema_start_mal'])
    for x in ut['rutter']:
        print()
        print(f"== {x['hopp']} hopp, {x['sprang']} språng, temanärhet medel {x['tema_medel']}, sämst {x['tema_samst']}")
        for h in x['hallpunkter']:
            print(f"  {'SPRÅNG ' if h['sprang'] else ''}t={h['t']:.2f} tema {h['tema_mot_forra']:.2f} {h['andrat']}  {h['id']} [{h['hylla']}]")
            print(f"      {h['karna']}")


if __name__ == '__main__':
    main()
