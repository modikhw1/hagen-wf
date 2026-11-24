# Pass 9: kontroller med ägaren (K1–K4)

Förberett 17 nov 2026. Fyra kontroller, en per gräns mellan sakerna vi skiljer på: din smak, vad LeTrend-innehåll är, hur serien påverkar uppfattningen och publikens utfall. Urval, ordning och prognoser låstes innan du sett något (`data/format/kontroll/forregistrering.json`).

## Så kör du

1. Öppna `data/format/kontroll/spelare/index.html` i Chrome (dra in filen). Klippen spelas lokalt utan siffror.
2. Starta Granola och Miles med prompten för kontrollen.
3. Efter varje sittning: tryck **Ladda ner svar** och lägg filen i `data/format/kontroll/svar/`. Klistra in Granolas transkript som `hagen-ui/_anteckningar/transkript/transkript 10-k1.txt` (k2, k3 osv.).
4. Spelaren minns var du är (i webbläsaren), så du kan sluta mitt i och fortsätta senare.

**Öppna inte** `las.json` eller `kandidater.json` och sök inte upp klippen på TikTok. De visar modellens bedömningar och siffrorna.

## Ordning

| | Vad | Prompt | Tid |
|---|---|---|---|
| **K1** | 20 par: vilket vill du hellre ha i biblioteket? Sedan visas siffrorna: ändrar de något? | `pass-9-k1.txt` | ~30 min, går att dela 10 + 10 |
| **K3** | 30 klipp: lägg i egna högar, namnge dem, markera mest LeTrend | `pass-9-k3.txt` | ~25 min |
| **K2** | 8 klipp ensamma (1–5), sedan i sitt konto: betyg igen, vad bär, vad är utfyllnad | `pass-9-k2.txt` | ~25 min |
| **K4** | Pass 8b, klient B–F (låst sedan 6 nov) | `pass-8b.txt` | en klient per sittning |

## Vad varje kontroll mäter

- **K1, smak mot utfall.** Paren är valda så att nyttan i harness v6 (som träffade dina pass 7-val 16 av 19) och de sju mötesfälten (som följer publikens utfall) alltid pekar åt olika håll. Avslöjandet efteråt mäter om siffrorna flyttar din smak.
- **K3, LeTrend i dina egna ord.** Inga kategorier från Miles; E18 visade att Miles ord blev "dina". Högarna jämförs med mötesfälten, och namnen med E17-axlarna.
- **K2, serien och uppfattningen.** Argon (E16) har kallat ett klipp per konto bärande och ett ihopkastat. Ändras ditt betyg när du ser klippet bland kontots andra, och åt vilket håll?
- **K4, CM-formen.** Om anpassningen går att skicka som den står.

## Efteråt

`../scen/.venv/Scripts/python.exe -u format/kontroll_analys.py` (från `video/`) räknar hypoteserna i förregistreringen. Skälen i transkripten kodas fritt och blir nya abstrakta hypoteser som prövas mot utfall och undanhållna konton. Inget skrivs om efter dina svar.
