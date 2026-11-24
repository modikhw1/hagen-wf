# Felsökning: MaskedMimic håller inte kroppen (0039)

Läs det här först. Det ersätter att läsa in sig på mappen. Uppdatera bladet när något nytt är känt. FORSKNING, AMASS-tränade vikter.

## Målet
Referensen (gelato S1, kvinna står bakom disk, 156 rutor) ska gå genom kontrollern och komma ut inom cirka 10 cm per led (diagnosgräns, inget krav från ägaren). Först därefter går en fri mening → villkor → ny rörelse att pröva (`mening.py`).

## Varvet (under en minut när tjänsten är varm)
Från projektroten:
```
scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/kropp.py diag
scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/kropp.py kor forvarld/kropp/forskning/mm/ut/diag_hall.json
```
- `kropp.py` skickar den lokala `kor_mm.py` med i anropet. Ändra `kor_mm.py`, kör igen. Ingen utplacering, ingen uppladdning.
- Varje villkorsfil får en egen container. Första anropet till en kall container tar 1–2 min, sedan cirka 13 s för 150 rutor (arbetaren håller simulatorn laddad).
- Utfall: `ut/raw_<namn>.npz`, `ut/logg_<namn>.txt`, och en rad med rothöjd över tid och fel mot referensen.
- Tjänsten (`tjanst.py`, appen `hagen-mm-tjanst`) placeras bara ut igen om avbildningen ändras. Kör aldrig `modal run modal_mm.py` i felsökningen: det skapar en ny app och laddar upp ProtoMotions varje gång (5–25 min).
- Starta inte fler än 6 samtidigt. 16 nov var L4 slut hos Modal (jobb låg i kö 20–30 min); tjänsten tar därför L4, A10G eller T4.

## Löst 16 nov: tre fel, i den ordning de hittades
| fel | belägg | rättning |
|---|---|---|
| **Kamerans inåkning låg i kroppen.** `varld.npz` för S1 har kameran still i alla rutor, medan rotens djup i kamerarummet går 2,70 → 1,82 m. Bäckenet färdades 72 cm med fötterna förankrade. | `diag_exempel` (projektets egen rörelse) står; vår referens faller; stillastående första ruta står. | `mening.stabilisera`: roten står kvar i sidled och djupled. Rätt plats för rättningen är kedjans kameralösning, inte här. |
| **Benen var gissade.** De skyms av disken. Redan i ruta 0 låg fotlederna 31–37 cm framför bäckenet, som på en barpall. | med roten fast står hon, men vandrar 1 m och vrider sig 45°. | `mening.stabilisera`: raka ben under bäckenet, vända som bäckenet. Sekvensen har redan `ben_synliga`; den bör styra detta. |
| **Ingen kropp var bunden.** `masked_mimic_repeat_mask_probability = 1.0` upprepar förra masken, och startens mask är tom. | fyra olika villkor gav samma siffror; `MASK aktiva 0`. | `kor_mm.py`: 0.0 som förval (`upprepa_mask` i villkorsfilen). Loggar `MASK` vid steg 0, 1, 5, 30. |

Den slumpade startfasen (rättad av Codex) var också ett fel, men inte det som fällde henne.

## Läget efter rättningarna (`ref_stabil.npz`, alla sex kroppar bundna i position)
| | före | efter |
|---|---|---|
| alla leder, medelfel | 107 cm | 13 cm |
| bäcken, median | 96 cm | 4 cm |
| höger hand vid ge (rutor 90–146) | 202 cm | 8 cm |
| höger hand vid skopa (rutor 28–66) | 122 cm | 42 cm |
| rothöjd | faller till 0,1 m | 0,90 m hela klippet |

## Löst 16 nov kväll
| fel | belägg | rättning |
|---|---|---|
| **Hon böjde sig inte vid skopandet.** Förvalet beta(2, 5) för målens tider lägger målen långt fram i klippet. | höger hand vid skopa 42 cm, huvud 45 cm; med `tid [1, 40]` 5 och 11 cm. | `kor_mm.py`: förval `tid [2, 60]` (mål nära i tiden). Svep: [1, 25] till [2, 60] ger 7,9–9,4 cm för alla leder; [1, 120] är sämre. |
| **Rycket var 6–10 gånger originalets.** | höger hand 449 mot 72 m/s³. | `tagning.jamna`: gaussfilter sigma 1 ruta på utfallet ger 93, utan att träffen ändras (8,0 cm före och efter). |

Bruset (`brus` i villkorsfilen) gör ingen skillnad: `vae_noise` är redan noll i den här vägen. Två körningar med samma indata skiljer cirka 0,5 cm.

**Läget:** alla sex bundna i position, gelato S1: alla leder 8 cm, bäcken 5,5, huvud 7,7, höger hand 5,5 vid skopa och 7,9 vid ge, fotväg 25 cm.

## Den allmänna vägen (16 nov kväll)
```
kedjans kalla_*.json + liggare_*.json  ──tagning.las──►  sekvens, värld, händelser i tagningens rutor
                                         tagning.referens  MHR → SMPL, rimlighetsgrind, bara de rättningar grinden kräver
mening + erfarenheter.json  ──förståndet──►  recept (vilka kroppar binds, hur målen avviker)
                                         tjänsten          MaskedMimic fyller i resten av kroppen (cirka 35 s)
                                         mått              per bunden kropp, per händelse i liggaren, mot originalet
                          ◄──förståndet──  bedömning och justerat recept (--varv)
                                         tagning.tillbaka  MHR-sekvens i kedjans format (rundresa 0,1 cm)
```
```
scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/mening.py "<mening>" <namn> [--kalla <k> --liggare <l> --scen s1 --person A] [--varv 2]
scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/tagning.py <kalla> <liggare> [<scen> <person>]      bara läsning och grind
```
- **Rimlighetsgrinden** (`tagning.rimlighet`, `referens`): bäckenets avstånd från fötternas mitt, rotens väg mot fötternas, bäckenhöjd, och `ben_synliga`. Benen byts mot raka när de inte syns eller ställningen inte går att stå i; roten låses när den färdas över 15 cm och benen inte går att lita på. Varje beslut skrivs ut med skäl och följer med till förståndet och till `logg.json`. Gränserna är diagnosgränser.
- **Sittande** flaggas (bäcken under 0,65 m) men stöds inte: simuleringen har ingen möbel.
- **Erfarenheter** (`erfarenheter.json`): mätta regler som går in i prompten. Det är här vägen tränas. Kontrollprov: utan erfarenheterna hittade slingan inte "andra handen" på tre varv (vänster hand 21–31 cm från målet); med dem på första försöket (9 cm).

## Körda meningar
| mening | tagning | utfall |
|---|---|---|
| ont i höger höft, skyddar benet | gelato s1 A | står, höger knä avlastat, höger hand 17 cm (före nya förval) |
| skopar och räcker fram med andra handen | gelato s1 A | 1 varv, 98 s: vänster hand 9 cm från målet (skopa 15, räcka 7). Kroppen vrider sig och tar ett brett steg. `ut/mening_andra_handen3/` |
| osäker, tvekar innan han lyfter köttbiten, håller den lägre | b-tilltal s1 A | varv 1 föll (för stora ändringar), varv 2 står: händerna 13–23 cm från målen. `ut/mening_slaktare_tvekar/` |

## Löst 16 nov sen kväll
| sak | belägg | åtgärd |
|---|---|---|
| **Varvtiden.** 25 av 33 s var simulatorns uppstart. | A, A, B, A i samma arbetare: 13,4, 12,6, 5,7 (48 rutor), 13,0 s väggtid; alla leder 7,7–7,9 cm varje gång, alltså inget läckage mellan uppdrag. | `arbetare.py` håller simulator och policy laddade i containern. `tjanst.py` (klassen `VarmKroppSlutlig`) skickar uppdrag till den och faller tillbaka på en process per anrop om arbetaren dör, inte svarar inom 120 s, eller om `kor_mm.py` som skickas med skiljer sig från den utplacerade. Byggd av Codex, som avbröts före rapporten; verifierad av mig. |
| **Förståndet svajade.** Geminis gratisnivå gav 503 och tidsgränser, och Codex som reserv tog 25–30 s per anrop. | bryggan `token-budget-beacon.lovable.app`: `gemini-3.5-flash` 2,0–2,4 s och `gemini-3-flash-preview` 1,6 s i tio av tio anrop. | `mening.py` och regibordets `forstand.py`: bryggan först (`BEACON_NYCKEL` i `video/.env.local`), sedan gratisnivån, sedan Codex. `FORSTAND_VIA`, `FORSTAND_BEACONMODELL`. |
| **Kroppen hamnade fel i förvärlden.** Grinden tar bort inåkningen ur roten, men scenens kamera står still och förväntar sig den. | första renderingen: kroppen 65 cm för långt bak och snett i bild. Efter: roten 7–9 cm från originalets plats i världen. | `tagning.referens` sparar det grinden tog bort (`aterflytt`), och `tagning.tillbaka` lägger tillbaka det. Kroppen simuleras stillastående och visas där bilden kräver. |
| **Streckfilmen tog över en minut.** | 154 rutor i matplotlib. | bladet ritas först (någon sekund), filmen varannan ruta. Regibordet visar bladet direkt och filmen när den är klar. |

**Tider nu** (gelato S1, 156 rutor): förståndet 4–5 s per anrop, kroppen 13–17 s, en hel mening med bedömning 32 s, regibordets knapp 47 s till blad.

**Lärdom:** min kontroll av vägen tillbaka mätte bara om MHR-kroppen stämde med sig själv (0,1 cm). Felet syntes först i en rendering i scenen. Mät i världen mot originalet, och titta på en bild i scenen, innan något kallas klart.

## Regibordet
`byggsten/hand`: när förståndet lägger en mening på nivån scenlagret och klippet har en kropp (`forstand.KROPP`, i dag bara gelato) visas "Kör på kroppen". Den kör `mening.py` som kommando och visar beskrivning, mått, bedömning, blad och film i loggen.

## Rendering i förvärlden
```
scen/.venv/Scripts/python.exe -X utf8 forvarld/kropp/forskning/mm/forvarld_film.py <mening-namn> [<mening-namn> ...]
```
Lokal Blender, samma väg som 0034 (`forvarld/gelato/bild.py`). Ger `ut/mening_<första>/forvarld.mp4`: original, före, och en kolumn per mening. Bara gelato S1 har en plan.

## Kvar
- **Inferensen är nu det långsamma:** cirka 65 ms per steg, 10 s för 150 rutor. Inte undersökt.
- **Receptspråket saknar tempo.** "Fortare" blev en tidsförskjutning. En ändring som spelar en del av referensen snabbare eller långsammare finns inte.
- **Vid andra handen böjer hon sig inte**, hon vrider sig och kliver. Erfarenheten om fritt huvud är inlagd men inte omprövad på just den meningen.
- **Rättningarna i grinden hör hemma i kedjan:** kameralösningen för S1 (inåkningen) och läsningen av skymda ben. Förslag till kedjan, kräver ägaren.
- **Disken och föremålen finns inte i simuleringen.** Handen går genom tråget; ingenting hindrar henne från att stå där disken står.
- **Sittande stöds inte.** Sex kroppar: inga fingrar, ingen blick, inga armbågar eller knän som villkor.
- **Bara gelato har plan för rendering och knapp i regibordet.** `mening.py` går på alla tagningar, men bilden i scenen gör det inte.
- **Ingen människa har bedömt utfallen.**

## Filer
| fil | vad |
|---|---|
| `kor_mm.py` | körs i containern: referens → `.motion` → policy → kroppar per steg. Diagnoslägen via fältet `diag` i villkorsfilen. |
| `tjanst.py`, `arbetare.py`, `kropp.py` | varm tjänst med en arbetare som håller simulatorn laddad, och lokalt kommando |
| `forvarld_film.py` | utfall renderade i förvärlden med lokal Blender |
| `modal_mm.py` | avbildningen. Ändras den byggs allt om. |
| `folj.py` | fel per led mot referensen, för en råfil |
| `mhr_smpl.py` | MHR ↔ SMPL-MJCF |
| `tagning.py` | vilken tagning som helst ur kedjans källa och liggare: läsning, rimlighetsgrind, utjämning, vägen tillbaka till MHR |
| `mening.py` | fri mening → recept → kropp → mått → justering, för vilken tagning som helst |
| `erfarenheter.json` | mätta regler som går in i förståndets prompt |
| `jamfor.py` | tabell över flera råfiler mot en referens |
| `streck.py` | streckfilm och blad direkt ur simulatorns kroppar |
| `RATTNING-0039.md`, `DIAG-0039.md` | Codex två rapporter |

## Logg
- 16 nov 15:39: startfasen rättad. 16:46: verifierad, räckte inte (107 cm per led).
- 16 nov 17:05: `diag officiell` körd: 90,8 cm per led, faller. Övriga fyra stoppades av Modals gräns för nya appar.
- 16 nov 17:21–17:36: varm tjänst uppe (L4 var slut; A10G och T4 tillåtna). Tre fel hittade på 15 minuter, cirka 25 körningar à 35 s. Höftprovet kört.
- 16 nov 17:40–18:30: tidssampling och utjämning; allmän väg (`tagning.py`), slinga och erfarenheter; andra handen och ett andra klipp (b-tilltal) körda.
- 16 nov 18:45–19:00 och 22:30–22:45: arbetaren verifierad, bryggan inkopplad, regibordets knapp provkörd, läget i förvärlden rättat.

## 17 nov: trofé syntes inte i förvärlden (rättat)
- **Symptom:** `bild/m_trofe2` var pixelidentisk med basen, fast `sekvens.npz` hade händerna 17 cm högre.
- **Orsak:** äldre källor (b-tilltal S3) saknar `golv_version`. Riggen läser via `metrisk.las`, som då tar `pose_fore_kontakt` och `cam_t_fore_golv`. `tagning.las` läste rått med `np.load`, så `tillbaka` skrev ny `pose` men lät `pose_fore_kontakt` stå kvar som originalet. Riggen renderade originalet. Utgångsläget var också fel: `cam_t` 7 cm från det riggen visar.
- **Rättning:** `tagning.las` läser nu via `metrisk.las`. Sekvensen får `golv_version 2` och riggen tar den nya posen.
- **Drabbade körningar:** `trofe2`, `b_trofe`, `bord_225429`. Gamla utfall ligger som `*_fore_golvfix`. `b_trofe` körs inte om (dubblett av `trofe2`).
- **Kontroll framåt:** jämför alltid en ruta mot basen (medelskillnad > 0) innan en rendering visas.
- 17 nov: ny ändringstyp `vrid` (bara Head): `vrid_grader` sidled (+ vänster), `nick_grader` (+ ned). Vrider referensens G för Neck (40 %) och Head (100 %); huvudet binds 1 (position och rotation). Mått `Head_vrid`, `Head_nick` i `andel_av_andringen`. Uttråkad: sidled 71–75 % (var 17–37 % med forskjut).
