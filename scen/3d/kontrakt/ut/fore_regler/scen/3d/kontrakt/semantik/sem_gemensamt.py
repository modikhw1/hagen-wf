"""Gemensamma hjälpare för semantiksteget: klippregister, uppmätta tagningar och spår, hashar och en liten schemakontroll.

Allt här läser bara. Inget skrivs utanför semantik/ut/.
"""
import hashlib
import json
import re
from pathlib import Path

import numpy as np

HIT = Path(__file__).resolve().parent
ROT = HIT.parents[3]                     # hagen-wf
SCEN = ROT / 'scen'
INGEST_UT = SCEN / '3d/ingest/ut'
KLIPPMAPP = SCEN / 'klipp'
UT = HIT / 'ut'

# Klippregistret: kort namn -> ingestmapp och källvideo. Ingestmappens namn följer inte alltid videons.
KLIPP = {
    'notan': dict(ingest='notan-tagningar', video='d-dialog-notan.mp4'),
    'b': dict(ingest='b-tilltal-ravara-tagningar', video='b-tilltal-ravara.mp4'),
    'a': dict(ingest='a-sketch-servering-tagningar', video='a-sketch-servering.mp4'),
    'kenny': dict(ingest='kand-kennysgelato-tagningar', video='kand-kennysgelato2.0-7596403003901381910.mp4'),
}


def ladda(p):
    b = Path(p).read_bytes()
    try: return json.loads(b.decode('utf-8'))
    except UnicodeDecodeError: return json.loads(b.decode('cp1252'))   # äldre ingestfiler


def skriv(p, data):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def klipp_vagar(namn):
    if namn not in KLIPP: raise SystemExit(f'Okänt klipp {namn}. Kända: {", ".join(KLIPP)}')
    k = KLIPP[namn]
    return dict(namn=namn, ingest=INGEST_UT / k['ingest'], video=KLIPPMAPP / k['video'], ut=UT / namn)


def tagningar(ingest):
    """Tagningarna med bildintervall [start, slut) på källklockan. tagningar.json om den finns, annars summan av meta.json:s N."""
    ds = sorted([p for p in Path(ingest).iterdir() if p.is_dir() and p.name[:1] == 'S' and p.name[1:].isdigit() and (p / 'meta.json').exists()],
                key=lambda p: int(p.name[1:]))
    metas = {d.name: ladda(d / 'meta.json') for d in ds}
    fps = {m['fps'] for m in metas.values()}
    if len(fps) != 1: raise SystemExit('Olika fps mellan tagningar.')
    fps = fps.pop()
    tj = Path(ingest) / 'tagningar.json'
    gr = {}
    if tj.exists():
        for t in ladda(tj)['tagningar']: gr[t['id']] = (t['start'], t['slut'] + 1)
    ut, pos = [], 0
    for d in ds:
        n = metas[d.name]['N']
        a, b = gr.get(d.name, (pos, pos + n))
        if (b - a) != n or a != pos:
            raise SystemExit(f'{d.name}: tagningar.json ({a}..{b}) stämmer inte med meta.json (N={n}, kumulativt {pos}).')
        ut.append(dict(id=d.name, mapp=d, start=a, slut=b, N=n, fps=fps, bredd=metas[d.name]['bredd'], hojd=metas[d.name]['hojd'],
                       klippfil=Path(ingest) / 'klipp' / f'{d.name}.mp4'))
        pos += n
    return ut


def sparlista(shot):
    """Uppmätta spår i en tagning: {spar_id: {...}}. Boxar ur personer.json (lokal bildruta -> [x0,y0,x1,y1] i pixlar)."""
    d = shot['mapp']
    P = ladda(d / 'personer.json') if (d / 'personer.json').exists() else {}
    res = {}
    for tid in sorted(set(P) | {p.stem[8:] for p in d.glob('sekvens_*.npz')}, key=lambda s: (len(s), s)):
        boxar = {int(f): b for f, b in P.get(tid, {}).items()}
        inom = 0
        sp = d / f'sekvens_{tid}.npz'
        har_sek = sp.exists()
        if sp.exists():
            S = np.load(sp); inom = int(S['inom'].sum()); S.close()
        fr = sorted(boxar)
        W, H = shot['bredd'], shot['hojd']
        if boxar:
            hh = [(b[3] - b[1]) / H for b in boxar.values()]; ww = [(b[2] - b[0]) / W for b in boxar.values()]
            cx = [((b[0] + b[2]) / 2) / W for b in boxar.values()]; cy = [((b[1] + b[3]) / 2) / H for b in boxar.values()]
            kant = [b[0] <= 3 or b[1] <= 3 or b[2] >= W - 3 or b[3] >= H - 3 for b in boxar.values()]
            stat = dict(hojd_andel=round(float(np.median(hh)), 3), bredd_andel=round(float(np.median(ww)), 3),
                        mitt_x=round(float(np.median(cx)), 3), mitt_y=round(float(np.median(cy)), 3), kantandel=round(float(np.mean(kant)), 2))
        else:
            stat = dict(hojd_andel=None, bredd_andel=None, mitt_x=None, mitt_y=None, kantandel=None)
        res[tid] = dict(spar_id=tid, har_sekvens=har_sek, boxar=boxar, rutor_med_box=len(boxar), rutor_i_bild=inom,
                        forsta=fr[0] if fr else None, sista=fr[-1] if fr else None, **stat)
    return res


def tc(ruta, fps):
    return f'{ruta / fps:.2f}s'


# ---------------------------------------------------------------- liten JSON Schema-kontroll (inga paket)
def validera(data, schema, sokvag='$', rot=None):
    """Stöder type (även lista), enum, required, properties, additionalProperties:false, items, minItems, minimum, maximum, minLength. Ger lista med felmeddelanden."""
    fel = []
    t = schema.get('type')
    typer = t if isinstance(t, list) else ([t] if t else [])
    def ok(tp):
        return {'string': isinstance(data, str), 'number': isinstance(data, (int, float)) and not isinstance(data, bool),
                'integer': isinstance(data, int) and not isinstance(data, bool), 'boolean': isinstance(data, bool),
                'array': isinstance(data, list), 'object': isinstance(data, dict), 'null': data is None}[tp]
    if typer and not any(ok(x) for x in typer):
        return [f'{sokvag}: väntade {typer}, fick {type(data).__name__}']
    if 'enum' in schema and data not in schema['enum']:
        fel.append(f'{sokvag}: {data!r} ligger utanför {schema["enum"]}')
    if isinstance(data, str) and len(data) < schema.get('minLength', 0): fel.append(f'{sokvag}: för kort sträng')
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if 'minimum' in schema and data < schema['minimum']: fel.append(f'{sokvag}: {data} < {schema["minimum"]}')
        if 'maximum' in schema and data > schema['maximum']: fel.append(f'{sokvag}: {data} > {schema["maximum"]}')
    if isinstance(data, dict):
        for r in schema.get('required', []):
            if r not in data: fel.append(f'{sokvag}: saknar {r}')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            for k in data:
                if k not in props: fel.append(f'{sokvag}: okänt fält {k}')
        for k, v in data.items():
            if k in props: fel += validera(v, props[k], f'{sokvag}.{k}', rot)
    if isinstance(data, list):
        if len(data) < schema.get('minItems', 0): fel.append(f'{sokvag}: färre än {schema["minItems"]} poster')
        if 'items' in schema:
            for i, v in enumerate(data): fel += validera(v, schema['items'], f'{sokvag}[{i}]', rot)
    return fel


def norm_ord(s):
    return re.sub(r'[^\wåäöÅÄÖéèüø]', '', s.lower())
