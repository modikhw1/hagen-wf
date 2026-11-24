# GOLV2: löpande logg

## Klart (Codex, före avbrottet 19:03)
- Underlagen lästa i angiven ordning. Ingen äldre GOLV2-logg fanns.
- Defekten verifierad i koden: cam_t-skala, kontaktförflyttning, senare kameraoffset.
- GOLV2.md skriven före kodändring. Inga modellkörningar, ingen Blender.
- Baslinjetid sparad i ut/steg11/golv2_fore/tider.json.
  Grund 4,94 s, förvärmning 8,326 s; trim 0,21–0,64 s.

## Inventering efter avbrottet (Claude, 10 nov kväll)
Koden var halvvägs ändrad; loggen ovan sade att kodning inte börjat. Diff mot
ut/fore_golv2/ (med --strip-trailing-cr) visar:

- Ny `ingest/metrisk.py`: gemensam läsgräns. Äldre sekvenser (utan
  golv_version 2) läses med cam_t_fore_golv, annars cam_t_fore_kontakt, och
  pose_fore_kontakt; golv_skala blir 1. Ingen fil på disk skrivs om.
- Läsare bytta till `metrisk.las`: kompilera, trohet, kroppmatt, tropassning,
  golvmatning, plats, diskplats, mhr_rig, rum, rum_verify, vakt.
- `kompilera.py`: kamerakompensationen (gamla rad 172–183) BORTTAGEN.
  `for_plan` (golvmatning) löser platsens golv vid kompilering. Kameranyckel
  för stativ får `mal_m` (målpunkten) för webbens avståndsfråga.
- `golvmatning.py`: ny `kombinera` (starkaste cue-familj väljer, en röst per
  person och tagning), synliga fötter kräver låg vertikal fart och märks
  modellbedömda, kroppsräckvidd får aldrig rösta, begränsningstext när ingen
  fot syns. Nya `platsbeslut` (ett golv per registrerad kameragrupp; z ur
  bildmatchningens höjdrest), `for_plan` (cache 'golv2'), `rapport_3d`.
- `ingest_klipp.steg_golv`: skalar inte längre cam_t; mäter golvet med
  golvmatning.undersok och skriver golv_version 2. `kontakt.steg_kontakt`:
  enbart diagnostik, flyttar varken cam_t eller pose. Ingen ingest körd.
- `bildskydd.py`: floor_delta borttagen (används bara av jamn_utvardera).
- `kor_jamn.py`: blocket som tvingade endast_overkropp=false för notan borttaget.
- `tropassning.py`: stol och följbord flyttas i XY till medianbäckenet
  (platsens ankare kommer från de gamla, skalade kropparna).
- `kvalitet.py`: golv2_3d-tabell i rapporten, begränsningstext per tagning.
- engang/golv2_mata.py och golv2_tools.py (Codex egna mätverktyg).

Fel i det halvfärdiga läget:
- Kodningsskada: å/ä/ö blev '?' i strängar/kommentarer som skrevs via
  PowerShell-pipe (golvmatning, ingest_klipp, kontakt, kor_jamn, kvalitet,
  tropassning).
- Alla omskrivna filer fick CRLF i stället för LF.
- Mätningen "efter" (ut/golv2/efter) kördes före sista ändringarna och saknar
  b_plan.json; den räknas inte.
- Data på disk orörda: inga sekvens_*.npz eller varld.npz har golv_version.

Bedömning av GOLV2.md mot principen: håller. Kroppen behålls som skattad
(X = R·(F·pose + cam_t) + C), ingen cam_t-skala, ingen kameraförskjutning per
person, golvet väljs per plats med redovisad rest. Punkt 5 (skala bakgrund och
kamera tillsammans) införs bara som regel; ingen ny skala väljs. Slutförs.

## Tredje utföraren (Claude, 10 nov kväll)
- Kontrollerat: alla berörda filer är giltig UTF-8 utan '?'-skada, inga CRLF
  (skriptet `lf.py` i scratch). Diff mot backup genomläst.
- `golvmatning.for_plan`: äldre plats.py drog varje tagnings eget golvvärde
  från registreringens Z EFTER bildmatchningen. Det återställs nu före
  `platsbeslut`, så matchningens höjdrest (`hojdskillnad_mot_golvantagandet_m`)
  gäller samma ram som när den mättes. `platsbeslut` kopplar bara höjd vid
  matchning med status `uppmatt`.
- `kontakt.steg_kontakt` skriver inte längre om sekvensfilen (ren diagnostik).
- `kroppmatt`: 'stabil' delar translation med 'byggd' (nolluttryck borttaget).
- Kompilering fungerar: notan (snabb, 12,5 s kall), b. Golvbeslut notan:
  S1/S3/S6 en grupp (bildmatchning), sits som cue (antagen) utom S4 (synliga
  fötter, modellbedömd). b: kamerahöjd 1,45 (antagen) utom S5 (djup).
- Före-koden: kopia i scratch `fore_kod/` = arbetsträdet utan ut/ med
  backupfilerna ovanpå och utan metrisk.py.

- Matchningens höjdrest visade sig inte vara en kamerahöjdsmätning: med den
  överförd satt samma person (A, samma stol) 0,62/0,54/0,44 m i S1/S3/S6.
  Kvarvarande lutning är 5,5 resp. 2,6 grader (plats.py:s gräns 2). Höjden
  överförs nu bara om lutning <= 2 grader och fri rigid rest <= 0,15 m; annars
  redovisas den under `registrering_hojd` som ej accepterad och golvet väljs
  lokalt. Ingen notan-matchning klarar gränsen.
- Mätt (engang/golv2_mat.py, mat_fore med scratch-kopian, mat_efter):
  `ut/golv2/jamforelse.md`. Rot-, bildfel och IoU oförändrade utom b s3
  IoU 0,795 -> 0,773. Kamera->rumskamera 0,15-0,71 m -> 0 i notan.
  Bilder: `ut/golv2/mat_{fore,efter}/notan_s*_flyttad[_vid].png`, montage
  `ut/golv2/jamfor_flyttad*.png`.

- FYND (21:41–): test_flode tog > 21 min (före GOLV2 ca 4,5 min). Profilering:
  `for_plan` kall 1,5 s, varm cache-träff (inte orsaken). Orsaken var
  `golvmatning.rapport_3d` i full diagnostik: utan cache, laddade sekvensen
  om för varje ruta och körde stödet (`trostod.begransa`) på varje ruta:
  8,9 s notan / 4,2 s b per full kompilering (20,9 s under profilering).
  Rättat: data laddas en gång, stöd var 3:e ruta (STOD_STEG), beständig cache
  'golv2_3d'. Nu 3,1 s kall / 0,08 s varm notan, 1,3 / 0,07 s b; samma värden.
  Den pågående test_flode-körningen använder gamla modulen; körs om efteråt.

- ORSAK TILL TESTTIDEN (22:50): faulthandler visar att test_flode står i
  `test_bars_byggdata_ar_byteidentiska_med_referensen` rad 222,
  `assertEqual(plan, ref)`. Planen skiljer (avsiktligt) från den frysta
  referensen och unittest bygger en full difflib-diff av två stora planer före
  avkortning; det tar en timme+. rapport_3d var inte orsaken (snabb=True).
  Skillnaderna i bar: golvet -1,448 -> -1,508 (GOLV2-lokalt golv ur synliga
  fötter), stativkamerans riktning (målpunkt ur metrisk kropp), nytt `mal_m`.
  Diagnoskörning med snabb jämförelse (`scratch/tidtest.py --snabbdiff`)
  pågår för att lista alla fallerande prov utan diffkostnad.
- Codex-granskningens fynd, rättat i kod (22:30–22:50):
  1 S4: C:s fötter är utanför bild (0 fotpunkter i egen ruta, 0 användbara
    rutor); golvet väljs av person 4:s synliga fötter (55 rutor, modellbedömd).
    C:s sula över golvet är därmed konflikt mellan två personers skattade djup,
    inte mätt kontakt. Redovisas; kroppen flyttas inte (GOLV2).
  2 Kedja/dubbelbehandling: platsbeslut ackumulerar höjdrest längs grafen,
    flyttar även cue-intervall, sparar total flytt `z_flytt_m`; for_plan
    återställer basregistreringen för både äldre och version 2.
  3 Källor utan platsreferens: `golvmatning.lokalt_golv` (cache golv2_lokal)
    sätter golvet i kompilera och i kvalitet. Ensam identitetsplats behåller
    ramen och får golvhöjden i `golv.hojd_m` (samma som utan plats).
  4 Sits kräver semantikens `sitter` OCH identifierad sitstyp (mallens deltyp
    via bundet ankare); stolsprior bara för 'stol'. Låg höft/bord avgör inte.
  5 Synlig fot per sida och tillförlitlig ruta (undersok, rapport_3d,
    golv2_mat, kontakt).
  6 Cachenyckel golv2 innehåller trohet.py, trostod.py, tro_rigg.json,
    mhr_ledernamn.json.
  7 mhr_blender.py läser via metrisk.las; golv_sammanfatta.py,
    engang/mall_granska_blender.py, ingest/flera/plats_patchad_kopia.py märkta
    HISTORISKA (rå cam_t). Kopior i ut/fore_golv2/.

- Diagnoskörning (snabb jämförelse): test_flode 77 s, 46 prov, 3 fel; alla
  tre mätte det gamla beteendet. Ändrade prov (kopior i ut/fore_golv2/):
  a) `BarOforandrad.test_bars_byggdata_ar_byteidentiska_med_referensen`: ny
     referens `ut/bar/plan_efter_golv2.json` (gammal behålls). Skillnad =
     GOLV2-golv, stativriktning, mal_m.
  b) `Plats.test_tva_personer_i_samma_scen_foljer_var_sitt_ankare`: M0 läses
     ur en plan utan edits (for_plan löser registreringens Z), inte ur källan.
  c) `Plats.test_platssteget_ar_deterministiskt`: `test_plats_snapshot.py`
     kör nu arkivets solver (testdata/solver_fore_golv2/: plats.py,
     golvmatning.py, mhr_ledernamn.json från före GOLV2), eftersom
     referensen är definierad som arkivets solvers utdata. Assertion orörd.
  Den gamla test_flode-processen (21:41) stoppades 22:58; orsaken var känd.
- Svit startad 23:00 per modul med `scratch/tidtest.py` (vanlig unittest).

- Fler prov som mätte gammalt beteende (kopior i ut/fore_golv2/):
  d) test_rumsmall.GolvOchSkymning.test_overensstammande_cues_ar_uppmatta och
     .test_planterad_avvikare_avvisas_och_redovisas: väntat värde 0,21 (median
     mellan familjer) -> 0,20 (fotfamiljen väljer, GOLV2 punkt 3).
  e) test_kroppmatt.Omkorningslogg.test_slutligt_utsnittsbeslut_loggas_efter_
     historisk_golvregel: endast_overkropp förväntas nu stå kvar (True);
     kor_jamn tvingar inte längre false för den gamla golvskalan.
  test_plats_snapshot.py lägger nu kontrakt/ på sys.path (python -I).
- SVIT GRÖN 23:20: test_flode 46 (42,6 s), test_rumsmall 19 (4,9), test_regler
  18 (0,2), test_text_disk 12 (18,5), test_kroppmatt 18 (6,4), test_props 6
  (0,6), test_handelser 16 (3,5), test_snabb 7 (3,1), test_steg11 19 (74,7),
  bro.test_bro 34 (1,0), ingest test_rum 3 (0,0), semantik/test_semantik.py
  "alla tester ok". 198 unittest-prov, 0 fel. Loggar i scratch/svit/.

- Efter sista kodändringen (mappsignatur via os.scandir och processminne i
  for_plan, golv2-nyckeln varm 55 -> 17 ms): svit igen, alla moduler gröna:
  test_flode 46 (48,3 s), rumsmall 19 (4,8), regler 18 (0,1), text_disk 12
  (9,4), kroppmatt 18 (6,8), props 6 (0,6), handelser 16 (2,3), snabb 7 (2,6),
  steg11 19 (66,3), bro 34 (1,0), test_rum 3, semantik "alla tester ok".
  Modultider före (ut/steg10c/efter_*_tid.json): flode 169, rumsmall 7,2,
  regler 2,2, text_disk 8,8, kroppmatt 10,2, props 1,4, handelser 4,8,
  snabb 9,9, bro 2,1, rum 0,85 s.
- Snabbväg (`steg11_mata.py golv2_efter --forvarm`, kall cache): grund 5,34 s
  (omkörning 5,22) mot 4,94; förvärmning 7,36 (7,84) mot 8,33; trim och övriga
  edits 0,21–0,61 mot 0,21–0,64. Grundens +0,3–0,4 s är golv2-beslutet som
  räknas en gång per dataset (for_plan kall ca 1,0 s) och sedan ligger i
  beständig cache.
- Sanningskontroll (`node forvarld/varld/snabb-mat.mjs sanning`,
  logg/sanning-2026-11-10T22-01-08-123Z.json): 13 av 15 utan avvikelse. Kvar:
  stativkamerans avstånd, webben 0,144 m mot planen 1,651 m (nära) och
  1,885 m (vidare). `mal_m` finns i planens nycklar men webben
  (sanning.mjs/viewer.js, utanför scen/3d) läser den inte; inte ändrat.
- Mätning omkörd med sulhöjd (trosula) och alla spår i bilderna:
  `ut/golv2/jamforelse.md`, bilder `ut/golv2/mat_{fore,efter}/`, montage
  `ut/golv2/jamfor_flyttad*.png`, `ut/golv2/s4_vid_fore_efter.png`.
  Full kompilering med kvalitet.md: `ut/golv2/full/`.

## Kvar / öppet
- Notan S4/C svävar 0,11 m (fötter utanför bild; golvet från person 4).
- b S5/C 0,51 m över djupgolvet (före och efter); b s7/C −0,095 m (förr +0,10).
- Webbens stativavstånd (se ovan).
- ingest-stegen golv/kontakt är ändrade men inte körda (ingen ingest).

## Exakta kommandon (projektroten)
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/golv2_mat.py mat_efter
scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/golv2_mat.py mat_fore --kod <kopia: arbetsträdet utan ut/, backupfilerna ovanpå, utan ingest/metrisk.py>
scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/golv2_jamfor.py mat_fore mat_efter
scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/steg11_mata.py golv2_efter --forvarm
node forvarld/varld/snabb-mat.mjs sanning
```

Alla befintliga filer som ändras ska först kopieras till
ut/fore_golv2/<sökväg relativt projektroten>. Inga ändringar i kroppsbank/rumsbank.
