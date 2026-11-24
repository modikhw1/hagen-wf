"""0029: för in en genererad kropp och scenen kring den i en källa. Befintliga utdata skrivs aldrig över.

  scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_generering.py <kalla.json> <ny kalla.json> <spec.json>

Allmänt för vilken tagning, generator och kropp som helst; specen säger vad som gäller för just den här tagningen:
  {"scen": "s1", "person": "A",
   "sekvens": <npz: kroppen ur genereringen, rättad>,                       -> matning.personer[].rorelse (scenens post)
   "ursprung": {"generator": str, "las": str, "status": str,
                "filer": {<roll>: <sökväg>, ...}},                           -> matning.personer[].ursprung (filpekare med sha256)
   "kamera_plan": <plan.json med renderkameran>,                            -> matning.kameror[].renderbana (npz bredvid källan)
   "kamera_metod": str,
   "scen_plan": <plan.json med scenen kring kroppen>, "objekt": [id-prefix, ...], "ersatter": [objekt-id, ...],
   "handforemal": {"id": str, "faste": <sked_faste.json>}}                  -> matning.scenbygge[]
Kroppens ursprung står alltså i källan: vilken generering, vilken tidsavbildning, vilken roträttning. En senare ändring kan be om en
ny generering i stället för att lappa. Sökvägar i specen är relativa till specens mapp; i källan relativa till källans mapp.
Renderbanan sparas i platsens ram tillsammans med platsens transform vid mätningen (till_plats), så att kompilatorn kan följa med
om scenen flyttas till en annan plats.
"""
import copy, hashlib, json, os, sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
from gemensamt import ladda, skriv


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def filref(p, mapp, roll):
    p = Path(p).resolve(); fmt = p.suffix.lstrip('.').lower()
    return dict(sokvag=os.path.relpath(p, mapp).replace('\\', '/'), sha256=sha(p), format=fmt, roll=roll)


def main():
    kin, kut, specf = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    if kut.exists(): raise SystemExit(f'{kut} finns redan; befintliga utdata skrivs aldrig över.')
    K = ladda(kin); sp = ladda(specf); bas = specf.parent; mapp = kut.parent; P = lambda x: (bas / x).resolve()
    sid, pid = sp['scen'], sp['person']; ksc = next(s for s in K['semantik']['scener'] if s['id'] == sid)
    # 1. kroppen och dess ursprung
    mp = next(m for m in K['matning']['personer'] if m['person'] == pid and m.get('scen') in (None, sid))
    gammal = copy.deepcopy(mp['rorelse'])
    z = np.load(P(sp['sekvens'])); n_ny = len(z['pose']); n_gl = next(x['form'][0] for x in gammal.get('nycklar', []) if x['namn'] == 'pose')
    if n_ny != n_gl: raise SystemExit(f'Sekvensen har {n_ny} rutor, tagningen {n_gl}.')
    mp['rorelse'] = dict(filref(P(sp['sekvens']), mapp, f'Kroppsrörelse i MHR-form per ruta, {sid}: läst ur en generering ({sp["ursprung"]["generator"]}), tidspassad och roträttad.'),
                         nycklar=gammal.get('nycklar', []))
    mp['ursprung'] = dict(typ='generering', generator=sp['ursprung']['generator'], las=sp['ursprung']['las'], status=sp['ursprung']['status'],
                          filer=[dict(filref(P(v), mapp, k)) for k, v in sp['ursprung']['filer'].items()], ersatt_lasning=gammal['sokvag'])
    # 2. renderbanan
    pl = ladda(P(sp['kamera_plan'])); d = next(x for x in pl['scener'] if x['id'] == sid); a, b = d['ut']
    nk = pl['renderkamera']['nycklar'][a:b]; reg = next(r for p in K['matning']['platser'] for r in p['registreringar'] if r['scen'] == sid)
    bana = mapp / f'{sid}_renderbana_{kut.stem}.npz'
    np.savez(bana, matris=np.array([k['matris'] for k in nk]), lins_mm=np.array([k['lins_mm'] for k in nk]), till_plats=np.array(reg['till_plats']['matris']))
    kam = next(k for k in K['matning']['kameror'] if k['id'] == ksc['kamera'])
    kam['renderbana'] = dict(fil=filref(bana, mapp, f'Renderkamerans bana per ruta i platsens ram, {sid}.'), metod=sp['kamera_metod'],
                             kalla=filref(P(sp['kamera_plan']), mapp, 'Planen kameran löstes i.'), status='matt mot originalets synliga överkropp')
    # 3. scenen kring kroppen
    sc = ladda(P(sp['scen_plan'])); ds = next(x for x in sc['scener'] if x['id'] == sid); sa, sb = ds['ut']; kr = sc['kallrutor']
    obj = []
    for o in sc['objekt']:
        if not any(o['id'] == p or o['id'].startswith(p + ':') for p in sp['objekt']): continue
        u0, u1 = o.get('synlig_ut') or [sa, sb]; u0, u1 = max(u0, sa), min(u1, sb)
        if u0 >= u1: continue
        o = copy.deepcopy(o); o.pop('synlig_ut', None); o.pop('scen', None); o['synlig_kalla'] = [int(kr[u0]), int(kr[u1 - 1]) + 1]
        if 'glas' in str(o.get('status', '')): o['yta'] = 'glas'   # renderas genomskinlig (gennedbrytning/s_glas_blender.py); mhr_rig ger bara färg
        obj.append(o)
    fa = ladda(P(sp['handforemal']['faste']))
    post = dict(scen=sid, ersatter=sp['ersatter'], objekt=obj, kalla=filref(P(sp['scen_plan']), mapp, f'Planen scenen byggdes i ({sid}).'),
                handforemal=[dict(id=sp['handforemal']['id'], offset_m=fa['offset_m'], status=fa['status'], kalla=filref(P(sp['handforemal']['faste']), mapp, 'Fästet mätt ur genereringen.'),
                                  post={k: v for k, v in next(h for h in sc['handforemal'] if h['id'] == sp['handforemal']['id'] and h['scen'] == sid).items() if k not in ('synlig_ut', 'kontroll_rutor', 'offset_m')})])
    K['matning'].setdefault('scenbygge', [])
    K['matning']['scenbygge'] = [x for x in K['matning']['scenbygge'] if x['scen'] != sid] + [post]
    K['revision'] = K['revision'] + 1
    skriv(kut, K); print('KALLA', kut, 'revision', K['revision'], 'objekt', len(obj))


if __name__ == '__main__': main()
