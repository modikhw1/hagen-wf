# Scenmotorn: resultat av tre metoder (7 nov 2026)

Allt körs lokalt på CPU, utan GPU och utan API-krediter. Uppspelaren visas på `localhost:5190/spela/` (starta med `.venv/Scripts/python.exe -m http.server 5190` i `scen/`). Skärmbilderna ligger i `ark/skarm/fall-a.png`, `fall-b.png` och `fall-c.png`.

## Vad som byggdes

1. **Fyra paketerade beroenden**, alla via pip, utan egna bryggor runt ffmpeg:
   - **PySceneDetect 0.7**: scengränser.
   - **Ultralytics YOLO11n-pose**: 17 leder per person, spårning med ByteTrack.
   - **YOLO-World v2**: föremål ur fritt ordförråd ("plate", "raw meat", "scale" …).
   - **Depth Anything V2 Small** (transformers): djup ur en bild.
   - Dessutom **MediaPipe PoseLandmarker** för 3D-pose i meter.
2. **`scen-json` v0** är ett gemensamt format för alla tre metoderna: scener, kamera, händelser, föremål, figurer med originalspår och motivsegment, och bakgrund. Se `README.md`.
3. **Rörelsebiblioteket** (`data/bibliotek/motiv.json`) innehåller 32 motiv ur 858 rörelsefönster om 1,6 s. De kommer från 63 bankklipp, som alla är andra än de tre testklippen.
4. **Uppspelaren** tar semantiska kommandon som `scen 2 gestikulerar`, `ta bort scen 3`, `scen 1 närbild`, `spegla scen 3` och `a1 till bord`. Varje ändring får närhet mot biblioteket och mot bankens struktur, och en hastighet, det vill säga hur långt ändringen ligger från originalet.

## De tre fallen

| | **A · 2D-spår** | **B · semantisk graf** | **C · rum 2,5D** |
|---|---|---|---|
| Klipp | sketch, servering, 22,7 s, 8 riktiga scener | tilltal, tre personer gissar vikt, 15,7 s, 6 takter | sketch, tre personer, en statisk vidbild, 27,3 s |
| Ryggrad | automatisk: PySceneDetect + YOLO | handskriven graf (takter, avsikt, överlämningar); rörelser fylls i automatiskt | automatisk: djup + golvplan + ankare + banor |
| Beräkning per klipp (CPU) | 72 s (scener 2,5 s, poser 23 s, föremål 46 s) | samma 45 s + ca 10 min att skriva grafen | 78 s + rum 17 s |
| Scengränser mot facit | träffar 4 av 7, 4 av 5 föreslagna rätt | automatiskt: träffar 2 av 4, bara 2 av 8 föreslagna rätt (handhållet, texten byts) → handskriven graf krävs | 1 av 1 (rätt: ingen klippning) |
| Personer/identitet | 8 spår-id för 2 roller | 4 aktörer, satta för hand | 9 spår → 5 aktörer för 3 verkliga personer |
| Föremål | pizza/tallrik hittas i serveringen; spettet blir "kniv"/"flaska" | köttbiten blir "pizza"/"box"; vågen hittas inte som våg | tallrik/mat i 38 % av bilderna; bord och stolar blir ankare |
| Händelser | låg nivå: syns, vänd mot kamera, lyfter hand | hög nivå: frågar, räcker, väger i händerna, gissar, döljer ansiktet | rumslig: kommer in, går ut, vid bord, möter |
| Avsikt (krok, vändning, payoff) | saknas | finns i alla 6 scener | saknas |
| Originalets rörelser, närhet ≥ 80 | 78 % (median 82,9) | 83 % (median 90,0) | 87 % (median 87,4) |
| Rörelsebyten provade (32 motiv × 3 farter × spegel) | 1 344, varav 80 % rimliga | 1 152, varav 76 % rimliga | 1 152, varav 83 % rimliga |
| Strukturändringar ≥ 80 (ta bort, dubbla, halvera, dubbla längd) | 88 % | 100 % | 0 %: en enda scen kan inte tas bort, och en dubblad längd ger ett 55 s klipp |

## Fynd

**1. Rimligheten hänger på hur långt ändringen går från originalet.** Avståndet mäts i d90-enheter, där d90 är avståndet som 90 % av verkliga osedda rörelser ligger inom.

| Avstånd från originalrörelsen | A | B | C |
|---|---|---|---|
| nära, under 1 d90 | 100 % rimliga | 100 % | 100 % |
| mellan, 1–2 d90 | 85 % | 71 % | 95 % |
| långt, över 2 d90 | 17 % | 3 % | 57 % |

Det motsvarar velocity: små steg från klippets egen rörelse håller alltid, och stora hopp håller sällan. Gränsen kan visas för CM som en regel.

**2. Utsnittet styr friheten.** Vidbilden i C tål stora rörelsebyten (57 % rimliga långt från originalet). Närbilderna och halvbilderna i A och B gör det nästan inte (3–17 %). En figur som går tvärs genom bilden passar i en total, men inte när huvudet fyller rutan.

**3. Kalibreringen skiljer verkligt från orimligt.** Kontroller på osedda klipp, i andel som når 80+:

| Kontroll | Andel 80+ |
|---|---|
| verkliga rörelser | 88 % |
| speglade | 90 % |
| baklänges | 88 % |
| halv fart | 99 % |
| dubbel fart | 75 % |
| lätt brus | 91 % |
| kraftigt brus | 61 % |
| byta leder | 8 % |
| teleport (figuren hoppar) | 0 % |

Kraftigt brus slinker igenom för ofta. Avståndet ser hur figuren rör sig i stort, men inte detaljer i lederna.

**4. Ändringar går på under 1 sekund med god marginal.** I Node tar en strukturändring 1,8 ms inklusive kloning av hela scenen. En närhetsberäkning tar 0,4 ms med 264 referensfönster och ungefär 2 ms med 1 500. Kommandotolken är regelbaserad, så det finns ingen LLM-fördröjning. En LLM för fri text skulle kosta 300–800 ms (inte testat, alla modellvägar är stängda).

**5. Intention fångas bara av den semantiska grafen.** Automatiken ger vad som syns och var: poser, banor, utsnitt och tid. Den ger aldrig varför. Takterna fråga → gissning → facit → reaktion i B finns bara för att de skrevs. Det Jev skulle lära sig, kopplingen mellan rörelse/scentyp och avsikt, finns alltså inte i något paketerat beroende. Det måste ligga i grafen, skriven av en LLM eller CM, med de automatiska spåren som fyllning.

## Brister som syntes

- **Scendetektorn** missar klipp mellan två bilder av samma person (A, klippet till spettet vid 6,0 s). Den hittar också falska klipp när textlagret byts i ett handhållet klipp (B).
- **Identiteten** bryts i vidbilden: 3 personer blev 5 aktörer, och ett spår blandar servitören med den unge mannen. Att slå ihop spår bara efter position räcker inte. Det skulle behöva utseende (ReID, som finns i Ultralytics BoT-SORT med ReID) eller en hand som rättar.
- **Föremål med fritt ordförråd** träffar vanliga saker (tallrik, pizza, bord) men felmärker råvaror och vågen. Föremålsdetektionen är också den långsammaste delen (46 s av 72).
- **Bakgrundsplattan** (median av bildrutor) blir suddig när kameran rör sig lite. Den behåller dessutom personer som står still, till exempel kvinnan i C. Djupet duger för golv och ankare, men fötternas position i djupled brusar även efter utjämning.
- **3D-posen** från MediaPipe (36, 72 respektive 15 poser) utvinns men används inte i uppspelningen. Planvyn i 2,5D (x och djup) räckte för att flytta personer.
- **Motivnamnen** är grova, eftersom de räknas ur geometri. "Håller fram" dominerar, och 5 av 32 motiv bygger på ett enda fönster (avvikare). Gränsen för nära utsnitt har bara 3 osedda fönster att kalibrera mot, så där används den globala gränsen.
- **Närheten är satt till 80 som "lika nära som 90 % av verkliga".** Varje utsnittsklass kalibreras för sig, men varje fönster bedöms ensamt. Övergången mellan två motiv bedöms inte.

## Programmeringskostnad mot framtida flexibilitet

| | Kod | Vad det kostar framåt | Vad det ger framåt |
|---|---|---|---|
| A · 2D-spår | ~76 rader utvinning + ~100 rader i scenbyggaren, bara paketerat | inget per klipp, ~1 min CPU | snabb ryggrad för många klipp; bra för tid, utsnitt och rörelse, svag för mening |
| B · semantisk graf | grafen ~60 rader JSON per klipp | ~10 min per klipp för hand, eller ett VLM-anrop på kontaktarket | enda vägen till avsikt och takter; enklast att ändra semantiskt eftersom kommandona ändrar takter och inte pixlar |
| C · rum 2,5D | ~114 rader rum + ~60 rader aktörer och händelser, ovanpå A | ~20 s extra CPU per klipp | rumsliga kommandon (till bord, ut, in) och frihet i vidbilder; kräver bättre identitet |

## Hur det kan sättas ihop (en iakttagelse, inget beslut)

Fallen kompletterar varandra mer än de konkurrerar:

- **Grafen från B** som ryggrad: takter, avsikt och föremål.
- **Spåren från A** fyller rörelser och tid automatiskt.
- **Rummet från C** används bara när utsnittet är en total.

Rimlighetsmåttet kan sedan fungera som ratt. Små steg från originalet är fria, stora steg kräver en vidbild eller CM:s godkännande.

## Filer

| Fil | Vad |
|---|---|
| `py/utvinn.py` | scener, poser och föremål → `data/<klipp>/spar.json` |
| `py/rum.py` | platta, djup, golv, ankare, banor och 3D-pose → `data/<klipp>/rum.json`, `data/<klipp>/rum/` |
| `py/motiv.py` | rörelsebiblioteket, kalibrering och kontroller → `data/bibliotek/motiv.json`, `referens.json` |
| `py/struktur.py` | bankens scenlängder, antal och klipplängder → `data/bibliotek/struktur.json` |
| `py/bygg_scen.py` | `scen-json` per metod → `data/<klipp>/scen-<metod>.json` |
| `py/flex.py` | flexibilitetstestet → `data/flex.json` |
| `data/b-tilltal-ravara/semantik.json` | den handskrivna grafen |
| `data/bank/` | spår ur 63 bankklipp (bara poser) |
| `spela/index.html` | uppspelning, kommandon, närhet och hastighet. Testläge: `#fall=1&kmd=scen 2 gestikulerar;ta bort scen 3&t=5` |
