# Överlämning: K1 del 1 och de två domarna (18 nov 2026, kväll)

Läs först [k1-del1.md](k1-del1.md) (fynden), sedan den här filen (läget och vad som återstår). Bakgrund till hela essensspåret finns i [overlamning-17nov.md](overlamning-17nov.md) och [essens.md](essens.md). Kontrollernas plan står i `miles/pass-9.md`.

## Var vi står

### Gjort

**K1 par 1–12 är kodade** ur Granola-transkriptet `Desktop/transkript 2.txt`.
- Spelarens svarsfil saknas. Ägaren har inte tryckt *Ladda ner svar*, så valen finns bara i webbläsarens localStorage.
- Kodningen gjordes av tre kodare: Claude och två blinda (Pro och Argon, som bara såg transkriptet).
- Filer i `data/format/kontroll/kodning/`:
  - `k1-del1-claude.json`: val, smak och fritt kodade skäl per par
  - `k1-del1-blind-pro.json` och `k1-del1-blind-argon.json`
  - `k1-del1-konsensus.json`: majoritet av tre
  - `pass7-blind-pro.json` och `pass7-blind-flash.json`: smaken i pass 7 (transkript 8), blindkodad i efterhand

**Huvudfyndet.** Ägaren gör två domar:
- **Biblioteksdomen** handlar om överförbarhet. Den träffar utfallet på slumpnivå: 5 av 11 i K1 och 12 av 19 i pass 7.
- **Smaken** (bättre innehåll) träffar klippet som gått bäst mot kontot i 20 av 26 par (K1 8/11, pass 7 12/15).
- Analysskript: `video/format/kontroll_k1_del1.py`.

**E41, förregistrerat** (`data/format/e41/`). Pro läser varje klipp för sig: överförbarhet, bärare, hålla och svepsekund.
- Läst: 240 replikeringsklipp (`e19/argon-ids.json`) och de 40 K1-klippen.
- Resultat: HE41b–d faller, HE41a håller svagt. Svepsekunden +0,17 (p 0,056) är bara utforskande.
- Skript: `video/format/e41.mjs` och `e41_analys.py`.
- Läsarbyte från Argon till Pro (Argons kvot tog slut) är dokumenterat i förregistreringen. De 7 Argon-läsningarna ligger i `lasning-argon/`.

**E42, förregistrerat** (`data/format/e42/`). Pro läser paren med ägarens två frågor, i båda ordningarna.
- Alla fyra hypoteserna faller.
- Ägarparen: tittarvalet träffar ägarens smak i 11 av 22.
- Utfallsparen: 57 av 107 (53 %).
- Kvoten tog slut efter 131 av 200 utfallspar. Skript: `video/format/e42.mjs` och `e42_analys.py`.

**v2-promptar** i `miles/`: `pass-9-k1-v2.txt`, `-k2-v2.txt`, `-k3-v2.txt`. Originalen är orörda.
- Alla tre har Miles-disciplin: upprepa frågan ordagrant, ge aldrig exempel, sammanfatta aldrig.
- K2 frågar "as content".
- K3 har en ny tittarfråga.
- Tillägget med HK3d och HK2e står under `tillagg_18nov` i `data/format/kontroll/forregistrering.json`.

**Låsta prognoser** för K1 par 13–20: `data/format/e41/prognos-k1-13-20.json`.
- `bib_overforbar`: klippet med högst överförbarhet.
- `smak_halla`: klippet med högst hålla.
- Gäller HE41e–g.
- OBS: E41:s "hålla" träffade ägarens smak i bara 3 av 10 i provet, så HE41f väntas falla. Det är ärligt låst ändå.

### Kostnad
Ungefär 14 USD via beacon-proxyn (Pro cirka 0,015 USD per klipp, parläsning cirka 0,018 USD). Ägaren gav 10–40.

### Kvoter vid stopp (cirka 23:00)
Argon och Pro svarade `quota_exhausted` (429), Flash 3.8 svarade. Pröva med ett ensamt anrop innan något startas.

## Vad som återstår, i ordning

1. **Ägarens svarsfil.** Be ägaren trycka *Ladda ner svar* i `data/format/kontroll/spelare/index.html`. Lägg filen i `data/format/kontroll/svar/`. Jämför valen i filen med konsensuskodningen. Avvikelser är intressanta, eftersom spelarens radioknapp är biblioteksvalet.

2. **K1 par 13–20**, när ägaren kört dem med `pass-9-k1-v2.txt`:
   - Transkriptet läggs som `../hagen-ui/_anteckningar/transkript/transkript 10-k1.txt` eller liknande.
   - Koda med samma tre kodare. Blindkodning: `cd video && LOVABLE_KONTO=beacon node format/kontroll_kodning.mjs "<transkript>" ../data/format/kontroll/kodning/k1-del2-blind-pro.json google/gemini-3.1-pro-preview`, och samma sak med Argon.
   - **Öppna inte E41-läsningarna av K1-klippen förrän ägaren är kodad.** Det kräver förregistreringen.
   - Pröva sedan HE41e–g mot den låsta prognosen. Kör `video/format/kontroll_analys.py` (HK1a–e) när svarsfilen finns.
   - HK1a och HK1b kan inte längre hålla matematiskt: nyttan 6/11 och fälten 5/11, och 15/20 krävs. Säg det rakt ut.
   - Utvidga `kontroll_k1_del1.py` till par 1–20, eller skriv en del 2.

3. **K2 och K3** med v2-promptarna. Koda HK3d (tittarhögen) ur transkriptet. Svarsfilen har bara `mest` och `aldrig`.

4. **Valfritt när kvoten öppnar:** de 69 utfallspar i E42 som saknas.
   - Kör `timeout 570 node format/e42.mjs --mangd utfall --par 6` i förgrunden, upprepat.
   - Resultatet ändras troligen inte (53 % på 107). Låg prioritet.

## Öppna idéer, inte prövade

- **Ägarens smak som egen etikett.** Den är den enda läsaren som träffar publiken parvis (77 %). Samla den billigt i kommande pass med en extra fråga: "which one do you like more as content". Fråga ägaren först, och ändra inte K1 mitt i.
- **Varför missar Pro?**
  - Läs skälen i `e42/lasning/*.json` (`viewer_reason`) mot ägarens smakskäl i `k1-del1-claude.json`. Hypotes: modellen värderar premiss och "smart idé", medan ägaren och publiken värderar att uppmärksamheten aldrig tappas, mänsklighet och charm.
  - Pröva Argon på parfrågan när kvoten finns. Läsaren var den största hävstången i E19, där Argon gav +0,16 över Flash.
  - Gör det inte genom att skriva om frågorna efter resultatet. Gör en ny förregistrering.
- **Gratismått mot smaken** (26 par, utforskande, inget förregistrerat): det valda klippet är längre i 18 av 26 och har tidigare tal i 11 av 16. För litet för att bära. Pröva bara som förregistrerad hypotes på nya ägarpar.
- **Exponering.** Ägaren känner igen tre konton (lilla.pixel, rosen.pizza, corniche-talaren). Kontrollera framtida urval mot konton ägaren sett, inte bara klipp.

## Fällor
- Granola blandar Miles, ägaren och klippens ljud under "Me" och "Them". Par 4 transkriberades som "Care for". Miles samtal bryts efter cirka 25 minuter.
- Beacon-skripten försöker igen vid 429. När kvoten är helt slut står de still utan att skriva något. Räkna filerna i `lasning/` för att se framsteg.
- Python körs med `scen/.venv/Scripts/python.exe`. `python` finns inte i PATH. Sätt `PYTHONIOENCODING=utf-8`.
- Vakten för `delegat/` listar sex gamla uppdrag utan svar (0037, 0040–0043, 0045) varje gång den startas om. De hör inte till det här spåret.
