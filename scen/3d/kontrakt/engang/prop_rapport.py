"""Samla verifierade resultat och den manuella bildgranskningen, efter filmerna."""
import json
import sys
from pathlib import Path
H=Path(__file__).resolve().parents[1];O=H/'ut/prop_granskning'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
tests=read(O/(sys.argv[1]+'.json' if len(sys.argv)>1 else 'prov_slut.json'))
renders=read(O/'renderingar.json');reg=read(O/'regression.json');before=read(O/'notan_fore_efter.json')
assert len(tests)==5 and all(x['exit']==0 for x in tests),tests
assert len(renders)==5 and all(x['exit']==0 for x in renders),renders
assert all(x['gron'] for x in reg['resultat']),reg
visual=read(O/'synbedomning.json');props_visual=read(O/'prop_synbedomning.json')
px=read(O/'px_avstamning.json');ablation=read(O/'stegablation.json')
lines=['# Uppföljning av jämn-passet och första rekvisitan','',
       'Lokalt arbete, utan nätanrop, modellservice, kroppskörning, nedladdning eller installation. Tunga jobb kördes ett i taget. Den öppna Blender-sessionen användes inte. Befintliga ändrade filer har kopior med relativa sökvägar i `ut/fore_prop/`.','',
       '## Prov och faktiska rättningar','',
       '| Prov | Exit | Väggtid s |','|---|---:|---:|']
for x in tests:lines.append(f"| {x['prov']} | {x['exit']} | {x['sek']:.2f} |")
lines+=['',
    'Den första fulla körningen fann 19 fel från inaktuella mätfilshashar och fyra fall där historiska prov jämfördes med ändrade indata. Nya hashlåsta källkopior används av proven; ursprunglig notan-källa och barklippets exempel är bevarade. Stödprovens ursprungliga pose har frysts i `testdata/`; dagens alla notan-rutor prövas separat. Platsens historiska efterbearbetade filmreferens är inte en ny automatisk platslösning. Proven jämför två nya körningar exakt, och filmregressionen skyddar kamera/person/tid mot den sparade planen. Se `testdata/README.md`. Inga fysik-, kvalitets- eller testtoleranser har höjts. Bro ändrades bara i testets källsökväg; semantik-koden ändrades inte.','',
    'Nytt regressionsprov fångar tabellens tappade fingerleder. En processlokal cache för högst 32 identiska kroppsmätningar förkortar upprepade kompileringar; filer, kamera, stöd och tidsurval ingår i nyckeln och cacheinvalidering provas. Ingen maskruta utesluts därifrån.','',
    '## Px-glappet och den gamla avvikelsen','',
    'Tabellens `if not rel: d=d[[0,1]]` behöll endast två axelleder när benen var dolda. Kvalitetssidan behöll dessutom 42 fingerleder: 44 par. Båda använder nu samma urval. Samtliga sju scener stämmer mot filmens lagrade kvalitet med högst 0,00005 px rest; se `px_avstamning.json`. Filmerna byggdes alltså med vald metod, och behövde inte göras om på grund av tabellfelet. Råformens påstådda konstans var också fel, men formbyte gav identisk FK i den isolerade b S1-ablationen och förklarar inte dess glapp.','',
    '| Klipp/scen | Rättad tabell median/p90 px | Film median/p90 px |','|---|---:|---:|']
for x in px:lines.append(f"| {x['klipp']}/{x['scen']} | {x['tabell'][0]:.2f}/{x['tabell'][1]:.2f} | {x['film'][0]:.2f}/{x['film'][1]:.2f} |")
lines+=['',
    'Stegvis ablation isolerade det gamla komponent-Hampel-filtret för handled/underarm: med rå cam_t går b S1 p90 från <0,001 till 56,79 px och a S1 till 32,20 px. Lågpassning och det gamla cam_t-filtret bidrar också. Enbart gammal cam_t på råa parametrar ger a S1 10,29/39,50 px. Att enbart återställa rå rot förbättrar inte helheten. Det tidigare säkra påståendet om roten var för starkt. Detta är belagt för de två ablaterade scenerna; ingen universell ensam orsak påstås. `stegablation.json` och `identitetsablation.json` har alla mellanled.','',
    'Vald metod är rör 4 Hz k2 med ny cam_t, låst identitet och utan bildskyddets per-ruta-blandning. Tre jämförbara rader för b S1 ur den rättade tabellen:','',
    '| Metod | Median/p90 px | IoU synlig | Darr cm/ruta² | Täckning |','|---|---:|---:|---:|---:|',
    '| Gammal stabilisering | 12,51/53,80 | 0,780 | 0,77 | 100 % |',
    '| Bildskydd, tom2 | 2,77/6,02 | 0,788 | 2,86 | 100 % |',
    '| Rör 4 Hz k2 + ny cam_t | 15,73/48,50 | 0,782 | 0,97 | 100 % |','',
    'Metoden är lugnare än bildskyddet men löser inte både fingerpassning och darr överallt. Kenny S1 har 3,77 och a S1 4,41 cm/ruta² i den byggda kroppen. Px är en passningsrest mot estimatorns egna punkter, inte ett oberoende kvalitetsbevis. Full metodjämförelse: `../jamn_tabell/tabell.md`.','',
    '## Kamera och diskar','',
    'Kenny S2:s skala var oidentifierbar: kameran rörde sig när ingen full person fanns, och var konstant under personens mätbara rutor. Argmin på en platt ojämnhetskurva gav k≈785 och 11 693 m. Translationen avvisas nu, rotationen behålls, och den använda banan är 0 m. Gränserna är p90 5 m/s, max 15 m/s och sträcka 5 m/s × längd. Det är en märkt okänd translation, inte återfunnen sann kamerarörelse. `test_kroppmatt.Kamerabana` prövar gränserna.','',
    'Diskarna har sammanhängande front/skiva och bakre hyllor, men är fortfarande grova parametriska möbler. I de öppnade b s8–s10-bladen är tom2:s tunna skena över höften borta. Fronten kan nu läsas som disk, men motsvarar inte källans exakta glasmonter. Skymningskontrollen granskar synliga delar mot källmasken och loggar utelämnade mallbitar; den ändrar inte personer.','',
    '## Notan och bar före/efter','',
    'Notans gamla film har ommätts med dess plan och säkerhetskopierade sekvens/värld från fore_jamn. Samma rådata och masker används. Alla sju scener ingår; före/efter nedan är golv_tom/jamn_tom.','',
    '| Scen/person | Px median/p90 före → efter | IoU synlig före → efter | Darr före → efter | Maskrutor före/efter |','|---|---|---|---|---|']
for r in before['efter']['kropp']:
    old=next(x for x in before['fore']['kropp'] if x['scen']==r['scen'] and x['person']==r['person'])
    op=next(x for x in before['fore']['bildtrohet']['personer'] if x['scen']==r['scen'] and x['person']==r['person'])
    np=next(x for x in before['efter']['bildtrohet']['personer'] if x['scen']==r['scen'] and x['person']==r['person'])
    lines.append(f"| {r['scen']}/{r['person']} | {op['median_px']:.2f}/{op['p90_px']:.2f} → {np['median_px']:.2f}/{np['p90_px']:.2f} | {old['mask'].get('iou_synlig_median',0):.3f} → {r['mask'].get('iou_synlig_median',0):.3f} | {old['darr_cm_per_ruta2']['byggd']:.2f} → {r['darr_cm_per_ruta2']['byggd']:.2f} | {old['mask'].get('rutor',0)}/{r['mask'].get('rutor',0)} |")
lines+=['',
    'Bar: golden-regressionen mot `ut/bar/plan_efter_baromkorning.json` är oförändrad i byggdata; nya kvalitetsfält tillkommer. Den nya diagnostiken finns i `bar_kvalitet_prop.md`, planen i `bar_plan_prop.json`. Detta är inget nytt bar-renderprov. Personer, kameror och tidskarta jämförs även separat i `regression.json`. Notans propfilm har samma personer, kameror och tidskarta som jamn_tom.','',
    '## Manuell bedömning per scen före props','',visual['metod'],'',visual['text'],'',
    'Bedömningen nedan gäller vad stillbilderna visar. Hela klippets darr och de automatiska gränserna på kvalitetssidan gäller dessutom; en stillbild med rimlig pose gör inte en darrig film godkänd.','',
    '| Klipp/scen | tom2 eller golv_tom | tom3 eller jamn_tom | Vad som syns |','|---|---|---|---|']
for clip in ['b','kenny','a','notan']:
    for sid,old,new,note in visual[clip]:lines.append(f'| {clip}/{sid} | {old} | {new} | {note} |')
lines+=['',visual['visning_fore_props'],'','### Remsor','']
for clip,note in visual['remsor'].items():lines.append(f'- {clip}: {note}')
lines+=['','Den extra `strip_notan_golv_jamn.png` visar den begärda golv_tom-jämförelsen: lugn rörelse i båda fönstren, men ett smalt bord och blottade ben i jamn_tom S6 där källans bord fyller nederdelen. S4:s gest är likartad; texten finns i den nya filmen.','',
    '## Rekvisita','',
    'Se `../../PROPS.md`. Typ, användning och ursprunglig hållare kommer från sparad semantik med modell/konfidens. Bildregioner är manuellt avlästa i två källrutor. Bredd och RGB mäts i regionerna; färgen är en osäker regionmedian och bankens material används fortfarande. Handposition och rörelse kommer från befintliga handledsleder. Djup, grepp, dolda sidor och proportioner är märkta antagna/bankvärden. Kamerahanden i b S5 använder förgrundsspår 2 och antaget djup 0,65 m. Inga nya fulla kroppar har hittats på.','',
    'Bank: papper med kött, våg, glassked, glasspatel, tallrik, burk, matlåda, kortterminal, mynt, kebabskärare, portion på tallrik och burgare. Alla har greppunkt och reserverad modell_ref. Byte, tillägg, flytt och borttagning fungerar i regi. Lila molnfrukt med turkos detalj är uttryckligen påhittad i `ut/b/produkter_fiktiva.json`; dess byte finns i `ut/b/regi_prop_byte.json`.','',
    '### Byggd geometri och bildmatchning per propfilm','',
    '| Film | Byggda propinstanser / listade | Väggtid s | Film, blad och kvalitet |','|---|---:|---:|---|']
for r in renders:
    folder=H/'ut'/r['klipp']/r['mapp'];p=read(folder/'plan.json');built=sum(x['byggd'] for x in p.get('props',[]));total=len(p.get('props',[]))
    assert (folder/'film.mp4').exists() and (folder/'kvalitet.md').exists()
    lines.append(f"| {r['klipp']}/{r['mapp']} | {built}/{total} | {r['sek']:.2f} | film.mp4, blad/sN.png, kvalitet.md |")
for clip,entries in props_visual.items():
    lines+=['','### '+clip,'','| Scen | Omdöme | Vad som syns mot källan |','|---|---|---|']
    for sid,verdict,note in entries:lines.append(f'| {sid} | {verdict} | {note} |')
lines+=['','## Filer och återstående arbete','',
    'Pipeline: kalla_prop.py, prop_referenser.json, propbank.py, propplan.py och ingest/prop_blender.py är nya. Kompilator, Blenderingång, kvalitetssida, schema och README har kopplats ihop. Trohet och metodutvärdering delar nu ledurval; kroppmatt har cache med invalideringsprov. Stödberäkning, personer, kameror, tidskarta och betalda kroppsfiler har inte ändrats i propdelen. Nya tester/underlag samt bro-testets inaktiva källsökväg har uppdaterats. Engångsverktyg ligger i engang/. Alla befintliga ändrade filer kan återställas från fore_prop.','',
    'Den manuella granskningens återstående problem och förslag finns i `slutbedomning.json`. Ägarvisning gäller uttryckligen märkta teknikprov; inget klipp beskrivs som en färdig trogen kundfilm.']
path=O/'rapport.md'
if path.exists():raise FileExistsError(path)
path.write_text('\n'.join(lines)+'\n',encoding='utf-8');print(path)
