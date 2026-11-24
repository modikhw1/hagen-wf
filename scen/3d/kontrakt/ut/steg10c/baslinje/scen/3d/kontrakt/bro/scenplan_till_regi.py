"""Harnessens scenplan + kalla + patch + kundlinje -> förslag till regi.json (harnessen föreslår, tillämpar aldrig).

Kör från projektroten:
  scen/.venv/Scripts/python.exe scen/3d/kontrakt/bro/scenplan_till_regi.py \
      <scenplan.json> <kalla.json> <patch.json> <linje.json> <ut_mapp> [--konto K --id ID] [--platsbank mapp]

Skriver två filer i <ut_mapp>:
  forslag.json  alla förslag, regi-formade, med extra fält under "forslag" (behover_text, valfri, konfidens ...)
  regi.json     det som schemat kan uttrycka. Förslag som saknar text eller är valfria blir en flagga (allvar fraga)
                så att de syns men inte ändrar filmen.
Alla redigeringar har ursprung harness-forslag och godkand_av_cm null. kompilera.py tillämpar inte sådana
förrän CM har godkänt dem. Inga texter hittas på: en ny replik skrivs bara om planen bär den.
Scenplanen kommer ur video/format/h-scener.mjs (scenplan(c, L)), se gor_scenplan.mjs.
Bara standardbiblioteket.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ATGARDER = ('behall', 'fritt', 'byt_produkt', 'byt_lokal', 'frontfigur', 'risk', 'eget_tal', 'forenkla')
HARNESS_ENUM = ('behall', 'byt', 'byt_produkt', 'byt_lokal', 'frontfigur', 'risk', 'eget_tal', 'forenkla', 'tillat', 'fritt')
OKAND_ROST = dict(motor=None, rost_id=None, stil=None)


def ladda(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def skriv(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def slug(t):
    t = (t or '').lower()
    for a, b in (('å', 'a'), ('ä', 'a'), ('ö', 'o'), ('é', 'e')):
        t = t.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '_', t).strip('_') or 'x'


# ---------------------------------------------------------------- uppslag i kalla
def personer_i(kalla, scen_ids):
    """Personer i scenerna, i ordning. Personer utan roll (okand_*) räknas bara om inga andra finns."""
    pid = {p['id']: p for p in kalla['semantik']['personer']}
    alla = []
    for s in kalla['semantik']['scener']:
        if s['id'] in scen_ids:
            for p in s['personer']:
                if p not in alla:
                    alla.append(p)
    kand = [p for p in alla if pid.get(p, {}).get('roll') is not None]
    return kand or alla


def repliker_i(kalla, scen_ids):
    return [r for r in kalla['semantik']['repliker'] if r.get('scen') in scen_ids]


def props_i(kalla, scen_ids):
    """Props som scenerna äger: agare eller fäste är en person i scenen, eller rum_ref är en fast del i scenens rum."""
    sem = kalla['semantik']
    scener = [s for s in sem['scener'] if s['id'] in scen_ids]
    pers = {p for s in scener for p in s['personer']}
    rum = {r['id']: r for r in sem['rum']}
    fasta = set()
    for s in scener:
        fasta.update(rum.get(s.get('miljo'), {}).get('fasta', []))
    ut = []
    for p in sem['props']:
        faste = p.get('faste') or {}
        if p.get('agare') in pers or (faste.get('person') in pers if isinstance(faste, dict) else False) or p.get('rum_ref') in fasta:
            ut.append(p)
    return ut


def produktlista(L):
    t = (L.get('produkter') or '').strip().rstrip('.')
    delar = re.split(r',\s*|\s+och\s+', t)
    return [d.strip() for d in delar if d.strip()]


def valj_frontfigur(L, skal):
    fram = L.get('frontfigurer') or []
    for f in fram:
        if skal and skal.startswith(f.get('etikett', '\0')):
            return f
    return next((f for f in fram if f.get('funktion') == 'fokus'), fram[0] if fram else None)


# Generiska rumsmallar som kan passa en lokaldel i kundlinjen. Bara ett tips till CM: mallarna är inte kundens lokal.
LOKAL_TILL_MALL = {'bar': ['bar_disk'], 'disk_kassa': ['bar_disk'], 'matsal': ['restaurang_tva']}


def _ids(mapp):
    ut = set()
    if mapp and Path(mapp).is_dir():
        for f in sorted(Path(mapp).glob('*.json')):
            try:
                ut.add(ladda(f).get('id', f.stem))
            except (ValueError, OSError):
                continue
    return ut


def hitta_plats(L, platsbank=None, rumsmall=None):
    """Mall eller plats för kunden, bara vid exakt id: <konto> eller <konto>_<lokaldel>. Returnerar
    ('rumsmall_id', id), ('tillgang_id', id) eller None. Ingen gissning på liknande namn."""
    konto = L.get('konto')
    kand = [konto] + [f'{konto}_{d}' for d in L.get('lokal') or []]
    for fält, mapp in (('rumsmall_id', rumsmall), ('tillgang_id', platsbank)):
        ids = _ids(mapp)
        for k in kand:
            if k in ids:
                return fält, k
    return None


# ---------------------------------------------------------------- redigeringar
class Bygg:
    def __init__(self, plan_fil):
        self.edits = []
        self.plan_fil = plan_fil

    def ny(self, op, b, kommentar, konf, extra=None, **falt):
        e = dict(id=f'h{len(self.edits) + 1}', op=op,
                 ursprung=dict(typ='harness-forslag',
                               harness=dict(atgard=b['atgard'], beat_nr=b['nr'], funktion=b.get('funktion'),
                                            skal=b.get('skal'), kalla_fil=self.plan_fil),
                               godkand_av_cm=None, tid=None),
                 kommentar=kommentar)
        e.update(falt)
        ex = dict(status='forslag', beat_nr=b['nr'], konfidens=konf, behover_text=False, valfri=False,
                  tillampas_som_standard=True, varning=None)
        ex.update(extra or {})
        e['forslag'] = ex
        self.edits.append(e)
        return e


def bygg_forslag(plan, kalla, patch, L, plan_fil=None, platsbank=None, rumsmall=None):
    beats = plan['beats']
    just = {j['beat_nr']: j for j in patch['justering']}
    scen_ordning = [s['id'] for s in kalla['semantik']['scener']]
    alla_beats_per_scen = {}
    for j in patch['justering']:
        for s in j['scener']:
            alla_beats_per_scen.setdefault(s, []).append(j['beat_nr'])
    bygg = Bygg(plan_fil)
    varningar, behalls, hoppade = [], [], []
    casta_sedd = {}
    produkter = produktlista(L)
    plats = hitta_plats(L, platsbank, rumsmall)
    mallar = [m for d in L.get('lokal') or [] for m in LOKAL_TILL_MALL.get(d, [])]
    mallar = [m for i, m in enumerate(mallar) if m not in mallar[:i]]
    for b in beats:
        nr, at = b['nr'], b['atgard']
        if at not in HARNESS_ENUM:
            raise ValueError(f'okänd åtgärd {at!r} i beat {nr}')
        if nr not in just:
            raise ValueError(f'patchen har ingen justering för beat {nr}')
        scener, konf = just[nr]['scener'], just[nr]['konfidens']
        skal = b.get('skal') or ''
        bas = f"Beat {nr} ({b.get('funktion')}, {b.get('bar')}): {skal}"
        lag = ' Beatet är bara grovt placerat på scenen (konfidens lag): kontrollera.' if konf == 'lag' else ''
        if at == 'behall':
            behalls.append(nr)
        elif at == 'risk':
            sc = scener[0] if len(scener) == 1 else None
            bygg.ny('flagga', b, bas + (f' Berörda scener: {", ".join(scener)}.' if len(scener) > 1 else ''), konf,
                    scen=sc, orsak=skal or 'Harnessen flaggar en risk utan skäl.', allvar='risk',
                    extra=dict(tillampas_som_standard=False))
            varningar.append(dict(beat_nr=nr, atgard=at, scener=scener, text=skal))
        elif at == 'eget_tal':
            rep = repliker_i(kalla, scener)
            ny = b.get('replik', b.get('ny_replik'))
            ny = [ny] if isinstance(ny, str) else ny
            if not rep:
                bygg.ny('flagga', b, bas + ' Scenerna har inga repliker att byta; en ny replik måste läggas till av CM.' + lag, konf,
                        scen=scener[0] if len(scener) == 1 else None,
                        orsak=f'Eget tal i beat {nr}, men kalla har inga repliker i {", ".join(scener)}. CM lägger till repliker.',
                        allvar='fraga', extra=dict(behover_text=True, tillampas_som_standard=False))
                continue
            ok = isinstance(ny, list) and len(ny) == len(rep) and all(isinstance(t, str) and t.strip() for t in ny)
            for k, r in enumerate(rep):
                text = ny[k] if ok else None
                bygg.ny('byt_replik', b,
                        bas + (' Texten kommer ur planen.' if ok else ' Ingen ny text finns: CM eller ett senare steg skriver den.') + lag, konf,
                        extra=dict(behover_text=not ok, originaltext=r['text'], scen=r.get('scen'), harness_replik_beat=ny if ny and not ok else None),
                        replik=r['id'], text=text, sprak=r['sprak'], rost=dict(OKAND_ROST),
                        tidspolicy='samma_lucka', max_talfaktor=None)
        elif at == 'frontfigur':
            f = valj_frontfigur(L, skal)
            if f is None:
                bygg.ny('flagga', b, bas, konf, scen=scener[0] if len(scener) == 1 else None,
                        orsak='Frontfigur föreslogs men kundlinjen har ingen.', allvar='risk',
                        extra=dict(tillampas_som_standard=False))
                continue
            pers = personer_i(kalla, scener)
            antal = {p: sum(1 for r in repliker_i(kalla, scener) if r['talare'] == p) for p in pers}
            topp = sorted(pers, key=lambda p: (-antal[p], pers.index(p)))
            vald = topp[0] if topp and (len(topp) == 1 or antal[topp[0]] > antal[topp[1]]) else None
            person = vald or 'PLATSHALLARE:person_beat' + str(nr)
            nyckel = (person, f['etikett'])
            if nyckel in casta_sedd:
                casta_sedd[nyckel]['forslag']['beat_nr_ovriga'] = casta_sedd[nyckel]['forslag'].get('beat_nr_ovriga', []) + [nr]
                hoppade.append(dict(beat_nr=nr, atgard=at, orsak=f'{person} castas redan som {f["etikett"]} av beat {casta_sedd[nyckel]["forslag"]["beat_nr"]}'))
                continue
            kom = bas + (f' Personen är den som talar mest i scenen.' if vald and len(pers) > 1 else '') \
                + ('' if vald else f' CM väljer person bland: {", ".join(pers) or "inga kända"}.') + lag
            casta_sedd[nyckel] = bygg.ny(
                'casta', b, kom, konf,
                extra=dict(kandidater=pers, kundens_frontfigur=f, person_vald_av_harness=bool(vald)),
                person=person, kundroll=dict(id='PLATSHALLARE:' + slug(L.get('konto')) + ':' + slug(f['etikett']), namn=f['etikett']),
                utseende=dict(rigg_ref=None, troja_farg=None, hud=None, har=None, harstil=None, hojd_m=None), rost=None)
        elif at == 'byt_produkt':
            pr = props_i(kalla, scener)
            ny_typ = produkter[0] if produkter else None
            if ny_typ is None:
                bygg.ny('flagga', b, bas, konf, scen=scener[0] if len(scener) == 1 else None,
                        orsak='Produkten ska bytas men kundlinjen har inga produkter.', allvar='fraga',
                        extra=dict(tillampas_som_standard=False))
                continue
            mal = pr if pr else [None]
            for p in mal:
                bygg.ny('byt_prop', b,
                        bas + (' Målet är det första av kundens produkter; CM väljer.' ) +
                        ('' if p else ' Inget prop i scenerna kopplas till beatet i kalla: CM pekar ut vilket.') + lag, konf,
                        extra=dict(alternativ=produkter, mal_saknas=p is None),
                        prop=p['id'] if p else f'PLATSHALLARE:prop_beat{nr}', ny_typ=ny_typ, tillgang_id=None, matt_m=None)
        elif at == 'byt_lokal':
            for s in scener:
                rum = (dict(kalla='bank', tillgang_id=plats[1] if plats[0] == 'tillgang_id' else None, ord=[], beskrivning=None,
                            **({'rumsmall_id': plats[1]} if plats[0] == 'rumsmall_id' else {})) if plats else
                       dict(kalla='ord', tillgang_id=None, ord=list(L.get('lokal') or []),
                            beskrivning='Kundens lokal, delar: ' + ', '.join(L.get('lokal') or ['okänd'])))
                bygg.ny('byt_miljo', b,
                        bas + ('' if plats else ' Kundens lokal finns varken som plats i plats_bank eller som mall i rumsmall: den måste skapas.' + (f' Generiska mallar att utgå från: {", ".join(mallar)}.' if mallar else '')) + lag, konf,
                        extra=dict(plats_saknas=plats is None, kundens_lokaldelar=list(L.get('lokal') or []), mallkandidater=mallar),
                        scen=s, rum=rum, ankare=[], rakna_om_kontakt=True)
        elif at == 'forenkla':
            for s in scener:
                pers = personer_i(kalla, [s])
                regler = ['inga_effekter']
                mp = L.get('max_personer')
                if isinstance(mp, int) and len(pers) > mp:
                    regler.append('farre_personer')
                bygg.ny('forenkla', b, bas + lag, konf, scen=s, regler=regler)
        elif at == 'fritt':
            for s in scener:
                delar = [n for n in alla_beats_per_scen.get(s, []) if n != nr]
                bygg.ny('fri_scen', b,
                        bas + ' Valfritt: förslaget är att scenen stryks, men kunden kan också göra den på eget sätt.' + lag, konf,
                        extra=dict(valfri=True, tillampas_som_standard=False,
                                   varning=(f'Scenen delas med beat {", ".join(map(str, delar))}; strykning tar bort även dem.' if delar else None)),
                        scen=s, lage='stryk')
    kt = kalla['tidsbas']
    v = kalla['klipp']['video']
    standard = [
        'utdata.fps = kallans tidsbas', 'utdata.bredd/hojd = kallans video', 'utdata.stil_ref = null',
        'utdata.ljudpolicy = original (ingen röstsyntes bestäms av harnessen)', 'utdata.render_backend = blender_mhr',
        'ramar = inga låsta beats, ingen offsetgräns, retiming tillåten, max_talfaktor 1.15 (som exemplen)']
    from collections import Counter
    return dict(
        schema_version='regi-forslag/1',
        kalla=dict(klipp_id=kalla['klipp']['id'], sha256=kalla['klipp']['sha256'], revision=kalla['revision']),
        kund=dict(id=L.get('konto'), namn=None),
        skapad=None,
        edits=bygg.edits,
        utdata=dict(fps_taljare=kt['fps_taljare'], fps_namnare=kt['fps_namnare'], bredd=v['bredd'], hojd=v['hojd'],
                    stil_ref=None, ljudpolicy='original', render_backend='blender_mhr'),
        ramar=dict(bevara_beats=[], bevara_klippoffset_s=None, tillat_retiming=True, max_talfaktor=1.15),
        standardvarden=standard,
        varningar=varningar,
        behalls_beats=behalls,
        hoppade_over=hoppade,
        sammanfattning=dict(per_op=dict(sorted(Counter(e['op'] for e in bygg.edits).items())),
                            per_atgard=dict(sorted(Counter(b['atgard'] for b in beats).items())),
                            antal_forslag=len(bygg.edits)),
    )


def till_regi(forslag):
    """Det schemat kan uttrycka. Förslag som behöver text, eller som är valfria, blir en flagga (fraga)."""
    edits = []
    for e in forslag['edits']:
        ex = e['forslag']
        k = {n: v for n, v in e.items() if n != 'forslag'}
        if e['op'] == 'byt_replik' and (k['text'] is None):
            orsak = (f"Eget tal: byt replik {k['replik']} (\"{ex.get('originaltext')}\") mot ny text som ännu inte finns. "
                     'CM eller ett senare steg skriver den.')
            k = dict(id=k['id'], op='flagga', ursprung=k['ursprung'], kommentar=k['kommentar'],
                     scen=ex.get('scen'), orsak=orsak, allvar='fraga')
        elif e['op'] == 'fri_scen':
            k = dict(id=k['id'], op='flagga', ursprung=k['ursprung'], kommentar=k['kommentar'], scen=k['scen'],
                     orsak=f"Valfritt: scenen {k['scen']} bär inte idén och kan strykas eller göras fritt av kunden."
                           + (' ' + ex['varning'] if ex.get('varning') else ''),
                     allvar='fraga')
        edits.append(k)
    return dict({'$schema': 'regi.schema.json', 'schema_version': 'regi/1'}, kalla=forslag['kalla'], kund=forslag['kund'],
                skapad=None, edits=edits, utdata=forslag['utdata'], ramar=forslag['ramar'])


def valj_plan(data, konto=None, id_=None):
    if 'beats' in data:
        return data
    if konto and id_ and konto in data and id_ in data[konto]:
        return data[konto][id_]
    raise ValueError('filen är inte en scenplan; ange --konto och --id för en pass6-fil')


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for n in ('plan', 'kalla', 'patch', 'linje', 'ut'):
        a.add_argument(n)
    a.add_argument('--konto')
    a.add_argument('--id')
    a.add_argument('--platsbank', default=str(Path(__file__).resolve().parent.parent / 'plats_bank'))
    a.add_argument('--rumsmall', default=str(Path(__file__).resolve().parent.parent / 'rumsmall'))
    x = a.parse_args()
    ut = Path(x.ut)
    if (ut / 'regi.json').exists() or (ut / 'forslag.json').exists():
        a.error('regi.json eller forslag.json finns redan i utmappen; välj en ny.')
    plan = valj_plan(ladda(x.plan), x.konto, x.id)
    f = bygg_forslag(plan, ladda(x.kalla), ladda(x.patch), ladda(x.linje), plan_fil=Path(x.plan).as_posix(), platsbank=x.platsbank, rumsmall=x.rumsmall)
    skriv(ut / 'forslag.json', f)
    skriv(ut / 'regi.json', till_regi(f))
    print(json.dumps(f['sammanfattning'], ensure_ascii=False))


if __name__ == '__main__':
    main()
