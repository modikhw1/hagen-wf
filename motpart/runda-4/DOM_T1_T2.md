# Dom: T1 mot T2 (20 nov 2026, orkestratorn)

Två Opus-agenter på xhigh läste ägarens ord (`AGARENS_ORD_20NOV.md`) oberoende av varandra. Underlag: `T1-tolkning/TOLKNING.md` och `T2-tolkning/TOLKNING.md`. Stickprov på citat: T1 5/5 och T2 5/5 håller. T2:s rad om fri text står på rad 391 och inte 392.

## Står (oberoende samstämt)
| # | slutsats | T1 | T2 |
|---|---|---|---|
| S1 | Styrsignalen är ägarens val, inte hans ord. Smaken träffar publiken 20/26, orden 9/19. | `k1-del1.md:25`, `essens.md:73` | samma |
| S2 | Embryot finns i `byggsten/hand` (handflata, fingrar, `rutt.py`, `anpassa.py`). Ingen människa har bedömt det. | §3 | `README.md:17,249` |
| S3 | Mellanläget är ett prov på pipen, inte produkten ("ett klipp i mitten, fingrar utåt", 14 nov). | rättelse 1 | punkt 3 |
| S4 | Mush går att mäta. Medelvärdet ligger nära riktiga klipp men tappar särprägel. Därför godkänner "nära riktiga klipp" ensamt mush, och det krävs två villkor. | 0,81–0,83 behållet | −32 % särprägel |
| S5 | Kompromissen uttrycks deterministiskt som val av vem som härmar vem, block för block, med krav på verkliga grannar. Experten styr genom att ändra en post i vektorn. | ≤ 2 drag/steg | −1,5 %, 82 % nära verkligt |
| S6 | Sidospår för just denna fråga: kärnans attityd, rumsmått i cm, G1–G7, Kimodo, arbetsbord v2. | §7 | punkt 11 |

Varning för S4–S5: båda proven är byggarnas egna mått på 2 bilder/s, alltså diagnos och inte dom.

## Fäller eller svagt
| # | invändning | träffar |
|---|---|---|
| F1 | Rummet ser inte ägarens egna exempel (lokal, talare, mat, energi). Experimenten prövar ett abstrakt rum, inte "talking head byter lokal". | båda; T1 erkänner (§4 rad 156) |
| F2 | Att snäppa mot en verklig granne ger någon annans klipp, inte A förändrat. X1 och E2 prövar återvinning, inte omvandling. | båda; T1 erkänner |
| F3 | Datagrunden är 240p med 2 bilder/s och originalen är raderade (`overlamning-17nov.md:66`). Rörlighet, ägarens första dimension, kan inte mätas. | T1 hittade det, T2 missade det |
| F4 | Tillförande ändringar (ny lokal, ny talare) kräver generering eller fungerande 3D. Generering är spärrad (K7, "generativt bara för 1:1") och 3D är trasig. Ingen av dem löser det; båda lämnar det till ägaren. | båda |
| F5 | Orkestratorns `runda-4/UPPDRAG.md:6` och panelens innehåll utgår fortfarande från meningsvägen. Metoden (blint val med kontrollpar) håller. | T2 §2.4 har rätt |

## Fynd värt att lyfta (T2)
Modellfria mått känner igen **kontot** väl (0,116 mot slump 0,012) men knappt **typen** (0,442 mot 0,388). Tolkning (antagande): utan modell ser måtten vem och var, alltså "etnicitet och personlighet", men inte vad, alltså meningen. Det som bär mening kräver en läsare med uppmätt pålitlighet (T2:s starkaste invändning, talsegment +0,15). Det ger en naturlig delning: dimensioner för identitet mäts utan modell, dimensioner för mening kräver en läsare, och de mäts inte på samma sätt.

## Sammanslagen väg (förslag, ej beslutat)
1. **Datagrund:** hämta om ett urval (~200 klipp) i ≥ 8 bilder/s från url:erna i korten. 0 USD. Förutsättning för rörelsedimensioner. (F3)
2. **Panel 2 (domaren):** trioval på verkliga klipp, "vilken liknar mest" och mush mot flyttad mot omöjlig kombination. T1:X1 och T2:E1 sammanslagna. Fälls enligt T1:s kriterium (≤ 4/12). (S4, S5)
3. **Ett reglage som går att utföra idag:** "långsammare" eller annan energi via medielagret (tempo, klipp, ljud), deterministiskt, mätt om efteråt och blint ordnat av ägaren. T1:X2 och T2:E3. Det enda av ägarens exempel som går utan 3D och utan generering. (F1, F4)
4. **Ägarbeslut:** får en låst, deterministisk recept-sida styra generativ rendering för tillförande ändringar (ny lokal, ny talare)? Annars kräver de en fungerande 3D, och den finns inte. (F4)
5. **Rätta UPPDRAG.md** så att runda 4 mäter riktningar i rummet, inte meningar. (F5)

---

## Tillägg 20 nov kl. 21: T3 (GPT-6-astra xhigh, `T3-codex/GRANSKNING.md`)

T3 granskade T1, T2 och den här domen ur representationsinlärning och mätteori. Orkestratorn verifierade huvudfyndet genom omkörning (`T3-codex/robusthet.py`, exit 0, samma tal).

### Det som ändras i domen
| tidigare | nu | skäl |
|---|---|---|
| S4 "mush går att mäta" | **fallit som slutsats**, kvar som hypotes | Ett medelvärde av två centrerade vektorer har förväntad norm ≈ 1/√2 ≈ 0,71 av ändpunkternas utan att någon video finns. T2:s −32 % och T1:s 0,81–0,83 är till stor del geometri. Avstånd från mitten mäter att klippet är ovanligt, inte att det är distinkt eller sammanhängande. Motexempel: A′ = B′ kan ha hög norm men noll inbördes distinktion. |
| S5 "vald korsning bevarar särprägel, 82 % nära verkligt" | **svagt** | En slumpkorsning bevarar normen av algebraiska skäl. Talet 82 % är bästa av 64 masker mätt på samma bank, och tröskeln är medianen, så hälften av riktiga klipp hamnar på fel sida per konstruktion. |
| T2:s fynd: kontot 0,116, typen 0,442 | **kontot halveras till 0,058** | `diagnos_modellfri.py:78` `argsort(argsort())` ger lika värden olika rang, och raderna ligger i kontoordning (90 % av grannraderna har samma konto). Med medelrang blir kontot 0,058 och typen 0,446. Kontot ligger fortfarande över slumpen 0,012. |
| Orkestratorns delning "modellfritt = vem/var, läsare = mening" | **dras inte ur dessa tester** | Typen +5 procentenheter är varken noll eller en gräns. "Modellfritt" ska heta "utan fri LLM-tolkning", eftersom Silero och YOLO är modeller. Liknelsen med etniciteter föreskriver ingen tvådelning. |
| S1 "ord bär inte" | **för absolut** | Ägaren kan inte artikulera allt, men det betyder inte att ord saknar informationsvärde. |

### Det som står kvar
S2, S3, S6 och F1–F5 står. T3 skärper F2: diagnoserna producerar vektorer, inte ändrade klipp.

### T3:s viktigaste poäng
Representationen ska först tåla irrelevanta förändringar, som omkodning, upplösning och ljudnivå. Den ska också kunna styra en faktisk, begriplig ändring av **samma** innehåll innan geometrisk särprägel får kallas skydd mot mush. Lovable-provet är en fråga om beslutsförmåga: väljer systemets förinställda policy åtgärder som kräver färre rättelser än en enkel konstant regel?

### Konsekvens för steg 2–3 (förslag, ej beslutat av ägaren)
- **Steg 2** byts från trioval över vektorer till **T3:D1, invarians**: försök förstöra mätaren utan att ändra innehållet. Ta 12 klipp ur steg 1:s datagrund, gör omkodningar, ändrad upplösning och ljudnivå, och lägg till en verklig tempoändring som positiv kontroll. Förbehandlingen fryses på referenskonton. Mätaren fälls om de tekniska ändringarna flyttar den lika mycket som tempoändringen gör.
- **Steg 3** byts till **T3:D2, ömsesidigt ingrepp**: 6 par ur osedda konton. En fryst förinställd policy ändrar både A och B mot varandra och från varandra, i medielagret med pauser och klipprytm. Den jämförs blint mot originalen och mot en konstant regel med samma redigeringsbudget. Det är faktiska ändrade filer, inga grannar. Ägaren bedömer riktning, avsikt kvar, sammanhang och antal rättelser.
