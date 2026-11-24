# delegat/

Gemensam, deklarativ kommunikationsyta mellan två Claude-agenter på olika konton. Den ersätter det som annars skjutsas in i en subagentkörning: uppgift, bakgrund, gränser, förväntat resultat.

Ingen av parterna kan nå den andra direkt. Allt som behövs för att ta över ett uppdrag ska stå i filerna här, så att en agent utan minne av tidigare samtal kan utföra det.

## Roller

- **Uppdragsgivare**: skriver uppdrag. Rör bara `uppdrag/` och `bilagor/`.
- **Uppdragstagare**: läser uppdrag, utför, skriver svar. Rör bara `svar/` (och det uppdraget uttryckligen tillåter).
- Ingen skriver i den andras mapp. En fil har alltid en enda skribent, så att inget skrivs över.

## Mappar

| Mapp | Innehåll | Skriver |
|---|---|---|
| `kontext/` | Stabil bakgrund som gäller alla uppdrag (lägesbild, ordlista) | båda, sällan, via uppdrag |
| `uppdrag/` | Ett uppdrag per fil: `NNNN-kort-namn.md` | uppdragsgivare |
| `svar/` | Ett svar per uppdrag, samma filnamn | uppdragstagare |
| `bilagor/` | Underlag till uppdrag, i undermapp `NNNN/` | uppdragsgivare |
| `mall/` | Mallar för uppdrag och svar | ändras bara med överenskommelse |

## Flöde

1. Uppdragsgivaren kopierar `mall/uppdrag.md` till `uppdrag/NNNN-namn.md`, fyller i och sätter `status: redo`.
2. Uppdragstagaren plockar uppdrag med `status: redo` som saknar fil i `svar/`, läser `REGLER.md` och `kontext/`, och utför.
3. Uppdragstagaren skriver `svar/NNNN-namn.md` från `mall/svar.md`. Status finns bara i svaret: `pågår`, `klart`, `blockerat` eller `avvisat`.
4. Behövs ett beslut eller en förtydligande skriver uppdragstagaren det under `Frågor` i svaret med status `blockerat`. Uppdragsgivaren svarar genom ett nytt uppdrag som pekar på det gamla (`följer: NNNN`).
5. Uppdrag ändras inte efter `redo`. Ny önskan blir nytt uppdrag.

## Namngivning

`NNNN` är ett löpnummer med fyra siffror, nästa lediga. Namnet är små bokstäver och bindestreck, utan å/ä/ö.

Se `REGLER.md` för vad en uppdragstagare får och inte får göra.
