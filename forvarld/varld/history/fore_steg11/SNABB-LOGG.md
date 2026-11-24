# Snabbvägen: löpande logg

10 november 2026. Uppdrag: koppla kontraktets snabbväg (kompilera(..., snabb=True)) till
webbvärlden, mäta, sanningskontrollera. Inget under scen/ ändrat. Ingen Blender, ingen
Modal. Detaljer och tabeller finns i README.md, avsnittet om snabbvägen.

## Klart
- Vägen ändring → visning → kompilerad plan kartlagd i kod (README, steg 1–7).
- kompilator_demon.py: långlivad Pythonprocess, JSON-rader över stdin/stdout. Kommandon
  kompilera, spara_plan, diagnostik, stang. Cache omdirigerad till pipeline/cache.
- kompilator.mjs: håller processen, tar bara senaste väntande lista, kör sanningskontroll,
  loggar i logg/kompilering.jsonl. Kvalitetskontroll i egen process.
- server.mjs: /api/kompilera, /api/kompilering (long poll), /api/kompilering/rader,
  /api/kvalitetskontroll, /api/kvalitet. Uppvärmning vid start.
- viewer.js/index.html: statusrad ”kompilerad: ja/nej, ms, avvikelser: n” och knappen
  Kvalitetskontroll med egen statusrad.
- sanning.mjs: jämförelse fält för fält. snabb-mat.mjs: mätning (tid, sanning).
- Mätt: kall 5,8–7,2 s (replik 12,9 s), varm ny process 0,76–0,81 s, varm långlivad
  0,35–0,36 s. Mål under 300 ms nåddes inte. Nya tidsurval kostar 2,5–8 s (se Fel).
- Sanningskontroll: 15 fall plus ångra, loggat i logg/sanning-2026-11-10T17-12-27-594Z.json.
- Chattprov: 12 Jev-anrop (budgeten slut), logg/chatprov-snabb-*.json.
- Kvalitetskontroll: 66 s kall, 10,4 s varm; redigering blockeras inte.

## Fel och begränsningar i snabbvägen/kontraktet (inte ändrade, redovisade)
1. Nytt tidsurval kostar 2,5–8 s även i långlivad process. Återgivning, från projektroten:
   starta kompilator_demon.py (eller anropa kompilera med snabb=True i en process),
   kompilera pipeline/kalla.json med regi = pipeline/base-regi.json, sedan med en
   trimma_scen på s3 (slut_s 5.21, lage klipp_slut). Andra anropet tar ca 7 s.
   cProfile: kvalitet.planbeslut → skymning.los → skymning.mat, 7,0 av 7,7 s.
   Samma edit en gång till: 0,45 s. README:s ”varm 0,79 s” gäller upprepad likadan edit.
2. Källkontrollen i kompilera() (kontrollera.kontrollera) tar 154 av ca 330 ms varje
   anrop, varav 82 ms sha256 över 85 mätfiler. Ingen bugg, men det som hindrar 300 ms.
3. Kamera: renderkamera stativ ger brännvidd ×1,374 (87,9 mm) för både inramning
   ”nara” med mål (s7) och ”hel” utan mål (s1). Troligen avsiktligt halvbildsval, ej
   utrett. Webbens stativ är ×1,12 respektive ×0,88.
4. duplicera_scen ger två skarmtext med samma id (st1 för s1 och s1_copy) i planen.
5. byt_miljo, byt_prop med tillgang_id och lagg_till_prop med tillgang_id avvisas för
   webbens id:n. Webben och kontraktet har inte samma bank av platser och föremål.
6. Kompilering av en regi som bryter schemat (byt_replik utan rost.stil och
   max_talfaktor) kastar för hela regin i stället för att avvisa den editen. Chattens
   egna edits innehåller fälten, så det syntes bara i mitt handbyggda prov.
7. Piper-syntes körs även i snabbvägen för byt_replik (12,9 s kall, 0,36 s med varm
   talcache). TAL_CACHE styrs av miljövariabel, så den kan flyttas utan kodändring.

## Inte gjort
- Ingen jämförelse pixel för pixel av webbens renderade kamera mot planens; kamerasiffror
  för webben är omräknade ur viewer.js-formeln.
- Ingen rensning av pipeline/snabb/ (plan-kontrollerad-*.json, plan-q*.json, ca 5 MB).
- Statusraden är inte testad på mobil bredd; knappen deaktiveras under körning men
  hindrar inte en andra flik.
- Kontraktsonly-edits (tidssträckning, lägg till scen, flytta_prop, rörelse, uttryck)
  är inte körda genom snabbvägen, bara lästa i schema/kod.
- Klipp b, riktig kvalitetsgranskning av resultatet, hashminnebindning i kompilatorn.

## Nästa
1. Be kompilatorns ägare ta skymningsbeslut per scen/ruta (cachenyckel per scen), så att
   en ny trimning inte räknar om alla scener. Då bör nya trimningar landa runt 0,4 s.
2. Pröva stat-nyckelbunden sha256 i kontrollera.hashar (sparar ca 80 ms).
3. Bestäm om webbens kamerafaktorer ska följa planens eller tvärtom; samma för
   standardtextstorlek (27 mot 30 px).
4. Bestäm hur webbens plåtbakgrunder ska bli platser i kontraktets bank.
5. Koppla statusradens avvikelselista till en synlig panel, inte bara hovring.

## Exakta kommandon (från projektroten)
```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
node forvarld/varld/server.mjs
node forvarld/varld/snabb-mat.mjs tid
node forvarld/varld/snabb-mat.mjs sanning
node forvarld/varld/ui-snabb-check.mjs
node forvarld/varld/chat-snabb.mjs          # 12 Jev-anrop, budgeten är redan använd
# Kompilatorn direkt, enstaka edit, ny process:
scen/.venv/Scripts/python.exe scen/3d/kontrakt/kompilera.py forvarld/varld/pipeline/kalla.json forvarld/varld/pipeline/edit-regi.json forvarld/varld/pipeline/utplan.json --snabb
```
Säkerhetskopior före ändring: forvarld/varld/history/fore_snabb/ (server.mjs, viewer.js,
index.html, README.md; sökväg relativt forvarld/varld).
