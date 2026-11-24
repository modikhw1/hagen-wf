"""0026 punkt 4: bär scenen meningen? Handlingsspårets påståenden h1–h9 prövade mot scenens geometri, och filmen med remsan.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/v_mening.py
Kroppen: samspel/dreamina.json (leder i världen per planruta ur den byggda scenen, samma kropp som i s_scen). Disken, tråget och kundens
arm: s_scen/plan.json. Per segment prövas det spåret påstår, med mått:
  hållning (bålens lutning ändras som påstått), hand i tråget (fingertoppen innanför trågets yta och under ovankanten), hand över diskens
  kant (fingertoppen förbi bakkanten och över ovankanten), kontakt sked–kundens hand (avstånd mellan skeden och kundarmens ände).
Utfall per segment: sant (påståendet håller i minst 70 % av rutorna), nästan (30–70 %), falskt (< 30 %). Trösklar är diagnos.
Ut: s_scen/mening.json, s_scen/film.mp4 (original | scen, remsa under), s_scen/film_rutor.jpg.
"""
import json, math
from pathlib import Path
import cv2, numpy as np

import sys
HIT = Path(__file__).resolve().parent
sys.path.insert(0, str(HIT)); from tagning import OFFS, HANDLING, T as KONF   # 0030
def _arg(n, f): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else f
UT = HIT / _arg('--ut', 's_scen'); SP = HIT / _arg('--samspel', 'samspel/dreamina.json'); FILM = HIT / _arg('--film', str(Path(_arg('--ut', 's_scen')) / 'film.mp4'))


def main():
    plan = json.loads((UT / 'plan.json').read_text(encoding='utf-8')); sp = {r['ruta']: r for r in json.loads(SP.read_text())['rutor']}
    HJ = json.loads(HANDLING.read_text(encoding='utf-8')); seg = HJ['segment']
    ob = {o['id']: o for o in plan['objekt']}; bas, fram, bak = ob['disk_A'], ob['disk_A:fram'], ob['disk_A:bak']
    th = bas['rotation_rad'][2]; ex, ey = np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)]); c = np.array(bas['pos_m'][:2])
    L, D = bas['matt_m'][0], bas['matt_m'][1]; top = fram['pos_m'][2] + fram['matt_m'][2] / 2; tragg = bas['pos_m'][2] + bas['matt_m'][2] / 2
    lok = lambda p: np.array([(np.array(p[:2]) - c) @ ex, (np.array(p[:2]) - c) @ ey, p[2]])
    arm = ob['kund:arm']; ap = np.array(arm['pos_m']); al = arm['matt_m'][0]; ay, apt = arm['rotation_rad'][2], arm['rotation_rad'][1]
    arm_slut = ap + al / 2 * np.array([math.cos(apt) * math.cos(ay), math.cos(apt) * math.sin(ay), -math.sin(apt)])
    def lut(r):
        le = r['leder']; v = np.array(le['c_neck']['huvud']) - np.array(le['root']['huvud']); return math.degrees(math.atan2(math.hypot(v[0], v[1]), v[2]))
    def i_trag(r):
        f = lok(r['leder']['r_middle3']['svans']); return abs(f[0]) < L / 2 and -D / 2 + .20 < f[1] < D / 2 - .05 and f[2] < top
    def over_kant(r):
        f = lok(r['leder']['r_middle3']['svans']); return f[1] < D / 2 and f[2] > top
    def kontakt(r):
        s = np.array(r['sked'] or r['leder']['r_middle3']['svans']); return float(np.linalg.norm(s - arm_slut)) < .12
    PROV = {'luta_sig': ('bålen lutar sig (lutningen ökar eller är > 35°)', lambda rr, i: lut(rr[i]) > 35 or (i > 0 and lut(rr[i]) > lut(rr[i - 1]))),
            'ta': ('handen i tråget', lambda rr, i: i_trag(rr[i])),
            'rata_pa_sig': ('bålen rätar på sig (lutningen minskar)', lambda rr, i: i > 0 and lut(rr[i]) < lut(rr[i - 1]) + .2),
            'sta': ('står upprätt (lutning < 30°)', lambda rr, i: lut(rr[i]) < 30),
            'racka': ('handen över diskens kant', lambda rr, i: over_kant(rr[i])),
            'halla': ('handen över diskens kant', lambda rr, i: over_kant(rr[i]))}
    rader = []
    for s in seg:
        a, b = s['rutor_plan']; rr = [sp[u] for u in range(a, b + 1) if u in sp]; h = s['handling']['varde']; vad, f = PROV.get(h, ('—', lambda rr, i: True))
        andel = float(np.mean([f(rr, i) for i in range(len(rr))])); post = dict(id=s['id'], handling=h, prov=vad, andel=round(andel, 2))
        if (s.get('kontakt') or {}).get('varde') and 'kund' in str(s['kontakt']['varde']):
            k = float(np.mean([kontakt(r) for r in rr])); post['kontakt_sked_kundhand_andel'] = round(k, 2); andel = min(andel, k) if k < andel else andel
        if s['id'] == 'h3': post['handen_i_traget_rutor'] = [u for u in range(a, b + 1) if u in sp and i_trag(sp[u])][:6]
        post['utfall'] = 'sant' if andel >= .7 else ('nästan' if andel >= .3 else 'falskt'); rader.append(post)
    # 0027: kroppens storlek och läge i bild mot originalet per segment, och avståndet hand–sked per ruta
    import r_rot
    nk = plan['renderkamera']['nycklar']; per = {}
    for u in sp:
        m = r_rot.mal2d(u)
        if m is None or m[1].sum() < 3: continue
        q, s_ = m; K = np.array(nk[u]['matris']); P = np.array([sp[u]['leder'][j]['huvud'] for j in r_rot.OVER]); pp = r_rot.proj(P, K[:3, :3], K[:3, 3], nk[u]['lins_mm'])
        bw = lambda x: np.linalg.norm(x[2] - x[3]); per[u] = (float(np.median(np.linalg.norm(pp[s_] - q[s_], axis=1)) / 1920 * 1000), bw(pp) / max(bw(q), 1e-6))
    hs = {u: round(float(np.linalg.norm(np.array(sp[u]['sked']) - np.array(sp[u]['leder']['r_middle3']['svans']))), 3) for u in sp if sp[u].get('sked')}
    for r in rader:
        a, b = next(s['rutor_plan'] for s in seg if s['id'] == r['id']); x = [per[u] for u in range(a, b + 1) if u in per]
        if x: r['lage_i_bild_promille'] = round(float(np.median([y[0] for y in x])), 1); r['storlek_mot_original'] = round(float(np.median([y[1] for y in x])), 2)
        hx = [hs[u] for u in range(a, b + 1) if u in hs]
        if hx: r['sked_till_fingertopp_m'] = round(float(np.median(hx)), 3)
    (UT / 'mening.json').write_text(json.dumps(dict(trag_ovankant_m=round(top, 3), traggolv_m=round(tragg, 3), segment=rader, sked_till_fingertopp_per_ruta=hs), ensure_ascii=False, indent=1), encoding='utf-8')
    for r in rader: print(r)
    # film: original | scen, med remsan
    from PIL import Image, ImageDraw, ImageFont
    cap = cv2.VideoCapture(plan['kallvideo']); w, hh, R = 405, 720, 150
    try: fnt = ImageFont.truetype('arial.ttf', 17)
    except OSError: fnt = ImageFont.load_default()
    vw = cv2.VideoWriter(str(FILM), cv2.VideoWriter_fourcc(*'mp4v'), 29.97, (2 * w, hh + R)); bilder = []
    farg = [(230, 159, 0), (86, 180, 233), (0, 158, 115), (240, 228, 66), (0, 114, 178), (213, 94, 0), (204, 121, 167), (120, 120, 120), (180, 60, 60)]
    for u in range(0, 156):
        cap.set(cv2.CAP_PROP_POS_FRAMES, plan['kallrutor'][u]); ok, o = cap.read()
        im = cv2.imread(str(UT / 'render' / f'f{u:04d}.png'), cv2.IMREAD_UNCHANGED)
        if im is None: im = np.full((1920, 1080, 3), 128, np.uint8)
        elif im.shape[2] == 4: al_ = im[..., 3:4] / 255.; im = (im[..., :3] * al_ + 128 * (1 - al_)).astype(np.uint8)
        top_ = np.hstack([cv2.resize(o, (w, hh)), cv2.resize(im, (w, hh))])
        P = Image.new('RGB', (2 * w, hh + R), (20, 20, 20)); P.paste(Image.fromarray(cv2.cvtColor(top_, cv2.COLOR_BGR2RGB)), (0, 0)); dr = ImageDraw.Draw(P)
        k = u - OFFS
        for j, s in enumerate(seg):
            a, b = s['rutor_klipp']; dr.rectangle([a * 2 * w / 148, hh + 6, (b + 1) * 2 * w / 148, hh + 28], fill=farg[j % len(farg)]); dr.text((a * 2 * w / 148 + 3, hh + 8), s['id'], font=fnt, fill=(0, 0, 0))
        if 0 <= k < 148:
            dr.line([k * 2 * w / 148, hh + 2, k * 2 * w / 148, hh + 32], fill=(255, 255, 255), width=3)
            s = next(x for x in seg if x['rutor_klipp'][0] <= k <= x['rutor_klipp'][1]); m = next(x for x in rader if x['id'] == s['id'])
            for t_, y in ((f"{s['id']}  {s['handling']['varde']}  mål: {s['mal']['varde']}  föremål: {s['foremal']['varde']}", hh + 40),
                          (f"kontakt: {s['kontakt']['varde']}   kamera: {'+'.join(s['kamera']['varde'])}", hh + 64),
                          (f"i scenen: {m['prov']}: {m['utfall']} ({m['andel']})", hh + 88), (f"planruta {u}, klippruta {k}", hh + 112)):
                dr.text((8, y), t_, font=fnt, fill=(235, 235, 235))
        fr = cv2.cvtColor(np.array(P), cv2.COLOR_RGB2BGR); vw.write(fr)
        if u in (20, 45, 70, 100, 125, 150): bilder.append(cv2.resize(fr, (405, 435)))
    vw.release(); cv2.imwrite(str(FILM.with_name(FILM.stem + '_rutor.jpg')), np.hstack(bilder))


if __name__ == '__main__': main()
