"""0025 del A: relevanslistan för ett klipp, framtagen blint (utan ägarens input). Ett steg som går att köra vid ingest.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/relevans/relevans_steg.py <klipp> [--korning 1] [--modell google/gemini-2.5-flash]
<klipp> = ingestmappens namn (kand-kennysgelato-tagningar, e-dialog-guacamole-tagningar).
1. Underlaget samlas ur de filer som finns för klippet (allt valfritt, det som saknas redovisas):
   data/analys/<id>.json (scener: kamera, händer, saker), data/bank/sallning/<id>.json (innehåll, typ), data/e5/pro-b/<id>.json
   (helhet, handling, kärna, platser, beats), deklarationen (berättat rum, roller, relevans), semantiken (sammanfattning, kärna, props,
   repliker), och planens id (objekt, personer, handföremål, skärmtext).
2. En modell (gatewayen, som ingest/rum_video.py) ser tagningarnas kontaktblad (brief/kontakt_S*.jpg) och får underlaget som givna fakta.
   Den föreslår klippets mening och en post per sak, med ett litet allmänt ordförråd (TYP, ROLL, BEHANDLING).
Ut: relevans/<klipp>/korning_<n>.json (svar, användning, kostnad), prompt_<n>.txt, underlag.json; relevans.json = körning 1.
Gemini föreslår; den är inte källa för vad ägaren tycker.
"""
import argparse, base64, json, os, urllib.request
from pathlib import Path

HIT = Path(__file__).resolve().parent; ROT = HIT.parents[3]; ING = ROT / 'scen/3d/ingest/ut'; KON = ROT / 'scen/3d/kontrakt/ut'
GATEWAY = 'https://ai-gateway.vercel.sh/v1/chat/completions'
TYP = ['person', 'kroppsdel', 'foremal_i_hand', 'foremal', 'mobel', 'bakgrund', 'text', 'kamera']
ROLL = ['bar', 'ramar', 'brus']
BEHANDLING = ['eget_lager', 'forenklad_form', 'bakas_in_i_personen', 'utelamnas']
KALLA = ['matt', 'last', 'antagen']
# klippets deklaration och plan (de senaste som kedjan använder)
KLIPP = {'kand-kennysgelato-tagningar': dict(dekl='plats_n06-hand/deklaration_upplost.json', plan='kand-kennysgelato_n06-hand/narvaro/plan.json'),
         'e-dialog-guacamole-tagningar': dict(dekl='plats/deklaration.json', plan='e-dialog-guacamole_grupp/narvaro/plan.json')}

SCHEMA = {'type': 'object', 'required': ['mening', 'poster'], 'properties': {
    'mening': {'type': 'string', 'description': 'the point of the clip in one or two sentences: what a viewer must understand'},
    'poster': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'namn', 'typ', 'roll', 'varfor', 'tagningar', 'samspel', 'kalla', 'behandling', 'plan_id'], 'properties': {
        'id': {'type': 'string', 'description': 'short snake_case id; reuse the plan id when the thing exists in the plan'},
        'namn': {'type': 'string'}, 'typ': {'type': 'string', 'enum': TYP}, 'roll': {'type': 'string', 'enum': ROLL},
        'varfor': {'type': 'string', 'description': 'one sentence: why this role'},
        'tagningar': {'type': 'array', 'items': {'type': 'string'}}, 'samspel': {'type': 'array', 'items': {'type': 'string'}, 'description': 'ids it touches or stands in relation to'},
        'kalla': {'type': 'string', 'enum': KALLA}, 'behandling': {'type': 'string', 'enum': BEHANDLING},
        'plan_id': {'type': 'string', 'description': 'matching id in the plan or declaration, or empty string'}}}}}}

PROMPT = """You decide what matters in a short vertical video clip, so that a lightweight editable 3D version of it keeps what carries the clip's meaning and drops the rest.
The 3D version will later be changed with words ("make it longer", "swap the background", "let her smile after she gets the food"). It does not need every detail; it needs what makes the point of the clip come through.

You see one contact sheet per shot (frames left to right in time). The facts below come from earlier analysis steps and are given; you may disagree only where the images clearly show otherwise.

GIVEN FACTS
{fakta}

TASK
1. mening: the point of the clip in one or two sentences.
2. poster: one entry per thing that appears or is implied (people, body parts that act, objects in hands, objects, furniture, background, on-screen text, the camera itself).
   - typ: one of {typ}
   - roll: "bar" = without it the point falls; "ramar" = packages the scene (place, setting) but the point survives a simpler version; "brus" = can be left out
   - behandling: "eget_lager" = its own layer in the decomposition (isolated, completed where hidden); "forenklad_form" = a simple shape (box, plane, coloured wall); "bakas_in_i_personen" = generated together with the person (e.g. an object held in the hand); "utelamnas" = left out
   - kalla: "matt" if it comes from the measured plan or ingest facts, "last" if you read it from the images, "antagen" if inferred
   - plan_id: the matching id from the plan or declaration when it exists, else ""
   - samspel: the ids it touches or stands in relation to
Keep the vocabulary general; do not invent new roles or treatments. Answer with JSON only."""


def las(p):
    try: return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError): return None


def underlag(klipp):
    k = KLIPP[klipp]; T = las(ING / klipp / 'tagningar.json'); vid = Path(T['klipp']).stem; did = vid.removeprefix('kand-')
    u, saknas = {}, []
    a = las(ROT / f'data/analys/{did}.json')
    if a: u['innehallsanalys_per_scen'] = [dict(start=s['start'], slut=s['slut'], kamera=s['kamera']['ord'], hander_andel=s['hander']['andel'], saker=s.get('saker'), utsnitt=s['utsnitt']['varde']) for s in a['scener']]
    else: saknas.append('data/analys')
    b = las(ROT / f'data/bank/sallning/{did}.json')
    if b: u['sallning'] = {x: b.get(x) for x in ('innehall', 'typ', 'personer_max', 'inne_i_verksamheten', 'skal')}
    else: saknas.append('data/bank/sallning')
    e = las(ROT / f'data/e5/pro-b/{did}.json')
    if e: u['innehallsbedomning'] = {x: e.get(x) for x in ('helhet', 'handling', 'karna', 'mall', 'platser', 'beats', 'redigeringsskamt')}
    else: saknas.append('data/e5')
    d = las(ING / klipp / k['dekl'])
    if d: u['deklaration'] = {x: d.get(x) for x in ('berattat_rum', 'roller', 'relevans') if d.get(x)}
    s = las(ING / klipp / 'semantik/semantik.json')
    if s: u['semantik'] = {x: s['data'].get(x) for x in ('klipp', 'props', 'repliker', 'skarmtext', 'plats', 'ej_personer')}
    else: saknas.append('semantik')
    p = las(KON / k['plan'])
    if p:
        u['plan'] = dict(objekt=sorted({o['id'].split(':')[0] + (':' + o['deltyp'] if o.get('deltyp') else '') for o in p['objekt']}), personer=[x['id'] for x in p['personer']],
                         handforemal=[dict(id=h['id'], foremal=h['foremal'], person=h['person']) for h in (p.get('handforemal') or [])],
                         skarmtext=[dict(id=t['id'], text=t['text']) for t in (p.get('skarmtext') or [])])
    u['tagningar'] = [dict(id=t['id'], sekunder=[round(t['start'] / T['fps'], 2), round((t['slut'] + 1) / T['fps'], 2)]) for t in T['tagningar']]
    return u, saknas


def main():
    a = argparse.ArgumentParser(); a.add_argument('klipp'); a.add_argument('--korning', type=int, default=1); a.add_argument('--modell', default='google/gemini-2.5-flash')
    x = a.parse_args(); ut = HIT / x.klipp; ut.mkdir(parents=True, exist_ok=True)
    u, saknas = underlag(x.klipp); (ut / 'underlag.json').write_text(json.dumps(dict(underlag=u, saknas=saknas), ensure_ascii=False, indent=1), encoding='utf-8')
    text = PROMPT.format(fakta=json.dumps(u, ensure_ascii=False, indent=1), typ=TYP); (ut / f'prompt_{x.korning}.txt').write_text(text, encoding='utf-8')
    bilder = sorted((ING / x.klipp / 'brief').glob('kontakt_S*.jpg'))
    inn = [dict(type='text', text=text)] + [c for f in bilder for c in (dict(type='text', text=f'Contact sheet, shot {f.stem.split("_")[1]}:'),
                                                                         dict(type='image_url', image_url=dict(url='data:image/jpeg;base64,' + base64.b64encode(f.read_bytes()).decode())))]
    body = dict(model=x.modell, max_tokens=16000, messages=[dict(role='user', content=inn)],
                response_format=dict(type='json_schema', json_schema=dict(name='relevans', strict=True, schema=SCHEMA)))
    k = os.environ.get('AI_GATEWAY_API_KEY') or Path(os.environ['AI_GATEWAY_NYCKELFIL']).read_text(encoding='utf-8').splitlines()[0].strip()
    req = urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=600)); svar = json.loads(d['choices'][0]['message']['content'])
    r = dict(klipp=x.klipp, korning=x.korning, modell=x.modell, kostnad_usd=(d.get('usage') or {}).get('cost'), bilder=[f.name for f in bilder],
             saknat_underlag=saknas, ordforrad=dict(typ=TYP, roll=ROLL, behandling=BEHANDLING, kalla=KALLA), **svar)
    (ut / f'korning_{x.korning}.json').write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
    if x.korning == 1: (ut / 'relevans.json').write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
    print(x.klipp, x.korning, 'kostnad', r['kostnad_usd'], '|', r['mening'])
    for p in r['poster']: print('  ', p['roll'], p['typ'], p['id'], '->', p['behandling'], '|', p['varfor'][:90])


if __name__ == '__main__': main()
