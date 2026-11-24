"""Mätpunkter för webbens egen utsnittsberäkning, ur planen utan edits.

Inga färdigräknade stativpositioner exporteras. Kroppens mål mäts före
eventuellt benstöd, precis som i kompilera.kameranycklar.
"""
import numpy as np
from gemensamt import HIT, ladda
from kompilera import F, gravitation, las_sekvens


def underlag(plan, kalla):
    namn = ladda(HIT.parent / 'ingest/mhr_ledernamn.json')
    platser = {p['id']: ladda(p['fil']['sokvag']) for p in plan['matning'].get('platser', [])}
    scener = {}
    for s in plan['scener']:
        v = las_sekvens(s['varld'])
        m = np.array(s.get('till_plats', np.eye(4)))
        g = m[:3, :3] @ gravitation(v)
        a, b = s['kalla']; start = s['lokal_start']
        mal = {}
        for p in plan['matning']['personer']:
            if p.get('scen') not in (None, s['id']):
                continue
            seq = las_sekvens(p['rorelse']['sokvag'])
            mal[p['person']] = {}
            for punkt, led in [('huvud', 'c_head'), ('kropp', 'c_spine2')]:
                i = namn.index(led)
                mal[p['person']][punkt] = [
                    dict(ruta=a+f-start, mal_m=(g @ (v['kam_C'][f] + v['kam_R'][f] @
                         (F @ (seq['pose'][f, i, :3]/100) + seq['cam_t'][f])) + m[:3, 3]).tolist())
                    for f in range(start, start+b-a) if seq['inom'][f]]
        plats = platser.get(s.get('plats_id'))
        tagning = next((r.get('tagning') for p in plan['matning'].get('platser', [])
                        for r in p['registreringar'] if r['scen'] == s['id']), None)
        props = []
        for prop in kalla['semantik']['props']:
            sedd = plats is None or tagning is None or any(
                o['id'] == prop['id'] and any(x['tagning'] == tagning for x in o.get('observationer', []))
                for o in plats['objekt'])
            o = next((o for o in plan['objekt'] if o['id'] == prop['id'] and
                      o['synlig_ut'][0] <= s['ut'][0] < o['synlig_ut'][1]), None)
            if sedd and o:
                props.append(dict(id=prop['id'], pos_m=o['pos_m']))
        scener[s['id']] = dict(mal=mal, props=props)
    return dict(kameror=plan['renderkamera']['nycklar'], scener=scener,
                bredd=plan['utdata']['bredd'], hojd=plan['utdata']['hojd'])
