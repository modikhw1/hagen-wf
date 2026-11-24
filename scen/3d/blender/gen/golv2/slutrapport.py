import sys,json,hashlib,shutil,re
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.path[:0]=[str(HERE),str(P/'ingest')]
from prova import save,log,sha
def load(p):return json.loads((HERE/p).read_text(encoding='utf-8'))
def write(p,text):
    dest=HERE/p
    if dest.exists():
        back=P/'kontrakt/ut/fore_golv2_blender'/dest.relative_to(ROOT);back.parent.mkdir(parents=True,exist_ok=True)
        if not back.exists():shutil.copy2(dest,back)
    dest.write_text(text,encoding='utf-8',newline='\n')
rows=load('bildmatning.json');summary=load('sammanfattning.json');ingest=load('ingest_matning.json');props=load('prop_jamforelse.json')
contacts=load('mobelkontakter.json');seats=load('sitskontakter.json')
assert all(load('fore_indatakontroll.json')[i]['byteidentisk'] for i in range(len(load('fore_indatakontroll.json'))))
assert all(x['antal_scen_skillnader']==0 for x in load('exakt_scenjamforelse.json').values())
assert all(s['golv_version']==2 and s['cam_t']['exakt_mot_metrisk'] and s['pose']['exakt_mot_metrisk'] and s['cam_t']['kontakt_exakt_orord'] and s['pose']['kontakt_exakt_orord'] for r in ingest for s in r['sekvenser'])
assert all(r['varld_version']==2 for r in ingest)
assert max(r['blender_numpy_max_px'] for r in rows)<.02
assert all(sha(Path(f))==h for f,h in load('original_hashar.json').items())
v=['# Varje renderad ruta','',
   'Pixlar avser källans 576×1024. IoU är rasteriserad Blenderhud mot YOLO-union inom egen bbox med 8 % marginal. Synlig IoU klipper hud under källmaskens nederkant. Möbler undanlagda enbart i hudpasset. 44 ledpar utan dolda höfter/knän, varav 42 finger-/handledspunkter. Ledpunkterna är estimatorns egna, inte oberoende annotationer. Inga diagnostiska toleranser ändrade.','',
   '| Scen/ruta | Ledfel efter median/p90 px | IoU före → efter | Synlig IoU före → efter | Sula efter cm | Bilder |',
   '|---|---:|---:|---:|---:|---|']
for r in rows:
    sid,u=r['scen'],r['ut'];a,b=r['fore'],r['efter'];prefix=f'jamforelser/{sid}_{u:03d}'
    v.append(f'| {sid}/{u} | {b["median_px"]:.2f}/{b["p90_px"]:.2f} | {a["mask"]["iou"]:.6f} → {b["mask"]["iou"]:.6f} | {a["mask"]["iou_synlig"]:.6f} → {b["mask"]["iou_synlig"]:.6f} | {100*b["sula_over_golv_m"]:.3f} | [sida]({prefix}_sida.png), [RGB-överlägg]({prefix}_rgb_overlagg.png), [hud]({prefix}_overlagg.png), [före/efter]({prefix}_fore_efter.png), [flyttad]({prefix}_flyttad.png) |')
write('RUTOR.md','\n'.join(v)+'\n')
v=['# Alla numeriska försämringar i de prövade måtten','',
   'Små rasternedgångar redovisas också. De är inte belägg för en visuellt märkbar försämring. Kontakter, inklusive alla före/efter-rutor, finns i mobelkontakter.json och sitskontakter.json.','',
   '| Ruta | Δ IoU efter−före | Δ synlig IoU | Δ median led px | Δ p90 led px |', '|---|---:|---:|---:|---:|']
for r in rows:
    a,b=r['fore'],r['efter'];d=[b['mask']['iou']-a['mask']['iou'],b['mask']['iou_synlig']-a['mask']['iou_synlig'],b['median_px']-a['median_px'],b['p90_px']-a['p90_px']]
    if d[0]<0 or d[1]<0 or d[2]>0 or d[3]>0:v.append(f'| {r["scen"]}/{r["ut"]} | {d[0]:+.8f} | {d[1]:+.8f} | {d[2]:+.8f} | {d[3]:+.8f} |')
v+=['','## Rekvisita, samtliga befintliga källregioner','',
    'Beräknad bankforms omslutning, samma geometri/matriser som Blender. Källboxarna är tidigare manuellt avlästa, inte objektmasker. Dessa referensrutor är inte exakt de 21 renderprovrutorna. Breddkvot 1 vore lika bred som källregionen.','',
    '| Scen/prop/källruta | Centrumfel före → efter px | Breddkvot före → efter | Försämring |','|---|---:|---:|---|']
fore={(r['scen'],r['prop']):r for r in props if r['fas']=='fore'}
for r in [r for r in props if r['fas']=='efter']:
    old=fore[r['scen'],r['prop']]
    for a,b in zip(old['jamforelse'],r['jamforelse']):
        bad=[]
        if b['centrumfel_px']>a['centrumfel_px']+1e-8:bad.append('centrum')
        if abs(b['breddkvot']-1)>abs(a['breddkvot']-1)+1e-8:bad.append('bredd')
        v.append(f'| {r["scen"]}/{r["prop"]}/{b["kallruta"]} | {a["centrumfel_px"]:.6f} → {b["centrumfel_px"]:.6f} | {a["breddkvot"]:.6f} → {b["breddkvot"]:.6f} | {", ".join(bad) or "ingen"} |')
v+=['','S4/C: sulhöjden ökar från cirka 0 till 10,4–11,9 cm. S7 saknar synlig sits före och efter. Före/efter-bordskontakter ska läsas som led mot mallmöbel, inte som bevisad handkontakt; personer gestikulerar.']
write('FORSAMRINGAR.md','\n'.join(v)+'\n')
maxdrop=max(r['fore']['mask']['iou']-r['efter']['mask']['iou'] for r in rows)
table='\n'.join(f'| {r["scen"]} | {r["fore_iou"]:.3f} → {r["efter_iou"]:.3f} | {r["efter_iou_synlig"]:.3f} | {min(r["median_px"]):.1f}–{max(r["median_px"]):.1f} | {max(r["p90_px"]):.1f} | [alla tre](montage/{r["scen"]}_alla.png), [vid](montage/{r["scen"]}_vid.png) |' for r in summary)
it=[]
for r in ingest:
    for s in r['sekvenser']:
        it.append(f'| {r["klipp"]}/{r["tagning"]}/{s["fil"][8:-4]} | {100*s["cam_t"]["max_mot_ra"]:.3f} | {s["pose"]["max_mot_ra"]:.6f} |')
tests=load('testresultat.json')
assert len(tests)==3 and all(r['exit']==0 for r in tests)
testtext='; '.join(f'{r["modul"]}: '+re.search(r'Ran (\d+) tests', (HERE/f'{r["modul"]}.log').read_text(encoding='utf-8')).group(1)+' gröna' for r in tests)
report=f'''# GOLV2 i Blender

**Dom: nej, hela notanscenen återges inte tillräckligt troget; nej, scenen håller inte fullt från flyttad kamera. Kropparnas ursprungsprojektion är däremot bevarad.** Den viktigaste nya bildförsämringen gäller ytfäst rekvisita: hamburgarens centrumfel ökar i S3 cirka **35 → 103 px**, S2 **124 → 153 px**, S7 **17 → 45 px**. Burken i S3 går **50 → 70 px**. Se [S3 före/efter och källa](montage/s3_alla.png). Detta är inte ett nytt kroppsfel.

## Del 1: riktiga ingestdata på kopior

Bara `steg_golv` och `steg_kontakt` kördes på notan S1–S7 och bar, under `scen/3d/kontrakt/ut/golv2_ingestprov/data/`. **8 världsfiler och 10 sekvenser fick golv_version=2; inga körfel.** Kontaktsteget lämnar båda arrayerna exakt orörda.

Mot **metrisk.las(indata)** är samtliga cam_t och pose exakt lika, tal för tal (maxskillnad 0). Mot **råindata på disk är de inte oförändrade**: golvstegets avsiktliga migration återställer historiskt golv/kontakt. Största absoluta komponentändring:

| Klipp/tagning/person | cam_t, cm | pose, rå arrayenhet |
|---|---:|---:|
{chr(10).join(it)}

Poseändringarna i S4/4 och bar/2 är återställning av `pose_fore_kontakt`; övriga poser är orörda. Posearrayen blandar cm, quaternion och skala; redovisad maxkomponent ligger i translationsdelen. Alla återställda värden är exakt den befintliga metriska läsarens värden, inte nya skattningar.

Kompilering från kopian ger **exakt samma scen** som dagens original genom metrisk: kamera, kropp, stöd, rum, props, tidskarta och övriga planfält är identiska utan numerisk tolerans. Hela filen är inte identisk: notan har 23 ändrade filhashar och en ändrad byggunderlagsförteckning; bar 5 hashändringar och en förteckning. Extra `golv_prov.json` i kopian förklarar listlängden. Bara sökvägar och denna filproveniens undantogs i den exakta scenjämförelsen. [Diffar](notan_plandiff.json), [bar](bar_plandiff.json), [exakt kontroll](exakt_scenjamforelse.json).

**921 ursprungsfiler SHA256-kontrollerade: 0 ändrade.** Banker skrevs inte. [Ingestmått](ingest_matning.json), [originalkontroll](original_kontroll.json).

## Del 2: faktiskt Blenderresultat

Ordinarie väg: tom regi → `kompilera.py` → `ingest/mhr_rig.py:bygg` → FBX lod3/Workbench i **Blender 5.2.3**. Den planvägen använder mhr_rig:s metriska läsare. Även just `blender/mhr_blender.py:importera` prövades separat på S1, med tre nycklade världsposer: exakt samma cam_t/pose som metrisk (inte rå cam_t).

**21 rutor, 288×512:** 2/36/70, 75/93/111, 116/142/168, 173/213/253, 258/268/278, 283/309/334, 339/360/380. Varje ruta renderades från original och från +0,5 m kamerahöger/+0,3 m världsupp, med oförändrad lins och samma målpunkt på originalets optiska axel vid torsons djup. Mitt även med halverad lins för golvöversikt; de vidare bilderna är separat diagnostik.

Förejämförelsen är **ny Blender-rendering med arkiverad före-GOLV2-kod**, omkompilerad mot exakt samma dagens källmanifest, tomma regi och FBX som efter. Alla berörda gamla sekvens-/världsdata är byteidentiska med dagens original. Kodursprung: `fore/kodursprung.json`. Inga produktionsfiler ersattes.

Blenderleder mot numpy: max **{max(r['blender_numpy_max_px'] for r in rows):.6f} px / {1e6*max(r['blender_numpy_max_m'] for r in rows):.2f} µm**. Synliga leder före/efter flyttar högst **{max(r['max_synlig_ledflytt_px'] for r in rows):.6f} px**. Inga synliga ändringar av överkroppens storlek eller hållning hittades. S6 har kvar tydlig handavvikelse, och S3:s slutruta har p90 68 px. Måttet domineras av fingrar och är mot estimatorns egna punkter.

| Tagning | Hud-IoU median före → efter | Synlig IoU efter | Ledmedian, spann px | Största rut-p90 px | Bilder |
|---|---:|---:|---:|---:|---|
{table}

IoU är verkligt Blenderhudpass mot YOLO, inom personens egen ruta. Hår, kläder och skymmande bord skiljer mask från hud. De små nedgångarna är högst **{maxdrop:.6f}** i en enskild ruta; orörda leder och likadana överkroppsbilder talar för raster-/flyttalsrest. S4:s högre IoU följer ändrad dold benpose. [Alla 21 mätningar och överlägg](RUTOR.md), [alla numeriska försämringar](FORSAMRINGAR.md).

**Sett från flyttad kamera:** A/B sitter överlag rimligt vid stolarna i S1–S6; möbelhöjderna är 43 cm sits och 76 cm bord. Sulorna ligger cirka 0,1 mm över golvet efter stöd. Rotleden ligger 9,6–11,9 cm över sitsen, inte en oberoende mätning av hudkontakt. S5:s bäcken är 17–19 cm från sitscentrum och nära kanten. **S7 har ingen synlig sits** före eller efter; händerna hamnar i mittprovet 30/42 cm utanför bordsskivans XY-gräns efter, mot 0/8 cm före. Så bordskontakten håller sämre. Handledshöjder och gester redovisas separat i `mobelkontakter.json`.

**S4/C bekräftat:** sulan är **10,38 / 11,24 / 11,90 cm** över golvet, före cirka 0. I oförändrat utsnitt syns inte fötterna; i [vidare Blenderbild](montage/s4_vid.png) är glappet och frånvaron av fotkontakt synligt. Ingen rättning gjord. Golvet kommer från person 4:s synliga fötter; den personen utelämnas av planen. Det är därför ingen verklig samtidig flerpersonsrendering som styrker inbördes storlek. Kropparnas storlek mot de generiska stolarna ser rimlig ut, men rummet är fortfarande en mall.

**Orsak till rekvisitaförsämringen, belagt i planen:** bildstrålen missar bordsskivan mer efter GOLV2: S2 34,4→41,0 cm, S3 6,5→14,7 cm, S7 35,6→70,1 cm. `propplan.py` klipper då till bordskanten. Kamerakompensationen har tagits bort medan möblerna ligger i mallramen. Det förklarar de uppmätta propskillnaderna. De redan för stora hamburgarna finns även före; breddkvoten ökar exempelvis S3 2,11→2,29 och S7 1,95→2,21. Att lösa detta kräver beslut om möbel-/ytpassning; golvlogik, toleranser och design lämnades orörda.

## Filer och avgränsning

`efter/` och `fore/`: planer, sparade .blend, originalbilder, flyttade vyer, hudpass och Blenderloggar. `jamforelser/`: sida vid sida, RGB 50/50, hudöverlägg och före/efter för varje ruta. `montage/`: samtliga 21 rutor visuellt granskade, samt sju vidare före/efter. Masker och vanliga vyer körs i separata pass för att undvika Blenders återutvärdering av animerad synlighet; tidiga felaktiga provbilder/mått ersattes. Slutliga vyer renderades ur återöppnad ordinarie scen.

Ingen produktionskod ändrad; bara provverktyg och artefakter tillagda. Ändrad befintlig provkod säkerhetskopierades under `ut/fore_golv2_blender/`. Seriellt från kontrakt/: **{testtext}** (83 prov, 0 fel). Testloggar finns här. Blender gav en varning om misslyckad miniatyrbild, men byggnad, PNG och .blend lyckades.

**Inte kört:** helfilm, ljud/muxning, ny inferens/övrig ingest, Modal, GPU-tjänst, full diagnostikkompilering eller hela 198-provsuiten. Ingen oberoende verklig golv-/möbelinmätning eller mänsklig 2D-annotation finns i detta prov. Körhistorik och nästa kommando: `kontrakt/GOLV2-BLENDER-LOGG.md`.
'''
write('UNDERLAG.md',report)
report=f'''# GOLV2 i Blender

**Dom: nej för hela notanscenen; nej, den håller inte fullt från flyttad kamera. Kropparnas ursprungsprojektion är bevarad, men ytfäst rekvisita har blivit sämre.**

Viktigaste försämringen: hamburgarens centrumfel mot befintliga källregioner ökar **S3 35→103 px, S2 124→153 px, S7 17→45 px**; S3:s burk **50→70 px**. Det syns i [S3:s tre käll-/före-/efterbilder](montage/s3_alla.png). Måtten är planens projektion av samma bankgeometri som Blender, mot tidigare manuellt avlästa objektboxar.

## Del 1

- Bara golv och kontakt körda på kopior av notan S1–S7 och bar under `kontrakt/ut/golv2_ingestprov/data/`. **8 världsfiler och 10 sekvenser fick golv_version=2, inga fel.**
- **cam_t/pose exakt lika metrisk.las(indata), maxskillnad 0.** Kontakt ändrar ingenting. Mot råfilerna är de däremot inte orörda: äldre golv/kontakt återställs avsiktligt. Största cam_t-komponentändringen är 72,06 cm (S7); pose återställs för S4/person 4 och bar/person 2. [Alla skillnader](UNDERLAG.md), [tal för tal-kontroll](ingest_matning.json).
- Kompilering ger **exakt samma scen utan numerisk tolerans**: kroppar, kameror, stöd, möbler, props och tidskarta. Hela planfilerna skiljer endast sökvägar/proveniens: 23 filhashar i notan, 5 i bar och byggunderlagets förteckning. [Exakt scenkontroll](exakt_scenjamforelse.json).
- **921 originalfiler hashkontrollerade, 0 ändrade.** Banker skrevs inte.

## Del 2

**21 rutor, början/mitt/slut i alla sju tagningar, 288×512, Blender 5.2.3 Workbench.** Tom regi → kompilator → ordinarie `ingest/mhr_rig.py`. Före renderades på nytt med arkiverad före-GOLV2-kod mot samma källmanifest, data och FBX. Även `blender/mhr_blender.py` prövades separat: metriska värden läses exakt.

Originalkamera: Blender mot numpy skiljer högst **0,00222 källpixel**; synliga leder före/efter högst **0,00143 px**. Personernas bildläge, storlek och överkroppshållning ser bevarade ut. S6:s handfel och S3:s slutruta (p90 68 px) finns kvar. Ledmåttet är mot estimatorns egna punkter, huvudsakligen fingrar.

| Tagning | Hud-IoU median före → efter | Synlig IoU efter | Ledmedian, spann px | Största rut-p90 px | Bilder |
|---|---:|---:|---:|---:|---|
{table}

Hudpasset är verklig Blenderhud mot YOLO inom egen bbox; hår/kläder/occlusion gör att mask och hud skiljer sig. Största enskilda IoU-nedgång är **{maxdrop:.6f}**, utan synlig överkroppsförsämring. S4:s benpose ger något bättre IoU. [Alla rutor, sida vid sida och överlägg](RUTOR.md), [varje numerisk försämring](FORSAMRINGAR.md).

Flyttad kamera: +0,5 m kamerahöger, +0,3 m upp, samma mål och lins. A/B sitter överlag rimligt i S1–S6; sulor cirka 0,1 mm över golvet efter stöd, sits 43 cm och bord 76 cm. Rotleden ligger 9,6–11,9 cm över sitsen, vilket inte bevisar hudkontakt. S5 sitter nära stolskanten. **S7 saknar renderad sits före/efter**; dess handleder är i mittprovet 30/42 cm utanför bordet efter, mot 0/8 cm före. [Kontakter](mobelkontakter.json).

**S4/C svävar 10,38/11,24/11,90 cm**, bekräftat i Blender. Fötterna är fortfarande beskurna med oförändrad lins; en separat [vidare före/efterbild](montage/s4_vid.png) visar glappet. Ingen rättning. Person 4, som ger golvcue, utelämnas av planen; samtidig inbördes personstorlek är därför inte verifierad.

Rekvisitans försämring följer möbelpassningen: bildstrålen missar bordsskivan S3 6,5→14,7 cm och S7 35,6→70,1 cm; befintlig propkod klipper till bordskanten. Kamerakompensationen försvinner medan möblerna ligger i mallramen. Det belägger orsaken till propskillnaderna; att lösa den kräver ett placeringsbeslut. Redan före var hamburgarna för stora. Golvlogik, toleranser och design ändrades inte.

## Filer och körning

`efter/`, `fore/`: .blend, planer, renderingar och loggar. `jamforelser/`: 21 sida-vid-sida, RGB 50/50, hudöverlägg och före/efter. `montage/`: alla rutor visuellt granskade samt sju vidare vyer. [Metod och fullständigt underlag](UNDERLAG.md).

Ingen produktionskod ändrad. Tidiga fel i provskriptets mask-/kamerapass rättades och resultaten ersattes; slutliga vanliga vyer renderades separat ur återöppnad scen. **Seriellt från kontrakt/: {testtext} — 83 prov, 0 fel.**

Inte kört: helfilm/ljud, full diagnostikkompilering, hela 198-provsuiten, övrig ingest, Modal eller GPU-tjänst. Ingen oberoende golv-/möbelinmätning. Löpande logg: `kontrakt/GOLV2-BLENDER-LOGG.md`.
'''
write('RAPPORT.md',report)
log('KLART: rapport, samtliga 21 bildjämförelser, per-rutemått, alla numeriska försämringar, kontakter och seriella 83 gröna prov finns i blender/gen/golv2/. Dom: ursprungsprojektionen för kroppar bevarad; hela scenen underkänd genom sämre ytfästa props, S4-svävning och brister i S7. 921 ursprungsfiler oförändrade. Ingen produktionskod/design/tolerans ändrad.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck")
print('RAPPORT KLAR',len(report),'tecken')
