"""Uppdrag 0004: omräkning utan kompilering. Lyften ur 0001 (tabell 6) körda med olika fokal, kameran flyttad längs sin
blickriktning så att personen ligger kvar på samma bildrad och med samma storlek (avstånd till personen skalas med f_ny/f_gammal).
Körs: scen/.venv/Scripts/python.exe -B -I lins.py   (läser n06-fler/narvaro/plan.json, skriver lins_resultat.json och lins_tabeller.md)
Antaganden (diagnos, inte krav): personens referenspunkt = bröst 1,05 m över golvet vid personplatsen; kamerahöjden hålls (1,40 m);
yaw och roll hålls; pitch räknas om så att referenspunkten får samma bildrad."""
import copy, json, math, os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
UT = os.path.dirname(HERE); KONTRAKT = os.path.dirname(UT)
sys.path.insert(0, KONTRAKT); sys.path.insert(0, os.path.dirname(KONTRAKT))
import mobellyft as ml, foremallyft as fl  # noqa: E402

plan0 = json.load(open(f'{UT}/b-tilltal-ravara_n06-fler/narvaro/plan.json', encoding='utf8'))
pl = plan0['plats'][0]; ank = {a['id']: np.array(a['pos_m'], float) for a in pl['uppmatta_ankare']}
PERSON = {'S1': 'A', 'S2': 'A', 'S3': 'B', 'S4': 'B'}; PREF_Z = 1.05
W, H = float(plan0['utdata']['bredd']), float(plan0['utdata']['hojd']); SENS = 36.


def rz(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.]])


def nyckel_ny(key, person_xy, f_ny):
    """Ny kamera för en tagning: samma bildrad/storlek för personen vid ny fokal. Returnerar ny nyckel och diagnostik."""
    M = np.asarray(key['matris'], float); f_gl = float(key['lins_mm']) / SENS * W; C = M[:3, 3]; R = M[:3, :3]
    fram = R @ [0, 0, -1.]; yaw = math.atan2(fram[1], fram[0]); hfram = np.array([math.cos(yaw), math.sin(yaw)])
    P = np.array([person_xy[0], person_xy[1], PREF_Z])
    d = P - C; lokal = d @ R; v0 = -lokal[1] / -lokal[2] * f_gl               # bildrad (px under mitten) för referenspunkten
    D = float((P[:2] - C[:2]) @ hfram); D2 = D * f_ny / f_gl                  # horisontellt avstånd skalas med fokalen
    C2 = np.array([C[0] + (D - D2) * hfram[0], C[1] + (D - D2) * hfram[1], C[2]])   # flytta längs blicken, behåll sidoläget
    alfa2 = math.atan2(C[2] - PREF_Z, D2)                                      # sänkningsvinkel till referenspunkten
    theta2 = alfa2 - math.atan(v0 / f_ny)                                      # ny pitch (ned) så att punkten hamnar på samma bildrad
    # gammal pitch (ned) för jämförelse
    th0 = -math.asin(fram[2])
    # bygg ny rotation: yaw hålls, pitch=theta2 ned, roll hålls (R = Rz(yaw) Rx(...) approximerat med samma roll)
    f2 = np.array([hfram[0] * math.cos(theta2), hfram[1] * math.cos(theta2), -math.sin(theta2)])
    hoger = np.cross(f2, [0, 0, 1.]); hoger /= np.linalg.norm(hoger); upp = np.cross(hoger, f2)
    R2 = np.column_stack([hoger, upp, -f2])
    k2 = copy.deepcopy(key); N = np.eye(4); N[:3, :3] = R2; N[:3, 3] = C2; k2['matris'] = N.tolist(); k2['lins_mm'] = f_ny / W * SENS
    return k2, dict(D_gammal_m=round(D, 2), D_ny_m=round(D2, 2), pitch_gammal_ned_grader=round(math.degrees(th0), 1),
                    pitch_ny_ned_grader=round(math.degrees(theta2), 1), kamera_ny_xy=[round(float(C2[0]), 2), round(float(C2[1]), 2)])


def planera(f_ny):
    p = copy.deepcopy(plan0); diag = {}
    for s in p['scener']:
        u0, u1 = s['ut']; mid = (u0 + u1 - 1) // 2; sid = s['id'].upper()
        pe = ank[f'staplats_{PERSON.get(sid, "C")}'][:2]
        k2, d = nyckel_ny(p['renderkamera']['nycklar'][mid], pe, f_ny)
        p['renderkamera']['nycklar'][mid] = k2; diag[sid] = d
    return p, diag


def lyften(p):
    obj = {o['id']: o for o in p['objekt']}; pl_ = p['plats'][0]; res = {}
    disk = obj['disk_C']; spec = pl_['deklarerat']['mobler']['disk_C']
    for b in spec['bilder']:
        try: res.setdefault('disk_C', {})[b['tagning']] = [float(v) for v in ml._enbildslage(p, pl_, {}, disk, b)]
        except ValueError as ex: res.setdefault('disk_C', {})[b['tagning']] = str(ex)
    stod = disk; topp = float(stod['pos_m'][2]) + float(stod['matt_m'][2]) / 2.
    for b in pl_['deklarerat']['foremal']['vag']['bilder']:
        try: res.setdefault('vag', {})[b['tagning']] = [float(v) for v in fl._traff(p, b, topp)[0]]
        except ValueError as ex: res.setdefault('vag', {})[b['tagning']] = str(ex)
    return res


def spridning(d, tagn):
    pts = [np.array(d[t]) for t in tagn if isinstance(d.get(t), list)]
    return max((float(np.hypot(*(a - b))) for i, a in enumerate(pts) for b in pts[i + 1:]), default=float('nan'))


ut = {}; rader = []
for f_ny in (1024., 900., 780., 700.):
    p, diag = planera(f_ny); r = lyften(p); ut[int(f_ny)] = dict(lyft=r, kameror=diag)
rader.append('## Lyft ur en tagnings box (m från den gemensamma medianen av tagningarna S7–S11 för samma fokal)')
rader.append('| f (px) / lins mm | disk_C S7 | S8 | S9 | S11 | spridning S8,S9,S11 (m) | vågen S8 | S9 | S10 | S11 | spridning S8–S11 (m) |')
rader.append('|---|---|---|---|---|---|---|---|---|---|---|')
for f_ny, v in ut.items():
    d, g = v['lyft']['disk_C'], v['lyft']['vag']
    med_d = np.median([d[t] for t in ('S7', 'S8', 'S9', 'S11') if isinstance(d.get(t), list)], axis=0)
    med_v = np.median([g[t] for t in ('S8', 'S9', 'S10', 'S11') if isinstance(g.get(t), list)], axis=0)
    fd = lambda t, m, dd: f'{np.hypot(*(np.array(dd[t]) - m)):.2f}' if isinstance(dd.get(t), list) else 'bakom kameran'
    rader.append(f'| {f_ny} / {f_ny / 16:.0f} | {fd("S7", med_d, d)} | {fd("S8", med_d, d)} | {fd("S9", med_d, d)} | {fd("S11", med_d, d)} | {spridning(d, ("S8", "S9", "S11")):.2f} | '
                 f'{fd("S8", med_v, g)} | {fd("S9", med_v, g)} | {fd("S10", med_v, g)} | {fd("S11", med_v, g)} | {spridning(g, ("S8", "S9", "S10", "S11")):.2f} |')
rader.append('\n## Lyft (x, y) per tagning')
for f_ny, v in ut.items():
    rader.append(f'f={f_ny}: disk_C ' + ', '.join(f'{t} ' + (f'({x[0]:.2f},{x[1]:.2f})' if isinstance(x, list) else x) for t, x in sorted(v['lyft']['disk_C'].items(), key=lambda kv: int(kv[0][1:]))))
    rader.append(f'        vag ' + ', '.join(f'{t} ' + (f'({x[0]:.2f},{x[1]:.2f})' if isinstance(x, list) else x) for t, x in sorted(v['lyft']['vag'].items(), key=lambda kv: int(kv[0][1:]))))
rader.append('\n## Kameror per tagning vid f=780 px (jämför kolumn D_gammal)')
rader.append('| tagn | D gammal m | D ny m | pitch gammal° | pitch ny° | kamera xy ny |')
rader.append('|---|---|---|---|---|---|')
for sid, d in ut[780]['kameror'].items():
    rader.append(f'| {sid} | {d["D_gammal_m"]} | {d["D_ny_m"]} | {d["pitch_gammal_ned_grader"]} | {d["pitch_ny_ned_grader"]} | {d["kamera_ny_xy"]} |')
open(f'{HERE}/lins_tabeller.md', 'w', encoding='utf8').write('\n'.join(rader) + '\n')
json.dump({str(k): v for k, v in ut.items()}, open(f'{HERE}/lins_resultat.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('\n'.join(rader))
