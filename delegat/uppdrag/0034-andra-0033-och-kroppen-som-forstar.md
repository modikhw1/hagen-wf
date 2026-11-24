---
id: 0034
titel: Ändrar 0033, och kroppen som förstår: en kontroller som anpassar hela kroppen till nya mål, i realtid och utan generativ video
status: redo
från: orkestratorn (Fable), efter ägarens besked 13 nov kväll
datum: 2026-11-13
följer: 0033
tillåten_skrivning: [forvarld/kropp/, scen/3d/kontrakt/, scen/3d/gennedbrytning/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

## Ändring av 0033 (gäller genast, också om 0033 redan pågår)
- **Gör** punkt 1 (fyll i 0031), 3 (kunden som roll) och 4 (bild för allt).
- **Stryk** punkt 2 (speglingen) och punkt 5 (Dreamina bredvid). Skälen står nedan.
- `d_video/dreamina-paket/vanster_hand/` ska inte köras. Låt mappen ligga, men skriv i dess `LAS-MIG.md` överst: "Återkallad 13 nov: Dreamina används bara för att återskapa originalet."

## Ägarens besked, som gäller allt framåt
1. **Dreamina, och generativ video överhuvudtaget, är bara till för att återskapa originalet så likt som möjligt vid ingest.** Den ska aldrig göra alternativa versioner. Ändringar som en CM ber om får inte gå genom generativ video.
2. **Jevs ändringar ska vara blixtsnabba ändringar i 3D, utan generativ AI.** Det är innovationen. Ägaren vet att det går, men det finns ingen tydlig teknisk beskrivning av hur. En API-nyckel till Claude eller Codex som modellerar om är det närmaste i dag, och ägaren vill hitta en väg runt även det.
3. **Att byta arm är inte att spegla axlar.** Det kräver att hela kroppen anpassar sig: bålen roteras, ett nytt sätt att skopa uppstår, och kroppen ska ändå kunna ge mottagaren glassen. Det kräver en intelligens som är bunden till kroppen och vet vad som är "standard", det vill säga hur människor rör sig. Det går bortom liggaren.
4. **Ägarens två trådar, som inte löser problemet men är värda att ta upp:**
   - Det finns, och kommer att finnas, över tusen analyserade klipp med olika rörelser, kameravinklar och scener. Det är ett dataset. Det är bara oklart hur och varför det skulle lösa detta.
   - Jev kan inte improvisera fram en ändring av en riggad kropp. Ägarens tanke: en bank av rörelser som tränas och bakas in, och animationer som styrs som av en riktig person, eller av en AI som simulerar kroppsrörelser i realtid.

## Orkestratorns läsning: det här finns, under andra namn
Ägaren frågade om han är en drömmare. Nej. Spel och animationsforskning har byggt just detta, och det är inte generativ video. Det är små, kroppsbundna kontroller som tränas på rörelsedata och körs i realtid:
- **Motion matching** (Ubisoft; UE5 har det inbyggt): en databas av rörelser där varje ruta väljs för att passa nya mål. Banken av klipp är databasen.
- **Inlärd IK med rörelseprior** (till exempel ProtoRes från Unity): ange några mål ("vänster hand här, fötterna där"), och nätet ger en naturlig helkroppspose i realtid, tränad på mocap.
- **Kontroller för samspel med föremål** (Neural State Machine, Starke 2019; DeepPhase): sitta, bära, ta, ge, där kroppen anpassar sig till föremålets läge.
- **Fysikbaserade kontroller** (DeepMimic, AMP, PHC; NVIDIA MaskedMimic och ramverket ProtoMotions): en simulerad kropp som lärt sig röra sig som människor, och som fyller i hela kroppen ur ofullständiga mål, till exempel "vänster hand ska nå kundens hand vid 3,5 s, behåll originalets stil".

Med det faller ägarens trådar på plats:
- **Jev går inte in i vikterna.** Jev väljer en frihetsgrad i liggaren. Liggaren gör valet till **mål** (vilken kroppsdel, vilket mål, när, vilka kontakter som ska hållas). Kontrollern gör målen till rörelse i hela kroppen. Intelligensen om kroppen sitter i kontrollern, intelligensen om meningen i liggaren, och Jev kopplar ihop dem på under en sekund. Det är samma resultat som "Jev i vikterna", men delat så att varje del kan bytas.
- **De tusen klippen blir träningsdata.** När ingesten ger 3D-rörelse per klipp, blir banken en domänspecifik rörelsedatabas: servera, gestikulera, sitta vid bar, titta i mobil. Det är precis vad motion matching och kontrollerna tränas på. Kedjan vi bygger är alltså också datainsamlingen.

Det här är orkestratorns läsning, inte ägarens beslut och inte prövat. Uppdraget ska pröva den.

## Mål
Det är känt vilken väg som ger "ge glassen med andra handen" som en naturlig helkroppsrörelse, framtagen på under några sekunder utan generativ video, och ett första prov finns i bild.

## Att göra
1. **Kartan** (`forvarld/kropp/KARTA.md`, högst två sidor). För varje väg ovan, och för andra du hittar:
   - vad den gör, vad den tar som indata (mål, kontakter, stil), hur snabbt den kör, och på vilken hårdvara
   - öppen kod och licens. Viktigt: AMASS och flera mocap-dataset är bara för icke-kommersiellt bruk. CMU mocap är fritt. Ange det per väg.
   - kroppsmodell (SMPL, SMPL-X, egen) och hur långt det är till MHR, som kedjan använder i dag. Är MHR rätt kropp för det här, eller ska kedjan byta?
   - vad den skulle behöva av våra data, och om de tusen klippen hjälper
2. **Gränssnittet** (`forvarld/kropp/GRANSSNITT.md`): hur en frihetsgrad i liggaren blir mål till kontrollern. Skriv ut det för "andra handen": kroppsdelar, mål per tid (tråget i skopa, kundens hand i ge), kontakter (fötterna stilla, skeden i handen), stil (originalets rörelse som referens), och vad kontrollern lämnar tillbaka.
3. **Ett prov.** Välj den väg som går snabbast att få igång lokalt eller med lite moln, och gör "andra handen" för gelato S1. Om ingen förtränad kontroller går att köra inom uppdraget: gör det enklaste som har samma form, en optimering över hela sekvensen där kroppen ska nå målen ur punkt 2, hålla kontakterna och ligga nära originalets rörelse och en rimlig pose. Säg tydligt vad provet är och inte är.
   - Mät tiden per sekvens.
   - Rendera i förvärlden: original, före, efter.
   - Titta själv på h3, h6 och h8: roterar bålen, skopar hon på ett nytt sätt, når skeden kundens hand?
4. **Rekommendation**, högst tio rader: vilken väg ska byggas, vad den kostar i tid och data, och vad som måste in i kedjan för att de tusen klippen ska bli träningsdata.

## Gränser
- Ingen generativ video, ingen bildgenerering, ingen LLM som modellerar om rörelsen.
- Paket får installeras i `scen/.venv` om de namnges i svaret med version. Ett eget venv under `forvarld/kropp/` är tillåtet om beroendena krockar.
- Modal är tillåtet för att köra en förtränad kontroller eller en kort optimering, högst 2,00 dollar. Ingen träning från början i det här uppdraget.
- Webbsökning tillåten.
- Rör inte `app/`, `video/`.
- Egna trösklar är diagnos, inte krav.

## Klart när
- `KARTA.md` och `GRANSSNITT.md`.
- Provet för "andra handen", med tid, film och de tre raderna per segment.
- Rekommendationen.
- Tillägg överst i `NASTA.md`.

## Leveransform
`delegat/svar/0034-andra-0033-och-kroppen-som-forstar.md` enligt mallen, högst cirka 80 rader.
