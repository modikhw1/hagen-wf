---
id: 0022
titel: Sätt ihop kroppen: överkropp ur originalet, underkropp ur antagandet. Och en källa som inte tappar armen.
status: utkast   # ÅTERKALLAT 01:10 av orkestratorn på ägarens begäran, ersatt av 0023. Utför inte.
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0021
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

Fortsätter 0021. Sätt svar 0021 till `klart` med en pekare hit; punkt 6 och 7 där tas om här i den mån de behövs.

> **Återkallat.** Ägaren avvisar sammansatt kropp: hela poängen med genereringen är att slippa klippa och klistra. Har du börjat: stanna, behåll det som är gjort, och gå till 0023.

## Mål
En kropp i förvärlden för gelato S1 som har originalets överkropp och armar (lutningen ned i disken, armen fram mot kameran) och antagandets ben och rot (står rakt, stilla fötter, ingen huk), i alla 148 rutor.

## Bakgrund
`g_forvarld/k/tre_bredvid_rutor.jpg` visar läget tydligt:
- **Dagens läsning** har överkroppen rätt där den syns: hon lutar sig ned i disken och räcker fram armen. Men benen är påhittade av läsaren (huk i början, knä uppdraget i slutet).
- **Variant k** (kamerafri, förgrundsfri källa) har benen rätt: raka, stilla, benlängdens spridning 1,8 %, hela kroppen i 148 av 148 rutor. Men överkroppen är fel där det gäller: lutningen i rutorna 40–70 är borta och armen går åt sidan kring ruta 100. Orsaken är känd: armen bakom glaset finns inte i personmasken, så källan hade ett hål där, och modellen hittade på (den svarta formen).
- **Variant (a)** (källan som den är) följde överkroppen men klippte benen.

Var och en har rätt där den hade underlag. Det är princip 6 i `STRATEGI.md`: originalet avgör där det syns, antagandet gäller där det inte syns. Den principen ska nu gälla **inom kroppen**, led för led, och inte bara mellan lager.

## Att göra
1. **Sammansatt kropp.** Bygg en kropp per ruta ur två läsningar:
   - ur dagens läsning av originalet: bål från midjan och upp, huvud, armar och händer, i de rutor och för de leder som har bildstöd (ingesten har redan mått på det: `palitlig_1.json`, `handsyn_1.json`)
   - ur den genererade läsningen (k): höft, ben, fötter och rotens bana
   - där originalet saknar bildstöd för en överkroppsled: den genererade, och märk rutan
   Gör det i kroppsmodellens parametrar (ledvinklar), inte genom att klistra ihop 3D-punkter, så att skelettet förblir ett skelett. Midjan är skarven: redovisa hur bålens lutning i originalet förs över på en höft som står rakt (lutningen ska tas i ryggraden och höftleden, fötterna ska stå kvar). Jämna skarven över tiden.
2. **Mät den sammansatta kroppen** som i 0021, och lägg till: överkroppens leder i originalets rutor ska nu ligga lika nära som i dagens läsning (det är samma data), och benen lika stabila som i k. Någon av dem sämre än sin källa betyder att sammansättningen förstör något; hitta vad.
3. **En källa som inte tappar armen.** Två varianter på fal, cirka 0,15 dollar var, i den här ordningen:
   - **k2: kamerafri men inte förgrundsfri.** Samma avbildning som k, men originalets alla pixlar ligger kvar (disk, glas, hennes arm bakom glaset). Bara kundens hand maskas bort. Startbilden och prompten säger vad som ska bort. Variant (a) visade att modellen då tar bort disken själv och följer överkroppen.
   - **k3: förgrundsfri med bättre mask.** Personmasken ur segmenteraren i full upplösning, med armen bakom glaset medtagen (prompta också "arm", "hand", och förena maskerna), och skärmtexten borttagen ur hennes yta.
   Läs och mät båda. Följer någon av dem överkroppen lika bra som (a) med benen lika bra som k, behövs sammansättningen mindre, men kör punkt 1 ändå: den är skyddet när generatorn hittar på.
4. **In i förvärlden.** Den sammansatta kroppen (med ben ur den bästa av k, k2, k3) i gelatos plan, renderad. Fyra bredvid varandra: original, dagens förvärld, k, sammansatt. Handföremålet (skeden) sitter kvar i handen som i dagens plan.
5. **Titta** på rutorna 0, 30, 55, 80, 100, 112, 136, 146 och beskriv per ruta: stämmer överkroppen med originalet, står benen rimligt, och syns skarven i midjan.
6. **Kontrollen, första version.** Skriv de mått som i natt har skilt bra från dåligt som en liten funktion som ger ja eller nej per tagning med skäl: hela kroppen i bild, benlängdens spridning, rotens största hopp, överkroppens avstånd till originalet där det har bildstöd, främmande föremål i lager 2 (yta i det genererade som inte är hon). Kör den på a, k, k2, k3 och den sammansatta. Trösklarna är diagnos; redovisa dem och hur de fem fallen hamnar.

## Gränser
- Bara nya filer under `scen/3d/gennedbrytning/`. Kedjans kod ändras inte; behövs något ur `mhr_rig.py` eller `sekvens_stabil.py` annorlunda, gör det i en kopia och beskriv ändringen.
- Fal: högst 0,45 dollar i det här uppdraget (k2, k3 och en reserv). Kör aldrig om en generering oförändrad.
- Codex: inga körningar. Veckan står på 97 %.
- Modal för läsning och segmentering som förut.
- Punkt 1 går före punkt 3 om tiden tryter. Den kostar inget och gäller oavsett generator.

## Klart när
- Sammansatt kropp som sekvens, mätt i samma tabell som dagens, a och k.
- k2 och k3 genererade, lästa och mätta, eller ett skäl till varför inte.
- Filmen med fyra bredvid varandra, med sökväg, och rutbeskrivningen ur punkt 5.
- Kontrollens utfall på de fem fallen.
- `STRATEGI.md`: princip 6 utvidgad till led för led, den sammansatta kroppen som steg, och tabellen "Prövat hittills".
- Bedömning i högst sex rader: vad som nu är ingeststeget för kroppen, vad en tagning kostar, och vilken tagning som bör provas härnäst för att se om det håller utanför gelato (förslag: `b-tilltal-ravara` S2, fast kamera, handen utan bildstöd i 52 av 52 rutor).

## Leveransform
`delegat/svar/0022-overkropp-ur-originalet-underkropp-ur-antagandet.md` enligt mallen, högst cirka 80 rader.
