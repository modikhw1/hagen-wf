"""0026 punkt 3: scenen kring kroppen, i en kopia av planen. Kedjans kod (mhr_rig.py, mobellyft.py) oförändrad.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/s_scen.py [--bygg]
Utgår från g_forvarld/dreamina_t/plan.json (n06-hand med S1:s rörelse ur Dreamina-utfallet, tidspassad) och samspel/dreamina.json
(leder i världen ur den byggda scenen, j_samspel_blender.py).
1. Disken. Källor längs diskens djupaxel (+ = mot henne): färgmaskerna ur 0025 (fargkod/disk_3d.json, ruta 0 och 112; 55 gick inte),
   segmenterarens mask i ruta 112, och tråget som villkor: fingertoppens lägsta punkt i h3–h4 ska ligga innanför diskens yta (minst
   TRAG_MARGINAL innanför bakkanten) och under ovankanten. Valet: den minsta flytt mot henne som uppfyller villkoret; källorna redovisas.
2. Tråget. Disken blir en bas (upp till tråggolvet) och fyra kanter (fram 0,20 m, bak och sidor 0,05 m) upp till ovankanten. Trågets djup
   = ovankanten minus fingertoppens lägsta punkt, begränsat till 0,10–0,35 m (antagen utanför det).
3. Skeden: planens handforemal (0013) ligger kvar; synlig i S1.
4. Bakgrunden: väggen finns. En bakre bänk (antagen: 0,90 m hög, 0,60 m djup) läggs mot väggen, längs hela väggen, som i "rummet utan disk".
5. Kunden: originalet är filmat från kundens plats; bara handen syns (h8). En antagen person (låda för kroppen, cylinder för huvudet) står vid
   kameran, utanför bild, och en arm (låda) går från axeln till skedens läge mitt i h8, synlig bara i h8. Allt märkt antagen.
Allt i S1 (synlig_ut 0–156). Ut: s_scen/plan.json, s_scen/scen.json (val och källor); --bygg bygger och renderar S1 med mhr_rig.
"""
import copy, json, math, subprocess, sys
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent; ROT = HIT.parents[2]; ING = HIT.parent / 'ingest'; S1 = ING / 'ut/kand-kennysgelato-tagningar/S1'
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
def _arg(n, f): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else f
# 0027: --plan, --samspel, --ut, --sked (offset_m ur r_sked.py), --ljus (ljus disk, mörkt tråg); förval som i 0026
UT = HIT / _arg('--ut', 's_scen'); LJUS = '--ljus' in sys.argv
TRAG_MARGINAL = .10; OFFS = 7
TRAG_MAX = float(_arg('--trag-max', '.35'))   # 0028: tråget får vara så djupt som handen når (annars ligger handen inne i diskens bas)


def lada(id_, pos, matt, yaw, farg, status, synlig=(0, 156), roll=(0., 0.)):
    return dict(id=id_, namn=id_, typ='lada', pos_m=[float(x) for x in pos], rotation_rad=[float(roll[0]), float(roll[1]), float(yaw)], matt_m=[float(x) for x in matt],
                farg=farg, top_slope=0, fas_m=0.0, status=status, deltyp='bord', modell_ref=None, texturprojektion=None, synlig_ut=list(synlig))


def main():
    plan = json.loads((HIT / _arg('--plan', 'g_forvarld/dreamina_t/plan.json')).read_text(encoding='utf-8')); sp = json.loads((HIT / _arg('--samspel', 'samspel/dreamina.json')).read_text())
    if '--sked' in sys.argv:
        sk = json.loads((HIT / _arg('--sked', '')).read_text(encoding='utf-8'))
        for h in plan['handforemal']:
            if h['scen'] == 's1': off_gammal = np.array(h['offset_m']); h['offset_m'] = sk['offset_m']; h['offset_status'] = sk['status']
    H = {s['id']: s['rutor_plan'] for s in json.loads((HIT / 'handling/S1/handling.json').read_text(encoding='utf-8'))['segment']}
    disk = next(o for o in plan['objekt'] if o['id'] == 'disk_A'); th = disk['rotation_rad'][2]; L, D, Hh = disk['matt_m']; c0 = np.array(disk['pos_m'])
    ex, ey = np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)])   # diskens längd- och djupaxel (+y mot henne)
    lok = lambda p, c: np.array([(np.array(p[:2]) - c[:2]) @ ex, (np.array(p[:2]) - c[:2]) @ ey, p[2]])
    # fingertoppen i h3–h4
    rr = [r for r in sp['rutor'] if H['h3'][0] <= r['ruta'] <= H['h4'][1]]
    ft = np.array([r['leder']['r_middle3']['svans'] for r in rr]); lag = int(np.argmin(ft[:, 2])); p_lag = ft[lag]
    y_lag = lok(p_lag, c0)[1]   # fingertoppens djupkoordinat med disken där den står
    # minsta flytt s (mot henne, +y) så att fingertoppen ligger minst TRAG_MARGINAL innanför bakkanten: y_lag - s <= D/2 - marginal
    s_trag = max(0., y_lag - (D / 2 - TRAG_MARGINAL))
    k3 = json.loads((HIT / 'fargkod/disk_3d.json').read_text(encoding='utf-8'))['rader']
    kallor = {f"{x['kalla']} ruta {x['ruta']}": x.get('flytt_mot_henne_m') for x in k3 if x.get('status') == 'flyttad' and x['kalla'] in ('V1', 'V2', 'seg')}
    kallor['tråget som villkor (minsta flytt)'] = round(float(s_trag), 3)
    s = s_trag; c = c0 + np.r_[s * ey, 0]
    top_lag = float(p_lag[2]); djup = Hh - top_lag + (.03 if TRAG_MAX > .35 else 0); djup_status = 'matt (fingertoppens lägsta punkt' + (' + 0,03 m)' if TRAG_MAX > .35 else ')')
    if not .10 <= djup <= TRAG_MAX: djup = float(np.clip(djup, .10, TRAG_MAX)); djup_status = f'antagen (handens punkt utanför 0,10–{TRAG_MAX:.2f} m)'
    golv = c0[2] - Hh / 2
    # disken som bas + fyra kanter
    plan['objekt'] = [o for o in plan['objekt'] if o['id'] != 'disk_A']
    bas_h = Hh - djup; P = lambda lx, ly, z: [*(c[:2] + lx * ex + ly * ey), z]
    fram, bak, sida = .20, .05, .05
    bak_h = djup   # 0028 --bak-lag: bakkanten (hennes sida) sänks till under underarmen där den passerar kanten i h3–h4 (montern öppen mot personalen, antagen)
    if '--bak-lag' in sys.argv:
        yk = D / 2 - bak / 2; zs = []
        for r in rr:
            e, w = np.array(r['leder']['r_lowarm']['huvud']), np.array(r['leder']['r_wrist']['huvud']); ye, yw = lok(e, c0)[1] - s_trag, lok(w, c0)[1] - s_trag
            if (ye - yk) * (yw - yk) <= 0 and ye != yw: zs.append(float(e[2] + (w[2] - e[2]) * (yk - ye) / (yw - ye)))
        if zs: bak_h = float(np.clip(min(zs) - .05 - (golv + Hh - djup), .03, djup))
    df = '#e4ddcf' if LJUS else disk['farg']; tf = '#5a4636' if LJUS else '#e9dfc7'
    plan['objekt'] += [lada('disk_A', P(0, 0, golv + bas_h / 2), [L, D, bas_h], th, df, 'flyttad (0026), bas till tråggolvet'),
                       lada('disk_A:fram', P(0, -D / 2 + fram / 2, golv + bas_h + djup / 2), [L, fram, djup], th, df, 'antagen kant' + (' (glas, 0028)' if '--glas' in sys.argv else '')),
                       lada('disk_A:bak', P(0, D / 2 - bak / 2, golv + bas_h + bak_h / 2), [L, bak, bak_h], th, df, 'antagen kant' + (f' (sänkt till {bak_h:.2f} m under underarmen, 0028)' if bak_h < djup else '')),
                       lada('disk_A:v', P(-L / 2 + sida / 2, 0, golv + bas_h + djup / 2), [sida, D, djup], th, df, 'antagen kant'),
                       lada('disk_A:h', P(L / 2 - sida / 2, 0, golv + bas_h + djup / 2), [sida, D, djup], th, df, 'antagen kant'),
                       lada('disk_A:trag', P(0, (fram - bak) / 2, golv + bas_h + .005), [L - 2 * sida, D - fram - bak, .01], th, tf, f'tråggolv, djup {djup:.2f} m: {djup_status}')]
    # bakre bänk mot väggen
    vagg = next(o for o in plan['objekt'] if o['id'] == 'vagg_bak'); vw = np.array(vagg['pos_m']); vyaw = vagg['rotation_rad'][2]
    vy = np.array([-math.sin(vyaw), math.cos(vyaw)]); bank_c = vw[:2] - vy * (vagg['matt_m'][1] / 2 + .30)
    plan['objekt'].append(lada('bank_bak', [*bank_c, golv + .45], [vagg['matt_m'][0] * .8, .60, .90], vyaw, '#b9bcc0', 'antagen (0,90 m hög, 0,60 m djup; rummet utan disk)'))
    # skeden: läge mitt i h8 ur scenen
    mitt = (H['h8'][0] + H['h8'][1]) // 2; r8 = next(r for r in sp['rutor'] if r['ruta'] == mitt); sked = np.array(r8['sked'] or r8['leder']['r_middle3']['svans'])
    if '--sked' in sys.argv and r8.get('sked_R') and '--samspel-har-fastet' not in sys.argv:   # 0027: skedens läge med det nya fästet (samma ram som i den byggda scenen)
        # 0028: --samspel-har-fastet när samspelet är läst ur en scen byggd med samma fäste; då är r8['sked'] redan rätt
        A = np.array(r8['sked_R']); sked = sked - A @ off_gammal + A @ np.array(sk['offset_m'])
    # kunden vid kameran, utanför bild
    kam = np.array(plan['renderkamera']['nycklar'][mitt]['matris'])[:3]; kpos = kam[:, 3]; blick = -kam[:, 2]; hoger = kam[:, 0]
    bas = kpos[:2] + .05 * blick[:2] / np.linalg.norm(blick[:2]) - .35 * hoger[:2] / np.linalg.norm(hoger[:2])
    kyaw = math.atan2(blick[1], blick[0]) - math.pi / 2
    ks = (H['h8'][0], H['h8'][1] + 1) if LJUS else (0, 156)   # 0027: kunden finns där hen finns i originalets bild (h8); kameran åker annars genom hen
    plan['objekt'] += [lada('kund:kropp', [*bas, golv + .85], [.42, .26, 1.0], kyaw, '#7d8fa6', 'antagen (kunden, utanför bild)', synlig=ks),
                       lada('kund:ben', [*bas, golv + .40], [.36, .22, .80], kyaw, '#4a5566', 'antagen (kunden, utanför bild)', synlig=ks),
                       dict(lada('kund:huvud', [*bas, golv + 1.50], [.20, .20, .24], kyaw, '#d9b8a0', 'antagen (kunden, utanför bild)', synlig=ks), typ='cylinder')]
    axel = np.array([*(bas + .22 * hoger[:2] / np.linalg.norm(hoger[:2])), golv + 1.30]); v = sked - axel; lang = float(np.linalg.norm(v))
    yaw = math.atan2(v[1], v[0]); pitch = -math.asin(v[2] / lang)
    plan['objekt'].append(lada('kund:arm', list((axel + sked) / 2), [lang, .09, .09], yaw, '#e0a882' if LJUS else '#d9b8a0', 'antagen (kundens arm möter skeden i h8)', synlig=(H['h8'][0], H['h8'][1] + 1), roll=(0., pitch)))
    plan.setdefault('beslut', []).append('0026: disken flyttad efter tråget som villkor, tråg, bakre bänk och antagen kund (gennedbrytning/s_scen.py, kopia av planen).')
    UT.mkdir(exist_ok=True); (UT / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
    rap = dict(disk=dict(fore_pos_m=c0.round(3).tolist(), efter_pos_m=[*np.round(c[:2], 3).tolist(), round(float(c0[2]), 3)], flytt_mot_henne_m=round(float(s), 3),
                         kallor_flytt_mot_henne_m=kallor, valt='tråget som villkor: minsta flytt som lägger fingertoppens lägsta punkt (h3–h4) minst 0,10 m innanför bakkanten',
                         fingertopp_lagst=dict(plan_ruta=rr[lag]['ruta'], z_m=round(top_lag, 3), djup_fore_flytt_m=round(float(y_lag), 3)),
                         bakkant_hojd_m=round(bak_h, 3), trag=dict(djup_m=round(djup, 3), status=djup_status, under_ovankanten=bool(top_lag < Hh))),
               bank_bak=dict(pos_m=[round(float(x), 3) for x in bank_c], status='antagen'),
               kund=dict(bas_xy=[round(float(x), 3) for x in bas], arm_langd_m=round(lang, 2), sked_h8=[round(float(x), 3) for x in sked], status='antagen i sin helhet'))
    (UT / 'scen.json').write_text(json.dumps(rap, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(rap, ensure_ascii=False, indent=1))
    if '--bygg' in sys.argv:
        with open(UT / 'blender.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', '--factory-startup', '-t', '8', '--python-exit-code', '1', '--python', str(ING / 'mhr_rig.py'), '--',
                            str(S1), plan['kallvideo'], '--plan', str(UT / 'plan.json'), '--ut', str(UT), '--tillat-flaggad'], cwd=ROT, stdout=f, stderr=subprocess.STDOUT, check=True)
        if '--glas' in sys.argv:   # 0028: montrens front som glas (antagen), efter bygget, före renderingen
            with open(UT / 'glas.log', 'w', encoding='utf-8') as f:
                subprocess.run([BLENDER, '-b', str(UT / 'scen.blend'), '--factory-startup', '--python-exit-code', '1', '--python', str(HIT / 's_glas_blender.py'), '--', _arg('--glas', 'disk_A:fram')],
                               cwd=ROT, stdout=f, stderr=subprocess.STDOUT, check=True)
        (UT / 'render').mkdir(exist_ok=True)
        with open(UT / 'render.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', str(UT / 'scen.blend'), '-o', str(UT / 'render' / 'f####'), '-F', 'PNG', '-s', '0', '-e', '155', '-a'], cwd=ROT, stdout=f, stderr=subprocess.STDOUT, check=True)


if __name__ == '__main__': main()
