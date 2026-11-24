---
id: 0010
titel: Bygg in det som bar i proven: mätta kameragrupper och segmenterade rutor med kontroller, och kör b-tilltal till film
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0008
tillåten_skrivning: [scen/3d/ingest/rum_grupper.py, scen/3d/ingest/rum_rutor.py, scen/3d/ingest/modal_segmentera.py, scen/3d/ingest/rum_detektera.py, scen/3d/ingest/rum_konsensus.py, scen/3d/ingest/rum_uppsattning.py, scen/3d/ingest/test_rum.py, scen/3d/klipp_kor.py, scen/3d/kontrakt/ut/fore_mattram_0010/, scen/3d/ingest/ut/, scen/3d/kontrakt/ut/, scen/3d/PIPE.md, scen/3d/NASTA.md]
---

## Mål
Kedjan från video till film använder mätning där proven visade att mätning bär, i stället för Geminis gissning, och det är visat på `b-tilltal-ravara` och ett klipp till att resultatet blir bättre eller lika.

## Bakgrund
Fyra prov i kväll, läs svaren i `delegat/svar/`:
- **0002:** SIFT på bakgrund med maskade personer mäter säkert vilka tagningar som delar kameraplats. Slumpnivån är under cirka 40 F-inliers, kakelalias når cirka 104, och säkra par börjar vid cirka 125.
- **0008:** rutor ur Grounding DINO + SAM 2 (Apache-2.0) träffar avlästa kanter inom 1 promille där Geminis `box_2d` låg 66–177 promille fel. Två kontroller fångar resten: överlapp mellan element, och homografiöverföring mellan tagningar som delar plats.
- **0007:** passningen utesluter nu avvikande rutor själv.
- **0003:** Gemini läser en plankarta bra (rätt kamera i 51 av 52), men ska inte granska geometri. Byggs inte in här.

Kedjans steg i dag står i `scen/3d/NASTA.md` överst (sju steg). Gemini fortsätter säga **vad** som finns, vem som är vem och vad som är relevant.

## Att göra
1. **`ingest/rum_grupper.py`** (ur `ingest/bakgrund_prov/matcha.py`): ger per klipp `delar_plats` som grupper av tagningar, med tal per par och status `matt`, samt vilka tagningar som saknar mätbar koppling. Nollkontrollen ska räknas per klipp (blandade rutpar ur samma klipp duger inte; använd ett annat klipp eller permuterade matchningar) så att gränsen inte är ett fast tal.
2. **`rum_konsensus.py`** tar grupperna som givna fakta för frågan "samma kamera", på samma sätt som ingestens fakta redan är givna. Geminis röstning och fokusfrågorna används bara för par som mätningen inte säger något om. Mätt och röstat ska gå att skilja i utdata.
3. **`ingest/rum_rutor.py`** + `modal_segmentera.py` (ur `ingest/rutprov/`): rutor per element och tagning ur segmenteraren, med Geminis elementnamn som prompt. Tre kontroller, var och en med orsak i utdata: överlapp mellan olika element, homografiöverföring inom grupperna ur punkt 1, och `null` när elementet inte hittas. En ruta som faller i en kontroll förs inte vidare.
4. **Koppla in** rutorna där `rum_detektera.py` och uppsättningen i dag levererar `bild`/`bilder`, bakom en flagga (`--rutor segment|gemini`), så att gamla vägen går att köra för jämförelse.
5. **Kör `b-tilltal-ravara` hela vägen** med nya vägen, nivå 0,6, till en ny variant (`n06-matt`), `prepare` och `render`. Kör sedan ett klipp till, `e-dialog-guacamole` eller `kand-kennysgelato`.
6. **Skriv in det i `PIPE.md`** (steget, var det ligger, vad som är mätt och vad som är hypotes) och ett kort lägesavsnitt överst i `NASTA.md`.

## Gränser
- Bara filerna och mapparna i `tillåten_skrivning`. I `ut/`-mapparna skrivs bara nya varianter; befintliga mappar skrivs aldrig över. Baslinje av ändrad kod först till `kontrakt/ut/fore_mattram_0010/kod/`.
- Modal för segmenteringen och gatewayen för eventuella nya Gemini-körningar är förhandsgodkända enligt `REGLER.md`. Tak: 1,00 dollar Modal, 0,50 dollar gateway. Återanvänd befintliga Gemini-svar där det går.
- Rendering med kedjans vanliga körväg (`klipp_kor.py … render`) ingår.
- Ändra inget medan ett test, en kompilering eller en rendering kör. Verifiera med tom cache.
- Trösklar i kontrollerna är diagnos. Redovisa dem i utdata och i svaret, och säg vilka som är härledda ur data (nollkontrollen) och vilka som är valda.
- Blir något av stegen större än väntat: gör 1–3 klart och redovisa, hellre än alla sex halvt.

## Klart när
- Snabbtesterna och ingesttesterna är gröna, med antal, och nya prov finns för grupperna och de tre rutkontrollerna.
- b-tilltal, nya vägen mot gamla (`n06-fler` med 0007:s kod): spridning för `disk_C` och vågen mellan tagningar, antal uteslutna och stoppade rutor, ankarrest, och personerna mot facit (ska vara 55 av 55).
- Projektion i slutkameran: diskkant och våg i s6, s10 och s11 jämfört med originalets nyckelbild, i promille av bildhöjden.
- Film finns för b-tilltal i nya varianten, med sökväg. Säg vad som syns bättre och vad som fortfarande är fel.
- Andra klippet går igenom utan handpåläggning, eller så är det beskrivet var det stannar.
- `PIPE.md` och `NASTA.md` uppdaterade.

## Leveransform
`delegat/svar/0010-matt-ram-in-i-kedjan.md` enligt mallen, högst cirka 80 rader, med faktisk kostnad.
