"""Kontrollerar exempel/<klipp>/kalla.json och regi.json mot schemana, bara med standardbiblioteket.

Kör:  scen/.venv/Scripts/python.exe scen/3d/kontrakt/kontrollera.py [klippmapp]     (standard: exempel/bar)

Tre kontroller:
  1. Schemalint: varje egenskap i båda schemana har description, och alla $ref pekar på något som finns.
  2. Validering mot schemat. Stöder den delmängd av JSON Schema 2020-12 som schemana använder:
     type, enum, const, properties, required, additionalProperties, items, minItems, maxItems,
     minLength, minProperties, minimum, maximum, pattern, $ref (lokal), anyOf, oneOf, allOf.
  3. Referenser: scen/person/prop/replik-id i regi finns i kalla (eller börjar med PLATSHALLARE:), och
     id:n inom kalla pekar på varandra (scen.miljo, scen.kamera, scen.personer, replik.talare).
Hashar i matning.* kontrolleras också mot filerna om de finns (annars varning).
"""
import json, re, sys, hashlib
from pathlib import Path

HIT = Path(__file__).resolve().parent
fel_lista, varningar = [], []


def ladda(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


# ---------------------------------------------------------------- 1. lint
def lint(schema, namn):
    defs = schema.get('$defs', {})

    def gå(s, sokvag):
        if not isinstance(s, dict):
            return
        if '$ref' in s:
            m = re.fullmatch(r'#/\$defs/(\w+)', s['$ref'])
            if not m or m.group(1) not in defs:
                fel_lista.append(f'{namn}: {sokvag}: $ref {s["$ref"]} pekar ingenstans')
        for k, v in s.get('properties', {}).items():
            if not isinstance(v, dict) or 'description' not in v:
                fel_lista.append(f'{namn}: {sokvag}.{k}: description saknas')
            gå(v, f'{sokvag}.{k}')
        for k in ('items',):
            if k in s:
                gå(s[k], sokvag + '[]')
        for k in ('anyOf', 'oneOf', 'allOf'):
            for i, b in enumerate(s.get(k, [])):
                gå(b, f'{sokvag}.{k}[{i}]')
        if s.get('type') == 'object' or 'properties' in s:
            if 'properties' in s and 'additionalProperties' not in s:
                fel_lista.append(f'{namn}: {sokvag}: additionalProperties ska anges')
    gå(schema, '')
    for k, v in defs.items():
        gå(v, f'$defs.{k}')


# ---------------------------------------------------------------- 2. validator
def typ_ok(v, t):
    if t == 'null': return v is None
    if t == 'boolean': return isinstance(v, bool)
    if t == 'integer': return isinstance(v, int) and not isinstance(v, bool)
    if t == 'number': return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == 'string': return isinstance(v, str)
    if t == 'array': return isinstance(v, list)
    if t == 'object': return isinstance(v, dict)
    raise ValueError(t)


def diskriminator(grenar):
    """Egenskap som alla grenar har som const (op, typ): används för att peka ut rätt gren i felmeddelandet."""
    gem = None
    for g in grenar:
        if '$ref' in g:
            g = RAD['$defs'][g['$ref'].split('/')[-1]]
        k = {n for n, p in g.get('properties', {}).items() if 'const' in p}
        gem = k if gem is None else gem & k
    return next(iter(sorted(gem)), None) if gem else None


def validera(v, s, sokv, rot):
    global RAD
    RAD = rot
    fel = []
    if '$ref' in s:
        mal = rot['$defs'][s['$ref'].split('/')[-1]]
        fel += validera(v, mal, sokv, rot)
    t = s.get('type')
    if t is not None:
        ts = t if isinstance(t, list) else [t]
        if not any(typ_ok(v, x) for x in ts):
            return fel + [f'{sokv}: typ {type(v).__name__}, väntade {ts}']
    if 'const' in s and v != s['const']:
        fel.append(f'{sokv}: ska vara {s["const"]!r}, är {v!r}')
    if 'enum' in s and v not in s['enum']:
        fel.append(f'{sokv}: {v!r} finns inte i enum {s["enum"]}')
    if isinstance(v, str):
        if 'minLength' in s and len(v) < s['minLength']: fel.append(f'{sokv}: för kort sträng')
        if 'pattern' in s and not re.search(s['pattern'], v): fel.append(f'{sokv}: matchar inte {s["pattern"]}')
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if 'minimum' in s and v < s['minimum']: fel.append(f'{sokv}: {v} < minimum {s["minimum"]}')
        if 'maximum' in s and v > s['maximum']: fel.append(f'{sokv}: {v} > maximum {s["maximum"]}')
    if isinstance(v, list):
        if 'minItems' in s and len(v) < s['minItems']: fel.append(f'{sokv}: färre än {s["minItems"]} element')
        if 'maxItems' in s and len(v) > s['maxItems']: fel.append(f'{sokv}: fler än {s["maxItems"]} element')
        if 'items' in s:
            for i, x in enumerate(v):
                fel += validera(x, s['items'], f'{sokv}[{i}]', rot)
    if isinstance(v, dict):
        if 'minProperties' in s and len(v) < s['minProperties']: fel.append(f'{sokv}: för få egenskaper')
        for k in s.get('required', []):
            if k not in v: fel.append(f'{sokv}: obligatoriskt fält {k} saknas')
        props = s.get('properties', {})
        for k, x in v.items():
            if k in props: fel += validera(x, props[k], f'{sokv}.{k}', rot)
            elif s.get('additionalProperties', True) is False: fel.append(f'{sokv}: okänt fält {k}')
    for k in ('allOf',):
        for g in s.get(k, []): fel += validera(v, g, sokv, rot)
    if 'anyOf' in s:
        if not any(not validera(v, g, sokv, rot) for g in s['anyOf']):
            fel.append(f'{sokv}: ingen gren i anyOf passar')
    if 'oneOf' in s:
        grenar = s['oneOf']
        traffar = [g for g in grenar if not validera(v, g, sokv, rot)]
        if len(traffar) != 1:
            d = diskriminator(grenar) if isinstance(v, dict) else None
            val = None
            if d:
                for g in grenar:
                    gg = rot['$defs'][g['$ref'].split('/')[-1]] if '$ref' in g else g
                    if gg['properties'][d].get('const') == v.get(d): val = g
            if val is not None:
                fel += validera(v, val, sokv, rot)
            else:
                fel.append(f'{sokv}: {len(traffar)} grenar i oneOf passar, väntade 1' + (f' ({d} = {v.get(d)!r} känns inte igen)' if d else ''))
    return fel


# ---------------------------------------------------------------- 3. referenser
def id_ok(i, giltiga, var):
    if i is None or i == 'alla' or (isinstance(i, str) and i.startswith('PLATSHALLARE:')): return
    if i not in giltiga: fel_lista.append(f'{var}: id {i!r} finns inte i kalla')


def referenser(K, R):
    sem, mat = K['semantik'], K['matning']
    scener = {s['id'] for s in sem['scener']}; pers = {p['id'] for p in sem['personer']}
    props = {p['id'] for p in sem['props']}; repl = {r['id'] for r in sem['repliker']}
    rum = {r['id'] for r in sem['rum']}; kam = {k['id'] for k in mat['kameror']}
    for s in sem['scener']:
        id_ok(s['miljo'], rum, f'scen {s["id"]}.miljo'); id_ok(s['kamera'], kam, f'scen {s["id"]}.kamera')
        for p in s['personer']: id_ok(p, pers, f'scen {s["id"]}.personer')
        if s['slut_s'] <= s['start_s']: fel_lista.append(f'scen {s["id"]}: slut_s <= start_s')
    # platser: scenernas plats_id, bindningar mot ankare, registreringar, och att semantik och matning beskriver samma ankare
    plats = {p['id']: p for p in sem.get('platser', [])}; platsm = {p['id']: p for p in mat.get('platser', [])}
    for pid in plats:
        if pid not in platsm: fel_lista.append(f'plats {pid}: matning.platser saknar mätdelen')
    for pid, pm in platsm.items():
        if pid not in plats: fel_lista.append(f'matning.platser {pid}: saknar semantik.platser')
        else:
            if {a['id'] for a in plats[pid]['ankare']} != {a['id'] for a in pm['ankare']}: fel_lista.append(f'plats {pid}: ankare i semantik och matning är inte samma uppsättning')
        for r in pm['registreringar']:
            id_ok(r['scen'], scener, f'matning.platser {pid}.registreringar.scen'); id_ok(r['kamera'], kam, f'matning.platser {pid}.registreringar.kamera')
            if abs(r['till_plats']['skala'] - 1.0) > 1e-9: varningar.append(f'plats {pid}, scen {r["scen"]}: skala {r["till_plats"]["skala"]} stöds inte av byggaren')
    for s in sem['scener']:
        if s.get('plats_id'):
            id_ok(s['plats_id'], plats, f'scen {s["id"]}.plats_id')
            if s['plats_id'] in platsm and s['id'] not in {r['scen'] for r in platsm[s['plats_id']]['registreringar']}: fel_lista.append(f'scen {s["id"]}: plats {s["plats_id"]} saknar registrering för scenen')
            if s.get('kamera_bindning') and s['plats_id'] in plats:
                id_ok(s['kamera_bindning']['ankare'], {a['id'] for a in plats[s['plats_id']]['ankare']}, f'scen {s["id"]}.kamera_bindning.ankare')
            for b in s.get('bindningar', []):
                id_ok(b['person'], pers, f'scen {s["id"]}.bindningar.person')
                if s['plats_id'] in plats: id_ok(b['ankare'], {a['id'] for a in plats[s['plats_id']]['ankare']}, f'scen {s["id"]}.bindningar.ankare')
    for p_ in sem['props']:
        if p_.get('plats_id'):
            id_ok(p_['plats_id'], plats, f'prop {p_["id"]}.plats_id')
            if p_['plats_id'] in plats and p_['rum_ref'] not in {o['id'] for o in plats[p_['plats_id']]['objekt']}: fel_lista.append(f'prop {p_["id"]}: rum_ref {p_["rum_ref"]} finns inte i platsen')
    for r in sem['repliker']:
        id_ok(r['talare'], pers, f'replik {r["id"]}.talare')
        for o in r['ord']:
            if not (r['start_s'] - 0.05 <= o['start_s'] <= o['slut_s'] <= r['slut_s'] + 0.05): varningar.append(f'replik {r["id"]}: ord utanför repliken')
    for m in mat['personer']: id_ok(m['person'], pers, 'matning.personer.person')
    for r in mat['rum']: id_ok(r['id'], rum, 'matning.rum.id')
    for p in sem['props']:
        id_ok(p['agare'], pers, f'prop {p["id"]}.agare')
    events = sem.get('handelser', [])
    event_ids = {e['id'] for e in events}
    if len(event_ids) != len(events): fel_lista.append('kalla: dubblerade händelse-id')
    for event in events:
        label = 'händelse ' + event['id']
        id_ok(event['scen'], scener, label + '.scen')
        id_ok(event['vem'], pers, label + '.vem'); id_ok(event['till_vem'], pers, label + '.till_vem')
        id_ok(event['prop'], props, label + '.prop')
        scene = next((s for s in sem['scener'] if s['id'] == event['scen']), None)
        if event['start_s'] > event['slut_s']: fel_lista.append(label + ': omvänt tidsintervall')
        if scene and not scene['start_s'] - 1e-4 <= event['start_s'] <= event['slut_s'] <= scene['slut_s'] + 1e-4:
            fel_lista.append(label + ': tid utanför scenen')
        if event['ursprung']['typ'] == 'modellbedomd' and not event['ursprung']['modell']:
            fel_lista.append(label + ': modell saknas för modellbedömning')
    for proof in mat.get('handelsebevis', []): id_ok(proof['handelse'], event_ids, 'matning.handelsebevis.handelse')
    n = K['tidsbas']['antal_rutor']; fps = K['tidsbas']['fps_taljare'] / K['tidsbas']['fps_namnare']
    if abs(n / fps - K['tidsbas']['langd_s']) > 0.001: fel_lista.append('tidsbas: langd_s stämmer inte med antal_rutor / fps')
    for s in sem['scener']:
        if s['slut_s'] > K['tidsbas']['langd_s'] + 1e-6: fel_lista.append(f'scen {s["id"]} slutar efter klippets slut')
    if R['kalla']['klipp_id'] != K['klipp']['id']: fel_lista.append('regi.kalla.klipp_id skiljer från kalla.klipp.id')
    if R['kalla']['sha256'] != K['klipp']['sha256']: fel_lista.append('regi.kalla.sha256 skiljer från kalla.klipp.sha256')
    if R['kalla']['revision'] != K['revision']: varningar.append(f'regi.kalla.revision {R["kalla"]["revision"]} != kalla.revision {K["revision"]}')
    ids = [e['id'] for e in R['edits']]
    if len(ids) != len(set(ids)): fel_lista.append('regi: dubblerade edit-id')
    skapade_scener, skapade_props = set(), set()
    for e in R['edits']:
        if e['op'] in ('lagg_till_scen', 'duplicera_scen'): skapade_scener.add(e['ny_id'])
        if e['op'] == 'lagg_till_prop': skapade_props.add(e['ny_id'])
    for e in R['edits']:
        v = f'edit {e["id"]} ({e["op"]})'
        grp = {g['id'] for g in sem.get('scengrupper', [])} if e['op'] in ('ta_bort_scen', 'flytta_scen') else set()   # 0016
        for fält, mängd in (('scen', scener | skapade_scener | grp), ('efter', scener | skapade_scener | grp), ('person', pers), ('prop', props | skapade_props), ('replik', repl)):
            if fält in e: id_ok(e[fält], mängd, f'{v}.{fält}')
        if e['op'] == 'trimma_scen' and 'start_s' not in e and 'slut_s' not in e and not e.get('tid'): fel_lista.append(f'{v}: start_s eller slut_s krävs')
        if e['op'] == 'trimma_scen':
            sc = next((s for s in sem['scener'] if s['id'] == e['scen']), None)
            if sc and ('slut_s' in e and e['slut_s'] > sc['slut_s'] + 1e-6 and e.get('lage') != 'hall_sista' or 'start_s' in e and e['start_s'] < sc['start_s'] - 1e-6):
                fel_lista.append(f'{v}: utanför scenens källintervall')
        if 'tid' in e:
            from handelser import los_edit
            try: los_edit(e, events, K['tidsbas']['langd_s'])
            except ValueError as ex: fel_lista.append(v + ': ' + str(ex))
        if e['op'] == 'renderkamera' and e.get('mal') and e['mal']['typ'] == 'person': id_ok(e['mal']['id'], pers, f'{v}.mal.id')
        if e['op'] in ('ta_bort_handling', 'tempo_handling', 'upprepa_handling'):   # 0029: segmenten finns i scenens handlingsspår
            spar = next((h for h in sem.get('handling', []) if h['scen'] == e['scen']), None)
            if spar is None: fel_lista.append(f'{v}: scenen {e["scen"]} har inget handlingsspår i kalla')
            else:
                segs = [x['id'] for x in spar['segment']]
                for fält in ('segment', 'fran', 'till'):
                    if fält in e and e[fält] not in segs: fel_lista.append(f'{v}.{fält}: {e[fält]!r} finns inte i handlingsspåret ({", ".join(segs)})')
                if e['op'] == 'upprepa_handling' and e['fran'] in segs and e['till'] in segs and segs.index(e['till']) < segs.index(e['fran']):
                    fel_lista.append(f'{v}: till ligger före fran')
        for varning in mening_varning(sem, e): varningar.append(varning)   # 0029: en ändring som river det som bär meningen går igenom, med varning
        if e['ursprung']['typ'] == 'harness-forslag' and not e['ursprung'].get('harness'): fel_lista.append(f'{v}: harness saknas')
    if any(isinstance(x, str) and 'PLATSHALLARE:' in x for e in R['edits'] for x in e.values() if isinstance(x, str)):
        if not all(e.get('kommentar') for e in R['edits'] if any(isinstance(x, str) and x.startswith('PLATSHALLARE:') for x in e.values())):
            fel_lista.append('regi: en redigering med PLATSHALLARE-id saknar kommentar')


def mening_traffar(sem, e):
    """0029: relevansposter (semantik.relevans) som editen tar bort, byter eller skär i. Utan relevanslista: inga.
    En post träffas när editens prop/person är postens ref (eller ref är ett prefix till id:t), eller när editen tar bort eller ändrar
    ett handlingssegment vars föremål, mål eller kontakt är postens ref. Returnerar [(post, hur)]."""
    rel = sem.get('relevans')
    if not rel: return []
    def ref_ok(ref, x):
        if not (ref and x): return False
        x, ref = str(x), str(ref)
        return x == ref or x.startswith(ref + ':') or ref.startswith(x + ':') or ref.endswith(':hand:' + x) or ref.endswith(':pa:' + x)
    ut = []
    if e['op'] in ('ta_bort_prop', 'byt_prop'):
        hur = 'tas bort' if e['op'] == 'ta_bort_prop' else 'byts'
        ut += [(p, hur) for p in rel['poster'] if ref_ok(p.get('ref'), e.get('prop'))]
    if e['op'] in ('casta',):
        ut += [(p, 'byter utseende') for p in rel['poster'] if ref_ok(p.get('ref'), e.get('person'))]
    if e['op'] in ('ta_bort_handling', 'tempo_handling'):
        spar = next((h for h in sem.get('handling', []) if h['scen'] == e['scen']), None)
        s = next((x for x in (spar or {}).get('segment', []) if x['id'] == e.get('segment')), None)
        if s:
            vals = [str((s.get(f) or {}).get('varde') or '') for f in ('foremal', 'mal', 'kontakt')]
            vals += [y for v in vals if '>' in v for y in v.split('>')]
            hur = f'segmentet {s["id"]} ({(s.get("handling") or {}).get("varde")}) ' + ('tas bort' if e['op'] == 'ta_bort_handling' else 'ändrar tempo')
            for p in rel['poster']:
                if p.get('roll') in ('bar', 'ramar') and any(ref_ok(p.get('ref'), v) for v in vals): ut.append((p, hur))
    return ut


def mening_varning(sem, e):
    ut = []
    for p, hur in mening_traffar(sem, e):
        namn = p.get('namn') or p['id']
        if p['roll'] == 'bar': ut.append(f'Meningen bärs av {namn} ({p["id"]}, ref {p.get("ref")}): edit {e["id"]} {hur}. Klippets mening: {sem["relevans"]["mening"]}')
        elif p['roll'] == 'ramar': ut.append(f'{namn} ({p["id"]}) ramar meningen: edit {e["id"]} {hur}.')
    return ut


_HASHMINNE = {}   # (sökväg, storlek, ändring, skapad) -> sha256. Tomt i en ny process, så en kommandoradskörning hashar alltid allt.


def sha_fil(p):
    """sha256 av en fil. I en långlivad process räknas den om först när filens stämpel (storlek, ändrings- och skapandetid) ändrats."""
    try:
        st = p.stat(); k = (str(p), st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    except OSError:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    h = _HASHMINNE.get(k)
    if h is None:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        for gammal in [x for x in _HASHMINNE if x[0] == k[0]]: del _HASHMINNE[gammal]
        _HASHMINNE[k] = h
    return h


def hashar(K, mapp, kallfil=None):
    stale = []
    def pek(o, v):
        if isinstance(o, dict):
            if 'sokvag' in o and 'sha256' in o:
                p = (mapp / o['sokvag']).resolve()
                if not p.exists(): varningar.append(f'{v}: filen {o["sokvag"]} finns inte här, hash ej kontrollerad')
                else:
                    h = sha_fil(p)
                    if h != o['sha256']:
                        fel_lista.append(f'{v}: sha256 stämmer inte för {o["sokvag"]}'); stale.append(o['sokvag'])
                    else: pek.n += 1
            for k, x in o.items(): pek(x, f'{v}.{k}')
        elif isinstance(o, list):
            for i, x in enumerate(o): pek(x, f'{v}[{i}]')
    pek.n = 0
    pek(K['matning'], 'matning')
    # videons hash ligger i klipp.sha256, sökvägen i klipp.video.sokvag
    p = (mapp / K['klipp']['video']['sokvag']).resolve()
    if p.exists() and sha_fil(p) != K['klipp']['sha256']: fel_lista.append('klipp.sha256 stämmer inte med videofilen')
    elif p.exists(): pek.n += 1
    if stale:
        source = Path(kallfil) if kallfil else Path(mapp) / 'kalla.json'
        if any(x['sokvag'] in stale for x in K['matning'].get('handelsekallor', [])):
            fel_lista.append('Händelseunderlaget har ändrats. Mät om med scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_handelser.py <aktuell kalla_prop.json> <semantik.json> <ny kalla_handelser.json>; uppdatera regins revision. Hasha inte om gamla händelser.')
        else:
            fel_lista.append('Ingest har ändrat mätfiler efter källmanifestet. Granska ändringen och uppdatera uttryckligen: scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_omhasha.py "' + str(source.resolve()) + '" --uppdatera')
    return pek.n


def main():
    mapp = HIT / (sys.argv[1] if len(sys.argv) > 1 else 'exempel/bar')
    sk_k, sk_r = ladda(HIT / 'kalla.schema.json'), ladda(HIT / 'regi.schema.json')
    K, R = ladda(mapp / 'kalla.json'), ladda(mapp / 'regi.json')
    lint(sk_k, 'kalla.schema'); lint(sk_r, 'regi.schema')
    fel_lista.extend(validera(K, sk_k, 'kalla', sk_k)); fel_lista.extend(validera(R, sk_r, 'regi', sk_r))
    n_hash = 0
    if not fel_lista:
        referenser(K, R)
        n_hash = hashar(K, mapp)
    for w in varningar: print('VARNING', w)
    for f in fel_lista: print('FEL', f)
    print(f'{len(fel_lista)} fel, {len(varningar)} varningar. {len(R["edits"])} redigeringar, {len(K["matning"]["kvalitet"])} kvalitetsposter, {n_hash} hashar kontrollerade.')
    sys.exit(1 if fel_lista else 0)


main()
