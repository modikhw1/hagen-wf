"""Uppdrag 0001: sammanställer tabellerna (tabeller.md) ur kameror.json, lyft_fler.json och kör den faktiska resolvern på en minneskopia.
Körs: scen/.venv/Scripts/python.exe -B -I sammanfatta.py   (kräver att kameror.py och lyft.py körts först)"""
import copy, json, os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
UT = os.path.dirname(HERE); KONTRAKT = os.path.dirname(UT)
sys.path.insert(0, KONTRAKT); sys.path.insert(0, os.path.dirname(KONTRAKT))
import boxpassning as bp, mobellyft as ml, foremallyft as fl  # noqa: E402

plan = json.load(open(f'{UT}/b-tilltal-ravara_n06-fler/narvaro/plan.json', encoding='utf8'))
kam = json.load(open(f'{HERE}/kameror.json', encoding='utf8'))['fler']['scener']
lyft = json.load(open(f'{HERE}/lyft_fler.json', encoding='utf8'))
pl = plan['plats'][0]; obj = {o['id']: o for o in plan['objekt']}
person = np.array(next(a for a in pl['uppmatta_ankare'] if a['id'] == 'staplats_C')['pos_m'][:2])
ut_ = []


def fm(v):
    return 'ej använd' if v is None else f'{v:.0f}'


def p(*a):
    s = ' '.join(str(x) for x in a); print(s); ut_.append(s)


def komplettgrupper(punkter, tol=.3):
    """Fullänk: alla par i en grupp inom tol m; girig, störst först."""
    rest = dict(punkter); grupper = []
    while rest:
        bast = max(([k] + [j for j in rest if j != k and np.hypot(*(np.asarray(rest[k]) - np.asarray(rest[j]))) <= tol] for k in rest), key=len)
        grupp = []
        for k in bast:
            if all(np.hypot(*(np.asarray(rest[k]) - np.asarray(rest[j]))) <= tol for j in grupp): grupp.append(k)
        grupper.append(grupp)
        for k in grupp: rest.pop(k)
    return grupper


# --- tabell 1: kameror ---
p('## Tabell 1. Lösta kameror (gemensam ram = planens världskoordinater, rummets yaw -3,06°)')
p('| tagn | x m | y m | z m | yaw° | pitch° | roll° | FOV° (lins) | deklarerad kamera | m till person C |')
p('|---|---|---|---|---|---|---|---|---|---|')
dekl_kam = {'S1': 'kamera_1', 'S2': 'kamera_1', 'S3': 'kamera_1', 'S4': 'kamera_1', 'S5': 'kamera_2', 'S6': 'kamera_3', 'S7': 'kamera_3',
            'S8': 'kamera_4', 'S9': 'kamera_4', 'S10': 'kamera_4', 'S11': 'kamera_4'}
for sid, k in kam.items():
    S = sid.upper(); pos = np.array(k['pos_m'][:2])
    f = np.array([np.cos(np.radians(k['yaw_grader'])), np.sin(np.radians(k['yaw_grader']))])
    anker = {'S1': 'A', 'S2': 'A', 'S3': 'B', 'S4': 'B'}.get(S, 'C')
    pe = np.array(next(a for a in pl['uppmatta_ankare'] if a['id'] == f'staplats_{anker}')['pos_m'][:2])
    p(f'| {S} | {k["pos_m"][0]:.2f} | {k["pos_m"][1]:.2f} | {k["pos_m"][2]:.2f} | {k["yaw_grader"]:.1f} | {k["pitch_grader"]:.1f} | {k["roll_grader"]:.1f} | {k["fov_h_grader"]:.1f} ({k["lins_mm"]:.0f} mm) | {dekl_kam[S]} | {float((pe - pos) @ f):.2f} |')

# --- tabell 2: lyft per tagning ---
disk = lyft['disk_C']; vag = lyft['vag']
konsensus_C = np.median([v['lyft_xy'] for t, v in disk['per_tagning'].items() if t != 'S6'], axis=0)
final_C = np.array([1.8707678992395045, 0.9061292569107198])
fit_C = np.array(disk['fit_xy'])
p('\n## Tabell 2. disk_C lyft ur EN tagnings box (ren geometri, ingen klämning), avstånd på golvet till tre referenser')
p(f'Referenser: fit = obegränsad robust passning mot alla fem boxar {fit_C.tolist()}; slut = vad `mobellyft.los` ger nu efter klämning {final_C.round(3).tolist()}; med = median av lyften utan S6 {konsensus_C.round(3).tolist()}.')
p('| tagn | box [ymin,xmin,ymax,xmax] | lyft x,y | m till fit | m till slut | m till med | fit-rms px | använda kanter |')
p('|---|---|---|---|---|---|---|---|')
for t, v in sorted(disk['per_tagning'].items(), key=lambda kv: int(kv[0][1:])):
    xy = np.array(v['lyft_xy'])
    p(f'| {t} | {v["box"]} | {xy[0]:.2f}, {xy[1]:.2f} | {np.hypot(*(xy - fit_C)):.2f} | {np.hypot(*(xy - final_C)):.2f} | {np.hypot(*(xy - konsensus_C)):.2f} | {v["fit_rms_px"]:.0f} | {",".join(v["fit_kanter"])} |')
lyften = {t: v['lyft_xy'] for t, v in disk['per_tagning'].items()}
p('Grupper (fullänk, 0,3 m):', komplettgrupper(lyften))
p('disk_A: inga boxar (detektionen gav tom lista trots att uppsättningen säger S1–S4); ingen lyft möjlig.')

fit_V = np.array(vag['fit_xy'])
p('\n## Tabell 3. Vågen lyft ur EN tagnings box (bottenmitt mot disk_C:s ovansida, z=0,9), obeskuret och klämt mot disken')
p(f'Referens: obegränsad passning mot fyra boxar {fit_V.tolist()}; disk_C i planen har mitt {obj["disk_C"]["pos_m"][:2]} (y-spann {obj["disk_C"]["pos_m"][1] - .25:.2f}–{obj["disk_C"]["pos_m"][1] + .25:.2f}).')
p('| tagn | box | lyft x,y | klämd x,y | m obeskuret→fit | fit-rms px | kanter |')
p('|---|---|---|---|---|---|---|')
for t, v in sorted(vag['per_tagning'].items(), key=lambda kv: int(kv[0][1:])):
    xy = np.array(v['lyft_xy']); kl = v['lyft_klamd_xy']
    p(f'| {t} | {v["box"]} | {xy[0]:.2f}, {xy[1]:.2f} | {kl[0]:.2f}, {kl[1]:.2f} | {np.hypot(*(xy - fit_V)):.2f} | {v["fit_rms_px"]:.0f} | {",".join(v["fit_kanter"])} |')
p('Grupper (fullänk, 0,3 m):', komplettgrupper({t: v['lyft_xy'] for t, v in vag['per_tagning'].items()}))
p('Grupper efter klämning (0,3 m):', komplettgrupper({t: v['lyft_klamd_xy'] for t, v in vag['per_tagning'].items()}))

# --- tabell 4: faktiska resolvern på kopia ---
kopia = copy.deepcopy(plan); rap = ml.los(kopia)
dc = next(r for r in rap if r['mobel'] == 'disk_C')
p('\n## Tabell 4. `mobellyft.los` på en minneskopia av n06-fler (nuvarande kod): disk_C')
p(f'status={dc["status"]} start={[round(v, 3) for v in dc["start_pos_m"][:2]]} slut={[round(v, 3) for v in dc["slutlig_pos_m"][:2]]} klämd={dc.get("klamd")} granskonflikt={dc.get("granskonflikt")}')
p('| tagn | rms före px | rms efter px | kanter | centrumdjup efter m | kameramarginal m | personmarginal m (krav 0,10) | lokal konflikt |')
p('|---|---|---|---|---|---|---|---|')
kl = {k['tagning']: k for k in dc['klamningar']}
for pt in sorted(dc['per_tagning'], key=lambda x: int(x['tagning'][1:])):
    k = kl[pt['tagning']]
    p(f'| {pt["tagning"]} | {fm(pt["fore_rms_px"])} | {fm(pt["efter_rms_px"])} | {",".join(pt["kanter"])} | {k["centrumdjup_efter_m"]:.2f} | {k["uppnadd_kameramarginal_m"]:.2f} | {k["uppnadd_personmarginal_m"]:.2f} | {k["granskonflikt"]} |')

# --- kontroll: nyckelbilderna (avläst med ögat) ---
p('\n## Kontroll: disk_C om S6/S7-boxens övre kant sätts där bordsytan syns i nyckelbilden (avläst på ögat, ca 0,87 av höjden)')
mob = obj['disk_C']
for t, y0 in (('S6', 870), ('S7', 875)):
    xy = ml._enbildslage(plan, pl, {}, mob, dict(tagning=t, box_2d=[y0, 0, 1000, 1000]))
    p(f'{t}: box [{y0},0,1000,1000] -> lyft x,y = {xy[0]:.2f}, {xy[1]:.2f}')
p(f'Personplats C (framfor) = {person.tolist()}; bordets bakkant får högst ligga 0,10 m framför personen.')
open(f'{HERE}/tabeller.md', 'w', encoding='utf8').write('\n'.join(ut_) + '\n')

# --- föremålslyftet efter möbellyftet (kedjan: mobellyft -> foremallyft) ---
frap = fl.los(kopia)
p('\n## Tabell 5. `foremallyft.los` efter möbellyftet på samma minneskopia')
for r in frap:
    p(f'{r["foremal"]}: status={r["status"]} {r.get("orsak", "")} slut={[round(v, 3) for v in r.get("slutlig_pos_m", [])[:2]]}')
vr = next(r for r in frap if r['foremal'] == 'vag')
vfin = np.array(vr['slutlig_pos_m'][:2])
for pt in sorted(vr['per_tagning'], key=lambda x: int(x['tagning'][1:])):
    p(f'  vag {pt["tagning"]}: rms före {fm(pt["fore_rms_px"])} efter {fm(pt["efter_rms_px"])} px, kanter {",".join(pt["kanter"])}')

# --- tabell 6: samlad per tagning (till svaret) ---
p('\n## Tabell 6. Samlad per tagning: avstånd på golvet (m) mellan lyft ur just den tagningens box och det slutliga läget i planen')
p('| tagn | kamera x,y | yaw/pitch/FOV | disk_C | disk_A | vågen (obeskuret / klämt) |')
p('|---|---|---|---|---|---|')
for sid, k in kam.items():
    S = sid.upper()
    dC = disk['per_tagning'].get(S); vv = vag['per_tagning'].get(S)
    c1 = f'{np.hypot(*(np.array(dC["lyft_xy"]) - final_C)):.2f}' if dC else '–'
    c3 = (f'{np.hypot(*(np.array(vv["lyft_xy"]) - vfin)):.2f} / {np.hypot(*(np.array(vv["lyft_klamd_xy"]) - vfin)):.2f}') if vv else '–'
    p(f'| {S} | {k["pos_m"][0]:.2f}, {k["pos_m"][1]:.2f} | {k["yaw_grader"]:.0f}/{k["pitch_grader"]:.1f}/{k["fov_h_grader"]:.1f} | {c1} | {"ingen box" if S in ("S1", "S2", "S3", "S4") else "–"} | {c3} |')
open(f'{HERE}/tabeller.md', 'w', encoding='utf8').write('\n'.join(ut_) + '\n')
