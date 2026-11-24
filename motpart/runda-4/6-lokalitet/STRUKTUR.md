# struktur/1: rummet som primitiver (variant Ls, 21 nov)

Varför: facit för 0.0 (38 tagningar enligt Gemini, 16 hold-out enligt Codex) visar att rum och objekt brister i nästan varje tagning. Skärvor per pixel faller sönder när kameran vrids. Pipeutvärderingen (`ut/codex/pipeval/PIPEVAL.md`) rekommenderar struktur som första byte.

Kod: `struktur.py <klipp>` läser `ut/<k>/struktur_in/<sid>.npz` (skrivs av lokalitet.py) och skriver `ut/<k>/struktur.json`, `struktur/<sid>.bin` och texturbilden `struktur/<sid>.png`. Inga klippkonstanter. Regler:

- Golvet är planet z=0. Väggar är vertikala plan (RANSAC, riktningen låst till huvudriktningen). Taket blir ett plan om det syns.
- En struktur får aldrig dölja det kameran såg. Plana rumsytor som döljer mer än 10 % av sina synliga hörn förkastas. Väggar går bara till golv och tak när observationerna når dit.
- Möbler blir lådor längs huvudriktningen. Bara föremål som börjar nära golvet går ned till golvet. Syns bara framsidan sträcks lådan bakåt (antaget). Bord blir en skiva med ben.
- Textur: originalets mittruta, och bakom personen rumshjärnans hypotes om grind 1b släppt den. Den används bara där inget ligger framför. Övriga ytor får sin medelfärg och märks antagna.
- Hybrid (efter blint prov 1): allt som inte är rum (föremål, mat, oklassat) behåller Lt:s texturerade nät.

## Blint parvis prov 1 (Gemini, 54 tagningar i 8 klipp, Lt och Ls slumpade som X/Y, nyckeln utanför arbetsmappen)

Inga regler justerades mot provet.

| | Ls bättre | Lt bättre | lika |
|---|---|---|---|
| från originalkameran | 0 | 53 | 1 |
| rummet vid vridning | 44 | 4 | 6 |
| föremålen | 3 | 6 | 45 |
| helhet för att regissera om | 39 | 8 | 7 |

God nog: Ls 36 delvis och 18 nej. Lt 54 nej. Ls förlorade 0°-vyn på enfärgade block och förenklade föremål, vilket ledde till hybriden ovan. Prov 2 kör hybriden.

## Prov 2 och 3

Prov 2 (Gemini, hybrid): rum Ls 39 / Lt 12, helhet Ls 30 / Lt 16, originalkameran Lt 53 / lika 1. Lt var oförändrad men fick 8 "delvis" mot 0 i prov 1. Domarens brus är alltså ungefär ±8 per kategori.

Därefter två ändringar, båda allmänna:
- Varje triangel som ligger klart framför det kameran såg skärs bort. Tidigare gällde det bara väggar och tak.
- Antagna ytor (utan textur) döljs från originalkameran, där bakgrundsduken visar originalets pixlar. Samma regel som för fyllnaden bakom personen.

Prov 3 (Codex gpt-6.2-astra xhigh, eftersom Neons kvot var slut och Argon gav 503; ny slumpning):

| | Ls bättre | Lt bättre | lika |
|---|---|---|---|
| från originalkameran | 0 | 23 | 31 |
| rummet vid vridning | 48 | 4 | 2 |
| föremålen | 8 | 16 | 30 |
| helhet för att regissera om | 39 | 13 | 2 |

God nog: Ls 38 delvis och 16 nej, Lt 13 delvis och 41 nej. Ingen är god nog fullt ut.

Slutsats efter tre blinda prov med två domare: struktur är klart bättre för rummet och för att regissera om. Bilden från originalkameran är nu i nivå med Lt eller något sämre. Föremålen är det som återstår: form, kontakt och plan som skär genom maten. Efter prov 3 ställs små föremål på sin stödyta (kontakt_dz, ±3 cm i praktiken). Prov 4 väntar på en domare.

## Föremål med SAM 3 (21 nov, kl. 20)

Ägaren beställde SAM 3.1 och fick åtkomst hos Meta kl. 20.07. Repot `facebook/sam3.1` innehåller bara Metas egen checkpoint och inga transformers-vikter. Därför kördes `facebook/sam3` via transformers 5.24 (`Sam3Model`). För enskilda bilder är skillnaden liten; 3.1 tillför främst spårning i video.

- `modal_sam3.py`: 24 begrepp (mat, kärl, möbler) i mittrutan per tagning. 8 klipp tog 114 s. Utdata ligger i `ut/<k>/foremal_sam3/`.
- Referens med Grounding DINO + SAM 2.1 (Apache, `modal_foremal.py`): 1–12 föremål per bild mot 10–50 för SAM 3. SAM 3 tar dessutom med tallrik, disk, sås och pannor, och räknar inte sedeln som föremål.
- I struktur.py:
  - Varje SAM 3-föremål blir en skärva ur originalets djup, så att 0° blir exakt. Det ställs på sin stödyta och får en kjol ned till den, för volym och kontakt.
  - Pixlarna delas exklusivt: den minsta masken vinner, så mat går före tallrik och tallrik före bricka.
  - Bord, disk, stol, pall och bänk från SAM 3 blir lådor och ersätter de OneFormer-möbler de täcker.
  - Resten (det som syns och inte är person, rum eller föremål) blir en egen skärva.
  - Hybriden med Lt-bitar används bara när SAM 3 saknas.
- Licens: SAM License (Meta), där vikterna kräver godkännande. Den måste stämmas av innan produktion.

Blint prov 4 (Ls med SAM 3 mot Lt) pågår.

## Prov 4 (Argon, Ls med SAM 3 mot Lt)

| | Ls bättre | Lt bättre | lika |
|---|---|---|---|
| från originalkameran | 0 | 25 | 29 |
| rummet | 51 | 2 | 1 |
| föremålen | 32 | 4 | 18 |
| helhet | 49 | 3 | 2 |

God nog: Ls 9 ja, 29 delvis och 16 nej, de första "ja" i något prov. Lt 2 delvis och 52 nej. Domaren var Argon, eftersom Neons kvot var slut. Argon kan vara sämre, så resultatet ska vägas därefter.

Därefter två allmänna rättningar för originalkameran:
- Föremål flyttas inte för kontakt. Kjolen sluter mot stödytan.
- Rumsytor får aldrig textur från föremålspixlar. Det gav dubbla kärl i 0°.

Prov 5 (Argon) pågår.

Öppet:
- Överlagrad grafik (sedlar, bildtext) blir 3D. Begrepp som "text" och "logo" skulle också fånga riktiga skyltar.
- Mat i förgrunden projiceras på lodräta lådor (Spanjorskan).
- Taket skymmer i helrumsvyn.
- Rörelseoskärpa (08burgerkebab S8).

## Prov 5–6 och Codex rättningar (21 nov, kl. 21–22)

Prov 5 hade två domare på samma bilder. Argon: rum Ls 34 / Lt 19. Codex 6.2 astra: rum Ls 41 / Lt 12, föremål 21 / 15, originalkameran Ls 3 / Lt 21. Lt var oförändrad men fick 2 "delvis" av Argon i prov 4 och 18 i prov 5, så Argon är brusig. Codex används som jämförelsedomare.

Codex kodgranskning (`ut/codex/struktur_granskning.md`) gav 11 fel och 5 risker. Codex rättade dem (`ut/codex/struktur_ratta.md`):
- djupsprång mäts från kameran
- projektiv textur per fragment
- stol och `antagen_djup` maskeras och döljs
- pixlar förbrukas först när föremålet har byggts
- förklarad yta räknas på accepterad geometri
- möbelalias ger inte dubbla lådor
- golvregeln gäller även bord och stolar
- maskmått kontrolleras mot metadatan
- NMS använder IoU
- ingen dold takprior
- areafiltret beror på begreppet
- SAM 3 räknar bilden en gång per ruta (8 klipp på 35 s, tidigare 114 s)

Prov 6 (Codex 6.2 astra, samma domare som prov 5):

| | Ls bättre | Lt bättre | lika |
|---|---|---|---|
| från originalkameran | 13 | 5 | 36 |
| rummet | 42 | 10 | 2 |
| föremålen | 17 | 17 | 20 |
| helhet | 37 | 16 | 1 |

Ls 1 ja, 36 delvis och 17 nej; Lt 17 delvis och 37 nej. Ls är nu minst lika bra som Lt i alla fyra kategorierna och vinner för första gången även från originalkameran.

Efter prov 6: möbler mäts bara på pixlar som inget föremål gör anspråk på, och bordsskivans höjd tas ur vågräta ytor. Bordsskivan låg tidigare över tallriken. Prov 7 (Neon, Argon som reserv) startar kl. 22.51.

## Sittande kroppar (kontakt/1, `kontakt_sittande.py`)

Mätning i paket_L: stående har fötterna på cirka 0,08 m i alla klipp (L2b), bäckenet på 0,85 m och huvudet på 1,55 m. Sittande har fötterna mellan −0,36 och +0,28 m, alltså under golvet eller svävande.

Regel:
- Sittande kroppar skalas kring kamerans centrum (J' = C + s(J − C)) så att den lägsta foten hamnar på 0,08 m. Projektionen i originalkameran behålls exakt, och bara avstånd och storlek ändras.
- s begränsas till 0,75–1,33. Utanför spannet flaggas spåret som opålitligt och lämnas orört (Babas S2 är en närbild med delvis synlig person, Chickenstreet S5 p1 ett skräpspår).
- Utfall: s mellan 0,77 och 1,12. Resultatet skrivs till `paket_Ls.json`, som Ls-vyn använder.

Stolshöjd som andra villkor (bäckenet på sitsen) är nästa steg. SAM 3:s "chair" ger stolens topp, inte sitsen.

## Prov 7–8 (Claude som domare, plus Neon i prov 7)

Prov 7, efter Codex rättningar och bordsskivan under föremålen:
- Claude: originalkameran Ls 23 / Lt 1, rum 39 / 4, föremål 25 / 7, helhet 39 / 4. God nog: Ls 5 ja, 40 delvis, 9 nej. Lt 17 delvis, 37 nej.
- Neon: originalkameran 25 / 7, rum 30 / 19, föremål 18 / 10, helhet 30 / 15. Neon är strängare på god nog (Ls 12 delvis).

Efter prov 7 gjordes fem ändringar:
- smådelar och enstaka pixlar visas bara från originalkameran
- taket döljs i fri kamera
- antagna ytor gjordes halvgenomskinliga
- generösare texturkrav för möbler
- sittande kroppar fick kontakt med golvet

Prov 8 (Claude): god nog för Ls föll till 0 ja, 34 delvis och 20 nej, medan Lt var stabil. Skälen ("golv och bord saknas", "genomskinliga bänkar") pekar på att halvgenomskinliga antagna ytor ser ut som tomrum. Neon klagade i stället på enfärgade block; det är två sidor av samma avvägning. Därför är de antagna ytorna opaka igen. Prov 9 (Claude) prövar det.

Prov 9 (Claude, opaka antagna ytor igen; domaren använde kontaktark och var strängare mot båda): originalkameran Ls 12 / Lt 0 / lika 42, rum 39 / 6, föremål 21 / 4, helhet 36 / 5. God nog: Ls 6 ja, 28 delvis, 20 nej. Lt 12 delvis, 42 nej. Förhållandet mellan Ls och Lt är detsamma som i prov 7.

## Läget 21 nov kväll

Nio blinda parvisa prov med fyra domartyper (Gemini Neon, Argon, Codex 6.2 astra och Claude) ger samma riktning. Ls vinner rummet i alla prov, och efter SAM 3 och Codex rättningar vinner Ls eller är lika även för föremålen och från originalkameran.

Kvarstående, i den ordning domarna nämner dem:
1. Bord med mat försvinner vid vridning i cirka 10 tagningar, när brickans eller bordets mask och djup inte ger någon stödyta.
2. Dolda sidor blir platta, otexturerade färgytor.
3. Textöverlägg (bildtext, sedlar) ligger kvar och blir 3D.
4. Mörka bilder och rörelseoskärpa (blackstone, 08burgerkebab S8) går inte att använda i någon variant. Ingesten borde välja en skarpare ruta.
5. Pipens egen dom (L8) är inte kalibrerad mot det här.

Domarnas brus är ±5–10 per kategori. Jämför därför bara inom samma domare.

## Prov 10 (Neon och Codex; orbit kring motivet)

Fri kamera kretsade kring medelpunkten av alla bitar. I Ls, med stora plan, hamnade den långt in i rummet, så närliggande bord svängde ut ur bild ("bordet med mat försvinner"). Nu kretsar den kring motivet: medianen av föremål och personer, annars kamerans mittaxel på medianddjup. Punkten kommer från struktur.py och används för både Lt och Ls.

| | Neon prov 10 (prov 7) | Codex prov 10 (prov 6) |
|---|---|---|
| rum Ls/Lt | 38/12 (30/19) | 50/3 (42/10) |
| föremål | 23/14 (18/10) | 28/16 (17/17) |
| helhet | 39/14 (30/15) | 48/5 (37/16) |
| originalkameran | 26/8 (25/7) | 6/27 (13/5) |
| god nog Ls, ja+delvis / nej | 32/22 (12/42) | 44/10 (37/17) |

Domarna är oeniga om originalkameran. Codex skäl var att Lt är något skarpare framifrån och att en lila antagen bänkskiva täckte pannan. Därefter skärs otexturerade rumsytor bort där de bara syns genom föremål (kjolen sluter). Prov 11 pågår.

Självbedömning (`sjalvbedomning.py`, korsvalidering per klipp, 54 tagningar): starkast är låg skärpa och mörk bild, därefter förkastade väggar och många föremål. Vid 0,5 flaggas 17 tagningar och 10 av 21 "nej" fångas. L8 "hög" ger för Ls 13 tagningar, varav 2 nej. Nästa allmänna steg: välj den skarpaste rutan i mittentredjedelen av tagningen.

## Prov 11 och skärpa från originalkameran

Prov 11 (efter att otexturerade rumsytor genom föremål tagits bort):
- Neon: rum 45/5, föremål 29/9, helhet 44/6, originalkameran 24/7. God nog Ls 31 delvis, 23 nej.
- Codex: rum 48/5, föremål 31/13, helhet 46/5, originalkameran 8/25. God nog Ls 43 delvis, 11 nej.

Codex föredrog Lt från originalkameran för att den var "skarpare framifrån". Mätt med Laplace på 0°-bilderna var Ls i median cirka 10 % suddigare, eftersom texturen samplades med mipmaps. Lt:s videotextur har inga. Nu laddas Ls-texturen utan mipmaps och med linjärt filter. Efter ändringen är medianen Ls 1 068 mot Lt 953, och Ls är skarpare i 31 av 47 tagningar. Prov 12 pågår.

## Prov 12 och rumstextur (22 nov, natt)

Prov 12 (Codex, efter rättningen av skärpan): originalkameran Ls 21 / Lt 14 (tidigare 8/25), rum 45/8, föremål 34/13, helhet 45/7. God nog Ls 43 delvis, 11 nej; Lt 8 delvis, 46 nej. Ls vinner alla fyra kategorierna. Neon hade ingen kvot kvar.

Codex huvudinvändning: "golv och bord tar slut under föremålen". Det var hålregeln från prov 10. Nu har rumsytorna en egen textur (`struktur/<sid>_rum.png`) där föremålspixlarna är ifyllda ur omgivningen (Telea). Bänken under pannan och brickan under burgaren blir då hela och ser ut som sin omgivning. Föremålen behåller originalets pixlar. Hålregeln är borttagen. Prov 13 (Codex) pågår.

Prov 13 (Codex): originalkameran Lt 40 / Ls 6, en försämring. Rum 47/6, föremål 30/13 och helhet 44/7 höll. Rumsytan som bara syns genom föremål var texturerad men inte märkt som antagen, så den låg över pannorna framifrån. Nu märks den delen som antagen och döljs från originalkameran (samma regel som all antagen geometri). Prov 14 (Codex) pågår.
