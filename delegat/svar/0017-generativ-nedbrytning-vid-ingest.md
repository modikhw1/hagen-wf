---
id: 0017
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-12
---

> **13 nov:** det som återstår (0017 del G, 0018 punkterna 4–6, 0019 varianterna b och c) redovisas i `delegat/svar/0021-kamerafri-kalla-och-in-i-forvarlden.md`.

## Läge efter del C (0018 punkterna 1–2 är invävda; ingen video körd än)
Del A–C är klara, och bilderna är låsta i efterhand med `passa.py`. Video, del D–G, är inte startad. Enligt 0019 ska nyckelbilderna nu göras med Codex innan något animeras. Fal-kostnad hittills är 0,015 USD (`scen/3d/gennedbrytning/kostnad.json`).

**Fal-saldot är cirka 1,90 USD**, enligt ägarens anteckning i `fal_ai.txt`. Det är mindre än 0017:s tak på 4 USD och 0019:s tak på 5 USD. Taket är därför i praktiken satt till 1,85 USD i `fal/falapi.py`.

**A.** Tabellen finns i [fal_modeller.md](../../scen/3d/gennedbrytning/fal_modeller.md). Den är hämtad ur fal:s plattforms-API (schema och pris), inte ur minnet.
- `luma/agent/ray/v3.2/video-to-video` kostar 0,03 USD per sekund i 540p och tar `start_image_url` eller upp till 64 `keyframes` vid valda källrutor. Ägarens Luma-recept med nyckelbilder finns alltså på fal, för cirka 0,15 USD per tagning.
- Maskad video finns också: `fal-ai/wan-vace-14b/inpainting` för 0,08 USD per sekund.

**B. Tom scen** (`b_tom/`, jämförelse i `jamfor_B.jpg`). Utanför personmasken, efter registrering mot originalet:

| Tom scen | Skala mot originalet | Ändrad utanför masken (>12 gråvärden) | Medelfel | Utseende |
|---|---|---|---|---|
| B1 maskad, `object-removal/mask` (0,006) | 1,000 | 12 % | 6,1 | hon är borta, men fyllningen är rörig och texten står kvar |
| B2 promptad STEP A, Uni-1 (0,003) | 0,72 (annat format, 1504×2784) | 29 % | 13,9 | ren, texten borta, kaffemaskin och bänk påhittade |
| Ägarens GPT (`gpt/`) | 1,14 (941×1672) | 36 % | 15,6 | ren och rimlig |

Den maskade borttagningen rör minst utanför masken men ger sämst fyllning. Båda promptade ritar om hela bilden lätt. Vidare går B2 (registrerad) och ägarens GPT-bild, där det bakom henne är märkt `antagen`.

**C. Isolerad person**, före och efter passning (`c_isolerad/`, `passad/*_kontroll.jpg`):

| Isolerad | Rå position | Efter passning: skala, rotation | Överlapp synlig del / IoU ovan disken | Rest huvud / axlar (px) |
|---|---|---|---|---|
| C1 STEP B, Uni-1 | omställd, mindre och centrerad (huvudet 476 px bort) | 0,88, 8,8° | 0,85 / 0,79 | 24 / 20 / 21 |
| C2 städad komposit, Uni-1 | låst (8 px) | 0,69 (bara formatet), 0,05° | 0,85 / 0,77 | 8 / 23 / 13 |
| Ägarens GPT STEP B | rätt i sidled, större | 1,05 i sin 941-ram, alltså cirka 1,09 gånger originalet, 0,1° | 0,87 / 0,78 | 15 / 18 / 17 |

- **Promptningen som höll positionen:** att städa en komposit med låst position (C2). AB-upplägget i Uni-1 (C1) gjorde det inte och ställde om henne.
- **Ägarens GPT-bild** var bara större. Den mätta storleken är cirka 1,09 gånger, inte 1,5–1,7. Den skillnaden ser jag inte förklaringen till.
- **Efter passningen** ligger alla tre inom 8–24 px i huvud och axlar.
- **Armarna avviker hos alla:** i originalet räcker hon ned i disken, i de isolerade hänger armarna eller är böjda. Det syns inte i överlappet men kommer att synas i läsningen.
- **Bäst pose och identitet:** ägarens GPT-bild, med hår, ansikte, tröja och märke. C2 är grövre i underkroppen. C3 (Nano Banana Pro, 0,15) är inte körd, eftersom passningen löser storleken lokalt.

**Princip 3 som efterbehandling:** `passa.py` passar likformigt mot originalets överkropp och lägger resultatet på grå duk i originalets format. Den körs alltid.

## Efter del C (13 nov)
- **Del D och E–F är gjorda i 0019:** variant (a) med Ray 3.2 och startbild, 0,15 USD. Kroppen ur den isolerade videon har bålens största hopp 2,9° (var 7,3°) och rotens 4 cm (var 16,5 cm). Tabellen finns i svar 0019.
- **Del G är inte gjord:** den nya läsningen måste genom ingestens sekvenssteg in i en kopia av gelatos plan.
- **Del H är inte gjord.**

## Nästa (från läget efter del C; se svar 0019)
1. Codex-omslag för bild och nyckelbilder vid rutorna 0, cirka 60–80, 112 och 146 (0019).
2. Luma Ray 3.2 med startbild (a) och med start- och slutbild (b), cirka 0,15 USD per körning.
3. Läsning med `modal_sam3db.py` och film i förvärlden.

## Avvikelser
- **Nyckeln exponerades:** ett felmeddelande skrev ut fal-nyckeln i uppdragstagarens verktygsutdata, eftersom `fal_ai.txt` har en anteckning efter nyckeln. Inget skickades någonstans. Rotera nyckeln. Klienten läser nu bara första raden och rensar nyckeln ur alla fel.
- **B2 kördes om:** första B2-anropet avvisades (data-URI, HTTP 422) innan något genererades, och kördes om med uppladdad bild. Det avvisade anropet ligger i `b_tom/B2_fel_datauri/`.
