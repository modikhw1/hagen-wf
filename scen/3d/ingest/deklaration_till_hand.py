"""Översätter en rumsdeklaration till det handformat som plats.py läser, och genererar rumsmallen ur de deklarerade platserna.

    python deklaration_till_hand.py <ingestmapp med S1..> [--ut <mapp>] [--deklaration <fil>]
    -> <ut>/hand.json, <ut>/hand_logg.json (standard <ingestmapp>/plats_berattat/) och kontrakt/rumsmall/dekl_<klipp>.json

Inget i filen är knutet till ett visst klipp. Allt klippspecifikt står i deklarationen (se dess fält `format`):
  - Kamerans lutning per tagning löses ur den deklarerade kamerahöjden: den lutning (utan rollning) som lägger huvudpersonens höft
    på rätt höjd över golvet. Sittande: sitthöjd + höftled. Stående: rollens deklarerade höfthöjd, annars benens egen längd.
  - `kamera_vid` ger tagningar utanför dialogparet en kameraplats: kameran står vid den platsens huvud och ser mot huvudpersonen.
  - En plats med `las` får sitt läge ur läsningen: rakt fram från kameraplatsen på det lästa avståndet.
  - Rumsmallen byggs av platserna: stolar och ståplatser med ankare för rollernas hemplatser, bord, golv och två väggar. Väggarna är mallvärden kring platserna;
    kontrakt/vaggar.py vidgar dem efter registreringen till att rymma kamerorna (`vaggar.bak.y_m` / `vaggar.sida.x_m` i deklarationen gör en vägg hård).
  - Bord och diskar (typ `bord`): `storlek_m.hojd/langs_x/langs_y` och `mitt_m` får vara tal (hårt) eller [min, max]. Mallen får intervallets mitt, och `hand.deklarerat.mobler`
    för det vidare till kontrakt/, där mobelintervall.py låter skymningskontrollen justera inom intervallet. `massiv: true` bygger möbeln som en låda ner till golvet."""
import argparse, glob, json, math
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent; MALLAR = HIT.parent / 'kontrakt' / 'rumsmall'
HOFT, OGON, HANDLED = [9, 10], [1, 2], [41, 62]
HOFT_OVER_SITS = 0.085; FOTLED = 0.065; SULA = 0.025; HUVUD_FRAMFOR_HOFT = 0.25; HAND_OVER_YTA = 0.035
STIL = dict(golv='#a8a299', vagg='#e5ddc7', stol='#6d6252', bord='#333638', ben='#303537', foremal='#b9bec4')


def skalar(v):
    """Deklarerat värde som tal. Ett intervall [min, max] ger sin mitt (startvärde för lutning och mall); kompilatorn får sedan röra sig inom intervallet."""
    return round(float(np.mean(v)), 9) if isinstance(v, (list, tuple)) else v


def kropp(mapp, pid='1'):
    return np.array([(lambda d: d['pred_keypoints_3d'] + d['pred_cam_t'])(np.load(f)) for f in sorted(glob.glob(str(mapp / 'kropp' / pid / '*.npz')))])


def handsyn(T, n, pid='1'):
    """(rutor, 2) sant där handleden hör till en hand med bildstöd: kolumn 0 höger (MHR70 41), kolumn 1 vänster (62). Utan handsyn-fil: allt sant."""
    f = T / f'handsyn_{pid}.json'
    if not f.exists(): return np.ones((n, 2), bool)
    h = json.loads(f.read_text(encoding='utf-8')); return np.c_[h['h']['synlig'][:n], h['v']['synlig'][:n]]


def benlangd(K):
    """Höft till golv för en stående kropp: lår + underben + fotled + sula, ur kroppens egna leder."""
    l = lambda a, b: np.median(np.linalg.norm(K[:, a] - K[:, b], axis=-1))
    return float(np.mean([l(9, 11) + l(11, 13), l(10, 12) + l(12, 14)]) + FOTLED + SULA)


def los(K, H, hofthojd):
    hoft = np.median(K[:, HOFT].mean(1), axis=0); ps = np.radians(np.linspace(-60, 60, 24001))
    us = np.c_[np.zeros_like(ps), -np.cos(ps), -np.sin(ps)]; p = ps[np.argmin(np.abs(us @ hoft + (H - hofthojd)))]
    u = np.array([0, -math.cos(p), -math.sin(p)]); plan = lambda X: float(np.linalg.norm(X - (X @ u) * u))
    return math.degrees(p), plan(hoft), plan(np.median(K[:, OGON].mean(1), axis=0))


def riktning(grader): return np.array([math.cos(math.radians(grader)), math.sin(math.radians(grader))])


def ersatt_stod(D, fid):
    """Närmast byggda stöd när föremålets `pa` inte byggs (till exempel inslagspapper): det bord vars `tagningar_i_bild` täcker flest av
    föremålets egna tagningar (första bordet vid lika). None utan bord eller utan gemensamma tagningar."""
    f = (D.get('foremal') or {}).get(fid) or {}; tag = set(f.get('tagningar_i_bild') or [])
    bord = [(len(tag & set(p.get('tagningar_i_bild') or [])), -i, pid) for i, (pid, p) in enumerate((D.get('platser') or {}).items()) if isinstance(p, dict) and p.get('typ') == 'bord']
    if not bord: return None
    n, _, pid = max(bord)
    return pid if n > 0 else None


def foremal_id(D, fid, kedja=()):
    """Mall-id för ett föremål, inklusive hela stöd-kedjan. None för handhållna eller trasiga kedjor utan något bord att ersätta stödet med."""
    if fid in kedja: return None
    f = (D.get('foremal') or {}).get(fid)
    if not isinstance(f, dict) or not f.get('pa'): return None
    pa = f['pa']
    if pa in D.get('platser', {}): return f'{pa}:pa:{fid}'
    foralder = foremal_id(D, pa, kedja + (fid,))
    if foralder: return f'{foralder}:pa:{fid}'
    ers = ersatt_stod(D, fid)                       # stödet byggs inte: ersättningsstöd i stället för en bruten kedja
    return f'{ers}:pa:{fid}' if ers else None


def huvud(pl):
    """Var huvudet sitter över en plats: en sittande lutar sig fram över bordet."""
    return np.array(pl['pos_m'][:2]) + (HUVUD_FRAMFOR_HOFT * riktning(pl['blick_grader']) if pl['typ'] == 'sits' else 0)


def oversatt(I, D):
    P, R, N = D['platser'], D['roller'], D.get('narvaro', {})
    roll_i = {t: r for r, v in R.items() if isinstance(v, dict) for t in v['tagningar']}
    hem = {pl['roll']: pid for pid, pl in P.items() if pl.get('roll')}
    hand = dict(deklaration=dict(fil='plats/deklaration.json', version=D['schema_version'], datum=D['datum']), golv_deklarerat=True, rumsmall=f'dekl_{D["klipp"]}')
    logg, K, vila = {}, {}, {}
    for t, k in D['kameror'].items():
        if not isinstance(k, dict): continue
        pid = str(k.get('spar_id', '1'))
        if not (I / t / 'kropp' / pid).exists() or t not in roll_i: continue
        r = k.get('huvudroll', roll_i[t]); K[t] = kropp(I / t, pid); staende = R[r]['lage'] == 'står'; H = skalar(k['hojd_m'])
        roll_i[t] = r
        hh = (R[r].get('hofthojd_m') or benlangd(K[t])) if staende else skalar(P[k.get('person_plats') or hem[r]].get('sitthojd_m', 0.45)) + HOFT_OVER_SITS
        p, d_hoft, d_ogon = los(K[t], H, hh)
        hand[t] = dict(kamerahojd_m=H, kameralutning_grader=round(p, 2), orsak=f"Kamerahöjd {H} m ({k.get('hojd_status', 'antagen')}); lutningen löst ur höjden med höften {hh:.2f} m över golvet.")
        if 'huvudroll' in k: hand[t]['huvudroll'] = r
        u = np.array([0, -math.cos(math.radians(p)), -math.sin(math.radians(p))]); hs = handsyn(I / t, len(K[t]), pid); hj = np.where(hs, K[t][:, HANDLED] @ u, np.nan)
        if np.isfinite(hj).any(): vila[t] = float(np.nanpercentile(np.nanmin(np.where(np.isfinite(hj).any(1)[:, None], hj, np.inf), axis=1)[np.isfinite(hj).any(1)], 10)) + H
        logg[t] = dict(roll=r, kamerahojd_m=H, hofthojd_m=round(hh, 3), benlangd_last_m=round(benlangd(K[t]), 3), kameralutning_grader=round(p, 2), kamera_till_hoft_m=round(d_hoft, 3), kamera_till_ogon_m=round(d_ogon, 3))
    for pid, pl in P.items():            # bord vars höjd ges av kroppens kontakt: lägsta vilande handled minus halva handens tjocklek
        if pl['typ'] == 'bord' and pl.get('hojd_regel') == 'vilande_handled':
            v = [(t, vila[t]) for t in vila if roll_i[t] in pl.get('roller', []) and t not in N.get('bryter_rummet', [])]
            if v:
                t, h = min(v, key=lambda x: x[1]); dekl = pl['storlek_m']['hojd']
                if isinstance(dekl, (list, tuple)):      # intervall: handleden sänker bara taket, golvet i intervallet följer med om taket hamnar under det
                    tak = round(min(dekl[1], h - HAND_OVER_YTA), 3); pl['storlek_m']['hojd'] = [min(dekl[0], tak), tak]
                else: pl['storlek_m']['hojd'] = round(min(dekl, h - HAND_OVER_YTA), 3)
                logg[pid] = dict(hojd_m=pl['storlek_m']['hojd'], deklarerad_m=dekl, lagsta_synliga_handled_m=round(h, 3), ur_tagning=t,
                                 regel='deklarerad höjd, sänkt om en synlig handled ligger lägre än höjden + %.3f m' % HAND_OVER_YTA)
    for pid, pl in P.items():            # platser vars läge ska läsas
        if pl.get('las') and pl.get('pos_m') is None:
            vid = P[pl['las']['kamera_vid']]; d = logg[pl['las']['tagning']]['kamera_till_hoft_m']
            xy = huvud(vid) + d * riktning(vid['blick_grader']); pl['pos_m'] = [round(float(xy[0]), 3), round(float(xy[1]), 3), 0.0]
            logg[pid] = dict(last_pos_m=pl['pos_m'], avstand_m=d, fran=pl['las']['kamera_vid'])
    for pid, pl in P.items():            # bord som står framför en plats
        if pl.get('framfor') and 'mitt_m' not in pl:
            s = P[pl['framfor']]; xy = np.array(s['pos_m'][:2]) + (HUVUD_FRAMFOR_HOFT + skalar(pl['storlek_m']['langs_y']) / 2) * riktning(s['blick_grader'])
            pl['mitt_m'] = [round(float(xy[0]), 3), round(float(xy[1]), 3), 0.0]
    for t, k in D['kameror'].items():
        if t not in hand: continue
        r = roll_i[t]; pp = P[k.get('person_plats') or hem[r]]
        if k.get('kamera_vid') or k.get('person_plats'):
            hand[t]['person_pos_m'] = [float(pp['pos_m'][0]), float(pp['pos_m'][1]), 0.0]; hand[t]['orsak'] += f" Huvudpersonen på {k.get('person_plats') or hem[r]}."
        if k.get('kamera_vid'):
            v = np.array(pp['pos_m'][:2]) - huvud(P[k['kamera_vid']]); hand[t]['kamera_blick_grader'] = round(math.degrees(math.atan2(v[1], v[0])), 1)
            hand[t]['orsak'] += f" Kameran vid {k['kamera_vid']}."
        if t in N.get('bryter_rummet', []): hand[t]['bryter_rummet'] = True
        # Flera deklarerade roller i samma tagning: varje roll med hemplats (eller tagningens person_plats för huvudrollen) bär sin plats och blickriktning,
        # så att plats.py kan passa kameran mot alla på en gång. Tagning med bara en deklarerad roll får inget fält och går som förut.
        if t not in N.get('bryter_rummet', []):
            fler = {}
            for rr, v in R.items():
                if not isinstance(v, dict) or t not in v.get('tagningar', []) or rr not in hem and rr != r: continue
                pid_ = (k.get('person_plats') or hem.get(rr)) if rr == r else hem[rr]
                if pid_ in P and P[pid_].get('pos_m') is not None:
                    fler[rr] = dict(plats=pid_, pos_m=[float(P[pid_]['pos_m'][0]), float(P[pid_]['pos_m'][1]), 0.0], blick_grader=P[pid_].get('blick_grader'))
            if len(fler) >= 2: hand[t]['flera_roller'] = fler
    # Det som är uttryckligen deklarerat och därför bindande genom hela kompilatorn (plats.py för det vidare till plats.json, kontrakt/ läser det).
    # Bara det som står i deklarationen tas med; standardvärden (t.ex. sitthöjd 0,45 när inget anges) är inga deklarationer.
    # Varje värde är ett tal (hårt) eller [min, max] (kompilatorn får röra sig inom intervallet).
    dekl = {}
    if isinstance(D.get('golv'), dict) and D['golv'].get('hojd_m') is not None:
        gs = D['golv'].get('status'); dekl['golv_hojd_m'] = D['golv']['hojd_m']; dekl['golv_status'] = gs if gs in ('uppmatt', 'modellbedomd', 'antagen') else 'antagen'; dekl['golv_status_deklarerad'] = gs
    sit = {pid: pl['sitthojd_m'] for pid, pl in P.items() if pl['typ'] == 'sits' and pl.get('sitthojd_m') is not None and pl.get('roll')}
    kam = {t: k['hojd_m'] for t, k in D['kameror'].items() if t in hand and isinstance(k, dict) and k.get('hojd_m') is not None}
    # Valfri kameraposition i platsens xy. Tal är hårt; [min,max] ger bildkameralösaren frihet inom intervallet.
    # Accepterat format per kamera: "xy_m": {"x": ..., "y": ...} eller [x, y].
    kamxy = {}
    for t,k in D['kameror'].items():
        xy=k.get('xy_m') if isinstance(k,dict) else None
        if isinstance(xy,dict):e={'x_m':xy.get('x'),'y_m':xy.get('y')}
        elif isinstance(xy,(list,tuple)) and len(xy)>=2:e={'x_m':xy[0],'y_m':xy[1]}
        else:continue
        kamxy[t]={n:v for n,v in e.items() if v is not None}
    # Bord och diskar: höjd, mått och mittpunkt. Tal är hårda; [min, max] får kontrakt/mobelintervall.py välja inom (ett värde per möbel för hela klippet).
    mob = {}
    for pid, pl in P.items():
        if pl['typ'] != 'bord': continue
        s_, m_ = pl.get('storlek_m') or {}, pl.get('mitt_m') or [None, None]
        e = dict(hojd_m=s_.get('hojd'), langs_x_m=s_.get('langs_x'), langs_y_m=s_.get('langs_y'), mitt_x_m=m_[0], mitt_y_m=m_[1],
                 **({'massiv': True} if pl.get('massiv') is True else {}), **({'bild': pl['bild']} if pl.get('bild') is not None else {}),
                 **({'bilder': pl['bilder']} if pl.get('bilder') is not None else {}),
                 **({'framfor': pl['framfor']} if (pl.get('bild') is not None or pl.get('bilder') is not None) and pl.get('framfor') is not None else {}))
        mob[pid] = {k: v for k, v in e.items() if v is not None}
    if mob: dekl['mobler'] = mob
    # Väggar med uttryckligt läge (D['vaggar'] = {bak: {y_m, status}, sida: {x_m, status}}) är hårda: kontrakt/vaggar.py flyttar dem aldrig och flaggar en konflikt i stället.
    vag = {}
    for nyckel, koord, id_ in (('bak', 'y_m', 'vagg_bak'), ('sida', 'x_m', 'vagg_sida')):
        v_ = (D.get('vaggar') or {}).get(nyckel)
        if isinstance(v_, dict) and v_.get(koord) is not None: vag[id_] = {koord: v_[koord], 'status': v_.get('status', 'antagen')}
    if vag: dekl['vaggar'] = vag
    if sit: dekl['sitthojd_m'] = sit
    if kam: dekl['kamerahojd_m'] = kam
    if kamxy: dekl['kamera_xy_m'] = kamxy
    # Bildrutor och stödrelationer hör inte hemma i den strikt validerade rumsmallen. De följer därför den redan
    # genomgående deklarerat-vägen: hand.json -> plats.json -> plan.plats[].deklarerat.
    fm = {}
    for fid, f in (D.get('foremal') or {}).items():
        if not isinstance(f, dict): continue
        e = {k: f[k] for k in ('pa', 'halls_av', 'bild', 'bilder') if f.get(k) is not None}
        oid = foremal_id(D, fid)
        if oid: e['objekt_id'] = oid
        if oid and f.get('pa') and f['pa'] not in (D.get('platser') or {}) and not foremal_id(D, f['pa']):
            e['stod_ersatt'] = dict(fran=f['pa'], till=oid.split(':pa:')[0], orsak='stödet byggs inte; närmast byggda bord används')
        if e: fm[fid] = e
    if fm: dekl['foremal'] = fm
    if dekl: hand['deklarerat'] = dekl
    # dialogparet: de två roller med flest lästa rutor; avståndet mellan deras hemplatser
    antal = {}
    for t in K: antal[roll_i[t]] = antal.get(roll_i[t], 0) + len(K[t])
    par = sorted(antal, key=antal.get, reverse=True)[:2]
    if len(par) == 2 and all(r in hem for r in par):
        hand['layout'] = dict(val='deklarerad', status=D.get('berattat_rum', {}).get('status', 'antagen'), stolsavstand_m=round(float(np.linalg.norm(np.array(P[hem[par[0]]]['pos_m']) - P[hem[par[1]]]['pos_m'])), 3),
                              orsak=f"Deklarerat rum (plats/deklaration.json, {D['schema_version']}): {D.get('berattat_rum', {}).get('beskrivning', '')}".strip())
    return hand, logg


def lyft_bildruta(I, D, hand, bild, z_m):
    """Bildruta (tagning, box_2d [ymin, xmin, ymax, xmax] i 0-1000, Gemini-konvention) -> xy där rutans bottenmitt möter planet z = z_m.
    Kameran: den deklarerade kameraplatsens xy, tagningens kamerahöjd, yaw och lutning ur handformatet (lutning > 0 = nedåt), fokal och bildmått ur ingesten.
    Ger None om något saknas eller om strålen inte når planet framför kameran."""
    t = bild.get('tagning'); h = hand.get(t) if hand else None; k = D['kameror'].get(t) or {}; kp = D['platser'].get(k.get('kamera_vid')) or {}
    if not h or not kp.get('pos_m') or len(bild.get('box_2d') or []) != 4: return None
    meta = json.loads((I / t / 'meta.json').read_text(encoding='utf-8')); W, Hp = meta['bredd'], meta['hojd']
    sek = sorted((I / t).glob('sekvens_*.npz'))
    if not sek: return None
    f = float(np.load(sek[0], allow_pickle=True)['fokal'])
    y0, x0, y1, x1 = bild['box_2d']; u, v = (x0 + x1) / 2000 * W, y1 / 1000 * Hp
    psi = math.radians(h.get('kamera_blick_grader', kp.get('blick_grader', 90))); p = math.radians(h['kameralutning_grader'])
    fram = np.array([math.cos(p) * math.cos(psi), math.cos(p) * math.sin(psi), -math.sin(p)]); hoger = np.array([math.sin(psi), -math.cos(psi), 0.])
    ned = np.cross(fram, hoger); d = hoger * (u - W / 2) / f + ned * (v - Hp / 2) / f + fram
    C = np.array([kp['pos_m'][0], kp['pos_m'][1], h['kamerahojd_m']])
    if d[2] >= -1e-6: return None
    s_ = (z_m - C[2]) / d[2]
    return None if s_ <= 0 else (C + s_ * d)[:2].tolist()


def rumsmall(D, hand=None, I=None):
    P = D['platser']; xy = np.array([[skalar(c) for c in (pl.get('pos_m') or pl.get('mitt_m'))[:2]] for pl in P.values()]); lo, hi = xy.min(0) - 2.0, xy.max(0) + 1.2
    mat = lambda f: dict(farg=f, ben_farg=STIL['ben']); bas = dict(modell_ref=None, texturprojektion=None)
    for nyckel, koord, i in (('bak', 'y_m', 1), ('sida', 'x_m', 0)):    # uttryckligt deklarerad vägg: läget går före mallens 1,2 m marginal
        v_ = (D.get('vaggar') or {}).get(nyckel)
        if isinstance(v_, dict) and v_.get(koord) is not None: hi[i] = skalar(v_[koord])
    mitt = (lo + hi) / 2
    golv = dict(id='golv', typ='golv', pos_m=[float(mitt[0]), float(mitt[1]), -0.08], matt_m=[float(hi[0] - lo[0]), float(hi[1] - lo[1]), 0.08], yaw_rad=0, material=mat(STIL['golv']), ankare=[], **bas)
    delar = [golv,
             dict(id='vagg_bak', typ='vagg', pos_m=[float(mitt[0]), float(hi[1]), 0], matt_m=[float(hi[0] - lo[0]), 0.12, 2.7], yaw_rad=0, material=mat(STIL['vagg']), ankare=[], **bas),
             dict(id='vagg_sida', typ='vagg', pos_m=[float(hi[0]), float(mitt[1]), 0], matt_m=[0.12, float(hi[1] - lo[1]), 2.7], yaw_rad=0, material=mat(STIL['vagg']), ankare=[], **bas)]
    for pid, pl in P.items():
        if pl['typ'] == 'sits':
            h = skalar(pl.get('sitthojd_m', 0.45))
            a = [dict(id=pid, typ='sate', pos_m=[0, 0, 0], riktning_rad=math.pi / 2, sate_hojd_m=h, backen_over_sate_m=HOFT_OVER_SITS, fotled_over_golv_m=FOTLED)] if pl.get('roll') else []
            delar.append(dict(id=pid, typ='stol', pos_m=[pl['pos_m'][0], pl['pos_m'][1], 0], matt_m=[0.48, 0.48, h], yaw_rad=math.radians(pl['blick_grader'] - 90), material=mat(STIL['stol']), ankare=a, **bas))
        elif pl['typ'] == 'staplats' and pl.get('roll'):
            golv['ankare'].append(dict(id=pid, typ='staplats', pos_m=[pl['pos_m'][0] - golv['pos_m'][0], pl['pos_m'][1] - golv['pos_m'][1], 0.08], riktning_rad=math.radians(pl['blick_grader']), fotled_over_golv_m=FOTLED))
        elif pl['typ'] == 'bord':
            s = pl['storlek_m']; extra={'massiv': True} if pl.get('massiv') is True else {}
            delar.append(dict(id=pid, typ='bord', pos_m=[skalar(pl['mitt_m'][0]), skalar(pl['mitt_m'][1]), 0], matt_m=[skalar(s['langs_x']), skalar(s['langs_y']), skalar(s['hojd'])], yaw_rad=0, material=mat(STIL['bord']), ankare=[], **extra, **bas))
    # Föremål på en möbel eller ett annat föremål: massiva lådor som står på stödets ovansida. En stöd-kedja kodas i delens id,
    # exempelvis disk_C:pa:vag:pa:kottbit, så att hela kedjan följer möbeln genom kompileringen.
    # Utan bildruta förskjuts föremålet en fjärdedel av stödets bredd åt sidan. Läget på stödet är antaget.
    # Föremål som hålls av en roll (halls_av) byggs inte här; de kräver handens läge per ruta.
    byggda = {}
    def bygg_foremal(fid, kedja=()):
        if fid in byggda: return byggda[fid]
        if fid in kedja: return None
        f = (D.get('foremal') or {}).get(fid)
        if not isinstance(f, dict) or not f.get('storlek_m') or not f.get('pa'): return None
        pa = f['pa']; b = P.get(pa); stod = None
        if not (b and b.get('typ') == 'bord'):
            stod = bygg_foremal(pa, kedja + (fid,))
            if not stod:
                pa = ersatt_stod(D, fid)            # stödet byggs inte (till exempel inslagspapper): närmast byggda bord
                if not pa: return None
                b = P[pa]
        if b and b.get('typ') == 'bord':
            s = b['storlek_m']; bx, by = skalar(b['mitt_m'][0]), skalar(b['mitt_m'][1])
            sx, sy, z = skalar(s['langs_x']), skalar(s['langs_y']), skalar(s['hojd']); stod_id = pa
        else:
            bx, by = stod['pos_m'][:2]; sx, sy = stod['matt_m'][:2]
            z = stod['pos_m'][2] + stod['matt_m'][2]; stod_id = stod['id']
        st = [skalar(v) for v in f['storlek_m']]
        # Med bildruta: deklarerad kameralift är bara ett startläge. kontrakt/foremallyft.py gör om lyftet mot slutkameran.
        xy = lyft_bildruta(I, D, hand, f['bild'], z) if f.get('bild') and I is not None else None
        if xy:
            xy = [min(max(xy[0], bx - sx / 2 + st[0] / 2), bx + sx / 2 - st[0] / 2),
                  min(max(xy[1], by - sy / 2 + st[1] / 2), by + sy / 2 - st[1] / 2)]
        else: xy = [bx + sx / 4, by]
        d = dict(id=f'{stod_id}:pa:{fid}', typ='bord', massiv=True, pos_m=[xy[0], xy[1], z],
                 matt_m=st, yaw_rad=0, material=mat(STIL['foremal']), ankare=[], **bas)
        delar.append(d); byggda[fid] = d
        return d
    for fid in (D.get('foremal') or {}): bygg_foremal(fid)
    return dict(schema_version='rumsmall/1', id=f'dekl_{D["klipp"]}', beskrivning=f'Genererad ur rumsdeklarationen för {D["klipp"]} ({D["schema_version"]}).', fiktiv=False, status='mall',
                antaganden=['Platsernas lägen kommer ur deklarationen (ägaren, läst eller antaget, se den).', 'Väggar, material och möblernas form är mallvärden.'], delar=delar)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); a.add_argument('ingest'); a.add_argument('--ut'); a.add_argument('--deklaration'); x = a.parse_args()
    I = Path(x.ingest).resolve(); ut = Path(x.ut).resolve() if x.ut else I / 'plats_berattat'; ut.mkdir(parents=True, exist_ok=True)
    D = json.loads(Path(x.deklaration or I / 'plats' / 'deklaration.json').read_text(encoding='utf-8'))
    hand, logg = oversatt(I, D); m = rumsmall(D, hand, I)
    (ut / 'hand.json').write_text(json.dumps(hand, indent=1, ensure_ascii=False), encoding='utf-8')
    (ut / 'hand_logg.json').write_text(json.dumps(logg, indent=1, ensure_ascii=False), encoding='utf-8')
    (ut / 'deklaration_upplost.json').write_text(json.dumps(D, indent=1, ensure_ascii=False), encoding='utf-8')     # med lästa lägen ifyllda
    (MALLAR / f'{m["id"]}.json').write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding='utf-8')
    for t, v in logg.items(): print(t, v)
    print('->', ut / 'hand.json', '|', MALLAR / f'{m["id"]}.json')
