"""Fokusfrågor: de par av tagningar som konsensusen är osäker på (andel 0,25–0,75) ställs som smala frågor till videomodellen, flera gånger.

    python rum_fokus.py <ingestmapp> <konsensus_meta.json> [--modell google/gemini-2.5-flash] [--n 5] [--max-par 8] [--ut fokus.json]
    -> fokus.json: {falt: {"Sx|Sy": {andel, antal, svar}}}; ges till rum_konsensus.py --fokus

Först brett (hela deklarationen), sedan smalt där det brett är osäkert. Andel = ja / (ja + nej); "oklart" räknas inte.
"""
import argparse, base64, json, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rum_video import GATEWAY, las_json, nyckel

FRAGA = {
    'person_plats': 'Does the main person in shot {a} ({ta}) stand on the same spot in the room as the main person in shot {b} ({tb}), within about half a metre? They may be different people; judge the spot, using walls, tiles, windows, counters and fixtures behind and around them.',
    'huvudroll': 'Is the main person in shot {a} ({ta}) the same individual as the main person in shot {b} ({tb})? Use face, hair, clothing and on-screen names.',
    'kamera_vid': 'Are shots {a} ({ta}) and {b} ({tb}) filmed from the same camera position, within about half a metre (the angle may differ)? Use how the background lines up.'}
SCHEMA = {'type': 'object', 'required': ['svar', 'sakerhet', 'ledtradar'], 'properties': {
    'svar': {'type': 'string', 'enum': ['ja', 'nej', 'oklart']}, 'sakerhet': {'type': 'number'}, 'ledtradar': {'type': 'array', 'items': {'type': 'string'}}}}


def main():
    a = argparse.ArgumentParser(description=__doc__); a.add_argument('ingest'); a.add_argument('meta'); a.add_argument('--modell', default='google/gemini-2.5-flash')
    a.add_argument('--n', type=int, default=5); a.add_argument('--max-par', type=int, default=8); a.add_argument('--ut')
    a = a.parse_args(); I = Path(a.ingest); T = las_json(I / 'tagningar.json'); fps = T.get('fps') or 30.0
    tid = {t['id']: f"{t['start'] / fps:.2f}–{(t['slut'] + 1) / fps:.2f} s" for t in T['tagningar']}
    meta = json.loads(Path(a.meta).read_text(encoding='utf-8')); video = Path(T['klipp'])
    v = 'data:video/mp4;base64,' + base64.b64encode(video.read_bytes()).decode(); K = nyckel()
    jobb = []
    for falt, par in meta['par'].items():
        osakra = sorted(((abs(x[0] - .5), p) for p, x in par.items() if .25 <= x[0] <= .75), key=lambda z: z[0])[:a.max_par]
        jobb += [(falt, p) for _, p in osakra]
    def fraga(falt, p):
        x, y = p.split('|'); text = FRAGA[falt].format(a=x, b=y, ta=tid[x], tb=tid[y]) + ' Answer in JSON; give the tells behind your answer (in Swedish).'
        body = dict(model=a.modell, max_tokens=4000, messages=[dict(role='user', content=[dict(type='text', text=text), dict(type='file', file=dict(file_data=v, filename=video.name))])],
                    response_format=dict(type='json_schema', json_schema=dict(name='svar', strict=True, schema=SCHEMA)))
        r = urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
        import time
        for forsok in range(5):     # 429 (för många anrop): vänta och försök igen
            try: d = json.load(urllib.request.urlopen(r, timeout=300)); return falt, p, json.loads(d['choices'][0]['message']['content']), (d.get('usage') or {}).get('cost') or 0
            except urllib.error.HTTPError as e:
                if e.code != 429: return falt, p, dict(svar='oklart', fel=str(e)[:200]), 0
                time.sleep(5 * (forsok + 1))
            except Exception as e: return falt, p, dict(svar='oklart', fel=str(e)[:200]), 0
        return falt, p, dict(svar='oklart', fel='429 efter fem försök'), 0
    with ThreadPoolExecutor(3) as ex: svar = list(ex.map(lambda j: fraga(*j), [j for j in jobb for _ in range(a.n)]))
    ut, kostnad = {}, 0
    for falt, p, s, c in svar:
        kostnad += c; e = ut.setdefault(falt, {}).setdefault(p, dict(svar=[]))
        e['svar'].append(s)
    for falt, d in ut.items():
        for p, e in d.items():
            ja = sum(s.get('svar') == 'ja' for s in e['svar']); nej = sum(s.get('svar') == 'nej' for s in e['svar'])
            e.update(andel=ja / (ja + nej) if ja + nej else None, antal=ja + nej, ja=ja, nej=nej, tidigare=meta['par'][falt][p][0])
            print(f"{falt:<13} {p:<8} brett {e['tidigare']:.2f} -> fokus {e['andel'] if e['andel'] is None else round(e['andel'], 2)} (ja {ja}, nej {nej})")
    fil = Path(a.ut) if a.ut else Path(a.meta).with_name('fokus.json'); fil.write_text(json.dumps(ut, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(svar)} frågor, kostnad {kostnad:.4f} USD ->', fil)


if __name__ == '__main__': main()
