# C-cm-mening: CM:s mening till en ändring i förvärlden (spår C, runda 3)

Resultat och svagheter står i [RAPPORT.md](RAPPORT.md). Den här filen beskriver kedjan, hur man kör den och gränssnittet mot medielagret (spår D).

## Kedjan

```
mening ──► router.tolka ──► nivå + drag (eller nej / motfråga / typbyte / medie)
                               │
                               ├─ medie ──► medie_till_D(begäran) ──► spår D  ("ej i detta spår" tills D ansluter)
                               ├─ ryggrad (kontrast, takter) ──► byggsten/hand/tillstand.tillampa (ingen modell)
                               └─ drag ──► drag.plan_<op> ──► bar.vakt (K5) ──► drag.gor_<op> ──► nytt scenpaket/2
                                                                │ stopp: "Meningen bärs av …" + motfråga, inget ändras
                                                                │ varning: ändringen görs, varningen visas
allt ovan går genom k7.Vakt: varje anrop loggas; nät, underprocesser, spegling och generering spärras
```

| fil | vad |
|---|---|
| `kallor.py` | Allmän koppling från ett paket till de källor som redan finns: relevans (cachad Gemini-läsning), källa (`scen/3d/kontrakt/*/kalla*.json`), liggare, ryggrad (`byggsten/hand/ut/ryggrad_<id>.json`), recept. Inget klippnamn i koden. |
| `bar.py` | Liggaren och relevansen (K5): bärlistan (bär / ramar / tillfälligt / brus / okänd, med källa per post) och vakten som prövar ett drags effekter mot den, inklusive liggarens förvillkorskedja (STRIPS). |
| `router.py` | Deterministisk router med svenska regler. Ordlistor för personer och föremål byggs per klipp ur källorna. |
| `drag.py` | Lagliga drag på `scenpaket/2`: tidslinje (ta bort, flytta, håll slutet, korta, tempo, upprepa), föremål (ta bort, byta, lägga till, flytta, produkt i hand), plats (byt miljö, flytta en interaktion med kameran), kamera (stabilisera, närmare, brännvidd) och kropp (stå kvar, Argons gång som märkt platshållare). |
| `k7.py` | K7-logg och spärr. `larmprov()` visar att spärren larmar. |
| `forhand.py` | Förhandsvisning genom paketets kamera (PIL, grindarnas projektion). |
| `kor.py` | Kör allt och mäter: K1-klassning, K3-latens, K5, K7, A:s bevarandemått, blinda bildpar med dold nyckel. |
| `frys.py` | Fryste meningar och facitförslag före första körningen (`meningar/manifest.json`). |
| `ANDRINGSLOGG.md` | Varje regeländring efter första körningen. |

## Köra

```powershell
$env:PYTHONIOENCODING="utf-8"
scen\.venv\Scripts\python.exe motpart\runda-3-opus\C-cm-mening\kor.py --larmprov   # K7: tre avsiktliga brott ska stoppas
scen\.venv\Scripts\python.exe motpart\runda-3-opus\C-cm-mening\kor.py              # alla meningar, alla paket, bilder (~5 min)
scen\.venv\Scripts\python.exe motpart\runda-3-opus\C-cm-mening\kor.py --holdout    # routerns nivåval på osedda meningar
```

Utdata i `ut/`: `resultat.json` (allt per mening), `RESULTAT.md` (tabell), `latens.json`, `k7_logg.jsonl`, `k7_larmprov.json`,
`holdout_resultat.json`, `barlistor/<klipp>.json`, `paket/<id>__<klipp>/paket_efter.json` (kan byggas i Blender med
`byggsten/brygga/emit_bpy.py`), `blind/par_NNN.png` och den dolda nyckeln i `blind_nyckel/nyckel.json`.

Paket som körs: `forvarld_karna/ut/<klipp>/paket.json` och, när de finns, spår B:s `B-nasta-klipp/ut/<ingestmapp>/paket.json`
(märkta `<klipp>(B)` och `<id>@B`).

`C_UT=<mapp>` styr utmappen. `ut_k7A/` är samma körning under A:s K7-vakt (`--utan-bilder`). `ut_B_slutpaket/` är en omkörning 20 nov
på B:s slutliga paket (`--utan-bilder`), och den gav samma utfall som `ut/` (ANDRINGSLOGG #9–10).

## Gränssnitt mot medielagret (spår D)

Routern skickar meningar om skärmtext, ljud, repliker, B-roll, montage och manus/utseende till medielagret. C letar efter
`motpart/runda-3-opus/D-medielager/medielager/grans_c.py` med funktionen `hantera(begaran: dict) -> dict`. Finns den inte
blir svaret `{"status": "ej_i_detta_spar"}` och meningen räknas som "routad till D".

**Begäran (C → D):**
```json
{
  "klipp": "gelato",                       // C:s namn på klippet
  "ingest": "kand-kennysgelato-tagningar", // ingestmappen under scen/3d/ingest/ut/
  "mening": "ta bort Vs-skylten och musikbytet",
  "lager": "skarmtext",                     // skarmtext | ljud | repliker | broll | montage | manus
  "typ": "tar_bort",                        // tar_bort | byter | lagger_till
  "mal": ["st2"],                           // id ur källans skärmtext/repliker eller relevansens textposter (kan vara tom)
  "k5": {"niva": "stopp", "stopp": ["Meningen bärs av Text vs …"], "varning": [], "info": []},
  "tidskarta": null                         // se nedan; sätts när C har ändrat tidslinjen i samma pass
}
```
K5 är redan prövad av C. Vid `niva: "stopp"` ska D inte ändra något; C visar motfrågan.

**Svar (D → C):** `{"status": "utford" | "nej" | "motfraga", "skal": "...", "andrat": [...], "fil": "<väg till D:s nya lager>"}`.
D:s anrop körs inne i C:s K7-vakt: nät och underprocesser spärras, utom `ffmpeg`/`ffprobe` (loggas som tillåtna).

**Tidskartan (C → D):** när C ändrar tidslinjen (tar bort, flyttar, håller, kortar, omsamplar) får det nya paketet
`tidskarta = [{tagning, ny: [a, b), kalla: [gammal ruta per ny ruta], markering}]`. Text och ljud som hör till en ruta i
originalet hittar sin nya plats genom den. Blandade rutor (skarv vid upprepning) har källrutan för den första halvan.

## Router: var en språkmodell skulle behövas

Routern är regler. Den klarar de meningar den skrevs mot men inte omskrivningar (holdout: 7 av 22 rätt nivå, se RAPPORT.md).
En modell behövs i tre lägen, och bara där:
1. **Ingen regel träffar** (utfallet `motfraga`, regel `ingen_regel`): välj nivå och drag bland de lagliga, givet klippets
   ordlista. Det är Jevs roll i `byggsten/hand` (ett slutet val bland lagliga drag). Uppmätt där: cirka 0,00006 USD och
   170–660 ms per anrop (`byggsten/hand/README.md:104-105,193`; `ut/regi/bord-*/logg.json`, fältet `usd`).
2. **Pronomen och roller** när flera personer passar ("han som sitter till höger"). Samma slutna val.
3. **Nya drag** (förståndet): 13–19 s med `codex exec`, cirka 3 s med Gemini Flash (`byggsten/hand/README.md:155,162`).
   Inte inkopplat här; ett lärt drag skulle sparas som en ny regel.
En lokal modell kan ta läge 1 och 2. Den är inte prövad i det här spåret.
