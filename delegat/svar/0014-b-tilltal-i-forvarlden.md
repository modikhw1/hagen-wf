---
id: 0014
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-12
---

## Resultat
Tio meningar kördes genom tillstånd, Jev (familj, delar, konkret val), regi och snabbvägen (`kompilera(..., snabb=True)`) på `b-tilltal-ravara_n06-hand`. Tre gick hela vägen till bild, och två av dem visar det som begärdes. Jev routade alla tio till rätt familj, men valde fel i två konkreta val (m2, m10). De flesta stopp ligger före Jev: tillståndet saknar begreppen. Kostnad: 30 Jev-anrop, 92 591 inputtokens, cirka 0,004 USD.

| # | Mening | Jevs val | Väntat | Kom till | Saknades |
|---|---|---|---|---|---|
| 1 | Ta bort scen 5. | scen.ordning: ta_bort s5 | samma | bild ✔ | – (r3 "Lærke, hvad tror du…" börjar i s4 och klipps mitt i) |
| 2 | Låt Morten gissa före Mads. | flytta s3 efter s2 (ingen ändring) | flytta s3+s4 först | kompilerad, no-op | regi flyttar en scen åt gången; tavlan är kumulativ (st5–st81) och följer inte ordningen |
| 3 | Byt "Vægt:" i sista scenen… | text.andra: st79, byt | samma | bild ✔ | – (raden bryts i två; st67 i s10 är oförändrad) |
| 4 | Gå närmare Lærke i s6. | kamera.utsnitt: s6, C, nära | samma | bild ✘ | stativ med "nära" ger 64→58,2 mm och 12 cm framåt, alltså ungefär samma utsnitt; inget mått på nuvarande utsnitt att gå närmare från |
| 5 | Ta bort vågen. | prop.andra: saknas, ta_bort | vågen | ej tillämpad | vågen finns inte bland `semantik.props` (bara disk, terminal, hylla, bord) |
| 6 | Byt köttbiten mot en ost. | prop.andra: saknas, byt, typ saknas | köttbiten → ost | ej tillämpad | köttbiten finns i planens `handforemal` men inte i källans props; ingen proptyp "ost" |
| 7 | Låt en fjärde person gissa också. | lagg_till efter s4, mall s11 | ny person + scenpar + tavelrad | avvisad (schema) | ingen person att casta, ingen mall för "ny person gissar"; provets regibyggare följde inte `mall`-schemat |
| 8 | Flytta det hela till en glassbar. | plats.byt: glass_disk | glass_disk | avvisad | "ingen bunden person kan följa med utan ankaret staplats_A": glassmallen har inga motsvarande ståplatser |
| 9 | Gör slutet en sekund längre. | scen.langd: s11 +1,0 s | samma | kompilatorn föll | s11 slutar vid källans slut; `trimma_scen` kan inte gå utanför källintervallet, och det finns ingen håll/frys-op. Hela regin kastas (inte bara editen) |
| 10 | Låt Mads stå med armarna i kors… | person.rorelse: C, s2 | A, s2 | avvisad (schema) | Jev valde Lærke; inget rörelsebibliotek med armar i kors (`bibliotek.id`/`version` saknas) |

Bilder: [m1](../../forvarld/btilltal/ut/bild/m1_fore_efter.png) visar s6 där s5 låg, tavlan stämmer. [m3](../../forvarld/btilltal/ut/bild/m3_fore_efter.png) visar "Rigtig vægt:" i s11, men texten bryts på två rader. [m4](../../forvarld/btilltal/ut/bild/m4_fore_efter.png): före och efter är nästan lika, så bilden visar inte "närmare".

**Vad scenformatet behöver bära** (flest upplåsta först):
1. Föremål som namngivna objekt i källan, även i hand och på disk (våg, köttbit), med typ och byte: m5, m6, delvis m9 (vågens display), m7.
2. Skärmtext som datastruktur (tavla med rader per person och gissning) i stället för 81 lösa överlägg: m2, m7, och m3 utan radbrytningsfel.
3. Scengrupper som enhet ("Mortens gissning" = s3+s4), och flytt/borttag per grupp: m2, m7, m1 (repliken som korsar s4/s5).
4. Ståplatser som roller (person vid disk) och inte som rumsunika ankar-id:n, så att de kan mappas mot en annan rumsmall: m8, m7.
5. Ett nuvarande utsnitt per tagning (avstånd, brännvidd, inramning) som "närmare" räknas från: m4.
6. Tidsändring utöver källan (håll sista rutan, sakta, frys): m9.
7. Ett rörelse- och hållningsbibliotek med id och version: m10.
8. Personer som castbara mallar (ny person från en befintlig rolls rörelser): m7.

**Geometriarbetet från kvällen:**
- Det spelade roll: 0013 (föremål i handen) gör att köttbiten syns i handen i m1-, m3- och m4-bilderna. Jag har inte kontrollerat att kameragrupperna från 0012 bär m4:s stativ.
- Det spelade ingen roll: fokal per klipp, DA3-ram och sidled (0009–0012) ändrade inget av utfallen. Ingen mening stannade på geometri, utan på tillstånd, regi och tidsmodell.
- Notan-vägens antaganden som inte gäller här: ankare per person och rum (m8), ingen kumulativ skärmtext (m2), props bara på möbler (m5, m6), en scen = en handling (m2), slutet får förlängas (m9).

## Ändrade eller nya filer
Nya: `forvarld/btilltal/kompilera.py`, `forvarld/btilltal/bild.py`, `forvarld/btilltal/ut/` (tillstand.json, routning.json, anrop/, anropslogg.jsonl, regi/, plan/, kompilering.json, bild/, cache/). Före pausen: `meningar.json` och `prov.mjs`. Inget ändrat utanför `forvarld/btilltal/`.

## Kontroll mot "Klart när"
- [x] Tio meningar med tidsstämpel (20:57:58Z) före första körningen.
- [x] Tabell: mening, Jevs val, väntat val, hur långt den kom och vad som saknades.
- [x] Före- och efterbild för m1, m3 och m4, med en rad om var och en.
- [x] Lista på åtta rader, ordnad efter hur många meningar varje sak låser upp.
- [x] Tre rader om geometriarbetet.

## Avvikelser
- Prov.mjs byggde fel `mall` för `lagg_till_scen` (m7) och fel `bibliotek` för `rorelse` (m10). Schemat avvisade dem. Jag rättade inte detta eftersom uppdraget gällde mätning; stoppet skulle ändå ha kommit vid tillståndet.
- Stillbilderna är Workbench-renderingar av en ruta (mhr_rig utan `--render`, därefter `-f N`) med planens skärmtext ovanpå. De är inte komponerade över källfilmen.
- Snabb plan har `bildtrohet.flaggad: true` (`ej_kord`) eftersom diagnostiken hoppas över. Inget renderades tyst; jag byggde scen.blend och renderade en ruta.
