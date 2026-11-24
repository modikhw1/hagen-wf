# GOLV2 i Blender

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
| s1 | 0.637 → 0.636 | 0.666 | 2.0–4.0 | 6.2 | [alla tre](montage/s1_alla.png), [vid](montage/s1_vid.png) |
| s2 | 0.637 → 0.637 | 0.669 | 4.9–9.5 | 25.0 | [alla tre](montage/s2_alla.png), [vid](montage/s2_vid.png) |
| s3 | 0.668 → 0.668 | 0.709 | 1.8–4.6 | 68.0 | [alla tre](montage/s3_alla.png), [vid](montage/s3_vid.png) |
| s4 | 0.709 → 0.723 | 0.723 | 0.3–1.6 | 2.0 | [alla tre](montage/s4_alla.png), [vid](montage/s4_vid.png) |
| s5 | 0.660 → 0.660 | 0.685 | 1.1–4.1 | 8.7 | [alla tre](montage/s5_alla.png), [vid](montage/s5_vid.png) |
| s6 | 0.663 → 0.663 | 0.711 | 14.2–19.5 | 41.0 | [alla tre](montage/s6_alla.png), [vid](montage/s6_vid.png) |
| s7 | 0.551 → 0.551 | 0.558 | 1.3–2.6 | 3.8 | [alla tre](montage/s7_alla.png), [vid](montage/s7_vid.png) |

Hudpasset är verklig Blenderhud mot YOLO inom egen bbox; hår/kläder/occlusion gör att mask och hud skiljer sig. Största enskilda IoU-nedgång är **0.000224**, utan synlig överkroppsförsämring. S4:s benpose ger något bättre IoU. [Alla rutor, sida vid sida och överlägg](RUTOR.md), [varje numerisk försämring](FORSAMRINGAR.md).

Flyttad kamera: +0,5 m kamerahöger, +0,3 m upp, samma mål och lins. A/B sitter överlag rimligt i S1–S6; sulor cirka 0,1 mm över golvet efter stöd, sits 43 cm och bord 76 cm. Rotleden ligger 9,6–11,9 cm över sitsen, vilket inte bevisar hudkontakt. S5 sitter nära stolskanten. **S7 saknar renderad sits före/efter**; dess handleder är i mittprovet 30/42 cm utanför bordet efter, mot 0/8 cm före. [Kontakter](mobelkontakter.json).

**S4/C svävar 10,38/11,24/11,90 cm**, bekräftat i Blender. Fötterna är fortfarande beskurna med oförändrad lins; en separat [vidare före/efterbild](montage/s4_vid.png) visar glappet. Ingen rättning. Person 4, som ger golvcue, utelämnas av planen; samtidig inbördes personstorlek är därför inte verifierad.

Rekvisitans försämring följer möbelpassningen: bildstrålen missar bordsskivan S3 6,5→14,7 cm och S7 35,6→70,1 cm; befintlig propkod klipper till bordskanten. Kamerakompensationen försvinner medan möblerna ligger i mallramen. Det belägger orsaken till propskillnaderna; att lösa den kräver ett placeringsbeslut. Redan före var hamburgarna för stora. Golvlogik, toleranser och design ändrades inte.

## Filer och körning

`efter/`, `fore/`: .blend, planer, renderingar och loggar. `jamforelser/`: 21 sida-vid-sida, RGB 50/50, hudöverlägg och före/efter. `montage/`: alla rutor visuellt granskade samt sju vidare vyer. [Metod och fullständigt underlag](UNDERLAG.md).

Ingen produktionskod ändrad. Tidiga fel i provskriptets mask-/kamerapass rättades och resultaten ersattes; slutliga vanliga vyer renderades separat ur återöppnad scen. **Seriellt från kontrakt/: test_flode: 46 gröna; test_rumsmall: 19 gröna; test_kroppmatt: 18 gröna — 83 prov, 0 fel.**

Inte kört: helfilm/ljud, full diagnostikkompilering, hela 198-provsuiten, övrig ingest, Modal eller GPU-tjänst. Ingen oberoende golv-/möbelinmätning. Löpande logg: `kontrakt/GOLV2-BLENDER-LOGG.md`.
