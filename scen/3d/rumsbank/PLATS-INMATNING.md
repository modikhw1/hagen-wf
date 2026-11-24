# Förslag till inmatning i plats.py

Detta är ett gränssnittsförslag, inte en inkoppling. Inga filer i ingest eller kontrakt har ändrats. Ingen av de testade kedjorna är här godkänd som automatisk metrisk sanning.

## Observationer före ett möblerat rum

Behåll varje tagning som en egen observation tills en gemensam transform har stöd i bakgrunden. Ett nät som returnerar alla bilder i samma koordinatsystem har inte därmed bevisat att motbilderna föreställer ett konsekvent rekonstruerat rum. Klippövergångar är inte kameraförflyttningar.

En adapter behöver lämna följande, med hänvisning till källa och osäkerhet:

- Per bildruta: OpenCV K i pixlar, bildens exakta resize/crop-transform, kamera-till-värld R och C, tidsindex och mask för giltig statisk bakgrund.
- Djup: Z-djup, inte avstånd längs strålen; meter eller uttryckligen obestämd skala; modellens konfidens och egna spärrar sparade separat.
- Per tagning: upp-riktning, ett observerat golvplan med normal och offset, planrester i cm och grader, synlig stödyta samt osäkerhet. Saknat golv förblir saknat.
- Per plats: SE(3), eller Sim(3) innan skalan låsts, mellan tagningar. Spara matchande bakgrundspunkter, samstämmighet och skäl för avvisning. Sittplatser och kamerastationer ur scengrammatik märks antagna.
- Möbelobservationer: ytfläckar, synliga kanter, semantisk etikett och skymningsstöd. Fit till mall först därefter. En partiell bordsskiva ger inte automatiskt hela bordets längd och bredd.

Den nuvarande kedjan behöver fortfarande personmasker, statisk/dynamisk klassning, reprojektionskontroll, gravitationsanpassning, robust planpassning, objektidentifiering, mallpassning, ankare och kvalitetsbeslut. Alla dessa steg saknas som färdigt plats-kontrakt i råutdata från MapAnything och DA3. ViPE skattar kamera och djup men ger inte heller ett semantiskt möblerat rum eller redigerbara kroppar.

## Meterskala utan att skala kroppsroten

En monokulär sekvens har ingen geometriskt observerbar absolut längdenhet utan ytterligare mått. Modellens ord ”metric” betyder en inlärd meterskattning. På ett stativ kan även fokal och djup vara svagt bestämda. En normal dörrhöjd eller bordshöjd är en prior tills det fysiska måttet har bekräftats.

Lås skalan från minst ett identifierat fysiskt mått med osäkerhet, helst flera: exempelvis det faktiska biljardbordets kända hörn, en uppmätt bordsskivehöjd eller en känd persons längd. För ett bord på 2,4 × 1,3 m måste rätt bord och dess fyra hörn först bindas till bilderna. Här är borden beskurna och skymda; att tvinga måtten på en godtycklig grön yta vore ingen verifiering. Kroppsmodellens längd och djup ger ytterligare cues, men är inte ett oberoende facit.

Passa en gemensam skala för bakgrundens punkter och kamerans translation. Använd robusta fel och avvisa en gemensam lösning om cues motsäger varandra. Skala aldrig endast kroppens `cam_t`, och använd inte olika skala per ruta för att få fötterna att nå ett uppskattat golv.

Med kroppsmodellens oförändrade kamerarumsposition `x_cam(t)` gäller:

```text
X_body_world(t) = R_camera(t) @ x_cam(t) + C_camera(t)
x_cam(t) = F @ vertex_body(t) + cam_t_body(t)
projection = K(t) @ x_cam(t)
```

När bakgrund och kamerabana byter gemensam skala, byggs kropparnas världslägen om med samma oförändrade `x_cam`. Då behålls projektionen. Att skala endast `cam_t_body` flyttar en kropp med ändlig storlek och bevarar inte dess projektion.

Ett byte av K måste ske före kroppsestimeringen, eller följas av en bildbunden ompassning med fasta kroppslängder. En ny brännvidd kan inte stoppas in i en gammal kroppslösning och samtidigt påstås bevara bildpassningen. Alternativt används den redan accepterade K som villkor till geometriestimatorn. Den senare varianten har inte testats i denna bank.

Flytta och rotera till ett gemensamt golvkoordinatsystem med en rigid transform av kamera, personer och bakgrund tillsammans. Om synliga fötter ändå motsäger bakgrunden måste mätkonflikten visas eller lösas med ny kalibrering. Dolda ben kan få ett märkt stöd från mallar; den synliga överkroppen och dess bildstrålar skall inte ändras tyst.

## Vad detta inte löser

Osynliga golv, bakgrund bakom personer, möblers baksidor, speglar och glas, rullande slutare, verkliga zoomningar, oöverlappande motbilder och felaktiga kroppsposer förblir osäkra. Ingen av dessa kamerametoder gör ett TikTok-klipp till ett säkert 1:1-rum. Även en bra återprojektion i originalkameran verifierar inte en osedd vy.
