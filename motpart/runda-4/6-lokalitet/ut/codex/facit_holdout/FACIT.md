# Blint facit: hold-out för 0.0
16 tagningar: blackstone 6, fratelli 5, chickenstreet 5. Ingen kod ändrad.
Alla 16 original, 64 QA-bilder (0°, 35°, 35f, 50h) och 10 befintliga fyllnad/v2-bilder granskades individuellt.
Viktigast skrevs i blindanteckningar.json före väljarens val; bilddomarna låstes i blind_bedomning.json före L8 och fyllnadsgrinden.
Bedömningen gäller mittrutan, inte animation eller kamerarörelse över hela tagningen.
Ok kamera betyder visuellt passande utsnitt/linjer; ok skala betyder rimlig relativ storlek, inte verifierade meter.
Brist kan betyda otillräckligt bildstöd. Ingen synlig person ger kropp=ok med uttryckligt ej tillämpligt skäl.
Mörka osedda baksidor räknas inte som fel. Hål/skärvor bedöms i ytor som originalet faktiskt visade.
God_nog: ja = användbar för omregi; delvis = användbara grova delar med kvarstående fel; nej = centrala delar/kontakter saknas eller underlaget räcker inte.

## 1. L8 korsat med god_nog
| L8-dom | ja | delvis | nej | totalt |
|---|---:|---:|---:|---:|
| hög | 0 | 0 | 3 | 3 |
| medel | 0 | 1 | 4 | 5 |
| låg | 0 | 1 | 0 | 1 |
| konflikt | 0 | 0 | 2 | 2 |
| okänd | 0 | 0 | 5 | 5 |
| Totalt | 0 | 2 | 14 | 16 |

Detta är ett litet hold-out, inte en uppskattning av felandelar för de kommande 200–500 klippen.
Blackstone s2 är otillräckligt underlag: oskarpt/skymt original. Dess nej bevisar inte ett specifikt rekonstruktionsfel.

## 2. Vanligaste kategoribristerna
Rangordning med allvarlighetsvikt 2 för fel och 1 för brist; lika poäng skulle rangordnas efter antal fel.
| Rang | Kategori | fel | brist | ok | poäng |
|---|---|---:|---:|---:|---:|
| 1 | Objekt | 15 | 1 | 0 | 31 |
| 2 | Rum | 13 | 3 | 0 | 29 |
| 3 | Golv/kontakt | 4 | 12 | 0 | 20 |
| 4 | Kropp | 6 | 5 | 5 | 17 |
| 5 | Skala | 0 | 6 | 10 | 6 |
| 6 | Kamera | 0 | 1 | 15 | 1 |

Kroppens fem ok gäller tagningar utan identifierbar person; samtliga 11 tillämpliga tagningar har brist/fel.
Golvets 12 brister är främst overifierbara stöd/kontakter, inte 12 konstaterade svävningar.
Skalans sex brister gäller svagt/obefintligt måttstöd; ingen säker relativ storleksmiss konstaterades i de tio tydliga personscenerna.
Objekt och rum är de tydligaste förbättringsprioriteringarna: en välmatchad frontal projektion döljer sönderfall vid vridning.

## 3. Över- och underskattning
- Hög men nej: chickenstreet s3 har splittrat golv/bord/stolar och fel sitt-/fotdjup.
- Hög men nej: chickenstreet s4 har trasiga stödytor, fel kvittohand och bristande sitt-/fotkontakt.
- Hög men nej: chickenstreet s5 har en extra liten blå kroppsfigur/fragment, saknat greppat papper och trasig bänk/bord/golv.
- L8:s 99/95/97 procent observerad bildtäckning i dessa tre betyder inte sammanhängande, regisserbar geometri.
- Omvänt finns ingen låg/konflikt med god_nog=ja. Chickenstreet s2 får låg men delvis: kamera och huvudvägg ser rimliga ut; disk/kontakt/gest har kvarstående fel. Flyktpunktsavvikelsen 26,9° syns inte som motsvarande utsnittsfel i mittrutan.
- Fratelli s3 är medel och delvis. Övriga medel är nej; konflikt i fratelli s1/chickenstreet s1 stämmer med synliga hand-/objektproblem.
- V2 separat: 9 ja, 1 delvis, 0 nej; blackstones 6 saknar fil och har null, inte nej.
- Fyllnadsgrinden: fratelli s3 har låg tillit men v2=ja. Fratelli s5 har hög men delvis: bilden uppfinner en pelarfot under den handhållna brickan. Övriga 8 har hög och ja. Detta gäller visuell 2D-användbarhet, inte bevisad dold geometri.
- Väljaren: 1 ja, 10 delvis, 5 nej. Fratelli s1 täcker person+bricka+café. Negativa är blackstone s2/s3, fratelli s5 och chickenstreet s1/s4; s2:s nej beror på obestämbart original.
- Vanligt väljarglapp är bortvalda samtalspartner, små handlingsbärande föremål och möbler som får rollen i_handen genom 2D-närhet.

## 4. Fem återkommande fel och rimliga orsakssteg
Orsakerna nedan är hypoteser från bilderna och metadata, inte verifiering av intern kod.
1. **Föremål saknar form, stöd och handgrepp** (objekt: 15 fel): mat/brickor/rekvisita blir bildflikar eller saknas. Rimliga steg: OneFormer-instansgränser, objektens MoGe-djup och registrering mellan hand, objekt och stödyta; 2D-närhet räcker inte som grepp.
2. **Synliga plana ytor blir skärvor och dragna remsor** (rum: 13 fel): väggar, bord och hyllor tappar sammanhang. Rimliga steg: MoGe-djup vid kanter/skymningar, segmentgränser och triangulering/plananpassning.
3. **Sitt- och fotkontakt saknar gemensam stödyta** (4 fel, 12 brister): kroppen placeras utan verifierad hel sits eller golvyta. Rimliga steg: golvplan, kroppsskalning mot persondjup och registrering till möblernas djup; bildpassning ensam styrker inte fysisk kontakt.
4. **Personrekonstruktionen är ofullständig eller felregistrerad** (kropp: 6 fel, 5 brister av 11 tillämpliga): personer stannar i fotot, dubbleras som fragment eller får fel händer/ben. Rimliga steg: personinstanser/identitet, SAM 3D Body-pose och dess överföring till rummets koordinater.
5. **Personkonturer och hål överlever trots användbar 2D-fyllnad**: nio v2 får ja, medan varje motsvarande rum ändå har brist/fel. Rimliga steg: OneFormer-personmask, urtag av originalpersonen och integration/registrering av fyllnadsdjupet i originalnätet; fyllnadsbildens realism är ett annat prov än slutnätets täthet.

KLAR
