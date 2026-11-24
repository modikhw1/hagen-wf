# Dolda fötter: löpande logg

## 2026-11-10: inventering och design före kod

Läst: `GOLV2.md`, slutet av `GOLV2-LOGG.md`, `EFTER-GOLV2.md`, hela
`GOLV2-BLENDER-LOGG.md` och `blender/gen/golv2/RAPPORT.md`. Inga mätdata,
banker eller produktionsfiler är ändrade. En filinventering råkade följa
ett Windows-glob in i `kontrakt/ut`; åtkomstskyddet stoppade läsningen och
fortsatt inventering använder endast uttryckligen angivna källmappar.

### Rekvisita och möbelkontakt, görs först

Blenderprovet belägger att dagens ytrekvisita klipps mot mallskivans kant:
hamburgarens siktlinjemiss är efter GOLV2 0,147 m i S3 och 0,701 m i S7,
mot 0,065 respektive 0,356 m före. Centrumfelet blir 35→103 px i S3 och
17→45 px i S7. Samma rapport visar att handlederna i S7 efter GOLV2 ligger
30/42 cm utanför bordet, mot 0/8 cm före. `tropassning.py` flyttar i dag
stol och följbord en gång till medianbäckenet över alla tagningar. Det
gemensamma medianläget lämnar stora, tagningsegna XY-rester i S3 och S7.

Design: behåll platsens gemensamma mall och höjd, men spara per tagning den
bundna personens medianbäckenrest mot det gemensamma ankarläget. När
tagningens byggobjekt skapas flyttas just den bundna stolen och delar med
`folj_ankare` (bordet) med denna XY-rest. Kropp och kamera flyttas inte.
Beslutet är antaget och rapporteras per scen. Ytrekvisita löses därefter mot
samma scenlokala bord som Blender bygger. Detta ska prövas mot samma
centrumfel och Blenderbilder; hypotesen godtas inte utan mätning.

### Dolda fötter

1. Golvet beslutas först med oförändrad GOLV2-läsning. Regeln är endast
   kandidat när personen saknar varje synlig, tillförlitlig fotruta och
   tagningens valda golv kommer från en annan person eller annan mätt/
   modellbedömd ledtråd. Saknat golv ger ingen faktor och befintlig
   begränsningstext står kvar.
2. För varje fot bildas stabila stödfotsfönster ur sulans vertikala fart och
   spridning. Högst en stödfot per ruta används: den stabilare foten, och
   vid lika stabilitet den lägre. En snabbt rörlig pendelfot får därför inte
   styra bara för att den råkar vara lägst. Faktorn är medianen av
   kontaktfaktorerna under stabila stödrutor och är en per person/tagning.
3. För bildruta f är kameracentrum `C_f` och varje kroppspunkt `X_f`.
   Tydningen är `X'_f = C_f + k (X_f - C_f)`. Samma konstanta `k` används
   när kameran rör sig; fixpunkten är respektive bildrutas faktiska
   kameracentrum. I MHR-data betyder det samma faktor på `pose[..., :3]`
   och `cam_t`, aldrig bara avståndet. Blender skalar dessutom den importerade
   kroppens vilogeometri likformigt så att även hudens tjocklek följer med.
4. Tillåtet intervall är 0,93–1,07 (högst 7 %). Det rymmer ägarens cirka
   6 % för S4/C med en procentenhets marginal. Begärd faktor utanför
   intervallet klipps till gränsen; kvarvarande sul-/golvrest rapporteras.
5. Samma identitet i andra tagningar: en tagning med synlig tillförlitlig fot
   är längdreferens. En dold tagning får då faktorn som ger referenslängden,
   inte en konkurrerande golvfaktor; eventuell kontaktrest blir konflikt.
   Utan synlig referenstagning används golvfaktorn. Synliga tagningar och
   andra personer ändras inte.
6. Beräkningen sparas i mätningens personpost och kopieras till planens
   scenperson. Tillämpningen sker en gång i `ingest/metrisk.py`; kompilator,
   diagnostik, propfästen, webbunderlag och Blender registrerar planens
   beslut mot samma läsgräns. Rapporten märker beslutet `antagen` och visar
   faktor, längd före/efter, golvets källa och kvarvarande konflikt.
7. Handfäst rekvisita följer automatiskt den skalade handleden genom samma
   metriska läsning. Ytrekvisita och möbler följer scenens möbelrest ovan.
   Kontakter mäts efter båda reglerna.

Säkerhetskopior skapas före varje befintlig fil som ändras under
`kontrakt/ut/fore_dolda_fotter/<projektrelativ sökväg>`.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
& 'scen/.venv/Scripts/python.exe' -m unittest test_props
# kör från scen/3d/kontrakt
```
