# Facit för hold-out (spår A, 20 nov 2026)

**Facit är en uppskattning.** Det är märkt för hand i originalvideons pixlar (540×960) och bygger på standardstorlekar med intervall. Ingenting är uppmätt på plats, och ingen djupmodell, MoGe, SAM eller VLM ingår. Intervallen är 90 % (p05–p95) under märkarens antaganden, som står i varje ankarfil.

## Läget per klipp

| klipp | ruta | golv | facit kamerahöjd | grund |
|---|---|---|---|---|
| `faros_shipandterrace-7540756212032326934` | 73 | syns | **1,36–1,61 m** (p50 1,51) | stående man med fötterna i bild (1,70–1,95 m); horisonten ur 15 kanter inåt rummet (hyllor, bänkskiva) och 14 frontala kanter |
| `faros_shipandterrace-7511394441094008086` | 0 | syns | **1,39–1,70 m** (p50 1,56) | stående servitris med fötterna i bild (1,55–1,80 m); horisont y ∈ [185, 265] ur ordningsgränser (takskarven ses underifrån, bortre stolsryggar och bord ses ovanifrån) |
| `sabai.soong-7474616203366108439` | 222 | syns inte | **gränser 0,95–1,97 m** | tallrikarna i midjehöjd ses ovanifrån; ansiktet ses rakt framifrån, och ingen hjässa syns ovanifrån |
| `thepitaspot-7680489103195917590` | 212, 744 | syns inte | **gräns > 0,70 m** | bordsskivan ses ovanifrån; golvet syns inte i någon översiktsruta |

Möbelhöjder ingår inte. I faros_7540 går bänken ut ur bild, och i faros_7511 syns inte bordsbenen under det närmaste hörnet. Ruta 466 i faros_7511 har två stående personer, men sulorna skärs av bildkanten. Det står under `ej_matbart` i ankarfilerna.

För sabai och pitaspot är facit framför allt **epistemiskt**: kamerahöjden går inte att mäta ur pixlarna. Ett ärligt system märker den som `antagen`. Den som påstår `matt` får en varning och ska redovisa varifrån höjden kommer.

## Filer

- `<klipp>.facit.json`: facit per klipp (`rutor[]` med `kamera_hojd_m` {p05, p50, p95} eller `kamera_hojd_granser_m` [lo, hi], `kamera_hojd_matbar`, `golv_synligt`, varianterna och grunden). `facit_alla.json` innehåller alla fyra.
- `ankare/*.json`: märkningen (fot- och topp-pixlar, linjefamiljer, intervall och källor). `faros_7511_r0.json` (19 nov) är ersatt av `_v2` och har `ersatt_av`. Det äldre ankarets horisont ur korta golvfogar gav 0,95–2,5 m.
- `rutor/z/`: förstoringarna med rutnät som märkningen gjordes i. Alla bilder som en siffra bygger på är granskade.
- `bygg_facit.py`: bygger facit ur ankarna. Det kör `matt/rumsskala.py` en gång per antagande om lodrät flyktpunkt och tar **unionen** av intervallen.
- `ruta_rutnat.py`, `facit_vp.py`: märkverktyg (rutnät; LSD+RANSAC föreslår linjefamiljer som märkaren granskar).

## Hur spår B:s utdata jämförs

1. Kör B:s kedja på hold-out-klippet med **fryst kod** (sha256 på B:s filer före körningen, se `../../HOLDOUT.md`).
2. Skriv ett påstående i det generiska formatet (videorutans index i originalet, inte i tagningen):
   ```json
   {"faros_shipandterrace-7540756212032326934":
     {"rutor": {"73": {"kamera_hojd_m": 1.47, "kamera_hojd_status": "matt", "matt": {}}}}}
   ```
   Ur `paket.json` (scenpaket/2) tar man tagningen som innehåller videorutan, kamerans z i `tagningar[].kamera.nycklar` vid den rutan (eller `tagningar[].kamera.hojd.v`) och `tagningar[].kamera.hojd.status` som `kamera_hojd_status`.
3. Jämför:
   ```powershell
   $env:PYTHONIOENCODING="utf-8"
   scen\.venv\Scripts\python.exe motpart\runda-3-opus\A-domare\matt\holdout_jamfor.py --pastaende pas.json --logg jamforelse.json
   ```
   Utfall per ruta: `inom`/`utanfor` (med avstånd i cm) mot metrologifacit, `inom_granser`/`utanfor_granser` mot ordningsgränser, `varning_matt_utan_golv` och `saknas`. Läs alltid `antal_saknas`: ett tomt påstående ger `inom_alla` med `antal_inom = 0`. Självtest: `holdout_jamfor.py --sjalvtest` (6/6, felinjektion +25 cm, bord 0,45 m, under gränsen, mätt utan golv).

För nya märkningar (fler rutor eller möbelhöjder): lägg en ankarfil i `ankare/` och kör `bygg_facit.py`. Det ändrar inte det befintliga facit för tidigare rutor, men ändringen ska skrivas som tillägg med tid i `../../HOLDOUT.md`.
