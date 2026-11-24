"""0013: avståndet i slutkameran mellan föremålets projicerade mitt (Blenders världsläge i kontrollrutorna, handforemal_rapport.json) och
maskens tyngdpunkt i samma ruta, i promille av bildhöjden. Också Pythons förutsagda läge (handledens ram · förskjutning) mot Blenders.
Körs från scen/3d/kontrakt:  python ut/fore_hand_0013/matt_hand.py <variantmapp> ..."""
import json, sys
from pathlib import Path
import numpy as np
sys.path[:0] = ['.', '../ingest']
sys.stdout.reconfigure(encoding='utf-8')
import handforemal as hf
alla = {}
for v in sys.argv[1:]:
    d = Path('ut') / v / 'narvaro'; plan = json.loads((d / 'plan.json').read_text(encoding='utf-8'))
    rap = {(r['id'], r['scen']): r for r in json.loads((d / 'handforemal_rapport.json').read_text(encoding='utf-8'))}
    h = float(plan['utdata']['hojd']); res = []
    for fp in plan['kvalitet'].get('handforemal') or []:
        for t in fp['tagningar']:
            if not t.get('id'): continue
            r = rap.get((t['id'], t['scen'])) or {}; post = next(x for x in plan['handforemal'] if x['id'] == t['id'] and x['scen'] == t['scen'])
            scen = next(s for s in plan['scener'] if s['id'] == t['scen']); k = hf._Kropp(scen, next(p for p in scen['personer'] if p['id'] == post['person']))
            rader = []
            for kp in r.get('kontroll', []):
                pr = next(p for p in t['prov'] if p['ruta'] == kp['ruta'])
                uv, _ = hf.projicera(plan, kp['ut'], kp['varld']); fel = float(np.linalg.norm(uv - np.array(pr['tyngdpunkt_px']))) / h * 1000
                R, p = k.ram(kp['ruta'], post['sida']); py = R @ np.array(post['offset_m']) + p
                rader.append(dict(ruta=kp['ruta'], promille=round(fel), python_mot_blender_m=round(float(np.linalg.norm(py - np.array(kp['varld']))), 4)))
            res.append(dict(foremal=fp['foremal'], tagning=t['tagning'], hand=f"{post['person']}:{post['sida']}", offset_status=post['offset_status'],
                            matt_m=post['matt_m'], utan_bildstod=t.get('utan_bildstod'), rutor=rader, status=r.get('status', 'byggd' if r else 'saknas i rapporten')))
    alla[v] = res
    print('==', v)
    for x in res: print(' ', x['tagning'], x['hand'], x['offset_status'], x['matt_m'], [(q['ruta'], q['promille'], q['python_mot_blender_m']) for q in x['rutor']], x['utan_bildstod'], x['status'])
json.dump(alla, open('ut/fore_hand_0013/matt_hand.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
