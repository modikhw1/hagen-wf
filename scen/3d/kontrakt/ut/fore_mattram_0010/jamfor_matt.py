"""Uppdrag 0010: b-tilltal nya vägen (n06-matt: segmenterarens rutor + kontroller) mot gamla vägen (n06-fler2: Geminis rutor, samma kod efter 0007/0009).
Körs (från scen/): .venv/Scripts/python.exe -B 3d/kontrakt/ut/fore_mattram_0010/jamfor_matt.py   Läser planerna, skriver jamfor_matt.json och stdout."""
import json, os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); UT = os.path.dirname(HERE); KON = os.path.dirname(UT)
sys.path.insert(0, KON); sys.path.insert(1, os.path.join(os.path.dirname(KON), 'ingest'))
import boxpassning as bp, mobellyft as ml, foremallyft as fl  # noqa: E402
H = 1024.
ut = {}


def plan(v): return json.load(open(f'{UT}/b-tilltal-ravara_n06-{v}/narvaro/plan.json', encoding='utf8'))


def forsta(p): return {o['id']: o for o in reversed(p['objekt'])}                         # första posten per id vinner inte nödvändigtvis; geometrin är densamma


def spridning(d, tagn):
    q = [np.array(d[t]) for t in tagn if isinstance(d.get(t), list)]
    return round(max((float(np.hypot(*(a - b))) for i, a in enumerate(q) for b in q[i + 1:]), default=float('nan')), 2), len(q)


for v in ('fler2', 'matt'):
    p = plan(v); obj = forsta(p); pl = p['plats'][0]; res = dict(variant=v)
    dc = obj['disk_C']; vag = obj.get('disk_C:pa:vag'); res['disk_C_pos'] = [round(x, 3) for x in dc['pos_m'][:2]]; res['vag_pos'] = [round(x, 3) for x in vag['pos_m'][:2]] if vag else None
    ml_ = {r['mobel']: r for r in p['kvalitet'].get('mobel_lyft', [])}; d = ml_.get('disk_C', {})
    res['mobel_lyft'] = dict(status=d.get('status'), orsak=d.get('orsak'), ordningsniva=d.get('ordningsniva'), granskonflikt=d.get('granskonflikt'), uteslutna=d.get('uteslutna_boxar'),
                             hoppade=d.get('hoppade_boxar'), antal_boxar=d.get('antal_boxar'), i_passning=d.get('antal_boxar_i_passning'),
                             lag_kameramarginal=min([k['uppnadd_kameramarginal_m'] for k in d.get('klamningar', [])] or [None]) if d.get('klamningar') else None)
    fo = {r['foremal']: r for r in p['kvalitet'].get('foremal_lyft', [])}
    res['foremal_lyft'] = {k: dict(status=r.get('status'), orsak=r.get('orsak'), uteslutna=r.get('uteslutna_boxar'), stod_ersatt=r.get('stod_ersatt')) for k, r in fo.items()}
    # lyft per tagning ur variantens egna rutor (som i 0004), spridning mellan tagningar
    bil = {'disk_C': pl['deklarerat']['mobler']['disk_C'].get('bilder') or [], 'vag': pl['deklarerat']['foremal'].get('vag', {}).get('bilder') or []}
    topp = dc['pos_m'][2] + dc['matt_m'][2] / 2.; lyft = {'disk_C': {}, 'vag': {}}
    for b in bil['disk_C']:
        try: lyft['disk_C'][b['tagning']] = ml._enbildslage(p, pl, {}, dc, b).tolist()
        except Exception as ex: lyft['disk_C'][b['tagning']] = str(ex)
    for b in bil['vag']:
        try: lyft['vag'][b['tagning']] = [float(x) for x in fl._traff(p, b, topp)[0]]
        except Exception as ex: lyft['vag'][b['tagning']] = str(ex)
    res['rutor'] = {k: {b['tagning']: b['box_2d'] for b in v_} for k, v_ in bil.items()}
    res['spridning_disk_C_S6_S9_S11'] = spridning(lyft['disk_C'], ('S6', 'S7', 'S8', 'S9', 'S11')); res['spridning_vag_S8_S11'] = spridning(lyft['vag'], ('S8', 'S9', 'S10', 'S11'))
    res['lyft'] = {k: {t: ([round(x, 2) for x in q] if isinstance(q, list) else q) for t, q in d_.items()} for k, d_ in lyft.items()}
    # projektion i slutkameran: diskens övre kant och vågens kanter i s6, s10, s11 (promille av bildhöjden) mot referensrutor ur segmenteraren
    SEG = json.load(open(f'{UT}/fore_mattram_0010/deklaration_n06_matt.json', encoding='utf8'))
    ref = {('disk_C', 'S6'): SEG['platser']['disk_C']['bilder'], ('disk_C', 'S11'): SEG['platser']['disk_C']['bilder'], ('vag', 'S10'): SEG['foremal']['vag']['bilder']}
    pr = {}
    for (el, t), lista in ref.items():
        box = next((b['box_2d'] for b in lista if b['tagning'] == t), None)
        if not box: pr[f'{el} {t}'] = 'ingen referensruta'; continue
        try:
            bd, key, _ = bp.bilddata(p, dict(tagning=t, box_2d=box)); o = dc if el == 'disk_C' else vag
            k = bp.projicerade_kanter(p, o, o['pos_m'][:2], key)
            pr[f'{el} {t}'] = dict(topp_promille=round((k['topp'] - box[0] / 1000 * H) / H * 1000), botten_promille=round((k['botten'] - box[2] / 1000 * H) / H * 1000) if box[2] < 990 else 'beskuren')
        except ValueError as ex: pr[f'{el} {t}'] = str(ex)
    res['projektion_mot_segmenterarens_ruta'] = pr
    ut[v] = res
json.dump(ut, open(f'{HERE}/jamfor_matt.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1, default=float)
for v, r in ut.items(): print(json.dumps(r, ensure_ascii=False)[:1800]); print()
