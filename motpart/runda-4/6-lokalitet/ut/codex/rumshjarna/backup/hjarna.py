"""rumshjärna/1: orkestrator för genererat rum utan förgrund (V2) som hypotes i 0.0.

Bildgenerering används bara för BORTTAGNING (personer + det de håller, överlagrad text). Allt annat är hjärnans logik:
1. behov: tagningar där personen täcker >= 2 % av mittrutan (andra tagningar behöver ingen hypotes)
2. rum över tagningar (L7, geometriska bevis): i varje grupp väljs ett ankare (minst personyta). Ankarets referens är
   originalrutan om den saknar person, annars ankarets egen V2. Övriga i gruppen genereras MOT referensen (samma
   möbler, samma föremål, samma placering), så att scen 3 liknar scen 1 i stället för att varje scen bestämmer själv.
   Utan geometriska bevis: ingen koppling, oberoende generering.
3. linjering: varje bild registreras tillbaka till originalets utsnitt (ECC affin på kantbilder); misslyckas den
   märks bilden 'ej konvergerad' och lokaliteten använder den inte.
4. observation: samma MoGe/OneFormer/GeoCalib som originalet (modal_obs::bildobs)
5. andra rösten (likhet.py): geometri och utseende på V2; utseende ensamt länkar aldrig (matnärbilder liknar varandra
   oavsett plats), betingade par räknas inte (likheten är skapad av hjärnan själv). Kandidater renderas utan koppling.
Lokaliteten (lokalitet.py) avgör sedan per tagning om hypotesen får användas (djupfel, kanttrohet, linjering).

usage: python hjarna.py <nyckel> [--parallell 4] [--plan]
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent; LOK = HERE.parent; ROOT = LOK.parents[2]
sys.path.insert(0, str(LOK)); sys.path.insert(0, str(HERE))
import lokalitet as L  # noqa: E402

CX = Path.home() / '.codex'
PROMPT_V2 = (HERE / 'promptar' / 'v2_rum.txt').read_text(encoding='utf-8').strip()
PROMPT_K = (HERE / 'promptar' / 'v2_konsistent_allman.txt').read_text(encoding='utf-8').strip()
BILDINSTR = '\n\nUse your image generation tool to create the image. Reply only with "done." when the image exists.'
BEHOV = 0.02


def ruta_png(video, u, dst):
    if not dst.is_file():
        cap = cv2.VideoCapture(str(ROOT / 'data/format/kontroll/klipp' / (video + '.mp4'))); cap.set(cv2.CAP_PROP_POS_FRAMES, u); ok, fr = cap.read()
        assert ok, (video, u); cv2.imwrite(str(dst), fr)
    return dst


def codex_bild(dst, prompt, bilder):
    """Ett bildanrop; parallellsäkert: bilden hämtas ur sessionens egen katalog (generated_images/<session-id>/)."""
    if dst.is_file():
        return json.loads(dst.with_suffix('.json').read_text(encoding='utf-8')) if dst.with_suffix('.json').is_file() else {'cache': True}
    t0 = time.time(); instr = prompt + BILDINSTR
    with tempfile.TemporaryDirectory() as d:
        cmd = [shutil.which('codex') or 'codex', 'exec', '--skip-git-repo-check', '-s', 'read-only', '-C', d, '-c', 'model_reasoning_effort="low"']
        cmd += ['--image=' + str(Path(b).resolve()) for b in bilder] + ['-']
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900, input=instr)
    m = re.search(r'session id:\s*([0-9a-f-]{36})', r.stderr or '')
    sid = m.group(1) if m else None
    kand = sorted((CX / 'generated_images' / sid).glob('*.png'), key=lambda p: p.stat().st_mtime) if sid else []
    fram = None
    if sid:
        sess = next(iter(CX.glob(f'sessions/*/*/*/rollout-*{sid}.jsonl')), None)
        fram = bool(sess) and prompt[:120] in sess.read_text(encoding='utf-8', errors='replace')
    post = {'exit': r.returncode, 'session': sid, 'prompt_fram': fram, 'sekunder': round(time.time() - t0, 1), 'bilder': [Path(b).name for b in bilder],
            'prompt_sha': hashlib.sha256(prompt.encode()).hexdigest()[:12], 'stderr_slut': (r.stderr or '')[-400:]}
    if kand:
        shutil.copy(kand[-1], dst); post['kalla'] = str(kand[-1])
    dst.with_suffix('.json').write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding='utf-8')
    return post


def kant(im):
    return cv2.GaussianBlur(cv2.Canny(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 60, 160).astype(np.float32), (0, 0), 3)


def registrera(org, gen):
    gen = cv2.resize(gen, (org.shape[1], org.shape[0]), interpolation=cv2.INTER_AREA)
    try:
        W = np.eye(2, 3, dtype=np.float32)
        cc, W = cv2.findTransformECC(kant(org), kant(gen), W, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), None, 5)
        ut = cv2.warpAffine(gen, W, (org.shape[1], org.shape[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        return ut, {'linjering': 'registrerad', 'ecc': round(float(cc), 3), 'forflyttning_px': [round(float(W[0, 2]), 1), round(float(W[1, 2]), 1)],
                    'skala': round(float(np.sqrt(abs(np.linalg.det(W[:, :2])))), 3)}
    except cv2.error:
        return gen, {'linjering': 'ej konvergerad'}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('nyckel'); ap.add_argument('--parallell', type=int, default=4); ap.add_argument('--plan', action='store_true')
    a = ap.parse_args()
    out = LOK / 'ut' / a.nyckel; d = LOK / 'ut' / 'rumshjarna' / a.nyckel; gen = d / 'gen'; fyll = d / 'fyllnad'
    gen.mkdir(parents=True, exist_ok=True); fyll.mkdir(parents=True, exist_ok=True)
    meta = json.loads((out / 'obs_gpu.json').read_text(encoding='utf-8')); rep = json.loads((out / 'lokalitet.json').read_text(encoding='utf-8'))
    gk = L.gruppkarta(meta['etiketter']); video = meta['klipp']
    # 1. behov per tagning
    tag = {}; pmask = {}
    for t in meta['tagningar']:
        u = t['nyckelrutor'][len(t['nyckelrutor']) // 2]; o = L.ladda(out, u, gk, 'obs_gpu')
        pers = np.isin(o['I'], [i for i, l in o['segs'].items() if gk.get(l) == 'person']) if 'I' in o else o['G'] == 'person'
        tag[t['id']] = {'ruta': u, 'personandel': round(float(pers.mean()), 3), 'behov': bool(pers.mean() >= BEHOV)}; pmask[t['id']] = pers
        ruta_png(video, u, d / f"{t['id']}_orig.png")
    # 2. plan: ankare per rumsgrupp (L7), referens = originalruta utan person, annars ankarets V2
    grupper = rep.get('rum_over_tagningar', {}).get('grupper', [])
    i_grupp = {s: g for g in grupper for s in g}
    fas1, fas2 = [], []
    for g in grupper:
        ank = min(g, key=lambda s: tag[s]['personandel'])
        for s in g:
            tag[s]['grupp'] = sorted(g, key=lambda x: int(x[1:])); tag[s]['ankare'] = ank
        ref = d / f'{ank}_orig.png' if not tag[ank]['behov'] else gen / f'{ank}_v2.png'
        if tag[ank]['behov']:
            fas1.append((ank, None))
        for s in g:
            if s != ank and tag[s]['behov']:
                fas2.append((s, (ank, ref))); fas1.append((s, None))  # båda kandidaterna; valet görs på uppmätt förskjutning
    for s, v in tag.items():
        if v['behov'] and s not in i_grupp:
            fas1.append((s, None))
    plan = {'behov_tröskel': BEHOV, 'tagningar': tag, 'fas1_oberoende': [s for s, _ in fas1], 'fas2_mot_ankare': {s: r[0] for s, r in fas2}}
    (d / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
    print('plan', a.nyckel, 'oberoende', plan['fas1_oberoende'], 'mot ankare', plan['fas2_mot_ankare'], flush=True)
    if a.plan:
        return

    def gor(job):
        s, ref = job
        src = d / f'{s}_orig.png'
        if ref is None:
            return s, codex_bild(gen / f'{s}_v2.png', PROMPT_V2, [src]), gen / f'{s}_v2.png', 'oberoende'
        ank, rfil = ref
        dst = gen / f'{s}_v2_k{ank}.png'
        return s, codex_bild(dst, PROMPT_K, [src, rfil]), dst, f'mot ankare {ank} ({"originalruta" if rfil.name.endswith("_orig.png") else "ankarets V2"})'
    t0 = time.time(); logg = {}
    for fas in (fas1, fas2):
        with ThreadPoolExecutor(a.parallell) as ex:
            for s, post, dst, kons in ex.map(gor, fas):
                logg.setdefault(s, []).append({'post': post, 'fil': dst, 'konsistens': kons})
                print(s, 'klar' if dst.is_file() else 'MISSLYCKAD', post.get('sekunder'), flush=True)
    # 3. linjering tillbaka till eget utsnitt
    # Gemini-granskningen 21 nov: alla 8 falskt släppta var ankarbetingade (perspektivskifte, inklistrat ankarinnehåll).
    # Ankarbetingad kandidat väljs bara om dess lokala förskjutning är liten och inte sämre än den oberoende.
    from rest import rest_px
    fl = {}
    for s, kand in logg.items():
        org = cv2.imread(str(d / f'{s}_orig.png'))
        pm = cv2.resize(pmask[s].astype(np.uint8), (org.shape[1], org.shape[0]), interpolation=cv2.INTER_NEAREST)
        synlig = ~cv2.dilate(pm, np.ones((31, 31), np.uint8)).astype(bool)
        bud = []
        for v in kand:
            if not v['fil'].is_file():
                continue
            reg, info = registrera(org, cv2.imread(str(v['fil'])))
            info['rest'] = rest_px(org, reg, synlig) if info['linjering'] == 'registrerad' else None
            bud.append((reg, {'kalla': v['fil'].name, 'konsistens': v['konsistens'], **info, 'sekunder': v['post'].get('sekunder'), 'prompt_fram': v['post'].get('prompt_fram')}))
        if not bud:
            continue
        med = lambda b: b[1]['rest']['median_px'] if b[1].get('rest') else 99.0
        obe = [b for b in bud if b[1]['konsistens'] == 'oberoende']; ank = [b for b in bud if b[1]['konsistens'] != 'oberoende']
        if ank and med(ank[0]) <= 2.0 and (not obe or med(ank[0]) <= med(obe[0]) + 0.5):
            val, skal = ank[0], 'ankarbetingad: liten förskjutning'
        else:
            val = min(bud, key=med); skal = 'minst förskjutning' if len(bud) > 1 else 'enda kandidaten'
        cv2.imwrite(str(fyll / f'{s}_v2.png'), val[0])
        fl[s] = {**val[1], 'val': skal, 'kandidater': [{k_: b[1].get(k_) for k_ in ('kalla', 'linjering', 'rest')} for b in bud]}
    (fyll / 'fyllnad.json').write_text(json.dumps(fl, ensure_ascii=False, indent=1), encoding='utf-8')
    gen_s = round(time.time() - t0, 1)
    # 4. observation på Modal (samma modeller som originalet)
    t1 = time.time()
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    for f in fyll.glob('*.obs.npz'):
        f.unlink()
    r = subprocess.run([str(ROOT / 'scen/.venv/Scripts/modal.exe'), 'run', str(LOK / 'modal_obs.py') + '::bildobs', '--katalog', str(fyll)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=1200)
    obs_s = round(time.time() - t1, 1)
    # 5. andra rösten om samma plats (likhet.py: geometri på V2, utseende, cirkularitet borträknad)
    import likhet
    likhet.main(a.nyckel)
    res = {'plan': plan, 'fyllnad': fl, 'tid_s': {'generering': gen_s, 'observation': obs_s}, 'modal_ok': 'klar' in (r.stdout or '')}
    (d / 'hjarna.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(json.dumps({k: res[k] for k in ('tid_s', 'modal_ok')}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
