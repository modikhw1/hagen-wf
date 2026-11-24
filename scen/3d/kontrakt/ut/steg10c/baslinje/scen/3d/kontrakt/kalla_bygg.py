"""Bygg en källbeskrivning utan nätanrop. Befintliga utdata skrivs aldrig över.

python kalla_bygg.py <ingestmapp> <ny kalla.json> [--video <källvideo>]
Flera tagningar (mapp med S1, S2, ...): --video, --scen3d och --ordtider (se kalla_flera.py).
Lokala analys-, sållnings-, e4- och v5-filer söks med videons klipp-id.
"""
import argparse
import copy
import hashlib
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
from gemensamt import HIT, ladda, skriv, kontrollmodul

ROT = HIT.parents[2]


def sha(p):
    with Path(p).open('rb') as f:
        h = hashlib.sha256()
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def skillnader(a, b, stig=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for k in sorted(a.keys() | b.keys()) for d in
                (skillnader(a[k], b[k], stig + '/' + k) if k in a and k in b else
                 [dict(falt=stig + '/' + k, fore=a.get(k), efter=b.get(k))])]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in skillnader(x, y, stig + '/' + str(i))]
    return [] if a == b else [dict(falt=stig, fore=a, efter=b)]


def bygg(ut, mal, video=None, platsfil=None):
    ut, mal = Path(ut).resolve(), Path(mal).resolve()
    meta = ladda(ut / 'meta.json'); kvalitet = []
    ordlista = ladda(HIT / 'ordlista.json')
    def rel(p): return Path(os.path.relpath(p, mal.parent)).as_posix()
    def rotref(p): return Path(os.path.relpath(p, ROT)).as_posix()
    def kvalitetspost(post, status, metod, fil=None, osakerhet=None, steg=None):
        kvalitet.append(dict(post=post, status=status, metod=metod, osakerhet=osakerhet,
                            saknas_steg=steg, kalla_fil=rotref(fil) if fil else None))
    def saknas(post, steg):
        kvalitetspost(post, 'saknas', 'Ingen tillgänglig källa för uppgiften.', steg=steg)
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
    antagen = not video and not meta.get('kallvideo')
    if not video: video = meta.get('kallvideo')
    if not video:
        # Äldre ingest saknar identitet. Kräv en unik dimensionsmatchning och märk antagandet.
        import cv2
        kandidater = []
        for p in sorted((ROT / 'scen/klipp').glob('*.mp4')):
            cap = cv2.VideoCapture(str(p))
            matt = (int(cap.get(3)), int(cap.get(4)), int(cap.get(7)), cap.get(5)); cap.release()
            if matt[:3] == (meta['bredd'], meta['hojd'], meta['N']) and abs(matt[3] - meta['fps']) < .001: kandidater.append(p)
        if len(kandidater) != 1: raise ValueError('Källvideon kan inte identifieras entydigt; ange --video.')
        video = kandidater[0]
    video = Path(video).resolve(); digest = sha(video)
    if meta.get('kallvideo_sha256') and meta['kallvideo_sha256'] != digest: raise ValueError('Källvideons hash avviker från meta.json.')
    ident = video.stem.removeprefix('kand-')
    def lokal(stig):
        p = ROT / stig / (ident + '.json')
        return (ladda(p) if p.exists() else {}), p
    analys, ap = lokal('data/analys'); sall, sp = lokal('data/bank/sallning')
    e4, ep = lokal('data/format/e4/lager-gemini-3.1-flash-lite'); v5, vp = lokal('data/format/harness/v5')
    fps = Fraction(str(meta['fps'])).limit_denominator(100000); langd = round(meta['N'] / float(fps), 4)
    ljud = analys.get('meta', {}).get('ljud')
    if ljud is None:
        try:
            probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(video)], capture_output=True, check=True)
            ljud = any(s['codec_type'] == 'audio' for s in __import__('json').loads(probe.stdout)['streams'])
        except (OSError, subprocess.CalledProcessError): saknas('klipp.video.ljud', 'Läs ljudspår med ffprobe.')
    k = dict(schema_version='kalla/1', revision=1,
             klipp=dict(id=ident, konto=sall.get('konto', analys.get('konto')), sha256=digest,
                        video=dict(sokvag=rel(video), format=video.suffix[1:], bredd=meta['bredd'], hojd=meta['hojd'], ljud=ljud),
                        beskrivning=sall.get('innehall'), beskrivning_kalla=rotref(sp) if sall else None),
             tidsbas=dict(fps_taljare=fps.numerator, fps_namnare=fps.denominator, antal_rutor=meta['N'], langd_s=langd,
                          regel='Tid i sekunder på källklockan: tid_s = ruta / fps. Ruta 0 = 0,0 s. Intervall är halvöppna [start, slut).'))
    kvalitetspost('klipp.video', 'antagen' if antagen else 'uppmatt',
                  'Unik matchning på bredd, höjd, bildantal och fps.' if antagen else 'Angiven källvideo, SHA-256 läst ur filen.', video,
                  'Mått bevisar inte ursprunget.' if antagen else None)
    kvalitetspost('tidsbas', 'uppmatt', 'Bildantal och fps ur meta.json.', ut / 'meta.json')
    personer = [dict(id=p.stem[8:], roll=None, beskrivning=None, roll_kalla=None) for p in sorted(ut.glob('sekvens_*.npz'))]
    rum = ladda(ut / 'rum.json') if (ut / 'rum.json').exists() else None
    cam = ladda(ut / 'kamera.json') if (ut / 'kamera.json').exists() else None
    scener = []
    for i, s in enumerate(analys.get('scener', [])):
        slut = langd if abs(s['slut'] - langd) < .001 else s['slut']
        scener.append(dict(id=f's{i+1}', start_s=s['start'], slut_s=slut, funktion=None, bar=None, syfte=None,
                           miljo='rum_1' if rum else None, personer=[p['id'] for p in personer],
                           kamera='kam_1' if cam else None, segmentering='klippdetektering'))
    if scener: kvalitetspost('semantik.scener.segmentering', 'uppmatt', 'Scengränser ur lokal klippdetektering; slutet snäpps till sista rutan inom 1 ms.', ap)
    else: saknas('semantik.scener', 'Klippdetektering eller tidsatt scenplan.')
    props = [dict(id=o['id'], typ=o['label'].replace(' ', '_'), etikett=o['label'], agare=None, stod=None,
                  faste=None, rum_ref=o['id'], kalla='rum.json') for o in (rum or {}).get('objects', []) if o['id'].startswith('prop_')]
    rumsem = [dict(id='rum_1', typ=e4.get('kontotyp', 'okand'), beskrivning='Rum från ingest; typ från e4 om tillgänglig.',
                   vaggar=[w['id'] for w in rum['walls']], fasta=[dict(id=o['id'], typ=o['label'].replace(' ', '_'))
                   for o in rum['objects'] if o['id'] not in {p['id'] for p in props}])] if rum else []
    moment = lambda namn: dict(finns=e4.get(namn), vad=None, scen=scener[0]['id'] if e4.get(namn) and len(scener) == 1 else None)
    sem = dict(scener=scener, beats=[], repliker=[], personer=personer, props=props, rum=rumsem, skarmtext=[],
               ljud=dict(tal=e4.get('tal'), musik=e4.get('musik'), trendljud=e4.get('trendljud'), kalla=rotref(ep) if e4 else None),
               intention=dict(karna=sall.get('innehall'), krok=moment('krok'), vandning=moment('vandning'), payoff=moment('payoff'),
                              kalla='modellbedomd' if e4 or sall else 'saknas'), serie=None)
    # Harness-beats saknar ofta tider och person-id: behåll null-bindning, gissa inte.
    for i, b in enumerate(v5.get('beats', [])):
        if all(n in b for n in ('funktion', 'bar', 'vad')):
            sem['beats'].append(dict(id=f'b{i+1}', nr=i+1, scen=None, funktion=b['funktion'], bar=b['bar'], vad=b['vad'], bunden=b.get('bunden')))
    for post, steg in [('scener.funktion_bar_syfte', 'Tidsätt och bind harnessens scenplan.'), ('personer.roll_beskrivning', 'Bind roller till ingest-personer.'),
                       ('skarmtext', 'OCR med tider.'), ('serie', 'CM anger serieposition.'), ('intention.payoff', 'Bedöm payoff.'),
                       ('props.stod_faste', 'Mät stöd och grepp.')]: saknas('semantik.' + post, steg)
    if not sem['beats']: saknas('semantik.beats', 'Harnessens v5-kort och scenplan.')
    else: kvalitetspost('semantik.beats', 'modellbedomd', 'Obundna beats ur lokalt v5-kort.', vp)
    if e4:
        kvalitetspost('semantik.ljud', 'modellbedomd', 'Ljudklassning ur lokalt e4-lager.', ep, 'Inte kontrollerad mot ljudet.')
        kvalitetspost('semantik.repliker', 'modellbedomd' if e4.get('tal') == 'inget' else 'saknas',
                      'e4 tal = ' + str(e4.get('tal')) + '; inget tidsatt transkript.', ep, steg='Transkribera om tal finns.')
    else: saknas('semantik.ljud', 'Klassificera ljud.'); saknas('semantik.repliker', 'Transkript med ordtider.')
    saknas('matning.ljud', 'Extrahera separat ljudfil med hash.')
    if not sall: saknas('klipp.beskrivning', 'Beskriv klippet.')
    if sall or e4: kvalitetspost('semantik.intention', 'modellbedomd', 'Kärna från sållning; krok och vändning från e4.', sp if sall else ep)
    V = np.load(ut / 'varld.npz') if (ut / 'varld.npz').exists() else None
    koordinater = copy.deepcopy(ordlista['koordinater'])
    koordinater['varld'].update(skala_till_meter=float(V['k']) if V is not None else None,
                               upp=V['upp'].tolist() if V is not None else None,
                               golvplan=f"X·upp = golv_h (golv_h = {float(V['golv_h']):.4f} m)" if V is not None and 'golv_h' in V else '')
    if V is None or 'golv_h' not in V: saknas('matning.koordinater.varld.golvplan', 'Kör värld- och golvsteget.')
    kameror = []
    if cam:
        kameror.append(dict(id='kam_1', spar_colmap=pek(ut/'kamera.json', 'COLMAP-bana.'), spar_metrisk=pek(ut/'varld.npz', 'Metrisk kamerabana.'),
                            fokal_px=cam.get('fokal_px'), statisk=cam.get('statisk'), registrerade_rutor=cam.get('registrerade'),
                            utvalda_rutor=cam.get('av'), reprojektionsfel_px=cam.get('fel_px'), metrisk_skala_k=float(V['k']) if V is not None else None))
    else: saknas('matning.kameror', 'Kör kamerasteget.')
    mp = []
    for p in personer:
        pid=p['id']; s=np.load(ut/f'sekvens_{pid}.npz'); inom=np.flatnonzero(s['inom'])
        pal= ladda(ut/f'palitlig_{pid}.json') if (ut/f'palitlig_{pid}.json').exists() else None
        mp.append(dict(person=pid, rorelse=pek(ut/f'sekvens_{pid}.npz', 'Kroppsrörelse i MHR-form per ruta.'),
                       synlighet=pek(ut/f'synlighet_{pid}.json', 'Synlig underkropp.'), palitlighet=pek(ut/f'palitlig_{pid}.json', 'Pålitlig kroppsanpassning.'),
                       kontakt=pek(ut/f'kontakt_{pid}.json', 'Fotkontakt efter IK.'), rutor_inom=[int(inom[0]), int(inom[-1])+1] if len(inom) else [0, 0],
                       rutor_kanda=int(s['kand'].sum()), rutor_otillforlitliga=sum(not v for v in pal.values()) if pal is not None else None,
                       rutor_ben_synliga=int(s['ben_synliga'].sum())))
        s.close()
    if rum:
        for post, status, metod in [('props', 'uppmatt', 'Objektlådor ur rum.json; stöd och fäste saknas.'),
                                    ('rum.golv', 'uppmatt' if rum['floor'].get('verified') else 'antagen', 'Golv från ingest, källa: ' + rum['floor']['source']),
                                    ('rum.vaggar', 'uppmatt', 'Anpassade väggplan ur rum.json.'), ('rum.fasta', 'uppmatt', 'Fasta objekt ur rum.json.')]:
            kvalitetspost('semantik.' + post, status, metod, ut/'rum.json', 'Metrisk skala och utsträckning är inte oberoende verifierade.')
    else: saknas('semantik.rum', 'Kör rumsteget.')
    for post, status, metod, fil in [('skala', 'antagen', 'Skala vald ur kropparnas rotbanor.', 'varld.npz'),
                                    ('kameror.bana', 'uppmatt', 'COLMAP och interpolerade mellanrutor.', 'kamera.json'),
                                    ('personer.rorelse', 'uppmatt', 'Stabiliserad MHR-sekvens; skymda leder är modellskattningar.', 'tider.json'),
                                    ('personer.uttryck', 'uppmatt', 'expr finns men används inte av MHR-renderaren.', 'tider.json')]:
        if (ut/fil).exists(): kvalitetspost('matning.'+post, status, metod, ut/fil)
        else: saknas('matning.'+post, 'Kör motsvarande ingest-steg.')
    plats_mat = None
    if platsfil:
        from kalla_plats import plats_delar
        psem, plats_mat, per_scen, pprops = plats_delar(platsfil, [(s['id'], s['kamera'], ut.name) for s in scener], pek, {s['id']: s['personer'] for s in scener})
        for s in scener: s['plats_id'], s['bindningar'] = per_scen[s['id']]
        for p in props:   # rum.json-rekvisitan finns kvar som semantik; den pekar nu på platsens objekt
            if p['rum_ref'] in {o['id'] for o in psem['objekt']}: p['plats_id'] = psem['id']
        sem['platser'] = [psem]
        kvalitetspost('semantik.platser', 'uppmatt', 'En tagning: platsen är tagningens egen Blender-värld, transformen är identitet (ingest/plats.py).', Path(platsfil), 'Golvhöjden är antagen om inga fötter syns.')
    k['semantik'] = sem
    k['matning'] = dict(koordinater=koordinater, kameror=kameror, personer=mp,
                        rum=[dict(id='rum_1', fil=pek(ut/'rum.json', 'Rumsgeometri.'))] if rum else [],
                        masker=[p for p in [pek(ut/'masker.npy', 'Union av personmasker.'), pek(ut/'personer.json', 'Personrutor.')] if p],
                        korlogg=pek(ut/'tider.json', 'Ingest-logg.'), kvalitet=kvalitet)
    if plats_mat: k['matning']['platser'] = [plats_mat]
    mod=kontrollmodul(); schema=ladda(HIT/'kalla.schema.json'); fel=mod.validera(k,schema,'kalla',schema)
    if fel: raise ValueError('\n'.join(fel))
    return k


def main():
    a=argparse.ArgumentParser(description=__doc__); a.add_argument('ingest'); a.add_argument('ut'); a.add_argument('--video')
    a.add_argument('--jamfor', default=str(HIT/'exempel/bar/kalla.json')); a.add_argument('--plats', help='plats.json från ingest/plats.py; utan den byggs kalla utan plats')
    a.add_argument('--scen3d'); a.add_argument('--ordtider'); a.add_argument('--semantik'); x=a.parse_args()
    if Path(x.ut).exists(): a.error('Utfilen finns redan; välj en ny sökväg.')
    from kalla_flera import tagningar, bygg_flera
    if not (Path(x.ingest)/'meta.json').exists() and tagningar(x.ingest):
        # Flerklippsfall: mappen innehåller S1, S2, ... (en ingest-mapp per tagning).
        if not x.video: a.error('Flerklippsfallet kräver --video (hela källklippet).')
        import sys
        sys.path.insert(0, str(HIT.parent / 'ingest'))
        from semantik_input import hitta
        semfil = hitta(x.ingest, x.semantik) if not x.scen3d else x.semantik
        if not semfil and not x.scen3d: a.error('Ange --scen3d och vid tal --ordtider, eller klippets egen --semantik.')
        k=bygg_flera(x.ingest, x.ut, x.video, x.scen3d, x.ordtider, sha, x.plats, semfil); skriv(x.ut, k)
        print(f'{len(k["semantik"]["scener"])} scener, {len(k["semantik"]["repliker"])} repliker, {len(k["matning"]["kvalitet"])} kvalitetsposter'); return
    k=bygg(x.ingest, x.ut, x.video, x.plats); skriv(x.ut, k)
    diff=skillnader(ladda(x.jamfor), k); rapport=Path(x.ut).with_suffix('.skillnader.json'); skriv(rapport, diff)
    print(f'{len(diff)} skillnader; samtliga före/efter-värden: {rapport}')
    for d in diff: print(d['falt'])


if __name__ == '__main__': main()
