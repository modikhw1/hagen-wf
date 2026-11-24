"""Föremål i handen (uppdrag 0013): fäste per tagning, från deklaration till byggare.

Indata: ``plan.plats[].deklarerat.foremal[<id>]`` med ``bilder`` (ur ingest/rum_rutor.py, en post per tagning; ``nyckelbilder`` bär maskens
tyngdpunkt, bredd och höjd per nyckelbild) och/eller ``halls_av`` (roll). Utdata: ``plan.handforemal`` (en post per tagning där föremålet
hålls, id ``<roll>:hand:<id>``) och ``plan.kvalitet.handforemal``. Byggaren (ingest/mhr_rig.py) fäster posten vid handledsbenet med
Child Of, så att föremålet följer handens matris genom hela tagningen, också där handvilan har lugnat handen.

1. Vilken hand: per nyckelbild skärs strålen genom maskens tyngdpunkt (slutkameran) med handledens kameradjup, för båda händerna hos de
   personer som är lästa i scenen. Handen med kortast avstånd i 3D, om det är under HAND_GRANS_M, håller föremålet i den bilden.
   Tagningen räknas som hållen när minst hälften av nyckelbilderna med mask säger det; handen är den som flest bilder valde.
   Saknas mask i tagningen men deklarationen har ``halls_av`` och rollen syns: rollens hand närmast deklarationens bildruta (annars höger).
2. Fästet: förskjutningen i handledens ram (rotation och läge ur riggen, se trohet.ruta_pose) är medianen över tagningens nyckelbilder.
   Utan mask: AVSTAND_UTAN_MASK_M längs handens x-axel, märkt ``antagen``.
3. Storlek: maskens bredd och höjd (promille) gånger djupet genom brännvidden, median, inom deklarerat intervall. Ellipsoid.
4. Kedjan: ``:pa:``-kopior av samma föremål (t.ex. ``disk_C:pa:kottbit``) visas inte där föremålet är i handen. Handposterna ligger inte i
   ``plan.objekt`` och kan alltså inte strykas av skymningskontrollen (kontrakt/skymning.py läser bara ``objekt``).
5. Två händer (båda under gränsen i samma bild) och byte av hand inom en tagning redovisas; ett fäste per tagning byggs.
Gränserna är egna val (diagnos), inte mätta."""
import json
from pathlib import Path
import numpy as np

HAND_GRANS_M = .25          # tyngdpunktens punkt på handens djup högst så här långt från handleden (antaget)
TVA_HANDER_KVOT = 1.5       # båda händerna "håller" när den andra är inom 1,5 × den närmaste och under gränsen (antaget)
AVSTAND_UTAN_MASK_M = .08   # förskjutning längs handens x-axel när mask saknas (antaget)
LED = dict(h='r_wrist', v='l_wrist')
METOD = ('Stråle genom maskens tyngdpunkt i slutkameran, skuren med handledens kameradjup; närmaste hand (3D) under '
         f'{HAND_GRANS_M:.2f} m håller. Förskjutning i handledens ram = median över tagningens nyckelbilder. Mått ur maskens bredd/höjd på handens djup, '
         'inom deklarerat intervall. Byggaren fäster med Child Of vid handledsbenet.')


def _rigg():
    from trohet import IX
    return IX


def _kamera(plan, u):
    key = plan['renderkamera']['nycklar'][u]; w = float(plan['utdata']['bredd']); h = float(plan['utdata']['hojd'])
    fok = float(key['lins_mm']) / float(plan['renderkamera'].get('sensor_bredd_mm', 36.)) * w
    return np.asarray(key['matris'], float), fok, w, h


def projicera(plan, u, X):
    M, fok, w, h = _kamera(plan, u); c = (np.asarray(X, float) - M[:3, 3]) @ M[:3, :3]
    return np.array([c[0] / -c[2] * fok + w / 2., -c[1] / -c[2] * fok + h / 2.]), float(-c[2])


def stralpunkt(plan, u, x_pm, y_pm, djup):
    """Punkten på strålen genom bildpunkten (promille) med kameradjupet ``djup`` (längs kamerans -z)."""
    M, fok, w, h = _kamera(plan, u)
    lokal = np.array([(x_pm / 1000. * w - w / 2.) / fok, -(y_pm / 1000. * h - h / 2.) / fok, -1.])
    return M[:3, 3] + M[:3, :3] @ (lokal * float(djup))


def _quat(x):
    """Rad i pose (x, y, z, w från index 3) -> 3x3."""
    qx, qy, qz, qw = [float(v) for v in x[3:7]]; n = np.sqrt(qx * qx + qy * qy + qz * qz + qw * qw) or 1.
    qx, qy, qz, qw = qx / n, qy / n, qz / n, qw / n
    return np.array([[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
                     [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
                     [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]])


class _Kropp:
    """Handledernas ram (rotation, läge) per lokal ruta för en person i en scen, med samma pose, stöd och plats som byggaren."""

    def __init__(self, scen, pm):
        from trohet import ruta_pose
        from metrisk import las as las_sekvens
        self.scen, self.pm, self._rp = scen, pm, ruta_pose
        self.data = (las_sekvens(pm['rorelse']), dict(np.load(scen['varld'])))
        self.ix = _rigg()

    def ram(self, f, sida):
        pose, q, t = self._rp(self.scen, self.pm, int(f), True, self.data)
        r = pose[self.ix[LED[sida]]]
        return q @ _quat(r), q @ (np.asarray(r[:3], float) / 100.) + t

    def inom(self, f):
        s = self.data[0]
        return bool(s['inom'][f]) if 'inom' in s.files else True


def kandidat(f):
    """Kan föremålet hållas? Ja om deklarationen säger ``halls_av``, eller om det har nyckelbilder och inget byggt stöd
    (inget ``pa``, eller ``stod_ersatt``: stödet byggs inte, som köttbitens inslagspapper). Ett föremål som står på en byggd möbel
    (vågen på disken) räknas inte som hållet bara för att en hand är nära."""
    if not isinstance(f, dict): return False
    if f.get('halls_av'): return True
    har_nb = any(isinstance(b, dict) and b.get('nyckelbilder') for b in f.get('bilder') or [])
    return har_nb and (not f.get('pa') or bool(f.get('stod_ersatt')))


def _deklarerade(plan):
    for pl in plan.get('plats', []):
        for fid, f in ((pl.get('deklarerat') or {}).get('foremal') or {}).items():
            if kandidat(f): yield pl, fid, f


def _scen_for(plan, tagning):
    return next((s for s in plan.get('scener', []) if str(s['id']).casefold() == str(tagning).casefold()), None)


def _intervall(dekl):
    sm = dekl.get('storlek_m') or ((dekl.get('bild') or {}).get('storlek_m_dekl'))
    if not isinstance(sm, (list, tuple)) or len(sm) != 3: return None
    return [tuple(map(float, v)) if isinstance(v, (list, tuple)) else (float(v), float(v)) for v in sm]


def los(plan):
    """Skriver plan['handforemal'] och plan['kvalitet']['handforemal']. Ger rapporten, eller None när inget föremål hålls/har handdata."""
    poster, rapport = [], []
    N = len(plan.get('kallrutor') or plan['renderkamera']['nycklar'])
    for pl, fid, dekl in _deklarerade(plan):
        iv = _intervall(dekl); bilder = {str(b.get('tagning')).upper(): b for b in dekl.get('bilder') or [] if isinstance(b, dict)}
        rpost = dict(foremal=fid, halls_av=dekl.get('halls_av'), metod=METOD, tagningar=[],
                     troskel=dict(hand_grans_m=HAND_GRANS_M, tva_hander_kvot=TVA_HANDER_KVOT, avstand_utan_mask_m=AVSTAND_UTAN_MASK_M, status='valda, diagnostiska'))
        for scen in plan.get('scener', []):
            t = str(scen['id']).upper(); a, b = scen['ut']; lasta = [pm for pm in scen['personer'] if not pm.get('narvaro')]
            if not lasta: continue
            kroppar = {pm['id']: _Kropp(scen, pm) for pm in lasta}
            bild = bilder.get(t); nb = [n for n in (bild or {}).get('nyckelbilder') or [] if n.get('tyngdpunkt_2d')]
            val, prov = [], []
            for n in nb:
                f = int(n['ruta']); u = a + f - int(scen['lokal_start'])
                if not (a <= u < b): continue
                ty, tx = n['tyngdpunkt_2d']; kand = []
                for pid, k in kroppar.items():
                    if not k.inom(f): continue
                    for sida in ('h', 'v'):
                        R, p = k.ram(f, sida); _, djup = projicera(plan, u, p)
                        if djup <= 0: continue
                        P = stralpunkt(plan, u, tx, ty, djup)
                        kand.append((float(np.linalg.norm(P - p)), pid, sida, R, p, P, djup))
                kand.sort(key=lambda z: z[0])
                if not kand: continue
                d0 = kand[0]; halls = d0[0] <= HAND_GRANS_M
                tva = halls and len(kand) > 1 and kand[1][0] <= HAND_GRANS_M and kand[1][0] <= TVA_HANDER_KVOT * d0[0] and kand[1][1] == d0[1]
                _, fok, w, h = _kamera(plan, u)
                post = dict(ruta=f, ut=u, avstand_m=round(d0[0], 3), person=d0[1], sida=d0[2], i_hand=halls, tva_hander=bool(tva),
                            andra_handen_m=round(kand[1][0], 3) if len(kand) > 1 else None)
                if halls:
                    R, p, P, djup = d0[3], d0[4], d0[5], d0[6]
                    post.update(offset=(R.T @ (P - p)).tolist(), djup_m=round(djup, 3),
                                bredd_m=float(n['bredd_2d']) / 1000. * w * djup / fok if n.get('bredd_2d') else None,
                                hojd_m=float(n['hojd_2d']) / 1000. * h * djup / fok if n.get('hojd_2d') else None,
                                tyngdpunkt_px=[tx / 1000. * w, ty / 1000. * h])
                prov.append(post)
                if halls: val.append((d0[1], d0[2]))
            tpost = dict(tagning=t, scen=scen['id'], synlig_ut=[a, b], nyckelbilder_med_mask=len(prov), i_hand=sum(p['i_hand'] for p in prov), prov=prov)
            hand = None
            if prov and len(val) * 2 >= len(prov) and val:
                par = max(set(val), key=val.count); hand = dict(person=par[0], sida=par[1], kalla='mask')
                if len(set(val)) > 1: tpost['handbyte_i_tagningen'] = sorted({f'{x}:{s}' for x, s in val})
                if any(p['tva_hander'] for p in prov): tpost['tva_hander'] = 'båda händerna nära i minst en bild; fäst vid den närmaste'
            elif not prov and dekl.get('halls_av') in kroppar:
                hand = dict(person=dekl['halls_av'], sida=_narmaste_sida(plan, scen, kroppar[dekl['halls_av']], bild), kalla='halls_av (ingen mask i tagningen)')
            elif prov: tpost['orsak'] = f"föremålet är i handen i {len(val)} av {len(prov)} nyckelbilder; inte hållet i tagningen"
            else: tpost['orsak'] = 'ingen mask och ingen halls_av-roll i scenen'
            if hand:
                egna = [p for p in prov if p['i_hand'] and (p['person'], p['sida']) == (hand['person'], hand['sida'])]
                if egna:
                    off = np.median(np.array([p['offset'] for p in egna]), axis=0); off_status = 'matt'
                else:
                    off = np.array([AVSTAND_UTAN_MASK_M, 0., 0.]); off_status = 'antagen'
                matt, matt_status = _matt(egna, iv)
                hs = _utan_bildstod(scen, hand['person'], hand['sida'])
                hid = f"{hand['person']}:hand:{fid}"
                poster.append(dict(id=hid, foremal=fid, scen=scen['id'], person=hand['person'], sida=hand['sida'], ben=LED[hand['sida']],
                                   synlig_ut=[a, b], offset_m=[round(float(x), 4) for x in off], offset_status=off_status, matt_m=[round(x, 3) for x in matt],
                                   matt_status=matt_status, form='ellipsoid', farg='#b5654a', kontroll_rutor=[p['ruta'] for p in egna][:8]))
                tpost.update(hand=hand, id=hid, offset_m=poster[-1]['offset_m'], offset_status=off_status, matt_m=poster[-1]['matt_m'],
                             utan_bildstod=hs)
            rpost['tagningar'].append(tpost)
        if any(p['foremal'] == fid for p in poster): _gom_pa_kopior(plan, fid, [p['synlig_ut'] for p in poster if p['foremal'] == fid], rpost, N)
        rapport.append(rpost)
    if not rapport: return None
    plan['handforemal'] = poster
    plan.setdefault('kvalitet', {})['handforemal'] = rapport
    return rapport


def _narmaste_sida(plan, scen, k, bild):
    """Utan mask: handen vars projektion ligger närmast bildrutans mitt i scenens mittruta; utan ruta höger hand."""
    if not bild or len(bild.get('box_2d') or []) != 4: return 'h'
    a, b = scen['ut']; u = (a + b - 1) // 2; f = int(scen['lokal_start']) + u - a
    y0, x0, y1, x1 = bild['box_2d']; _, _, w, h = _kamera(plan, u); m = np.array([(x0 + x1) / 2000. * w, (y0 + y1) / 2000. * h])
    return min(('h', 'v'), key=lambda s: float(np.linalg.norm(projicera(plan, u, k.ram(f, s)[1])[0] - m)))


def _matt(egna, iv):
    """[bredd, bredd, höjd] ur masken på handens djup, inom deklarerat intervall [[x], [y], [z]]."""
    br = [p['bredd_m'] for p in egna if p.get('bredd_m')]; ho = [p['hojd_m'] for p in egna if p.get('hojd_m')]
    if iv is None: iv = [(.05, .3), (.05, .3), (.05, .3)]
    mitt = [(lo + hi) / 2. for lo, hi in iv]
    if not br: return mitt, 'deklarerat (mitt), ingen mask'
    b = float(np.clip(np.median(br), iv[0][0], iv[0][1])); hh = float(np.clip(np.median(ho), iv[2][0], iv[2][1])) if ho else mitt[2]
    d = float(np.clip(b, iv[1][0], iv[1][1]))
    return [b, d, hh], 'mask, inom deklarerat intervall'


def _utan_bildstod(scen, pid, sida):
    """Rutor i scenen där handen som håller saknar bildstöd enligt ingest/handsyn.py (dold), samt störda."""
    pm = next((p for p in scen['personer'] if p['id'] == pid), None)
    if pm is None: return None
    fil = Path(pm['rorelse']).parent / f"handsyn_{pm.get('ingest_id')}.json"
    if not fil.exists(): return dict(status='handsyn saknas')
    H = json.loads(fil.read_text(encoding='utf-8')); a, b = scen['ut']; rutor = range(int(scen['lokal_start']), int(scen['lokal_start']) + (b - a))
    syn = H[sida]['synlig']; st = H[sida].get('stord') or [False] * len(syn)
    return dict(rutor=len(rutor), utan_bildstod=int(sum(not syn[i] for i in rutor if i < len(syn))), stord=int(sum(bool(st[i]) for i in rutor if i < len(st))))


def _gom_pa_kopior(plan, fid, intervall, rpost, N):
    """``:pa:``-kopior av föremålet visas inte under de intervall där det är i handen."""
    from mobellyft import _minus
    suffix = ':pa:' + fid; ny = []; andrade = []
    for o in plan['objekt']:
        if not str(o.get('id', '')).endswith(suffix): ny.append(o); continue
        rest = _minus(o.get('synlig_ut') or [0, N], intervall)
        if rest != [o.get('synlig_ut') or [0, N]]: andrade.append(dict(id=o['id'], fore=o.get('synlig_ut') or [0, N], efter=rest))
        for r in rest:
            k = dict(o); k['synlig_ut'] = r; ny.append(k)
    plan['objekt'] = ny
    if andrade: rpost['pa_kopior_dolda'] = andrade
