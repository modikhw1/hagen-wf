"""Var finns elementen i bild: objektdetektion på en nyckelbild per tagning (videomodellen avgör vad, bilden avgör var).

    python rum_detektera.py <ingestmapp> <deklaration för nivån> [--n 3] [--modell google/gemini-2.5-flash] [--ut <fil>]
    -> deklarationen med `bilder` (tagning, box_2d) för varje möbel och föremål, ur medianen av n detektioner per nyckelbild

Varför: rutor per tagning ur hela videon blev schablonvärden (samma ruta i alla tagningar), medan detektion på en enskild bild ger
rutor som följer bilden. Nyckelbilden är tagningens mittruta. En tagning där elementet inte hittas i minst hälften av körningarna får ingen ruta.
Elementen och deras beskrivningar tas ur deklarationen (möbler i `platser` med typ bord, föremål i `foremal`).
"""
import argparse, base64, json, statistics, subprocess, tempfile, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rum_video import GATEWAY, las_json, nyckel


def nyckelbild(I, t, fps):
    meta = las_json(I / t / 'meta.json'); v = Path(meta['kallvideo']); f = Path(tempfile.gettempdir()) / f'rum_detektera_{I.name}_{t}.jpg'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f"{meta['N'] / 2 / fps:.3f}", '-i', str(v), '-frames:v', '1', str(f)], check=True)
    return base64.b64encode(f.read_bytes()).decode()


def main():
    a = argparse.ArgumentParser(description=__doc__); a.add_argument('ingest'); a.add_argument('deklaration'); a.add_argument('--n', type=int, default=3)
    a.add_argument('--modell', default='google/gemini-2.5-flash'); a.add_argument('--ut')
    a = a.parse_args(); I = Path(a.ingest); T = las_json(I / 'tagningar.json'); fps = T.get('fps') or 30.0
    D = json.loads(Path(a.deklaration).read_text(encoding='utf-8'))
    element = {p: (v.get('beskrivning') or p) for p, v in D['platser'].items() if v.get('typ') == 'bord'}
    element.update({f: (v.get('beskrivning') or f) for f, v in (D.get('foremal') or {}).items()})
    # Bara tagningar där uppsättningen säger att elementet syns (tagningar_i_bild); detektioner i andra tagningar är falska träffar.
    tillatna = {k: set(v.get('tagningar_i_bild') or []) for k, v in list(D['platser'].items()) + list((D.get('foremal') or {}).items()) if k in element}
    lista = '\n'.join(f'- {k}: {b}' for k, b in element.items()); K = nyckel()
    fraga = ('Detect these elements in the image if they are visible (ids and descriptions):\n' + lista +
             '\nReturn a JSON object {"element": [{"id": <one of the ids>, "box_2d": [ymin, xmin, ymax, xmax] normalised 0-1000}]}. Omit elements that are not visible.')
    def kor(t, bild):
        body = dict(model=a.modell, max_tokens=3000, response_format=dict(type='json_object'),
                    messages=[dict(role='user', content=[dict(type='text', text=fraga), dict(type='image_url', image_url=dict(url='data:image/jpeg;base64,' + bild))])])
        r = urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
        for forsok in range(5):
            try: d = json.load(urllib.request.urlopen(r, timeout=120)); break
            except urllib.error.HTTPError as e:
                if e.code != 429: return t, [], 0
                time.sleep(5 * (forsok + 1))
        else: return t, [], 0
        try: s = json.loads(d['choices'][0]['message']['content']); s = s.get('element', s) if isinstance(s, dict) else s
        except ValueError: s = []
        return t, [x for x in s if isinstance(x, dict) and x.get('id') in element and len(x.get('box_2d') or []) == 4], (d.get('usage') or {}).get('cost') or 0
    bilder = {t['id']: nyckelbild(I, t['id'], fps) for t in T['tagningar']}
    with ThreadPoolExecutor(3) as ex: svar = list(ex.map(lambda j: kor(*j), [(t, b) for t, b in bilder.items() for _ in range(a.n)]))
    per, kostnad = {}, 0
    for t, s, c in svar:
        kostnad += c
        for x in s: per.setdefault(x['id'], {}).setdefault(t, []).append(x['box_2d'])
    for eid in element:
        rutor = [dict(tagning=t, box_2d=[round(statistics.median(v)) for v in zip(*b)], antal=len(b)) for t, b in sorted(per.get(eid, {}).items()) if len(b) >= a.n / 2 and (not tillatna[eid] or t in tillatna[eid])]
        mal = D['platser'][eid] if eid in D['platser'] else D['foremal'][eid]
        mal['bilder'] = [{k: r[k] for k in ('tagning', 'box_2d')} for r in rutor]; mal['bilder_kalla'] = f'rum_detektera.py: median av {a.n} detektioner per nyckelbild ({a.modell})'
        if rutor: mal['bild'] = {k: max(rutor, key=lambda r: (r['box_2d'][2] - r['box_2d'][0]) * (r['box_2d'][3] - r['box_2d'][1]))[k] for k in ('tagning', 'box_2d')}
        print(f"{eid:<12}", ' '.join(f"{r['tagning']}:{r['box_2d']}" for r in rutor) or 'inga rutor')
    ut = Path(a.ut) if a.ut else Path(a.deklaration).with_name(Path(a.deklaration).stem + '_detekterad.json')
    ut.write_text(json.dumps(D, ensure_ascii=False, indent=2), encoding='utf-8'); print(f'{len(svar)} anrop, kostnad {kostnad:.4f} USD ->', ut)


if __name__ == '__main__': main()
