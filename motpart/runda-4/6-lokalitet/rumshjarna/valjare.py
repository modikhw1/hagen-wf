"""rumshjärna/2, väljaren: rangordnar OneFormer-instanserna per tagning efter hur mycket de bär scenens mening.

Bygger bara på signaler som redan finns (inget GPU-anrop): obs_gpu/*.npz (via lokalitet.ladda), nat.json + nat/*.bin,
paket_L.json (kroppsspår), lokalitet.json (L2c handkontakt, L7 rum över tagningar), pose2d.json (2D-led) och
originalrutan ur videon. V3 "essens" (bildgenerering) är en röst med låg vikt där bilden finns.

Klasser: 'person', 'objekt', 'rum' (vägg/golv/tak/fönster/dörr m.m. och utomhusstruktur) och 'overlagg' (skärmtext).
Rum och överlägg rangordnas för sig; de tävlar inte med objekten.

Signaler (alla 0..1, var och en med skäl). Poängen är ett viktat medel över de signaler som FINNS för instansen;
en signal som saknas (ingen person i bild, ingen V3, bara en tagning) röstar inte, i stället för att räknas som 0.
  hand       0,30  endast valda förgrundspersoners händer: 2D (pose2d, förlängd armbåge->handled) och associerad 3D.
                   (avstånd från kroppsspårets händer till instansens nät-hörn kring mittrutan). 3D-vittnet halveras när
                   L2c säger att kroppsdjupet är osäkert (k_hand avviker och tillämpades inte), och kvartas när 2D-händer
                   finns men föremålet inte syns vid dem (djupförväxling längs strålen). Stödytor (golv/bänk/bord/spis/
                   skåp) får halv poäng: de berörs men hålls inte. Storlek mäts robust (5–95 %);
                   stora kärl får hållas när två händer eller starkt 2D-stöd finns.
  kropp      0,30  bara personer (i handens ställe): andel säkra 2D-leder (pose2d) inom personens mask.
  aterkomst  0,20  L7: samma etikett och överlappande 3D-låda (gruppens ram, nat-transform) i andra tagningar i samma
                   rum, andel av gruppens övriga tagningar. Utan 3D-bevis: etiketten finns i andra tagningar, väger 1/4.
  bild       0,26  hälften centrering, hälften storlek (sqrt(andel/0,40), tak 1).
  skarpa     0,06  Laplacevarians inom eroderad mask, mot medianen för segment >=1 %;
                   0,5 + 0,25*log2(kvot), klämd 0..1. Små segments avvikelse krymps mot neutral 0,5.
  semantik   0,10  liten prior för restauranginnehåll, se PRIOR nedan.
  v3         0,08  andel av instansen som inte är platt grå i <sid>_v3_essens.png (samma grå-detektion som analys.py).
Osäkert segment (OneFormer-poäng < 0,75, lokalitet.ladda 'osakra') multipliceras med 0,8.

Minsta mängd: huvudperson(er) valda på yta/djup -> handobjekt -> platsmarkör (ej ensam dekor) -> fokus -> stöd.
Stöd jämförs utan hand, med mjuk dubblettdämpning och skydd för stora synliga objekt; högst sex objekt.
Alla roller har area-/poänggolv. Kompletterande strukturetiketter får egna rumsankare (högst tre).
Textmask ensam slår inte ut möbler/personer: grafik kräver rektangel + OCR-valuta med sedelstöd eller bildplansrörelse.
Flaggar segmenteringsluckor och oskarpa rutor för granskning, utan att hitta på nya objekt.
Skriver ut/rumshjarna/<klipp>/valjare.json. Inga klippkonstanter; samma kod på alla klipp.
"""
from __future__ import annotations
import hashlib, json, math, re, sys
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; LOK = HERE.parent
sys.path.insert(0, str(LOK))
import lokalitet as L  # noqa: E402

# Textur är inget mått på berättelsevikt. Flytta halva skärpevikten till synlig yta,
# så att en reflex i ett litet glas inte slår en stor slät rekvisita.
VIKT = {'hand': 0.30, 'kropp': 0.30, 'aterkomst': 0.20, 'bild': 0.26, 'skarpa': 0.06, 'semantik': 0.10, 'v3': 0.08}
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
# Under dessa ytor är rollen normalt ett bakgrundsfragment. Handrollen har lägre
# golv eftersom verkliga redskap kan vara små; rumsankare måste bära synligt rum.
ROLL_ANDEL = {'person': 0.01, 'i_handen': 0.003, 'platsmarkor': 0.02,
              'fokus': 0.01, 'stod': 0.01, 'rumsankare': 0.05}
ROLL_POANG = {'person': 0.0, 'i_handen': 0.25, 'platsmarkor': 0.30,
              'fokus': 0.25, 'stod': 0.25, 'rumsankare': 0.30}
GRAFIK_ETIKETTER = ('painting', 'poster', 'signboard', 'trade name', 'bulletin board', 'flag')
# Sex ger plats åt mat, kärl, dryck, bord och utrustning utan att hand/platsroller
# förbrukar hela budgeten. Fortfarande ett tak, inte ett mål att fylla.
MAX_OBJEKT = 6


def robust_utbredning(P):
    P = P[np.isfinite(P).all(axis=1)]
    return float(np.linalg.norm(np.percentile(P, 95, axis=0) - np.percentile(P, 5, axis=0))) if len(P) else 0.0


def poang(signaler, utan=()):
    vikter = {k: VIKT[k] for k in signaler if k not in utan}
    return sum(v * signaler[k]['varde'] for k, v in vikter.items()) / sum(vikter.values())


def huvudpersoner(o, pers_ids, pose_ruta, pose_hw):
    """Yta och robust djup före centrering; associera varje 2D-skelett till en mask."""
    I = o['I']; h, w = I.shape
    area = {i: float((I == i).mean()) for i in pers_ids}
    djup = {}
    for i in pers_ids:
        z = o['P'][..., 2][(I == i) & o['M']]
        djup[i] = float(np.median(z)) if len(z) else None
    kandidater = [i for i in pers_ids if area[i] >= ROLL_ANDEL['person']]
    valda = []
    if kandidater:
        storst = max(kandidater, key=lambda i: area[i])
        # En medverkande får vara något mindre, men inte en avlägsen centrerad gäst.
        valda = [i for i in kandidater if area[i] >= 0.6 * area[storst]
                 and (djup[i] is None or djup[storst] is None or djup[i] <= 1.3 * djup[storst])]
    koppling = {}
    for qi, q in enumerate(pose_ruta):
        kp = np.array(q['kp']); ok = kp[:, 2] > 0.5
        if ok.sum() < 4 or not pers_ids:
            continue
        xy = kp[ok, :2] * (w / pose_hw[0], h / pose_hw[1])
        xs, ys = np.clip(xy[:, 0].astype(int), 0, w-1), np.clip(xy[:, 1].astype(int), 0, h-1)
        andelar = {i: float(cv2.dilate((I == i).astype(np.uint8), np.ones((5, 5), np.uint8))[ys, xs].mean()) for i in pers_ids}
        i = max(andelar, key=andelar.get)
        if andelar[i] >= 0.5:
            koppling[qi] = i
    return valda, koppling, djup


def grafikoverlagg(frame, grannar, I, segs, namn, texter, t_s):
    """Konservativ CPU-heuristik: platt rektangel OCH en oberoende grafiksignal.

    Djupets planhet räcker inte (riktiga tavlor är också plana). OCR-valuta i en
    stor rektangel med sedelstöd eller stilla bildplansgrafik över rörlig omgivning ger stöd.
    Okända klistermärken utan dessa bevis lämnas osäkra i stället för att radera skyltar.
    """
    if frame is None:
        return {}
    h, w = I.shape
    gray = cv2.cvtColor(cv2.resize(frame, (w, h)), cv2.COLOR_BGR2GRAY)
    ut = {}
    for i, label in segs.items():
        if forsta(namn.get(label, '')) not in GRAFIK_ETIKETTER:
            continue
        m = (I == i).astype(np.uint8)
        if m.mean() < 0.01:
            continue
        cnt = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea, default=None)
        if cnt is None:
            continue
        rect = cv2.minAreaRect(cnt); rw, rh = rect[1]
        if min(rw, rh) < 2:
            continue
        fyllnad = cv2.contourArea(cnt) / (rw * rh)
        poly = cv2.approxPolyDP(cnt, 0.025 * cv2.arcLength(cnt, True), True)
        if fyllnad < 0.88 or len(poly) != 4:
            continue
        _, _, bw, _ = cv2.boundingRect(cnt)
        ord_ = []
        for tx in texter:
            if not tx['fran_s'] <= t_s < tx['till_s']:
                continue
            x0, y0, x1, y1 = tx['box']; cx, cy = int((x0+x1)*w/2), int((y0+y1)*h/2)
            if 0 <= cx < w and 0 <= cy < h and m[cy, cx]:
                ord_.append(tx['text'].lower())
        # Valutalexikon är generellt, inga belopp, klippnamn eller instans-ID.
        text = ' '.join(ord_)
        valuta = re.search(r'\b(kronor|kroner|dollars?|euros?|pounds?|banknote|riksbank)\b', text)
        # Pris på en verklig meny är inte sedelgrafik. Kräv bank-/sedeltext
        # eller stor överlappning med en person (en bild klistrad framför kroppen).
        sedel = re.search(r'\b(riksbank|banknote|reserve|central bank)\b', text)
        person_ids = [j for j, l in segs.items() if forsta(namn.get(l, '')) == 'person']
        person_bakom = False
        for j in person_ids:
            yp, xp = np.where(I == j)
            if len(xp):
                box = np.zeros_like(m); box[yp.min():yp.max()+1, xp.min():xp.max()+1] = 1
                person_bakom |= (m.astype(bool) & box.astype(bool)).sum() >= 0.8 * m.sum()
        if valuta and (sedel or person_bakom and re.search(r'\d', text)) and max(rw, rh) / min(rw, rh) >= 1.5 and bw >= 0.25*w:
            ut[i] = 'rektangulär valutagrafik; OCR: ' + ' / '.join(ord_)
            continue
        # En klistrad bild är pixelstilla trots rörelse strax utanför dess kant.
        # Kräv båda tidsriktningarna: en enstaka stillbild/klippgräns är inget bevis.
        inner = cv2.erode(m, np.ones((5, 5), np.uint8)).astype(bool)
        ring = cv2.dilate(m, np.ones((15, 15), np.uint8)).astype(bool) & ~m.astype(bool)
        bevis = []
        for granne in grannar:
            other = cv2.cvtColor(cv2.resize(granne, (w, h)), cv2.COLOR_BGR2GRAY)
            delta = cv2.absdiff(gray, other)
            # Inre variation krävs; stora enfärgade väggskyltar är inte ett vittne.
            bevis.append(inner.sum() >= 80 and ring.sum() >= 80 and gray[inner].std() > 20
                         and np.percentile(delta[inner], 90) <= 3 and np.median(delta[ring]) >= 12)
        if len(bevis) == 2 and all(bevis):
            ut[i] = 'rektangulär grafik pixelstilla i båda grannrutor medan omgivningen rör sig'
    return ut


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
    cap.release()
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
    grannrutor = {t['id']: [mitt[t['id']] + d for d in (-3, 3)
                           if t['ut'][0] <= mitt[t['id']] + d < t['ut'][1]] for t in meta['tagningar']}
    rutor = las_rutor(L.ROOT / 'data/format/kontroll/klipp' / (meta['klipp'] + '.mp4'),
                      set(mitt.values()) | {u for us in grannrutor.values() for u in us})

    # Förberedelse för återkomst: varje tagnings nät-lådor i sin grupps ram, och etiketter per tagning
    lador = {}; etik_per_t = {}
    for t in meta['tagningar']:
        sid = t['id']; o = L.ladda(out, mitt[sid], gk, 'obs_gpu')
        etik_per_t[sid] = {forsta(namn[l_]) for i_, l_ in o['segs'].items() if (o['I'] == i_).mean() >= MIN_ANDEL}
        if sid in nat:
            M4 = np.array(nat[sid]['transform']) if 'transform' in nat[sid] else None
            lador[sid] = [(forsta(b['etikett']), *i_grupp(M4, np.array(b['min']), np.array(b['max']))) for b in nat[sid]['bitar'] if b['instans'] >= 0]

    res = {'schema': 'valjare/2', 'klipp': nyckel, 'kod_sha256': sha_kort(__file__),
           'kallor': {f: sha_kort(out / f) for f in ('lokalitet.json', 'paket_L.json', 'nat.json', 'obs_gpu.json', 'pose2d.json')},
           'metod': {'vikter': VIKT, 'prior': {str(k): list(v) for k, v in PRIOR.items()}, 'prior_ovrigt': PRIOR_OVRIGT,
                     'rum_grupper': RUM_GRUPPER, 'rum_etiketter': RUM_ETIKETTER, 'min_andel': MIN_ANDEL,
                     'roll_min_andel': ROLL_ANDEL, 'roll_min_poang': ROLL_POANG, 'max_objekt': MAX_OBJEKT,
                     'bild_storlekstak': 0.40, 'skarpa_full_andel': 0.02,
                     'poang': 'viktat medel över tillgängliga signaler; osäkert segment x0,8; stöd jämförs utan hand'},
           'tagningar': {}}
    for t in meta['tagningar']:
        sid = t['id']; u = mitt[sid]; info = rep['tagningar'].get(sid, {})
        o = L.ladda(out, u, gk, 'obs_gpu'); I = o['I']; h, w = I.shape
        frame = rutor.get(u)
        segs = {int(i_): int(l_) for i_, l_ in o['segs'].items()}
        pers_ids = [i_ for i_, l_ in segs.items() if gk.get(l_) == 'person']
        pers_mask = np.isin(I, pers_ids)
        pose_ruta = pose['rutor'][u]['personer'] if pose and u < len(pose['rutor']) else []
        valda_pers, pose_koppling, persondjup = huvudpersoner(o, pers_ids, pose_ruta, pose['bild_px'] if pose else (w, h))
        ovl = L.overlagg_mask(frame, skarmtext, u / meta['fps'], h, w) if frame is not None else np.zeros((h, w), bool)
        grafik = grafikoverlagg(frame, [rutor[v] for v in grannrutor[sid] if v in rutor], I, segs, namn, skarmtext, u / meta['fps'])
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
        # Många små etiketter/reflexer får inte sätta referensen för stora släta motiv.
        referens = [v for i_, v in lapvar.items() if (I == i_).mean() >= 0.01 and i_ not in grafik]
        lap_med = float(np.median(referens)) if referens else None
        # V3
        v3fil = dst / f'{sid}_v3_essens.png'; kvar = v3_kvar(v3fil, (h, w)) if v3fil.is_file() else None
        # 2D-händer ur pose2d (mittrutan): handpunkt = handled + 0,35*(handled - armbåge), radie = halva underarmen
        hander2d = []
        if pose:
            sx, sy = w / pose['bild_px'][0], h / pose['bild_px'][1]
            for qi, q in enumerate(pose_ruta):
                if pose_koppling.get(qi) not in valda_pers:
                    continue
                kp = np.array(q['kp'])
                for e_, wr in ((7, 9), (8, 10)):
                    if kp[wr, 2] > 0.4 and kp[e_, 2] > 0.4:
                        a_ = kp[e_, :2] * (sx, sy); b_ = kp[wr, :2] * (sx, sy); fa = np.linalg.norm(b_ - a_)
                        if fa > 2:
                            hander2d.append((b_ + 0.35 * (b_ - a_), max(3.0, 0.5 * fa), pose_koppling[qi]))
        # 3D-händer ur kroppsspåret, i tagningens lokala ram, rutor kring mittrutan
        hander3d = []; spar_ok = 0
        M4 = np.array(nat[sid]['transform']) if sid in nat and 'transform' in nat[sid] else None
        hornen = nat_hörn(out / 'nat', nat[sid]) if sid in nat else {}
        # Personer finns avsiktligt inte i nat-näten. Associera därför spåret
        # genom projektion med paketets befintliga kamera, aldrig till ett
        # obefintligt personnät eller genom att anta att första spåret är motivet.
        torso = [ix[n] for n in ('c_spine0', 'c_spine1', 'c_spine2', 'c_spine3', 'l_uparm', 'r_uparm') if n in ix]
        kamera = next((t_['kamera']['nycklar'] for t_ in pak['tagningar'] if t_['id'] == sid), [])
        spar_agare = {}
        for pid, spar in pak.get('rorelse', {}).items():
            for tr in spar:
                if tr['tagning'] != sid or tr.get('tilltro', {}).get('overkropp') == 'skymd_antagen':
                    continue
                rows = [row for row in tr['rutor'] if abs(row[0] - u) <= 6]
                if not rows or not valda_pers or not kamera:
                    continue
                row = min(rows, key=lambda row: abs(row[0] - u))
                J = np.array(row[1:], float).reshape(-1, 3) / 1000.0
                cam = min(kamera, key=lambda k: abs(k[0] - row[0]))
                uv, z = L.project(J[torso], np.array(cam[1:4]), L.q2R(cam[4:8]), L.f_px(cam[8], W0), W0, H0)
                xy = uv * (w / W0, h / H0)
                ok = (z > 0) & np.isfinite(xy).all(1) & (xy[:, 0] >= 0) & (xy[:, 0] < w) & (xy[:, 1] >= 0) & (xy[:, 1] < h)
                if ok.sum() < 2:
                    continue
                xs, ys = xy[ok, 0].astype(int), xy[ok, 1].astype(int)
                match = {}
                for i_ in pers_ids:
                    md = cv2.dilate((I == i_).astype(np.uint8), np.ones((5, 5), np.uint8))
                    match[i_] = float(md[ys, xs].mean())
                agare = max(match, key=match.get) if match else None
                if agare not in valda_pers or match[agare] < 0.5:
                    continue
                spar_agare[pid] = agare
                spar_ok += 1
                for row in rows:
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
            # En OCR-rektangel bakom texten kan täcka en riktig stol/person. Kräv
            # grafiskt utseende också; dekortext är inte automatiskt skärmtext.
            textandel = float((m & ovl).sum() / m.sum())
            if i_ in grafik or (e in GRAFIK_ETIKETTER and textandel > 0.5):
                klass = 'overlagg'
            sig = {}
            # 1. hand
            if klass == 'objekt' and (hander2d or hander3d is not None):
                s2, s3, delar = 0.0, None, []; handtraff = 0
                for c_, r_, agare in hander2d:
                    disk = np.hypot(xx - c_[0], yy - c_[1]) <= r_; bas = (disk & ~pers_mask).sum()
                    if bas > 0:
                        v2 = min(1.0, (disk & m).sum() / bas / 0.5)
                        s2 = max(s2, v2); handtraff += v2 >= 0.5
                if hander2d:
                    delar.append(f'2D: täcker {s2 * 50:.0f} % av handens omgivning')
                if hander3d is not None and i_ in hornen:
                    P = hornen[i_]['P']; P = P[:: max(1, len(P) // 3000)]
                    d = float(min(np.min(np.linalg.norm(P - hh_, axis=1)) for hh_ in hander3d))
                    s3 = float(np.clip((KONTAKT_M[1] - d) / (KONTAKT_M[1] - KONTAKT_M[0]), 0, 1)) * tillit3d
                    delar.append(f'3D: närmaste nät-hörn {d:.2f} m från handen')
                if s3 and hander2d and s2 < 0.05:  # 3D nära men inget av föremålet syns vid handen i bilden: djupförväxling längs strålen
                    s3 *= 0.25; delar.append('3D utan stöd i 2D (x0,25)')
                v = max(s2, s3 or 0.0)
                # Kontakt bevisar inte grepp, särskilt inte en vilande hand bakom
                # ett glas. Handroll kräver synligt 2D-stöd när 2D finns.
                halls = v >= 0.5 and (s2 >= 0.5 if hander2d else (s3 or 0) >= 0.75)
                ext = robust_utbredning(hornen[i_]['P']) if i_ in hornen else None
                starkt_2d = s2 >= 0.8 or handtraff >= 2
                if v > 0 and (grupp in L.STOD or ((ext is not None and ext > STOR_YTA_M) or andel > STOR_YTA_ANDEL) and not starkt_2d):
                    v *= 0.5; halls = False; delar.append('stödyta/stor yta: berörs, hålls inte (x0,5)')
                elif starkt_2d and grupp not in L.STOD:
                    delar.append('starkt 2D-stöd/två händer: storlek hindrar inte grepp')
                sig['hand'] = {'varde': round(v, 3), 'halls': bool(halls), 'utbredning_robust_m': ext,
                               'skal': '; '.join(delar + [hk_skal])}
            if klass == 'person' and pose and u < len(pose['rutor']):  # kroppen: 2D-skelettets leder inom personens mask
                md = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool); bast_k = (0.0, 0)
                for qi, q in enumerate(pose_ruta):
                    if pose_koppling.get(qi) != i_:
                        continue
                    kp = np.array(q['kp']); ok = kp[:, 2] > 0.5
                    if ok.sum() >= 4:
                        xs = np.clip((kp[ok, 0] * w / pose['bild_px'][0]).astype(int), 0, w - 1); ys = np.clip((kp[ok, 1] * h / pose['bild_px'][1]).astype(int), 0, h - 1)
                        bast_k = max(bast_k, (float(md[ys, xs].mean()), int(ok.sum())))
                if bast_k[1]:  # Inget matchat skelett är saknad signal, inte bevis mot personen.
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
            # Mättnad först vid 40 %: 40 % golv måste kunna skiljas från 20 % vägg.
            cen = float(1 - rc[m].mean()); stor = min(1.0, math.sqrt(andel / 0.40))
            sig['bild'] = {'varde': round(0.5 * cen + 0.5 * stor, 3), 'skal': f'andel {andel * 100:.1f} %, centrering {cen:.2f}'}
            # 4. skärpa
            if i_ in lapvar and lap_med:
                kv = lapvar[i_] / max(lap_med, 1e-6)
                raw = float(np.clip(0.5 + 0.25 * math.log2(max(kv, 1e-6)), 0, 1))
                tillit = min(1.0, math.sqrt(andel / 0.02))
                sig['skarpa'] = {'varde': round(0.5 + tillit * (raw - 0.5), 3),
                                 'skal': f'Laplacevarians {lapvar[i_]:.0f} = {kv:.2f} x median för >=1 %; areatillit {tillit:.2f}'}
            # 5. semantik
            pv = 1.0 if klass == 'person' else prior(e)
            sig['semantik'] = {'varde': pv, 'skal': f"prior för '{e}'" + ('' if klass == 'person' else f" ({'innehåll' if pv == 1.0 else 'möbel/utrustning' if pv == 0.6 else 'dekor' if pv == 0.25 else 'övrigt'})")}
            # 6. V3
            if kvar is not None:
                sig['v3'] = {'varde': round(float(kvar[m].mean()), 3), 'skal': 'andel kvar (ej platt grå) i V3 essens'}
            total = poang(sig); utan_hand = poang(sig, utan=('hand',))
            anm = []
            if i_ in o.get('osakra', []):
                total *= 0.8; utan_hand *= 0.8; anm.append('osäkert segment (OneFormer < 0,75) x0,8')
            if i_ in grafik:
                anm.append(grafik[i_])
            if klass == 'person':
                if i_ not in valda_pers:
                    # Ett korrekt skelett i bakgrunden bevisar person, inte huvudroll.
                    total *= 0.5; utan_hand *= 0.5
                    anm.append('bakgrundsperson enligt yta/djup x0,5')
                if spar_ok and andel >= 0.01:
                    anm.append(f'kroppsspår finns i tagningen ({spar_ok})')
            poster.append({'instans': int(i_), 'etikett': e, 'grupp': grupp, 'klass': klass, 'poang': round(total, 3),
                           'poang_utan_hand': round(utan_hand, 3), 'huvudperson': i_ in valda_pers,
                           'andel_bild': round(andel, 4), 'nat_bit': i_ in hornen, 'signaler': sig, 'anm': anm})
        poster.sort(key=lambda p_: -p_['poang'])
        huvud = [p_ for p_ in poster if p_['klass'] in ('person', 'objekt')]
        rum = [p_ for p_ in poster if p_['klass'] == 'rum']; ovl_l = [p_ for p_ in poster if p_['klass'] == 'overlagg']
        # minsta mängd
        mm = []; tagna = set()
        def godkand(p_, roll):
            # Handomgivning=0 betyder ej hållet, inte oviktigt som fokus/stöd/plats.
            v = p_['poang_utan_hand'] if roll in ('fokus', 'stod', 'platsmarkor') else p_['poang']
            if roll == 'rumsankare':
                # Släta golv/väggar behöver varken restaurangprior eller textur.
                # Pröva samma rumspoäng som används vid rumssorteringen.
                v = 0.7 * p_['signaler']['bild']['varde'] + 0.3 * p_['poang']
            return p_['andel_bild'] >= ROLL_ANDEL[roll] and v >= ROLL_POANG[roll]
        def lagg(p_, roll, varfor):
            if p_['instans'] not in tagna and godkand(p_, roll):
                tagna.add(p_['instans']); mm.append({'instans': p_['instans'], 'etikett': p_['etikett'], 'klass': p_['klass'], 'roll': roll, 'varfor': varfor})
        pers = [p_ for p_ in huvud if p_['klass'] == 'person' and p_['instans'] in valda_pers]
        for p_ in pers:
            lagg(p_, 'person', f"förgrund: andel {p_['andel_bild'] * 100:.1f} %, mediandjup {persondjup[p_['instans']]}")
        obj = [p_ for p_ in huvud if p_['klass'] == 'objekt']
        for p_ in sorted([p_ for p_ in obj if godkand(p_, 'i_handen') and p_['signaler'].get('hand', {}).get('varde', 0) >= 0.5 and p_['signaler']['hand']['halls']],
                         key=lambda p_: -p_['signaler']['hand']['varde'])[:2]:
            lagg(p_, 'i_handen', p_['signaler']['hand']['skal'].split(';')[0])
        # En lampa kan komplettera miljön, men dess återkomst bevisar inte platsens
        # funktion. Ensam dekor får därför aldrig bära platsmarkörsrollen.
        plats = [p_ for p_ in obj if godkand(p_, 'platsmarkor') and prior(p_['etikett']) != 0.25
                 and p_['signaler'].get('aterkomst', {}).get('varde', 0) >= 0.5]
        if plats:
            lagg(plats[0], 'platsmarkor', plats[0]['signaler']['aterkomst']['skal'])
        fokus = [p_ for p_ in obj if godkand(p_, 'fokus') and (prior(p_['etikett']) != 0.25 or p_['andel_bild'] >= 0.05)]
        if fokus:
            lagg(fokus[0], 'fokus', f"högst poäng bland fokusdugliga objekt ({fokus[0]['poang']})")
        stod = [p_ for p_ in obj if godkand(p_, 'stod')]
        ej_hallna = [p_ for p_ in stod if not p_['signaler'].get('hand', {}).get('halls', False)]
        bast_stod = max((p_['poang_utan_hand'] for p_ in ej_hallna or stod), default=0)
        while stod and sum(x['klass'] == 'objekt' for x in mm) < MAX_OBJEKT:
            # Mjuk dämpning, ingen etikettspärr: flera stora matbrickor kan vara
            # viktiga, medan många små glas/lock inte bör gå före annan rekvisita.
            def stodvikt(p_):
                n = sum(x['klass'] == 'objekt' and x['etikett'] == p_['etikett'] for x in mm)
                return p_['poang_utan_hand'] * 0.85 ** n
            p_ = max(stod, key=stodvikt); v = stodvikt(p_); stod.remove(p_)
            if p_['instans'] in tagna:
                continue
            stor_synlig = p_['andel_bild'] >= 0.05
            if prior(p_['etikett']) == 0.25 and not stor_synlig and not any(prior(x['etikett']) != 0.25 and x['klass'] == 'objekt' for x in mm):
                # Ett förbjudet dekor-fokus får inte smyga tillbaka som ensamt
                # stödobjekt. Små lampor kompletterar en scen med funktionella objekt.
                continue
            if v >= 0.75 * bast_stod or stor_synlig:
                lagg(p_, 'stod', f"utan hand {p_['poang_utan_hand']}, dämpad {v:.3f}, referens {bast_stod:.3f}"
                     + ('; >=5 % synligt motiv/underlag' if stor_synlig else '; >=0,75 x referens'))
        # En enda strukturyta kan inte beskriva både golv och vägg/fläkt. Välj
        # upp till tre olika etiketter som klarar golven; area prioriteras inom
        # detta urval och etiketten får inte upprepas för väggfragment.
        rumval = sorted([p_ for p_ in rum if godkand(p_, 'rumsankare')],
                        key=lambda p_: -(0.7 * p_['signaler']['bild']['varde'] + 0.3 * p_['poang']))
        rumetik = set()
        for p_ in rumval:
            if p_['etikett'] not in rumetik and len(rumetik) < 3:
                lagg(p_, 'rumsankare', f"kompletterande strukturyta, andel {p_['andel_bild'] * 100:.1f} %")
                rumetik.add(p_['etikett'])
        flaggor = []
        if not obj:
            flaggor.append('inga objektinstanser: motivet kan sakna segmentering')
        for p_ in poster:
            if p_['etikett'] in ('wall', 'table') and p_['andel_bild'] > 0.8:
                flaggor.append(f"{p_['etikett']}#{p_['instans']} >80 %: kontrollera sammanslaget närbildsmotiv")
        for c_, r_, _ in hander2d:
            disk = np.hypot(xx-c_[0], yy-c_[1]) <= r_
            if disk.any() and np.isin(I[disk], [i for i, l in segs.items() if forsta(namn[l]) in ('wall', 'person')]).mean() > 0.9:
                flaggor.append('handomgivning >90 % wall/person: möjligt osegmenterat handobjekt')
        if frame is None:
            flaggor.append('originalruta saknas: skärpa och grafikdetektion kunde inte kontrolleras')
        elif lap_med is not None and lap_med < 10:
            # Diagnostik, inte radering: släta motiv och rörelseoskärpa kan inte
            # säkert skiljas åt med Laplacevarians ensam.
            flaggor.append('mycket låg Laplacevarians: kontrollera oskärpa/övergångsruta')
        res['tagningar'][sid] = {
            'ruta': u, 'rum': info.get('rum'), 'l7_grupp': grp, 'kroppsspar': spar_ok, 'hander_2d': len(hander2d),
            'huvudpersoner': valda_pers, 'pose_till_instans': pose_koppling, 'spar_till_instans': spar_agare,
            'flaggor': list(dict.fromkeys(flaggor)),
            'hander_3d': 0 if hander3d is None else len(hander3d), 'handkontakt_L2c': hk, 'v3': v3fil.is_file(),
            'topp3': [f"{p_['etikett']}#{p_['instans']} ({p_['poang']})" for p_ in huvud[:3]],
            'minsta_mangd': mm, 'rangordning': huvud, 'rum_klass': rum, 'overlagg': ovl_l}
        print(sid, 'topp3', res['tagningar'][sid]['topp3'], '| mängd', [f"{x['etikett']}:{x['roll']}" for x in mm])
    (dst / 'valjare.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('->', dst / 'valjare.json')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'duepiani')
