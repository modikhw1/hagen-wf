
## 2026-11-10T23:24:54
Underlag och ordinarie plan → ingest/mhr_rig.py lästa. Blender 5.2 finns enligt ingest_klipp.py. Första filsökningen gick av misstag rekursivt in i ut/; ingen fortsatt sådan sökning. Inga original ändrade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py ingest
```

## 2026-11-10T23:25:04
Golv och kontakt färdiga på kopia: notan/S1. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py ingest
```

## 2026-11-10T23:25:04
Golv och kontakt färdiga på kopia: notan/S2. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py ingest
```

## 2026-11-10T23:25:05
Golv och kontakt färdiga på kopia: notan/S3. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py ingest
```

## 2026-11-10T23:25:07
Golv och kontakt färdiga på kopia: notan/S4. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py ingest
```

## 2026-11-10T23:25:08
Golv och kontakt färdiga på kopia: notan/S5. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py ingest
```

## 2026-11-10T23:25:08
Golv och kontakt färdiga på kopia: notan/S6. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py ingest
```

## 2026-11-10T23:25:09
Golv och kontakt färdiga på kopia: notan/S7. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py ingest
```

## 2026-11-10T23:25:14
Golv och kontakt färdiga på kopia: bar/bar. Mätvärden sparade i blender/gen/golv2/ingest_matning.json. Original kopierade, ej skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py compile
```

## 2026-11-10T23:25:15
Del 1 steg körda på sju notantagningar samt bar. SHA256 för samtliga kopierade original oförändrade. Inga bankfiler skrivna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py compile
```

## 2026-11-10T23:25:32
Båda kompileringsvägarna körda. Fulla normaliserade plandiffar finns i blender/gen/golv2/*_plandiff.json. Absoluta kopiesökvägar normaliserade; inga numeriska fält undantagna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck
```

## 2026-11-10T23:26:10
Del 1: nyskriven kopia och dagens metriska läsning har identiska scen-, kropp-, kamera- och objektdata. Full plan skiljer endast filhashar och byggunderlagets filförteckning (extra golv_prov.json); diffarna bevarade. Föreplan vald: ut/golv2/mat_fore/notan_plan.json, framställd med före-GOLV2-kod.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py efter
```

## 2026-11-10T23:27:37
Blender efter: s1 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:27:39
Blender efter: s2 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:27:41
Blender efter: s3 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:27:43
Blender efter: s4 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:27:45
Blender efter: s5 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:27:47
Blender efter: s6 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:27:48
Blender efter: s7 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:27:59
Blender fore: s1 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:28:00
Blender fore: s2 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:28:02
Blender fore: s3 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:28:03
Blender fore: s4 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:28:05
Blender fore: s5 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:28:06
Blender fore: s6 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:28:08
Blender fore: s7 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:29:00
Båda Blenderkörningarna färdiga: 21 rutor vardera, original/silhuett/flyttad samt sju vidare översikter. Källrutor, sida-vid-sida, överlägg, före/efter och mätvärden skapade. Mätning gäller faktiska Blenderleder och rasteriserad Blenderhud; masken är oberoende YOLO men nyckelpunkterna är estimatorns egna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck
```

## 2026-11-10T23:30:27
Korrigerad föreplan kompilerad med arkiverad GOLV2-förekod i separat process mot exakt samma dagens källmanifest och tomma regi som efterplanen. Moduler laddades från backup, deras resursbas behölls; inga produktionsfiler byttes. Första mask-/sidopassen hade provskriptsfel och ersätts efter rättning.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:30:51
Blender efter: s1 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:30:53
Blender efter: s2 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:30:56
Blender efter: s3 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:30:58
Blender efter: s4 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:31:00
Blender efter: s5 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:31:03
Blender efter: s6 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:31:05
Blender efter: s7 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py fore
```

## 2026-11-10T23:31:14
Blender fore: s1 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:31:16
Blender fore: s2 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:31:18
Blender fore: s3 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:31:20
Blender fore: s4 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:31:21
Blender fore: s5 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:31:23
Blender fore: s6 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:31:25
Blender fore: s7 renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py analys
```

## 2026-11-10T23:31:54
Separat Blenderprov av just blender/mhr_blender.py: importera() läser notan S1 genom metrisk, cam_t/pose exakt lika, tre världsposer nycklade. Ordinarie planväg använder ingest/mhr_rig.py (inte denna äldre direktimportör). Faktisk möbelgeometri exporterad ur sparad scen.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/analysera.py
```

## 2026-11-10T23:32:06
Båda Blenderkörningarna färdiga: 21 rutor vardera, original/silhuett/flyttad samt sju vidare översikter. Källrutor, sida-vid-sida, överlägg, före/efter och mätvärden skapade. Mätning gäller faktiska Blenderleder och rasteriserad Blenderhud; masken är oberoende YOLO men nyckelpunkterna är estimatorns egna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck
```

## 2026-11-10T23:33:14
Slutliga mask- och kamerabilder ersatta efter provskriptsrättning. Normaliserad full plan är exakt lika efter att enbart filproveniens (sha256 och byggunderlag) tagits bort; samtliga övriga fält jämförda utan tolerans. Kontakter mot sits/bord samt faktiska RGB-överlägg skapade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck
```

## 2026-11-10T23:34:15
Scenen återöppnad separat för oberoende kontroll av faktiska möbler/synlighet och S4:s vidare vy. Inga maskpass föregår denna render. Höft/sits och handled/bord uppmätta i planens/Blenders meter; rotleden är inte en fysisk sittyta.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/slutrapport.py
```

## 2026-11-10T23:35:21
fore: samtliga original- och sidovyer omrenderade direkt ur sparad scen, i en process utan maskpass. Detta undviker kvarvarande synlighetsstate efter bort-/återkoppling av maskpassets animationer. Kamerans matris kontrollerad efter render. Dessa bilder är de slutliga.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/analysera.py
```

## 2026-11-10T23:35:37
efter: samtliga original- och sidovyer omrenderade direkt ur sparad scen, i en process utan maskpass. Detta undviker kvarvarande synlighetsstate efter bort-/återkoppling av maskpassets animationer. Kamerans matris kontrollerad efter render. Dessa bilder är de slutliga.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/analysera.py
```

## 2026-11-10T23:36:22
Båda Blenderkörningarna färdiga: 21 rutor vardera, original/silhuett/flyttad samt sju vidare översikter. Källrutor, sida-vid-sida, överlägg, före/efter och mätvärden skapade. Mätning gäller faktiska Blenderleder och rasteriserad Blenderhud; masken är oberoende YOLO men nyckelpunkterna är estimatorns egna.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck
```

## 2026-11-10T23:36:24
Slutliga mask- och kamerabilder ersatta efter provskriptsrättning. Normaliserad full plan är exakt lika efter att enbart filproveniens (sha256 och byggunderlag) tagits bort; samtliga övriga fält jämförda utan tolerans. Kontakter mot sits/bord samt faktiska RGB-överlägg skapade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck
```

## 2026-11-10T23:38:21
Seriell provkörning från kontrakt/: test_flode, exit 0. UTF-8/LF-logg: blender/gen/golv2/test_flode.log. Inga produktionsändringar har behövts; dessa är regressionskontroller för läsning/golv/kropp.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
& 'C:\Users\praiseworthy\Desktop\hagen-wf\scen\.venv\Scripts\python.exe' -m unittest test_rumsmall # kör från scen/3d/kontrakt
```

## 2026-11-10T23:38:26
Seriell provkörning från kontrakt/: test_rumsmall, exit 0. UTF-8/LF-logg: blender/gen/golv2/test_rumsmall.log. Inga produktionsändringar har behövts; dessa är regressionskontroller för läsning/golv/kropp.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
& 'C:\Users\praiseworthy\Desktop\hagen-wf\scen\.venv\Scripts\python.exe' -m unittest test_kroppmatt # kör från scen/3d/kontrakt
```

## 2026-11-10T23:38:36
Seriell provkörning från kontrakt/: test_kroppmatt, exit 0. UTF-8/LF-logg: blender/gen/golv2/test_kroppmatt.log. Inga produktionsändringar har behövts; dessa är regressionskontroller för läsning/golv/kropp.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/slutrapport.py
```

## 2026-11-10T23:41:09
KLART: rapport, samtliga 21 bildjämförelser, per-rutemått, alla numeriska försämringar, kontakter och seriella 83 gröna prov finns i blender/gen/golv2/. Dom: ursprungsprojektionen för kroppar bevarad; hela scenen underkänd genom sämre ytfästa props, S4-svävning och brister i S7. 921 ursprungsfiler oförändrade. Ingen produktionskod/design/tolerans ändrad.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck
```

## 2026-11-10T23:41:58
Slutkontroll: 21 original + 21 hudpass + 21 flyttade + 7 vidare bilder per fas finns. Rapportlänkar kontrollerade. Genererade textfiler validerade UTF-8 och normaliserade till LF (kopior före normalisering sparade). SHA256-kontroll efter alla tester: 921 original, 0 ändrade.

Nästa kommando (projektroten):
```powershell
$env:PYTHONIOENCODING='utf-8'
scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/prova.py hashcheck
```
