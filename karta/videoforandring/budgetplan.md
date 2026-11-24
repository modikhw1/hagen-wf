# Harnessen v5 med 50–150 dollar (4 nov 2026)

Pengarna räcker långt till modellanrop. Det som är dyrt är ägarens tid. Strategin är därför att låta modellerna göra så mycket som möjligt billigt, och att ägarens intervjuer bara används där de ger mest information per minut.

## Kostnad per enhet
Priserna är Gemini 3.1 Pro preview från `typer/gemini.mjs`: cirka 2 dollar per miljon tokens in och 12 dollar ut. Tokenmängderna är uppmätta. 1 dollar ≈ 10,5 kr.

| Enhet | Tokens | Kostnad |
|---|---|---|
| Formatkort v5, Pro på video | ~11 500 | ~0,05 $ |
| Kundlinje, 10 klipp i en fil, Pro | ~34 000 | ~0,11 $ |
| Matchning eller anpassning, text, Pro | ~15 000 | ~0,06 $ |
| Lite-lager (sållning), 3.5 Flash-Lite | ~4 800 | < 0,001 $ |

Om Vertex batchläge stöds för modellen halveras priset. Det kontrolleras först.

## Varför jämförelsedatan begränsar
- **35 bedömningar ger en felmarginal på rho kring ±0,18.** Skillnaden mellan v0 (0,18) och v5:s grundvärde (0,59) syns, men en skillnad på 0,1–0,2 mellan två varianter gör det inte.
- **Matchningen syns bara inom klipp.** Hos de åtta klipp som visades för flera kunder står kunden för en tredjedel av variansen, och i pass 4–5 finns bara ett tiotal sådana jämförelser. Ett korsat urval ger 20–25 per pass.
- **Ägarens eget brus är okänt.** Utan omtest går det inte att veta hur högt modellen alls kan nå.
- **Ägaren är enda facit.** Utfallen i E4 är ett andra facit som inte kostar ägarens tid, men de mäter räckvidd och inte LeTrend-värde.

## Nivå 1: cirka 50 dollar
| # | Vad | Varför | Kostnad |
|---|---|---|---|
| 1 | Gör klart v5: 32 kort, 5 kundlinjer, matchning, Pro som CM, anpassningar | Grunden för allt annat | ~3 $ |
| 2 | Omtest av v5-lagren: 30 klipp × 2 extra körningar | Vilka nya lager är stabila? Krippendorffs alfa, som i E1 | ~3 $ |
| 3 | **Större bibliotek:** Lite sållar cirka 4 000 nya klipp ur banken (123 konton), Pro v5 på de bästa 400 | Kärnhyllan var för liten, så samma sketcher återkom hos alla kunder | ~2 $ + ~20 $ |
| 4 | **Andra facit:** Pro v5 på 300 klipp ur E4, stratifierat per konto | Förutsäger grundvärdet räckvidd inom konto, oberoende av ägaren? | ~15 $ |
| 5 | Pass 6 och 7: kundlinjer för 6 nya kunder, matchning och låsta prognoser | Testet | ~2 $ |
| | | | **~45 $** |

## Nivå 2: cirka 100 dollar (nivå 1 plus)
| # | Vad | Varför | Kostnad |
|---|---|---|---|
| 6 | **Modelljämförelse** på 46 klipp med ägarens omdömen (27 kalibreringsklipp och 19 ur pass 4–5): 3.1 Pro, 3.8 Flash, 3.5 Flash-Lite, Argon och andra som tar video via API, 2 körningar var | E1 visade att modellvalet väger tungt och formuleringen knappt alls. Mått: överensstämmelse med ägaren, omtest och kostnad | ~15–25 $ |
| 7 | **Perception på Vertex direkt:** 1, 2 och 4 bilder per sekund, mediaResolution, 2×2-rutnät. 40 klipp × 3 inställningar | Lovable skickade aldrig fps vidare, så allt hittills är sett med 1 bild/s. Krok (0,26), eskalering (0,46) och redigeringsskämt (0,31) är svaga lager som kan vara ett perceptionsproblem | ~15 $ |
| 8 | **Självkonsistens:** 3 körningar per bibliotekskort, median för de värderande lagren | De värderande lagren brusade kring 60 % i omtest | ~10 $ |
| | | | **~95 $** |

## Nivå 3: cirka 150 dollar (nivå 2 plus)
| # | Vad | Varför | Kostnad |
|---|---|---|---|
| 9 | Pro v5 på hela E4 (1 322 klipp) | En kalibrerad modell från lager till ägarens passform, med korsvalidering. Ägaren är målet och utfallen ett hjälpmål | ~50–65 $ |
| 10 | **Två varianter av anpassningen** för 20 klipp och kund, som ägaren jämför parvis | Avgör om v5-anpassningen är bättre än v0, och vilken form som håller | ~3 $ |
| | | | **~150 $** |

## Intervjuerna (ägarens tid, cirka 2,5 timmar)
| Pass | Längd | Vad | Ger |
|---|---|---|---|
| **6, test** | 45 min | 3 nya kunder × 6 klipp, korsat: 4 klipp visas för alla 3. 4 klipp från pass 4–5 visas igen. 3 anpassningar v5 | Låst test av v5, cirka 12 jämförelser inom klipp, **ägarens omtest** (bruset) |
| **7, parvis** | 30 min | 40 par: "vilket är det bättre biblioteksklippet?", valda där v5 är osäker (aktiv inlärning) | Grundvärdet som Bradley–Terry direkt från ägaren (H16 prövat på ägaren, inte på Pro) |
| **8, kundlinjer** | 15 min | Ägaren bekräftar eller rättar punkterna under "att bekräfta" för 6 kunder | Hur ofta linjen är fel, och vad CM måste fråga |
| **9, test** | 45 min | Som pass 6 med 3 andra kunder och anpassningar A mot B | Replikering och anpassningsformen |
| (frivilligt) | 45 min | En CM bedömer samma klipp som i pass 6 | Om två personer är överens, och hur högt det alls går att nå |

Miles får tre ändringar:
- Klippets innehåll sägs med numret.
- Första repliken säger att klippet ska bedömas för kunden, inte för den som gjort klippet.
- Speglingen används bara när ett svar är oklart.

## Ordning och disciplin
1. Gör klart v5 (nivå 1, steg 1–2) och utvärdera på utvecklingsdatan.
2. Skriv en förregistrering för pass 6 och lås prognoserna. Kör sedan pass 6.
3. Kör steg 3, 4, 6 och 7 parallellt med passen. De kostar inte ägarens tid.
4. Lås pass 9 efter att v6 byggts på det pass 6–8 lärt. Pass 9 är det andra testet.
5. Klipp som ägaren sett räknas aldrig som test. Prognoserna låses innan passet.

## Vad som kan gå fel
- **Argon är okänd.** Den tas med om den tar video via ett API till ett känt pris. Annars hoppas den över.
- **Ägarens egen drift.** Andelen nej till biblioteket gick från 60 till 29 % mellan pass 1 och 3. Omtestet i pass 6 mäter det.
- **E4-utfallen mäter räckvidd, inte LeTrend.** De används som ett andra facit och aldrig som ensamt facit.
