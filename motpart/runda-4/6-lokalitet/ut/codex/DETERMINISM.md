# Motprov 2: determinism

Oförändrad källkod och byteidentiska indata kördes två gånger med samma interpreter och argument:

```text
.venv/Scripts/python.exe -I -X utf8 -W ignore lokalitet.py babasburgers --obs gpu
```

För att samtidigt följa förbudet mot ändringar i andra `ut/`-filer kördes kommandot i en isolerad kataloghierarki under `ut/codex/isolated/motpart/runda-4/6-lokalitet/`. Interpretervägen är absolut till den befintliga `.venv`; `lokalitet.py`, `geom.py`, video, observationer, pose och valt ingest kopierades utan kodändringar. Detta är alltså en isolerad reproduktion, inte en körning som skriver över den levande ut-katalogen. Programmets vanliga relativa mål är även där `ut/babasburgers/paket_L.json`. Direkt körning på originalplatsen skulle också skriva `nat/*.bin`, `nat.json` och `lokalitet.json` (källrader 794–795, 883–890), vilket inte var tillåtet.

Originalet säkerhetskopierades före första körningen till `paket_L.original.json` och kopierades tillbaka efter respektive körning. Ingen originalobservation eller originaldiagnos ändrades. [baseline.json](baseline.json) och [integrity.json](integrity.json) kontrollerar de skyddade filerna.

| Fil | SHA256 | Tid/exit |
|---|---|---|
| Original, säkerhetskopia och återställt original | `b6825ffbf2c1bd7d48ff5dcd5abbcbb4c59f9b75b257d1c06cad64957596065e` | — |
| Körning 1 | `b6825ffbf2c1bd7d48ff5dcd5abbcbb4c59f9b75b257d1c06cad64957596065e` | 63.91 s / 0 |
| Körning 2 | `b6825ffbf2c1bd7d48ff5dcd5abbcbb4c59f9b75b257d1c06cad64957596065e` | 65.08 s / 0 |

Källkodens SHA256: `a1540f5838720061456fe1b7e6a87c6838acc016149c793a1b9bd0bfec029227`. Originalet och de två körningarna är byteidentiska för det begärda paketet. Resultatet gäller denna maskin, dessa fasta observationer och dessa två separata processer. Det säger inget om determinism i nya GPU-observationer, andra OpenCV-versioner eller olika maskiner. Inga Modal-jobb startades.

Körbara omslag från `6-lokalitet/`:

```powershell
# Endast för en ny evidenskatalog: audit.py prepare. Befintlig baseline skrivs inte över.
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py det1
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py det2
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py integrity
```

Varje omslag har 155 s timeout för sin underprocess. Körloggar: [1](determinism-1.log), [2](determinism-2.log); maskinläsbara kommandon och hashvärden: [1](determinism-1.json), [2](determinism-2.json).
