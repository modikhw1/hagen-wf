"""Uppdrag 0001, del B steg 1: lösta kameror per tagning (läge, yaw, pitch, roll, FOV) i planens gemensamma ram.
Körs: scen/.venv/Scripts/python.exe -B -I kameror.py [plan.json]   (läser bara, skriver kameror.json bredvid)."""
import json, math, sys, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
UT = os.path.dirname(HERE)
PLANER = {v: f'{UT}/b-tilltal-ravara_n06-{v}/narvaro/plan.json' for v in ('mobel2', 'skymning', 'fler')}


def scenkamera(plan, scen):
    u0, u1 = scen['ut']; ruta = (u0 + u1 - 1) // 2
    key = plan['renderkamera']['nycklar'][ruta]
    M = np.asarray(key['matris'], float); R = M[:3, :3]
    f = R @ [0, 0, -1.]; r = R @ [1., 0, 0]
    sensor = float(plan['renderkamera'].get('sensor_bredd_mm', 36.))
    return dict(ruta=ruta, pos_m=[round(float(v), 3) for v in M[:3, 3]],
                yaw_grader=round(math.degrees(math.atan2(f[1], f[0])), 2),
                pitch_grader=round(math.degrees(math.asin(f[2])), 2),
                roll_grader=round(math.degrees(math.asin(r[2])), 2),
                lins_mm=round(float(key['lins_mm']), 2),
                fov_h_grader=round(math.degrees(2 * math.atan(sensor / (2 * float(key['lins_mm'])))), 2))


def main():
    ut = {}
    for namn, sokvag in PLANER.items():
        plan = json.load(open(sokvag, encoding='utf8'))
        scener = plan.get('scener') or plan['matkamera']['scener']
        bk = {p['scen']: p for p in plan['kvalitet'].get('bildkamera', {}).get('scener', [])}
        rum_yaw = math.degrees(plan['objekt'][0]['rotation_rad'][2])
        rad = {}
        for s in scener:
            k = scenkamera(plan, s); k['yaw_mot_rummet_grader'] = round(k['yaw_grader'] - rum_yaw, 2)
            b = bk.get(s['id'], {})
            k['bildkamera_status'] = b.get('status'); k['bildkamera_justering'] = b.get('justering')
            rad[s['id']] = k
        ut[namn] = dict(rum_yaw_grader=round(rum_yaw, 2), scener=rad)
    json.dump(ut, open(f'{HERE}/kameror.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    for namn, d in ut.items():
        print(f'== {namn} (rummets yaw {d["rum_yaw_grader"]}°)')
        print('scen   x      y      z    yaw  yaw/rum pitch roll  fov   bildkamera')
        for sid, k in d['scener'].items():
            j = k['bildkamera_justering'] or {}
            print(f'{sid:4} {k["pos_m"][0]:6.2f} {k["pos_m"][1]:6.2f} {k["pos_m"][2]:5.2f} {k["yaw_grader"]:6.1f} {k["yaw_mot_rummet_grader"]:6.1f} {k["pitch_grader"]:5.1f} {k["roll_grader"]:5.1f} {k["fov_h_grader"]:5.1f}  {k["bildkamera_status"]} dx={j.get("dx_m", 0):.2f} dy={j.get("dy_m", 0):.2f} dyaw={j.get("yaw_grader", 0):.1f}')


main()
