# ingest: källklipp → Blender-förrendering (ett kommando)

```
scen/.venv/Scripts/python.exe scen/3d/ingest/ingest_klipp.py <klipp.mp4> <utmapp> [--personer 2] [--steg 1] [--om <steg>]
```

| Steg | Verktyg (färdiga, inte egenbyggda) | Barklippet (202 rutor, 2 personer) |
|---|---|---|
| personer | YOLO11-seg + BoT-SORT med ReID (Ultralytics) + sammanslagning av spårfragment | 41 s, 5 ID:n slogs ihop till 2 personer (181 och 183 rutor) |
| kamera | COLMAP (pycolmap), var 3:e ruta, personerna maskade | 184 s, 68/68 registrerade, 0,75 px |
| kropp | SAM 3D Body ViT-H på Modal-GPU (`modal_sam3db.py`) | 69 s, 364 jobb, 0,5 s/jobb |
| sekvens | MHR-modellen (identiteten låst, luckor med slerp) + utjämnat rotdjup (Savitzky–Golay, utan tidsförskjutning) | 20 s |
| varld | COLMAP-kameran × personerna → metrisk värld (skalan väljs efter jämnaste rotbana; gravitationen från ryggarna) | 3 s, ojämnhet 0,93 cm/ruta² |
| blender | headless Blender: MHR:s `lod3.fbx` per person (ingen retargeting), nycklad kamera, golv och ljud (`mhr_rig.py`) | 36 s |
| jamfor | ffmpeg: källa \| överlägg \| rendering med originalljud | 9 s |

- **Från noll:** cirka 6 min, varav COLMAP står för 3 min. **Med cache:** 1 min.
- `--om <steg>` kör om från steget och rensar allt efter det. Det fixade en tidig bugg där gamla kroppsresultat med gamla person-ID:n blandades in.
- `tider.json` loggar tid och mått per steg.
- Utdata: `ut/<klipp>/scen.blend`, `render/`, `jamforelse.mp4`.

**Kända gränser:**
- Rum och föremål: steget `rum` finns sedan 9 nov kväll (se längre ned).
- Ansiktsuttrycken är inte inkopplade.
- Klipp med kameraklipp inuti hanteras inte, eftersom COLMAP antar en sammanhängande tagning.
- Vid ren panorering är kamerans förflyttning liten, och skalan blir osäker.
- COLMAP:s fokal kan variera mellan körningar (1 658 mot 2 154 px), vilket påverkar djupet men inte överlägget.

Codex D byggde `rum`; uttryck och Seedance väntar (`scen/3d/klipp2/CODEX-D.md`).

## Spärrar och tyngd (9 nov kväll): `vakt`, rotfix, tillförlitlighet, `kontakt`
Mät först, rätta sedan. `vakt.py <ut> [--tag x]` (4 s, ingen modell) ger `vakt_<tag>.json/.png`: skak (bål och lemmar), ledhopp (> 25°/ruta),
fotglidning i kontaktperioder, golv, rotfart och 2D-avvikelse mot SAM 3D Bodys råa anpassning. Före/efter finns i `ut/*/vakt_fore.json` och `vakt_v8.json`.

| Fel (vakt) | Orsak | Rättning |
|---|---|---|
| Kroppen flippar 100–180° (bar ruta 116, 126) | **vårt fel:** MHR-roten är extrinsisk `xyz`-Euler; nära ±π byter anpassningen likvärdig trippel, och utjämning av Euler drar genom 0 | `sekvens_stabil.py`: roten som kvaternion med kontinuerligt tecken (fyll, Hampel, lågpass), tillbaka till Euler sist |
| Handled/underarm 38–45° på en ruta | tvetydigt vrid i en bild ("candy wrapper") | Hampel per parameter + fartgräns 0,3 rad/ruta (fram+bak, centrerad) på vrid-/handledsparametrar |
| Skräpkroppar som flyger när personen går ut ur bild | modellen gissar på halva kroppar | `palitlig_<pid>.json`: < 35 % av kroppspunkterna i bild eller < 15 % i masken -> rutan räknas som okänd |
| Rotdjup hoppar 2,4 -> 3,7 m, ×1,6 i golvsteget | avståndet är svagt bestämt ur en kamera; golvskala per ruta från osynliga ben | `cam_t` = siktlinje (6 Hz) × avstånd (Hampel ±7, 2 m/s, 1,5 Hz, `padtype='even'`); konstant golvskala om benen syns < 20 % |
| Fötter glider (0,77 cm/ruta i kontakt) | ingen kontaktmodell | `kontakt.py`: kontakt (höjd/fart, hysteres) -> begränsad kroppsförskjutning (längs siktlinjen helt, sidled ½, max 4 cm) -> **analytisk tvåbens-IK i numpy** på MHR:s globala leder (höften fast, knät i originalplanet, foten flyttas utan vridning) |

Blenders IK fungerar inte på MHR-riggen: bensvansarna pekar inte mot nästa led (vadens svans ligger ~30 cm från vristen). Därför görs IK före Blender.

Resultat, före -> efter:
- bar p1: skak max 44 -> 5 cm, ledhopp 88 -> 41°, rot 7,0 -> 4,4 m/s, 2D överkropp p95 37 -> 2,0 %
- bar p2: skak 86 -> 8 cm, ledhopp 157 -> 51°, rot 6,9 -> 1,9 m/s, 2D p95 8,8 -> 4,7 %
- biljard: ledhopp 45 -> 23° (rutor > 25°: 19 -> 0), glidning i kontaktperioder 0,77 -> 0,00 cm/ruta, 2D oförändrad (3,7 %)

Kvarstående och avsiktligt:
- I bar står fötterna "under golvet" fler rutor (12 -> 56). Benen syns aldrig bakom disken, och disken från `rum` (Codex D) döljer dem.
- Bar p2:s ledhopp 30–50° i ruta 107–110 och 125–129 är äkta: kollegan snurrar runt (källan bekräftar).

Prövat och förkastat:
- **Maskprompt** till SAM 3D Body (`personmasker.py`, `--maskprompt`) gav sämre resultat i bar (2D 1,9 -> 16 %, bålskak p95 1,8 -> 8,9 cm). Det är av som standard.
- **SAM-Body4D** är blockerat: SAM 3 är gated för vår HF-token, och Depth-Anything-V2-Large är CC-BY-NC.
- **Gemini-granskning** (`scen/3d/granska/granska.mjs`): Pro saknas på gratisnycklarna och den betalda är tom; gratiskön för Flash svarade inte ens på ett ord på över 2 min. Skriptet finns kvar till senare.

## Steg `rum` (Codex D, 9 nov 21:00–21:26, kvoten tog slut 21:26)
Ordningen är nu ... golv → kontakt → **rum** → blender. Steget består av `rum.py`, `rum_objects.py`, `rum_gemini.py`, `modal_rum.py` och `rum_verify.py`, med tester i `test_rum.py` (3 OK). Licenser finns i `scen/3d/RUM-LICENSES.md`. Djupet och detekteringarna ligger i cache under `ut/<klipp>/rum/`, så en omkörning med `--om rum` tar 25–30 s utan externa anrop. Verifierat av Claude 21:35 efter att kvoten tog slut.
- **biljard:** tre biljardbord på 2,4 × 1,3–1,5 × 0,8 m, fyra väggar (närmaste 1,5 m från kameran) och personens avstånd till borden (0,3–3,2 m). Borden skymmer kroppen rätt i renderingen.
- **bar:** diskens framkant följer källan över hela klippet (`rum/overlay.jpg`) och döljer underkropparna; kortterminalen finns med som rekvisita. Diskens mått i `rum.md` (0,98 × 0,30 × 1,25 m) är otydliga, troligen för att disken fortsätter utanför bild.
- **Varning:** MoGe och COLMAP är oense om den metriska skalan med 75 % (bar) och 197 % (biljard). Rummet använder COLMAP-skalan; MoGe:s absoluta skala är inte pålitlig här.
- **Vakt:** identisk med v8 före och efter `rum`. Steget rör inte kropparna.

## Steg `plats` (10 nov): alla tagningar i en plats
`plats.py <ingestmapp> [--ut <mapp>] [--hand <fil>]` läser bara tidigare stegs utdata (varld, sekvens, rum, masker, MoGe-djupcache, tagningsvideor) och kör inga steg om. Utdata: `plats/plats.json` (golv, sammanslagna objekt, ankare, tagningarnas transform med kvalitet, bindningar), `plats_matt.json` (siffrorna bakom besluten) och `plats.md`. En ensam ingest-mapp ger identitetsfallet (platsen = tagningens egen värld) och kräver `--ut` (skriver aldrig i ingest-mappen). Ordning, billigast först: (1) SIFT + RANSAC + 3D ur MoGe-djup lägger tagningar på samma kamerastation (uppmätt, tröskelvärden i `TROSKEL`); (2) personer som landmärken (bäcken på golvet + torsoriktning); (3) scengrammatik som märks `antagen`: de två huvudrollerna sitter vända mot varandra, motbildernas kameror står vid motpartens huvud, stolsavstånd ur kamerornas uppmätta avstånd; (4) rest: kamerastationens medelläge med handgjord blickriktning (`hand.json`, annars godtycklig 0 grader). Skala är 1,0 (antagen). Objekt från alla tagningar slås ihop (samma etikett, < 0,5 m, topphöjd inom 0,25 m) efter rimlighetsfilter; avvisade observationer och väggfragment listas med orsak. Körtid notan: 5–7 s. Bild: `plats_oversikt.py` (Blender, headless) ritar platsen uppifrån och snett med alla roller på sina ankare och kameramarkörer.

Resultat notan: bildmatchning kopplar bara S1/S3/S6 (samma station, 356–590 inliers, 3D-rest 6–10 cm); motbilderna delar inga särdrag. Se plats_matt.json.

Rumsmall (10 nov): `plats.py --rumsmall <id>` passar parametriska möbler från `kontrakt/rumsmall/`; djupfragment sparas bara som evidens. `mhr_rig.py --plan` bygger mallrummet och stöder osynliga ben mot sitt/ståankare, med ledlista i `stod_rapport.json`. Se kontraktets README; utan plan används den tidigare byggvägen.

Bildtrohet (10 nov, uppföljning): golvstegets skalning av enbart `cam_t` ändrar projektionen när kroppen har ändlig storlek. Kontraktets kompilator kompenserar detta i flerklippskameror med dolda ben, utan omkörning av ingest. `kvalitet.bildtrohet` jämför byggda riggleder med sparade 2D-punkter före CM-kameraändring; flaggad render kräver `--tillat-flaggad`. Planer med `benlangder_m` använder kontraktets längdbevarande stöd och numpy-skinning av uppmätt FBX-fothud. Bäcken och uppmätt överkropp skyddas; korta ben får hänga, stående ben böjs mot golvet. Stols- och bordhöjd passas i planen, utan ändring av ingestdata. Befintliga CLI-anrop och byggen utan plan behåller sin tidigare väg. Se `../kontrakt/ut/notan/tro_rapport.md` för mått, osäkerheter och granskade bilder.

Golv och skymning (10 nov, fortsatt uppföljning): platssteget kombinerar nu befintliga fot-, djup-, kropps- och möbelcues, sist kamerahöjdens prior. Värden, spridning, avvisningar och konflikter över 10 cm sparas i `golv.matning`; ett gemensamt golv har egen kamerahöjd per tagning. Möbelhöjder är märkta priorer. MHR70 13–14 är vrister, trots den äldre synlighetskommentaren. Maskverifierade synliga lår/knälägen skyddas separat i planen; fasta mått gäller ändrade dolda segment. En ensam tagning behåller standardgolvet, med `--tillampa-golv` som uttryckligt alternativ. Inga ingeststeg körs om. Kontraktets kompilering skriver `kvalitet.md`, prövar skala och mallskymning och redovisar varje antagande; se `../kontrakt/ut/notan/golv_rapport.md`.

## Lokal bild- och diskpassning

`bildskydd.py` begränsar stabiliseringens avvikelse från sparade, tillförlitliga 2D-kroppspunkter utan nytt kroppsanrop. En kort kameratranslation nollställs, men kamerans rotation bevaras. Orimlig metrisk fart avvisas separat. Det ändrar inga diagnostiska bildtrösklar.

`kamera_vertikal.py` kan komplettera kamerans pitch/roll med bakgrundskanter utanför personmasken; osäkra flyktpunkter avvisas mot kameragruppen. Interpolation och överföring från samma modellbedömda kamerauppställning är antagna, och loggas i `vertikaler.json`. `diskplats.py` skiljer på kund- och personalsida, använder parametriska disk-/monterramar och kan passa gemensam kamera/personhöjd mot redovisade källpixlar. Ursprung, kontaktrester och pixelrester sparas i platsen. Glasytor utelämnas i Workbench; ramar och sockel är mallgeometri.


## Utjämning av kroppssekvensen: varför den drev och vad som gäller nu (10 nov, jämn-passet)

**Problem.** Bildskyddet (`bildskydd.py`) blandade ruta för ruta tillbaka estimatorns råpose tills p90-avvikelsen mot estimatorns EGNA 2D-punkter var högst 6 px. Mätet i kvalitetssidan är samma punkter, så p90 hamnade på 6,0 av konstruktion, och priset var dolt: den stabiliserade posens medianandel var 0,13–0,85 och darret (medel andra differens av ledpositionerna, cm/ruta²) steg 2,5–5 gånger (b S1 0,77 → 2,86, b S5 1,14 → 4,55, kenny S1 1,34 → 6,0, a S1 2,21 → 6,47). Bildskyddet är därför borttaget ur `ingest_klipp.py` (filen ligger kvar, anropas inte; gamla `bildskydd_*.json` är omdöpta till `*.json.gammal`, kopior i `<tagning>/fore_jamn/`).

**Verifierad orsak till avvikelsen, uppföljning 10 november.** Den tidigare ablationen använde samma felaktiga ledurval som metodtabellen. Den var därför inget tillräckligt stöd för påståendet att rad-Hampel och rotorienteringen ensamma förklarade felet. `kontrakt/engang/jamn_stegablation.py` isolerar nu stegen med filmens 44/48 ledpar. Underlag: `kontrakt/ut/prop_granskning/stegablation.json`.

| Tagning | Benhållning, rå cam_t p90 px | + rad-Hampel | + komponent-Hampel för handled/underarm | + fartgräns | + lågpass |
|---|---:|---:|---:|---:|---:|
| b S1 | < 0,001 | < 0,001 | 56,79 | 56,79 | 53,46 |
| a S1 | < 0,001 | < 0,001 | 32,20 | 30,18 | 64,47 |

Komponent-Hampel ersatte verkliga handleds-/underarmsvinklar med fönstermedianer. Det flyttade alla deras fingerleder och gav ett stort p90-fel trots nästan oförändrade axlar. Lågpassningen spred och ändrade avvikelsen. Kamerarumspositionens gamla filter bidrog också: med råa kroppsparametrar ger enbart gammal cam_t b S1 3,38/8,47 px och a S1 10,29/39,50 px. Det är alltså inte samma sak som kamerans världsbana eller golvsteget. Enbart återställd rå rot förbättrar inte helheten: b S1 median 12,51 → 15,02 px, a S1 11,99 → 17,12 px med gammal cam_t. Det tidigare säkra påståendet om roten var för starkt.

Råa formparametrar varierar (b S1 maxspann 1,335), men första form, medianform och per-ruta-form ger samma FK-resultat i den testade b S1-ablationen. Variationen förklarar därför inte dess px-glapp. Det glappet kom från att tabellen felaktigt uteslöt fingrar när benen var dolda.

**Oberoende kontroll (silhuett-IoU mot YOLO-masken) skiljer inte metoderna åt.** I alla sju scener ligger IoU inom ±0,01 för rå, gammal, bildskydd och nya metoder (b S1 0,792 / 0,780 / 0,788 / 0,780). Det betyder att px-avvikelsen mest är fingerleder (42 av 48 mätta punkter) och brus som inte syns i kroppens kontur: bildskyddets "bättre passning" köpte ingen mätbar bildmatchning men 3–5 gånger mer darr.

**Metoden nu (`sekvens_jamn.py`, anropas från `sekvens_stabil.py`).** Per parameterspår (och rotens kvaternionskomponenter) en Whittaker-utjämnare (symmetrisk, ingen fasförskjutning, andra differensen, 4 Hz halveffekt) vars avvikelse från estimatet är begränsad till k = 2 brusenheter, där bruset skattas per spår ur tredje differensen (robust, MAD). Brus som estimatorn har ruta för ruta jämnas ut; en verklig rörelse som skulle hamna längre från estimaten än bruset ersätts aldrig av en kompromiss. Luckor (opålitliga rutor, dolda ben) och trasiga rutor (≥ 25 % av spåren > 6 brusenheter från den utjämnade kurvan, två varv) har vikt 0 och överbryggas mjukt; ingen medianruta, ingen konstant benhållning, ingen slerp. Vrid/handled behåller fartgränsen 0,3 rad/ruta. `cam_t`: siktlinjen och log-avståndet utjämnas som egna spår (2 Hz, k = 2). Benlängder och identitet är som förr (formparametrarna låsta; parameterutjämning ändrar inte benlängden, testat). Fc, k, d och trasig-gränserna är våra val (`STANDARD`).

**Vad som byttes mot vad, rättad tabell.** b S1 gammal: 12,51/53,80 px, darr 0,77; bildskydd: 2,77/6,02 px, darr 2,86; vald rör 4 Hz k2 + ny cam_t: 15,73/48,50 px, darr 0,97. b S5 p90 46,14 → 30,98 mot gammal metod, men darr 1,14 → 1,53. Kenny S1 p90 62,34 → 50,14, darr 1,28 → 3,77. Metoden är jämnare än bildskyddet, men löser inte både fingerpassning och darr i alla scener. Gränserna är oförändrade; Kenny S1 och a S1 är fortfarande problem, inte godkända resultat.

**Omkörning.** `kor_jamn.py <ingestmapp>` kör sekvens, varld, golv och kontakt direkt på stegfunktionerna (inget `--om`, som skulle ha flyttat rummets cache till arkivet), efter att filerna som skrivs över kopierats till `<tagning>/fore_jamn/`. Därefter `kor_jamn.py --vertikaler b|kenny|a` (vertikalerna lades förr på efteråt). Rummet och plats-filerna körs inte om: b, kenny och a har 0 uppmätta objekt i platsen, och ankarnas lägen skiljer bara centimeter; `kalla_omhasha.py` räknar om kontraktets hashar. `jamn_utvardera.py` jämför metoder på rå-estimaten.

### Kamerabana (kenny S2: 11,7 km)
Orsak: skalsökningen i `steg_varld` väljer k som minimerar rotbanans ojämnhet. I kenny S2 registrerades COLMAP-kameran bara på ruta 0–51 men personen syns först på ruta 60–95, där kameran är konstant (interpolationen håller sista posen). Ojämnheten blev därför identisk (till 1e-14) för alla k, och argmin gav ett slumpmässigt k = 785 (COLMAP-banan 14,9 enheter → 11 693 m). Hastighetsregeln (p90 > 5 m/s) fångade det redan i `varld.npz` (translation avvisad, rotation behålls), men `tider.json` och kvalitetsloggen visade ändå 11,7 km. Nu: (1) `regler.skala_bestamd`: en platt ojämnhetskurva (spridning < 2 % av medel) betyder oidentifierbar skala och translationen avvisas med den orsaken; (2) `regler.kamerabana_rimlig` kontrollerar varje metrisk bana mot **p90-fart ≤ 5 m/s, maxfart ≤ 15 m/s och sträcka ≤ 5 m/s × klippets längd** (egna gränser för en handhållen mobil inomhus); skälen skrivs i `skalbeslut`. Kvalitetssidan visar kamerabanan per scen (se kontraktets README).

Kroppsmåttet har nu även en beständig cache i `kontrakt/ut/cache/kroppmatt/`, utöver högst 32 processlokala sammanfattningar. Mätfiler, kamera, tidsurval, bildmått, stöd, kod och riggdata ingår i nyckeln. Ändrat underlag ger ommätning; inga maskrutor hoppas över. Test i `test_kroppmatt.Matcache` och `test_snabb.Cache`. För editkompilering finns `kompilera.py --snabb`; det bevarar byggbesluten och märker diagnostiken okörd. Full pipelinekörning behåller full diagnostik som standard. Se kontraktets README.


### Slutvärden i tidsloggen, steg 10c

`kor_jamn.py` loggar sekvensens slutliga utsnittsbeslut efter att den historiska
golvregeln har tillämpats. `varld.kamerans_vag_m` avser den accepterade banan;
`varld.skalbeslut.vag_m` avser kandidaten före eventuell avvisning. Kenny S2
har 0 m accepterad translation. Den sparade jämn-körningens avvisade kandidat
är 14 307,266 m; den äldre tidsloggen visade 11 693,57 m. Dessa är två olika
kandidatkörningar, inte två längder på den använda kamerabanan.

27 befintliga tagningsloggar har synkats med sina redan sparade varld.npz och
utsnitt. `loggsynk` anger underlag och föregående fält; `sek` behåller den
historiska körtiden och är ingen ny mätning. Inga ingeststeg kördes i synken.
Varning om inaktuella källmanifest görs vid stegkörning och jämn-omkörning.
Själva loggfunktionen har åter sitt ursprungliga beteende.

En läsinventering av direkta MHR-beroenden finns i
`../kontrakt/MHR-BEROENDEN.md`. Den är underlag inför ett möjligt modellbyte,
inte en genomförd migrering.
