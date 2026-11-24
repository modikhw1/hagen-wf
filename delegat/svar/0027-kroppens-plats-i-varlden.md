---
id: 0027
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat (läget när användningsgränsen nåddes)
Alla sökvägar under `scen/3d/gennedbrytning/`.

**1. Var felet sitter** (`r_fel.py`, `g_forvarld/<v>/fel.json`). Projektionsfelet mot dagens 2D-läsning av originalet i varje steg:

| Steg | Dreamina h3–h4 | Dreamina h6–h9 | k2 h3–h4 |
|---|---|---|---|
| A: läsningen genom inversen | 42 promille, storlek 1,04 | 12, 1,00 | 27, 1,26 |
| B: efter rotformeln | 65, 1,21 | 26, 1,10 | 65, 1,43 |
| C: sekvens, stöd och kamera | samma som B | samma som B | samma som B |

- **Det största felet syns inte i bilden, det syns i världen.** Fötterna glider 1,8 m och ändrar höjd med 0,76 m (k2: 1,7 m).
- **Orsaken är planens kamera.** Den står still, med samma läge och fast lins (64 mm) i alla rutor (`varld.npz`: metrisk translation avvisad). Originalets inåkning på 1,9× kan därför bara tas upp av att kroppen åker mot kameran. Rotformeln lägger till 10–20 % i storlek. Tidspassningen och genereringens egen glidning syns i steg A.

**2. Rättningen** (`r_rot.py`):
- **Kroppen** flyttas som helhet per ruta, så att fötterna står still. Det är placering; inga leder kommer ur någon annan läsning.
- **Kameran** får läge (och nu lins) per ruta, löst mot originalets synliga överkropp.
- **Ett fel hittades och rättades:** scenens `till_plats` hade missats. Efter rättningen stämmer den byggda roten exakt med den beräknade.

| Utfall i den byggda scenen (`s_scen3/`) | Före | Efter |
|---|---|---|
| Fötternas glidning | 1,8 m | 0,10 m |
| Fötternas höjdändring | 0,76 m | 0,04 m |
| Läge i bild per segment | 11–73 promille | 14–36 promille |
| Storlek | 1,07–1,25 | 0,89–1,04 (h3 0,68) |

**Kvar:** den lösta kameran sjönk till diskens höjd (z 0,87–0,92 m) i h3–h4, och i ruta 45–70 skymmer diskens kant därför armen och tråget. En ny lösning med låst kamerahöjd (1,3 m), kameran på kundens sida och linsen fri ger 21 promille (h3 43). Den är skriven till `g_forvarld/dreamina_t_rot/`, men **inte byggd eller renderad**. Kamerans väg är skakig (8,8 m).

**3. Skeden** (`r_sked.py`, `r_sked2.py`): skeden hittas i genereringen i 49 rutor. Fästet räknas i den ram som scenen faktiskt använder: skedobjektets världsrotation, alltså sekvensens handled.
- **Avstånd sked–fingertopp:** 0,13–0,15 m före, **0,09 m** efter, i alla segment.
- **Steget är allmänt:** det fungerar för vilken kropp och vilket handföremål som helst som syns i genereringen.

**4–5. Scenen och måtten** (`s_scen3/`, filmen i [s_scen/film2.mp4](../../scen/3d/gennedbrytning/s_scen/film2.mp4), mått i `s_scen3/mening.json`):
- Disken är ljus och tråget mörkt. Kunden syns bara i h8.
- **h1–h9:** sant utom h6 (handen över kanten först i slutet av h6, som i originalet) och h9 (lutar sig fortfarande).
- **h3 är nu sant** (95 %, mot 50 %). Med fötterna låsta står hon rätt mot disken, och disken behöver bara flyttas 0,16 m.
- **h8:s kontakt är 100 %.**
- **Bilden bär det inte än** i ruta 45–70, på grund av kamerahöjden.

**6. k2** (Ray 3.2) med samma rättning, oförändrad:
- **h3–h4:** 64 → 24 promille.
- **h7–h9:** 13 → 28 promille.
- **Totalt:** 23 → 24 promille.
- **Orsak:** k2:s fötter bleknade i början, så ankaret för fötterna är osäkert.

Rättningen kräver alltså en generering med hela kroppen.

**Guacamole S1** behöver tre saker:
- inversen av utzoomningen (62 %) före avbildningens invers i `g_forvarld`
- "sätet står still" i stället för fötterna (han sitter)
- en kamera som knappt rör sig (skala 0,98–1,00), så att kameralösningen nästan bara lämnar linsen

## Bedömning (stängd i 0028)
- Roten är löst för en generering med hela kroppen: fötterna glider 0,10 m mot 1,8 m, och läget i bild ligger på 13–45 promille.
- Kameran är löst som en jämn inåkning (0,73 m, zoom 48–126 mm), och tippningen den hittar (30° i h3) stämmer med originalets egen mätning.
- Skopandet syns i bilden, men först när montern får glasfront och en låg kant mot personalen ([svar 0028](0028-stang-0027-kameran.md)).
- Svagaste ledet nu: kroppen står lågt mot disken (handen 0,6 m under ovankanten). Det ger ett orimligt djupt tråg, och vyn i h3 blir mindre och mer framifrån än originalets.
- k2 bär inte rättningen (fötterna bleknar). Guacamole kräver inversen av utzoomningen och ett ankare i sätet.

## Kvar att göra (utfört i 0028)
1. Bygg och rendera med den nya kameran (låst höjd): `s_scen.py --plan g_forvarld/dreamina_t_rot/plan_sked.json …`. `plan_sked.json` måste göras om ur den nya `plan.json`.
2. Mät om h1–h9 och film2.
3. Uppdatera STRATEGI. Raderna om tidspassning finns redan, roträttningen saknas.
4. Bedömning.

## Avvikelser
- Användningsgränsen nåddes före punkterna 4–7 i sista varvet.
- Modal användes inte. Kostnad 0.
