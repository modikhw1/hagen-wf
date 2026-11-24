# Videoförändring

> **Från 2 nov 2026 lever den här delen i `video/` (port 5181).** Den började som en ren kopia av `app/`, som nu är wireframen och står fryst. Fokus här är den underliggande funktionen: en inlärning av vad som förändras per klipp (längd, antal scener, hur scenerna sätts ihop, klippets intention). Den ska balansera flera slutmål och samtidigt vara enkel för CM att arbeta i. Reglaget i `#v` är ett mätinstrument. Den färdiga appen ser troligen ut mer som Claude Design, där reglage sitter på enskilda delar av videon. Layouten ändras inte förrän det kommer instruktioner om det. Tänkandet bakom inlärningen finns i [inlarning.md](inlarning.md).

En egen kategori, inte en vy. Den är en mycket abstraherad föregångare till regibordet i hagen-ui och ska senare bakas in i helheten (kundrummet, granskning, anpassning).

Det är ett internt verktyg för att **definiera och kalibrera vertikaler**: dimensioner som ett klipp kan röra sig längs, och som till slut strukturerar backendlogiken.

## Tanken

- **Beskrivning och utformning är olika lager.** Ingest sätter ord på ett klipp för kunden. Utformning är det klippet är byggt av. Roller som hook och punchline används inte.
- **Tio verkligheter.** Samma förutsättningar, tio AI-regissörer som inte känner varandra, där var och en skriver om originalet mot sitt steg på vertikalen. Originalet är ground truth.
- **Värdet mäts, det deklareras inte.** Det mäts på det som renderas, över tid, eftersom en scen kan gå från mycket till lite rörelse.
- **Reglaget byter inte allt.** Mellan två steg stannar de scener vars mätta värde fortfarande håller, och Jev avgör vilka. Det ska inte rycka.
- **Mot ett kreativt rum** (creative bricolage): rörelser lånas från riktiga klipp, och AI-video renderas först i slutet.

## Strukturen, fem lager

1. **Biblioteket (offline).** Scendelning och GVHMR/WATCH ger rörelser (SMPL-X) och kamerabana. Kameran märks med CameraBench-ord. Med tiden blir det en ordbok av riktiga rörelser.
2. **Scenspråket.** Ett manus i JSON (lokal, roller, rörelser och kamera) som three.js spelar deterministiskt. AI:n skriver data, ingen kod.
3. **Regissörerna (offline).** Tio instruktioner ger tio manus. De mäts efteråt och regenereras om de hamnar fel.
4. **Mätmotorn.** Rörelse i bildrymden (lederna projicerade genom kameran), uppdelad på kamera och motiv, som en kurva över tid. Samma kod offline och live.
5. **Väljaren (Jev).** Choice per scen (stanna eller byt) och Score för hur ryckigt bytet blir. En deterministisk lösare sköter siffrorna, Jev sköter omdömet.

## Första vertikalen: kreativ scenografi

- **Låst:** lokal, rekvisita, personal, handling, antal scener och syfte.
- **Rörligt:** kamerans plats, utsnitt, vinkel, rörelse och övergångar, samt hur mycket personerna agerar (`amp`, `tempo`).

## Byggt: spelaren och manuset (del 1 av 5)

`localhost:5180/#v` visar originalet "Nonna smakar" som manus, spelat i 3D. `#vgalleri` visar varje rörelse i ordboken framifrån och från sidan, som ett kalibreringsverktyg.

Kod i `app/src/forandring/`:

| Fil | Vad |
|---|---|
| `motor/skelett.js` | 22 leder i SMPL-ordning, T-pose som vila. Riktig rörelsedata kan läggas in utan översättning |
| `motor/pose.js` | Pose skriven semantiskt (vinklar i grader) eller som kvaternioner per led. Båda blir 22 kvaternioner. `amp` skalar agerandet |
| `motor/ordbok.js` | Rörelseordboken. Handgjorda nyckelposer nu, `kalla` anger var de kommer ifrån |
| `motor/docka.js` | Dockor på skelettet: Marco och Nonna, ansikte, kläder och rekvisita i handen |
| `motor/lokal.js` | Fratellis lokal i meter: disk, ugn, dörr, meny, lampa, deg och pizza |
| `motor/kamera.js` | Utsnitt, mål, vinkel och höjd, plus CameraBench-operationer över scenens tid och deterministiskt skak |
| `motor/kontur.js` | Tecknad kontur i ett pass |
| `motor/spelare.js` | Manus och tid ger bild, deterministiskt. Övergångarna klipp, mjuk, whip och zoom. `stage()` ger ledernas och kamerans läge för mätmotorn |
| `manus/schema.js` | Formatet och `validera()`, som också kontrollerar låsningarna mot originalet |
| `manus/nonna-smakar.js` | Originalet |
| `manus/galleri.js` | Galleriet |

Det första v1–v4 (2D, kamera interpolerad från reglaget) ligger i `_utkast/forandring-v1-v4/` och byggs inte vidare.

## Byggt: reglaget (del 2–4 i en första version)

Reglaget 1–10 under tidslinjen byter scener mellan verkligheter. Varje scenbild visar vilken verklighet den kommer från (siffran), och under scenen syns mätt värde, aktivitetskurva (blå = kamera, svart = motiv) och beslutet (stannar eller 5→8).

| Fil | Vad |
|---|---|
| `manus/regissor.js` | Tio regissörer, skrivna som regler med egen slump. Steg 5 är originalet, mitt på skalan. De skriver om kamera, övergång, `amp` och `tempo`. Handlingen är låst |
| `motor/matning.js` | Rörelse i bildrymden per scen, för kamera och motiv. Skalan kalibreras per scen i tre punkter: lugnast 1, originalet 5, mest rörlig 10. Ogiltiga bilder markeras: kamera i en vägg eller en person, bakhuvud i närbild, motivet syns inte |
| `motor/valjare.js` | En scen stannar om dess värde ligger inom trögheten, annars byts den till närmaste giltiga verklighet. Svaret har samma form som Jevs (Choice med sannolikhet) |
| `motor/lokal.js` | `RUM` och `kameraOk()`: var en kamera får stå |

I testet byttes 2–3 av 5 scener per steg. Bytet tar 1–5 ms, eftersom spelaren bara byter manus och inte bygger om lokal och dockor.

## Byggt: uttrycksrummet och kedjan (31 okt 2026)

Reglaget väljer nu bland uppmätta kamerauttryck (uttrycksrummet, ~7 900 per scen, se [brygga.md](brygga.md)) i stället för bland tio regissörer. Vertikalen heter **Rörlighet**: hur aktiv, rörlig och expansiv bilden är som helhet, mätt med kamera- och motivrörelse, pixelmått (energi, kanter, symmetri, entropi, balans) och ryck.

**Kedjan är enheten.** Alla uttryck i klippet placeras på en gemensam skala (`placeraAlla`), så originalets scener får olika steg, alltså en *profil*. Reglaget flyttar profilen (`malProfil`): på 5 är målet originalet, mot 1 och 10 plattas profilen ut tills alla scener har samma mål. Scenerna väljs sedan tillsammans (`valjKedja`, dynamisk programmering över scenerna) med:

- avvikelse från scenens mål
- tröghet: att byta bort scenens nuvarande uttryck kostar efter hur olika det nya är
- grannar: lågt mål straffar olikhet mellan grannscener (enhetligt), högt mål straffar likhet (variation)
- hem: nära 5 dras varje scen tillbaka till originalets kamera, även efter en omväg
- skyddsräcken: `tillat(i, x)`, där ett otillåtet uttryck aldrig väljs (fylls i steg 3, från biblioteket per position och innehållstyp)

Under scenremsan i `#v` syns kurvan: originalets profil (streckad), målet för reglagets läge och valda steg per scen. Med Jev på väljer Jev bland de närmaste uttrycken för de scener som byts, med scenens mål i kedjan och grannarnas kameror i texten. Kedjans val ligger först bland kandidaterna.

Kod: `app/kalibrering/placering.mjs` (tester i `placering.test.mjs`), vyn i `app/src/forandring/Forandring.jsx`.

## Nästa steg

- Skyddsräcken: Gemini föreslår innehållstyp per klipp, och biblioteket ger vad som klassiskt förekommer per position (öppning, mitt, slut) och typ.
- Bedömningar som tränar rörlighetsmodellen: samma scen, två kameror.

## Öppet

- Hur klipp som inte passar i samma skala ska re-alignas.
- Vilka vertikaler som följer: innehållets innebörd, längd och scenrörelse, och hur de kopplas.
- Avatarer: dockor nu, VRM på samma skelett senare.
- Slutrendering: samma deterministiska spelare i headless, eller HyperFrames.
