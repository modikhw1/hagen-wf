"""Uppdrag 0001, del B steg 2: hur långt hamnar disk_C, disk_A och vågen från sitt passade läge när de lyfts ur
EN tagnings bildruta? Läser plan + deklarerade boxar, importerar repots moduler skrivskyddat (-B, inga filer ändras).
Körs: scen/.venv/Scripts/python.exe -B -I lyft.py [variant=fler]   Skriver lyft_<variant>.json bredvid."""
import copy, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
UT = os.path.dirname(HERE); KONTRAKT = os.path.dirname(UT)
sys.path.insert(0, KONTRAKT); sys.path.insert(0, os.path.dirname(KONTRAKT))
import boxpassning as bp, mobellyft as ml, foremallyft as fl  # noqa: E402

variant = sys.argv[1] if len(sys.argv) > 1 else 'fler'
plan = json.load(open(f'{UT}/b-tilltal-ravara_n06-{variant}/narvaro/plan.json', encoding='utf8'))
pl = plan['plats'][0]
mobler = pl['deklarerat']['mobler']; foremal = pl['deklarerat']['foremal']
obj = {o['id']: o for o in plan['objekt']}
ut = {}


def kam(tagning):
    s = fl._scen(plan, tagning); u0, u1 = s['ut']; ruta = (u0 + u1 - 1) // 2
    M = np.asarray(plan['renderkamera']['nycklar'][ruta]['matris'], float)
    f = (M[:3, :3] @ [0, 0, -1.])[:2]; f /= np.linalg.norm(f)
    return M[:2, 3], f


def fordela(xy, ref, tagning):
    """Avstånd till ref samt uppdelat i djup (längs kamerans blick) och sida, meter på golvet."""
    c, f = kam(tagning); d = np.asarray(xy) - np.asarray(ref)
    return dict(m=float(np.hypot(*d)), djup_m=float(d @ f), sida_m=float(d @ np.array([f[1], -f[0]])))


def grupper(punkter, tol=.3):
    """Enkellänk: tagningar vars lyft ligger inom tol m (kedjat) hör ihop."""
    namn = list(punkter); grp = {n: i for i, n in enumerate(namn)}
    for a in namn:
        for b in namn:
            if np.hypot(*(np.asarray(punkter[a]) - np.asarray(punkter[b]))) <= tol:
                ga, gb = grp[a], grp[b]
                for n in namn:
                    if grp[n] == gb: grp[n] = ga
    ut_ = {}
    for n, g in grp.items(): ut_.setdefault(g, []).append(n)
    return list(ut_.values())


def kantrapport(objekt, xy, bild):
    box, key, _ = bp.bilddata(plan, bild)
    mal = bp.anvanda_kanter(plan, box)
    try:
        pr = bp.projicerade_kanter(plan, objekt, xy, key)
    except ValueError as ex:
        return dict(orsak=str(ex), kanter=list(mal))
    fel = {k: round(pr[k] - v, 1) for k, v in mal.items()}
    return dict(kanter=list(mal), residual_px=fel, rms_px=round(float(np.sqrt(np.mean(np.square(list(fel.values()))))), 1),
                beskuren={k: (k not in mal) for k in ('vanster', 'hoger', 'topp', 'botten')})


# ---------- möbler ----------
def mobel(did):
    spec = mobler[did]; bilder = spec.get('bilder') or []; o = obj[did]; r = dict(antal_boxar=len(bilder))
    if not bilder:
        r['orsak'] = 'inga boxar i deklarationen (detektorn hittade den i ingen tagning)'; return r
    per = {}; lyft = {}
    for b in bilder:
        t = b['tagning']
        try:
            xy_geo = ml._enbildslage(plan, pl, {}, o, b)             # enbildsvägen utan person-/kameraklämning
            xy_kl = ml._enbildslage(plan, pl, spec, o, b)            # med klämning mot person
            lyft[t] = xy_geo
            per[t] = dict(box=b['box_2d'], lyft_xy=[round(float(v), 3) for v in xy_geo], lyft_klamd_xy=[round(float(v), 3) for v in xy_kl])
        except (ValueError, KeyError, IndexError) as ex:
            per[t] = dict(box=b['box_2d'], orsak=str(ex))
    r['per_tagning'] = per
    if len(bilder) > 1:
        start = ml._enbildslage(plan, pl, {}, o, ml.tillforlitligast(plan, bilder))
        xy, info = bp.passa(plan, o, bilder, start)
        r['fit_xy'] = [round(float(v), 3) for v in xy]; r['fit_lyckad'] = info['lyckad']
        for p in info['per_tagning']:
            t = p['tagning']; per[t].update(fit_rms_px=p['efter_rms_px'], fit_residual_px=p['efter_residualer_px'], fit_kanter=p['kanter'])
            if t in lyft: per[t]['avstand_till_fit'] = fordela(lyft[t], xy, t)
            per[t]['kantrapport'] = kantrapport(o, xy, next(b for b in bilder if b['tagning'] == t))
        r['grupper_lyft_0_3m'] = grupper(lyft)
    return r


# ---------- föremål på möbel ----------
def foremal_pa(fid):
    f = foremal[fid]; bilder = f.get('bilder') or []; o = obj[f['objekt_id']]
    stod = obj[f['pa']] if f['pa'] in obj else obj[foremal[f['pa']]['objekt_id']]
    topp = float(stod['pos_m'][2]) + float(stod['matt_m'][2]) / 2.
    r = dict(antal_boxar=len(bilder), stod=stod['id'], stod_pos=[round(v, 3) for v in stod['pos_m']])
    per = {}; lyft = {}
    for b in bilder:
        t = b['tagning']
        try:
            xy, _ = fl._traff(plan, b, topp); lyft[t] = xy
            per[t] = dict(box=b['box_2d'], lyft_xy=[round(float(v), 3) for v in xy], lyft_klamd_xy=[round(float(v), 3) for v in fl._klam(stod, o, xy)])
        except ValueError as ex:
            per[t] = dict(box=b['box_2d'], orsak=str(ex))
    r['per_tagning'] = per
    if len(bilder) > 1:
        po = dict(o); po['pos_m'] = [float(o['pos_m'][0]), float(o['pos_m'][1]), topp + float(o['matt_m'][2]) / 2.]
        xy, info = bp.passa(plan, po, bilder, np.asarray(o['pos_m'][:2], float))
        r['fit_xy'] = [round(float(v), 3) for v in xy]; r['fit_lyckad'] = info['lyckad']
        for p in info['per_tagning']:
            t = p['tagning']; per[t].update(fit_rms_px=p['efter_rms_px'], fit_residual_px=p['efter_residualer_px'], fit_kanter=p['kanter'])
            if t in lyft: per[t]['avstand_till_fit'] = fordela(lyft[t], xy, t)
            per[t]['kantrapport'] = kantrapport(po, xy, next(b for b in bilder if b['tagning'] == t))
        r['grupper_lyft_0_3m'] = grupper(lyft)
    return r


ut['disk_C'] = mobel('disk_C'); ut['disk_A'] = mobel('disk_A')
ut['vag'] = foremal_pa('vag')
# den faktiska resolvern på en kopia i minnet (ingen fil skrivs)
kopia = copy.deepcopy(plan)
rap = ml.los(kopia) or []
ut['los_mobler'] = [{k: v for k, v in p.items() if k in ('mobel', 'status', 'orsak', 'slutlig_pos_m', 'start_pos_m', 'start_framfor_alla_kameror', 'start_orsak', 'granskonflikt', 'klamd', 'klamningsgrans')} for p in rap]
ut['plan_foremal_lyft'] = plan['kvalitet'].get('foremal_lyft')
ut['plan_mobel_lyft'] = [{k: v for k, v in p.items() if k in ('mobel', 'status', 'orsak', 'slutlig_pos_m', 'granskonflikt')} for p in plan['kvalitet'].get('mobel_lyft', [])]
json.dump(ut, open(f'{HERE}/lyft_{variant}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1, default=float)


def skriv(namn, r):
    print(f'\n=== {namn}: {r["antal_boxar"]} boxar; fit={r.get("fit_xy")} {r.get("orsak", "")}')
    for t, p in r.get('per_tagning', {}).items():
        a = p.get('avstand_till_fit') or {}; k = p.get('kantrapport') or {}
        print(f'  {t:4} box={p["box"]}  lyft={p.get("lyft_xy")} klamd={p.get("lyft_klamd_xy")}  '
              f'd_fit={a.get("m", float("nan")):.2f}m (djup {a.get("djup_m", float("nan")):+.2f}, sida {a.get("sida_m", float("nan")):+.2f})  fit_rms={p.get("fit_rms_px")}px {k.get("residual_px", k.get("orsak", ""))}  {p.get("orsak", "")}')
    if 'grupper_lyft_0_3m' in r: print('  grupper(0,3 m):', r['grupper_lyft_0_3m'])


for n in ('disk_C', 'disk_A', 'vag'): skriv(n, ut[n])
print('\nlos() på kopia:', json.dumps(ut['los_mobler'], ensure_ascii=False)[:900])
print('plan mobel_lyft:', json.dumps(ut['plan_mobel_lyft'], ensure_ascii=False)[:600])
