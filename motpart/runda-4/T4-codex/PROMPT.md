Du är T4 (GPT-6-astra, xhigh) i repot C:\Users\praiseworthy\Desktop\hagen-wf (Windows). Skriv på svenska med korrekta å/ä/ö. Du har ungefär 15 minuter. Ditt jobb är att FÖRREGISTRERA steg 2 och 3 i runda 4 så skarpt att de inte kan bli cirkulära, och att ge insikt orkestratorn saknar. Du bygger inte stegen.

Läs först:
1. motpart/runda-4/AGARENS_ORD_20NOV.md (ägarens ord, ordagrant)
2. motpart/runda-4/UPPDRAG.md (rättelsen 20 nov kväll)
3. motpart/runda-4/DOM_T1_T2.md (hela, särskilt tillägget om T3 och "Konsekvens för steg 2–3")
4. motpart/runda-4/T3-codex/GRANSKNING.md (avsnitt D)
5. motpart/runda-4/1-datagrund/URVAL.md och urval.json (steg 1: ~200 klipp i originalbildtakt, hämtas just nu till C:\Users\praiseworthy\Downloads\letrend-r4\; rör inte hämtningen, läs bara)
6. Extraktorerna som ger de lokala måtten: video/format/e28-tek.mjs, video/format/e30_tal.py, video/format/e37_personer.py (och data/format/e28, e30, e37 för utdataformat)
7. Medielagrets operationer: motpart/runda-3-opus/D-medielager/medielager/operationer.py, matning.py, README.md och RAPPORT.md

Leverera motpart/runda-4/T4-codex/FORREGISTRERING.md med:

A. Steg 2 (invarians, T3:D1). Exakt protokoll: vilka 12 klipp ur urval.json (regel + frö, inte handplock), vilka innehållsbevarande ingrepp (omkodning, upplösning, ljudnivå, bildtakt 30→15, ev. beskärning några px) med exakta ffmpeg-parametrar, vilken positiv kontroll (verklig tempo-/pausändring) och hur den görs, vilka mått som körs (namnge fält ur extraktorerna), hur förbehandlingen fryses (referenskonton vs testkonton; rätta rangfelet T3 hittade), och förhandsbestämda fällningskriterier per mått (t.ex. effektkvot teknisk/positiv). Ange vilka mått du förväntar fälls och varför, innan något körs.

B. Steg 3 (ömsesidigt ingrepp, T3:D2). Vilka operatorer i medielagret som faktiskt finns och kan ändra energi/tempo deterministiskt (pauskortning, klipprytm, tempo utan tonhöjd, ljudnivå/musik) – citera fil:rad; vilka som saknas och måste skrivas. Definiera den frysta förinställda policyn (vad den läser, hur den väljer ändring för A och B mot varandra respektive från varandra) och den konstanta jämförelseregeln med samma redigeringsbudget. Parurval (6 par, konton som inte använts för att justera metoden). Panelens frågor till ägaren (riktning, avsikt kvar, sammanhang, antal rättelser) med kontrollpar. Fällningskriterier. Märk tydligt vad som är ditt förslag och vad ägaren måste sätta.

C. Insikt: vad i hela upplägget (T1, T2, T3, domen, stegen) är fortfarande fel, cirkulärt eller pekar bort från ägarens mål (klipp som rör sig mot/från varandra längs dimensioner utan mush, deterministiskt, där harnessen fattar besluten som Lovable)? Vad är den mest informativa billiga saken att göra som ingen föreslagit? Högst en sida.

Regler: läs fritt, skriv BARA i motpart/runda-4/T4-codex/. Små kontrollskript får köras om de tar under 2 minuter (använd .\scen\.venv\Scripts\python.exe). Inga nätverks-, betalda eller generativa anrop. Varje påstående om repot med fil:rad. Märk antaganden. Sista rad: "Viktigast:" med en mening.
