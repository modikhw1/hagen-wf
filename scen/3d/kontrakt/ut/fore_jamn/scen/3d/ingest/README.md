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
