"""Läsbar inventering inför ett eventuellt modellbyte. Ändrar bara rapporten."""
from pathlib import Path
import re
from steg10c_filer import ROT, andra
H=ROT/'scen/3d/kontrakt';I=H.parent/'ingest'
rows=[]
# Direkta modellord, lednamn, parameterdimensioner och estimatorns råformat.
pat=re.compile(r'\bmhr\b|mhr_|blender_mhr|\b127\b|\b18439\b|\b204\b|\b208\b|pred_(?:joint|keypoints|vertices|global)|[\'\"](?:[lr]_(?:wrist|upleg|lowleg|foot|ball|talocrural|subtalar|transversetarsal|thumb|index|middle|ring|pinky|uparm|lowarm|clavicle)|c_spine|c_head|c_neck|root(?:_r[xyz])?[\'\"])',re.I)
# Fasta riggindex utan modellnamn: rot=1, nacke=110 och 34-gräns.
indexpat=re.compile(r"(?:pose|rest).*?(?:\[.*?\b(?:1|110)\s*[:,\]]|:34|34:|i\s*\+\s*1)")
skip={'ut','__pycache__','.venv'}
for base in (H,I):
 for p in sorted(base.rglob('*')):
  if any(x in skip for x in p.relative_to(base).parts) or p.suffix not in ('.py','.json'):continue
  if p.name in ('mhr_ledernamn.json','tro_rigg.json'):continue
  if p.name.startswith('steg10c_') or p.name=='modal_gemx.py':continue
  for n,line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
   s=line.strip()
   if not (pat.search(s) or indexpat.search(s)):continue
   # Numerisk bildmasktröskel, hash, vanliga pixel-/geometrivärden är inga riggantaganden.
   if ' > 127)' in s or 'sha256' in s and not 'mhr' in s.lower():continue
   if re.fullmatch(r'"[0-9a-f]{64}"[, ]*',s):continue
   if p.name=='modal_sam3db.py' and 'pyrootutils' in s:continue
   if re.search(r"pose\[a\]|pose\[b\]|pose\[i\]|pose\[int\(",s) and not pat.search(s):continue
   if 'mhr_rig:' in s and 'print(' in s:continue
   if p.name=='rum.py' and ('pop(' in s or '# mhr_rig.py' in s):continue
   where=p.relative_to(H.parent).as_posix()+':'+str(n)
   typ='Hårt'
   if p.name.startswith('test_') or 'testdata' in p.parts:typ='Prov'
   elif p.suffix=='.json' or p.name.startswith('kalla_') and ('roll=' in s or 'uppmatt' in s):typ='Avtal'
   elif p.name.startswith(('verifiera_','tro_granska','golv_sammanfatta')) or 'engang' in p.parts:typ='Verktyg'
   if p.name=='kroppmatt.py' and ('18439' in s or 'pred_vertices' in s):what='Hudtopologi/estimatorhörn hör till MHR lod1 (18 439 hörn), inte en allmän kroppsmodell.'
   elif '127' in s:what='Ledantalet är fast 127; pose, prov eller metadatadimension måste bytas för annan rigg.'
   elif re.search(r'\b204\b|\b208\b|root_r[xyz]|mhr_parametrar|mhr_model_params',s):what='MHR:s 204 poseparametrar, rotens Eulerparametrar och/eller utökning till 208 med kvaternion är formatspecifika.'
   elif 'lod' in s.lower() or 'mhr_model.pt' in s or 'mhr_skelett' in s or 'mhr_ledernamn' in s:what='Läser eller väljer en namngiven MHR-rigg, modell, hierarki eller FBX-fil.'
   elif re.search(r'pred_keypoints|MHR70',s,re.I):what='Råpunkterna och deras ordning är SAM 3D Body/MHR70; punktnummer kan inte återanvändas för SOMA.'
   elif 'pred_' in s:what='Läser SAM 3D Bodys MHR-råformat (globala leder/rotationer, hörn eller kameratranslation).'
   elif indexpat.search(s):what='Använder fasta MHR-index eller kopplingen modellled i = FBX-ben i−1 (rot 1, nacke 110 där de förekommer).'
   elif re.search(r"['\"](?:[lr]_|c_spine|c_head|c_neck|root['\"])",s):what='Ledval, kameramål, propgrepp eller benhierarki använder MHR:s lednamn.'
   elif 'blender_mhr' in s:what='Renderbackend/validering är låst till blender_mhr; avtal eller kommando är modellbundet.'
   elif 'MHR' in s or 'mhr' in s:what='Anger MHR-format/modellrum i källavtal, byggkedja, diagnos eller dokumentation.'
   else:what='Modellbunden led-/parameteruppdelning används här.'
   snippet=s.replace('|','&#124;').replace('`','')
   if len(snippet)>230:snippet=snippet[:227]+'…'
   rows.append((where,typ,what,snippet))
# Filer vars hela innehåll är själva ledtabellen/hierarkin, inte enskilda oberoende antaganden.
rows += [('ingest/mhr_ledernamn.json:1','Hårt','Hela tabellen låser ordning och namn för MHR:s 127 leder.','127 lednamn, inklusive den extra modellroten.'),('kontrakt/tro_rigg.json:1','Hårt','Hela exporten låser MHR-namn och föräldraindex till lod3.fbx.','namn och foralder från MHR-FBX.')]
# Bindningar som inte nämner MHR med namn på användningsraden.
manual={
 'kontrakt/trohet.py':[(13,'NAMN =','Riggfilens namn/ordning återanvänds som ledindex.'),(19,'for start, sida','MHR70-händerna börjar på 21/42 och har 21 punkter med omvänd fingerordning.'),(20,'PAR +=','Exakt MHR70 till MHR-rigg-mappning för alla fingerleder.')],
 'kontrakt/trosula.py':[(22,"d=dict(np.load",'tro_fothud.npz är exporterad MHR-hud med MHR-vikter, vilopose och ledindex.'),(24,'offsets=','j−1 antar extra modellrot före FBX-benens index.')],
 'kontrakt/propplan.py':[(12,'from trohet import','Propfästen ärver MHR:s ledindex och poseformat.'),(55,'med_stod=','Optimeringen för handfästen bygger på MHR:s BEN-urval; andra leder skyddas.')],
 'kontrakt/kroppmatt.py':[(33,"d = np.load",'tro_hud.npz innehåller MHR-topologi, viloleder och skinvikter.')],
 'kontrakt/trostod.py':[(13,'from kroppsstod import','Importerar MHR:s lednamn, BEN och rotationshjälpare.'),(15,'FORALDER=','MHR:s exporterade hierarki styr benlängder och stöd-IK.')],
 'ingest/ingest_klipp.py':[(260,'rot =','MHR-led 1 används som kroppsrot i metrisk kameraskalsökning.'),(261,'nacke =','MHR-led 110 används som nacke i gravitationsskattningen.')],
 'ingest/mhr_rig.py':[(49,'P = np.array','Viloposens led i+1 matchas mot FBX-ben i, i importordning.'),(53,'C = {','Rotationskorrektion använder samma led i+1 och FBX-benordning.'),(74,'t, q =','Varje animerad FBX-matris tar MHR-poseled i+1.')],
 'ingest/kroppsstod.py':[(54,'for sida in','Benstödet slår upp MHR:s upleg/lowleg/foot/ball per sida.')],
 'ingest/sekvens_stabil.py':[(44,'poses =','MHR-modellen genererar hela poseformatet från parametrarna.')],
}
for file,sites in manual.items():
 p=H.parent/file;lines=p.read_text(encoding='utf-8-sig').splitlines()
 for hint,token,what in sites:
  candidates=[(abs(n-hint),n,s.strip()) for n,s in enumerate(lines,1) if token in s]
  if not candidates:continue
  _,n,s=min(candidates);where=file+':'+str(n)
  rows=[r for r in rows if r[0]!=where];rows.append((where,'Hårt',what,s[:230].replace('|','&#124;').replace('`','')))
rows.sort(key=lambda r:(r[0].rsplit(':',1)[0],int(r[0].rsplit(':',1)[1])))
counts={t:sum(r[1]==t for r in rows) for t in ('Hårt','Avtal','Prov','Verktyg')}
text='''# MHR-beroenden inför ett möjligt byte till GEM-X/SOMA

Läsinventering 10 november 2026. Ingen anpassning av modellen eller riggen är gjord.
Tabellen gäller aktiv Pythonkod, scheman, statiska JSON-data, exempel, prov och
engångsverktyg under kontrakt/ och ingest/. Sökvägarna räknas från scen/3d/.
En rad är en referenspunkt; flera rader kan beskriva samma mekanism.
Genererade utdata, cache, historiska säkerhetskopior och pycache räknas inte som
nya kodberoenden. De måste byggas om eller behållas tydligt versionsmärkta vid
ett modellbyte. Binärdata inventeras via sina läsare och i listan nedan.

Sökningen omfattade MHR/SAM, riggfiler, 127 leder, 204/208 parametrar,
MHR70-råpunkter, pred_*-fält, lednamn och fasta index. Numeriska masktrösklar
(t.ex. 127 i en bildmask), SHA256-delsträngar och vanliga geometrivärden är
bortsorterade. Tabellen är en läsning av dagens kod, ingen utfästelse att en
namnöversättning skulle räcka. Inga modellkörningar, nätanrop eller Blenderanrop.

'''
text+=f"Inventerat: {len(rows)} referenspunkter i {len(set(r[0].rsplit(':',1)[0] for r in rows))} filer. Fördelning: "+', '.join(f'{k} {v}' for k,v in counts.items())+'.\n\n'
text+='''## Det som är hårt bundet

- MHR:s 127 globala leder, extra rot, cm/Y upp och kvaternion xyzw samt
  FBX-regeln led i = ben i−1. SOMA:s topologi och koordinater behöver eget avtal.
- 204 poseparametrar, 72 uttryck, 45 formparametrar och namngivna rot-/hand-/ben-
  parametrar i sekvenskedjan. GEM-X:s SOMA-parametrar är inte samma indata.
- MHR70 till riggleder: fingrar, handled 41/62, benens synlighet och skymnings-
  grupper. Dessa måste utgå från SOMA:s verkliga punktnamn, inte gissade index.
- Lod1/lod3-hud, viloposer, föräldrar, fothud och benvikter. Byt eller exportera
  om tro_hud.npz, tro_fothud.npz och tro_rigg.json för den nya riggen.
- Stöd-IK, sulkontakt och antropometriska priorer runt MHR root måste verifieras
  på nytt. Parametrisk propbank och rena tidsankare är i sig modelloberoende;
  deras handmätning och fästen är fortfarande MHR-bundna här.

## Riggtillgångar

| Tillgång | Vad den låser |
|---|---|
| ingest/mhr_ledernamn.json | 127 namn i exakt modellordning. |
| kontrakt/tro_rigg.json | MHR-lod3-namn och föräldraindex. |
| kontrakt/tro_hud.npz | MHR-lod1-hörn, trianglar, skinvikter och viloleder. |
| kontrakt/tro_fothud.npz | MHR-lod3-fothud, skinvikter, rest-heads och riggrotation. |
| kontrakt/testdata/stod_s1_fore_jamn.npz | Fryst MHR-pose för stödregression; kräver en separat ny SOMA-referens. |
| ../klipp2/sam3db/mhr/assets/lod1.fbx och lod3.fbx | Externa MHR-hud/riggfiler som läses av koden nedan. |
| ../klipp2/sam3db/ckpt-vith/assets/mhr_model.pt | Extern MHR-FK/modell. |
| ../klipp2/sam3db/mhr_parametrar.json och mhr_skelett.json | Externa parameternamn och föräldrar. |

modal_gemx.py lästes översiktligt men har inte ändrats: dess native77/SOMA-
export är en separat dataväg, ingen färdig MHR-översättare. Den filen utvecklas
samtidigt av en annan agent; dess radnummer/utformning kan därför ändras.

## Alla referenspunkter

Hårt = algoritm, råformat eller rigg. Avtal = schema/manifest/backend.
Prov = provdata/krav. Verktyg = diagnostik, exportkontroll eller engångsarbete.
Även ett verktyg kan kräva en verklig ny riggexport.

| Fil:rad | Typ | Vad som förutsätts | Kod/avtal vid referensen |
|---|---|---|---|
'''
for where,typ,what,s in rows:text+=f'| {where} | {typ} | {what} | `{s}` |\n'
p=H/'MHR-BEROENDEN.md'
if p.exists():andra(str(p.relative_to(ROT)),lambda old:text)
else:p.write_text(text,encoding='utf-8')
print(len(rows),'referenspunkter',len(set(r[0].rsplit(':',1)[0] for r in rows)),'filer',counts)
