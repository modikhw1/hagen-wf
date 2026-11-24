"""Engångsinkoppling av händelser och tidsatta props; sparar före ändring."""
import json
from steg10_filer import andra


def ersatt(s, old, new):
    assert s.count(old) == 1, old[:120]
    return s.replace(old, new)


def kalla(s):
    d = json.loads(s)
    def field(desc, typ, **kw): return dict(description=desc, type=typ, **kw)
    nullable = lambda desc: field(desc, ['string', 'null'])
    d['properties']['semantik']['properties']['handelser'] = field('Valfria händelser på källklockan. Tidpunkt: start_s = slut_s.', 'array', items={'$ref': '#/$defs/handelse'})
    d['properties']['matning']['properties']['handelsekallor'] = field('Hashlåsta underlag för händelser. Efter ändring ska händelser mätas om.', 'array', items={'$ref': '#/$defs/filref'})
    props = dict(id=field('Unikt händelse-id.', 'string', minLength=1),
        typ=field('Vad detektionen eller bedömningen avser.', 'string', enum=['person_synlig','person_forsvinner','handmote','replik_start','prop_synlig','hallarbyte_kandidat','scen_handling']),
        vad=field('Konkret beskrivning, med begränsningar.', 'string', minLength=1),
        vem=nullable('Person-id eller null när det är okänt.'), till_vem=nullable('Mottagarens person-id eller null.'),
        prop=nullable('Prop-id eller null.'), scen=field('Scen-id.', 'string'),
        start_s=field('Start på hela klippets källklocka.', 'number', minimum=0),
        slut_s=field('Slut på källklockan; samma som start vid en tidpunkt.', 'number', minimum=0),
        ursprung=field('Ursprung och konfidens för själva påståendet.', 'object', properties=dict(
            typ=field('Uppmätt, antaget eller tidigare modellbedömt.', 'string', enum=['uppmatt','antagen','modellbedomd']),
            metod=field('Hur uppgiften togs fram och dess begränsning.', 'string'),
            konfidens=field('Bedömd tillförlitlighet, ingen kalibrerad sannolikhet.', 'string', enum=['lag','medel','hog']),
            modell=nullable('Sparad modell vid modellbedömning, annars null.')),
            required=['typ','metod','konfidens','modell'], additionalProperties=False),
        bevis=field('Lokal evidens; rutnummer ligger i mätdelen av händelsens belägg.', 'object', properties=dict(
            filer=field('Relativa sökvägar, hashlåsta i matning.handelsekallor.', 'array', items=field('Sökväg.', 'string')),
            rutor=field('Källrutor från noll, slutgräns får vara antal_rutor.', 'array', items=field('Ruta.', 'integer', minimum=0)),
            notering=field('Osäkerhet och observationens innebörd.', 'string')), required=['filer','rutor','notering'], additionalProperties=False))
    # Semantik innehåller sekunder och id; provrutorna hör till matning.
    props.pop('bevis')
    d['$defs']['handelse'] = field('En tidsatt observation eller tydligt märkt bedömning.', 'object', properties=props, required=list(props), additionalProperties=False)
    d['properties']['matning']['properties']['handelsebevis'] = field('Belägg till händelser, med bildrutor och filer.', 'array', items=field('Belägg för ett händelse-id.', 'object', properties=dict(
        handelse=field('Id i semantik.handelser.', 'string'),
        filer=field('Relativa sökvägar.', 'array', items=field('Sökväg.', 'string')),
        rutor=field('Källrutor, slutgräns får vara antal_rutor.', 'array', items=field('Ruta.', 'integer', minimum=0)),
        notering=field('Observationens begränsningar.', 'string')), required=['handelse','filer','rutor','notering'], additionalProperties=False))
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def regi(s):
    d = json.loads(s)
    def field(desc, typ, **kw): return dict(description=desc, type=typ, **kw)
    d['$defs']['handelseankare'] = field('Händelse på hela klippets källklocka; spann kräver en uttrycklig kant.', 'object', properties=dict(
        handelse=field('Id i kalla.semantik.handelser.', 'string', minLength=1),
        kant=field('Välj början eller slutet av ett händelsespann.', 'string', enum=['start','slut']),
        offset_s=field('Offset från händelsens kant i sekunder.', 'number')),
        required=['handelse'], additionalProperties=False)
    d['$defs']['handelseram'] = field('Från/fram till händelser, halvöppet intervall på källklockan.', 'object', properties=dict(
        fran=dict(description='Från denna händelse.', **{'$ref':'#/$defs/handelseankare'}),
        till=dict(description='Fram till denna händelse.', **{'$ref':'#/$defs/handelseankare'})), minProperties=1, additionalProperties=False)
    for op in ['trimma_scen','skarmtext','byt_prop','lagg_till_prop','ta_bort_prop','flytta_prop']:
        d['$defs'][op]['properties']['tid'] = dict(description='Valfria händelseankare. Utelämnad gräns är aktuell scenkant.', **{'$ref':'#/$defs/handelseram'})
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def kompilera(s):
    s = ersatt(s, "    for e in R['edits']:\n        # En edit är atomisk", "    tidsbeslut = {}\n    for e in R['edits']:\n        # En edit är atomisk")
    s = ersatt(s, "        try:\n            if e['ursprung']['typ']=='harness-forslag'", "        try:\n            from handelser import los_edit\n            try:\n                e, tidsbeslut_edit = los_edit(e, K['semantik'].get('handelser', []), K['tidsbas']['langd_s'])\n            except ValueError as ex:\n                raise EjTillampad(str(ex)) from ex\n            if e['ursprung']['typ']=='harness-forslag'")
    start = s.index("            elif op in ('byt_prop','lagg_till_prop','flytta_prop','ta_bort_prop'):")
    end = s.index("            elif op=='byt_miljo':", start)
    s = s[:start] + '''            elif op in ('byt_prop','lagg_till_prop','flytta_prop','ta_bort_prop'):
                if e.get('tillgang_id'): raise EjTillampad('Extern proptillgång är reserverad; använd en typ i propbanken.')
                from proptid import andra as andra_prop
                span = (ruta(tidsbeslut_edit['kalla_s'].get('start_s', 0)), ruta(tidsbeslut_edit['kalla_s'].get('slut_s', K['tidsbas']['langd_s']))) if tidsbeslut_edit else (0, N)
                for s in valda(e):
                    def redigera(o):
                        if op=='lagg_till_prop':
                            if o is not None: raise EjTillampad('Objekt-id finns redan i det valda intervallet.')
                            from propbank import BANK
                            if e['typ'] in BANK:
                                from propplan import ny
                                o=ny(e)
                                if e.get('faste'):
                                    if e['faste']['person'] not in {m['person'] for m in ktx[s['kx']]['ms']} or e['faste']['led'] not in lednamn:
                                        raise EjTillampad('Handfästets person eller led saknas i scenen.')
                                else: placera(s,o,e.get('plats'),e.get('stod'))
                            else:
                                if e.get('faste'): raise EjTillampad('Handfäste kräver en typ i propbanken.')
                                o=dict(id=e['ny_id'],namn='rum:'+e['typ']+':'+e['ny_id'],typ='lada',matt_m=storlek(e.get('matt_m')),rotation_rad=[0,0,0],farg='#e2ac46',top_slope=0)
                                placera(s,o,e.get('plats'),e.get('stod'))
                        else:
                            if o is None: raise EjTillampad('Objektet finns inte i det valda intervallet: '+e['prop'])
                            if op=='ta_bort_prop': return None
                            if op=='flytta_prop':
                                if not e['till']: raise EjTillampad('Flytt kräver en explicit placering.')
                                placera(s,o,e['till'])
                                if o['typ']=='rekvisita': o['propdata']['lage']='explicit'
                            elif o['typ']=='rekvisita':
                                from propplan import byt
                                try: byt(o,e['ny_typ'],e.get('matt_m'))
                                except ValueError as exc: raise EjTillampad(str(exc))
                            else:
                                o.update(namn='rum:'+e['ny_typ']+':'+e['prop'],farg='#e2ac46')
                                if e.get('matt_m') is not None: o['matt_m']=storlek(e['matt_m'])
                        return o
                    changed=andra_prop(s,e.get('ny_id') if op=='lagg_till_prop' else e['prop'],span,redigera)
                    if changed is not None: andring[s['id']]=changed
                if not andring: raise EjTillampad('Händelseintervallet träffar ingen vald scen.')
''' + s[end:]
    # Spara bara tidsbeslut från lyckade edits, så att atomisk återställning gäller.
    marker = "tillampat.append("
    pos = s.index(marker)
    line_start = s.rfind('\n', 0, pos) + 1
    indent = s[line_start:pos]
    s = s[:line_start] + indent + "if tidsbeslut_edit: tidsbeslut[e['id']] = tidsbeslut_edit\n" + s[line_start:]
    s = ersatt(s, "                o=copy.deepcopy(o); o['synlig_ut']=[start,slut]\n                if flerklipp or o['typ']=='rekvisita': o['scen']=s['id']\n                byggobjekt.append(o)",
        "                from proptid import byggposter\n                for o in byggposter(o,s,[start,slut]):\n                    if flerklipp or o['typ']=='rekvisita': o['scen']=s['id']\n                    byggobjekt.append(o)")
    s = ersatt(s, "            if fk[0][1]['typ']!='rekvisita' and len(fk)==len(scener)", "            if not any('_propversioner' in o for _,o in fk) and fk[0][1]['typ']!='rekvisita' and len(fk)==len(scener)")
    s = ersatt(s, "                    o=copy.deepcopy(o); o['synlig_ut']=list(iv_ut[s['id']])\n                    if flerklipp or o['typ']=='rekvisita': o['scen']=s['id']\n                    byggobjekt.append(o)",
        "                    from proptid import byggposter\n                    for o in byggposter(o,s,iv_ut[s['id']]):\n                        if flerklipp or o['typ']=='rekvisita': o['scen']=s['id']\n                        byggobjekt.append(o)")
    s = ersatt(s, "uppl?st hand-/ytf?ste. Grepp, djup och dolda sidor ?r antagna; m?tregion", "upplöst hand-/ytfäste. Grepp, djup och dolda sidor är antagna; mätregion")
    marker = "    reks=[o for o in plan['objekt'] if o['typ']=='rekvisita']"
    s = ersatt(s, marker, '''    from handelser import till_plan, intervall_ut
    if K['semantik'].get('handelser'):
        plan['handelser'] = till_plan(K['semantik']['handelser'], scener, intervall, float(fps), ruta)
    for applied in tillampat:
        if applied['id'] in tidsbeslut:
            timing = tidsbeslut[applied['id']]
            bounds = timing['kalla_s']
            occurrences = intervall_ut(ruta(bounds.get('start_s', 0)), ruta(bounds.get('slut_s', K['tidsbas']['langd_s'])), scener, intervall, float(fps))
            selected = next(e for e in R['edits'] if e['id'] == applied['id']).get('scen', 'alla')
            timing['forekomster'] = [x for x in occurrences if selected == 'alla' or x['scen'] == selected]
            applied['andring']['tid'] = timing
''' + marker)
    return s


def propplan(s):
    s = ersatt(s, "p=o['propdata'];a,b=sc['ut'];refs=p.get('bildregioner',[])", "p=o['propdata'];sa,sb=sc['ut'];a,b=o.get('synlig_ut',sc['ut']);refs=p.get('bildregioner',[])")
    s = ersatt(s, "uref=a+fref-sc['lokal_start']", "uref=sa+fref-sc['lokal_start']")
    s = ersatt(s, "uref=int(np.clip(uref,a,b-1))", "uref=int(np.clip(uref,a,b-1));fref=sc['lokal_start']+uref-sa")
    s = ersatt(s, "f=sc['lokal_start']+u-a", "f=sc['lokal_start']+u-sa")
    s = ersatt(s, "u=a+ref['lokal_ruta']-sc['lokal_start']", "u=sa+ref['lokal_ruta']-sc['lokal_start']")
    s = ersatt(s, "report.append(dict(scen=sc['id'],prop=o['id']", "report.append(dict(scen=sc['id'],ut=[a,b],prop=o['id']")
    return s


if __name__ == '__main__':
    for name, fn in [('kalla.schema.json',kalla),('regi.schema.json',regi),('kompilera.py',kompilera),('propplan.py',propplan)]:
        andra('scen/3d/kontrakt/' + name, fn)
