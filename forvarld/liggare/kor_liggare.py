"""0031: kör liggarprompten (prompt_liggare.md) mot en modell via gatewayen, så att steget går att köra om vid ingest.

  scen/.venv/Scripts/python.exe forvarld/liggare/kor_liggare.py <kalla.json> <ut-liggare.json> [--modell google/gemini-2.5-flash] [--bara-underlag <fil>]
Underlaget: källans personer, scener, props, skärmtext, handlingsspår (kort) och relevanslista, ingestens kontaktblad (brief/kontakt_S*.jpg
eller relevanssteget kontaktblad), regi-operationerna och liggarschemat. --bara-underlag skriver prompten med underlag utan att anropa
(för en stark modell som körs för hand, eller ett paket). Nyckeln läses ur AI_GATEWAY_NYCKELFIL och skrivs aldrig ut.
"""
import argparse, base64, json, os, sys, time, urllib.request
from pathlib import Path

DIR = Path(__file__).resolve().parent; ROOT = DIR.parents[1]; KON = ROOT / 'scen/3d/kontrakt'; ING = ROOT / 'scen/3d/ingest/ut'
GATEWAY = 'https://ai-gateway.vercel.sh/v1/chat/completions'
OPS = """- ta_bort_handling {scen, segment}: remove an action-track segment (crossfade over it)
- tempo_handling {scen, segment, faktor}: play a segment slower (>1) or faster (<1)
- upprepa_handling {scen, fran, till, antal}: play a run of segments again
- satt_frihetsgrad {scen, frihetsgrad, parameter, varde, rutor, mal}: execute a degree of freedom in 3D (today: parameter kroppsdel = mirror the arm and IK to the same targets)
- byt_prop {scen, prop, ny_typ}: swap a prop (a held object becomes a placeholder of the new type)
- ta_bort_prop {scen, prop}: remove a prop or piece of furniture
- renderkamera {scen, kamera_id, lage: stativ}: a still camera
- trimma_scen {scen, slut_s, lage: hall_sista}: extend the end by holding the last frame
- flytta_scen {scen, efter}: move a shot (efter null = first)
- ta_bort_scen {scen}: remove a shot
- byt_miljo {scen, rum}: swap the room for a template in the bank (only templates that exist)"""


def underlag(kf):
    K = json.loads(Path(kf).read_text(encoding='utf-8')); s = K['semantik']
    hand = [dict(scen=h['scen'], segment=[{k: (g.get(k) or {}).get('varde') if isinstance(g.get(k), dict) else g.get(k) for k in ('id', 'vem', 'rutor', 'tid_s', 'hallning', 'handling', 'kroppsdel', 'foremal', 'i_handen', 'mal', 'blick', 'kontakt', 'beskrivning')} for g in h['segment']]) for h in s.get('handling', [])]
    u = dict(klipp=K['klipp']['id'], tidsbas=K['tidsbas'], personer=s['personer'], scener=[{k: x.get(k) for k in ('id', 'start_s', 'slut_s', 'funktion', 'syfte', 'personer')} for x in s['scener']],
             props=[{k: p.get(k) for k in ('id', 'typ', 'etikett', 'stod', 'deklaration')} for p in s['props']], skarmtext=[{k: t.get(k) for k in ('id', 'scen', 'text', 'start_s', 'slut_s')} for t in s['skarmtext']],
             handlingsspar=hand, relevans=s.get('relevans'), scenbygge=[dict(scen=b['scen'], objekt=[o['id'] for o in b['objekt']]) for b in K['matning'].get('scenbygge', [])],
             rutor_regel='frames are source frames [first, last+1) at the clip fps; scene s<n> spans its start_s..slut_s')
    return u


def kontaktblad(kf):
    K = json.loads(Path(kf).read_text(encoding='utf-8')); kam = K['matning']['kameror'][0]['spar_metrisk']['sokvag']
    klipp = (Path(kf).parent / kam).resolve().parent.parent.name
    b = sorted((ING / klipp / 'brief').glob('kontakt_S*.jpg')) or sorted((ROOT / 'scen/3d/gennedbrytning/relevans' / klipp / 'kontakt').glob('kontakt_S*.jpg'))
    return b


def main():
    a = argparse.ArgumentParser(); a.add_argument('kalla'); a.add_argument('ut'); a.add_argument('--modell', default='google/gemini-2.5-flash'); a.add_argument('--bara-underlag'); x = a.parse_args()
    mall = (DIR / 'prompt_liggare.md').read_text(encoding='utf-8').split('---', 1)[1]
    text = mall.replace('{underlag}', json.dumps(underlag(x.kalla), ensure_ascii=False, indent=1)).replace('{operationer}', OPS).replace('{schema}', (KON / 'liggare.schema.json').read_text(encoding='utf-8'))
    bilder = kontaktblad(x.kalla)
    if x.bara_underlag: Path(x.bara_underlag).write_text(text + '\n\nIMAGES: ' + ', '.join(str(b) for b in bilder), encoding='utf-8'); print('underlag', x.bara_underlag); return
    inn = [dict(type='text', text=text)] + [c for f in bilder for c in (dict(type='text', text=f'Contact sheet {f.stem}:'), dict(type='image_url', image_url=dict(url='data:image/jpeg;base64,' + base64.b64encode(f.read_bytes()).decode())))]
    body = dict(model=x.modell, max_tokens=32000, messages=[dict(role='user', content=inn)], response_format=dict(type='json_object'))
    k = os.environ.get('AI_GATEWAY_API_KEY') or Path(os.environ['AI_GATEWAY_NYCKELFIL']).read_text(encoding='utf-8').splitlines()[0].strip()
    t = time.time(); req = urllib.request.Request(GATEWAY, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=900)); svar = d['choices'][0]['message']['content']; s = round(time.time() - t, 1)
    L = json.loads(svar.strip().removeprefix('```json').removesuffix('```'))
    ut = Path(x.ut); ut.write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding='utf-8')
    ut.with_suffix('.anrop.json').write_text(json.dumps(dict(modell=x.modell, usage=d.get('usage'), sekunder=s, bilder=[b.name for b in bilder]), ensure_ascii=False, indent=1), encoding='utf-8')
    print(x.modell, 'sekunder', s, 'kostnad', (d.get('usage') or {}).get('cost'))


if __name__ == '__main__': main()
