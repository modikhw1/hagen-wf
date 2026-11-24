# Ursprungligt uppdrag (19 nov 2026, 21:49), ordagrant

Du är spår B i runda 3 av ett motpartsprotokoll i repot C:\Users\praiseworthy\Desktop\hagen-wf (Windows, Git Bash/PowerShell; Python-miljö: `scen\.venv\Scripts\python.exe`, sätt `PYTHONIOENCODING=utf-8`). Skriv allt på svenska med korrekt å/ä/ö.

LÄS FÖRST: `motpart/runda-3-opus/UPPDRAG.md`, `LAGE.md`, `forvarld_karna/ARKITEKTUR.md`, `motpart/PROTOKOLL.md` (A1–A6, C1–C9), `motpart/runda-1-claude/SYFTE.md` §4 (K4 och K2), `motpart/runda-1-claude/RUM.md`, `motpart/runda-1-claude/MENING.md` och `motpart/runda-2-neon/MOTANGREPP_V4_FINAL.md` (ta det som håller: fysiska ankare, epistemiska zoner, kroppslivscykeln, rörelseoskärpegrinden; se det generativa med skepsis).

DITT MÅL (K4): ett klipp som ingen byggt för går från ingest till en ändringsbar 1:1-förvärld (`scenpaket/2`-kompatibel) utan en rad klippspecifik kod, utan handskriven deklaration och med allt antaget märkt `antagen`. Det är det som skiljer en motor från en samling demos.

Arbetsordning:
1. Gör en allmän version av kärnkedjan i din mapp (`motpart/runda-3-opus/B-nasta-klipp/karna/`, kopia plus patchar av `forvarld_karna/`). Rätta det runda 1 och 2 visat är fel, bekräfta varje fel med eget motprov innan du rättar det:
   - kamerahöjdsklämman och kappa-skalningen (C1)
   - pitch/roll som kastas, så att alla kameror blir vågräta (C2)
   - mappnamnsroller och `bonaqua`/fokaltabell (A6)
   - R25 som flyttar kroppsrörelse till kameran (A2)
   - grindar som inte kan larma (A3)
   - `grindar.mat` som bara mäter en person (C3)
   Skalan ska komma ur allmänna fysiska prior (föremålsklasser med kända storleksfördelningar, personlängd, dörrar, golv- och bordsplan) med osäkerhet, inte ur per-klipp-konstanter. Det som inte syns (väggar bakom kameran, utanför bild) ska vara epistemiskt märkt, inte påhittat. Kroppar som bara delvis syns får inte bli spökbålar eller svävande fötter: märk synlighet per led och lägg inte in gissade leder som sanning.
2. Utveckla och regressionstesta på notan, guacamole, gelato och a-sketch (råcache i `scen/3d/ingest/ut/`). Kör sedan på hold-out. Spår A skriver `motpart/runda-3-opus/HOLDOUT.md` (vänta på den om den inte finns, och titta INTE på hold-out-klippen förrän din kod är fryst). Saknar ett hold-out-klipp råcache: kör den lokala ingesten som finns (`scen/3d/ingest/`). Inga betalda API:er.
3. Frys koden (sha256 i rapporten) och kör hold-out en gång. Redovisa resultatet som det blir, även dåligt. Mät med spår A:s mått om de finns (`motpart/runda-3-opus/A-domare/README.md`), annars med egna oberoende mått, och märk dem som egna. Bevis för K4:
   - `grep -rn <klipp-id>` i din kod ger 0
   - tre representativa rutor per tagning, original bredvid förvärldens rendering (Blender 5.2 headless via befintlig `byggsten/brygga/emit_bpy.py` eller egen kopia), samlade i en kontaktkarta som ägaren kan döma

GEMENSAMMA REGLER (gäller alla spår):
- Skriv BARA i `motpart/runda-3-opus/B-nasta-klipp/`. Ändra inget i `forvarld_karna/`, `byggsten/`, `scen/` (läs och kör gärna, men skriv utdata till din mapp), `data/`, `video/`, `app/`, `motpart/runda-1*`, `motpart/runda-2*`. Radera ingenting någonstans.
- Inga nya betalda generativa API-anrop (Codex-bild, fal, Higgsfield, Dreamina, Seedance, Gemini, Modal-GPU). Lokala modeller och befintliga cacher går bra. Om något verkligen kräver ett betalt anrop: skriv det som förslag.
- Ingen klippspecifik kod. Inga handskrivna deklarationer. Ingen spegling som metod (ägaren har strukit den).
- Egna mått är diagnos, inte krav. Säg aldrig "lyckat" utifrån egna grindar. Trogen originalet går före stiliserat.
- Varje påstående har bevis (fil:rad, kommando, bild) och ett motprov. "0 fel" räknas bara om grinden visats kunna larma. Granska varje bild du hänvisar till med Read-verktyget innan du påstår något om den.
- Parallella spår: A (domare, mått, hold-out), C (CM-mening till drag på `scenpaket/2`) och D (medielager och manus). Spår C kan vilja läsa dina paket. Lägg dem i `B-nasta-klipp/ut/<klipp>/paket.json` och beskriv formatändringar i `B-nasta-klipp/README.md`.

AVSLUTA med `motpart/runda-3-opus/B-nasta-klipp/RAPPORT.md`: vad som är gjort, per rättat fel före/efter med bevis, resultatet på hold-out oförskönat, vad som inte hanns med och dina svagaste punkter. Ditt slutsvar till mig: max 25 rader plus sökväg.