"""Långlivad kompilatorprocess för webbvärlden. Importerar kontraktets kompilator en gång.

Protokoll: en JSON-rad per begäran på stdin, en JSON-rad per svar på stdout.
  {"id":..,"cmd":"kompilera","regi":{...regi/1...}}  -> snabb kompilering (snabb=True)
  {"id":..,"cmd":"spara_plan","fil":"plan-x.json"}    -> skriver senaste snabba plan under pipeline/snabb/
  {"id":..,"cmd":"diagnostik","plan":"plan-x.json"}   -> full kvalitetskontroll av en sparad snabb plan (egen process; syntetiserar även väntande tal)
  {"id":..,"cmd":"forvarm"}                           -> räknar skymningsdata för alla källrutor i senaste plan (efter grundkompileringen)
  {"id":..,"cmd":"syntetisera_tal","plan":"plan-x.json"} -> talsyntes som eget steg för en sparad snabb plan
  {"id":..,"cmd":"stang"}
Allt som loggas går till stderr. Cachen läggs under forvarld/varld/pipeline/cache,
så att inget skrivs under scen/. Kompilatorn ändras inte.
"""
import json, os, sys, time, hashlib, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KONTRAKT = ROOT / 'scen/3d/kontrakt'
sys.dont_write_bytecode = True
sys.path.insert(0, str(KONTRAKT))
os.chdir(ROOT)
for s in (sys.stdout, sys.stderr):
    s.reconfigure(encoding='utf-8')

t0 = time.perf_counter()
_CACHE = Path(os.environ.get('NOTAN_CACHE') or HERE / 'pipeline/cache')
os.environ.setdefault('TAL_CACHE', str(_CACHE.parent / (_CACHE.name + '_tal')))   # talcachen läses av tal.py vid import
import datacache
datacache.CACHE = _CACHE
import kompilera as K
from gemensamt import ladda, skriv
IMPORT_MS = (time.perf_counter() - t0) * 1000

KALLA = HERE / 'pipeline/kalla.json'
UT = HERE / 'pipeline/snabb'
UT.mkdir(parents=True, exist_ok=True)
senaste = {'plan': None}


def runs(tal):
    """Komprimerar en lista heltal till [start, slut)-intervall (kompakt och jämförbar)."""
    out = []
    for t in tal:
        if out and out[-1][1] == t:
            out[-1][1] = t + 1
        else:
            out.append([t, t + 1])
    return out


def sammanfatta(plan):
    return dict(
        tidskarta=plan['tidskarta'],
        kallrutor_intervall=runs(plan['kallrutor']),
        antal_rutor=len(plan['kallrutor']),
        scener=[dict(id=s['id'], ut=s['ut'], kalla=s['kalla']) for s in plan['scener']],
        skarmtext=[dict(id=t['id'], scen=t['scen'], text=t.get('text'), start_s=t.get('start_s'),
                        slut_s=t.get('slut_s'), box=t.get('box'), stil=t.get('stil')) for t in plan.get('skarmtext') or []],
        renderkamera=plan.get('renderkamera'),
        objekt=[dict(id=o['id'], typ=o.get('typ'), status=o.get('status')) for o in plan.get('objekt') or []
                if not str(o['id']).startswith(('golv', 'vagg'))][:400],
        antal_objekt=len(plan.get('objekt') or []),
        props=plan.get('props'),
        personer=plan.get('personer'),
        plats=[dict(id=p['id']) for p in plan.get('plats') or []],
        scen_plats=[dict(id=s['id'], plats_id=s.get('plats_id')) for s in plan['scener']],
        tal=plan.get('tal'),
        tillgangar=[dict(id=o['id'], tillgang=o['tillgang']) for o in (plan.get('objekt') or []) + (plan.get('props') or []) if o.get('tillgang')],
        lokalbyte=plan.get('lokalbyte') or [],
        tillampat=[dict(id=e['id'], op=e['op'], andring=json.dumps(e.get('andring'), ensure_ascii=False)[:200]) for e in plan['tillampat']],
        ej_tillampat=[dict(id=e['id'], op=e['op'], orsak=e.get('orsak')) for e in plan['ej_tillampat']],
        varningar=plan['varningar'],
        diagnostik=plan['kvalitet'].get('diagnostik'),
        utdata=plan['utdata'],
    )


def kompilera(msg):
    regi = msg['regi']
    fil = UT / 'regi-latest.json'
    fil.write_text(json.dumps(regi, ensure_ascii=False), encoding='utf-8')
    t = time.perf_counter()
    plan = K.kompilera(str(KALLA), str(fil), snabb=True)
    ms_komp = (time.perf_counter() - t) * 1000
    senaste['plan'] = plan
    t = time.perf_counter()
    sam = sammanfatta(plan)
    return dict(ok=True, kompileraMs=ms_komp, sammanfattaMs=(time.perf_counter() - t) * 1000, sammanfattning=sam)


def spara_plan(msg):
    if not senaste['plan']:
        raise ValueError('Ingen snabb plan finns än.')
    fil = UT / msg['fil']
    t = time.perf_counter()
    skriv(fil, senaste['plan'])
    return dict(ok=True, fil=str(fil.relative_to(ROOT)), skrivMs=(time.perf_counter() - t) * 1000)


def forvarm(msg):
    """Räknar skymningens ruta- och träffdata för alla källrutor i senaste plan, så att nya tidsurval går snabbt (skymning.forvarm)."""
    import skymning
    if not senaste['plan']:
        raise ValueError('Ingen snabb plan finns än.')
    t = time.perf_counter()
    n = skymning.forvarm(senaste['plan'])
    return dict(ok=True, rutor=n, forvarmMs=(time.perf_counter() - t) * 1000)


def syntetisera_tal(msg):
    """Separat talsteg: syntetiserar väntande repliker i en sparad snabb plan (tal.syntetisera_plan) och skriver en ny planfil."""
    import tal
    t = time.perf_counter()
    plan = tal.syntetisera_plan(ladda(UT / msg['plan']))
    ut = UT / f'plan-tal-{int(time.time())}.json'
    skriv(ut, plan)
    return dict(ok=True, syntesMs=(time.perf_counter() - t) * 1000, fil=str(ut.relative_to(ROOT)),
                tal=[dict(edit=x['edit'], ljud=x.get('ljud'), regel=x.get('regel'), taktfaktor=x.get('taktfaktor_mot_original')) for x in plan.get('tal', [])],
                varningar=plan['varningar'])


def sammanfatta_kvalitet(q):
    bt = q.get('bildtrohet', {})
    pers = bt.get('personer') or []
    kropp = (q.get('kropp') or {}).get('rader') or []
    sky = ((q.get('skymning') or {}).get('fore') or {}).get('per_del') or []
    return dict(
        bildtrohet=dict(flaggad=bt.get('flaggad'), status=bt.get('status'), granser=bt.get('granser'),
                        personer=[dict(scen=x['scen'], person=x['person'], median_px=round(x['median_px'], 2), p90_px=round(x['p90_px'], 2),
                                       bbox_iou=round(x['bbox_iou'], 3), flaggad=x['flaggad']) for x in pers],
                        utelamnade=bt.get('utelamnade_personer')),
        kropp=dict(grans=(q.get('kropp') or {}).get('grans'),
                   rader=[dict(scen=r['scen'], person=r['person'], tackning=r.get('tackning'),
                               iou_synlig_median=(r.get('mask') or {}).get('iou_synlig_median'),
                               tyngdpunkt_p90=(r.get('mask') or {}).get('tyngdpunkt_p90')) for r in kropp]),
        skymning=dict(delar=len(sky), flaggade=sum(1 for d in sky if d.get('flaggad'))))


def diagnostik(msg):
    import diagnostik as D
    t = time.perf_counter()
    plan = D.diagnostik(ladda(UT / msg['plan']))
    ms = (time.perf_counter() - t) * 1000
    ut = UT / f'plan-kontrollerad-{int(time.time())}.json'
    skriv(ut, plan)
    q = plan['kvalitet']
    bt = q.get('bildtrohet', {})
    return dict(ok=True, diagnostikMs=ms, fil=str(ut.relative_to(ROOT)),
                bildtrohetFlaggad=bt.get('flaggad'), bildtrohetStatus=bt.get('status'),
                varningar=plan['varningar'],
                kvalitet=sammanfatta_kvalitet(q))


def main():
    print(json.dumps(dict(ready=True, importMs=IMPORT_MS)), flush=True)
    for rad in sys.stdin:
        rad = rad.strip()
        if not rad:
            continue
        msg = {}
        try:
            msg = json.loads(rad)
            cmd = msg.get('cmd')
            if cmd == 'stang':
                print(json.dumps(dict(id=msg.get('id'), ok=True)), flush=True)
                return
            svar = dict(kompilera=kompilera, diagnostik=diagnostik, spara_plan=spara_plan, forvarm=forvarm, syntetisera_tal=syntetisera_tal)[cmd](msg)
        except Exception as e:
            svar = dict(ok=False, fel=f'{type(e).__name__}: {e}', spar=traceback.format_exc()[-1500:])
        svar['id'] = msg.get('id')
        print(json.dumps(svar, ensure_ascii=False), flush=True)



if __name__ == '__main__':
    main()
