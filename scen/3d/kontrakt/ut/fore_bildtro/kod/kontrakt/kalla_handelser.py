"""Komplettera kalla med lokala händelser; ingen modellservice eller ingest.

Spårgränser är detektioner, inte bevis för att någon går in/ut. Handmöten
är närhet i 2D, inte säker överlämning. Semantiska handlingar behåller den
sparade modellens ursprung och scenens hela tidsintervall.
"""
import argparse
import copy
import hashlib
import itertools
import json
import os
from pathlib import Path
import numpy as np


def ursprung(typ, metod, konfidens='lag', modell=None):
    return dict(typ=typ, metod=metod, konfidens=konfidens, modell=modell)


def spargranser(frames, n):
    """Endast första/sista observation, inga gissade försvinnanden i luckor."""
    frames = sorted({int(f) for f in frames if 0 <= int(f) < n})
    if not frames:
        return []
    return [('person_synlig', frames[0]), ('person_forsvinner', frames[-1] + 1)]


def handmoten(a, b, w, h, gransandel=.03, min_rutor=2):
    """Minst två intilliggande råa handledspar inom 3 % av bildhöjden."""
    hits = []
    for f in sorted(a.keys() & b.keys()):
        aa, bb = np.asarray(a[f]), np.asarray(b[f])
        ok_a = np.isfinite(aa).all(1) & (aa >= 0).all(1) & (aa < [w, h]).all(1)
        ok_b = np.isfinite(bb).all(1) & (bb >= 0).all(1) & (bb < [w, h]).all(1)
        if not ok_a.any() or not ok_b.any():
            continue
        distance = np.linalg.norm(aa[ok_a, None] - bb[None, ok_b], axis=2).min()
        if distance <= gransandel * h:
            hits.append(f)
    runs = []
    for f in hits:
        if runs and runs[-1][-1] == f - 1:
            runs[-1].append(f)
        else:
            runs.append([f])
    return [[r[0], r[-1] + 1] for r in runs if len(r) >= min_rutor]


def fyll(kalla, bas, semantik=None, semfil=None):
    k = copy.deepcopy(kalla)
    bas = Path(bas).resolve()
    fps = k['tidsbas']['fps_taljare'] / k['tidsbas']['fps_namnare']
    w, h = k['klipp']['video']['bredd'], k['klipp']['video']['hojd']
    events, dependencies = [], {}
    scenes = k['semantik']['scener']
    n_total = k['tidsbas']['antal_rutor']

    def beroende(path):
        path = Path(path).resolve()
        if path not in dependencies and path.is_file():
            dependencies[path] = dict(sokvag=os.path.relpath(path, bas).replace('\\', '/'),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), format=path.suffix[1:],
                roll='Underlag för lokala händelser; ändring kräver ny händelsemätning.')
        return dependencies.get(path, {}).get('sokvag', str(path))

    def event(eid, typ, vad, sid, start, slut, origin, vem=None, till=None, prop=None, bevis=None):
        events.append(dict(id=eid, typ=typ, vad=vad, vem=vem, till_vem=till, prop=prop,
                           scen=sid, start_s=round(start, 6), slut_s=round(slut, 6),
                           ursprung=origin, bevis=bevis or dict(filer=[], rutor=[], notering='')))

    for scene in scenes:
        sid = scene['id']
        a, b = round(scene['start_s'] * fps), round(scene['slut_s'] * fps)
        measurements = [m for m in k['matning']['personer'] if m.get('scen') in (None, sid)]
        camera = next(c for c in k['matning']['kameror'] if c['id'] == scene['kamera'])
        folder = (bas / camera['spar_metrisk']['sokvag']).resolve().parent
        trackfile = folder / 'personer_matning.json'
        if not trackfile.exists(): trackfile = folder / 'personer.json'
        tracks = json.loads(trackfile.read_text(encoding='utf-8')) if trackfile.exists() else {}
        trackref = beroende(trackfile) if tracks else None
        offset = camera.get('kalla_ruta0', 0)
        wrists = {}
        for m in measurements:
            pid = m['person']
            track = tracks.get(str(m.get('ingest_id', pid)), {})
            frames = [int(f) for f in track if a <= int(f) + offset < b]
            for typ, f in spargranser(frames, b - offset):
                t = (offset + f) / fps
                note = ('Spåret finns redan vid klippet/scenens start; inget uppmätt inträde.' if f + offset == a
                        else 'Spåret slutar vid klippgräns; ingen uppmätt utgång.' if f + offset == b
                        else 'Detektionsgräns; skymning eller spårfel kan ge samma gräns som inträde/utgång.')
                event(f'{sid}_{pid}_{typ}', typ,
                      'Första observerade personrutan' if typ == 'person_synlig' else 'Efter sista observerade personrutan',
                      sid, t, t, ursprung('uppmatt', 'Personspårets första/sista detektion i personer_matning.json eller äldre personer.json.'),
                      vem=pid, bevis=dict(filer=[trackref], rutor=[offset + f], notering=note))
            if len({x['person'] for x in measurements}) < 2:
                continue
            wrists.setdefault(pid, {})
            for path in sorted((folder / 'kropp' / str(m.get('ingest_id', pid))).glob('*.npz')):
                f = int(path.stem)
                if f not in frames:
                    continue
                with np.load(path) as raw:
                    pts = raw['pred_keypoints_2d'][[41, 62], :2].copy()
                beroende(path)
                wrists[pid][f] = pts
        for p1, p2 in itertools.combinations(sorted(wrists), 2):
            for i, (fa, fb) in enumerate(handmoten(wrists[p1], wrists[p2], w, h)):
                event(f'{sid}_handmote_{p1}_{p2}_{i+1}', 'handmote', 'Två personers skattade handleder möts i bilden',
                      sid, (offset + fa) / fps, (offset + fb) / fps,
                      ursprung('uppmatt', 'Råa handledspunkter, avstånd högst 3 % av bildhöjden under minst två intilliggande rutor; diagnostiska val.'),
                      vem=p1, till=p2, bevis=dict(filer=[trackref], rutor=[offset + fa, offset + fb],
                      notering='2D-närhet kan bero på perspektiv. Ingen propöverlämning är fastställd.'))

    for line in k['semantik']['repliker']:
        t = line['start_s']
        # Replikernas avrundade scenetikett kan ligga efter ordets faktiska start.
        scene = next((s for s in scenes if s['start_s'] <= t < s['slut_s']), None)
        if scene is None:
            continue
        measured = line.get('kalla') in ('whisper', 'ordtider')
        model = None if measured else (semantik or {}).get('ursprung', {}).get('modell')
        event('replik_' + line['id'] + '_start', 'replik_start', 'Repliken börjar: ' + line['text'], scene['id'], t, t,
              ursprung('uppmatt' if measured else 'modellbedomd',
                       'Sparad lokal tal-/ordtid; automatisk tidsuppskattning.' if measured else 'Sparad repliktid i semantiken; inte ommätt ljud.',
                       'medel' if measured else 'lag', model), vem=line['talare'])

    for prop in k['semantik']['props']:
        previous = None
        for record in sorted(prop.get('rekonstruktion', {}).get('scener', []),
                             key=lambda x: next(s['start_s'] for s in scenes if s['id'] == x['scen'])):
            refs = sorted(record['bildregioner'], key=lambda x: x['kallruta'])
            if refs:
                f = refs[0]['kallruta']
                event(record['scen'] + '_' + prop['id'] + '_synlig', 'prop_synlig', 'Första avlästa förekomst i scenen: ' + prop['etikett'],
                      record['scen'], f / fps, f / fps,
                      ursprung('uppmatt', 'Manuellt avläst källregion från propmätningen; inte uppmätt inträdestid.'),
                      prop=prop['id'], bevis=dict(filer=[], rutor=[f], notering='Föremålet kan vara synligt tidigare. Två provrutor är ingen kontinuerlig objektspårning.'))
            if record['lage'] != 'hand' or record.get('hallare') is None or not refs:
                continue
            if previous and previous['hallare'] != record['hallare']:
                # Händelsen är ett kandidatspann på den NYA scenen, inte en exakt
                # fysisk överlämning över ett klipp. Generisk mat kan ha flera exemplar.
                scene = next(s for s in scenes if s['id'] == record['scen'])
                event(record['scen'] + '_' + prop['id'] + '_hallarbyte', 'hallarbyte_kandidat',
                      'Olika föreslagna hållare på var sin sida av klipp; möjlig överlämning', record['scen'],
                      scene['start_s'], refs[0]['kallruta'] / fps,
                      ursprung('antagen', 'Skillnad i propmätningens scenvisa hållarbindningar; identitet och kontakt är inte uppmätta.'),
                      vem=previous['hallare'], till=record['hallare'], prop=prop['id'],
                      bevis=dict(filer=[], rutor=[refs[0]['kallruta']], notering='Kan vara klipp eller olika exemplar; får inte kallas säker mottagning.'))
            previous = record

    if semantik:
        origin = semantik['ursprung']
        ref = beroende(semfil) if semfil else None
        for shot in semantik['data'].get('tagningar', []):
            scene = next((s for s in scenes if s['id'] == shot['tagning'].lower()), None)
            if scene:
                event(scene['id'] + '_semantisk_handling', 'scen_handling', shot['vad'], scene['id'], scene['start_s'], scene['slut_s'],
                      ursprung('modellbedomd', 'Sparad semantisk scenbeskrivning; exakt handlingstid saknas.', shot['konfidens'], origin['modell']),
                      bevis=dict(filer=[ref] if ref else [], rutor=[], notering='Hela scenen är ett tidsfönster; ingen ny modell har anropats.'))
    events.sort(key=lambda e: (e['start_s'], e['id']))
    k['matning']['handelsebevis'] = [dict(handelse=e['id'], **e.pop('bevis')) for e in events]
    k['semantik']['handelser'] = events
    k['matning']['handelsekallor'] = list(dependencies.values())
    k['matning']['kvalitet'].append(dict(post='semantik.handelser', status='uppmatt',
        metod='Lokala spårgränser, råa handledsmöten, avlästa propregioner och sparade repliktider; semantiska handlingar och hållarbyten märks var för sig.',
        osakerhet='Ingen kontinuerlig propdetektor. Detektionsstart är inte fysisk entré, 2D-handmöte är inte mottagning; hållarbyte över klipp är antaget.',
        saknas_steg='Kontinuerlig objektidentitet och säker handkontakt kräver separat granskning.', kalla_fil=None))
    k['revision'] += 1
    return k


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kalla'); p.add_argument('semantik'); p.add_argument('ut')
    a = p.parse_args()
    src, sem, dst = (Path(x).resolve() for x in (a.kalla, a.semantik, a.ut))
    if dst.exists():
        raise FileExistsError(dst)
    if src.parent != dst.parent:
        raise ValueError('Källkopian måste ligga bredvid originalet.')
    k = fyll(json.loads(src.read_text(encoding='utf-8')), src.parent,
             json.loads(sem.read_text(encoding='utf-8')), sem)
    dst.write_text(json.dumps(k, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(dst, len(k['semantik']['handelser']), 'händelser')


if __name__ == '__main__':
    main()
