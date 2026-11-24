# Granskning (Claude), 31 okt 2026, kväll

## Målet i tre led
1. Ett riktigt klipp blir pålitligt en representation med ~90 % grov likhet.
2. Reglaget styr vertikalen Rörlighet, förklarat som en mix av spakar, isolerat till vertikalen, med kedjan som enhet.
3. Träningsdata ur 1000+ klipp, med urval.

## Var vi står, ärligt
| Led | Läge | Bärande antagande som inte är validerat |
|---|---|---|
| 1 Rekonstruktion | 80–88 % på 3 klipp (eget mått). Bakgrund nära foto (projicerad ren skiva), poser 93–100 % PCK, kamera 76–100 %. Dockorna är skyltdockor. | Att måttet motsvarar "90 % grov likhet" för en människa. Utsnitt/antal hänger på att detektorn ser dockorna (brus ±20 % mellan körningar). |
| 2a Variation | Uttryck = kamera + agerande (amp). För rekonstruktioner håller bara kameror nära originalets: närmare utsnitt och ±15°; vidare utsnitt ser 15–40 % av det originalet såg. | Att 3D-rekonstruktionen tål nya vyer. Den gör det inte: världen finns bara framifrån. |
| 2b Vertikalen | Linjär modell, startvikter, **0 mänskliga bedömningar**. Stegen är ranger. Pixelmåtten kan belöna artefakter. Förklaringen är korrekt räknad men förklarar en ovaliderad modell. | Att modellen motsvarar upplevd rörlighet. Helt otestat. |
| 2c Kedjan | Fungerar (mål, tröghet, grannar, hem på 5). Skyddsräcken inkopplingsbara men tomma. | Att typerna (4 från Gemini) räcker som skyddsräcken; för få klipp per typ. |
| 3 Bank | Profiler lösta 63/78, nedladdning pågår, sållning/urval/bedömningsvy klara. | Inget stort; mest tid. |

## Den strategiska felbedömningen
Jag har behandlat 3D-rekonstruktionen som basen för hela vertikalen. Men de flesta spakar för Rörlighet är **2D-operationer på originalvideon**: digital omkadrering (zoom/beskärning, panorering inom bilden), kamerans rörelse (lägga till eller ta bort skak, stabilisera), hastighet och ramper, klipprytm (hoppklipp inom en scen, kortare/längre scener inom låsningen), frysning. De ger:
- **fotografisk** kvalitet (originalets pixlar), så "5 = originalet" är exakt och 3–7 ser riktiga ut;
- exakt samma analys (inga dockor som detektorn missar), alltså pålitliga mått;
- spakar som är isolerade och lätta att förklara ("kameran zoomar 15 % in under repliken");
- bedömningar på riktiga bilder, vilket gör kalibreringen meningsfull.

3D behövs bara för det 2D inte kan: ny vinkel, ny kamerahöjd, ändrat agerande (amp), och som förhandsvisning av regi. Där gäller rekonstruktionens begränsning (nära originalvyn), tills världen utvidgas (utmålning) eller en AI-videomodell renderar med rekonstruktionen som styrning.

## Ny plan (förslag)
1. **2D-lagret på riktiga klipp** (stort, mest värde): en virtuell kamera i bild (beskärning/zoom/pan-bana över originalets 1080p/720p), skak och stabilisering, hastighet, hoppklipp. Rendera med ffmpeg/WebGL i webbläsaren. Mät med samma analys. Uttrycksrum = kombinationer av dessa per scen.
2. **Kalibrering på 2D-varianter**: par i `#bedom` (riktig video), du gör ~60, Gemini-domare (ser video) gör tusentals och valideras mot dina (mål ≥ 80 % överens). Modellen tränas, korsvalideras. Pixelmåttens vikt bestäms av data.
3. **Reglaget** väljer bland 2D-varianter för 2–8, 3D-varianter (vinkel, agerande) där 2D inte räcker; kedjan och förklaringen som nu. Skyddsräcken från banken (fler klipp per typ).
4. **3D vidare** bara där det ger något: utmålning för vidare vyer, mänskligare figurer, eventuellt AI-videorendering.
5. **Sluta**: lappa rekonstruktionsmåttet procent för procent; mäta uttryck som ändå blir ogiltiga.
