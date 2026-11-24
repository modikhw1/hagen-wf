# GEM-X – arbetslogg

## 2026-11-10 – start

Ägarens beslut: endast GEM-X utvärderas. Steg 2 får börja först när steg 1
kör och inte är tydligt sämre än slutsekvensen. Ingen lokal inferens.
Budget: 90 GPU-minuter totalt, högst 30 för att få första körningen att fungera.
Tidigare fast-vith-reservation är inte en körning (events tom, debiterat 0).
Inga GEM-X-GPU-anrop har ännu gjorts. Inga befintliga filer har ändrats.

Läst: ingest/README.md, kontrakt/README.md, modal_sam3db.py, manifest,
budget, evaluate.py och sparade GEM-X-installations-/inferenskällor.
Primärkällorna GitHub NVlabs/GEM-X och HF nvidia/GEM-X öppnade igen.
motion-video saknar boxes-argument och följer bara huvudpersonen. Plan:
använd samma upstream-funktion med en avgränsad adapter för det_track
som levererar varje befintligt personspår, och spara adapterns proveniens.
Kameraintrinsik hämtas från manifestet, antagen i befintlig kedja.
Ingen handmodell eller gated tillgång hämtas/accepteras.

Nästa: lås kodrevision, CPU-bygg och CPU-hämtning till Modal-volym,
sedan ett sekventiellt GPU-anrop med hård startbudget.

Kommandon körs från projektroten med:
`$env:PYTHONIOENCODING='utf-8'; scen/.venv/Scripts/python.exe ...`
