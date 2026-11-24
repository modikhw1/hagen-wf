"""rumshjärna/2, väljaren: rangordnar OneFormer-instanserna per tagning efter hur mycket de bär scenens mening.

Bygger bara på signaler som redan finns (inget GPU-anrop): obs_gpu/*.npz (via lokalitet.ladda), nat.json + nat/*.bin,
paket_L.json (kroppsspår), lokalitet.json (L2c handkontakt, L7 rum över tagningar), pose2d.json (2D-led) och
originalrutan ur videon. V3 "essens" (bildgenerering) är en röst med låg vikt där bilden finns.

Klasser: 'person', 'objekt', 'rum' (vägg/golv/tak/fönster/dörr m.m. och utomhusstruktur) och 'overlagg' (skärmtext).
Rum och överlägg rangordnas för sig; de tävlar inte med objekten.

Signaler (alla 0..1, var och en med skäl). Poängen är ett viktat medel över de signaler som FINNS för instansen;
en signal som saknas (ingen person i bild, ingen V3, bara en tagning) röstar inte, i stället för att räknas som 0.
  hand       0,30  föremål i/vid handen: 2D (pose2d, handpunkt förlängd från armbåge->handled) i mittrutan, och 3D
                   (avstånd från kroppsspårets händer till instansens nät-hörn kring mittrutan). 3D-vittnet halveras när
                   L2c säger att kroppsdjupet är osäkert (k_hand avviker och tillämpades inte), och kvartas när 2D-händer
                   finns men föremålet inte syns vid dem (djupförväxling längs strålen). Stödytor (golv/bänk/bord/spis/
                   skåp) och stora ytor (>1 m eller >15 % av bilden) får halv poäng: de berörs men hålls inte.
  kropp      0,30  bara personer (i handens ställe): andel säkra 2D-leder (pose2d) inom personens mask.
  aterkomst  0,20  L7: samma etikett och överlappande 3D-låda (gruppens ram, nat-transform) i andra tagningar i samma
                   rum, andel av gruppens övriga tagningar. Utan 3D-bevis: etiketten finns i andra tagningar, väger 1/4.
  bild       0,20  hälften centrering (medel över maskens pixlar), hälften storlek (sqrt(andel/0,10), tak 1).
  skarpa     0,12  Laplacevarians i originalrutan inom eroderad mask, mot medianen över tagningens instanser:
                   0,5 + 0,25*log2(kvot), klämd 0..1 (dubbelt så skarp -> 0,75).
  semantik   0,10  liten prior för restauranginnehåll, se PRIOR nedan.
  v3         0,08  andel av instansen som inte är platt grå i <sid>_v3_essens.png (samma grå-detektion som analys.py).
Osäkert segment (OneFormer-poäng < 0,75, lokalitet.ladda 'osakra') multipliceras med 0,8.

Minsta mängd (roller, i ordning): huvudperson(er) -> föremål i handen -> platsmarkör (återkommer i rummet) ->
fokus (bäst rankade objekt) -> fler objekt så länge poängen >= 0,75 x bästa objektets (högst 4 objekt) -> ett rumsankare.
Skriver ut/rumshjarna/<klipp>/valjare.json. Inga klippkonstanter; samma kod på alla klipp.
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; LOK = HERE.parent
sys.path.insert(0, str(LOK))
import lokalitet as L  # noqa: E402

VIKT = {'hand': 0.30, 'kropp': 0.30, 'aterkomst': 0.20, 'bild': 0.20, 'skarpa': 0.12, 'semantik': 0.10, 'v3': 0.08}
# Semantisk prior (första ordet i ADE-etiketten). Liten med flit: den bryter lika lägen, den avgör inte.
PRIOR = {
    1.0: ('food', 'plate', 'bowl', 'tray', 'glass', 'bottle', 'pot', 'basket', 'cup'),             # det som serveras/äts
    0.6: ('table', 'desk', 'counter', 'countertop', 'bar', 'kitchen island', 'buffet', 'stove', 'oven', 'hood',
          'microwave', 'dishwasher', 'sink', 'refrigerator', 'cabinet', 'shelf', 'case', 'chair', 'stool', 'seat',
          'bench', 'sofa', 'armchair', 'swivel chair', 'booth', 'box', 'bag', 'barrel'),                # möbler/utrustning
    0.25: ('painting', 'plant', 'flower', 'vase', 'lamp', 'light', 'chandelier', 'sconce', 'cushion', 'pillow',
           'sculpture', 'poster', 'clock', 'flag', 'signboard', 'trade name', 'bulletin board', 'fan', 'blind'),  # dekor
}
PRIOR_OVRIGT = 0.4
RUM_GRUPPER = ('golv', 'tak', 'vagg')
RUM_ETIKETTER = ('building', 'sky', 'house', 'skyscraper', 'tree', 'mountain', 'hill', 'sea', 'water', 'river', 'lake',
                 'land', 'stairs', 'stairway', 'step', 'bridge', 'tower', 'awning', 'canopy', 'rail', 'bannister')
MIN_ANDEL = 0.0005   # instanser under 0,05 % av bilden är brus för väljaren
STOR_YTA_M, STOR_YTA_ANDEL = 1.0, 0.15
KONTAKT_M = (0.08, 0.20)  # 3D: <=0,08 m full kontakt, >=0,20 m ingen


def forsta(etikett):
    return etikett.split(',')[0].strip().lower()


def prior(e):
    for v, ord_ in PRIOR.items():
        if e in ord_:
            return v
    return PRIOR_OVRIGT


def sha_kort(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16] if Path(p).is_file() else None


def las_rutor(video, behov):
    cap = cv2.VideoCapture(str(video)); ut = {}; i = 0; mx = max(behov)
    while i <= mx:
        ok, f = cap.read()
        if not ok:
            break
        if i in behov:
            ut[i] = f
        i += 1
    return ut


def v3_kvar(fil, hw):
    img = cv2.imread(str(fil)); hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    las = hsv[..., 1] < 18
    mod = int(np.argmax(np.bincount(hsv[..., 2][las].ravel(), minlength=256))) if las.any() else 200
    gra = las & (np.abs(hsv[..., 2].astype(int) - mod) < 14)
    return cv2.resize((~gra).astype(np.uint8), (hw[1], hw[0]), interpolation=cv2.INTER_NEAREST).astype(bool)


def nat_hörn(nat_dir, man_t):
    """instans -> (hörn i tagningens lokala ram, låda min/max, etikett)"""
    blob = (nat_dir / man_t['fil']).read_bytes(); ut = {}
    for b in man_t['bitar']:
        if b['instans'] < 0:
            continue
        off, n = b['pos']; P = np.frombuffer(blob[off:off + n], np.float32).reshape(-1, 3)
        ut[b['instans']] = {'P': P, 'min': np.array(b['min']), 'max': np.array(b['max']), 'etikett': b['etikett']}
    return ut


def i_grupp(M4, lo, hi):
    """axelparallell låda i gruppens ram ur lokal låda"""
    c = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    if M4 is not None:
        c = c @ M4[:3, :3].T + M4[:3, 3]
    return c.min(0), c.max(0)


def main(nyckel):
    out = LOK / 'ut' / nyckel; dst = LOK / 'ut' / 'rumshjarna' / nyckel; dst.mkdir(parents=True, exist_ok=True)
    meta = json.loads((out / 'obs_gpu.json').read_text(encoding='utf-8'))
    gk = L.gruppkarta(meta['etiketter']); namn = {int(k): v for k, v in meta['etiketter'].items()}
    rep = json.loads((out / 'lokalitet.json').read_text(encoding='utf-8'))
    nat = json.loads((out / 'nat.json').read_text(encoding='utf-8'))['tagningar']
    pak = json.loads((out / 'paket_L.json').read_text(encoding='utf-8'))
    pose = json.loads((out / 'pose2d.json').read_text(encoding='utf-8')) if (out / 'pose2d.json').is_file() else None
    W0, H0 = meta['bild_px']; ix = {n: i for i, n in enumerate(pak.get('leder', []))}
    grupper = rep.get('rum_over_tagningar', {}).get('grupper', [])
    tl = next((p_ for p_ in (L.ROOT / 'arbetsbord/data/ingest_v2' / nyckel / 'tidslinje.json', out / 'ingest_v2' / 'tidslinje.json') if p_.is_file()), None)
    skarmtext = json.loads(tl.read_text(encoding='utf-8')).get('skarmtext', []) if tl else []
    mitt = {t['id']: nat.get(t['id'], {}).get('ruta', t['nyckelrutor'][len(t['nyckelrutor']) // 2]) for t in meta['tagningar']}
    rutor = las_rutor(L.ROOT / 'data/format/kontroll/klipp' / (meta['klipp'] + '.mp4'), set(mitt.values()))

    # Förberedelse för återkomst: varje tagnings nät-lådor i sin grupps ram, och etiketter per tagning
    lador = {}; etik_per_t = {}
    for t in meta['tagningar']:
        sid = t['id']; o = L.ladda(out, mitt[sid], gk, 'obs_gpu')
        etik_per_t[sid] = {forsta(namn[l_]) for i_, l_ in o['segs'].items() if (o['I'] == i_).mean() >= MIN_ANDEL}
        if sid in nat:
            M4 = np.array(nat[sid]['transform']) if 'transform' in nat[sid] else None
            lador[sid] = [(forsta(b['etikett']), *i_grupp(M4, np.array(b['min']), np.array(b['max']))) for b in nat[sid]['bitar'] if b['instans'] >= 0]

    res = {'schema': 'valjare/1', 'klipp': nyckel, 'kod_sha256': sha_kort(__file__),
           'kallor': {f: sha_kort(out / f) for f in ('lokalitet.json', 'paket_L.json', 'nat.json', 'obs_gpu.json', 'pose2d.json')},
           'metod': {'vikter': VIKT, 'prior': {str(k): list(v) for k, v in PRIOR.items()}, 'prior_ovrigt': PRIOR_OVRIGT,
                     'rum_grupper': RUM_GRUPPER, 'rum_etiketter': RUM_ETIKETTER, 'min_andel': MIN_ANDEL,
                     'poang': 'viktat medel över tillgängliga signaler; osäkert segment x0,8'},
           'tagningar': {}}
    for t in meta['tagningar']:
        sid = t['id']; u = mitt[sid]; info = rep['tagningar'].get(sid, {})
        o = L.ladda(out, u, gk, 'obs_gpu'); I = o['I']; h, w = I.shape
        frame = rutor.get(u)
        segs = {int(i_): int(l_) for i_, l_ in o['segs'].items()}
        pers_ids = [i_ for i_, l_ in segs.items() if gk.get(l_) == 'person']
        pers_mask = np.isin(I, pers_ids)
        ovl = L.overlagg_mask(frame, skarmtext, u / meta['fps'], h, w) if frame is not None else np.zeros((h, w), bool)
        # skärpa: Laplace i full upplösning
        lapvar = {}
        if frame is not None:
            g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
            lap = cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 0.8), cv2.CV_32F, ksize=3)
            for i_ in segs:
                m = cv2.resize((I == i_).astype(np.uint8), (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
                m = cv2.erode(m, np.ones((7, 7), np.uint8)).astype(bool)
                if m.sum() >= 80:
                    lapvar[i_] = float(lap[m].var())
        lap_med = float(np.median(list(lapvar.values()))) if lapvar else None
        # V3
        v3fil = dst / f'{sid}_v3_essens.png'; kvar = v3_kvar(v3fil, (h, w)) if v3fil.is_file() else None
        # 2D-händer ur pose2d (mittrutan): handpunkt = handled + 0,35*(handled - armbåge), radie = halva underarmen
        hander2d = []
        if pose and u < len(pose['rutor']):
            sx, sy = w / pose['bild_px'][0], h / pose['bild_px'][1]
            for q in pose['rutor'][u]['personer']:
                kp = np.array(q['kp'])
                for e_, wr in ((7, 9), (8, 10)):
                    if kp[wr, 2] > 0.4 and kp[e_, 2] > 0.4:
                        a_ = kp[e_, :2] * (sx, sy); b_ = kp[wr, :2] * (sx, sy); fa = np.linalg.norm(b_ - a_)
                        if fa > 2:
                            hander2d.append((b_ + 0.35 * (b_ - a_), max(3.0, 0.5 * fa)))
        # 3D-händer ur kroppsspåret, i tagningens lokala ram, rutor kring mittrutan
        hander3d = []; spar_ok = 0
        M4 = np.array(nat[sid]['transform']) if sid in nat and 'transform' in nat[sid] else None
        for pid, spar in pak.get('rorelse', {}).items():
            for tr in spar:
                if tr['tagning'] != sid or tr.get('tilltro', {}).get('overkropp') == 'skymd_antagen':
                    continue
                spar_ok += 1
                for row in tr['rutor']:
                    if abs(row[0] - u) > 6:
                        continue
                    J = np.array(row[1:], float).reshape(-1, 3) / 1000.0
                    if M4 is not None:
                        J = (J - M4[:3, 3]) @ M4[:3, :3]
                    hander3d += [J[ix[n]] for n in ('l_hand_mitt', 'r_hand_mitt') if n in ix]
        hander3d = np.array(hander3d) if hander3d else None
        hk = info.get('handkontakt'); tillit3d = 1.0; hk_skal = 'L2c: inga handprov'
        if hk:
            hk_skal = f"L2c: {hk['prov']} handprov, kollision {hk['kollision_fore']}, k_hand {hk['k_hand']}, tillämpat {hk['tillampat']}"
            if not hk['tillampat'] and abs(hk['k_hand'] - 1) > 0.1:
                tillit3d = 0.5; hk_skal += ' -> kroppsdjupet osäkert, 3D-vittnet halveras'
        hornen = nat_hörn(out / 'nat', nat[sid]) if sid in nat else {}
        grp = next((g_ for g_ in grupper if sid in g_), None)
        ovriga = [s for s in etik_per_t if s != sid]
        yy, xx = np.mgrid[:h, :w]; rc = np.hypot((xx + 0.5) / w - 0.5, (yy + 0.5) / h - 0.5) / math.hypot(0.5, 0.5)

        poster = []
        for i_, l_ in segs.items():
            m = I == i_; andel = float(m.mean())
            if andel < MIN_ANDEL:
                continue
            etik = namn.get(l_, '?'); e = forsta(etik); grupp = gk.get(l_, 'ovrigt')
            klass = 'person' if grupp == 'person' else 'rum' if (grupp in RUM_GRUPPER or e in RUM_ETIKETTER) else 'objekt'
            if ovl.any() and (m & ovl).sum() / m.sum() > 0.5:
                klass = 'overlagg'
            sig = {}
            # 1. hand
            if klass == 'objekt' and (hander2d or hander3d is not None):
                s2, s3, delar = 0.0, None, []
                for c_, r_ in hander2d:
                    disk = np.hypot(xx - c_[0], yy - c_[1]) <= r_; bas = (disk & ~pers_mask).sum()
                    if bas > 0:
                        s2 = max(s2, min(1.0, (disk & m).sum() / bas / 0.5))
                if hander2d:
                    delar.append(f'2D: täcker {s2 * 50:.0f} % av handens omgivning')
                if hander3d is not None and i_ in hornen:
                    P = hornen[i_]['P']; P = P[:: max(1, len(P) // 3000)]
                    d = float(min(np.min(np.linalg.norm(P - hh_, axis=1)) for hh_ in hander3d))
                    s3 = float(np.clip((KONTAKT_M[1] - d) / (KONTAKT_M[1] - KONTAKT_M[0]), 0, 1)) * tillit3d
                    delar.append(f'3D: närmaste nät-hörn {d:.2f} m från handen')
                if s3 and hander2d and s2 < 0.05:  # 3D nära men inget av föremålet syns vid handen i bilden: djupförväxling längs strålen
                    s3 *= 0.25; delar.append('3D utan stöd i 2D (x0,25)')
                v = max(s2, s3 or 0.0); halls = v > 0
                ext = float(np.linalg.norm(hornen[i_]['max'] - hornen[i_]['min'])) if i_ in hornen else None
                if v > 0 and (grupp in L.STOD or (ext is not None and ext > STOR_YTA_M) or andel > STOR_YTA_ANDEL):
                    v *= 0.5; halls = False; delar.append('stödyta/stor yta: berörs, hålls inte (x0,5)')
                sig['hand'] = {'varde': round(v, 3), 'halls': halls, 'skal': '; '.join(delar + [hk_skal])}
            if klass == 'person' and pose and u < len(pose['rutor']):  # kroppen: 2D-skelettets leder inom personens mask
                md = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool); bast_k = (0.0, 0)
                for q in pose['rutor'][u]['personer']:
                    kp = np.array(q['kp']); ok = kp[:, 2] > 0.5
                    if ok.sum() >= 4:
                        xs = np.clip((kp[ok, 0] * w / pose['bild_px'][0]).astype(int), 0, w - 1); ys = np.clip((kp[ok, 1] * h / pose['bild_px'][1]).astype(int), 0, h - 1)
                        bast_k = max(bast_k, (float(md[ys, xs].mean()), int(ok.sum())))
                sig['kropp'] = {'varde': round(bast_k[0], 3), 'skal': f'{bast_k[0] * 100:.0f} % av {bast_k[1]} säkra 2D-leder inom masken' + (f'; kroppsspår i tagningen: {spar_ok}' if spar_ok else '; inget kroppsspår')}
            # 2. återkomst
            if ovriga and klass != 'overlagg':
                s_lab = sum(e in etik_per_t[s] for s in ovriga) / len(ovriga)
                v = 0.25 * s_lab; skal = f'etiketten finns i {sum(e in etik_per_t[s] for s in ovriga)}/{len(ovriga)} andra tagningar (utan 3D-bevis, x0,25)'
                if grp and len(grp) > 1 and sid in lador and i_ in hornen:
                    lo, hi = i_grupp(M4, hornen[i_]['min'], hornen[i_]['max']); traff = []
                    for s in grp:
                        if s == sid or s not in lador:
                            continue
                        if any(e2 == e and np.all(lo - 0.2 <= hi2) and np.all(lo2 - 0.2 <= hi) for e2, lo2, hi2 in lador[s]):
                            traff.append(s)
                    s3 = len(traff) / (len(grp) - 1)
                    if s3 >= v:
                        v = s3; skal = f'L7: samma etikett och 3D-läge i {len(traff)}/{len(grp) - 1} tagningar i rummet {traff}'
                    else:
                        skal += f'; L7: 3D-läget återkommer inte i rummet ({len(grp) - 1} andra tagningar)'
                sig['aterkomst'] = {'varde': round(v, 3), 'skal': skal}
            # 3. bild
            cen = float(1 - rc[m].mean()); stor = min(1.0, math.sqrt(andel / 0.10))
            sig['bild'] = {'varde': round(0.5 * cen + 0.5 * stor, 3), 'skal': f'andel {andel * 100:.1f} %, centrering {cen:.2f}'}
            # 4. skärpa
            if i_ in lapvar and lap_med:
                kv = lapvar[i_] / max(lap_med, 1e-6)
                sig['skarpa'] = {'varde': round(float(np.clip(0.5 + 0.25 * math.log2(max(kv, 1e-6)), 0, 1)), 3),
                                 'skal': f'Laplacevarians {lapvar[i_]:.0f} = {kv:.2f} x tagningens median'}
            # 5. semantik
            pv = 1.0 if klass == 'person' else prior(e)
            sig['semantik'] = {'varde': pv, 'skal': f"prior för '{e}'" + ('' if klass == 'person' else f" ({'innehåll' if pv == 1.0 else 'möbel/utrustning' if pv == 0.6 else 'dekor' if pv == 0.25 else 'övrigt'})")}
            # 6. V3
            if kvar is not None:
                sig['v3'] = {'varde': round(float(kvar[m].mean()), 3), 'skal': 'andel kvar (ej platt grå) i V3 essens'}
            vs = sum(VIKT[k] for k in sig); poang = sum(VIKT[k] * s_['varde'] for k, s_ in sig.items()) / vs
            anm = []
            if i_ in o.get('osakra', []):
                poang *= 0.8; anm.append('osäkert segment (OneFormer < 0,75) x0,8')
            if klass == 'person':
                if spar_ok and andel >= 0.01:
                    anm.append(f'kroppsspår finns i tagningen ({spar_ok})')
            poster.append({'instans': int(i_), 'etikett': e, 'grupp': grupp, 'klass': klass, 'poang': round(poang, 3),
                           'andel_bild': round(andel, 4), 'nat_bit': i_ in hornen, 'signaler': sig, 'anm': anm})
        poster.sort(key=lambda p_: -p_['poang'])
        huvud = [p_ for p_ in poster if p_['klass'] in ('person', 'objekt')]
        rum = [p_ for p_ in poster if p_['klass'] == 'rum']; ovl_l = [p_ for p_ in poster if p_['klass'] == 'overlagg']
        # minsta mängd
        mm = []; tagna = set()
        def lagg(p_, roll, varfor):
            if p_['instans'] not in tagna:
                tagna.add(p_['instans']); mm.append({'instans': p_['instans'], 'etikett': p_['etikett'], 'klass': p_['klass'], 'roll': roll, 'varfor': varfor})
        pers = [p_ for p_ in huvud if p_['klass'] == 'person']
        if pers:
            bast = pers[0]['poang']
            for p_ in pers:
                if p_['andel_bild'] >= 0.01 and p_['poang'] >= 0.8 * bast:
                    lagg(p_, 'person', f"poäng {p_['poang']}, andel {p_['andel_bild'] * 100:.1f} %")
        obj = [p_ for p_ in huvud if p_['klass'] == 'objekt']
        for p_ in sorted([p_ for p_ in obj if p_['signaler'].get('hand', {}).get('varde', 0) >= 0.5 and p_['signaler']['hand']['halls']],
                         key=lambda p_: -p_['signaler']['hand']['varde'])[:2]:
            lagg(p_, 'i_handen', p_['signaler']['hand']['skal'].split(';')[0])
        plats = [p_ for p_ in obj if p_['signaler'].get('aterkomst', {}).get('varde', 0) >= 0.5]
        if plats:
            lagg(plats[0], 'platsmarkor', plats[0]['signaler']['aterkomst']['skal'])
        if obj:
            lagg(obj[0], 'fokus', f"högst poäng bland objekten ({obj[0]['poang']})")
            for p_ in obj[1:]:
                if sum(x['klass'] == 'objekt' for x in mm) >= 4 or p_['poang'] < 0.75 * obj[0]['poang']:
                    break
                lagg(p_, 'stod', f"poäng {p_['poang']} >= 0,75 x bästa objektets")
        if rum:
            lagg(rum[0], 'rumsankare', f"bäst rankade strukturyta (andel {rum[0]['andel_bild'] * 100:.1f} %)")
        res['tagningar'][sid] = {
            'ruta': u, 'rum': info.get('rum'), 'l7_grupp': grp, 'kroppsspar': spar_ok, 'hander_2d': len(hander2d),
            'hander_3d': 0 if hander3d is None else len(hander3d), 'handkontakt_L2c': hk, 'v3': v3fil.is_file(),
            'topp3': [f"{p_['etikett']}#{p_['instans']} ({p_['poang']})" for p_ in huvud[:3]],
            'minsta_mangd': mm, 'rangordning': huvud, 'rum_klass': rum, 'overlagg': ovl_l}
        print(sid, 'topp3', res['tagningar'][sid]['topp3'], '| mängd', [f"{x['etikett']}:{x['roll']}" for x in mm])
    (dst / 'valjare.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('->', dst / 'valjare.json')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'duepiani')
