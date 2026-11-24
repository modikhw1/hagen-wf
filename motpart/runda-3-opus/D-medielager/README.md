# D-medielager: skärmtext, tal/musik, mat/B-roll och montage som ändringsbara lager

Spår D i runda 3 (19–20 nov 2026). Mål: K8 (medielagren går att ändra) och K6 (manus per scen) i
`motpart/runda-1-claude/SYFTE.md` §4. Resultatet står i [RAPPORT.md](RAPPORT.md).

Allt körs lokalt. Inga betalda anrop. Ingen generativ bild, video eller röst i ändringsledet (K7).

## Mappen

| sökväg | vad |
|---|---|
| `medielager/` | koden (ingest, operationer, manus, mätning) |
| `urval.py` → `urval.json` | stratifierat urval av 20 bankklipp, frö 20261119, plus spår A:s hold-out |
| `forbered.py` | ingestens tunga delsteg i omgångar (tagningar, ocr, sep, tal), cachade |
| `kor_k8.py` | ingest, fyra CM-meningar per klipp, mätning, felinjektion, manus, granskningsark |
| `k8/` | resultat (`resultat.jsonl`, `resultat_holdout.jsonl`, sammanställning) |
| `lager/<klipp>/` | `tidslinje.json` (schema `medielager/1`) och en nyckelruta per tagning |
| `forhands/<klipp>/` | förhandsvisningar (mp4, 540×960) och den nya tidslinjen per operation |
| `granskning/` | före/efter-ark (övre rad original, nedre rad förhandsvisning) |
| `manus/` | manus per scen, för originalet och per utförd ändring |
| `prov/` | provformuläret för K6 (`index.html`) och nyckeln (`nyckel.json`) |
| `_cache/` | återskapbart: egen venv (rapidocr, demucs), OCR-rådata, ljudstammar, whisper-utdata, loggar |

## Miljöer
- `scen/.venv` (används, ändras inte): faster-whisper med KB-whisper small (läses ur `scen/3d/cache/whisper`),
  silero-vad, PySceneDetect, OpenAI CLIP ViT-B/32 (`scen/weights/clip`), YOLO11n-seg (`scen/py/modeller`).
- `_cache/venv` (egen, skapad med uv): RapidOCR 3.10 (PP-OCRv6 small, onnxruntime), Demucs 4.1 (htdemucs), torch 2.15 CPU.
  Återskapas med `uv venv _cache/venv --python 3.12`, sedan `uv pip install torch torchaudio --index-url
  https://download.pytorch.org/whl/cpu` och `uv pip install demucs rapidocr onnxruntime soundfile opencv-python-headless`.

## Ingest (allmän, ingen klippspecifik kod)

```python
from medielager.ingest import ingest            # körs i scen/.venv
fil = ingest("data/format/kontroll/klipp/<id>.mp4")   # → lager/<id>/tidslinje.json
```

| lager | hur | andra läsare (för jämförelse) |
|---|---|---|
| tagningar | PySceneDetect AdaptiveDetector på en nedskalad kopia; rutdiff för stilla/rörlig | ContentDetector; bankens E4/l2 `montage`, `klipp` |
| skärmtext | RapidOCR på en ruta per sekund; rader → block; spår över tid; start/slut förfinade på 10 rutor/s med igenkänning i lådan; typ `overlag`/`scen`/`osaker` ur rörelse i bild; stil (glyffärg, kontur, platta, radhöjd, position); textremsor | E4 `skarmtext`, l2 `text_tung` |
| tal | KB-whisper small med ordtider | silero-vad |
| musik | Demucs htdemucs: röst kontra trummor+bas+övrigt; musik = trummor+bas över -35 dB rel. topp i minst 20 % av 0,5 s-fönstren; sångrisk | E4 `musik`, `trendljud` |
| mat/person | YOLO11n-seg (personer) och CLIP noll-skott (mat, person, miljö, text; plats) på tre rutor per tagning | E4 `mat_andel` |
| montage | antal tagningar, tagningslängder, klipp per 10 s; B-rolltagningar | E4/l2 `montage` |

Alla trösklar är mina och är diagnos, inte krav.

## Ändringsoperationer (funktioner)

```python
from medielager import operationer as op       # körs i scen/.venv
op.byt_text(tl, ny_text, mal=None)              # mal: "x3", del av den gamla texten, eller None (största fria raden)
op.ta_bort_text(tl, mal=None)
op.lagg_till_text(tl, text, fran=0.0, till=None, position="mitt")
op.ta_bort_musik(tl)
op.byt_musik(tl, kalla)                         # kalla: ljudfil från CM eller kundens eget klipp; annars motfråga
op.byt_matbild(tl, mot=None, kundmaterial_lista=op.kundmaterial(tl))
op.korta_montage(tl, andel=0.3, mal_s=None)
```

Varje anrop ger ett `Resultat` (dict): `utfall` (`utford` | `nej` | `motfraga`), `skal`, `lager`, `tidslinje` (ny,
med nyckeln `andring`), `forhandsvisning` (mp4), `andrat` (tid, låda, om bild/ljud rördes, tidsavbildning),
`metoder` (verktygen, för K7-loggen), `generativt` (alltid `False`), `alternativ` (vid motfråga).

Hur de gör:
- **byt_text / ta_bort_text:** den gamla texten täcks med samma platta som originalet (om den hade en) eller med
  oskärpa i lådan; den nya ritas med Pillow i den lästa stilen och läggs på med ffmpeg under samma tid. Ljudet strömkopieras.
- **ta_bort_musik:** röststammen ur Demucs blir nytt ljud; bilden strömkopieras (bitidentisk).
- **byt_musik:** röststammen plus en fil som CM bifogar, eller musik ur kundens eget klipp. Ingen ny musik genereras.
- **byt_matbild:** första tagningen klassad som mat byts mot en annan mattagning ur kundens eget material (samma klipp
  eller kundens andra klipp i banken), vald på `mot` med CLIP eller på högst matsannolikhet. Ljudet strömkopieras.
  Text som låg ovanpå ritas om. Finns maten bara i tagningar med en person, eller saknar kunden annan egen matbild:
  ärligt nej.
- **korta_montage:** stryker B-rolltagningar utan tal, sedan kortar tagningar utan tal mot mitten (minst 1 s). Första
  och sista tagningen och allt tal rörs inte. Med musik: talstammen följer tagningarna, musikbädden löper obruten.
  Färre än tre tagningar: ärligt nej.

## Ingång för spår C (routern)

```python
from medielager.api import utfor
r = utfor(kalla, mening, lager=None, typ=None, **param)
```
`kalla` är en videosökväg (ingest körs vid behov), en tidslinje (dict) eller en `tidslinje.json`. `lager` och `typ`
tas direkt ur `C-cm-mening/router.py` (`r_medie`: lager `skarmtext|ljud|repliker|broll|montage|manus`,
typ `tar_bort|lagger_till|byter`). Saknas de läses de ur meningen med regler. `repliker` och `manus` ger nej i
förhandsvisningen (en ny röst vore generativ) och hänvisar till manuset.

## Koppling till scenpaket/2 (förslag, originalschemat är orört)

`forvarld_karna/scen_brygga.py` skriver `scenpaket/2` med `tidsbas.fps`, `tagningar[].ut = [a, b)` i rutor och
`mening.repliker = []`. Förslag: en ny toppnyckel `medielager` som pekar på (eller bäddar in) `medielager/1`:

```json
"medielager": {
  "schema": "medielager/1",
  "fil": "motpart/runda-3-opus/D-medielager/lager/<klipp>/tidslinje.json",
  "tidsbas": "sekunder; rutor = round(sek * tidsbas.fps), intervall [a, b)",
  "tagningar_karta": {"t1": "s1", "t2": "s2"},
  "skarmtext": [{"id": "x1", "text": "...", "ut": [0, 98], "box": [0.12, 0.53, 0.88, 0.58], "typ": "overlag", "stil": {}}],
  "tal": [{"ut": [10, 66], "text": "...", "ord": [{"o": "...", "ut": [10, 18]}]}],
  "musik": {"finns": true, "ut": [[0, 300]], "stammar": {"tal": "...", "musik": "..."}},
  "mat": {"tagningar": ["t3"]},
  "montage": {"antal_tagningar": 8, "b_roll": ["t3", "t5"]}
}
```
- `mening.repliker` kan fyllas ur `tal.segment` (text, tid, ord) direkt.
- `tagningar_karta` binder D:s tagningar (PySceneDetect) till paketets (ingestens) genom största överlapp i rutor;
  `tidslinje.json` har redan `scenpaket2.tagningar` i rutor för den bindningen.
- Grindarna G1–G7 rör inte medielagret; en egen grind skulle vara "text i lådan läses som tidslinjen säger".

## Kör

```
cd motpart/runda-3-opus/D-medielager
set PYTHONIOENCODING=utf-8
..\..\..\scen\.venv\Scripts\python.exe -X utf8 urval.py
..\..\..\scen\.venv\Scripts\python.exe -X utf8 forbered.py tagningar     (sedan ocr, sep, tal; kan köras parallellt)
..\..\..\scen\.venv\Scripts\python.exe -X utf8 kor_k8.py urval
..\..\..\scen\.venv\Scripts\python.exe -X utf8 sammanstall.py
```
