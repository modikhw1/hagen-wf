"""0024 punkt 4: handlingsspåret för en tagning (gelato S1). Gränserna kommer ur mätning, namnen ur en modell som ser klippet.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/l_handling.py [--gemini google/gemini-2.5-pro]
Ordning (som uppdraget):
1. Mätta signaler per klippruta (klippets ruta k = planens ruta k+7):
   - bålens lutning framåt ur läsningen av k2 (d_video/k2/kontroll.json), utjämnad
   - fingertoppens läge i diskens ram med fötterna låsta (samspel/k2_samspel_last.json): bakom, över eller framför disken, höjd, djup
   - handledens vändpunkter och närmaste ruta (nyckel/handledsbana.json, ur dagens läsning)
   - kamerans skala och förskjutning per ruta (kamerafri/avbildning.json): skala < 1 och fallande = zoomar in; förskjutning i y växer = tippar ned
   - kundens hand i bild: ingestens maskdelar som kommer in från bildkanten (samma fil), luckor upp till 12 rutor fyllda, kluster med minst tre träffar
2. Segment = sträckor där tillståndet (hållning, handläge, handens rörelseriktning) är detsamma. Korta sträckor (< 6 rutor) slås ihop med grannen.
   Kameran per segment ur skalans och förskjutningens förändring.
3. Handföremålet ur planen (plan.handforemal).
4. Gemini får klippet, segmentgränserna och de mätta fälten som givna, och fyller bara handling (verb ur ORD), kroppsdel, mål, kontakt
   och en kort beskrivning per segment. Svaret märks 'last'. Prompten sparas bredvid.
--utan-hand: modellen får inte handläget och handens rörelse, bara gränser, hållning, kundens hand och kamera.
Ut: handling/S1/handling.json, handling/S1/remsa.mp4 (originalet med segmenten som textremsa), handling/S1/remsa.jpg, gemini.json, prompt.txt.
Ordförrådet är litet och allmänt, inte skrivet för glass.
"""
import argparse, base64, json, os, urllib.request
from pathlib import Path
import cv2, numpy as np
from scipy.signal import savgol_filter

HIT = Path(__file__).resolve().parent; UT = HIT / 'handling/S1'; KLIPP = HIT / 'luma-agaren/1_kalla_gelato_S1.mp4'
PLAN = HIT.parent / 'kontrakt/ut/kand-kennysgelato_n06-hand/narvaro/plan.json'; FPS = 29.97; OFFS = 7
ORD = ['sta', 'ga', 'luta_sig', 'rata_pa_sig', 'vanda_sig', 'titta', 'peka', 'ta', 'halla', 'lyfta', 'sanka', 'racka']
HALLNING = ['upprat', 'lutar_sig', 'rater_pa_sig', 'lutar_sig_framat_lite']
GATEWAY = 'https://ai-gateway.vercel.sh/v1/chat/completions'


def signaler():
    lut = np.array([x[1] if x[1] is not None else np.nan for x in json.loads((HIT / 'd_video/k2/kontroll.json').read_text(encoding='utf-8'))['lutning_per_ruta']])
    ok = ~np.isnan(lut); x = np.arange(len(lut)); lut = savgol_filter(np.interp(x, x[ok], lut[ok]), 9, 2)
    sp = json.loads((HIT / 'samspel/k2_samspel_last.json').read_text(encoding='utf-8'))['rutor']
    n = len(lut); hand = [sp[i + OFFS]['hand'] for i in range(n)]; ft = np.array([sp[i + OFFS]['fingertopp_lok'] for i in range(n)])
    ft = np.stack([savgol_filter(ft[:, j], 9, 2) for j in range(3)], 1)
    avb = json.loads((HIT / 'kamerafri/avbildning.json').read_text(encoding='utf-8'))['rutor']
    sk = np.array([a['skala'] for a in avb]); ty = np.array([a['forskjutning'][1] for a in avb])
    # kundens hand: maskdelar som kommer in från bildkanten (kamerafri/avbildning.json), luckor upp till 12 rutor fylls, kluster med färre än tre träffar stryks
    kh = set(json.loads((HIT / 'kamerafri/avbildning.json').read_text(encoding='utf-8'))['kanthand_borttagen_rutor']); kund = np.zeros(n, bool)
    kl = []
    for i in sorted(kh):
        if kl and i - kl[-1][-1] <= 12: kl[-1].append(i)
        else: kl.append([i])
    for k in kl:
        if len(k) >= 3: kund[k[0]:k[-1] + 1] = True    # minst tre träffar per kluster
    return dict(n=n, lut=lut, hand=hand, ft=ft, sk=sk, ty=ty, kund=kund)


def tillstand(S, i):
    l = S['lut'][i]; dl = S['lut'][min(i + 3, S['n'] - 1)] - S['lut'][max(i - 3, 0)]
    if dl > 6: h = 'lutar_sig'                 # lutningen ökar
    elif dl < -6: h = 'rater_pa_sig'           # lutningen minskar
    elif l > 45: h = 'lutar_sig'               # böjd och stilla
    else: h = 'upprat'
    dz = S['ft'][min(i + 3, S['n'] - 1), 2] - S['ft'][max(i - 3, 0), 2]; dy = S['ft'][min(i + 3, S['n'] - 1), 1] - S['ft'][max(i - 3, 0), 1]
    rorelse = 'mot_kameran' if dy < -0.04 else ('upp' if dz > 0.05 else ('ned' if dz < -0.05 else 'stilla'))
    return h, S['hand'][i], rorelse, bool(S['kund'][i])


def segmentera(S):
    st = [tillstand(S, i) for i in range(S['n'])]; seg = []
    for i, s in enumerate(st):
        if seg and seg[-1]['t'] == s: seg[-1]['b'] = i
        else: seg.append(dict(t=s, a=i, b=i))
    # korta sträckor slås ihop med föregående (eller nästa för den första)
    andrat = True
    while andrat:
        andrat = False
        for j, s in enumerate(seg):
            if s['b'] - s['a'] + 1 < 6 and len(seg) > 1:
                k = j - 1 if j > 0 else j + 1; seg[k]['a'] = min(seg[k]['a'], s['a']); seg[k]['b'] = max(seg[k]['b'], s['b']); seg.pop(j); andrat = True; break
    # grannar med samma tillstånd efter sammanslagning
    ut = []
    for s in seg:
        if ut and ut[-1]['t'] == s['t']: ut[-1]['b'] = s['b']
        else: ut.append(s)
    return ut


def kamera(S, a, b):
    ds = np.log(S['sk'][b] / S['sk'][a]); dt = S['ty'][b] - S['ty'][a]; r = []
    if ds < -0.08: r.append('zoomar_in')
    elif ds > 0.08: r.append('zoomar_ut')
    if dt > 60: r.append('tippar_ned')
    elif dt < -60: r.append('tippar_upp')
    return r or ['stilla']


def gemini(modell, seg, foremal, utan_hand=False):
    # utan_hand: modellen får inte handläget mot disken eller handens rörelse (de mätningarna kan vara fel där kroppen står fel i rummet)
    hand = lambda s: '' if utan_hand else f"hand={s['hand_mot_mobel']['varde']}, hand_motion={s['handens_rorelse']['varde']}, "
    rader = '\n'.join(f"{s['id']}: frames {s['rutor_klipp'][0]}-{s['rutor_klipp'][1]} ({s['tid_s'][0]:.2f}-{s['tid_s'][1]:.2f} s); measured: posture={s['hallning']['varde']}, "
                      f"{hand(s)}customer_hand_visible={s['kundens_hand_syns']['varde']}, camera={'+'.join(s['kamera']['varde'])}" for s in seg)
    text = f"""You watch a 5-second vertical video clip (one shot, {FPS} fps, 148 frames) of a person at a shop counter.
The segment boundaries below come from measurement and are fixed. Do not move, merge or split them. The measured fields are given facts.
Your only job is to name what happens in each segment, in a small, general vocabulary that works for any clip.

Known objects (from the scene plan): person "A" (the server), furniture "disk_A" (the display counter in front of her), hand object "{foremal}" (a small tasting spoon in her right hand), "kamera" (the camera, i.e. the viewer), "kund" (an off-screen customer whose hand may appear).

Segments:
{rader}

For each segment answer:
- handling: exactly one verb from {ORD}
- kroppsdel: the body part doing it (e.g. "hogra_armen", "overkroppen", "huvudet", "hela_kroppen")
- foremal: "{foremal}" if she holds or uses it in this segment, else null
- mal: what the action is directed at: "disk_A", "kamera", "kund", or null
- kontakt: what touches what, as "a>b" (e.g. "{foremal}>glass_i_traget", "hand>{foremal}"), or null
- beskrivning: one short English sentence of what happens, without guessing beyond what is visible
- sakerhet: 0-1
Answer with JSON only: {{"segment": [{{"id": ..., "handling": ..., "kroppsdel": ..., "foremal": ..., "mal": ..., "kontakt": ..., "beskrivning": ..., "sakerhet": ...}}]}}"""
    k = os.environ.get('AI_GATEWAY_API_KEY') or Path(os.environ['AI_GATEWAY_NYCKELFIL']).read_text(encoding='utf-8').splitlines()[0].strip()
    body = dict(model=modell, max_tokens=8000, response_format=dict(type='json_object'), messages=[dict(role='user', content=[dict(type='text', text=text),
                dict(type='file', file=dict(file_data='data:video/mp4;base64,' + base64.b64encode(KLIPP.read_bytes()).decode(), filename=KLIPP.name))])])
    req = urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=600)); svar = d['choices'][0]['message']['content']
    (UT / 'prompt.txt').write_text(text, encoding='utf-8')
    (UT / 'gemini.json').write_text(json.dumps(dict(modell=modell, usage=d.get('usage'), svar=svar), ensure_ascii=False, indent=1), encoding='utf-8')
    t = svar.strip().removeprefix('```json').removesuffix('```')
    return json.loads(t), (d.get('usage') or {}).get('cost')


def remsa(H):
    from PIL import Image, ImageDraw, ImageFont
    cap = cv2.VideoCapture(str(KLIPP)); W, Hh = 540, 960; R = 300
    vw = cv2.VideoWriter(str(UT / 'remsa.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W, Hh + R))
    try: fnt = ImageFont.truetype('arial.ttf', 19); fs = ImageFont.truetype('arial.ttf', 15)
    except OSError: fnt = fs = ImageFont.load_default()
    farg = [(230, 159, 0), (86, 180, 233), (0, 158, 115), (240, 228, 66), (0, 114, 178), (213, 94, 0), (204, 121, 167), (120, 120, 120)]
    seg = H['segment']; n = H['rutor_klipp']; bilder = []; i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        im = Image.new('RGB', (W, Hh + R), (20, 20, 20)); im.paste(Image.fromarray(cv2.cvtColor(cv2.resize(f, (W, Hh)), cv2.COLOR_BGR2RGB)), (0, 0))
        dr = ImageDraw.Draw(im)
        for j, s in enumerate(seg):
            a, b = s['rutor_klipp']; dr.rectangle([a * W / n, Hh + 6, (b + 1) * W / n, Hh + 30], fill=farg[j % len(farg)])
            dr.text((a * W / n + 3, Hh + 9), s['id'], font=fs, fill=(0, 0, 0))
        dr.line([i * W / n, Hh + 2, i * W / n, Hh + 34], fill=(255, 255, 255), width=3)
        s = next(x for x in seg if x['rutor_klipp'][0] <= i <= x['rutor_klipp'][1])
        rad = [f"{s['id']}  rutor {s['rutor_klipp'][0]}-{s['rutor_klipp'][1]}  (ruta {i})",
               f"handling: {s['handling']['varde']}  [{s['handling']['kalla']}]",
               f"kroppsdel: {s['kroppsdel']['varde']}   hållning: {s['hallning']['varde']}",
               f"föremål: {s['foremal']['varde']}   mål: {s['mal']['varde']}",
               f"kontakt: {s['kontakt']['varde']}",
               f"hand mot disk: {s['hand_mot_mobel']['varde']}  kund: {'ja' if s['kundens_hand_syns']['varde'] else 'nej'}  kamera: {'+'.join(s['kamera']['varde'])}",
               (s.get('beskrivning') or {}).get('varde') or '']
        y = Hh + 42
        for t in rad:
            for k in range(0, len(t), 52): dr.text((8, y), t[k:k + 52], font=fnt, fill=(235, 235, 235)); y += 24
        fr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR); vw.write(fr)
        if any(i == (x['rutor_klipp'][0] + x['rutor_klipp'][1]) // 2 for x in seg): bilder.append(cv2.resize(fr, (270, 630)))
        i += 1
    vw.release(); cv2.imwrite(str(UT / 'remsa.jpg'), np.hstack(bilder))


def main():
    a = argparse.ArgumentParser(); a.add_argument('--gemini'); a.add_argument('--utan-hand', action='store_true'); x = a.parse_args(); UT.mkdir(parents=True, exist_ok=True)
    S = signaler(); seg = segmentera(S); plan = json.loads(PLAN.read_text(encoding='utf-8'))
    hf = next(h for h in plan['handforemal'] if h['scen'] == 's1'); fid = hf['id']
    H = dict(tagning='S1', klipp='kand-kennysgelato', scen='s1', rutor_klipp=S['n'], ruta_plan_minus_klipp=OFFS, fps=FPS,
             ordforrad=ORD, kalla_forklaring=dict(matt='ur läsningen eller kameran', last='ur en modell som såg klippet', antagen='antagande utan mätning eller seende'),
             signaler=dict(lutning='d_video/k2/kontroll.json (k2, utjämnad)', hand='samspel/k2_samspel_last.json (fötterna låsta: antagen)',
                           kamera='kamerafri/avbildning.json', foremal=str(PLAN.relative_to(HIT.parent))), segment=[])
    for j, s in enumerate(seg):
        a_, b_ = s['a'], s['b']; h, hand, rorelse, kund = s['t']
        H['segment'].append(dict(id=f'h{j + 1}', vem='A', rutor_klipp=[a_, b_], rutor_plan=[a_ + OFFS, b_ + OFFS], tid_s=[round(a_ / FPS, 2), round((b_ + 1) / FPS, 2)],
                                 hallning=dict(varde=h, kalla='matt'), hand_mot_mobel=dict(varde=hand, mobel='disk_A', kalla='matt'),
                                 handens_rorelse=dict(varde=rorelse, kalla='matt'), kundens_hand_syns=dict(varde=kund, kalla='matt'), kamera=dict(varde=kamera(S, a_, b_), kalla='matt'),
                                 lutning_grader=[round(float(S['lut'][a_]), 1), round(float(S['lut'][b_]), 1)],
                                 handling=dict(varde=None, kalla=None), kroppsdel=dict(varde=None, kalla=None),
                                 foremal=dict(varde=fid if hf['synlig_ut'][0] <= a_ + OFFS <= hf['synlig_ut'][1] else None, kalla='matt'),
                                 mal=dict(varde=None, kalla=None), kontakt=dict(varde=None, kalla=None)))
    if x.gemini:
        g, kostnad = gemini(x.gemini, H['segment'], fid, x.utan_hand); H['gemini'] = dict(modell=x.gemini, kostnad_usd=kostnad, fick_handlaget=not x.utan_hand)
        for s, gs in zip(H['segment'], sorted(g['segment'], key=lambda q: int(str(q['id']).lstrip('h')))):
            for f in ('handling', 'kroppsdel', 'mal', 'kontakt'): s[f] = dict(varde=gs.get(f), kalla='last')
            if gs.get('foremal') != s['foremal']['varde']: s['foremal']['modellen_sager'] = gs.get('foremal')
            s['beskrivning'] = dict(varde=gs.get('beskrivning'), kalla='last', sakerhet=gs.get('sakerhet'))
            if s['handling']['varde'] not in ORD: s['handling']['utanfor_ordforradet'] = True
    (UT / 'handling.json').write_text(json.dumps(H, ensure_ascii=False, indent=1), encoding='utf-8')
    for s in H['segment']: print(s['id'], s['rutor_klipp'], s['hallning']['varde'], s['hand_mot_mobel']['varde'], s['handens_rorelse']['varde'], s['kundens_hand_syns']['varde'], s['kamera']['varde'], s['handling']['varde'], s['mal']['varde'])
    remsa(H)


if __name__ == '__main__': main()
