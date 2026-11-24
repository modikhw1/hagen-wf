"""ordtider_klipp.py: ordtider ur ett klipps ljud (lokal Whisper) för vilket klipp som helst, och koppling till semantik.json:s repliker.

Generaliserar scen/3d/ordtider.py (som bara gäller notan: fast språk, fast manus, skriver in i scen3d.json). Skillnader:
  - Ljudet tas ur klippets mp4 med ffmpeg. Språk och modell väljs per klipp. Inga modeller hämtas: bara det som redan ligger på disk används.
  - Whisper körs UTAN replikerna som ledtråd (ordtider.py gav dem som initial_prompt). Annars hittar Whisper det modellen skrev även när ljudet
    saknar det, och en påhittad replik skulle se belagd ut.
  - Modellens repliker kopplas till Whispers ord med en monoton ordmatchning (viktad LCS med oskarp ordjämförelse). Varje replik får start, slut,
    ord med tider och en täckning (andel av replikens ord som Whisper hörde). Repliker med låg täckning flaggas som ej stödda av ljudet och får inga tider.
  - Whisper-ord som ingen replik förklarar rapporteras som tal utan replik.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/semantik/ordtider_klipp.py <klipp> [--sprak sv] [--modell auto|kb-medium|kb-small|systran-small] [--bara-ra]

Utdata i semantik/ut/<klipp>/: ordtider_ra.json (Whispers ord, oberoende av modellens text) och, om semantik.json finns, ordtider.json i ordtider.json-formatet
(model, language, audio, seconds, match_ratio, words, lines[{i, speaker, text, start, end, words}]) med extrafält (stodd, tackning, ursprung).
"""
import argparse
import difflib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sem_gemensamt import SCEN, ladda, skriv, klipp_vagar, norm_ord  # noqa: E402

MODELLER = {
    'kb-medium': SCEN / '3d/cache/whisper/models--KBLab--kb-whisper-medium',
    'kb-small': SCEN / '3d/cache/whisper/models--KBLab--kb-whisper-small',
    'systran-small': SCEN / 'cache/whisper/models--Systran--faster-whisper-small',
}
LIKHET_MIN = 0.7          # oskarp ordjämförelse: minsta teckenlikhet för att två ord räknas som samma
TACKNING_MIN = 0.5        # replik utan minst så stor andel hörda ord flaggas
MAX_SEK_PER_ORD = 0.8     # träffarna får inte spridas över mer än 3 s + 0,8 s per replikord


def snapshot(namn):
    d = MODELLER[namn] / 'snapshots'
    c = sorted(p for p in d.glob('*') if (p / 'model.bin').exists()) if d.exists() else []
    return c[-1] if c else None


def valj_modell(val, sprak):
    if val != 'auto':
        if snapshot(val) is None: raise SystemExit(f'Modellen {val} finns inte på disk.')
        return val
    if sprak == 'sv':
        for n in ('kb-medium', 'kb-small'):
            if snapshot(n): return n
    if snapshot('systran-small'): return 'systran-small'          # flerspråkig
    raise SystemExit('Ingen användbar Whisper-modell på disk (inget hämtas).')


def ljud(video):
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-vn', '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
    if not pcm: return None
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768


def transkribera(video, sprak, modellnamn):
    from faster_whisper import WhisperModel
    v = ljud(video)
    if v is None: return dict(modell=None, sprak=None, ord=[], sekunder=0, anm='klippet har inget ljudspår')
    t0 = time.perf_counter()
    m = WhisperModel(str(snapshot(modellnamn)), device='cpu', compute_type='int8')    # sökväg = ingen nedladdning
    segs, info = m.transcribe(v, language=None if sprak in (None, 'okand') else sprak, word_timestamps=True, beam_size=5, vad_filter=False, condition_on_previous_text=False)
    ord_ = [dict(w=w.word.strip(), start=round(w.start, 3), end=round(w.end, 3), p=round(w.probability, 3)) for s in segs for w in s.words]
    return dict(modell=f'{modellnamn} ({snapshot(modellnamn).parents[1].name}, faster-whisper, int8, CPU)', sprak=info.language, sprak_sannolikhet=round(info.language_probability, 3),
                ord=ord_, sekunder=round(time.perf_counter() - t0, 1), ljud_s=round(len(v) / 16000, 2))


def lik(a, b):
    if a == b: return 1.0
    if not a or not b: return 0.0
    r = difflib.SequenceMatcher(a=a, b=b).ratio()
    return r if r >= LIKHET_MIN else 0.0


def justera(rader, ord_):
    """Kopplar replikerna (ordnade; dict med id och text) till Whisper-orden. Returnerar en post per replik och orden ingen replik förklarar.
    Post: id, stodd, tackning, start_s, slut_s, ord[{ord, start_s, slut_s, sannolikhet, horde}], skal."""
    tok = [(i, w, norm_ord(w)) for i, r in enumerate(rader) for w in r['text'].split()]
    tok = [t for t in tok if t[2]]
    hw = [norm_ord(o['w']) for o in ord_]
    n, m = len(tok), len(hw)
    dp = np.zeros((n + 1, m + 1))
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = lik(tok[i - 1][2], hw[j - 1])
            dp[i, j] = max(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1] + s if s else -1)
    par = {}; i, j = n, m
    while i > 0 and j > 0:
        s = lik(tok[i - 1][2], hw[j - 1])
        if s and abs(dp[i, j] - (dp[i - 1, j - 1] + s)) < 1e-9: par[i - 1] = j - 1; i -= 1; j -= 1
        elif dp[i, j] == dp[i - 1, j]: i -= 1
        else: j -= 1
    anvanda = set(par.values())
    res = []
    for ri, r in enumerate(rader):
        mine = [k for k, t in enumerate(tok) if t[0] == ri]
        hort = [k for k in mine if k in par]
        ordtid = [None] * len(mine)
        for a, k in enumerate(mine):
            if k in par: o = ord_[par[k]]; ordtid[a] = (o['start'], o['end'], o['p'])
        tack = len(hort) / len(mine) if mine else 0.0
        stodd, skal = True, None
        if not mine: stodd, skal = False, 'repliken har inga ord'
        elif tack < TACKNING_MIN: stodd, skal = False, f'Whisper hörde {len(hort)} av {len(mine)} ord (täckning {tack:.0%} under {TACKNING_MIN:.0%})'
        else:
            a = min(ord_[par[k]]['start'] for k in hort); b = max(ord_[par[k]]['end'] for k in hort)
            if b - a > 3 + MAX_SEK_PER_ORD * len(mine): stodd, skal = False, f'träffarna är utspridda över {b - a:.1f} s för {len(mine)} ord'
        if not stodd:
            res.append(dict(id=r['id'], stodd=False, tackning=round(tack, 3), start_s=None, slut_s=None, ord=[], skal=skal)); continue
        # saknade ord: mellan grannarna (som ordtider.py:manusord)
        for a in range(len(mine)):
            if ordtid[a] is None:
                fo = next((ordtid[x][1] for x in range(a - 1, -1, -1) if ordtid[x]), None)
                ef = next((ordtid[x][0] for x in range(a + 1, len(mine)) if ordtid[x]), None)
                fo = fo if fo is not None else ef; ef = ef if ef is not None else fo
                ordtid[a] = (fo, max(fo, ef), None, False)
        ordut = [dict(ord=tok[k][1], start_s=round(ordtid[a][0], 3), slut_s=round(ordtid[a][1], 3), sannolikhet=ordtid[a][2], horde=k in par) for a, k in enumerate(mine)]
        res.append(dict(id=r['id'], stodd=True, tackning=round(tack, 3), start_s=ordut[0]['start_s'], slut_s=ordut[-1]['slut_s'], ord=ordut, skal=None))
    # Whisper-ord som ingen stödd replik förklarar
    stodda = {r['id'] for r in res if r['stodd']}
    forklarade = {par[k] for k, t in enumerate(tok) if k in par and rader[t[0]]['id'] in stodda}
    okl = [j for j in range(m) if j not in forklarade]
    spann, cur = [], []
    for j in okl:
        if cur and (j != cur[-1] + 1): spann.append(cur); cur = []
        cur.append(j)
    if cur: spann.append(cur)
    oforklarat = [dict(start_s=ord_[s[0]]['start'], slut_s=ord_[s[-1]]['end'], text=' '.join(ord_[j]['w'] for j in s)) for s in spann if len(s) >= 3]
    return res, oforklarat


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('klipp'); a.add_argument('--sprak'); a.add_argument('--modell', default='auto'); a.add_argument('--bara-ra', action='store_true')
    a.add_argument('--semantik', help='semantik.json (standard: ut/<klipp>/semantik.json)')
    x = a.parse_args()
    v = klipp_vagar(x.klipp); ut = v['ut']; ut.mkdir(parents=True, exist_ok=True)
    sem_fil = Path(x.semantik) if x.semantik else ut / 'semantik.json'
    sem = ladda(sem_fil) if sem_fil.exists() else None
    sprak = x.sprak or (sem['data']['klipp']['sprak'] if sem else None)
    ra_fil = ut / 'ordtider_ra.json'
    if ra_fil.exists():
        ra = ladda(ra_fil); print('använder', ra_fil, '(ta bort filen för att köra om)')
    else:
        namn = valj_modell(x.modell, sprak)
        print(f'Whisper {namn}, språk {sprak or "autodetektera"} ...', flush=True)
        ra = transkribera(v['video'], sprak, namn)
        ra['klipp'] = x.klipp; ra['ljud'] = str(v['video'].relative_to(SCEN.parent)).replace('\\', '/')
        skriv(ra_fil, ra)
    print(f'{len(ra["ord"])} ord, {ra.get("sekunder")} s, modell {ra["modell"]}, språk {ra["sprak"]}')
    if x.bara_ra or not sem: return
    rader = sorted(sem['data']['repliker'], key=lambda r: (r['start_s'], r['slut_s']))
    res, ofork = justera(rader, ra['ord'])
    lines = []
    for i, (r, j) in enumerate(zip(rader, res)):
        lines.append(dict(i=i, id=r['id'], speaker=r['talare'], text=r['text'], est_start=r['start_s'], est_end=r['slut_s'],
                          start=j['start_s'], end=j['slut_s'], stodd=j['stodd'], tackning=j['tackning'], skal=j['skal'],
                          words=[dict(w=o['ord'], start=o['start_s'], end=o['slut_s'], p=o['sannolikhet'], horde=o['horde']) for o in j['ord']]))
    stodda = [l for l in lines if l['stodd']]
    ut_ = dict(model=ra['modell'], language=ra['sprak'], audio=ra['ljud'], seconds=ra['sekunder'],
               match_ratio=round(sum(l['tackning'] for l in lines) / len(lines), 3) if lines else None,
               words=ra['ord'], lines=lines, tal_utan_replik=ofork,
               ursprung={'typ': 'lokal_whisper', 'not': 'Tider och orden är Whispers. Texten (text) och talaren är modellens och oprövad mot en människa. Repliker med stodd=false hördes inte och har inga tider.'})
    skriv(ut / 'ordtider.json', ut_)
    print(f'{len(stodda)} av {len(lines)} repliker stödda av ljudet; {len(ofork)} spann tal utan replik')
    for l in lines:
        print(f'  {l["id"]} {l["speaker"]} {"" if l["stodd"] else "EJ STÖDD "}täckning {l["tackning"]:.0%} {l["start"]}-{l["end"]}  {l["text"][:70]}')
    for o in ofork: print(f'  tal utan replik {o["start_s"]}-{o["slut_s"]}: {o["text"][:80]}')


if __name__ == '__main__':
    main()
