# Kalibrering av vertikaler

Hur en vertikal går från definition till något en modell (och Jev) kan bedöma blixtsnabbt och pålitligt. Varje **central** vertikal kalibreras för sig. **Kombinerade** vertikaler öppnas först när de centrala de bygger på är kalibrerade, så att det går att se vad som kommer från vilken.

Öppna `localhost:5180/#kalibrering`.

## Kedjan

```
riktiga klipp ──► analys (#bibliotek) ──► egenskaper per scen/klipp
                     │ granskning                    │
                     ▼                               ▼
                 rättelser               parvisa bedömningar (#kalibrering)
                 (facit för analysen)               │
                                      ┌─────────────┼──────────────┐
                                      ▼             ▼              ▼
                               tränad modell    Jev (text)    startvikter
                               (Bradley–Terry)  score / par   (definitionen)
                                      └──── överens med människan, på osedda klipp ────┘
                                                    │
                                                 grind
                                                    ▼
                                       kombinerade vertikaler
```

## Vertikalerna

Definieras i `app/kalibrering/vertikaler.mjs`: fråga, ändar, nivåer för Jev, vilka egenskaper som får användas, startvikter och grind.

| Vertikal | Nivå | Enhet | Bygger på mätningen |
|---|---|---|---|
| Kreativ scenografi | central | scen | kamerans rörelse, utsnitt, vinkel, vridning, dynamik |
| Agerande | central | scen | personernas och händernas rörelse i bild |
| Klipprytm | central | klipp | scener per sekund, hopp, utsnittsbyten |
| Energi | kombinerad | klipp | scenografi + agerande + rytm |
| Humor ↔ marknadsföring | kombinerad | klipp | kräver dessutom semantik (vad som sägs och händer) |

## Arbetsprocedur

1. **Granska analysen först** (`#bibliotek`). Ett par klipp per pass. Rätta klipptyper, missade scenbyten och utsnitt. Rättelserna är facit för analysens gränser (`analys/tolka.mjs`); `npm run analysera -- --tolka` tolkar om på sekunder.
2. **Bedöm par** (`#kalibrering` → Bedöm). Två riktiga scener spelas i loop. ← A, → B, ↓ lika, mellanslag hoppar. Paren väljs där modellen är mest osäker, bland scener som bedömts få gånger och helst från olika klipp, så varje svar lär modellen så mycket som möjligt. Svarstiden sparas (snabba svar är säkrare än tvekande).
3. **Titta på skalan** (Skala). Biblioteket i modellens ordning. Ser en scen fel ut på sin plats är det ett bra par att bedöma härnäst.
4. **Läs modellen** (Modell). Vikterna visar vad människans svar har flyttat bort från definitionen. Om en egenskap som inte borde spela roll får stor vikt: antingen fångar mätningen något oväntat, eller så behöver frågan skärpas.
5. **Kalibrera Jev** (Jev). Jev får scenen som text, alltså det som mätts, och vertikalens nivåer. Kör på de bedömda paren och se hur ofta Jev och människan är överens. Skriv om nivåerna, spara och kör igen. Svar sparas per formulering, så jämförelser kostar bara för det som är nytt. Nyckeln ligger i `app/.env.local` och lämnar aldrig servern.
6. **Grinden.** En vertikal är kalibrerad vid minst 150 bedömningar, 20 olika klipp och 80 % överens på klipp modellen inte sett (korsvalidering där bedömningar av samma klipp hålls ihop). Då öppnas de kombinerade vertikaler som bygger på den.

## Varför just så här

- **Parvisa jämförelser i stället för betyg:** människor är mycket mer samstämmiga när de jämför två saker än när de sätter ett tal på en, och svaren går fort.
- **Bradley–Terry på mätta egenskaper:** fungerar med hundratals bedömningar, vikterna går att läsa, och formatet (ett tal per scen) är detsamma som Jevs score. Med tusentals bedömningar kan modellen bytas mot en större utan att datan ändras.
- **Startvikter som definition:** modellen dras mot definitionen när det finns få bedömningar och lämnar den när människan ser något annat. Startvikterna är också baslinjen: tränad modell och Jev ska slå dem.
- **Jev som blixtbedömare:** samma fråga, samma par, ett tydligt mått på överensstämmelse. Jev blir användbar i appen när den håller samma nivå som den tränade modellen på osedda klipp.
- **Text nu, bild senare:** Jev får det som mätts som text. Bildinput (`jev-preview`) är experimentell enligt TypeSafe och prövas när textversionen har en nivå att jämföra mot.

## Filer

| Fil | Vad |
|---|---|
| `app/kalibrering/egenskaper.mjs` | Egenskaper per scen och klipp, och scenen som text |
| `app/kalibrering/vertikaler.mjs` | Vertikalerna och grinden |
| `app/kalibrering/modell.mjs` | Träning, korsvalidering, skala och val av nästa par (`npm run test:kalibrering`) |
| `app/kalibrering/jev.mjs` | Jev-anrop (score och par) med sparade svar |
| `data/bedomningar/<vertikal>.jsonl` | Bedömningarna, en per rad |
| `data/vertikaler.json` | Egna formuleringar av fråga och nivåer |
| `data/jev/<vertikal>.json` | Jevs svar per formulering |

## Begränsningar och nästa steg

- Kamerans höjd, vinkel och djup mäts inte i 2D. GPU-steget (CameraBench-modellen, MegaSaM) kräver att GPU-kvoten i GCP-projektet Hagen höjs (`GPUS_ALL_REGIONS` är 0).
- En bedömare i taget. Med flera kan samstämmigheten mellan människor mätas, och den sätter taket för vad modellen kan nå.
- Humor ↔ marknadsföring kräver semantik per scen (Gemini via Vertex, med analysens scener som ram).
