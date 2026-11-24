# Diagnos: 1 h 22 min väntan utan resultat (runda 4, steg 2, 20 nov 2026)

Skriven av orkestratorn (Claude Opus 5.5) på ägarens begäran, som underlag för en agent som ska bygga ett system som förhindrar detta. Det här är fakta och orsaker. Lösningsförslag står sist, som krav och inte som färdig design.

## 1. Vad som hände

Ägaren svarade på B7-frågorna cirka 21:20. Då fanns redan ett pågående uppdrag (steg 2, invarians), som startats 21:20 på orkestratorns initiativ med ägarens tidigare godkännande. Ägaren fick inget besked om förväntad tid. Klockan 22:43 frågade ägaren "Vad exakt har jag väntat 1h22m på?". Då hade inget mätresultat tagits fram.

| tid | händelse | belägg |
|---|---|---|
| 21:02–21:20 | T4 (Codex astra xhigh) skriver förregistreringen, 44 KB | `T4-codex/FORREGISTRERING.md` |
| 21:20 | orkestratorn startar steg 2-agenten (Sonnet, bakgrund) med "följ protokollet exakt" | konversation |
| 21:20–21:33 | agenten skriver adapter, recept, analys (8 skript) | mtimes i `2-invarians/` |
| 21:33–22:21 | **referensmätning: 144 klipp × 3 extraktorer, 21 batcher, sekventiellt (48 min)** | `ref_kor.logg.txt`, `ref_mat.jsonl` (144 rader) |
| 22:22–22:42 | provkörning + byggkontroll | `dry_*` |
| 22:42 | manifest fryst | `MANIFEST.md` |
| 22:43 | skarpt test på 12 klipp startar (ca 20–30 min kvar) | `test_kor.logg.txt` |
| 22:43 | ägaren frågar | – |

Tidigare samma kväll fanns liknande väntetider: steg 1 (hämtning) tog 32 min, T1/T2 15–17 min var, och domarens panel 15 min. Ingen av dem fick en tidsuppskattning innan start.

## 2. Rotorsaker

**R1. Ingen tidsuppskattning före start.** Orkestratorn granskade protokollets *innehåll* (cirkularitet, bevarande), men inte dess *kostnad*. Det enkla överslaget gjordes aldrig: 156 klipp × upp till 13 mätfiler × 3 extraktorer på CPU. Det fanns redan data att räkna på, eftersom steg 1 visade median 30–60 s per klipp och storlekar på 1080p.

**R2. Protokollet saknade en proportionalitetsprövning.** T4 krävde att skalan fryses på 144 referensklipp från 72 konton, för att rätta ett rangfel som T3 hittat i T2:s kod. Felet går att rätta med medelrang på några sekunder. Frysningen skyddar mot läckage från testdata, vilket är metodiskt rätt men överdimensionerat för en pilot på 12 klipp. Ingen frågade "vad är det billigaste som besvarar frågan?".

**R3. Dyra tekniska val förstärkte varandra.**
- FFV1 förlustfri i 1080×1920 blir ca 18 MB/s, så ett 58 s klipp blir ca 1 GB.
- Disken hade 9 GB ledigt. Därför tvingades agenten bygga, mäta och radera en variant i taget, vilket gjorde allt sekventiellt.
- Maskinen har lite RAM, så extraktorerna kunde inte köras parallellt.
- Allt detta stod redan i minnet och i steg 1:s rapport (disk 9,3 GB, 128 klipp i 1080p), men det matades inte in i bedömningen.

**R4. Den mänskliga delen planerades in sist, fast den var en nödvändig grind.** Protokollet A2 kräver en blind människa som ser och hör att ingreppen inte ändrade innehållet (P ska uppfattas som snabbare i ≥ 10/12). Agenten kan inte göra det (`2-invarians/AVVIKELSER.md`, avvikelse 1). Det dyra automatiska ledet kördes alltså först och ger bara en "ofiltrerad" halv dom. Ägarens 10 minuter hade kunnat schemaläggas parallellt eller före, för varianterna går att bygga på några minuter.

**R5. Ingen hjärtslag till ägaren.** Bakgrundsagenter rapporterar bara när de är klara. Orkestratorn är instruerad att inte polla och sade ingenting mellan 21:20 och 22:43. Ägaren visste inte om något pågick, hur långt det kommit eller hur länge det skulle ta.

**R6. Överlämning av ett förslag som ett låst kontrakt.** T4 märkte protokollet "Förslag". Orkestratorn skickade det vidare med "följ exakt, ändra inget". Det gjorde att agenten inte fick förenkla när kostnaden blev synlig. Agenten tolkade i stället sex luckor själv och dokumenterade dem (bra), men kunde inte stoppa och fråga om omfattningen.

**R7. Rigoritet på fel ställe.** Kvällens riktning (ägarens ord 20 nov) gäller att klipp ska röras mot och från varandra utan mush. Steg 2 prövar om mätinstrumentet tål omkodning. Det är en nödvändig sidofråga men inte målet. Orkestratorn lät sidofrågans rigör växa utan att väga den mot vad ägaren väntade på.

## 3. Bidragande faktorer
- Ägaren hade sagt "ta det sekventiellt och så långsamt det behöver gå". Orkestratorn läste det som tillåtelse att inte uppskatta tid. Ägarens mening var kvalitet före brådska, inte att väntan inte behöver redovisas.
- Kedjan av granskare (T1 → T2 → T3 → T4) gav allt skarpare protokoll men ingen granskare hade i uppdrag att bedöma genomförbarhet (tid, disk, RAM, mänskligt beroende).
- Codex-kvoten styrdes noga (minne `reference-codex-kvot`), men ägarens tid hade ingen motsvarande budget.

## 4. Krav på ett system som förhindrar detta
1. **Uppskattning före start (grind).** Varje uppdrag som väntas ta över 5 min får en förhandsuppskattning: antal enheter × uppmätt tid per enhet. Tiden per enhet mäts med en pilot på 1–2 enheter, inte med en gissning. Uppskattningen visas för ägaren med sannolikt intervall innan start.
2. **Budgettak med stopp-och-fråga.** Uppdraget bär ett tak för väggtid (och disk och kostnad). Vid 1,5 × uppskattningen stannar agenten och rapporterar i stället för att fortsätta.
3. **Hjärtslag.** Långa körningar skriver framsteg till en känd fil (`<mapp>/FRAMSTEG.json`: steg, n av N, ETA, ledigt utrymme). Orkestratorn sammanfattar för ägaren med jämna mellanrum, eller när ägaren frågar, utan att läsa hela agentloggen.
4. **Genomförbarhetsgranskning av protokoll.** Förregistreringar och uppdrag prövas mot: väggtid, disk, RAM, och om någon del kräver en människa. Det som kräver en människa schemaläggs först eller parallellt, aldrig efter den dyra automatiken.
5. **Proportionalitet.** Varje protokoll anger det billigaste provet som besvarar huvudfrågan och motiverar varje kostsamt tillägg (t.ex. 144 referensklipp) med vad det skyddar mot. Pilot först, full skala efter.
6. **Förslag ≠ låst kontrakt.** Ett protokoll från en granskare blir låst först när orkestratorn (eller ägaren) har godkänt kostnaden. Utförande agenter får rätt att stoppa och föreslå en billigare väg när kostnaden blir synlig.
7. **Maskinens kända gränser som indata.** Disk, RAM, CPU/GPU, kvoter (Codex, Modal) läses automatiskt före start och följer med i uppdraget.

## 5. Läget när diagnosen skrevs
Steg 2:s skarpa test kör (start 22:43). Resultatet blir en ofiltrerad sifferdom. Den blinda kontrollen kräver ägaren (~10 min).
