"""0030: handlingsspåret för valfri tagning i valfritt klipp, ur ingestens läsning. Allmän version av l_handling.py (som var skrivet för gelato S1).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/m_handling.py <kalla.json> <scen> [--gemini google/gemini-2.5-flash] [--ut handling/<klipp>]
Gränserna kommer ur mätning, namnen ur en modell som ser tagningen. Indata ur källan: scenens personer och deras sekvenser
(matning.personer[].rorelse), scenens kamera (varld.npz), tidsbasen och tagningens video (ingestens klipp/S<n>.mp4).
1. Mätta signaler per ruta och person, i världen (kam_R · F · modellrum, upp ur varld.npz):
   - bålens lutning (rot -> nacke mot upp), utjämnad
   - sitter: låret (höft -> knä) mer än 55° från lodrätt i båda benen
   - handens läge mot kroppen (den hand som är högst eller längst fram): nere, midja, brost, uppe, framme (> 0,35 m framför bålen)
   - handens rörelse: upp, ned, mot_kameran, stilla (förändring över ±3 rutor)
   - huvudet: sankt (nacke -> huvud lutar > 25° mer framåt än bålen) eller rakt
   - kameran: vridningens förändring över segmentet (tippar, panorerar) eller stilla
2. Segment per person = sträckor med samma tillstånd (hållning, handläge, rörelse, huvud). Korta sträckor (< 6 rutor) slås ihop.
3. Modellen (Flash) får tagningen, segmenten och de mätta fälten som givna och fyller handling (ett verb ur ORD), kroppsdel, föremål,
   mål, blick (vart personen tittar) och kontakt. Svaret märks last. Ett verb utanför ordförrådet märks, och läggs inte till tyst.
Ut: <ut>/<scen>/handling.json (samma form som gelatos), prompt.txt, gemini.json.
Ordförrådet: gelatos tolv verb plus tala (0030: b-tilltal är tal) och sitta (0030: guacamole sitter). Blick och i_handen (vad händerna bär) är egna fält (0030).
"""
import argparse, base64, json, os, urllib.request
from pathlib import Path
import numpy as np
from scipy.signal import savgol_filter

HIT = Path(__file__).resolve().parent; ING = HIT.parent / 'ingest'
N = json.loads((ING / 'mhr_ledernamn.json').read_text()); F = np.diag([1., -1., -1.])
ORD = ['sta', 'ga', 'sitta', 'luta_sig', 'rata_pa_sig', 'vanda_sig', 'titta', 'peka', 'tala', 'ta', 'halla', 'lyfta', 'sanka', 'racka']
NYA_ORD = {'tala': 'b-tilltal: personerna talar och gissar; inget av de tolv verben säger det', 'sitta': 'guacamole: mannen sitter; hållningen behöver ett verb'}
GATEWAY = 'https://ai-gateway.vercel.sh/v1/chat/completions'
ix = N.index


def signaler(seq, V):
    z = np.load(seq); P = z['pose'][..., :3] / 100.; n = len(P); inom = z['inom'].astype(bool)
    up = V['upp'] / np.linalg.norm(V['upp'])
    W = lambda v, f: V['kam_R'][f] @ F @ v
    lut, sitt, hand, hojd, fram, huvud, wp = [], [], [], [], [], [], []
    for f in range(n):
        p = P[f]; spine = W(p[ix('c_neck')] - p[ix('root')], f); sn = spine / np.linalg.norm(spine)
        lut.append(np.degrees(np.arccos(np.clip(sn @ up, -1, 1))))
        lar = [W(p[ix(k)] - p[ix(h)], f) for h, k in (('l_upleg', 'l_lowleg'), ('r_upleg', 'r_lowleg'))]
        sitt.append(all(np.degrees(np.arccos(abs(v @ up) / np.linalg.norm(v))) > 55 for v in lar))
        hd = W(p[ix('c_head')] - p[ix('c_neck')], f); hn = hd / np.linalg.norm(hd)
        huvud.append(np.degrees(np.arccos(np.clip(hn @ up, -1, 1))) - lut[-1])
        root = W(p[ix('root')], f); bal_fram = sn - (sn @ up) * up
        horis = np.cross(up, W(p[ix('l_upleg')] - p[ix('r_upleg')], f)); horis = horis / (np.linalg.norm(horis) + 1e-9)   # bålens framåt i golvplanet
        bast = None
        for w in ('l_wrist', 'r_wrist'):
            q = W(p[ix(w)], f) - root; h = q @ up; fr = q @ horis
            if bast is None or h + fr > bast[0] + bast[1]: bast = (h, fr, W(p[ix(w)], f))
        h, fr, pw = bast; hojd.append(h); fram.append(fr); wp.append(pw)
    sm = lambda a: savgol_filter(np.asarray(a, float), min(9, n - (1 - n % 2)), 2) if n >= 5 else np.asarray(a, float)
    return dict(n=n, inom=inom, lut=sm(lut), sitt=np.array(sitt), hojd=sm(hojd), fram=sm(fram), huvud=sm(huvud), wp=np.array(wp), kam_R=V['kam_R'][:n], kam_C=V['kam_C'][:n])


def tillstand(S, i):
    n = S['n']; a, b = max(i - 3, 0), min(i + 3, n - 1); l = S['lut'][i]; dl = S['lut'][b] - S['lut'][a]
    if S['sitt'][i]: h = 'sitter'
    elif dl > 6: h = 'lutar_sig'
    elif dl < -6: h = 'rater_pa_sig'
    elif l > 35: h = 'lutar_sig'
    else: h = 'upprat'
    hj, fr = S['hojd'][i], S['fram'][i]
    lage = 'framme' if fr > .35 else ('uppe' if hj > .55 else ('brost' if hj > .25 else ('midja' if hj > -.05 else 'nere')))
    d = S['wp'][b] - S['wp'][a]; kam = S['kam_C'][i]; mot = (S['wp'][i] - kam); mot = mot / (np.linalg.norm(mot) + 1e-9)
    rorelse = 'mot_kameran' if d @ -mot > .06 else ('upp' if S['hojd'][b] - S['hojd'][a] > .06 else ('ned' if S['hojd'][b] - S['hojd'][a] < -.06 else 'stilla'))
    huvud = 'sankt' if S['huvud'][i] > 25 else 'rakt'
    return h, lage, rorelse, huvud


def segmentera(S):
    st = [tillstand(S, i) if S['inom'][i] else ('utanfor_bild',) * 4 for i in range(S['n'])]; seg = []
    for i, s in enumerate(st):
        if seg and seg[-1]['t'] == s: seg[-1]['b'] = i
        else: seg.append(dict(t=s, a=i, b=i))
    while len(seg) > 1:
        j = next((j for j, s in enumerate(seg) if s['b'] - s['a'] + 1 < 6), None)
        if j is None: break
        k = j - 1 if j > 0 else j + 1; seg[k]['a'] = min(seg[k]['a'], seg[j]['a']); seg[k]['b'] = max(seg[k]['b'], seg[j]['b']); seg.pop(j)
        ut = []
        for s in seg:
            if ut and ut[-1]['t'] == s['t']: ut[-1]['b'] = s['b']
            else: ut.append(s)
        seg = ut
    return seg


def kamera(S, a, b):
    R = S['kam_R'][b] @ S['kam_R'][a].T; ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
    if ang < 4: return ['stilla']
    fa, fb = S['kam_R'][a][:, 2], S['kam_R'][b][:, 2]; dp = np.degrees(np.arcsin(np.clip(fb[1], -1, 1)) - np.arcsin(np.clip(fa[1], -1, 1)))
    return ['tippar_ned' if dp > 0 else 'tippar_upp'] if abs(dp) > ang * .6 else ['panorerar']


def gemini(modell, video, seg, kand, nkalla, fps, ut):
    rader = '\n'.join(f"{s['id']} ({s['vem']}): frames {s['rutor_tagning'][0]}-{s['rutor_tagning'][1]} ({s['tid_tagning_s'][0]:.2f}-{s['tid_tagning_s'][1]:.2f} s); measured: posture={s['hallning']['varde']}, "
                      f"hand={s['handens_lage']['varde']}, hand_motion={s['handens_rorelse']['varde']}, head={s['huvud']['varde']}, camera={'+'.join(s['kamera']['varde'])}" for s in seg)
    text = f"""You watch one shot of a vertical video ({fps:.2f} fps, {nkalla} frames).
The segment boundaries below come from measurement and are fixed. Do not move, merge or split them. The measured fields are given facts.
Your only job is to name what happens in each segment, in a small, general vocabulary that works for any clip.

Known in the scene: {kand}

Segments:
{rader}

For each segment answer:
- handling: exactly one verb from {ORD}. If none fits, give the closest and add "utanfor": "<your verb>".
- kroppsdel: the body part doing it (e.g. "hogra_armen", "overkroppen", "huvudet", "hela_kroppen", "munnen")
- foremal: the object held or used (an id from the known list, or a short English noun), else null
- i_handen: what the person's hands hold or carry in this segment, as a short English noun per hand ("right: phone, left: null"), or null if empty
- mal: what the action is directed at: a person id, an object id, "kamera", or null
- blick: where the person looks: a person id, an object id or noun, "kamera", "ned", or null
- kontakt: what touches what, as "a>b", or null
- beskrivning: one short English sentence of what happens, without guessing beyond what is visible
- sakerhet: 0-1
Answer with JSON only: {{"segment": [{{"id": ..., "handling": ..., "kroppsdel": ..., "foremal": ..., "i_handen": ..., "mal": ..., "blick": ..., "kontakt": ..., "beskrivning": ..., "sakerhet": ...}}]}}"""
    k = os.environ.get('AI_GATEWAY_API_KEY') or Path(os.environ['AI_GATEWAY_NYCKELFIL']).read_text(encoding='utf-8').splitlines()[0].strip()
    body = dict(model=modell, max_tokens=8000, response_format=dict(type='json_object'), messages=[dict(role='user', content=[dict(type='text', text=text),
                dict(type='file', file=dict(file_data='data:video/mp4;base64,' + base64.b64encode(Path(video).read_bytes()).decode(), filename=Path(video).name))])])
    req = urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=600)); svar = d['choices'][0]['message']['content']
    (ut / 'prompt.txt').write_text(text, encoding='utf-8')
    (ut / 'gemini.json').write_text(json.dumps(dict(modell=modell, usage=d.get('usage'), svar=svar), ensure_ascii=False, indent=1), encoding='utf-8')
    return json.loads(svar.strip().removeprefix('```json').removesuffix('```')), (d.get('usage') or {}).get('cost')


def main():
    a = argparse.ArgumentParser(); a.add_argument('kalla'); a.add_argument('scen'); a.add_argument('--gemini'); a.add_argument('--ut'); x = a.parse_args()
    kf = Path(x.kalla).resolve(); K = json.loads(kf.read_text(encoding='utf-8')); sem = K['semantik']; sc = next(s for s in sem['scener'] if s['id'] == x.scen)
    fps = K['tidsbas']['fps_taljare'] / K['tidsbas']['fps_namnare']; a0 = round(sc['start_s'] * fps); b0 = round(sc['slut_s'] * fps)
    kam = next(k for k in K['matning']['kameror'] if k['id'] == sc['kamera']); V = np.load(kf.parent / kam['spar_metrisk']['sokvag'])
    tagdir = (kf.parent / kam['spar_metrisk']['sokvag']).parent; klipp = tagdir.parent.name; tag = tagdir.name; video = tagdir.parent / 'klipp' / f'{tag}.mp4'
    ut = (HIT / (x.ut or f'handling/{klipp}')) / x.scen; ut.mkdir(parents=True, exist_ok=True)
    pers = [(m['person'], kf.parent / m['rorelse']['sokvag']) for m in K['matning']['personer'] if m.get('scen') in (None, x.scen) and m['person'] in sc['personer']]
    alla = []
    for pid, seq in pers:
        S = signaler(seq, V); off = a0 - kam.get('kalla_ruta0', a0) if 'kalla_ruta0' in kam else 0
        for j, s in enumerate(segmentera(S)):
            if s['t'][0] == 'utanfor_bild': continue
            h, lage, ror, hu = s['t']; ra, rb = s['a'], s['b']
            alla.append(dict(id=None, vem=pid, rutor_tagning=[ra, rb], tid_tagning_s=[round(ra / fps, 2), round((rb + 1) / fps, 2)], rutor_plan=[a0 + ra + off, a0 + rb + off],
                             hallning=dict(varde=h, kalla='matt'), handens_lage=dict(varde=lage, kalla='matt'), handens_rorelse=dict(varde=ror, kalla='matt'),
                             huvud=dict(varde=hu, kalla='matt'), kamera=dict(varde=kamera(S, ra, rb), kalla='matt'),
                             lutning_grader=[round(float(S['lut'][ra]), 1), round(float(S['lut'][rb]), 1)],
                             handling=dict(varde=None, kalla=None), kroppsdel=dict(varde=None, kalla=None), foremal=dict(varde=None, kalla=None),
                             i_handen=dict(varde=None, kalla=None), mal=dict(varde=None, kalla=None), blick=dict(varde=None, kalla=None), kontakt=dict(varde=None, kalla=None)))
    alla.sort(key=lambda s: (s['vem'], s['rutor_tagning'][0]))
    for i, s in enumerate(alla): s['id'] = f'{x.scen}h{i + 1}'
    H = dict(klipp=klipp, tagning=tag, scen=x.scen, kalla=str(kf), rutor_tagning=b0 - a0, fps=fps, ordforrad=ORD, nya_ord=NYA_ORD,
             kalla_forklaring=dict(matt='ur läsningen eller kameran', last='ur en modell som såg klippet', antagen='antagande utan mätning eller seende'),
             signaler=dict(kropp='ingestens sekvens per person, i världen (varld.npz)', kamera='varld.npz kam_R'), video=str(video), segment=alla)
    if x.gemini and alla:
        kand = '; '.join([f'person "{p["id"]}" ({p.get("roll")}: {p.get("beskrivning")})' for p in sem['personer'] if p['id'] in sc['personer']] +
                         [f'object "{p["id"]}" ({p.get("etikett") or p.get("typ")})' for p in sem['props']] + ['"kamera" (the camera, i.e. the viewer)'])
        g, kostnad = gemini(x.gemini, video, alla, kand, b0 - a0, fps, ut); H['gemini'] = dict(modell=x.gemini, kostnad_usd=kostnad)
        svar = {str(q.get('id')): q for q in g.get('segment', [])}
        for s in alla:
            q = svar.get(s['id']) or {}
            for f in ('handling', 'kroppsdel', 'foremal', 'i_handen', 'mal', 'blick', 'kontakt'): s[f] = dict(varde=q.get(f), kalla='last' if q else None)
            s['beskrivning'] = dict(varde=q.get('beskrivning'), kalla='last', sakerhet=q.get('sakerhet'))
            if s['handling']['varde'] not in ORD or q.get('utanfor'): s['handling']['utanfor_ordforradet'] = q.get('utanfor') or s['handling']['varde']
    (ut / 'handling.json').write_text(json.dumps(H, ensure_ascii=False, indent=1), encoding='utf-8')
    for s in alla: print(s['id'], s['vem'], s['rutor_plan'], s['hallning']['varde'], s['handens_lage']['varde'], s['handens_rorelse']['varde'], s['huvud']['varde'], s['kamera']['varde'], s['handling']['varde'], s['mal']['varde'], s['blick']['varde'])
    if H.get('gemini'): print('kostnad', H['gemini']['kostnad_usd'])


if __name__ == '__main__': main()
