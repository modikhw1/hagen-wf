# GOLV2 i Blender

**Dom: nej, hela notanscenen återges inte tillräckligt troget; nej, scenen håller inte fullt från flyttad kamera. Kropparnas ursprungsprojektion är däremot bevarad.** Den viktigaste nya bildförsämringen gäller ytfäst rekvisita: hamburgarens centrumfel ökar i S3 cirka **35 → 103 px**, S2 **124 → 153 px**, S7 **17 → 45 px**. Burken i S3 går **50 → 70 px**. Se [S3 före/efter och källa](montage/s3_alla.png). Detta är inte ett nytt kroppsfel.

## Del 1: riktiga ingestdata på kopior

Bara `steg_golv` och `steg_kontakt` kördes på notan S1–S7 och bar, under `scen/3d/kontrakt/ut/golv2_ingestprov/data/`. **8 världsfiler och 10 sekvenser fick golv_version=2; inga körfel.** Kontaktsteget lämnar båda arrayerna exakt orörda.

Mot **metrisk.las(indata)** är samtliga cam_t och pose exakt lika, tal för tal (maxskillnad 0). Mot **råindata på disk är de inte oförändrade**: golvstegets avsiktliga migration återställer historiskt golv/kontakt. Största absoluta komponentändring:

| Klipp/tagning/person | cam_t, cm | pose, rå arrayenhet |
|---|---:|---:|
| notan/S1/1 | 22.906 | 0.000000 |
| notan/S2/1 | 35.040 | 0.000000 |
| notan/S3/1 | 19.900 | 0.000000 |
| notan/S4/1 | 18.908 | 0.000000 |
| notan/S4/4 | 5.027 | 3.548321 |
| notan/S5/1 | 11.005 | 0.000000 |
| notan/S6/1 | 18.910 | 0.000000 |
| notan/S7/1 | 72.059 | 0.000000 |
| bar/bar/1 | 1.351 | 0.000000 |
| bar/bar/2 | 5.863 | 58.129295 |

Poseändringarna i S4/4 och bar/2 är återställning av `pose_fore_kontakt`; övriga poser är orörda. Posearrayen blandar cm, quaternion och skala; redovisad maxkomponent ligger i translationsdelen. Alla återställda värden är exakt den befintliga metriska läsarens värden, inte nya skattningar.

Kompilering från kopian ger **exakt samma scen** som dagens original genom metrisk: kamera, kropp, stöd, rum, props, tidskarta och övriga planfält är identiska utan numerisk tolerans. Hela filen är inte identisk: notan har 23 ändrade filhashar och en ändrad byggunderlagsförteckning; bar 5 hashändringar och en förteckning. Extra `golv_prov.json` i kopian förklarar listlängden. Bara sökvägar och denna filproveniens undantogs i den exakta scenjämförelsen. [Diffar](notan_plandiff.json), [bar](bar_plandiff.json), [exakt kontroll](exakt_scenjamforelse.json).

**921 ursprungsfiler SHA256-kontrollerade: 0 ändrade.** Banker skrevs inte. [Ingestmått](ingest_matning.json), [originalkontroll](original_kontroll.json).

## Del 2: faktiskt Blenderresultat

Ordinarie väg: tom regi → `kompilera.py` → `ingest/mhr_rig.py:bygg` → FBX lod3/Workbench i **Blender 5.2.3**. Den planvägen använder mhr_rig:s metriska läsare. Även just `blender/mhr_blender.py:importera` prövades separat på S1, med tre nycklade världsposer: exakt samma cam_t/pose som metrisk (inte rå cam_t).

**21 rutor, 288×512:** 2/36/70, 75/93/111, 116/142/168, 173/213/253, 258/268/278, 283/309/334, 339/360/380. Varje ruta renderades från original och från +0,5 m kamerahöger/+0,3 m världsupp, med oförändrad lins och samma målpunkt på originalets optiska axel vid torsons djup. Mitt även med halverad lins för golvöversikt; de vidare bilderna är separat diagnostik.

Förejämförelsen är **ny Blender-rendering med arkiverad före-GOLV2-kod**, omkompilerad mot exakt samma dagens källmanifest, tomma regi och FBX som efter. Alla berörda gamla sekvens-/världsdata är byteidentiska med dagens original. Kodursprung: `fore/kodursprung.json`. Inga produktionsfiler ersattes.

Blenderleder mot numpy: max **0.002211 px / 2.44 µm**. Synliga leder före/efter flyttar högst **0.001427 px**. Inga synliga ändringar av överkroppens storlek eller hållning hittades. S6 har kvar tydlig handavvikelse, och S3:s slutruta har p90 68 px. Måttet domineras av fingrar och är mot estimatorns egna punkter.

| Tagning | Hud-IoU median före → efter | Synlig IoU efter | Ledmedian, spann px | Största rut-p90 px | Bilder |
|---|---:|---:|---:|---:|---|
| s1 | 0.637 → 0.636 | 0.666 | 2.0–4.0 | 6.2 | [alla tre](montage/s1_alla.png), [vid](montage/s1_vid.png) |
| s2 | 0.637 → 0.637 | 0.669 | 4.9–9.5 | 25.0 | [alla tre](montage/s2_alla.png), [vid](montage/s2_vid.png) |
| s3 | 0.668 → 0.668 | 0.709 | 1.8–4.6 | 68.0 | [alla tre](montage/s3_alla.png), [vid](montage/s3_vid.png) |
| s4 | 0.709 → 0.723 | 0.723 | 0.3–1.6 | 2.0 | [alla tre](montage/s4_alla.png), [vid](montage/s4_vid.png) |
| s5 | 0.660 → 0.660 | 0.685 | 1.1–4.1 | 8.7 | [alla tre](montage/s5_alla.png), [vid](montage/s5_vid.png) |
| s6 | 0.663 → 0.663 | 0.711 | 14.2–19.5 | 41.0 | [alla tre](montage/s6_alla.png), [vid](montage/s6_vid.png) |
| s7 | 0.551 → 0.551 | 0.558 | 1.3–2.6 | 3.8 | [alla tre](montage/s7_alla.png), [vid](montage/s7_vid.png) |

IoU är verkligt Blenderhudpass mot YOLO, inom personens egen ruta. Hår, kläder och skymmande bord skiljer mask från hud. De små nedgångarna är högst **0.000224** i en enskild ruta; orörda leder och likadana överkroppsbilder talar för raster-/flyttalsrest. S4:s högre IoU följer ändrad dold benpose. [Alla 21 mätningar och överlägg](RUTOR.md), [alla numeriska försämringar](FORSAMRINGAR.md).

**Sett från flyttad kamera:** A/B sitter överlag rimligt vid stolarna i S1–S6; möbelhöjderna är 43 cm sits och 76 cm bord. Sulorna ligger cirka 0,1 mm över golvet efter stöd. Rotleden ligger 9,6–11,9 cm över sitsen, inte en oberoende mätning av hudkontakt. S5:s bäcken är 17–19 cm från sitscentrum och nära kanten. **S7 har ingen synlig sits** före eller efter; händerna hamnar i mittprovet 30/42 cm utanför bordsskivans XY-gräns efter, mot 0/8 cm före. Så bordskontakten håller sämre. Handledshöjder och gester redovisas separat i `mobelkontakter.json`.

**S4/C bekräftat:** sulan är **10,38 / 11,24 / 11,90 cm** över golvet, före cirka 0. I oförändrat utsnitt syns inte fötterna; i [vidare Blenderbild](montage/s4_vid.png) är glappet och frånvaron av fotkontakt synligt. Ingen rättning gjord. Golvet kommer från person 4:s synliga fötter; den personen utelämnas av planen. Det är därför ingen verklig samtidig flerpersonsrendering som styrker inbördes storlek. Kropparnas storlek mot de generiska stolarna ser rimlig ut, men rummet är fortfarande en mall.

**Orsak till rekvisitaförsämringen, belagt i planen:** bildstrålen missar bordsskivan mer efter GOLV2: S2 34,4→41,0 cm, S3 6,5→14,7 cm, S7 35,6→70,1 cm. `propplan.py` klipper då till bordskanten. Kamerakompensationen har tagits bort medan möblerna ligger i mallramen. Det förklarar de uppmätta propskillnaderna. De redan för stora hamburgarna finns även före; breddkvoten ökar exempelvis S3 2,11→2,29 och S7 1,95→2,21. Att lösa detta kräver beslut om möbel-/ytpassning; golvlogik, toleranser och design lämnades orörda.

## Filer och avgränsning

`efter/` och `fore/`: planer, sparade .blend, originalbilder, flyttade vyer, hudpass och Blenderloggar. `jamforelser/`: sida vid sida, RGB 50/50, hudöverlägg och före/efter för varje ruta. `montage/`: samtliga 21 rutor visuellt granskade, samt sju vidare före/efter. Masker och vanliga vyer körs i separata pass för att undvika Blenders återutvärdering av animerad synlighet; tidiga felaktiga provbilder/mått ersattes. Slutliga vyer renderades ur återöppnad ordinarie scen.

Ingen produktionskod ändrad; bara provverktyg och artefakter tillagda. Ändrad befintlig provkod säkerhetskopierades under `ut/fore_golv2_blender/`. Seriellt från kontrakt/: **test_flode: 46 gröna; test_rumsmall: 19 gröna; test_kroppmatt: 18 gröna** (83 prov, 0 fel). Testloggar finns här. Blender gav en varning om misslyckad miniatyrbild, men byggnad, PNG och .blend lyckades.

**Inte kört:** helfilm, ljud/muxning, ny inferens/övrig ingest, Modal, GPU-tjänst, full diagnostikkompilering eller hela 198-provsuiten. Ingen oberoende verklig golv-/möbelinmätning eller mänsklig 2D-annotation finns i detta prov. Körhistorik och nästa kommando: `kontrakt/GOLV2-BLENDER-LOGG.md`.
