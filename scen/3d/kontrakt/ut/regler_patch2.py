import sys
from pathlib import Path
sys.path.insert(0, str(Path('scen/3d/ingest').resolve()))
from sakra_filer import sakerhetskopiera

def edit(path, old, new):
    p=Path(path);s=p.read_text(encoding='utf-8')
    if old not in s:raise ValueError(f'{p}: {old[:120]}')
    sakerhetskopiera(p);p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')

P='scen/3d/ingest/plats.py'
edit(P,"    V = dict(np.load(d / 'varld.npz')); G = gravitation(V['upp'])", "    meta = ladda(d / 'meta.json')\n    if not (d / 'varld.npz').exists():\n        if ladda(d / 'personer.json'): raise ValueError(f'{tid}: personer finns men varld.npz saknas; kör världsteget.')\n        from ingest_klipp import steg_varld\n        steg_varld(d, meta)\n    V = dict(np.load(d / 'varld.npz')); G = gravitation(V['upp'])")
edit(P,"    personer = {}\n    for p", "    if rum is None:\n        rum = dict(floor=dict(height=float(V.get('golv_h', -1.45)), source='antagen kamerahöjd; rummet okänt', verified=False), objects=[], walls=[], status='saknas')\n        golv = dict(hojd_m=rum['floor']['height'], kalla=rum['floor']['source'], verifierad=False, uppmatt_ur_fotter=False)\n    personer = {}\n    for p")
edit(P,"                             fokal_px=float(S['fokal']))", "                             fokal_px=float(S['fokal']),\n                             endast_overkropp=ladda(d / f'utsnitt_{pid}.json').get('endast_overkropp', False) if (d / f'utsnitt_{pid}.json').exists() else False)")
edit(P,"        r = bildruta(t, args, start); start += t['N']", "        n0 = start; start += t['N']\n        if not t['statisk']: continue\n        r = bildruta(t, args, n0)")
edit(P,"    rollmap = roller(tagningar, args.scen3d) if not ensam else", "    from semantik_input import hitta, Semantik\n    semfil = hitta(mapp, getattr(args, 'semantik', None))\n    sem = Semantik(semfil) if semfil else None\n    rollmap = roller(tagningar, args.scen3d) if not ensam else")
edit(P,"    matt = dict(version=VERSION", "    if sem:\n        for t in tagningar:\n            pfil = t['mapp'] / 'personer.json'\n            filtrerade, rm, beslut = sem.filtrera(t['id'], ladda(pfil))\n            t['personer'] = {p: pp for p, pp in t['personer'].items() if p in filtrerade}\n            for p in t['personer']: rollmap[(t['id'], p)] = rm[p]\n            t['semantik_beslut'] = beslut\n            for p, pp in t['personer'].items(): pp['semantisk_placering'] = sem.placering(t['id'], rm[p])\n    matt = dict(version=VERSION")
edit(P,"    stationer = []\n    if ident or not all(t['statisk'] for t in tagningar):", "    stationer = []; par = []\n    sem_disk = bool(sem and sem.data['plats']['typ'] == 'butik_eller_disk' and not any(p['vander_mot_varandra'] == 'ja' for p in sem.data['par']))\n    if ident or sem_disk:")
edit(P,"        matt['c_bildmatchning'] = []", "        mt, accept = matcha_par(tagningar, args) if not ident else ([], {})\n        matt['c_bildmatchning'] = avrunda(mt, 3)")
edit(P,"'rörlig kamera')", "'semantiken anger ingen dialogaxel mellan kolleger')")
edit(P,"staende = hojd > STOL_MAX_BACKENHOJD_M; kind = 'staplats' if staende else 'sate'; aid = f'{\"staplats\" if staende else \"stol\"}_{r}'", "from regler import hallningsbeslut\n            obs = [(t, p) for t in tagningar for p, pp in t['personer'].items() if rollmap[(t['id'], p)] == r]\n            tydlig = max(obs, key=lambda tp: tp[0]['personer'][tp[1]]['ben_synliga'] / max(tp[0]['personer'][tp[1]]['rutor'], 1))\n            tt, pid = tydlig; pp = tt['personer'][pid]\n            hb = hallningsbeslut(hojd, pp['ben_synliga'] / max(pp['rutor'], 1), pp.get('semantisk_placering'))\n            staende = hb['hallning'] == 'star'; kind = 'staplats' if staende else 'sate'; aid = f'{\"staplats\" if staende else \"stol\"}_{r}'")
edit(P,"            if max(e['sprid'] for e in lst) > STILLA_MAX_SPRIDNING_M: continue", "            if max(e['sprid'] for e in lst) > STILLA_MAX_SPRIDNING_M and not sem: continue")
edit(P,"hallning='star' if staende else 'sitter', status='antagen',", "hallning=hb['hallning'], status=hb['status'], hallningsbeslut=hb,")
edit(P,"        for r, lst in sorted(per_roll.items()):", "        for r, lst in sorted(per_roll.items()):\n            if sem:\n                lst = [e for e in lst if not next(t for t in tagningar if t['id'] == e['tagning'])['personer'][e['ingest_id']].get('endast_overkropp')]\n                if not lst: continue")
edit(P,"if ident else f'golvet under stol_{par[0]}'", "if ident else (f'golvet under stol_{par[0]}' if len(par) == 2 else 'gemensamt golv; XY oregistrerat')")
edit(P,"if ident else f'+Y från stol_{par[0]} mot stol_{par[1]}, X höger sett längs +Y, Z upp'", "if ident else (f'+Y från stol_{par[0]} mot stol_{par[1]}, X höger sett längs +Y, Z upp' if len(par) == 2 else 'X höger, Y framåt, Z upp; koppling mellan kameraställen okänd')")
edit(P,"    if not ident or hand.get('rumsmall') or getattr(args, 'rumsmall', None):", "    if sem:\n        plats['typ'] = sem.data['plats']['typ']; plats['semantik'] = dict(fil=str(sem.fil), plats=sem.data['plats'], ursprung=sem.ursprung(sem.data['plats']['konfidens']))\n        from semantik_plats import moblera_semantiskt\n        moblera_semantiskt(plats, sem)\n        matt['semantik'] = dict(fil=str(sem.fil), beslut=[dict(tagning=t['id'], beslut=t['semantik_beslut']) for t in tagningar])\n        return plats, matt, ut, tagningar, reg\n    if not ident or hand.get('rumsmall') or getattr(args, 'rumsmall', None):")
edit(P,"a.add_argument('--scen3d', default=str(HIT.parent / 'scen3d.json'))", "a.add_argument('--scen3d'); a.add_argument('--semantik')")

G='scen/3d/kontrakt/golvmatning.py'
edit(G,"        for pid,pp in t['personer'].items():", "        for pid,pp in t['personer'].items():\n            if pp.get('endast_overkropp'): continue")
edit(G,"            seated=hip-old<.82 and vanligt_bord", "            placering=pp.get('semantisk_placering')\n            seated=(placering['hallning']=='sitter' if placering and pp['ben_synliga']/max(pp['rutor'],1)<.2 else hip-old<.82 and vanligt_bord)")

K='scen/3d/kontrakt/kompilera.py'
edit(K,"float(next(iter(seq.values()))['fokal'])", "float(next(iter(seq.values()))['fokal'] if seq else kam.get('fokal_px') or max(K['klipp']['video']['bredd'], K['klipp']['video']['hojd']))")
edit(K,"flerklipp = any(m.get('scen') for m in matning['personer'])", "flerklipp = any('kalla_ruta0' in c for c in matning['kameror']) or any(m.get('scen') for m in matning['personer'])")
