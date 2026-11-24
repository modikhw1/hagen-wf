"""Förståndet: den långsamma vägen i slingan.

När Jev inte hittar ett drag går CM:s mening hit. En språkmodell läser meningen mot klippets tillstånd,
kundens linje och CM:s avsikt med passet, och svarar med ett recept: en kort följd steg i ett slutet språk.
Koden utför stegen. Modellen ändrar aldrig tillståndet själv.

Ett recept som gick att utföra sparas som ett lärt drag (ut/lardrag.json). Nästa gång står det bland
dragen Jev väljer mellan, och går då den snabba vägen.

Två vägar till modellen, vald med FORSTAND_VIA:
  beacon (standard): bryggan till Google Cloud (token-budget-beacon.lovable.app, BEACON_NYCKEL i video/.env.local). Stabil, cirka 2 s.
  gemini: Google AI Studio direkt, nyckeln GEMINI_API_KEY_GRATIS i video/.env.local. gemini-3-flash-preview med
    minimalt tänkande svarar på cirka 3 s (16 nov). gemini-3.5-flash tog 45-68 s på gratisnivån, flash-lite gav 503.
  codex: Codex CLI på ägarens plan (codex exec, skrivskyddat, i en tom mapp). 13-19 s, mest uppstart.
Modellen byts med FORSTAND_MODELL (och FORSTAND_EFFORT för codex).
"""
import copy
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

import tillstand as ts

HERE = Path(__file__).resolve().parent
UT = HERE / 'ut'
LARDA = UT / 'lardrag.json'
LOGG = UT / 'forstand'
VIA = os.environ.get('FORSTAND_VIA', 'beacon')
BEACONMODELL = os.environ.get('FORSTAND_BEACONMODELL', 'gemini-3.5-flash')
MODELL = os.environ.get('FORSTAND_MODELL', 'gemini-3-flash-preview' if VIA == 'gemini' else 'gpt-5.6-sol')
EFFORT = os.environ.get('FORSTAND_EFFORT', 'low')
CODEXMODELL = MODELL if VIA == 'codex' else os.environ.get('FORSTAND_CODEXMODELL', 'gpt-5.6-sol')

HALLNING = ('star', 'sitter', 'gar', 'ligger')
HANTERING = ('ater', 'visar_upp', 'racker', 'tillagar', 'betalar', 'talar', 'text')
OPS = ('drag', 'satt', 'byt_element', 'markera', 'ny_takt')
FALT = ('stalle', 'hallning', 'hantering', 'kollega', 'skylt', 'zoom', 'sek')
NIVA = ('ryggrad', 'manus', 'scenlagret', 'utanfor')

_S = {'type': 'string'}
SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['niva', 'avsikt', 'arver', 'bryter_ryggraden', 'skal_brott', 'namn', 'fras', 'galler', 'steg', 'foljder', 'fraga'],
    'properties': {
        'niva': {'type': 'string', 'enum': list(NIVA)},
        'avsikt': _S, 'arver': _S, 'bryter_ryggraden': {'type': 'boolean'}, 'skal_brott': _S,
        'namn': _S, 'fras': _S, 'galler': {'type': 'string', 'enum': ['klippet', 'typen', 'alla']},
        'steg': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False,
            'required': ['op', 'takt', 'drag', 'param', 'falt', 'varde', 'var', 'ny', 'funktion', 'text'],
            'properties': {'op': {'type': 'string', 'enum': list(OPS)}, 'takt': _S, 'drag': _S, 'param': _S, 'falt': _S,
                           'varde': _S, 'var': _S, 'ny': _S, 'funktion': _S, 'text': _S}}},
        'foljder': {'type': 'array', 'items': _S}, 'fraga': _S}}

REGLER = """Du är förståndet i ett regibord för content managers (CM) på en byrå som gör kortvideo åt restauranger och kaféer.
CM har laddat in ett befintligt klipp som förlaga och vill forma om det för en kund. CM skrev en mening som det snabba valet inte kunde placera.
Läs vad CM vill och svara med ett recept: en kort följd steg som koden utför. Kör inga kommandon och läs inga filer. Svara bara med JSON enligt schemat.

RYGGRADEN är det som ärvs från förlagan och inte får gå förlorat:
1. Typen av innehåll. En matvisning blir inte en sketch.
2. Inspelningstekniken och tonen: tempo, om det är avsiktligt eller slarvigt. Den mänskligheten ärvs.
3. Längden och meningen: en långsam sketch förblir en långsam sketch.
4. Det som förmedlas mellan raderna.
Det som BYTS är fyllningen: repliker, bakgrund, mat, vara, erbjudande, uppmaning, och inslag som är kundens egna.

UTBYTE SKER PÅ FUNKTION, INTE PÅ KATEGORI. Fråga vad ett inslag gör för klippet i sitt sammanhang ("visar hur kul stället är", "bevisar att portionen är stor") och hitta det hos kunden som gör samma sak. Byt inte magdansare mot magiker för att båda är uppträdanden. Kundens egenskaper kan styra tillbaka på inspelningen: en roterande kebab filmas på ett annat sätt än en burgare, och då hör det till följderna.

NIVÅ:
- ryggrad: ändringen gäller takter, ställen, personer, vad som visas, längd. Skriv steg.
- manus: bara vad som sägs eller står i text. Använd markera.
- scenlagret: hur en kropp rör sig, håller något, ser ut, eller hur kameran rör sig inom en scen. Skriv inga steg. Beskriv i foljder vad kroppen eller kameran ska göra.
- utanfor: går inte att göra här. Säg varför i skal_brott.
Om ändringen tar bort eller urholkar något ur ryggraden: bryter_ryggraden = true, skriv skälet i skal_brott och lämna steg tomt. Föreslå i foljder vad CM kan göra i stället.
Är meningen för oklar för att välja: lämna steg tomt och ställ en kort motfråga i fraga. Annars är fraga tom.

STEGEN (fält som inte används är tom sträng):
- op drag: ett av de lagliga dragen nedan. drag = dragets namn. param: för byt_lokal "ställe|vilka" där vilka är forsta, sista, alla_fria eller alla; för byt_produkt produktens namn; annars tomt.
- op satt: sätt ett fält på takter. takt = väljare. falt och varde: stalle (STALLEN), hallning (star, sitter, gar, ligger), hantering (lägg till en av: ater, visar_upp, racker, tillagar, betalar, talar), kollega (ja eller nej), skylt (texten, eller tomt för ingen), zoom (0.6 till 1.4, lägre är tätare bild), sek (sekunder).
- op byt_element: ett inslag i en takt byts mot kundens. takt = väljare, var = inslaget i förlagan, ny = vad som kommer i stället hos kunden, funktion = vad inslaget gör för klippet (det som ärvs).
- op markera: en anteckning på takter om vad manus måste lösa. takt = väljare, text = anteckningen.
- op ny_takt: en ny takt. takt = väljaren för takten den läggs efter, text = vad som händer, funktion = taktens funktion (krok, visning, vandning, avslut eller liknande), varde = ställe.
Väljare för takt: nr:3, forsta, sista, alla, ryggrad, fria, eller funktion:visning.
Håll receptet kort, oftast ett till tre steg. Ryggradstakter får flyttas och fyllas om men aldrig tas bort.

DET LÄRDA DRAGET: receptet sparas och erbjuds nästa gång.
- namn: kort, små bokstäver och understreck.
- fras: en mening som beskriver draget så att det går att känna igen på en ny mening från en CM. Skriv den allmänt om galler är typen eller alla.
- galler: klippet om receptet nämner just det här klippets innehåll eller kundens saker; typen om det passar klipp av samma typ; alla om det passar vilket klipp som helst. Använd väljare som forsta, sista eller funktion: i stället för nr: när galler inte är klippet.

avsikt: vad CM vill uppnå, en mening. arver: vad som ska stå kvar från förlagan efter ändringen, en mening.
foljder: vad som följer med ändringen och som CM måste veta, högst fyra korta punkter. Skriv på svenska."""


def _valj(T, valjare):
    v = (valjare or '').strip().lower()
    if v in ('alla', ''):
        return list(T)
    if v == 'forsta':
        return T[:1]
    if v == 'sista':
        return T[-1:]
    if v == 'ryggrad':
        return [t for t in T if t['bar'] == 'ryggrad']
    if v == 'fria':
        return [t for t in T if t['bar'] != 'ryggrad']
    if v.startswith('nr:'):
        n = re.sub(r'\D', '', v)
        return [t for t in T if n and t['nr'] == int(n)]
    if v.startswith('funktion:'):
        return [t for t in T if (t['funktion'] or '').lower() == v.split(':', 1)[1].strip()]
    return []


def kor_recept(s, steg, ryggrad, kund=None):
    """Utför receptets steg i ordning. Ger (nytt tillstånd, logg). Ett steg som inte går stoppar allt."""
    n = copy.deepcopy(s)
    logg = {'utfort': True, 'andrat': [], 'foljder': []}

    def stopp(varfor):
        return s, {'utfort': False, 'stopp': varfor, 'andrat': [], 'foljder': []}

    for i, st in enumerate(steg, 1):
        op = st.get('op')
        if op == 'drag':
            drag, param = st.get('drag') or '', (st.get('param') or '').strip() or None
            if drag not in ts.lagliga_drag(n, ryggrad) or drag in ('manus', 'scenlagret', 'ingen_passar', 'byt_upplagg'):
                return stopp(f'steg {i}: draget {drag} går inte att göra här')
            if drag == 'byt_lokal':
                d = [x.strip() for x in (param or '').split('|')]
                param = (d[0], d[1] if len(d) > 1 and d[1] in ('forsta', 'sista', 'alla_fria', 'alla') else 'alla_fria')
            n, l = ts.tillampa(n, drag, ryggrad, param=param, kund=kund)
            if not l['utfort']:
                return stopp(f"steg {i}: {l['stopp']}")
            logg['andrat'] += l['andrat']
            logg['foljder'] += l['foljder']
            continue
        T = _valj(n['takter'], st.get('takt'))
        if not T:
            return stopp(f"steg {i}: ingen takt matchar '{st.get('takt')}'")
        nr = ', '.join(str(t['nr']) for t in T)
        if op == 'satt':
            falt, v = st.get('falt'), (st.get('varde') or '').strip()
            if falt not in FALT:
                return stopp(f'steg {i}: okänt fält {falt}')
            for t in T:
                if falt == 'stalle':
                    if v not in ts.STALLEN:
                        return stopp(f'steg {i}: okänt ställe {v}')
                    t.setdefault('var_stalle', t['stalle'])
                    t['stalle'] = v
                    if v not in ('bord', 'uteservering') and t['hallning'] == 'sitter':
                        t['hallning'] = 'star'
                elif falt == 'hallning':
                    if v not in HALLNING:
                        return stopp(f'steg {i}: okänd hållning {v}')
                    t['hallning'] = v
                elif falt == 'hantering':
                    if v not in HANTERING:
                        return stopp(f'steg {i}: okänd hantering {v}')
                    if v not in t['hantering']:
                        t['hantering'] = [v] + t['hantering']
                elif falt == 'kollega':
                    t['kollega'] = v.lower() in ('ja', 'true', '1')
                elif falt == 'skylt':
                    t['skylt'] = v or None
                elif falt in ('zoom', 'sek'):
                    try:
                        x = float(v.replace(',', '.'))
                    except ValueError:
                        return stopp(f'steg {i}: {falt} är inget tal')
                    t[falt] = round(min(1.4, max(0.6, x)), 2) if falt == 'zoom' else round(max(1.0, x), 1)
            logg['andrat'].append(f'takt {nr}: {falt} = {v or "ingen"}')
        elif op == 'byt_element':
            var, ny, fn = ((st.get(k) or '').strip() for k in ('var', 'ny', 'funktion'))
            if not ny:
                return stopp(f'steg {i}: inget att byta till')
            for t in T:
                t['markning'].append(f'byt: {var} → {ny}' + (f' (bär: {fn})' if fn else ''))
            n['platser'] = [p for p in n['platser'] if p['plats'] != var] + \
                [{'plats': var, 'har': ny, 'typ': 'inslag', 'var': var, 'funktion': fn}]
            logg['andrat'].append(f"takt {nr}: '{var}' byts mot '{ny}'" + (f', som bär samma sak: {fn}' if fn else ''))
        elif op == 'markera':
            text = (st.get('text') or '').strip()
            if not text:
                return stopp(f'steg {i}: tom anteckning')
            for t in T:
                t['markning'].append(text if text.startswith('manus') else 'manus: ' + text)
            logg['andrat'].append(f'takt {nr} märkt: {text}')
        elif op == 'ny_takt':
            efter = T[-1]
            k = copy.deepcopy(efter)
            k.pop('var_stalle', None)
            k.update(nr=max(t['nr'] for t in n['takter']) + 1, bar='kan strykas', vad=(st.get('text') or 'Ny takt.').strip(),
                     funktion=(st.get('funktion') or efter['funktion']).strip(), markning=['manus: ny takt'],
                     kollega=False, skylt=None)
            v = (st.get('varde') or '').strip()
            if v in ts.STALLEN:
                k['stalle'] = v
            x = ts.las(k['vad'])
            k['hallning'], k['hantering'] = x['hallning'], x['hantering']
            n['takter'].insert(n['takter'].index(efter) + 1, k)
            logg['andrat'].append(f"ny takt {k['nr']} efter takt {efter['nr']}: {k['vad']}")
        else:
            return stopp(f'steg {i}: okänd op {op}')
    for t in n['takter']:
        t['markning'] = list(dict.fromkeys(t['markning']))
    if not logg['andrat']:
        return stopp('receptet har inga steg')
    return n, logg


# --- lärda drag ---------------------------------------------------------------------------------

def _las_larda():
    return json.loads(LARDA.read_text(encoding='utf-8')) if LARDA.exists() else []


def larda_for(s):
    """Lärda drag som gäller det här klippet: {dragnamn: post}."""
    ut = {}
    for d in _las_larda():
        if d['galler'] == 'alla' or (d['galler'] == 'typen' and d['typ'] == s['typ']) or (d['galler'] == 'klippet' and d['klipp'] == s['klipp']):
            ut['lard_' + d['namn']] = d
    return ut


def spara_lart(s, svar, mening, kund):
    namn = re.sub(r'[^a-z0-9_]', '', (svar.get('namn') or '').lower().replace(' ', '_'))[:40] or time.strftime('drag_%H%M%S')
    alla = [d for d in _las_larda() if d['namn'] != namn]
    alla.append({'namn': namn, 'fras': svar['fras'], 'galler': svar['galler'], 'typ': s['typ'], 'klipp': s['klipp'],
                 'steg': svar['steg'], 'arver': svar['arver'], 'avsikt': svar['avsikt'], 'foljder': svar['foljder'],
                 'mening': mening, 'kund': (kund or {}).get('konto'), 'tid': time.strftime('%Y-%m-%d %H:%M'), 'anvant': 0})
    LARDA.write_text(json.dumps(alla, ensure_ascii=False, indent=1), encoding='utf-8')
    return namn


def glom(namn):
    alla = _las_larda()
    kvar = [d for d in alla if d['namn'] != namn]
    LARDA.write_text(json.dumps(kvar, ensure_ascii=False, indent=1), encoding='utf-8')
    return len(alla) - len(kvar)


def rakna_anvant(namn):
    alla = _las_larda()
    for d in alla:
        if d['namn'] == namn:
            d['anvant'] = d.get('anvant', 0) + 1
    LARDA.write_text(json.dumps(alla, ensure_ascii=False, indent=1), encoding='utf-8')


# --- anropet ------------------------------------------------------------------------------------

class Forstand:
    def __init__(self, tak=60):
        self.n, self.tak, self.ms = 0, tak, 0
        self.exe = shutil.which('codex')

    def fraga(self, prompt):
        self.n += 1
        if self.n > self.tak:
            raise RuntimeError('tak för förståndet nått')
        LOGG.mkdir(parents=True, exist_ok=True)
        if VIA == 'beacon':   # bryggan till Google Cloud: stabil, cirka 2 s
            try:
                return self._beacon(prompt)
            except Exception as e:
                self.reserv = f'{type(e).__name__}: {str(e)[:80]}'
        if VIA in ('beacon', 'gemini'):
            try:
                return self._gemini(prompt)
            except Exception as e:   # gratisnivån svajar (503, tidsgräns): gå över till codex i stället för att tappa meningen
                self.reserv = f'{type(e).__name__}: {str(e)[:80]}'
        if not self.exe:
            raise RuntimeError('codex finns inte i PATH')
        tom = LOGG / 'tom'
        tom.mkdir(exist_ok=True)
        schema = LOGG / 'schema.json'
        schema.write_text(json.dumps(SCHEMA), encoding='utf-8')
        ut = LOGG / f"svar_{time.strftime('%Y%m%d-%H%M%S')}_{self.n}.txt"
        t0 = time.perf_counter()
        p = subprocess.run([self.exe, 'exec', '-m', CODEXMODELL, '-c', f'model_reasoning_effort={EFFORT}', '-s', 'read-only',
                            '--skip-git-repo-check', '--ephemeral', '-C', str(tom), '--output-schema', str(schema), '-o', str(ut), '-'],
                           input=prompt.encode('utf-8'), capture_output=True, timeout=180)
        ms = round((time.perf_counter() - t0) * 1000)
        self.ms += ms
        text = ut.read_text(encoding='utf-8') if ut.exists() else ''
        if not text.strip():
            raise RuntimeError('förståndet svarade inte: ' + p.stderr.decode('utf-8', 'replace')[-300:])
        svar, _ = json.JSONDecoder().raw_decode(text[text.index('{'):])
        ut.with_suffix('.json').write_text(json.dumps({'prompt': prompt, 'svar': svar, 'ms': ms, 'modell': CODEXMODELL, 'effort': EFFORT},
                                                      ensure_ascii=False, indent=1), encoding='utf-8')
        ut.unlink()
        return svar, ms


def _utan_extra(s):
    """Geminis responseSchema tar inte additionalProperties."""
    if isinstance(s, dict):
        return {k: _utan_extra(v) for k, v in s.items() if k != 'additionalProperties'}
    return [_utan_extra(x) for x in s] if isinstance(s, list) else s


def _gemini_nyckel():
    for rad in (HERE.parents[1] / 'video' / '.env.local').read_text(encoding='utf-8').splitlines():
        if rad.startswith(os.environ.get('FORSTAND_NYCKELNAMN', 'GEMINI_API_KEY_GRATIS') + '='):
            return rad.split('=', 1)[1].strip()
    raise RuntimeError('ingen Gemini-nyckel i video/.env.local')


def _gemini(self, prompt):
    body = {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
            'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': _utan_extra(SCHEMA), 'temperature': 0.2,
                                 'thinkingConfig': {'thinkingLevel': os.environ.get('FORSTAND_TANK', 'minimal')}}}
    req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{MODELL}:generateContent',
                                 data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'x-goog-api-key': _gemini_nyckel()})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=int(os.environ.get('FORSTAND_TIDSGRANS', '20'))) as r:
        j = json.loads(r.read())
    ms = round((time.perf_counter() - t0) * 1000)
    self.ms += ms
    svar = json.loads(''.join(p.get('text', '') for p in j['candidates'][0]['content']['parts'] if not p.get('thought')))
    for st in svar.get('steg', []):
        for k in ('takt', 'drag', 'param', 'falt', 'varde', 'var', 'ny', 'funktion', 'text'):
            st.setdefault(k, '')
    (LOGG / f"svar_{time.strftime('%Y%m%d-%H%M%S')}_{self.n}.json").write_text(
        json.dumps({'prompt': prompt, 'svar': svar, 'ms': ms, 'modell': MODELL, 'via': 'gemini', 'usage': j.get('usageMetadata')},
                   ensure_ascii=False, indent=1), encoding='utf-8')
    return svar, ms


def _beacon(self, prompt):
    env = {r.split('=', 1)[0]: r.split('=', 1)[1].strip() for r in (HERE.parents[1] / 'video' / '.env.local').read_text(encoding='utf-8').splitlines()
           if '=' in r and not r.startswith('#')}
    body = {'model': BEACONMODELL, 'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json', 'responseJsonSchema': SCHEMA,
                                 'thinkingConfig': {'thinkingLevel': os.environ.get('FORSTAND_TANK', 'low')}}}
    req = urllib.request.Request(env.get('BEACON_URL') or 'https://token-budget-beacon.lovable.app/api/public/v1/generate', data=json.dumps(body).encode(),
                                 headers={'authorization': 'Bearer ' + env['BEACON_NYCKEL'], 'content-type': 'application/json'})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.loads(r.read())
    ms = round((time.perf_counter() - t0) * 1000)
    self.ms += ms
    svar = json.loads(''.join(p.get('text', '') for p in j['candidates'][0]['content']['parts'] if not p.get('thought')))
    (LOGG / f"svar_{time.strftime('%Y%m%d-%H%M%S')}_{self.n}.json").write_text(
        json.dumps({'prompt': prompt, 'svar': svar, 'ms': ms, 'modell': BEACONMODELL, 'via': 'beacon', 'usd': (j.get('proxy') or {}).get('cost_usd')},
                   ensure_ascii=False, indent=1), encoding='utf-8')
    return svar, ms


Forstand._gemini = _gemini
Forstand._beacon = _beacon


def bygg_prompt(s, mening, ryggrad, kund, anpassa, avsikt, jevsvar):
    drag = ts.lagliga_drag(s, ryggrad)
    rader = [REGLER, '', 'STALLEN: ' + '; '.join(f'{k} = {v}' for k, v in ts.STALLEN.items()), '',
             'LAGLIGA DRAG NU:'] + [f'- {k}: {v}' for k, v in drag.items() if k not in ('manus', 'scenlagret', 'ingen_passar')]
    larda = larda_for(s)
    if larda:
        rader += ['', 'REDAN LÄRDA DRAG (föreslå inte samma igen):'] + [f"- {d['namn']}: {d['fras']}" for d in larda.values()]
    rader += ['', 'KLIPPETS TILLSTÅND:', ts.tillstandstext(s)]
    if s.get('kontrast'):
        rader.append(f"Klippet bygger på en kontrast mellan två sidor (styrka {s['kontrast']}).")
    if s.get('risk'):
        rader.append('Kortets risk vid anpassning: ' + s['risk'])
    if kund:
        kl = (anpassa or {}).get('kundens_linje') or {}
        rader += ['', f"KUNDEN: @{kund['konto']}. Filmar oftast i: {', '.join(list(kl.get('rum') or {})[:3]) or kund.get('rum')}. "
                      f"Visar i egna klipp: {', '.join((kl.get('produkter') or [])[:5]) or kund.get('produkt')}."]
    rader += ['', 'CM:S AVSIKT MED PASSET: ' + (avsikt or 'inte angiven'), '', f'CM SKRIVER: "{mening}"']
    if jevsvar:
        rader.append(f"Det snabba valet gav {jevsvar.get('val')} med marginal {jevsvar.get('marginal')} (näst: {jevsvar.get('nast')}).")
    return '\n'.join(rader)


def steg(s, mening, ryggrad, kund, anpassa, avsikt, forstand, jevsvar=None):
    """Den långsamma vägen för en mening. Ger (nytt tillstånd, svar) i samma form som slinga.steg."""
    f, ms = forstand.fraga(bygg_prompt(s, mening, ryggrad, kund, anpassa, avsikt, jevsvar))
    svar = {'mening': mening, 'forstand': {'niva': f['niva'], 'avsikt': f['avsikt'], 'arver': f['arver'], 'ms': ms, 'modell': MODELL,
                                           'steg': f['steg']},
            'rader': [], 'foljder': list(f.get('foljder') or [])}
    if f['avsikt']:
        svar['rader'].append('Läst som: ' + f['avsikt'])
    if f['bryter_ryggraden']:
        svar['utfall'] = 'stoppat'
        svar['rader'].append('Stoppat, det rör ryggraden: ' + f['skal_brott'])
        return s, svar
    if f['fraga'].strip() and not f['steg']:
        svar['utfall'] = 'osaker'
        svar['rader'].append(f['fraga'])
        return s, svar
    if f['niva'] in ('scenlagret', 'utanfor') or not f['steg']:
        svar['utfall'] = f['niva'] if f['niva'] != 'ryggrad' else 'ingen_passar'
        svar['rader'].append({'scenlagret': 'Det hör till scenlagret: kropp eller kamera inom en scen. Uppställningen ändras inte här.',
                              'utanfor': 'Går inte att göra här: ' + f['skal_brott'],
                              'manus': 'Det är manus. Inget i uppställningen ändras.'}.get(f['niva'], 'Inget recept.'))
        return s, svar
    ny, logg = kor_recept(s, f['steg'], ryggrad, kund)
    if not logg['utfort']:
        svar['utfall'] = 'stoppat'
        svar['rader'].append('Receptet gick inte att utföra: ' + logg['stopp'] + '.')
        return s, svar
    ny['historik'] = s['historik'] + ['forstand']
    svar['utfall'] = 'utfort'
    svar['rader'].append('Ändrat: ' + '; '.join(logg['andrat']) + '.')
    if f['arver']:
        svar['rader'].append('Ärvs: ' + f['arver'])
    svar['foljder'] += [x for x in logg['foljder'] if x not in svar['foljder']]
    namn = spara_lart(s, f, mening, kund)
    svar['lart'] = {'namn': namn, 'fras': f['fras'], 'galler': f['galler']}
    return ny, svar


def utfor_lart(s, post, ryggrad, kund):
    """Ett lärt drag som Jev valde: receptet körs utan modell."""
    ny, logg = kor_recept(s, post['steg'], ryggrad, kund)
    if not logg['utfort']:
        return s, {'utfall': 'stoppat', 'rader': [f"Det lärda draget {post['namn']} gick inte här: {logg['stopp']}."], 'foljder': []}
    ny['historik'] = s['historik'] + ['lard_' + post['namn']]
    rakna_anvant(post['namn'])
    return ny, {'utfall': 'utfort', 'rader': ['Ändrat: ' + '; '.join(logg['andrat']) + '.', 'Ärvs: ' + post['arver']],
                'foljder': list(dict.fromkeys(logg['foljder'] + post.get('foljder', []))),
                'lart': {'namn': post['namn'], 'fras': post['fras'], 'galler': post['galler'], 'ateranvant': True}}


# --- scenlagret: kroppen ------------------------------------------------------------------------
# Klipp som har en läst kropp i kedjan. Bordet talar med kroppsvägen genom filer och ett kommando (byggstenar importerar inte kedjans kod).
# FORSKNING: kroppen kommer ur MaskedMimic SMPL (AMASS-tränad, icke-kommersiell).
KROPPSVAG = HERE.parents[1] / 'forvarld' / 'kropp' / 'forskning' / 'mm'
_G = dict(kalla='kand-kennysgelato_n06-hand/kalla_0033.json', liggare='kand-kennysgelato_n06-hand/liggare_0033.json')
_B = dict(kalla='b-tilltal-ravara_n06-hand/kalla_0032.json', liggare='b-tilltal-ravara_n06-hand/liggare_0032.json')
_Q = dict(kalla='e-dialog-guacamole_grupp/kalla_0032.json', liggare='e-dialog-guacamole_grupp/liggare_0032.json')
# Tagningar som är körda genom kroppsvägen. Fler går att lägga till: allt som finns i kedjans kalla och liggare och där personen står.
TAGNINGAR = {
    'gelato_s1_A': dict(_G, scen='s1', person='A', namn='Gelato, s1: hon skopar ett smakprov och räcker fram det'),
    'slaktaren_s1_A': dict(_B, scen='s1', person='A', namn='Slaktaren, s1: Mads frågar vad köttbiten väger'),
    'slaktaren_s3_B': dict(_B, scen='s3', person='B', namn='Slaktaren, s3: Morten håller köttbiten och tänker'),
    'slaktaren_s6_C': dict(_B, scen='s6', person='C', namn='Slaktaren, s6: Lærke gissar'),
    'guacamole_s2_B': dict(_Q, scen='s2', person='B', namn='Guacamole, s2: servitören svarar bakom bardisken'),
}
KROPP = {'kennysgelato2.0-7596403003901381910': 'gelato_s1_A'}   # bankklipp som har en tagning


def har_kropp(klipp):
    return klipp in KROPP and (KROPPSVAG / 'mening.py').exists()


def kropp(tagning, mening, varv=2):
    """Skickar en mening till kroppsvägen. Ger svar i bordets form, med namnet på mappen där bild och film ligger."""
    import sys
    k = TAGNINGAR[tagning]; namn = 'bord_' + time.strftime('%H%M%S'); t0 = time.perf_counter()
    p = subprocess.run([sys.executable, '-X', 'utf8', str(KROPPSVAG / 'mening.py'), mening, namn, '--kalla', k['kalla'], '--liggare', k['liggare'],
                        '--scen', k['scen'], '--person', k['person'], '--varv', str(varv), '--utan-film'], capture_output=True, text=True, encoding='utf-8', errors='replace',
                       cwd=HERE.parents[1], env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1'), timeout=600)
    lf = KROPPSVAG / 'ut' / f'mening_{namn}' / 'logg.json'
    if not lf.exists():
        return {'mening': mening, 'utfall': 'stoppat', 'rader': ['Kroppen gick inte att köra: ' + (p.stdout + p.stderr)[-300:]], 'foljder': []}
    L = json.loads(lf.read_text(encoding='utf-8')); sista = L['varv'][-1]; m = sista['matt']
    # Bladet direkt (någon sekund). Filmen ritas i bakgrunden och dyker upp i bordet när den är klar.
    streck = [sys.executable, '-X', 'utf8', str(KROPPSVAG / 'streck.py'), str(lf.parent / 'streck.mp4'), str(lf.parent / 'ref_bas.npz')] +         [f"varv {v['varv']}={lf.parent / ('mm_v%d.npz' % v['varv'])}" for v in L['varv']]
    subprocess.run(streck + ['--bara-blad'], capture_output=True, cwd=HERE.parents[1], timeout=120)
    subprocess.Popen(streck, cwd=HERE.parents[1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec = json.loads((lf.parent / f"recept_v{sista['varv']}.json").read_text(encoding='utf-8'))
    rader = ['Kroppen: ' + rec.get('beskrivning', ''), ('Står. ' if m['star'] else 'FÖLL. ') + 'Bundna kroppar till sina mål, cm: ' + ', '.join(f'{a} {b}' for a, b in m['bundna_till_mal_cm'].items()) + '.']
    rader += [f"Varv {v['varv']}: {v['bedomning_efter']}" for v in L['varv'] if v.get('bedomning_efter')]
    return {'mening': mening, 'utfall': 'utfort' if m['star'] else 'stoppat', 'rader': rader,
            'foljder': ['Ärvs: ' + rec.get('arver', '')] + [f"Antaget i referensen: {b['atgard']}" for b in L['antaganden']] + ['FORSKNING: rörelsemodellen är AMASS-tränad och får inte användas kommersiellt.'],
            'kropp': {'namn': namn, 'tagning': tagning, 'varv': len(L['varv']), 's': round(time.perf_counter() - t0, 1), 'andringar': sista['recept']['andringar']}}


def scen(namn):
    """Startar renderingen i förvärlden (lokal Blender, några minuter) i bakgrunden. Bordet frågar scenstatus tills bilderna finns."""
    import sys
    d = KROPPSVAG / 'ut' / f'mening_{namn}'
    if not (d / 'sekvens.npz').exists():
        return False
    with open(d / 'forvarld.log', 'w', encoding='utf-8') as f:
        subprocess.Popen([sys.executable, '-X', 'utf8', str(KROPPSVAG / 'forvarld_film.py'), namn], cwd=HERE.parents[1], stdout=f, stderr=subprocess.STDOUT,
                         env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1'))
    return True


def scenstatus(namn):
    d = KROPPSVAG / 'ut' / f'mening_{namn}'; logg = (d / 'forvarld.log').read_text(encoding='utf-8', errors='replace') if (d / 'forvarld.log').exists() else ''
    klar = 'FORVARLD_KLAR' in logg
    return {'klar': klar, 'fel': None if klar or 'Traceback' not in logg else logg[-300:],
            'bilder': sorted(f.name for f in d.glob('forvarld_r*.png')) if klar else [], 'film': klar and (d / 'forvarld.mp4').exists()}
