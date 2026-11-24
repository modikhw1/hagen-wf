"""semantik_ingest.py: ett klipp -> semantik.json, kallas semantiska lager som ett utkast (modellbedömt), bundet till uppmätta spår.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/semantik/semantik_ingest.py <klipp> [--modell gemini-3.5-flash] [--torrkorning]
    scen/.venv/Scripts/python.exe scen/3d/kontrakt/semantik/semantik_ingest.py <klipp> --bearbeta-svar <svar_ra.json>   (ingen anrop)

Ett Gemini-anrop per klipp via gratisnyckeln (video/.env.local: GEMINI_API_KEY_GRATIS), samma slutpunkt och samma sätt att skicka video
(inlineData, video/mp4, x-goog-api-key) som video/typer/lovable.mjs (LOVABLE_KONTO=aistudio). Skillnaden: lovable.mjs skickar bara video;
här följer ett kontaktblad per tagning med, där varje uppmätt spår är inritat och märkt "S3:1". Nyckeln skrivs aldrig ut.
Anropen räknas i ut/anrop.json; taket är 10 anrop totalt för det här arbetet. Ingen automatisk omförsökning: varje försök räknas.

Svaret valideras mot semantik.schema.json och mot mätningen (spår och tagningar måste finnas). Ogiltigt svar skrivs till
ut/<klipp>/avvisat.json med felen och repareras aldrig.
"""
import argparse
import base64
import json
import sys
import time
from pathlib import Path

import cv2
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sem_gemensamt import (HIT, ROT, UT, ladda, skriv, sha256, sha_bytes, klipp_vagar, tagningar, sparlista, validera)  # noqa: E402
from kontaktblad import blad, spartabell  # noqa: E402

PROMPT_VERSION = 'semantik-prompt/1'
STANDARD_MODELL = 'gemini-3.5-flash'
TAK = 10
SLUTPUNKT = 'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent'

PROMPT = """You analyse a short vertical social-media video (a sketch, a pitch to camera or a place showcase) so that it can be rebuilt as a 3D scene.
You get: (1) the video with its audio, (2) a shot table, (3) for every shot one CONTACT SHEET: up to 6 frames in time order (left to right, top to bottom),
each frame headed with the shot name, the source frame number and the time in seconds. A tracker has measured the people in each shot. Every measured
track is drawn as a coloured box labelled SHOT:TRACKID (for example S3:1) and listed in the track table. The label is a key into measured data.

HARD RULES
- Track ids are only unique inside one shot. S3:1 and S1:1 are different tracks; you decide whether they are the same person. Box colours carry no meaning between shots.
- The tracker is not always right. A box can be a person in the story, but also a foreground arm or hand (for example a point-of-view arm that holds something
  toward the camera), a passer-by or another guest in the background, a reflection, a poster or a screen, or a false detection. Look at the sheet and decide for
  every single track. Every track on every sheet must appear exactly once: either inside a person's "spar" list or in "ej_personer" with a reason.
- A person is someone who takes part in the story. Give people stable ids P1, P2, ... across the whole clip. Match people between shots by face, hair, clothes, build,
  and the surroundings. People in the same uniform are different people unless something shows they are the same. If a track shows no face and no distinguishing
  feature, say "osaker" instead of guessing. A shot can show a person who is NOT tracked (for example speaking off screen): then simply list no track for that shot.
- Answer "osaker" (or confidence "osaker") wherever you cannot tell. Never invent. An empty list is a valid answer. Do not fill in speech you cannot hear and
  on-screen text you cannot read.
- Speech: write every spoken line in the original language exactly as spoken, in time order, with the speaker's person id ("okand" if you cannot tell who speaks),
  the shot where the line starts, an approximate start and end in seconds on the source clock, and the language code. If there is no speech, return an empty list.
- On-screen text: text overlaid or visible and meaningful (subtitles, titles, price boards). Quote it exactly, per shot.
- Camera set-ups: group shots that were filmed from the same spot and angle (typical for a conversation: shot / reverse shot, the same framing returning later).
  Not merely "same room".
- Pairs: for each pair of people that interact, say whether they face each other (vander_mot_varandra) and what is between them / how they are arranged (over):
  samma_bord (same table), separata_bord (two separate tables across the room), disk_mellan (a counter between them), sida_vid_sida, ingenting_mellan, osaker.
- Place and placement: say what kind of place it is. Pick rumsmall_forslag only if one of the templates really fits; otherwise "ingen_passar".
  Templates: notan_tva_bord = two separate tables with one chair each, the two people facing each other across the room; restaurang_tva = one shared table with two chairs;
  bar_disk = a bar counter with standing positions behind it and a shelf; fiktiv_lokal = an invented generic venue. For each person give posture
  (sitter/star/rorlig) and anchor kind: sate = seated on chair or stool, bordskant = at a table edge, staplats = standing at a spot in the room, sta_bakom = standing behind a counter,
  annat/ingen_passar when none fits; and the furniture (vid_del) they sit or stand at.
- Props: only objects the action depends on (something handed over, shown, eaten, weighed, paid with), with the person who holds or uses it. English snake_case type.
- Shot function (funktion), one per shot, in this vocabulary: krok (opening hook), uppbyggnad (build-up), vandning (the turn, twist or escalation), punchline (the payoff
  of the joke or point), visning (showing food, drink, product or place), tilltal (a person talks to the camera), avslut (closing beat), ingen (none of them), osaker.
  Add one sentence about what happens in the shot.
- Free text in Swedish, short and concrete. Spoken lines and on-screen text in their original language. Field names and enum values exactly as in the response schema.
"""


def las_nyckel():
    env = ROT / 'video/.env.local'
    if not env.exists(): raise SystemExit('video/.env.local saknas')
    for rad in env.read_text(encoding='utf-8').splitlines():
        if rad.startswith('GEMINI_API_KEY_GRATIS='):
            v = rad.split('=', 1)[1].strip().strip('"\'')
            if v: return v
    raise SystemExit('GEMINI_API_KEY_GRATIS saknas eller är tom i video/.env.local')


def sandbar_schema(s):
    """Schemat som skickas: samma som semantik.schema.json utan $schema/$id."""
    s = json.loads(json.dumps(s)); s.pop('$schema', None); s.pop('$id', None)
    return s


def skottar(klipp):
    """Allt som behövs för att bygga begäran: tagningar, spår, blad (jpeg-bytes), tabell."""
    v = klipp_vagar(klipp); shots = tagningar(v['ingest']); data = []
    for sh in shots:
        sp = sparlista(sh); bild, rutor = blad(sh, sp)
        ok, jpg = cv2.imencode('.jpg', bild, [cv2.IMWRITE_JPEG_QUALITY, 82])
        data.append(dict(shot=sh, spar=sp, jpg=jpg.tobytes(), rutor=rutor))
    return v, data


def tabelltext(klipp, data):
    sh0 = data[0]['shot']; N = sum(d['shot']['N'] for d in data); fps = sh0['fps']
    rader = [f'CLIP {klipp}: {len(data)} shots, {N} frames, {fps} fps, {N / fps:.2f} s. Frame size {sh0["bredd"]}x{sh0["hojd"]}.',
             'SHOT TABLE (source frame range [first, last], seconds):']
    for d in data:
        s = d['shot']
        rader.append(f'{s["id"]}: frames {s["start"]}..{s["slut"] - 1} ({s["start"] / fps:.2f}-{s["slut"] / fps:.2f} s), {len(d["spar"])} measured track(s)')
    rader.append('TRACK TABLE (measured; box height/width are fractions of the frame):')
    for d in data: rader += [r.strip() for r in spartabell(d['shot'], d['spar'])]
    return '\n'.join(rader)


def bygg_begaran(video, klipp, data, schema):
    """Returnerar (body, sammanfattning). sammanfattning har hashar och storlekar men ingen base64."""
    tabell = tabelltext(klipp, data); vb = Path(video).read_bytes()
    parts = [dict(inlineData=dict(mimeType='video/mp4', data=base64.b64encode(vb).decode())),
             dict(text=PROMPT), dict(text=tabell)]
    blad_hash = {}
    for d in data:
        sid = d['shot']['id']
        parts.append(dict(text=f'CONTACT SHEET for {sid} (frames {d["shot"]["start"]}..{d["shot"]["slut"] - 1}; the frames shown are local frames {d["rutor"]}):'))
        parts.append(dict(inlineData=dict(mimeType='image/jpeg', data=base64.b64encode(d['jpg']).decode())))
        blad_hash[sid] = sha_bytes(d['jpg'])
    parts.append(dict(text='Now answer with the JSON described by the response schema. Every track listed in the track table must be accounted for.'))
    body = dict(contents=[dict(role='user', parts=parts)],
                generationConfig=dict(temperature=0.1, responseMimeType='application/json', responseJsonSchema=sandbar_schema(schema), maxOutputTokens=32768))
    ind = dict(video_sha256=sha256(video), video_byte=len(vb), prompt_sha256=sha_bytes(PROMPT.encode()), tabell_sha256=sha_bytes(tabell.encode()),
               schema_sha256=sha256(HIT / 'semantik.schema.json'), kontaktblad_sha256=blad_hash,
               personer_json_sha256={d['shot']['id']: sha256(d['shot']['mapp'] / 'personer.json') for d in data},
               tagningar_json_sha256=(sha256(Path(data[0]['shot']['mapp']).parent / 'tagningar.json') if (Path(data[0]['shot']['mapp']).parent / 'tagningar.json').exists() else None),
               begaran_byte=len(json.dumps(body)))
    return body, ind, tabell


# ------------------------------------------------------------ anropsräknare
def anropslogg():
    p = UT / 'anrop.json'
    return p, (ladda(p) if p.exists() else [])


def antal_skickade():
    return sum(1 for a in anropslogg()[1] if a.get('skickad'))


def anropa(body, modell, klipp):
    p, logg = anropslogg()
    if antal_skickade() >= TAK: raise SystemExit(f'Taket på {TAK} anrop är nått. Inget skickas.')
    nyckel = las_nyckel()
    post = dict(nr=antal_skickade() + 1, klipp=klipp, modell=modell, tid=time.strftime('%Y-%m-%d %H:%M:%S'), skickad=True, status='skickad', http=None, tokens=None)
    logg.append(post); skriv(p, logg)          # räknas innan svaret kommer: ett avbrutet anrop räknas ändå
    t0 = time.perf_counter()
    try:
        # Ingen nyckel i URL; undantagstexter från requests skrivs inte ut (de kan bära rubriker).
        r = requests.post(SLUTPUNKT.format(m=modell), headers={'x-goog-api-key': nyckel, 'content-type': 'application/json'}, json=body, timeout=300)
    except requests.RequestException as e:
        post.update(status='natfel', http=None, typ=type(e).__name__); skriv(p, logg)
        raise SystemExit('Nätfel mot Gemini (' + type(e).__name__ + '). Anropet räknas.') from None
    post.update(http=r.status_code, ms=round((time.perf_counter() - t0) * 1000))
    if r.status_code != 200:
        post['status'] = 'http_fel'; post['svar_borjan'] = r.text[:300]; skriv(p, logg)
        raise SystemExit(f'Gemini svarade HTTP {r.status_code}: {r.text[:300]}')
    j = r.json(); um = j.get('usageMetadata', {})
    post.update(status='ok', tokens={k: um.get(k) for k in ('promptTokenCount', 'candidatesTokenCount', 'thoughtsTokenCount', 'totalTokenCount')}); skriv(p, logg)
    return j, post


# ------------------------------------------------------------ kontroll mot mätningen
def kontrollera_mot_matning(d, data):
    """(fel, varningar). Fel = svaret pekar på något som inte finns (avvisas). Varning = ofullständigt men användbart."""
    fel, var = [], []
    sp = {x['shot']['id']: x['spar'] for x in data}; shots = list(sp)
    pid = [p['id'] for p in d['personer']]
    if len(set(pid)) != len(pid): fel.append('personer: dubbla id')
    ref = set()
    def spar(t, s, vem):
        if t not in sp: fel.append(f'{vem}: okänd tagning {t}'); return
        if s not in sp[t]: fel.append(f'{vem}: {t}:{s} är inte ett uppmätt spår (finns: {sorted(sp[t])})'); return
        if (t, s) in ref: fel.append(f'{vem}: {t}:{s} används två gånger')
        ref.add((t, s))
    for p in d['personer']:
        for x in p['spar']: spar(x['tagning'], x['spar_id'], f'person {p["id"]}')
    for e in d['ej_personer']: spar(e['tagning'], e['spar_id'], 'ej_personer')
    alla = {(t, s) for t in sp for s in sp[t]}
    for t, s in sorted(alla - ref, key=lambda x: (int(x[0][1:]), x[1])): var.append(f'spår {t}:{s} är varken person eller ej_person i svaret')
    kant = set(pid) | {'okand'}
    for r in d['repliker']:
        if r['talare'] not in kant: fel.append(f'replik {r["id"]}: okänd talare {r["talare"]}')
        if r['tagning'] not in sp: fel.append(f'replik {r["id"]}: okänd tagning {r["tagning"]}')
        if r['slut_s'] < r['start_s']: fel.append(f'replik {r["id"]}: slut före start')
    for p in d['par']:
        for k in ('a', 'b'):
            if p[k] not in pid: fel.append(f'par: okänd person {p[k]}')
        for t in p['tagningar']:
            if t not in sp: fel.append(f'par: okänd tagning {t}')
    for p in d['placeringar']:
        if p['person'] not in pid: fel.append(f'placering: okänd person {p["person"]}')
        for t in p['tagningar']:
            if t not in sp: fel.append(f'placering: okänd tagning {t}')
    for o in d['props']:
        if o['hallare'] not in set(pid) | {'ingen', 'osaker'}: fel.append(f'prop {o["id"]}: okänd hållare {o["hallare"]}')
        for t in o['tagningar']:
            if t not in sp: fel.append(f'prop {o["id"]}: okänd tagning {t}')
    for s in d['skarmtext']:
        if s['tagning'] not in sp: fel.append(f'skärmtext: okänd tagning {s["tagning"]}')
    sett = set()
    for k in d['kamerauppstallningar']:
        for t in k['tagningar']:
            if t not in sp: fel.append(f'kamerauppställning {k["id"]}: okänd tagning {t}')
            elif t in sett: fel.append(f'kamerauppställning: {t} i två grupper')
            sett.add(t)
    for t in shots:
        if t not in sett: var.append(f'{t} saknas i kamerauppställningarna')
    funk = [x['tagning'] for x in d['tagningar']]
    for t in funk:
        if t not in sp: fel.append(f'tagningar: okänd tagning {t}')
    if len(set(funk)) != len(funk): fel.append('tagningar: en tagning har flera poster')
    for t in shots:
        if t not in funk: var.append(f'{t} saknar funktionspost')
    return fel, var


def behandla_svar(raw_json, klipp, data, ind, post, modell, ut, ursprung_typ='modellbedomd'):
    """Validerar svaret och skriver semantik.json (eller avvisat.json). Reparerar inget. Returnerar (ok, sokvag)."""
    schema = ladda(HIT / 'semantik.schema.json'); ut = Path(ut); ut.mkdir(parents=True, exist_ok=True)
    try:
        j = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
        delar = j['candidates'][0]['content']['parts']
        text = ''.join(p.get('text', '') for p in delar if not p.get('thought'))
        fin = j['candidates'][0].get('finishReason')
        d = json.loads(text)
    except Exception as e:
        skriv(ut / 'avvisat.json', dict(orsak='svaret är inte tolkningsbar JSON', undantag=type(e).__name__ + ': ' + str(e)[:200], ursprung=dict(typ=ursprung_typ, modell=modell, prompt_version=PROMPT_VERSION)))
        return False, ut / 'avvisat.json'
    fel = validera(d, schema)
    varn = []
    if not fel:
        f2, varn = kontrollera_mot_matning(d, data); fel += f2
    if fin not in (None, 'STOP'): fel.append(f'finishReason {fin}')
    if fel:
        skriv(ut / 'avvisat.json', dict(orsak='svaret uppfyller inte schemat eller mätningen', fel=fel, varningar=varn,
                                         ursprung=dict(typ=ursprung_typ, modell=modell, prompt_version=PROMPT_VERSION), indata=ind, anrop=post, svar=d))
        return False, ut / 'avvisat.json'
    ut_ = dict(schema_version='semantik/1', klipp=klipp,
               ursprung={'typ': ursprung_typ, 'modell': modell, 'prompt_version': PROMPT_VERSION,
                         'not': 'Allt i data är modellbedömt och inte mätt. Spår (tagning + spar_id) är mätta nycklar; vem de är, roller, ordning, platsval och funktioner är bedömningar.'},
               indata=ind, anrop=post, kontroll=dict(fel=[], varningar=varn), data=d)
    skriv(ut / 'semantik.json', ut_)
    avv = ut / 'avvisat.json'
    if avv.exists(): avv.rename(ut / f'avvisat_tidigare_{int(time.time())}.json')
    return True, ut / 'semantik.json'


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('klipp'); a.add_argument('--modell', default=STANDARD_MODELL); a.add_argument('--torrkorning', action='store_true')
    a.add_argument('--bearbeta-svar', help='Validera ett redan sparat råsvar (svar_ra.json) utan anrop.')
    a.add_argument('--ny', action='store_true', help='Anropa även om ut/<klipp>/svar_ra.json redan finns (räknas som ett nytt anrop).')
    x = a.parse_args()
    v, data = skottar(x.klipp); schema = ladda(HIT / 'semantik.schema.json'); ut = v['ut']; ut.mkdir(parents=True, exist_ok=True)
    for d in data: (ut / 'blad').mkdir(exist_ok=True); (ut / 'blad' / f'{d["shot"]["id"]}.jpg').write_bytes(d['jpg'])
    body, ind, tabell = bygg_begaran(v['video'], x.klipp, data, schema)
    (ut / 'tabell.txt').write_text(tabell, encoding='utf-8')
    print(f'{x.klipp}: {len(data)} tagningar, begäran {ind["begaran_byte"] / 1e6:.2f} MB (video {ind["video_byte"] / 1e6:.2f} MB), modell {x.modell}')
    if x.torrkorning: print('torrkörning: inget anrop'); return
    if x.bearbeta_svar:
        ra = json.loads(Path(x.bearbeta_svar).read_text(encoding='utf-8'))
        post = ra.pop('_anrop', None) if isinstance(ra, dict) else None
        ok, p = behandla_svar(ra, x.klipp, data, ind, post, x.modell, ut)
        print('ok' if ok else 'AVVISAT', p); sys.exit(0 if ok else 2)
    if (ut / 'svar_ra.json').exists() and not x.ny:
        raise SystemExit(f'{ut / "svar_ra.json"} finns redan. Använd --bearbeta-svar för att validera om, eller --ny för ett nytt anrop (räknas).')
    print(f'anrop {antal_skickade() + 1} av {TAK} ...', flush=True)
    j, post = anropa(body, x.modell, x.klipp)
    skriv(ut / 'svar_ra.json', dict(j, _anrop=post))
    ok, p = behandla_svar(j, x.klipp, data, ind, post, x.modell, ut)
    print('tokens', post['tokens'], f'{post["ms"] / 1000:.0f} s')
    print('ok' if ok else 'AVVISAT', p); sys.exit(0 if ok else 2)


if __name__ == '__main__':
    main()
