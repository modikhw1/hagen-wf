"""0029: mening i källan. Handlingsspåret per tagning och relevanslistan per klipp förs in som semantik.handling och semantik.relevans.

  scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_mening.py <kalla.json> <ny kalla.json> <spec.json>
spec: {"handling": [{"scen": "s1", "fil": <handling.json>, "rattelser": {<segment-id>: {<fält>: {"varde": .., "kalla": .., "skal": ..}}}}],
       "relevans": {"fil": <relevans.json>, "tillagg": [<post>], "rattelser": {<post-id>: {<fält>: ..}}}}
Allmänt: handling.json (gennedbrytning/l_handling.py) och relevans.json (gennedbrytning/relevans/relevans_steg.py) har samma form för
varje klipp. Segmentens rutor blir källrutor, halvöppna [a, b) som allt annat i källan; tid i sekunder på källklockan. Varje fält bär
sin källa (matt, last, antagen); en rättelse märks rattad med skäl. Inget fält uppfinns: saknas ett värde är det null.
Befintliga utdata skrivs aldrig över.
"""
import copy, json, sys
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode = True
from gemensamt import ladda, skriv

FALT = ['hallning', 'hand_mot_mobel', 'handens_rorelse', 'kundens_hand_syns', 'kamera', 'handling', 'kroppsdel', 'foremal', 'mal', 'kontakt', 'beskrivning']


def segment(s, fps, ratt):
    a, b = s['rutor_plan'][0], s['rutor_plan'][1] + 1
    ut = dict(id=s['id'], vem=s.get('vem'), rutor=[a, b], tid_s=[round(float(a / fps), 4), round(float(b / fps), 4)],
              lutning_grader=s.get('lutning_grader'))
    for f in FALT:
        v = copy.deepcopy(s.get(f))
        if isinstance(v, dict): v = {k: v[k] for k in ('varde', 'kalla', 'mobel', 'sakerhet') if k in v}
        elif v is not None: v = dict(varde=v, kalla='okand')
        ut[f] = v
    for f, ny in (ratt or {}).get(s['id'], {}).items():
        ut[f] = dict(varde=ny['varde'], kalla=ny.get('kalla', 'rattad'), rattad=dict(fore=(ut.get(f) or {}).get('varde'), skal=ny['skal']))
    return ut


def main():
    kin, kut, specf = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    if kut.exists(): raise SystemExit(f'{kut} finns redan; befintliga utdata skrivs aldrig över.')
    K = ladda(kin); sp = ladda(specf); bas = specf.parent; fps = Fraction(K['tidsbas']['fps_taljare'], K['tidsbas']['fps_namnare'])
    scener = {s['id'] for s in K['semantik']['scener']}; hand = []
    for h in sp.get('handling', []):
        H = ladda(bas / h['fil'])
        if h['scen'] not in scener: raise SystemExit('Scenen finns inte i källan: ' + h['scen'])
        seg = [segment(s, fps, h.get('rattelser')) for s in H['segment']]
        for x, y in zip(seg, seg[1:]):
            if x['rutor'][1] != y['rutor'][0]: raise SystemExit(f'Segmenten {x["id"]} och {y["id"]} har lucka eller överlapp.')
        hand.append(dict(scen=h['scen'], tagning=H.get('tagning'), ordforrad=H.get('ordforrad'), kalla_forklaring=H.get('kalla_forklaring'),
                         kalla=dict(fil=str(h['fil']).replace(chr(92), '/'), modell=(H.get('gemini') or {}).get('modell')), segment=seg))
    if hand: K['semantik']['handling'] = hand
    if sp.get('relevans'):
        R = ladda(bas / sp['relevans']['fil']); poster = []
        for p in R['poster'] + sp['relevans'].get('tillagg', []):
            q = {k: p.get(k) for k in ('id', 'namn', 'typ', 'roll', 'behandling', 'varfor', 'tagningar', 'samspel', 'kalla')}
            q['ref'] = p.get('plan_id') or None
            for f, ny in sp['relevans'].get('rattelser', {}).get(p['id'], {}).items(): q[f] = ny
            poster.append(q)
        K['semantik']['relevans'] = dict(mening=R['mening'], modell=R.get('modell'), kalla=str(sp['relevans']['fil']).replace(chr(92), '/'), poster=poster)
        if sp['relevans'].get('mobler_som_props'):
            # En möbel som relevanslistan namnger och som planen bygger, men som källan saknar som prop, blir en prop (rum_ref = planens id),
            # så att Jev och regin kan peka på den. Typen är relevanslistans namn; ingen form uppfinns.
            har = {p['id'] for p in K['semantik']['props']}
            for p in poster:
                if p.get('typ') == 'mobel' and p.get('ref') and p['ref'] not in har:
                    K['semantik']['props'].append(dict(id=p['ref'], typ=(p.get('namn') or p['ref']).lower().replace(' ', '_'), etikett=p.get('namn') or p['ref'], agare=None, stod=None, faste=None,
                                                       rum_ref=p['ref'], kalla='relevans (kalla_mening.py)', plats_id=None)); har.add(p['ref'])
    K['revision'] = K['revision'] + 1
    skriv(kut, K); print('KALLA', kut, 'revision', K['revision'], 'handling', sum(len(h['segment']) for h in hand), 'relevans', len(K['semantik'].get('relevans', {}).get('poster', [])))


if __name__ == '__main__': main()
