---
id: 0031
titel: Liggaren: vad en handling betyder, vad som får ändras, och "ge glassen med andra handen" hela vägen till bild
status: redo
från: orkestratorn (Fable), efter ägarens beslut 13 nov kväll
datum: 2026-11-13
följer: 0030
tillåten_skrivning: [scen/3d/kontrakt/, scen/3d/gennedbrytning/, forvarld/gelato/, forvarld/liggare/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

Läs `delegat/kontext/malbild.md` och `vagen.md` först. `vagen.md` är uppdaterad i kväll med det här steget.

## Varför
Ägarens fråga i kväll, nästan ordagrant: om en CM säger "gör att kvinnan ger glassen med andra handen", då måste något först förstå att det hon gör (tillstånd 1) är något, att det som ska bli (tillstånd 2) är något annat, och det måste finnas en hjärna som förstår vad det ena är mot det andra. Ägaren antar att spelvärlden har tänkt på detta, och är tveksam till att Jev ensam kan göra det pålitligt, eller att en dyr modell ska sitta live som orkestrator.

0029 och 0030 visar samma sak med siffror. Allt som stannade, stannade på att tillståndet **beskriver** handlingar men inte vet vad de **betyder**:
- "Byt glassen mot en kaka" och "två smakprov": begreppet *vad handen bär* saknas, och förlopp (h3–h8 som en enhet) saknas.
- "Kunden tar emot med andra handen": Jev tog bort h8. Kunden finns inte som roll.
- Meningen i tillståndet drog två svar fel: Jev letade handlingar där meningen gällde en person eller ett innehåll.
- Jev gav olika svar med samma tillstånd (b-tilltal m2), och segmentfrågan skrevs om tre gånger mot testmeningarna.

Orkestratorns förslag, som ägaren har sagt ja till: **intelligensen ska inte sitta live, den ska ligga i en liggare.** Spel löser detta i slutna världar så: The Sims och Smart Objects i UE5 lägger meningen i föremålet (kylskåpet säger vad det kan göras med och hur); planerare (GOAP, HTN) ger varje handling förvillkor och effekt; parametrisk animation (motion warping, IK, spegling) gör att samma rörelse kan spelas mot nya mål. Ingen har gjort det för godtycklig inläst video, men delarna finns.

Tre lager med olika fart:
1. **Liggaren** skrivs vid ingest av en stark modell. Minuter är i sin ordning. Den säger per handling: roller, tillstånd före och efter, vad som bär meningen och vad som är tillfälligt, vilka ändringar som är lagliga (frihetsgrader), och hur en ändring sprider sig.
2. **Jev** förstår inget på djupet, och behöver inte. Jev väljer bland de lagliga ändringar liggaren redan har räknat ut. Det är så Jev styr NPC:er: tillstånd plus lagliga handlingar ger ett val. Är inget alternativ rätt, säger Jev det, och meningen går till en långsam väg (en stark modell som skriver regi på några sekunder).
3. **Utförandet** har tre nivåer: direkt i 3D (spegling, IK, tidstöjning), en rörelseredigeringsmodell (sekunder), och ny generering (minuter, för slutrenderingen).

Det här uppdraget bygger lager 1, ytan som lager 2 läser, och nivå 1 av lager 3, och visar det på ägarens egen mening.

## Mål
1. En kort genomgång av vad som går att låna (`forvarld/liggare/LANA.md`).
2. Ett schema för liggaren, allmänt och litet.
3. Gelatos liggare, skriven som en stark modell skulle skriva den vid ingest, med en prompt som går att köra via API senare.
4. "Gör att kvinnan ger glassen med andra handen" hela vägen: liggaren, Jevs val, spridningen, speglad rörelse med IK, skeden i vänster hand, och en film före och efter.
5. Gelatos tio meningar plus ägarens mening, mot liggaren, flera körningar per mening.

## Att göra

### 1. Låna (högst en sida, `forvarld/liggare/LANA.md`)
Sök och läs, kort, med länkar. För varje: vad det är, vad vi lånar, finns öppen kod och under vilken licens.
- **Meningen i föremålet:** UE5 Smart Objects och Contextual Animation, The Sims annonser (advertisements).
- **Handling som förvillkor och effekt:** GOAP (F.E.A.R.), HTN, PDDL.
- **Roller:** semantiska ramar, FrameNet (till exempel ramen Giving: Donor, Recipient, Theme). Vi behöver ett litet och allmänt rollförråd, inte FrameNet i sin helhet.
- **Rörelse mot nya mål:** motion warping, IK, spegling (mirroring) av en arm.
- **Text-styrd rörelseredigering:** forskning där en källrörelse plus en mening ger en ny rörelse (till exempel MotionFix och efterföljare). Är något moget nog och öppet nog att köra på MHR- eller SMPL-kroppar? Bara läsa, inget installeras i det här uppdraget.

### 2. Schemat (`kontrakt/liggare.schema.json`)
Förslag, ändra om något bättre visar sig. Håll det litet och allmänt, inget som bara gäller glass.
- **Entiteter** (`id`, typ, och **affordanser**: vad den kan göras med). Personer, kroppsdelar som kan bära (vänster och höger hand), föremål, innehåll (glassen på skeden är en egen entitet, inte en egenskap hos skeden), möbler, och platser (tråget, kundsidan). Koppla till källans id.
- **Fakta** i tillståndet, korta predikat: `i_hand(A, höger, sked)`, `på(glass_prov, sked)`, `i(glass, tråg)`, `vid(A, disk_bakom)`, `vänd_mot(A, kund)`.
- **Händelser** över handlingsspårets segment: en ram (`ge`, `ta`, `skopa`, `luta_sig`, `tala`, `titta` …), rollerna (agent, sak, mottagare, verktyg, källa, kroppsdel), **förvillkor** och **effekt** som fakta, och `rutor`.
- **Förlopp**: händelser som hör ihop under ett syfte ("servera smakprov" = ta sked, skopa, lyfta, räcka fram, kunden tar emot). Förloppet är den enhet CM oftast menar.
- **Mening**: vilka roller och fakta som bär poängen (ur relevanslistan), och vilka som är tillfälliga. Här: att hon *ger* kunden ett *smakprov* bär; vilken hand är tillfälligt; att disken står mellan dem ramar.
- **Frihetsgrader**: per händelse eller förlopp, lagliga parametrar med värdedomän (`kroppsdel ∈ {vänster, höger}`, `tempo ∈ [0,5, 2]`, `antal ∈ {1, 2, 3}`, `sak ∈ {innehåll som går att ta med sked}`), vilken **utförandenivå** varje kräver (3D direkt, redigering, ny generering), och **spridning**: vilka andra händelser och fakta som måste följa med. Byts handen i "räcka fram", byts den i hela förloppet från det att skeden tas upp, och skedens fäste flyttas.
- **Jev-ytan** genereras ur liggaren: en kort lista av lagliga ändringar med id och en rad text, plus `ingen_passar`. Det är den som går in i Jevs tillstånd, inte hela liggaren.

### 3. Gelatos liggare
- Skriv den som en stark modell skulle göra vid ingest: utgå från källan (`kalla_0029.json`), handlingsspåret, relevanslistan, kontaktbladen och några rutor ur originalet. Du är själv den starka modellen i det här provet. Skriv ned prompten du skulle ge en API-modell (`forvarld/liggare/prompt_liggare.md`) och följ den, så att steget går att köra om senare.
- Kör samma prompt med Flash via gatewayen som jämförelse (högst 0,10 dollar). Vad skiljer, och är Flash tillräcklig?
- Kontrollera liggaren mekaniskt: varje händelses förvillkor ska vara sant i tillståndet före den, och effekten sann efter. Ett skript, `kontrakt/liggare_kontroll.py`. Hittar det en lucka (till exempel att skeden plötsligt är i handen utan att någon tog den), är det liggaren som är fel.
- För in en referens till liggaren i källan (nytt valfritt fält), bakåtkompatibelt med sha256 som tidigare.

### 4. "Ge glassen med andra handen" hela vägen
- **Jev**: Jev-ytan ur liggaren, och meningen "Gör att kvinnan ger glassen med andra handen." Fem körningar. Väntat val: förloppet "servera smakprov", `kroppsdel = vänster`.
- **Spridningen**: ur liggaren, mekaniskt, inte med en modell. Skriv ut vilka händelser och fakta som ändras.
- **Utförande nivå 1** i kompilatorn (ny regi-operation, allmän, till exempel `satt_frihetsgrad`): spegla armens rörelse från höger till vänster i de berörda rutorna (byt vänster och höger arms ledvinklar, spegla mot kroppens mittplan), behåll bål, ben och huvud ur genereringen, och låt IK föra vänster hand till tråget i skopa och till kundens hand i räcka fram. Skedens fäste flyttas till vänster handled. Mjuk övergång in och ut.
- Det här är inte sammansättning i ägarens mening: kroppen kommer fortfarande ur en generering, och ändringen är en följd av CM:s mening, inte en lapp över en dålig läsning. Märk rutorna `utförd_niva_1` i planen. Ser det fel ut, säg det rakt.
- **Utförande nivå 3, som paket**: en Dreamina-prompt där hon gör samma sak med vänster hand (`d_video/dreamina-paket/vanster_hand/`). Ägaren kan köra den. Då finns båda vägarna att jämföra.
- **Film** före och efter, bredvid originalet, med remsan.

### 5. Meningarna mot liggaren
- Gelatos tio meningar (`forvarld/gelato/meningar.json`) plus ägarens: "Gör att kvinnan ger glassen med andra handen." Lägg den som nr 11 i en ny fil, rör inte den gamla.
- Varje mening fem gånger med Jev-ytan. Redovisa: vanligaste valet, hur ofta, och om det går till bild. Jämför med 0029.
- För de meningar där Jev säger `ingen_passar`: **den långsamma vägen**. Ge liggaren och meningen till en stark modell (du själv i provet, och Flash som jämförelse) och be om en regi eller ett tydligt nej med skäl. Mät tiden för Flash-anropet. Det är den väg ägaren undrade över ("en Fable-nyckel som orkestrator i live-appen"): den används bara när liggaren inte räcker.
- Väntat (orkestratorns gissning, inte krav): m3 (två smakprov) och m4 (kaka) bör nu gå, eftersom förlopp och innehåll finns. m9 (kunden) bör bli `ingen_passar` eller en ändring på kundens roll, inte ta bort h8. m8 (le) och m10 (foodtruck) bör gå till den långsamma vägen och få ett skälat nej.

## Gränser
- Före-kopior av ändrad kod i kedjan (`kontrakt/ut/fore_0031/kod/`). Testsviten före och efter.
- Bakåtkompatibelt: alla tidigare källor ger samma plan med tom cache.
- Ingen ny bild- eller videogenerering. Jev: högst 0,10 dollar. Gateway: högst 0,20 dollar (Flash). Modal: bara om en läsning måste köras om, högst 0,30 dollar. Codex: nej.
- Webbsökning för punkt 1 är tillåten. Inget installeras.
- Rör inte `app/`, `video/`, `forvarld/btilltal/`, `forvarld/guacamole/`.
- Egna trösklar är diagnos, inte krav. Ändra inte Jevs frågor efter att ha sett svaren på testmeningarna; skriv frågan först, och redovisa om du ändå måste.

## Klart när
- `LANA.md`.
- `liggare.schema.json`, gelatos liggare, prompten, Flash-jämförelsen och kontrollskriptet med utfall.
- "Andra handen": Jevs fem val, spridningen, och `forvarld/gelato/ut_0031/andra_handen.mp4` före och efter. Dreamina-paketet för nivå 3.
- Tabell: elva meningar × fem körningar, med och utan liggare (0029:s tillstånd som utan), och den långsamma vägen för dem som inte passade.
- Tillägg i `PIPE.md` och överst i `NASTA.md`.
- Bedömning i högst tio rader: bär liggaren det ägaren frågade om, vad i den kom ur modellen och vad ur mätning, vad Flash klarar mot en stark modell, och vad som är nästa steg.

## Leveransform
`delegat/svar/0031-liggaren.md` enligt mallen, högst cirka 100 rader.
