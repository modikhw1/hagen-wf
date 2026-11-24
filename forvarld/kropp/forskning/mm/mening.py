"""FORSKNING (0044, ägarens prov 16 nov): en fri mening -> villkor för MaskedMimic -> ny helkroppsrörelse, för vilken tagning som helst.

Förståndet (en språkmodell) skriver inte rörelsen. Det skriver hur målen för högst sex kroppar (Pelvis, L_Ankle, R_Ankle, L_Hand,
R_Hand, Head) ändras kring originalets rörelse, och vilka av dem som binds. MaskedMimic (AMASS-tränad, icke-kommersiell) fyller i
resten av kroppen i en fysiksimulering. Sedan mäts utfallet, och förståndet får måtten och får justera (--varv).

  scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/mening.py "<mening>" <namn>
      [--kalla <kalla.json> --liggare <liggare.json> --scen s1 --person A]     förval: gelato s1 A
      [--varv 2] [--torr] [--recept <fil.json>] [--utan-film]
Ger ut/mening_<namn>/: recept_v<n>.json, mm_v<n>.npz, matt_v<n>.json, sekvens.npz (MHR, kedjans format), streck.mp4 och streck_blad.png.
Allt är märkt licens: forskning. Tjänsten (tjanst.py) måste vara utplacerad.
"""
import json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
import numpy as np
HIT = Path(__file__).resolve().parent; ROOT = HIT.parents[3]
sys.path.insert(0, str(HIT)); import mhr_smpl as M, tagning as TG
RAMP = 8
KROPPAR = ('Pelvis', 'L_Ankle', 'R_Ankle', 'L_Hand', 'R_Hand', 'Head')
FORVAL = dict(kalla='kand-kennysgelato_n06-hand/kalla_0033.json', liggare='kand-kennysgelato_n06-hand/liggare_0033.json', scen='s1', person='A')
VIA = os.environ.get('FORSTAND_VIA', 'beacon'); BEACON = os.environ.get('FORSTAND_BEACONMODELL', 'gemini-3.5-flash'); GEMINI = os.environ.get('FORSTAND_MODELL', 'gemini-3-flash-preview')
CODEX = os.environ.get('FORSTAND_CODEXMODELL', 'gpt-5.6-sol'); EFFORT = os.environ.get('FORSTAND_EFFORT', 'medium')

_S, _N, _I = {'type': 'string'}, {'type': 'number'}, {'type': 'integer'}
SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['beskrivning', 'arver', 'villkor', 'andringar', 'forvantat', 'bedomning', 'fardig'],
          'properties': {'beskrivning': _S, 'arver': _S, 'forvantat': {'type': 'array', 'items': _S}, 'bedomning': _S, 'fardig': {'type': 'boolean'},
                         'villkor': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'required': ['kropp', 'tillstand'],
                                                                'properties': {'kropp': {'type': 'string', 'enum': list(KROPPAR)}, 'tillstand': _I}}},
                         'andringar': {'type': 'array', 'items': {
                             'type': 'object', 'additionalProperties': False,
                             'required': ['kropp', 'typ', 'ruta_fran', 'ruta_till', 'fram_cm', 'vanster_cm', 'upp_cm', 'faktor', 'fordroj_rutor', 'vrid_grader', 'nick_grader', 'kalla_kropp', 'skal'],
                             'properties': {'kropp': {'type': 'string', 'enum': list(KROPPAR)}, 'typ': {'type': 'string', 'enum': ['forskjut', 'skala', 'fordroj', 'hall', 'ta_fran', 'tempo', 'vrid']},
                                            'ruta_fran': _I, 'ruta_till': _I, 'fram_cm': _N, 'vanster_cm': _N, 'upp_cm': _N, 'faktor': _N, 'fordroj_rutor': _I, 'vrid_grader': _N, 'nick_grader': _N,
                                            'kalla_kropp': _S, 'skal': _S}}}}}

REGLER = """Du översätter en regimening till villkor för en fysikbaserad rörelsemodell (MaskedMimic). Kör inga kommandon. Svara bara med JSON enligt schemat.

Modellen har originalets rörelse som referens. Den kan bindas till mål för högst sex kroppar: Pelvis, L_Ankle, R_Ankle, L_Hand, R_Hand, Head.
Allt annat (knän, höfter, ryggrad, axlar, armbågar) fyller modellen i själv så att kroppen håller balansen och ser mänsklig ut.
Du skriver alltså inte rörelsen. Du säger vilka kroppar som binds, och hur deras mål avviker från originalet. Kroppen räknar ut resten.

TÄNK I PRIORITERINGAR, INTE I ETIKETTER. "Haltar" är inte en etikett: det är att ett ben skyddas, så foten får kortare tid i marken, lyfts mindre, och bäckenet lutar över det friska benet. "Trött" är att bäckenet sjunker, huvudet hänger och handen kommer sent. Fråga vad personen prioriterar och vad det gör med de sex kropparna.

VILLKOR: listan över kroppar som binds. tillstand 0 = bara position, 1 = position och rotation, 2 = bara rotation. Position (0) följs bäst.
- En kropp som inte står i listan är FRI: den följer inte originalet, modellen hittar på vad den gör. Bind därför den kroppsdel som utför händelserna, annars försvinner handlingen. En fri arm kan hamna var som helst: bind den i position om den ska bete sig som i originalet.
- Bind inte mer än så, för det som är bundet kan inte kompensera.
- Fötterna (L_Ankle, R_Ankle) bundna med 0 håller personen på platsen. Släpp dem om personen ska få flytta sig eller ta ett steg.
- Bäckenet (Pelvis) bundet låser tyngdpunkten. Släpp det om kroppen ska få kompensera med hela sin tyngd.

ÄNDRINGAR: hur målet för en bunden kropp avviker från originalet, i ett rutintervall. Riktningarna är personens egna: fram (dit personen är vänd), vänster, upp. Centimeter.
- forskjut: flytta målet med fram_cm, vanster_cm, upp_cm under intervallet. Mjuk in- och utgång.
- skala: gör kroppens rörelse större eller mindre kring sitt medelläge i intervallet. faktor 0.5 = halva rörelsen, 1.5 = större.
- fordroj: målet kommer fordroj_rutor senare (positivt) eller tidigare (negativt) än i originalet.
- hall: håll kroppen kvar där den var i intervallets första ruta.
- tempo: kroppen gör intervallets rörelse fortare eller långsammare. faktor 1.5 = en och en halv gång så fort, och då är den klar tidigt och väntar i slutläget; faktor 0.6 = långsammare, och då hinner den inte hela rörelsen. Använd för brådska, tvekan eller lugn. Lägg samma tempo på de kroppar som ska röra sig ihop.
- ta_fran: kroppen får en annan kropps bana i intervallet. kalla_kropp = kroppen vars bana tas (till exempel L_Hand tar R_Hand: vänster hand gör det höger gjorde). Den andra handen får då inte också vara bunden till samma bana: ge den en egen ändring eller släpp den.
- vrid (bara Head): huvudet vrids i förhållande till originalet under intervallet. vrid_grader = sidled, positivt åt vänster, negativt åt höger (högst 80). nick_grader = positivt nedåt, negativt uppåt (högst 45). Använd för blick och uppmärksamhet: att titta bort, titta ner, vända sig mot någon. Att flytta huvudet med forskjut vrider det inte. Huvudet binds då i position och rotation automatiskt; ge det ingen forskjut samtidigt om inte meningen kräver det.
Fält som inte används sätts till 0 eller tom sträng. skal: en kort mening om varför just den ändringen uttrycker meningen.
Håll ändringarna måttliga: högst 30 cm förskjutning, faktor mellan 0.3 och 1.8, högst 30 rutors fördröjning. Hellre tre tydliga ändringar än tio små.
Det som inte nämns ska stå kvar som i originalet: handlingen (vad personen gör, mot vem, när) ärvs.

beskrivning: hur kroppen ska se ut efteråt, två meningar. arver: vad som står kvar. forvantat: två till fyra saker en betraktare ska kunna se om det lyckades.
bedomning och fardig används i senare varv. I första varvet: bedomning tom, fardig false."""

VARV = """DETTA ÄR VARV {n}. Ditt förra recept kördes genom kroppen. Här är receptet och vad som mättes.
FÖRRA RECEPTET: {recept}
MÅTT: {matt}
Så läser du måtten: andel_av_andringen är det viktigaste: hur stor del av din begärda ändring som faktiskt blev av för varje ändrad kropp (1.0 = hela, 0 = ingenting hände, negativt = åt fel håll). Under 0.5 betyder att meningen INTE syns i kroppen, oavsett vad övriga mått säger: då är du inte färdig. Pröva då att släppa det som håller emot (bäcken, huvud, den andra handen), att göra ändringen större, eller en annan sorts ändring. bundna_till_mal_cm är hur nära varje bunden kropp kom sitt mål (under 12 är bra, över 25 betyder att kroppen inte kunde eller ville). handelser_cm är samma sak under varje händelse i liggaren. mot_originalet_cm visar hur mycket varje kropp avviker från originalet: där din ändring ska synas ska det vara stort, och annars litet. star=false betyder att personen föll. fotvag_cm är hur långt fötterna vandrade.
Skriv i bedomning, i två meningar, om avsikten med meningen syns i måtten och vad som gick sönder. Justera sedan receptet: större eller mindre förskjutning, bind eller släpp en kropp, flytta ett intervall. Om utfallet redan uttrycker meningen utan att handlingen gått förlorad: lämna receptet oförändrat och sätt fardig true."""


def ram(S):
    upp = np.array([0., 0., 1.]); v = np.median(S[:, TG.ix('L_Hip')] - S[:, TG.ix('R_Hip')], axis=0); v[2] = 0; v /= np.linalg.norm(v)
    return np.cross(v, upp), v, upp


def beskriv(t, ref):
    S = ref['S']; fr, va, up = ram(S); R = np.stack([fr, va, up]); p0 = S[0, 0]
    rader = [f"TAGNINGEN: {t['beskrivning']}", f"REFERENSEN: {len(S)} rutor i {t['fps']:.2f} rutor per sekund ({len(S) / t['fps']:.1f} s)."]
    if ref['beslut']: rader.append('Antaganden i referensen: ' + ' '.join(f"{b['atgard']}, eftersom {b['skal']}." for b in ref['beslut']))
    rader.append('Händelser (ur liggaren): ' + ('; '.join(f"{h['id']} {h['ram']} rutor {h['rutor'][0]}–{h['rutor'][1]}" + (f" med {h['kropp']}" if h['kropp'] else '')
                                                         + (f" ({', '.join(f'{k}: {v}' for k, v in h['roller'].items() if k != 'kroppsdel')})" if h['roller'] else '') for h in t['handelser']) or 'inga') + '.')
    rader.append('Kropparna i personens riktningar, cm från bäckenets läge i ruta 0 (fram, vänster, upp), och hur mycket de rör sig:')
    for k in KROPPAR:
        q = (S[:, TG.ix(k)] - p0) @ R.T * 100
        rader.append(f"- {k}: start ({q[0][0]:.0f}, {q[0][1]:.0f}, {q[0][2]:.0f}); spann fram {np.ptp(q[:, 0]):.0f}, vänster {np.ptp(q[:, 1]):.0f}, upp {np.ptp(q[:, 2]):.0f}"
                     + ''.join(f"; vid {h['id']} ({q[h['rutor'][0]:h['rutor'][1], 0].mean():.0f}, {q[h['rutor'][0]:h['rutor'][1], 1].mean():.0f}, {q[h['rutor'][0]:h['rutor'][1], 2].mean():.0f})" for h in t['handelser'][:6]))
    return '\n'.join(rader)


def _utan_extra(s):
    if isinstance(s, dict): return {k: _utan_extra(v) for k, v in s.items() if k != 'additionalProperties'}
    return [_utan_extra(x) for x in s] if isinstance(s, list) else s


def fraga(prompt, ut, varv):
    """Gemini direkt (cirka 3 s, svajar) och annars codex exec (15-35 s). Ger (svar, sekunder, väg)."""
    (ut / f'prompt_v{varv}.txt').write_text(prompt, encoding='utf-8'); t0 = time.time()
    if VIA in ('beacon', 'gemini'):   # bryggan till Google Cloud (token-budget-beacon): stabil, cirka 2 s, bråkdelar av ett öre per anrop
        try:
            env = {r.split('=', 1)[0]: r.split('=', 1)[1].strip() for r in (ROOT / 'video/.env.local').read_text(encoding='utf-8').splitlines() if '=' in r and not r.startswith('#')}
            if VIA == 'beacon' and env.get('BEACON_NYCKEL'):
                body = {'model': BEACON, 'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                        'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json', 'responseJsonSchema': SCHEMA, 'thinkingConfig': {'thinkingLevel': os.environ.get('FORSTAND_TANK', 'low')}}}
                req = urllib.request.Request(env.get('BEACON_URL') or 'https://token-budget-beacon.lovable.app/api/public/v1/generate', data=json.dumps(body).encode(),
                                             headers={'authorization': 'Bearer ' + env['BEACON_NYCKEL'], 'content-type': 'application/json'})
                with urllib.request.urlopen(req, timeout=60) as r: j = json.loads(r.read())
                return json.loads(''.join(p.get('text', '') for p in j['candidates'][0]['content']['parts'] if not p.get('thought'))), round(time.time() - t0, 1), BEACON
        except Exception as e:
            print(f'  (bryggan svarade inte: {type(e).__name__} {str(e)[:80]}; går över till gratisnivån)', flush=True)
    if VIA in ('beacon', 'gemini'):
        try:
            nyckel = next(r.split('=', 1)[1].strip() for r in (ROOT / 'video/.env.local').read_text(encoding='utf-8').splitlines() if r.startswith('GEMINI_API_KEY_GRATIS='))
            body = {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                    'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': _utan_extra(SCHEMA), 'temperature': 0.2, 'thinkingConfig': {'thinkingLevel': os.environ.get('FORSTAND_TANK', 'low')}}}
            req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI}:generateContent', data=json.dumps(body).encode(),
                                         headers={'Content-Type': 'application/json', 'x-goog-api-key': nyckel})
            for forsok in range(3):   # gratisnivån svarar ofta 503 i första försöket
                try:
                    with urllib.request.urlopen(req, timeout=25) as r: j = json.loads(r.read())
                    break
                except Exception:
                    if forsok == 2: raise
                    time.sleep(1.5)
            return json.loads(''.join(p.get('text', '') for p in j['candidates'][0]['content']['parts'] if not p.get('thought'))), round(time.time() - t0, 1), GEMINI
        except Exception as e:
            print(f'  (gemini svarade inte: {type(e).__name__}; går över till codex)', flush=True)
    tom = ut / 'tom'; tom.mkdir(exist_ok=True); (ut / 'schema.json').write_text(json.dumps(SCHEMA), encoding='utf-8'); sf = ut / 'svar.txt'; sf.unlink(missing_ok=True)
    p = subprocess.run([shutil.which('codex'), 'exec', '-m', CODEX, '-c', f'model_reasoning_effort={EFFORT}', '-s', 'read-only', '--skip-git-repo-check', '--ephemeral',
                        '-C', str(tom), '--output-schema', str(ut / 'schema.json'), '-o', str(sf), '-'], input=prompt.encode('utf-8'), capture_output=True, timeout=300)
    text = sf.read_text(encoding='utf-8') if sf.exists() else ''
    if not text.strip(): sys.exit('förståndet svarade inte: ' + p.stderr.decode('utf-8', 'replace')[-300:])
    return json.JSONDecoder().raw_decode(text[text.index('{'):])[0], round(time.time() - t0, 1), CODEX


def vikt(n, a, b):
    w = np.zeros(n); a, b = max(0, a), min(n, b)
    for f in range(n):
        if a <= f < b: w[f] = 1
        elif a - RAMP <= f < a: w[f] = (f - a + RAMP) / RAMP
        elif b <= f < b + RAMP: w[f] = 1 - (f - b + 1) / RAMP
    return w[:, None]


def mal_ur(recept, S):
    """Målbanor för de kroppar receptet ändrar. Ger namn, mal (T,k,3), vikt (T,k) och vad som klipptes."""
    fr, va, up = ram(S); n = len(S); klippt = []; banor = {}

    def kl(x, lo, hi, vad):
        y = min(hi, max(lo, x))
        if y != x: klippt.append(f'{vad}: {x} -> {y}')
        return y
    for a in recept['andringar']:
        if a['typ'] == 'vrid': continue   # vridning bärs av rotationsmålet (vrid_G), inte av positionsmålen
        j = TG.ix(a['kropp']); ref = S[:, j]; mal = banor.setdefault(a['kropp'], ref.copy()); w = vikt(n, a['ruta_fran'], a['ruta_till'])
        i0 = max(0, min(n - 2, a['ruta_fran'])); i1 = max(i0 + 1, min(n, a['ruta_till']))
        if a['typ'] == 'forskjut':
            mal += w * (fr * kl(a['fram_cm'], -40, 40, 'fram_cm') + va * kl(a['vanster_cm'], -40, 40, 'vanster_cm') + up * kl(a['upp_cm'], -40, 40, 'upp_cm')) / 100
        elif a['typ'] == 'skala':
            mal += w * (kl(a['faktor'], 0.0, 2.0, 'faktor') - 1) * (ref - ref[i0:i1].mean(0))
        elif a['typ'] == 'fordroj':
            d = int(kl(a['fordroj_rutor'], -45, 45, 'fordroj_rutor')); mal += w * (ref[np.clip(np.arange(n) - d, 0, n - 1)] - ref)
        elif a['typ'] == 'hall':
            mal += w * (ref[i0] - ref)
        elif a['typ'] == 'tempo':   # kroppen gör intervallets rörelse fortare (faktor över 1: klar tidigt, väntar sedan) eller långsammare (under 1: hinner inte hela)
            f = kl(a['faktor'], 0.4, 2.5, 'faktor'); tt = np.clip(i0 + (np.arange(n) - i0) * f, i0, i1 - 1); lo = np.floor(tt).astype(int); hi = np.minimum(lo + 1, n - 1); fr_ = (tt - lo)[:, None]
            mal += w * ((1 - fr_) * ref[lo] + fr_ * ref[hi] - ref)
        elif a['typ'] == 'ta_fran':
            if a.get('kalla_kropp') in M.SN: mal += w * (S[:, TG.ix(a['kalla_kropp'])] - ref)
            else: klippt.append(f"ta_fran: okänd kalla_kropp {a.get('kalla_kropp')!r}, hoppad")
    namn = sorted(banor)
    return namn, (np.stack([banor[k] for k in namn], 1) if namn else np.zeros((n, 0, 3))), np.ones((n, len(namn))), klippt


VRID_ANDEL = (('Neck', 0.4), ('Head', 1.0))   # global vridning per kropp: nacken tar en del, huvudet hela


def vrid_G(recept, ref):
    """Referensens globala rotationer med receptets huvudvridningar (typ vrid). Ger G och vad som klipptes.
    Vridningen sker kring personens egna axlar: upp (positivt = åt vänster) och vänster (positivt = nedåt)."""
    from scipy.spatial.transform import Rotation as Ro
    S = ref['S']; G = ref['G'].copy(); n = len(G); _, va, up = ram(S); klippt = []
    for a in recept['andringar']:
        if a['typ'] != 'vrid': continue
        if a['kropp'] != 'Head': klippt.append(f"vrid på {a['kropp']}: bara Head kan vridas, hoppad"); continue
        yaw = float(np.clip(a.get('vrid_grader', 0) or 0, -80, 80)); pit = float(np.clip(a.get('nick_grader', 0) or 0, -45, 45))
        if (yaw, pit) != (a.get('vrid_grader', 0) or 0, a.get('nick_grader', 0) or 0): klippt.append(f'vrid: {a.get("vrid_grader")}/{a.get("nick_grader")} -> {yaw}/{pit}')
        w = vikt(n, a['ruta_fran'], a['ruta_till'])[:, 0]; ax = up * np.radians(yaw) + va * np.radians(pit)
        for kropp, andel in VRID_ANDEL:
            G[:, TG.ix(kropp)] = Ro.from_rotvec(w[:, None] * andel * ax[None]).as_matrix() @ G[:, TG.ix(kropp)]
    return G, klippt


def vrid_andel(q, ref, G2, k):
    """Hur stor del av den begärda huvudvridningen som blev av, i sidled och nick (som andel_av_andringen)."""
    from scipy.spatial.transform import Rotation as Ro
    _, va, up = ram(ref['S']); j = TG.ix('Head'); G0 = ref['G'][1:1 + k, j]
    beg = Ro.from_matrix(G2[1:1 + k, j] @ np.transpose(G0, (0, 2, 1))).as_rotvec(); fakt = (Ro.from_quat(q[:, j]) * Ro.from_matrix(G0).inv()).as_rotvec(); ut = {}
    for etikett, axel in (('Head_vrid', up), ('Head_nick', va)):
        b, f = beg @ axel, fakt @ axel; stor = np.abs(b) > np.radians(5)
        if stor.sum() >= 3: ut[etikett] = round(float(np.median(f[stor] / b[stor])), 2)
    return ut


def matt(mm, t, ref, namn, mal, recept, sigma=1.0):
    """Mått i SMPL-rummet, efter utjämning: hur nära de bundna kom sina mål, per händelse, och avvikelsen från originalet."""
    S = ref['S']; P, Qr, k, dt = TG.las_utfall(mm, S, sigma); R = S[1:1 + k]; bundna = [v['kropp'] for v in recept['villkor']]
    cm = lambda a, b: round(float(np.median(np.linalg.norm(a - b, axis=-1))) * 100, 1)
    malbana = lambda b: mal[1:1 + k, namn.index(b)] if b in namn else R[:, TG.ix(b)]
    ut = {'steg': k, 'star': bool(P[:, 0, 2].min() > np.median(R[:, 0, 2]) - 0.3), 'lagsta_backen_m': round(float(P[:, 0, 2].min()), 2),
          'bundna_till_mal_cm': {b: cm(P[:, TG.ix(b)], malbana(b)) for b in bundna}, 'handelser_cm': {}, 'mot_originalet_cm': {}}
    for h in t['handelser']:
        a, b = max(0, h['rutor'][0] - 1), min(k, h['rutor'][1] - 1)
        if b - a < 3: continue
        for kropp in ([h['kropp']] if h['kropp'] else []) + [x for x in ('L_Hand', 'R_Hand') if x in namn and x != h['kropp']]:
            ut['handelser_cm'][f"{h['id']}_{h['ram']}_{kropp}"] = {'till_mal': cm(P[a:b, TG.ix(kropp)], malbana(kropp)[a:b]), 'mot_originalet': cm(P[a:b, TG.ix(kropp)], R[a:b, TG.ix(kropp)])}
    # Hur mycket av den begärda ändringen blev av: kroppens faktiska förflyttning från originalet, mätt längs den begärda riktningen.
    # 1.0 = hela ändringen, 0 = ingenting hände, negativt = åt fel håll. Det här måttet går inte att läsa fel, till skillnad från avstånden.
    ut['andel_av_andringen'] = {}
    for i, b in enumerate(namn):
        beg = mal[1:1 + k, i] - R[:, TG.ix(b)]; stor = np.linalg.norm(beg, axis=1) > 0.03
        if stor.sum() >= 3:
            fakt = P[stor, TG.ix(b)] - R[stor, TG.ix(b)]; ut['andel_av_andringen'][b] = round(float(np.median((fakt * beg[stor]).sum(1) / (beg[stor] ** 2).sum(1))), 2)
    if any(a['typ'] == 'vrid' for a in recept['andringar']): ut['andel_av_andringen'].update(vrid_andel(Qr, ref, vrid_G(recept, ref)[0], k))
    for b in ('Pelvis', 'Head', 'L_Hand', 'R_Hand', 'L_Ankle', 'R_Ankle', 'L_Knee', 'R_Knee', 'Torso', 'L_Elbow', 'R_Elbow'):
        ut['mot_originalet_cm'][b] = cm(P[:, TG.ix(b)], R[:, TG.ix(b)])
    ryck = lambda X: round(float(np.median(np.linalg.norm(np.diff(X, 3, axis=0), axis=1)) / dt ** 3), 1)
    ut['ryck_m_per_s3'] = {b: {'ny': ryck(P[:, TG.ix(b)]), 'original': ryck(R[:, TG.ix(b)])} for b in ('Pelvis', 'R_Hand', 'Head')}
    ut['fotvag_cm'] = round(sum(float(np.linalg.norm(np.diff(P[:, TG.ix(f), :2], axis=0), axis=1).sum()) for f in ('L_Ankle', 'R_Ankle')) * 50, 1)
    ut['rotens_forflyttning_cm'] = round(float(np.linalg.norm(P[-1, 0, :2] - P[0, 0, :2])) * 100, 1)
    return ut


def kor(recept, t, ref, ut, varv, kor_fn):
    S = ref['S']; n = len(S); namn, mal, w, klippt = mal_ur(recept, S); G2, kv = vrid_G(recept, ref); recept['klippt'] = klippt + kv; bundna = {v['kropp'] for v in recept['villkor']}
    if any(a['typ'] == 'vrid' and a['kropp'] == 'Head' for a in recept['andringar']):   # vridningen bärs av rotationsmålet: huvudet binds i position och rotation
        hv = next((v for v in recept['villkor'] if v['kropp'] == 'Head'), None)
        if hv is None: recept['villkor'].append({'kropp': 'Head', 'tillstand': 1}); bundna.add('Head'); recept.setdefault('tillagt', []).append('Head bunden i position och rotation, eftersom den vrids')
        elif hv['tillstand'] != 1: hv['tillstand'] = 1; recept.setdefault('tillagt', []).append('Head position och rotation, eftersom den vrids')
    for k in namn:
        if k not in bundna: recept['villkor'].append({'kropp': k, 'tillstand': 0}); recept.setdefault('tillagt', []).append(f'{k} bunden, eftersom den har en ändring')
    for a in recept['andringar']:   # en lånad bana binds bara i position (erfarenheter.json)
        if a['typ'] == 'ta_fran':
            for v in recept['villkor']:
                if v['kropp'] == a['kropp'] and v['tillstand'] != 0: v['tillstand'] = 0; recept.setdefault('tillagt', []).append(f"{a['kropp']} bara position, eftersom banan är lånad")
    recept['licens'] = 'forskning'; (ut / f'recept_v{varv}.json').write_text(json.dumps(recept, ensure_ascii=False, indent=1), encoding='utf-8')
    np.savez(ut / 'ref.npz', G=G2.astype(np.float32), rot=ref['rot'].astype(np.float32), fps=t['fps'], mal_namn=np.array(namn), mal=mal.astype(np.float32), mal_vikt=w.astype(np.float32))
    V = json.dumps(dict(diag='officiell', villkor=recept['villkor'], steg=n - 2), ensure_ascii=False); t0 = time.time()
    r = kor_fn.remote((ut / 'ref.npz').read_bytes(), V, (HIT / 'kor_mm.py').read_text(encoding='utf-8'))
    (ut / f'logg_v{varv}.txt').write_text(r['stdout'] + chr(10) + '--- STDERR ---' + chr(10) + r['stderr'], encoding='utf-8')
    if not r['ok']: sys.exit(f"körningen föll; se {ut / f'logg_v{varv}.txt'}")
    mm = ut / f'mm_v{varv}.npz'; mm.write_bytes(r['npz']); m = matt(mm, t, ref, namn, mal, recept); m['kropp_s'] = round(time.time() - t0, 1)
    (ut / f'matt_v{varv}.json').write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')
    return mm, m


def kort(recept):
    return {'villkor': [f"{v['kropp']}:{v['tillstand']}" for v in recept['villkor']],
            'andringar': [' '.join([a['kropp'], a['typ'], f"{a['ruta_fran']}-{a['ruta_till']}"] + [f'{k}={a[k]}' for k in ('fram_cm', 'vanster_cm', 'upp_cm', 'faktor', 'fordroj_rutor', 'vrid_grader', 'nick_grader', 'kalla_kropp') if a.get(k)]) for a in recept['andringar']]}


def main():
    a = sys.argv[1:]; mening, namn_ut = a[0], a[1]; arg = lambda k, d=None: a[a.index('--' + k) + 1] if '--' + k in a else d
    t = TG.las(arg('kalla', FORVAL['kalla']), arg('liggare', FORVAL['liggare']), arg('scen', FORVAL['scen'] if '--kalla' not in a else None), arg('person', FORVAL['person'] if '--kalla' not in a else None))
    ref = TG.referens(t); ut = HIT / 'ut' / f'mening_{namn_ut}'; ut.mkdir(parents=True, exist_ok=True); t0 = time.time(); varv_max = int(arg('varv', 2))
    print(f"TAGNING {t['namn']}: {len(ref['S'])} rutor. Rimlighet före {ref['fore']}"); [print(f"  antagande {b['vad']}: {b['atgard']} ({b['skal']})") for b in ref['beslut']]
    np.savez(ut / 'ref_bas.npz', G=ref['G'].astype(np.float32), rot=ref['rot'].astype(np.float32), fps=t['fps'])
    erf = json.loads((HIT / 'erfarenheter.json').read_text(encoding='utf-8')) if (HIT / 'erfarenheter.json').exists() else []
    erftext = 'ERFARENHETER ur tidigare körningar (mätta; följ dem om inte meningen kräver annat):\n' + '\n'.join(f"- {e['regel']}" for e in erf)
    bas = '\n\n'.join([REGLER, erftext, beskriv(t, ref), f'REGIMENINGEN: "{mening}"']); logg = []; kor_fn = None
    if '--recept' in a: recept, s, via = json.loads(Path(arg('recept')).read_text(encoding='utf-8')), 0, 'fil'
    else: recept, s, via = fraga(bas, ut, 1)
    recept.update(mening=mening, tagning=t['namn'], modell=via, forstand_s=s)
    print(f'VARV 1 recept ({via}, {s} s):', json.dumps(kort(recept), ensure_ascii=False)); print('  ', recept.get('beskrivning', ''))
    if '--torr' in a:
        namn, mal, w, klippt = mal_ur(recept, ref['S']); (ut / 'recept_v1.json').write_text(json.dumps(recept, ensure_ascii=False, indent=1), encoding='utf-8'); print('TORR', ut); return
    import modal; kor_fn = modal.Function.from_name('hagen-mm-tjanst', 'kor'); mm = None
    for varv in range(1, varv_max + 1):
        mm, m = kor(recept, t, ref, ut, varv, kor_fn); logg.append(dict(varv=varv, recept=kort(recept), matt=m, forstand_s=recept.get('forstand_s'), modell=recept.get('modell')))
        print(f"VARV {varv} andel av ändringen: {m['andel_av_andringen']}")
        print(f"VARV {varv} mått ({m['kropp_s']} s): står {m['star']}, bundna {m['bundna_till_mal_cm']}, händelser {m['handelser_cm']}, fotväg {m['fotvag_cm']} cm"); print('   mot originalet:', m['mot_originalet_cm'])
        if varv == varv_max or '--recept' in a: break
        sm = {k: m[k] for k in ('star', 'lagsta_backen_m', 'andel_av_andringen', 'bundna_till_mal_cm', 'handelser_cm', 'mot_originalet_cm', 'fotvag_cm')}
        ny, s, via = fraga(bas + '\n\n' + VARV.format(n=varv + 1, recept=json.dumps({k: recept[k] for k in ('beskrivning', 'villkor', 'andringar', 'forvantat')}, ensure_ascii=False), matt=json.dumps(sm, ensure_ascii=False)), ut, varv + 1)
        print(f'VARV {varv + 1} bedömning ({via}, {s} s):', ny.get('bedomning', '')); logg[-1]['bedomning_efter'] = ny.get('bedomning', '')
        if ny.get('fardig'): print('   förståndet: färdig, receptet står.'); break
        ny.update(mening=mening, tagning=t['namn'], modell=via, forstand_s=s); recept = ny; print(f'VARV {varv + 1} recept:', json.dumps(kort(recept), ensure_ascii=False))
    slut = len(logg); shutil.copy(ut / f'mm_v{slut}.npz', ut / 'mm.npz'); TG.tillbaka(t, ref, ut / 'mm.npz', ut / 'sekvens.npz')
    (ut / 'logg.json').write_text(json.dumps(dict(mening=mening, tagning=t['namn'], kalla=t['kalla'], liggare=t['liggare'], scen=t['scen'], person=t['person'], licens='forskning',
                                                  antaganden=ref['beslut'], rimlighet=dict(fore=ref['fore'], efter=ref['efter']), varv=logg, allt_s=round(time.time() - t0, 1)), ensure_ascii=False, indent=1), encoding='utf-8')
    if '--utan-film' not in a:
        subprocess.run([sys.executable, '-X', 'utf8', str(HIT / 'streck.py'), str(ut / 'streck.mp4'), str(ut / 'ref_bas.npz')] + [f'varv {i}={ut / f"mm_v{i}.npz"}' for i in range(1, slut + 1)], check=False)
    print(f'KLART {ut}  {time.time() - t0:.0f} s, {slut} varv. MHR-sekvens: {ut / "sekvens.npz"}')


if __name__ == '__main__': main()
