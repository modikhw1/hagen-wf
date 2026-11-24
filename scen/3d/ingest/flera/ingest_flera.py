"""Flertagningsklipp: ett källklipp med klipp inuti -> tagningar -> ingest_klipp.py per tagning.

Kör:  scen/.venv/Scripts/python.exe scen/3d/ingest/flera/ingest_flera.py <klipp.mp4> <utmapp> [--max-person-rutor 1500] [--total 5000] [--bara S1,S3] [--endast-dela]
      (PYTHONIOENCODING=utf-8, från repots rot)

1. Klippdetektering: klippgrans.py (HSV-skillnad + grannskapskvot, se dess docstring). Kantrester (< 12 rutor först/sist i klippet,
   i praktiken övertoning från/till svart) slås ihop med grannen. Inre tagningar < 12 rutor behålls som egna tagningar och märks 'kort'.
2. Delar upp till <utmapp>/klipp/S<n>.mp4 (bildruteexakt omkodning, H.264 + AAC, bildfrekvensen bevaras) och skriver tagningar.json.
3. Per tagning, i ordning och återupptagbart (hoppar över tagningar med jamforelse.mp4):
   a. personer-steget körs här (in-process, samma kod som ingest_klipp) för att veta hur många personer som spåras;
   b. VAKT på det betalda steget: personrutor = antal (person, ruta)-jobb i personer.json (<= rutor x personer). Överstiger det
      --max-person-rutor (1500), eller skulle den löpande totalsumman över alla klipp (budget.json) passera --total (5000), stoppas
      tagningen före kropp och orsaken skrivs i status.json. Tagningar < 12 rutor körs bara om de kostar <= 24 personrutor.
   c. ingest_klipp.py <S<n>.mp4> <utmapp>/S<n> körs som underprocess; logg i <utmapp>/loggar/S<n>.log.
4. status.json: exit-kod, väggtid, tid per steg (tider.json), personer, kamera (registrerade/av), statisk/rörlig, golvkälla,
   ben synliga/skymda, rum (väggar/objekt), antal kroppsjobb.
Budget: flera/budget.json (löpande, delas av alla körningar av detta skript).
"""
import sys, os, json, time, subprocess, argparse
from pathlib import Path
HIT = Path(__file__).resolve().parent; ING = HIT.parent; SCEN = ING.parent.parent
sys.path.insert(0, str(HIT)); sys.path.insert(0, str(ING))
PY = SCEN / '.venv/Scripts/python.exe'
KORT = 12
from sakra_filer import sakerhetskopiera
from semantik_input import hitta, Semantik
from regler import kamerabeslut


def fps_rat(klipp):
    """Verklig bildfrekvens (n, d). Den angivna r_frame_rate gäller när den stämmer med medelfrekvensen (avg_frame_rate,
    rutor/längd) inom 1 %; annars gäller avg_frame_rate. Rättat 20 nov 2026: en källa med r_frame_rate 60/1 men 467 rutor
    på 15,6 s (avg 5604/187) delades till 60 fps, och varje ruta dubblerades. Före-version: ingest_flera.py.fore_fps.bak."""
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate,avg_frame_rate', '-of', 'json', str(klipp)], capture_output=True, text=True).stdout
    s = json.loads(r)['streams'][0]
    def rat(t):
        a, b = (t or '0/0').split('/'); return int(a), int(b)
    rn, rd = rat(s.get('r_frame_rate')); an, ad = rat(s.get('avg_frame_rate'))
    if rd and an and ad and abs(rn / rd - an / ad) > 0.01 * (an / ad):
        print(f"fps: angiven {rn}/{rd} skiljer från verklig medelfrekvens {an}/{ad}; använder {an}/{ad}", flush=True)
        return an, ad
    return rn, rd


def planera(klipp):
    import klippgrans
    N, g, bort, sc = klippgrans.hitta(klipp)
    starts = [0] + [d['ruta'] for d in g]; poang = [None] + [d['poang'] for d in g]; kvot = [None] + [d['kvot'] for d in g]
    seg = [dict(start=s, slut=(starts[i + 1] if i + 1 < len(starts) else N) - 1, gransscore=poang[i], kvot=kvot[i]) for i, s in enumerate(starts)]
    anm = []
    while len(seg) > 1 and seg[-1]['slut'] - seg[-1]['start'] + 1 < KORT:
        r = seg.pop(); seg[-1]['slut'] = r['slut']; anm.append(f"kantrest sist (ruta {r['start']}-{r['slut']}, {r['slut']-r['start']+1} rutor) hopslagen med föregående")
    while len(seg) > 1 and seg[0]['slut'] - seg[0]['start'] + 1 < KORT:
        r = seg.pop(0); seg[0]['start'] = r['start']; seg[0]['gransscore'] = None; anm.append(f"kantrest först (ruta {r['start']}-{r['slut']}) hopslagen med nästa")
    for i, s in enumerate(seg, 1):
        s['id'] = f'S{i}'; s['rutor'] = s['slut'] - s['start'] + 1; s['kort'] = s['rutor'] < KORT
    return dict(N=N, troskel=klippgrans.TROSKEL, kvot=klippgrans.KVOT, tagningar=seg, anmarkningar=anm, forkastade_kandidater=bort)


def dela(klipp, ut, plan):
    (ut / 'klipp').mkdir(parents=True, exist_ok=True); n, d = fps_rat(klipp); fps = n / d
    import cv2
    for s in plan['tagningar']:
        o = ut / 'klipp' / f"{s['id']}.mp4"
        if o.exists() and int(cv2.VideoCapture(str(o)).get(7)) == s['rutor']: continue
        a, b = s['start'], s['slut'] + 1
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(klipp), '-vf', f'trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS',
                        '-af', f'atrim=start={a*d/n:.6f}:end={b*d/n:.6f},asetpts=PTS-STARTPTS', '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', f'{n}/{d}',
                        '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', str(o)], check=True)
        got = int(cv2.VideoCapture(str(o)).get(7))
        if got != s['rutor']: print(f"VARNING {s['id']}: {got} rutor, väntade {s['rutor']}", flush=True); s['rutor_efter_delning'] = got
    return fps


def budget_las():
    p = HIT / 'budget.json'; return json.loads(p.read_text()) if p.exists() else dict(total=0, tagningar={})


def budget_skriv(b):
    sakerhetskopiera(HIT / 'budget.json')
    (HIT / 'budget.json').write_text(json.dumps(b, indent=1, ensure_ascii=False), encoding='utf-8')


def forsteg_personer(klipp, ut):
    import ingest_klipp as IK
    ut.mkdir(parents=True, exist_ok=True)
    if (ut / 'meta.json').exists() and (ut / 'personer.json').exists(): M = json.loads((ut / 'meta.json').read_text())
    else:
        sakerhetskopiera(ut)
        M = IK.meta(klipp, ut)
    if not (ut / 'personer.json').exists():
        t = time.time(); IK.rensa_efter(ut, 'personer'); r = IK.steg_personer(klipp, ut, M, 2); IK.logg(ut, 'personer', time.time() - t, **r)
    P = json.loads((ut / 'personer.json').read_text()); return M, P


def sammanfatta(ut, rc=None, vagg=None, extra=None):
    j = lambda n: json.loads((ut / n).read_text()) if (ut / n).exists() else None
    t = j('tider.json') or {}; P = j('personer.json') or {}
    s = dict(exit=rc, vagg_s=vagg, tider_s={k: v.get('sek') for k, v in t.items() if isinstance(v, dict)}, personer=len(P), person_ruta={k: len(v) for k, v in P.items()})
    k = t.get('kamera')
    if k: s.update(kamera_registrerade=k.get('registrerade'), kamera_av=k.get('av'), kamera_statisk=k.get('statisk'), kamera_fel_px=k.get('fel_px'))
    g = t.get('golv')
    if g: s['golv_kalla'] = g.get('kalla'); s['golv_kamerahojd'] = g.get('kamerahojd_over_golv')
    q = t.get('sekvens')
    if q: s['ben'] = {pid: dict(synliga=v.get('ben_synliga_rutor'), skymda=v.get('ben_skymda_rutor'), otillforlitliga=v.get('otillforlitliga'), rutor=v.get('rutor')) for pid, v in q.items() if isinstance(v, dict)}
    r = t.get('rum')
    if r: s['rum'] = dict(vaggar=r.get('walls'), objekt=r.get('objects'))
    kr = t.get('kropp')
    if kr: s['kropp_jobb'] = kr.get('jobb'); s['kropp_s'] = kr.get('sek'); s['kropp_s_per_jobb'] = kr.get('sek_per_jobb_median')
    s['jamforelse'] = (ut / 'jamforelse.mp4').exists()
    if extra: s.update(extra)
    return s


def main():
    a = argparse.ArgumentParser(); a.add_argument('klipp'); a.add_argument('ut'); a.add_argument('--max-person-rutor', type=int, default=1500)
    a.add_argument('--total', type=int, default=5000); a.add_argument('--bara', default=None); a.add_argument('--endast-dela', action='store_true')
    a.add_argument('--semantiskt', action='store_true', help='Billiga steg för alla tagningar, semantikpaus, sedan bara berättelsepersoner.')
    a.add_argument('--semantik'); a.add_argument('--granska-budget', action='store_true')
    a.add_argument('--regler', action='store_true', help='Pröva befintlig brännvidd och personmängd, kör ogiltiga kroppar igen.')
    a.add_argument('--till', default='rum', choices=['rum', 'jamfor'])
    a.add_argument('--uppdrag', default='regler-2026-11-10'); a.add_argument('--uppdragstak', type=int, default=1500)
    x = a.parse_args()
    klipp, ut = Path(x.klipp).resolve(), Path(x.ut).resolve(); ut.mkdir(parents=True, exist_ok=True); (ut / 'loggar').mkdir(exist_ok=True)
    pj = ut / 'tagningar.json'
    if pj.exists(): plan = json.loads(pj.read_text())
    else:
        plan = planera(klipp); plan.update(klipp=str(klipp)); plan['fps'] = dela(klipp, ut, plan); pj.write_text(json.dumps(plan, indent=1, ensure_ascii=False))
    print(f"{klipp.name}: {plan['N']} rutor, {len(plan['tagningar'])} tagningar", [(s['id'], s['start'], s['slut']) for s in plan['tagningar']], plan['anmarkningar'], flush=True)
    if x.endast_dela: return
    sakerhetskopiera(ut / 'status.json')
    sem = None
    if x.semantiskt or x.regler or x.semantik:
        # Alla kontaktblad måste kunna byggas innan någon betald kropp startas.
        for s in plan['tagningar']:
            forsteg_personer(ut / 'klipp' / f'{s["id"]}.mp4', ut / s['id'])
        sf = hitta(ut, x.semantik)
        if sf is None and (ut / 'semantik/semantik.json').exists(): sf = ut / 'semantik/semantik.json'
        if not sf or not sf.exists():
            config = ut / 'semantik_klipp.json'
            if not config.exists(): config.write_text(json.dumps(dict(ingest=str(ut), video=str(klipp), ut=str(ut / 'semantik')), ensure_ascii=False), encoding='utf-8')
            print('STOPP före betald kropp. Kör följande uttryckliga semantikanrop och lokala ordtider, granska sedan och kör detta kommando igen:', flush=True)
            print(f'{PY} scen/3d/kontrakt/semantik/semantik_ingest.py {config}', flush=True)
            print(f'{PY} scen/3d/kontrakt/semantik/ordtider_klipp.py {config}', flush=True)
            return
        sem = Semantik(sf)
    sp = ut / 'status.json'; st = json.loads(sp.read_text()) if sp.exists() else {}
    val = set(x.bara.split(',')) if x.bara else None; B = budget_las()
    skriv = lambda: sp.write_text(json.dumps(st, indent=1, ensure_ascii=False))
    for s in plan['tagningar']:
        sid = s['id']
        if val and sid not in val: continue
        u = ut / sid; k = ut / 'klipp' / f'{sid}.mp4'
        if not sem and (u / 'jamforelse.mp4').exists() and (u / 'tider.json').exists():
            st[sid] = sammanfatta(u, extra=dict(status='klar', start=s['start'], slut=s['slut'], rutor=s['rutor'])); print(f'{sid}: klar sedan förut', flush=True); continue
        T = time.time(); extra = dict(start=s['start'], slut=s['slut'], rutor=s['rutor'], kort=s['kort'])
        try:
            M, P = forsteg_personer(k, u)
        except BaseException as e:
            st[sid] = dict(status='fel_personer', orsak=repr(e)[-300:], **extra); skriv(); print(sid, 'personer misslyckades', e, flush=True); continue
        om = None
        if sem:
            original = u / 'personer_matning.json'
            if original.exists(): P = json.loads(original.read_text())
            fp, rm, beslut = sem.filtrera(sid, P)
            K = json.loads((u / 'kamera.json').read_text()) if (u / 'kamera.json').exists() else {}
            kb = kamerabeslut(K, M)
            import numpy as np
            focals = [float(np.load(f)['fokal']) for f in u.glob('sekvens_*.npz') if f.stem[8:] in fp]
            fore = json.loads((u / 'personer.json').read_text())
            invalid = fore != fp or any(abs(f-kb['fokal_px']) > .01 for f in focals) or any(not (u / f'sekvens_{p}.npz').exists() for p in fp)
            om = 'kropp' if invalid else ('sekvens' if x.regler and fp else 'varld' if x.regler else None)
            P = fp
            print(sid, 'kropp måste köras om' if invalid else 'kropp återanvänds', 'personrutor', sum(map(len, P.values())), 'kamera', kb, flush=True)
            if not x.granska_budget:
                sakerhetskopiera(u)
                if not original.exists(): original.write_text(json.dumps(fore), encoding='utf-8')
                (u / 'personer.json').write_text(json.dumps(fp), encoding='utf-8')
                (u / 'semantik_beslut.json').write_text(json.dumps(dict(fil=str(sem.fil), roller=rm, beslut=beslut), ensure_ascii=False), encoding='utf-8')
                K['beslut'] = kb; K['statisk'] = K.get('statisk', True) or kb['kalla'] != 'COLMAP'
                (u / 'kamera.json').write_text(json.dumps(K), encoding='utf-8')
        jobb = sum(len(v) for v in P.values()); est = M['N'] * len(P); extra.update(personer_spårade=len(P), personrutor_jobb=jobb, personrutor_uppskattning=est)
        if x.granska_budget: continue
        spent = (u / 'kropp/timing.json').exists() and om != 'kropp'; stopp = None
        if not spent:
            if est > x.max_person_rutor or jobb > x.max_person_rutor: stopp = f'vakt: uppskattning {est} (jobb {jobb}) > {x.max_person_rutor} personrutor'
            elif sum(v['personrutor'] for v in B.get('korningar', []) if v['uppdrag'] == x.uppdrag) + jobb > x.uppdragstak: stopp = f'vakt: uppdragstaket {x.uppdragstak} personrutor skulle passeras'
            elif B['total'] + jobb > x.total: stopp = f"vakt: totalbudget {x.total} skulle passeras ({B['total']} + {jobb})"
            elif s['kort'] and jobb > 24: stopp = f'kort tagning ({s["rutor"]} rutor) med {jobb} personrutor > 24'
            if stopp:
                st[sid] = sammanfatta(u, extra=dict(status='stoppad_av_vakt', orsak=stopp, **extra)); skriv(); print(sid, stopp, flush=True); continue
            B['tagningar'][f'{ut.name}/{sid}'] = B['tagningar'].get(f'{ut.name}/{sid}', 0) + jobb
            B.setdefault('korningar', []).append(dict(uppdrag=x.uppdrag, tagning=f'{ut.name}/{sid}', personrutor=jobb, status='reserverad före anrop'))
            B['total'] += jobb; budget_skriv(B)
        with open(ut / 'loggar' / f'{sid}.log', 'a', encoding='utf-8') as lg:
            lg.write(f'\n==== {time.ctime()} ====\n'); lg.flush()
            r = subprocess.run([str(PY), str(ING / 'ingest_klipp.py'), str(k), str(u), '--till', x.till] + (['--om', om] if om else []), stdout=lg, stderr=subprocess.STDOUT, env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUNBUFFERED': '1'})
        fel = None
        if r.returncode:
            tail = (ut / 'loggar' / f'{sid}.log').read_text(encoding='utf-8', errors='replace')[-600:].strip().splitlines()
            fel = tail[-1][:300] if tail else '?'
        st[sid] = sammanfatta(u, r.returncode, round(time.time() - T, 1), dict(status='klar' if not r.returncode and (x.till == 'rum' or (u / 'jamforelse.mp4').exists()) else 'fel', orsak=fel, **extra))
        skriv(); print(sid, st[sid]['status'], fel or '', flush=True)
    if not x.granska_budget: skriv()


if __name__ == '__main__':
    main()
