# Scenskrift `ss/0.1`

Ett JSON-språk som Gemini skriver efter att ha sett ett klipp. Det sätter rum, personer, föremål och kamera i tid. Varje händelse har en tidpunkt i heltal, och rörelser beskrivs som waypoints mellan vilka uppspelaren interpolerar.

## Grundregler

| Regel | Värde |
|---|---|
| Tid | heltal i **takter** (`tick`). Standard 1 takt = 0,1 s. `t: 37` = 3,7 s. Huvudet anger `tick`, så språket kan bli finare (t.ex. 1/30 s) utan att ändras. |
| Precision | Gemini ser bara de bildrutor det samplar. Vid `fps: 10` är 0,1 s verklig observation; finare än samplingen blir interpolation. |
| Plats i bild | `[y, x]` 0–1000 (Geminis eget format för punkter och rutor), y nedåt. |
| Djup | `d` 0–9 inom rummet: 0 = vid kameran, 9 = längst in. |
| Kroppspunkt | höftmitt. `f` = fötternas golvpunkt om de syns, annars utelämnas. |
| Interpolation | linjär mellan två waypoints för samma entitet i samma tagning. Utanför första/sista waypoint finns entiteten inte i bild. |

## Delar

| Nyckel | Innehåll |
|---|---|
| `huvud` | `ss`, `tick`, `langd` (takter), `fps_sedd` |
| `rum` | uppsättningar: `id` (R1…), `typ`, `beskr`, `ankare` (fasta saker med `[y,x]` och `d`), `golv_y` (där golvet möter bakväggen i bild) |
| `roller` | personer: `id` (P1…), `roll`, `utseende` (för att känna igen samma person mellan tagningar), `funktion` i berättelsen |
| `foremal` | `id` (O1…), `typ`, `beskr`, `vikt` (bärande/stöd/bakgrund) |
| `tagningar` | `id` (S1…), `in`, `ut`, `rum`, `utsnitt`, `kamera`, `vinkel`, `takt` (berättartakt), `avsikt` (en mening) |
| `banor` | per entitet och tagning: `av` (P/O-id), `tagning`, `wp`: `[{t, p:[y,x], d, f?, k, v, h}]` |
| `handlingar` | `{t, dur, vem, verb, obj?, mot?}` |
| `repliker` | `{t, dur, vem, till, text}` |
| `textlager` | `{in, ut, text, p:[y,x]}` |
| `kamerabana` | per tagning: `[{t, zoom, p:[y,x]}]`, där bildens mitt pekar (frivillig) |

## Slutna ordlistor

- `k` (kroppsläge): står, går, springer, sitter, böjd, hukar, sträcker
- `v` (vänd): kamera, vänster, höger, bort, eller ett id (P2, O1) när personen tittar på någon eller något
- `h` (händer): tomma, håller, ger, tar, pekar, gestikulerar, arbetar, äter, betalar, telefon, ansikte
- `utsnitt`: detalj, närbild, halvbild, helbild, total, pov
- `kamera`: statisk, handhållen, panorering, åkning, zoom
- `takt`: krok, uppbyggnad, vändning, payoff, avslut
- `verb`: går_in, går_ut, går_till, vänder_sig, sätter_sig, reser_sig, räcker, tar_emot, tar, lägger, håller_upp, visar, serverar, beställer, betalar, ringer, pratar, frågar, svarar, skär, lagar, smakar, äter, väger, reagerar, skrattar, döljer_ansikte, pekar, klappar

## Waypoint-regler (till Gemini)

1. Varje synlig person och varje bärande föremål får en waypoint vid tagningens början och slut.
2. En ny waypoint sätts när punkten flyttar sig mer än 50 enheter, eller när `k`, `v` eller `h` ändras.
3. När en entitet rör sig får det gå högst 10 takter (1 s) mellan två waypoints.
4. Ett föremål som bärs av någon får `h: "håller"` hos bäraren, och föremålets bana följer handen.

## Hur det kompletterar de lokala spåren

YOLO ger täta positioner men ingen identitet över klipp och ingen mening. Scenskrift ger identitet (utseende), kroppsläge, blickriktning, handlingar, berättartakt och avsikt i glesa waypoints. Waypoints kan knäppas fast mot närmaste YOLO-spår vid samma tidpunkt: Gemini sätter namnet, YOLO den exakta platsen.
