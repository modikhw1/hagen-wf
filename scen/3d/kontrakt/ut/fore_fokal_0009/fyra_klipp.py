"""Uppdrag 0009: vilket fokalvärde varje tagning i de fyra klippen skulle få med fokal_klipp.bestam, på minneskopia (inget skrivs utom tabellen).
Körs (från scen/): .venv/Scripts/python.exe -B 3d/kontrakt/ut/fore_fokal_0009/fyra_klipp.py"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ING = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'ingest'))
sys.path.insert(0, ING)
import fokal_klipp as fk
KLIPP = {'b-tilltal-ravara': (0.09, 0.47, 0.92, 0.75), 'e-dialog-guacamole': None, 'notan': None, 'kand-kennysgelato': None}
ut = {}; rader = []
for k, overlay in KLIPP.items():
    I = f'{ING}/ut/{k}-tagningar'
    if not os.path.isdir(I): rader.append(f'## {k}: ingestmapp saknas'); continue
    tag = fk.skatta_klipp(I, overlay); dim = max(max(int(t.get('bredd') or 0), int(t.get('hojd') or 0)) for t in tag.values())
    klipp, per = fk.bestam({t: dict(colmap=d['colmap'], colmap_godkand=d['colmap_godkand'], vp=d['vp']) for t, d in tag.items()}, dim)
    ut[k] = dict(dim=dim, klipp=klipp, tagningar={t: dict(per[t], idag_fokal_px=tag[t]['idag_fokal_px'], vp_antal=len(tag[t]['vp'])) for t in tag})
    rader.append(f"## {k} (dim {dim} px) klippvärde: {klipp.get('fokal_px')} px, spridning {klipp.get('spridning_px')}, {klipp['antal_kandidater']} kandidater ur {klipp['antal_tagningar']} tagningar")
    rader.append('| tagn | idag px | ny px | status | källa | COLMAP rå | VP-kandidater | läs om? |\n|---|---|---|---|---|---|---|---|')
    for t, d in ut[k]['tagningar'].items():
        idag = d['idag_fokal_px']; omlas = bool(idag and abs(d['fokal_px'] - idag) / idag > .10)
        d['laes_om'] = omlas
        rader.append(f"| {t} | {idag if idag is None else round(idag)} | {round(d['fokal_px'])} | {d['fokal_status']} | {d['fokal_kalla']} | {d['colmap_px'] and round(d['colmap_px'])} | {d['vp_antal']} | {'JA' if omlas else 'nej'} |")
    rader.append('')
json.dump(ut, open(f'{HERE}/fyra_klipp.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
open(f'{HERE}/fyra_klipp.md', 'w', encoding='utf8').write('\n'.join(rader) + '\n'); print('\n'.join(rader))
