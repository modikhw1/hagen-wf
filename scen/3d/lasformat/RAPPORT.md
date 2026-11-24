# Läsbarhetsöversättning för 3D-läsning — S4

## Dom

**Ja för kroppsläsning i format A; nej för rummet och nej för B/C som helhet.** Wan VACE höll servitörens rörelse: medianavvikelsen mot originalets SAM-läsning är cirka 3 pixlar och rotbanans form avviker högst 1,40 pixel vid p95. Format A gör de dolda benen läsbara i alla 85 rutor och ger stabila golvkontakter utan mätbar fotglidning. Det tar bort den osäkra dold-fot-skalning som gjorde servitören cirka 1,90 m och ger i stället 1,734 m i den råa kroppsläsningen.

A har samtidigt något mer bålskak, genererade skor som inte är bildfacit och klart sämre MoGe-stabilitet än originalet. Det är därför ett användbart **hjälpformat för kropp/ben/kontakt**, inte en ersättare för originalbilden eller ett bättre rumsformat. B och C visar också benen, men placerar sulorna 11–13 cm över valt golv och är inte säkrare.

## Resultat per format

Servitören är den centrala stående personen, **ingest-ID 1**. Uppdragsbeskrivningen kallar honom ID 4, men `personer.json` och bildpositionerna visar att ID 4 är den vänstra sittande personen.

| Format | Drift mot original | Bålskak p95 | Fotglidning | Golv / kontakt | MoGe-djupets tidsvariation | Servitörens råa MHR-längd | VACE-kostnad |
|---|---:|---:|---:|---|---:|---:|---:|
| Original | facit | 0,235 cm | ej mätbar, fötterna dolda | flyter 14,7–16,3 cm över golv | 2,4 % | 1,758 m; senare dold-fot-regel: 1,898 m | – |
| A realistiskt | 3,01 px; rot p95 1,40 px | 0,355 cm | p90 0,25 cm/ruta; 0 glidrutor | båda fötterna i kontakt i 84 rutor; 1,9–2,8 cm över plan | 23,1 %; djup-/kroppsgolv skiljer 42,9 cm | 1,734 m | 0,261 USD |
| B förenklat | 3,18 px; rot p95 1,16 px | 0,265 cm | ej giltigt utan kontakt | fötterna flyter 10,8–11,6 cm; golvkonflikt 17,4 cm | 4,4 % | 1,735 m | 0,261 USD |
| C rutgolv | 2,92 px; rot p95 1,05 px | 0,791 cm | ej giltigt utan kontakt | fötterna flyter 11,9–13,1 cm; golvkonflikt 19,9 cm | 16,4 % | 1,730 m | 0,261 USD |

Driftkolumnen visar median för överkroppsleder efter att 480 × 832-duken mappats tillbaka till originalets 576 × 1024-koordinater; den breddade ytan räknas bort. Alla format jämförs över 85 rutor. 3D-rotbanans förskjutning avviker 4,8–5,6 mm i median. Den direkta armledsdriften är 2,2–2,8 px; armhastighetskorrelationen är låg eftersom små skillnader mellan två SAM-körningars skak dominerar derivatan.

Kedjans binära kroppstillförlitlighet är 85/85 rutor både före och efter, så den skiljer inte fallen åt. Det användbara säkerhetsmåttet är bensynlighet: **0/85 i originalet, 85/85 i A, B och C**. A är den enda varianten där denna nya information också ger sammanhängande fotkontakt. MoGe-talet är medianens tidsvariation i 15 djupkartor efter normalisering och bortmaskning av personer; lägre är stabilare.

## Metod och körning

- Källa: `notan-tagningar/klipp/S4.mp4`, 85 rutor, 30 fps, 576 × 1024.
- Rörelsefacit: befintlig SAM 3D Body-läsning, aldrig manuellt facit.
- Modell: [Wan2.1-VACE-14B](https://huggingface.co/Wan-AI/Wan2.1-VACE-14B), diffusers-revision `db79b90c…`. Modellkort och [officiellt VACE-repo](https://github.com/ali-vilab/VACE) anger **Apache-2.0**.
- VACE:s maskstyrning användes direkt: svarta områden bevaras, vita genereras. Personer, ansikten, mimik, mat och undertext skyddades med originalmasker. Bakgrund och 182 nya pixlar under källbilden genererades.
- Modellen fick 49 rutor vid 16 fps, 480 × 832. Resultatet mappades tillbaka till exakt 85 rutor vid 30 fps; originalets personpixlar från varje exakt tidpunkt lades tillbaka.
- A, B och C kördes i samma varma A100-SXM4-80GB-container. Vikterna hämtades en gång till Modal Volume `lasformat-wan21-vace`. Toppminne: 52,43 GB.

Gemensam modelladdning tog 94,0 GPU-s och kostade cirka 0,065 USD. Varje variant tog cirka 376 GPU-s och 0,261 USD. VACE totalt: **0,847 USD**. SAM 3D Body och MoGe loggade ytterligare 261 GPU-modellsekunder; eftersom befintliga funktioner inte skriver vald GPU är deras 0,181 USD konservativt beräknade med A100-pris. Samlad beräknad modellkostnad: **1,028 USD**, plus eventuell containerstart i Modals faktiska debitering — långt under stoppgränsen 12 USD. Full logg finns i [`budget.json`](budget.json).

## Bildobservationer

- **A:** mest lik den realistiska restaurangen. Kompletta ben och skor, men en synlig horisontell outpaint-skarv och för stora skor.
- **B:** lugnare ytor och tydligt golv visuellt, men mörka vertikala sidoartefakter och skadad undertext. 3D-kedjan hittar två oförenliga golvhöjder.
- **C:** realistisk, men modellen tolkar rutprompten som dekorativt cirkel-/mosaikmönster i stället för ett regelbundet kvadratnät. Det förbättrar inte golvskattningen.
- Alla varianter gav även en extra/annan persondetektion med dålig geometri. Slutsatsen ovan gäller den spårade centrala servitören.

## Bilder och videor

Varje jämförelse visar **original | genererat | genererat med kroppen projicerad**.

| Format | Video | Stillbild ruta 45 | Enbart genererat |
|---|---|---|---|
| A | [sida vid sida](ut/A/sida_vid_sida.mp4) | [bild](ut/A/sida_vid_sida_f0045.jpg) | [video](genererat/A_01/video_30fps.mp4) · [stillar](genererat/A_01/) |
| B | [sida vid sida](ut/B/sida_vid_sida.mp4) | [bild](ut/B/sida_vid_sida_f0045.jpg) | [video](genererat/B_01/video_30fps.mp4) · [stillar](genererat/B_01/) |
| C | [sida vid sida](ut/C/sida_vid_sida.mp4) | [bild](ut/C/sida_vid_sida_f0045.jpg) | [video](genererat/C_01/video_30fps.mp4) · [stillar](genererat/C_01/) |

![A, ruta 45: original, genererat och kropp projicerad](ut/A/sida_vid_sida_f0045.jpg)

![B, ruta 45: original, genererat och kropp projicerad](ut/B/sida_vid_sida_f0045.jpg)

![C, ruta 45: original, genererat och kropp projicerad](ut/C/sida_vid_sida_f0045.jpg)

## Vad som inte fungerade

- Ett regelbundet rutgolv gick inte att prompta fram: C blev ett dekorativt mosaikmönster och fick både sämre skak och instabilare rum.
- Visuellt lugnt golv räckte inte: B såg tydligt ut men två personer gav golv som skilde 17,4 cm och servitörens sulor svävade.
- Maskad outpaint fungerade tekniskt, men den hårda maskgränsen gav skarv och VACE hittade på skostorlek, sidoytor och ibland bakgrundspersoner. Undertextskyddet var inte perfekt i B.
- Ingen variant förbättrade MoGe mot originalet. A förbättrade kroppskontakten men gjorde rumsdjupet mycket mindre tidsstabilt.
- COLMAP fick 0/29 användbara bildpar eftersom den genererade kameran är låst. Kedjan gick därför på antagen stillastående kamera/fokal; det är väntat, men ingen ny kamerageometri vanns.

## Rekommendation

Gå vidare med **A som separat kroppsförbehandling**, och behåll originalet som källa för rum, ansikte, mat och bild. Nästa lilla prov bör använda en mjuk övergångszon runt den gamla nederkanten och explicit skoreferens, sedan automatiskt förkasta utfallet om (1) överkroppsdrift överstiger ungefär 5 px, (2) bensynlighet inte blir full, (3) fotkontakt saknas eller (4) extra personspår uppstår. Försök inte förbättra MoGe med samma genererade video; kombinera A:s kropp med originalets rum i stället.

## Mätt respektive resonerat

**Mätt:** led-, arm- och rotbanedrift mot originalets råa SAM-resultat; skak, fotglidning, kontakt, sulhöjd, rå MHR-längd, synliga benrutor, MoGe-stabilitet, GPU-tid och kostnad. Rådata finns i [`matning.json`](matning.json), [`drift.png`](drift.png), [`rum_matning.json`](rum_matning.json) och respektive `ut/<format>/vakt_lasformat.json`.

**Resonerat:** A:s små ledavvikelser innebär att rörelsen är bevarad tillräckligt väl för just detta test. Det visar inte att genererade fötter är anatomiskt sanna; de är en modellgissning som råkar ge en mer användbar och stabil 3D-läsning. En framtida produktionslösning bör därför behålla originalets överkroppsrörelse som hårt facit och behandla de nyskapade fötterna som osäker inferens.

## Löpande logg

1. Ingest-README och modellunderlag lästes. Originalets resultat kopierades till denna mapp och `vakt.py` kördes utan att skriva i befintlig utdata.
2. Originalets ID 1: 1,758 m rå MHR-längd, 0 synliga benrutor, bålskak p95 0,235 cm. Den befintliga dold-fot-regeln skalar senare identiteten till 1,898 m.
3. Maskerad outpaint-indata och exakt tidsmappning skapades.
4. Wan2.1-VACE-14B kördes en gång per format i samma varma container.
5. Befintlig ingest-kedja kördes genom personer, kamera, kropp, sekvens, värld, golv och kontakt. `vakt.py` kördes på alla format.
6. Korsjämförelse mot originalets råa SAM-leder genomfördes i originalbildens koordinater.
7. MoGe kördes på alla tre. Djupkartornas tidsstabilitet mättes mot originalet.
8. Befintliga Blender- och jämförsteg kördes; slutliga trepanelsvideor och stillbilder skapades.

## Tillägg 11 nov: format A på fyra andra tagningar (orkestratorn)

Körda parallellt med `modal_vace_klipp.py` (en container per tagning, ~1,1 USD) och mätta med `mat_klipp.py` (SAM på genererat mot originalets SAM).

| Tagning | Drift median / p90 (px) | Kommentar |
|---|---|---|
| notan S1, sittande vid bord | 3,1 / 4,0 | Breddningen visar bordets framsida; benen är skymda av bordet även i verkligheten. Liten vinst. |
| råvara S5, handhållet, bakom disk | 3,1 / 8,9 | Breddningen visar disk och hand. SAM lägger ben i den nya ytan, men de syns inte i bild (måttet "ben i bild" är missvisande här). |
| Kenny S2, glassdisk, person mest utanför bild | 9,6 / 41,8 | Huvudmotivet är en hand; ingen användbar kropp att läsa. |
| servering S2, bakom disk | 3,6 / 7,1 | Disk i nederkant; inga ben att visa. |

Slutsats: Wan håller klippet (cirka 3 px) i alla tagningar med en läsbar person. Breddningen ger bara ny information i den sorts bild där benen finns men är beskurna av ramen, som S4: en stående person på öppet golv. Bakom disk och bord finns inget att avslöja. Skakmåttet i `mat_klipp/resultat.json` är inte jämförbart, eftersom råvideon i 16 fps upprepar rutor när den mappas till 30 fps. En rättvis jämförelse kräver samma återläggning av personpixlar som `postprocess.py` gör för S4.
