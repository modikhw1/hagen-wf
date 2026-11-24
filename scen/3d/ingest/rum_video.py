"""Rumshypotes ur hela videon: en videomodell ser klippet och föreslår ett rum där alla tells binds ihop (PIPE Öppet punkt 6).

    python rum_video.py <ingestmapp med tagningar.json> [--modell google/gemini-2.5-flash] [--ut <fil>]
    -> <ingestmapp>/brief/rum_video_<modell>.json (svar + användning + kostnad)

Modellen får hela klippet och tagningsgränserna i sekunder, så att dess tagnings-id stämmer med ingestens.
Svaret är en hypotes enligt grundregeln: den föreslår, originalets läsningar dömer. Inget skrivs till deklarationen.
Nyckeln läses ur miljövariabeln AI_GATEWAY_API_KEY eller första raden i filen som AI_GATEWAY_NYCKELFIL pekar på.
"""
import argparse, base64, json, os, urllib.request
from pathlib import Path

GATEWAY = 'https://ai-gateway.vercel.sh/v1/chat/completions'

XYZ = {'type': 'array', 'items': {'type': 'number'}, 'description': '[x, y, z] in metres: x right, y forward (depth) from the first shot camera, z up, floor z = 0'}
LEDTRADAR = {'type': 'array', 'items': {'type': 'string'}, 'description': 'concrete visual or audio tells this claim rests on, with shot ids'}
SCHEMA = {'type': 'object', 'required': ['klipptyp', 'lokal', 'ett_rum', 'zoner', 'karaktarer', 'objekt', 'tagningar', 'osakert'], 'properties': {
    'klipptyp': {'type': 'object', 'required': ['typ', 'beskrivning'], 'properties': {
        'typ': {'type': 'string', 'enum': ['en_kamera_en_scen', 'ihopklippt_samma_lokal', 'sketch_flera_roller', 'snabbklipp_olika_miljoer', 'annat']},
        'beskrivning': {'type': 'string'}, 'ledtradar': LEDTRADAR}},
    'lokal': {'type': 'object', 'required': ['typ', 'beskrivning'], 'properties': {'typ': {'type': 'string'}, 'beskrivning': {'type': 'string'}, 'ledtradar': LEDTRADAR}},
    'ett_rum': {'type': 'object', 'required': ['svar', 'sakerhet'], 'properties': {'svar': {'type': 'boolean'}, 'sakerhet': {'type': 'number'}, 'ledtradar': LEDTRADAR}},
    'zoner': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'beskrivning', 'mitt_m'], 'properties': {
        'id': {'type': 'string'}, 'beskrivning': {'type': 'string'}, 'mitt_m': XYZ, 'ledtradar': LEDTRADAR}}},
    'karaktarer': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'beskrivning', 'tagningar', 'hallning'], 'properties': {
        'id': {'type': 'string'}, 'namn': {'type': 'string'}, 'beskrivning': {'type': 'string'},
        'tagningar': {'type': 'array', 'items': {'type': 'string'}}, 'hallning': {'type': 'string', 'enum': ['star', 'sitter', 'gar', 'blandat']}, 'ledtradar': LEDTRADAR}}},
    'objekt': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'beskrivning', 'relevans', 'pos_m'], 'properties': {
        'id': {'type': 'string'}, 'beskrivning': {'type': 'string'},
        'relevans': {'type': 'string', 'enum': ['bar_scenen', 'satter_rummet', 'stryks']},
        'pa': {'type': 'string', 'description': 'what it rests on: floor, another object id, or a character id (held)'},
        'pos_m': XYZ, 'storlek_m': XYZ, 'ledtradar': LEDTRADAR}}},
    'tagningar': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'zon', 'karaktarer', 'kamera_pos_m', 'kamera_blick_mot'], 'properties': {
        'id': {'type': 'string'}, 'zon': {'type': 'string'}, 'karaktarer': {'type': 'array', 'items': {'type': 'string'}},
        'karaktar_pos_m': XYZ, 'kamera_pos_m': XYZ, 'kamera_blick_mot': {'type': 'string', 'description': 'what the camera points at (character, object or zone id)'},
        'samma_uppstallning_som': {'type': 'string', 'description': 'id of an earlier shot with the same camera set-up, or empty'}, 'ledtradar': LEDTRADAR}}},
    'osakert': {'type': 'array', 'items': {'type': 'string'}}}}

PROMPT = """You see a short-form video (usually filmed on a phone) cut into shots. Shot boundaries in seconds:
{tagningar}

Build ONE coherent spatial hypothesis of where this was filmed, so that a 3D scene can be reconstructed:
- What kind of clip this is (one camera one scene, cut together in one location, sketch with roles, or fast cuts between different places).
- The location type and how it is laid out. Decide whether all shots share one room; if they do, place every zone, character, object and camera in ONE metric frame (x right, y forward from the first shot's camera, z up, floor z = 0). Do not leave shots as separate islands. If two shots likely show the same spot from different angles, put them at the same coordinates.
- Every character (same person across shots gets one id), their posture, and where they stand.
- Important objects, their relevance (carries the scene / sets the room / to be dropped), what they rest on (floor, another object, or held by a character), position and rough size.
- For each shot: zone, visible characters, character and camera position, what the camera points at, and whether it reuses an earlier shot's set-up.
Bind the tells together: walls, tiles, windows, counters, light, clothing, props, on-screen text, sound. Give the tells behind each claim. Use realistic metric sizes (counter ~0.9 m high, person ~1.7 m). List what you are unsure about. Write descriptions in Swedish."""


# Variant scen3d: rummet i ett 3D-språk (golvpolygon, väggar med öppningar, orienterade lådor, kameror med yaw/pitch/FOV),
# med ingestens mätningar som givna fakta. Svaret kan projiceras och mätas mot originalet (rum_video_mat.py).
XY = {'type': 'array', 'items': {'type': 'number'}, 'description': '[x, y] metres'}
LADA = {'type': 'object', 'required': ['id', 'typ', 'mitt_m', 'storlek_m', 'yaw_grader', 'pa', 'relevans'], 'properties': {
    'id': {'type': 'string'}, 'typ': {'type': 'string'}, 'mitt_m': {**XYZ, 'description': 'bottom-centre [x, y, z] in metres'},
    'storlek_m': {**XYZ, 'description': '[width along local x, depth along local y, height]'}, 'yaw_grader': {'type': 'number'},
    'material': {'type': 'string'}, 'pa': {'type': 'string', 'description': '"golv", the id of the box it stands on, or the person id holding it'},
    'relevans': {'type': 'string', 'enum': ['bar_scenen', 'satter_rummet', 'stryks']}, 'ledtradar': LEDTRADAR}}
SCHEMA_3D = {'type': 'object', 'required': ['klipptyp', 'lokal', 'rum', 'lador', 'personer', 'tagningar', 'osakert'], 'properties': {
    'klipptyp': SCHEMA['properties']['klipptyp'], 'lokal': SCHEMA['properties']['lokal'],
    'rum': {'type': 'object', 'required': ['golv_polygon', 'takhojd_m', 'vaggar'], 'properties': {
        'golv_polygon': {'type': 'array', 'items': XY}, 'takhojd_m': {'type': 'number'},
        'vaggar': {'type': 'array', 'items': {'type': 'object', 'required': ['fran', 'till', 'material'], 'properties': {
            'fran': XY, 'till': XY, 'material': {'type': 'string'},
            'oppningar': {'type': 'array', 'items': {'type': 'object', 'required': ['typ', 'mitt_langs_m', 'bredd_m', 'underkant_m', 'hojd_m'], 'properties': {
                'typ': {'type': 'string'}, 'mitt_langs_m': {'type': 'number'}, 'bredd_m': {'type': 'number'}, 'underkant_m': {'type': 'number'}, 'hojd_m': {'type': 'number'}}}},
            'ledtradar': LEDTRADAR}}}}},
    'lador': {'type': 'array', 'items': LADA},
    'personer': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'langd_m'], 'properties': {
        'id': {'type': 'string'}, 'namn': {'type': 'string'}, 'beskrivning': {'type': 'string'}, 'langd_m': {'type': 'number'}, 'endast_hand': {'type': 'boolean'}}}},
    'tagningar': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'personer', 'kamera'], 'properties': {
        'id': {'type': 'string'},
        'personer': {'type': 'array', 'items': {'type': 'object', 'required': ['spar', 'person', 'fot_m', 'blick_yaw_grader'], 'properties': {
            'spar': {'type': 'string', 'description': 'tracked person id from the facts, or "otrackad"'}, 'person': {'type': 'string'},
            'fot_m': {**XY, 'description': 'floor point between the feet'}, 'blick_yaw_grader': {'type': 'number'}}}},
        'kamera': {'type': 'object', 'required': ['pos_m', 'yaw_grader', 'pitch_grader'], 'properties': {
            'pos_m': XYZ, 'yaw_grader': {'type': 'number'}, 'pitch_grader': {'type': 'number'}, 'samma_som': {'type': 'string'}}},
        'ledtradar': LEDTRADAR}}},
    'osakert': {'type': 'array', 'items': {'type': 'string'}}}}

PROMPT_3D = """You see a short-form phone video cut into shots. Reconstruct the place as a 3D scene description that a renderer can build directly.

Coordinate system: metres, right-handed, z up, floor z = 0. Yaw in degrees counter-clockwise from +x (yaw 90 = facing +y). Camera pitch in degrees, negative = looking down. Put the first shot's camera at x = 0, y = 0.

Measured facts from the footage (treat as given, do not contradict them):
- Frame: {bredd}x{hojd} px portrait, horizontal field of view {hfov:.1f} degrees, vertical {vfov:.1f} degrees, same lens in all shots.
- Shots, time ranges and tracked persons (bbox = median box in pixels [x0, y0, x1, y1], dist = measured camera-to-hip distance):
{fakta}

Describe:
1. rum: the floor polygon, ceiling height and walls (from/to points, material, openings such as windows, doors, hatches).
2. lador: furniture and objects as oriented boxes (bottom-centre, size, yaw, material). Small objects stand on a box ("pa" = that box id) or are held by a person ("pa" = person id).
3. personer: each distinct person once (same person across shots = same id), with height. A person seen only as a hand gets endast_hand = true.
4. tagningar: for every shot, each tracked person with their floor position and facing, and the camera pose. The camera pose must make each person appear where the bbox says, at the measured distance. Reuse the same pose (samma_som) when a shot repeats an earlier set-up.
If all shots are in one place, everything must live in this single frame; do not leave shots as separate islands. Bind together walls, tiles, windows, counters, light, clothing, props, on-screen text and sound. Give tells. List what you are unsure about. Write descriptions in Swedish."""


# Variant deklaration: modellen ser videon och skriver scenens deklaration (format 0.8) direkt. Geometrin räknas sedan av lösaren
# (deklaration_till_hand + plats.py) ur ingestens mätningar; modellen står för topologin, identiteterna, relevansen och grova mått.
PROMPT_DEKL = """You see a short-form phone video, cut into shots, of the clip "{klipp}". Write its scene declaration as ONE JSON object in format deklaration/0.8.
The declaration is consumed by a solver that places cameras and bodies from measurements; your job is the topology and the hypotheses the measurements cannot give:
which shots share a place and a camera set-up, who is who across shots, where the places lie relative to each other in one room, which furniture matters, and rough sizes.

Measured facts (given; do not contradict them):
- Frame {bredd}x{hojd} px portrait, horizontal FOV {hfov:.1f} deg, vertical {vfov:.1f} deg.
{fakta}

Rules:
- Frame convention: the first shot's camera place is at pos_m [0, 0, <height>] with blick_grader 90 (looking along +y). Everything else in that one frame.
- A role's standing place uses "las": {{"kamera_vid": <camera place>, "tagning": <shot>}} with pos_m null, so the solver puts the person at the measured distance from that camera. Choose camera positions so that persons who stand on the same spot in different shots land on the same point.
- Camera places are entries in "platser" with typ "staplats", roll null and their own id (e.g. kamera_1); "kameror.<shot>.kamera_vid" and "las.kamera_vid" always name such a camera place, never a shot id.
- The floor is the frame's zero: "golv": {{"hojd_m": [0.0, 0.0], "status": "antagen"}}.
- Every number is marked: status "antagen" (your guess) with [min, max] intervals wherever the format allows, "last" (from the facts above, with kalla), never "deklarerad" (only the owner declares).
- The footage may show little. Where you cannot tell, keep the most plausible hypothesis, widen the interval, and say so in a field "osakert" (list of strings).
- Descriptions in Swedish.

The general instruction for the declaration (written for an LLM that sees contact sheets; you see the video instead):
{uppdrag}

JSON schema of the declaration:
{schema}

Format example from a different clip (its provenance markings are older; follow the rules above, not its markings):
{exempel}

Answer with the JSON object only."""

# Variant uppsattning (pass 2): med den konsoliderade deklarationen som given karta bedömer modellen vad som är centralt för videons uppsättning.
# Varje element får en tröskel på en fast stege 0–1; ett reglage L bygger det som har tröskel <= L (0 = figurer i tomt rum, 1 = allt).
STEGE = [(0.0, 'figures only (the people)'), (0.2, 'room shell needed to read the space: floor, the main walls behind the action, their material and colour'),
         (0.4, 'furniture the characters touch, lean on, work at or stand behind'), (0.6, 'objects the action depends on (held, shown, weighed, handed over) and what they rest on'),
         (0.8, 'things that give the location its identity: equipment, displays, signage, characteristic fixtures'), (1.0, 'everything else: decor, background details, clutter')]
SCHEMA_UPP = {'type': 'object', 'required': ['sammanfattning', 'rekommenderad_niva', 'element'], 'properties': {
    'sammanfattning': {'type': 'string', 'description': 'what the set-up is and what must be present for the scene to read'},
    'rekommenderad_niva': {'type': 'number', 'description': 'lowest ladder level at which the clip still reads as itself'},
    'element': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'kategori', 'troskel', 'bar_handlingen', 'pa', 'tagningar', 'storlek_m'], 'properties': {
        'id': {'type': 'string', 'description': 'short snake_case id; reuse ids from the given declaration when the element is in it'},
        'beskrivning': {'type': 'string'},
        'kategori': {'type': 'string', 'enum': ['figur', 'rumsskal', 'mobel', 'foremal', 'utrustning', 'dekor', 'text']},
        'troskel': {'type': 'number', 'enum': [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]},
        'bar_handlingen': {'type': 'boolean'},
        'pa': {'type': 'string', 'description': '"golv", "vagg", the id of the element it rests on, or the role id that holds it'},
        'ankare': {'type': 'string', 'description': 'the place id in the declaration it belongs to (e.g. staplats_C, disk_C), or empty'},
        'tagningar': {'type': 'array', 'items': {'type': 'string'}},
        'storlek_m': {'type': 'array', 'items': {'type': 'number'}, 'description': '[width, depth, height] rough metres'},
        'bilder': {'type': 'array', 'description': 'every shot where the element is visible, with its box in that shot',
                   'items': {'type': 'object', 'required': ['tagning', 'box_2d'], 'properties': {'tagning': {'type': 'string'}, 'box_2d': {'type': 'array', 'items': {'type': 'number'}}}}},
        'bild': {'type': 'object', 'required': ['tagning', 'box_2d'], 'description': 'where the element is most clearly visible',
                 'properties': {'tagning': {'type': 'string'}, 'box_2d': {'type': 'array', 'items': {'type': 'number'}, 'description': '[ymin, xmin, ymax, xmax] normalised 0-1000 in that shot'}}},
        'ledtradar': {'type': 'array', 'items': {'type': 'string'}}}}}}}
PROMPT_UPP = """You see a short-form phone video, cut into shots. A consolidated scene declaration has already been made from several readings; treat it as the given map of places, roles and cameras:
{deklaration}

Your task now is only to judge what the set-up of this video consists of and how central each element is, so that a 3D scene can be built at any fidelity on this ladder:
{stege}
List every element you can see (people, room shell, furniture, objects, equipment, decor, on-screen text). For each, give the LOWEST ladder level at which it must be present (troskel),
whether the action depends on it, what it rests on or who holds it, which declared place it belongs to, the shots it appears in, a rough size,
and for furniture, objects and equipment the shot where it is most clearly visible with its bounding box (box_2d, [ymin, xmin, ymax, xmax], 0-1000),
plus a box for every other shot where it is visible (bilder), so that its position can be fitted across shots.
Then give the lowest level at which this clip still reads as itself (rekommenderad_niva), and say in one or two sentences what must be there for it to read.
Reuse ids from the declaration (roles A, B, C; places such as staplats_C, disk_C). Descriptions in Swedish."""


def fakta(I, T, fps):
    import math
    import numpy as np
    rader, bild = [], None
    for t in T['tagningar']:
        S = I / t['id']; meta = json.loads((S / 'meta.json').read_text(encoding='utf-8')); pers = las_json(S / 'personer.json') or {}
        bild = bild or (meta['bredd'], meta['hojd'], float(np.load(next(S.glob('sekvens_*.npz')), allow_pickle=True)['fokal']))
        spar = []
        for pid, rutor in sorted(pers.items()):
            box = np.median(np.array(list(rutor.values())), axis=0).round().astype(int).tolist()
            d = None
            for f in sorted((S / 'kropp' / pid).glob('*.npz'))[:1]: pass
            k = (las_json(I / 'brief' / 'lasning.json') or {}).get('tagningar', {}).get(t['id'], {})
            for p in k.get('personspar', []):
                if str(p.get('spar_id')) == pid: d = (p.get('kropp') or {}).get('kamera_till_hoft_m')
            spar.append(f"track {pid}: {len(rutor)} frames, bbox {box}" + (f", dist {d} m" if d else ''))
        rader.append(f"- {t['id']} {t['start'] / fps:.2f}–{(t['slut'] + 1) / fps:.2f} s: " + ('; '.join(spar) or 'no tracked person'))
    b, h, f = bild
    return '\n'.join(rader), dict(bredd=b, hojd=h, hfov=math.degrees(2 * math.atan(b / 2 / f)), vfov=math.degrees(2 * math.atan(h / 2 / f)))


def nyckel():
    k = os.environ.get('AI_GATEWAY_API_KEY')
    if not k and os.environ.get('AI_GATEWAY_NYCKELFIL'):
        k = Path(os.environ['AI_GATEWAY_NYCKELFIL']).read_text(encoding='utf-8').splitlines()[0].strip()
    if not k: raise SystemExit('Sätt AI_GATEWAY_API_KEY eller AI_GATEWAY_NYCKELFIL.')
    return k


def strikt(s):
    if isinstance(s, dict) and s.get('type') == 'object':
        return {**s, 'additionalProperties': False, 'properties': {k: strikt(v) for k, v in s['properties'].items()}}
    if isinstance(s, dict) and s.get('type') == 'array' and 'items' in s: return {**s, 'items': strikt(s['items'])}
    return s


def anropa_beacon(body, temperatur=0.1):
    """Samma anrop via ägarens Vertex-proxy (token-budget-beacon, se video/typer/lovable.mjs beaconDelar). Gateway-kroppen översätts till
    Vertex-format; svaret ges tillbaka i gatewayens form så att resten av skriptet är oförändrat. Argon får inget thinkingConfig (hänger annars)."""
    import time, urllib.error
    env = {}
    for rad in (Path(__file__).resolve().parents[3] / 'video' / '.env.local').read_text(encoding='utf-8-sig').splitlines():
        if '=' in rad and not rad.lstrip().startswith('#'): k, v = rad.split('=', 1); env[k.strip()] = v.strip().strip(chr(34) + chr(39))
    nyck, url = env.get('BEACON_NYCKEL'), env.get('BEACON_URL') or 'https://token-budget-beacon.lovable.app/api/public/v1/generate'
    if not nyck: raise SystemExit('BEACON_NYCKEL saknas i video/.env.local')
    m = body['model'].split('/')[-1]; contents = []
    for msg in body['messages']:
        delar = [msg['content']] if isinstance(msg['content'], str) else msg['content']; parts = []
        for d in delar:
            if isinstance(d, str): parts.append(dict(text=d))
            elif d.get('type') == 'text': parts.append(dict(text=d['text']))
            elif d.get('type') == 'file': parts.insert(0, dict(inlineData=dict(mimeType='video/mp4', data=d['file']['file_data'].split(',', 1)[1])))
        contents.append(dict(role='model' if msg['role'] == 'assistant' else 'user', parts=parts))
    gc = dict(temperature=temperatur, responseMimeType='application/json')
    rf = body.get('response_format') or {}
    if rf.get('type') == 'json_schema': gc['responseJsonSchema'] = strikt(rf['json_schema']['schema'])
    if 'argon' not in m: gc['thinkingConfig'] = dict(includeThoughts=True)
    data = json.dumps(dict(model=m, upstreamStream=True, contents=contents, generationConfig=gc)).encode()
    for forsok in range(4):
        t0 = time.time(); req = urllib.request.Request(url, data=data, headers={'authorization': 'Bearer ' + nyck, 'content-type': 'application/json'})
        try: j = json.load(urllib.request.urlopen(req, timeout=900)); break
        except urllib.error.HTTPError as e:
            fel = e.read()[:400]
            if e.code in (429, 500, 503) and forsok < 3: print(f'beacon {e.code}, försöker igen'); time.sleep(8 * (forsok + 1)); continue
            raise SystemExit(f'beacon HTTP {e.code}: {fel!r}')
    if j.get('placeholder'): raise SystemExit(f'beacon stopp: {json.dumps(j)[:400]}')
    text = ''.join(p.get('text', '') for p in (j.get('candidates') or [{}])[0].get('content', {}).get('parts', []) if not p.get('thought'))
    u = j.get('usageMetadata') or {}
    usage = dict(cost=(j.get('proxy') or {}).get('cost_usd'), in_tokens=u.get('promptTokenCount'), total_tokens=u.get('totalTokenCount'),
                 sekunder=round(time.time() - t0, 1), finish=(j.get('candidates') or [{}])[0].get('finishReason'))
    return dict(usage=usage, choices=[dict(message=dict(content=text))])


def las_json(f):
    for kodning in ('utf-8', 'cp1252'):
        try: return json.loads(Path(f).read_text(encoding=kodning))
        except UnicodeDecodeError: continue


def main():
    a = argparse.ArgumentParser(description=__doc__); a.add_argument('ingest'); a.add_argument('--modell', default='google/gemini-2.5-flash'); a.add_argument('--ut')
    a.add_argument('--variant', choices=['zoner', 'scen3d', 'deklaration', 'uppsattning'], default='zoner')
    a.add_argument('--via', choices=['gateway', 'beacon'], default='gateway', help='beacon = ägarens Vertex-proxy (BEACON_NYCKEL i video/.env.local)')
    a.add_argument('--temperatur', type=float, default=0.1, help='bara --via beacon')
    a.add_argument('--konsensus', help='konsoliderad deklaration för varianten uppsattning')
    a.add_argument('--reparera', type=int, default=0, help='antal reparationsvarv med validatorns fel (variant deklaration)')
    a.add_argument('--exempel', default=str(Path(__file__).resolve().parent / 'ut/e-dialog-guacamole-tagningar/plats/deklaration.json'),
                   help='formatexempel för varianten deklaration; aldrig klippets egen deklaration')
    a = a.parse_args(); I = Path(a.ingest)
    T = las_json(I / 'tagningar.json'); video = Path(T['klipp']); fps = T.get('fps') or 30.0
    if not T.get('fps'): print('Varning: fps saknas i tagningar.json, antar 30.')
    rader = '\n'.join(f"{t['id']}: {t['start'] / fps:.2f}–{(t['slut'] + 1) / fps:.2f} s" for t in T['tagningar'])
    if a.variant == 'scen3d':
        f, bild = fakta(I, T, fps); text, schema = PROMPT_3D.format(fakta=f, **bild), SCHEMA_3D; rader = f
    elif a.variant == 'deklaration':
        assert Path(a.exempel).resolve().parent.parent != I.resolve(), 'Exemplet får inte vara klippets egen deklaration.'
        from scenbrief import UPPDRAG, deklarationsschema
        f, bild = fakta(I, T, fps); rader = f
        text = PROMPT_DEKL.format(klipp=I.name, fakta=f, uppdrag=UPPDRAG, schema=json.dumps(deklarationsschema(), ensure_ascii=False),
                                  exempel=Path(a.exempel).read_text(encoding='utf-8'), **bild); schema = None
    elif a.variant == 'uppsattning':
        D = json.loads(Path(a.konsensus).read_text(encoding='utf-8'))
        karta = {k: D.get(k) for k in ('berattat_rum', 'roller', 'platser', 'kameror')}
        text = PROMPT_UPP.format(deklaration=json.dumps(karta, ensure_ascii=False), stege=chr(10).join(f'- {n}: {t}' for n, t in STEGE)); schema = SCHEMA_UPP
    else: text, schema = PROMPT.format(tagningar=rader), SCHEMA
    if a.via == 'beacon' and 'argon' in a.modell:     # Argon hänger på frågor om ljud/tal: ljud stryks som ledtråd
        text = text.replace(', on-screen text and sound.', ' and on-screen text.').replace(', on-screen text, sound.', ', on-screen text.')
    v = base64.b64encode(video.read_bytes()).decode()
    body = dict(model=a.modell, max_tokens=32000, messages=[dict(role='user', content=[dict(type='text', text=text),
                dict(type='file', file=dict(file_data='data:video/mp4;base64,' + v, filename=video.name))])],
                response_format=dict(type='json_schema', json_schema=dict(name='rumshypotes', strict=True, schema=schema)) if schema else dict(type='json_object'))
    def anropa(body):
        if a.via == 'beacon':
            d = anropa_beacon(body, a.temperatur); text = d['choices'][0]['message']['content']
            try: return d, text, json.loads(text)
            except ValueError: return d, text, dict(ratt_text=text)
        req = urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + nyckel(), 'Content-Type': 'application/json'})
        import time
        for forsok in range(6):     # 429 (för många anrop samtidigt): vänta och försök igen
            try: d = json.load(urllib.request.urlopen(req, timeout=600)); break
            except urllib.error.HTTPError as e:
                if e.code != 429 or forsok == 5: raise SystemExit(f'HTTP {e.code}: {e.read()[:400]!r}')
                time.sleep(10 * (forsok + 1))
        text = d['choices'][0]['message']['content']
        try: return d, text, json.loads(text)
        except ValueError: return d, text, dict(ratt_text=text)
    d, text, svar = anropa(body); anvandning = [d.get('usage')]; varv = []
    # Reparationsvarv (variant deklaration): validatorns fel går tillbaka i samma konversation, och modellen svarar med hela den rättade deklarationen.
    for i in range(a.reparera if a.variant == 'deklaration' else 0):
        import tempfile
        from scenbrief import granska
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / 'forslag.json'; f.write_text(json.dumps(svar, ensure_ascii=False), encoding='utf-8')
            try: g = granska(I, f, Path(td) / 'granskning.md')
            except Exception as e: g = dict(godkand=False, schemafel=[f'granskningen kraschade: {e}'])
        fel = {k: v for k, v in g.items() if isinstance(v, list) and v and k != 'oversattning'}
        if not g.get('oversattning', {}).get('ok', True): fel['oversattning'] = [str(g['oversattning'].get('logg', ''))[-800:]]
        varv.append(dict(varv=i, godkand=g.get('godkand'), fel={k: len(v) for k, v in fel.items()}))
        if g.get('godkand'): break
        body['messages'] += [dict(role='assistant', content=text), dict(role='user', content=[dict(type='text', text=
            'The validator rejected the declaration. Fix every error below without changing your hypothesis unless an error forces it, and answer with the complete corrected JSON object only.\n'
            + json.dumps(fel, ensure_ascii=False)[:12000])])]
        d, text, svar = anropa(body); anvandning.append(d.get('usage'))
        if i == a.reparera - 1:
            with tempfile.TemporaryDirectory() as td:
                f = Path(td) / 'forslag.json'; f.write_text(json.dumps(svar, ensure_ascii=False), encoding='utf-8')
                try: g = granska(I, f, Path(td) / 'granskning.md')
                except Exception as e: g = dict(godkand=False)
            varv.append(dict(varv='slut', godkand=g.get('godkand'), fel={k: len(v) for k, v in g.items() if isinstance(v, list) and v}))
    ut = Path(a.ut) if a.ut else I / "brief" / f"rum_video_{a.variant}_{a.modell.split('/')[-1]}.json"; ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text(json.dumps(dict(modell=a.modell, video=str(video), tagningar=rader.splitlines(), anvandning=anvandning[0] if len(anvandning) == 1 else anvandning,
                                  reparationsvarv=varv, svar=svar), ensure_ascii=False, indent=2), encoding='utf-8')
    kostnad = sum((u or {}).get('cost') or 0 for u in anvandning)
    print(f"{a.modell}: {len(anvandning)} anrop, kostnad {kostnad:.4f} USD, varv {varv} -> {ut}")


if __name__ == '__main__': main()
