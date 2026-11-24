"""Flerklippsfallet för kalla_bygg.py: ett klipp som består av flera ingest-mappar (en per tagning).

Anropas från kalla_bygg.py när den givna mappen saknar meta.json men har undermappar S1, S2, ...
Allt lokalt, inget nätanrop. Det som saknar källa blir null och listas under matning.kvalitet.
"""
import os
import subprocess
from fractions import Fraction
from pathlib import Path
import numpy as np
from gemensamt import HIT, ladda, kontrollmodul

ROT = HIT.parents[2]

# Hand-kalibrerade scen3d.json använder engelska beat-namn; harnessens ordförråd (kalla.schema.json, scen.funktion) är svenskt.
# Beatet "reaction" har ingen motsvarighet och lämnas null. "payoff" -> avslut är närmast (sista tagningen, klippet slutar där).
BEAT_TILL_FUNKTION = {'hook': 'krok', 'build-up': 'uppbyggnad', 'turn': 'vandning', 'punchline': 'punchline',
                      'payoff': 'avslut', 'reaction': None}


def tagningar(mapp):
    ds = [p for p in Path(mapp).iterdir() if p.is_dir() and (p / 'meta.json').exists() and p.name[:1] == 'S' and p.name[1:].isdigit()]
    return sorted(ds, key=lambda p: int(p.name[1:]))


def bygg_flera(mapp, mal, video, scen3d, ordtider, sha, platsfil=None):
    mapp, mal = Path(mapp).resolve(), Path(mal).resolve()
    # plats.json (ingest/plats.py) används om den finns i <mapp>/plats/ eller anges; annars byggs kalla utan plats som förr.
    platsfil = Path(platsfil).resolve() if platsfil else (mapp / 'plats/plats.json' if (mapp / 'plats/plats.json').exists() else None)
    ds = tagningar(mapp)
    if not ds: raise ValueError('Inga tagningsmappar S1, S2, ... med meta.json hittades.')
    video = Path(video).resolve(); digest = sha(video)
    S3 = ladda(scen3d); OT = ladda(ordtider)
    ordlista = ladda(HIT / 'ordlista.json'); kvalitet = []
    rel = lambda p: Path(os.path.relpath(p, mal.parent)).as_posix()
    rotref = lambda p: Path(os.path.relpath(p, ROT)).as_posix()

    def post(namn, status, metod, fil=None, osakerhet=None, steg=None):
        kvalitet.append(dict(post=namn, status=status, metod=metod, osakerhet=osakerhet,
                             saknas_steg=steg, kalla_fil=rotref(fil) if fil else None))

    def saknas(namn, steg): post(namn, 'saknas', 'Ingen tillgänglig källa för uppgiften.', steg=steg)

    def pek(p, roll):
        p = Path(p)
        if not p.exists(): saknas(roll, 'Kör motsvarande ingest-steg.'); return None
        x = dict(sokvag=rel(p), sha256=sha(p), format=p.suffix[1:], roll=roll)
        if p.suffix in ('.npz', '.npy'):
            arr = np.load(p, allow_pickle=False)
            data = {n: arr[n] for n in arr.files} if p.suffix == '.npz' else {'arr': arr}
            x['nycklar'] = [dict(namn=n, form=list(a.shape), dtype=str(a.dtype),
                                  **ordlista['arrayer'].get(n, dict(enhet=None, beskrivning='Array från ingest.')))
                            for n, a in data.items()]
            if p.suffix == '.npz': arr.close()
        return x

    # --- tidsbas: tagningarnas bildantal ligger intill varandra
    metas = [ladda(d / 'meta.json') for d in ds]
    fpsv = {m['fps'] for m in metas}; matt = {(m['bredd'], m['hojd']) for m in metas}
    if len(fpsv) != 1 or len(matt) != 1: raise ValueError('Tagningarna har olika fps eller bildmått.')
    fps = Fraction(str(metas[0]['fps'])).limit_denominator(100000); bredd, hojd = matt.pop()
    N = sum(m['N'] for m in metas); langd = round(N / float(fps), 4)
    starts = np.concatenate([[0], np.cumsum([m['N'] for m in metas])]).tolist()
    s3sh = {s['id']: s for s in S3['shots']}
    for d, a, m in zip(ds, starts, metas):
        sh = s3sh.get(d.name)
        if sh and abs(sh['source']['inSec'] * float(fps) - a) > 1.0:
            raise ValueError(f'{d.name}: ingest börjar på ruta {a} men scen3d.json säger {sh["source"]["inSec"] * float(fps):.1f}.')
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(video)], capture_output=True, check=True)
    import json as _j
    strommar = _j.loads(probe.stdout)['streams']
    vstr = next(s for s in strommar if s['codec_type'] == 'video')
    if int(vstr['nb_frames']) != N: raise ValueError(f'Källvideon har {vstr["nb_frames"]} rutor, tagningarna summerar till {N}.')
    ljud = any(s['codec_type'] == 'audio' for s in strommar)
    ident = video.stem.removeprefix('kand-')
    k = dict(schema_version='kalla/1', revision=(3 if ladda(platsfil).get('rumsmall') else 2) if platsfil else 1,
             klipp=dict(id=ident, konto=None, sha256=digest,
                        video=dict(sokvag=rel(video), format=video.suffix[1:], bredd=bredd, hojd=hojd, ljud=ljud),
                        beskrivning=None, beskrivning_kalla=None),
             tidsbas=dict(fps_taljare=fps.numerator, fps_namnare=fps.denominator, antal_rutor=N, langd_s=langd,
                          regel='Tid i sekunder på källklockan: tid_s = ruta / fps. Ruta 0 = 0,0 s. Intervall är halvöppna [start, slut).'))
    post('klipp.video', 'uppmatt', 'Angiven källvideo, SHA-256 läst ur filen; bildantal i videon = summan av tagningarnas N.', video)
    post('tidsbas', 'uppmatt', f'Tagningarnas bildantal ur meta.json summerar till {N} rutor (källvideon: {vstr["nb_frames"]}).', ds[0] / 'meta.json')

    # --- personer: ingest-id är per tagning; roller ur scen3d.json (handkalibrerad, inte mätt)
    roller = {a['id']: a for a in S3['actors']}
    personer, matpers, scener, props, rum, masker = {}, [], [], [], [], []
    mappning = []
    sekv_info = {}
    for i, (d, a, m) in enumerate(zip(ds, starts, metas)):
        sid = f's{i + 1}'; b = a + m['N']; sh = s3sh.get(d.name)
        ids = sorted(p.stem[8:] for p in d.glob('sekvens_*.npz'))
        antal = {}
        for pid in ids:
            s = np.load(d / f'sekvens_{pid}.npz'); antal[pid] = int(s['inom'].sum()); s.close()
        aktorer = [x['id'] for x in sh['actors']] if sh else []
        # En roll per ingest-person. Fler personer än roller: den med flest rutor i bild får rollen, övriga får ingen roll.
        rang = sorted(ids, key=lambda p: (-antal[p], p))
        tilldelat = dict(zip(rang, aktorer))
        for pid in ids:
            klipp_id = tilldelat.get(pid) or f'okand_{sid}_{pid}'
            tilldelat[pid] = klipp_id
            mappning.append(dict(scen=sid, ingest_id=pid, person=klipp_id, rutor_i_bild=antal[pid], harledd=len(ids) > len(aktorer)))
            if klipp_id not in personer:
                akt = roller.get(klipp_id)
                personer[klipp_id] = dict(id=klipp_id, roll=akt['role'] if akt else None,
                                          beskrivning=None, roll_kalla='scen3d' if akt else None)
        # kamera
        V = np.load(d / 'varld.npz'); tid = ladda(d / 'tider.json').get('kamera', {})
        colmap = d / 'kamera.json'; cam = ladda(colmap) if colmap.exists() else {}
        kam = dict(id=f'kam_{sid}', spar_colmap=pek(colmap, f'COLMAP-bana {sid}.') if colmap.exists() else None,
                   spar_metrisk=pek(d / 'varld.npz', f'Kamerabana i metrisk värld {sid}.'),
                   fokal_px=cam.get('fokal_px', tid.get('fokal_px')), statisk=tid.get('statisk'),
                   registrerade_rutor=tid.get('registrerade'), utvalda_rutor=tid.get('av'),
                   reprojektionsfel_px=tid.get('fel_px'), metrisk_skala_k=float(V['k']), kalla_ruta0=a)
        V.close()
        k.setdefault('_kameror', []).append(kam)
        for pid in ids:
            s = np.load(d / f'sekvens_{pid}.npz'); inom = np.flatnonzero(s['inom'])
            pal = ladda(d / f'palitlig_{pid}.json') if (d / f'palitlig_{pid}.json').exists() else None
            matpers.append(dict(person=tilldelat[pid], rorelse=pek(d / f'sekvens_{pid}.npz', f'Kroppsrörelse i MHR-form per ruta, {sid}.'),
                                synlighet=pek(d / f'synlighet_{pid}.json', 'Synlig underkropp.'),
                                palitlighet=pek(d / f'palitlig_{pid}.json', 'Pålitlig kroppsanpassning.'),
                                kontakt=pek(d / f'kontakt_{pid}.json', 'Fotkontakt efter IK.'),
                                rutor_inom=[int(inom[0]), int(inom[-1]) + 1] if len(inom) else [0, 0],
                                rutor_kanda=int(s['kand'].sum()),
                                rutor_otillforlitliga=sum(not v for v in pal.values()) if pal is not None else None,
                                rutor_ben_synliga=int(s['ben_synliga'].sum()), scen=sid, ingest_id=pid))
            s.close()
        # rum
        rj = ladda(d / 'rum.json')
        rid = f'rum_{sid}'
        rum.append((rid, rj, d))
        for o in rj['objects']:
            props.append(dict(id=f'{sid}_{o["id"]}', typ=o['label'].replace(' ', '_'), etikett=o['label'], agare=None, stod=None,
                              faste=None, rum_ref=o['id'], kalla='rum.json', scen=sid))
        for pm in (pek(d / 'masker.npy', f'Union av personmasker, {sid}.'), pek(d / 'personer.json', f'Personrutor, {sid}.')):
            if pm: masker.append(pm)
        beat = sh['beat'] if sh else None
        funk = BEAT_TILL_FUNKTION.get(beat)
        scener.append(dict(id=sid, start_s=round(a / float(fps), 4), slut_s=round(b / float(fps), 4), funktion=funk, bar=None, syfte=None,
                           miljo=rid, personer=[tilldelat[p] for p in ids], kamera=f'kam_{sid}', segmentering='antagen'))
        sekv_info[sid] = dict(beat=beat, funktion=funk)
    kameror = k.pop('_kameror')
    plats_sem = plats_mat = None
    if platsfil:
        from kalla_plats import plats_delar
        plats_sem, plats_mat, per_scen, props = plats_delar(platsfil, [(s['id'], s['kamera'], ds[i].name) for i, s in enumerate(scener)], pek,
                                                            {s['id']: s['personer'] for s in scener})
        for s in scener: s['plats_id'], s['bindningar'] = per_scen[s['id']]

    # --- repliker: ordtider.json (Whispers tider, manusets ord)
    s_av = lambda t: next((s for s in scener if s['start_s'] - 1e-6 <= t < s['slut_s'] - 1e-6), scener[-1])
    repliker = []
    for l in OT['lines']:
        ov = {s['id']: max(0.0, min(l['end'], s['slut_s']) - max(l['start'], s['start_s'])) for s in scener}
        sid = max(sorted(ov), key=lambda x: ov[x])
        sc = next(s for s in scener if s['id'] == sid)
        repliker.append(dict(id=f'r{l["i"] + 1}', talare=l['speaker'], sprak=OT.get('language', 'sv'), text=l['text'],
                             start_s=l['start'], slut_s=l['end'], i_bild=l['speaker'] in sc['personer'], scen=sid,
                             ord=[dict(ord=w['w'], start_s=w['start'], slut_s=w['end'], sannolikhet=w.get('p')) for w in l['words']],
                             kalla='whisper'))
    post('semantik.repliker', 'uppmatt', f'{len(repliker)} repliker med ordtider ur {OT["model"]} (språk {OT["language"]}); orden är manusets, tiderna Whispers (match_ratio {OT["match_ratio"]}). scen = scenen med störst överlapp; i_bild = talaren är i den scenens personlista.',
         Path(ordtider), 'Ordtider kan avvika några hundradelar; i_bild är ett enkelt mått på personlistan och säger inte om munnen syns.')
    post('semantik.repliker.talare', 'antagen', 'Talare A/B ur ordtider.json; rollerna kommer från den handkalibrerade scen3d.json.', Path(ordtider))

    # --- semantik
    rumsem = [dict(id=rid, typ='okand', beskrivning=f'Rum {rid[4:]} ur rum.json; ingen rumstypsbedömning finns.',
                   vaggar=[w['id'] for w in rj['walls']], fasta=[]) for rid, rj, _ in rum]
    sem = dict(scener=scener, beats=[], repliker=repliker, personer=list(personer.values()), props=props, rum=rumsem, skarmtext=[],
               ljud=dict(tal='dialog', musik=None, trendljud=None, kalla=rotref(Path(ordtider))),
               intention=dict(karna=None, krok=dict(finns=None, vad=None, scen=None), vandning=dict(finns=None, vad=None, scen=None),
                              payoff=dict(finns=None, vad=None, scen=None), kalla='saknas'), serie=None)
    for post_namn, steg in [('semantik.beats', 'Harnessens v5-kort: bar (karna/stod/fri) per beat saknas, så inga beats skrivs.'),
                            ('semantik.skarmtext', 'OCR med tider. Källan har inbrända undertexter men de är inte lästa.'),
                            ('semantik.serie', 'CM anger serieposition.'), ('semantik.intention', 'Sållning/e4/v5 saknas för detta klipp.'),
                            ('semantik.scener.bar_syfte', 'Harnessens scenplan.'), ('klipp.beskrivning', 'Beskriv klippet.'),
                            ('semantik.ljud.musik_trendljud', 'Klassificera ljudet; ingen e4-körning finns.'),
                            ('semantik.props.stod_faste', 'Mät stöd och grepp.'), ('matning.ljud', 'Extrahera separat ljudfil med hash.')]:
        saknas(post_namn, steg)
    for s in scener:
        if s['funktion'] is None:
            saknas(f'semantik.scener.{s["id"]}.funktion', f'Beatet "{sekv_info[s["id"]]["beat"]}" har ingen motsvarighet i harnessens ordförråd (krok, uppbyggnad, vandning, punchline, visning, tilltal, avslut).')
    post('semantik.scener.funktion', 'antagen',
         'Beat ur den handkalibrerade scen3d.json (shots[].beat) översatt till harnessens ordförråd: ' +
         ', '.join(f'{e} -> {sv}' for e, sv in BEAT_TILL_FUNKTION.items() if sv) + '; reaction -> null (ingen motsvarighet). payoff -> avslut är närmast, inte säkert.',
         Path(scen3d), 'Beatnamnen är handsatta och mappningen är mitt val, inte harnessens.')
    post('semantik.scener.segmentering', 'antagen',
         f'Scenerna är tagningarna S1–S{len(ds)}; gränserna är summan av ingest-mapparnas bildantal och stämmer med scen3d.json source.inSec/outSec (±1 ruta). Hur de ursprungligen hittades dokumenteras inte i ingest.',
         Path(scen3d), 'Ingen lokal klippdetektering (data/analys) finns för detta klipp.')
    post('semantik.personer.roll', 'antagen',
         'Klippnivåns roller A/B/C och vilken person i bild som är vilken per tagning kommer från scen3d.json (shots[].actors, actors[].role). Ingest-id är per tagning ("1" i nästan alla mappar) och binds till roll i ordning efter flest rutor i bild. Inte mätt; ingen igenkänning av personer över klipp har gjorts.',
         Path(scen3d), 'Tagning S4 har två ingest-personer men bara en roll (C) i scen3d.json. Personen med flest rutor i bild (id 1, alla 85) har fått C; den andra (id 4, kantbild, 55 rutor) har ingen roll (id okand_s4_4). Valet är kontrollerat mot bilden, inte mot scen3d.json.')
    post('semantik.rum', 'antagen', ('Varje tagning har ett eget rum.json; de är observationer av platsen och slås ihop i plats.json.' if platsfil else 'Varje tagning har ett eget rum.json i eget världskoordinatsystem. Ingen registrering mellan tagningar finns: rummen är inte samma koordinatsystem och inte kopplade till varandra.'), None,
         'Samma fysiska lokal syns i flera tagningar men det är inte mätt; kontinuitet mellan scenerna finns inte i data.', 'Registrera tagningarna mot varandra (gemensamt rum).')
    for s_id, (rid, rj, d) in zip([s['id'] for s in scener], rum):
        post(f'semantik.rum.{rid}.golv', 'uppmatt' if rj['floor'].get('verified') else 'antagen', 'Golv från ingest, källa: ' + rj['floor']['source'] + '. Rumsmåtten är modellskattningar.', d / 'rum.json',
             'Metrisk skala och utsträckning är inte oberoende verifierade.')
    if platsfil:
        post('semantik.platser', 'antagen', 'En plats för alla tagningar (ingest/plats.py). Tagningar med samma kamerastation läggs ihop med bildmatchning (uppmätt); resten placeras med personens uppmätta bäcken och riktning mot ett ankare, där dialogaxel, stolsavstånd och motbildskamera är scengrammatik (antagen). Se plats_matt.json.', platsfil,
             'Registrering mellan olika kamerastationer är antagen, inte mätt: motbildernas bakgrunder delar inga särdrag. Brännvidd (1024 px) och golv (1,45 m under kameran) är antagna i de flesta tagningar.')
        post('semantik.platser.ankare', 'antagen', 'Ankare ur personernas uppmätta bäcken (median över rutor) och bordens sedda kant; läget i platsen följer registreringen.', platsfil, 'Se matning.platser[].ankare[].osakerhet_m.')
    post('matning.skala', 'antagen', 'varld.npz k = 1,0 i alla tagningar; skalan är antagen (kamerahöjd 1,45 m där golvet inte syns).', ds[0] / 'varld.npz', 'Rummens och personernas metriska skala är antagen i tagningar utan synliga fötter.')
    post('matning.kameror.bana', 'antagen', 'Alla tagningar har statisk kamera. S2 och S5 har en COLMAP-registrering (2 rutor); övriga saknar spår och har identitetskamera.', None,
         'Fokallängd saknas i tagningar utan COLMAP (null); mhr_rig använder kroppsmodellens fokal.')
    post('matning.personer.rorelse', 'uppmatt', 'Stabiliserade MHR-sekvenser per tagning; skymda leder är modellskattningar.', ds[0] / 'sekvens_1.npz')
    post('matning.personer.uttryck', 'uppmatt', 'expr finns men används inte av MHR-renderaren; munnen följer inte ny text.', ds[0] / 'sekvens_1.npz')
    post('matning.korlogg', 'saknas', 'Körloggen (tider.json) hashlåses inte: den skrivs om vid varje ingest-körning och skulle ogiltigförklara kalla.', None, None, None)
    post('klipp.person_mappning', 'antagen', 'Tabell ingest-id -> klippnivåns person per tagning: ' +
         '; '.join(f'{x["scen"]}:{x["ingest_id"]}->{x["person"]}' for x in mappning), Path(scen3d))

    if plats_sem: sem['platser'] = [plats_sem]
    k['semantik'] = sem
    koordinater = __import__('copy').deepcopy(ordlista['koordinater'])
    koordinater['varld'].update(skala_till_meter=None, upp=None,
                               golvplan='Per tagning: se varld.npz (upp, golv_h) i matning.kameror[].spar_metrisk. Varje tagning har ett eget världssystem.')
    k['matning'] = dict(koordinater=koordinater, kameror=kameror, personer=matpers,
                        rum=[dict(id=rid, fil=pek(d / 'rum.json', f'Rumsgeometri {rid}.')) for rid, _, d in rum],
                        masker=masker, korlogg=None, kvalitet=kvalitet)
    if plats_mat: k['matning']['platser'] = [plats_mat]
    mod = kontrollmodul(); schema = ladda(HIT / 'kalla.schema.json'); fel = mod.validera(k, schema, 'kalla', schema)
    if fel: raise ValueError('\n'.join(fel))
    return k
