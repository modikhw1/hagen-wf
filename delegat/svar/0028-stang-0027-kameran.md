---
id: 0028
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
Alla sökvägar under `scen/3d/gennedbrytning/`. Film: [s_scen/film3.mp4](../../scen/3d/gennedbrytning/s_scen/film3.mp4), med remsan och rutbild `film3_rutor.jpg`.

**1–2. Kameran** (`r_kamera.py`, `g_forvarld/dreamina_t_kam/`). Banan löses nu över hela tagningen i stället för fritt per ruta. Följande är låst:
- höjden, 1,30 m
- en rak bana i golvplanet
- linsen i början, 64 mm (det ingesten läste kroppen med)
- jämna förlopp genom nio knutar

Åkningen, zoomen och en liten rättning av tippning och panorering är fria. Varför: dolly och zoom byter av varandra per ruta, så den fria lösningen skakar. Med fri vridning men utan rummets gräns backade kameran 5 m ut med 280 mm tele.
- Väg **0,73 m** (8,8), största ryck **2 mm** per ruta² (124), zoom 48–126 mm, fel 20,7 promille (20,9).
- Lösningen tippar ned **30° i ruta 39–50**, utan att ha fått veta det. Ingestens vertikalmätning såg 34,5° i ruta 39, men avvisade värdet. Tippningen i originalet är alltså verklig.
- Prövat och förkastat (detaljer i STRATEGI): originalets COLMAP-bana, ren dolly, fri höjd, höjdprofil.

**3. Synligheten var geometrin, inte kamerahöjden.** Mätt med strålar i den byggda scenen (`r_synlig_blender.py`), ruta 45–70:

| | hand | underarm | tråg |
|---|---|---|---|
| 0027 (`s_scen3`) | 0 % | – | 0 % |
| ny kamera, samma scen | 89 % | 0 % | 95 % |
| + glasfront och sänkt bakkant (`s_scen5`) | **100 %** | **100 %** | **95 %** |

Handen går 0,6 m under diskens ovankant. Ingen kamera med rimligt fel ser den genom en massiv front.
- **Glasfronten** följer originalet, som är en glasmonter (`--glas`, `s_glas_blender.py`).
- **Bakkanten** sänks under underarmen, till 0,12 m över tråggolvet. Montern är öppen mot personalen (`--bak-lag`). Underarmen gick annars genom kanten.
- **Tråget** får vara så djupt som handen når, 0,62 m (`--trag-max`). Det är djupare än en riktig glassbytta, och det är kroppens mätning, inte montern.
- **Skedens fäste** är mätt om mot den nya scenen: 0,07–0,08 m från fingertoppen.

**h1–h9** (`s_scen5/mening.json`; läge i promille, storlek mot originalet):
- **Sanna:** h1 (17, 0,89), h2 (16, 0,88), h3 95 % (45, **0,71**), h4 (26), h5 (33), h7 (17), h8 med kontakten 100 % (13, 0,95).
- **Falska som i 0027:** h6 (handen över kanten först i slutet) och h9 (lutar sig).

**4. Vad en betraktare ser** (ruta för ruta, 30–65 och 118–145):
- **h3:** Hon böjer sig fram och sticker ned högerarmen i montern genom glaset, och handen rör sig i tråget. Skopandet går att se, men kameran ser henne mer framifrån och mindre (0,71) än originalets vy ovanifrån. Skeden syns knappt.
- **h8:** Hon står upprätt och räcker fram armen mot kameran, och kundens arm (en brun låda) kommer in nerifrån och möter skeden. Det läses som att hon ger provet. Diskens ovansida syns inte i bild, och benen syns genom glaset, så disken läses svagt.

**5.** `STRATEGI.md` har två nya avsnitt: "Roträttning" (0027) och "Kameran" (0028), med synligheten.
**6.** Svar 0027 har satts till `klart`, med bedömning.

## Ändrade eller nya filer
- `r_kamera.py`, `r_synlig.py`, `r_synlig_blender.py`, `s_glas_blender.py`: nya.
- `s_scen.py`: flaggorna `--trag-max`, `--glas`, `--bak-lag`, `--samspel-har-fastet`. Utan flaggor är beteendet oförändrat.
- `g_forvarld/dreamina_t_kam/`, `s_scen4/`, `s_scen5/`, `samspel/dreamina_kam_scen{4,5}.json`, `s_scen/film3*`: utdata. `g_forvarld/prov_*`: provkameror.
- `STRATEGI.md`, `delegat/svar/0027-…md`.

## Kontroll mot "Klart när"
- [x] `film3.mp4` med remsan, där armen och tråget syns i h3: hand och underarm 100 %, tråget 95 %.
- [x] h1–h9 och synligheten i rutorna 45–70.
- [x] 0027 och 0028 `klart`.

## Avvikelser
- **Disken har ändrats, inte bara kameran:** glasfront, sänkt bakkant och djupare tråg. Alla tre är märkta som antagna i planen. Uppdraget nämnde bara kameran, men utan ändringarna syns handen inte från någon kamera som passar originalet.
- **Kvar:** h3:s storlek (0,71) och läge (45 promille). Originalet filmar ovanifrån, närmare. En högre kamera ökar felet, eftersom kroppen står lågt mot disken.
- Inga genereringar och ingen Modal. Kostnad 0. Tid cirka 30 minuter (`tidslogg-0028-0029.log`).
