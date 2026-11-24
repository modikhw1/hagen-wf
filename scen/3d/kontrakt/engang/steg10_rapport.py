"""Samla faktiska test-, data- och bildresultat; inga nya renderingar."""
import datetime
import json
from pathlib import Path

H = Path(__file__).resolve().parents[1]
O = H/'ut/aterupptagning'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def fmt(x, n=2): return 'saknas' if x is None else f'{x:.{n}f}'

tests = read(O/'prov_1.json')
extra = read(O/'riktade_slut.json')
data = read(O/'data_resultat.json')
visual = read(O/'synbedomning.json')
before = read(H/'ut/prop_granskning/notan_fore_efter.json')
px = read(H/'ut/prop_granskning/px_avstamning.json')
assert all(r['exit']==0 for r in tests+extra)
assert all(r['gron'] for r in data['regressioner'] if r['krav'])
lines = ['# Steg 10: verifierad kod, props som data och händelser','',
    'Återupptagningen följde den reducerade omfattningen: inga nätanrop, paketinstallationer, betalda modeller, kroppssteg eller nya renderingar. Blender-GUI användes inte. Tunga jobb kördes sekventiellt. Arkivet backup8/kod.tar lästes i en separat scratchpad-mapp, aldrig över projektet.','',
    '## Vad som fanns och vad som behölls','',
    'Den avbrutna körningen hade rättat ledurvalet i metodtabellen, gjort stegvisa stabiliseringsablationer, infört kroppsmåttcache och ett bakåtkompatibelt golvbeslut, samt lagt till propkälla, bank, planmatriser, kvalitet och en Blenderbyggare. Den sista sparade fulla sviten hade 116 prov och ett fel: notans bord hade tappats i delar av planen. Körningen hann därefter återställa golvbeslutet och bygga jamn_tom_rattad. Ingen av de begärda propfilmerna tom4/prop_byte/prop_tom fanns.','',
    'Detta behölls. Återupptagningen slutförde hashkontroll, händelser, tidsatta propändringar, verkliga dataplaner och regressioner. Inga utjämningsparametrar eller kvalitets-/testtoleranser ändrades. Den tidigare rapporttextens påstående om en använd fryst stödpose var inaktuellt: de aktuella stödproven läser dagens rättade notan-data. De oanvända analysartefakterna finns kvar. Den ursprungliga notan-källan uppdaterades uttryckligen; barklippets exempel ändrades inte.','',
    '## Prov och väggtider','',
    'Alla kommandon kördes från projektroten med scen/.venv/Scripts/python.exe, PYTHONIOENCODING=utf-8, och fyra CPU-trådar för långa prov. Kontraktsmappen sattes i PYTHONPATH för unittest.','',
    '| Prov | Antal | Exit | Väggtid s |','|---|---:|---:|---:|']
for r in tests+extra:
    lines.append(f"| {r['prov']} | {r.get('antal') or '–'} | {r['exit']} | {r['sek']:.2f} |")
lines += ['', 'Exakta kommandon och resultat finns i prov_1.json, prov_1.log, riktade_slut.json och riktade_slut.log. Fyra aktuella prop-/händelsekällor validerade utan varningar (kallkontroll.json). AST-kontroll, radslut och filändringar dokumenteras i filkontroll.json.','',
    'Rättningar: tidsfönster för propvarianter, bevarat äldre planformat för edits utan ankare, propbyte begränsat till scener där föremålet finns, strikt kontroll av händelse-id/personer/prop/tider, och ingestskanning som skiljer källmanifest från omhashningsloggar. Den kvarvarande kameraloggen avslöjade också ett verkligt fel: kor_jamn loggade bara en sammanfattning och lämnade tider.varld på en äldre körning. Nu loggas varje faktiskt stegresultat. Den aktuella Kenny-loggen har synkats från varld.npz, med den gamla posten bevarad och utan påstående om ny ingest.','',
    '## Inaktuella hashar','',
    'Notans exempel hade 16 fel efter omkörningar som skrev över filer på samma sökvägar: sju varld.npz, åtta sekvensfiler och kontakt_4.json. Det var ett verkligt manifestfel, inte ett skäl att stänga av hashkontrollen. kalla_omhasha.py exempel/notan/kalla.json --uppdatera uppdaterade alla 16 efter granskning. Original, före/efter-hash och ändrade pekare finns i ut/fore_prop/ och exempel/notan/kalla.json.omhashning.json. Semantikens revision behölls eftersom semantiken inte ändrades. kontrollera.py accepterar nu 64 hashar i notan och 15 i bar.','',
    'En ingestomkörning varnar nu direkt om berörda manifest, med exakt uppdateringskommando. Kontroll och kompilering stoppar fortfarande på avvikande hash. Händelsernas underlag är separat hashlåst: ändras det krävs ny mätning med kalla_handelser.py; gamla händelser kan inte göras aktuella bara genom omhashning.','',
    '## Px-glapp, drift och vald metod','',
    'Den ursprungliga tabellen tog bara två axelpar när benen var dolda, medan filmen räknade axlar plus 42 fingerleder. Urvalet delas nu mellan tabell och kvalitetsmätning: 44 par utan ben, 48 med ben. För b S1 beskriver 15,73/48,50 px filmen; 2,5/5,2 px beskrev det felaktigt begränsade urvalet. Ingen omrendering behövdes för detta: filmerna var byggda med den valda metoden.','',
    '| Klipp/scen | Rättad tabell median/p90 px | Film median/p90 px |','|---|---:|---:|']
for r in px:
    lines.append(f"| {r['klipp']}/{r['scen']} | {r['tabell'][0]:.2f}/{r['tabell'][1]:.2f} | {r['film'][0]:.2f}/{r['film'][1]:.2f} |")
lines += ['',
    'Alla sju avstämningar skiljer högst 0,00005 px. Tabellens metodmått tas före golv/kontakt/stöd i tagningens kamera; filmsidan mäter den byggda kroppen. De jämförda filmvärdena är numeriskt lika här, vilket ablationen visar; det är inte ett generellt löfte för andra planer. Underlag: ../prop_granskning/px_avstamning.json.','',
    'Stegvis ablation med rätt ledurval isolerar komponent-Hampel för handled/underarm som en viktig orsak till avvikelsen från estimatet: b S1 går från <0,001 till 56,79 px p90, a S1 till 32,20 px. Lågpass och det gamla cam_t-filtret bidrar också; med råa parametrar och bara gammal cam_t blir a S1 10,29/39,50 px. Att enbart återställa rå rot löser inte helheten. Det är belagt för dessa två scener, inte en universell ensam orsak eller bevis för den verkliga handens rörelse. Råformen varierar, men formval gav samma FK i b S1-ablationen.','',
    'Vald metod: rörutjämning 4 Hz, k=2, andra differensen; cam_t:s siktlinje/logavstånd 2 Hz. Identitet och benlängder hålls fasta. Luckor och avvisade estimatorrutor överbryggas över tid. Den iterativa viktningen försöker hålla sig inom ett brusbaserat parameterrör; det är en numerisk approximation, inte en hård garanti för ett visst pixelavstånd efter kinematik och stöd. Parametrarna behölls.','',
    '| b S1, metod | Median/p90 px | IoU synlig | Darr cm/ruta² | Täckning |','|---|---:|---:|---:|---:|',
    '| Gammal stabilisering | 12,51/53,80 | 0,780 | 0,77 | 100 % |',
    '| Bildskydd | 2,77/6,02 | 0,788 | 2,86 | 100 % |',
    '| Vald rörutjämning | 15,73/48,50 | 0,782 | 0,97 | 100 % |','',
    'Metoden är lugnare än bildskyddet, men fingerpassningen är sämre än det passningsdrivna 6 px-resultatet. Kenny S1 och a S1 har fortfarande för mycket darr. IoU-skillnaderna är små och ingen statistisk överlägsenhet visas. Ingen av de prövade metoderna har visats lösa alla sceners samtidiga krav på nära fingrar och lugn kropp. Hela jämförelsen finns i ../jamn_tabell/tabell.md.','',
    '## Kenny-kamera och diskar','',
    'Kenny S2: COLMAP observerar rutor 0–51, medan den fulla personen observeras först senare. Under personens rutor hålls kameran konstant. Skalsökningens mål blir därför platt; ett godtyckligt minimum gav tidigare cirka 11,7 km. Translationen i den använda varld.npz är 0 m och märkt okänd/avvisad; rotationen behålls. En senare provskala i filens diagnostik gav 14,3 km, också avvisad. Det är diagnostik före avvisning, inte den byggda kamerabanan.','',
    'Kontrollen prövar p90-fart högst 5 m/s, maxfart 15 m/s och väg högst 5 m/s × scenlängd. Platt skalkurva avvisas separat. Den gamla 11,7 km-posten levde kvar i tider.json eftersom kor_jamn inte loggade varld-resultatet; det rättades i denna återupptagning.','',
    'Diskarna har skiva, sammanhängande front och bakre hyllor. B s8–s10 saknar nu de gamla tvärskenorna över höften. De läses som grova diskar, men inte som källans glasmonter med våg. Den delvisa skymningskontrollen använder källans mask och loggar justering/utelämning av mallbitar. Kropparna flyttas inte för att få möblerna att passa.','',
    '## Notan och bar före/efter','',
    'Notans golv_tom ommättes med sin sparade kamera/plan och sekvens/varld från respektive fore_jamn. Samma rådata och masker används. Efter nedan är den aktuella dataplanens rättade golvbeslut, samma bas som den redan befintliga jamn_tom_rattad. Ursprungliga jamn_tom har dessutom en separat visuell bedömning nedan.','',
    '| Scen/person | Px median/p90 före → efter | IoU synlig före → efter | Darr före → efter | Maskrutor före/efter |','|---|---|---|---|---|']
new = read(H/'ut/notan/data_prop/plan.json')
for row in new['kvalitet']['kropp']['rader']:
    old = next(x for x in before['fore']['kropp'] if x['scen']==row['scen'] and x['person']==row['person'])
    op = next(x for x in before['fore']['bildtrohet']['personer'] if x['scen']==row['scen'] and x['person']==row['person'])
    np_ = next(x for x in new['kvalitet']['bildtrohet']['personer'] if x['scen']==row['scen'] and x['person']==row['person'])
    lines.append(f"| {row['scen']}/{row['person']} | {op['median_px']:.2f}/{op['p90_px']:.2f} → {np_['median_px']:.2f}/{np_['p90_px']:.2f} | {old['mask'].get('iou_synlig_median',0):.3f} → {row['mask'].get('iou_synlig_median',0):.3f} | {old['darr_cm_per_ruta2']['byggd']:.3f} → {row['darr_cm_per_ruta2']['byggd']:.3f} | {old['mask'].get('rutor',0)}/{row['mask'].get('rutor',0)} |")
bar=read(H/'ut/bar/data_prop/plan.json')
lines += ['',
    'Bar: byggdata är identiska mot ut/bar/plan_efter_baromkorning.json (ordinarie regression), inklusive objekt, kamera och tillämpade edits. Bar ingick inte i de fyra lokala jämn-omkörningarna. Före/efter är därför oförändrad kropp och samma källa; nya oberoende kvalitetsfält är diagnostik, inte en ny film.','',
    '| Bar s1/person, före = efter | IoU / IoU synlig | Darr byggd | Bedömda rutor |','|---|---:|---:|---:|']
for r in bar['kvalitet']['kropp']['rader']:
    lines.append(f"| {r['person']} | {r['mask'].get('iou_median',0):.3f} / {r['mask'].get('iou_synlig_median',0):.3f} | {r['darr_cm_per_ruta2']['byggd']:.3f} | {r['passning_bedomda']}/{r['ruta_antal']} |")
lines += ['',
    'Notans gamla jamn_tom är inte längre exakt samma golv-/kamerabas: den avbrutna körningen rättade redan före propdelen ett tappat äldre golvbeslut. Ursprungliga jämförelsen loggas öppet som avvikande. Prop-/händelseplanen jämförs dessutom exakt mot en ny tom baslinje med dagens källfiler; människor, kameror, scenbeskrivningar, källrutor och tidskarta är identiska. Sparade jamn_tom_rattad jämförs också i data_resultat.json.','',
    '## Synbedömning per scen','',visual['metod'],'',visual['text'],'',
    '| Klipp/scen | tom2 eller golv_tom | tom3 eller jamn_tom | Observation |','|---|---|---|---|']
for clip in ['b','kenny','a','notan']:
    for sid,old,now,note in visual[clip]:lines.append(f'| {clip}/{sid} | {old} | {now} | {note} |')
lines += ['', visual['visning'],'','### Remsor','']
for clip,note in visual['remsor'].items():lines.append(f'- {clip}: {note}')
lines += ['',
    '## Props som data','',
    'Se ../../PROPS.md. Kalla har semantisk typ/användning, bankform och scenvisa hållare, hand/led eller mall-/propstöd, avlästa bildregioner och RGB, samt metod/konfidens per uppgift. Typ/användning kommer vanligen från sparad Gemini-semantik. Bildregioner är lokalt manuellt avlästa och färgen är en osäker pixelmedian. Handrörelse kommer från sparade handledsleder. Storlek i meter, grepp, djup och dolda sidor är antagna/bankvärden, inte uppmätta tillgångar.','',
    'Banken innehåller kött på papper, våg, glassked, glasspatel, tallrik, burk, matlåda, kortterminal, mynt, kebabskärare, liten matportion och burgare; varje typ har grepppunkt och modell_ref:null. Den lila fiktiv_molnfrukt är uttryckligen påhittad.','',
    'Handfästen löses till 4×4-matriser per utdataruta efter samma kroppsstöd som filmen. Mallstöd är en konkret skiva/yta; missad siktlinje begränsas till kanten och rapporteras som antagande. Okänd position ger ingen geometri. Byte/tillägg/flytt/borttagning provas genom kompilatorn; tidsankare delar synlighetsintervall utan att ändra kropp/kamera/tid.','',
    '| Dataplan | Upplösta/listade propinstanser | Väggtid s |','|---|---:|---:|']
for r in data['korningar']:
    lines.append(f"| {r['klipp']}/{r['mapp']} | {r['upplosta']}/{r['props']} | {r['sek']:.2f} |")
lines += ['',
    'Notan har burgare på borden/i handen samt en lokalt avläst gul burk som semantiken saknade. B har kött/papper och våg, inklusive kamerahand som redan införd data. Kenny har sked/spatel; a har mynt, skärare och liten matportion/tallrik. Saknade fästen och dålig mallpassning redovisas i respektive kvalitetssida. Inga nya propfilmer skapades.','',
    'Varje data_prop/kvalitet.md innehåller en rad per prop/scen med närvaro i planen, handled/yta, projicerat centrumfel/breddkvot på provrutorna och antaganden. Måttet kräver ingen render och är ingen oberoende segmentering av den synliga produkten. Bankens material används; det är inte den uppmätta regionfärgen.','',
    'Den tidigare Blenderbyggaren och b S5:s förenklade förgrundshand finns kvar bakom sina gränssnitt. De är inte renderverifierade här. Ingen Blenderutvidgning gjordes; ingen körning kopplades till GUI. Browseradaptern är nästa separat avgränsade arbete.','',
    '## Händelser och ankare','',
    'Se ../../HANDELSER.md för schema, detektion, kommandon och regiexempel. Fält: id, typ/vad, vem, till_vem, prop, scen, tidpunkt eller spann, ursprung med metod/modell/konfidens. Källrutor och filbelägg finns i matning; underlagen har hashar.','',
    '| Klipp | Spårstarter/slut | Replikstarter | Avlästa propförekomster | Semantiska scenspann | Hållarbyteskandidater | Handmöten |','|---|---:|---:|---:|---:|---:|---:|']
for clip in ['notan','b']:
    e=read(O/(clip+'_handelser.json'));c=e['antal']
    lines.append(f"| {clip} | {c.get('person_synlig',0)}/{c.get('person_forsvinner',0)} | {c.get('replik_start',0)} | {c.get('prop_synlig',0)} | {c.get('scen_handling',0)} | {c.get('hallarbyte_kandidat',0)} | {c.get('handmote',0)} |")
lines += ['',
    'Notan: 39 poster. Bakgrundsspår okand_s4_4 börjar 6,70 s; övriga starter ligger vid scenklipp och bevisar ingen entré. B: 54 poster; A→B och B→C är två antagna hållarbyteskandidater över klipp, inte säkert uppmätta mottagningar. Ingen kontinuerlig objektidentitet eller faktisk överräckning har kunnat fastställas. En avläst propförekomst är den första av två provrutor, inte säkert första synliga bildrutan.','',
    'Editens tid kan skrivas tid.fran/tid.till med handelse, eventuell kant=start/slut och offset_s. Ett spann kräver vald kant. Planen sparar upplöst källtid och alla förekomster efter trimning/omordning/duplicering. B:s fiktiva byte finns både för hela klippet och från s6_prop_o1_synlig till början av s8_semantisk_handling. Notans byte av burk från en avläst förekomst finns i data_eventbyte. Båda verkliga klippens prov kontrollerar att originaltypen finns utanför intervallet och att person/kamera/tid är oförändrade.','',
    '## Filer, protokoll och kvarstående problem','',
    'Pipelineändringar och nya filer står i ../../README.md och filkontroll.json. Nya huvudfiler: kalla_handelser.py, handelser.py, proptid.py, ingest/kallstatus.py och test_handelser.py. Befintlig kompilator, scheman, hashverktyg, propupplösning, ingestloggning och README/PROPS ändrades. Engångsverktygen ligger i engang/. Före-kopior med relativa sökvägar finns i ut/fore_prop/, med en extra snapshot från återupptagningens start.','',
    '1. Kenny S1 och a S1 har fortsatt för mycket darr; flera scener har fingerfel. Grön kod betyder inte grön filmkvalitet.',
    '2. Propplanens djup, grepp, mallpassning och mått är fortfarande grova antaganden; vissa propinstanser utelämnas när position saknas.',
    '3. Ingen säker matöverlämning eller kontinuerlig propidentitet är uppmätt; CM måste välja/granska ett osäkert spann.',
    '4. Kenny S2:s separata arm och a S3/S6:s huvudinnehåll saknas fortfarande i de granskade filmerna.',
    '5. Ursprungliga notan/jamn_tom har tappade bord; använd den redan befintliga jamn_tom_rattad som senare referens.',
    '6. Browseradapter/slututseende är inte byggda i detta uppdrag; planens äldre backendnamn är blender_mhr.',
    '7. Maskmåttet är oberoende av kroppsestimatorns 2D-punkter men har kända skevheter för kläder, hår, skymning och föremål.',
    '8. Kvalitetsgränserna är diagnostiska projektval. Textfont/radbrytning och grova mallmiljöer matchar inte källan exakt.','',
    'Nästa arbete med störst värde: läs dessa dataplaner i browsern och granska handfäste, propdjup och stödytor interaktivt innan mer renderarbete.','']
start=datetime.datetime.fromisoformat(read(O/'start.json')['start'])
lines += [f'Rapport skapad {datetime.datetime.now().isoformat(timespec="seconds")}; väggtid sedan protokollstart {(datetime.datetime.now()-start).total_seconds():.1f} s. Dataplanernas och provens separata tider finns ovan.']
(O/'rapport.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(O/'rapport.md')
