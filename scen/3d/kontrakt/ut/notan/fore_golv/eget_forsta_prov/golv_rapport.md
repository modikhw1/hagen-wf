# Golv, skala och synlighet

Alla värden nedan är lokala beräkningar från befintlig ingest. Inget ingeststeg, nätjobb eller GUI-anrop har körts. Säkerhetskopior: fore_golv/scen/... . Tidigare filmer och blad är orörda.

## Golvbeslut

Ett golv z=0 används i platsen. Varje tagning har egen kamerahöjd och egen translation till detta plan; samma golvförskjutning för alla kameror skulle återinföra höjdantagandet. Poolen beskriver robust konsensus bland de tidigare registrerade golvoffsetarna, inte en ny global längdskala. Golvhöjder från olika kameraorigo kan inte jämföras direkt utan transformen.

Priorer: vanligt bord 72–76 cm, sits 43–48 cm, MHR root över sits 2–15 cm (riggled, inte mätt sittyta); kamerahöjd 1,45 m med reservintervall 1,20–1,70 m. Sittande knä får sjunka 0–12 cm i golvcue, fotled/sula antas 8 cm med posemarginal 3 cm. Dessa är priorer. Modellgolv har antaget felintervall 5 cm RANSAC plus lutning över 0,5 m; ingest sparade inte ett residualstandardfel. Diagnostisk cue-tolerans 10 cm.

| Tagning | Cue | Värde ± spridning i tidigare platsram, cm | Använd | Beslut |
|---|---|---|---|---|
| S1 | djupgolv | 33.16 ± 11.76 | True | använd |
| S1 | kamerahöjd 1,45 m | 0.00 ± 25.00 | False | kameraprior endast sista utväg |
| S1 | sittande ben A | 17.31 ± 9.00 | True | använd |
| S1 | sitshöjd A | 12.93 ± 9.00 | True | använd |
| S1 | stilla handled/bord A | 17.73 ± 5.00 | True | använd |
| S2 | kamerahöjd 1,45 m | 0.00 ± 25.00 | False | kameraprior endast sista utväg |
| S2 | sittande ben B | 20.18 ± 9.00 | True | använd |
| S2 | sitshöjd B | 16.96 ± 9.00 | True | använd |
| S2 | stilla handled/bord B | 31.57 ± 5.00 | True | använd |
| S3 | djupgolv | 15.23 ± 9.22 | True | använd |
| S3 | kamerahöjd 1,45 m | 0.00 ± 25.00 | False | kameraprior endast sista utväg |
| S3 | sittande ben A | 16.86 ± 9.00 | True | använd |
| S3 | sitshöjd A | 11.31 ± 9.00 | True | använd |
| S3 | stilla handled/bord A | 17.73 ± 5.00 | True | använd |
| S4 | djupgolv | 27.59 ± 9.18 | False | avvisad: avvikare mot robust familjemedian |
| S4 | kamerahöjd 1,45 m | 0.00 ± 25.00 | False | kameraprior endast sista utväg |
| S4 | stående räckvidd C | -0.84 ± 12.00 | True | använd |
| S4 | synliga fötter 4 | -2.48 ± 3.00 | True | använd |
| S5 | kamerahöjd 1,45 m | 0.00 ± 25.00 | False | kameraprior endast sista utväg |
| S5 | sittande ben B | 20.12 ± 9.00 | True | använd |
| S5 | sitshöjd B | 16.81 ± 9.00 | True | använd |
| S5 | stilla handled/bord B | 31.57 ± 5.00 | True | använd |
| S6 | djupgolv | 38.27 ± 6.39 | False | avvisad: avvikare mot robust familjemedian |
| S6 | kamerahöjd 1,45 m | 0.00 ± 25.00 | False | kameraprior endast sista utväg |
| S6 | sittande ben A | 16.51 ± 9.00 | True | använd |
| S6 | sitshöjd A | 10.61 ± 9.00 | True | använd |
| S6 | stilla handled/bord A | 17.73 ± 5.00 | True | använd |
| S7 | kamerahöjd 1,45 m | 0.00 ± 25.00 | False | kameraprior endast sista utväg |
| S7 | sittande ben B | 23.36 ± 9.00 | True | använd |
| S7 | sitshöjd B | 23.04 ± 9.00 | True | använd |
| S7 | stilla handled/bord B | 31.57 ± 5.00 | True | använd |

| Tagning | Golv i tagningens värld, m | Flytt från tidigare, cm | Spridning ± cm / cuespann cm | Status |
|---|---|---|---|---|
| S1 | -1.2748 | +17.52 | 27.40 / 20.23 | antagen; konflikt |
| S2 | -1.2482 | +20.18 | 16.39 / 14.61 | antagen; konflikt |
| S3 | -1.2895 | +16.05 | 13.74 / 6.42 | antagen; inom tolerans |
| S4 | -1.6020 | -1.66 | 12.82 / 30.07 | antagen; konflikt |
| S5 | -1.2488 | +20.12 | 16.45 / 14.76 | antagen; konflikt |
| S6 | -1.2849 | +16.51 | 14.90 / 27.66 | antagen; konflikt |
| S7 | -1.2164 | +23.36 | 13.21 / 8.53 | antagen; inom tolerans |

Pool: 20.98 cm, spridning ±33.82 cm, cuespann 40.76 cm, antagen. Modellskattningar och/eller kroppsställning och möbelpriorer; direkta oberoende mätningar saknas. Konflikten flaggas, inte dold i ett medelvärde.

S1/S3/S6 har djupgolv +33,16/+15,23/+38,27 cm. S4 har djupgolv +27,59 cm men kontrollerad fot från bakgrundspersonen nära −2,53 cm. Foten skyddas mot restaurangpriorer i den lokala konsensusen; djupgolvet avvisas. S2/S5/S7 saknar djupgolv. Kamera-priorn används inte i notans beslut.

S7: 0 av 46 rutor har fotstöd i mask + personens egen bbox + knä/vrist/tå/häl. I ruta 0 slutar bbox vid y=497 medan skattade vrister ligger vid y=688–690 och tå/häl vid y=696–724. Synliga mörka byxben/skor i källan bevisar inte att modellens vida fotställning är uppmätt. Ingests synlighet testar index 13–14 (vrister), men kommentaren kallar dem knän. Varken dessa punkter eller de bildmässigt synliga skorna kan ge ett tillförlitligt metriskt fotläge ur sparad data. Inga nya fotmått har hittats på.

S4: 55 mask/bbox-kontrollerade fotrutor hör till bakgrundsperson 4, inte servitören C. Personen renderas fortfarande inte eftersom den saknar roll/stödankare. Synliga tillförlitliga ben lämnas oförändrade av stödsolvern.

## Skala och möbler

Skala 1,0 behålls i alla transformerna. Kroppsmodellen ger meter; inga ben skalas. Djupskalan är 1,0 men saknar parallaxverifiering. Möbelpriorerna kan pröva förenlighet, inte legitimera en ny kroppsskala.

A: stilla handled minus root 26.42 cm; prioravstånd 9–31 cm ger skalförenlighet 0.341–1.173. Skala 1,0 inom: True.

B: stilla handled minus root 34.61 cm; prioravstånd 9–31 cm ger skalförenlighet 0.260–0.896. Skala 1,0 inom: False.

B:s handledskontakt, kroppens meter och vanliga bord/sitsar är alltså inte helt förenliga genom enbart golvtranslation. Golvet höjs, men möbelpriorerna märks som antagna och handledsresten behålls synlig. Den tidigare rapportens slutsats att fasta ben i sig måste ge hängande fötter var för stark: ett dolt knä kan sjunka med samma benlängder.

| Möbel/person | Höjd före → efter, cm | Kontaktrest |
|---|---|---|
| sate/A | 54.48 → 43.00 | root över sits 5.76 cm |
| bord/A | 91.73 → 75.22 | handled +0.00 cm |
| sate/B | 60.29 → 43.00 | root över sits 8.11 cm |
| bord/B | 105.00 → 76.00 | handled +9.39 cm |

| Scen/person | Vänster sula min–max cm | Höger sula min–max cm | Handled/skiva min / median / p90 cm |
|---|---|---|---|
| s1/A | 0.022–0.061 | 0.010–0.010 | 22.33/26.41/28.21 |
| s2/B | 0.058–0.084 | 0.010–0.010 | 8.60/13.75/15.67 |
| s3/A | 0.010–0.010 | 0.025–0.042 | 5.60/9.27/12.42 |
| s4/C | 0.010–0.010 | 0.014–0.055 | ej bordkontakt |
| s5/B | 0.037–0.046 | 0.010–0.010 | 9.54/12.46/14.95 |
| s6/A | 0.010–0.043 | 0.010–0.016 | -0.58/4.07/7.53 |
| s7/B | 0.010–0.024 | 0.010–0.076 | 8.08/16.90/48.50 |

Alla 383 rutor: största benlängdsfel 6.53e-10 m, största ändring i skyddade leder 0.

## Bildutsnitt

| Scen/person | Före median/p90 px | Efter median/p90 px |
|---|---|---|
| s1/A | 1.40/4.11 | 1.40/4.11 |
| s2/B | 2.09/13.98 | 2.09/13.98 |
| s3/A | 1.69/19.12 | 1.69/19.12 |
| s4/C | 0.87/4.18 | 0.87/4.18 |
| s5/B | 2.92/9.92 | 2.92/9.92 |
| s6/A | 19.89/68.40 | 19.89/68.40 |
| s7/B | 2.00/4.88 | 2.00/4.88 |

## Skymning

Var sjätte ruta och sista rutan; unionmask inom egen bbox, var tredje maskpixel. Djup från närmaste sparad MHR70-punkt. Mätkamera före regi. Provandel, inte exakt hudarea.

| Scen | Del | Före → efter synliga prov skymda |
|---|---|---|
| s1 | bord_A | 0.306 → 0.306 % (131/42761) |
| s1 | bord_B | 0.000 → 0.000 % (0/42761) |
| s1 | stol_A | 0.000 → 0.000 % (0/42761) |
| s1 | stol_B | 0.000 → 0.000 % (0/42761) |
| s2 | bord_A | 0.000 → 0.000 % (0/31226) |
| s2 | bord_B | 0.000 → 0.000 % (0/31226) |
| s2 | stol_A | 0.000 → 0.000 % (0/31226) |
| s2 | stol_B | 0.000 → 0.000 % (0/31226) |
| s3 | bord_A | 0.000 → 0.000 % (0/30844) |
| s3 | bord_B | 0.000 → 0.000 % (0/30844) |
| s3 | stol_A | 0.000 → 0.000 % (0/30844) |
| s3 | stol_B | 0.000 → 0.000 % (0/30844) |
| s4 | bord_A | 9.190 → 0.000 % (6036/65681) |
| s4 | bord_B | 0.000 → 0.000 % (0/65681) |
| s4 | stol_A | 0.000 → 0.000 % (0/65681) |
| s4 | stol_B | 0.000 → 0.000 % (0/65681) |
| s5 | bord_A | 0.000 → 0.000 % (0/19896) |
| s5 | bord_B | 0.000 → 0.000 % (0/19896) |
| s5 | stol_A | 0.000 → 0.000 % (0/19896) |
| s5 | stol_B | 0.000 → 0.000 % (0/19896) |
| s6 | bord_A | 0.000 → 0.000 % (0/30999) |
| s6 | bord_B | 0.000 → 0.000 % (0/30999) |
| s6 | stol_A | 0.000 → 0.000 % (0/30999) |
| s6 | stol_B | 0.000 → 0.000 % (0/30999) |
| s7 | bord_A | 0.000 → 0.000 % (0/5970) |
| s7 | bord_B | 0.000 → 0.000 % (0/5970) |
| s7 | stol_A | 0.000 → 0.000 % (0/5970) |
| s7 | stol_B | 0.000 → 0.000 % (0/5970) |

s4/bord_A: utelämnad endast i denna scen. Minst 2 % av synliga maskprov skyms. Höjd/ankare skyddas av kroppsevidens; inget uppmätt ändringsintervall för fotavtrycket. Lokal utelämning bevarar alla ankare.

Omvänd kontroll: maskfrånvaro kan vara segmenteringsfel. Bara rapport, ingen ny möbel:
- s1: 2/39 möjliga dolda punkter utan framförliggande mall.
- s2: 2/18 möjliga dolda punkter utan framförliggande mall.
- s3: 33/43 möjliga dolda punkter utan framförliggande mall.
- s4: 0/0 möjliga dolda punkter utan framförliggande mall.
- s5: 2/12 möjliga dolda punkter utan framförliggande mall.
- s6: 14/54 möjliga dolda punkter utan framförliggande mall.
- s7: 10/108 möjliga dolda punkter utan framförliggande mall.

## Bar, en tagning

Bardisk ger inga priorer för vanliga restaurangbord/sitsar. Standardplanen är oförändrad. Cuekontrollen körs även utan platsreferens.
- kamerahöjd 1,45 m: -1.4484 ± 0.250 m, används False.
- sittande ben 1: -1.1916 ± 0.090 m, används True.
- sitshöjd 1: -1.2542 ± 0.090 m, används True.
- synliga fötter 2: -1.4755 ± 0.030 m, används False.
- sittande ben 2: -1.1915 ± 0.090 m, används True.
- sitshöjd 2: -1.2424 ± 0.090 m, används True.
- stilla handled/bord 1: -1.3093 ± 0.050 m, används True.
- stilla handled/bord 2: -1.1870 ± 0.050 m, används True.

Beslut -1.2482 ± 0.147 m, antagen; cuespann 28.85 cm. Tidigare golv −1,4484 m; skillnad cirka −1,4 cm ger inget tydligt stöd för att ändra det. Endast en fotruta är verifierbar. Skala 1,0 saknar motsägande metrisk evidens men är inte oberoende verifierad. --tillampa-golv är ett uttryckligt alternativ i plats.py, inte aktiverat för bar.

## Filer och verifiering

CLI-positioner bevaras. plats.py får valfritt --tillampa-golv för ensam tagning. Inga JSON-scheman ändras. plats/1 får golv.matning; plan/1 kvalitet får golv_skala, skymning och ledersattningar. Notans källa/regi uppdateras till revision 4 för den nya hashlåsta platsfilen. Bar ändrar endast diagnostikfält.

| Fil | + / − rader |
|---|---|
| scen/3d/ingest/plats.py | +25 / −1 |
| scen/3d/kontrakt/kompilera.py | +2 / −0 |
| scen/3d/kontrakt/test_flode.py | +8 / −3 |
| scen/3d/kontrakt/test_rumsmall.py | +44 / −3 |
| scen/3d/kontrakt/trohet.py | +2 / −0 |
| scen/3d/kontrakt/tropassning.py | +7 / −2 |
| scen/3d/kontrakt/trostod.py | +10 / −6 |
| scen/3d/ingest/ut/notan-tagningar/plats/plats.json | +6073 / −137 |
| scen/3d/ingest/ut/notan-tagningar/plats/plats.md | +5 / −5 |
| scen/3d/ingest/ut/notan-tagningar/plats/plats_matt.json | +5965 / −29 |
| scen/3d/kontrakt/exempel/notan/kalla.json | +40 / −40 |
| scen/3d/kontrakt/exempel/notan/regi.json | +136 / −136 |
| scen/3d/kontrakt/exempel/notan/regi_byt_lokal.json | +1 / −1 |
| scen/3d/kontrakt/golvmatning.py | +163 / −0 |
| scen/3d/kontrakt/skymning.py | +114 / −0 |
| scen/3d/kontrakt/kvalitet.py | +65 / −0 |
| scen/3d/kontrakt/golv_exempel.py | +24 / −0 |
| scen/3d/kontrakt/verifiera_golv.py | +41 / −0 |
| scen/3d/kontrakt/golv_jamfor.py | +33 / −0 |
| scen/3d/kontrakt/golv_sammanfatta.py | +96 / −0 |

Fasernas väggtider: tider_golv.json. Film/mappar: golv_tom/, golv_redigerad/, golv_jamforelse/. kvalitet.md ligger bredvid varje plan; alla cuevärden finns även i plats.json och plan.json.
