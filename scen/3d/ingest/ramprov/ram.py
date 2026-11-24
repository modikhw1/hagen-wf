"""Uppdrag 0003: Gemini läser läge i en försatt koordinatram (plankarta = arm A, golvrutnät i originalbilden = arm B).
Körs (från scen/): .venv/Scripts/python.exe -B ram.py bilder | kontroll | kor <arm A|B> <n> | summera
Nyckeln läses via AI_GATEWAY_NYCKELFIL (sökväg) och skrivs aldrig ut. Geminis svar är hypotes och skrivs inte in i någon deklaration."""
import base64, json, math, os, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
import cv2, numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ING = os.path.dirname(HERE); D3 = os.path.dirname(ING)
UT = f'{D3}/kontrakt/ut'; I = f'{ING}/ut/b-tilltal-ravara-tagningar'
PLAN = json.load(open(f'{UT}/b-tilltal-ravara_n06-fler/narvaro/plan.json', encoding='utf8'))
W, H = 576, 1024
GATEWAY = 'https://ai-gateway.vercel.sh/v1/chat/completions'; MODELL = 'google/gemini-2.5-flash'
TAK_USD = .26      # 0,60 totalt minus 0,337 som första försöket kostade (alla svar tomma: tänkandet åt upp max_tokens)
SCENER = {s['id'].upper(): s for s in PLAN['scener']}
OBJ = {}
for o in PLAN['objekt']: OBJ.setdefault(o['id'], o)                       # n06-fler har två disk_A; den första gäller
PL = PLAN['plats'][0]; ANK = {a['id']: np.array(a['pos_m'], float) for a in PL['uppmatta_ankare']}
PERSON = {'S1': 'A', 'S2': 'A', 'S3': 'B', 'S4': 'B'}
os.makedirs(f'{HERE}/bilder', exist_ok=True); os.makedirs(f'{HERE}/svar', exist_ok=True)


def kamera(sid):
    u0, u1 = SCENER[sid]['ut']; mid = (u0 + u1 - 1) // 2; k = PLAN['renderkamera']['nycklar'][mid]
    return np.asarray(k['matris'], float), float(k['lins_mm']), mid - u0


def proj(P, M, lins):
    P = np.atleast_2d(np.asarray(P, float)); lok = (P - M[:3, 3]) @ M[:3, :3]; d = -lok[:, 2]
    fok = lins / 36. * W
    uv = np.c_[lok[:, 0] / np.maximum(d, 1e-9) * fok + W / 2, -lok[:, 1] / np.maximum(d, 1e-9) * fok + H / 2]
    return uv, d


def nyckelruta(sid, lokal):
    cap = cv2.VideoCapture(f'{I}/klipp/{sid}.mp4'); cap.set(cv2.CAP_PROP_POS_FRAMES, lokal); ok, img = cap.read()
    assert ok, sid; return img


def linje(img, a, b, M, lins, farg, tjock=1, steg=24):
    ts = np.linspace(0, 1, steg); P = np.array(a) * (1 - ts[:, None]) + np.array(b) * ts[:, None]; uv, d = proj(P, M, lins)
    pts = [tuple(np.round(u).astype(int)) for u, dd in zip(uv, d) if dd > .05 and -2000 < u[0] < 3000 and -2000 < u[1] < 4000]
    for p, q in zip(pts[:-1], pts[1:]): cv2.line(img, p, q, farg, tjock, cv2.LINE_AA)


def text(img, s, p, farg, skala=.42):
    p = (int(p[0]), int(p[1]))
    cv2.putText(img, s, p, cv2.FONT_HERSHEY_SIMPLEX, skala, (0, 0, 0), 3, cv2.LINE_AA); cv2.putText(img, s, p, cv2.FONT_HERSHEY_SIMPLEX, skala, farg, 1, cv2.LINE_AA)


def rutnat_bild(sid):
    """Arm B: golvrutnät 0,5 m (cyan, z=0) och diskens ovansida 0,25 m (gul, z=0,9) projicerade genom tagningens lösta kamera."""
    M, lins, lokal = kamera(sid); img = nyckelruta(sid, lokal)
    xs = np.arange(-1., 4.01, .5); ys = np.arange(-1., 3.01, .5)
    for x in xs: linje(img, (x, ys[0], 0), (x, ys[-1], 0), M, lins, (255, 255, 0))
    for y in ys: linje(img, (xs[0], y, 0), (xs[-1], y, 0), M, lins, (255, 255, 0))
    for x in xs[::2]:
        for y in ys[::2]:
            uv, d = proj([[x, y, 0]], M, lins)
            if d[0] > .3 and 8 < uv[0, 0] < W - 60 and 8 < uv[0, 1] < H - 8: text(img, f'{x:g},{y:g}', uv[0] - (10, 4), (255, 255, 0), .38)
    dc = OBJ['disk_C']; cx, cy = dc['pos_m'][:2]; hx, hy = dc['matt_m'][0] / 2, dc['matt_m'][1] / 2; z = dc['pos_m'][2] + dc['matt_m'][2] / 2
    for x in np.arange(cx - hx, cx + hx + .001, .25): linje(img, (x, cy - hy, z), (x, cy + hy, z), M, lins, (0, 255, 255))
    for y in np.arange(cy - hy, cy + hy + .001, .25): linje(img, (cx - hx, y, z), (cx + hx, y, z), M, lins, (0, 255, 255))
    for x, y in ((cx - hx, cy - hy), (cx + hx, cy - hy), (cx - hx, cy + hy), (cx + hx, cy + hy), (cx, cy - hy)):
        uv, d = proj([[x, y, z]], M, lins)
        if d[0] > .3 and 8 < uv[0, 0] < W - 70 and 8 < uv[0, 1] < H - 8: text(img, f'T {x:.2f},{y:.2f}', uv[0] - (10, 4), (0, 255, 255), .36)
    cv2.imwrite(f'{HERE}/bilder/B_{sid}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90]); return img


def karta_bild():
    """Arm A: plankarta uppifrån med rutnät i meter, rummets väggar, personplatserna A/B/C och de lösta kamerorna som numrerade pilar.
    Möbler, vågen och köttbiten är medvetet inte inritade: det är dem modellen ska placera."""
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 7), dpi=110)
    ax.set_xlim(-2.5, 4.0); ax.set_ylim(-3.0, 3.0); ax.set_aspect('equal'); ax.grid(True, color='#bbbbbb', lw=.6)
    ax.set_xticks(np.arange(-2.5, 4.01, .5)); ax.set_yticks(np.arange(-3, 3.01, .5)); ax.tick_params(labelsize=7)
    ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)  [kamerorna tittar mot +y]')
    ax.axhline(2.565 - .06, color='k', lw=3); ax.text(-2.4, 2.45, 'back wall (tiled)', fontsize=8)
    ax.axvline(3.343 - .06, color='k', lw=3); ax.text(3.0, -2.8, 'side wall', fontsize=8, rotation=90)
    for n, p in ANK.items():
        if n.endswith('A'): ax.plot(*p[:2], 'o', color='tab:green', ms=9); ax.text(p[0] + .05, p[1] + .08, 'person A/B', fontsize=8, color='tab:green')
        elif n.endswith('C'): ax.plot(*p[:2], 'o', color='tab:red', ms=9); ax.text(p[0] + .05, p[1] + .08, 'person C', fontsize=8, color='tab:red')
    for sid in SCENER:
        s = sid.upper(); M, lins, _ = kamera(s); C = M[:3, 3]; f = (M[:3, :3] @ [0, 0, -1.])[:2]; f /= np.linalg.norm(f)
        ax.annotate('', xy=C[:2] + .45 * f, xytext=C[:2], arrowprops=dict(arrowstyle='-|>', color='tab:blue', lw=1.8))
        ax.text(C[0] - .06 * f[1] - .1, C[1] - .12, s[1:], fontsize=9, color='tab:blue', weight='bold')
    ax.set_title('Plan view of the shop (metres). Numbered arrows = camera positions of shots 1-11.', fontsize=9)
    fig.savefig(f'{HERE}/bilder/A_karta.png', bbox_inches='tight'); plt.close(fig)


def kontroll():
    """Utan anrop: golvpunkter vid personplatsen projiceras genom den lösta kameran och jämförs med ingestens ankelleder (MHR70 13/14)."""
    rader = []
    for sid in SCENER:
        s = sid.upper(); M, lins, lokal = kamera(s); pe = ANK[f'staplats_{PERSON.get(s, "C")}']
        uv, d = proj([[pe[0], pe[1], 0.]], M, lins)
        npz = [f for f in sorted(os.listdir(f'{I}/{s}/kropp/1')) if f.endswith('.npz')]
        z = np.load(f'{I}/{s}/kropp/1/{npz[min(lokal, len(npz) - 1)]}', allow_pickle=True)
        kp = np.asarray(z['pred_keypoints_2d'], float); skala = np.array([W / 576, H / 1024])   # kropp-npz ligger redan i utdatans upplösning (576x1024)
        ank = kp[[13, 14]].mean(0) * skala
        rader.append(dict(tagning=s, rutnat_fot_px=[round(float(v)) for v in uv[0]], ingest_ankel_px=[round(float(v)) for v in ank],
                          skillnad_px=round(float(np.hypot(*(uv[0] - ank))), 1), skillnad_m_vid_djup=round(float(np.hypot(*(uv[0] - ank)) / (lins / 36. * W) * d[0]), 2),
                          djup_m=round(float(d[0]), 2), fot_i_bild=bool(0 <= ank[1] < H)))
        print(rader[-1])
    json.dump(rader, open(f'{HERE}/kontroll_projektion.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)


FRAGA_A = ('You see (1) a top-down plan map of a butcher shop with a metre grid, the room walls, the person positions and the solved camera positions '
           'as numbered blue arrows (numbers 1-11 = shots), and (2) one frame from shot {n}. Counters, the scale and the meat are NOT drawn on the map. '
           'Use the map coordinates. Answer with JSON only: {{"camera_arrow": <number of the arrow that is this shot\'s camera>, '
           '"arrow_direction_matches_view": <true/false>, "counter_front_edge_center": {{"x": <m>, "y": <m>}} or null, '
           '"counter_x_range": [<xmin>, <xmax>] or null, "scale": {{"x": <m>, "y": <m>}} or null (the electronic scale if visible), '
           '"meat": {{"x": <m>, "y": <m>}} or null, "notes": "<one short sentence>"}}. Coordinates in metres on the map.')
FRAGA_B = ('This frame (shot {n}) has a projected floor grid (cyan lines, labels "x,y" in metres at z=0) and the top of the counter as a second grid (yellow, labels "T x,y"). '
           'Answer with JSON only: {{"grid_aligned": "yes" | "shifted" | "tilted" | "unclear", "grid_problem": "<direction, e.g. grid appears too far right/closer/farther>" or null, '
           '"counter_front_edge_center": {{"x": <m>, "y": <m>}} or null (floor coordinate where the counter front meets the floor, if visible; otherwise the top-front edge using the T grid), '
           '"scale_base": {{"x": <m>, "y": <m>}} or null (electronic scale, use the T grid), "meat": {{"x": <m>, "y": <m>}} or null, '
           '"person_feet": {{"x": <m>, "y": <m>}} or null, "notes": "<one short sentence>"}}.')


def nyckel():
    f = os.environ.get('AI_GATEWAY_NYCKELFIL')
    return open(f, encoding='utf-8').read().splitlines()[0].strip()


def b64(p): return base64.b64encode(open(p, 'rb').read()).decode()


def anrop(arm, sid, k):
    n = int(sid[1:]); bilder = [f'{HERE}/bilder/A_karta.png', f'{HERE}/bilder/B_{sid}.jpg'] if arm == 'A' else [f'{HERE}/bilder/B_{sid}.jpg']
    if arm == 'A':
        keyf = f'{HERE}/bilder/nyckel_{sid}.jpg'; cv2.imwrite(keyf, nyckelruta(sid, kamera(sid)[2]), [cv2.IMWRITE_JPEG_QUALITY, 88]); bilder = [bilder[0], keyf]
    inneh = [dict(type='text', text=(FRAGA_A if arm == 'A' else FRAGA_B).format(n=n))]
    for p in bilder: inneh.append(dict(type='image_url', image_url=dict(url=('data:image/png;base64,' if p.endswith('.png') else 'data:image/jpeg;base64,') + b64(p))))
    body = dict(model=MODELL, max_tokens=int(os.environ.get('RAM_MAXTOK', '3000')), response_format=dict(type='json_object'), messages=[dict(role='user', content=inneh)],
                providerOptions=dict(google=dict(thinkingConfig=dict(thinkingBudget=int(os.environ.get('RAM_TANKE', '0'))))))
    for forsok in range(4):
        try:
            r = urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + nyckel(), 'Content-Type': 'application/json'})
            d = json.load(urllib.request.urlopen(r, timeout=180)); break
        except urllib.error.HTTPError as e:
            if e.code != 429: return dict(arm=arm, tagning=sid, k=k, fel=f'HTTP {e.code}', kostnad=0)
            time.sleep(5 * (forsok + 1))
    else: return dict(arm=arm, tagning=sid, k=k, fel='429', kostnad=0)
    raa = (d['choices'][0].get('message') or {}).get('content'); fin = d['choices'][0].get('finish_reason')
    try: svar = json.loads(raa)
    except (ValueError, KeyError, TypeError): svar = None
    return dict(arm=arm, tagning=sid, k=k, svar=svar, raa=(raa or '')[:600] if svar is None else None, finish=fin, tokens=(d.get('usage') or {}).get('completion_tokens'),
                kostnad=float((d.get('usage') or {}).get('cost') or 0))


def kor(arm, n):
    tagn = os.environ.get('RAM_TAGN', '').split(',') if os.environ.get('RAM_TAGN') else [s.upper() for s in SCENER]
    jobb = [(arm, s, k) for s in tagn for k in range(n)]; kostnad = 0.; ut = []; suff = os.environ.get('RAM_SUFF', '')
    with ThreadPoolExecutor(3) as ex:
        for i in range(0, len(jobb), 6):
            for r in ex.map(lambda j: anrop(*j), jobb[i:i + 6]): ut.append(r); kostnad += r['kostnad']
            print(f'arm {arm}: {len(ut)}/{len(jobb)} anrop, hittills {kostnad:.4f} USD', flush=True)
            json.dump(ut, open(f'{HERE}/svar/arm{arm}{suff}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
            if kostnad > TAK_USD: print('kostnadstak nått, avbryter'); break
    print(f'arm {arm} klar: {len(ut)} anrop, {kostnad:.4f} USD')


if __name__ == '__main__':
    a = sys.argv[1]
    if a == 'bilder':
        karta_bild()
        for s in SCENER: rutnat_bild(s.upper())
        print('bilder klara')
    elif a == 'kontroll': kontroll()
    elif a == 'kor': kor(sys.argv[2], int(sys.argv[3]))
    elif a == 'prov': print(json.dumps(anrop(sys.argv[2], sys.argv[3], 0), ensure_ascii=False)[:1800])
