# Scen3D: ett riktigt 3D-rum ur ett exempelklipp, redigerbart med semantiska operationer

> **Pipen från klipp till förvärld står i [PIPE.md](PIPE.md) (11 nov).** Börja där. Den här filen beskriver första scenen från 7 nov.

Klipp: `scen/klipp/d-dialog-notan.mp4` (hampuslundgren, "vem tar notan", 12,8 s, 7 tagningar).
Byggt 7 nov 2026, i fas 1–2 av Codex (gpt-6-astra, xhigh) med Claude som granskare. Fas 3 påbörjades av Codex och slutfördes av Claude när Codex-krediterna tog slut.

Det här är inte en video med effekter. Klippet har översatts till ett **rum med objekt**: bord, stolar, väggar, fönster, lampor, disk och rekvisita, alla med semantiska id. Personerna är **rundade 3D-figurer** som drivs av klippets uppmätta 3D-rörelse: kropp, händer, ansikte och munrörelser. Varje tagning har en **3D-kamera** som återger källans bildutsnitt och kan flyttas fritt efteråt. Allt beskrivs i `scen3d.json` och ändras med `op.py`.

## Köra

```powershell
scen/.venv/Scripts/python.exe -m http.server 8000 --directory scen/3d
# öppna http://localhost:8000/   (Spela, Originalljud, Textning, Fri kamera, val av kamera/figur)
```

Uppspelaren läser om `scen3d.json` varje sekund, så en ändring syns direkt. Fas 4: standardfigur X Bot, ljudläge "Designade röster" eller "Originalljud", textning ord för ord. Syfte och regler står i `SYFTE.md`, frön för nästa scen i `FRON-1.5.md`. `#t=8.2&capture=1&mode=mask&cam=S6` ger en fryst bildruta.

| Steg | Kommando | Tid (CPU) |
|---|---|---|
| Fas 1/1b: mätning, kamera, placering | `python -B scen/3d/fas1.py` sedan `fas1b.py all` / `fas1b_finish.py` | cirka 2–4 min |
| Fas 2: bygga `scen3d.json` ur layouten | `python -B scen/3d/fas2.py` | under 1 s |
| Fas 3: kalibrera rekvisita mot källan | `python -B scen/3d/kalibrera_rekvisita.py` | cirka 2 s |
| Verifiering, snabb eller full | `python -B scen/3d/verifiera.py [--quick]` | 10 s / cirka 2 min |
| Demonstration av ändringarna | `bash scen/3d/demo-andringar.sh` och `python -B scen/3d/demo_render.py efter` | under 1 s / cirka 15 s |
| Fas 4: stabiliserade armar | `python -B scen/3d/stabilisera.py` | cirka 10 s |
| Fas 4: ordtider ur källjudet | `python -B scen/3d/ordtider.py medium --skriv` | cirka 2 min |
| Fas 4: kamera-ingest och klipp mot tal | `python -B scen/3d/kamerarorelse.py`, sedan `kamera_ingest.py --skriv` | cirka 10 s |
| Fas 4: designade röster och munkurvor | `python -B scen/3d/roster.py [--testa] --skriv` | cirka 14 s |
| Fas 4: verifiering (procedural mot X Bot) | `python -B scen/3d/verifiera_fas4.py` | cirka 3 min |
| Förhandsfilm (bara för granskning) | `python -B scen/3d/mvp_render.py` | cirka 4 min |

Återställ till basen (före ändringarna): `cp scen/3d/scen3d.bas.json scen/3d/scen3d.json`.

## Kedjan och vad som valdes

| Del | Valt | Jämfört med | Varför |
|---|---|---|---|
| Kroppens 3D-pose | MediaPipe PoseLandmarker, metriska världspunkter, 30 fps, plus Hand- och FaceLandmarker | 10 fps-datan i `data/ra` | Full bildfrekvens; händer och ansikte (munrörelser, ögonbryn) behövs |
| Kamerans synvinkel | Gemensam **68°** för hela klippet (mobilens huvudkamera, stående) | Fri synvinkel per tagning | Felkurvan är nästan flat (0,0125→0,0172 H mellan 30° och 70°), så posen kan inte bestämma synvinkeln. Fritt val gav 40–73° och slog i gränserna. |
| Kamerans läge | En kamera per tagning (PnP på kroppen) | En kamera per uppställning (S1/S3/S6, S2/S5) | Kameran flyttades mellan tagningarna (A:s bakgrund förskjuts 20–78 px); delad kamera gav 63–66 px fel i S6 |
| Rum och bord | Bord B mätt ur S7:s kanter: 0,59 × 1,17 m. Kanten sitter med 0,3/0,5 px fel. | Granskarens gissning 1,05 m bred | Mätningen passade bättre; 1,05 m gav 66 px kroppsfel i S7 |
| Djup för placering | PnP + gemensamma föremål (burken i S1 och S7) | Depth Anything V2 skalad med kroppslängden | Djupet gav större fel |
| Figurer | **Procedurella rundade figurer** (kapslar, ellipsoider), drivna av leder, händer och blendshapes | VRM-avatar via three-vrm + kalidokit (CC0 VRoid), fyra mappningar | VRM blev anime-stil och följde lutning och gester sämre |
| Figurer (fas 4, standard) | **Neutrala dockor, Mixamo X Bot**: rollfärgad lös tröja och neutralt kortklippt hår, lika för alla (ingen likhet); ansikte på huvudytan; mun efter designad röst | Procedurella figurerna (kopierar hår och kläder = likhet), VRM (anime), hårridå som castingval (förkastad: ful, hjälpte inte) | Ledfelet 0,007–0,037 H klarar kravet i alla tagningar. Silhuetten är 0,51–0,81 i snitt per tagning och klarar 0,5 i S2–S6 i varje bildruta. Undantag: S1 bildruta 0 (0,474), där hennes långa hår och stora jacka saknas |
| Armar (fas 4) | Leder på bildstrålar, fasta benlängder, One-Euro | MediaPipes världspunkter direkt | Flaxindex 0,0027 → 0, ryck −80 %, återprojektion 24 → 10 px |
| Repliker och röster (fas 4) | Ordtider ur KBLab Whisper; Piper-röster (alma, nst) i ordtidsluckor | Uppskattade tider per tagning | Ord klipps aldrig av `langd`; textning ord för ord; röster ±0,02 s i sin lucka |
| Rekvisitans storlek | Minsta kvadrat mot källrutor (Gemini 3.5 Flash-Lite, gratis) över alla tagningar samtidigt | Fas 2:s antagna mått | Rekvisitan var 1,2–2,4 gånger för stor, B:s hamburgare låg 661 px fel |
| Förfining av kameran mot föremål | **Förkastad** | Kamera + föremål gemensamt (`forfina_kameror.py`), bordshöjd fri (`testa_bordshojd.py`) | Kameran slog i gränserna (−3°, −6 cm) och flyttade kroppsfelet i stället för att minska det; bordshöjden landade på 0,745 m utan vinst |

## Resultat

| Tagning | Ledfel (median px / andel av H) | Silhuettöverlapp mot källan | Kommentar |
|---|---|---|---|
| S1 (A) | 16 / 0,016 | 0,68 | |
| S2 (B) | 23 / 0,022 | 0,69 | |
| S3 (A) | 27 / 0,026 | 0,67 | |
| S4 (C) | 14 / 0,014 | 0,84 | |
| S5 (B) | 36 / 0,035 | 0,68 | |
| S6 (A) | 39 / 0,038 | 0,73 | Svagaste kameran |
| S7 (B långt bort) | 18 / 0,018 | 0,43 | Liten figur; munnen syns knappt |

Siffrorna gäller bildrutan mitt i varje tagning (`verifiera.py --quick`) efter kalibreringen. Fas 2:s fulla verifiering med tre bildrutor per tagning finns i `rapport.md`. Kravet var ledfel ≤ 0,04 H och silhuettöverlapp ≥ 0,5 för S1–S6.

**Rekvisita efter kalibrering** (`data/kalibrering-3.json`, bild `verifiering/fas3/kalibrering.jpg`):
- Burk, mugg, såskopp och B:s hamburgare, låda och pommes ligger inom ±25 % i storlek och inom 30 px i mitt.
- A:s hamburgare och pommes är delvis skymda i källan, så källrutorna blir för små och höjden slår i nedre gränsen.
- Brickan och det inslagna föremålet ligger 25–72 px fel i någon tagning. Det beror på att ett fast föremål ska passa tre tagningar med olika kameror, och kamerornas lutning är osäker med ±1–2°.

## Datamodellen (`scen3d.json`, schema `scen3d/2`)

| Nyckel | Innehåll |
|---|---|
| `set[]` | Rummet: `id` (`table:A`, `wall:A:window`, `lamp:0` …), `type`, `transform` (position i meter, yaw i grader), `dims`, `color`, `provenance` (hur det mättes) |
| `props[]` | Rekvisita: `id` = ägare:etikett (`A:can`, `A:burger`, `A:burger_wrap`), `type` (paper_cup, drink_can, burger, pizza_slice, fries_box, food_box, paper_wrap, tray, sauce_cup, card_terminal, fry), `dims`, `transform`, `support`, `semantic` |
| `actors[]` | A, B, C: `look` (längd, hud, hår, frisyr, kläder), `transform`, `motion` (spår, intensitet, handankare, humör), `seated` |
| `shots[]` | `source` (in/ut i källan, `shotId`, fryst `camera`), `duration`, `actors[]` (per tagning: `transform`, `transformKeyframes`, `motion`: intensitet, spegling, humör, `fromShot`), `camera.keyframes[]` (pos, mål, upp, fov, t) och `camera.orbit`, `propOverrides` (synlighet, transform, fästa i hand), `beat`, `dialogue`, `audioRange` |
| `dialogue[]`, `audio` | Repliker med tider och källans ljud |
| `editLog[]` | Varje ändring: operation, argument, resultat, ms |

Källkameran (`source.camera`) är den kamera rörelsen **mättes** med. Bildkameran (`camera`) kan ändras fritt utan att figurerna förvrängs.

## Operationer (`op.py`)

```
python -B scen/3d/op.py --help      # alla kommandon och väljare
python -B scen/3d/op.py list        # allt adresserbart per tagning
```

**Väljare:** `A`/`B`/`C` (aktör), `A:cup` (ägare:etikett), `S1:burger` (etikett synlig i en tagning), `table:A` (rummet), `A:huvud` (målpunkt: näsan enligt posen).

**Kommandon:**
- Föremål: `flytta`, `rotera`, `byt`, `dolj`, `visa`.
- Kamera: `dolly`, `zoom`, `orbit`, `kamera`.
- Tagningar: `langd` (replik-säker som standard: pauser krymper, talet högst ×1,15, ord klipps aldrig; `--lage trim` eller `stretch`), `duplicera` (tyst kopia), `ta-bort`, `flytta-tagning`.
- Aktörer: `lagg-till-aktor`, `vand`, `titta` (bara huvudet mot ett mål, högst 80°), `spegla`, `intensitet`, `humor`, `utseende`, `casting` (rollnamn, röst, tröjfärg).
- Repliker: `replik N --text "..."` ger en designad röst i samma lucka (0,4–0,6 s med `rostserver.py` igång, annars ~6 s); rälsen varnar om farten.
- Övrigt: `angra`.

Alla operationer loggas och tar **3–14 ms**. Undantaget är den första operationen som behöver en huvudpunkt: den bygger cachen `data/huvudpunkter.json` och tar cirka 100 ms en gång.

## Demonstration: sju semantiska ändringar (`demo-andringar.sh`)

| Begäran | Operationer | Utfall |
|---|---|---|
| 1. Byt hamburgaren mot pizza på A:s bord | `byt A:burger --typ pizza_slice` | Pizzan ligger i lådan; lådan är eget föremål och står kvar |
| 2. Långsam inzoomning på hennes ansikte i punchlinen | `dolly S6 --mot A:huvud --faktor 0.55` | Kameran åker från 0,80 m till 0,44 m framför hennes ansikte |
| 3. Servitören vänder sig mot henne, tagningen kortas till 1,6 s | `vand S4 C --mot A`, `langd S4 --s 1.6` | Han vänder kroppen 135°, så vi ser honom bakifrån och från sidan. Ett "titta mot" (bara huvudet) saknas. |
| 4. Bort med burken, muggen närmare henne i kroken | `dolj A:can --tagning S1`, `flytta A:cup --mot A --m 0.12 --tagning S1` | Gäller bara S1 |
| 5. Ny sista tagning där kameran kretsar 90° runt hans bord | `duplicera S7 --som S8`, `orbit S8 --runt B --grader 90 --radie 1.7`, `langd S8 --s 3 --lage stretch` | Rummet håller ihop från nya vinklar, se `verifiering/fas3/demo/S8-orbit.jpg`. Hans rörelse går i halv fart. |
| 6. Servitören står bakom henne i punchlinen, rätt djup och skala | `lagg-till-aktor S6 C --bakom A --avstand 0.85 --sida 0.3 --vand-mot A --fran-tagning S4` | Han står bakom henne, skymd i rätt ordning och innanför fönsterväggen. Han rör sig som i S4. Den täta bilden beskär hans huvud; för att se honom helt behöver bilden också vidgas. |
| 7. Hon ska kännas mer stressad | `intensitet` ×1,5 och `humor stressed` i S1, S3 och S6, `langd` S1 1,9 s och S3 1,5 s | Mer gestik, ögonbryn och tryckta läppar, tätare klipp |

Bilder: `verifiering/fas3/demo/fore-efter.jpg` och `S8-orbit.jpg`. Ett svep genom hela den redigerade tidslinjen (69 bildrutor, 13,6 s) gav noll sidfel, och varje bildruta hade sin huvudaktör.

## Begränsningar

- **Kropparnas skala och dolda kroppsdelar** är antaganden: sittande ben, höfthöjd 0,6 m, bordshöjd 0,75 m. Servitörens plats i rummet är ett antagande.
- **Kamerorna** är lösta ur kroppen med en gemensam synvinkel. Lutningen är osäker med ±1–2°, vilket syns som 20–40 px förskjutning för vissa föremål.
- **Att vända en aktör** roterar hela den uppmätta posen. Det fungerar för små vridningar men blir onaturligt vid stora, eftersom personen fortfarande gör det hen gjorde mot kameran.
- **En tillagd aktör** loopar sin egen tagnings rörelse; den reagerar inte på den nya scenen.
- **Byte av föremålstyp** gäller hela rummet, inte en enskild tagning.
- **Munrörelser i S7** syns knappt, eftersom ansiktet är för litet i källan.
- **Kostnad:** allt körs lokalt på CPU. Gemini användes bara på gratisnivån för rekvisitarutor (cirka 7 anrop i fas 3), Luma inte alls. Codex-användningen var bygget.
