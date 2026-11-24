"""Mallval från platstyp. Mått är mallvärden; anpassning är ett antagande."""
import copy
import numpy as np
from rumsmall import las, ankare, passa


def moblera_semantiskt(plats, sem):
    pl = sem.data['plats']; typ = pl['typ']; forslag = pl['rumsmall_forslag']
    val = ('bar_disk' if typ == 'butik_eller_disk' else forslag)
    beslut = dict(status='modellbedomd', ursprung=sem.ursprung(pl['konfidens']), platstyp=typ,
                  forslag=forslag, vald=val, orsak=pl['motivering'])
    plats['mallbeslut'] = beslut; plats['utelamnade'] = []
    if val in ('ingen_passar', 'osaker'):
        beslut.update(vald=None, orsak='Ingen passande mall enligt semantiken; rummet förblir okänt.')
        return
    if typ != 'butik_eller_disk':
        from rumsmall import moblera
        try: moblera(plats, val)
        except ValueError as e: beslut.update(vald=None, orsak=str(e))
        return
    m, sha = las(val); m = copy.deepcopy(m)
    # Bars fasta id 1/2 beskriver inte nya roller. Instansen får egna ankare.
    for d in m['delar']: d['ankare'] = []
    disk = next(d for d in m['delar'] if d['typ'] == 'bardisk')
    fitank = [a for a in plats['ankare'] if a['typ'] == 'staplats']
    if not fitank:
        beslut.update(vald=None, orsak='Inga användbara ståankare; ingen metrisk mallpassning möjlig.')
        return
    for i, a in enumerate(fitank):
        # Serverande står bakom, kund framför. Avstånd och diskhöjd är mallvärden.
        role = sem.personer.get(a.get('roll'), {}).get('roll', '')
        kund = role == 'customer'; y = 1.0 if kund else -.65
        direction = -np.pi/2 if kund else np.pi/2
        disk['ankare'].append(dict(id=a['id'], typ='staplats', pos_m=[(i-(len(fitank)-1)/2)*.6, y, 0.], riktning_rad=float(direction), fotled_over_golv_m=.065))
    fit = passa(m, fitank, plats['golv']['hojd_m'])
    from rumsmall import rz
    R = rz(fit['yaw_rad']); t = np.array(fit['translation_m'])
    for d in m['delar']:
        d['pos_m'] = (R @ d['pos_m'] + t).tolist(); d['yaw_rad'] += fit['yaw_rad']
    fitted = ankare(m)
    # Stöd behåller personens eget ankare; möbelresten får inte flytta kroppen.
    for a in fitted:
        b = next((b for b in fitank if b['id'] == a['id']), None)
        if b: a.update(pos_m=b['pos_m'], riktning_rad=b['riktning_rad'])
    beslut.update(status='antagen', rest_m=fit['rms_m'], tolerans_m=.5,
                  mismatch='Bardisk är närmaste mall; saknar chark-/glass-/serveringsdiskens särskilda geometri och material.' + (' Ankarrest över 0,5 m.' if fit['rms_m'] > .5 else ''))
    plats['rumsmall'] = dict(id=m['id'], sha256=sha, status='mall', fiktiv=m['fiktiv'], passning=fit,
                            justeringar=[], passningsevidens=[], delar=m['delar'], ankare=fitted,
                            antaganden=m['antaganden'] + [beslut['mismatch']], texturprojektion=None)
