"""Uppdrag 0008 del B och C: jämför Geminis rutor med segmenterarens (Grounding DINO + SAM 2), rita bilder och räkna om lyften utan kompilering.
Körs (från scen/): .venv/Scripts/python.exe -B 3d/ingest/rutprov/jamfor.py   Skriver jamfor.json, jamfor.md och bilder/rutor_S*.jpg"""
import copy, json, os, sys
import cv2, numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ING = os.path.dirname(HERE); D3 = os.path.dirname(ING); UT = f'{D3}/kontrakt/ut'
sys.path.insert(0, f'{D3}/kontrakt'); sys.path.insert(0, ING)
import mobellyft as ml, foremallyft as fl  # noqa: E402
os.makedirs(f'{HERE}/bilder', exist_ok=True)
I = f'{ING}/ut/b-tilltal-ravara-tagningar'; W, H = 576., 1024.
DEKL = json.load(open(f'{I}/brief/uppsattning3/deklaration_n06_detekterad.json', encoding='utf8'))
SEG = json.load(open(f'{HERE}/seg_resultat.json', encoding='utf8'))['resultat']
PLAN = json.load(open(f'{UT}/b-tilltal-ravara_n06-fler/narvaro/plan.json', encoding='utf8'))
GEM = {}
for eid, d in list(DEKL['platser'].items()) + list(DEKL['foremal'].items()):
    for b in d.get('bilder') or []: GEM.setdefault(eid, {})[b['tagning']] = b['box_2d']
ETIKETT = {'disk': 'counter', 'vag': 'scale', 'kottbit': 'meat'}      # delsträng i Grounding DINO:s fras


def per_mille(b, w=W, h=H): return [b[1] / h * 1000, b[0] / w * 1000, b[3] / h * 1000, b[2] / w * 1000]


def segbox(sid, nyckel):
    """Median över tidens nyckelbilder av den starkaste fyndet vars fras innehåller nyckeln; masken ger rutan när den finns."""
    boxar = []
    for r in SEG:
        if not r['id'].startswith(sid + '_'): continue
        kand = [f for f in r['fynd'] if nyckel in f['etikett']]
        if not kand: continue
        f = max(kand, key=lambda z: z['poang']); b = f.get('mask_box_px') or f['dino_box_px']
        boxar.append(per_mille([b[0], b[1], b[2], b[3]], r['bredd'], r['hojd']))
    if not boxar: return None, 0
    return [round(float(v)) for v in np.median(np.array(boxar), axis=0)], len(boxar)


def iou(a, b):
    ix = max(0., min(a[3], b[3]) - max(a[1], b[1])); iy = max(0., min(a[2], b[2]) - max(a[0], b[0])); i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i; return i / u if u > 0 else 0.


# avlästa rätta kanter ur 0001 (på ögat): bordsytans övre kant S6 ca 870 och S7 ca 875 promille; vågarmens högerkant i S8 ca 505 px = 877 promille
AVLAST = {('disk', 'S6'): ('topp', 870), ('disk', 'S7'): ('topp', 875), ('vag', 'S8'): ('hoger', 877)}
rader = []; NYA = {}
for el, (eid, nyckel) in {'disk_C': ('disk_C', 'counter'), 'disk_A': ('disk_A', 'counter'), 'vag': ('vag', 'scale')}.items():
    for s in [f'S{i}' for i in range(1, 12)]:
        sb, n = segbox(s, nyckel); g = GEM.get(eid, {}).get(s)
        if sb is None and g is None: continue
        post = dict(element=el, tagning=s, gemini=g, segmenterare=sb, antal_bildrutor=n, iou=None if (g is None or sb is None) else round(iou(g, sb), 2))
        a = AVLAST.get(({'disk_C': 'disk', 'vag': 'vag'}.get(el), s))
        if a and sb:
            idx = {'topp': 0, 'hoger': 3}[a[0]]; post['avlast'] = f'{a[0]} {a[1]}'; post['fel_gemini_promille'] = None if g is None else round(g[idx] - a[1]); post['fel_segmenterare_promille'] = round(sb[idx] - a[1])
        rader.append(post)
        if sb: NYA.setdefault(el, {})[s] = sb
# --- bilder: Gemini (gult) och segmenterare (grönt) för S6–S11, bordet och vågen ---
for s in ['S%d' % i for i in range(6, 12)]:
    cap = cv2.VideoCapture(f'{I}/klipp/{s}.mp4'); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.set(cv2.CAP_PROP_POS_FRAMES, n // 2); ok, img = cap.read()
    for el, farg in (('disk_C', (0, 255, 255)), ('vag', (255, 200, 0))):
        g = GEM.get(el, {}).get(s); sb = NYA.get(el, {}).get(s)
        for b, c, tag in ((g, farg, 'G'), (sb, (0, 255, 0), 'S')):
            if b: cv2.rectangle(img, (int(b[1] / 1000 * W), int(b[0] / 1000 * H)), (int(b[3] / 1000 * W) - 1, int(b[2] / 1000 * H) - 1), c, 2 if tag == 'G' else 3); cv2.putText(img, f'{el} {tag}', (int(b[1] / 1000 * W) + 4, int(b[0] / 1000 * H) + 16), cv2.FONT_HERSHEY_SIMPLEX, .5, c, 2, cv2.LINE_AA)
    cv2.imwrite(f'{HERE}/bilder/rutor_{s}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 88])
# --- del C: lyft med de nya rutorna ---
plan = copy.deepcopy(PLAN); pl = plan['plats'][0]; obj = {}
for o in plan['objekt']: obj.setdefault(o['id'], o)
disk = obj['disk_C']; topp = disk['pos_m'][2] + disk['matt_m'][2] / 2.


def lyft(ruta_per_tagning):
    ut = {}
    for el, boxar in ruta_per_tagning.items():
        for s, b in boxar.items():
            try:
                bild = dict(tagning=s, box_2d=b)
                ut.setdefault(el, {})[s] = ml._enbildslage(plan, pl, {}, disk, bild).tolist() if el == 'disk_C' else [float(v) for v in fl._traff(plan, bild, topp)[0]]
            except (ValueError, KeyError, IndexError) as ex: ut.setdefault(el, {})[s] = str(ex)
    return ut


def spridning(d, tagn):
    p = [np.array(d[t]) for t in tagn if isinstance(d.get(t), list)]
    return round(max((float(np.hypot(*(a - b))) for i, a in enumerate(p) for b in p[i + 1:]), default=float('nan')), 2), len(p)


gem_lyft = lyft({'disk_C': GEM['disk_C'], 'vag': GEM['vag']}); seg_lyft = lyft({'disk_C': NYA.get('disk_C', {}), 'vag': NYA.get('vag', {})})
c = dict(
    disk_C_S6_S9_S11=dict(gemini=spridning(gem_lyft['disk_C'], ('S6', 'S7', 'S8', 'S9', 'S11')), segmenterare=spridning(seg_lyft.get('disk_C', {}), ('S6', 'S7', 'S8', 'S9', 'S11'))),
    disk_C_S7_S8_S9_S11=dict(gemini=spridning(gem_lyft['disk_C'], ('S7', 'S8', 'S9', 'S11')), segmenterare=spridning(seg_lyft.get('disk_C', {}), ('S7', 'S8', 'S9', 'S11'))),
    vag_S8_S11=dict(gemini=spridning(gem_lyft['vag'], ('S8', 'S9', 'S10', 'S11')), segmenterare=spridning(seg_lyft.get('vag', {}), ('S8', 'S9', 'S10', 'S11'))),
    lyft_gemini=gem_lyft, lyft_segmenterare=seg_lyft)
json.dump(dict(rutor=rader, effekt=c), open(f'{HERE}/jamfor.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1, default=float)
with open(f'{HERE}/jamfor.md', 'w', encoding='utf8') as f:
    f.write('| element | tagn | Gemini | segmenterare (median, n rutor) | IoU | avläst kant | fel Gemini / segm. (promille) |\n|---|---|---|---|---|---|---|\n')
    for r in rader: f.write(f"| {r['element']} | {r['tagning']} | {r['gemini']} | {r['segmenterare']} ({r['antal_bildrutor']}) | {r['iou']} | {r.get('avlast', '')} | {r.get('fel_gemini_promille', '')} / {r.get('fel_segmenterare_promille', '')} |\n")
print(open(f'{HERE}/jamfor.md', encoding='utf8').read())
for k in ('disk_C_S6_S9_S11', 'disk_C_S7_S8_S9_S11', 'vag_S8_S11'): print(k, c[k])
for el in ('disk_C', 'vag'):
    print(el, 'Gemini', {t: ([round(v, 2) for v in x] if isinstance(x, list) else x) for t, x in gem_lyft[el].items()})
    print(el, 'segm  ', {t: ([round(v, 2) for v in x] if isinstance(x, list) else x) for t, x in seg_lyft.get(el, {}).items()})

# --- överlappskontroll mellan element: bordsrutan som i stort sett är vågrutan är en felidentifiering (S9) ---
flaggade = [s for s in NYA.get('disk_C', {}) if s in NYA.get('vag', {}) and iou(NYA['disk_C'][s], NYA['vag'][s]) >= .7]
c['flaggade_dubbelrutor'] = flaggade
c['disk_C_utan_flaggade_S6_S9_S11'] = dict(segmenterare=spridning(seg_lyft.get('disk_C', {}), [t for t in ('S6', 'S7', 'S8', 'S9', 'S11') if t not in flaggade]),
                                          gemini=spridning(gem_lyft['disk_C'], ('S6', 'S7', 'S8', 'S9', 'S11')))
json.dump(dict(rutor=rader, effekt=c), open(f'{HERE}/jamfor.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1, default=float)
print('flaggade dubbelrutor (bord≈våg):', flaggade, c['disk_C_utan_flaggade_S6_S9_S11'])
