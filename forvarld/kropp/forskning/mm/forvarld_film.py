"""FORSKNING: utfall ur mening.py renderade i förvärlden (MHR-kroppen i scenen), bredvid originalet och den lästa kroppen. Vilket klipp som helst.

  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/forvarld_film.py <mening-namn> [<mening-namn> ...]
Alla namn måste gälla samma tagning (samma kalla, scen och person). Läser ut/mening_<namn>/logg.json och sekvens.npz.

Planen är klippets redan kompilerade plan: <kallans mapp>/narvaro/plan.json, eller för gelato forvarld/kropp/ut/plan/bas.json.
Tagningens sekvens byts mot utfallet, scenen byggs i lokal Blender med kedjans rigg (scen/3d/ingest/mhr_rig.py), och bara
tagningens rutor renderas. Ut: ut/mening_<första>/forvarld.mp4 och forvarld_r<ruta>.png: original | före | en kolumn per mening.
Kroppen kommer ur MaskedMimic (AMASS-tränad): forskning.
"""
import json, subprocess, sys
sys.dont_write_bytecode = True
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
HIT = Path(__file__).resolve().parent; ROOT = HIT.parents[3]; KON = ROOT / 'scen/3d/kontrakt/ut'; U = HIT / 'ut'
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
RIG = ROOT / 'scen/3d/ingest/mhr_rig.py'; GLAS = ROOT / 'scen/3d/gennedbrytning/s_glas_blender.py'
PLAN = {'kand-kennysgelato_n06-hand': ROOT / 'forvarld/kropp/ut/plan/bas.json'}   # klipp där förvärldens plan inte är kallans narvaro/plan.json
F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)


def lika(a, b):
    try: return Path(a).resolve() == Path(b).resolve()
    except Exception: return False


def byt(x, gammal, ny, n=[0]):
    if isinstance(x, dict): return {k: byt(v, gammal, ny, n) for k, v in x.items()}
    if isinstance(x, list): return [byt(v, gammal, ny, n) for v in x]
    if isinstance(x, str) and x.lower().endswith('.npz') and lika(x, gammal): n[0] += 1; return str(ny)
    return x


def bygg(plan, d):
    """Scenen i Blender ur en plan. Samma steg som forvarld/gelato/bild.py, men tagningsmappen tas ur planen."""
    if (d / 'scen.blend').exists(): return
    d.mkdir(parents=True, exist_ok=True); P = json.loads(plan.read_text(encoding='utf-8')); tag = Path(P['matning']['kameror'][0]['spar_metrisk']['sokvag']).parent
    with open(d / 'blender.log', 'w', encoding='utf-8') as f:
        subprocess.run([BLENDER, '-b', '--factory-startup', '-t', '8', '--python-exit-code', '1', '--python', str(RIG), '--', str(tag), P['kallvideo'],
                        '--plan', str(plan), '--ut', str(d), '--tillat-flaggad'], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
    glas = sorted({o['id'] for o in P.get('objekt', []) if o.get('yta') == 'glas'})
    if glas:
        with open(d / 'glas.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', str(d / 'scen.blend'), '--factory-startup', '--python-exit-code', '1', '--python', str(GLAS), '--', ','.join(glas)],
                           cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)


def rutor(plan, d, a, b):
    bygg(plan, d); saknas = [u for u in range(a, b) if not (d / f'r{u:04d}.png').exists()]
    if saknas:
        with open(d / f'r{a}_{b}.log', 'w', encoding='utf-8') as f:
            subprocess.run([BLENDER, '-b', str(d / 'scen.blend'), '-o', str(d / 'r####'), '-F', 'PNG', '-s', str(min(saknas)), '-e', str(max(saknas)), '-a'],
                           cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
    return [d / f'r{u:04d}.png' for u in range(a, b)]


def main():
    namn = sys.argv[1:]; L = {n: json.loads((U / f'mening_{n}' / 'logg.json').read_text(encoding='utf-8')) for n in namn}; L0 = L[namn[0]]
    if any((L[n]['kalla'], L[n]['scen'], L[n]['person']) != (L0['kalla'], L0['scen'], L0['person']) for n in namn): sys.exit('alla meningar måste gälla samma tagning')
    variant = Path(L0['kalla']).parent.name; basplan = PLAN.get(variant, KON / variant / 'narvaro' / 'plan.json')
    if not basplan.exists(): sys.exit(f'ingen kompilerad plan för {variant}: {basplan}')
    K = json.loads((KON / L0['kalla']).read_text(encoding='utf-8')); sc = {s['id']: s for s in K['semantik']['scener']}; kam = {k['id']: k for k in K['matning']['kameror']}
    mp = next(m for m in K['matning']['personer'] if m.get('scen') in (None, L0['scen']) and m['person'] == L0['person'])
    gammal = (KON / Path(L0['kalla']).parent / mp['rorelse']['sokvag']).resolve(); off = kam[sc[L0['scen']]['kamera']].get('kalla_ruta0', 0)
    P = json.loads(basplan.read_text(encoding='utf-8')); n = len(np.load(gammal)['pose'])
    tk = next((x for x in P['tidskarta'] if x['kalla'][0] <= off < x['kalla'][1]), None)
    if tk is None: sys.exit(f'tagningens rutor ({off}) finns inte i planens tidskarta')
    a = tk['ut'][0] + (off - tk['kalla'][0]); b = min(a + n, tk['ut'][1]); (U / 'plan').mkdir(exist_ok=True); bild = U / 'bild'
    fore = rutor(basplan, bild / f'bas_{variant}', a, b); kol = {}
    for m in namn:
        r = [0]; pl = byt(P, gammal, U / f'mening_{m}' / 'sekvens.npz', r)
        if not r[0]: sys.exit(f'planen pekar inte på tagningens sekvens ({gammal})')
        pl['licens'] = 'forskning'; pl.setdefault('anteckningar', []).append('FORSKNING. Kroppen ur MaskedMimic SMPL (ProtoMotions v3.0, AMASS-tränad, icke-kommersiell), via mening.py.')
        pf = U / 'plan' / f'm_{m}.json'; pf.write_text(json.dumps(pl, ensure_ascii=False, indent=1), encoding='utf-8'); kol[m] = rutor(pf, bild / f'm_{m}', a, b)
    cap = cv2.VideoCapture(P['kallvideo']); W, H = 300, 533; k = 2 + len(namn); BR = k * (W + 8); fps = P['utdata']['fps_taljare'] / P['utdata']['fps_namnare']
    ut = U / f'mening_{namn[0]}' / 'forvarld.mp4'; v = cv2.VideoWriter(str(ut), cv2.VideoWriter_fourcc(*'mp4v'), fps, (BR, H + 64)); visa = {int(round(x)) for x in np.linspace(0, b - a - 1, 4)[1:3]}
    for i, u in enumerate(range(a, b)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, P['kallrutor'][u]); ok, fr = cap.read(); orig = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)) if ok else None
        r = Image.new('RGB', (BR, H + 64), '#1c1c1c'); d = ImageDraw.Draw(r)
        for j, (im, rub) in enumerate([(orig, 'original'), (Image.open(fore[i]), 'före (läst kropp)')] + [(Image.open(kol[m][i]), L[m]['mening'][:34]) for m in namn]):
            if im is not None: r.paste(im.convert('RGB').resize((W, H)), (j * (W + 8), 28))
            d.text((j * (W + 8) + 4, 4), rub, fill='white', font=F)
        d.text((6, H + 36), f"{L0['tagning']}  ruta {i}   kroppen efter: MaskedMimic (AMASS-tränad, bara forskning). Antaget: {'; '.join(x['vad'] for x in L0['antaganden']) or 'inget'}.", fill='white', font=F)
        v.write(cv2.cvtColor(np.array(r), cv2.COLOR_RGB2BGR))
        if i in visa: r.save(U / f'mening_{namn[0]}' / f'forvarld_r{i}.png')
    v.release(); print('FORVARLD_KLAR', ut, f'rutor {a}-{b}')


if __name__ == '__main__': main()
