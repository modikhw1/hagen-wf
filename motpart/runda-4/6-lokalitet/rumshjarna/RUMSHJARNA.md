# Rumshjärna/1: bildgenerering som hypotes i 0.0 (21 nov)

## Frågan

Hur kan bildgenerering användas i ingesten utan att pipen börjar lita på något som kan vilseleda den? Bilden ska anpassas för pipens svagheter (MoGe, OneFormer, SAM 3D Body). Logiken mellan scener ska ligga i vår kod och inte i modellen.

## Försöket

Steg 1, Due Piani med 4 tagningar och 3 varianter (12 bilder). Prompterna ligger i `promptar/`:

| variant | prompt | vad den gav | pipens läsning |
|---|---|---|---|
| V1 pipe-vänlig (platta färger, grå siluett) | `v1_pipe.txt` | trogen linjering (±7 px) men tecknad stil | lodlinjen **sämre**: S4 −4,7° mot fuserade −7,2°, S8 −58,6° mot −51,3° |
| V2 rum utan förgrund | `v2_rum.txt` | personer, det de håller och text borta; rummet fortsätter trovärdigt | lodlinjen **närmare** den fuserade än originalets egen MoGe i 4/4 (S4 −7,9/−7,2, S6 −10,1/−10,0, S1 −8,0/−8,7, S8 −51,6/−51,3) |
| V3 essens (resten platt grått) | `v3_essens.txt` | behåller person, spis och huv och tar bort golv, väggar och hyllor | rangordningen är rimlig men räcker inte som sanning, se nedan |

Slutsats: **borttagning (V2) är det som håller.** Förenkling i stil (V1) skadar geometrin. Prioritering (V3) kräver förståelse av videon och används inte i flödet än.

Steg 2, återkopplingen (scen 3 ska likna scen 1). S6 genererades mot S4:s V2. Antalet SIFT-inliers mellan rummen S4 och S6 steg från 58 till 148 (originalen ger 127). Modellen flyttade då utsnittet 51 px. Bilden registreras därför tillbaka till sitt eget utsnitt (ECC affin) och resten efter registreringen blir 0,3 px.

Steg 3, allmänt på 5 klipp: 30 bilder på 38 tagningar, alla 30 lyckades. Se `hjarna.py`.

## Flödet (`hjarna.py <klipp>`)

1. **Behov**: bara tagningar där personen täcker minst 2 % av mittrutan. En bild per tagning räcker, eftersom nätet byggs ur mittrutan och andra nyckelrutor redan fyller det de såg.
2. **Rum över tagningar (L7, geometriska bevis)**: varje grupp får ett ankare, den tagning som har minst personyta. Ankarets referens är originalrutan om den saknar person, annars ankarets V2. Övriga tagningar i gruppen genereras mot referensen med `v2_konsistent_allman.txt`. Utan geometriska bevis görs ingen koppling.
3. **Linjering** tillbaka till originalets utsnitt. Om den inte konvergerar används bilden inte.
4. **Observation** med samma MoGe, OneFormer och GeoCalib som originalet (`modal_obs.py::bildobs`).
5. **Andra rösten** (`likhet.py`): geometri och utseende på V2. Utseende ensamt länkar aldrig. Betingade par räknas inte, eftersom deras likhet är skapad av hjärnan själv.

## Grinden i lokaliteten (`lokalitet.py`, regel 1b)

Hypotesen används per tagning bara om alla tre villkoren nedan gäller. Djupfelet och trohet mäts på de ytor som originalet ser, utanför personen:

- djupfel ≤ 12 % (median av |MoGe(V2)·k − MoGe(original)| / djup)
- kanttrohet ≥ 0,4 (korrelation mellan kantbilderna)
- linjeringen registrerad

När hypotesen släpps igenom gäller detta:

- Den fyller bara celler som originalet inte ser och som ingen annan nyckelruta har observerat. Observation går alltid före.
- Personens kärna kräver att hypotesen ligger bakom personens djup. Ringen runt kärnan (vidgning, text, kantpixlar) jämförs mot hypotesen direkt.
- Kantpixlar (hår, ärm) som svävar framför hypotesen blir hål och fylls.
- En observation ur en annan ruta som ligger klart framför hypotesen är personkant i den rutan, inte rum.
- Bitarna märks `tilltro: genererad`. De syns bara i orbit eller när duken är av, på samma sätt som antagna bitar, och räknas inte som observerad bildtäckning i L8.
- A/B: `LOKALITET_UTAN_GENFYLL=1` kör samma kod utan hypotesen.

## Utfall (5 klipp)

| klipp | genererade | släppta | avvisade (orsak) |
|---|---|---|---|
| duepiani | 11 | 10 | S2: närbild där tallriken (motivet) togs bort med personen, linjeringen misslyckades |
| 08burgerkebab | 10 | 8 | S7 djupfel 0,18, S8 djupfel 0,53 |
| babasburgers | 6 | 5 | S1 djupfel 0,20 |
| spanjorskan | 2 | 2 | – |
| kennysgelato2.0 | 1 | 1 | – |

A/B i 3D (babasburgers S5, 08burgerkebab S4, kennysgelato S1): grå antagna siluetter ersätts av rum som fortsätter, alltså bordskant, stålbänk och golv under den liggande kroppen. I Due Piani S4/S6 är väggen bakom personen hel. Grindarna (`test_grindar.py`) håller.

Kostnad: 5 klipp tog cirka 17 min väggtid (generering 12,6 min med 4 parallella, observation 3,4 min). Codex 5h-kvot gick från 13 % till 32 %, alltså cirka 0,6 % per bild. Allt cachas per tagning, så en ny regel kostar sekunder.

## Vad hjärnan inte litar på

- **Utseende som bevis för samma plats.** DINOv2 på babasburgers ger 0,94 för par utan geometrisk koppling, eftersom matnärbilder liknar varandra oavsett plats. Därför länkar utseende aldrig.
- **Betingad likhet.** S6 liknar S4 för att vi bad om det.
- **Bakgrundspersoner.** V2 tar bort alla personer, även gäster vid andra bord (Spanjorskan S1). I 0.0 är de ändå hål idag. Det är en avvägning att ta upp med ägaren.
- **Föremål i handen som är motivet** (tallriken i Due Piani S2). Prompten säger "allt de håller". Grinden fångade det här, men en framtida variant bör behålla föremål som OneFormer ser som egna instanser.

## Öppet

- V3 och prioritering: en väljare som rangordnar instanser bör bygga på egna signaler först (handkontakt L2c, föremål i handen, återkomst över tagningar i samma rum, centrering och skärpa) och ta V3 som en röst bland flera.
- Kandidater för samma plats utan bevis (`likhet.json`, t.ex. babasburgers där samma bordsunderlägg syns i de flesta tagningar) kan prövas igen med L7 på V2, men bara i de områden originalet ser.
- Djupfel med skala och förskjutning (inte bara skala) kan rädda gränsfall som babasburgers S1.

## Omgång 2–3 (21 nov 15–16): oberoende granskning, nya grindar och Codex rättningar

Gemini Neon xhigh granskade alla 30 bilder visuellt (`ut/agy/rumshjarna/GRANSKNING.md`). Grinden hade släppt igenom 8 av 26 som var delvis användbara eller oanvändbara, och **alla 8 var ankarbetingade**: perspektivet hade skiftat, eller innehåll från ankaret hade klistrats in. Av de 16 oberoende bilderna var 14 användbara.

Åtgärder:
1. **Kandidatval** (`hjarna.py`): varje gruppmedlem får både en oberoende och en ankarbetingad bild. Den ankarbetingade väljs bara om den lokala förskjutningen är högst 2 px och inte sämre än den oberoendes, annars väljs den med minst förskjutning.
2. **Grind 1b** fick fler villkor: lokal förskjutning (DIS-flöde på ytor originalet ser, i full upplösning, `rest.py`) högst 3 px, och modellernas relativa djupskala 0,6–1,6. Överlagrad grafik och ogiltiga warp-pixlar räknas inte med.
3. **Codex motprov** (`ut/codex/rumshjarna/MOTPROV.md`) hittade 8 fel och 4 risker, som Codex sedan rättade (`RATTA.md`):
   - proveniensen per triangel
   - fyllnaden ur andra rutor vid kamerarotation (konservativt: nyckelrutor som roterat mer än 0,5° används inte)
   - kravet bakom personen gäller bara personens kärna
   - kantpixlar tas bort bara om även originalet har ett djupsprång
   - cachen nycklas på prompt och indatahashar (befintliga bilder migrerade med `migrera_cache.py`)
   - verkliga bildmått
   - giltighetsmask
   - Modal-fel stoppar körningen
   - betingning läses ur den faktiskt valda källan

Omgång 3, grind mot Geminis omdöme (R2-domen gäller för de utbytta tagningarna):

| grind | användbar | delvis | oanvändbar |
|---|---|---|---|
| släppt (24) | 21 | 3 | 0 |
| avvisad (6) | 2 | 2 | 2 |

- Släppta men bara delvis användbara: 08burgerkebab S1 och S5 (ankarbetingade, påhittat innehåll) samt S6.
- Avvisade fast användbara: Due Piani S3 (mörkt glas, 3,8 px) och S10 (bunken hon håller togs bort, så skalan stämmer inte).
- Grindtesterna håller. Med cache tog en körning av alla 5 klipp cirka 7 min.

Avvägning att ta med ägaren: ankarbetingningen ger konsekventa rum mellan scener (ägarens idé), men 2 av 5 släppta ankarbilder har påhittat innehåll. De oberoende bilderna är tillförlitligare (18 av 19 användbara).
