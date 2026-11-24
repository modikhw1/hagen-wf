"""kalla.json + regi.json -> deterministisk, upplöst plan/1. Bara stdlib och numpy."""
import argparse
import copy
import math
import re
import sys
from fractions import Fraction
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
from gemensamt import HIT, ladda, skriv, kontrollera
sys.path.insert(0, str(HIT.parent/'ingest'))
from metrisk import las as las_sekvens, registrera_dolda_fotter
from rumsmall import byggobjekt as mallobjekt, las as las_mall, som_plats

F = np.diag([1., -1., -1.])
FARGER = ['#c9b7a5', '#8fa3b8', '#b89a8f', '#9fb48f', '#b0a0c0']


class EjTillampad(ValueError): pass


class _Klar(Exception): pass   # 0033: en edit som är färdig tidigt i sin gren


# ---- 0029: handlingar och scenbygge. Bara i bruk när källan har semantik.handling eller matning.scenbygge och regin använder dem.
def _slerp_matris(A, B, w):
    from scipy.spatial.transform import Rotation as Ro
    ra, rb = Ro.from_matrix(A), Ro.from_matrix(B)
    return (ra * Ro.from_rotvec(w * (ra.inv() * rb).as_rotvec())).as_matrix()


def blanda_nyckel(p, q, w):
    """Kameranyckel mellan p och q: läget linjärt, rotationen sfäriskt, linsen linjärt. w = 0 ger p."""
    if w <= 1e-9 or p == q: return copy.deepcopy(p)
    A, B = np.array(p['matris']), np.array(q['matris']); M = np.eye(4)
    M[:3, :3] = _slerp_matris(A[:3, :3], B[:3, :3], w); M[:3, 3] = (1 - w) * A[:3, 3] + w * B[:3, 3]
    ut = dict(matris=M.tolist(), lins_mm=(1 - w) * p['lins_mm'] + w * q['lins_mm'])
    if 'mal_m' in p and 'mal_m' in q: ut['mal_m'] = ((1 - w) * np.array(p['mal_m']) + w * np.array(q['mal_m'])).tolist()
    return ut


def omsampla(fil, L, offs, n, mapp):
    """Skriver en kopia av en mätfil (sekvens_*.npz eller varld.npz) med rutorna i rutlistans ordning. Arrayer med n rutor först samplas om:
    sant/falskt och heltal tas ur närmaste källruta; kvaternioner i pose (kolumn 3:7) normaliserat linjärt; rotationsmatriser sfäriskt;
    övrigt linjärt. Övriga arrayer kopieras. Filnamnet är en hash av källfilen och rutlistan, så samma ändring ger samma fil."""
    import hashlib, json as _json
    src = Path(fil); h = hashlib.sha256((str(src.resolve()) + str(src.stat().st_size) + str(src.stat().st_mtime_ns) + _json.dumps([list(x) for x in L])).encode()).hexdigest()[:20]
    mapp = Path(mapp); mapp.mkdir(parents=True, exist_ok=True); ut = mapp / f'{src.stem}_{h}.npz'
    if ut.exists(): return str(ut)
    z = np.load(src, allow_pickle=False); i0 = np.array([x[0] - offs for x in L]); i1 = np.array([x[1] - offs for x in L]); w = np.array([x[2] for x in L], float)
    d = {}
    for k in z.files:
        a = z[k]
        if a.ndim == 0 or a.shape[0] != n: d[k] = a; continue
        ww = w.reshape(-1, *([1] * (a.ndim - 1)))
        if not np.issubdtype(a.dtype, np.floating): d[k] = np.where(ww < .5, a[i0], a[i1]); continue
        if a.ndim == 3 and a.shape[1:] == (3, 3):
            d[k] = np.array([a[p] if wi <= 1e-9 else _slerp_matris(a[p], a[q], wi) for p, q, wi in zip(i0, i1, w)]).astype(a.dtype); continue
        b = (1 - ww) * a[i0] + ww * a[i1]
        if k == 'pose' and a.ndim == 3 and a.shape[2] >= 7:
            q0, q1 = a[i0][..., 3:7], a[i1][..., 3:7]; s = np.sign(np.sum(q0 * q1, axis=-1, keepdims=True)); s[s == 0] = 1
            q = (1 - ww) * q0 + ww * s * q1; b[..., 3:7] = q / np.linalg.norm(q, axis=-1, keepdims=True)
        d[k] = b.astype(a.dtype)
    np.savez(ut, **d)
    return str(ut)


ARMLED = ('clavicle', 'uparm', 'lowarm', 'wrist', 'pinky', 'ring', 'middle', 'index', 'thumb')


def spegla_armar(fil, a, b, overgang, mapp):
    """0031, utförande nivå 1: armarna byter sida i rutorna [a, b) (sekvensens lokala rutor). Varje armled tar den andra sidans pose,
    speglad över kroppens mittplan i just den rutan (normalen = höftled vänster minus höger plus nyckelben vänster minus höger, genom
    roten och nacken). Läget speglas, rotationen blir -H·R (MHR:s vänster- och högerben har viloaxlar R_v = -H0·R_h, uppmätt ur viloposen). Bål, ben och huvud orörda. Mjuk övergång
    (overgang rutor) in och ut, utom vid sekvensens kanter. Skriver en kopia; filnamnet är en hash av källan och intervallet."""
    import hashlib, json as _json
    from scipy.spatial.transform import Rotation as Ro
    src = Path(fil); h = hashlib.sha256((str(src.resolve()) + str(src.stat().st_mtime_ns) + _json.dumps([a, b, overgang])).encode()).hexdigest()[:20]
    mapp = Path(mapp); mapp.mkdir(parents=True, exist_ok=True); ut = mapp / f'{src.stem}_spegel_{h}.npz'
    if ut.exists(): return str(ut)
    N = ladda(HIT.parent / 'ingest/mhr_ledernamn.json'); z = dict(np.load(src)); P = z['pose'].copy(); n = len(P)
    par = [(N.index(x), N.index('r_' + x[2:])) for x in N if x.startswith('l_') and any(k in x for k in ARMLED) and ('r_' + x[2:]) in N]
    ix = N.index
    for f in range(max(0, a), min(n, b)):
        w = 1.0
        if overgang:
            if a > 0 and f - a < overgang: w = (f - a + 1) / (overgang + 1)
            if b < n and b - 1 - f < overgang: w = min(w, (b - f) / (overgang + 1))
        p = P[f]; nv = (p[ix('l_upleg'), :3] - p[ix('r_upleg'), :3]) + (p[ix('l_clavicle'), :3] - p[ix('r_clavicle'), :3]); nv = nv / np.linalg.norm(nv)
        c = (p[ix('root'), :3] + p[ix('c_neck'), :3]) / 2; H = np.eye(3) - 2 * np.outer(nv, nv)
        ny = p.copy()
        for li, ri in par:
            for dst, srci in ((li, ri), (ri, li)):
                q = p[srci]; pos = q[:3] - 2 * ((q[:3] - c) @ nv) * nv
                R = -H @ Ro.from_quat(q[3:7]).as_matrix(); ny[dst, :3] = pos   # viloposen: R_vänster = -H0·R_höger (MHR:s ben har speglade axlar); ny[dst, 3:7] = Ro.from_matrix(R).as_quat()
        if w < 1:
            q0, q1 = p[:, 3:7], ny[:, 3:7]; s = np.sign(np.sum(q0 * q1, axis=1, keepdims=True)); s[s == 0] = 1
            q = (1 - w) * q0 + w * s * q1; ny[:, 3:7] = q / np.linalg.norm(q, axis=1, keepdims=True); ny[:, :3] = (1 - w) * p[:, :3] + w * ny[:, :3]
        P[f] = ny
    z['pose'] = P.astype(z['pose'].dtype); np.savez(ut, **z)
    return str(ut)


def sammanfatta_rutlista(L, start):
    """Rutlistan i korta stycken för planen: utrutor, källrutor och märke (läst, overgang, omsamplad, upprepning)."""
    ut = []
    for j, x in enumerate(L):
        m = x[3] or 'last'
        if ut and ut[-1]['marke'] == m and ut[-1]['ut'][1] == start + j: ut[-1]['ut'][1] += 1; ut[-1]['kalla'][1] = max(ut[-1]['kalla'][1], x[1] + 1)
        else: ut.append(dict(ut=[start + j, start + j + 1], kalla=[x[0], max(x[0], x[1]) + 1], marke=m))
    return ut


def scenbygge_i_plan(plan, byggen, ursprung, iv_ut):
    """0029: scenen kring en kropp (kalla.matning.scenbygge) in i planen, sist, i de utrutor som kommer ur scenen. Byggets objekt ersätter
    planens objekt med samma id i de rutorna (och bara där). Ett ersatt objekt som en edit redan tagit bort ur scenen kommer inte tillbaka.
    Handföremålens fäste sätts per scen som kommer ur källscenen."""
    kr = plan['kallrutor']; logg = []
    for b in byggen:
        sid = b['scen']; scener = [s for s, u in ursprung.items() if u == sid]
        if not scener: logg.append(dict(scen=sid, status='scenen finns inte i tidslinjen')); continue
        uts = sorted(tuple(iv_ut[s]) for s in scener)
        def i_scen(o):
            a, c = o.get('synlig_ut') or [0, len(kr)]; return [(max(a, u0), min(c, u1)) for u0, u1 in uts if max(a, u0) < min(c, u1)]
        borta = [r for r in b.get('ersatter', []) if not any(o['id'] == r and i_scen(o) for o in plan['objekt'])]
        nya = []
        for o in plan['objekt']:
            if o['id'] not in b.get('ersatter', []) or not i_scen(o): nya.append(o); continue
            a, c = o.get('synlig_ut') or [0, len(kr)]; delar = [a]
            for u0, u1 in uts: delar += [u0, u1]
            delar.append(c); bitar = [(x, y) for x, y in zip(delar[::2], delar[1::2]) if x < y]
            for x, y in bitar: q = copy.deepcopy(o); q['synlig_ut'] = [x, y]; nya.append(q)
        lagda = 0
        val = {}   # 0033: valda varianter (satt_frihetsgrad på en platshållarperson), per person
        for s_ in scener: val.update(ursprung.get('_val', {}).get(s_, {}))
        for o in b['objekt']:
            if any(o['id'] == r or o['id'].startswith(r + ':') for r in borta): continue
            pid_ = o['id'].split(':')[0]
            if pid_ in val and val[pid_] in (o.get('varianter') or {}).get('kroppsdel', {}):
                o = dict(copy.deepcopy(o), **o['varianter']['kroppsdel'][val[pid_]]); o['variant'] = dict(kroppsdel=val[pid_])
            o = {k: v for k, v in o.items() if k != 'varianter'} if 'varianter' in o else o
            ka, kb = o['synlig_kalla']
            for u0, u1 in uts:
                j = u0
                while j < u1:
                    if not ka <= kr[j] < kb: j += 1; continue
                    k = j
                    while k + 1 < u1 and ka <= kr[k + 1] < kb: k += 1
                    q = copy.deepcopy(o); q.pop('synlig_kalla'); q['synlig_ut'] = [j, k + 1]; q['ursprung_bygge'] = sid; nya.append(q); lagda += 1; j = k + 1
        plan['objekt'] = nya
        fasten = []
        for f in b.get('handforemal', []):
            mall = next((h for h in plan.get('handforemal') or [] if h['id'] == f['id']), None) or (dict(f['post'], kontroll_rutor=[]) if f.get('post') else None)
            if mall is None: fasten.append(dict(id=f['id'], status='handföremålet finns inte i planen')); continue
            plan.setdefault('handforemal', [])
            for s in scener:
                h = next((x for x in plan['handforemal'] if x['id'] == f['id'] and x['scen'] == s), None)
                if h is None: h = copy.deepcopy(mall); h.update(scen=s, synlig_ut=list(iv_ut[s])); plan['handforemal'].append(h)
                h['offset_m'] = list(f['offset_m']); h['offset_status'] = f.get('status', 'matt'); fasten.append(dict(id=f['id'], scen=s))
                d = next((x for x in plan.get('scener') or [] if x['id'] == s), None)
                if d is not None and d.get('handlingsrutor'): h['kontroll_rutor'] = []
        logg.append(dict(scen=sid, scener=scener, objekt=lagda, ersatta=[r for r in b.get('ersatter', []) if r not in borta], borttagna_av_edit=borta, fasten=fasten))
    plan.setdefault('kvalitet', {})['scenbygge'] = logg
    plan['beslut'].append('0029: scenen kring kroppen (matning.scenbygge) lagd sist i scenens utrutor; ersatta objekt står kvar i övriga scener.')


def gravitation(v):
    u = v['upp'] / np.linalg.norm(v['upp']); z = np.array([0., 0., 1.]); c = float(u @ z)
    if c < -1 + 1e-10: return np.diag([1., -1., -1.])
    x, y, z = np.cross(u, z); vx = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def transform(pos, rot):
    m = np.eye(4); m[:3, :3] = rot; m[:3, 3] = pos
    return m.tolist()


def sikta(pos, mal):
    bak = np.array(pos) - mal; norm = np.linalg.norm(bak)
    if not np.all(np.isfinite(bak)): raise EjTillampad('Kamerans position eller mål är inte ändliga tal.')
    if norm < 1e-8: raise EjTillampad('Kamerans position och mål sammanfaller.')
    bak /= norm; hoger = np.cross([0., 0., 1.], bak)
    if np.linalg.norm(hoger) < 1e-8: hoger = np.cross([0., 1., 0.], bak)
    hoger /= np.linalg.norm(hoger)
    return transform(pos, np.column_stack([hoger, np.cross(bak, hoger), bak]))


def storlek(matt):
    if matt is None or min(matt) <= 0: raise EjTillampad('Lådan kräver tre positiva mått i matt_m.')
    return [matt[0], matt[2], matt[1]]  # kontrakt: bredd, höjd, djup -> lokalt XYZ


def tillgangspost(e):
    """Vilken tillgång en prop-edit pekar på och om dess geometri är byggd. Ingen Blender-byggnad: ett kort har ingen 3D-geometri."""
    from propbank import BANK
    tid, kalla = e['tillgang_id'], e.get('tillgang_kalla')
    if kalla == 'propbank':
        if tid not in BANK: raise EjTillampad('Tillgången ' + repr(tid) + ' finns inte i propbanken.')
        return dict(id=tid, kalla='propbank', geometri='byggd')
    if kalla == 'kort':
        return dict(id=tid, kalla='kort', geometri='ej_byggd',
                    anmarkning='2D-fotokort ur klippet. Ingen 3D-geometri är byggd; objektets låda står kvar som platshållare i planen.')
    raise EjTillampad('Extern proptillgång kräver tillgang_kalla (propbank eller kort); utan den är tillgang_id reserverad. Annars: använd en typ i propbanken.')


def rumobjekt(rum, G):
    objekt = [dict(id='golv', namn='golv', typ='plan', pos_m=[0, 0, rum['floor']['height']],
                   rotation_rad=[0, 0, 0], matt_m=[40, 40, 0], farg='#5a554e', top_slope=0)]
    for w in rum['walls']:
        t = G @ w['tangent']
        objekt.append(dict(id=w['id'], namn='rum:'+w['id'], typ='lada', pos_m=(G @ w['centre']).tolist(),
                            rotation_rad=[0, 0, math.atan2(t[1], t[0])], matt_m=[w['width'], .01, w['height']], farg='#77716a', top_slope=0))
    for o in rum['objects']:
        farg = '#347e77' if o['label'] == 'pool table' else '#a58b68' if o['label'] == 'bar counter' else '#777e87'
        objekt.append(dict(id=o['id'], namn='rum:'+o['label']+':'+o['id'], typ='lada', pos_m=(G @ o['centre']).tolist(),
                            rotation_rad=[0, 0, o['yaw']], matt_m=o['size'], farg=farg, top_slope=o.get('top_slope', 0)))
    return {o['id']: o for o in objekt}


def platsobjekt(pl):
    """Platsens golv, väggar och fasta objekt som byggobjekt. Platsen är redan i sitt eget koordinatsystem (Z upp), ingen gravitation behövs.
    Samma fält och ordning som rumobjekt, så identitetsfallet ger samma objekt som rum.json direkt."""
    if pl.get('rumsmall'): return {o['id']:o for o in mallobjekt(pl['rumsmall'])}
    objekt = [dict(id='golv', namn='golv', typ='plan', pos_m=[0, 0, pl['golv']['hojd_m']], rotation_rad=[0, 0, 0], matt_m=[40, 40, 0], farg='#5a554e', top_slope=0)]
    for w in pl['vaggar']:
        objekt.append(dict(id=w['id'], namn='rum:'+w['id'], typ='lada', pos_m=w['centrum_m'], rotation_rad=[0, 0, w['yaw_rad']],
                            matt_m=[w['bredd_m'], .01, w['hojd_m']], farg='#77716a', top_slope=0))
    for o in pl['objekt']:
        farg = '#347e77' if o['etikett'] == 'pool table' else '#a58b68' if o['etikett'] == 'bar counter' else '#777e87'
        objekt.append(dict(id=o['id'], namn='rum:'+o['etikett']+':'+o['id'], typ='lada', pos_m=o['centrum_m'], rotation_rad=[0, 0, o['yaw_rad']],
                            matt_m=o['matt_m'], farg=farg, top_slope=o.get('top_slope', 0)))
    return {o['id']: o for o in objekt}


def fokalredovisning(f_px, dim, kam):
    """Brännvidd per tagning med status och källa till planens kvalitet.kamerakalibrering. `fokal_status`/`fokal_kalla` i kamerans post vinner;
    annars: lika med längsta sidan = antagen, annars mätt av COLMAP i ingesten."""
    antagen = abs(float(f_px) - float(dim)) < 1e-6
    return dict(fokal_px=float(f_px), fokal_status=kam.get('fokal_status') or ('antagen' if antagen else 'matt'),
                fokal_kalla=kam.get('fokal_kalla') or ('bildens längsta sida' if antagen else 'COLMAP (kamera.json)'))


def ankarpose(a):
    c, z = math.cos(a['riktning_rad']), math.sin(a['riktning_rad'])
    return np.array(transform(a['pos_m'], np.array([[c, -z, 0.], [z, c, 0.], [0., 0., 1.]])))


def kompilera(kallfil, regifil, platsbank=None, *, snabb=False):
    """snabb hoppar bara över diagnostik. Fulla flödet behåller diagnostik som standard."""
    kallfil, regifil = Path(kallfil).resolve(), Path(regifil).resolve()
    K, R = ladda(kallfil), ladda(regifil)
    ids_fore = [e.get('id') if isinstance(e, dict) else None for e in (R.get('edits') if isinstance(R, dict) and isinstance(R.get('edits'), list) else [])]
    avvisade = []   # schemafelaktiga edits avvisas enskilt (se gemensamt.kontrollera); övriga fel i kalla/regi avvisar hela regin
    varningar = kontrollera(K, R, kallfil.parent, kallfil, avvisade=avvisade)
    def absolut(o):
        if isinstance(o, dict): return {k: str((kallfil.parent/v).resolve()) if k == 'sokvag' else absolut(v) for k,v in o.items()}
        if isinstance(o, list): return [absolut(v) for v in o]
        return o
    matning = absolut(K['matning'])
    registrera_dolda_fotter()
    # Saknade filer får vara varningar i kontraktet, men aldrig i en byggbar plan.
    def filer(o):
        if isinstance(o, dict):
            if 'sokvag' in o and not Path(o['sokvag']).is_file(): raise ValueError('Mätfil saknas: ' + o['sokvag'])
            for v in o.values(): filer(v)
        elif isinstance(o, list):
            for v in o: filer(v)
    filer(matning)
    kameror = {k['id']: k for k in matning['kameror']}; rumfiler = {r['id']: r for r in matning['rum']}
    if not kameror or not rumfiler or any(s['kamera'] not in kameror or s['miljo'] not in rumfiler for s in K['semantik']['scener']):
        raise ValueError('Byggaren kräver en uppmätt kamera och ett rum för varje scen.')
    platsm = {p['id']: p for p in matning.get('platser', [])}; PL = {i: ladda(p['fil']['sokvag']) for i, p in platsm.items()}
    from golvmatning import for_plan
    matning, PL = for_plan(K, matning, PL)
    registrera_dolda_fotter(matning)
    platsm = {p["id"]: p for p in matning.get("platser", [])}
    from tropassning import anpassa
    PL, benlangder, hojdpassning = anpassa(K, matning, PL)
    platsbank = Path(platsbank) if platsbank else HIT/'rumsmall'
    flerklipp = any('kalla_ruta0' in c for c in matning['kameror']) or any(m.get('scen') for m in matning['personer'])   # mätningar per scen (kalla_flera.py); annars ett sammanhängande klipp
    N = K['tidsbas']['antal_rutor']
    fps = Fraction(K['tidsbas']['fps_taljare'], K['tidsbas']['fps_namnare'])
    ofps = Fraction(R['utdata']['fps_taljare'], R['utdata']['fps_namnare'])
    if fps != ofps: raise ValueError('Ändrad bildfrekvens stöds inte ännu; ange källans fps.')
    if R['utdata']['render_backend'] != 'blender_mhr': raise ValueError('Planen kräver blender_mhr.')
    if R['utdata']['stil_ref']: raise ValueError('stil_ref kan inte lösas till MHR-material.')
    if R['utdata']['ljudpolicy']=='designade_rostar': raise ValueError('designade_rostar kräver ett röstbygge som inte ingår.')
    if not (kallfil.parent/K['klipp']['video']['sokvag']).is_file(): raise ValueError('Källvideon saknas.')
    if R['ramar']['bevara_klippoffset_s'] is not None: raise ValueError('bevara_klippoffset_s stöds inte ännu.')
    # Tider i kalla är avrundade (3-4 decimaler): närmaste ruta, inte uppåt. 0,667 s vid 30 fps är ruta 20.
    def ruta(t): return min(N, math.floor(Fraction(str(t)) * fps + Fraction(1, 2)))
    pers = {p['id']: dict(id=p['id'], roll=p['roll'], farg=FARGER[i % len(FARGER)],
                         **({} if flerklipp else dict(rorelse=next(m['rorelse']['sokvag'] for m in matning['personer'] if m['person']==p['id']))))
            for i,p in enumerate(sorted(K['semantik']['personer'], key=lambda p:p['id']))}
    # Mätningen läses en gång per scen: kamera (varld.npz), personer och rum. kx pekar ut den i ktx så att scenerna kan kopieras billigt.
    ktx = {}; filcache = {}
    def laddad(fil):
        if fil not in filcache: filcache[fil] = las_sekvens(fil)
        return filcache[fil]
    def kontext(sk, Mover=None, platsover=None):
        kam = kameror[sk['kamera']]; V = laddad(kam['spar_metrisk']['sokvag']); G = gravitation(V); offs = kam.get('kalla_ruta0', 0)
        # Plats: transformen M tar tagningens Blender-värld (G @ mätvärld) in i platsen. G_eff = Rz G och T = translation; utan plats T = None.
        reg = next((r for r in platsm.get(sk.get('plats_id'), {}).get('registreringar', []) if r['scen'] == sk['id']), None) if sk.get('plats_id') else None
        M = Mover if Mover is not None else (np.array(reg['till_plats']['matris']) if reg else None); T = None; plats = platsover or (PL[sk['plats_id']] if reg else None)
        if reg and abs(reg['till_plats']['skala'] - 1.0) > 1e-9: raise ValueError('Platsens transform har skala utom 1,0; byggaren stöder bara 1,0.')
        if M is not None and not flerklipp and not np.allclose(M, np.eye(4)): raise ValueError('En plats-transform som inte är identitet kräver flera tagningar (scener i planen).')
        if M is not None: G = M[:3, :3] @ G; T = M[:3, 3]
        pt = (lambda x: G @ x) if T is None else (lambda x: G @ x + T)
        ms = [m for m in matning['personer'] if m.get('scen') in (None, sk['id'])]
        seq = {m['person']: laddad(m['rorelse']['sokvag']) for m in ms}
        # Ett sammanhängande klipp mäts över hela tidsbasen; i flerklippsfallet över scenens egna rutor.
        antal = N if 'kalla_ruta0' not in kam else ruta(sk['slut_s']) - ruta(sk['start_s'])
        if 'kalla_ruta0' in kam and offs != ruta(sk['start_s']): raise ValueError(f'kalla_ruta0 för {kam["id"]} stämmer inte med scenens start.')
        if len(V['kam_R']) != antal: raise ValueError('Kamerans bildantal avviker från tidsbasen.')
        for pid, s in seq.items():
            if len(s['pose']) != antal or len(s['inom']) != antal: raise ValueError('Fel bildantal för person ' + pid)
        objekt = platsobjekt(plats) if plats is not None else rumobjekt(ladda(rumfiler[sk['miljo']]['fil']['sokvag']), G)
        if plats is not None and plats.get('rumsmall'):
            from tropassning import scenpassa_objekt
            objekt=scenpassa_objekt(objekt,plats['rumsmall'],sk['id'])
        if plats is None:
            # GOLV2: utan platsreferens väljs tagningens golv lokalt, samma regel som platsens.
            from golvmatning import lokalt_golv
            golv2 = lokalt_golv(Path(kam['spar_metrisk']['sokvag']).parent)['golv_hojd_m']
            if golv2 is not None: objekt['golv']['pos_m'][2] = float(golv2)
        # Semantiska prop-id kan skilja från mätningens objekt-id.
        for p in K['semantik']['props']:
            if p.get('scen') in (None, sk['id']) and p['rum_ref'] in objekt and p['id'] != p['rum_ref']:
                o=objekt.pop(p['rum_ref']); o['id']=p['id']; objekt[p['id']]=o
        from propplan import fran_kalla
        for p in K['semantik']['props']:
            obj=fran_kalla(p,sk['id'])
            if obj is not None: objekt[obj['id']]=obj
        spar = [dict(matris=transform(pt(V['kam_C'][i]), G @ V['kam_R'][i] @ F),
                     lins_mm=float(next(iter(seq.values()))['fokal'] if seq else kam.get('fokal_px') or max(K['klipp']['video']['bredd'], K['klipp']['video']['hojd'])) * 36 / K['klipp']['video']['bredd']) for i in range(antal)]
        kalibrering = None
        fokal = fokalredovisning(float(next(iter(seq.values()))['fokal'] if seq else kam.get('fokal_px') or max(K['klipp']['video']['bredd'], K['klipp']['video']['hojd'])),
                                 max(K['klipp']['video']['bredd'], K['klipp']['video']['hojd']), kam)
        camera_binding = sk.get('kamera_bindning')
        if camera_binding and plats:
            source_place=PL[sk['plats_id']]
            old=next(a for a in source_place['ankare'] if a['id']==camera_binding['ankare'])
            new=next((a for a in plats['ankare'] if a['id']==camera_binding['ankare']),None)
            if new is None:
                kind='kamera_personal' if camera_binding['ankare'].startswith('kamera_personal') else 'kamera_kund'
                new=next(a for a in plats['ankare'] if a['id']==kind)
            oldM=np.array(reg['till_plats']['matris'])
            current=np.eye(4) if M is None else M
            follow=ankarpose(new)@np.linalg.inv(ankarpose(old))@oldM@np.linalg.inv(current)
            for key in spar:key['matris']=(follow@np.array(key['matris'])).tolist()
        rspar = spar
        if kam.get('renderbana'):
            # 0029: renderkameran löst mot originalet (gennedbrytning/r_kamera.py), i platsens ram vid lösningen. Följer med om scenen flyttas.
            rb = np.load(kam['renderbana']['fil']['sokvag']); mats, lins = rb['matris'], rb['lins_mm']
            if len(mats) != antal: raise ValueError(f'Renderbanan för {kam["id"]} har {len(mats)} rutor, tagningen {antal}.')
            follow = (np.eye(4) if M is None else M) @ np.linalg.inv(rb['till_plats'])
            rspar = [dict(matris=(follow @ mats[i]).tolist(), lins_mm=float(lins[i])) for i in range(antal)]
        return dict(V=V, G=G, T=T, M=M, tagning=reg['tagning'] if reg else None, plats=plats, plats_id=plats['id'] if plats is not None else None, offs=offs, ms=ms, seq=seq, objekt=objekt, spar=spar,rspar=rspar,kalibrering=kalibrering,fokal=fokal)
    scener = []
    for s in K['semantik']['scener']:
        ktx[s['id']] = c = kontext(s)
        scener.append(dict(id=s['id'], a=ruta(s['start_s']), b=ruta(s['slut_s']), ursprung=s['id'], kx=s['id'],
                           objekt=copy.deepcopy(c['objekt']), kamera=copy.deepcopy(c['rspar']), ljud=True))
    if not scener: raise ValueError('Källan saknar tidsatta scener.')
    # 0016: scengrupper (intilliggande tagningar med samma roll) och föremål som deklarationen bygger. Saknas de i källan gäller allt som förut.
    grupper = {g['id']: list(g['scener']) for g in K['semantik'].get('scengrupper', [])}
    dekl_props = {p['id']: p for p in K['semantik']['props'] if p.get('deklaration')}
    foremal_edits = []   # tillämpas på planens föremål efter att deklarationen lyfts (foremallyft, handforemal)
    hallna = []          # 0016: scener som förlängs genom att hålla sista rutan
    skyddade = {b['scen'] for b in K['semantik']['beats'] if b['id'] in R['ramar']['bevara_beats']}
    if None in skyddade: raise ValueError('Ett bevarat beat saknar scenbindning.')
    tillampat, ej = [], []; standard = []   # standardvärden som planen själv valt, inte CM; skrivs i andring
    lednamn = ladda(HIT.parent/'ingest/mhr_ledernamn.json')
    def scen(sid):
        s=next((s for s in scener if s['id']==sid), None)
        if s is None: raise EjTillampad('Scenen finns inte i den aktuella tidslinjen: '+sid)
        return s
    def valda(e): return scener if e.get('scen', 'alla')=='alla' else [scen(e['scen'])]
    def hitta(s, pid):
        if pid not in s['objekt']: raise EjTillampad('Objektet finns inte i scenen: '+pid)
        return s['objekt'][pid]
    def placera(s, o, plats, stod=None):
        if plats:
            ref=hitta(s, plats['relativt']); yaw=ref['rotation_rad'][2]; c, z=math.cos(yaw), math.sin(yaw)
            o['pos_m']=(np.array(ref['pos_m']) + np.array([[c,-z,0],[z,c,0],[0,0,1]]) @ plats['forskjutning_m']).tolist()
        elif stod:
            ref=hitta(s, stod); o['pos_m']=[*ref['pos_m'][:2], ref['pos_m'][2]+ref['matt_m'][2]/2+o['matt_m'][2]/2]
        else: raise EjTillampad('Placering saknas: ange plats eller stod; ingen position uppfinns.')
    def kameranycklar(e, s):
        lage=e['lage']; a,b=s['a'],s['b']; c=ktx[s['kx']]; V,G,seq,spar,offs=c['V'],c['G'],c['seq'],c['spar'],c['offs']; resultat=copy.deepcopy(c['rspar'])
        T=c['T']; pt=(lambda x: G @ x) if T is None else (lambda x: G @ x + T); ny=(lambda x: G @ x) if T is None else (lambda x: x)   # nyckelbilder: platsens koordinater direkt
        if lage=='folj_uppmatt':
            if e.get('mal') or e.get('inramning') or e.get('fov_grader'): raise EjTillampad('folj_uppmatt med ändrat utsnitt stöds inte.')
            return resultat
        if lage not in ('stativ', 'nyckelbilder'): raise EjTillampad('Kameraläget stöds inte: '+lage)
        fov=e.get('fov_grader')
        if fov is None and lage=='stativ': fov=40; standard.append(dict(falt='fov_grader',varde=40,orsak='CM angav ingen synvinkel'))
        if fov is not None and not 0<fov<180: raise EjTillampad('fov_grader måste vara mellan 0 och 180.')
        def nyckel(pos, mal, fov):
            # Vertikal FOV, men Blender har horisontell sensor 36 mm.
            lins=36 * R['utdata']['hojd'] / R['utdata']['bredd'] / (2*math.tan(math.radians(fov)/2))
            return dict(matris=sikta(pos, mal), lins_mm=lins, mal_m=np.asarray(mal).tolist())
        if lage=='nyckelbilder':
            keys=e.get('nyckelbilder', [])
            if not keys or any(y['t_s']<=x['t_s'] for x,y in zip(keys,keys[1:])): raise EjTillampad('Kameranycklar måste finnas och ha stigande tider.')
            for f in range(a-offs,b-offs):
                t=(f-(a-offs))/float(fps); left=max((k for k in keys if k['t_s']<=t),key=lambda k:k['t_s'],default=keys[0]); right=next((k for k in keys if k['t_s']>=t),keys[-1])
                w=0 if left is right else (t-left['t_s'])/(right['t_s']-left['t_s'])
                pos=ny((1-w)*np.array(left['pos_m'])+w*np.array(right['pos_m'])); mal=ny((1-w)*np.array(left['mal_m'])+w*np.array(right['mal_m']))
                resultat[f]=nyckel(pos,mal,(1-w)*left['fov_grader']+w*right['fov_grader'])
        else:
            mal=e.get('mal'); pos=pt(V['kam_C'][a-offs]); punkter=[]
            if mal and mal['typ']=='person':
                if mal['id'] not in seq: raise EjTillampad('Personmålet saknar rörelse.')
                punkt=mal.get('punkt')
                if punkt is None: punkt='kropp'; standard.append(dict(falt='mal.punkt',varde='kropp (c_spine2)',orsak='CM angav ingen målpunkt'))
                namn={'huvud':'c_head', 'kropp':'c_spine2'}.get(punkt)
                if namn is None: raise EjTillampad('Okänd målpunkt på person.')
                S=seq[mal['id']]; i=lednamn.index(namn)
                punkter=[pt(V['kam_C'][f]+V['kam_R'][f] @ (F @ (S['pose'][f,i,:3]/100)+S['cam_t'][f]))
                         for f in range(a-offs,b-offs) if S['inom'][f]]
                if not punkter: raise EjTillampad('Personmålet är inte synligt i scenen.')
                target=np.median(punkter,axis=0)
            elif mal and mal['typ']=='prop': target=np.array(hitta(s,mal['id'])['pos_m'])
            elif mal: raise EjTillampad('Punktmål saknar numeriska koordinater; använd nyckelbilder.')
            else:
                target=pos + G @ V['kam_R'][a-offs] @ [0.,0.,1.]
                standard.append(dict(falt='mal',varde='uppmätta kamerans blickriktning',orsak='CM angav inget mål'))
            if e.get('inramning'):
                hojd={'hel':2.1,'halv':1.25,'nara':.55}[e['inramning']]
                # För huvudmål placeras huvudet i bildens övre del, med luft ovanför.
                if mal and mal['typ']=='person' and mal.get('punkt')=='huvud': target=target-np.array([0,0,hojd*.28])
                riktning=pos-target; nr=np.linalg.norm(riktning)
                if nr<1e-8: raise EjTillampad('Kamerans position och mål sammanfaller.')
                riktning/=nr
                avstand=hojd/(2*math.tan(math.radians(fov)/2))
                # Ett stativ kan inte följa en person. Öka avståndet vid behov så
                # huvudets uppmätta bana och scenens rekvisita ryms i samma bild.
                rot=np.array(sikta(target+riktning,target))[:3,:3]
                tv=math.tan(math.radians(fov)/2); th=tv*R['utdata']['bredd']/R['utdata']['hojd']
                for prop in K['semantik']['props']:
                    # I en plats ryms bara de objekt som tagningen själv har sett (annars backar kameran för bord vid andra änden av rummet).
                    sedd=c['plats'] is None or c['tagning'] is None or any(o['id']==prop['id'] and any(x['tagning']==c['tagning'] for x in o.get('observationer',[])) for o in c['plats']['objekt'])
                    if prop['id'] in s['objekt'] and sedd:
                        o=s['objekt'][prop['id']]; punkter.append(np.array(o['pos_m']))
                for punkt in punkter:
                    x,y,z=rot.T @ (punkt-target)
                    avstand=max(avstand,z+(abs(x)+.25)/th,z+(abs(y)+.2)/tv)
                pos=target+riktning*avstand
            key=nyckel(pos,target,fov)
            for f in range(a-offs,b-offs): resultat[f]=copy.deepcopy(key)
        return resultat
    from skarmtext import edit as textedit, los as lostext
    texts = copy.deepcopy(K['semantik']['skarmtext'])
    tal_vantar = {}   # edit-id -> post; platsen i utdata avgörs först när alla scenedits är gjorda
    def talbyte(e):
        if not K['semantik']['repliker']: raise EjTillampad('Talersättning ingår inte; barkällan saknar kända repliker.')
        r = next((x for x in K['semantik']['repliker'] if x['id'] == e['replik']), None)
        if r is None: raise EjTillampad('Repliken finns inte i kalla' + (' (platshållare-id).' if e['replik'].startswith('PLATSHALLARE:') else ': ' + e['replik'] + '.'))
        if e['sprak'] != 'sv': raise EjTillampad(f'Piper-rösterna är svenska; språket {e["sprak"]!r} stöds inte.')
        if (e['rost'] or {}).get('motor') not in (None, 'piper'): raise EjTillampad('Bara röstmotorn piper stöds.')
        if e['tidspolicy'] != 'samma_lucka': raise EjTillampad('forlang_scen stöds inte: scenen förlängs inte för en ny text. Använd samma_lucka.')
        if not e['text'].strip() or e['text'] == r['text']: raise EjTillampad('Den nya texten är tom eller densamma som originalets.')
        roll = next((p['roll'] for p in K['semantik']['personer'] if p['id'] == r['talare']), None)
        try:
            import tal
            rost = (e['rost'] or {}).get('rost_id') or tal.standardrost(roll)
            lucka = round(r['slut_s'] - r['start_s'], 4)
            if snabb:
                # Snabbvägen syntetiserar inget tal. Längderna är mätta bara om båda redan ligger i talcachen; annars uppskattade efter teckenantal mot originalet.
                (nat_o, nat_n), langd_kalla = tal.langder_utan_syntes(rost, r['text'], e['text'], lucka)
            else: nat_o, nat_n = tal.mat_langd(rost, r['text']), tal.mat_langd(rost, e['text']); langd_kalla = 'matt'
        except Exception as ex:   # Piper eller röstfil saknas: editen avslås, kompileringen fortsätter
            raise EjTillampad(f'Talsyntesen kan inte köras här ({type(ex).__name__}: {ex}).')
        grans = e['max_talfaktor'] or R['ramar']['max_talfaktor'] or 1.15
        rel = nat_n / nat_o; procent = round((rel - 1) * 100, 1); regel = 'inom_gransen'
        if rel > grans:
            if langd_kalla == 'matt': raise EjTillampad(f'Nekad: den nya texten ({nat_n:.2f} s i normaltempo mot originalets {nat_o:.2f} s) kräver {procent} % högre taltakt än originalet i samma lucka ({lucka:.2f} s); gränsen är {round((grans-1)*100,1)} %.')
            regel = 'over_gransen_uppskattad'   # en uppskattning får inte ensam avslå editen; syntessteget avgör
        utfall = 'passar' if rel <= 1.03 else 'stracks'
        if snabb: ls = tempo = langd = None
        else:
            x, ls, tempo = tal.passa(rost, e['text'], lucka)
            langd = round(len(x) / tal.SR, 4)
        tecken = [max(1, len(w)) for w in e['text'].split()]; summa = sum(tecken); t0 = 0.0; ord_ny = []
        for w, n in zip(e['text'].split(), tecken):
            ord_ny.append(dict(ord=w, start_rel_s=round(t0, 4), slut_rel_s=round(t0 + lucka * n / summa, 4))); t0 += lucka * n / summa
        post = dict(edit=e['id'], replik=r['id'], talare=r['talare'], rost=dict(motor='piper', rost_id=rost), text=e['text'], text_original=r['text'],
                    kalla_slot_s=[r['start_s'], r['slut_s']], slot_langd_s=lucka, naturlig_original_s=nat_o, naturlig_ny_s=nat_n,
                    taktfaktor_mot_original=round(rel, 4), utfall=utfall, stracka_procent=max(0.0, procent), length_scale=None if ls is None else round(ls, 4), extra_tempo=None if tempo is None else round(max(1.0, tempo), 4),
                    syntetiserad_langd_s=langd, grans_taktfaktor=grans, regel=regel, ord_ny=ord_ny, ord_ny_kalla='uppskattade efter teckenlängd (som op.py), inte mätta')
        if snabb: post.update(ljud='vantar', langd_kalla=langd_kalla)   # ljudet syntetiseras i ett eget steg (tal.syntetisera_plan / bygg_ljud.py)
        tal_vantar[e['id']] = post
        return dict(replik=r['id'], utfall=utfall, stracka_procent=post['stracka_procent'], slot_langd_s=lucka, naturlig_ny_s=nat_n, naturlig_original_s=nat_o,
                    **(dict(ljud='vantar', langd_kalla=langd_kalla, regel=regel) if snabb else {}))
    def gruppedit(e, op):
        def medlemmar(gid):
            m=[x for x in scener if x['ursprung'] in grupper[gid] or x['id'] in grupper[gid]]
            if not m: raise EjTillampad('Gruppens scener finns inte i den aktuella tidslinjen: '+gid)
            return m
        ms=medlemmar(e['scen']) if e['scen'] in grupper else [scen(e['scen'])]
        if any(x['ursprung'] in skyddade for x in ms): raise EjTillampad('Gruppen innehåller ett beat som ska bevaras.')
        ids={x['id'] for x in ms}; ka=min(x['a'] for x in ms); kb=max(x['b'] for x in ms)
        korsar=[r['id'] for r in K['semantik']['repliker'] if any(r['start_s']*float(fps)<g<r['slut_s']*float(fps) for g in (ka,kb))]
        if op=='ta_bort_scen':
            for x in ms: scener.remove(x)
            return dict(grupp=e['scen'],borttaget=[[x['a'],x['b']] for x in ms],repliker_over_gransen=korsar)
        efter=None
        if e.get('efter'):
            efter=medlemmar(e['efter'])[-1] if e['efter'] in grupper else scen(e['efter'])
            if efter['id'] in ids: raise EjTillampad('En grupp kan inte flyttas efter sig själv.')
        for x in ms: scener.remove(x)
        i=scener.index(efter)+1 if efter else 0
        scener[i:i]=ms
        return dict(grupp=e['scen'] if e['scen'] in grupper else None,efter=e.get('efter'),ordning=[x['id'] for x in scener],repliker_over_gransen=korsar)
    # 0029: handlingsspåret (semantik.handling) per scen. En scen vars rutor ändrats per handling bär rutlista: en post per utruta,
    # (r0, r1, w, märke) = källrutan r0, eller en blandning (1-w)·r0 + w·r1; märke None (läst), overgang, omsamplad eller upprepning.
    spar_handling = {h['scen']: h for h in K['semantik'].get('handling', [])}
    def rutlista(s): return s['rutlista'] if s.get('rutlista') is not None else [(r, r, 0.0, None) for r in range(s['a'], s['b'])]
    def segmentet(s, sid):
        h = spar_handling.get(s['ursprung'])
        if h is None: raise EjTillampad(f'Scenen {s["id"]} har inget handlingsspår i källan.')
        g = next((x for x in h['segment'] if x['id'] == sid), None)
        if g is None: raise EjTillampad(f'Segmentet {sid} finns inte i handlingsspåret för {s["ursprung"]}.')
        return g
    def korrida(L, a, b, namn):
        idx = [i for i, x in enumerate(L) if a <= x[0] < b and x[3] in (None, 'omsamplad')]
        if not idx: raise EjTillampad(f'{namn} finns inte längre i scenens tidslinje (redan borttaget eller bortklippt).')
        if idx != list(range(idx[0], idx[-1] + 1)): raise EjTillampad(f'{namn} är inte sammanhängande i scenens tidslinje efter tidigare ändringar.')
        return idx[0], idx[-1] + 1
    def overgang(x, y, k):
        return [(x[0] if x[2] < .5 else x[1], y[0] if y[2] < .5 else y[1], j / (k + 1), 'overgang') for j in range(1, k + 1)]
    def handlingsedit(e, op):
        s = scen(e['scen'])
        if s['ursprung'] in skyddade: raise EjTillampad('Scenen innehåller ett beat som ska bevaras.')
        if not flerklipp: raise EjTillampad('Handlingsändringar kräver en plan med scener per tagning (flerklipp).')
        if s.get('hall'): raise EjTillampad('Handlingsändring i en scen som redan hålls stöds inte ännu.')
        L = list(rutlista(s)); n0 = len(L)
        if op == 'ta_bort_handling':
            g = segmentet(s, e['segment']); i0, i1 = korrida(L, *g['rutor'], 'Segmentet ' + g['id'])
            if i0 == 0 and i1 == len(L): raise EjTillampad('Segmentet är hela scenen; ta bort scenen i stället.')
            lage = e.get('overgang') or 'korsovertoning'; k = e.get('overgang_rutor') or 6
            fore, efter = (L[i0 - 1] if i0 > 0 else None), (L[i1] if i1 < len(L) else None)
            if lage == 'klipp' or fore is None or efter is None: mitt = []
            elif lage == 'hall': mitt = [(fore[0], fore[1], fore[2], 'overgang')] * k
            else: mitt = overgang(fore, efter, k)
            L[i0:i1] = mitt
            andring = dict(segment=g['id'], handling=(g.get('handling') or {}).get('varde'), borttagna_kallrutor=list(g['rutor']), overgang=lage if mitt else 'klipp',
                           overgang_rutor=len(mitt), rutor_fore=n0, rutor_efter=len(L), status='övergången är interpolerad, inte läst' if mitt and lage == 'korsovertoning' else None)
        elif op == 'tempo_handling':
            g = segmentet(s, e['segment']); i0, i1 = korrida(L, *g['rutor'], 'Segmentet ' + g['id']); run = L[i0:i1]; n = len(run)
            m = max(1, round(n * e['faktor'])); nara = e.get('samplning') == 'narmast'; ny = []
            for j in range(m):
                x = 0.0 if m == 1 else j * (n - 1) / (m - 1); lo = int(math.floor(x)); hi = min(n - 1, lo + 1); w = x - lo
                p, q = run[lo], run[hi]
                if nara: ny.append((p[0], p[0], 0.0, 'omsamplad') if w < .5 else (q[0], q[0], 0.0, 'omsamplad'))
                else: ny.append((p[0], q[0], w, 'omsamplad') if w > 1e-9 else (p[0], p[0], 0.0, 'omsamplad'))
            L[i0:i1] = ny
            andring = dict(segment=g['id'], handling=(g.get('handling') or {}).get('varde'), faktor=e['faktor'], rutor_segment_fore=n, rutor_segment_efter=m,
                           samplning='narmast' if nara else 'interpolerad', rutor_fore=n0, rutor_efter=len(L), status='omsamplade rutor är interpolerade, inte lästa')
        else:
            g0, g1 = segmentet(s, e['fran']), segmentet(s, e['till'])
            if g1['rutor'][1] <= g0['rutor'][0]: raise EjTillampad('till ligger före fran i handlingsspåret.')
            i0, i1 = korrida(L, g0['rutor'][0], g1['rutor'][1], f'Segmenten {g0["id"]}–{g1["id"]}'); run = L[i0:i1]; k = e.get('overgang_rutor') or 6; ny = []
            for _ in range(e['antal'] - 1): ny += overgang(run[-1], run[0], k) + [(x[0], x[1], x[2], 'upprepning') for x in run]
            L[i1:i1] = ny
            andring = dict(fran=g0['id'], till=g1['id'], antal=e['antal'], rutor_foljd=len(run), overgang_rutor=k, rutor_fore=n0, rutor_efter=len(L),
                           status='andra varvet är samma rörelse (upprepning), övergången interpolerad')
        s['rutlista'] = L
        return {k_: v for k_, v in andring.items() if v is not None}
    tidsbeslut = {}
    for e in R['edits']:
        # En edit är atomisk: även ett fel i den sista scenen rullar tillbaka hela editen.
        fore=copy.deepcopy((scener,pers,texts)); op=e['op']; andring={}; standard.clear()
        try:
            from handelser import los_edit
            try:
                e, tidsbeslut_edit = los_edit(e, K['semantik'].get('handelser', []), K['tidsbas']['langd_s'])
            except ValueError as ex:
                raise EjTillampad(str(ex)) from ex
            if e['ursprung']['typ']=='harness-forslag' and e['ursprung'].get('godkand_av_cm') is not True:
                raise EjTillampad('Harnessförslaget är inte godkänt av CM.')
            if op=='lagg_till_replik': raise EjTillampad('Att lägga till repliker ingår inte; barkällan saknar kända repliker.' if not K['semantik']['repliker'] else 'Att lägga till repliker ingår inte.')
            if op=='byt_replik': andring=talbyte(e)
            elif op=='skarmtext':
                try: textedit(texts,e,K['semantik']['scener'])
                except ValueError as ex: raise EjTillampad(str(ex)) from ex
                andring=dict(skarmtext_id=e['skarmtext_id'],atgard=e['atgard'])
            elif op=='casta':
                if e['person'] not in pers: raise EjTillampad('Personen saknas.')
                if any(v is not None for k,v in e['utseende'].items() if k!='troja_farg') or e.get('rost'): raise EjTillampad('MHR-förhandsvisningen stöder endast helkroppsfärg och rollnamn.')
                p=pers[e['person']]; farg=e['utseende'].get('troja_farg') or p['farg']
                if not re.fullmatch('#[0-9a-fA-F]{6}', farg): raise EjTillampad('Färg måste vara #RRGGBB.')
                roll=e['kundroll']['namn']
                if farg.lower()==p['farg'].lower() and roll==p['roll']: raise EjTillampad('Castingen ändrar ingenting: ingen ny färg (troja_farg) och samma rollnamn.')
                p.update(farg=farg.lower(), roll=roll); andring=copy.deepcopy(p)
            elif op in ('ta_bort_scen','flytta_scen') and (e['scen'] in grupper or e.get('efter') in grupper):
                andring=gruppedit(e,op)
            elif op in ('trimma_scen','ta_bort_scen','flytta_scen','duplicera_scen'):
                s=scen(e['scen'])
                if s['ursprung'] in skyddade: raise EjTillampad('Scenen innehåller ett beat som ska bevaras.')
                if op=='trimma_scen' and s.get('rutlista') is not None: raise EjTillampad('Trimning efter en handlingsändring i samma scen stöds inte ännu; lägg trimningen först.')
                if op=='trimma_scen' and e['lage']=='hall_sista':
                    if e.get('start_s') is not None: raise EjTillampad('hall_sista förlänger bara slutet; start_s ska utelämnas.')
                    if e.get('slut_s') is None: raise EjTillampad('hall_sista kräver slut_s.')
                    h=math.floor(Fraction(str(e['slut_s']))*fps+Fraction(1,2))-s['b']-s.get('hall',0)   # utan ruta():s tak vid källans slut
                    if h<=0: raise EjTillampad('hall_sista förlänger bara förbi scenens nuvarande slut; använd klipp_slut för att korta.')
                    if s.get('hall',0)+h>s['b']-s['a']: raise EjTillampad('Hållningen får inte vara längre än scenens egna rutor.')
                    s['hall']=s.get('hall',0)+h; andring=dict(fore=[s['a'],s['b']],hall_rutor=s['hall'],kallruta=s['b']-1,status='hållen, inte läst')
                elif op=='trimma_scen':
                    if e['lage']=='stracka': raise EjTillampad('Tidssträckning stöds inte.')
                    if e.get('start_s') is None and e.get('slut_s') is None: raise EjTillampad('Trimningen saknar start_s och slut_s och ändrar ingenting.')
                    a=s['a'] if e.get('start_s') is None else ruta(e['start_s']); b=s['b'] if e.get('slut_s') is None else ruta(e['slut_s'])
                    if not s['a']<=a<b<=s['b']: raise EjTillampad('Trimningen är tom eller utanför nuvarande intervall.')
                    if (a,b)==(s['a'],s['b']): raise EjTillampad('Trimningen ändrar inte scenens intervall.')
                    if e['lage']=='replik_sakert':
                        for r in K['semantik']['repliker']:
                            for word in r['ord'] or [r]:
                                if any(word['start_s'] < t < word['slut_s'] for t in (a/float(fps),b/float(fps))): raise EjTillampad('Trimningen skulle klippa ett ord eller en replik.')
                    andring=dict(fore=[s['a'],s['b']],efter=[a,b]); s.update(a=a,b=b)
                    if s.get('kamera_edit'): s['kamera']=kameranycklar(s['kamera_edit'],s)
                elif op=='ta_bort_scen': scener.remove(s); andring=dict(borttaget=[s['a'],s['b']])
                else:
                    if e.get('efter')==s['id'] and op=='flytta_scen': raise EjTillampad('En scen kan inte flyttas efter sig själv.')
                    efter=scen(e['efter']) if e.get('efter') else (s if op=='duplicera_scen' else None)
                    if op=='duplicera_scen':
                        if any(x['id']==e['ny_id'] for x in scener): raise EjTillampad('Scen-id finns redan.')
                        s=copy.deepcopy(s); s['id']=e['ny_id']; s['ljud']=e['med_ljud']
                    else: scener.remove(s)
                    scener.insert(scener.index(efter)+1 if efter else 0,s); andring=dict(ordning=[s['id'] for s in scener])
            elif op in ('byt_prop','ta_bort_prop') and e['prop'] in dekl_props:
                d=dekl_props[e['prop']]
                if e.get('scen','alla')!='alla' and e['scen'] not in d['deklaration']['scener']: raise EjTillampad(f'Föremålet {e["prop"]} syns inte i scenen {e["scen"]}.')
                if e.get('tid'): raise EjTillampad('Tidsintervall stöds inte för deklarerade föremål; ange scen eller alla.')
                foremal_edits.append(e); andring=dict(prop=e['prop'],former=d['deklaration']['former'],scen=e.get('scen','alla'),vantar='tillämpas på planens föremål efter lyftet')
            elif op in ('byt_prop','lagg_till_prop','flytta_prop','ta_bort_prop'):
                tillgang = tillgangspost(e) if e.get('tillgang_id') else None
                from proptid import andra as andra_prop
                span = (ruta(tidsbeslut_edit['kalla_s'].get('start_s', 0)), ruta(tidsbeslut_edit['kalla_s'].get('slut_s', K['tidsbas']['langd_s']))) if tidsbeslut_edit else (0, N)
                for s in valda(e):
                    if op!='lagg_till_prop' and e.get('scen','alla')=='alla' and e['prop'] not in s['objekt']: continue
                    def redigera(o):
                        if op=='lagg_till_prop':
                            if o is not None: raise EjTillampad('Objekt-id finns redan i det valda intervallet.')
                            from propbank import BANK
                            if e['typ'] in BANK:
                                from propplan import ny
                                o=ny(e)
                                if e.get('faste'):
                                    if e['faste']['person'] not in {m['person'] for m in ktx[s['kx']]['ms']} or e['faste']['led'] not in lednamn:
                                        raise EjTillampad('Handfästets person eller led saknas i scenen.')
                                else: placera(s,o,e.get('plats'),e.get('stod'))
                            else:
                                if e.get('faste'): raise EjTillampad('Handfäste kräver en typ i propbanken.')
                                o=dict(id=e['ny_id'],namn='rum:'+e['typ']+':'+e['ny_id'],typ='lada',matt_m=storlek(e.get('matt_m')),rotation_rad=[0,0,0],farg='#e2ac46',top_slope=0)
                                placera(s,o,e.get('plats'),e.get('stod'))
                        else:
                            if o is None: raise EjTillampad('Objektet finns inte i det valda intervallet: '+e['prop'])
                            if op=='ta_bort_prop': return None
                            if op=='flytta_prop':
                                if not e['till']: raise EjTillampad('Flytt kräver en explicit placering.')
                                placera(s,o,e['till'])
                                if o['typ']=='rekvisita': o['propdata']['lage']='explicit'
                            elif o['typ']=='rekvisita':
                                from propplan import byt
                                try: byt(o,e['ny_typ'],e.get('matt_m'))
                                except ValueError as exc: raise EjTillampad(str(exc))
                            else:
                                o.update(namn='rum:'+e['ny_typ']+':'+e['prop'],farg='#e2ac46')
                                if e.get('matt_m') is not None: o['matt_m']=storlek(e['matt_m'])
                        if tillgang: o['tillgang']=copy.deepcopy(tillgang)
                        return o
                    pid=e.get('ny_id') if op=='lagg_till_prop' else e['prop']
                    versions=bool(s['objekt'].get(pid,{}).get('_propversioner'))
                    changed=andra_prop(s,pid,span,redigera)
                    if changed is not None:
                        if tidsbeslut_edit or versions: andring[s['id']]=changed
                        else: andring[s['id']]=copy.deepcopy(s['objekt'][pid]) if op!='ta_bort_prop' else dict(borttaget=pid)
                if not andring: raise EjTillampad('Händelseintervallet träffar ingen vald scen.')
            elif op=='byt_miljo':
                # Platsbyte: ersätt platsens geometri, behåll ankarnas namn. Personerna följer sina ankare: scenens transform räknas om så att
                # det bundna ankaret i källplatsen hamnar på samma namn i den nya platsen. Banken är en mapp med plats-JSON (plats/1).
                mallid=e['rum'].get('rumsmall_id') or e['rum'].get('tillgang_id')
                platta = e['rum']['kalla'] in ('platta','upload') and not e['rum'].get('rumsmall_id') and bool(mallid)
                if not platta and (e['rum']['kalla']!='bank' or not mallid): raise EjTillampad('Bara kalla=bank med tillgang_id eller rumsmall_id, eller kalla=platta/upload med tillgang_id, stöds; övriga källor kräver en färdig mall.')
                bf=platsbank/(mallid+'.json')
                if not platta and not bf.is_file(): raise EjTillampad(f'Platsen {mallid!r} finns inte i platsbanken ({platsbank}).')
                if platta and not bf.is_file():
                    # Ingen byggd plats: planen bär vilken lokal som gäller. Scenens uppmätta rum står kvar som platshållare, märkt ej_byggd.
                    for s in valda(e):
                        s['lokal']=dict(tillgang_id=mallid,kalla=e['rum']['kalla'],geometri='ej_byggd',beskrivning=e['rum'].get('beskrivning'),ersatter=(ktx[s['kx']]['plats'] or {}).get('id'),
                                        anmarkning='Bakgrundsplåt eller uppladdad bild. Ingen plats är byggd av den; scenens uppmätta rum står kvar som platshållare i planen.')
                        andring[s['id']]=dict(lokal=mallid,geometri='ej_byggd')
                else:
                    raw=ladda(bf)
                    if 'rumsmall_ref' in raw: bf=(bf.parent/raw['rumsmall_ref']).resolve(); raw=ladda(bf)
                    try:
                        if raw.get('schema_version')=='rumsmall/1':
                            mall,hash_mall=las_mall(bf);ny=som_plats(mall);ny['rumsmall']['sha256']=hash_mall
                        else: ny=raw
                    except ValueError as fel: raise EjTillampad('Ogiltig rumsmall: '+str(fel)) from fel
                    karta={a['fran']:a['till'] for a in e.get('ankare',[])}; nyank={a['id']:a for a in ny['ankare']}
                    for s in valda(e):
                        c=ktx[s['kx']]
                        if c['plats'] is None: raise EjTillampad(f'Scenen {s["id"]} har ingen plats; byt_miljo gäller platser med ankare.')
                        ksc=next(x for x in K['semantik']['scener'] if x['id']==s['ursprung']); gamla={a['id']:a for a in c['plats']['ankare']}
                        for bind in ksc.get('bindningar',[]):
                            aid=karta.get(bind['ankare'],bind['ankare'])
                            if aid not in nyank: raise EjTillampad(f'Scenen {s["id"]}: ingen bunden person kan följa med utan ankaret {aid}.')
                            if nyank[aid]['typ']!=gamla[bind['ankare']]['typ']: raise EjTillampad(f'Ankaret {aid} har fel typ i kundmallen.')
                        val=next(((b,karta.get(b['ankare'],b['ankare'])) for b in sorted(ksc.get('bindningar',[]),key=lambda b:b['person']) if b['ankare'] in gamla and karta.get(b['ankare'],b['ankare']) in nyank),None)
                        if val is None: raise EjTillampad(f'Scenen {s["id"]}: ingen bunden person har ett ankare med motsvarande namn i {ny["id"]}; personerna kan inte följa med.')
                        b,till=val; Mn=ankarpose(nyank[till])@np.linalg.inv(ankarpose(gamla[b['ankare']]))@c['M']
                        nyckel=f'{s["id"]}#{e["id"]}'; ktx[nyckel]=nc=kontext(ksc,Mover=Mn,platsover=ny)
                        nc['ankarkarta']=karta
                        nc['person_transformer']={bind['person']:(ankarpose(nyank[karta.get(bind['ankare'],bind['ankare'])])@np.linalg.inv(ankarpose(gamla[bind['ankare']]))@c.get('person_transformer',{}).get(bind['person'],c['M'])).tolist() for bind in ksc.get('bindningar',[])}
                        s['kx']=nyckel; s['objekt']=copy.deepcopy(nc['objekt']); s['kamera']=copy.deepcopy(nc['rspar']); s.pop('lokal',None)
                        if s.get('kamera_edit'): s['kamera']=kameranycklar(s['kamera_edit'],s)
                        andring[s['id']]=dict(plats_fran=c['plats']['id'],plats_till=ny['id'],ref_person=b['person'],ankare_fran=b['ankare'],ankare_till=till,
                                              ankare_utan_motsvarighet=[i for i in gamla if karta.get(i,i) not in nyank])
            elif op in ('ta_bort_handling','tempo_handling','upprepa_handling'):
                if scen(e['scen']).get('spegling'): raise EjTillampad('Handlingsändring efter en speglad hand i samma scen stöds inte ännu; lägg den först.')
                andring=handlingsedit(e, op)
            elif op=='satt_frihetsgrad':
              try:
                # 0031: nivå 1 ur liggaren. kroppsdel: armarna speglas i förloppets rutor, föremålet i handen byter handled, IK-fönster märks.
                s=scen(e['scen'])
                if e.get('person') and e['person'] not in pers:
                    # 0033: en person som inte är läst (platshållare i scenbygget): variant i bygget (objekt['varianter']['kroppsdel'])
                    if e['parameter']!='kroppsdel': raise EjTillampad('Bara kroppsdel stöds för en platshållarperson.')
                    s.setdefault('scenbygge_val',{})[e['person']]=e['varde']
                    andring=dict(frihetsgrad=e['frihetsgrad'],person=e['person'],varde=e['varde'],status='variant i scenbygget (antagen platshållare)')
                    raise _Klar()
                if not flerklipp: raise EjTillampad('satt_frihetsgrad kräver en plan med scener per tagning.')
                if s.get('rutlista') is not None: raise EjTillampad('Spegling efter en handlingsändring i samma scen stöds inte ännu; lägg speglingen först.')
                if e['varde']=='hoger' and not s.get('spegling'): raise EjTillampad('Handlingen görs redan med höger hand.')
                a_,b_=e['rutor']
                if not (s['a']<=a_<b_<=s['b']): raise EjTillampad('Rutorna ligger utanför scenen.')
                if s.get('spegling') and e['varde']=='hoger': s.pop('spegling'); andring=dict(spegling='borttagen')
                else:
                    s['spegling']=dict(rutor=[a_,b_],mal=e.get('mal') or {},person=e.get('person'),overgang=6 if e.get('overgang_rutor') is None else e['overgang_rutor'],frihetsgrad=e['frihetsgrad'])
                    andring=dict(frihetsgrad=e['frihetsgrad'],parameter='kroppsdel',varde=e['varde'],rutor=[a_,b_],ik_fonster=e.get('mal') or {},status='utförd_niva_1: armarna speglade, handföremålet till vänster handled; IK i bygget')
              except _Klar: pass
            elif op=='renderkamera':
                s=scen(e['scen']); s['kamera']=kameranycklar(e,s); s['kamera_edit']=e
                andring=dict(kallintervall=[s['a'],s['b']],lage=e['lage'],forsta_nyckel=s['kamera'][s['a']-ktx[s['kx']]['offs']])
                if standard: andring['standardvarden']=copy.deepcopy(standard)
            else: raise EjTillampad('Operationen stöds inte av denna byggare.')
            if tidsbeslut_edit: tidsbeslut[e['id']] = tidsbeslut_edit
            tillampat.append(dict(id=e['id'],op=op,andring=andring))
        except (EjTillampad, ArithmeticError, KeyError, IndexError, TypeError, np.linalg.LinAlgError) as ex:
            # En trasig edit får aldrig avbryta hela kompileringen.
            scener,pers,texts=fore; ej.append(dict(id=e['id'],op=op,orsak=str(ex) if isinstance(ex,EjTillampad) else f'Editen kunde inte tolkas ({type(ex).__name__}: {ex}).'))
    if not scener: raise ValueError('Alla scener togs bort; det finns inga rutor att rendera.')
    rutor, intervall, renderkamera, byggobjekt, delplan = [], [], [], [], []
    iv_scen = []   # ett intervall per scen (utan hållna rutor), för de steg som parar scener och intervall
    iv_ut={}; platsmodus=all(ktx[s['kx']]['plats'] is not None for s in scener)
    for s in scener:
        L=s.get('rutlista')
        if L is not None:
            # 0029: scenens rutor efter handlingsändringar. Lästa rutor i följd behåller ljudet; övergångar och omsamplade rutor är tysta.
            start=len(rutor); rutor.extend(int(x[0] if x[2]<.5 else x[1]) for x in L); slut=len(rutor); j=0
            while j<len(L):
                k_=j; las=L[j][3] is None and L[j][2]==0
                while las and k_+1<len(L) and L[k_+1][3] is None and L[k_+1][2]==0 and L[k_+1][0]==L[k_][0]+1: k_+=1
                if not las:
                    while k_+1<len(L) and L[k_+1][3]==L[j][3] and not (L[k_+1][3] is None and L[k_+1][2]==0): k_+=1
                intervall.append(dict(ut=[start+j,start+k_+1],kalla=[L[j][0],L[k_][0]+1],ljud=bool(s['ljud'] and las),**({} if las else dict(handling=L[j][3]))))
                j=k_+1
        else:
            start=len(rutor); rutor.extend(range(s['a'],s['b'])); slut=len(rutor)
            intervall.append(dict(ut=[start,slut],kalla=[s['a'],s['b']],ljud=s['ljud']))
        if flerklipp:
            c=ktx[s['kx']]
            delplan.append(dict(id=s['id'],ut=[start,slut],kalla=[s['a'],s['b']],lokal_start=s['a']-c['offs'],
                                varld=kameror[next(x['kamera'] for x in K['semantik']['scener'] if x['id']==s['ursprung'])]['spar_metrisk']['sokvag'],
                                personer=[dict(id=m['person'],ingest_id=m.get('ingest_id'),rorelse=m['rorelse']['sokvag'],
                                               **({'dolda_fotter':copy.deepcopy(m['dolda_fotter'])} if m.get('dolda_fotter') else {})) for m in c['ms']]))
            if next(x for x in K['semantik']['scener'] if x['id']==s['ursprung']).get('kamera_bindning'):
                delplan[-1]['kamera_bindning']=copy.deepcopy(next(x for x in K['semantik']['scener'] if x['id']==s['ursprung'])['kamera_bindning'])
            if s.get('lokal'): delplan[-1]['lokal']=copy.deepcopy(s['lokal'])
            if c['M'] is not None: delplan[-1].update(plats_id=c['plats_id'],till_plats=c['M'].tolist())
            if c['plats'] and c['plats'].get('rumsmall'):
                sk=next(x for x in K['semantik']['scener'] if x['id']==s['ursprung'])
                bind={x['person']:x for x in sk.get('bindningar',[])}
                an={a['id']:a for a in c['plats']['rumsmall']['ankare']}
                behall=[]; uteslut=[]
                for pm in delplan[-1]['personer']:
                    b=bind.get(pm['id']); aid=c.get('ankarkarta',{}).get(b['ankare'],b['ankare']) if b else None
                    if b and aid in an:
                        pm['ankare']=aid
                        cut=Path(pm['rorelse']).with_name('utsnitt_'+str(pm.get('ingest_id') or Path(pm['rorelse']).stem[8:])+'.json')
                        only_upper=aid in ('sta_bakom','kundsida') and cut.exists() and ladda(cut).get('endast_overkropp',False)
                        if only_upper:
                            pm['stod_utelamnat']=dict(status='antagen',orsak='Endast överkropp: binds till disksida, men inget golv- eller fotstöd härleds ur dolda ben.')
                        else:
                            from tropassning import scenpassa_ankare
                            pm['stod']=scenpassa_ankare(an[aid],c['plats']['rumsmall'],sk['id'])
                            if pm['id'] in benlangder: pm['benlangder_m']=benlangder[pm['id']]
                        syn=next((v for v in c['plats']['golv'].get('matning',{}).get('fotsynlighet',[])
                                  if v['tagning']==c['tagning'] and v['ingest_id']==pm.get('ingest_id')),None)
                        if syn:
                            skydd={str(v['ruta']):v['synliga_knan'] for v in syn['per_ruta'] if any(v.get('synliga_knan',[]))}
                            if skydd:pm['skyddade_knan']=skydd
                        if pm['id'] in c.get('person_transformer',{}) and not np.allclose(c['person_transformer'][pm['id']],c['M'],atol=1e-10):pm['till_plats']=c['person_transformer'][pm['id']]
                        behall.append(pm)
                    elif pers[pm['id']]['roll'] is None:
                        uteslut.append(dict(person=pm['id'],orsak='Ingen roll eller bunden mallsits inom platsstegets tolerans. Renderas inte utan stöd.'))
                    else: behall.append(pm)
                delplan[-1]['personer']=behall;delplan[-1]['utelamnade']=uteslut
        if flerklipp and s.get('spegling'):
            # 0031: speglade armar i förloppets rutor (sekvensens lokala rutor), en kopia av sekvensen i datacache/spegling
            sp_=s['spegling']; c=ktx[s['kx']]; d_=delplan[-1]; pid_=sp_['person'] or (d_['personer'][0]['id'] if d_['personer'] else None)
            for pm in d_['personer']:
                if pm['id']==pid_: pm['rorelse']=spegla_armar(pm['rorelse'],sp_['rutor'][0]-c['offs'],sp_['rutor'][1]-c['offs'],sp_['overgang'],Path(__import__('datacache').CACHE)/'spegling')
            d_['spegling']=dict(person=pid_,rutor_kalla=sp_['rutor'],ut=[start+sp_['rutor'][0]-s['a'],start+sp_['rutor'][1]-s['a']],status='utförd_niva_1',
                                ik=[dict(namn=k,ben='l_wrist',mal_ben='r_wrist',ut=[start+v[0]-s['a'],start+v[1]-s['a']]) for k,v in sp_['mal'].items()],frihetsgrad=sp_['frihetsgrad'])
        if L is not None:
            c=ktx[s['kx']]; offs_=c['offs']; n_=len(c['V']['kam_R']); d_=delplan[-1]; ut_mapp=Path(__import__('datacache').CACHE)/'handling'
            d_.update(kalla=[min(x[0] for x in L),max(x[1] for x in L)+1],lokal_start=0,varld=omsampla(d_['varld'],L,offs_,n_,ut_mapp),kalla_scen=s['ursprung'],
                      handlingsrutor=sammanfatta_rutlista(L,start))
            for pm in d_['personer']:
                pm['rorelse']=omsampla(pm['rorelse'],L,offs_,n_,ut_mapp)
                if pm.get('skyddade_knan'): pm['skyddade_knan']={str(j):pm['skyddade_knan'][str(x[0]-offs_)] for j,x in enumerate(L) if str(x[0]-offs_) in pm['skyddade_knan']}
                if pm.get('dolda_fotter'): pm.pop('dolda_fotter'); d_.setdefault('utelamnat',[]).append(dict(person=pm['id'],falt='dolda_fotter',orsak='per ruta i källans ordning; följer inte med omsamplade rutor'))
            renderkamera.extend(blanda_nyckel(s['kamera'][x[0]-offs_],s['kamera'][x[1]-offs_],x[2]) for x in L)
            iv_scen.append(dict(ut=[start,slut],kalla=[s['a'],s['b']],ljud=s['ljud'],rutlista=True))
        else:
            renderkamera.extend(s['kamera'][s['a']-ktx[s['kx']]['offs']:s['b']-ktx[s['kx']]['offs']])
            iv_scen.append(intervall[-1])
        if s.get('hall'):
            # Sista lästa rutan: den sista där scenens alla personer är lästa (inom). Saknas en sådan hålls scenens sista ruta.
            c=ktx[s['kx']]; h=s['hall']; lok=s['b']-1-c['offs']
            while lok>s['a']-c['offs'] and c['seq'] and not all(bool(q['inom'][lok]) for q in c['seq'].values()): lok-=1
            kr=lok+c['offs']; rutor.extend([kr]*h); renderkamera.extend(copy.deepcopy(s['kamera'][lok]) for _ in range(h))
            intervall.append(dict(ut=[slut,slut+h],kalla=[kr,kr+1],ljud=False,hall=True))
            hallna.append(dict(scen=s['id'],ut=[slut,slut+h],kallruta=kr,lokal=lok,delplan=copy.deepcopy(delplan[-1]) if flerklipp else None))
            slut+=h
        iv_ut[s['id']]=[start,slut]
        if not platsmodus:
            for o in s['objekt'].values():
                from proptid import byggposter
                for o in byggposter(o,s,[start,slut]):
                    if flerklipp or o['typ']=='rekvisita': o['scen']=s['id']
                    byggobjekt.append(o)
    if platsmodus:
        # Platsens rum byggs en gång: ett objekt som finns oförändrat i alla scener syns hela tiden; annars läggs det scen för scen.
        for i in dict.fromkeys(i for s in scener for i in s['objekt']):
            fk=[(s,s['objekt'][i]) for s in scener if i in s['objekt']]
            if not any('_propversioner' in o for _,o in fk) and fk[0][1]['typ']!='rekvisita' and len(fk)==len(scener) and all(o==fk[0][1] for _,o in fk):
                o=copy.deepcopy(fk[0][1]); o['synlig_ut']=[0,len(rutor)]; byggobjekt.append(o)
            else:
                for s,o in fk:
                    from proptid import byggposter
                    for o in byggposter(o,s,iv_ut[s['id']]):
                        if flerklipp or o['typ']=='rekvisita': o['scen']=s['id']
                        byggobjekt.append(o)
    # Ersättningsreplikernas plats i utdata. En replik får bara bytas om luckan ligger hel inom en sammanhängande, ljudsatt bit av utdata.
    korn = []
    for iv in [x for x in intervall if not x.get('hall')]:
        if korn and korn[-1]['ljud'] == iv['ljud'] and korn[-1]['kalla'][1] == iv['kalla'][0] and korn[-1]['ut'][1] == iv['ut'][0]:
            korn[-1]['kalla'][1] = iv['kalla'][1]; korn[-1]['ut'][1] = iv['ut'][1]
        else: korn.append(dict(ut=list(iv['ut']), kalla=list(iv['kalla']), ljud=iv['ljud']))
    tal_plan = []; ordning = {i: n for n, i in enumerate(ids_fore) if isinstance(i, str)}; senaste = {}
    for eid, post in tal_vantar.items(): senaste[post['replik']] = eid
    for eid, post in tal_vantar.items():
        ap = next(x for x in tillampat if x['id'] == eid); orsak = None; platser = []
        if senaste[post['replik']] != eid: orsak = f'Ersatt av den senare editen {senaste[post["replik"]]} på samma replik.'
        else:
            s0, s1 = post['kalla_slot_s']
            for kb in korn:
                if kb['ljud'] and kb['kalla'][0] / float(fps) <= s0 + 1e-6 and s1 <= kb['kalla'][1] / float(fps) + 1e-6:
                    platser.append(round(kb['ut'][0] / float(fps) + (s0 - kb['kalla'][0] / float(fps)), 4))
            if not platser: orsak = 'Luckan ligger inte hel i utdata: scenen är bortklippt eller trimmad, ligger i en tyst scen, eller klipps mitt i luckan av en scengräns som inte längre är sammanhängande.'
        if orsak:
            tillampat.remove(ap); ej.append(dict(id=eid, op='byt_replik', orsak=orsak))
        else:
            for u0 in platser: tal_plan.append(dict(post, ut_slot_s=[u0, round(u0 + post['slot_langd_s'], 4)]))
            if post.get('regel') == 'over_gransen_uppskattad': varningar.append(f'Repliken {post["replik"]} ({eid}): uppskattad taktfaktor {post["taktfaktor_mot_original"]:.2f} över gränsen {post["grans_taktfaktor"]:.2f}. Syntessteget (tal.syntetisera_plan) avgör.')
            ap['andring']['ut_slot_s'] = [[u0, round(u0 + post['slot_langd_s'], 4)] for u0 in platser]
    for a_ in avvisade: ordning[a_['id']] = a_['index']; ej.append(dict(id=a_['id'], op=a_['op'], orsak=a_['orsak']))
    tillampat.sort(key=lambda x: ordning[x['id']]); ej.sort(key=lambda x: ordning[x['id']])
    utdata=copy.deepcopy(R['utdata']); utdata.update(antal_rutor=len(rutor),render_motor='BLENDER_WORKBENCH',upplosning_procent=100,
                                                   bildformat='PNG',farglage='RGBA',transparent=True)
    plan=dict(schema_version='plan/1',koordinater='Blender: Z upp, meter, radianer; kameramatris world_from_camera, lokal -Z blick, Y upp.',
                tidskarta=intervall,kallrutor=rutor,personer=list(pers.values()),objekt=byggobjekt,
                renderkamera=dict(lage='upplosta_nycklar',sensor_bredd_mm=36,nycklar=renderkamera),
                utdata=utdata,matning=matning,kallvideo=str((kallfil.parent/K['klipp']['video']['sokvag']).resolve()),
                kallbild_bredd=K['klipp']['video']['bredd'],tillampat=tillampat,ej_tillampat=ej,varningar=varningar,
                beslut=['Halvbild = minst 1,25 m vertikalt utsnitt; huvudmål ligger 28 % över bildcentrum. Stativ vidgas för huvudets bana och rekvisita, med 25 cm sidomarginal.',
                        'Propbyte och tillägg visas som ockragula lådor; mått behålls om matt_m är null.',
                        'Ingen talersättning: blandat_duckad använder bara tidsmappat originalljud.'])
    from handelser import till_plan, intervall_ut
    if K['semantik'].get('handelser'):
        plan['handelser'] = till_plan(K['semantik']['handelser'], scener, iv_scen, float(fps), ruta)
    for applied in tillampat:
        if applied['id'] in tidsbeslut:
            timing = tidsbeslut[applied['id']]
            bounds = timing['kalla_s']
            occurrences = intervall_ut(ruta(bounds.get('start_s', 0)), ruta(bounds.get('slut_s', K['tidsbas']['langd_s'])), scener, iv_scen, float(fps))
            selected = next(e for e in R['edits'] if e['id'] == applied['id']).get('scen', 'alla')
            timing['forekomster'] = [x for x in occurrences if selected == 'alla' or x['scen'] == selected]
            applied['andring']['tid'] = timing
    reks=[o for o in plan['objekt'] if o['typ']=='rekvisita']
    if reks:
        plan['props']=reks
        plan['beslut'][1]='Rekvisita byggs med parametrisk bankform och upplöst hand-/ytfäste. Grepp, djup och dolda sidor är antagna; mätregion och ursprung finns per prop.'
        plan['objekt']=[o for o in plan['objekt'] if o['typ']!='rekvisita']
    resolved_text=lostext(texts,scener,iv_scen,tal_plan,float(fps),K['klipp']['video']['bredd'],K['klipp']['video']['hojd'])
    if any(s.get('rutlista') is not None for s in scener):
        # 0029: i en scen med ändrade handlingar syns texten i de utrutor vars källruta ligger i textens källintervall.
        omsamp={s['id']:s for s in scener if s.get('rutlista') is not None}; kvar=[]
        for x in resolved_text:
            if x['scen'] not in omsamp: kvar.append(x); continue
            u0,u1=iv_ut[x['scen']]; ta,tb=round(x['start_s']*float(fps)),round(x['slut_s']*float(fps)); js=[j for j in range(u0,u1) if ta<=rutor[j]<tb]
            if js: x['ut']=[min(js),max(js)+1]; kvar.append(x)
        resolved_text=kvar
    if resolved_text:plan['skarmtext']=resolved_text
    if platsmodus:
        anv={ktx[s['kx']]['plats']['id']:ktx[s['kx']]['plats'] for s in scener}
        plan['plats']=[dict(id=i,golv_hojd_m=pl['golv']['hojd_m'],ankare=pl['ankare'],objekt=[o['id'] for o in pl['objekt']],scener=[s['id'] for s in scener if ktx[s['kx']]['plats']['id']==i])
                        for i,pl in anv.items()]
        for p in plan['plats']:
            pl=anv[p['id']]
            if pl.get('deklarerat'):p['deklarerat']=copy.deepcopy(pl['deklarerat'])
            if pl.get('rumsmall'):
                p['rumsmall']=copy.deepcopy(pl['rumsmall']);p['ankare']=copy.deepcopy(pl['rumsmall']['ankare'])
                p['uppmatta_ankare']=copy.deepcopy(pl['ankare']);p['utelamnade']=copy.deepcopy(pl.get('utelamnade',[]))
        if any(pl.get('rumsmall') for pl in anv.values()):
            plan['beslut'].append('Rumsmall: djupfragment är enbart evidens. Mallens delar byggs en gång. Stöd begränsar bara osynliga ben; uppmätt överkropp och synliga ben lämnas exakt oförändrade.')
            if not flerklipp:
                pl=next(iter(anv.values()));an={a['id']:a for a in pl['rumsmall']['ankare']}
                bind={b['person']:b for s in K['semantik']['scener'] for b in s.get('bindningar',[])}
                for pm in plan['personer']:
                    if pm['id'] in bind and bind[pm['id']]['ankare'] in an:
                        pm['stod']=copy.deepcopy(an[bind[pm['id']]['ankare']])
                        if pm['id'] in benlangder: pm['benlangder_m']=benlangder[pm['id']]
        plan['beslut'].append('Platsen: rummet byggs en gång i platsens koordinater; varje scens personer och kamera flyttas in med scenens transform (yaw + translation, skala 1,0). Transformernas ursprung och säkerhet står i kalla.matning.platser[].registreringar.')
    if flerklipp:
        # Flerklippsplan: varje scen har egna mätfiler (scener) och talersättningarna ligger i tal. Bar (ett klipp) får inga av dessa nycklar.
        plan['scener']=delplan; plan['tal']=tal_plan
        plan['beslut'][2]=('Talersättning: ersatta repliker syntetiseras med Piper (bygg_ljud.py) och läggs i sina luckor i utdatatiden; originaltalet i luckan tas bort helt (tal och ljudbädd går inte att skilja). Övrigt originalljud är tidsmappat.' if tal_plan
                           else 'Ingen talersättning: blandat_duckad använder bara tidsmappat originalljud.')
        if not platsmodus: plan['beslut'].append('Varje scen har egen uppmätt kamera och eget rum i eget världssystem; tagningarna är inte registrerade mot varandra.')
        plan['beslut'].append('Munnen följer inte ny text (uttryck/expr används inte av MHR-renderaren).')
    # Kontrollera alltid mätkameran före CM-edits, även för klippta/kopierade scener.
    plan['kallbild_hojd']=K['klipp']['video']['hojd']
    matnycklar=[]
    for s in scener:
        c=ktx[s['kx']]
        if s.get('rutlista') is not None: matnycklar.extend(copy.deepcopy(c['spar'][(x[0] if x[2]<.5 else x[1])-c['offs']]) for x in s['rutlista'])
        else: matnycklar.extend(c['spar'][s['a']-c['offs']:s['b']-c['offs']])
        if s.get('hall'): h_=next(x for x in hallna if x['scen']==s['id']); matnycklar.extend(copy.deepcopy(c['spar'][h_['lokal']]) for _ in range(s['hall']))
    plan['matkamera']=dict(sensor_bredd_mm=36,nycklar=matnycklar)
    if not flerklipp:
        plan['matkamera']['scener']=[dict(id=s['id'],ut=iv_ut[s['id']],lokal_start=s['a'],
                                        varld=kameror[next(sk['kamera'] for sk in K['semantik']['scener'] if sk['id']==s['ursprung'])]['spar_metrisk']['sokvag'],personer=plan['personer']) for s in scener]
    if any(s.get('lokal') for s in scener): plan['lokalbyte']=[dict(scen=s['id'],**copy.deepcopy(s['lokal'])) for s in scener if s.get('lokal')]
    plan['kvalitet']=dict(hojdpassning=hojdpassning,
                         kamerakalibrering=[dict(scen=s['id'],**(ktx[s['kx']]['kalibrering'] or {}),**ktx[s['kx']]['fokal']) for s in scener])
    from skarmtext import diagnostik as textdiagnostik
    textdiagnostik(plan)
    from datacache import signatur, matfiler
    plan['kvalitet']['byggunderlag']=signatur(matfiler(plan,alla=True))
    plan['kvalitet']['kallvideo_sha256']=K['klipp']['sha256']
    # Deklarerade värden (golv, sitthöjd, kamerahöjd) är bindande; varje avvikelse flaggas här och som varning. Utan deklaration: ingen post.
    from deklarationskontroll import kontrollera as kontrollera_deklaration
    dekl_kontroll=kontrollera_deklaration(plan)
    if dekl_kontroll:
        plan['kvalitet']['deklaration']=dekl_kontroll
        for x in dekl_kontroll['avvikelser']:
            plan['varningar'].append(f"Deklarationen bryts: {x['typ']} {x['id']} deklarerat {x['deklarerat']} m, planen har {x['planens_m']} m (avvikelse {x['avvikelse_m']} m). {x.get('orsak','')}")
        for x in (dekl_kontroll.get('registrering') or {}).get('over_troskel',[]):
            plan['varningar'].append(f"Flerrollsregistrering: {x['tagning']}/{x['scen']} roll {x['roll']} ligger {x['restfel_m']*100:.0f} cm från sin deklarerade plats {x.get('deklarerad_plats')} (tröskel {x['troskel_m']*100:.0f} cm); läsningen och deklarationen skiljer i rollernas inbördes läge. {('Lästa avståndet mellan rollerna är '+format(x['laspar_avstand_m'],'.2f')+' m mot deklarerade '+format(x['deklarerat_avstand_m'],'.2f')+' m. ') if x.get('laspar_avstand_m') is not None else ''}Kropparna är inte flyttade individuellt.")
    from kvalitet import planbeslut, komplettera
    from bildkamera import los as los_bildkamera
    from mobellyft import los as los_mobel
    # En möbel vars bildruta bekräftar läget måste flyttas innan intervallet och
    # skymningen avgör om den kan stå kvar. Vägen utan möbelbild behåller den
    # tidigare anropsordningen och därmed oförändrade planer/cachebeslut.
    har_mobelbild=any(isinstance(spec,dict) and (spec.get('bild') or spec.get('bilder')) for pl in plan.get('plats',[])
                      for spec in ((pl.get('deklarerat') or {}).get('mobler') or {}).values())
    if har_mobelbild:
        los_bildkamera(plan) # bara deklarerade rum; kroppar och kamerans bundna z lämnas orörda
        los_mobel(plan)      # bildbekräftat XY först; intervallet söker därefter bland tillåtna värden på rätt plats
        planbeslut(plan, PL)
    else:
        planbeslut(plan, PL)
        los_bildkamera(plan)
        los_mobel(plan)
    from mobelintervall import skriv_i_plats
    skriv_i_plats(plan)     # de valda möbelmåtten (deklarerade intervall) även i planens kopia av rumsmallen
    from vaggar import kor as anpassa_vaggar
    anpassa_vaggar(plan)    # generade väggar vidgas till kameror, möbler och rollankare; slutplanens geometri kontrolleras (bara deklarerade rum)
    from foremallyft import los as los_foremal
    los_foremal(plan)        # deklarerade bildrutor lyfts först nu, mot slutkameran och möblernas valda geometri
    from handforemal import los as los_handforemal
    los_handforemal(plan)    # 0013: föremål i handen (plan.handforemal); planer utan halls_av eller nyckelbilder lämnas orörda
    if matning.get('scenbygge'):   # 0029; 0033: valda varianter per scen följer med under nyckeln _val
        urs_ = {s['id']: s['ursprung'] for s in scener}
        if any(s.get('scenbygge_val') for s in scener): urs_['_val'] = {s['id']: s['scenbygge_val'] for s in scener if s.get('scenbygge_val')}
        scenbygge_i_plan(plan, matning['scenbygge'], urs_, iv_ut)
    for d_ in [d for d in (plan.get('scener') or []) if d.get('spegling')]:
        # 0031: föremålet i handen följer handen till andra sidan (r_wrist <-> l_wrist); förskjutningen speglas i handledens ram (x)
        for h in plan.get('handforemal') or []:
            if h['scen']==d_['id'] and h['person']==d_['spegling']['person'] and h.get('ben') in ('r_wrist','l_wrist'):
                h['ben']={'r_wrist':'l_wrist','l_wrist':'r_wrist'}[h['ben']]; h['sida']={'h':'v','v':'h'}.get(h.get('sida'),h.get('sida'))
                h['offset_m']=[-h['offset_m'][0],h['offset_m'][1],h['offset_m'][2]]; h['offset_status']=str(h.get('offset_status'))+'; speglad (0031, antagen)'; h['kontroll_rutor']=[]
        plan['beslut'].append('0031: speglad hand (satt_frihetsgrad) utförd på nivå 1; rutorna märks utförd_niva_1 i scenens spegling, IK görs i bygget.')
    if K['semantik'].get('relevans'):
        # 0029: relevanslistan i planen, och varningarna om det som bär meningen samlade för Jev och CM.
        plan['mening']=dict(mening=K['semantik']['relevans']['mening'],varningar=[v for v in plan['varningar'] if v.startswith('Meningen bärs av') or ' ramar meningen: ' in v])
    if snabb:
        # Flaggad för att den befintliga rendergrinden ska kräva uttrycklig granskning.
        plan['kvalitet']['bildtrohet']=dict(status='ej_kord',flaggad=True,personer=[])
        plan['kvalitet']['diagnostik']='ej_kord'
    else:
        from trohet import mat
        plan['kvalitet']['bildtrohet']=mat(plan)
        komplettera(plan, PL, med_planbeslut=False)
    if plan.get('props'):
        from propplan import los as los_props
        los_props(plan)
    if foremal_edits: foremal_i_plan(plan, foremal_edits, dekl_props)
    if hallna: halla_i_plan(plan, hallna)
    if not snabb and plan['kvalitet']['bildtrohet']['flaggad']:
        plan['varningar'].append('Bildtrohet överskrider egna diagnostiska trösklar. Se kvalitet.bildtrohet; render kräver uttryckligt granskningsläge.')
    return plan


def foremal_i_plan(plan, edits, dekl):
    """0016: ta bort eller byt ett föremål som deklarationen byggt, i alla dess former: kopior per kameragrupp (<stöd>:pa:<id>),
    handfästen (plan.handforemal) och barn till dem. byt till en okänd typ behåller plats, fäste och storlek; formen är en platshållare."""
    ut={s['id']:s['ut'] for s in (plan.get('scener') or plan['matkamera'].get('scener',[]))}
    def i_scen(post, sid):
        if sid=='alla': return True
        if post.get('scen') is not None: return post['scen']==sid
        a,b=post.get('synlig_ut') or [0,len(plan['kallrutor'])]; sa,sb=ut[sid]; return a<sb and sa<b
    def tag(i, fid): return i==fid or i.endswith(':pa:'+fid) or (':pa:'+fid+':') in i or i.endswith(':hand:'+fid)
    for e in edits:
        fid=e['prop']; sid=e.get('scen','alla'); traffar=[]
        for lista in ('objekt','props'):
            if plan.get(lista) is None: continue
            nya=[]
            for o in plan[lista]:
                if tag(str(o.get('id','')),fid) and i_scen(o,sid):
                    traffar.append(o['id'])
                    if e['op']=='ta_bort_prop': continue
                    o.update(namn='platshallare:'+e['ny_typ']+':'+fid,farg='#e2ac46',form_status='platshallare',byte=dict(fran=fid,till=e['ny_typ'],edit=e['id']))
                nya.append(o)
            plan[lista]=nya
        if plan.get('handforemal') is not None:
            nya=[]
            for h in plan['handforemal']:
                if h.get('foremal')==fid and i_scen(h,sid):
                    traffar.append(h['id']+'@'+h['scen'])
                    if e['op']=='ta_bort_prop': continue
                    h.update(etikett=e['ny_typ'],farg='#e2ac46',form_status='platshallare',byte=dict(fran=fid,till=e['ny_typ'],edit=e['id']))
                nya.append(h)
            plan['handforemal']=nya
        post=next(x for x in plan['tillampat'] if x['id']==e['id'])
        post['andring'].pop('vantar',None); post['andring']['traffade']=traffar
        if not traffar:
            plan['tillampat'].remove(post); plan['ej_tillampat'].append(dict(id=e['id'],op=e['op'],orsak=f'Föremålet {fid} har ingen form i planen i det valda urvalet.'))


def halla_i_plan(plan, hallna):
    """0016: en hållen scen upprepar sista källrutan. Kropparna läses som närvaro med upprepad ruta (mhr_rig oförändrad);
    text, föremål och handfästen som syns vid scenens slut står kvar under hållningen. Rutorna märks hållna, inte lästa."""
    plan['hallna_rutor']=[dict(scen=h['scen'],ut=h['ut'],kallruta=h['kallruta'],status='hållen: upprepar sista lästa källrutan, inte läst') for h in hallna]
    for h in hallna:
        a,b=h['ut']; n=b-a
        def forlang(post, nyckel):
            if post.get(nyckel) and post[nyckel][1]==a: post[nyckel]=[post[nyckel][0],b]
        # Former som stegen efter tidslinjen lagt helt inom hållningen saknar scen där (kameragruppskopior); de tas bort, slutets former förlängs.
        for lista in ('objekt','props'):
            if plan.get(lista) is not None: plan[lista]=[o for o in plan[lista] if not (o.get('synlig_ut') and a<=o['synlig_ut'][0] and o['synlig_ut'][1]<=b)]
        for t in plan.get('skarmtext') or []:
            if t['scen']==h['scen']: forlang(t,'ut')
        for lista in ('objekt','props'):
            for o in plan.get(lista) or []: forlang(o,'synlig_ut')
        for x in plan.get('handforemal') or []:
            if x['scen']==h['scen']: forlang(x,'synlig_ut')
        if h['delplan'] is not None:
            d=h['delplan']; d.update(id=h['scen']+'#hall',ut=[a,b],kalla=[h['kallruta'],h['kallruta']+1],lokal_start=max(0,h['lokal']-n+1),
                                     hall=dict(scen=h['scen'],kallruta=h['kallruta'],status='hållen, inte läst'))
            for pm in d['personer']:
                pm['narvaro']=dict(hall=True,kalla_scen=h['scen'],status='hållen sista ruta'); pm['varld']=d['varld']; pm['rutor']=[h['lokal']]*n
            i=next(i for i,x in enumerate(plan['scener']) if x['id']==h['scen'])
            plan['scener'].insert(i+1,d)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('kalla'); p.add_argument('regi'); p.add_argument('ut'); p.add_argument('--platsbank',help='mapp med plats-JSON för byt_miljo (standard: plats_bank/)'); p.add_argument('--snabb',action='store_true',help='lös byggbeslut utan kvalitetsdiagnostik; planen märks ej kontrollerad'); a=p.parse_args()
    plan=kompilera(a.kalla,a.regi,a.platsbank,snabb=a.snabb); skriv(a.ut,plan)
    from trohet import rapport
    if not a.snabb:rapport(plan,a.ut)
    for namn in ('tillampat','ej_tillampat'):
        print(namn)
        for e in plan[namn]: print(e['id'],e['op'],e.get('orsak',e.get('andring')))


if __name__=='__main__': main()
