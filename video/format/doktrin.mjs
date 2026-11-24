// LeTrend-doktrinen v5 (4 nov 2026): ägarens principer ur Miles-pass 1–6 och experimenten E1–E4 och
// serietestet, samlade på ett ställe. Alla steg i harnessen v5 läser härifrån: ingest (v5.mjs),
// kundlinjen (h-linje.mjs), matchningen (h-match5.mjs) och anpassningen (h-anpassa5.mjs).
// Människoläsbar version med källor: karta/videoforandring/doktrin.md.

export const LETREND = `LeTrend hjälper lokala restauranger, barer och kaféer att göra TikTok som personalen själv spelar in med en telefon. En content manager (CM) väljer klipp ur LeTrends bibliotek och rekommenderar dem till en kund, som gör sin egen version. Kunden spelar in utan handhållning och utan att förväntas klippa avancerat. TikTok driver med klassisk marknadsföring: det bästa känns som ett tv-program eller ett inside-skämt med personalen, där verksamheten är scenen och säljet är invävt.`

// Klippets grundvärde: det klippet är värt i sig, oberoende av kund. Väger tyngst i ägarens omdömen.
export const GRUNDVARDE = `Klippets grundvärde (oberoende av kund):
- Det starkaste kännetecknet är en fristående premiss: en idé som är rolig eller intressant i sig och går att säga i en mening utan verksamhetens namn. En absurd eller igenkännbar premiss bär även när den görs klumpigt ("even if you fail, it's still funny").
- Värdet ska finnas kvar utan efterarbete. Det LeTrend rekommenderar måste vara starkt nog även om kunden bara filmar och klipper enkelt. Klipp vars värde sitter i snabb klippning, effekter, ljus eller ett produktionsteam är inte biblioteksklipp, hur bra de än ser ut.
- Uppbyggnad och vändning ersätter karisma: ett klipp med eskalering bär med en vanlig anställd, en lång tagning utan vändning kräver en personlighet.
- Människor bär idén. Verksamheten är scenen, inte beroendet. Ett klipp som hänger på en viss person, lokal, rekvisita, nisch eller ett event går inte att flytta.
- Planerat, inte fångat. Eventfångster reagerar på något som redan händer.
- Visningar och montage utan person blir "just a pretty picture": ingen krok, ingen relation, inget att anpassa. En visning behöver en människa i bild och eget ljud.
- Instagram-polering, CapCut-mallar och reklamfilm är en annan fil än TikTok-språket med självironi och personer i fokus. De kan fungera som referens för komposition men inte som förlaga.
- Ett biblioteksklipp ska höja taket: lära en annan verksamhet något den inte redan gör.
- Hyllor: kärna (fristående premiss, bär överallt), mitten (godkänd men villkorad av kunden: segment, kapacitet, situation), situation (sällan använda lägen som flytt, nyöppning, högtid), capcut_referens, ute.`

// Kundens linje: passform är fortsättning på det kunden redan gör, inte att fylla luckor.
export const LINJE = `Kundens linje och passform:
- Passform betyder att klippet fortsätter kundens nuvarande linje som nästa klipp. Kunden ska inte göras om ("we're not asking the chicken shop to be improved"). Ett klipp på ett annat språk än kundens "would feel different, it would stick out", även om det är bra.
- Kontots språk har flera delar: strategi (en egen sketchvärld som ett tv-program, ett högt producerat tilltal mot publiken, premiumvisning med vardagshumor, ren visning, kampanj), kantighet (familjär och barnsäker, lekfull, kantig med mörk humor, vuxen), tempo och hur mycket kontot lutar sig på klippning, och vem personerna är framför kameran.
- Tonen är en egen gräns: Gen Z-självironi eller vuxna parteman passar inte en familjär verksamhet, och för fånigt sänker en kantig.
- Konton byter kurs. Det som kontot gjort på sistone väger tyngre än det gamla.
- Personen som fokus (karisman bär klippet) och personen som behållare (personen säljer konceptet) är olika krav. Fokus kräver kundens egen frontfigur med rätt styrka.
- Luckor i mixen är ett medvetet val för CM, inte en passform. Ett klipp som fyller en lucka men bryter linjen passar sämre som nästa klipp.
- Ju längre klippets färdiga utseende ligger från kundens version, desto mindre är förlagan värd: kebabbilder är en dålig förlaga för ett steakhouse. Bilder som är bundna till en viss produkt eller lokal måste göras om, och då återstår bara idén.`

// Utfall mätt inom samma konto (E4, 1 322 klipp; serietestet, 93 konton).
export const UTFALL = `Det LeTrend vet om utfall, mätt inom samma konto: personer i bild, spelad situation, humor och direkt tilltal ger räckvidd och gillanden. En matvisning med en person i bild når ungefär dubbelt så långt som utan, med trendljud ungefär hälften. Klipp med kontots återkommande person når 30–60 % längre, och ett återkommande format cirka 30 %. Tävlingar, uppmaningar och erbjudanden ger kommentarer men inte räckvidd.`

// Anpassning: kärnan och det som bär, inte en scenlista; rösten är kundens egen.
export const ANPASSNING = `Så anpassar LeTrend:
- Originalklippet är ryggraden. Ange kärnan och det som bär, och lämna resten fritt. En lista över sekvenser ger lika vikt åt det som inte bär.
- En sketch som passar rekommenderas för vad den är: "you wouldn't change the script to fit the client". Att skriva om beats är kreativt skrivande och riskabelt. De praktiska bytena (produkt, lokal, vem som spelar) sköter personalen själv.
- Skriv inte in slumpen. Inskrivna misstag ("spill lite sås") blir falska och stela. Lämna utrymme för det som händer på riktigt.
- Repliker ska låta som verklig kommunikation, i personalens egen röst. Ge exempel på ton, inte manus att läsa upp.
- Säg om personen är fokus eller behållare, och vad det kräver av hen.
- Briefen är en guide, inte en manual. Den ska få kunden att förstå varför klippet passar dem och hur det hänger ihop med det de redan gör.`

// Kort doktrin (E8): ungefär en tredjedel av längden. Prövar om prompten slår i modellens gräns.
export const KORT = `LeTrend hjälper lokala restauranger, barer och kaféer att göra TikTok som personalen spelar in själv med telefon, utan avancerad klippning. En CM rekommenderar biblioteksklipp som kunden gör en egen version av.
Ett bra biblioteksklipp har en fristående premiss som bär även när den görs klumpigt, bärs av människor (inte av en viss persons karisma, ett event, en unik produkt eller polering) och har värdet kvar utan efterarbete. Vändning ersätter karisma. Visning utan person, Instagram-polering och CapCut-mallar är inte kärnan. Hyllor: kärna, mitten (villkorad av kunden), situation, capcut_referens, ute.`
