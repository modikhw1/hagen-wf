# semantik: kallas semantiska lager ur en första Gemini-körning, bundet till uppmätta spår

Ingest mäter allt som går att mäta (personspår med kroppsrörelse, kamera, rum). Det som inte går att mäta saknades för varje nytt klipp: vem som är vem mellan tagningarna, roller, vilka tagningar som delar kameraställe, vem som vänder sig mot vem, transkript med talare, ordtider, platstyp och vad personerna sitter eller står vid, rekvisita, scenfunktion och skärmtext. För notan kom det ur handkalibrerade filer (`scen3d.json`, `ordtider.py`). Den här mappen gör ett utkast av samma sak automatiskt. Utkastet är **modellbedömt**, inte mätt, och alla värden bär det.

Inget utanför `semantik/` är ändrat. All utdata ligger i `semantik/ut/<klipp>/`. Klippen heter `notan`, `b`, `a`, `kenny` (register i `sem_gemensamt.py`).

## Flödet

```
ingest/ut/<klipp>-tagningar/S*/personer.json, klipp/S*.mp4, tagningar.json
        │
        ├─ kontaktblad.py ─────────► ut/<klipp>/blad/S<n>.jpg   (spåren inritade och märkta S3:1)
        ▼
semantik_ingest.py  ──(1 Gemini-anrop: video + blad + spårtabell + prompt + schema)──►  semantik.json  (eller avvisat.json)
        ▼
ordtider_klipp.py   ──(lokal Whisper, utan ledtråd)──►  ordtider_ra.json, ordtider.json
        ▼
till_kalla_underlag.py ──►  underlag/{vem_ar_vem, scen3d_roller, hand, ordtider_underlag, ofunna_repliker, patch}.json
        ▼
kor_nedstroms.py    ──►  plats.py, kalla_bygg.py, bro-patchen, schemakontroll  (nedstroms.json)
```

Kör från projektroten med `scen/.venv/Scripts/python.exe` och `PYTHONIOENCODING=utf-8`:

```
python -B scen/3d/kontrakt/semantik/semantik_ingest.py <klipp> [--torrkorning | --bearbeta-svar svar_ra.json | --ny]
python -B scen/3d/kontrakt/semantik/ordtider_klipp.py <klipp> [--sprak da] [--modell auto|kb-medium|kb-small|systran-small]
python -B scen/3d/kontrakt/semantik/till_kalla_underlag.py <klipp>
python -B scen/3d/kontrakt/semantik/kor_nedstroms.py <klipp> [--plats-skript scen/3d/ingest/flera/plats_patchad_kopia.py]
python -B scen/3d/kontrakt/semantik/utvardera_notan.py       (bara notan: jämför mot facit)
python -B scen/3d/kontrakt/semantik/test_semantik.py          (inga nätanrop; MOCK-svar bara för kodprov)
```

## Hur modellens svar knyts till mätningen

1. **Ett kontaktblad per tagning** (högst sex rutor, tidsordnade, 3 × 2). Varje uppmätt spår är ritat vid sin uppmätta box (`personer.json`) och märkt `S3:1`, alltså tagning och spårets nyckel i den tagningens `personer.json`. Rutan är rubricerad med tagning, källbildruta och sekund. Färgerna betyder inget mellan tagningar, och det står i prompten.
2. **En spårtabell i text** med samma nycklar och mått (rutor, boxens storlek, läge, om den ligger mot bildkanten) och en tagningstabell med bildintervall och sekunder.
3. **Videon med ljud** i samma anrop (`inlineData`, `video/mp4`, som `video/typer/lovable.mjs`). Bladen kan inte bära ljud, och Geminis standard är en bild per sekund, så bladen står för synen och videon för tal och skärmtext.
4. **Svaret får bara peka på det som finns.** `personer[].spar` har `(tagning, spar_id)`; varje uppmätt spår ska stå i exakt en persons lista eller i `ej_personer` med typ och skäl (främre arm eller hand, bakgrundsperson, reflektion, affisch eller skärm, felaktig detektion). Ett spår som inte finns, ett som används två gånger, en okänd person, tagning eller talare, ett schemafel eller ett avbrutet svar (`finishReason` annat än STOP) **avvisar hela svaret**: `avvisat.json` får felen, `semantik.json` skrivs inte, inget repareras. Spår som svaret glömt blir varningar, inte fel (de blir `okand_s<n>_<id>` nedströms).
5. `semantik.json` har modellnamn, promptversion och hashar (video, prompt, tabell, schema, varje blad, varje `personer.json`, `tagningar.json`) samt anropets tokens.

Promptens regler och varför: spår är bara unika inom en tagning, och trackern har fel (prompten räknar upp främre arm, förbipasserande, reflektion, affisch). "osaker" och tomma listor är giltiga svar överallt, så att modellen inte tvingas gissa. Personer i samma uniform räknas som olika om inget visar annat. Talet ska skrivas ordagrant i originalspråket och inte hittas på. Uppräkningarna följer redan befintliga ordförråd: ankartyperna `sate, bordskant, staplats, sta_bakom, annat`, möbeltyperna i rumsmallarna, rumsmall-id, scenfunktionerna i harnessen. "ingen_passar" är tillåtet. Schemat (`semantik.schema.json`) skickas som `responseJsonSchema` och kontrolleras sedan igen lokalt med en egen kontroll (`sem_gemensamt.validera`).

Anropsräknaren `ut/anrop.json` räknar varje försök, även de som svarat 503, och stoppar vid 10. Nyckeln läses ur `video/.env.local` (`GEMINI_API_KEY_GRATIS`) i processen och skrivs aldrig ut eller sparas. Modell: `gemini-3.5-flash` (en av de tre som gratisnivån tar enligt `lovable.mjs`).

## Ordtider (`ordtider_klipp.py`)

Generaliserar `scen/3d/ordtider.py`. Ljudet tas ur klippet med ffmpeg. Modell: KBLab kb-whisper-medium för svenska, annars den flerspråkiga Systran faster-whisper-small (båda låg redan på disk; inget hämtas). **Whisper får inga repliker som ledtråd** (ordtider.py gav manuset som `initial_prompt`); annars hittar Whisper det modellen skrev även när ljudet saknar det. Modellens repliker kopplas till Whispers ord med en monoton, oskarp ordmatchning. Varje replik får täckning (andel hörda ord), start, slut och orden med tider. Täckning under 50 %, eller träffar spridda över mer än 3 s + 0,8 s per ord, flaggar repliken `stodd=false`: den får inga tider och hamnar i `ofunna_repliker.json`. Whisper-ord som ingen replik förklarar listas som `tal_utan_replik`.

## Vad som är kopplat till uppmätta id, och vad som inte är det

Kopplat: vilket spår som är vilken person, vilka spår som inte är personer, vilka tagningar som delar kameraställe, vilka personer som talar i vilken tagning (via person-id), ordens tider (Whisper på riktigt ljud).

Fritt, alltså bedömningar utan mätning: personernas roller och beskrivningar, kamerauppställningarnas innehåll, platstyp och mallval, hållning och möbel per person, vänder-sig-mot-varandra, rekvisita och hållare, scenfunktion, skärmtext, replikernas text och talare.

## Underlagen (`till_kalla_underlag.py`) och de befintliga verktygen

| Fil | Används av | Hur |
|---|---|---|
| `scen3d_roller.json` | `plats.py --scen3d`, `kalla_bygg.py --scen3d` | Minimal scen3d-form: `actors`, `shots[].actors/beat/source`. Verktygen binder roller till spår i ordning efter rutor i bild, så aktörslistan skrivs i den ordningen, med `okand_s<n>_<id>` där spåret inte är en berättelseperson. |
| `hand.json` | `plats.py --hand` | `rumsmall` och `layout` (status `modellbedomd`). Inga meterlägen; `plats.py` får räkna dem. |
| `ordtider_underlag.json` | `kalla_bygg.py --ordtider` | `ordtider.json`-format med bara de repliker Whisper hörde. |
| `patch.json` | `bro/kort_till_kalla.tillampa_patch` | Följer `kalla-patch/1` för scener, intention, beats (tom) och serie. Bron har inga fält för personer, skärmtext, props och plats: de ligger i avsnittet `tillagg`, som `till_kalla_underlag.tillampa_tillagg()` läser. |
| `vem_ar_vem.json` | människor och granskning | Spår → person, roll, skäl, dubbletter. Alla poster har `ursprung`. |

Varje värde har `ursprung = {typ: modellbedomd, modell, prompt_version, konfidens}`. Personerna får bokstavsnamn A, B, C i ordning efter första tagning där de syns (modellens P1, P2 sparas), eftersom `plats.py` och rumsmallarna namnger ankare efter person-id (`stol_A`). Två spår i samma tagning som modellen pekat på samma person (dubbelspår) ger den ena `okand_`. `tillampa_tillagg` rättar det `kalla_bygg` skriver fast: `roll_kalla: scen3d` blir `modell`, replikernas `kalla: whisper` blir `modell`, och en kvalitetspost om modellbedömt underlag läggs till.

## Vad en människa fortfarande måste göra

- Granska varje person-till-spår-koppling mot kontaktbladen, särskilt personer som kan vara samma skådespelare i två roller och personer utan synligt ansikte.
- Läsa och rätta transkriptet, särskilt siffror, främmande språk och repliker Whisper inte hörde (`ofunna_repliker.json`).
- Avgöra mallval och möbler när ingen rumsmall passar, och hållning (se nedan: mätt sittande kan vara fel).
- Ange kameraställen som bildmatchningen inte hittar, och meterlägen för personer i tagningar utan bildkoppling.
- Besluta scenfunktion där tolkningen är öppen (vad som är punchline).
- Skriva beats och serieposition; modellen ger dem inte.

## Kända luckor (verktygen är inte ändrade)

Se slutrapporten i arbetsloggen och `ut/<klipp>/nedstroms.json`: `plats.py` kraschar utan patch vid rörlig kamera, `varld.npz` saknas för tagning utan person, `plats.py` avgör sittande eller stående bara ur uppmätt bäckenhöjd (ingen handöverstyrning per roll), `bar_disk`-mallens ankarnamn matchar inte generella personid, och `kalla_flera.py` skriver `roll_kalla: scen3d` och `kalla: whisper` fast.

## Komplettering: text och disk (lokalt)

Standardbygget i `kalla_flera.py` för nu vidare den sparade skärmtexten. Position, stil och synlighet kommer från källbilderna via `../skarmtext.py`, inte från ett nytt modelljobb. När fontmallar inte räcker kan `../textreferenser/` ange en granskad källruta och box; pixelmasken följs sedan genom tagningen. Textinnehållets ursprung hålls isär från lokaliseringen och fontapproximationen. Undertexter pekar på sin replik så att ett godtaget replikbyte också byter undertext.

Butik/disk använder nu chark-, glass- eller serveringsdisk i `ingest/diskplats.py`. Ankartyper som motsäger kundrollen rättas med redovisat antagande. Mått är mallvärden; stilla handleder är bara möjlig kontakt-evidens. Ankarnas konstruktionsrest är inte en oberoende mätning av rummets riktighet.
