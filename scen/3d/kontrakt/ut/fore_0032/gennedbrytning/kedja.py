"""0030: den generativa nedbrytningen som en körbar kedja för en tagning. Ett kommando, cache per steg, och ett rent stopp där en
manuell generering behövs.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/kedja.py <konfig.json> [--fran <steg>] [--till <steg>] [--tvinga]
Konfigen (kedja/<klipp>/<tagning>.json) har tagningens parametrar (tagning.py läser samma fil genom GENNED_TAGNING) och:
  namn          kedjans namn; varianterna heter <namn>, <namn>_t, <namn>_t_rot, <namn>_t_kam, scenen s_<namn>
  leverantor    dreamina_hand (paket + väntan på svar/) eller fal_ray (API; kräver saldo); kedjan vet inget mer om leverantören
  paket         mappen leverantören läser ur och svarar i (d_video/dreamina-paket/<...>); svaret är en mp4 i <paket>/svar/
  kalla         källan kroppen förs in i (kontrakt/ut/.../kalla_*.json) och specarna för kalla_generering/kalla_mening (valfritt)
Stegen (STRATEGI.md, 0030), i ordning:
  generering -> las -> tid -> kontroll -> forvarld -> samspel -> rot -> kamera -> scen1 -> sked -> scen2 -> mening -> kalla
Cache: kedja/<namn>/steg.json har per steg en hash av konfigen, stegets indatafiler och skripten. Ett steg körs om bara när något av det
ändrats (eller med --tvinga). Varje steg loggar kommando, väggtid och utfall i kedja/<namn>/logg.jsonl.
Relevans och tom scen (bildmodell) ligger före genereringen och körs inte här; relevanssteget har eget kommando (relevans/relevans_steg.py).
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

HIT = Path(__file__).resolve().parent; ROT = HIT.parents[2]; PY = ROT / 'scen/.venv/Scripts/python.exe'; PY_SAM = HIT.parent / 'klipp2/sam3db/.venv/Scripts/python.exe'
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
STEG = ['generering', 'las', 'tid', 'kontroll', 'forvarld', 'samspel', 'rot', 'kamera', 'scen1', 'sked', 'scen2', 'mening', 'kalla']


class Vantar(Exception): pass


def sha(p):
    p = Path(p)
    if p.is_dir(): return hashlib.sha256(''.join(sha(x) for x in sorted(p.rglob('*')) if x.is_file()).encode()).hexdigest()
    if not p.exists(): return 'saknas'
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def main():
    a = argparse.ArgumentParser(); a.add_argument('konfig'); a.add_argument('--fran'); a.add_argument('--till'); a.add_argument('--tvinga', action='store_true'); x = a.parse_args()
    kf = Path(x.konfig).resolve(); K = json.loads(kf.read_text(encoding='utf-8')); namn = K['namn']; v = namn
    arbete = HIT / 'kedja' / namn; arbete.mkdir(parents=True, exist_ok=True); cache_f = arbete / 'steg.json'
    cache = json.loads(cache_f.read_text(encoding='utf-8')) if cache_f.exists() else {}
    env = dict(os.environ, GENNED_TAGNING=str(kf), PYTHONIOENCODING='utf-8')
    sys.path.insert(0, str(HIT)); os.environ['GENNED_TAGNING'] = str(kf)
    import tagning; T = tagning.T; kam = T['kamera']; sf = T['scen_flaggor']; hf = T.get('handforemal')

    def kor(cmd, logg, cwd=ROT):
        with open(arbete / logg, 'w', encoding='utf-8') as f:
            r = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode: raise RuntimeError(f'{cmd[1] if len(cmd) > 1 else cmd[0]} föll (rc {r.returncode}); se {arbete / logg}')

    D = lambda *p: HIT.joinpath(*p)
    steg = {
        'generering': dict(indata=[K['paket']], fn=lambda: generering(K, v)),
        'las': dict(indata=[D('d_video', v, 'isolerad.mp4'), D('f_las.py')], fn=lambda: kor([PY, D('f_las.py'), v], 'las.log')),
        'kontroll': dict(indata=[D('d_video', v + '_t', 'las'), D('h_kontroll.py')], fn=lambda: kor([PY, D('h_kontroll.py'), v + '_t'], 'kontroll.log')),   # på källans rutor, efter tidspassningen
        'tid': dict(indata=[D('d_video', v, 'las'), D('t_tid.py')], fn=lambda: kor([PY, D('t_tid.py'), v], 'tid.log')),
        'forvarld': dict(indata=[D('d_video', v + '_t'), D('g_forvarld.py'), tagning.PLAN], fn=lambda: kor([PY, D('g_forvarld.py'), v + '_t', '--kamerafri'] if K.get('kamerafri', True) else [PY, D('g_forvarld.py'), v + '_t'], 'forvarld.log')),
        'samspel': dict(indata=[D('g_forvarld', v + '_t', 'scen.blend')], fn=lambda: kor([BLENDER, '-b', D('g_forvarld', v + '_t', 'scen.blend'), '--python', D('j_samspel_blender.py'), '--', D('samspel', v + '.json')], 'samspel.log')),
        'rot': dict(indata=[D('samspel', v + '.json'), D('g_forvarld', v + '_t', 'sekvens_1.npz'), D('r_rot.py')],
                    fn=lambda: kor([PY, D('r_rot.py'), v + '_t', D('samspel', v + '.json'), '--fot-rutor', *T['fot_rutor']], 'rot.log')),
        'kamera': dict(indata=[D('g_forvarld', v + '_t_rot', 'plan.json'), D('samspel', v + '_rot.json'), D('r_kamera.py')],
                       fn=lambda: kor([PY, D('r_kamera.py'), v + '_t_rot', f'samspel/{v}_rot.json', '--modell', kam['modell'], '--hojd', kam['hojd'], '--vrid', '--lins0', kam['lins0'],
                                       '--ymin', kam['ymin'], '--vrid-vikt', kam['vrid_vikt'], '--skriv', v + '_t_kam'], 'kamera.log')),
        'scen1': dict(indata=[D('g_forvarld', v + '_t_kam', 'plan.json'), D('samspel', v + '_rot.json'), D('s_scen.py')],
                      fn=lambda: (kor([PY, D('s_scen.py'), '--plan', f'g_forvarld/{v}_t_kam/plan.json', '--samspel', f'samspel/{v}_rot.json', '--ut', f's_{v}_1', '--ljus',
                                       '--trag-max', sf['trag_max'], '--glas', sf['glas'], *(['--bak-lag'] if sf.get('bak_lag') else []), '--bygg'], 'scen1.log'),
                                  kor([BLENDER, '-b', D(f's_{v}_1', 'scen.blend'), '--python', D('j_samspel_blender.py'), '--', D('samspel', f'{v}_scen1.json')], 'scen1_samspel.log'))),
        'sked': dict(indata=[D('samspel', f'{v}_scen1.json'), D('d_video', v, 'isolerad.mp4'), D('r_sked2.py')],
                     fn=lambda: None if not hf else (kor([PY, D('r_sked.py'), v, '--ben', hf['ben'], '--ljus', hf['ljus']], 'sked_r.log'),
                                                     kor([PY, D('r_sked2.py'), v, f's_{v}_1', f'samspel/{v}_scen1.json'], 'sked.log'))),
        'scen2': dict(indata=[D(f's_{v}_1', 'sked_faste.json'), D('samspel', f'{v}_scen1.json'), D('s_scen.py')],
                      fn=lambda: (kor([PY, D('s_scen.py'), '--plan', f'g_forvarld/{v}_t_kam/plan.json', '--samspel', f'samspel/{v}_scen1.json', '--ut', f's_{v}', '--ljus',
                                       *(['--sked', f's_{v}_1/sked_faste.json'] if hf else []), '--trag-max', sf['trag_max'], '--glas', sf['glas'], *(['--bak-lag'] if sf.get('bak_lag') else []), '--bygg'], 'scen2.log'),
                                  kor([BLENDER, '-b', D(f's_{v}', 'scen.blend'), '--python', D('j_samspel_blender.py'), '--', D('samspel', f'{v}_scen2.json')], 'scen2_samspel.log'),
                                  kor([BLENDER, '-b', D(f's_{v}', 'scen.blend'), '--python', D('r_synlig_blender.py'), '--', D(f's_{v}', 'synlig.json')], 'scen2_synlig.log'))),
        'mening': dict(indata=[D('samspel', f'{v}_scen2.json'), D(f's_{v}', 'plan.json'), D('v_mening.py')],
                       fn=lambda: kor([PY, D('v_mening.py'), '--ut', f's_{v}', '--samspel', f'samspel/{v}_scen2.json', '--film', f's_{v}/film.mp4'], 'mening.log')),
        'kalla': dict(indata=[D(f's_{v}', 'plan.json')], fn=lambda: kalla(K, v, kor)),
    }
    i0 = STEG.index(x.fran) if x.fran else 0; i1 = STEG.index(x.till) + 1 if x.till else len(STEG)
    for s in STEG[i0:i1]:
        nyckel = sha(kf) + ''.join(sha(p) for p in steg[s]['indata'])
        if not x.tvinga and cache.get(s, {}).get('nyckel') == nyckel and cache[s].get('status') == 'klar':
            print(f'{s:11s} cache', flush=True); continue
        t = time.time()
        try:
            steg[s]['fn'](); status = 'klar'
        except Vantar as e:
            status = 'vantar'; print(f'{s:11s} VÄNTAR: {e}', flush=True)
        except Exception as e:
            status = 'fel'; print(f'{s:11s} FEL: {e}', flush=True)
        post = dict(steg=s, status=status, s=round(time.time() - t, 1), tid=time.strftime('%Y-%m-%d %H:%M:%S'))
        with open(arbete / 'logg.jsonl', 'a', encoding='utf-8') as f: f.write(json.dumps(post, ensure_ascii=False) + '\n')
        cache[s] = dict(nyckel=nyckel if status == 'klar' else None, **post); cache_f.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
        if status != 'klar': sys.exit(2 if status == 'vantar' else 1)
        print(f'{s:11s} klar {post["s"]} s', flush=True)


def generering(K, v):
    """Leverantören är utbytbar: kedjan skriver eller läser ett paket och tar emot en video av den isolerade personen."""
    paket = HIT / K['paket']; svar = sorted((paket / 'svar').glob('*.mp4')); ut = HIT / 'd_video' / v; ut.mkdir(parents=True, exist_ok=True)
    if K.get('befintlig'):
        src = HIT / K['befintlig']   # en generering som redan finns (t.ex. d_video/dreamina/isolerad.mp4) körs genom kedjan igen
        shutil.copy(src, ut / 'isolerad.mp4'); (ut / 'kalla.json').write_text(json.dumps(dict(leverantor=K['leverantor'], fil=str(src), anmarkning='befintlig generering'), ensure_ascii=False), encoding='utf-8'); return
    if K['leverantor'] == 'fal_ray':
        raise Vantar('fal_ray: kör d2_video.py med saldo på fal (ingen ny generering i 0030); lägg utfallet i ' + str(paket / 'svar'))
    if not svar:
        (paket / 'svar').mkdir(parents=True, exist_ok=True)
        raise Vantar(f'paketet ligger i {paket} (LAS-MIG.md). Lägg Dreaminas mp4 i {paket / "svar"} och kör samma kommando igen.')
    import cv2
    c = cv2.VideoCapture(str(svar[-1])); n = int(c.get(cv2.CAP_PROP_FRAME_COUNT))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(svar[-1]), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-an', str(ut / 'isolerad.mp4')], check=True)
    (ut / 'kalla.json').write_text(json.dumps(dict(leverantor=K['leverantor'], fil=str(svar[-1]), rutor=n), ensure_ascii=False), encoding='utf-8')


def kalla(K, v, kor):
    if not K.get('kalla'): return
    k = K['kalla']; KON = HIT.parent / 'kontrakt'
    for steg, skript in (('generering', 'kalla_generering.py'), ('mening', 'kalla_mening.py')):
        if k.get(steg): kor([PY, KON / skript, KON / k[steg]['fran'], KON / k[steg]['till'], ROT / k[steg]['spec']], f'kalla_{steg}.log', cwd=KON)


if __name__ == '__main__': main()
