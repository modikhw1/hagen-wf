# Harnessen v6: körordning (4 nov 2026)

Alla skript körs från `video/` och skriver till `data/format/`.

## Miljövariabler och modellvägar
| Väg | Variabel | Anmärkning |
|---|---|---|
| Lovable-brygga 1–4 | `LOVABLE_KONTO=1…4` | `LOVABLE_URL_n` och `LOVABLE_NYCKEL_n` i `video/.env.local`. Bryggan läser hemligheten `ANALYS_NYCKEL` och måste publiceras om efter att hemligheten ändrats. Prompten får vara högst 20 000 tecken och videon högst cirka 15 MB. |
| AI Studio, gratisnivå | `LOVABLE_KONTO=aistudio` | Bara Flash. 20 anrop per dag, modell och projekt. |
| Vertex direkt | `GEMINI_VAG=vertex` (typer/gemini.mjs) | Används inte av format-skripten. Faktureringen i projektet Hagen är spärrad. |

Uppmätt kostnad (konto 4): Flash 3.8 cirka 9 000 tokens per kort, och cirka 0,005 krediter per 1 000 tokens.

## Kedjan
| Steg | Kommando | Kostnad |
|---|---|---|
| 1. Sålla banken | `node format/e10-bank.mjs` och `bank-tratt2.mjs` (sketcher) eller `bank-tratt3.mjs` (tilltal), som också hämtar filerna | 0 |
| 2. Kort v5, original | `node format/kort5.mjs --extra <extra.json> --idfil <ids.txt> --ut ../<katalog>/kort --modell google/gemini-3.8-flash --kortdoktrin` | ~9 000 tokens per klipp |
| 3. Kort v5, rutnät (sketcher) | samma med `--rutnat` | ~9 000 tokens per klipp |
| 4. Tema | `node format/tema.mjs` (text, 12 klipp per anrop) | låg |
| 5. Bibliotek v6 | `node format/bibliotek-v6-bygg.mjs` → `harness/bibliotek-v6.json` | 0 |
| 6. Kundlinje | `node format/h-linje.mjs --konton a,b` (Pro, de 10 senaste klippen) | ~25 000 tokens per kund |
| 7. Förslag per kund | `node format/h-forslag.mjs` → `karta/videoforandring/forslag-v6.md` | 0 |
| 8. Scenplan | `node format/h-scener.mjs --konto k --id id` | 0 |
| 9. Anpassning | `node format/h-anpassa5.mjs --konto k --id id [--ut katalog]` (Pro, text) | ~6 000 tokens |

## Efter ägarens pass
| Pass | Koda svaren i | Analys |
|---|---|---|
| 6 | `harness/pass6/agare.json` | `node format/h-pass6-analys.mjs` (v5, v6 och v6.1) |
| 7 | `harness/pass7/agare.json` | `node format/h-pass7-analys.mjs` |
| 8 | `harness/pass8/agare.json` | `node format/h-pass8-analys.mjs` |

## Utvärdering utan nya anrop
- `node format/meta.mjs`: räckeskartan med konfidens
- `hyllor-grund.mjs`: att grundvärdet sorterar mellan hyllorna och nyttan inom dem
- `e11.mjs` och `e11b.mjs`: hela banken
- `triad.mjs`: sanning, preferens och nytta per lager
