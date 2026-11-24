import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('scen/3d/ingest').resolve()))
from sakra_filer import sakerhetskopiera
def edit(path,old,new):
 p=Path(path);s=p.read_text(encoding='utf-8')
 if old not in s:raise ValueError(f'{p}: {old[:100]}')
 sakerhetskopiera(p);p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')

F='scen/3d/kontrakt/kalla_flera.py'
edit(F,'def bygg_flera(mapp, mal, video, scen3d, ordtider, sha, platsfil=None):','def bygg_flera(mapp, mal, video, scen3d, ordtider, sha, platsfil=None, semantik=None):')
edit(F,"    S3 = ladda(scen3d); OT = ladda(ordtider)", "    import sys\n    sys.path.insert(0, str(HIT.parent / 'ingest'))\n    from semantik_input import Semantik\n    sm = Semantik(semantik) if semantik else None\n    S3 = ladda(scen3d) if scen3d else dict(shots=[], actors=[])\n    OT = ladda(ordtider) if ordtider else (sm.ordtider() if sm else dict(lines=[], model='saknas', language='sv', match_ratio=None))")
edit(F,"        tilldelat = dict(zip(rang, aktorer))", "        tilldelat = dict(zip(rang, aktorer))\n        if sm:\n            fp, tilldelat, beslut = sm.filtrera(d.name, ladda(d / 'personer.json'))\n            ids = [p for p in ids if p in fp]\n            for v in beslut: post(f'semantik.identitet.{d.name}.{v[\"spar_id\"]}', 'modellbedomd', str(v), sm.fil)")
edit(F,"                akt = roller.get(klipp_id)", "                akt = roller.get(klipp_id)\n                if sm:\n                    pp = sm.personer.get(klipp_id)\n                    if pp: akt = dict(role=pp['roll'])")
edit(F,"beskrivning=None, roll_kalla='scen3d' if akt else None)", "beskrivning=sm.personer[klipp_id]['beskrivning'] if sm and klipp_id in sm.personer else None, roll_kalla=('modellbedomd' if sm else 'scen3d') if akt else None)\n                if sm and klipp_id in sm.personer: personer[klipp_id]['ursprung'] = sm.ursprung(sm.personer[klipp_id]['konfidens'])")
edit(F,"        rj = ladda(d / 'rum.json')", "        rj = ladda(d / 'rum.json') if (d / 'rum.json').exists() else dict(floor=dict(height=-1.45, source='antagen kamerahöjd; okänt rum', verified=False), objects=[], walls=[])\n        if not rj['objects'] and not rj['walls']: post(f'semantik.rum.{sid}', 'saknas', 'Tomt rumsteg betyder okänt rum; det bevisar ingen tom lokal.', d / 'rum.json')")
edit(F,"        beat = sh['beat'] if sh else None", "        beat = sh.get('beat') if sh else None")
edit(F,"                   fokal_px=cam.get('fokal_px', tid.get('fokal_px')), statisk=tid.get('statisk'),", "                   fokal_px=cam.get('beslut', {}).get('fokal_px', cam.get('fokal_px', tid.get('fokal_px'))), statisk=bool(np.allclose(V['kam_C'], V['kam_C'][0])),")
edit(F,"                             kalla='whisper'))", "                             kalla='modellbedomd' if sm else 'whisper'))\n        if sm: repliker[-1]['ursprung'] = dict(l.get('ursprung', sm.ursprung('osaker')), ordtider=dict(typ='modellbedomd', modell=OT['model'], konfidens='se ordens sannolikhet'))")
edit(F,"         Path(ordtider),", "         Path(ordtider) if ordtider else sm.fil if sm else None,")
edit(F,"Path(ordtider))", "Path(ordtider) if ordtider else sm.fil if sm else None)")
edit(F,"kalla=rotref(Path(ordtider))", "kalla=rotref(Path(ordtider) if ordtider else sm.fil) if ordtider or sm else 'saknas'")
edit(F,"Path(scen3d),", "Path(scen3d) if scen3d else sm.fil if sm else None,")
edit(F,"Path(scen3d))", "Path(scen3d) if scen3d else sm.fil if sm else None)")
edit(F,"    k['semantik'] = sem", "    k['semantik'] = sem\n    if sm:\n        byshot = {t['tagning']: t for t in sm.data['tagningar']}\n        for s in scener:\n            t = byshot.get(s['id'].upper())\n            if t:\n                s.update(funktion=None if t['funktion'] in ('ingen', 'osaker') else t['funktion'], syfte=t['vad'])\n                post(f'semantik.scener.{s[\"id\"]}', 'modellbedomd', str(dict(t, ursprung=sm.ursprung(t['konfidens']))), sm.fil)\n        for r in rumsem:\n            r.update(typ=sm.data['plats']['typ'], beskrivning=sm.data['plats']['beskrivning'])\n        # Äldre notan-specifika påståenden ersätts av verkligt underlag.\n        for q in kvalitet:\n            if q['post'] in ('semantik.personer.roll', 'semantik.scener.funktion', 'semantik.repliker', 'semantik.repliker.talare', 'klipp.person_mappning'):\n                q.update(status='modellbedomd', metod='Klippets semantik: ' + str(sm.sem['ursprung']) + '. Värdenas konfidens finns på personer, repliker och scenposter.', kalla_fil=rotref(sm.fil), osakerhet='Modellbedömt; måste granskas.')\n        for q in kvalitet:\n            if q['post'] == 'matning.kameror.bana': q['metod'] = 'Kamera och statisk/rörlig enligt varje tagnings kamera.json, varld.npz och dokumenterade kvalitetsbeslut.'\n        for p in sm.data['placeringar']: post('semantik.placering.' + sm.namn[p['person']], 'modellbedomd', str(dict(p, ursprung=sm.ursprung(p['konfidens']))), sm.fil)\n        for p in sm.data['par'] + sm.data['kamerauppstallningar']: post('semantik.relation', 'modellbedomd', str(dict(p, ursprung=sm.ursprung(p['konfidens']))), sm.fil)")

B='scen/3d/kontrakt/kalla_bygg.py'
edit(B,"a.add_argument('--scen3d', default=str(HIT.parent/'scen3d.json')); a.add_argument('--ordtider', default=str(HIT.parent/'data/ordtider.json'))", "a.add_argument('--scen3d'); a.add_argument('--ordtider'); a.add_argument('--semantik')")
edit(B,"        k=bygg_flera(x.ingest, x.ut, x.video, x.scen3d, x.ordtider, sha, x.plats);", "        import sys\n        sys.path.insert(0, str(HIT.parent / 'ingest'))\n        from semantik_input import hitta\n        semfil = hitta(x.ingest, x.semantik) if not x.scen3d else x.semantik\n        if not semfil and not x.scen3d: a.error('Ange --scen3d och vid tal --ordtider, eller klippets egen --semantik.')\n        k=bygg_flera(x.ingest, x.ut, x.video, x.scen3d, x.ordtider, sha, x.plats, semfil);")

# Tillägg är bakåtkompatibla; bron använder fortfarande sina äldre enumvärden.
p=Path('scen/3d/kontrakt/kalla.schema.json');s=json.loads(p.read_text(encoding='utf-8'));sakerhetskopiera(p)
def walk(o):
 if isinstance(o,dict):
  props=o.get('properties',{})
  if 'roll_kalla' in props or ('talare' in props and 'ord' in props):
   props['ursprung']=dict(type='object', description='Modell och konfidens för värdet; ordtider har separat modell.')
   key='roll_kalla' if 'roll_kalla' in props else 'kalla'
   if 'modellbedomd' not in props[key].get('enum',[]):props[key].setdefault('enum',[]).append('modellbedomd')
  for v in o.values():walk(v)
 elif isinstance(o,list):
  for v in o:walk(v)
walk(s);p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
