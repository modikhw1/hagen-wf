"""Rumsväggar som inte kan blockera kameran (12 nov 2026, problem 4 i GUACAMOLE-LOGG.md).

Rumsmallen `dekl_<klipp>` (ingest/deklaration_till_hand.py `rumsmall`) byggs kring PLATSERNA: golv och två väggar ligger 2,0 m bortom
lägsta och 1,2 m bortom högsta plats. Kamerorna är inte kända när mallen skrivs, och vid S4 i guacamole står kameran 1,0 m utanför sidoväggen.
Väggarna saknar dessutom källmätning; de är mallvärden.

Därför görs det i två steg. Mallen byggs som förut (steg 1, orörd). Efter att alla tagningar registrerats och kamerorna finns i platsens
koordinater anpassar `anpassa` de GENERERADE väggarna och golvet (steg 2, i kompilatorn): rummets utsträckning (i rummets egna axlar, mallens yaw)
vidgas till att rymma alla renderkamerans lägen med marginalen KAMERA_MARGINAL_M, alla möbler med MOBEL_MARGINAL_M och alla rollers ankare. Bara utåt: ingen vägg
flyttas inåt, och rymmer rummet redan allt rörs ingenting. Väggar som deklarationen anger uttryckligen (`deklarerat.vaggar`) är hårda och flyttas aldrig; ryms inte
kamerorna inom dem redovisas en konflikt och en varning.

`kontrollera` mäter sedan slutplanens geometri (inte kroppens projektion mot mask): per scen och provruta, ligger kameran utanför rummet (golvets yta,
insidan av varje vägg) eller i en vägg, och skär sikten från kameran till någon synlig roll (tre höjder över rollens ankare) en vägg? Varning om ja.

Körs bara för platser med `deklarerat` (deklarerade rum). Gamla vägen (plats/hand.json) och klipp utan deklaration får inga ändringar och inget nytt fält.
Alla gränser (marginaler, provhöjder) är antagna algoritmval, inte mätvärden."""
import copy
import math
import numpy as np

KAMERA_MARGINAL_M = 0.5      # kamerans avstånd till väggens insida (antaget: rymmer en lins och en liten kameraförflyttning)
MOBEL_MARGINAL_M = 0.1       # möbelns avstånd till väggens insida (antaget)
ANKARE_MARGINAL_M = 0.3      # kropp kring ett rollankare (antaget: ungefär en halv stolsbredd)
GENERERADE = ('vagg_bak', 'vagg_sida')     # väggarna som ingest/deklaration_till_hand.py genererar
PUNKTHOJDER_M = (0.4, 1.0, 1.6)          # höjder över golvet där sikten till en roll provas (antaget: knä/höft, mage, huvud)
EPS = 1e-9
IGNORERA_SOM_MOBEL = ('golv', 'vagg', 'fonster', 'lampa')


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


def _axlar(yaw):
    return np.array([math.cos(yaw), math.sin(yaw)]), np.array([-math.sin(yaw), math.cos(yaw)])


def _scener(plan, plats_id):
    ss = plan.get('scener') or plan['matkamera']['scener']
    return [s for s in ss if s.get('plats_id', plats_id) == plats_id]


def _provrutor(scen):
    a, b = scen['ut']
    return sorted(set(range(a, b, 3)) | {b - 1})


def _kameralagen(plan, scen):
    """(ruta, xyz) för scenens provrutor i den renderade kameran (plan.renderkamera.nycklar), alltså det som faktiskt visas."""
    nyck = plan['renderkamera']['nycklar']
    return [(u, np.array(nyck[u]['matris'], float)[:3, 3]) for u in _provrutor(scen)]


def _lador(plan):
    """Planens lådor med rotation: [(objekt, centrum, halvmått, yaw)]."""
    return [(o, np.array(o['pos_m'], float), np.array(o['matt_m'], float) / 2, float((o.get('rotation_rad') or [0, 0, 0])[2])) for o in plan['objekt']]


def _hornen_uv(o, ax_u, ax_v):
    """Lådans fyra hörn projicerade på rummets axlar: [(u, v)]."""
    c = np.array(o['pos_m'][:2], float); h = np.array(o['matt_m'][:2], float) / 2; R = _rz(float((o.get('rotation_rad') or [0, 0, 0])[2]))
    ut = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = c + R @ np.array([sx * h[0], sy * h[1]]); ut.append((float(p @ ax_u), float(p @ ax_v)))
    return ut


def segment_skar_lada(a, b, centrum, halv, yaw):
    """Sant om sträckan a–b (xyz) skär eller börjar/slutar i lådan (centrum, halva måtten, rotation kring z)."""
    R = np.eye(3); R[:2, :2] = _rz(-yaw)
    p = R @ (np.asarray(a, float) - centrum); q = R @ (np.asarray(b, float) - centrum); d = q - p
    t0, t1 = 0.0, 1.0
    for i in range(3):
        if abs(d[i]) < EPS:
            if abs(p[i]) > halv[i] + EPS: return False
        else:
            ta, tb = (-halv[i] - p[i]) / d[i], (halv[i] - p[i]) / d[i]
            if ta > tb: ta, tb = tb, ta
            t0, t1 = max(t0, ta), min(t1, tb)
            if t0 > t1 + EPS: return False
    return True


def anpassa(plan):
    """Steg 2: vidgar generade väggar och golv så att de rymmer kameror, möbler och rollankare. Skriver i plan['objekt'] och plan['plats'][].rumsmall.delar
    och returnerar poster (en per plats med deklaration och generade väggar). Tom lista om ingenting är deklarerat."""
    poster = []
    for pl in plan.get('plats') or []:
        rm = pl.get('rumsmall')
        if not pl.get('deklarerat') or not rm: continue
        delar = {d['id']: d for d in rm['delar']}
        golv, bak, sida = delar.get('golv'), delar.get('vagg_bak'), delar.get('vagg_sida')
        if golv is None or (bak is None and sida is None): continue
        hard = set((pl['deklarerat'].get('vaggar') or {}))
        yaw = float(golv['yaw_rad']); u, v = _axlar(yaw)
        c = np.array(golv['pos_m'][:2], float); W, Dp = golv['matt_m'][0], golv['matt_m'][1]
        cu, cv = float(c @ u), float(c @ v)
        fore = dict(lo_u=cu - W / 2, hi_u=cu + W / 2, lo_v=cv - Dp / 2, hi_v=cv + Dp / 2)
        halv_u = bak['matt_m'][1] / 2 if bak is not None else (sida['matt_m'][0] / 2 if sida is not None else 0.06)
        halv_s = sida['matt_m'][0] / 2 if sida is not None else halv_u
        # Vad rummet måste rymma, i rummets axlar (u längs mallens x, v längs mallens y): (min_u, max_u, min_v, max_v) per källa med sin marginal.
        krav = []
        kam = []
        for s in _scener(plan, pl['id']):
            for _, p in _kameralagen(plan, s): kam.append((float(p[:2] @ u), float(p[:2] @ v)))
        for q in kam: krav.append(('kamera', q[0] - KAMERA_MARGINAL_M, q[0] + KAMERA_MARGINAL_M, q[1] - KAMERA_MARGINAL_M, q[1] + KAMERA_MARGINAL_M))
        for o in plan['objekt']:
            if o.get('deltyp') in IGNORERA_SOM_MOBEL or o.get('typ') == 'rekvisita': continue
            hs = _hornen_uv(o, u, v)
            krav.append((f'mobel:{o["id"].split(":")[0]}', min(h[0] for h in hs) - MOBEL_MARGINAL_M, max(h[0] for h in hs) + MOBEL_MARGINAL_M,
                         min(h[1] for h in hs) - MOBEL_MARGINAL_M, max(h[1] for h in hs) + MOBEL_MARGINAL_M))
        for a in pl.get('ankare') or []:
            q = np.array(a['pos_m'][:2], float)
            krav.append((f'ankare:{a["id"]}', float(q @ u) - ANKARE_MARGINAL_M, float(q @ u) + ANKARE_MARGINAL_M, float(q @ v) - ANKARE_MARGINAL_M, float(q @ v) + ANKARE_MARGINAL_M))
        # Insidan av väggen ska ligga utanför det som kravet rymmer; väggens mittlinje är därför halva tjockleken längre ut.
        beh = dict(lo_u=min([k[1] for k in krav] + [fore['lo_u']]), hi_u=max([k[2] for k in krav] + [fore['hi_u'] - halv_s]) + halv_s,
                   lo_v=min([k[3] for k in krav] + [fore['lo_v']]), hi_v=max([k[4] for k in krav] + [fore['hi_v'] - halv_u]) + halv_u)
        efter = dict(fore)
        konflikter = []
        for nyckel, vagg_id, finns, hallen in (('hi_v', 'vagg_bak', bak is not None, 'vagg_bak' in hard), ('hi_u', 'vagg_sida', sida is not None, 'vagg_sida' in hard)):
            if not finns:
                efter[nyckel] = max(fore[nyckel], beh[nyckel])
            elif hallen:
                if beh[nyckel] > fore[nyckel] + EPS:
                    kallor = sorted({k[0] for k in krav if (k[4] if nyckel == 'hi_v' else k[2]) + (halv_u if nyckel == 'hi_v' else halv_s) > fore[nyckel] + EPS})
                    konflikter.append(dict(vagg=vagg_id, deklarerad_hard=True, ligger_vid_m=fore[nyckel], krav_m=beh[nyckel], saknas_m=beh[nyckel] - fore[nyckel], orsak_kallor=kallor,
                                           orsak='Väggen är uttryckligen deklarerad och flyttas inte; rummet rymmer inte allt (kameror, möbler, rollankare) innanför den.'))
            else:
                efter[nyckel] = max(fore[nyckel], beh[nyckel])
        efter['lo_u'] = min(fore['lo_u'], beh['lo_u']); efter['lo_v'] = min(fore['lo_v'], beh['lo_v'])
        andrad = any(abs(efter[k] - fore[k]) > 1e-9 for k in fore)
        vaggposter = []
        def ny_pos(d, uu, vv):
            q = uu * u + vv * v
            return [float(q[0]), float(q[1]), d['pos_m'][2]]
        nytt = {}
        mid_u, mid_v = (efter['lo_u'] + efter['hi_u']) / 2, (efter['lo_v'] + efter['hi_v']) / 2
        nytt['golv'] = (ny_pos(golv, mid_u, mid_v), [efter['hi_u'] - efter['lo_u'], efter['hi_v'] - efter['lo_v'], golv['matt_m'][2]])
        if bak is not None: nytt['vagg_bak'] = (ny_pos(bak, mid_u if 'vagg_bak' not in hard else float(np.array(bak['pos_m'][:2]) @ u), efter['hi_v'] if 'vagg_bak' not in hard else float(np.array(bak['pos_m'][:2]) @ v)),
                                              [efter['hi_u'] - efter['lo_u'] if 'vagg_bak' not in hard else bak['matt_m'][0], bak['matt_m'][1], bak['matt_m'][2]])
        if sida is not None: nytt['vagg_sida'] = (ny_pos(sida, efter['hi_u'] if 'vagg_sida' not in hard else float(np.array(sida['pos_m'][:2]) @ u), mid_v if 'vagg_sida' not in hard else float(np.array(sida['pos_m'][:2]) @ v)),
                                                  [sida['matt_m'][0], efter['hi_v'] - efter['lo_v'] if 'vagg_sida' not in hard else sida['matt_m'][1], sida['matt_m'][2]])
        for did, d in (('golv', golv), ('vagg_bak', bak), ('vagg_sida', sida)):
            if d is None: continue
            pos, matt = nytt[did]
            flytt = float(np.linalg.norm(np.array(pos[:2]) - np.array(d['pos_m'][:2])))
            if did != 'golv':
                vaggposter.append(dict(id=did, status='deklarerad' if did in hard else 'antagen', kallmatning=None if did not in hard else 'deklarationen',
                                       hard=did in hard, pos_fore_m=[round(x, 4) for x in d['pos_m'][:2]], pos_efter_m=[round(x, 4) for x in pos[:2]], flyttad_m=round(flytt, 4),
                                       matt_fore_m=[round(x, 4) for x in d['matt_m']], matt_efter_m=[round(x, 4) for x in matt]))
            if not andrad: continue
            if did == 'golv':
                # ankare ligger i delens lokala ram; håll dem på samma plats i platsen när golvets origo flyttas
                dp = np.array(pos[:2]) - np.array(d['pos_m'][:2]); lok = _rz(float(d['yaw_rad'])).T @ dp
                for a in d.get('ankare') or []: a['pos_m'][0] -= float(lok[0]); a['pos_m'][1] -= float(lok[1])
            d['pos_m'][:2] = pos[:2]; d['matt_m'] = list(matt)
            for o in plan['objekt']:
                if o['id'] == did: o['pos_m'][:2] = pos[:2]; o['matt_m'] = list(matt)
        poster.append(dict(plats=pl['id'], rum_yaw_rad=yaw, andrad=andrad, kamerorna=len(kam), fore=fore, krav=beh, efter=efter, vaggar=vaggposter, konflikter=konflikter,
                           marginaler_m=dict(kamera=KAMERA_MARGINAL_M, mobel=MOBEL_MARGINAL_M, ankare=ANKARE_MARGINAL_M),
                           regel='Bara utåt: rummets utsträckning (rummets axlar) vidgas till kameror + marginal, möbler + marginal och rollankare + marginal. Hårda (deklarerade) väggar flyttas inte. '
                                 'Generade väggar saknar källmätning och är antagna.'))
    return poster


def _lagen(plan, pl):
    """Ankarpositioner per id i platsen (rumsmallens ankare, som planens personer stöder sig på)."""
    return {a['id']: np.array(a['pos_m'], float) for a in (pl.get('ankare') or [])}


def kontrollera(plan):
    """Mäter slutplanens geometri per scen: kameran utanför rummet / i en vägg, och väggar mellan kameran och synliga roller. Returnerar (post, varningar)."""
    ut = []; varn = []
    for pl in plan.get('plats') or []:
        if not pl.get('deklarerat') or not pl.get('rumsmall'): continue
        golv = next((o for o in plan['objekt'] if o['id'] == 'golv'), None)
        vagg = [(o, c, h, y) for o, c, h, y in _lador(plan) if o.get('deltyp') == 'vagg']
        if golv is None or not vagg: continue
        gc = np.array(golv['pos_m'], float); gh = np.array(golv['matt_m'], float) / 2; gy = float((golv.get('rotation_rad') or [0, 0, 0])[2]); Rg = _rz(-gy)
        lagen = _lagen(plan, pl)
        for s in _scener(plan, pl['id']):
            roller = []
            for pm in s.get('personer') or plan.get('personer') or []:
                p = (pm.get('stod') or {}).get('pos_m') if isinstance(pm, dict) else None
                if p is None and pm.get('ankare') in lagen: p = lagen[pm['ankare']].tolist()
                if p is not None: roller.append((pm['id'], np.array(p, float)))
            utanfor = []; i_vagg = []; blockerade = {}; blockerande = set(); n = 0
            for u_, cam in _kameralagen(plan, s):
                n += 1
                synliga = [(o, c, h, y) for o, c, h, y in vagg if o.get('synlig_ut', [0, len(plan['kallrutor'])])[0] <= u_ < o.get('synlig_ut', [0, len(plan['kallrutor'])])[1]]
                inne = bool(np.all(np.abs(Rg @ (cam[:2] - gc[:2])) <= gh[:2] + EPS))
                for o, c, h, y in synliga:
                    ax = int(np.argmin(h[:2])); R = _rz(y); nn = R[:, ax]; sida_g = float((gc[:2] - c[:2]) @ nn); sida_k = float((cam[:2] - c[:2]) @ nn)
                    if sida_g * sida_k < 0: inne = False
                    if segment_skar_lada(cam, cam, c, h, y): i_vagg.append(u_)
                if not inne: utanfor.append(u_)
                for rid, p in roller:
                    for z in PUNKTHOJDER_M:
                        for o, c, h, y in synliga:
                            if segment_skar_lada(cam, [p[0], p[1], z], c, h, y):
                                blockerade.setdefault(rid, set()).add(u_); blockerande.add(o['id'])
            flaggad = bool(utanfor or i_vagg or blockerade)
            post = dict(plats=pl['id'], scen=s['id'], provrutor=n, rutor_kamera_utanfor_rummet=len(utanfor), rutor_kamera_i_vagg=len(set(i_vagg)),
                        roller_med_vagg_i_sikten={r: len(rr) for r, rr in sorted(blockerade.items())}, blockerande_vaggar=sorted(blockerande), roller_provade=[r for r, _ in roller], flaggad=flaggad)
            ut.append(post)
            if flaggad:
                varn.append(f'Rumsväggar: scen {s["id"]}: kameran ligger utanför rummet i {len(utanfor)} av {n} provrutor, i en vägg i {len(set(i_vagg))}, '
                            f'och {", ".join(sorted(blockerande)) or "ingen vägg"} ligger mellan kameran och {", ".join(sorted(blockerade)) or "ingen roll"}. Väggarna är mallvärden utan källmätning.')
    return ut, varn


def kor(plan):
    """Steg 2 i kompilatorn: anpassa väggarna, kontrollera planens geometri och redovisa i plan['kvalitet']['rumsvaggar'] (bara för deklarerade rum)."""
    poster = anpassa(plan)
    if not poster: return None
    kontroll, varn = kontrollera(plan)
    for p in poster:
        for k in p['konflikter']:
            varn.append(f"Rumsväggar: den deklarerade väggen {k['vagg']} ligger {k['saknas_m']:.2f} m för nära för att rymma {', '.join(k['orsak_kallor'])}; hårda väggar flyttas inte.")
    plan['kvalitet']['rumsvaggar'] = dict(platser=poster, kontroll=kontroll, flaggade_scener=[k['scen'] for k in kontroll if k['flaggad']])
    plan['varningar'].extend(varn)
    return plan['kvalitet']['rumsvaggar']
