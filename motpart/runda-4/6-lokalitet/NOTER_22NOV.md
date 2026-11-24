# Noter: läget för 0.0, 22 nov kl. 01

Det här är en sammanfattning av vad som gjorts 21–22 nov och var vi står. Detaljerna finns i `STRUKTUR.md` (struktur och alla blinda prov), `rumshjarna/RUMSHJARNA.md` (genererat rum), `HOLDOUT.md`, `RAPPORT.md` och `ut/codex/pipeval/PIPEVAL.md`.

## Målet

En allmän och pålitlig 0.0, alltså scenen före all modifiering, avläst ur originalvideon till 3D. Den ska vara "god nog" för de kommande 200–500 klippen. Inga klippspecifika lösningar: varje regel ska hålla på nästa klipp.

## Vad vi gjort, i ordning

1. **Rumshjärnan, bildgenerering som hypotes.** Bildmodellen tar bort personer, det de håller och bildtext ur en ruta per tagning (V2). Bilden används bara bakom personen, och bara om en grind godkänner den: djupet, kanterna, linjeringen, den lokala förskjutningen och skalan. Gemini granskade bilderna, och därefter genereras även en oberoende bild för tagningar som tidigare bara genererades mot ett ankare. Resultat: 0 oanvändbara bilder har släppts igenom på 54 tagningar. Ägaren ser bildgenereringen som en krycka, och den har inte utvecklats vidare.
2. **Facit för hela 0.0.** Gemini dömde 38 tagningar och Codex 16 tagningar ur nya klipp (hold-out). Bara 16 % var god nog. Objekt och rum brast nästan överallt, eftersom skärvor per pixel faller sönder när kameran vrids. Pipens egen dom (L8) sa nästan ingenting om kvaliteten.
3. **Pipeutvärdering** (Codex med webbsökning). Behåll MoGe, GeoCalib och SAM 3D Body. Byt till struktur (plan och lådor), bättre segmentering (SAM 3) och kontakt mellan kropp och möbler.
4. **Struktur, variant Ls** (`struktur.py`):
   - Golv, väggar och tak blir plan. Möbler blir lådor; bord blir skiva med ben.
   - Föremål (SAM 3) blir skärvor ur originalets djup, med en kjol ned till stödytan.
   - Resten blir egna skärvor, och små delar visas bara från originalkameran.
   - Grundregler:
     - en yta får aldrig dölja det kameran såg (prövas per pixel)
     - antagna ytor visas inte från originalkameran
     - föremål flyttas inte
     - möbler mäts utan föremålens pixlar
     - rumsytor under föremål får ifylld textur men räknas som antagna
5. **SAM 3** (`modal_sam3.py`). Ägaren skaffade åtkomst kl. 20.07. 3.1-repot har bara Metas egen checkpoint, så `facebook/sam3` används via transformers. 24 begrepp; 8 klipp tar 35 s. Referensen Grounding DINO + SAM 2.1 (Apache) hittade 1–12 föremål per bild mot 10–50 för SAM 3.
6. **Kodgranskning.** Codex granskade två gånger (12 + 16 fynd) och rättade sina fynd. Det gällde bland annat projektiv textur per pixel, djupsprång från kameran, pixlar som förbrukades för tidigt och att samma bild räknades om för varje begrepp.
7. **Sittande kroppar** (`kontakt_sittande.py`). De skalas kring kamerans centrum så att fötterna hamnar på golvet. Dockan ligger kvar på personen från originalkameran. Spår som skulle behöva en skala utanför 0,75–1,33 flaggas i stället.
8. **Fri kamera** kretsar kring motivet (föremål och personer). Tidigare svängde närliggande bord ut ur bild.
9. **Självbedömning** (`sjalvbedomning.py`). Mörker och oskärpa förutsäger "inte god nog" bäst. Vid tröskel 0,5 flaggas 17 av 54 tagningar och 10 av 21 nej fångas. L8 "hög" stämmer nu bra för Ls: 13 tagningar, varav 2 nej.

## Hur vi mäter

Blinda parvisa prov: Lt (skärvor) mot Ls (struktur) på 54 tagningar i 8 klipp, varav 3 klipp aldrig ingått i kalibreringen. Varianterna slumpas som X och Y per tagning, och nyckeln ligger utanför arbetsmappen. Fyra domartyper har använts (Gemini Neon, Argon, Codex 6.2 astra och Claude). Ingen regel har ställts in mot en dom; ändringar görs bara efter domarnas felmönster. Domarnas brus är ±5–10 per kategori, så jämför bara inom samma domare. Codex är stabilast.

## Utvecklingen hos samma domare (Codex 6.2 astra), Ls mot Lt

| prov | originalkameran | rum | föremål | helhet | god nog Ls (delvis+ja / nej) |
|---|---|---|---|---|---|
| 3 (före SAM 3) | 0/23 | 48/4 | 8/16 | 39/13 | 38/16 |
| 6 (Codex rättningar) | 13/5 | 42/10 | 17/17 | 37/16 | 37/17 |
| 10 (orbit kring motivet) | 6/27 | 50/3 | 28/16 | 48/5 | 44/10 |
| 12 (skärpan rättad) | **21/14** | 45/8 | 34/13 | 45/7 | 43/11 |
| 14 (rumstextur under föremål) | 7/19 | 48/5 | 31/12 | 46/5 | 43/11 |

Lt låg i samma prov på cirka 8–12 delvis och 42–46 nej.

## Var vi står

- **Ls är klart bättre än Lt** för att regissera om. Den vinner rum, föremål och helhet i alla prov sedan SAM 3. Cirka 80 % av tagningarna är "delvis" god nog och cirka 20 % "nej". Ingen tagning får "ja" av Codex.
- **Från originalkameran pendlar resultatet** mellan proven: 21/14 i prov 12, 6/40 i prov 13 och 7/19 i prov 14, med många "lika". Skärpan rättades i prov 12 (Ls är nu skarpare enligt Laplace). Rumstexturen under föremålen gav en försämring i prov 13 som delvis är rättad. Rumstexturen är en avvägning: bättre underlag vid vridning, men vissa ytor nära föremålen syns fortfarande framifrån.
- **Ls-vyn** finns på http://127.0.0.1:5206/ i kolumnen "Ls · struktur (plan, lådor, kärl)", bredvid "L · texturerade instanser". Kryssa i "Fri kamera".

## Kvar, i den ordning domarna nämner det

1. Bänkfronter och bordsskivor delas upp i remsor och flak. Lådorna är låsta till rummets huvudriktning, så hörn som sticker fram skärs bort. Nästa steg: flytta en lådyta bakåt i stället för att skära den.
2. Föremålens kanter: revor genom tallriksbrätten och pommes, och överbrödet lossnar. Det beror på djupsprången i skärvorna.
3. Originalkameran: hitta de rumsytor som fortfarande lägger sig framför föremål framifrån, eller välj tröskeln per yta.
4. Bildtext och grafik som ligger ovanpå videon blir 3D. Begrepp som "text" skulle också fånga riktiga skyltar.
5. Mörka bilder och rörelseoskärpa går inte att använda. Ingesten bör välja den skarpaste rutan i mittentredjedelen.
6. Sittande: bäckenet ska hamna på sitsen. SAM 3:s stol ger stolens topp, inte sitsen.
7. L8 och självbedömningen behöver kalibreras om mot Ls på fler klipp.

## Beslut som väntar på ägaren

1. Ska Ls bli huvudrepresentationen för 0.0? Lt finns kvar för jämförelse.
2. SAM 3:s licens (SAM License, gated) för produktion, eller Apache-vägen (Grounding DINO + SAM 2.1), som är svagare.

## Kvoter vid 01-tiden

- Codex godsendat: cirka 65 % använt; fönstret återställs kring kl. 03.
- Codex letrend: återställs kl. 02.00.
- agy Neon: slut till cirka kl. 03.
- Argon: brusig, används bara som reserv.
- Opus via agy: slut.

## Tillägg kl. 01.45

- **Prov 14 dömt av Claude** (kontaktark, medelnivå, samma underlag som Codex prov 14): originalkameran Ls 4 / Lt 3 / lika 47, rum 47/4, föremål 29/4, helhet 45/4. God nog: Ls 6 ja, 36 delvis, 12 nej. Lt 3 ja, 29 delvis, 22 nej. Domen ligger i `ut/blind_ls_r14b/dom_claude.json`.
  - Codex (7/19) och Claude (4/3/47) är oeniga om originalkameran för samma version. Den skillnaden ligger inom domarnas brus.
  - Båda ger Ls ett klart övertag i rum, föremål och helhet.
- **Byggt men inte dömt** (prov 15): varje möbel får egen orientering (minsta omslutande rektangel, när den är minst 20 % tätare än huvudriktningens låda) mot remsorna, och djupgränsen inom SAM 3-masker är 12 % mot revorna. Alla 8 klipp är ombyggda, så vyn på 5206 visar den här versionen. Den ska prövas blint mot prov 14 när en domare finns.
- Codex godsendat hade 11 % kvar och stoppades på ägarens begäran. En Claude-subagent på medelnivå med kontaktark tog cirka 120 000 token för 54 tagningar.

## Titta själv

`http://127.0.0.1:5206/?klipp=<klipp>&vy=Lt,Ls` visar Original, Lt ("L · texturerade instanser", skärvor) och Ls ("Ls · struktur", plan, lådor och kärl) bredvid varandra. Kryssa i "Fri kamera" och dra i 3D-rutorna. Utan `&vy=` visas alla äldre varianter (A, B, L) också.
