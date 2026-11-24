# Utforskning: OpenAI Image-Gen som Geometrisk "Mall" inför 3D-Ingest

Pilot körd 20 nov 2026 via [`scen/3d/gennedbrytning/codex_bild.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/gennedbrytning/codex_bild.py) (`CODEX_RAA=1`) och objektivt mätt med [`arbetsbord/utforskning/mall_pilot/mat_geometri.py`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/mall_pilot/mat_geometri.py). Syfte: testa om bildförenkling till matta arkitektur-/kroppsblock kan agera renad **mall-ruta** vid ingest (ta bort visuellt brus, reflektioner, textöverlägg och i vissa fall slutföra skymd kropp) samtidigt som kameravinkel, perspektiv och posering förblir 1:1.

---

## 1. Testfall & Kvantitativ Mätning ([`matning.json`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/mall_pilot/matning.json))

| Fall | Rå upplösning -> Mall | Körtid | Kvotpåverkan | Kantreduktion | Phase shift `[dx, dy]` px | Grov struktur IoU | Central grad-korr | Diskvinkel rå -> mall |
|---|---|---|---|---|---|---|---|---|
| `guacamole_s1` | `576x1024` -> `941x1672` | 80.5 s | 20 % -> 21 % (primär) | **90.6 %** (`0.0860` -> `0.0081`) | `[0.21, 0.00]` | `0.1371` | `0.0158` | `-0.82°` -> `25.80°` |
| `asketch_s7` | `576x1024` -> `941x1672` | 69.8 s | ~1 % (22 % efter, sek 3 %) | **63.2 %** (`0.0338` -> `0.0124`) | `[-0.01, -0.48]` | `0.2303` | **`0.5661`** | `0.00°` -> `-1.53°` |
| `gelato_s1` | `1080x1920` -> `941x1672` | 56.0 s | 22 % -> 23 % (sek 3 % -> 4 %) | **72.3 %** (`0.0349` -> `0.0097`) | `[-0.24, -1.58]` | `0.2218` | `0.0248` | `0.00°` -> `0.00°` |

*(Metrisk mätning i `mat_geometri.py`: mall-bilden ned-/omskalas först till råbildens bredd x höjd före Sobel-gradient, Canny-kantdensitet och fas-korrelation.)*

---

## 2. Visuell Inspektion ([`kontakt_mall_pilot.png`](file:///C:/Users/praiseworthy/Desktop/hagen-wf/arbetsbord/utforskning/mall_pilot/kontakt_mall_pilot.png))

1. **`guacamole_s1`:**
   - **Vad som städades bort:** Alla hängande vinglas och takställningar, papperslyktor, färgstarka väggmålningar/dödskallar, krukväxter, sugrör, förgrunds-iPad och telefonhållande hand i vänster nederkant, kvittolåda, plastbackar under disken samt den pålagda vita skärmtexten (`"Ursäkta, kommer guacamolen av sig själv?"`).
   - **Vad som bevarades:** Exakt L-formad bardiskvinkel, bakhörn mellan grå matta väggar, takplan samt personens kroppshållning, huvudlutning, armstöd mot disken och telefonhållande grepp (`phase_shift = [0.21, 0.0]` px).
   - **Förklaring till vinkelskift (`-0.82°` -> `25.80°`):** I råbilden dominerade de horisontella glasställen ovanför baren Hough-medianen nära `0°`. När dessa städades bort blev den faktiska perspektivlutande bardiskkanten dominant (`~26°`), vilket underlättar linje-/Manhattan-extraktion.

2. **`asketch_s7`:**
   - **Vad som städades bort:** Hängande julgirlanger, julkulor, glödlampa, förbipasserande fotgängare utanför fönstret samt spegelbilden av kvinnans huvud upp-och-ner i den blanksvarta disken. Pizzaslicen reducerades till ett enkelt matt rektangulärt block på brickan.
   - **Vad som bevarades:** Fönsterkarmens spröjs, kameraperspektiv, kvinnans profil/blickriktning och tray-hållande hand (`central_grad_corr = 0.5661`, `phase_shift = [-0.01, -0.48]` px).

3. **`gelato_s1`:**
   - **Vad som städades bort:** All glass, metallkantiner, smaketiketter (`BANAN MED NUTELLACRISP`, `PISTAGE`, `FERRERO ROCHER`), reflektioner, bakgrundsmaskiner och skärmtext (`"Smakproverna vi ger kunder"`).
   - **Skymd kropp simulerad bakom klarglas:** Bildgenereringen rensade glassdisken till halvtransparenta klarglasribbor och ritade in ben och skor i stående ställning bakom disken, samtidigt som höger arm, axel och övre-högra huvudutsnitt låg kvar mot originalet (`phase_shift = [-0.24, -1.58]` px).

---

## 3. Styrkor, Risker & Ingest-beslut

- **Varför den fungerar för djup & rumspussel:** Kantdensiteten faller med **63–91 %** utan att flytta rumsstrukturen nämnvärt (sub-pixel/1.6 px global shift). För monokulära djup-/normalmodeller (MoGe) försvinner falska djupsignaler från speglingar i blanka diskar (`asketch_s7`), transparenta hängglas (`guacamole_s1`) och textoverlays (`gelato_s1`).
- **Kritisk invändning — syntetiserad anatomi är inte uppmätt ground truth:** I `gelato_s1` var personens underkropp 100 % dold bakom metallkantiner. Att image-gen ritar ben bakom klarglas ger en plausibel *prior* så en pose-detektor kan gissa golvkontakt, men de nya benkoordinaterna är **uppskattade/modellerade antaganden** och måste flaggas som `kalla = "mall_prior"` i ingest-metadata så de inte misstas för observerade bilddata.
- **Observerade tekniska begränsningar i `codex_bild.py`:**
  1. Upplösningen låses till ~`941x1672` oavsett om indata är `576x1024` eller `1080x1920`, så 2D-nyckelpunkter måste alltid normaliseras i `[0, 1]` eller reskalas.
  2. Rollout-detektorn i `.codex.json` matchade en äldre lokal rolloutfil (`rollout-2026-11-20T13-31-09-...`, `prompt_fram.hel = false`, `130` tecken) trots att de tre bilderna faktiskt genererades med fulla prompter (1 302–1 380 tecken) i separata sessioner.
- **Placering i arkitekturen:** Strikt **endast en gång vid tung ingest** (kostnad 56–80 s och ~1 % 5-timmarskvot per utvald nyckelruta, dvs. ~3–6 min för 4–5 representativa nyckelrutor per klipp). **Aldrig** i CM-loopen (`K7`: 0 generativa anrop i redigerings- och förhandsvisningsledet).
