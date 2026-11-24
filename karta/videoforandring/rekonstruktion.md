# Rekonstruktion: riktigt klipp → manus som motorn spelar

Milstolpen: ett analyserat klipp ska pålitligt bli en 3D-version som återger klippets innehåll (rörelser, personernas plats, kamera, miljö) i grova drag, och **sedan** gå att dra i med reglaget. Rekonstruktionen är basen (5 på reglaget), och vertikalen styr ändringarna.

`npm run rekon -- <id> [<id> …] [--steg …] [--om]`. Kod i `app/rekon/`, data i `data/rekon/<id>/`. Visa i `#rekon/<id>` (original och rekonstruktion sida vid sida, synkade) och dra i `#v/<id>`.

## Stegen

| Steg | Vad | Fil |
|---|---|---|
| `spar` | Rutor i 720 bredd. Personer hittas (COCO-person, ansikten), och Pose körs på en utskuren bild per person, eftersom Pose på hela rutan slår ihop personer som står nära varandra. Färger provtas (överdel, underdel, hud, hår). | `spar.js`, `spar-ra.json` |
| `lokal` | Gemini (3 Flash, låg tänkandenivå, ~5 öre per scen) lägger ut miljön i en nyckelbild per scen: rutor, form, kategori, färg, material, placering, storlek i meter. | `lokal.mjs`, `lokal-2d.json` |
| `platta` | Ren skiva: nyckelbilden utan personer och textning (Gemini 2.5 Flash Image, ~0,4 kr per bild). Kontroll med persondetektorn, och tvätt igen om någon finns kvar. Registreras mot originalrutan med skala och förskjutning, eftersom modellen flyttar bilden lite. | `platta.mjs`, `platta-s<i>.jpg` |
| `manus` | Följning och identiteter, geometri, kamerabana, rörelser, figurer och lokal blir ett manus. | `manus.mjs`, `manus.json` |
| `mat` | Rekonstruktionsgraden: manuset renderas, körs genom samma Se och Tolka som originalet och jämförs. | `mat.mjs`, `jamfor.mjs`, `grad.json` |

## Hur manuset byggs

- **Följning** (`spar.mjs`): spår inom scenen (överlapp, närhet, färg), identiteter över scenerna (färg, aldrig två samtidiga spår). Två nästan lika poser blir en, och en pose vars bål ligger närmare en annan persons ruta hör till den personen. Pose låser annars på grannen när personerna överlappar.
- **Geometri** (`geometri.mjs`): mobilkamera med 68° på höjden. Avståndet till en person räknas ur kroppen: MediaPipes 3D-punkter är i meter, så längden i 3D delat med längden i bild ger avståndet. Kamerans höjd och lutning skattas per scen ur axelhöjd (1,42 m) och anklar (0,08 m), med svaga antaganden (1,45 m, 0°). Kamerabanan är analysens bakgrundsrörelse per ruta, summerad.
- **Skymning:** MediaPipes synlighet gäller inte skymning. Bakom en disk säger den att höfterna syns (0,99) och ritar knäna i höfthöjd. Därför används rimlighet: knän som inte ligger under höften och punkter nedanför personens ruta räknas som dolda, och dolda ben står i vila.
- **Rörelser** (`rorelse.mjs`, skriven av Codex): punkter till 22 ledrotationer (minsta rotation per ben, bål och huvud ur axlar, höfter och öron), utjämnade i tid, med luckor fyllda.
- **Scen-världar:** varje scen ställs upp för sig (origo x = 40 · i), med kameran där den stod i originalet.
- **Lokalen** (`lyft.mjs`, skriven av Codex): Geminis rutor lyfts till 3D med kameramodellen (golvplan, väggplan, ovanpå andra föremål). Den rena skivan projiceras på geometrin från originalkamerans läge, som en diaprojektor. Det som inte syns därifrån får föremålets färg.
- **Antaget** listas i manuset (`antaget`) och visas i `#rekon`.

## Rekonstruktionsgraden

Renderingen körs genom exakt samma analys som originalet, och `jamfor.mjs` (skriven av Codex) ger åtta mått:

| Mått | Vad |
|---|---|
| Rörelser (pose) | Dockornas leder projicerade genom kameran mot originalets punkter (PCK, 0,2 × personens höjd) |
| Personer på plats | Rätt person i bild i rätt ruta (F1) |
| Scengränser | Samma klipp (F1, ±0,2 s) |
| Utsnitt | Samma utsnitt per scen (granne = halvt) |
| Antal personer | Per scen |
| Kamerarörelse | Pan, tilt, roll, zoom per scen |
| Bildens rörlighet | Pixelmåtten (energi, kant, symmetri, entropi, balans) |
| Bildens uppbyggnad | Korrelation per ruta, 18 × 32 gråskala |

Kebab (16,6 s, 3 scener, 2–3 personer):

- 67 % med enfärgad lokal (bildens uppbyggnad 18 %)
- 81 % med projicerad ren skiva (bildens uppbyggnad 76 %, kamera 100 %)

## Agerande som spak

Uttrycksrummet för ett rekonstruerat klipp är **kamera + agerande** (`amp`). `amp` skalar avvikelsen från personens egen medelpose, så det blir samma rörelse men lugnare (0,5–0,85) eller större (1,2–1,7), med tiden oförändrad. Id: `<kamera>~a<amp>`, eller `original~a1.4` för originalets kamera med större agerande.
